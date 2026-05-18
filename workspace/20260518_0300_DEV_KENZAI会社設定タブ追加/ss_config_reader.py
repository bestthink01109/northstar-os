"""
parsers/ss_config_reader.py

Googleスプレッドシートの「会社設定」シートから CompanyConfig を読み込む。

必要パッケージ:
    pip install gspread google-auth

認証方法:
    サービスアカウントの JSON キーファイル、または
    gspread が対応するその他の認証フローを使用。
"""

from __future__ import annotations

import logging
import os
from typing import Any, Optional

# gspread / google-auth はオプション依存
try:
    import gspread
    from google.oauth2.service_account import Credentials as SACredentials

    _GSPREAD_AVAILABLE = True
except ImportError:
    _GSPREAD_AVAILABLE = False

from base_config import (
    CompanyConfig,
    LABOR_SYSTEM_STANDARD,
    LABOR_SYSTEM_MONTHLY_VARIABLE,
    LABOR_SYSTEM_ANNUAL_VARIABLE,
    LAW_DAILY_MAX_HOURS,
    LAW_VARIABLE_WEEKLY_MAX_HOURS,
    LAW_WEEKLY_MAX_HOURS,
)

logger = logging.getLogger(__name__)

# Google API スコープ（読み取り専用）
_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]

# 「会社設定」シートのデフォルト名
SETTINGS_SHEET_NAME = "会社設定"

# セル位置（行インデックス = 0 始まり、列 B = index 1）
# B2 〜 B10 → rows 1 〜 9 (0-based, ヘッダ行 0 を除く)
_ROW_LABOR_SYSTEM = 1          # B2
_ROW_WEEKDAY_HOURS = 2         # B3
_ROW_SATURDAY_HOURS = 3        # B4
_ROW_SUNDAY_WORK = 4           # B5
_ROW_WEEKLY_LEGAL_LIMIT = 5    # B6
_ROW_HALF_DAY_THRESHOLD = 6    # B7
_ROW_MONTHLY_SCHEDULED = 7     # B8
_ROW_DAILY_MAX = 8             # B9
_ROW_WEEKLY_MAX = 9            # B10

# 労働時間制の日本語→内部コード マッピング
_LABOR_SYSTEM_MAP: dict[str, str] = {
    "通常": LABOR_SYSTEM_STANDARD,
    "standard": LABOR_SYSTEM_STANDARD,
    "月単位変形": LABOR_SYSTEM_MONTHLY_VARIABLE,
    "monthly_variable": LABOR_SYSTEM_MONTHLY_VARIABLE,
    "年単位変形": LABOR_SYSTEM_ANNUAL_VARIABLE,
    "annual_variable": LABOR_SYSTEM_ANNUAL_VARIABLE,
}


# ---------------------------------------------------------------------------
# 内部ユーティリティ
# ---------------------------------------------------------------------------

def _to_float(value: Any, field_name: str) -> float:
    """文字列・数値を float に変換する。失敗時は ValueError を送出。"""
    try:
        return float(str(value).strip())
    except (ValueError, TypeError) as exc:
        raise ValueError(f"'{field_name}' の値 '{value}' を数値に変換できません。") from exc


def _to_bool_sunday(value: Any) -> bool:
    """日曜労働フラグを bool に変換する。"""
    normalized = str(value).strip().lower()
    if normalized in {"あり", "true", "yes", "1", "有"}:
        return True
    if normalized in {"なし", "false", "no", "0", "無", ""}:
        return False
    raise ValueError(
        f"日曜労働の値 '{value}' を解釈できません。'あり' または 'なし' を入力してください。"
    )


def _parse_labor_system(value: Any) -> str:
    """日本語または英語の労働時間制文字列を内部コードに変換する。"""
    normalized = str(value).strip()
    result = _LABOR_SYSTEM_MAP.get(normalized)
    if result is None:
        raise ValueError(
            f"労働時間制 '{normalized}' は無効です。"
            f"有効値: {list(_LABOR_SYSTEM_MAP.keys())}"
        )
    return result


def _parse_optional_float(value: Any, field_name: str) -> Optional[float]:
    """空文字・None を None として扱い、値があれば float に変換する。"""
    if value is None or str(value).strip() == "":
        return None
    return _to_float(value, field_name)


# ---------------------------------------------------------------------------
# 認証
# ---------------------------------------------------------------------------

