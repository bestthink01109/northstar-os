#!/usr/bin/env python3
"""
main.py
給与計算エンジン 統一CLI エントリーポイント。

使用方法:
    # 平野工業（Excel入力 → 給与らくだCSV + 出勤簿Excel出力）
    python main.py --company hirano --month 202604

    # 平野工業・自動検出（最新の出勤簿.xlsxを自動検出）
    python main.py --company hirano --month 202604 --auto

    # 全社一括処理
    python main.py --all --month 202604
"""

import argparse
import os
import sys
import glob
from datetime import datetime

# パッケージとしてもスクリプトとしても動作するようパスを追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hirano.config import create_hirano_config
from hirano.employee_master import EMPLOYEE_MASTER as HIRANO_MASTER
from hirano.employee_master import get_employee_code as hirano_get_code
from hirano.corrections import apply_corrections as hirano_apply_corrections
from fukuoka_plant.config import create_fukuoka_plant_config
from fukuoka_plant.employee_master import EMPLOYEE_MASTER as FUKUOKA_MASTER
from fukuoka_plant.employee_master import get_employee_code as fukuoka_get_code
from junsei.config import create_junsei_config
from junsei.employee_master import EMPLOYEE_MASTER as JUNSEI_MASTER
from junsei.employee_master import get_employee_code as junsei_get_code
from parsers.excel_parser import ExcelParser
from core.overtime_calculator import OvertimeCalculator
from core.weekly_allocator import WeeklyAllocator
from core.monthly_aggregator import MonthlyAggregator
from core.validation import ValidationReport
from exporters.rakuda_csv_exporter import RakudaCSVExporter
from exporters.generic_csv_exporter import GenericCSVExporter
from exporters.attendance_sheet import AttendanceSheetExporter
from exporters.diff_report import DiffReportExporter, build_diff_data
from exporters.excel_clone_exporter import ExcelCloneExporter
from parsers.fix_reader import read_fixes


# ── 会社レジストリ ──
COMPANY_REGISTRY = {
    'hirano': {
        'create_config': create_hirano_config,
        'employee_master': HIRANO_MASTER,
        'get_employee_code': hirano_get_code,
        'apply_corrections': hirano_apply_corrections,
    },
    'fukuoka_plant': {
        'create_config': create_fukuoka_plant_config,
        'employee_master': FUKUOKA_MASTER,
        'get_employee_code': fukuoka_get_code,
        'apply_corrections': None,
    },
    'junsei': {
        'create_config': create_junsei_config,
        'employee_master': JUNSEI_MASTER,
        'get_employee_code': junsei_get_code,
        'apply_corrections': None,
    },
}


def find_excel_file(config, year, month):
    """出勤簿Excelファイルを自動検出する。"""
    patterns = [
        os.path.join(config.input_dir, f"*{year}{month:02d}*.xlsx"),
        os.path.join(config.input_dir, f"*{year}年{month}月*.xlsx"),
        os.path.join(config.input_dir, f"出勤簿*{month}月*.xlsx"),
        os.path.join(config.input_dir, f"出勤簿*.xlsx"),
    ]
    for pat in patterns:
        files = glob.glob(pat)
        # 一時ファイル（~$で始まるもの）を除外
        files = [f for f in files if not os.path.basename(f).startswith('~$')]
        if files:
            # 複数ヒットした場合は更新日時が最新のものを使用
            return max(files, key=os.path.getmtime)
    return None


