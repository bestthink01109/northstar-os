"""
config.py
平野工業の会社固有設定。
現行 payroll_engine.py にハードコードされていた全パラメータをここに集約。
"""

import os
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from base_config import CompanyConfig, SpecialEmployeeConfig


def create_hirano_config() -> CompanyConfig:
    """平野工業の設定インスタンスを生成して返す"""

    # Google Drive上のパス
    gdrive_base = os.path.expanduser(
        "~/Library/CloudStorage/GoogleDrive-bestthink01109@gmail.com"
        "/マイドライブ"
    )

    return CompanyConfig(
        # ── 基本情報 ──
        company_id='hirano',
        company_name='平野工業',

        # ── インプット ──
        input_type='excel',
        input_dir=os.path.join(gdrive_base, '🏢【KENZAI】給与計算', '📥 01_ここに入力データをポン（生データ用）', '平野工業'),

        # ── アウトプット ──
        output_format='kyuyo_rakuda',
        output_dir=os.path.join(gdrive_base, '🏢【KENZAI】給与計算', '📤 02_ここから完成品を取る（出力用）', '平野工業'),
        output_encoding='cp932',

        # ── 勤務体系（一般社員） ──
        weekday_scheduled_hours=7.0,       # 平日：所定7時間
        saturday_scheduled_hours=5.0,      # 土曜：所定5時間
        sunday_is_workday=False,           # 日曜は完全休日
        legal_daily_limit=8.0,             # 法定上限8時間/日
        weekly_scheduled_hours=40.0,       # 週所定40時間（7×5 + 5×1 = 40）

        # ── 休憩時間帯（一般社員） ──
        # 平日・土曜ともに同じ3区間（合計2.0時間）
        break_periods_weekday=[
            (10.0, 10.5),   # 午前休憩 10:00〜10:30（0.5h）
            (12.0, 13.0),   # 昼休憩   12:00〜13:00（1.0h）
            (14.0, 14.5),   # 午後休憩 14:00〜14:30（0.5h）
        ],
        break_periods_saturday=[
            (10.0, 10.5),
            (12.0, 13.0),
            (14.0, 14.5),
        ],

        # ── 有給 ──
        half_day_hours=3.5,                # 半日休：3.5時間（一般社員）

        # ── 特例社員 ──
        special_employees={
            '平野珠美': SpecialEmployeeConfig(
                weekday_scheduled_hours=8.0,     # 平日：所定8時間
                saturday_scheduled_hours=5.0,    # 土曜：一般と同じ5時間
                break_periods_weekday=[
                    (12.0, 13.0),                # 平野珠美氏は昼休憩1時間のみ
                ],
                break_periods_saturday=[
                    (10.0, 10.5),
                    (12.0, 13.0),
                    (14.0, 14.5),
                ],
                half_day_hours=4.0,              # 半日休：4.0時間
                has_daily_ot_in=False,            # 所定=法定8h のため日次の法定内残業なし
            ),
        },

        # ── 会社固有の休日設定 ──
        new_year_holidays=[1, 2, 3],       # 1月1〜3日は正月休み

        # ── WeeklyAllocator用 ──
        sat_scheduled_end=15.0,            # 土曜の所定終了: 15:00
        sat_overtime_max=18.0,             # 土曜の法定内残業上限: 18:00
    )
