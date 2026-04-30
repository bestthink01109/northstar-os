#!/usr/bin/env python3
"""
timecard_to_csv.py - タイムカード画像 → CSV 全自動変換スクリプト

【概要】
MAX社 ER-Sカードのタイムカード画像(HEIC/JPG)をローカルOCRで読み取り、
社員マスターの情報に基づいてビジネスルールを適用し、
給与らくだ用のCSVファイルを従業員ごとに出力する。

【実行環境】 macOS
【OCRエンジン】 Apple Vision Framework（macOS内蔵、API不要）

【使い方】
  python3 timecard_to_csv.py <画像フォルダ> <年月(YYYYMM)> [--master 社員マスター.csv] [--output 出力フォルダ]

【例】
  python3 timecard_to_csv.py ./images 202603 --master ./社員マスター.csv --output ./202603
"""

from __future__ import annotations

import argparse
import csv
import os
import re
import subprocess
import sys
import unicodedata
from calendar import monthrange
from datetime import datetime, date
from pathlib import Path


# =============================================================================
# 1. HEIC → JPG 変換
# =============================================================================

def convert_heic_to_jpg(image_dir: str) -> list[str]:
    """HEIC画像をJPGに変換し、全JPGファイルパスを返す（重複排除）"""
    image_path = Path(image_dir)
    heic_files = []
    jpg_files_existing = []

    for f in sorted(image_path.iterdir()):
        # NFC正規化して比較
        fname_nfc = unicodedata.normalize('NFC', f.name)
        fname_lower = fname_nfc.lower()

        # _temp.jpgは既存の一時ファイルなので除外
        if '_temp.' in fname_lower:
            continue

        if fname_lower.endswith('.heic'):
            heic_files.append(f)
        elif fname_lower.endswith(('.jpg', '.jpeg', '.png')):
            jpg_files_existing.append(f)

    # HEIC→JPG変換（NFC正規化したファイル名で出力）
    converted = set()
    result_files = []

    for f in heic_files:
        # NFC正規化した名前でJPGパスを生成
        stem_nfc = unicodedata.normalize('NFC', f.stem)
        jpg_name = stem_nfc + '.jpg'
        jpg_path = f.parent / jpg_name

        # 重複チェック（NFC正規化済みの名前で比較）
        if stem_nfc.lower() in converted:
            continue
        converted.add(stem_nfc.lower())

        if not jpg_path.exists():
            print(f"  変換中: {f.name} → {jpg_name}")
            proc = subprocess.run(
                ['sips', '-s', 'format', 'jpeg', str(f), '--out', str(jpg_path)],
                capture_output=True, text=True
            )
            if proc.returncode != 0:
                print(f"  ⚠ 変換失敗: {f.name} - {proc.stderr.strip()}")
                continue

        result_files.append(str(jpg_path))

    # 既存のJPGファイル（HEIC由来でないもの）を追加
    for f in jpg_files_existing:
        stem_nfc = unicodedata.normalize('NFC', f.stem).lower()
        if stem_nfc not in converted:
            converted.add(stem_nfc)
            result_files.append(str(f))

    return sorted(result_files)


# =============================================================================
# 2. Apple Vision Framework OCR
# =============================================================================

