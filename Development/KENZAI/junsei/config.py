"""
config.py
株式会社純青 の会社固有設定。
勤務体系は平野工業と同一。
インプット: 手書き出勤簿（自社フォーマット、OCR）
アウトプット: 給与らくだCSV + 出勤簿Excel

追加項目: 外勤手当（外勤欄に◯がある日を集計）
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from base_config import CompanyConfig, SpecialEmployeeConfig


def create_junsei_config() -> CompanyConfig:
    """純青の設定インスタンスを生成して返す"""

    gdrive_base = os.path.expanduser(
        "~/Library/CloudStorage/GoogleDrive-bestthink01109@gmail.com"
        "/マイドライブ"
    )

    return CompanyConfig(
        # ── 基本情報 ──
        company_id='junsei',
        company_name='純青',

        # ── インプット ──
        input_type='ocr',                   # 手書き出勤簿（OCR）
        input_dir=os.path.join(gdrive_base, '純青'),

        # ── アウトプット ──
        output_format='kyuyo_rakuda',        # 給与らくだ
        output_dir=os.path.join(gdrive_base, 'Development', '純青'),
        output_encoding='cp932',

        # ── 勤務体系（平野工業と同一） ──
        weekday_scheduled_hours=7.0,
        saturday_scheduled_hours=5.0,
        sunday_is_workday=False,
        legal_daily_limit=8.0,
        weekly_scheduled_hours=40.0,

        # ── 休憩時間帯（平野工業と同一） ──
        break_periods_weekday=[
            (10.0, 10.5),
            (12.0, 13.0),
            (14.0, 14.5),
        ],
        break_periods_saturday=[
            (10.0, 10.5),
            (12.0, 13.0),
            (14.0, 14.5),
        ],

        # ── 有給 ──
        half_day_hours=3.5,

        # ── 特例社員（現時点ではなし） ──
        special_employees={},

        # ── 会社固有の休日設定 ──
        new_year_holidays=[1, 2, 3],

        # ── WeeklyAllocator用 ──
        sat_scheduled_end=15.0,
        sat_overtime_max=18.0,
    )