def process_company(company_id, year, month, excel_path=None, verbose=True, suffix=''):
    """
    1社分の給与計算処理を実行する。

    Args:
        company_id: 会社ID（'hirano' 等）
        year, month: 対象年月
        excel_path: Excelファイルパス（Noneの場合は自動検出）
        verbose: 詳細出力
        suffix: 出力ファイル名に付加するサフィックス（例: '【修正分】'）
        fix_path: 修正入力済み差異レポートのパス
    """
    reg = COMPANY_REGISTRY.get(company_id)
    if reg is None:
        print(f"[エラー] 未登録の会社ID: {company_id}")
        print(f"[利用可能] {list(COMPANY_REGISTRY.keys())}")
        return False

    config = reg['create_config']()
    employee_master = reg['employee_master']
    get_code_fn = reg['get_employee_code']
    apply_corrections_fn = reg.get('apply_corrections')  # 補正関数（会社ごとに異なる）

    print(f"{'='*60}")
    print(f"  {config.company_name} 給与計算 ({year}年{month}月)")
    print(f"{'='*60}")

    # ── 1. 入力ファイルの特定とパーサー生成 ──
    input_path = excel_path  # CLIの--fileで指定された場合
    if config.input_type == 'excel':
        if input_path is None:
            input_path = find_excel_file(config, year, month)
        if input_path is None or not os.path.exists(input_path):
            print(f"[エラー] 出勤簿Excelが見つかりません: {config.input_dir}")
            return False
        print(f"[入力] {os.path.basename(input_path)}")
        parser = ExcelParser(config)
    elif config.input_type == 'ocr':
        if input_path is None:
            input_path = config.input_dir
        if not os.path.exists(input_path):
            print(f"[エラー] 入力ディレクトリが見つかりません: {input_path}")
            return False
        print(f"[入力] OCR入力: {input_path}")
        try:
            from parsers.ocr_parser import OCRParser
            parser = OCRParser(config)
        except ImportError as e:
            print(f"[エラー] OCRパーサーの読み込みに失敗: {e}")
            return False
    elif config.input_type == 'pdf':
        if input_path is None:
            input_path = config.input_dir
        if not os.path.exists(input_path):
            print(f"[エラー] 入力ディレクトリが見つかりません: {input_path}")
            return False
        print(f"[入力] PDF入力: {input_path}")
        try:
            from parsers.pdf_parser import PDFParser
            parser = PDFParser(config)
        except ImportError as e:
            print(f"[エラー] PDFパーサーの読み込みに失敗: {e}")
            return False
    else:
        print(f"[エラー] 未対応の入力タイプ: {config.input_type}")
        return False

    # ── 2. パーサーでデータ読み取り ──
    all_sheets = parser.parse(input_path, employee_master)
    if not all_sheets:
        print("[エラー] データが取得できませんでした")
        return False
    print(f"[解析] {len(all_sheets)}名分のデータを検出")

    # ── 2b. 入力補正値の適用（corrections.py の CORRECTIONS に定義された値を day_rec に注入） ──
    if apply_corrections_fn is not None:
        apply_corrections_fn(all_sheets, year, month)

    # ── 2c. 差異レポートからの手動補正値の適用 ──
    if fix_path and os.path.exists(fix_path):
        print(f"[手動補正] 差異レポートから修正値を読み込みます: {os.path.basename(fix_path)}")
        try:
            manual_corrections = read_fixes(fix_path)
            for sheet_data in all_sheets:
                name = sheet_data['sheet_name']
                if name not in manual_corrections:
                    continue
                day_corrections = manual_corrections[name]
                for day_rec in sheet_data['days']:
                    d = day_rec['day']
                    if d not in day_corrections:
                        continue
                    for field, new_val in day_corrections[d].items():
                        old_val = day_rec.get(field)
                        day_rec[field] = new_val
                        print(f"  [手動補正適用] {name} Day{d} {field}: {old_val}→{new_val}")
        except Exception as e:
            print(f"[エラー] 修正値の読み込みに失敗しました: {e}")
            return False

    # ── 3. 各社員をコアエンジンで計算 ──
    calculator = OvertimeCalculator(config)
    allocator = WeeklyAllocator(config)
    aggregator = MonthlyAggregator()
    validator = ValidationReport()

    csv_records = []
    attendance_data = []
    all_issues = []
    all_diff_data = []
    clone_data = []

    for sheet_data in all_sheets:
        sheet_name = sheet_data['sheet_name']
        emp_code = get_code_fn(sheet_name)
        if emp_code is None:
            if verbose:
                print(f"  [スキップ] {sheet_name}: 社員マスター未登録")
            continue

        emp_info = employee_master[sheet_name]
        emp_full_name = emp_info['name']
        days = sheet_data['days']
        yr = sheet_data['year']
        mo = sheet_data['month']

        # パーサーが年月を取得できなかった場合（openpyxl で保存後など数式が未評価の状態）
        # CLI 引数の year・month をフォールバックとして使用する
        if yr is None or mo is None:
            yr = year
            mo = month
        # (a) 日次計算
        calc_results = []
        for day_rec in days:
            calc = calculator.calculate_day_dict(day_rec, sheet_name) if hasattr(calculator, 'calculate_day_dict') else self_calc_day_dict(calculator, day_rec, sheet_name)
            calc_results.append((day_rec, calc))

        # (b) 週次振り分け
        calc_results = allocator.allocate(days, calc_results, yr, mo)

        # (c) 月次集計
        monthly = aggregator.aggregate(sheet_data, calc_results)

        # (d) 検証（Excel入力の場合のみ差異検証を行う）
        if config.input_type == 'excel':
            issues = validator.validate(sheet_name, days, calc_results, monthly, sheet_data.get('summary_excel', {}))
        else:
            issues = []

        if issues:
            all_issues.append((sheet_name, issues))

        # (e) エクスポート用データ蓄積
        csv_records.append((emp_code, emp_full_name, monthly))
        attendance_data.append({
            'employee_name': emp_full_name,
            'employee_code': emp_code,
            'calc_results': calc_results,
            'monthly': monthly,
            'is_special': sheet_data.get('is_special', False),
        })

        # (f) 差異レポート用データ蓄積（Excel入力の場合）
        if config.input_type == 'excel':
            diff = build_diff_data(
                sheet_name, emp_code, emp_full_name,
                days, calc_results, monthly,
                sheet_data.get('summary_excel', {})
            )
            all_diff_data.append(diff)

        # (g) 入力フォーマット出力用データ蓄積
        clone_data.append({
            'sheet_name': sheet_name,
            'calc_results': calc_results,
            'monthly': monthly,
        })

        if verbose:
            status = 'OK' if not issues else f'差異{len(issues)}件'
            print(f"  [{status}] {sheet_name} (コード:{emp_code}) "
                  f"勤務:{monthly['total_work']}h 所内:{monthly['total_ot_in']}h "
                  f"法外:{monthly['total_ot_out']}h 遅早:{monthly['total_absence']}h")

    # ── 4. 差異レポート ──
    if all_issues:
        print(f"\n{'='*60}")
        print(f"  差異レポート（{len(all_issues)}名に差異あり）")
        print(f"{'='*60}")
        for sheet_name, issues in all_issues:
            print(f"\n[{sheet_name}]")
            for issue in issues:
                print(issue)

    # ── 4b. 差異レポートExcel出力（Excel入力の場合） ──
    os.makedirs(config.output_dir, exist_ok=True)
    if config.input_type == 'excel' and all_diff_data:
        diff_exporter = DiffReportExporter()
        diff_stem = f"{suffix}差異レポート_{config.company_name}_{yr}{mo:02d}.xlsx"
        diff_path = os.path.join(config.output_dir, diff_stem)
        diff_exporter.export(all_diff_data, diff_path, config.company_name, yr, mo)

    # ── 5. CSV出力 ──
    if config.output_format == 'kyuyo_rakuda':
        exporter = RakudaCSVExporter(encoding=config.output_encoding)
        csv_stem = f"{suffix}kintai6_{yr}{mo:02d}.csv"
        csv_path = os.path.join(config.output_dir, csv_stem)
        exporter.export(csv_records, csv_path, yr, mo)
    elif config.output_format == 'generic_csv':
        exporter = GenericCSVExporter(encoding=config.output_encoding)
        csv_stem = f"{suffix}勤怠_{config.company_name}_{yr}{mo:02d}.csv"
        csv_path = os.path.join(config.output_dir, csv_stem)
        exporter.export(csv_records, csv_path, yr, mo)
    else:
        print(f"[注意] 出力形式 '{config.output_format}' は未実装")

    # ── 6. 出勤簿Excel出力 ──
    if config.input_type == 'excel' and input_path:
        # 入力Excelと同じフォーマットで出力（書式・レイアウト完全保持）
        clone_exporter = ExcelCloneExporter()
        base_name = os.path.basename(input_path)
        # サフィックスは拡張子の前に挿入
        name_stem, name_ext = os.path.splitext(base_name)
        clone_stem = f"{suffix}【計算済】{name_stem}{name_ext}"
        clone_path = os.path.join(config.output_dir, clone_stem)
        clone_exporter.export(input_path, clone_path, clone_data)
    else:
        # OCR/PDF入力の場合は独自フォーマットの出勤簿を生成
        sheet_exporter = AttendanceSheetExporter()
        attendance_path = os.path.join(
            config.output_dir,
            f"{suffix}出勤簿_{config.company_name}_{yr}{mo:02d}.xlsx"
        )
        sheet_exporter.export(attendance_data, attendance_path, config.company_name, yr, mo)

    print(f"\n[完了] {config.company_name} {yr}年{mo}月 処理完了")
    return True


