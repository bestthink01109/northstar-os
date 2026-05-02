"""
config.py
株式会社福岡プラント機工 の会社固有設定。
勤務体系は平野工業と同一。
インプット: スキャンPDF（日報）
アウトプット: 税理士用汎用CSV + 出勤簿Excel
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from base_config import CompanyConfig, SpecialEmployeeConfig


def create_fukuoka_plant_config() -> CompanyConfig:
    """福岡プラント機工の設定インスタンスを生成して返す"""

    gdrive_base = os.path.expanduser(
        "~/Library/CloudStorage/GoogleDrive-bestthink01109@gmail.com"
        "/マイドライブ"
    )

    return CompanyConfig(
        # ── 基本情報 ──
        company_id='fukuoka_plant',
        company_name='福岡プラント機工',

        # ── インプット ──
        input_type='pdf',                   # スキャンPDF（日報）
        input_dir=os.path.join(gdrive_base, '🏢【KENZAI】給与計算', '📥 01_ここに入力データをポン（生データ用）', '福岡プラント機工'),

        # ── アウトプット ──
        output_format='kyuyo_rakuda',         # 税理士使用ソフト用
        output_dir=os.path.join(gdrive_base, '🏢【KENZAI】給与計算', '📤 02_ここから完成品を取る（出力用）', '福岡プラント機工'),
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