def _ensure_ocr_binary() -> str:
    """OCR用Swiftバイナリをコンパイルして返す（初回のみ）"""
    binary_path = '/tmp/_timecard_ocr'
    swift_path = '/tmp/_timecard_ocr.swift'

    # バイナリが既に存在すればそのまま使う
    if os.path.exists(binary_path):
        return binary_path

    swift_code = '''
import Foundation
import Vision
import AppKit

let args = CommandLine.arguments
guard args.count > 1 else {
    print("ERROR: No image path provided")
    exit(1)
}

let imagePath = args[1]
let url = URL(fileURLWithPath: imagePath)
guard let image = NSImage(contentsOf: url),
      let tiffData = image.tiffRepresentation,
      let bitmap = NSBitmapImageRep(data: tiffData),
      let cgImage = bitmap.cgImage else {
    print("ERROR: Cannot load image: \\(imagePath)")
    exit(1)
}

let request = VNRecognizeTextRequest()
request.recognitionLanguages = ["ja", "en"]
request.recognitionLevel = .accurate
request.usesLanguageCorrection = true

let handler = VNImageRequestHandler(cgImage: cgImage, options: [:])
do {
    try handler.perform([request])
} catch {
    print("ERROR: \\(error)")
    exit(1)
}

guard let observations = request.results else {
    print("ERROR: No results")
    exit(1)
}

let sorted = observations.sorted { a, b in
    let ay = 1.0 - a.boundingBox.midY
    let by = 1.0 - b.boundingBox.midY
    if abs(ay - by) < 0.015 {
        return a.boundingBox.midX < b.boundingBox.midX
    }
    return ay < by
}

for observation in sorted {
    if let candidate = observation.topCandidates(1).first {
        let box = observation.boundingBox
        let y = 1.0 - box.midY
        let x = box.midX
        print(String(format: "%.4f\\t%.4f\\t%@", y, x, candidate.string))
    }
}
'''

    print("  OCRバイナリをコンパイル中（初回のみ、1〜2分かかります）...")
    with open(swift_path, 'w') as f:
        f.write(swift_code)

    result = subprocess.run(
        ['swiftc', '-O', swift_path, '-o', binary_path],
        capture_output=True, text=True, timeout=180
    )

    if result.returncode != 0:
        print(f"  ⚠ コンパイル失敗: {result.stderr.strip()}")
        sys.exit(1)

    print("  OCRバイナリ準備完了 ✅")
    return binary_path


def ocr_image_apple_vision(image_path: str) -> str:
    """macOS Vision Frameworkを使ってOCRを実行し、テキストを返す"""
    binary = _ensure_ocr_binary()

    # 画像パスを絶対パスに変換
    abs_path = os.path.abspath(image_path)

    result = subprocess.run(
        [binary, abs_path],
        capture_output=True, text=True, timeout=30
    )

    if result.returncode != 0:
        print(f"  ⚠ OCRエラー: {image_path}")
        print(f"    stderr: {result.stderr.strip()}")
        return ""

    return result.stdout


# =============================================================================
# 3. OCR結果パース（MAX ER-Sカード形式）
# =============================================================================

def parse_timecard_ocr(ocr_text: str, card_type: str) -> list[dict]:
    """
    OCR結果をパースしてタイムカードデータを抽出する

    card_type: "front" (前半: 1-16日) or "back" (後半: 17-31日)

    Returns: [
        {"day": 1, "clock_in": "8:30", "clock_out": "17:45", "memo": ""},
        {"day": 2, "clock_in": "", "clock_out": "", "memo": "有休"},
        ...
    ]
    """
    records = []
    lines = ocr_text.strip().split('\n')

    if not lines:
        return records

    # OCRの各行は "y座標\tx座標\tテキスト" 形式
    parsed_items = []
    for line in lines:
        parts = line.split('\t')
        if len(parts) >= 3:
            try:
                y = float(parts[0])
                x = float(parts[1])
                text = parts[2].strip()
                parsed_items.append({'y': y, 'x': x, 'text': text})
            except ValueError:
                continue

    # X座標による列分類の閾値（OCR生データから判定）
    # 日付列: x ≈ 0.12〜0.17
    # 出勤列: x ≈ 0.22〜0.28
    # 退勤列: x ≈ 0.34〜0.40
    # メモ/その他: x > 0.45
    COL_DATE_MAX = 0.20
    COL_CLOCKIN_MIN = 0.20
    COL_CLOCKIN_MAX = 0.31
    COL_CLOCKOUT_MIN = 0.31
    COL_CLOCKOUT_MAX = 0.45

    # Y座標でグルーピング（近い行を同じ行とみなす）
    rows = group_by_rows(parsed_items, threshold=0.020)

    # 有効な日付範囲
    valid_days = range(1, 17) if card_type == "front" else range(17, 32)

    for row in rows:
        day = None
        clock_in_raw = ""
        clock_out_raw = ""
        memo_parts = []

        for item in row:
            x = item['x']
            text = item['text']

            # メモ検出（有休、欠勤、休けい等）- 位置問わず
            if re.search(r'有[休給]|欠勤|休けい|休憩', text):
                memo_parts.append(text)
                continue

            # --- 日付列 ---
            if x < COL_DATE_MAX:
                # 先頭の数字を抽出（「14土」→14、「9月」→9、「102」→10）
                d = extract_day_number(text)
                if d is not None and d in valid_days:
                    day = d

            # --- 出勤列 ---
            elif COL_CLOCKIN_MIN <= x < COL_CLOCKIN_MAX:
                t = clean_ocr_time(text)
                if t:
                    clock_in_raw = t

            # --- 退勤列 ---
            elif COL_CLOCKOUT_MIN <= x < COL_CLOCKOUT_MAX:
                t = clean_ocr_time(text)
                if t:
                    clock_out_raw = t

            # --- それ以降（メモ等） ---
            elif x >= COL_CLOCKOUT_MAX:
                if re.search(r'有[休給]|欠勤|休けい|休憩', text):
                    memo_parts.append(text)

        if day is not None:
            # 時刻の異常値検証
            clock_in_validated = validate_time(clock_in_raw, 'in')
            clock_out_validated = validate_time(clock_out_raw, 'out')

            records.append({
                'day': day,
                'clock_in': clock_in_validated,
                'clock_out': clock_out_validated,
                'memo': ' '.join(memo_parts),
                '_has_date': True,
            })
        elif clock_in_raw or clock_out_raw:
            # 日付なしだがデータありの行 → 後で推定
            clock_in_validated = validate_time(clock_in_raw, 'in')
            clock_out_validated = validate_time(clock_out_raw, 'out')
            records.append({
                'day': None,
                'clock_in': clock_in_validated,
                'clock_out': clock_out_validated,
                'memo': ' '.join(memo_parts),
                '_has_date': False,
            })

    # --- 日付なし行の推定 ---
    records = infer_missing_days(records, valid_days)

    # _has_date フラグを除去
    for rec in records:
        rec.pop('_has_date', None)

    return records


