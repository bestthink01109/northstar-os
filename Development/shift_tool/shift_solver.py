"""
AIシフト自動作成ツール - 制約ソルバー v2
Google OR-Tools CP-SAT を使用して介護施設のシフトを自動生成する。
固定シフトとの整合性を確保し、ソフト制約を適切に分離。
"""

import yaml
import datetime
import calendar
from ortools.sat.python import cp_model
from collections import defaultdict
from typing import Dict, List, Optional, Tuple, Any


# ============================================================
# 定数
# ============================================================

CARE_SHIFTS = ["A", "B", "C", "D", "night", "dawn"]
COOK_SHIFTS = ["cook1", "cook2"]
ALL_SHIFTS = CARE_SHIFTS + ["E"] + COOK_SHIFTS
OFF_TYPES = ["off", "希", "休"]
WORK_COUNTED = ["研", "健"]  # 出勤日数に算入（有給は別管理）
WEEKDAY_JP = ["月", "火", "水", "木", "金", "土", "日"]


def load_config(config_path: str) -> dict:
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def get_weekday_jp(year: int, month: int, day: int) -> str:
    d = datetime.date(year, month, day)
    return WEEKDAY_JP[d.weekday()]


def is_weekend(year: int, month: int, day: int) -> bool:
    return datetime.date(year, month, day).weekday() >= 5


def is_sunday(year: int, month: int, day: int) -> bool:
    return datetime.date(year, month, day).weekday() == 6