def self_calc_day_dict(calculator, day_rec, sheet_name):
    """
    OvertimeCalculator の calculate_day を dict 入出力に対応させるラッパー。
    day_rec が dict の場合に DayRecord 相当のアクセスを提供する。
    """
    from core.models import DayRecord, CalcResult

    # dict → DayRecord 変換
    if isinstance(day_rec, dict):
        dr = DayRecord(
            row=day_rec.get('row', 0),
            day=day_rec.get('day', 0),
            weekday=day_rec.get('weekday', ''),
            place=day_rec.get('place', ''),
            t_start=day_rec.get('t_start'),
            t_end=day_rec.get('t_end'),
            t_depart=day_rec.get('t_depart'),
            t_site_s=day_rec.get('t_site_s'),
            t_site_e=day_rec.get('t_site_e'),
            t_arrive=day_rec.get('t_arrive'),
            time_off=day_rec.get('time_off', 0.0),
            time_off_raw=day_rec.get('time_off_raw', ''),
            is_absent=day_rec.get('is_absent', False),
            is_paid=day_rec.get('is_paid', False),
            is_training=day_rec.get('is_training', False),
            is_saturday=day_rec.get('is_saturday', False),
            is_sunday=day_rec.get('is_sunday', False),
            excel_work=day_rec.get('excel_work', 0.0),
            excel_ot_out=day_rec.get('excel_ot_out', 0.0),
            excel_ot_in=day_rec.get('excel_ot_in', 0.0),
            excel_holiday_w=day_rec.get('excel_holiday_w', 0.0),
            excel_absence=day_rec.get('excel_absence', 0.0),
        )
    else:
        dr = day_rec

    result = calculator.calculate_day(dr, sheet_name)

    # CalcResult → dict 変換（後方互換）
    return {
        'work': result.work,
        'ot_in': result.ot_in,
        'ot_out': result.ot_out,
        'raw_ot': result.raw_ot,
        'absence': result.absence,
        'actual_work': result.actual_work,
        'scheduled': result.scheduled,
        'break_hours': result.break_hours,
        'notes': result.notes,
    }


