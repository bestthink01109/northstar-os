以下、チケットの完了条件をすべて満たす完全な実装を生成します。

<<<FILE:exporters/excel_clone_exporter.py>>>
"""
excel_clone_exporter.py
出勤簿Excel出力モジュール（UI/UX改修版 - 外販対応）

変更履歴:
  2026-05-18  外販対応UI/UX改修
    - ヘッダー行の書式改善（#2E4057背景 + 白文字 + 太字）
    - 交互行の背景色（#F5F5F5）
    - 合計行の強調表示（#E8F0FE + 太字 + 上罫線）
    - 会社名・社員名・期間を見出し表示
    - 列幅自動調整
    - 会社ロゴプレースホルダー
    - エラーメッセージ日本語化
"""

from __future__ import annotations

import os
import traceback
from copy import copy
from datetime import datetime, date
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import openpyxl
from openpyxl import Workbook
from openpyxl.cell.cell import Cell
from openpyxl.drawing.image import Image as XLImage
from openpyxl.styles import (
    Alignment,
    Border,
    Font,
    GradientFill,
    PatternFill,
    Side,
    numbers,
)
from openpyxl.styles.numbers import FORMAT_DATE_DATETIME
from openpyxl.utils import get_column_letter
from openpyxl.utils.exceptions import InvalidFileException

# ---------------------------------------------------------------------------
# 定数・カラーパレット
# ---------------------------------------------------------------------------

# ヘッダー行スタイル
HEADER_BG_COLOR = "2E4057"          # 濃紺
HEADER_FONT_COLOR = "FFFFFF"        # 白
# 交互行（偶数行）スタイル
STRIPE_BG_COLOR = "F5F5F5"          # 薄グレー
# 合計行スタイル
TOTAL_BG_COLOR = "E8F0FE"           # 薄青
# タイトル行スタイル
TITLE_BG_COLOR = "1A2940"           # より濃紺
TITLE_FONT_COLOR = "FFFFFF"
# 入力ガイド行
GUIDE_BG_COLOR = "FFF9C4"           # 薄黄

# 列幅設定（文字数単位）
COL_WIDTH_DATE = 12          # 日付列
COL_WIDTH_TIME = 10          # 時刻列
COL_WIDTH_PLACE = 18         # 工事場所列
COL_WIDTH_HOURS = 10         # 時間数列
COL_WIDTH_NAME = 20          # 氏名列
COL_WIDTH_DEFAULT = 14       # その他デフォルト

# フォント設定
FONT_NAME = "游ゴシック"
FONT_NAME_FALLBACK = "メイリオ"

# ---------------------------------------------------------------------------
# ユーティリティ関数
# ---------------------------------------------------------------------------

def _safe_font_name() -> str:
    """利用可能なフォント名を返す（フォールバックあり）。"""
    return FONT_NAME


def _make_thin_border(
    top: bool = False,
    bottom: bool = False,
    left: bool = False,
    right: bool = False,
) -> Border:
    """細線のBorderオブジェクトを生成する。"""
    thin = Side(style="thin", color="CCCCCC")
    medium = Side(style="medium", color="2E4057")
    return Border(
        top=medium if top else (thin if top is not None else None),
        bottom=thin if bottom else None,
        left=thin if left else None,
        right=thin if right else None,
    )


def _make_header_border() -> Border:
    """ヘッダー行用の罫線。"""
    thin = Side(style="thin", color="FFFFFF")
    return Border(
        bottom=Side(style="medium", color="FFFFFF"),
        right=thin,
    )


def _make_total_border() -> Border:
    """合計行用の罫線（上に太線）。"""
    return Border(
        top=Side(style="medium", color="2E4057"),
        bottom=Side(style="thin", color="2E4057"),
    )


def _apply_header_style(cell: Cell, bold: bool = True) -> None:
    """ヘッダー行セルにスタイルを適用する。"""
    cell.fill = PatternFill(
        fill_type="solid", fgColor=HEADER_BG_COLOR
    )
    cell.font = Font(
        name=_safe_font_name(),
        bold=bold,
        color=HEADER_FONT_COLOR,
        size=10,
    )
    cell.alignment = Alignment(
        horizontal="center", vertical="center", wrap_text=True
    )
    cell.border = _make_header_border()