class ShiftSolver:
    def __init__(self, config: dict):
        self.config = config
        self.year = config['month']['year']
        self.month = config['month']['month']
        self.num_days = config['month']['days']
        self.staff_list = config['staff']
        self.model = cp_model.CpModel()
        self.solver = cp_model.CpSolver()

        self.shift_vars: Dict[Tuple[int, int, str], Any] = {}
        self.off_vars: Dict[Tuple[int, int], Any] = {}

        self.fixed_assignments: Dict[Tuple[int, int], str] = {}
        self.off_requests: Dict[Tuple[int, int], str] = {}
        self._parse_requests()

        self.staff_map = {s['id']: s for s in self.staff_list}
        self.care_staff_ids = [
            s['id'] for s in self.staff_list if s['role'] == '介護職員'
        ]
        self.cook_staff_ids = [
            s['id'] for s in self.staff_list if s['role'] == '調理職員'
        ]

    def _parse_requests(self):
        requests = self.config.get('march_requests', {})
        for staff_id, reqs in requests.items():
            staff_id = int(staff_id)
            for req in reqs:
                day = req['day']
                req_type = req['type']
                if req_type == "dawn_if_needed":
                    continue
                if req_type in ["希", "off"]:
                    self.off_requests[(staff_id, day)] = "希"
                elif req_type == "有":
                    self.off_requests[(staff_id, day)] = "有"
                elif req_type in ALL_SHIFTS:
                    self.fixed_assignments[(staff_id, day)] = req_type
                elif req_type in WORK_COUNTED:
                    self.fixed_assignments[(staff_id, day)] = req_type

    def _get_all_possible_shifts(self, staff: dict) -> list:
        """スタッフが割当可能な全シフト（允許シフト + cook2特例等）"""
        return staff.get('allowed_shifts', [])

    def _create_variables(self):
        for staff in self.staff_list:
            sid = staff['id']
            allowed = self._get_all_possible_shifts(staff)

            for day in range(1, self.num_days + 1):
                has_fixed = (sid, day) in self.fixed_assignments
                has_off = (sid, day) in self.off_requests

                if has_fixed:
                    fixed_shift = self.fixed_assignments[(sid, day)]
                    for s in allowed:
                        v = self.model.NewBoolVar(f's{sid}_d{day}_{s}')
                        self.shift_vars[(sid, day, s)] = v
                        self.model.Add(v == (1 if s == fixed_shift else 0))
                    # 固定シフトがallowedにない場合（研修等）
                    if fixed_shift not in allowed:
                        v = self.model.NewBoolVar(f's{sid}_d{day}_{fixed_shift}')
                        self.shift_vars[(sid, day, fixed_shift)] = v
                        self.model.Add(v == 1)
                    ov = self.model.NewBoolVar(f's{sid}_d{day}_off')
                    self.off_vars[(sid, day)] = ov
                    self.model.Add(ov == 0)

                elif has_off:
                    for s in allowed:
                        v = self.model.NewBoolVar(f's{sid}_d{day}_{s}')
                        self.shift_vars[(sid, day, s)] = v
                        self.model.Add(v == 0)
                    ov = self.model.NewBoolVar(f's{sid}_d{day}_off')
                    self.off_vars[(sid, day)] = ov
                    self.model.Add(ov == 1)

                else:
                    vs = []
                    for s in allowed:
                        v = self.model.NewBoolVar(f's{sid}_d{day}_{s}')
                        self.shift_vars[(sid, day, s)] = v
                        vs.append(v)
                    ov = self.model.NewBoolVar(f's{sid}_d{day}_off')
                    self.off_vars[(sid, day)] = ov
                    vs.append(ov)
                    self.model.AddExactlyOne(vs)

    def _add_daily_coverage(self):
        """日別配置制約（ハード）"""
        for day in range(1, self.num_days + 1):
            is_sun = is_sunday(self.year, self.month, day)

            for shift in CARE_SHIFTS:
                avail = []
                for s in self.staff_list:
                    sid = s['id']
                    if (sid, day, shift) in self.shift_vars:
                        avail.append(self.shift_vars[(sid, day, shift)])
                if not avail:
                    continue
                if is_sun and shift == "A":
                    pass  # 日曜Aは許容
                else:
                    self.model.Add(sum(avail) >= 1)

            # 調理員
            for cs in COOK_SHIFTS:
                avail = []
                for s in self.staff_list:
                    sid = s['id']
                    if (sid, day, cs) in self.shift_vars:
                        avail.append(self.shift_vars[(sid, day, cs)])
                if avail:
                    self.model.Add(sum(avail) >= 1)

    def _add_weekend_off(self):
        """土日休み制約"""
        for staff in self.staff_list:
            sid = staff['id']
            if not staff.get('weekend_off', False):
                continue
            for day in range(1, self.num_days + 1):
                if is_weekend(self.year, self.month, day):
                    if (sid, day) not in self.off_requests and \
                       (sid, day) not in self.fixed_assignments:
                        ov = self.off_vars.get((sid, day))
                        if ov is not None:
                            self.model.Add(ov == 1)

    def _add_cook_constraints(self):
        """調理職員の曜日固定制約"""
        for staff in self.staff_list:
            sid = staff['id']
            if staff['role'] != '調理職員':
                continue
            fixed_off_wd = staff.get('fixed_off_weekday')
            fixed_wds = staff.get('fixed_weekdays', [])
            wd_shifts = staff.get('weekday_shifts', {})

            for day in range(1, self.num_days + 1):
                wd = get_weekday_jp(self.year, self.month, day)

                if fixed_off_wd and wd == fixed_off_wd:
                    ov = self.off_vars.get((sid, day))
                    if ov is not None:
                        self.model.Add(ov == 1)

                if fixed_wds:
                    if wd in fixed_wds:
                        if (sid, day) not in self.off_requests:
                            allowed = self._get_all_possible_shifts(staff)
                            wvs = [self.shift_vars[(sid, day, s)]
                                   for s in allowed
                                   if (sid, day, s) in self.shift_vars]
                            if wvs:
                                self.model.Add(sum(wvs) >= 1)
                    else:
                        if (sid, day) not in self.fixed_assignments:
                            ov = self.off_vars.get((sid, day))
                            if ov is not None:
                                self.model.Add(ov == 1)

                if wd in wd_shifts:
                    target = wd_shifts[wd]
                    var = self.shift_vars.get((sid, day, target))
                    if var is not None:
                        self.model.Add(var == 1)

    def _add_consecutive_work_limit(self):
        """連続勤務4日制限（ハード）"""
        for staff in self.staff_list:
            sid = staff['id']
            if staff['role'] == '調理職員':
                continue
            allowed = self._get_all_possible_shifts(staff)

            for start in range(1, self.num_days - 2):
                end = min(start + 4, self.num_days + 1)
                if end - start < 4:
                    continue
                work_vars = []
                all_fixed = True
                for d in range(start, end):
                    wvs = [self.shift_vars[(sid, d, s)]
                           for s in allowed
                           if (sid, d, s) in self.shift_vars]
                    if (sid, d) in self.fixed_assignments:
                        work_vars.append(1)
                    elif (sid, d) in self.off_requests:
                        work_vars.append(0)
                    elif wvs:
                        all_fixed = False
                        w = self.model.NewBoolVar(f'w_{sid}_{d}_{start}')
                        self.model.AddMaxEquality(w, wvs)
                        work_vars.append(w)
                    else:
                        work_vars.append(0)

                if all_fixed:
                    continue
                int_sum = sum(v for v in work_vars if isinstance(v, int))
                var_list = [v for v in work_vars if not isinstance(v, int)]
                if var_list:
                    self.model.Add(sum(var_list) + int_sum <= 3)

    def _add_night_cycle(self):
        """夜勤サイクル制約（固定シフトを尊重）"""
        exc_names = self.config['work_constraints']['night_cycle'].get(
            'exceptions', [])
        exc_ids = set()
        for en in exc_names:
            for s in self.staff_list:
                if s['name'] == en:
                    exc_ids.add(s['id'])

        for staff in self.staff_list:
            sid = staff['id']
            if sid in exc_ids:
                continue
            allowed = self._get_all_possible_shifts(staff)
            if 'night' not in allowed:
                continue

            for day in range(1, self.num_days + 1):
                nv = self.shift_vars.get((sid, day, 'night'))
                if nv is None:
                    continue

                # 夜勤→翌日は明け（ただし翌日に固定or希望がある場合はスキップ）
                if day + 1 <= self.num_days:
                    if (sid, day + 1) not in self.fixed_assignments and \
                       (sid, day + 1) not in self.off_requests:
                        dv = self.shift_vars.get((sid, day + 1, 'dawn'))
                        if dv is not None:
                            self.model.Add(dv >= nv)

                # 明け→翌日は休み（ただし翌日に固定or希望がある場合はスキップ）
                dv_today = self.shift_vars.get((sid, day, 'dawn'))
                if dv_today is not None and day + 1 <= self.num_days:
                    if (sid, day + 1) not in self.fixed_assignments and \
                       (sid, day + 1) not in self.off_requests:
                        ov_next = self.off_vars.get((sid, day + 1))
                        if ov_next is not None:
                            self.model.Add(ov_next >= dv_today)

    def _add_working_days(self):
        """勤務日数制約（上限はハード、下限はソフト制約→目的関数で最適化）"""
        self._work_count_info = {}  # 目的関数で使うための情報を保存

        for staff in self.staff_list:
            sid = staff['id']
            if staff['role'] == '調理職員':
                continue
            wd = staff.get('working_days')
            wd_max = staff.get('working_days_max', wd)
            if wd is None:
                continue

            allowed = self._get_all_possible_shifts(staff)
            work_count = []
            fixed_work = 0

            for day in range(1, self.num_days + 1):
                if (sid, day) in self.off_requests:
                    if self.off_requests[(sid, day)] == "有":
                        fixed_work += 1
                    continue
                if (sid, day) in self.fixed_assignments:
                    fixed_work += 1
                    continue
                wvs = [self.shift_vars[(sid, day, s)]
                       for s in allowed
                       if (sid, day, s) in self.shift_vars]
                if wvs:
                    w = self.model.NewBoolVar(f'wc_{sid}_{day}')
                    self.model.AddMaxEquality(w, wvs)
                    work_count.append(w)

            # 上限はハード制約
            if work_count and wd_max:
                self.model.Add(sum(work_count) + fixed_work <= wd_max)

            # 下限情報を保存（ソフト制約として目的関数で処理）
            self._work_count_info[sid] = {
                'vars': work_count,
                'fixed': fixed_work,
                'target': wd,
            }

    def _add_conflict_rules(self):
        """スタッフ間の競合制約"""
        for staff in self.staff_list:
            sid = staff['id']
            for rule in staff.get('conflict_rules', []):
                other_name = rule['when']
                other_shift = rule['has_shift']
                disallowed = rule['then_disallow']
                other_id = None
                for s in self.staff_list:
                    if s['name'] == other_name:
                        other_id = s['id']
                        break
                if other_id is None:
                    continue
                for day in range(1, self.num_days + 1):
                    ov = self.shift_vars.get((other_id, day, other_shift))
                    mv = self.shift_vars.get((sid, day, disallowed))
                    if ov is not None and mv is not None:
                        self.model.Add(mv + ov <= 1)

    def _add_objective(self):
        """目的関数: ソフト制約の最適化（勤務日数への接近 + メインシフト優遇 + 連休優遇）"""
        terms = []

        # 勤務日数ソフト制約（高い重み: 所定日数に近づけるインセンティブ）
        for sid, info in getattr(self, '_work_count_info', {}).items():
            work_vars = info['vars']
            fixed = info['fixed']
            target = info['target']
            # 各出勤日に重みをつけ、所定日数まで出勤するようインセンティブ
            for wv in work_vars:
                terms.append(10 * wv)  # 出勤1日あたり重み10で優遇

        # メインシフト優遇（重み3）
        for staff in self.staff_list:
            sid = staff['id']
            main_shifts = staff.get('main_shifts', [])
            for day in range(1, self.num_days + 1):
                for s in main_shifts:
                    v = self.shift_vars.get((sid, day, s))
                    if v is not None:
                        terms.append(3 * v)
                # 連休優遇（重み2）
                if day + 1 <= self.num_days:
                    o1 = self.off_vars.get((sid, day))
                    o2 = self.off_vars.get((sid, day + 1))
                    if o1 is not None and o2 is not None:
                        co = self.model.NewBoolVar(f'co_{sid}_{day}')
                        self.model.AddBoolAnd([o1, o2]).OnlyEnforceIf(co)
                        self.model.AddBoolOr(
                            [o1.Not(), o2.Not()]
                        ).OnlyEnforceIf(co.Not())
                        terms.append(2 * co)

        if terms:
            self.model.Maximize(sum(terms))

    def solve(self, time_limit_seconds: int = 60) -> Optional[dict]:
        print("変数を生成中...")
        self._create_variables()
        print("配置制約を追加中...")
        self._add_daily_coverage()
        print("土日休み制約を追加中...")
        self._add_weekend_off()
        print("調理職員制約を追加中...")
        self._add_cook_constraints()
        print("連続勤務制約を追加中...")
        self._add_consecutive_work_limit()
        print("夜勤サイクル制約を追加中...")
        self._add_night_cycle()
        print("勤務日数制約を追加中...")
        self._add_working_days()
        print("競合制約を追加中...")
        self._add_conflict_rules()
        print("目的関数を設定中...")
        self._add_objective()

        self.solver.parameters.max_time_in_seconds = time_limit_seconds
        self.solver.parameters.num_workers = 8

        print(f"\nソルバーを実行中（制限時間: {time_limit_seconds}秒）...")
        status = self.solver.Solve(self.model)

        if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
            label = '最適解' if status == cp_model.OPTIMAL else '実行可能解'
            print(f"解が見つかりました（ステータス: {label}）")
            return self._extract_solution()
        else:
            print(f"解が見つかりません（ステータス: {status}）")
            self._diagnose()
            return None

    def _extract_solution(self) -> dict:
        result = {
            'year': self.year,
            'month': self.month,
            'num_days': self.num_days,
            'facility_name': self.config['facility']['name'],
            'staff': [],
            'violations': [],
        }

        for staff in self.staff_list:
            sid = staff['id']
            sr = {
                'id': sid,
                'name': staff['name'],
                'role': staff['role'],
                'employment': staff['employment'],
                'schedule': {},
                'summary': {'work_days': 0, 'paid_leave': 0, 'public_holidays': 0},
            }

            for day in range(1, self.num_days + 1):
                assigned = None

                if (sid, day) in self.fixed_assignments:
                    assigned = self.fixed_assignments[(sid, day)]
                elif (sid, day) in self.off_requests:
                    assigned = self.off_requests[(sid, day)]
                else:
                    allowed = self._get_all_possible_shifts(staff)
                    for s in allowed:
                        v = self.shift_vars.get((sid, day, s))
                        if v is not None and self.solver.Value(v) == 1:
                            assigned = s
                            break
                    if assigned is None:
                        assigned = "休"

                sr['schedule'][day] = assigned

                if assigned == "有":
                    sr['summary']['paid_leave'] += 1
                    sr['summary']['work_days'] += 1
                elif assigned in OFF_TYPES:
                    sr['summary']['public_holidays'] += 1
                elif assigned in ALL_SHIFTS or assigned in WORK_COUNTED:
                    sr['summary']['work_days'] += 1

            result['staff'].append(sr)

        result['violations'] = self._check_violations(result)
        return result

    def _check_violations(self, result: dict) -> list:
        violations = []
        for day in range(1, self.num_days + 1):
            is_sun = is_sunday(self.year, self.month, day)
            sc = defaultdict(int)
            cc = defaultdict(int)

            for sr in result['staff']:
                a = sr['schedule'][day]
                si = self.staff_map[sr['id']]
                if a in ALL_SHIFTS:
                    sc[a] += 1
                    if si['role'] == '介護職員':
                        cc[a] += 1

            for s in CARE_SHIFTS:
                if s == "A" and is_sun:
                    continue
                if sc[s] == 0:
                    violations.append(f"Day {day}: {s}シフトに配置なし")

            for cs in COOK_SHIFTS:
                if sc[cs] == 0:
                    violations.append(f"Day {day}: {cs}に配置なし")

            # 介護配置パターン判定
            best = ((cc['B'] > 0 and cc['C'] > 0 and cc['night'] > 0 and cc['dawn'] > 0) or
                    (cc['C'] > 0 and cc['D'] > 0 and cc['night'] > 0 and cc['dawn'] > 0))
            if not best:
                good = (cc['night'] > 0 and cc['dawn'] > 0 and
                        cc['A'] > 0 and cc['C'] > 0)
                if good:
                    violations.append(f"Day {day}: 残業発生（次点パターン）")
                else:
                    worst = (cc['night'] > 0 and cc['dawn'] > 0 and
                             (cc['A'] > 0 or cc['D'] > 0))
                    if worst:
                        violations.append(f"Day {day}: 残業発生（最悪パターン）")

        # 個人別チェック
        for sr in result['staff']:
            sid = sr['id']
            si = self.staff_map[sid]
            name = sr['name']

            if si['role'] == '調理職員':
                continue

            consec = 0
            max_c = 0
            for day in range(1, self.num_days + 1):
                a = sr['schedule'][day]
                if a not in OFF_TYPES + ["有"]:
                    consec += 1
                    max_c = max(max_c, consec)
                else:
                    consec = 0
            if max_c > 3:
                violations.append(f"{name}: 最大{max_c}連勤（3制限超過）")

            twd = si.get('working_days')
            if twd and sr['summary']['work_days'] < twd:
                violations.append(
                    f"{name}: 勤務{sr['summary']['work_days']}日（所定{twd}日未満）")

        return violations

    def _diagnose(self):
        print("\n=== 診断 ===")
        print("制約が矛盾しています。以下を確認してください：")
        print("1. 固定シフトと夜勤サイクルの整合性")
        print("2. 希望休が多すぎないか")
        print("3. 連続勤務制限と勤務日数の整合性")


def create_shift(config_path: str, time_limit: int = 60) -> Optional[dict]:
    config = load_config(config_path)
    solver = ShiftSolver(config)
    return solver.solve(time_limit_seconds=time_limit)
