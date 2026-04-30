"""
validation.py
計算値とExcel記載値の差異を検出してレポート生成する。
"""


class ValidationReport:
    """計算値とExcel記載値の差異を検出してレポート生成する。"""

    def validate(self, sheet_name, days, calc_results, monthly, excel_summary):
        """
        日次・月次の計算値とExcel記載値を突合し、差異リストを返す。

        Args:
            sheet_name: シート名（社員名）
            days: DayRecordのリスト
            calc_results: list of (day_rec, calc)
            monthly: 月次集計結果（dict）
            excel_summary: Excelの集計値（dict）

        Returns:
            list of str: 差異メッセージのリスト
        """
        issues = []

        for day_rec, calc in calc_results:
            # dict/dataclass 両対応
            d = day_rec['day'] if isinstance(day_rec, dict) else day_rec.day
            wd = day_rec['weekday'] if isinstance(day_rec, dict) else day_rec.weekday

            calc_work = calc['work'] if isinstance(calc, dict) else calc.work
            calc_ot_in = calc['ot_in'] if isinstance(calc, dict) else calc.ot_in
            calc_ot_out = calc['ot_out'] if isinstance(calc, dict) else calc.ot_out
            calc_absence = calc['absence'] if isinstance(calc, dict) else calc.absence

            excel_work = day_rec['excel_work'] if isinstance(day_rec, dict) else day_rec.excel_work
            excel_ot_in = day_rec['excel_ot_in'] if isinstance(day_rec, dict) else day_rec.excel_ot_in
            excel_ot_out = day_rec['excel_ot_out'] if isinstance(day_rec, dict) else day_rec.excel_ot_out
            excel_absence = day_rec['excel_absence'] if isinstance(day_rec, dict) else day_rec.excel_absence

            # 日次の差異チェック（0.1h以上の差異を警告）
            w_diff = abs(calc_work - excel_work)
            oi_diff = abs(calc_ot_in - excel_ot_in)
            oo_diff = abs(calc_ot_out - excel_ot_out)
            ab_diff = abs(calc_absence - excel_absence)

            if w_diff > 0.1:
                issues.append(f"  {d}日({wd}) 勤務: 計算{calc_work:.1f}h vs Excel{excel_work:.1f}h")
            if oi_diff > 0.1:
                issues.append(f"  {d}日({wd}) 所内(法定内残業): 計算{calc_ot_in:.1f}h vs Excel{excel_ot_in:.1f}h")
            if oo_diff > 0.1:
                issues.append(f"  {d}日({wd}) 法定外残業: 計算{calc_ot_out:.1f}h vs Excel{excel_ot_out:.1f}h")
            if ab_diff > 0.1:
                issues.append(f"  {d}日({wd}) 欠勤: 計算{calc_absence:.1f}h vs Excel{excel_absence:.1f}h")

        # 月次集計との突合
        if isinstance(excel_summary, dict):
            w_sum_diff = abs(monthly['total_work'] - excel_summary.get('total_work', 0))
            oi_sum_diff = abs(monthly['total_ot_in'] - excel_summary.get('total_ot_in', 0))
            oo_sum_diff = abs(monthly['total_ot_out'] - excel_summary.get('total_ot_out', 0))

            if w_sum_diff > 0.1:
                issues.append(f"  [集計] 勤務合計: {monthly['total_work']}h vs Excel{excel_summary.get('total_work', 0)}h")
            if oi_sum_diff > 0.1:
                issues.append(f"  [集計] 所内合計: {monthly['total_ot_in']}h vs Excel{excel_summary.get('total_ot_in', 0)}h")
            if oo_sum_diff > 0.1:
                issues.append(f"  [集計] 法定外残業合計: {monthly['total_ot_out']}h vs Excel{excel_summary.get('total_ot_out', 0)}h")

        return issues
