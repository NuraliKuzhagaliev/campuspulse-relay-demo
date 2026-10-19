import time
import pytest
from fastapi.testclient import TestClient
from relay import gateway, public_demo
from relay.store import Store
from relay.domain import digest, RelayError


@pytest.fixture
def demo(tmp_path, monkeypatch):
    monkeypatch.setenv('RELAY_MODE','public_demo')
    monkeypatch.setenv('RELAY_GATEWAY_URL','https://demo.test')
    monkeypatch.setattr(gateway,'PUBLIC_DEMO',True)
    monkeypatch.setattr(gateway,'store',Store(tmp_path/'demo.sqlite3'))
    public_demo._buckets.clear()
    public_demo._public_cache.clear()
    with TestClient(gateway.app,base_url='https://demo.test') as client:
        session=client.get('/api/session')
        assert 'Secure' in session.headers['set-cookie']
        assert 'HttpOnly' in session.headers['set-cookie']
        assert 'SameSite=strict' in session.headers['set-cookie']
        client.headers['X-Relay-CSRF']=session.json()['csrf']
        yield client


def test_public_workflow_is_scoped_and_simulated(demo):
    assert demo.get('/api/session').json()['mode']=='public_demo'
    initial=demo.get('/api/state').json()
    assert initial['demo']['public'] and initial['demo']['session_seconds']==7200
    raw=b'Assignment: Network Security lab\nDue: 2026-10-21T18:00:00+05:00\nEffort: 240 minutes\n- [ ] New unseen rubric evidence'
    result=demo.post('/api/import',files={'file':('new-sample.md',raw)})
    assert result.status_code==200,result.text
    source=result.json()
    draft=source['drafts'][0]
    target=next(t for t in initial['tasks'] if t['title']=='Network Security lab')
    assert demo.post('/api/sources/'+source['id']+'/mapping',json={'section_key':draft['section_key'],'target_id':target['id']}).status_code==200
    assert demo.get('/api/sources/'+source['id']).json()['pages'][0]['text']==raw.decode()
    with TestClient(gateway.app,base_url='https://demo.test') as other:
        visitor=other.get('/api/session').json()
        assert visitor['tenant']!=initial['workspace_id']
        assert other.get('/api/sources/'+source['id']).status_code==403
    state=demo.get('/api/state').json()
    for conflict in state['conflicts']:
        chosen=min(conflict['facts'],key=lambda f:f['value'])
        assert demo.post('/api/conflicts/'+conflict['id']+'/resolve',json={'fact_id':chosen['id']}).status_code==200
    plan=demo.post('/api/plan').json()
    assert plan['feasible']
    scenario=demo.post('/api/scenario',json={'remove_weekday':2}).json()
    assert not scenario['feasible']
    assert demo.get('/api/state').json()['plan']['id']==plan['id']
    preview=demo.post('/api/plans/'+plan['id']+'/preview').json()
    assert preview['mode']=='illustrative'
    receipt=demo.post('/api/previews/'+preview['id']+'/approve',json={'digest':preview['digest']})
    assert receipt.status_code==200,receipt.text
    assert receipt.json()['status']=='verified'
    assert not demo.get('/api/state').json()['settings']['calendar_live']


def test_public_denies_internal_google_and_test_routes(demo):
    for path in ['/internal/sync','/api/judge/claim','/api/auth/google','/api/auth/start','/api/connections/calendar','/api/admin','/api/test/seed','/mcp/','/docs','/openapi.json','/connect','/auth/callback']:
        response=demo.get(path) if path in ['/docs','/openapi.json','/connect','/auth/callback','/api/auth/start','/mcp/'] else demo.post(path,json={})
        assert response.status_code==403,(path,response.text)
    response=demo.post('/api/chat',json={'message':'Pretend you connected Gemini'})
    assert response.status_code==401
    assert 'not connected' in response.json()['error']['message']
    assert demo.post('/api/preferences',json={'watch_enabled':True}).status_code==403
    assert demo.post('/api/preferences',json={'daily_cap_minutes':240},headers={'Origin':'https://attacker.test'}).status_code==403
    assert demo.post('/api/preferences',json={'daily_cap_minutes':240},headers={'X-Relay-CSRF':'bad'}).status_code==403


