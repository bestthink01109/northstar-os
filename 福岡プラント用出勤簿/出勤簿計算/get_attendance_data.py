import requests
import json
from datetime import datetime

# GAS Web App URL
GAS_URL = "https://script.google.com/macros/s/AKfycbyJRWyE6OMarLdiFTTVnQnN2SiS6uvjv0X-LM4d6FrDMqWr1ldLEZ-nW4ewJ66I8frtGg/exec"

def fetch_attendance_data(month_str=None):
    """
    GASから実績データを取得し、calc_xlwings.py形式に変換する
    month_str: '2026-04' のような形式。
    """
    if not month_str:
        month_str = datetime.now().strftime("%Y-%m")
    
    print(f"[{month_str}] の実績データをLINE連携システムから取得中...")
    
    try:
        response = requests.get(GAS_URL, params={"month": month_str}, timeout=60)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"データ取得エラー: {e}")
        if 'response' in locals():
            print(f"生のレスポンス内容 (先頭100文字): {response.text[:100]}")
        return {}

    # GASが2D配列（リストのリスト）を返す場合の処理
    if not isinstance(data, list):
        print(f"GASエラー: 予期しないデータ形式です。")
        return {}

    inject_data = {}
    # カラムインデックス: 0:タイムスタンプ, 1:氏名, 2:日付, 3:状態, 4:場所, 5:残業, 6:弁当
    for row in data:
        if len(row) < 7: continue
        
        name = str(row[1]).replace(" ", "").replace("　", "")
        if not name or name == "氏名": continue # ヘッダー除外
            
        if name not in inject_data:
            inject_data[name] = {
                "残業": {},
                "弁当": []
            }
        
        # 日付から日(int)を抽出
        date_val = str(row[2])
        try:
            if "T" in date_val:
                # ISO形式 (2026-04-01T15:00:00.000Z)
                # UTCから日本時間(JST)へ+9時間して変換
                iso_str = date_val.replace("Z", "+00:00")
                dt_utc = datetime.fromisoformat(iso_str)
                # 日本時間に変換（簡易的に+9時間）
                from datetime import timedelta
                dt_jst = dt_utc + timedelta(hours=9)
                day = dt_jst.day
            else:
                # シンプルな文字列 "2026-05-11" や "2026/05/11"
                dt = datetime.strptime(date_val.replace("/", "-").split(" ")[0], "%Y-%m-%d")
                day = dt.day
        except Exception as e:
            continue

        status = str(row[3])
        site = str(row[4])
        overtime = row[5]
        bento = str(row[6])

        # 状態(場所) のキーで日を管理
        status_key = status
        if site:
            status_key = f"{status}({site})"
        
        if status_key not in inject_data[name]:
            inject_data[name][status_key] = []
        inject_data[name][status_key].append(day)

        # 残業
        if overtime and str(overtime) != "0":
            inject_data[name]["残業"][day] = overtime
            
        # 弁当
        if bento == "〇":
            inject_data[name]["弁当"].append(day)

    return inject_data

def sync_staff_list(staff_names):
    """
    Excelの社員リストをGoogleスプレッドシートの「社員マスター」へ同期する
    """
    print(f"社員マスターをスプレッドシートへ同期中 ({len(staff_names)}名)...")
    try:
        payload = {
            "action": "sync_staff",
            "staff_list": staff_names
        }
        response = requests.post(GAS_URL, json=payload, timeout=15)
        response.raise_for_status()
        print(f"同期完了: {len(staff_names)}名を登録しました。")
        return True
    except Exception as e:
        print(f"同期エラー: {e}")
        return False
