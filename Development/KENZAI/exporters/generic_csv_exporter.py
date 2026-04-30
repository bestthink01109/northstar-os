"""
generic_csv_exporter.py
税理士用 汎用CSVエクスポーター。

福岡プラント機工など、給与らくだ以外の給与計算ソフトを使用する会社向け。
税理士が手入力しやすいフォーマットで出力する。

出力項目:
  社員コード, 社員氏名, 対象年月,
  勤務日数, 欠勤日数, 有給日数, 有給時間,
  総勤務時間, 所定内勤務時間, 法定内残業（延長）時間, 法定外残業時間,
  休日出勤時間, 遅刻早退時間, 深夜時間,
  備考
"""

import csv
import os


class GenericCSVExporter:
    """税理士用 汎用CSV エクスポーター"""

    HEADERS = [
        "社員コード",
        "社員氏名",
        "対象年月",
        "勤務日数",
        "欠勤日数",
        "有給日数",
        "有給時間",
        "総勤務時間",
        "所定内勤務時間",
        "法定内残業時間（延長）",
        "法定外残業時間",
        "休日出勤時間",
        "遅刻早退時間",
        "深夜残業時間",
        "備考",
    ]

    def __init__(self, encoding='cp932'):
        self.encoding = encoding

    def _fmt(self, val):
        """数値フォーマット: 0 → 空文字、整数なら小数点なし"""
        if val is None or val == 0 or val == 0.0:
            return ""
        v = float(val)
        return str(int(v)) if v == int(v) else str(v)

    def _fmt_z(self, val):
        """数値フォーマット: 0 → "0" として出力"""
        if val is None:
            return "0"
        v = float(val)
        return str(int(v)) if v == int(v) else str(v)

    def export(self, records, output_path, year, month):
        """
        CSVをエクスポートする。

        Args:
            records: list of (employee_code, employee_name, monthly_summary)
            output_path: 出力ファイルパス
            year, month: 対象年月
        """
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        date_str = f"{year}年{month}月"

        rows = []
        for emp_code, emp_name, monthly in records:
            # 所定内勤務時間 = 総勤務時間 - 延長 - 法定外残業
            total_work = monthly.get('total_work', 0)
            ot_in = monthly.get('total_ot_in', 0)
            ot_out = monthly.get('total_ot_out', 0)
            scheduled_work = round(total_work - ot_in - ot_out, 1)
            if scheduled_work < 0:
                scheduled_work = 0

            row = [
                str(emp_code),                                        # 社員コード
                emp_name,                                             # 社員氏名
                date_str,                                             # 対象年月
                self._fmt_z(monthly.get('attend_days', 0)),           # 勤務日数
                self._fmt(monthly.get('absent_days', 0)),             # 欠勤日数
                self._fmt(monthly.get('paid_days', 0)),               # 有給日数
                self._fmt(monthly.get('paid_hours', 0)),              # 有給時間
                self._fmt_z(total_work),                              # 総勤務時間
                self._fmt_z(scheduled_work),                          # 所定内勤務時間
                self._fmt_z(ot_in),                                   # 法定内残業時間（延長）
                self._fmt_z(ot_out),                                  # 法定外残業時間
                self._fmt(monthly.get('total_holiday_w', 0)),         # 休日出勤時間
                self._fmt(monthly.get('total_absence', 0)),           # 遅刻早退時間
                self._fmt(monthly.get('total_night', 0)),             # 深夜残業時間
                "",                                                    # 備考
            ]
            rows.append(row)

        # 社員コード順でソート
        rows.sort(key=lambda r: int(r[0]) if r[0].isdigit() else 9999)

        with open(output_path, 'w', encoding=self.encoding, errors='replace', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(self.HEADERS)
            writer.writerows(rows)

        print(f"[CSV出力] 完了: {output_path} ({len(rows)}名分)")
        return output_path
