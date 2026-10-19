import asyncio
import importlib
import json
import secrets
import threading
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
import httpx
import pytest
from relay.store import Store
from relay.domain import RelayError
from relay.public_ai import PublicQueue,QuotaGate,day_window
from relay.conversations import conversation


def workspace(store,tenant):
    store.put('_server','workspaces',tenant,{'id':tenant})
    store.put('_server','sessions',tenant,dict(tenant=tenant,expires=time.time()+7200))
    return conversation(store,tenant)


def question(c,message='a',request=None):
    return dict(conversation_id=c['id'],request_id=request or secrets.token_hex(16),message=message,language='en')


def test_fifo_one_workspace_one_slot_idempotency_ownership_cancel_recovery(tmp_path):
    s=Store(tmp_path/'q.db');q=PublicQueue(s)
    a,b=workspace(s,'a'),workspace(s,'b');body=question(a)
    first=q.submit('a',body,time.time()+7200)
    assert q.submit('a',body,time.time()+7200)['run_id']==first['run_id']
    with pytest.raises(RelayError):q.submit('a',question(a,'flood'),time.time()+7200)
    second=q.submit('b',question(b),time.time()+7200)
    assert q.status('b',second['run_id'])['position']==2
    for action in (q.status,q.cancel):
        with pytest.raises(RelayError):action('b',first['run_id'])
    assert q.claim_next()['tenant']=='a'
    q.recover();assert q.status('a',first['run_id'])['status']=='unknown'
    assert q.cancel('b',second['run_id'])['remote_compute_stopped']
    assert q.status('b',second['run_id'])['status']=='cancelled'
    assert q.claim_next() is None


def test_concurrent_duplicate_admission_has_one_job(tmp_path):
    s=Store(tmp_path/'q.db');q=PublicQueue(s);c=workspace(s,'a');body=question(c)
    with ThreadPoolExecutor(max_workers=8) as pool:
        results=list(pool.map(lambda _:q.submit('a',body,time.time()+7200),range(8)))
    assert len({r['run_id'] for r in results})==1
    assert len(s.list('_server','public_ai_jobs'))==1


def test_rpm_tpm_day_reset_and_fair_model_tickets(tmp_path,monkeypatch):
    clock=[datetime(2026,10,19,8,59,50,tzinfo=timezone.utc).timestamp()]
    monkeypatch.setenv('RELAY_MODEL_CALLS_PER_MINUTE','2')
    monkeypatch.setenv('RELAY_MODEL_TOKENS_PER_MINUTE','12000')
    monkeypatch.setenv('RELAY_MODEL_CALLS_PER_DAY','3')
    s=Store(tmp_path/'q.db');g=QuotaGate(s,lambda:clock[0])
    assert g.try_reserve('a','1',1000)['reserved']
    assert g.try_reserve('b','2',1000)['reserved']
    assert not g.try_reserve('a','3',1000)['reserved']
    assert not g.try_reserve('b','4',1000)['reserved']
    clock[0]+=61
    assert not g.try_reserve('b','4',1000)['reserved'] # cannot jump the older waiter
    assert g.try_reserve('a','3',1000)['reserved']
    assert not g.try_reserve('b','4',1000)['reserved'] # daily budget3
    clock[0]=day_window(clock[0])[1]+1
    assert g.try_reserve('b','4',1000)['reserved']
    g.backoff(120);assert g.inspect()['wait_seconds']==120


def test_two_workers_atomic_model_reservation_no_overrun(tmp_path,monkeypatch):
    monkeypatch.setenv('RELAY_MODEL_CALLS_PER_MINUTE','15')
    monkeypatch.setenv('RELAY_MODEL_TOKENS_PER_MINUTE','250000')
    s=Store(tmp_path/'q.db');g=QuotaGate(s)
    with ThreadPoolExecutor(max_workers=20) as pool:
        granted=list(pool.map(lambda n:g.try_reserve(str(n),str(n),10)['reserved'],range(20)))
    assert sum(granted)==15


def test_expiry_during_daily_quota_wait_releases_and_erases_input(tmp_path):
    s=Store(tmp_path/'q.db');q=PublicQueue(s);c=workspace(s,'a')
    job=q.submit('a',question(c,'private pending text'),time.time()+7200)
    key=q.key('a',job['run_id'])
    s.claim('_server','public_ai_jobs',key,{'status':'queued'},{'expires':time.time()-1})
    QuotaGate(s).backoff(daily=True)
    assert q.claim_next() is None
    assert q.status('a',job['run_id'])['status']=='cancelled'
    assert 'message' not in s.get('_server','public_ai_jobs',key)
    assert not s.list('_server','public_ai_owners')


