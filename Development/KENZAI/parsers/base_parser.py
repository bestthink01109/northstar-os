"""
base_parser.py
InputParser 抽象基底クラス。
全てのパーサー（Excel / OCR / PDF）はこのクラスを継承し、
共通の DayRecord 形式でデータを出力する。
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base_config import CompanyConfig


class InputParser(ABC):
    """
    入力データパーサーの抽象基底クラス。
    各サブクラスは parse() メソッドを実装し、
    社員ごとの月次データ（dict形式）を返す。
    """

    def __init__(self, config: CompanyConfig):
        self.config = config

    @abstractmethod
    def parse(self, source_path: str, employee_master: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        入力データを読み取り、社員ごとの月次データを返す。

        Args:
            source_path: 入力ファイルのパス（Excel / 画像フォルダ / PDFファイル）
            employee_master: 社員マスター辞書

        Returns:
            list of dict: 各社員のデータ
            [
                {
                    'sheet_name': str,       # ExcelParser用（社員識別子）
                    'year': int,
                    'month': int,
                    'hirano': bool,          # 後方互換（is_special に置換予定）
                    'is_special': bool,      # 特例社員フラグ
                    'days': [DayRecord or dict, ...],
                    'summary_excel': {...},  # ExcelParser のみ（検証用）
                },
                ...
            ]
        """
        pass
