"""Demand-driven, allowlisted PR-merged observations. No GitHub mutation API."""
import copy
import json
import os
import re
import threading
import time
from collections import OrderedDict
import httpx
from .connectors import GitHub
from .domain import RelayError, digest, now, instant
from .progress import command, task_in

_cache = OrderedDict()
_lock = threading.Lock()
FRESH_SECONDS = 900
CACHE_SECONDS = 300


def allowed_repos(svc):
    repos = {svc.settings()['github_repo'].lower()}
    if os.getenv('RELAY_MODE') != 'public_demo':
        repos |= {r.strip().lower() for r in os.getenv('RELAY_GATE_REPOS', '').split(',') if r.strip()}
    return repos


def validate_repo(svc, repo, number):
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,99}/[A-Za-z0-9][A-Za-z0-9_.-]{0,99}', repo) or '..' in repo or not 1 <= number <= 100000000:
        raise RelayError('PARSE_FAILED', 'Choose an allowlisted owner/repository and positive pull-request number.')
    if repo.lower() not in allowed_repos(svc):
        raise RelayError('ACCESS_DENIED', 'This repository is not configured for handoff reads. Public visitors cannot expand repository scope.')


def read_pr(repo, number):
    """Shared five-minute single-flight cache, fixed endpoint, bounded stream/ETag."""
    key = (repo.lower(), number)
    with _lock:
        cached = _cache.get(key)
        tick = time.time()
        if cached and tick - cached['checked_epoch'] < CACHE_SECONDS:
            return dict(copy.deepcopy(cached['value']), cache_age_seconds=round(tick-cached['checked_epoch'], 2))
        if tick < GitHub._public_backoff_until:
            raise RelayError('UPSTREAM_RATE_LIMITED', 'GitHub quota is in backoff; the last observation is retained.', {'retry_at_epoch': GitHub._public_backoff_until})
        headers = {'Accept': 'application/vnd.github+json', 'X-GitHub-Api-Version': '2022-11-28'}
        if cached and cached.get('etag'): headers['If-None-Match'] = cached['etag']
        # Public-only, intentionally anonymous: no private repository credential or data.
        url = f'https://api.github.com/repos/{repo}/pulls/{number}'
        began=time.monotonic()
        try:
            with httpx.Client(timeout=httpx.Timeout(10), follow_redirects=False) as client:
                with client.stream('GET', url, headers=headers) as response:
                    checked = now()
                    if time.monotonic()-began>12:raise RelayError('UPSTREAM_UNAVAILABLE','GitHub observation exceeded its bounded stream budget.')
                    if response.status_code == 304 and cached:
                        value = dict(cached['value'], last_checked_at=checked, confirmed_unchanged_at=checked, http_status=304)
                    elif response.status_code == 200:
                        body = bytearray()
                        for chunk in response.iter_bytes():
                            if time.monotonic()-began>12:raise RelayError('UPSTREAM_UNAVAILABLE','GitHub observation exceeded its bounded stream budget.')
                            body.extend(chunk)
                            if len(body) > 512000: raise RelayError('UNSUPPORTED_INPUT', 'Pull-request response exceeds 500 KiB.')
                        obj = json.loads(body)
                        if (obj.get('number') != number or obj.get('base', {}).get('repo', {}).get('full_name', '').lower() != repo.lower()
                            or obj.get('base', {}).get('repo', {}).get('private') is not False
                            or not isinstance(obj.get('merged'), bool) or obj.get('state') not in ('open', 'closed')):
                            raise RelayError('UPSTREAM_UNAVAILABLE', 'GitHub returned an unexpected public pull-request record.')
                        if obj.get('merged') and not obj.get('merged_at'):
                            raise RelayError('UPSTREAM_UNAVAILABLE', 'Merged metadata is incomplete; no gate release is inferred.')
                        if obj.get('merged_at'): instant(obj['merged_at'])
                        value = dict(repo=repo, number=number, url=f'https://github.com/{repo}/pull/{number}',
                                     state=obj['state'], merged=obj['merged'], merged_at=obj.get('merged_at'),
                                     head_sha=obj.get('head', {}).get('sha'), merge_sha=obj.get('merge_commit_sha'),
                                     observed_at=checked, last_checked_at=checked, http_status=200, provenance='live_public_github',
                                     response_sha256=__import__('hashlib').sha256(body).hexdigest())
                    else:
                        if response.status_code == 429 or (response.status_code == 403 and response.headers.get('x-ratelimit-remaining') == '0'):
                            try: retry = max(60, float(response.headers.get('retry-after', 60)))
                            except ValueError: retry = 60
                            try: reset = float(response.headers.get('x-ratelimit-reset', tick+retry))+60
                            except ValueError: reset = tick+retry
                            GitHub._public_backoff_until = max(tick+retry, reset)
                            raise RelayError('UPSTREAM_RATE_LIMITED', 'GitHub quota reached; no fresh gate observation is claimed.', {'http_status': response.status_code})
                        raise RelayError('PR_NOT_FOUND' if response.status_code == 404 else 'UPSTREAM_UNAVAILABLE', 'The public pull request is unavailable; its last observation is retained.', {'http_status': response.status_code})
                    _cache[key] = dict(value=value, checked_epoch=tick, etag=response.headers.get('etag') or (cached or {}).get('etag'))
                    _cache.move_to_end(key)
                    while len(_cache) > 128: _cache.popitem(last=False)
                    return dict(copy.deepcopy(value), cache_age_seconds=0)
        except (httpx.RequestError, ValueError, KeyError) as exc:
            raise RelayError('UPSTREAM_UNAVAILABLE', 'GitHub did not return a valid observation within the bounded request.') from exc


