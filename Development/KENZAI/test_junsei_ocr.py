#!/usr/bin/env python3
"""
test_junsei_ocr.py
純青OCRパイプライン動作テストスクリプト。

使用方法:
    # PDF1枚でテスト
    python3 test_junsei_ocr.py --pdf /path/to/出勤簿.pdf

    # 入力フォルダ全体でテスト
    python3 test_junsei_ocr.py --folder /path/to/folder

    # バックエンド指定テスト（mac_vision / claude / gemini）
    python3 test_junsei_ocr.py --pdf /path/to/出勤簿.pdf --backend mac_vision
"""

import sys
import os
import argparse
import json

# パス設定
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from junsei.config import create_junsei_config
from junsei.employee_master import EMPLOYEE_MASTER
from parsers.pdf_parser import PDFParser
from parsers.ocr_engine import OCREngine


def test_ocr_backends():
    """利用可能なOCRバックエンドを確認する。"""
    print("=" * 60)
    print("OCRバックエンド確認")
    print("=" * 60)
    engine = OCREngine()
    available = engine.get_available_backends()
    print(f"利用可能: {available}")
    if not available:
        print("⚠️  利用可能なOCRバックエンドがありません。")
        print("   以下を確認してください:")
        print("   - pyobjc-framework-Vision (Mac Vision)")
        print("   - ANTHROPIC_API_KEY 環境変数 (Claude)")
        print("   - GOOGLE_API_KEY or GEMINI_API_KEY 環境変数 (Gemini)")
        return False
    return True


def test_pdf_to_image(pdf_path: str):
    """PDF→画像変換テスト。"""
    print("\n" + "=" * 60)
    print(f"PDF→画像変換テスト: {os.path.basename(pdf_path)}")
    print("=" * 60)

    import fitz
    import tempfile

    doc = fitz.open(pdf_path)
    print(f"ページ数: {doc.page_count}")

    temp_dir = tempfile.mkdtemp(prefix='junsei_test_')
    images = []
    for page_num in range(doc.page_count):
        page = doc[page_num]
        mat = fitz.Matrix(300 / 72, 300 / 72)
        pix = page.get_pixmap(matrix=mat)
        img_path = os.path.join(temp_dir, f'page_{page_num + 1:03d}.png')
        pix.save(img_path)
        images.append(img_path)
        print(f"  ページ {page_num + 1}: {img_path} ({pix.width}x{pix.height}px)")

    doc.close()
    print(f"✅ PDF→画像変換完了: {len(images)}枚")
    return images, temp_dir


def test_ocr_single_page(image_path: str, backend: str = 'auto'):
    """1ページのOCRテスト。"""
    print("\n" + "=" * 60)
    print(f"OCRテスト: {os.path.basename(image_path)}")
    print("=" * 60)

    from parsers.pdf_parser import JUNSEI_EXPECTED_FORMAT
    engine = OCREngine(preferred_backend=backend)
    result = engine.recognize(image_path, language='ja', expected_format=JUNSEI_EXPECTED_FORMAT)

    print(f"使用バックエンド: {result['backend']}")
    if result.get('confidence') is not None:
        print(f"信頼度: {result['confidence']}")

    print("\n--- 生テキスト（先頭500文字）---")
    print(result['raw_text'][:500])

    if result.get('structured'):
        print("\n--- 構造化データ ---")
        print(json.dumps(result['structured'], ensure_ascii=False, indent=2)[:2000])
    else:
        print("\n⚠️  構造化データの抽出失敗（生テキストのみ）")

    return result