def validate_time(time_str: str, time_type: str) -> str:
    """時刻の異常値を検証し、明らかにおかしい値は空にする

    time_type: 'in' (出勤) or 'out' (退勤)
    """
    if not time_str:
        return ""

    try:
        minutes = time_to_minutes(time_str)
    except ValueError:
        return ""

    if time_type == 'in':
        # 出勤は通常 5:00〜15:00 の範囲
        if minutes < 300 or minutes > 900:  # 5:00〜15:00
            return ""
    elif time_type == 'out':
        # 退勤は通常 12:00〜23:59 の範囲
        if minutes < 720 or minutes > 1439:  # 12:00〜23:59
            return ""

    return time_str


def infer_missing_days(records: list[dict], valid_days: range) -> list[dict]:
    """日付なしの行に対して、前後の日付から推定して埋める

    タイムカードは日付順に並んでいるため、
    日付ありの行の間にある日付なし行は、間の欠番日を順に割り当てる
    """
    result = []
    i = 0

    while i < len(records):
        rec = records[i]

        if rec['_has_date'] and rec['day'] is not None:
            result.append(rec)
            i += 1
            continue

        # 日付なしの行 → 前後の日付あり行から推定
        # 前の日付あり行を探す
        prev_day = None
        for j in range(len(result) - 1, -1, -1):
            if result[j]['_has_date'] and result[j]['day'] is not None:
                prev_day = result[j]['day']
                break

        # 次の日付あり行を探す
        next_day = None
        for j in range(i + 1, len(records)):
            if records[j]['_has_date'] and records[j]['day'] is not None:
                next_day = records[j]['day']
                break

        # 推定: prev_day と next_day の間で未使用の日を割り当て
        if prev_day is not None:
            # prev_day+1 から順に、まだ使われていない日を探す
            used_days = {r['day'] for r in result if r['day'] is not None}
            candidate = prev_day + 1
            while candidate in used_days and candidate <= 31:
                candidate += 1
            if candidate in valid_days and candidate <= 31:
                if next_day is None or candidate < next_day:
                    rec['day'] = candidate
                    rec['_has_date'] = True
                    result.append(rec)

        i += 1

    return result


def extract_day_number(text: str) -> int | None:
    """OCRテキストから日付（1〜31）を抽出する

    対応パターン: "14土", "9月", "12才", "102", "5ま", "74.", "2月", "3" 等
    OCRが "7" を "74" や "74." と誤読するケースにも対応
    """
    # 先頭の数字だけ取り出す
    m = re.match(r'(\d{1,2})', text)
    if m:
        d = int(m.group(1))
        if 1 <= d <= 31:
            return d
        # 2桁で31超え → 先頭1桁だけ取り直す（例: "74." → 7）
        if d > 31 and len(m.group(1)) == 2:
            d1 = int(m.group(1)[0])
            if 1 <= d1 <= 9:
                return d1
    return None


