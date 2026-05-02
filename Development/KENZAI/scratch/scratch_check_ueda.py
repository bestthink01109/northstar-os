"""
上田力也氏 2026年4月 - allocate() 経由での週次結果検証スクリプト。
修正後の WeeklyAllocator が正しく動作するかを確認する。
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hirano.config import create_hirano_config
from parsers.excel_parser import ExcelParser
from core.overtime_calculator import OvertimeCalculator
from core.weekly_allocator import WeeklyAllocator
from hirano.employee_master import EMPLOYEE_MASTER
from main import self_calc_day_dict

EXCEL_PATH = (
    '/Users/fuminariaksse/Library/CloudStorage/'
    'GoogleDrive-bestthink01109@gmail.com/マイドライブ/'
    '🏢【KENZAI】給与計算/📥 01_ここに入力データをポン（生データ用）/'
    '平野工業/【出勤簿】202604.xlsx'
)

cfg = create_hirano_config()
parser = ExcelParser(cfg)
sheets = parser.parse(EXCEL_PATH, EMPLOYEE_MASTER)

for sh in sheets:
    name = sh.get('sheet_name', '')
    if '上田力也' not in name:
        continue

    print('=' * 60)
    print(f'  社員: {name}  {sh["year"]}年{sh["month"]}月')
    print('=' * 60)

    calc_engine = OvertimeCalculator(cfg)
    alloc = WeeklyAllocator(cfg)

    # 日次計算
    daily = []
    for d in sh['days']:
        res = self_calc_day_dict(calc_engine, d, name)
        daily.append((d, res))

    # 週次振り分け（修正後のallocate()を呼ぶ）
    allocated = alloc.allocate(sh['days'], daily, sh['year'], sh['month'])

    # 月次集計（手動）
    total_work   = 0.0
    total_ot_in  = 0.0
    total_ot_out = 0.0
    total_absence = 0.0

    print('\n── 振り分け後の日次結果 ──')
    for day_rec, calc in allocated:
        day_num = day_rec['day'] if isinstance(day_rec, dict) else day_rec.day
        weekday = day_rec['weekday'] if isinstance(day_rec, dict) else day_rec.weekday
        notes   = calc['notes'] if isinstance(calc, dict) else calc.notes
        work    = calc['work'] if isinstance(calc, dict) else calc.work
        ot_in   = calc['ot_in'] if isinstance(calc, dict) else calc.ot_in
        ot_out  = calc['ot_out'] if isinstance(calc, dict) else calc.ot_out
        absence = calc['absence'] if isinstance(calc, dict) else calc.absence

        if notes not in ('日曜休',):
            print(
                f'  Day{day_num:2d}({weekday}): '
                f'notes={str(notes):<20s} '
                f'work={work:.1f}h ot_in={ot_in:.1f}h ot_out={ot_out:.1f}h absence={absence:.1f}h'
            )

        total_work    += work
        total_ot_in   += ot_in
        total_ot_out  += ot_out
        total_absence += absence

    print('\n── 月次合計 ──')
    print(f'  実働時間合計  : {total_work:.1f}h')
    print(f'  所内残業（法定内）: {total_ot_in:.1f}h')
    print(f'  法定外残業    : {total_ot_out:.1f}h')
    print(f'  欠勤時間      : {total_absence:.1f}h')

    # Excel値との比較（出勤簿サマリー）
    if 'summary_excel' in sh:
        s = sh['summary_excel']
        print('\n── Excelサマリー値（比較用） ──')
        for k, v in s.items():
            print(f'  {k}: {v}')
