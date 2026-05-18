"""
base_config.py
CompanyConfig の定義。全クライアント共通の設定モデル。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# 定数
# ---------------------------------------------------------------------------
LABOR_SYSTEM_STANDARD = "standard"
LABOR_SYSTEM_MONTHLY_VARIABLE = "monthly_variable"
LABOR_SYSTEM_ANNUAL_VARIABLE = "annual_variable"

VALID_LABOR_SYSTEMS = {
    LABOR_SYSTEM_STANDARD,
    LABOR_SYSTEM_MONTHLY_VARIABLE,
    LABOR_SYSTEM_ANNUAL_VARIABLE,
}

# 法令上限値
LAW_WEEKLY_MAX_HOURS = 40.0          # 通常労働制 週法定上限
LAW_VARIABLE_WEEKLY_MAX_HOURS = 52.0  # 変形制 週上限（月単位）
LAW_DAILY_MAX_HOURS = 10.0            # 変形制 日上限
LAW_MONTHLY_MAX_HOURS_PER_YEAR = 3800.0  # 年単位変形 参考値（実装は別チケット）


# ---------------------------------------------------------------------------
# CompanyConfig
# ---------------------------------------------------------------------------
@dataclass
class CompanyConfig:
    """
    クライアント1社分の勤務条件を保持するデータクラス。

    Attributes
    ----------
    company_name : str
        会社名（識別用）
    labor_system : str
        労働時間制の種類。
        "standard" | "monthly_variable" | "annual_variable"
    weekday_hours : float
        平日所定労働時間（時間）。例: 7.0, 8.0
    saturday_hours : float
        土曜所定労働時間（時間）。なしの場合は 0.0。
    sunday_work : bool
        日曜労働ありなら True。
    weekly_legal_limit : float
        週法定労働時間上限（通常: 40.0）。
    half_day_threshold : float
        半日の基準時間（例: 3.5, 4.0）。
    monthly_scheduled_hours : Optional[float]
        月単位変形労働制の月所定労働時間。通常制の場合は None。
    daily_max_hours : float
        1日の上限時間（変形制: 10h 以内）。
    weekly_max_hours : float
        週の上限時間（通常: 40、変形月単位: 52 まで）。
    spreadsheet_id : Optional[str]
        設定を読み込んだスプレッドシート ID（SS 読み込み時のみ設定）。
    """

    company_name: str = "unknown"
    labor_system: str = LABOR_SYSTEM_STANDARD

    # 所定労働時間
    weekday_hours: float = 8.0
    saturday_hours: float = 0.0
    sunday_work: bool = False

    # 法的上限
    weekly_legal_limit: float = LAW_WEEKLY_MAX_HOURS

    # 半日基準
    half_day_threshold: float = 4.0

    # 変形労働時間制用
    monthly_scheduled_hours: Optional[float] = None
    daily_max_hours: float = LAW_DAILY_MAX_HOURS
    weekly_max_hours: float = LAW_WEEKLY_MAX_HOURS

    # メタ情報
    spreadsheet_id: Optional[str] = None

    # ------------------------------------------------------------------
    # バリデーション
    # ------------------------------------------------------------------
    def validate(self) -> list[str]:
        """
        設定値が法令・論理的に正しいか検証する。

        Returns
        -------
        list[str]
            エラーメッセージのリスト。空リストなら問題なし。
        """
        errors: list[str] = []

        # labor_system
        if self.labor_system not in VALID_LABOR_SYSTEMS:
            errors.append(
                f"labor_system '{self.labor_system}' は無効です。"
                f"有効値: {VALID_LABOR_SYSTEMS}"
            )

        # weekday_hours
        if not (0.0 < self.weekday_hours <= LAW_DAILY_MAX_HOURS):
            errors.append(
                f"平日所定労働時間 {self.weekday_hours}h は 0〜{LAW_DAILY_MAX_HOURS}h の範囲外です。"
            )

        # saturday_hours
        if not (0.0 <= self.saturday_hours <= LAW_DAILY_MAX_HOURS):
            errors.append(
                f"土曜所定労働時間 {self.saturday_hours}h は 0〜{LAW_DAILY_MAX_HOURS}h の範囲外です。"
            )

        # weekly_legal_limit
        if self.labor_system == LABOR_SYSTEM_STANDARD:
            if self.weekly_legal_limit > LAW_WEEKLY_MAX_HOURS:
                errors.append(
                    f"週法定労働時間上限 {self.weekly_legal_limit}h が法定上限 "
                    f"{LAW_WEEKLY_MAX_HOURS}h を超えています（通常労働制）。"
                )
        elif self.labor_system == LABOR_SYSTEM_MONTHLY_VARIABLE:
            if self.weekly_max_hours > LAW_VARIABLE_WEEKLY_MAX_HOURS:
                errors.append(
                    f"週上限時間 {self.weekly_max_hours}h が月単位変形制の法定上限 "
                    f"{LAW_VARIABLE_WEEKLY_MAX_HOURS}h を超えています。"
                )

        # daily_max_hours
        if self.daily_max_hours > LAW_DAILY_MAX_HOURS:
            errors.append(
                f"1日上限時間 {self.daily_max_hours}h が法定上限 {LAW_DAILY_MAX_HOURS}h を超えています。"
            )

        # half_day_threshold
        if not (0.0 < self.half_day_threshold < self.weekday_hours):
            errors.append(
                f"半日基準時間 {self.half_day_threshold}h は 0h〜平日所定時間 "
                f"{self.weekday_hours}h の範囲内でなければなりません。"
            )

        # monthly_scheduled_hours（月単位変形制の場合は必須）
        if self.labor_system == LABOR_SYSTEM_MONTHLY_VARIABLE:
            if self.monthly_scheduled_hours is None:
                errors.append(
                    "月単位変形労働制を選択した場合、"
                    "monthly_scheduled_hours（月所定労働時間）を設定してください。"
                )
            elif self.monthly_scheduled_hours <= 0:
                errors.append(
                    f"月所定労働時間 {self.monthly_scheduled_hours}h は正の値でなければなりません。"
                )

        return errors

    def validate_or_raise(self) -> None:
        """
        バリデーションエラーがあれば ValueError を送出する。
        """
        errors = self.validate()
        if errors:
            msg = "CompanyConfig バリデーションエラー:\n" + "\n".join(
                f"  - {e}" for e in errors
            )
            raise ValueError(msg)

    # ------------------------------------------------------------------
    # ファクトリ
    # ------------------------------------------------------------------
    @classmethod
    def for_construction(cls, company_name: str = "建設業") -> "CompanyConfig":
        """建設業デフォルト（7h×月〜金、5h×土）を返す。"""
        return cls(
            company_name=company_name,
            labor_system=LABOR_SYSTEM_STANDARD,
            weekday_hours=7.0,
            saturday_hours=5.0,
            sunday_work=False,
            weekly_legal_limit=40.0,
            half_day_threshold=3.5,
            daily_max_hours=10.0,
            weekly_max_hours=40.0,
        )

    @classmethod
    def for_standard_industry(cls, company_name: str = "一般企業") -> "CompanyConfig":
        """一般企業デフォルト（8h×月〜金）を返す。"""
        return cls(
            company_name=company_name,
            labor_system=LABOR_SYSTEM_STANDARD,
            weekday_hours=8.0,
            saturday_hours=0.0,
            sunday_work=False,
            weekly_legal_limit=40.0,
            half_day_threshold=4.0,
            daily_max_hours=10.0,
            weekly_max_hours=40.0,
        )

    # ------------------------------------------------------------------
    # 表示
    # ------------------------------------------------------------------
    def summary(self) -> str:
        """設定内容のサマリ文字列を返す。"""
        lines = [
            f"会社名          : {self.company_name}",
            f"労働時間制      : {self.labor_system}",
            f"平日所定時間    : {self.weekday_hours}h",
            f"土曜所定時間    : {self.saturday_hours}h",
            f"日曜労働        : {'あり' if self.sunday_work else 'なし'}",
            f"週法定上限      : {self.weekly_legal_limit}h",
            f"週上限          : {self.weekly_max_hours}h",
            f"日上限          : {self.daily_max_hours}h",
            f"半日基準        : {self.half_day_threshold}h",
        ]
        if self.monthly_scheduled_hours is not None:
            lines.append(f"月所定時間      : {self.monthly_scheduled_hours}h")
        if self.spreadsheet_id:
            lines.append(f"スプレッドシートID: {self.spreadsheet_id}")
        return "\n".join(lines)