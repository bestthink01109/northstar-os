"""
models.py
全パーサー・全計算ロジックで共通に利用するデータモデル定義。
パーサーの種類（Excel / OCR / PDF）に関係なく、
すべてのデータは最終的にこのモデルに変換されてからコアロジックに渡される。
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any


@dataclass
class DayRecord:
    """
    1日分の勤怠データ（全パーサー共通出力フォーマット）。
    ExcelParser / OCRParser / PDFParser いずれも最終的にこの形式へ変換する。
    """
    # 基本情報
    row: int = 0                           # 元データ上の行番号（デバッグ用）
    day: int = 0                           # 日（1〜31）
    weekday: str = ''                      # 曜日（月/火/水/木/金/土/日）
    place: str = ''                        # 場所/現場名

    # 時刻情報（float: 8.0 = 8:00, 17.5 = 17:30）
    t_start: Optional[float] = None        # 出勤時刻
    t_end: Optional[float] = None          # 退勤時刻
    t_depart: Optional[float] = None       # 出社時間（Excel J列等）
    t_site_s: Optional[float] = None       # 現場開始時間
    t_site_e: Optional[float] = None       # 現場終了時間
    t_arrive: Optional[float] = None       # 退社時間（Excel P列等）

    # 有給・休暇
    time_off: float = 0.0                  # 時間有給（時間数: 1.0, 3.5, 4.0 等）
    time_off_raw: str = ''                 # 時間有給の生値（"半日"/"1" 等）

    # フラグ
    is_absent: bool = False                # 欠勤フラグ
    is_paid: bool = False                  # 有給（全休）フラグ
    is_training: bool = False              # 研修フラグ
    is_saturday: bool = False              # 土曜日フラグ
    is_sunday: bool = False                # 日曜日フラグ

    # Excel記載値（検証用 — ExcelParserでのみ使用。OCR/PDFでは0.0のまま）
    excel_work: float = 0.0
    excel_ot_out: float = 0.0
    excel_ot_in: float = 0.0
    excel_holiday_w: float = 0.0
    excel_absence: float = 0.0


@dataclass
class CalcResult:
    """
    1日分の計算結果。OvertimeCalculator が DayRecord から算出する。
    """
    work: float = 0.0                      # 勤務時間（所定内）
    ot_in: float = 0.0                     # 法定内残業（延長時間）
    ot_out: float = 0.0                    # 法定外残業
    raw_ot: float = 0.0                    # 週次振り分け前の残業合計
    absence: float = 0.0                   # 欠勤時間（遅刻早退含む）
    actual_work: float = 0.0               # 実働時間（休憩控除後）
    scheduled: float = 0.0                 # その日の所定労働時間
    break_hours: float = 0.0               # 休憩控除時間
    notes: str = ''                        # メモ（デバッグ用）


@dataclass
class MonthlySummary:
    """
    1社員・1ヶ月分の集計結果。MonthlyAggregator が生成する。
    """
    attend_days: int = 0                   # 出勤日数
    total_work: float = 0.0                # 勤務時間合計
    total_ot_in: float = 0.0               # 法定内残業合計（延長時間）
    total_ot_out: float = 0.0              # 法定外残業合計
    total_absence: float = 0.0             # 遅刻早退時間合計
    total_holiday_w: float = 0.0           # 休日出勤時間合計
    paid_days: float = 0.0                 # 有給日数（全休）
    paid_hours: float = 0.0                # 有給時間（半休・時間休の合計）
    absent_days: int = 0                   # 欠勤日数
    scheduled_total: float = 0.0           # 月間所定労働時間合計


@dataclass
class EmployeeMonthData:
    """
    1社員・1ヶ月分の全データを束ねるコンテナ。
    パーサーの出力 → コア計算 → エクスポーターの入力 まで一貫して使用する。
    """
    # 社員情報
    employee_code: int = 0
    employee_name: str = ''
    sheet_name: str = ''                   # 元シート名（Excel用）

    # 期間
    year: int = 0
    month: int = 0

    # 特例フラグ
    is_special: bool = False               # 特例社員フラグ（平野珠美等）

    # データ
    days: List[DayRecord] = field(default_factory=list)
    calc_results: List[tuple] = field(default_factory=list)  # [(DayRecord, CalcResult), ...]
    monthly: Optional[MonthlySummary] = None

    # Excel検証用集計値（ExcelParser経由の場合のみ）
    summary_excel: Dict[str, Any] = field(default_factory=dict)
