import time
from concurrent.futures import ThreadPoolExecutor
import pytest
from fastapi.testclient import TestClient
from relay import gateway
from relay.domain import RelayError
from relay.judge import register,claim
from relay.limits import model_request
from relay.service import RelayService
from relay.store import Store


@pytest.fixture
def setup(tmp_path,monkeypatch):
    store=Store(tmp_path/'judge.db')
    monkeypatch.setenv('RELAY_JUDGE_ENABLED','true')
    monkeypatch.setenv('RELAY_GITHUB_REPO','owner/dedicated-demo')
    return store


def test_one_use_concurrent_claim_and_never_reuse_calendar(setup):
    invitation=register(setup,'exclusive@group.calendar.google.com')
    def enter():
        try:
            return claim(setup,invitation)
        except RelayError:
            return None
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(lambda _:enter(),range(2)))
    assert sum(value is not None for value in results)==1
    tenant,_=next(value for value in results if value is not None)
    setup.delete_workspace(tenant)
    with pytest.raises(RelayError,match='cannot be reused'):
        register(setup,'exclusive@group.calendar.google.com')


def test_expiry_and_disabled_entry(setup,monkeypatch):
    invitation=register(setup,'expires@group.calendar.google.com')
    tenant,_=claim(setup,invitation)
    value=setup.get(tenant,'meta','settings');value['judge_expires']=time.time()-1
    setup.put(tenant,'meta','settings',value)
    with pytest.raises(RelayError,match='expired'):
        RelayService(setup,tenant).settings()
    monkeypatch.setenv('RELAY_JUDGE_ENABLED','false')
    with pytest.raises(RelayError,match='not enabled'):
        claim(setup,'a'*43)
    with pytest.raises(RelayError):
        register(setup,'primary')


def test_judge_http_identity_upload_isolation_and_fixed_calendar(setup,monkeypatch):
    monkeypatch.setattr(gateway,'store',setup)
    monkeypatch.setattr(gateway,'CLOUD',True)
    first=register(setup,'first@group.calendar.google.com')
    second=register(setup,'second@group.calendar.google.com')
    with TestClient(gateway.app,base_url='https://testserver') as a, TestClient(gateway.app,base_url='https://testserver') as b:
        for client,invitation in ((a,first),(b,second)):
            opened=client.post('/api/judge/claim',json={'invitation':invitation})
            assert opened.status_code==200
            assert 'Secure' in opened.headers['set-cookie'] and 'HttpOnly' in opened.headers['set-cookie']
            client.headers['X-Relay-CSRF']=opened.json()['csrf']
        imported=a.post('/api/import',files={'file':('judge-unseen.md',b'Assignment: Private unseen lab\nEffort: 60 minutes')})
        assert imported.status_code==200
        source_id=imported.json()['id']
        assert a.get('/api/sources/'+source_id).status_code==200
        assert b.get('/api/sources/'+source_id).status_code==403
        assert b.post('/api/connections/calendar',json={'calendar_id':'first@group.calendar.google.com'}).status_code==403
        assert b.post('/api/judge/claim',json={'invitation':first}).status_code==403


def test_judge_reserved_capacity_and_global_cap(setup,monkeypatch):
    monkeypatch.setenv('RELAY_REQUESTS_TOTAL_DAY','3')
    monkeypatch.setenv('RELAY_JUDGE_RESERVED_REQUESTS','2')
    model_request(setup,'personal')
    with pytest.raises(RelayError,match='allowance'):
        model_request(setup,'personal')
    model_request(setup,'judge-a',judge=True)
    model_request(setup,'judge-b',judge=True)
    with pytest.raises(RelayError,match='allowance'):
        model_request(setup,'judge-c',judge=True)