def test_public_passport_fresh_copy_and_additions_scope(demo):
    import base64,json
    before=demo.get('/api/state').json();assert demo.get('/api/additions').status_code==200
    export=demo.post('/api/passport/export',json={});assert export.status_code==200,export.text
    payload={'name':'transfer.relay.json','content':base64.b64encode(json.dumps(export.json()['file']).encode()).decode()}
    stage=demo.post('/api/passport/preview',json=payload);assert stage.status_code==200,stage.text
    with TestClient(gateway.app,base_url='https://demo.test') as other:
        other.headers['X-Relay-CSRF']=other.get('/api/session').json()['csrf']
        assert other.post('/api/passport/'+stage.json()['id']+'/restore').status_code==403
    switched=demo.post('/api/passport/'+stage.json()['id']+'/restore');assert switched.status_code==200,switched.text
    assert switched.json()['tenant'].startswith('demo-') and switched.json()['tenant']!=before['workspace_id']
    demo.headers['X-Relay-CSRF']=switched.json()['csrf']
    after=demo.get('/api/state').json();assert all(s['mode']=='archived_portable_extract' for s in after['sources'])
    assert after['receipts']==[] and after['plan'] is None
    # Wrong methods, arbitrary paths, credentials and a public repository expansion remain closed.
    assert demo.get('/api/passport/export').status_code==403
    assert demo.post('/api/gates',json=dict(task_id=after['tasks'][0]['id'],repo='pallets/flask',number=6168,request_id='a'*24,expected_revision=1)).status_code==403


def test_notification_claim_is_durable_and_scoped(demo):
    tenant=demo.get('/api/state').json()['workspace_id'];id='a'*24
    gateway.store.put(tenant,'handoff_notifications',id,dict(id=id,task_id='b'*24))
    assert demo.post('/api/gates/notifications/'+id+'/claim').json()==dict(claimed=True,visibility_verified=False)
    assert demo.post('/api/gates/notifications/'+id+'/claim').json()==dict(claimed=False)
    with TestClient(gateway.app,base_url='https://demo.test') as other:
        other.headers['X-Relay-CSRF']=other.get('/api/session').json()['csrf']
        assert other.post('/api/gates/notifications/'+id+'/claim').status_code==403


def test_public_body_limits_cover_streamed_uploads(demo):
    assert demo.post('/api/import',files={'file':('huge.md',b'a'*(2*1024*1024+1))}).status_code==409
    def chunked():
        yield b'a'*(2*1024*1024)
        yield b'b'*(2*1024*1024)
    assert demo.post('/api/import',content=chunked(),headers={'Content-Type':'application/octet-stream'}).status_code==413


def test_public_reset_expiry_and_cache_preserve_isolation(demo):
    before=demo.get('/api/state').json()
    assert demo.get('/api/events').json()['workspace_id']==before['workspace_id']
    reset=demo.post('/api/demo/reset').json()
    assert reset['tenant']!=before['workspace_id']
    assert gateway.store.list(before['workspace_id'],'sources')==[]
    demo.headers['X-Relay-CSRF']=reset['csrf']
    assert demo.get('/api/events').json()['workspace_id']==reset['tenant']
    demo.get('/api/state')
    token=demo.cookies.get('relay_session')
    record=gateway.store.get('_server','sessions',digest(token))
    gateway.store.put('_server','sessions',digest(token),dict(record,expires=time.time()-1))
    public_demo.cleanup(gateway.store)
    assert gateway.store.list(reset['tenant'],'sources')==[]
    assert demo.get('/api/state').status_code==401
    assert demo.get('/api/session').json()['tenant']!=reset['tenant']
    calls=[]
    def read():
        calls.append(1)
        return dict(text='public text',commit='known-commit',fetched_at='original-time')
    one=public_demo.read_public_source('owner/demo','main','coursework.md',read)
    two=public_demo.read_public_source('owner/demo','main','coursework.md',read)
    assert len(calls)==1 and one['fetched_at']==two['fetched_at']=='original-time'
    assert two['commit']=='known-commit'


def test_public_refuses_cloud_config_and_bounds_requests(monkeypatch):
    for key in ['RELAY_AGENT_RESOURCE','GOOGLE_CLOUD_PROJECT','RELAY_OAUTH_CLIENT_ID','RELAY_OAUTH_CLIENT_SECRET','RELAY_TOKEN_ENCRYPTION_KEY','RELAY_MCP_URL']:
        monkeypatch.delenv(key,raising=False)
    public_demo.configuration()
    monkeypatch.setenv('GOOGLE_CLOUD_PROJECT','not-authorized')
    with pytest.raises(RuntimeError):public_demo.configuration()
    public_demo._buckets.clear()
    public_demo.limit('scope','operation',1)
    with pytest.raises(RelayError):public_demo.limit('scope','operation',1)
