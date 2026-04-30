"""
pdf_parser.py
スキャンPDF日報パーサー（株式会社福岡プラント機工用）。

スキャンPDF（画像として埋め込まれた日報）を
OCREngine で読み取り、DayRecord 形式に変換する。

日報の特徴（BUN_CEO確認済み）:
  - 1日1ページ または 月まとめ
  - フリーフォーマット（時間以外の情報も含まれる可能性）
  - 出退勤時刻が含まれている想定
  ※ サンプルPDF入手後にフォーマット解析を行い、本パーサーを精緻化する

フロー:
  1. PDFを画像に変換（pdf2image or fitz）
  2. 各ページをOCREngine で認識
  3. 認識結果から出退勤時刻を抽出してDayRecord形式に変換
"""

import os
import sys
import glob
import tempfile
from typing import List, Dict, Any, Optional
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from parsers.base_parser import InputParser
from parsers.ocr_engine import OCREngine
from base_config import CompanyConfig


# 福岡プラント機工の日報で期待されるデータ構造（OCRプロンプト用）
# ※ サンプルPDF入手後に精緻に調整する
FUKUOKA_EXPECTED_FORMAT = """
この日報から以下の勤怠情報を読み取ってください:
- 日付（YYYY-MM-DD形式、または○月○日形式）
- 社員名（記載がある場合）
- 出勤時刻（HH:MM形式）
- 退勤時刻（HH:MM形式）
- 休憩時間（記載がある場合）
- 作業内容（概要のみ）
- 特記事項（有給、欠勤、早退、遅刻等）

以下のJSON形式で出力してください:
{
  "date": "2026-04-01",
  "employee_name": "社員名",
  "start_time": "8:00",
  "end_time": "17:00",
  "break_hours": null,
  "work_summary": "作業概要",
  "notes": "特記事項（有給、欠勤等）"
}

複数日分のデータがある場合はJSON配列で出力してください。
"""


