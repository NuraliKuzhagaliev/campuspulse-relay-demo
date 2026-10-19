"""Explicit personal progress, not attention monitoring or submission verification."""
import copy
import math
import statistics
from .domain import RelayError, digest, now, instant


def revision(svc):
    try: return svc.store.get(svc.tenant, 'meta', 'additions')['revision']
    except RelayError: return 0


def check_revision(tx, expected):
    if tx.revision() != expected:
        raise RelayError('STALE_REVISION', 'This workspace changed in another tab or device. Refresh and review before retrying.', {'revision': tx.revision()})


def command(svc, request_id, expected_revision, operation, payload, fn):
    fingerprint = digest([operation, payload])
    def update(tx):
        previous = tx.get('addition_requests', request_id)
        if previous:
            if previous['digest'] != fingerprint:
                raise RelayError('IDEMPOTENCY_CONFLICT', 'This retry identifier belongs to a different operation.')
            return dict(previous['result'], duplicate=True)
        check_revision(tx, expected_revision)
        result = fn(tx)
        result['revision'] = tx.advance()
        tx.put('addition_requests', request_id, {'id': request_id, 'digest': fingerprint, 'result': result})
        return result
    return svc.store.atomic(svc.tenant, update)


def task_in(svc, task_id):
    task = next((t for t in svc.tasks() if t['id'] == task_id), None)
    if not task: raise RelayError('ACCESS_DENIED', 'Task unavailable in this workspace.')
    return task


def overlay(tasks, records):
    by_id = {r['id']: r for r in records}
    for task in tasks:
        p = by_id.get(task['id'])
        if not p: continue
        task['progress'] = p
        task['remaining_minutes'] = (0 if p['completion'] == 'completed' else
                                     math.ceil(p['remaining_minutes'] / 30) * 30 if p['remaining_minutes'] is not None else None)
        # Unknown remaining is not silently original minus logged time. An explicit
        # estimate must be supplied before this task can be scheduled again.
        if p['completion'] != 'completed' and p['remaining_minutes'] is None:
            task['minutes'] = None
            task['effort_max'] = None
        task['completion'] = 'self_reported' if p['completion'] == 'completed' else 'worked_on'
    return tasks


def view(svc):
    sessions = svc.store.list(svc.tenant, 'work_sessions')
    return dict(revision=revision(svc), progress=svc.store.list(svc.tenant, 'progress'),
                logs=svc.store.list(svc.tenant, 'work_logs'),
                sessions=[dict(s, recovery_required=s['status'] == 'running') for s in sessions])


