"""Bounded CP-SAT allocation; a second validator checks returned invariants."""
from collections import defaultdict
from datetime import timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from ortools.sat.python import cp_model
from .domain import PlanInput, RelayError, instant, digest

UNIT = timedelta(minutes=30)


def required_minutes(task, conservative=False):
    return task.remaining_minutes if task.remaining_minutes is not None else (task.effort_max if conservative and task.effort_max else task.minutes)


def interval_union(windows):
    """Canonical UTC union, preserving every positive gap (including DST folds)."""
    out = []
    for a, z in sorted((instant(w.start), instant(w.end)) for w in windows):
        if z <= a or z-a > timedelta(days=31):
            raise RelayError('PARSE_FAILED', 'Study windows must be positive and at most 31 days.')
        if out and a <= out[-1][1]:
            out[-1] = (out[-1][0], max(out[-1][1], z))
        else:
            out.append((a, z))
    return out


def build_recovery_plan(payload: dict) -> dict:
    """Allocate validated 30-minute study units before hard deadlines. Never writes externally."""
    p = PlanInput.model_validate(payload)
    try:
        zone = ZoneInfo(p.timezone)
    except ZoneInfoNotFoundError as exc:
        raise RelayError('PARSE_FAILED', 'Unknown IANA timezone.') from exc
    tasks = {t.id: t for t in p.tasks}
    if len(tasks) != len(p.tasks):
        raise RelayError('PARSE_FAILED', 'Task IDs must be unique.')
    visited, visiting = set(), set()
    def walk(tid):
        if tid not in tasks:
            raise RelayError('PARSE_FAILED', f'Missing dependency: {tid}')
        if tid in visiting:
            raise RelayError('PARSE_FAILED', 'Dependency cycle; correct prerequisites first.')
        if tid in visited:
            return
        visiting.add(tid)
        for dep in tasks[tid].dependencies:
            walk(dep)
        visiting.remove(tid)
        visited.add(tid)
    for tid in tasks:
        walk(tid)
    missing = [t.id for t in p.tasks if required_minutes(t,p.conservative) is None or (required_minutes(t,p.conservative)>0 and t.due is None)]
    if missing:
        raise RelayError('SOURCE_CONFLICT', 'A confirmed deadline and effort estimate are required before planning.', missing)
    for t in p.tasks:
        if t.effort_max is not None and t.effort_max < t.minutes:
            raise RelayError('PARSE_FAILED', 'The effort range maximum is below the estimate.')
    slots = set()
    for w in p.windows:
        start, end = instant(w.start), instant(w.end)
        if end <= start or end - start > timedelta(days=31):
            raise RelayError('PARSE_FAILED', 'Study windows must be positive and at most 31 days.')
        if start.astimezone(zone).minute % 30 or start.second or end.astimezone(zone).minute % 30 or end.second:
            raise RelayError('PARSE_FAILED', 'Study windows must align to 30-minute boundaries.')
        while start + UNIT <= end:
            if (not p.not_before or start >= instant(p.not_before)) and not any(start < instant(b.end) and instant(b.start) < start + UNIT for b in p.busy):
                slots.add(start)
            start += UNIT
    if len(slots) > 1500:
        raise RelayError('UNSUPPORTED_INPUT', 'Plan at most 1500 half-hour units in one run.')
    slots = sorted(slots)
    model = cp_model.CpModel()
    x = {}
    required = {t.id: required_minutes(t,p.conservative) // 30 for t in p.tasks}
    for tid, task in tasks.items():
        for j, s in enumerate(slots):
            if required[tid] and s + UNIT <= instant(task.due):
                x[tid, j] = model.new_bool_var(f'{tid}_{j}')
        model.add(sum(v for (t, _), v in x.items() if t == tid) <= required[tid])
    for j in range(len(slots)):
        model.add(sum(v for (t, k), v in x.items() if k == j) <= 1)
    days = defaultdict(list)
    for j, s in enumerate(slots):
        days[s.astimezone(zone).date()].append(j)
    for js in days.values():
        model.add(sum(v for (t, j), v in x.items() if j in js) <= p.daily_cap_minutes // 30)
    for tid, task in tasks.items():
        for dep in task.dependencies:
            for (t, j), var in x.items():
                if t == tid:
                    before = sum(v for (d, k), v in x.items() if d == dep and k < j)
                    model.add(before >= required[dep]).only_enforce_if(var)
    def block_units(block):
        start, end = instant(block.start), instant(block.end)
        if end <= start or (end-start).total_seconds() % 1800:
            raise RelayError('PARSE_FAILED', 'Pinned blocks must contain complete half-hour units.')
        while start < end:
            yield start
            start += UNIT
    for pin in p.pins:
        if pin.task_id not in tasks:
            raise RelayError('PARSE_FAILED', 'Pin references an unknown task.')
        for s in block_units(pin):
            key = (pin.task_id, slots.index(s)) if s in slots else None
            if key not in x:
                raise RelayError('INFEASIBLE', 'A pin violates availability or a hard deadline.')
            model.add(x[key] == 1)
    old = {(b.task_id, s) for b in p.baseline for s in block_units(b)}
    # Required work dominates priority, which dominates preservation, then early placement.
    stability_scale = 2000
    priority_scale = (len(x) + 1) * stability_scale
    required_scale = (sum(required.values()) * 10 + 1) * priority_scale
    model.maximize(sum((required_scale + tasks[t].priority * priority_scale +
                        (stability_scale if (t, slots[j]) in old else 0) + len(slots)-j) * var
                       for (t, j), var in x.items()))
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 5
    solver.parameters.num_search_workers = 1
    status = solver.solve(model)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        raise RelayError('INFEASIBLE' if status == cp_model.INFEASIBLE else 'UPSTREAM_UNAVAILABLE',
                         'No valid allocation was returned within the bounded solve.', {'solver_status': solver.status_name(status)})
    assigned = sorted([(slots[j], t) for (t, j), v in x.items() if solver.value(v)])
    blocks = []
    pin_units = {(b.task_id, s) for b in p.pins for s in block_units(b)}
    for s, tid in assigned:
        pinned = (tid, s) in pin_units
        if blocks and blocks[-1]['task_id'] == tid and instant(blocks[-1]['end']) == s and blocks[-1]['pinned'] == pinned:
            blocks[-1]['end'] = (s+UNIT).astimezone(zone).isoformat()
        else:
            blocks.append(dict(task_id=tid, start=s.astimezone(zone).isoformat(), end=(s+UNIT).astimezone(zone).isoformat(), pinned=pinned))
    allocated = defaultdict(int)
    for _, tid in assigned:
        allocated[tid] += 30
    unscheduled = {tid: count * 30 - allocated[tid] for tid, count in required.items() if count * 30 > allocated[tid]}
    capacity = sum(min(len(js)*30, p.daily_cap_minutes) for js in days.values())
    result = dict(blocks=blocks, feasible=not unscheduled, solver_status=solver.status_name(status),
                  required_minutes=sum(required.values())*30, capacity_minutes=capacity,
                  scheduled_minutes=len(assigned)*30, unscheduled_minutes=sum(unscheduled.values()),
                  unscheduled_by_task=unscheduled, slack_minutes=capacity-sum(required.values())*30,
                  preserved_units=sum((t, s) in old for s, t in assigned),
                  assumptions=['Effort values are estimates, not completion probabilities.',
                               'Only the supplied study windows are available. Hard deadlines remain fixed.'],
                  input=p.model_dump())
    result['id'] = digest(result)[:24]
    try:
        validate_plan(result)
    except AssertionError as exc:
        raise RelayError('PLAN_VALIDATION_FAILED', 'The returned allocation failed independent checks. No plan was accepted; review constraints and retry.') from exc
    return result


def validate_plan(plan: dict):
    """Independent constraints, using interval arithmetic rather than solver variables."""
    p = PlanInput.model_validate(plan['input'])
    tasks = {t.id:t for t in p.tasks}
    used = []
    minutes, days = defaultdict(int), defaultdict(int)
    zone = ZoneInfo(p.timezone)
    available = interval_union(p.windows)
    for b in plan['blocks']:
        a, z = instant(b['start']), instant(b['end'])
        if z <= a or (z-a).total_seconds() % 1800:
            raise AssertionError('Invalid block duration')
        if not any(wa <= a and z <= wz for wa, wz in available):
            raise AssertionError('Outside availability')
        if p.not_before and a < instant(p.not_before):
            raise AssertionError('Elapsed time reused')
        if z > instant(tasks[b['task_id']].due):
            raise AssertionError('Hard deadline violated')
        if any(a < instant(v.end) and instant(v.start) < z for v in p.busy):
            raise AssertionError('Busy overlap')
        if any(a < bz and ba < z for ba, bz in used):
            raise AssertionError('Study overlap')
        used.append((a,z))
        minutes[b['task_id']] += int((z-a).total_seconds()/60)
        s = a
        while s < z:
            days[s.astimezone(zone).date()] += 30
            s += UNIT
    if any(v > p.daily_cap_minutes for v in days.values()):
        raise AssertionError('Daily cap violated')
    for t in p.tasks:
        required = required_minutes(t,p.conservative)
        if minutes[t.id] > required:
            raise AssertionError('Excess effort')
        for dep in t.dependencies:
            descendants = [instant(b['start']) for b in plan['blocks'] if b['task_id'] == t.id]
            prior = [instant(b['end']) for b in plan['blocks'] if b['task_id'] == dep]
            dep_task = tasks[dep]
            dep_needed = required_minutes(dep_task,p.conservative)
            if descendants and (minutes[dep] < dep_needed or max(prior) > min(descendants)):
                raise AssertionError('Dependency order violated')
    for pin in p.pins:
        covered = sum((min(instant(b['end']),instant(pin.end))-max(instant(b['start']),instant(pin.start))).total_seconds()
                      for b in plan['blocks'] if b['task_id']==pin.task_id and instant(b['start'])<instant(pin.end) and instant(pin.start)<instant(b['end']))
        if covered != (instant(pin.end)-instant(pin.start)).total_seconds():
            raise AssertionError('Pin moved')
    return True


def compare_plan_scenarios(baseline: dict, scenario: dict) -> dict:
    """Compute a separate scenario without mutating the baseline or calendar."""
    import copy
    data = copy.deepcopy(baseline['input'])
    data['baseline'] = baseline['blocks']
    if 'remove_weekday' in scenario:
        zone = ZoneInfo(data['timezone'])
        data['windows'] = [w for w in data['windows'] if instant(w['start']).astimezone(zone).weekday() != scenario['remove_weekday']]
    if 'extra_minutes' in scenario:
        for t in data['tasks']:
            if t['id'] == scenario.get('task_id'):
                t['minutes'] += scenario['extra_minutes']
                if t.get('effort_max') is not None:
                    t['effort_max'] += scenario['extra_minutes']
                if t.get('remaining_minutes') is not None:
                    t['remaining_minutes'] += scenario['extra_minutes']
    return build_recovery_plan(data)