def _build_gspread_client(credentials_path: Optional[str] = None) -> "gspread.Client":
    """
    gspread クライアントを構築して返す。

    Parameters
    ----------
    credentials_path : Optional[str]
        サービスアカウント JSON キーファイルのパス。
        None の場合は環境変数 GOOGLE_APPLICATION_CREDENTIALS を参照。

    Raises
    ------
    EnvironmentError
        gspread / google-auth がインストールされていない場合。
    FileNotFoundError
        認証ファイルが見つからない場合。
    gspread.exceptions.APIError
        Google API 呼び出しに失敗した場合。
    """
    if not _GSPREAD_AVAILABLE:
        raise EnvironmentError(
            "gspread または google-auth がインストールされていません。\n"
            "  pip install gspread google-auth"
        )

    key_path = credentials_path or os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if not key_path:
        raise EnvironmentError(
            "Google 認証情報が見つかりません。\n"
            "  --credentials オプションで JSON キーファイルを指定するか、\n"
            "  環境変数 GOOGLE_APPLICATION_CREDENTIALS を設定してください。"
        )

    if not os.path.isfile(key_path):
        raise FileNotFoundError(
            f"認証ファイルが見つかりません: {key_path}"
        )

    creds = SACredentials.from_service_account_file(key_path, scopes=_SCOPES)
    client = gspread.authorize(creds)
    logger.info("gspread クライアント認証成功: %s", key_path)
    return client


# ---------------------------------------------------------------------------
# コアロジック: シートデータ → CompanyConfig
# ---------------------------------------------------------------------------

def _parse_sheet_values(
    all_values: list[list[Any]],
    company_name: str,
    spreadsheet_id: str,
) -> CompanyConfig:
    """
    「会社設定」シートの全セル値リストから CompanyConfig を生成する。

    Parameters
    ----------
    all_values : list[list]
        sheet.get_all_values() の戻り値（行 × 列 のリスト）。
    company_name : str
        会社名（識別用）。
    spreadsheet_id : str
        読み込み元スプレッドシート ID。

    Returns
    -------
    CompanyConfig
        バリデーション済みの設定オブジェクト。

    Raises
    ------
    ValueError
        セル値が不正またはバリデーションエラーの場合。
    IndexError
        シートの行数が不足している場合。
    """

    def get_b(row_idx: int, label: str) -> Any:
        """all_values[row_idx][1] を安全に取得する（B列 = index 1）。"""
        try:
            row = all_values[row_idx]
        except IndexError:
            raise IndexError(
                f"「会社設定」シートの行 {row_idx + 1}（{label}）が存在しません。"
                f"シートに B{row_idx + 1} まで入力されているか確認してください。"
            )
        if len(row) < 2:
            return ""
        return row[1]

    # B2: 労働時間制
    raw_labor_system = get_b(_ROW_LABOR_SYSTEM, "労働時間制の種類")
    labor_system = _parse_labor_system(raw_labor_system)

    # B3: 平日所定労働時間
    raw_weekday = get_b(_ROW_WEEKDAY_HOURS, "平日所定労働時間")
    weekday_hours = _to_float(raw_weekday, "平日所定労働時間")

    # B4: 土曜所定労働時間
    raw_saturday = get_b(_ROW_SATURDAY_HOURS, "土曜所定労働時間")
    saturday_hours = _to_float(raw_saturday, "土曜所定労働時間")

    # B5: 日曜労働
    raw_sunday = get_b(_ROW_SUNDAY_WORK, "日曜労働")
    sunday_work = _to_bool_sunday(raw_sunday)

    # B6: 週法定労働時間上限
    raw_weekly_legal = get_b(_ROW_WEEKLY_LEGAL_LIMIT, "週法定労働時間上限")
    weekly_legal_limit = _to_float(raw_weekly_legal, "週法定労働時間上限")

    # B7: 半日の基準時間
    raw_half_day = get_b(_ROW_HALF_DAY_THRESHOLD, "半日の基準時間")
    half_day_threshold = _to_float(raw_half_day, "半日の基準時間")

    # B8: 月単位変形・月所定労働時間（任意）
    raw_monthly = get_b(_ROW_MONTHLY_SCHEDULED, "月単位変形・月所定労働時間")
    monthly_scheduled_hours = _parse_optional_float(raw_monthly, "月単位変形・月所定労働時間")

    # B9: 月単位変形・1日上限時間
    raw_daily_max = get_b(_ROW_DAILY_MAX, "1日上限時間")
    daily_max_str = str(raw_daily_max).strip()
    daily_max_hours = _to_float(daily_max_str, "1日上限時間") if daily_max_str else LAW_DAILY_MAX_HOURS

    # B10: 月単位変形・週上限時間
    raw_weekly_max = get_b(_ROW_WEEKLY_MAX, "週上限時間")
    weekly_max_str = str(raw_weekly_max).strip()
    weekly_max_hours = _to_float(weekly_max_str, "週上限時間") if weekly_max_str else LAW_WEEKLY_MAX_HOURS

    config = CompanyConfig(
        company_name=company_name,
        labor_system=labor_system,
        weekday_hours=weekday_hours,
        saturday_hours=saturday_hours,
        sunday_work=sunday_work,
        weekly_legal_limit=weekly_legal_limit,
        half_day_threshold=half_day_threshold,
        monthly_scheduled_hours=monthly_scheduled_hours,
        daily_max_hours=daily_max_hours,
        weekly_max_hours=weekly_max_hours,
        spreadsheet_id=spreadsheet_id,
    )

    # バリデーション
    config.validate_or_raise()
    return config


