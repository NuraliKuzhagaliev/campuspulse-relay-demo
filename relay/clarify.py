"""Bounded decision-impact comparison; hypotheses never become canonical facts."""
import copy
import itertools
import threading
import time
from .domain import RelayError, digest, now, instant
from .connectors import busy_intervals
from .actions import unchanged_owned_ids
from .scheduler import build_recovery_plan
from .handoff import apply_gates
from .progress import command, task_in

_slots=threading.BoundedSemaphore(2)
_jobs={}
_lock=threading.Lock()


def payload(svc):
    settings=svc.settings()
    windows=settings['windows']
    events=svc.calendar().list(min((w['start'] for w in windows), default=now()), max((w['end'] for w in windows), default=now()))
    own=unchanged_owned_ids(events,svc.store.list(svc.tenant,'operations'),svc.tenant)
    value=dict(tasks=copy.deepcopy(svc.tasks()), windows=copy.deepcopy(windows), busy=busy_intervals(events,settings['timezone'],exclude_ids=own),
               timezone=settings['timezone'],daily_cap_minutes=settings['daily_cap_minutes'])
    if settings.get('mode')!='illustrative' or svc.store.list(svc.tenant,'progress') or svc.store.list(svc.tenant,'gates'): value['not_before']=now()
    if value.get('not_before'):
        editable={e['id'] for e in events if e['id'] in own and instant(e['start']['dateTime'])>=instant(value['not_before'])}
        value['busy']=busy_intervals(events,settings['timezone'],exclude_ids=editable)
    prior=svc.latest_plan()
    if prior:
        value['baseline']=[b for b in prior['blocks'] if not value.get('not_before') or instant(b['start'])>=instant(value['not_before'])]
        value['pins']=[b for b in prior.get('input',{}).get('pins',[]) if not value.get('not_before') or instant(b['start'])>=instant(value['not_before'])]
        if value.get('not_before'):value['busy'] += [dict(start=b['start'],end=b['end']) for b in prior['blocks'] if instant(b['start'])<instant(value['not_before'])<instant(b['end'])]
    apply_gates(svc,value)
    return value


def candidates(svc, bounds, offered_windows=None):
    out=[]
    for conflict in sorted(svc.current_conflicts(), key=lambda c:c['id']):
        if conflict['status']!='unresolved': continue
        choices=[]
        for fact in conflict['facts']:
            if not any(c['value']==fact['value'] for c in choices):
                choices.append(dict(value=fact['value'],fact_id=fact['id'],source_id=fact['source_id'],quote=fact['quote'],page=fact['page']))
        if len(choices)==2:
            out.append(dict(id=conflict['id'],kind='deadline',task_id=conflict['task_id'],choices=choices,origin='cited_source_variants'))
    tasks=svc.tasks()
    gaps=[dict(task_id=t['id'],field='remaining' if t.get('progress') else 'minutes',status='bounds_required') for t in tasks if t.get('minutes') is None]
    for bound in bounds:
        task=task_in(svc,bound['task_id'])
        values=bound['values']
        if len(values)!=2 or values[0]==values[1] or any(not isinstance(v,int) or v<=0 or v>10080 for v in values):
            raise RelayError('PARSE_FAILED','Offer two distinct positive effort bounds up to 10080 minutes.')
        out.append(dict(id=digest(['effort',task['id'],values])[:24],kind='effort',task_id=task['id'],
                        choices=[dict(value=v,origin='student_offered_bound') for v in values],origin='student_offered_bounds'))
    for window in offered_windows or []:
        from .domain import Interval
        value=Interval.model_validate(window).model_dump()
        if instant(value['end'])<=instant(value['start']) or (instant(value['end'])-instant(value['start'])).total_seconds()>86400:
            raise RelayError('PARSE_FAILED','Offer a positive availability interval up to one day.')
        out.append(dict(id=digest(['availability',value])[:24],kind='availability',task_id=None,
                        choices=[dict(value=False,origin='student_offered_availability'),dict(value=value,origin='student_offered_availability')],origin='student_offered_window'))
    return out, gaps


def cancel(svc, request_id):
    with _lock:
        event=_jobs.get((svc.tenant,request_id))
        if event:event.set()
    return dict(cancel_requested=bool(event),canonical_workspace_unchanged=True)


