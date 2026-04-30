"""
base_config.py
会社設定の基底クラス。各社はこのクラスを継承して固有のパラメータを定義する。
コアロジック（OvertimeCalculator, WeeklyAllocator等）はこの設定を参照して動作する。
"""

from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Any, Optional


@dataclass
class SpecialEmployeeConfig:
    """特例社員の設定（例：平野珠美氏のような所定8h社員）"""
    weekday_scheduled_hours: float = 8.0
    saturday_scheduled_hours: float = 5.0
    break_periods_weekday: List[Tuple[float, float]] = field(default_factory=list)
    break_periods_saturday: List[Tuple[float, float]] = field(default_factory=list)
    half_day_hours: float = 4.0
    has_daily_ot_in: bool = False   # 日次で法定内残業が発生するか


@dataclass
class CompanyConfig:
    """
    会社ごとの勤務体系・設定の基底クラス。
    各社は companies/<company_name>/config.py でこのクラスを継承し、
    固有のパラメータを設定する。
    """
    # ── 基本情報 ──
    company_id: str = ''                     # 内部識別子（フォルダ名等）
    company_name: str = ''                   # 表示用会社名

    # ── インプット ──
    input_type: str = 'excel'                # "excel" / "ocr" / "pdf"
    input_dir: str = ''                      # 入力ファイルのディレクトリ

    # ── アウトプット ──
    output_format: str = 'kyuyo_rakuda'      # "kyuyo_rakuda" / "generic_csv"
    output_dir: str = ''                     # 出力先ディレクトリ
    output_encoding: str = 'cp932'           # CSV出力文字コード

    # ── 勤務体系（一般社員） ──
    weekday_scheduled_hours: float = 7.0     # 平日の所定労働時間
    saturday_scheduled_hours: float = 5.0    # 土曜の所定労働時間
    sunday_is_workday: bool = False          # 日曜を出勤日とするか
    legal_daily_limit: float = 8.0           # 法定労働時間上限（日）
    weekly_scheduled_hours: float = 40.0     # 週所定労働時間

    # ── 休憩時間帯（一般社員） ──
    break_periods_weekday: List[Tuple[float, float]] = field(
        default_factory=lambda: [(10.0, 10.5), (12.0, 13.0), (14.0, 14.5)]
    )
    break_periods_saturday: List[Tuple[float, float]] = field(
        default_factory=lambda: [(10.0, 10.5), (12.0, 13.0), (14.0, 14.5)]
    )

    # ── 有給 ──
    half_day_hours: float = 3.5              # 半日休の時間数（一般社員）

    # ── 特例社員（名前 → 特例設定） ──
    special_employees: Dict[str, SpecialEmployeeConfig] = field(default_factory=dict)

    # ── 会社固有の休日設定 ──
    new_year_holidays: List[int] = field(default_factory=lambda: [1, 2, 3])  # 正月休み（日付リスト、1月のみ適用）
    company_holidays_weekday: List[str] = field(default_factory=list)        # 会社定休日の曜日（例: ["水", "日"]）

    # ── WeeklyAllocator用 ──
    sat_scheduled_end: float = 15.0          # 土曜の所定終了時刻
    sat_overtime_max: float = 18.0           # 土曜の法定内残業上限時刻

    def is_special_employee(self, name: str) -> bool:
        """特例社員かどうかを判定する"""
        return name in self.special_employees

    def get_special_config(self, name: str) -> Optional[SpecialEmployeeConfig]:
        """特例社員の設定を取得する（該当しない場合はNone）"""
        return self.special_employees.get(name)

    def get_scheduled_hours(self, name: str, is_saturday: bool) -> float:
        """指定社員の所定労働時間を返す"""
        special = self.get_special_config(name)
        if special:
            return special.saturday_scheduled_hours if is_saturday else special.weekday_scheduled_hours
        return self.saturday_scheduled_hours if is_saturday else self.weekday_scheduled_hours

    def get_break_periods(self, name: str, is_saturday: bool) -> List[Tuple[float, float]]:
        """指定社員の休憩時間帯を返す"""
        special = self.get_special_config(name)
        if special:
            if is_saturday and special.break_periods_saturday:
                return special.break_periods_saturday
            return special.break_periods_weekday
        return self.break_periods_saturday if is_saturday else self.break_periods_weekday

    def get_half_day_hours(self, name: str) -> float:
        """指定社員の半日休時間数を返す"""
        special = self.get_special_config(name)
        if special:
            return special.half_day_hours
        return self.half_day_hours