def clean_ocr_time(text: str) -> str:
    """OCRで読み取った時刻テキストをH:MM形式に変換する

    対応パターン:
      "19:00"  → "19:00"   (正常)
      "8:59"   → "8:59"    (正常)
      "8458"   → "8:58"    (コロンなし、先頭が8→8:58と推定、4を誤読)
      "19117"  → "19:17"   (5桁、19:17と推定、余分な1)
      "8=57"   → "8:57"    (=がコロンの誤読)
      "18229"  → "18:29"   (5桁、余分な2)
      "1806"   → "18:06"   (4桁)
      "858"    → "8:58"    (3桁)
      "888"    → "8:38"?   (曖昧)
      "18:10"  → "18:10"   (正常)
      "18207"  → "18:07"   (5桁)
    """
    text = text.strip()

    # まず記号をコロンに正規化（=, ., ;, etc）
    text = re.sub(r'[=;．・]', ':', text)

    # 正常な時刻形式 H:MM or HH:MM
    m = re.match(r'^(\d{1,2}):(\d{2})$', text)
    if m:
        h, mi = int(m.group(1)), int(m.group(2))
        if 0 <= h <= 23 and 0 <= mi <= 59:
            return f"{h}:{mi:02d}"

    # 数字のみを抽出
    digits = re.sub(r'[^\d]', '', text)

    if not digits:
        return ""

    # 3桁: H + MM（例: "858" → 8:58）
    if len(digits) == 3:
        h = int(digits[0])
        mi = int(digits[1:3])
        if 0 <= h <= 9 and 0 <= mi <= 59:
            return f"{h}:{mi:02d}"

    # 4桁: HH + MM（例: "1806" → 18:06, "8458" → 先頭を信用して H:MM推定）
    if len(digits) == 4:
        # まずHHMM（例: 1806 → 18:06）
        h = int(digits[:2])
        mi = int(digits[2:4])
        if 0 <= h <= 23 and 0 <= mi <= 59:
            return f"{h}:{mi:02d}"
        # 1桁H + 誤読 + MM（例: "8458" → 8が時、58が分、4は誤読）
        h = int(digits[0])
        mi = int(digits[2:4])
        if 0 <= h <= 9 and 0 <= mi <= 59:
            return f"{h}:{mi:02d}"

    # 5桁: HH + 誤読 + MM（例: "19117" → 19:17、"18229" → 18:29）
    if len(digits) == 5:
        h = int(digits[:2])
        mi = int(digits[3:5])
        if 0 <= h <= 23 and 0 <= mi <= 59:
            return f"{h}:{mi:02d}"

    return ""


def group_by_rows(items: list[dict], threshold: float = 0.020) -> list[list[dict]]:
    """Y座標が近いアイテムを同じ行としてグルーピング"""
    if not items:
        return []

    sorted_items = sorted(items, key=lambda x: (x['y'], x['x']))
    rows = []
    current_row = [sorted_items[0]]

    for item in sorted_items[1:]:
        if abs(item['y'] - current_row[-1]['y']) < threshold:
            current_row.append(item)
        else:
            rows.append(sorted(current_row, key=lambda x: x['x']))
            current_row = [item]

    if current_row:
        rows.append(sorted(current_row, key=lambda x: x['x']))

    return rows


def detect_card_type(ocr_text: str) -> str:
    """OCRテキストから前半/後半カードを判定"""
    if '前半' in ocr_text or '前' in ocr_text:
        return 'front'
    elif '後半' in ocr_text or '後' in ocr_text:
        return 'back'

    # テキストに含まれる日付の数字で判定
    days = re.findall(r'\b(\d{1,2})\b', ocr_text)
    day_nums = [int(d) for d in days if 1 <= int(d) <= 31]
    if day_nums:
        avg = sum(day_nums) / len(day_nums)
        return 'front' if avg < 16 else 'back'

    return 'front'  # デフォルト


# =============================================================================
# 4. 社員マスター読み込み
# =============================================================================

