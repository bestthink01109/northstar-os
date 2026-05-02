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

            # ── 1. 週内不足枠（バケツ）の算出 ──
            # 週の実労働時間が40時間（※週の日数×所定時間の合計）に不足する分をスライド枠とする
            sched_total  = 0.0
            actual_total = 0.0
            week_time_off = 0.0  # 時間有給の週合計（不就労扱い）

            for d in week_days:
                day_rec, calc = by_day[d]
                weekday = day_rec.weekday if hasattr(day_rec, 'weekday') else day_rec['weekday']
                
                if weekday == '日':
                    continue
                # new_year_holidays は1月のみ適用（正月休み）
                if month == 1 and d in self.config.new_year_holidays:
                    continue

                calc_scheduled = calc.scheduled if hasattr(calc, 'scheduled') else calc['scheduled']
                calc_actual    = calc.actual_work if hasattr(calc, 'actual_work') else calc['actual_work']

                # 時間有給（time_off）を収集：実労働ではないため不就労として算入する
                time_off_v = 0.0
                if hasattr(day_rec, 'time_off'):
                    time_off_v = day_rec.time_off or 0.0
                elif isinstance(day_rec, dict):
                    time_off_v = day_rec.get('time_off') or 0.0

                sched_total   += calc_scheduled
                actual_total  += calc_actual
                week_time_off += time_off_v

            # 不足分を算出（週の所定時間 - 週の実働時間 + 時間有給の不就労分）
            # ※ 時間有給は実労働ではないため shortage_budget を time_off 分だけ増やす
            shortage_budget = max(0.0, sched_total - actual_total) + week_time_off

            # ── 2. 各日の残業を抽出 ──
            # 一旦、すべての残業（actual_work > scheduled）を仮の「法定外残業」とみなし、
            # そこから優先順位に従ってバケツ（shortage_budget）を消費して「法定内残業」にスライドする。
            
            # 各日の残業情報を保持するリスト
            overtime_days = []
            for d in week_days:
                day_rec, calc = by_day[d]
                weekday = day_rec.weekday if hasattr(day_rec, 'weekday') else day_rec['weekday']
                is_saturday = day_rec.is_saturday if hasattr(day_rec, 'is_saturday') else day_rec['is_saturday']
                t_end = day_rec.t_end if hasattr(day_rec, 't_end') else day_rec['t_end']

                notes = calc.notes if hasattr(calc, 'notes') else calc.get('notes', '')
                # new_year_holidays は1月のみ適用（正月休み）
                is_new_year = (month == 1 and d in self.config.new_year_holidays)
                if notes in ('欠勤', '有給', '日曜休') or weekday == '日' or is_new_year:
                    continue

                actual_work = calc.actual_work if hasattr(calc, 'actual_work') else calc['actual_work']
                scheduled = calc.scheduled if hasattr(calc, 'scheduled') else calc['scheduled']
                
                raw_ot = max(0.0, actual_work - scheduled)

                # t_endの取得（土曜日の18:00制限用）
                if hasattr(calc, 't_end'):
                    t_e = calc.t_end
                elif isinstance(calc, dict):
                    t_e = calc.get('t_end')
                else:
                    t_e = None
                    
                overtime_days.append({
                    'day': d,
                    'is_saturday': weekday == '土',
                    't_end': t_e,
                    'raw_ot': raw_ot,
                    'ot_in': 0.0,
                    'ot_out': raw_ot, # 初期値は全て法定外
                    'calc': calc
                })

            # ── 3. バケツリレー（段階的スライド） ──
            remaining_budget = shortage_budget

            # 優先①: 土曜日の残業（最大3時間まで）
            for ot_info in overtime_days:
                if remaining_budget <= 0.0:
                    break
                if ot_info['is_saturday'] and ot_info['raw_ot'] > 0:
                    # 土曜の所内最大枠は3.0時間（15:00終了で18:00まで残業した場合を想定）
                    max_sat_in = 3.0
                    
                    # 実際の終了時間が考慮できる場合は、18:00までの範囲に制限する（既存ロジック準拠）
                    # 平野工業の config: sat_scheduled_end = 15.0, sat_overtime_max = 18.0
                    if ot_info['t_end'] is not None and ot_info['t_end'] > self.config.sat_scheduled_end:
                        ot_in_end = min(ot_info['t_end'], self.config.sat_overtime_max)
                        max_sat_in = max(0.0, ot_in_end - self.config.sat_scheduled_end)

                    # スライド可能な量（残業時間、土曜枠、バケツの残りのうち最小のもの）
                    slide_amount = min(ot_info['raw_ot'], max_sat_in, remaining_budget)
                    slide_amount = _round_half(slide_amount)

                    ot_info['ot_in'] = slide_amount
                    ot_info['ot_out'] = _round_half(ot_info['raw_ot'] - slide_amount)
                    remaining_budget -= slide_amount

            # 優先②: 平日（月〜金）の残業（各日最大1時間まで）
            # ── 残業時間の多い日を優先してot_inに振り分ける ──
            # 同じ残業時間の場合は日番号の降順（後の日）を優先する
            weekday_ots = sorted(
                [ot for ot in overtime_days if not ot['is_saturday'] and ot['raw_ot'] > 0],
                key=lambda x: (-x['raw_ot'], -x['day'])
            )
            for ot_info in weekday_ots:
                if remaining_budget <= 0.0:
                    break

                # すでに ot_in にスライドされている分は除外（土曜以外は0のはずだが念のため）
                remaining_raw_ot = max(0.0, ot_info['raw_ot'] - ot_info['ot_in'])
                if remaining_raw_ot <= 0:
                    continue
                    
                # 平日の所内最大枠は1.0時間（法定8.0h - 所定7.0h）
                # 厳密には、min(actual_work, 8.0) - scheduled なので最大1.0h
                # ここでは汎用的に legal_daily_limit - scheduled と計算
                calc = ot_info['calc']
                scheduled = calc.scheduled if hasattr(calc, 'scheduled') else calc['scheduled']
                max_weekday_in = max(0.0, self.config.legal_daily_limit - scheduled)
                
                # スライド可能な量（残りの残業時間、平日1日枠、バケツの残りのうち最小のもの）
                slide_amount = min(remaining_raw_ot, max_weekday_in, remaining_budget)
                slide_amount = _round_half(slide_amount)

                ot_info['ot_in'] += slide_amount
                ot_info['ot_out'] = _round_half(ot_info['raw_ot'] - ot_info['ot_in'])
                remaining_budget -= slide_amount

            # ── 4. 更新処理 ──
            # overtime_days を辞書化して簡単に検索できるようにする
            ot_dict = {item['day']: item for item in overtime_days}

            for d in week_days:
                day_rec, calc = by_day[d]
                
                if d in ot_dict:
                    ot_info = ot_dict[d]
                    new_ot_in = ot_info['ot_in']
                    new_ot_out = ot_info['ot_out']
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
                        raw_ot=calc.raw_ot if hasattr(calc, 'raw_ot') else 0.0,
                        absence=calc.absence if hasattr(calc, 'absence') else 0.0,
                        actual_work=calc.actual_work if hasattr(calc, 'actual_work') else 0.0,
                        scheduled=calc.scheduled if hasattr(calc, 'scheduled') else 0.0,
                        break_hours=calc.break_hours if hasattr(calc, 'break_hours') else 0.0,
                        notes=calc.notes if hasattr(calc, 'notes') else '',
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
