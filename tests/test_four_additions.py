import copy
import json
import time
from concurrent.futures import ThreadPoolExecutor
import pytest
from relay.domain import RelayError, digest
from relay.store import Store
from relay.service import RelayService
from relay import progress, clarify, handoff, passport
from relay.scheduler import build_recovery_plan, validate_plan


@pytest.fixture
def svc(tmp_path):
    service=RelayService(Store(tmp_path/'four.sqlite3'),'own')
    service.seed('2030-01-07')
    return service


def cmd(svc,task,action,**values):
    return progress.mutate(svc,task,dict(action=action,request_id=digest([action,values,time.time_ns()])[:24],expected_revision=progress.revision(svc),**values))


def resolve(svc):
    for c in svc.current_conflicts():svc.resolve(c['id'],min(c['facts'],key=lambda f:f['value'])['id'])


def test_remaining_is_explicit_rounds_up_and_completion_satisfies_prerequisite(svc):
    resolve(svc);task=next(t for t in svc.tasks() if t['minutes']==120)
    before=copy.deepcopy(svc.current_facts());plan=svc.plan();preview=svc.actions().preview(plan)
    cmd(svc,task['id'],'log',duration_minutes=45,category='implementation')
    assert next(t for t in svc.tasks() if t['id']==task['id'])['minutes'] is None
    with pytest.raises(RelayError,match='required'):svc.plan()
    cmd(svc,task['id'],'remaining',remaining_minutes=90)
    new=svc.plan(proposal=True)
    assert next(t for t in new['input']['tasks'] if t['id']==task['id'])['remaining_minutes']==90
    assert svc.latest_plan()['id']==plan['id'] and svc.latest_plan()['invalidated']
    assert svc.current_facts()==before
    with pytest.raises(RelayError):svc.actions().authorize(preview['id'],preview['digest'],svc.tenant)
    cmd(svc,task['id'],'remaining',remaining_minutes=5)
    assert next(t for t in svc.tasks() if t['id']==task['id'])['remaining_minutes']==30
    with pytest.raises(RelayError):cmd(svc,task['id'],'remaining',remaining_minutes=0)
    cmd(svc,task['id'],'complete')
    result=build_recovery_plan(dict(tasks=[dict(id='a',title='Done',remaining_minutes=0,minutes=120),dict(id='b',title='After',minutes=30,due='2030-01-08T11:00:00Z',dependencies=['a'])],windows=[dict(start='2030-01-08T09:00:00Z',end='2030-01-08T11:00:00Z')]))
    assert result['feasible'] and validate_plan(result)
    assert len(progress.view(svc)['logs'])==1


def test_concurrent_three_tab_stop_retry_and_correction_history(svc):
    task=svc.tasks()[0]['id'];started=cmd(svc,task,'start',category='lab')['session']
    body=dict(action='stop',duration_minutes=45,session_id=started['id'],expected_revision=progress.revision(svc),request_id='a'*24)
    with ThreadPoolExecutor(max_workers=3) as pool:results=list(pool.map(lambda _:progress.mutate(svc,task,body),range(3)))
    assert sum(not r.get('duplicate') for r in results)==1
    logs=progress.view(svc)['logs'];assert len(logs)==1
    with pytest.raises(RelayError) as error:progress.mutate(svc,task,dict(body,request_id='b'*24,action='remaining',remaining_minutes=90))
    assert error.value.code=='STALE_REVISION'
    cmd(svc,task,'correct',log_id=logs[0]['id'],log_revision=1,duration_minutes=40,reason='Removed break')
    log=progress.view(svc)['logs'][0];assert log['duration_minutes']==40 and log['corrections'][0]['duration_minutes']==45
    with pytest.raises(RelayError):cmd(svc,task,'correct',log_id=log['id'],log_revision=1,duration_minutes=30)


def test_timer_absence_is_interrupted_and_not_hours_of_work(svc):
    task=svc.tasks()[0]['id'];session=cmd(svc,task,'start')['session']
    session['last_seen_at']='2000-01-01T00:00:00Z';svc.store.put(svc.tenant,'work_sessions',session['id'],session)
    recovered=progress.heartbeat(svc,session['id'],7200000,session['revision'])
    assert recovered['status']=='interrupted' and recovered['active_seconds']==0
    assert progress.view(svc)['logs']==[]