def load_employee_master(master_path: str) -> list[dict]:
    """
    社員マスター.csvを読み込む（cp932/utf-8-sig自動判定）

    実際のCSVカラム:
      社員コード, 氏名, 雇用区分（月給 / 時給）, 勤怠パターン（A～E）,
      定時時間, 遅刻早退自動計算（ON / OFF）,
      休憩時間設定（12:00-13:00 / 13:00-14:00）,
      有給時間（時給者のみ。1日あたりの時間数
    """
    master_path = Path(master_path)
    if not master_path.exists():
        print(f"⚠ マスターファイルが見つかりません: {master_path}")
        sys.exit(1)

    # エンコーディング自動判定
    content = None
    for enc in ['utf-8-sig', 'cp932', 'utf-8']:
        try:
            with open(master_path, 'r', encoding=enc) as f:
                content = f.read()
            break
        except (UnicodeDecodeError, UnicodeError):
            continue

    if content is None:
        print(f"⚠ マスターファイルの文字コードを判定できません: {master_path}")
        sys.exit(1)

    # NFC正規化（Mac濁点分離対策）
    content = unicodedata.normalize('NFC', content)

    employees = []
    lines = content.strip().split('\n')
    if not lines:
        return employees

    # ヘッダー行を取得（カラム名に括弧や説明が含まれるため、部分一致で対応）
    header = lines[0]
    reader = csv.reader(lines)
    headers = next(reader)

    # カラムインデックスを部分一致で特定
    col_map = {}
    for i, h in enumerate(headers):
        h_clean = h.strip()
        if '社員コード' in h_clean:
            col_map['code'] = i
        elif '氏名' in h_clean:
            col_map['name'] = i
        elif '雇用' in h_clean:
            col_map['salary_type'] = i
        elif 'パターン' in h_clean:
            col_map['pattern'] = i
        elif '定時' in h_clean:
            col_map['regular_time'] = i
        elif '遅刻' in h_clean:
            col_map['late_check'] = i
        elif '休憩' in h_clean:
            col_map['break_time'] = i
        elif '有給' in h_clean:
            col_map['paid_leave_hours'] = i

    for row in reader:
        if not row or not any(cell.strip() for cell in row):
            continue  # 空行スキップ

        def get_col(key):
            idx = col_map.get(key)
            if idx is not None and idx < len(row):
                return row[idx].strip()
            return ''

        # 氏名の全角スペースを除去して統一
        raw_name = unicodedata.normalize('NFC', get_col('name'))
        name_normalized = raw_name.replace('\u3000', '').replace(' ', '')

        # 休憩時間を開始・終了に分割（例: "12:00-13:00"）
        break_time = get_col('break_time')
        break_start = ''
        break_end = ''
        break_match = re.match(r'(\d{1,2}:\d{2})\s*[-～~]\s*(\d{1,2}:\d{2})', break_time)
        if break_match:
            break_start = break_match.group(1)
            break_end = break_match.group(2)

        # 有給時間（「家族のためなし」等の特殊値に対応）
        paid_leave_raw = get_col('paid_leave_hours')
        paid_leave_hours = ''
        if re.match(r'\d{1,2}:\d{2}', paid_leave_raw):
            paid_leave_hours = paid_leave_raw
        # 「家族のためなし」等はそのまま空文字

        emp = {
            'code': get_col('code'),
            'name': raw_name,              # 表示用（全角スペースあり）
            'name_normalized': name_normalized,  # マッチング用（スペースなし）
            'salary_type': get_col('salary_type'),  # 月給 or 時給
            'pattern': get_col('pattern'),
            'late_check': get_col('late_check').upper() == 'ON',
            'break_start': break_start,
            'break_end': break_end,
            'regular_time': get_col('regular_time'),
            'paid_leave_hours': paid_leave_hours,
        }
        employees.append(emp)

    print(f"  マスター読み込み: {len(employees)}名")
    return employees


