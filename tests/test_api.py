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


def test_upload_path_rejected(client):
    assert client.post('/api/import',files={'file':('../escape.md',b'Assignment: Lab')}).status_code==403