def test_five_eligible_frozen_samples_required_and_corrected_logs_used(svc):
    for i in range(6):
        svc.import_source(f'lab{i}.md',f'Assignment: Work {i}\nCourse: Course\nTerm: Term\nAssignment ID: k{i}\nDue: 2030-01-11T18:00:00Z\nEffort: 120 minutes'.encode())
    tasks=[t for t in svc.tasks() if t['course']=='Course']
    target=tasks[-1];cmd(svc,target['id'],'start',category='lab');session=next(s for s in progress.view(svc)['sessions'] if s['status']=='running');cmd(svc,target['id'],'stop',session_id=session['id'],duration_minutes=1)
    def sample(task):
        session=cmd(svc,task['id'],'start',category='lab')['session']
        cmd(svc,task['id'],'stop',session_id=session['id'],duration_minutes=180)
        cmd(svc,task['id'],'complete')
    for task in tasks[:4]:sample(task)
    assert progress.suggestion(svc,target['id'])['status']=='insufficient_data'
    sample(tasks[4])
    suggestion=progress.suggestion(svc,target['id'])
    assert suggestion['sample_count']==5 and suggestion['suggested_minutes']==180
    assert all(s['frozen_estimate']==120 for s in suggestion['samples'])


def test_clarify_deadline_impact_joint_branches_cache_stale_and_unknown(svc):
    baseline=copy.deepcopy(svc.snapshot());result=clarify.analyze(svc,dict(request_id='a'*24,bounds=[]))
    assert result['tested']==2 and result['candidates'][0]['kind']=='deadline'
    assert svc.latest_plan()==baseline['plan'] and all(c['status']=='unresolved' for c in svc.current_conflicts())
    first=result['candidates'][0]
    clarify.answer(svc,result['id'],dict(candidate_id=first['id'],choice=None,request_id='b'*24,expected_revision=0))
    assert svc.current_conflicts()[0]['status']=='unresolved'
    with pytest.raises(RelayError):clarify.answer(svc,result['id'],dict(candidate_id=first['id'],choice=0,request_id='c'*24,expected_revision=1))
    resolve(svc)
    # Two extra-effort bounds each fit alone, but their high/high joint branch does not.
    tasks=svc.tasks();bounds=[dict(task_id=t['id'],values=[t['minutes'],t['minutes']+30]) for t in tasks[:2]]
    settings=svc.settings();settings['windows']=[dict(start='2030-01-07T09:00:00Z',end='2030-01-07T18:30:00Z')];settings['daily_cap_minutes']=720;svc.store.put(svc.tenant,'meta','settings',settings)
    joint=clarify.analyze(svc,dict(request_id='d'*24,bounds=bounds))
    assert joint['tested']==4 and [b['feasible'] for b in joint['branches']]==[True,True,True,False]
    again=clarify.analyze(svc,dict(request_id='e'*24,bounds=bounds));assert again['cached'] and again['candidates']==joint['candidates']


@pytest.mark.parametrize('merged,closed,expected',[(False,False,'waiting'),(False,True,'waiting'),(True,True,'condition_observed')])
def test_gate_explicit_merged_not_closed_and_only_downstream(svc,monkeypatch,merged,closed,expected):
    resolve(svc);task=svc.tasks()[0]
    gate=handoff.link(svc,dict(task_id=task['id'],repo=svc.settings()['github_repo'],number=1,request_id='a'*24,expected_revision=0))['gate']
    observation=dict(repo=gate['repo'],number=1,merged=merged,state='closed' if closed else 'open',merged_at='2026-10-19T00:00:00Z' if merged else None,merge_sha='a'*40,observed_at=__import__('relay.domain',fromlist=['now']).now(),last_checked_at=__import__('relay.domain',fromlist=['now']).now())
    monkeypatch.setattr(handoff,'read_pr',lambda *_:observation)
    result=handoff.observe(svc,gate['id']);assert result['status']==expected
    plan=svc.plan(proposal=True)
    assert all(b['task_id']!=task['id'] for b in plan['blocks']) if not merged else plan['feasible']
    handoff.observe(svc,gate['id']);assert len(svc.store.list(svc.tenant,'handoff_notifications'))==(1 if merged else 0)
    def unavailable(*args):raise RelayError('UPSTREAM_UNAVAILABLE','timeout')
    monkeypatch.setattr(handoff,'read_pr',unavailable)
    failed=handoff.observe(svc,gate['id']);assert failed['status']=='unavailable' and failed['observation']==observation
    other=RelayService(svc.store,'other');other.seed('2030-01-07')
    with pytest.raises(RelayError):handoff.observe(other,gate['id'])


