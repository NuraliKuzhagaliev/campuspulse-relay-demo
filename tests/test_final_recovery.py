"""Zero-provider regressions. These are not live Google/Gemini acceptance."""
import asyncio
import json
from types import SimpleNamespace
import pytest
from pydantic import ValidationError
from relay import oauth
from relay.domain import RelayError
from relay.store import Store
from relay.service import RelayService
from relay.extraction import extraction_proposal, page_citations
from relay.tool_diagnostics import schema_failure, safe_issues


def test_schema_error_keeps_locations_without_values():
    from relay.mcp_server import ExtractionCandidate
    secret='DO_NOT_PERSIST_PRIVATE_DOCUMENT_OR_TOKEN'
    with pytest.raises(ValidationError) as caught:
        ExtractionCandidate.model_validate(dict(field=secret,value=secret,page=1,quote=None,**{secret:secret}))
    failure=schema_failure(caught.value)
    assert failure['error']['code']=='TOOL_INPUT_INVALID'
    serialized=json.dumps(failure)
    assert secret not in serialized and 'literal_error' in serialized and ':redacted' in serialized
    assert safe_issues({'content':[{'type':'text','text':serialized}]})==failure['error']['details']['issues']
    assert 'UNKNOWN_PRIVATE_EXCEPTION' not in json.dumps(schema_failure(RuntimeError('UNKNOWN_PRIVATE_EXCEPTION')))


def test_reference_null_quote_is_accepted_but_literal_null_is_not(tmp_path):
    from relay.mcp_server import ExtractionCandidate
    svc=RelayService(Store(tmp_path/'refs.sqlite3'),'owner');svc.create_empty()
    source=svc.import_source('table.md',b'Assignment: Lattice map\nCourse: Solid state\nEffort: 45 minutes')
    reference=page_citations(source,1)[0]
    candidate=ExtractionCandidate(field='minutes',value=45,page=1,citation_id=reference['citation_id'],quote=None,original_expression=None).model_dump()
    result=extraction_proposal(source,[candidate]);assert result['fields'][0]['quote']==reference['quote']
    assert not result['applied']
    with pytest.raises(RelayError):extraction_proposal(source,[dict(candidate,citation_id=None)])
    with pytest.raises(RelayError):extraction_proposal(source,[dict(candidate,citation_id='a'*24)])


def test_actual_fastmcp_schema_failure_has_typed_redacted_result():
    from relay.mcp_server import RelayMCP, ExtractionCandidate
    server=RelayMCP('schema regression')
    @server.tool()
    def check(candidates:list[ExtractionCandidate])->dict:
        raise AssertionError('Invalid arguments must not reach the handler')
    result=asyncio.run(server.call_tool('check',{'candidates':[{'field':'PRIVATE_VALUE','value':'PRIVATE_VALUE','page':1}]}))
    assert result['error']['code']=='TOOL_INPUT_INVALID'
    assert 'PRIVATE_VALUE' not in json.dumps(result)


