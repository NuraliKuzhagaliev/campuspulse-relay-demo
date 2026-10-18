import pytest
from fastapi.testclient import TestClient
from relay import gateway
from relay.store import Store


@pytest.fixture
def managed_client(tmp_path,monkeypatch):
    monkeypatch.setattr(gateway,'store',Store(tmp_path/'managed.db'))
    monkeypatch.setenv('RELAY_AGENT_RESOURCE','projects/contract/locations/test/reasoningEngines/contract')
    monkeypatch.setenv('RELAY_AGENT_REVISION','contract-double-only')
    monkeypatch.setenv('RELAY_MCP_URL','https://mcp.contract/mcp/')
    monkeypatch.setenv('RELAY_CONTEXT_SECRET','contract-secret'*4)
    with TestClient(gateway.app) as c:
        s=c.get('/api/session').json();c.headers['X-Relay-CSRF']=s['csrf']
        c.get('/api/state')
        yield c


def test_gateway_multi_turn_duplicate_empty_and_tool_failure(managed_client,monkeypatch):
    c=managed_client;calls=[]
    def remote(resource,**kw):
        calls.append(kw)
        return {'text':'First option Monday; second option Tuesday.','status':'complete'}
    monkeypatch.setattr(gateway,'invoke_managed_query',remote)
    conversation=c.get('/api/conversation').json()['id']
    body=dict(message='Plan my week',conversation_id=conversation,request_id='first-request-12345')
    assert c.post('/api/chat',json=body).json()['status']=='complete'
    assert c.post('/api/chat',json=body).json()['status']=='complete' and len(calls)==1
    body.update(message='Keep Wednesday free and use the second option',request_id='second-request-12345')
    assert c.post('/api/chat',json=body).json()['status']=='complete'
    assert calls[-1]['history'][0]['assistant'].endswith('Tuesday.')
    monkeypatch.setattr(gateway,'invoke_managed_query',lambda *a,**k:{'text':'','status':'complete'})
    body.update(request_id='third-request-12345')
    assert c.post('/api/chat',json=body).json()['status']=='failed'
    assert c.get('/api/state').json()['events'][-1]['type']=='run_failed'
    monkeypatch.setattr(gateway,'invoke_managed_query',lambda *a,**k:{'text':'Some evidence retained','status':'complete','required_tool_failed':True})
    body.update(request_id='fourth-request-12345')
    assert c.post('/api/chat',json=body).json()['status']=='partial'
    fresh=c.post('/api/conversation/new').json()
    assert fresh['id']!=conversation and not fresh['turns']
    assert c.post('/api/chat',json=body).status_code==401


def test_two_tenants_cannot_read_or_cancel_conversations(managed_client,monkeypatch):
    c=managed_client
    convo=c.get('/api/conversation').json()['id']
    with TestClient(gateway.app) as other:
        session=other.get('/api/session').json();other.headers['X-Relay-CSRF']=session['csrf']
        assert other.post('/api/chat',json=dict(message='Read previous context',conversation_id=convo,request_id='other-request-12345')).status_code==403
        assert other.post('/api/runs/'+'a'*32+'/cancel').status_code==403