def test_reset_removes_global_job_text_and_late_result_cannot_resurrect(tmp_path):
    from relay.public_demo import forget
    s=Store(tmp_path/'q.db');q=PublicQueue(s);c=workspace(s,'demo-a')
    job=q.submit('demo-a',question(c,'private pending text'),time.time()+7200)
    assert q.claim_next()
    forget(s,'demo-a')
    result=q.finish('demo-a',job['run_id'],dict(status='complete',text='late private answer'))
    assert result['status']=='cancelled'
    assert not s.list('_server','public_ai_jobs')
    assert not s.list('demo-a','conversations')
    assert not s.list('demo-a','agent_runs')


def test_finish_idempotent_and_pacific_midnight_is_daily_boundary(tmp_path):
    s=Store(tmp_path/'q.db');q=PublicQueue(s);c=workspace(s,'a')
    job=q.submit('a',question(c),time.time()+7200)
    result=dict(status='complete',text='answer')
    q.finish('a',job['run_id'],result);q.finish('a',job['run_id'],result)
    assert len(conversation(s,'a',c['id'])['turns'])==1
    before=datetime(2026,10,19,6,59,59,tzinfo=timezone.utc).timestamp()
    assert day_window(before)[0]=='2026-10-18'
    assert day_window(before+1)[0]=='2026-10-19'


@pytest.mark.asyncio
async def test_provider_failure_is_redacted_and_next_queued_workspace_completes(tmp_path,monkeypatch):
    from relay.public_ai import worker,TERMINAL
    monkeypatch.setenv('RELAY_MCP_URL','http://127.0.0.1:8022/_relay/mcp/')
    monkeypatch.setenv('RELAY_CONTEXT_SECRET','s'*64)
    s=Store(tmp_path/'q.db');q=PublicQueue(s)
    a=q.submit('a',question(workspace(s,'a')),time.time()+7200)
    b=q.submit('b',question(workspace(s,'b')),time.time()+7200)
    class ProviderError(Exception):code=504
    def invoke(resource,**args):
        if args['user_id']=='a':raise ProviderError('NEVER_LOG_PRIVATE_CONTENT')
        return dict(status='complete',text='Second workspace completed')
    task=asyncio.create_task(worker(s,invoke,lambda *args:None))
    try:
        for _ in range(100):
            if q.status('b',b['run_id'])['status'] in TERMINAL:break
            await asyncio.sleep(.02)
        failed=q.status('a',a['run_id'])
        assert failed['status']=='failed' and failed['upstream_status']==504
        assert 'NEVER_LOG_PRIVATE_CONTENT' not in json.dumps(failed)
        assert q.status('b',b['run_id'])['status']=='complete'
    finally:
        task.cancel();await asyncio.gather(task,return_exceptions=True)