def test_passport_roundtrip_progress_exact_quotes_no_authority_and_atomic_retry(svc):
    resolve(svc);task=svc.tasks()[0]['id'];cmd(svc,task,'log',duration_minutes=45,category='lab');cmd(svc,task,'remaining',remaining_minutes=90)
    source_snapshot=copy.deepcopy(svc.snapshot());exported=passport.export(svc);raw=passport.encoded(exported['file'])
    assert all(secret not in raw.decode() for secret in ('calendar_id','approval_id','workspace_id','csrf','operations'))
    staged=passport.stage(svc,raw);result=passport.commit(svc,staged['id']);again=passport.commit(svc,staged['id']);assert result==again
    restored=RelayService(svc.store,result['tenant']);state=restored.snapshot()
    assert state['plan'] is None and state['receipts']==[] and not state['settings']['calendar_live']
    assert {t['id'] for t in state['tasks']}=={t['id'] for t in source_snapshot['tasks']}
    assert [(f['quote'],f['page']) for f in restored.current_facts()]==[(f['quote'],f['page']) for f in svc.current_facts()] or sorted((f['quote'],f['page']) for f in restored.current_facts())==sorted((f['quote'],f['page']) for f in svc.current_facts())
    assert progress.view(restored)['logs'][0]['duration_minutes']==45
    assert next(t for t in state['tasks'] if t['id']==task)['remaining_minutes']==90
    assert svc.snapshot()==source_snapshot or svc.snapshot()['tasks']==source_snapshot['tasks']
    # Re-export a restored workspace without pretending archived text is original bytes.
    second=passport.export(restored);assert all(s['historical_hash_algorithm']=='sha256(canonical_json(extracted_pages))' for s in second['file']['payload']['sources'])


def test_browser_json_integer_float_reserialization_retains_portable_checksum(svc):
    task=svc.tasks()[0]['id'];cmd(svc,task,'log',duration_minutes=45.0);cmd(svc,task,'remaining',remaining_minutes=90.0)
    envelope=passport.export(svc)['file']
    # Real browser JSON.stringify strips .0; this reproduces the observed failed transfer.
    browser_bytes=json.dumps(envelope).replace('45.0','45').replace('90.0','90').encode()
    staged=passport.stage(svc,browser_bytes)
    assert passport.commit(svc,staged['id'])['restored']


@pytest.mark.parametrize('attack',['checksum','tenant','dangling','path','version','quote'])
def test_passport_untrusted_input_safely_rejected(svc,attack):
    envelope=passport.export(svc)['file'];baseline=svc.tasks()
    if attack=='checksum':envelope['payload']['sources'][0]['title']='changed'
    if attack=='tenant':envelope['payload']['progress']=[dict(id=svc.tasks()[0]['id'],tenant_id='victim')]
    if attack=='dangling':envelope['payload']['assignments'][0]['source_ids']=['missing']
    if attack=='path':envelope['payload']['sources'][0]['filename']='C:\\secret.txt'
    if attack=='version':envelope['version']=99
    if attack=='quote':envelope['payload']['citations'][0]['quote']='not in included pages'
    if attack!='checksum':envelope['sha256']=passport.checksum(envelope['payload'])
    with pytest.raises(RelayError):passport.stage(svc,passport.encoded(envelope))
    assert svc.tasks()==baseline and svc.store.list(svc.tenant,'passport_stages')==[]


def test_legacy_snapshot_and_oversize_precise_unchanged(svc):
    with pytest.raises(RelayError) as legacy:passport.stage(svc,json.dumps(svc.snapshot()).encode())
    assert legacy.value.code=='LEGACY_SNAPSHOT_MISSING_EXTRACTS'
    with pytest.raises(RelayError) as oversized:passport.stage(svc,b' '*(passport.MAX_BYTES+1))
    assert oversized.value.code=='PASSPORT_TOO_LARGE'


def test_deadline_feasibility_question_outranks_unchanged_question(svc):
    svc.import_source('lab-friday.md',b'Assignment: Network Security lab\nCourse: Network Security\nDue: 2030-01-11T18:00:00+05:00\nEffort: 240 minutes',id='security-pdf',mode='illustrative')
    svc.import_source('ml-saturday.md',b'Assignment: ML report\nCourse: Machine Learning\nTerm: Illustrative 2026-10\nAssignment ID: ML report\nDue: 2030-01-12T18:00:00+05:00\nEffort: 180 minutes')
    settings=svc.settings();settings['windows']=[dict(start='2030-01-10T09:00:00+05:00',end='2030-01-10T18:00:00+05:00')];settings['daily_cap_minutes']=720;svc.store.put(svc.tenant,'meta','settings',settings)
    result=clarify.analyze(svc,dict(request_id='f'*24,bounds=[]))
    assert result['tested']==4
    assert result['candidates'][0]['feasibility_changing'] and result['candidates'][0]['task_id']==next(t['id'] for t in svc.tasks() if t['course']=='Network Security')
    assert not result['candidates'][1]['feasibility_changing']