def match_employee_to_image(image_path: str, employees: list[dict]) -> dict | None:
    """
    画像ファイル名から従業員をマッチング

    ファイル名パターン:
      - 社員コード_氏名_前半.jpg / 社員コード_氏名_後半.jpg
      - 氏名_前半.jpg / 氏名_後半.jpg
    """
    fname = Path(image_path).stem
    fname = unicodedata.normalize('NFC', fname)
    # スペース除去版も用意（マッチング精度向上）
    fname_nospace = fname.replace('\u3000', '').replace(' ', '')

    # まず社員コードで完全マッチを試みる（最優先）
    for emp in employees:
        code = emp['code']
        if code and code != 'なし' and code in fname:
            return emp

    # 次に氏名でマッチ（全角スペースあり/なし両方）
    for emp in employees:
        if emp['name'] and emp['name'] in fname:
            return emp
        if emp['name_normalized'] and emp['name_normalized'] in fname_nospace:
            return emp

    return None


# =============================================================================
# 5. ビジネスルール適用
# =============================================================================

def apply_business_rules(
    records: list[dict],
    employee: dict,
    year: int,
    month: int
) -> list[dict]:
    """
    OCR結果にビジネスルールを適用して最終CSVデータを生成

    ルール:
    1. 定時丸め: 出勤が定時より早い → 定時に置換
    2. 欠勤判定: 月給社員で水曜・日曜以外の無打刻日 → 欠勤
    3. 有給処理: 有給の日は打刻空欄 + 有給=1、パートは有給時間も設定
    """
    regular_time = employee.get('regular_time', '')
    salary_type = employee.get('salary_type', '')
    paid_leave_hours = employee.get('paid_leave_hours', '')
    is_monthly = salary_type == '月給'

    # 日ごとのデータをdict化
    day_data = {}
    for rec in records:
        day_data[rec['day']] = rec

    # 月の全日を処理
    _, days_in_month = monthrange(year, month)
    result = []

    for d in range(1, days_in_month + 1):
        dt = date(year, month, d)
        weekday = dt.weekday()  # 0=月, 2=水, 6=日
        is_wed_or_sun = weekday in (2, 6)  # 水曜=2, 日曜=6

        rec = day_data.get(d, None)

        # --- 有給判定 ---
        is_paid_leave = False
        if rec and re.search(r'有[休給]', rec.get('memo', '')):
            is_paid_leave = True

        if is_paid_leave:
            row = {
                'date': f"{month}月{d}日",
                'clock_in': '',
                'clock_out': '',
                'paid_leave': '1',
                'absence': '',
                'paid_leave_hours': paid_leave_hours if salary_type == '時給' else '',
            }
            result.append(row)
            continue

        # --- 出勤データあり ---
        if rec and (rec['clock_in'] or rec['clock_out']):
            clock_in = rec['clock_in']
            clock_out = rec['clock_out']

            # 定時丸め
            if clock_in and regular_time:
                clock_in = apply_regular_time_rounding(clock_in, regular_time)

            # 特殊ケース: 松井嘉子（出勤打刻なし → 定時固定）
            if not clock_in and clock_out and regular_time:
                clock_in = regular_time

            row = {
                'date': f"{month}月{d}日",
                'clock_in': clock_in,
                'clock_out': clock_out,
                'paid_leave': '',
                'absence': '',
                'paid_leave_hours': '',
            }
            result.append(row)
            continue

        # --- 出勤データなし ---
        if is_monthly:
            # 月給社員: 水・日以外は欠勤
            if not is_wed_or_sun:
                row = {
                    'date': f"{month}月{d}日",
                    'clock_in': '',
                    'clock_out': '',
                    'paid_leave': '',
                    'absence': '1',
                    'paid_leave_hours': '',
                }
                result.append(row)
        # 時給パート: 未出勤日は行を作らない

    return result


def apply_regular_time_rounding(clock_in: str, regular_time: str) -> str:
    """定時丸め: 出勤が定時より早い場合は定時に置換"""
    try:
        ci = time_to_minutes(clock_in)
        rt = time_to_minutes(regular_time)
        if ci < rt:
            return regular_time
        return clock_in
    except ValueError:
        return clock_in


def time_to_minutes(time_str: str) -> int:
    """H:MM または HH:MM を分に変換"""
    parts = time_str.split(':')
    if len(parts) == 2:
        return int(parts[0]) * 60 + int(parts[1])
    raise ValueError(f"Invalid time: {time_str}")


# =============================================================================
# 6. CSV出力
# =============================================================================

