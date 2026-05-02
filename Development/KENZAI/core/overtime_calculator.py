"""
overtime_calculator.py
日次の残業計算エンジン。
CompanyConfig から勤務体系・休憩時間帯を動的に取得し、
会社に依存しない汎用的な計算を行う。

【BUN_CEO確定ロジック】
実働時間 = 退社時間 - 出社時間 - 休憩時間
※ 時間休は「早退」として既に出退勤時刻に反映されているため、
  実働時間から差し引く処理は行わない。
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.models import DayRecord, CalcResult
from base_config import CompanyConfig


def _round_half(val):
    """0.5h単位で四捨五入（給与計算の慣例）"""
    return round(val * 2) / 2


class OvertimeCalculator:
    """
    日次の実働時間と勤務時間を計算する。
    所内/法定外の振り分けは別途 WeeklyAllocator で行う。
    """

    def __init__(self, config: CompanyConfig):
        self.config = config

    def _calculate_break_hours(self, t_s, t_e, employee_name, is_saturday):
        """出退勤時刻に基づく休憩時間の厳密計算"""
        breaks = self.config.get_break_periods(employee_name, is_saturday)

        break_h = 0.0
        for b_s, b_e in breaks:
            overlap_s = max(t_s, b_s)
            overlap_e = min(t_e, b_e)
            if overlap_e > overlap_s:
                break_h += (overlap_e - overlap_s)
        return break_h

    def calculate_day(self, day_rec: DayRecord, employee_name: str) -> CalcResult:
        """
        1日分の DayRecord から実働・勤務・所内・法定外を計算して返す。
        employee_name を使って CompanyConfig から勤務体系を動的取得する。
        """
        is_special = self.config.is_special_employee(employee_name)

        # 日曜は無条件休
        if day_rec.is_sunday:
            return CalcResult(notes='日曜休')

        # 所定時間の取得
        scheduled = self.config.get_scheduled_hours(employee_name, day_rec.is_saturday)

        # 欠勤
        if day_rec.is_absent:
            return CalcResult(
                absence=scheduled,
                scheduled=scheduled,
                notes='欠勤'
            )

        # 有給（全休）
        if day_rec.is_paid:
            return CalcResult(
                scheduled=scheduled,
                notes='有給'
            )

        t_s = day_rec.t_start
        t_e = day_rec.t_end

        # 時刻データなし → Excel値をそのまま採用（研修・特殊日等）
        if t_s is None or t_e is None:
            return CalcResult(
                work=day_rec.excel_work,
                ot_in=day_rec.excel_ot_in,
                ot_out=day_rec.excel_ot_out,
                absence=day_rec.excel_absence,
                actual_work=day_rec.excel_work + day_rec.excel_ot_in + day_rec.excel_ot_out,
                scheduled=scheduled,
                notes=f"時刻未記載(場所:{day_rec.place})"
            )

        # 休憩時間の厳密計算（手動入力があれば優先）
        if day_rec.break_mins is not None:
            break_h = day_rec.break_mins / 60.0
        else:
            break_h = self._calculate_break_hours(t_s, t_e, employee_name, day_rec.is_saturday)

        # 実働時間
        actual_work = max(0.0, t_e - t_s - break_h)

        # 勤務時間
        time_off = day_rec.time_off
        if time_off > 0:
            guaranteed = max(0.0, scheduled - time_off)
            work = _round_half(max(min(actual_work, scheduled), guaranteed))
        else:
            work = _round_half(min(actual_work, scheduled))

        # 欠勤（遅刻・早退・部分休による自動算出）
        absence = _round_half(max(0.0, scheduled - actual_work - time_off))

        # 特例社員: 所定=法定のため所内は発生しない
        if is_special:
            special_config = self.config.get_special_config(employee_name)
            if special_config and not special_config.has_daily_ot_in:
                ot_in = 0.0
                ot_out = _round_half(max(0.0, actual_work - scheduled))
                return CalcResult(
                    work=work, ot_in=ot_in, ot_out=ot_out,
                    absence=absence, actual_work=actual_work,
                    scheduled=scheduled, break_hours=break_h,
                    notes=f"実働{actual_work:.2f}h"
                )

        # その他の従業員: 所内/法定外は WeeklyAllocator に委ねる
        raw_ot_in = _round_half(max(0.0, min(actual_work, self.config.legal_daily_limit) - scheduled))
        raw_ot_out = _round_half(max(0.0, actual_work - self.config.legal_daily_limit))

        return CalcResult(
            work=work,
            ot_in=raw_ot_in,
            ot_out=raw_ot_out,
            raw_ot=_round_half(max(0.0, actual_work - scheduled)),
            absence=absence,
            actual_work=actual_work,
            scheduled=scheduled,
            break_hours=break_h,
            notes=f"実働{actual_work:.2f}h 欠勤{absence}h"
        )
