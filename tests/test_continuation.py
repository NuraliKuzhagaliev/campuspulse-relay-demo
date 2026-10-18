import copy
import pytest
from relay.evidence import extract_facts, conflicts
from relay.service import RelayService
from relay.store import Store
from relay.domain import RelayError, now
from relay.scheduler import build_recovery_plan, validate_plan


def brief(course='Networks', term='2026 Fall', title='Lab 1', key='lab-1', due='2026-10-21T18:00:00+05:00'):
    return f'Assignment: {title}\nCourse: {course}\nTerm: {term}\nAssignment ID: {key}\nDue: {due}\nEffort: 120 minutes'.encode()


def test_cross_course_and_semester_identity_and_explicit_reconciliation(tmp_path):
    s=RelayService(Store(tmp_path/'db'),'a')
    a=s.import_source('a.md',brief())
    b=s.import_source('b.md',brief(course='Machine Learning',due='2026-10-23T18:00:00+05:00'))
    c=s.import_source('c.md',brief(term='2027 Spring'))
    assert len(s.tasks())==3 and not s.current_conflicts()
    revised=s.import_source('repo.md',brief(title='  Renamed   LAB  ',key='LAB-1',due='2026-10-22T18:00:00+05:00'))
    assert revised['drafts'][0]['id']==a['drafts'][0]['id']
    assert len(s.tasks())==3 and len(s.current_conflicts())==1
    unknown=s.import_source('unknown.md',brief(course='',term=''))
    assert unknown['drafts'][0]['identity']['status']=='unresolved'
    s.map_assignment(unknown['id'],unknown['drafts'][0]['section_key'],'','','',a['drafts'][0]['id'])
    assert len(s.tasks())==3
    s.import_source('a.md',brief(title='New display name'),id=a['id'])
    assert len(s.tasks())==3
    other=RelayService(s.store,'other')
    with pytest.raises(RelayError):other.map_assignment(unknown['id'],unknown['drafts'][0]['section_key'],'','','',a['drafts'][0]['id'])


def test_legacy_collision_migration_retains_ambiguous_override_and_receipts(tmp_path):
    store=Store(tmp_path/'db'); s=RelayService(store,'a')
    for id,course in [('a','Networks'),('b','ML')]:
        source=s.import_source(id+'.md',brief(course=course))
        source.pop('identity_schema'); source['drafts'][0]['id']='old-collision'
        store.put('a','sources',source['id'],source)
    store.put('a','task_overrides','old-collision',{'id':'old-collision','values':{'minutes':30}})
    receipt={'id':'immutable','task_id':'old-collision','status':'verified'}
    store.put('a','receipts','immutable',receipt)
    assert len(s.tasks())==2
    assert all(t['minutes']==120 for t in s.tasks())
    assert store.get('a','receipts','immutable')==receipt
    assert store.get('a','identity_migrations','old-collision')['status']=='review_required'
    assert len(store.list('a','identity_history'))==2


def schedule(windows,**extra):
    return build_recovery_plan(dict(tasks=[dict(id='lab',title='Lab',minutes=120,due='2026-10-20T12:00:00+05:00')],windows=[dict(start='2026-10-20T'+a+':00+05:00',end='2026-10-20T'+b+':00+05:00') for a,b in windows],**extra))


def test_adjacent_overlap_and_real_gap_end_to_end():
    single=schedule([('09:00','11:00')])
    adjacent=schedule([('09:00','10:00'),('10:00','11:00')])
    overlap=schedule([('09:00','10:30'),('10:00','11:00')])
    assert single['blocks']==adjacent['blocks']==overlap['blocks']
    assert adjacent['feasible'] and validate_plan(adjacent)
    gap=schedule([('09:00','10:00'),('10:30','11:30')])
    assert len(gap['blocks'])==2 and validate_plan(gap)
    invalid=copy.deepcopy(gap);invalid['blocks']=[dict(task_id='lab',start='2026-10-20T09:00:00+05:00',end='2026-10-20T11:00:00+05:00')]
    with pytest.raises(AssertionError,match='availability'):validate_plan(invalid)


