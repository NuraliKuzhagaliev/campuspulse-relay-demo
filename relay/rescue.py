"""Bounded remedies over student-offered additions. No hidden relaxation or writes."""
import copy
import itertools
import time
from collections import defaultdict
from datetime import timedelta
from zoneinfo import ZoneInfo
from .domain import PlanInput, RelayError, instant, digest
from .scheduler import build_recovery_plan, interval_union, UNIT, required_minutes


def capacity_until(p, cutoff=None):
    days=defaultdict(int)
    for a,z in interval_union(p.windows):
        while a+UNIT<=z:
            if (not cutoff or a+UNIT<=cutoff) and (not p.not_before or a>=instant(p.not_before)) and not any(a<instant(b.end) and instant(b.start)<a+UNIT for b in p.busy):
                days[a.astimezone(ZoneInfo(p.timezone)).date()]+=30
            a+=UNIT
    return sum(min(n,p.daily_cap_minutes) for n in days.values())


def bottlenecks(payload):
    p=PlanInput.model_validate(payload)
    required={t.id:required_minutes(t,p.conservative) for t in p.tasks}
    # A prerequisite must be done by its dependent's deadline, even if its own is later.
    effective={t.id:instant(t.due) for t in p.tasks if required[t.id]>0}
    for _ in p.tasks:
        for t in p.tasks:
            for dep in t.dependencies:
                if dep in effective and t.id in effective:effective[dep]=min(effective[dep],effective[t.id])
    deadlines=[]
    for due in sorted(set(effective.values())):
        tids=[tid for tid,d in effective.items() if d<=due]
        demand=sum(required[tid] for tid in tids)
        cap=capacity_until(p,due)
        deadlines.append(dict(deadline=due.isoformat(),required_minutes=demand,available_minutes=cap,missing_minutes=max(0,demand-cap),task_ids=tids))
    total=sum(required.values());cap=capacity_until(p)
    return dict(required_minutes=total,capacity_minutes=cap,total_shortage_minutes=max(0,total-cap),deadlines=deadlines,
                qualification='Capacity lower bounds; dependency ordering, pins and indivisible slots are also checked by the solver.')


def minimal_rescue(baseline, additions):
    if len(additions)>5:
        raise RelayError('UNSUPPORTED_INPUT','Offer at most five candidate additions per comparison (32 bounded combinations).')
    start=time.monotonic(); proposals=[]; exhausted=True; checked=0
    base=copy.deepcopy(baseline['input']);accepted=base.get('baseline') or baseline['blocks'];base['baseline']=accepted
    validated=[]
    for w in additions:
        candidate=PlanInput.model_validate(dict(base,windows=[w]))
        a,z=instant(candidate.windows[0].start),instant(candidate.windows[0].end)
        if z<=a or z-a>timedelta(hours=12) or a.minute%30 or z.minute%30 or a.second or z.second:
            raise RelayError('PARSE_FAILED','Candidate additions must be positive, half-hour aligned and at most 12 hours.')
        validated.append(candidate.windows[0].model_dump())
    all_optimal=True
    for count in range(len(validated)+1):
        for indices in itertools.combinations(range(len(validated)),count):
            if time.monotonic()-start>10:
                exhausted=False;break
            data=copy.deepcopy(base);data['windows']+= [validated[i] for i in indices]
            try: plan=build_recovery_plan(data)
            except RelayError as exc:
                if exc.code not in ('INFEASIBLE','UPSTREAM_UNAVAILABLE'): raise
                all_optimal &= exc.code=='INFEASIBLE';checked+=1;continue
            checked+=1;all_optimal &= plan['solver_status']=='OPTIMAL'
            if plan['feasible']:
                before={(b['task_id'],b['start'],b['end']) for b in accepted}
                after={(b['task_id'],b['start'],b['end']) for b in plan['blocks']}
                added_capacity=capacity_until(PlanInput.model_validate(data))-capacity_until(PlanInput.model_validate(base))
                duration=lambda value:sum(int((z-a).total_seconds()/60) for a,z in interval_union(PlanInput.model_validate(value).windows))
                added_minutes=duration(data)-duration(base)
                proposals.append(dict(id=digest(indices)[:24],candidate_indices=list(indices),additions=[validated[i] for i in indices],
                                      added_minutes=added_minutes,added_capacity_minutes=added_capacity,accepted_blocks_moved=len(before-after),plan=plan))
        if not exhausted:break
    proposals.sort(key=lambda r:(r['added_minutes'],r['accepted_blocks_moved'],len(r['candidate_indices'])))
    return dict(bottlenecks=bottlenecks(base),remedies=proposals[:3],combinations_checked=checked,
                search_complete=exhausted and all_optimal,minimum_proven=exhausted and all_optimal and bool(proposals),
                scope='minimum among offered combinations' if exhausted and all_optimal else 'best found among offered alternatives',
                no_allowed_remedy=exhausted and all_optimal and not proposals,duration_ms=round((time.monotonic()-start)*1000))
