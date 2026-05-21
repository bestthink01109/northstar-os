"""
employee_master.py
株式会社純青 社員コードマスター
employees.csvから動的読み込み。
"""

import csv
import os

# CSVから動的に社員マスターを読み込む
# ※ employees.csvを書き換えるだけで自動反映されます
EMPLOYEE_MASTER = {}

csv_path = os.path.join(os.path.dirname(__file__), 'employees.csv')
if os.path.exists(csv_path):
    with open(csv_path, 'r', encoding='utf-8-sig', errors='replace') as f:
        reader = csv.DictReader(f)
        for row in reader:
            key_name = row.get('シート名', '').strip()
            if not key_name:
                # フォールバック: 1列目をキーにする
                vals = list(row.values())
                key_name = vals[0].strip() if vals else ''
            if not key_name:
                continue
            try:
                code = int(str(row.get('社員コード', '')).strip())
            except ValueError:
                continue
            full_name = str(row.get('正式氏名', '')).strip() or key_name
            # 外勤手当/日（純青固有。未設定は0）
            try:
                field_work_allowance = int(str(row.get('外勤手当/日', '0')).strip() or '0')
            except ValueError:
                field_work_allowance = 0

            EMPLOYEE_MASTER[key_name] = {
                'code': code,
                'name': full_name,
                'field_work_allowance': field_work_allowance,  # 外勤手当/日（円）
            }


def get_employee_code(name):
    """名前から社員コードを返す。未登録はNone。"""
    emp = EMPLOYEE_MASTER.get(name)
    return emp['code'] if emp else None


def get_field_work_allowance(name):
    """名前から外勤手当/日（円）を返す。未登録は0。"""
    emp = EMPLOYEE_MASTER.get(name)
    return emp['field_work_allowance'] if emp else 0
