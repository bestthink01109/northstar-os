"""
rakuda_csv_exporter.py
給与らくだ インポートCSV エクスポーター。
現行 export_rakuda_csv.py のロジックを移植・汎用化。
"""

import csv
import os


class RakudaCSVExporter:
    """給与らくだ インポートCSV を生成する（21列、cp932エンコード）。"""

    # kintai6.csv 完全準拠のヘッダー21列
    HEADERS = [
        "社員コード", "社員氏名", "タイムカード年月", "勤務日数", "欠勤日数",
        "有給日数", "勤務時間", "残業時間", "深夜残業時間", "早出時間",
        "延長時間", "休日出勤時間1", "休日残業時間1", "休日深夜残業時間1",
        "休日出勤時間2", "休日残業時間2", "休日深夜残業時間2", "45-60時間残業",
        "60越残業時間", "遅刻早退時間", "有給時間"
    ]

    def __init__(self, encoding='cp932'):
        self.encoding = encoding

    def export(self, records, output_path, year, month):
        """
        Args:
            records: list of (employee_code, employee_name, monthly_summary)
            output_path: 出力先ファイルパス
            year, month: 対象年月
        """
        csv_data = []

        for emp_code, emp_name, monthly in records:
            row = self._format_row(emp_code, emp_name, monthly, year, month)
            csv_data.append(row)

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, 'w', encoding=self.encoding, errors='replace', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(self.HEADERS)
            writer.writerows(csv_data)

        print(f"[CSV出力] 完了: {output_path} ({len(csv_data)}名分)")
        return output_path

    def _format_row(self, code, name, monthly, year, month):
        """1社員分のCSV行を生成する。"""

        def fmt(val):
            if val == 0 or val == 0.0:
                return ""
            v = float(val)
            return str(int(v)) if v.is_integer() else str(v)

        def fmt_z(val):
            if val == 0 or val == 0.0:
                return "0"
            v = float(val)
            return str(int(v)) if v.is_integer() else str(v)

        row = [
            str(code),                                      # 社員コード
            name,                                           # 社員氏名
            f"{year}/{month}/1",                            # タイムカード年月
            fmt_z(monthly['attend_days']),                   # 勤務日数
            "",                                             # 欠勤日数
            fmt_z(monthly['paid_days']),                     # 有給日数
            fmt_z(monthly['total_work']),                    # 勤務時間
            "",                                             # 残業時間（下で処理）
            "",                                             # 深夜残業時間
            "",                                             # 早出時間
            fmt_z(monthly['total_ot_in']),                   # 延長時間
            "",                                             # 休日出勤時間1
            "",                                             # 休日残業時間1
            "",                                             # 休日深夜残業時間1
            fmt_z(monthly.get('total_holiday_w', 0)),        # 休日出勤時間2
            "",                                             # 休日残業時間2
            "",                                             # 休日深夜残業2
            "",                                             # 45-60時間残業
            "0",                                            # 60越残業時間
            fmt_z(monthly['total_absence']),                 # 遅刻早退時間
            "0"                                             # 有給時間
        ]

        # 残業時間のフォーマット（kintai6互換）
        ot_out_str = fmt(monthly['total_ot_out'])
        if ot_out_str == "":
            row[7] = "0" if monthly['attend_days'] > 0 and monthly['total_ot_out'] == 0 else ""
        else:
            row[7] = ot_out_str

        return row
