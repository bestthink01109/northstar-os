"""
employee_master.py
株式会社純青 社員コードマスター
BUN_CEOから社員情報の提供を受け次第、追記する。
現時点: 8名（名前・コード未確定）
"""

import csv
import os

# CSVから動的に社員マスターを読み込む
# ※ BUN_CEOから社員名簿を受領後にemployees.csvを書き換えるだけで反映されます
EMPLOYEE_MASTER = {}

csv_path = os.path.join(os.path.dirname(__file__), 'employees.csv')
if os.path.exists(csv_path):
    with open(csv_path, 'r', encoding='utf-8-sig', errors='replace') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # 1列名(シート名/表示名)をキーにする
            key_name = list(row.values())[0].strip()
            # 2列目(社員コード), 3列目(正式氏名)を取得
            vals = list(row.values())
            if len(vals) >= 3 and key_name:
                try:
                    code = int(vals[1].strip())
                except ValueError:
                    continue  # コードが数値でない場合はスキップ
                full_name = vals[2].strip()
                EMPLOYEE_MASTER[key_name] = {'code': code, 'name': full_name}


def get_employee_code(name):
    """名前から社員コードを返す。未登録はNone。"""
    emp = EMPLOYEE_MASTER.get(name)
    return emp['code'] if emp else None