def _apply_stripe_style(cell: Cell, row_index: int) -> None:
    """交互行（偶数行）にストライプ背景を適用する。"""
    if row_index % 2 == 0:
        cell.fill = PatternFill(fill_type="solid", fgColor=STRIPE_BG_COLOR)
    else:
        cell.fill = PatternFill(fill_type="solid", fgColor="FFFFFF")
    cell.font = Font(name=_safe_font_name(), size=10)
    cell.alignment = Alignment(horizontal="center", vertical="center")
    cell.border = Border(
        bottom=Side(style="hair", color="CCCCCC"),
        right=Side(style="hair", color="CCCCCC"),
    )


def _apply_total_style(cell: Cell) -> None:
    """合計行セルにスタイルを適用する。"""
    cell.fill = PatternFill(fill_type="solid", fgColor=TOTAL_BG_COLOR)
    cell.font = Font(
        name=_safe_font_name(), bold=True, size=10, color="1A2940"
    )
    cell.alignment = Alignment(horizontal="center", vertical="center")
    cell.border = _make_total_border()


def _apply_title_style(cell: Cell, size: int = 14) -> None:
    """タイトル行セルにスタイルを適用する。"""
    cell.fill = PatternFill(fill_type="solid", fgColor=TITLE_BG_COLOR)
    cell.font = Font(
        name=_safe_font_name(),
        bold=True,
        size=size,
        color=TITLE_FONT_COLOR,
    )
    cell.alignment = Alignment(
        horizontal="left", vertical="center", indent=1
    )


# ---------------------------------------------------------------------------
# メインクラス
# ---------------------------------------------------------------------------