def test_elapsed_cutoff_busy_pin_and_dst():
    p=schedule([('09:00','12:00')],not_before='2026-10-20T09:15:00+05:00',busy=[dict(start='2026-10-20T10:00:00+05:00',end='2026-10-20T10:30:00+05:00')],pins=[dict(task_id='lab',start='2026-10-20T11:00:00+05:00',end='2026-10-20T11:30:00+05:00')])
    assert p['feasible'] and validate_plan(p)


def golden(s):
    s.seed('2026-10-19');c=s.current_conflicts()[0]
    s.resolve(c['id'],min(c['facts'],key=lambda f:f['value'])['id'])
    return s.plan()


def test_rescue_deadline_bottleneck_friday_alone_cannot_help(tmp_path):
    from relay.rescue import minimal_rescue
    from relay.scheduler import compare_plan_scenarios
    s=RelayService(Store(tmp_path/'db'),'a');base=golden(s)
    lost=compare_plan_scenarios(base,{'remove_weekday':2})
    friday=dict(start='2026-10-23T17:00:00+05:00',end='2026-10-23T19:00:00+05:00')
    early=dict(start='2026-10-20T16:00:00+05:00',end='2026-10-20T17:00:00+05:00')
    r=minimal_rescue(lost,[friday])
    assert r['bottlenecks']['total_shortage_minutes']==120
    assert r['bottlenecks']['deadlines'][0]['missing_minutes']==60
    assert r['no_allowed_remedy']
    r=minimal_rescue(lost,[friday,early])
    assert r['minimum_proven'] and r['combinations_checked']==4
    assert r['remedies'][0]['candidate_indices']==[0,1]
    assert r['remedies'][0]['plan']['feasible']
    assert s.latest_plan()['id']==base['id']
    assert minimal_rescue(lost,[])['no_allowed_remedy']


def test_preflight_structural_semantics_exception_and_missing(tmp_path):
    from relay.preflight import check_submission
    s=RelayService(Store(tmp_path/'db'),'a')
    source=s.import_source('brief.md',brief()+b'\nFilename: lab-*.md\nFormat: md\nSections: Method;Results\nWords: 3-100\nPages: 1-3\n- [ ] Include the required experimental screenshot')
    good=check_submission('lab-1.md',b'# Method\nA careful experiment.\n# Results\nObserved result.',source['facts'])
    states={r['requirement']['quote']:r['status'] for r in good['results']}
    assert states['Filename: lab-*.md']=='verified' and states['Sections: Method;Results']=='verified'
    assert states['Pages: 1-3']=='unknown'
    assert states['Include the required experimental screenshot']=='needs_review'
    bad=check_submission('other.md',b'# Method\nOnly method.',source['facts'])
    assert bad['missing_count']==2
    filename=next(f for f in source['facts'] if f['quote'].startswith('Filename:'))
    exception=check_submission('other.md',b'# Method\n# Results',source['facts'],{filename['id']:'Instructor allowed an alternate filename.'})
    assert next(r for r in exception['results'] if r['requirement']['id']==filename['id'])['status']=='needs_review'


def test_conversation_continuity_isolation_restart_duplicate_expiry(tmp_path):
    from relay.conversations import conversation,begin_run,finish_run,classify_result
    store=Store(tmp_path/'db');c=conversation(store,'a')
    r,created=begin_run(store,'a',c['id'],'request-123456789','Plan my week')
    finish_run(store,'a',r,'Plan my week',{'status':'complete','text':'Option 1 Monday. Option 2 Tuesday.'})
    restarted=Store(tmp_path/'db')
    assert conversation(restarted,'a',c['id'])['turns'][0]['assistant'].endswith('Tuesday.')
    duplicate,created=begin_run(restarted,'a',c['id'],'request-123456789','Plan my week')
    assert not created and duplicate['status']=='complete'
    second,created=begin_run(restarted,'a',c['id'],'second-1234567890','Use the second option; keep Wednesday free')
    assert created
    with pytest.raises(RelayError):conversation(store,'b',c['id'])
    assert conversation(store,'a')['turns']==[]
    store.claim('a','conversations',c['id'],{'closed':False},{'expires':0})
    with pytest.raises(RelayError):conversation(store,'a',c['id'])
    assert classify_result({'text':'','status':'complete'})['status']=='failed'
    assert classify_result({'text':'Useful partial quote','status':'complete','required_tool_failed':True})['status']=='partial'
    assert classify_result({'text':'','status':'unknown'})['status']=='unknown'