class PDFParser(InputParser):
    """
    スキャンPDF日報パーサー。
    PDF → 画像変換 → OCR → DayRecord形式 のパイプライン。
    """

    def __init__(self, config: CompanyConfig, ocr_backend: str = 'auto'):
        super().__init__(config)
        self.ocr = OCREngine(preferred_backend=ocr_backend)
        self._check_dependencies()

    def _check_dependencies(self):
        """PDF→画像変換に必要な依存パッケージを確認する。"""
        self._pdf_converter = None

        # PyMuPDF (fitz) を優先
        try:
            import fitz
            self._pdf_converter = 'fitz'
            return
        except ImportError:
            pass

        # pdf2image（popplerが必要）
        try:
            from pdf2image import convert_from_path
            self._pdf_converter = 'pdf2image'
            return
        except ImportError:
            pass

        print("[PDF] 警告: PDF→画像変換パッケージが見つかりません。")
        print("      次のいずれかをインストールしてください:")
        print("        pip install PyMuPDF")
        print("        pip install pdf2image  # + poppler")

    def parse(self, input_path: str, employee_master: Dict) -> List[Dict]:
        """
        PDFファイルまたはディレクトリから全社員分のデータを読み取る。

        1日1ページの場合: 各ページから1件の日次レコードを抽出
        月まとめの場合: 全ページの情報を統合して月次レコードを構成
        """
        all_data = []

        if os.path.isdir(input_path):
            pdf_files = sorted(glob.glob(os.path.join(input_path, '*.pdf')))
            for pdf_path in pdf_files:
                try:
                    data = self._parse_pdf(pdf_path, employee_master)
                    if data:
                        all_data.extend(data)
                except Exception as e:
                    print(f"[PDF] {os.path.basename(pdf_path)} の処理でエラー: {e}")
                    continue
        elif os.path.isfile(input_path) and input_path.lower().endswith('.pdf'):
            data = self._parse_pdf(input_path, employee_master)
            if data:
                all_data.extend(data)

        return all_data

    def parse_sheet(self, sheet_name: str, **kwargs) -> Dict:
        """
        特定のPDFファイルからデータを読み取る。
        kwargs:
            pdf_path: str
        """
        pdf_path = kwargs.get('pdf_path', '')
        if not pdf_path:
            raise ValueError("pdf_path が指定されていません")

        results = self._parse_pdf(pdf_path, {})
        for r in results:
            if r.get('sheet_name') == sheet_name:
                return r
        return results[0] if results else {}

    def _parse_pdf(self, pdf_path: str, employee_master: Dict) -> List[Dict]:
        """PDFファイルを処理してsheet_dataリストを返す。"""
        if self._pdf_converter is None:
            raise RuntimeError("PDF→画像変換パッケージがインストールされていません")

        print(f"[PDF] 処理中: {os.path.basename(pdf_path)}")

        # 1. PDFを画像に変換
        images = self._pdf_to_images(pdf_path)
        if not images:
            return []

        # 2. 各ページをOCRで認識
        page_results = []
        for i, img_path in enumerate(images):
            print(f"  [OCR] ページ {i+1}/{len(images)} を認識中...")
            result = self.ocr.recognize(
                img_path,
                language='ja',
                expected_format=FUKUOKA_EXPECTED_FORMAT,
            )
            page_results.append(result)

        # 3. 認識結果を社員ごとのDayRecordに変換
        employee_days = self._results_to_employee_days(page_results, employee_master)

        # 4. sheet_data形式に変換
        all_data = []
        for emp_name, days in employee_days.items():
            if not days:
                continue

            # 年月の推定
            year = datetime.now().year
            month = datetime.now().month
            if days[0].get('_date'):
                try:
                    dt = datetime.strptime(days[0]['_date'], '%Y-%m-%d')
                    year = dt.year
                    month = dt.month
                except (ValueError, TypeError):
                    pass

            all_data.append({
                'sheet_name': emp_name,
                'year': year,
                'month': month,
                'days': days,
                'summary_excel': {
                    'attend_days': sum(1 for d in days
                                       if d.get('t_start') is not None),
                    'paid_leave_days': sum(1 for d in days
                                           if d.get('is_paid', False)),
                    'paid_leave_hours': 0,
                },
            })

        # 一時画像ファイルの削除
        for img_path in images:
            try:
                os.remove(img_path)
            except OSError:
                pass

        return all_data

    def _pdf_to_images(self, pdf_path: str) -> List[str]:
        """PDFの各ページを画像ファイルに変換する。"""
        temp_dir = tempfile.mkdtemp(prefix='payroll_pdf_')

        if self._pdf_converter == 'fitz':
            return self._pdf_to_images_fitz(pdf_path, temp_dir)
        elif self._pdf_converter == 'pdf2image':
            return self._pdf_to_images_pdf2image(pdf_path, temp_dir)
        return []

    def _pdf_to_images_fitz(self, pdf_path: str, output_dir: str) -> List[str]:
        """PyMuPDF (fitz) を使用してPDF→画像変換。"""
        import fitz
        doc = fitz.open(pdf_path)
        images = []

        for page_num in range(doc.page_count):
            page = doc[page_num]
            # 300dpiで高品質レンダリング
            mat = fitz.Matrix(300 / 72, 300 / 72)
            pix = page.get_pixmap(matrix=mat)
            img_path = os.path.join(output_dir, f'page_{page_num + 1:03d}.png')
            pix.save(img_path)
            images.append(img_path)

        doc.close()
        return images

    def _pdf_to_images_pdf2image(self, pdf_path: str, output_dir: str) -> List[str]:
        """pdf2imageを使用してPDF→画像変換。"""
        from pdf2image import convert_from_path
        pages = convert_from_path(pdf_path, dpi=300, output_folder=output_dir,
                                   fmt='png')
        images = []
        for i, page in enumerate(pages):
            img_path = os.path.join(output_dir, f'page_{i + 1:03d}.png')
            page.save(img_path, 'PNG')
            images.append(img_path)
        return images

    def _results_to_employee_days(self, page_results: List[Dict],
                                   employee_master: Dict) -> Dict[str, List[Dict]]:
        """OCR結果を社員ごとのDayRecordリストに分類する。"""
        employee_days = {}
        unknown_emp = 'unknown'

        for result in page_results:
            structured = result.get('structured')
            if structured is None:
                continue

            # 単一dict or list[dict] の両対応
            items = structured if isinstance(structured, list) else [structured]

            for item in items:
                emp_name = item.get('employee_name', unknown_emp)

                # 社員マスターとのマッチング
                matched_name = emp_name
                for master_name in employee_master:
                    if master_name in emp_name or emp_name in master_name:
                        matched_name = master_name
                        break

                if matched_name not in employee_days:
                    employee_days[matched_name] = []

                day_rec = self._item_to_day_record(item)
                if day_rec:
                    employee_days[matched_name].append(day_rec)

        return employee_days

    def _item_to_day_record(self, item: Dict) -> Optional[Dict]:
        """OCR抽出アイテムをDayRecord互換dictに変換する。"""
        date_str = item.get('date', '')
        start = item.get('start_time')
        end = item.get('end_time')
        notes = item.get('notes', '')

        # 日付からday番号を抽出
        day_num = None
        if date_str:
            try:
                dt = datetime.strptime(date_str, '%Y-%m-%d')
                day_num = dt.day
            except ValueError:
                # "4月1日" 形式
                import re
                m = re.search(r'(\d{1,2})\s*日', date_str)
                if m:
                    day_num = int(m.group(1))

        if day_num is None:
            return None

        t_start = self._parse_time(start)
        t_end = self._parse_time(end)

        # 有給・欠勤の判定
        is_paid = any(kw in str(notes) for kw in ['有給', '有休', '年休'])
        is_absent = any(kw in str(notes) for kw in ['欠勤'])

        return {
            'row': day_num + 2,
            'day': day_num,
            'weekday': '',
            'place': '',
            't_start': t_start,
            't_end': t_end,
            't_depart': t_start,
            't_site_s': None,
            't_site_e': None,
            't_arrive': t_end,
            'time_off': 0.0,
            'time_off_raw': '',
            'is_absent': is_absent,
            'is_paid': is_paid,
            'is_training': False,
            'is_saturday': False,
            'is_sunday': False,
            'excel_work': 0.0,
            'excel_ot_out': 0.0,
            'excel_ot_in': 0.0,
            'excel_holiday_w': 0.0,
            'excel_absence': 0.0,
            'notes': notes,
            '_date': date_str,
        }

    def _parse_time(self, time_str: Optional[str]) -> Optional[float]:
        """時刻文字列をfloat（時間数）に変換する。"""
        if time_str is None or time_str == '' or time_str == 'null':
            return None
        try:
            time_str = str(time_str).replace('：', ':')
            parts = time_str.split(':')
            return int(parts[0]) + int(parts[1]) / 60.0
        except (ValueError, IndexError):
            return None