def analyze(svc, body):
    fingerprint=svc.source_versions()
    options,gaps=candidates(svc,body.get('bounds',[]),body.get('offered_windows',[]))
    selected_ids=body.get('candidate_ids',[])
    chosen=[c for c in options if not selected_ids or c['id'] in selected_ids][:3]
    cache_id=digest([fingerprint,chosen])[:24]
    try:return dict(svc.store.get(svc.tenant,'clarify_cache',cache_id),cached=True)
    except RelayError:pass
    if not _slots.acquire(False):raise RelayError('BUSY','Two clarification jobs are already running. Retry when one settles.')
    event=threading.Event();key=(svc.tenant,body['request_id'])
    with _lock:
        if any(t==svc.tenant for t,_ in _jobs):
            _slots.release();raise RelayError('BUSY','A clarification job is already running in this workspace.')
        _jobs[key]=event
    began=time.perf_counter();deadline=time.monotonic()+8;branches=[]
    try:
        base=payload(svc)
        if not chosen:
            result=dict(id=cache_id,candidates=[],gaps=gaps,branches=[],status='unsupported',reason='Offer evidence-backed alternatives or explicit effort bounds first.')
        else:
            for bits in itertools.product((0,1),repeat=len(chosen)):
                if event.is_set():raise RelayError('CANCELLED','Clarification cancelled. The original workspace is unchanged.')
                if time.perf_counter()-began>=8:break
                p=copy.deepcopy(base);tasks={t['id']:t for t in p['tasks']}
                assumptions=[]
                for candidate,bit in zip(chosen,bits):
                    value=candidate['choices'][bit]['value'];task=tasks.get(candidate['task_id'])
                    if candidate['kind']=='availability':
                        if value:p['windows'].append(value)
                        assumptions.append(dict(offered_window=value,origin='student_offered_availability'))
                    elif candidate['kind']=='deadline':task['due']=value
                    else:
                        import math
                        rounded=math.ceil(value/30)*30
                        task.update(minutes=rounded,effort_max=rounded,remaining_minutes=rounded)
                        assumptions.append(dict(task_id=task['id'],offered_minutes=value,solver_minutes=rounded,origin='student_offered_bound'))
                try:
                    if any(t.get('identity',{}).get('status')=='unresolved' for t in p['tasks']):raise RelayError('SOURCE_CONFLICT','Assignment identity remains unresolved.')
                    plan=build_recovery_plan(p,time_limit_seconds=min(1,max(.01,8-(time.perf_counter()-began))),deadline_monotonic=deadline,cancel_check=event.is_set)
                    branch=dict(choices=list(bits),status='evaluated',feasible=plan['feasible'],solver_status=plan['solver_status'],unscheduled_minutes=plan['unscheduled_minutes'],
                                blocks=plan['blocks'],unscheduled_by_task=plan['unscheduled_by_task'],assumptions=assumptions)
                except RelayError as exc:
                    if exc.code=='CANCELLED':raise
                    branch=dict(choices=list(bits),status='unknown' if exc.code=='UPSTREAM_UNAVAILABLE' else 'unsupported',error=exc.as_dict(),assumptions=assumptions)
                branches.append(branch)
            ranked=[]
            lookup={tuple(b['choices']):b for b in branches}
            for index,candidate in enumerate(chosen):
                changes=[]
                for bits,left in lookup.items():
                    if bits[index]:continue
                    other=list(bits);other[index]=1;right=lookup.get(tuple(other))
                    if not right or left['status']!='evaluated' or right['status']!='evaluated':continue
                    a={(b['task_id'],b['start'],b['end']) for b in left['blocks']};b={(b['task_id'],b['start'],b['end']) for b in right['blocks']}
                    changes.append(dict(feasibility_changed=left['feasible']!=right['feasible'],minutes_changed=abs(left['unscheduled_minutes']-right['unscheduled_minutes']),blocks_changed=len(a^b),
                                        joint_context=list(bits),affected_tasks=sorted({x[0] for x in a^b})))
                earliest=min((str(c['value']) for c in candidate['choices']),default='') if candidate['kind']=='deadline' else '9999'
                ranked.append(dict(candidate,comparisons=changes,feasibility_changing=any(c['feasibility_changed'] for c in changes),
                                   minutes_affected=max((c['minutes_changed'] for c in changes),default=0),blocks_affected=max((c['blocks_changed'] for c in changes),default=0),earliest_deadline=earliest,
                                   impact_known=bool(changes)))
            ranked.sort(key=lambda c:(not c['impact_known'],not c['feasibility_changing'],c['earliest_deadline'],-c['minutes_affected'],-c['blocks_affected'],c['id']))
            result=dict(id=cache_id,candidates=ranked,gaps=gaps,branches=branches,status='complete' if len(branches)==2**len(chosen) and all(b['status']=='evaluated' for b in branches) else 'partial',
                        tested=len(branches),possible_in_selected_set=2**len(chosen),other_candidates=max(0,len(options)-len(chosen)),
                        policy='Known impact first; feasibility change, earliest cited deadline, affected unscheduled minutes, changed blocks, stable identifier. blocks_changed counts removed plus added block entries, so a moved block can count twice; it is not a distinct moved-block count. Pairwise comparisons include all evaluated joint contexts; no probabilities or global relevance claim.')
        if event.is_set():raise RelayError('CANCELLED','Clarification cancelled. The original workspace is unchanged.')
        if svc.source_versions()!=fingerprint:raise RelayError('STALE_REVISION','Workspace changed during clarification; discard this comparison and retry.')
        result.update(sources=fingerprint,created_at=now(),duration_ms=round((time.perf_counter()-began)*1000),canonical_workspace_unchanged=True)
        def save(tx):
            for old in tx.list('clarify_cache')[:-2]:tx.delete('clarify_cache',old['id'])
            tx.put('clarify_cache',cache_id,result)
        svc.store.atomic(svc.tenant,save)
        return result
    finally:
        with _lock:_jobs.pop(key,None)
        _slots.release()