def source_binding(svc, task_id):
    task = task_in(svc, task_id)
    return {s['id']: s['version'] for s in svc.sources() if s['id'] in task['source_ids']}


def state(gate, svc):
    if gate.get('disabled'):return 'disabled'
    if gate.get('archived') or gate.get('source_versions') != source_binding(svc, gate['task_id']): return 'unknown'
    if gate.get('last_error'): return 'unavailable'
    obs = gate.get('observation')
    if not obs: return 'unknown'
    if (instant(now()) - instant(obs.get('confirmed_unchanged_at') or obs['observed_at'])).total_seconds() > FRESH_SECONDS: return 'stale'
    return 'condition_observed' if obs['merged'] and obs.get('merged_at') else 'waiting'


def downstream(tasks, root):
    found = {root}
    while True:
        extra = {t['id'] for t in tasks if any(d in found for d in t.get('dependencies', []))}
        if extra <= found: return sorted(found)
        found |= extra


def list_gates(svc):
    tasks = svc.tasks()
    out=[]
    for gate in svc.store.list(svc.tenant, 'gates'):
        try: status = state(gate, svc)
        except RelayError: status = 'unknown'
        out.append(dict(gate, status=status, downstream_task_ids=downstream(tasks, gate['task_id']), latest_safe_handoff=None,
                        threshold_reason='Unknown: waiting gates have no assumed release time; review an explicit conditional ETA or a fresh observed plan.'))
    return out


def link(svc, body):
    task = task_in(svc, body['task_id'])
    validate_repo(svc, body['repo'], body['number'])
    record = dict(id=digest([task['id'], body['repo'].lower(), body['number']])[:24], task_id=task['id'],
                  repo=body['repo'], number=body['number'], condition='pr_merged', created_at=now(),
                  source_versions=source_binding(svc, task['id']), origin='explicit_student_gate', observation=None,
                  eta=body.get('eta'), archived=False)
    if record['eta']: instant(record['eta'])
    def update(tx):
        if len(tx.list('gates')) >= 10 and not tx.get('gates', record['id']): raise RelayError('UNSUPPORTED_INPUT', 'Use at most ten handoff gates.')
        tx.put('gates', record['id'], record)
        return dict(gate=record)
    return command(svc, body['request_id'], body['expected_revision'], 'gate_link', {k:v for k,v in record.items() if k!='created_at'}, update)


def observe(svc, gate_id):
    gate = svc.store.get(svc.tenant, 'gates', gate_id)
    if gate.get('disabled'):raise RelayError('ACCESS_DENIED','This gate is disabled; explicitly link it again before observing.')
    validate_repo(svc, gate['repo'], gate['number'])
    observation=None; error=None
    try: observation=read_pr(gate['repo'], gate['number'])
    except RelayError as exc: error=dict(code=exc.code, at=now(), details=exc.details)
    def update(tx):
        current=tx.get('gates', gate_id)
        if not current or current['source_versions'] != gate['source_versions']: raise RelayError('STALE_REVISION', 'Gate changed during its observation. Refresh and retry.')
        previous=copy.deepcopy(current)
        current.update(last_error=error, last_attempt_at=now())
        if observation: current.update(observation=observation, archived=False)
        # Operational binding cannot be renewed by an observation after source changes.
        tx.put('gates', gate_id, current)
        old_key=digest([previous.get('observation'), (previous.get('last_error') or {}).get('code')])
        new_key=digest([current.get('observation'), (current.get('last_error') or {}).get('code')])
        if old_key != new_key: tx.advance()
        if observation and observation.get('merged') and not (previous.get('observation') or {}).get('merged'):
            notification_id=digest([gate_id, observation.get('merge_sha'), observation['merged_at']])[:24]
            if not tx.get('handoff_notifications', notification_id):
                tx.put('handoff_notifications', notification_id, dict(id=notification_id, gate_id=gate_id, task_id=current['task_id'], at=now(), origin='public_pr_condition_observed'))
        return current
    updated=svc.store.atomic(svc.tenant, update)
    return dict(updated, status=state(updated, svc))


def apply_gates(svc, payload, conditional=False):
    notes=[]
    tasks={t['id']: t for t in payload['tasks']}
    for gate in list_gates(svc):
        if gate.get('disabled'):continue
        task=tasks.get(gate['task_id'])
        if not task: continue
        status=gate['status']
        if status == 'condition_observed':
            task['release_not_before']=now() # Observation/current time, not historical merge time.
        elif conditional and gate.get('eta'):
            task['release_not_before']=gate['eta']
            notes.append(dict(gate_id=gate['id'], status='conditional_eta', eta=gate['eta']))
        else:
            task['external_blocked']=True
        notes.append(dict(gate_id=gate['id'], task_id=task['id'], status=status, downstream_task_ids=gate['downstream_task_ids']))
    return notes


def remove(svc, gate_id, body):
    def update(tx):
        gate=tx.get('gates',gate_id)
        if not gate:raise RelayError('ACCESS_DENIED','Gate unavailable in this workspace.')
        gate.update(disabled=True,disabled_at=now(),origin='explicit_student_removal')
        tx.put('gates',gate_id,gate)
        return dict(gate=gate)
    return command(svc,body['request_id'],body['expected_revision'],'gate_remove',{'gate_id':gate_id},update)