@pytest.mark.parametrize('text,expression',[('Submit the report on 03/04.','03/04'),('Сдать отчёт 3 апреля.','3 апреля'),('Есепті 3 сәуірде тапсырыңыз.','3 сәуірде')])
def test_prose_extraction_contract_citations_ambiguity_and_injection(text,expression):
    from relay.extraction import extraction_proposal
    source={'id':'prose','version':'v1','content_hash':'hash','pages':[{'page':2,'text':text}]}
    p=extraction_proposal(source,[dict(field='due',value='2026-04-03T18:00:00+05:00',page=2,quote=text,original_expression=expression,ambiguous=True)])
    assert p['fields'][0]['validation_status']=='ambiguous' and not p['applied']
    assert p['fields'][0]['source_version']=='v1'
    with pytest.raises(RelayError):extraction_proposal(source,[dict(field='due',value=None,page=2,quote='Invented quote')])
    p=build_recovery_plan(dict(tasks=[dict(id='lab',title='Lab',minutes=120,due='2026-11-01T03:00:00-05:00')],timezone='America/New_York',windows=[dict(start='2026-11-01T01:00:00-04:00',end='2026-11-01T01:00:00-05:00'),dict(start='2026-11-01T01:00:00-05:00',end='2026-11-01T02:00:00-05:00')]))
    assert p['feasible'] and validate_plan(p)


def test_remaining_effort_is_explicit_not_assumed_from_completion():
    data=dict(tasks=[dict(id='done',title='Done',minutes=120,remaining_minutes=0,completion='self_reported'),dict(id='partial',title='Partial',minutes=120,remaining_minutes=30,due='2026-10-20T12:00:00+05:00')],windows=[dict(start='2026-10-20T09:00:00+05:00',end='2026-10-20T09:30:00+05:00')])
    plan=build_recovery_plan(data)
    assert plan['feasible'] and plan['required_minutes']==30
    del data['tasks'][0]['remaining_minutes']
    with pytest.raises(RelayError):build_recovery_plan(data)


def test_context_renewal_never_outlives_original_authorization(monkeypatch):
    from relay import auth
    token=auth.sign_context('a','https://mcp.test/mcp','secret'*8,seconds=120)
    run=auth.RunAuthorization(token,'https://mcp.test/mcp','secret'*8)
    assert auth.verify_context(run.context(),'https://mcp.test/mcp','secret'*8)=='a'
    monkeypatch.setattr(auth.time,'time',lambda:run.until+1)
    with pytest.raises(RelayError):run.context()


def test_real_success_freshness_not_snapshot_time(tmp_path,monkeypatch):
    from relay.connectors import GitHub
    s=RelayService(Store(tmp_path/'db'),'a');s.seed('2026-10-19')
    original='2026-10-18T00:00:00+00:00'
    monkeypatch.setattr(GitHub,'read',lambda *a:dict(text=brief().decode(),commit='a'*40,fetched_at=original))
    s.sync_repo();one=s.snapshot()
    assert one['last_sync']==original
    assert s.snapshot()['last_sync']==original
    def unavailable(*a):raise RelayError('UPSTREAM_RATE_LIMITED','Observed mocked 429')
    monkeypatch.setattr(GitHub,'read',unavailable)
    with pytest.raises(RelayError):s.sync_repo()
    assert s.snapshot()['last_sync']==original
    assert s.snapshot()['freshness']['last_failed_attempt']['code']=='UPSTREAM_RATE_LIMITED'