def test_clarify_cancel_unknown_and_stale_never_accept_a_plan(svc,monkeypatch):
    real=clarify.build_recovery_plan
    def cancel_during(*args,**kwargs):
        clarify.cancel(svc,'a'*24)
        return real(*args,**kwargs)
    monkeypatch.setattr(clarify,'build_recovery_plan',cancel_during)
    with pytest.raises(RelayError) as cancelled:clarify.analyze(svc,dict(request_id='a'*24,bounds=[]))
    assert cancelled.value.code=='CANCELLED' and svc.latest_plan() is None
    def unknown(*args,**kwargs):raise RelayError('UPSTREAM_UNAVAILABLE','Solver UNKNOWN',{'solver_status':'UNKNOWN'})
    monkeypatch.setattr(clarify,'build_recovery_plan',unknown)
    result=clarify.analyze(svc,dict(request_id='b'*24,bounds=[]))
    assert result['status']=='partial' and all(b['status']=='unknown' for b in result['branches']) and not result['candidates'][0]['impact_known']
    # Source changes invalidate a cache even if its selected question IDs did not change.
    svc.import_source('another.md',b'Assignment: Another\nCourse: Another\nTerm: 2030\nDue: 2030-01-11T18:00:00Z\nEffort: 30 minutes')
    assert clarify.analyze(svc,dict(request_id='c'*24,bounds=[]))['id']!=result['id']


@pytest.mark.parametrize('status',[404,429,200,304,'timeout'])
def test_pr_transport_fixed_scope_bounded_cache_304_and_failure(svc,monkeypatch,status):
    import httpx
    handoff._cache.clear();monkeypatch.setattr(handoff.GitHub,'_public_backoff_until',0)
    original=httpx.Client;requests=[]
    obj=dict(number=1,base={'repo':{'full_name':svc.settings()['github_repo'],'private':False}},state='closed',merged=False,merged_at=None,head={'sha':'a'*40},merge_commit_sha=None)
    def handler(request):
        requests.append(request)
        assert request.url.host=='api.github.com' and request.method=='GET' and request.url.path.endswith('/pulls/1')
        assert 'authorization' not in request.headers
        if status=='timeout':raise httpx.ReadTimeout('timeout')
        return httpx.Response(status,json=obj,headers={'etag':'"one"','retry-after':'60'})
    monkeypatch.setattr(handoff.httpx,'Client',lambda **kwargs:original(transport=httpx.MockTransport(handler),**kwargs))
    key=(svc.settings()['github_repo'].lower(),1)
    if status==304:
        handoff._cache[key]=dict(value=dict(observed_at='2020-01-01T00:00:00Z',merged=False),checked_epoch=0,etag='"one"')
    if status in (200,304):
        first=handoff.read_pr(svc.settings()['github_repo'],1);second=handoff.read_pr(svc.settings()['github_repo'],1)
        assert len(requests)==1 and first['observed_at']==second['observed_at']
        if status==304:assert first['observed_at']=='2020-01-01T00:00:00Z' and requests[0].headers['if-none-match']=='"one"'
    else:
        with pytest.raises(RelayError) as error:handoff.read_pr(svc.settings()['github_repo'],1)
        assert error.value.code==({404:'PR_NOT_FOUND',429:'UPSTREAM_RATE_LIMITED'}.get(status,'UPSTREAM_UNAVAILABLE'))
        if status==429:assert handoff.GitHub._public_backoff_until>time.time()
    handoff._cache.clear()


def test_gate_stale_source_revalidation_and_explicit_removal(svc,monkeypatch):
    task=svc.tasks()[0];gate=handoff.link(svc,dict(task_id=task['id'],repo=svc.settings()['github_repo'],number=1,request_id='a'*24,expected_revision=0))['gate']
    gate['observation']=dict(merged=True,merged_at='2020-01-01T00:00:00Z',observed_at='2020-01-01T00:00:00Z');svc.store.put(svc.tenant,'gates',gate['id'],gate)
    assert handoff.list_gates(svc)[0]['status']=='stale'
    gate['source_versions']={};svc.store.put(svc.tenant,'gates',gate['id'],gate)
    assert handoff.list_gates(svc)[0]['status']=='unknown'
    handoff.remove(svc,gate['id'],dict(request_id='b'*24,expected_revision=1))
    assert handoff.list_gates(svc)[0]['status']=='disabled'


