import xlwings as xw
import os
import sys
import shutil
import re
import openpyxl.utils
from get_attendance_data import fetch_attendance_data, sync_staff_list
from datetime import datetime

def select_file():
    files = [f for f in os.listdir(".") if f.startswith("【出勤簿】") and f.endswith(".xlsx") and "計算式適用済" not in f]
    if not files:
        print("エラー: 【出勤簿】で始まるExcelファイルが見つかりません。")
        return None, None
    
    print("==================================================")
    print(" 処理する出勤簿ファイルを選択してください")
    print("==================================================")
    for i, f in enumerate(files):
        print(f" [{i+1}] {f}")
    print("==================================================")
    
    try:
        idx = int(input("番号を入力してください (1-{}): ".format(len(files)))) - 1
        if 0 <= idx < len(files):
            target = files[idx]
            # ファイル名から月を取得 (例: 【出勤簿】202604.xlsx -> 2026-04)
            match = re.search(r"(\d{4})(\d{2})", target)
            if match:
                month = f"{match.group(1)}-{match.group(2)}"
            else:
                month = datetime.now().strftime("%Y-%m")
            return target, month
    except Exception:
        pass
    return None, None

def main():
    # 1. ファイルと月の選択
    file_name, month = select_file()
    if not file_name:
        print("選択がキャンセルされました。")
        return

    # 2. データの取得
    print(f"{month} の実績データをLINEから取得して処理を開始します...")
    data = fetch_attendance_data(month)
    if not data:
        print("警告: 実績データが取得できませんでした。")

    # 3. ファイルの準備
    cwd = os.getcwd()
    file_path = os.path.join(cwd, file_name)
    output_name = file_name.replace(".xlsx", "_計算式適用済.xlsx")
    output_path = os.path.join(cwd, output_name)
    
    if os.path.exists(output_path):
        try: os.remove(output_path)
        except: print("警告: 既存の出力ファイルを削除できませんでした。開いている場合は閉じてください。")
    shutil.copy2(file_path, output_path)

    print(f"Excelを起動して高速処理中: {output_name}")
    
    # 4. xlwings で Excel を操作
    app = xw.App(visible=False)
    try:
        wb = app.books.open(output_path)
        
        # 設定シートから全社員名を取得
        ws_set = wb.sheets["設定"]
        staff_list_raw = ws_set.range("B5:B50").value
        staff_names = [str(n).strip() for n in staff_list_raw if n and str(n).strip()]
        print(f"設定シートから {len(staff_names)} 名の社員を読み込みました")

        # 社員名簿の同期
        sync_staff_list(staff_names)

        # 実績シートの更新
        if "実績" not in [s.name for s in wb.sheets]:
            print("エラー: '実績'シートが見つかりません。")
            return
        
        ws_jisseki = wb.sheets["実績"]
        emp_rows = {}
        for i, name in enumerate(staff_names):
            row = 3 + (i * 4)
            ws_jisseki.range(f"A{row}").value = name
            ws_jisseki.range(f"B{row}").value = "出勤状態"
            ws_jisseki.range(f"B{row+1}").value = "現場名"
            ws_jisseki.range(f"B{row+2}").value = "残業"
            ws_jisseki.range(f"B{row+3}").value = "弁当"
            emp_rows[name.replace(" ", "").replace("　", "")] = row

        # 実績データの流し込み
        for name, emp_data in data.items():
            clean_sn = name.replace(" ", "").replace("　", "")
            # 苗字のみの報告でもフルネームにマッチさせる（例：土本 -> 土本凱斗）
            base_row = None
            for full_n, r in emp_rows.items():
                if full_n.startswith(clean_sn):
                    base_row = r
                    break
            if not base_row: continue
            for key, days in emp_data.items():
                if key == "残業":
                    for d, h in days.items():
                        col = 3 + (int(d)-1)
                        ws_jisseki.range((base_row+2, col)).value = h
                elif key == "弁当":
                    for d in days:
                        col = 3 + (int(d)-1)
                        ws_jisseki.range((base_row+3, col)).value = "〇"
                else:
                    status = key
                    site = ""
                    if "(" in key:
                        status, site = key.split("(", 1)
                        site = site.replace(")", "")
                    for d in days:
                        col = 3 + (int(d)-1)
                        ws_jisseki.range((base_row, col)).value = status
                        if site:
                            ws_jisseki.range((base_row+1, col)).value = site

        # 個別シートの更新 (高速版)
        template_ws = wb.sheets["土本　凱斗"]
        existing_sheet_names = [s.name for s in wb.sheets]
        
        for name in staff_names:
            clean_sn = name.replace(" ", "").replace("　", "")
            if name not in existing_sheet_names:
                print(f"  新規シート作成: {name}")
                template_ws.copy(after=wb.sheets[-1], name=name)
                existing_sheet_names.append(name) # 追加
            
            ws = wb.sheets[name]
            base_row = emp_rows.get(clean_sn)
            if not base_row: continue

            print(f"  高速パッチ適用中: {name}")
            ws.range("AB2").value = name
            
            # ヘッダー等
            ws.range("AH1").value = "前月最終週の累計:"
            ws.range("AJ2").formula = f"=実績!$AH${base_row}"
            ws.range("AI1").value = "当月最終週の累計:"
            ws.range("AJ1").formula = '=IF($B$4="","", IF(WEEKDAY(MAX($B$4:$B$34),1)=7, 0, SUMIFS($R$4:$R$34, $BA$4:$BA$34, MAX($BA$4:$BA$34)) + SUMIFS($S$4:$S$34, $BA$4:$BA$34, MAX($BA$4:$BA$34))))'

            # 数式の一括取得・置換・一括書き戻し (ここが超高速)
            formula_range = ws.range("A1:AJ40")
            all_formulas = formula_range.formula
            new_formulas = []
            for row_formulas in all_formulas:
                new_row = []
                for f in row_formulas:
                    if isinstance(f, str) and "実績!" in f:
                        new_f = f
                        new_f = re.sub(r'(実績!\$?[A-Z]+\$?)3\b', rf'\g<1>{base_row}', new_f)
                        new_f = re.sub(r'(実績!\$?[A-Z]+\$?)4\b', rf'\g<1>{base_row+1}', new_f)
                        new_f = re.sub(r'(実績!\$?[A-Z]+\$?)5\b', rf'\g<1>{base_row+2}', new_f)
                        new_f = re.sub(r'(実績!\$?[A-Z]+\$?)6\b', rf'\g<1>{base_row+3}', new_f)
                        new_row.append(new_f)
                    else:
                        new_row.append(f)
                new_formulas.append(new_row)
            formula_range.formula = new_formulas

            # 共通項目 (D, F, BZ, AJ列を一括更新)
            # D, F, BZ, AJ 列は 4, 6, 78(BZ), 36(AJ)
            # ... 面倒なのでここだけは個別でも高速。
            for r in range(4, 35):
                c_let = openpyxl.utils.get_column_letter((r-3) + 2)
                ws.range(f"D{r}").formula = f'=IF(実績!{c_let}{base_row}="","",IF(実績!{c_let}{base_row}="休出(出張)","休出",IF(実績!{c_let}{base_row}="振出(出張)","振出",実績!{c_let}{base_row})))'
                ws.range(f"F{r}").formula = f'=IF(実績!{c_let}{base_row+1}="","",実績!{c_let}{base_row+1})' 
                ws.range(f"BZ{r}").formula = f'=IF(OR(実績!{c_let}{base_row}="休出(出張)",実績!{c_let}{base_row}="振出(出張)"),"出張","")'
                ws.range(f"AJ{r}").formula = f'=IF(実績!{c_let}{base_row+3}="","",実績!{c_let}{base_row+3})'

            ws.range("C38").formula = '=COUNTIFS($D$4:$D$34,"現場")+COUNTIFS($D$4:$D$34,"出張")+COUNTIFS($D$4:$D$34,"振出")'

        wb.save()
        wb.close()
        print(f"完了しました: {output_path}")
        
    finally:
        app.quit()

if __name__ == "__main__":
    main()
