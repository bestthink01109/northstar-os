"""
monthly_aggregator.py
月次集計エンジン。全日次データを集計して月次サマリーを生成する。

勤務日数・休日出勤時間は、Excelの集計行の値を優先的に使用する。
（現行エンジンとの100%互換を保証するため）
"""


class MonthlyAggregator:
    """全日次データを集計して月次サマリーを生成する。"""

    def aggregate(self, sheet_data, calc_results):
        """
        sheet_data: パーサーの返り値（summary_excel等を含む）
        calc_results: list of (day_rec, calc_dict_or_CalcResult)
        Returns: monthly dict
        """
        total_work = 0.0
        total_ot_in = 0.0
        total_ot_out = 0.0
        total_absence = 0.0
        total_holiday_w = 0.0
        attend_days = 0

        # summary_excelの取得（dict形式とEmployeeMonthData形式の両対応）
        if isinstance(sheet_data, dict):
            summary_excel = sheet_data.get('summary_excel', {})
        else:
            summary_excel = getattr(sheet_data, 'summary_excel', {})

        paid_days = summary_excel.get('paid_leave_days', 0) if isinstance(summary_excel, dict) else 0
        paid_hours = summary_excel.get('paid_leave_hours', 0) if isinstance(summary_excel, dict) else 0

        for day_rec, calc in calc_results:
            # dict形式とdataclass形式の両対応
            work = calc['work'] if isinstance(calc, dict) else calc.work
            ot_in = calc['ot_in'] if isinstance(calc, dict) else calc.ot_in
            ot_out = calc['ot_out'] if isinstance(calc, dict) else calc.ot_out
            absence = calc['absence'] if isinstance(calc, dict) else calc.absence

            total_work += work
            total_ot_in += ot_in
            total_ot_out += ot_out
            total_absence += absence
            if work > 0:
                attend_days += 1

            # 休日出勤時間の集計（Excel記載値から取得）
            if isinstance(day_rec, dict):
                excel_hw = day_rec.get('excel_holiday_w', 0.0)
            else:
                excel_hw = getattr(day_rec, 'excel_holiday_w', 0.0)
            total_holiday_w += excel_hw

        # 勤務日数：Excel集計行に値がある場合はそちらを優先
        # （現行エンジンとの互換性保証のため）
        excel_attend = summary_excel.get('attend_days', 0) if isinstance(summary_excel, dict) else 0
        if excel_attend > 0:
            attend_days = int(excel_attend)

        return {
            'attend_days': attend_days,
            'total_work': round(total_work, 1),
            'total_ot_in': round(total_ot_in, 1),
            'total_ot_out': round(total_ot_out, 1),
            'total_absence': round(total_absence, 1),
            'total_holiday_w': round(total_holiday_w, 1),
            'paid_days': paid_days,
            'paid_hours': paid_hours,
        }