def test_full_pipeline(pdf_path: str, backend: str = 'auto'):
    """PDFパーサー全体のパイプラインテスト。"""
    print("\n" + "=" * 60)
    print(f"パイプライン全体テスト: {os.path.basename(pdf_path)}")
    print("=" * 60)

    config = create_junsei_config()
    print(f"会社: {config.company_name} (input_type: {config.input_type})")
    print(f"社員マスター: {len(EMPLOYEE_MASTER)}名")
    for name, info in EMPLOYEE_MASTER.items():
        print(f"  - {name} (コード:{info['code']})")

    parser = PDFParser(config, ocr_backend=backend)
    print(f"\nPDF変換方式: {parser._pdf_converter}")

    # PDFファイルを直接解析
    all_data = parser.parse(pdf_path, EMPLOYEE_MASTER)

    if not all_data:
        print("\n⚠️  データが取得できませんでした。")
        print("   考えられる原因:")
        print("   1. OCRが失敗している（バックエンドAPIキーを確認）")
        print("   2. 社員名がマスターと一致していない")
        print("   3. 出勤簿フォーマットがOCRプロンプトと合っていない")
        return

    print(f"\n✅ {len(all_data)}名分のデータを取得")
    for sheet in all_data:
        name = sheet['sheet_name']
        year = sheet['year']
        month = sheet['month']
        days = sheet['days']
        attend = sum(1 for d in days if d.get('t_start') is not None)
        paid = sum(1 for d in days if d.get('is_paid', False))
        field = sum(1 for d in days if d.get('field_work', False))
        print(f"\n  [{name}] {year}年{month}月")
        print(f"    出勤日数: {attend}日")
        print(f"    有給日数: {paid}日")
        print(f"    外勤日数: {field}日")

        print(f"    --- 日次データ（先頭10日）---")
        for day_rec in days[:10]:
            t_s = day_rec.get('t_start')
            t_e = day_rec.get('t_end')
            start_str = f"{int(t_s)}:{int((t_s % 1) * 60):02d}" if t_s else "-"
            end_str = f"{int(t_e)}:{int((t_e % 1) * 60):02d}" if t_e else "-"
            flags = []
            if day_rec.get('is_paid'):
                flags.append('有給')
            if day_rec.get('field_work'):
                flags.append('外勤')
            flag_str = ' ' + ' '.join(flags) if flags else ''
            print(f"    {day_rec['day']:2d}日({day_rec['weekday']}) {start_str}〜{end_str}{flag_str}")


def main():
    parser = argparse.ArgumentParser(description='純青OCRパイプライン動作テスト')
    parser.add_argument('--pdf', '-p', help='テスト用PDFファイルパス')
    parser.add_argument('--folder', '-f', help='テスト用フォルダパス（PDF複数）')
    parser.add_argument('--backend', '-b', default='auto',
                        choices=['auto', 'mac_vision', 'claude', 'gemini'],
                        help='OCRバックエンド指定（デフォルト: auto）')
    parser.add_argument('--page-only', action='store_true',
                        help='1ページのOCRのみテスト（変換後の最初のページ）')
    args = parser.parse_args()

    # 1. バックエンド確認
    if not test_ocr_backends():
        sys.exit(1)

    if not args.pdf and not args.folder:
        # PDFが指定されていない場合、入力フォルダを使う
        config = create_junsei_config()
        input_dir = config.input_dir
        print(f"\n入力フォルダ: {input_dir}")
        import glob
        pdfs = glob.glob(os.path.join(input_dir, '*.pdf'))
        if not pdfs:
            print("⚠️  PDFファイルが見つかりません。")
            print(f"   以下のフォルダにPDFを置いてください:")
            print(f"   {input_dir}")
            sys.exit(1)
        args.pdf = pdfs[0]
        print(f"最初のPDF: {args.pdf}")

    target = args.pdf or args.folder

    if args.page_only and args.pdf:
        # PDF→画像変換 + 1ページOCRのみ
        images, temp_dir = test_pdf_to_image(args.pdf)
        if images:
            test_ocr_single_page(images[0], backend=args.backend)
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
    else:
        # フルパイプラインテスト
        test_full_pipeline(target, backend=args.backend)


if __name__ == '__main__':
    main()