def write_csv(
    data: list[dict],
    employee: dict,
    output_dir: str,
    year_month: str
):
    """従業員ごとのCSVファイルを出力（BOM付きUTF-8）"""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    code = employee['code']
    # CSV出力用の名前（全角スペースなし）
    name = employee.get('name_normalized', employee['name'])
    if code and code != 'なし':
        filename = f"{code}_{name}.csv"
    else:
        filename = f"{name}.csv"

    filepath = output_path / filename

    with open(filepath, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['日付', '出勤時間', '退出時間', '有給', '欠勤', '有給時間'])
        for row in data:
            writer.writerow([
                row['date'],
                row['clock_in'],
                row['clock_out'],
                row['paid_leave'],
                row['absence'],
                row['paid_leave_hours'],
            ])

    print(f"  ✅ 出力: {filepath}")
    return str(filepath)


# =============================================================================
# 7. メイン処理
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='タイムカード画像 → CSV 全自動変換'
    )
    parser.add_argument('image_dir', help='タイムカード画像フォルダ')
    parser.add_argument('year_month', help='対象年月 (YYYYMM)')
    parser.add_argument('--master', default='./社員マスター.csv',
                        help='社員マスターCSVのパス (default: ./社員マスター.csv)')
    parser.add_argument('--output', default=None,
                        help='CSV出力フォルダ (default: ./<YYYYMM>)')

    args = parser.parse_args()

    # 年月パース
    try:
        year = int(args.year_month[:4])
        month = int(args.year_month[4:6])
    except (ValueError, IndexError):
        print("⚠ 年月の形式が不正です。YYYYMM形式で指定してください。")
        sys.exit(1)

    output_dir = args.output or f"./{args.year_month}"

    print(f"=== タイムカード → CSV 変換 ===")
    print(f"  対象年月: {year}年{month}月")
    print(f"  画像フォルダ: {args.image_dir}")
    print(f"  マスター: {args.master}")
    print(f"  出力先: {output_dir}")
    print()

    # Step 1: 社員マスター読み込み
    print("[1/5] 社員マスター読み込み...")
    employees = load_employee_master(args.master)
    print()

    # Step 2: HEIC → JPG 変換
    print("[2/5] 画像変換 (HEIC → JPG)...")
    image_files = convert_heic_to_jpg(args.image_dir)
    print(f"  画像ファイル: {len(image_files)}枚")
    print()

    # Step 3: 従業員ごとに画像をグルーピング
    print("[3/5] 画像と従業員のマッチング...")
    emp_images: dict[str, list[str]] = {}  # name -> [image_paths]
    unmatched = []

    for img in image_files:
        emp = match_employee_to_image(img, employees)
        if emp:
            key = emp['name']
            if key not in emp_images:
                emp_images[key] = []
            emp_images[key].append(img)
            print(f"  {Path(img).name} → {emp['name']}")
        else:
            unmatched.append(img)
            print(f"  ⚠ マッチなし: {Path(img).name}")
    print()

    if unmatched:
        print(f"  ⚠ マッチできなかった画像: {len(unmatched)}枚")
        for u in unmatched:
            print(f"    - {Path(u).name}")
        print()

    # Step 4: OCR → パース → ルール適用
    print("[4/5] OCR処理 & ビジネスルール適用...")
    results = {}

    for emp in employees:
        name = emp['name']
        if name not in emp_images:
            continue

        print(f"\n  --- {name} ({emp['code']}) ---")
        all_records = []

        for img_path in sorted(emp_images[name]):
            print(f"    OCR: {Path(img_path).name}...")
            ocr_text = ocr_image_apple_vision(img_path)

            if not ocr_text:
                print(f"    ⚠ OCR結果なし")
                continue

            card_type = detect_card_type(ocr_text)
            print(f"    カード種別: {'前半' if card_type == 'front' else '後半'}")

            records = parse_timecard_ocr(ocr_text, card_type)
            print(f"    抽出レコード: {len(records)}件")
            all_records.extend(records)

        if all_records:
            # ビジネスルール適用
            final_data = apply_business_rules(all_records, emp, year, month)
            results[name] = (emp, final_data)
            print(f"    最終レコード: {len(final_data)}件")
    print()

    # Step 5: CSV出力
    print("[5/5] CSV出力...")
    for name, (emp, data) in results.items():
        if data:
            write_csv(data, emp, output_dir, args.year_month)

    print()
    print(f"=== 完了: {len(results)}名分のCSVを出力しました ===")


if __name__ == '__main__':
    main()