def answer(svc, analysis_id, body):
    analysis=svc.store.get(svc.tenant,'clarify_cache',analysis_id)
    if analysis['sources']!=svc.source_versions():raise RelayError('STALE_REVISION','The comparison is outdated. Recompute before answering.')
    candidate=next((c for c in analysis['candidates'] if c['id']==body['candidate_id']),None)
    if not candidate:raise RelayError('ACCESS_DENIED','Choose a question from your current comparison.')
    stamp=now()
    def update(tx):
        if analysis['sources']!=svc.source_versions():raise RelayError('STALE_REVISION','Workspace changed before the answer could be recorded. Recompute the comparison.')
        choice=body.get('choice')
        record=dict(id=candidate['id'],analysis_id=analysis_id,task_id=candidate['task_id'],kind=candidate['kind'],choice=choice,at=stamp,origin='student_assumption' if candidate['kind']=='effort' else 'explicit_evidence_choice',uncertain=choice is None)
        if choice is not None:
            alternative=candidate['choices'][choice]
            if candidate['kind']=='deadline':
                tx.put('resolutions',candidate['id'],dict(id=candidate['id'],fact_id=alternative['fact_id'],policy='explicit_user_choice',resolved_at=stamp,user=svc.tenant))
            elif candidate['kind']=='availability':
                settings=tx.get('meta','settings')
                if alternative['value']:
                    from .scheduler import interval_union
                    from .domain import Interval
                    settings['windows']=[dict(start=a.isoformat(),end=z.isoformat()) for a,z in interval_union([Interval.model_validate(w) for w in settings['windows']+[alternative['value']]])]
                    tx.put('meta','settings',settings)
                record['origin']='explicit_student_availability'
            else:
                import math
                minutes=math.ceil(alternative['value']/30)*30
                old=tx.get('task_overrides',candidate['task_id'],{'values':{}})
                values=dict(old['values'],minutes=minutes,effort_max=minutes)
                tx.put('task_overrides',candidate['task_id'],dict(id=candidate['task_id'],values=values,origin='student_assumption',updated_at=stamp))
                p=tx.get('progress',candidate['task_id'])
                if p:
                    p.update(remaining_minutes=alternative['value'],completion='in_progress',updated_at=stamp)
                    p['history'].append(dict(action='clarification_assumption',remaining_minutes=alternative['value'],at=stamp,origin='student_assumption'))
                    tx.put('progress',p['id'],p)
            record['alternative']=alternative
        tx.put('clarification_decisions',record['id'],record)
        return dict(decision=record,gap_remains=choice is None)
    return command(svc,body['request_id'],body['expected_revision'],'clarification_answer',{k:v for k,v in body.items() if k not in ('request_id','expected_revision')},update)