# ---------------------------------------------------------------------------
# 公開 API
# ---------------------------------------------------------------------------

def load_config_from_spreadsheet(
    spreadsheet_id: str,
    company_name: str = "unknown",
    sheet_name: str = SETTINGS_SHEET_NAME,
    credentials_path: Optional[str] = None,
) -> CompanyConfig:
    """
    Google スプレッドシートの「会社設定」シートから CompanyConfig を読み込む。

    Parameters
    ----------
    spreadsheet_id : str
        スプレッドシートの ID（URL の /d/<id>/ 部分）。
    company_name : str
        会社名（識別用ラベル）。
    sheet_name : str
        設定シートの名前（デフォルト: "会社設定"）。
    credentials_path : Optional[str]
        サービスアカウント JSON キーファイルのパス。
        None の場合は環境変数 GOOGLE_APPLICATION_CREDENTIALS を参照。

    Returns
    -------
    CompanyConfig
        バリデーション済みの設定オブジェクト。

    Raises
    ------
    EnvironmentError
        gspread がインストールされていない、または認証情報が不足している場合。
    FileNotFoundError
        認証ファイルが見つからない場合。
    ValueError
        シートの値が不正またはバリデーションエラーの場合。
    gspread.exceptions.SpreadsheetNotFound
        スプレッドシートが見つからない場合。
    gspread.exceptions.WorksheetNotFound
        「会社設定」シートが見つからない場合。
    """
    client = _build_gspread_client(credentials_path)

    try:
        spreadsheet = client.open_by_key(spreadsheet_id)
    except Exception as exc:
        raise type(exc)(
            f"スプレッドシート '{spreadsheet_id}' を開けませんでした: {exc}"
        ) from exc

    try:
        worksheet = spreadsheet.worksheet(sheet_name)
    except Exception as exc:
        available = [ws.title for ws in spreadsheet.worksheets()]
        raise type(exc)(
            f"シート '{sheet_name}' が見つかりません。"
            f"利用可能なシート: {available}"
        ) from exc

    all_values: list[list[Any]] = worksheet.get_all_values()
    logger.info(
        "スプレッドシート '%s' のシート '%s' を読み込みました（%d 行）。",
        spreadsheet_id,
        sheet_name,
        len(all_values),
    )

    config = _parse_sheet_values(all_values, company_name, spreadsheet_id)
    logger.info("CompanyConfig 読み込み完了:\n%s", config.summary())
    return config


def load_config_from_raw_values(
    all_values: list[list[Any]],
    company_name: str = "unknown",
    spreadsheet_id: str = "(local)",
) -> CompanyConfig:
    """
    既に取得済みのシートデータ（テスト・openpyxl 連携用）から CompanyConfig を生成する。

    Parameters
    ----------
    all_values : list[list[Any]]
        gspread の get_all_values() 相当の 2次元リスト。
    company_name : str
        会社名（識別用ラベル）。
    spreadsheet_id : str
        識別用の任意文字列。

    Returns
    -------
    CompanyConfig
        バリデーション済みの設定オブジェクト。
    """
    return _parse_sheet_values(all_values, company_name, spreadsheet_id)