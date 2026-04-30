"""
weekly_allocator.py
週次振り分けロジック（BUN_CEO式特例）。
CompanyConfig から週所定時間等を動的取得しパラメータ駆動で動作する。

【BUN_CEO確定ロジック】
ケースA: 不就労=0h（欠勤・有給・遅刻早退なし）
  → 所定超過は全て法定外（所内=0）

ケースB: 不就労が0h超〜3h以内
  → 土曜の15:00〜18:00分（最大3h）のみ「所内（法定内残業）」
  → 土曜18:00以降・平日の超過は全て法定外

ケースC: 不就労が3h超
  → 各日の実働8h未満超過分 = 所内（法定内残業）
  → 各日の実働8h超過分    = 法定外残業

不就労時間 = max(0, 週内全所定合計 - 週内実勤合計)
※ 有給・欠勤ともに出勤していない時間として不就労に算入する
"""

import calendar as _cal
from datetime import date, timedelta

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.models import DayRecord, CalcResult
from base_config import CompanyConfig


def _round_half(val):
    """0.5h単位で四捨五入（給与計算の慣例）"""
    return round(val * 2) / 2


class WeeklyAllocator:
    """
    BUN_CEO式特例ロジック（ケースA/B/C）による所内/法定外残業の週次確定。
    """

    def __init__(self, config: CompanyConfig):
        self.config = config

    def allocate(self, days, calc_results, year, month):
        """
        calc_results に週次判定(ケースA/B/C)を適用して所内/法定外を最終確定する。

        Args:
            days: DayRecordのリスト（互換用パラメータ、未使用）
            calc_results: list of (DayRecord, CalcResult相当dict)
            year: 対象年
            month: 対象月

        Returns: updated_calc_results（同じ構造、ot_in / ot_out を更新）
        """
        by_day = {}
        for day_rec, calc in calc_results:
            # DayRecordがdataclassの場合もdictの場合も対応
            day_num = day_rec.day if hasattr(day_rec, 'day') else day_rec['day']
            by_day[day_num] = (day_rec, calc)

        week_ranges = self._get_week_ranges(year, month)
        updated = dict(by_day)

        for w_start, w_end, wname in week_ranges:
            week_days = [d for d in range(w_start, w_end + 1) if d in by_day]
            if not week_days:
                continue

            # ── 週内所定時間合計の計算 ──
            sched_total = 0.0
            unlabor = 0.0   # 日次の不就労（不足分）の合計

            for d in week_days:
                day_rec, calc = by_day[d]
                weekday = day_rec.weekday if hasattr(day_rec, 'weekday') else day_rec['weekday']
                is_absent = day_rec.is_absent if hasattr(day_rec, 'is_absent') else day_rec['is_absent']
                is_paid = day_rec.is_paid if hasattr(day_rec, 'is_paid') else day_rec['is_paid']

                if weekday == '日':
                    continue
                if d in self.config.new_year_holidays:
                    continue
                if is_absent or is_paid:
                    continue

                calc_scheduled = calc.scheduled if hasattr(calc, 'scheduled') else calc['scheduled']
                calc_actual = calc.actual_work if hasattr(calc, 'actual_work') else calc['actual_work']

                sched_total += calc_scheduled
                unlabor += max(0.0, calc_scheduled - calc_actual)

            # 欠勤・有給日の所定時間を集計
            absent_sched = 0.0
            for d in week_days:
                day_rec, calc = by_day[d]
                weekday = day_rec.weekday if hasattr(day_rec, 'weekday') else day_rec['weekday']
                is_absent = day_rec.is_absent if hasattr(day_rec, 'is_absent') else day_rec['is_absent']
                is_paid = day_rec.is_paid if hasattr(day_rec, 'is_paid') else day_rec['is_paid']

                if (is_absent or is_paid) and weekday != '日' and d not in self.config.new_year_holidays:
                    calc_scheduled = calc.scheduled if hasattr(calc, 'scheduled') else calc['scheduled']
                    absent_sched += calc_scheduled

            has_absent_or_paid = absent_sched > 0.0

            # ── ケースA/B/C を確定 ──
            if has_absent_or_paid:
                if absent_sched <= 3.0 and unlabor <= 0.0:
                    case = 'B'
                else:
                    case = 'C'
            else:
                if unlabor <= 0.0:
                    case = 'A'
                elif unlabor <= 3.0:
                    case = 'B'
                else:
                    case = 'C'

            # ── 各日の所内/法定外を確定 ──
            for d in week_days:
                day_rec, calc = by_day[d]

                # dict形式とdataclass形式の両対応
                notes = calc.notes if hasattr(calc, 'notes') else calc.get('notes', '')
                if notes in ('欠勤', '有給', '日曜休'):
                    continue

                has_raw_ot = hasattr(calc, 'raw_ot') if not isinstance(calc, dict) else 'raw_ot' in calc
                if not has_raw_ot:
                    continue

                actual_work = calc.actual_work if hasattr(calc, 'actual_work') else calc['actual_work']
                scheduled = calc.scheduled if hasattr(calc, 'scheduled') else calc['scheduled']
                is_saturday = day_rec.is_saturday if hasattr(day_rec, 'is_saturday') else day_rec['is_saturday']
                t_end = day_rec.t_end if hasattr(day_rec, 't_end') else day_rec['t_end']

                new_ot_in = 0.0
                new_ot_out = 0.0

                if case == 'A':
                    # 皆勤週: 所定超過は全て法定外
                    new_ot_in = 0.0
                    new_ot_out = _round_half(max(0.0, actual_work - scheduled))

                elif case == 'B':
                    # 不就労3h以内: 土曜15:00〜18:00のみ所内、それ以外は法定外
                    if is_saturday and t_end is not None and t_end > self.config.sat_scheduled_end:
                        ot_in_end = min(t_end, self.config.sat_overtime_max)
                        raw_ot_in = max(0.0, ot_in_end - self.config.sat_scheduled_end)
                        new_ot_in = _round_half(min(raw_ot_in, unlabor))
                        new_ot_out = _round_half(max(0.0, t_end - self.config.sat_overtime_max))
                    else:
                        new_ot_in = 0.0
                        new_ot_out = _round_half(max(0.0, actual_work - scheduled))

                else:  # case == 'C'
                    # 不就労3h超: 各日の8h未満超過=所内、8h超=法定外
                    if actual_work > scheduled:
                        new_ot_in = _round_half(max(0.0, min(actual_work, self.config.legal_daily_limit) - scheduled))
                        new_ot_out = _round_half(max(0.0, actual_work - self.config.legal_daily_limit))
                    else:
                        new_ot_in = 0.0
                        new_ot_out = 0.0

                # 更新（dict形式とdataclass形式の両対応）
                if isinstance(calc, dict):
                    new_calc = dict(calc)
                    new_calc['ot_in'] = new_ot_in
                    new_calc['ot_out'] = new_ot_out
                else:
                    new_calc = CalcResult(
                        work=calc.work,
                        ot_in=new_ot_in,
                        ot_out=new_ot_out,
                        raw_ot=calc.raw_ot,
                        absence=calc.absence,
                        actual_work=calc.actual_work,
                        scheduled=calc.scheduled,
                        break_hours=calc.break_hours if hasattr(calc, 'break_hours') else 0.0,
                        notes=calc.notes,
                    )
                updated[d] = (day_rec, new_calc)

        # 元の順序を保持して返す
        result = []
        for day_rec, _ in calc_results:
            day_num = day_rec.day if hasattr(day_rec, 'day') else day_rec['day']
            result.append(updated[day_num])
        return result

    def _get_week_ranges(self, year, month):
        """
        年月からその月の全週境界を自動計算して返す（月曜始まり）。
        週の途中で月をまたぐ場合は月の境界で打ち切る。
        """
        _, last = _cal.monthrange(year, month)
        first_date = date(year, month, 1)
        last_date = date(year, month, last)

        weeks = []
        w_start = first_date
        w_num = 1
        while w_start <= last_date:
            days_to_sat = (5 - w_start.weekday()) % 7
            w_end = min(w_start + timedelta(days=days_to_sat), last_date)
            weeks.append((w_start.day, w_end.day, f'W{w_num}'))
            w_num += 1
            w_start = w_end + timedelta(days=1)

        return weeks