def mutate(svc, task_id, body):
    task = task_in(svc, task_id)
    stamp = now()
    action = body['action']
    payload = dict(body, task_id=task_id)
    payload.pop('request_id'); payload.pop('expected_revision')
    def update(tx):
        p = tx.get('progress', task_id) or dict(id=task_id, completion='in_progress', remaining_minutes=None,
                    origin='student_report', category=body.get('category', '').strip(), history=[], created_at=stamp,
                    frozen_estimate=task.get('minutes'), frozen_course=task['identity']['course'],
                    frozen_at=stamp, frozen_source_versions={s['id']: s['version'] for s in svc.sources() if s['id'] in task['source_ids']})
        if 'frozen_before_work' not in p:p['frozen_before_work']=action=='start'
        if action == 'start':
            if len(tx.list('work_sessions'))>=500:raise RelayError('UNSUPPORTED_INPUT','This workspace reached its 500-session limit. Save a portable workspace and start a fresh copy.')
            active = [s for s in tx.list('work_sessions') if s['status'] == 'running']
            if active: raise RelayError('SESSION_ACTIVE', 'Pause or recover the active session before starting another.')
            session_id = digest([task_id, body['request_id']])[:24]
            session = dict(id=session_id, task_id=task_id, status='running', started_at=stamp,
                           last_seen_at=stamp, active_seconds=0, origin='elapsed_session', revision=1)
            tx.put('work_sessions', session_id, session)
            tx.put('progress', task_id, p)
            return dict(session=session)
        if action in ('log', 'stop'):
            if len(tx.list('work_logs'))>=500:raise RelayError('UNSUPPORTED_INPUT','This workspace reached its 500 work-log limit.')
            duration = body.get('duration_minutes')
            if duration is None or not 0 < duration <= 1440:
                raise RelayError('PARSE_FAILED', 'Confirm a positive actual duration up to 1440 minutes.')
            if action == 'stop':
                session = tx.get('work_sessions', body.get('session_id'))
                if not session or session['task_id'] != task_id or session['status'] not in ('running', 'interrupted'):
                    raise RelayError('SESSION_CLOSED', 'This session is unavailable or already stopped. Refresh its history.')
                session.update(status='stopped', stopped_at=stamp, confirmed_minutes=duration, revision=session['revision'] + 1)
                tx.put('work_sessions', session['id'], session)
            ref = body.get('evidence_id')
            if ref and ref not in {f['id'] for f in svc.current_facts() if f['task_id'] == task_id}:
                raise RelayError('ACCESS_DENIED', 'Choose an evidence reference belonging to this task.')
            log_id = digest([task_id, body['request_id']])[:24]
            log = dict(id=log_id, task_id=task_id, duration_minutes=duration, origin='student_confirmed_timer' if action == 'stop' else 'student_manual',
                       created_at=stamp, updated_at=stamp, revision=1, corrections=[], interruptions=body.get('interruptions', ''),
                       checklist=body.get('checklist', []), evidence_id=ref, session_id=body.get('session_id'))
            tx.put('work_logs', log_id, log)
            p['completion'] = 'in_progress'
            p['remaining_minutes'] = None # Logging alone cannot certify remaining work.
        elif action == 'correct':
            log = tx.get('work_logs', body.get('log_id'))
            if not log or log['task_id'] != task_id: raise RelayError('ACCESS_DENIED', 'Work log unavailable.')
            if log['revision'] != body.get('log_revision'): raise RelayError('STALE_REVISION', 'This log was already corrected. Refresh its history.')
            duration = body.get('duration_minutes')
            if duration is None or not 0 < duration <= 1440: raise RelayError('PARSE_FAILED', 'Confirm a positive duration up to 1440 minutes.')
            log['corrections'].append(dict(duration_minutes=log['duration_minutes'], revision=log['revision'], corrected_at=stamp, reason=body.get('reason', '')))
            log.update(duration_minutes=duration, revision=log['revision'] + 1, updated_at=stamp)
            tx.put('work_logs', log['id'], log)
        elif action in ('remaining', 'complete', 'unknown'):
            remaining = body.get('remaining_minutes')
            if action == 'remaining' and (remaining is None or not 0 < remaining <= 10080):
                raise RelayError('PARSE_FAILED', 'Enter positive remaining minutes, choose unknown, or deliberately confirm completion.')
            p.update(remaining_minutes=0 if action == 'complete' else remaining if action == 'remaining' else None,
                     completion='completed' if action == 'complete' else 'in_progress')
        else: raise RelayError('PARSE_FAILED', 'Unsupported progress operation.')
        p['history'].append(dict(action=action, remaining_minutes=p['remaining_minutes'], completion=p['completion'], at=stamp, origin='student_report'))
        p.update(updated_at=stamp, revision=p.get('revision', 0) + 1)
        tx.put('progress', task_id, p)
        return dict(progress=p, log=locals().get('log'))
    return command(svc, body['request_id'], body['expected_revision'], action, payload, update)


def heartbeat(svc, session_id, delta_ms, session_revision):
    stamp = now()
    def update(tx):
        session = tx.get('work_sessions', session_id)
        if not session: raise RelayError('ACCESS_DENIED', 'Session unavailable.')
        if session['revision'] != session_revision: raise RelayError('STALE_REVISION', 'This timer changed elsewhere. Recover its recorded duration.')
        if session['status'] != 'running': return session
        gap = (instant(stamp) - instant(session['last_seen_at'])).total_seconds()
        if gap > 45 or gap < 0 or delta_ms > 30000:
            session['status'] = 'interrupted'
        else:
            session['active_seconds'] += min(max(0, gap), max(0, delta_ms / 1000))
        session.update(last_seen_at=stamp, revision=session['revision'] + 1)
        tx.put('work_sessions', session_id, session)
        return session
    return svc.store.atomic(svc.tenant, update)


def suggestion(svc, task_id):
    task = task_in(svc, task_id)
    records = svc.store.list(svc.tenant, 'progress')
    target = next((p for p in records if p['id'] == task_id), {})
    category = target.get('category')
    logs = svc.store.list(svc.tenant, 'work_logs')
    samples = []
    for p in records:
        if (p['id'] == task_id or p['completion'] != 'completed' or not category or p.get('category') != category
            or p.get('frozen_course') != task['identity']['course'] or not p.get('frozen_estimate') or not p.get('frozen_before_work') or p.get('import_trust')): continue
        duration = sum(l['duration_minutes'] for l in logs if l['task_id'] == p['id'])
        if duration > 0: samples.append(dict(task_id=p['id'], actual=duration, frozen_estimate=p['frozen_estimate'], ratio=duration/p['frozen_estimate']))
    baseline = target.get('frozen_estimate') or task.get('minutes')
    ratio = statistics.median(s['ratio'] for s in samples) if len(samples) >= 5 else None
    return dict(sample_count=len(samples), status='available' if ratio is not None and baseline else 'insufficient_data',
                suggested_minutes=min(10080, math.ceil(baseline * max(.5, min(2, ratio)) / 30) * 30) if ratio is not None and baseline else None,
                median_ratio=ratio, samples=samples, category=category,
                policy='Same workspace, exact confirmed course and student category; completed with positive corrected logs and pre-work frozen estimate. Median actual/frozen ratio capped 0.5–2, rounded up to 30 minutes. At least five samples. Explicit acceptance required.')