class ExcelCloneExporter:
    """
    出勤簿ExcelファイルをKENZAI形式でエクスポートするクラス。

    使用例::

        exporter = ExcelCloneExporter(template_path="template.xlsx")
        exporter.export(
            records=records,
            output_path="出勤簿_202604.xlsx",
            company_name="株式会社サンプル",
            employee_name="山田 太郎",
            period="2026年04月",
        )
    """

    # ヘッダー列定義: (列名, 幅, 書式)
    COLUMNS: List[Tuple[str, float, Optional[str]]] = [
        ("日付",       COL_WIDTH_DATE,    "YYYY/MM/DD"),
        ("曜日",       6,                 None),
        ("工事場所",   COL_WIDTH_PLACE,   None),
        ("出社時間",   COL_WIDTH_TIME,    "HH:MM"),
        ("退社時間",   COL_WIDTH_TIME,    "HH:MM"),
        ("休憩(h)",    COL_WIDTH_HOURS,   "0.0"),
        ("実働(h)",    COL_WIDTH_HOURS,   "0.0"),
        ("残業(h)",    COL_WIDTH_HOURS,   "0.0"),
        ("深夜(h)",    COL_WIDTH_HOURS,   "0.0"),
        ("備考",       COL_WIDTH_DEFAULT, None),
    ]

    # 日付列インデックス（0始まり）
    DATE_COL_IDX = 0
    # 合計行のラベル列インデックス
    TOTAL_LABEL_COL = 0

    def __init__(
        self,
        template_path: Optional[str] = None,
        logo_path: Optional[str] = None,
    ) -> None:
        """
        Parameters
        ----------
        template_path : str, optional
            既存のExcelテンプレートパス（Noneの場合は新規作成）
        logo_path : str, optional
            会社ロゴ画像のパス（PNG/JPEG）
        """
        self.template_path = template_path
        self.logo_path = logo_path

    # ------------------------------------------------------------------
    # パブリックAPI
    # ------------------------------------------------------------------

    def export(
        self,
        records: List[Dict[str, Any]],
        output_path: str,
        company_name: str = "",
        employee_name: str = "",
        period: str = "",
        hide_empty_rows: bool = False,
    ) -> str:
        """
        出勤簿Excelを生成して保存する。

        Parameters
        ----------
        records : list[dict]
            日次出勤データのリスト。各要素は以下のキーを持つ::

                {
                    "date": date | str,        # 日付
                    "place": str,              # 工事場所
                    "start_time": str,         # 出社時間 "HH:MM"
                    "end_time": str,           # 退社時間 "HH:MM"
                    "break_hours": float,      # 休憩時間(h)
                    "actual_hours": float,     # 実働時間(h)
                    "overtime_hours": float,   # 残業時間(h)
                    "midnight_hours": float,   # 深夜時間(h)
                    "note": str,               # 備考
                }

        output_path : str
            出力先ファイルパス
        company_name : str
            会社名（見出しに表示）
        employee_name : str
            社員名（見出しに表示）
        period : str
            対象期間（例: "2026年04月"）
        hide_empty_rows : bool
            勤務実績のない行を非表示にするか

        Returns
        -------
        str
            生成されたファイルの絶対パス

        Raises
        ------
        ValueError
            records が空またはNoneの場合
        IOError
            ファイル書き込みに失敗した場合
        """
        if not records:
            raise ValueError(
                "エラー：出勤データが空です。"
                "スプレッドシートにデータが入力されているか確認してください。"
            )

        try:
            wb = self._create_workbook()
            ws = wb.active
            ws.title = "出勤簿"

            # 現在の行カーソル
            current_row = 1

            # ① ロゴ + タイトルブロック
            current_row = self._write_title_block(
                ws, current_row, company_name, employee_name, period
            )

            # ② ヘッダー行
            header_row = current_row
            self._write_header_row(ws, current_row)
            current_row += 1

            # ③ データ行
            data_start_row = current_row
            actual_total = {
                "break_hours": 0.0,
                "actual_hours": 0.0,
                "overtime_hours": 0.0,
                "midnight_hours": 0.0,
            }

            for i, record in enumerate(records):
                row_num = current_row + i
                self._write_data_row(ws, row_num, i, record)

                # 非表示オプション
                if hide_empty_rows and self._is_empty_record(record):
                    ws.row_dimensions[row_num].hidden = True

                # 合計集計
                for key in actual_total:
                    try:
                        val = record.get(key, 0)
                        actual_total[key] += float(val) if val is not None else 0.0
                    except (TypeError, ValueError):
                        pass  # 数値変換できない場合はスキップ

            current_row += len(records)

            # ④ 合計行
            self._write_total_row(ws, current_row, actual_total)
            total_row = current_row
            current_row += 1

            # ⑤ 列幅設定
            self._adjust_column_widths(ws)

            # ⑥ 行高さ設定
            self._adjust_row_heights(ws, header_row, data_start_row, total_row)

            # ⑦ ウィンドウ枠の固定（ヘッダー行以降をスクロール）
            ws.freeze_panes = ws.cell(row=header_row + 1, column=1)

            # ⑧ 印刷設定
            self._setup_print_settings(ws)

            # ⑨ ロゴ画像の挿入
            if self.logo_path:
                self._insert_logo(ws)

            # ⑩ 保存
            output_path = str(Path(output_path).resolve())
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            wb.save(output_path)

            return output_path

        except ValueError:
            raise
        except InvalidFileException as e:
            raise IOError(
                f"エラー：Excelテンプレートファイルが壊れているか、"
                f"対応していない形式です。\n"
                f"対処法：テンプレートファイルを確認してください。\n"
                f"詳細：{e}"
            ) from e
        except PermissionError as e:
            raise IOError(
                f"エラー：ファイルへの書き込み権限がありません。\n"
                f"対処法：出力先フォルダの権限を確認するか、"
                f"ファイルが他のアプリで開かれていないか確認してください。\n"
                f"パス：{output_path}\n"
                f"詳細：{e}"
            ) from e
        except Exception as e:
            raise IOError(
                f"エラー：出勤簿Excelの生成に失敗しました。\n"
                f"対処法：入力データの形式を確認してください。\n"
                f"詳細：{type(e).__name__}: {e}\n"
                f"{traceback.format_exc()}"
            ) from e

    # ------------------------------------------------------------------
    # プライベートメソッド
    # ------------------------------------------------------------------

    def _create_workbook(self) -> Workbook:
        """Workbookを作成（テンプレートがある場合はロード）。"""
        if self.template_path and Path(self.template_path).exists():
            try:
                return openpyxl.load_workbook(self.template_path)
            except Exception as e:
                raise IOError(
                    f"エラー：テンプレートファイルを読み込めませんでした。\n"
                    f"パス：{self.template_path}\n"
                    f"対処法：ファイルが存在するか、Excelで開けるか確認してください。\n"
                    f"詳細：{e}"
                ) from e
        wb = Workbook()
        return wb

    def _write_title_block(
        self,
        ws,
        start_row: int,
        company_name: str,
        employee_name: str,
        period: str,
    ) -> int:
        """
        タイトルブロック（会社名・社員名・期間）を書き込む。

        Returns
        -------
        int
            次の書き込み行番号
        """
        total_cols = len(self.COLUMNS)
        logo_cols = 2  # ロゴ用に確保する列数

        # 行1: 会社名（大見出し）
        ws.row_dimensions[start_row].height = 36
        title_cell = ws.cell(row=start_row, column=logo_cols + 1, value=company_name)
        _apply_title_style(title_cell, size=16)
        ws.merge_cells(
            start_row=start_row,
            start_column=logo_cols + 1,
            end_row=start_row,
            end_column=total_cols,
        )

        # ロゴエリア（左上）のスタイル
        for col in range(1, logo_cols + 1):
            logo_cell = ws.cell(row=start_row, column=col)
            logo_cell.fill = PatternFill(fill_type="solid", fgColor=TITLE_BG_COLOR)

        # 行2: 社員名・期間
        ws.row_dimensions[start_row + 1].height = 28
        info_text = f"社員名：{employee_name}　　対象期間：{period}"
        info_cell = ws.cell(row=start_row + 1, column=1, value=info_text)
        info_cell.fill = PatternFill(fill_type="solid", fgColor="3D5A80")
        info_cell.font = Font(
            name=_safe_font_name(), size=12, color="FFFFFF", bold=False
        )
        info_cell.alignment = Alignment(
            horizontal="left", vertical="center", indent=1
        )
        ws.merge_cells(
            start_row=start_row + 1,
            start_column=1,
            end_row=start_row + 1,
            end_column=total_cols,
        )

        # 行3: 出力日時（右寄せ）
        ws.row_dimensions[start_row + 2].height = 18
        now_str = datetime.now().strftime("出力日時：%Y/%m/%d %H:%M")
        date_cell = ws.cell(row=start_row + 2, column=1, value=now_str)
        date_cell.fill = PatternFill(fill_type="solid", fgColor="F8F9FA")
        date_cell.font = Font(
            name=_safe_font_name(), size=9, color="666666", italic=True
        )
        date_cell.alignment = Alignment(
            horizontal="right", vertical="center"
        )
        ws.merge_cells(
            start_row=start_row + 2,
            start_column=1,
            end_row=start_row + 2,
            end_column=total_cols,
        )

        # 空白区切り行
        ws.row_dimensions[start_row + 3].height = 6

        return start_row + 4  # 次の書き込み行

    def _write_header_row(self, ws, row: int) -> None:
        """ヘッダー行を書き込む。"""
        ws.row_dimensions[row].height = 28
        for col_idx, (col_name, _width, _fmt) in enumerate(self.COLUMNS, start=1):
            cell = ws.cell(row=row, column=col_idx, value=col_name)
            _apply_header_style(cell)

    def _write_data_row(
        self,
        ws,
        row: int,
        row_index: int,
        record: Dict[str, Any],
    ) -> None:
        """
        1件分の出勤データ行を書き込む。

        Parameters
        ----------
        row : int
            書き込む行番号（1始まり）
        row_index : int
            データのインデックス（0始まり、ストライプ計算用）
        record : dict
            出勤データ
        """
        ws.row_dimensions[row].height = 20

        # 日付の取得・変換
        raw_date = record.get("date")
        if raw_date is None:
            raise ValueError(
                f"エラー：{row}行目の日付データが見つかりません。\n"
                f"対処法：スプレッドシートのA列（日付列）が空になっていないか確認してください。"
            )

        try:
            if isinstance(raw_date, str):
                parsed_date = datetime.strptime(raw_date, "%Y/%m/%d").date()
            elif isinstance(raw_date, datetime):
                parsed_date = raw_date.date()
            elif isinstance(raw_date, date):
                parsed_date = raw_date
            else:
                parsed_date = raw_date
        except ValueError:
            raise ValueError(
                f"エラー：{row}行目の日付形式が正しくありません。\n"
                f"入力値：'{raw_date}'\n"
                f"対処法：日付は YYYY/MM/DD 形式で入力してください（例：2026/04/01）。"
            )

        # 曜日
        weekday_ja = ["月", "火", "水", "木", "金", "土", "日"]
        try:
            weekday_str = weekday_ja[parsed_date.weekday()]
        except (AttributeError, IndexError):
            weekday_str = ""

        # データマッピング
        col_values = [
            parsed_date,
            weekday_str,
            record.get("place", ""),
            record.get("start_time", ""),
            record.get("end_time", ""),
            self._safe_float(record, "break_hours", row),
            self._safe_float(record, "actual_hours", row),
            self._safe_float(record, "overtime_hours", row),
            self._safe_float(record, "midnight_hours", row),
            record.get("note", ""),
        ]

        for col_idx, (value, (col_name, _width, fmt)) in enumerate(
            zip(col_values, self.COLUMNS), start=1
        ):
            cell = ws.cell(row=row, column=col_idx, value=value)
            _apply_stripe_style(cell, row_index)

            # 書式設定
            if fmt and value is not None and value != "":
                cell.number_format = fmt

            # 土日の文字色
            if col_idx == 2:  # 曜日列
                if weekday_str == "土":
                    cell.font = Font(
                        name=_safe_font_name(), size=10, color="1565C0"
                    )
                elif weekday_str == "日":
                    cell.font = Font(
                        name=_safe_font_name(), size=10, color="C62828"
                    )

    def _write_total_row(
        self, ws, row: int, totals: Dict[str, float]
    ) -> None:
        """合計行を書き込む。"""
        ws.row_dimensions[row].height = 24

        col_values = [
            "合　計",   # 日付列
            "",          # 曜日
            "",          # 工事場所
            "",          # 出社
            "",          # 退社
            totals.get("break_hours", 0.0),
            totals.get("actual_hours", 0.0),
            totals.get("overtime_hours", 0.0),
            totals.get("midnight_hours", 0.0),
            "",          # 備考
        ]

        for col_idx, (value, (_col_name, _width, fmt)) in enumerate(
            zip(col_values, self.COLUMNS), start=1
        ):
            cell = ws.cell(row=row, column=col_idx, value=value)
            _apply_total_style(cell)
            if fmt and isinstance(value, (int, float)):
                cell.number_format = fmt

    def _adjust_column_widths(self, ws) -> None:
        """列幅を設定する。"""
        for col_idx, (_col_name, width, _fmt) in enumerate(
            self.COLUMNS, start=1
        ):
            col_letter = get_column_letter(col_idx)
            ws.column_dimensions[col_letter].width = width

    def _adjust_row_heights(
        self,
        ws,
        header_row: int,
        data_start_row: int,
        total_row: int,
    ) -> None:
        """特定行の高さを設定する。"""
        ws.row_dimensions[header_row].height = 28
        ws.row_dimensions[total_row].height = 26

    def _setup_print_settings(self, ws) -> None:
        """印刷設定を構成する。"""
        ws.page_setup.orientation = ws.ORIENTATION_LANDSCAPE
        ws.page_setup.paperSize = ws.PAPERSIZE_A4
        ws.page_setup.fitToPage = True
        ws.page_setup.fitToWidth = 1
        ws.page_setup.fitToHeight = 0
        ws.print_title_rows = "1:5"  # タイトル行（ヘッダーを含むタイトルブロック）
        ws.sheet_view.showGridLines = False  # グリッド非表示

    def _insert_logo(self, ws) -> None:
        """会社ロゴ画像をシート左上に挿入する。"""
        if not self.logo_path:
            return
        logo_path = Path(self.logo_path)
        if not logo_path.exists():
            # ロゴが見つからなくても処理続行
            return
        try:
            img = XLImage(str(logo_path))
            img.width = 120
            img.height = 60
            ws.add_image(img, "A1")
        except Exception as e:
            # ロゴ挿入失敗はエラーにしない（警告のみ）
            print(
                f"警告：ロゴ画像の挿入をスキップしました。\n"
                f"原因：{e}\n"
                f"対処法：ロゴファイルが PNG または JPEG 形式であることを確認してください。"
            )

    @staticmethod
    def _safe_float(
        record: Dict[str, Any], key: str, row: int
    ) -> float:
        """
        辞書から安全にfloat値を取得する。

        Parameters
        ----------
        record : dict
            データ辞書
        key : str
            取得するキー
        row : int
            行番号（エラーメッセージ用）

        Returns
        -------
        float
            取得した数値（なければ 0.0）
        """
        col_names = {
            "break_hours": "休憩時間（F列）",
            "actual_hours": "実働時間（G列）",
            "overtime_hours": "残業時間（H列）",
            "midnight_hours": "深夜時間（I列）",
        }
        val = record.get(key)
        if val is None or val == "":
            return 0.0
        try:
            return float(val)
        except (TypeError, ValueError):
            col_label = col_names.get(key, key)
            raise ValueError(
                f"エラー：{row}行目の{col_label}に数値以外の値が入力されています。\n"
                f"入力値：'{val}'\n"
                f"対処法：時間数は数値（例：8.0, 1.5）で入力してください。"
            )

    @staticmethod
    def _is_empty_record(record: Dict[str, Any]) -> bool:
        """勤務実績のない行かどうかを判定する。"""
        for key in ("start_time", "end_time", "actual_hours"):
            val = record.get(key)
            if val is not None and val != "" and val != 0 and val != 0.0:
                return False
        return True


