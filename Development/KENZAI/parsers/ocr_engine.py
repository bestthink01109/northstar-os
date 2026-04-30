"""
ocr_engine.py
Mac Vision Framework + フォールバック（Claude/Gemini API）によるOCRエンジン。

優先順位:
  1. Mac Vision Framework（pyobjc-framework-Vision）← ローカル処理、高速、無料
  2. Claude API（anthropic）← フォールバック1
  3. Gemini API（google-generativeai）← フォールバック2

株式会社純青の手書き出勤簿（自社フォーマット）のOCRに使用。
"""

import os
import sys
import json
import base64
from typing import Optional, Dict, List, Any


class OCREngine:
    """
    マルチバックエンドOCRエンジン。
    Mac Vision → Claude → Gemini の優先順位でフォールバックする。
    """

    def __init__(self, preferred_backend: str = 'auto'):
        """
        Args:
            preferred_backend: 'mac_vision', 'claude', 'gemini', 'auto'
                               'auto' の場合は利用可能なバックエンドを優先順に試行
        """
        self.preferred_backend = preferred_backend
        self._backends = {}
        self._detect_backends()

    def _detect_backends(self):
        """利用可能なバックエンドを検出する。"""
        # 1. Mac Vision Framework
        try:
            import Vision
            import Quartz
            self._backends['mac_vision'] = True
            print("[OCR] Mac Vision Framework: 利用可能")
        except ImportError:
            self._backends['mac_vision'] = False
            print("[OCR] Mac Vision Framework: 未インストール（pyobjc-framework-Vision が必要）")

        # 2. Claude API (Anthropic)
        try:
            import anthropic
            api_key = os.environ.get('ANTHROPIC_API_KEY', '')
            if api_key:
                self._backends['claude'] = True
                print("[OCR] Claude API: 利用可能")
            else:
                self._backends['claude'] = False
                print("[OCR] Claude API: APIキー未設定（ANTHROPIC_API_KEY）")
        except ImportError:
            self._backends['claude'] = False
            print("[OCR] Claude API: 未インストール（anthropic パッケージが必要）")

        # 3. Gemini API
        try:
            import google.generativeai as genai
            api_key = os.environ.get('GOOGLE_API_KEY', '') or os.environ.get('GEMINI_API_KEY', '')
            if api_key:
                self._backends['gemini'] = True
                print("[OCR] Gemini API: 利用可能")
            else:
                self._backends['gemini'] = False
                print("[OCR] Gemini API: APIキー未設定（GOOGLE_API_KEY or GEMINI_API_KEY）")
        except ImportError:
            self._backends['gemini'] = False
            print("[OCR] Gemini API: 未インストール（google-generativeai パッケージが必要）")

    def get_available_backends(self) -> List[str]:
        """利用可能なバックエンドのリストを返す。"""
        return [k for k, v in self._backends.items() if v]

    def recognize(self, image_path: str, language: str = 'ja',
                  expected_format: Optional[str] = None) -> Dict[str, Any]:
        """
        画像からテキストを認識する。

        Args:
            image_path: 画像ファイルパス（.jpg, .png, .heic等）
            language: 認識言語（'ja' = 日本語）
            expected_format: 期待するデータ構造の説明（プロンプト用）
                             例: '出勤簿: 日付, 出勤時刻, 退勤時刻, 有給, 外勤'

        Returns:
            {
                'backend': 使用したバックエンド名,
                'raw_text': 認識された生テキスト,
                'structured': 構造化されたデータ（期待フォーマット指定時）,
                'confidence': 信頼度（0.0〜1.0、取得可能な場合）,
            }
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"画像ファイルが見つかりません: {image_path}")

        # 優先順位の決定
        if self.preferred_backend != 'auto' and self._backends.get(self.preferred_backend):
            order = [self.preferred_backend]
        else:
            order = ['mac_vision', 'claude', 'gemini']

        for backend in order:
            if not self._backends.get(backend):
                continue
            try:
                if backend == 'mac_vision':
                    return self._ocr_mac_vision(image_path, language)
                elif backend == 'claude':
                    return self._ocr_claude(image_path, language, expected_format)
                elif backend == 'gemini':
                    return self._ocr_gemini(image_path, language, expected_format)
            except Exception as e:
                print(f"[OCR] {backend} でエラー発生: {e}、次のバックエンドを試行...")
                continue

        raise RuntimeError("利用可能なOCRバックエンドがありません。"
                           "pyobjc-framework-Vision のインストールか、"
                           "ANTHROPIC_API_KEY / GOOGLE_API_KEY の設定が必要です。")

    # ─── Mac Vision Framework ───

    def _ocr_mac_vision(self, image_path: str, language: str) -> Dict[str, Any]:
        """macOS Vision Frameworkを使用したOCR。"""
        import Vision
        import Quartz

        # 画像の読み込み
        image_url = Quartz.CFURLCreateWithFileSystemPath(
            None, image_path, Quartz.kCFURLPOSIXPathStyle, False
        )
        image_source = Quartz.CGImageSourceCreateWithURL(image_url, None)
        if image_source is None:
            raise ValueError(f"画像を読み込めません: {image_path}")

        cg_image = Quartz.CGImageSourceCreateImageAtIndex(image_source, 0, None)
        if cg_image is None:
            raise ValueError(f"CGImageの生成に失敗: {image_path}")

        # テキスト認識リクエストの作成
        request = Vision.VNRecognizeTextRequest.alloc().init()

        # 言語設定
        if language == 'ja':
            request.setRecognitionLanguages_(['ja-JP', 'en-US'])
        else:
            request.setRecognitionLanguages_([language, 'en-US'])

        # 認識レベル: accurate（精度優先）
        request.setRecognitionLevel_(Vision.VNRequestTextRecognitionLevelAccurate)
        request.setUsesLanguageCorrection_(True)

        # リクエストの実行
        handler = Vision.VNImageRequestHandler.alloc().initWithCGImage_options_(
            cg_image, None
        )
        success = handler.performRequests_error_([request], None)

        if not success[0]:
            raise RuntimeError(f"Vision Framework OCR失敗: {success[1]}")

        # 結果の取得
        results = request.results()
        lines = []
        total_confidence = 0.0
        count = 0

        for observation in results:
            candidate = observation.topCandidates_(1)[0]
            text = candidate.string()
            confidence = candidate.confidence()
            lines.append(text)
            total_confidence += confidence
            count += 1

        raw_text = '\n'.join(lines)
        avg_confidence = total_confidence / count if count > 0 else 0.0

        return {
            'backend': 'mac_vision',
            'raw_text': raw_text,
            'structured': None,
            'confidence': round(avg_confidence, 3),
            'line_count': count,
        }

    # ─── Claude API ───

    def _ocr_claude(self, image_path: str, language: str,
                    expected_format: Optional[str] = None) -> Dict[str, Any]:
        """Claude APIを使用したOCR（構造化データ抽出に強い）。"""
        import anthropic

        # 画像をbase64エンコード
        with open(image_path, 'rb') as f:
            image_data = base64.standard_b64encode(f.read()).decode('utf-8')

        # MIMEタイプの判定
        ext = os.path.splitext(image_path)[1].lower()
        mime_map = {
            '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
            '.png': 'image/png', '.gif': 'image/gif',
            '.webp': 'image/webp', '.heic': 'image/heic',
        }
        media_type = mime_map.get(ext, 'image/jpeg')

        # プロンプト構築
        prompt = "この画像に記載されているテキストを正確に読み取り、全文をそのまま出力してください。\n"
        prompt += "手書き文字も可能な限り正確に読み取ってください。\n"

        if expected_format:
            prompt += f"\n期待するデータ構造:\n{expected_format}\n"
            prompt += "\n上記の構造に合わせて、JSON形式でも出力してください。\n"
            prompt += "JSONは ```json ``` ブロックに入れてください。\n"

        client = anthropic.Anthropic()
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": image_data,
                            },
                        },
                        {
                            "type": "text",
                            "text": prompt,
                        },
                    ],
                }
            ],
        )

        raw_text = message.content[0].text

        # JSON部分の抽出
        structured = None
        if '```json' in raw_text:
            try:
                json_str = raw_text.split('```json')[1].split('```')[0].strip()
                structured = json.loads(json_str)
            except (IndexError, json.JSONDecodeError):
                pass

        return {
            'backend': 'claude',
            'raw_text': raw_text,
            'structured': structured,
            'confidence': None,
        }

    # ─── Gemini API ───

    def _ocr_gemini(self, image_path: str, language: str,
                    expected_format: Optional[str] = None) -> Dict[str, Any]:
        """Gemini APIを使用したOCR。"""
        import google.generativeai as genai
        from pathlib import Path

        api_key = os.environ.get('GOOGLE_API_KEY') or os.environ.get('GEMINI_API_KEY')
        genai.configure(api_key=api_key)

        # 画像の読み込み
        with open(image_path, 'rb') as f:
            image_data = f.read()

        ext = os.path.splitext(image_path)[1].lower()
        mime_map = {
            '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
            '.png': 'image/png', '.gif': 'image/gif',
            '.webp': 'image/webp', '.heic': 'image/heic',
        }
        mime_type = mime_map.get(ext, 'image/jpeg')

        # プロンプト構築
        prompt = "この画像に記載されているテキストを正確に読み取り、全文をそのまま出力してください。\n"
        prompt += "手書き文字も可能な限り正確に読み取ってください。\n"

        if expected_format:
            prompt += f"\n期待するデータ構造:\n{expected_format}\n"
            prompt += "\n上記の構造に合わせて、JSON形式でも出力してください。\n"
            prompt += "JSONは ```json ``` ブロックに入れてください。\n"

        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content([
            prompt,
            {"mime_type": mime_type, "data": image_data},
        ])

        raw_text = response.text

        # JSON部分の抽出
        structured = None
        if '```json' in raw_text:
            try:
                json_str = raw_text.split('```json')[1].split('```')[0].strip()
                structured = json.loads(json_str)
            except (IndexError, json.JSONDecodeError):
                pass

        return {
            'backend': 'gemini',
            'raw_text': raw_text,
            'structured': structured,
            'confidence': None,
        }


# ─── テスト用 ───

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("使用方法: python ocr_engine.py <画像ファイルパス> [expected_format]")
        sys.exit(1)

    image_path = sys.argv[1]
    expected_format = sys.argv[2] if len(sys.argv) > 2 else None

    engine = OCREngine()
    print(f"\n利用可能なバックエンド: {engine.get_available_backends()}")
    print(f"認識中: {image_path}")
    print("=" * 60)

    result = engine.recognize(image_path, expected_format=expected_format)
    print(f"使用バックエンド: {result['backend']}")
    if result['confidence'] is not None:
        print(f"信頼度: {result['confidence']}")
    print(f"\n--- 認識結果 ---\n{result['raw_text']}")
    if result['structured']:
        print(f"\n--- 構造化データ ---\n{json.dumps(result['structured'], ensure_ascii=False, indent=2)}")
