"""
ocr_parser.py
手書き出勤簿OCRパーサー（株式会社純青用）。

自社フォーマットの手書き出勤簿を写真から読み取り、
共通の DayRecord 形式に変換する。

記載内容（BUN_CEO確認済み）:
  - 日付
  - 出勤時刻
  - 退勤時刻
  - 有給の記載
  - 外勤欄（◯がある日 → 外勤手当計算用）
  ※ 作業内容、その他は記載なし

フロー:
  1. OCREngine で画像 → テキスト/構造化データ
  2. 構造化データから DayRecord 形式に変換
  3. 外勤フラグは拡張フィールドとして保持
"""

import os
import sys
import glob
from typing import List, Dict, Any, Optional
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from parsers.base_parser import InputParser
from parsers.ocr_engine import OCREngine
from base_config import CompanyConfig


# 純青の出勤簿で期待されるデータ構造（OCRプロンプト用）
JUNSEI_EXPECTED_FORMAT = """
出勤簿の各行には以下の情報が含まれます:
- 日付（1〜31の数字）
- 曜日（月,火,水,木,金,土,日）
- 出勤時刻（HH:MM形式、例: 8:00, 07:30）
- 退勤時刻（HH:MM形式、例: 17:00, 18:30）
- 有給（有給休暇の場合「有」「有給」「有休」「○」等の記載）
- 外勤（外勤した日に「○」「◯」等の記載）
- 備考（早退、遅刻等の記載がある場合）

各行を以下のJSON配列形式で出力してください:
[
  {
    "day": 1,
    "weekday": "月",
    "start_time": "8:00",
    "end_time": "17:00",
    "paid_leave": false,
    "field_work": false,
    "notes": ""
  },
  ...
]
空白行やデータのない日も day と weekday を含めて出力してください。
出退勤時刻が記載されていない日は start_time と end_time を null にしてください。
"""