def test_calendar_recovery_reads_current_google_scope_without_selecting(tmp_path,monkeypatch):
    store=Store(tmp_path/'recovery.sqlite3');svc=RelayService(store,'owner');svc.create_empty()
    store.put('owner','private_connections','google',dict(ciphertext='OLD_TEST_CIPHER'))
    target='dedicated-test@group.calendar.google.com';calls=[]
    def credentials(*args):
        store.put('owner','private_connections','google',dict(ciphertext='REFRESHED_TEST_CIPHER'))
        return SimpleNamespace(scopes=oauth.SCOPES)
    monkeypatch.setattr(oauth,'credentials',credentials)
    class Session:
        def __init__(self,creds):pass
        def get(self,url,**kwargs):
            calls.append(url);return SimpleNamespace(status_code=200,json=lambda:dict(id=target,summary='Owned calendar',timeZone='Asia/Almaty'))
        def post(self,*args,**kwargs):raise AssertionError('No creation or event write permitted')
    monkeypatch.setattr('google.auth.transport.requests.AuthorizedSession',Session)
    result=oauth.recover_app_calendar(store,'owner',target)
    assert not result['selected'] and not result['events_written'] and len(calls)==1
    assert not svc.settings()['calendar_live']
    assert store.get('owner','private_connections','google')['ciphertext']=='REFRESHED_TEST_CIPHER'
    assert not store.list('visitor','private_connections')
    monkeypatch.setattr(oauth,'credentials',lambda *a:SimpleNamespace(scopes=oauth.EXISTING_SCOPES))
    with pytest.raises(RelayError):oauth.recover_app_calendar(store,'owner',target)
    monkeypatch.setattr(oauth,'credentials',lambda *a:SimpleNamespace(scopes=oauth.SCOPES+oauth.EXISTING_SCOPES))
    with pytest.raises(RelayError):oauth.recover_app_calendar(store,'owner',target)
    assert len(calls)==1


def test_connection_status_separates_consent_selection_and_actual_live_receipts(tmp_path,monkeypatch):
    from relay import gateway
    store=Store(tmp_path/'status.sqlite3');svc=RelayService(store,'owner');svc.create_empty()
    monkeypatch.setattr(gateway,'store',store);monkeypatch.setattr(oauth,'configuration',lambda:{})
    assert gateway.connection_status(svc)['acceptance']=='connection_required'
    store.put('owner','private_connections','google',dict(ciphertext='TEST_ONLY'))
    assert gateway.connection_status(svc)['acceptance']=='consent_complete_target_pending'
    settings=svc.settings();settings.update(calendar_live=True,calendar_id='owned-calendar');store.put('owner','meta','settings',settings)
    receipt=dict(mode='illustrative',status='verified',calendar_id='owned-calendar',outcomes=[{'status':'verified'}])
    store.put('owner','receipts','one',receipt)
    assert gateway.connection_status(svc)['acceptance']=='target_selected_read_back_pending'
    store.put('owner','receipts','one',dict(receipt,mode='live'))
    assert gateway.connection_status(svc)['acceptance']=='write_read_back_verified'
    store.put('owner','receipts','one',dict(receipt,mode='live',calendar_id='foreign-calendar'))
    assert gateway.connection_status(svc)['acceptance']=='target_selected_read_back_pending'


@pytest.mark.parametrize('target',['primary','owner@gmail.com','https://example.test/calendar','x\n@group.calendar.google.com'])
def test_calendar_recovery_rejects_urls_primary_and_control_characters(tmp_path,monkeypatch,target):
    monkeypatch.setattr(oauth,'credentials',lambda *a:pytest.fail('Bad IDs must be rejected before credentials or Google'))
    with pytest.raises(RelayError):oauth.recover_app_calendar(Store(tmp_path/'invalid.sqlite3'),'owner',target)


def test_calendar_recovery_rejects_google_denial_and_wrong_identity(tmp_path,monkeypatch):
    store=Store(tmp_path/'denied.sqlite3');store.put('owner','private_connections','google',dict(ciphertext='TEST'))
    monkeypatch.setattr(oauth,'credentials',lambda *a:SimpleNamespace(scopes=oauth.SCOPES))
    response=SimpleNamespace(status_code=403,json=lambda:{})
    monkeypatch.setattr('google.auth.transport.requests.AuthorizedSession',lambda *a:SimpleNamespace(get=lambda *a,**kw:response))
    with pytest.raises(RelayError):oauth.recover_app_calendar(store,'owner','own@group.calendar.google.com')
    response.status_code=200;response.json=lambda:dict(id='foreign@group.calendar.google.com',timeZone='Asia/Almaty')
    with pytest.raises(RelayError):oauth.recover_app_calendar(store,'owner','own@group.calendar.google.com')
    assert not store.get('owner','private_connections','google').get('app_calendar')