def test_recomputed_checksum_never_restores_receipt_authority(svc):
    envelope=passport.export(svc)['file'];envelope['payload']['sources'][0]['pages'][0]['text']+='\n<script>fetch("https://invalid.example/secret")</script>'
    envelope['sha256']=passport.checksum(envelope['payload'])
    staged=passport.stage(svc,passport.encoded(envelope));copy=RelayService(svc.store,passport.commit(svc,staged['id'])['tenant'])
    assert copy.store.list(copy.tenant,'approvals')==[] and copy.store.list(copy.tenant,'operations')==[] and copy.store.list(copy.tenant,'receipts')==[]
    with pytest.raises(RelayError):copy.actions().apply('historical-receipt')
    assert copy.snapshot()['agent']['verified'] is False


def test_offered_availability_comparison_and_choice_portable(svc):
    resolve(svc)
    offered=dict(start='2030-01-07T16:00:00+05:00',end='2030-01-07T17:00:00+05:00')
    before=copy.deepcopy(svc.settings())
    result=clarify.analyze(svc,dict(request_id='a'*24,bounds=[],offered_windows=[offered]))
    assert result['tested']==2 and result['candidates'][0]['kind']=='availability' and svc.settings()==before
    clarify.answer(svc,result['id'],dict(candidate_id=result['candidates'][0]['id'],choice=1,request_id='b'*24,expected_revision=0))
    assert svc.settings()['windows']!=before['windows']
    staged=passport.stage(svc,passport.encoded(passport.export(svc)['file']))
    target=RelayService(svc.store,passport.commit(svc,staged['id'])['tenant'])
    assert target.store.list(target.tenant,'clarification_decisions')[0]['kind']=='availability'


def test_restore_transaction_rolls_back_partial_copy(svc,monkeypatch):
    staged=passport.stage(svc,passport.encoded(passport.export(svc)['file']))
    from relay.store import WorkspaceTransaction
    original=WorkspaceTransaction.put
    def fail(tx,kind,id,value):
        if tx.tenant!=svc.tenant and kind=='source_versions':raise RuntimeError('deterministic disk/commit failure')
        return original(tx,kind,id,value)
    monkeypatch.setattr(WorkspaceTransaction,'put',fail)
    with pytest.raises(RuntimeError):passport.commit(svc,staged['id'])
    with svc.store.connect() as db:
        assert db.execute('SELECT COUNT(*) FROM records WHERE tenant != ?', (svc.tenant,)).fetchone()[0]==0
    assert svc.store.get(svc.tenant,'passport_stages',staged['id'])['status']=='staged'


def test_model_build_deadline_unknown_not_infeasible():
    with pytest.raises(RelayError) as error:build_recovery_plan(dict(tasks=[],windows=[]),deadline_monotonic=0)
    assert error.value.code=='UPSTREAM_UNAVAILABLE' and error.value.details['solver_status']=='UNKNOWN'


def test_progress_repair_preserves_started_calendar_history(svc,monkeypatch):
    from relay import service
    from relay.domain import instant
    from datetime import timedelta
    resolve(svc);plan=svc.plan();actions=svc.actions();preview=actions.preview(plan);receipt=actions.apply(actions.authorize(preview['id'],preview['digest'],svc.tenant))
    historical=svc.calendar().get(receipt['outcomes'][0]['event_id'])
    cutoff=(instant(historical['start']['dateTime'])+timedelta(minutes=30)).isoformat()
    monkeypatch.setattr(service,'now',lambda:cutoff)
    task_id=historical['extendedProperties']['private']['relay_task'];cmd(svc,task_id,'remaining',remaining_minutes=30)
    revised=svc.plan(proposal=True)
    assert revised['feasible'] and revised['historical_blocks']
    assert not any(instant(b['start'])<instant(historical['end']['dateTime']) and instant(historical['start']['dateTime'])<instant(b['end']) for b in revised['blocks'])
    fresh=svc.actions().preview(revised)
    kept=next(a for a in fresh['actions'] if a['event']['id']==historical['id'])
    assert kept['operation']=='keep' and kept['historical']
    a=svc.actions();a.apply(a.authorize(fresh['id'],fresh['digest'],svc.tenant))
    assert svc.calendar().get(historical['id'])==historical