class OCRParser(InputParser):
    """
    手書き出勤簿OCRパーサー。
    画像ファイル群を OCREngine で読み取り、DayRecord 形式に変換する。
    """

    def __init__(self, config: CompanyConfig, ocr_backend: str = 'auto'):
        super().__init__(config)
        self.ocr = OCREngine(preferred_backend=ocr_backend)

    def parse(self, input_path: str, employee_master: Dict) -> List[Dict]:
        """
        入力パスから全社員分のデータを読み取る。

        input_path がディレクトリの場合:
          - 社員名ごとのサブディレクトリ or ファイル名に社員名を含む画像を検出
        input_path が単一ファイルの場合:
          - そのファイルのみ処理

        Returns:
            list of sheet_data (parse_sheet互換のdict)
        """
        all_data = []

        if os.path.isdir(input_path):
            # ディレクトリ内の画像を社員名ごとに分類
            image_files = self._find_images(input_path)
            employee_images = self._classify_by_employee(image_files, employee_master)

            for emp_name, images in employee_images.items():
                try:
                    data = self._parse_employee_images(emp_name, images)
                    if data:
                        all_data.append(data)
                except Exception as e:
                    print(f"[OCR] {emp_name} の処理でエラー: {e}")
                    continue
        elif os.path.isfile(input_path):
            # 単一ファイル
            data = self._parse_single_image(input_path)
            if data:
                all_data.append(data)

        return all_data

    def parse_sheet(self, sheet_name: str, **kwargs) -> Dict:
        """
        特定の社員の画像群からデータを読み取る。

        kwargs:
            image_paths: list of str（画像ファイルパスのリスト）
        """
        image_paths = kwargs.get('image_paths', [])
        return self._parse_employee_images(sheet_name, image_paths)

    def _find_images(self, directory: str) -> List[str]:
        """ディレクトリ内の画像ファイルを全て検出する。"""
        extensions = ['*.jpg', '*.jpeg', '*.png', '*.heic', '*.webp']
        images = []
        for ext in extensions:
            images.extend(glob.glob(os.path.join(directory, ext)))
            images.extend(glob.glob(os.path.join(directory, '**', ext), recursive=True))
        return sorted(set(images))

    def _classify_by_employee(self, image_files: List[str],
                               employee_master: Dict) -> Dict[str, List[str]]:
        """画像ファイルを社員名ごとに分類する。"""
        result = {}

        for img_path in image_files:
            basename = os.path.basename(img_path)
            dirname = os.path.basename(os.path.dirname(img_path))

            for emp_name in employee_master:
                if emp_name in basename or emp_name in dirname:
                    if emp_name not in result:
                        result[emp_name] = []
                    result[emp_name].append(img_path)
                    break

        return result

    def _parse_employee_images(self, emp_name: str,
                                image_paths: List[str]) -> Optional[Dict]:
        """社員1名分の画像群からデータを抽出する。"""
        if not image_paths:
            return None

        all_days = []
        year, month = None, None

        for img_path in sorted(image_paths):
            print(f"  [OCR] {emp_name}: {os.path.basename(img_path)} を認識中...")

            result = self.ocr.recognize(
                img_path,
                language='ja',
                expected_format=JUNSEI_EXPECTED_FORMAT,
            )

            if result['structured']:
                days, yr, mo = self._structured_to_days(result['structured'])
                all_days.extend(days)
                if yr:
                    year = yr
                if mo:
                    month = mo
            else:
                # 構造化データが取れなかった場合、生テキストからベストエフォートで解析
                print(f"    [注意] 構造化抽出失敗、生テキストから解析を試行")
                days = self._raw_text_to_days(result['raw_text'])
                all_days.extend(days)

        if not all_days:
            return None

        # 年月が取れなかった場合は推定
        if not year or not month:
            year = datetime.now().year
            month = datetime.now().month

        return {
            'sheet_name': emp_name,
            'year': year,
            'month': month,
            'days': all_days,
            'summary_excel': {
                'attend_days': sum(1 for d in all_days
                                   if d.get('t_start') is not None),
                'paid_leave_days': sum(1 for d in all_days
                                       if d.get('is_paid', False)),
                'paid_leave_hours': 0,
            },
        }

    def _parse_single_image(self, image_path: str) -> Optional[Dict]:
        """単一画像からデータを読み取る。"""
        result = self.ocr.recognize(
            image_path,
            language='ja',
            expected_format=JUNSEI_EXPECTED_FORMAT,
        )

        emp_name = os.path.splitext(os.path.basename(image_path))[0]

        if result['structured']:
            days, year, month = self._structured_to_days(result['structured'])
            if days:
                return {
                    'sheet_name': emp_name,
                    'year': year or datetime.now().year,
                    'month': month or datetime.now().month,
                    'days': days,
                    'summary_excel': {
                        'attend_days': sum(1 for d in days
                                           if d.get('t_start') is not None),
                        'paid_leave_days': sum(1 for d in days
                                               if d.get('is_paid', False)),
                        'paid_leave_hours': 0,
                    },
                }
        return None

    def _structured_to_days(self, structured_data) -> tuple:
        """
        OCRの構造化データ（JSON配列）をDayRecord互換のdictリストに変換する。
        Returns: (days_list, year, month)
        """
        days = []
        year, month = None, None

        items = structured_data if isinstance(structured_data, list) else []

        for item in items:
            day_num = item.get('day')
            if day_num is None:
                continue

            weekday = item.get('weekday', '')
            start = item.get('start_time')
            end = item.get('end_time')
            is_paid = item.get('paid_leave', False)
            field_work = item.get('field_work', False)
            notes = item.get('notes', '')

            # 時刻のパース
            t_start = self._parse_time(start)
            t_end = self._parse_time(end)

            # 曜日から土日判定
            is_saturday = weekday == '土'
            is_sunday = weekday == '日'

            # 有給判定
            if isinstance(is_paid, str):
                is_paid = is_paid in ('有', '有給', '有休', '○', '◯', 'true', 'True')

            day_rec = {
                'row': day_num + 2,  # Excel互換のダミー行番号
                'day': int(day_num),
                'weekday': weekday,
                'place': '',
                't_start': t_start,
                't_end': t_end,
                't_depart': t_start,   # OCRでは出社=開始とみなす
                't_site_s': None,
                't_site_e': None,
                't_arrive': t_end,     # OCRでは退社=終了とみなす
                'time_off': 0.0,
                'time_off_raw': '',
                'is_absent': False,
                'is_paid': bool(is_paid),
                'is_training': False,
                'is_saturday': is_saturday,
                'is_sunday': is_sunday,
                'excel_work': 0.0,
                'excel_ot_out': 0.0,
                'excel_ot_in': 0.0,
                'excel_holiday_w': 0.0,
                'excel_absence': 0.0,
                # 純青固有: 外勤フラグ
                'field_work': bool(field_work),
                'notes': notes,
            }
            days.append(day_rec)

        return days, year, month

    def _raw_text_to_days(self, raw_text: str) -> List[Dict]:
        """
        生テキストからベストエフォートで日次データを抽出する。
        構造化抽出に失敗した場合のフォールバック。
        """
        import re
        days = []

        # 「数字 曜日 時刻 時刻」のパターンを検出
        # 例: "1 月 8:00 17:00"
        pattern = re.compile(
            r'(\d{1,2})\s*[日]?\s*'       # 日付
            r'[（(]?([月火水木金土日])[）)]?\s*'  # 曜日
            r'(\d{1,2}[:\：]\d{2})?\s*'    # 開始時刻
            r'[-~〜]?\s*'
            r'(\d{1,2}[:\：]\d{2})?'       # 終了時刻
        )

        for line in raw_text.split('\n'):
            m = pattern.search(line)
            if m:
                day_num = int(m.group(1))
                weekday = m.group(2)
                start = m.group(3)
                end = m.group(4)

                day_rec = {
                    'row': day_num + 2,
                    'day': day_num,
                    'weekday': weekday,
                    'place': '',
                    't_start': self._parse_time(start),
                    't_end': self._parse_time(end),
                    't_depart': self._parse_time(start),
                    't_site_s': None,
                    't_site_e': None,
                    't_arrive': self._parse_time(end),
                    'time_off': 0.0,
                    'time_off_raw': '',
                    'is_absent': False,
                    'is_paid': '有' in line or '有給' in line,
                    'is_training': False,
                    'is_saturday': weekday == '土',
                    'is_sunday': weekday == '日',
                    'excel_work': 0.0,
                    'excel_ot_out': 0.0,
                    'excel_ot_in': 0.0,
                    'excel_holiday_w': 0.0,
                    'excel_absence': 0.0,
                    'field_work': '◯' in line or '○' in line,
                    'notes': '',
                }
                days.append(day_rec)

        return days

    def _parse_time(self, time_str: Optional[str]) -> Optional[float]:
        """時刻文字列をfloat（時間数）に変換する。"""
        if time_str is None or time_str == '' or time_str == 'null':
            return None
        try:
            time_str = time_str.replace('：', ':')
            parts = time_str.split(':')
            return int(parts[0]) + int(parts[1]) / 60.0
        except (ValueError, IndexError):
            return None
