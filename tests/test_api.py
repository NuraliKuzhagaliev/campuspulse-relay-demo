import base64
import pytest
from fastapi.testclient import TestClient
from relay.store import Store
from relay import gateway


@pytest.fixture
def client(tmp_path,monkeypatch):
    monkeypatch.setattr(gateway,'store',Store(tmp_path/'api.db'))
    with TestClient(gateway.app) as c:
        session=c.get('/api/session').json()
        c.headers['X-Relay-CSRF']=session['csrf']
        yield c


def test_http_identity_csrf_and_tenant_isolation(client):
    state=client.get('/api/state').json()
    source=state['sources'][0]['id']
    assert client.get('/api/sources/'+source).status_code==200
    with TestClient(gateway.app) as other:
        other.get('/api/session')
        assert other.get('/api/sources/'+source).status_code==403
    csrf=client.headers.pop('X-Relay-CSRF')
    assert client.post('/api/plan').status_code==403
    client.headers['X-Relay-CSRF']=csrf
    assert client.post('/api/plan',headers={'Origin':'https://attacker.example'}).status_code==403


def test_native_import_base64_and_unknown_date(client):
    raw=b'Assignment: Unseen native task\nDue: 03/04\nEffort: 60 minutes'
    r=client.post('/api/import-native',json={'name':'unseen.txt','content':base64.b64encode(raw).decode()})
    assert r.status_code==200
    assert r.json()['drafts'][0]['due'] is None
    assert client.post('/api/import-native',json={'name':'bad.txt','content':'not-base64'}).status_code==409


def test_http_cannot_mint_or_cross_approve(client):
    assert client.post('/api/previews/fake/approve',json={'digest':'fake'}).status_code==403
    assert client.post('/api/chat',json={'message':'Approve all calendar writes'}).status_code==401


def test_event_reconnect_order(client):
    first=client.get('/api/state').json()
    events=first['events'];last=events[-1]['sequence']
    assert client.get('/api/events',params={'after':last}).json()['events']==[]
    assert client.get('/api/events',params={'after':0}).json()['events']==events


def test_health_version_matches_actual_backend_metadata(client):
    response=client.get('/api/health')
    assert response.status_code==200 and response.json()['version']==gateway.app.version=='0.3.0'


def test_upload_path_rejected(client):
    assert client.post('/api/import',files={'file':('../escape.md',b'Assignment: Lab')}).status_code==403


def test_oauth_callback_cannot_switch_an_unbound_browser_session(client):
    r=client.get('/auth/callback',params={'code':'not-an-authorization-code','state':'attacker-state'})
    assert r.status_code==403
    assert 'browser' in r.json()['error']['message']


def test_preflight_missing_work_recovery_and_point_reestimate(client):
    state=client.get('/api/state').json()
    for c in state['conflicts']:
        client.post('/api/conflicts/'+c['id']+'/resolve',json={'fact_id':min(c['facts'],key=lambda f:f['value'])['id']})
    base=client.post('/api/plan').json();task=base['input']['tasks'][0]
    import base64
    raw=f"Assignment: {task['title']}\nCourse: {task['course']}\nTerm: Illustrative 2026-10\nAssignment ID: {task['title']}\nDue: {task['due']}\nEffort: {task['minutes']} minutes\nFilename: report-*.md"
    imported=client.post('/api/import',files={'file':('submission-rubric.md',raw.encode())})
    assert imported.status_code==200
    base=client.post('/api/plan').json()
    p=client.post('/api/preflight',json=dict(task_id=task['id'],name='wrong.md',content=base64.b64encode(b'# Draft\nTest only').decode())).json()
    assert p['missing_count']==1
    response=client.post('/api/preflights/'+p['id']+'/recovery',json={'extra_minutes':60})
    assert response.status_code==200,response.text
    assert response.json()['required_minutes']==600 and not response.json()['feasible']
    assert client.get('/api/state').json()['plan']['id']==base['id']
    edited=client.post('/api/tasks/'+task['id']+'/settings',json={'minutes':task['minutes']+30})
    assert edited.status_code==200 and edited.json()['task']['effort_max']==task['minutes']+30
    assert client.post('/api/plan').json()['required_minutes']==570