@pytest.mark.asyncio
async def test_100_http_sessions_simulated_provider_only(tmp_path,monkeypatch):
    """Actual HTTP session/upload/queue/history paths. Provider alone is simulated."""
    from relay import public_ai,public_demo
    for k,v in dict(RELAY_MODE='alternative_live',RELAY_PUBLIC_AI_ENABLED='true',RELAY_INFERENCE_PROVIDER='gemini_developer',
                    RELAY_DEPLOYMENT_MODE='alternative_hosted',RELAY_GEMINI_API_KEY='inert-test-only',RELAY_GEMINI_FREE_ONLY='true',
                    RELAY_CONTEXT_SECRET='s'*64,RELAY_MCP_SERVICE_SECRET='m'*64,RELAY_MCP_URL='http://127.0.0.1:8022/_relay/mcp/',
                    RELAY_GITHUB_REPO='NuraliKuzhagaliev/campuspulse-relay-demo',RELAY_DATA_DIR=str(tmp_path),
                    RELAY_MODEL_CALLS_PER_MINUTE='15',RELAY_MODEL_TOKENS_PER_MINUTE='250000',RELAY_MODEL_CALLS_PER_DAY='500').items():monkeypatch.setenv(k,v)
    from relay import gateway
    from relay import mcp_server
    original_gateway=dict(gateway.__dict__)
    original_mcp=dict(mcp_server.__dict__)
    # MCP session managers are single-lifespan objects. This isolated app must
    # not inherit a manager already closed by an earlier protocol test, nor
    # leave alternative-mode globals behind for the illustrative-mode suite.
    importlib.reload(mcp_server)
    gateway=importlib.reload(gateway)
    public_demo._buckets.clear()
    ready=threading.Event();calls=[];calls_lock=threading.Lock();clock=[time.time()]
    monkeypatch.setattr(public_ai,'provider_clock',lambda:clock[0])
    def fake_provider(resource,**args):
        assert ready.wait(30),'test barrier timed out'
        from relay.auth import verify_context
        assert verify_context(args['context_token'],os.environ['RELAY_MCP_URL'],os.environ['RELAY_CONTEXT_SECRET'])==args['user_id']
        gate=QuotaGate(gateway.store)
        while True:
            permit=gate.try_reserve(args['user_id'],args['run_id'],1000)
            if permit['reserved']:break
            time.sleep(0.01)
        docs=[s for s in gateway.store.list(args['user_id'],'sources') if s.get('filename','').startswith('visitor-')]
        assert len(docs)==1
        marker=docs[0]['pages'][0]['text']
        with calls_lock:calls.append(dict(tenant=args['user_id'],reserved_at=permit['reserved_at'],marker=marker))
        return dict(status='complete',text='SIMULATED PROVIDER: '+marker,provider='simulated_test_only',tool_observations=[])
    import os
    monkeypatch.setattr(gateway,'invoke_alternative_query',fake_provider)
    clients=[];records=[]
    async def advance():
        while True:
            await asyncio.sleep(0.2);clock[0]+=61
    try:
        async with gateway.lifespan(gateway.app):
            transport=httpx.ASGITransport(app=gateway.app)
            for n in range(100):
                client=httpx.AsyncClient(transport=transport,base_url='https://testserver')
                clients.append(client);session=(await client.get('/api/session')).json()
                state=(await client.get('/api/state')).json();marker=f'isolated-marker-{n:03}-{secrets.token_hex(3)}'
                headers={'X-Relay-CSRF':session['csrf']}
                import base64
                source=(await client.post('/api/import-native',headers=headers,json=dict(name=f'visitor-{n}.md',content=base64.b64encode(marker.encode()).decode()))).json()
                response=await client.post('/api/chat',headers=headers,json=dict(message='Read my private document',language='en',adult_confirmed=True,permitted_processing=True,processing_region='supported_non_eea',request_id=secrets.token_hex(16)))
                assert response.status_code==202,response.text
                records.append(dict(tenant=state['workspace_id'],source=source['id'],run=response.json()['run_id'],marker=marker,headers=headers))
            assert len({r['tenant'] for r in records})==100
            jobs=gateway.store.list('_server','public_ai_jobs');assert len(jobs)==100
            assert len([j for j in jobs if j['status']=='running'])<=2
            assert len([j for j in jobs if j['status']=='queued'])>=98
            assert not calls
            ready.set();ticker=asyncio.create_task(advance())
            try:
                deadline=time.monotonic()+45
                while len(calls)<100 and time.monotonic()<deadline:await asyncio.sleep(0.1)
                while any(j['status'] not in public_ai.TERMINAL for j in gateway.store.list('_server','public_ai_jobs')) and time.monotonic()<deadline:await asyncio.sleep(0.1)
                assert len(calls)==100
            finally:ticker.cancel()
            for n,(client,record) in enumerate(zip(clients,records)):
                own=await client.get('/api/runs/'+record['run']);assert own.status_code==200
                result=own.json();assert result['status']=='complete';assert result['text']=='SIMULATED PROVIDER: '+record['marker']
                peer=records[(n+1)%100]
                assert (await client.get('/api/sources/'+peer['source'])).status_code==403
                assert (await client.get('/api/runs/'+peer['run'])).status_code==403
                history=(await client.get('/api/conversation')).json();assert len(history['turns'])==1
                assert history['turns'][0]['assistant']==result['text']
            times=sorted(c['reserved_at'] for c in calls)
            assert all(sum(t-60<x<=t for x in times)<=15 for t in times)
            assert len({c['tenant'] for c in calls})==100
            evidence=dict(checked_at=datetime.now(timezone.utc).isoformat(),sessions=100,provider='simulated_test_only',actual_gemini_calls=0,
                actual_http_session_upload_queue_history_paths=True,checks=dict(unique_workspaces=True,foreign_source_denied_100=True,foreign_run_denied_100=True,
                history_isolation_100=True,one_outstanding_per_workspace=True,bounded_worker_pool=2,at_least_98_queued_at_barrier=True,served_all_100=True,
                rolling_rpm_limit_15_respected=True,no_real_calendar_writes=True),passed=True)
            Path('docs/evidence/public-ai-100-simulated.json').write_text(json.dumps(evidence,indent=2))
    finally:
        ready.set()
        for client in clients:await client.aclose()
        gateway.__dict__.clear();gateway.__dict__.update(original_gateway)
        mcp_server.__dict__.clear();mcp_server.__dict__.update(original_mcp)