def main():
    parser = argparse.ArgumentParser(
        description='給与計算エンジン（マルチテナント対応）',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
    # 平野工業
    python main.py --company hirano --month 202604

    # 平野工業・ファイル直接指定
    python main.py --company hirano --month 202604 --file /path/to/出勤簿.xlsx

    # 全社一括処理
    python main.py --all --month 202604
        """
    )
    parser.add_argument('--company', '-c', help='会社ID（hirano, fukuoka_plant, junsei）')
    parser.add_argument('--month', '-m', required=True, help='対象年月（YYYYMM形式、例: 202604）')
    parser.add_argument('--file', '-f', help='入力ファイルパス（省略時は自動検出）')
    parser.add_argument('--all', '-a', action='store_true', help='全社一括処理')
    parser.add_argument('--quiet', '-q', action='store_true', help='簡潔な出力')
    parser.add_argument(
        '--suffix', '-s', default='',
        help='出力ファイル名に付加するサフィックス（例: --suffix 【修正分】）'
    )
    parser.add_argument(
        '--fix', help='差異レポートのパスを指定して手動修正を適用（出力ファイルに自動で【修正分】が付加されます）'
    )

    args = parser.parse_args()

    # 年月のパース
    try:
        year = int(args.month[:4])
        month = int(args.month[4:6])
    except (ValueError, IndexError):
        print(f"[エラー] 年月の形式が不正です: {args.month} (YYYYMM形式で指定してください)")
        sys.exit(1)

    suffix = args.suffix  # 例: '【修正分】'
    if args.fix:
        suffix = '【修正分】'
        
    if suffix:
        print(f"[オプション] 出力ファイルにサフィックス追加: {suffix}")

    if args.all:
        success = True
        for cid in COMPANY_REGISTRY:
            ok = process_company(cid, year, month, verbose=not args.quiet, suffix=suffix, fix_path=args.fix)
            if not ok:
                success = False
        sys.exit(0 if success else 1)
    elif args.company:
        ok = process_company(
            args.company, year, month,
            excel_path=args.file, verbose=not args.quiet, suffix=suffix, fix_path=args.fix
        )
        sys.exit(0 if ok else 1)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
