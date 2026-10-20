"""Workspace choice enforcement and lossless legacy Passport timezone handling."""
import json
import pytest
from fastapi.testclient import TestClient
from relay import gateway
from relay.domain import instant
from relay.service import RelayService
from relay.store import Store
from relay.passport import export, stage, commit, checksum
from relay.timezones import WORKSPACE_TIMEZONES


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv('RELAY_MODE','local')
    monkeypatch.setattr(gateway,'CLOUD',False)
    monkeypatch.setattr(gateway,'PUBLIC_DEMO',False)
    monkeypatch.setattr(gateway,'TEMPORARY_WEB',False)
    monkeypatch.setattr(gateway,'ALTERNATIVE',False)
    monkeypatch.setattr(gateway,'store',Store(tmp_path/'timezone.sqlite3'))
    with TestClient(gateway.app) as client:
        session=client.get('/api/session').json()
        client.headers['X-Relay-CSRF']=session['csrf']
        yield client


def context(zone):
    return dict(timezone=zone,start_date='2026-10-21',end_date='2026-10-21',start_time='18:00',end_time='18:30',weekdays=[2])


@pytest.mark.parametrize('zone,offset',[('Asia/Almaty','+05:00'),('Europe/Moscow','+03:00'),('UTC','+00:00')])
def test_three_workspace_zones_generate_exact_offsets(client,zone,offset):
    response=client.post('/api/planning-context',json=context(zone))
    assert response.status_code==200
    value=response.json()
    assert value['timezone']==zone and len(value['windows'])==1
    assert value['windows'][0]['start'].endswith(offset)
    assert instant(value['windows'][0]['end'])-instant(value['windows'][0]['start'])==__import__('datetime').timedelta(minutes=30)
    assert client.post('/api/preferences',json={'timezone':zone}).status_code==200


@pytest.mark.parametrize('zone',['авва','', 'UTC ', 'Europe/London','America/New_York','Asia/Qyzylorda','Etc/GMT','../UTC'])
@pytest.mark.parametrize('route',['/api/preferences','/api/planning-context'])
def test_direct_api_cannot_bypass_timezone_choices_or_change_state(client,zone,route):
    before=client.get('/api/state').json()['settings']
    body={'timezone':zone} if route.endswith('preferences') else context(zone)
    response=client.post(route,json=body)
    assert response.status_code==409
    assert response.json()['error']['code']=='UNSUPPORTED_TIMEZONE'
    assert client.get('/api/state').json()['settings']==before


@pytest.mark.parametrize('original,target',[('Asia/Qyzylorda','Asia/Almaty'),('America/New_York','UTC')])
def test_legacy_passport_previews_supported_zone_without_losing_instants(tmp_path,original,target):
    svc=RelayService(Store(tmp_path/'portable.sqlite3'),'owner');svc.create_empty()
    svc.import_source('legacy-note.md',b'An original historical note without coursework fields.')
    archive=export(svc)['file'];archive['payload']['preferences'].update(timezone=original,windows=[dict(start='2026-10-21T18:00:00-04:00',end='2026-10-21T18:30:00-04:00')])
    archive['sha256']=checksum(archive['payload'])
    preview=stage(svc,json.dumps(archive).encode())
    assert preview['original_timezone']==original and preview['restored_timezone']==target
    result=commit(svc,preview['id']);restored=RelayService(svc.store,result['tenant'])
    assert restored.settings()['timezone']==target and target in WORKSPACE_TIMEZONES
    assert restored.settings()['portable_original_timezone']==original
    assert restored.settings()['windows']==archive['payload']['preferences']['windows']
    assert svc.settings()['timezone']=='Asia/Almaty'  # The original workspace stays untouched.


@pytest.mark.parametrize('zone',WORKSPACE_TIMEZONES)
@pytest.mark.parametrize('deadline',['2026-10-23T18:00:00+05:00','2026-10-23T09:00:00-04:00','2026-10-23T13:00:00Z'])
def test_review_uses_explicit_source_offset_not_workspace_display_zone(client,zone,deadline):
    assert client.post('/api/preferences',json={'timezone':zone}).status_code==200
    text=f'Assignment: Clock report\nCourse: Clock science\nTerm: Autumn 2026\nAssignment ID: clock-source\nDue: {deadline}\nEffort: 30 minutes'
    imported=client.post('/api/import',files={'file':('clock.md',text.encode(),'text/markdown')})
    assert imported.status_code==200
    source=imported.json();response=client.post('/api/sources/'+source['id']+'/review')
    assert response.status_code==200
    proposal=response.json();due=next(f for f in proposal['fields'] if f['field']=='due')
    assert instant(due['value'])==instant(deadline)
    assert due['quote']=='Due: '+deadline and due['validation_status']=='needs_confirmation'
