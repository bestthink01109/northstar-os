"""
employee_master.py
平野工業 社員コードマスター（2026年2月時点）
companies/hirano/ 配下へ移植。
"""

import csv
import os

# CSVから動的に社員マスターを読み込む
EMPLOYEE_MASTER = {}

csv_path = os.path.join(os.path.dirname(__file__), 'employees.csv')
if os.path.exists(csv_path):
    with open(csv_path, 'r', encoding='utf-8-sig', errors='replace') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # 1列目(シート名/表示名)をキーにする
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

# 平野珠美のみ1日8h所定（その他は7h/5h）
# ※ 特例判定は CompanyConfig.is_special_employee() に移行済み
#    ただし後方互換のため関数も残す
HIRANO_TAMAMI_SHEET = '平野珠美'


def get_employee_code(sheet_name):
    """シート名から社員コードを返す。未登録はNone。"""
    emp = EMPLOYEE_MASTER.get(sheet_name)
    return emp['code'] if emp else None


def is_hirano_tamami(sheet_name):
    """平野珠美かどうか判定（特別の勤務体系を適用するため）"""
    return sheet_name == HIRANO_TAMAMI_SHEET