# ---------------------------------------------------------------------------
# スタンドアロン実行用エントリポイント
# ---------------------------------------------------------------------------

def export_attendance(
    records: List[Dict[str, Any]],
    output_path: str,
    company_name: str = "",
    employee_name: str = "",
    period: str = "",
    template_path: Optional[str] = None,
    logo_path: Optional[str] = None,
    hide_empty_rows: bool = False,
) -> str:
    """
    出勤簿Excelを生成するファサード関数。

    Parameters
    ----------
    records : list[dict]
        日次出勤データリスト
    output_path : str
        出力先ファイルパス
    company_name : str
        会社名
    employee_name : str
        社員名
    period : str
        対象期間
    template_path : str, optional
        テンプレートExcelパス
    logo_path : str, optional
        ロゴ画像パス
    hide_empty_rows : bool
        空行を非表示にするか

    Returns
    -------
    str
        生成ファイルの絶対パス

    Raises
    ------
    ValueError
        入力データが不正な場合
    IOError
        ファイル操作に失敗した場合
    """
    exporter = ExcelCloneExporter(
        template_path=template_path,
        logo_path=logo_path,
    )
    return exporter.export(
        records=records,
        output_path=output_path,
        company_name=company_name,
        employee_name=employee_name,
        period=period,
        hide_empty_rows=hide_empty_rows,
    )


if __name__ == "__main__":
    # 動作確認用サンプルデータ（202604）
    sample_records = [
        {
            "date": "2026/04/01",
            "place": "工場",
            "start_time": "08:00",
            "end_time": "17:00",
            "break_hours": 1.0,
            "actual_hours": 8.0,
            "overtime_hours": 0.0,
            "midnight_hours": 