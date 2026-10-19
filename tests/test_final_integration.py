import asyncio
import json
import time
from datetime import datetime, timezone, timedelta
import pytest
from relay.domain import RelayError, digest
from relay.store import Store
from relay.funding import validate_funding
from relay.providers import selected, current_availability
from relay.agent import tool_result_failed


@pytest.fixture
def clean_provider(monkeypatch):
    for name in ('RELAY_INFERENCE_PROVIDER','RELAY_DEPLOYMENT_MODE','RELAY_GEMINI_API_KEY','RELAY_GEMINI_FREE_ONLY','RELAY_AGENT_RESOURCE','RELAY_MODE'):
        monkeypatch.delenv(name,raising=False)


def test_funding_requires_exact_fresh_nonbillable_trial():
    at=datetime.now(timezone.utc)
    r=dict(source='gcp-free-trial',project_id='owned',billing_account='billingAccounts/test',
           account_type_human_confirmed='free_trial',eligibility_human_confirmed=True,
           covered_services_human_confirmed=True,no_personal_spending=True,billing_open_api_verified=True,
           credit_balance_api_verified=False,checked_at_utc=at.isoformat(),expires_at_utc=(at+timedelta(days=3)).isoformat(),
           balance_usd_human_confirmed=30,reserve_usd=10)
    assert validate_funding(r,'owned',15,24,'billingAccounts/test',at)['personal_spending_authorized_usd']==0
    for change in [dict(source='organizer-credits'),dict(account_type_human_confirmed='paid'),
                   dict(project_id='other'),dict(credit_balance_api_verified=True),dict(billing_open_api_verified=False),
                   dict(balance_usd_human_confirmed=20),dict(reserve_usd=0),dict(expires_at_utc=at.isoformat()),
                   dict(checked_at_utc=(at-timedelta(days=2)).isoformat())]:
        with pytest.raises(RelayError):validate_funding(r|change,'owned',15,24,'billingAccounts/test',at)


def test_provider_combinations_and_no_secret_in_metadata(clean_provider,monkeypatch):
    assert not selected()['configured']
    monkeypatch.setenv('RELAY_INFERENCE_PROVIDER','gemini_developer')
    assert not selected()['managed_agent_engine']
    monkeypatch.setenv('RELAY_GEMINI_API_KEY','private-test-secret')
    assert not selected()['configured']
    monkeypatch.setenv('RELAY_GEMINI_FREE_ONLY','true')
    assert selected()['configured'] and 'private-test-secret' not in json.dumps(selected())
    monkeypatch.setenv('RELAY_DEPLOYMENT_MODE','managed_gcp')
    with pytest.raises(RuntimeError):selected()
    monkeypatch.setenv('RELAY_MODE','public_demo')
    with pytest.raises(RuntimeError):selected()


def test_failed_freshness_does_not_leave_green_success(clean_provider,monkeypatch,tmp_path):
    monkeypatch.setenv('RELAY_AGENT_RESOURCE','managed-resource')
    s=Store(tmp_path/'db')
    s.put('_server','agent_evidence',digest('managed-resource'),dict(resource='managed-resource',revision='real-revision',observed_at='2026-10-19T01:00:00Z',expires=time.time()+300))
    assert current_availability(s)['verified']
    s.put('_server','agent_failures',digest('managed-resource'),dict(failed_at='2026-10-19T02:00:00Z',status='failed'))
    assert not current_availability(s)['verified']


def test_nested_tool_failures_are_not_green():
    assert tool_result_failed({'result':{'structuredContent':{'error':{'code':'ACCESS_DENIED'}}}})
    assert not tool_result_failed({'result':{'status':'verified','external_readback':True}})


def test_extraction_schema_and_redacted_typed_diagnostics():
    from relay.mcp_server import ExtractionCandidate
    from relay.agent import safe_error_codes
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        ExtractionCandidate(field='deadline',value='2026-10-23',page=1,quote='Due: 2026-10-23',original_expression='2026-10-23')
    candidate=ExtractionCandidate(field='due',value='2026-10-23T20:00:00+05:00',page=1,quote='Due: 2026-10-23T20:00:00+05:00',original_expression='2026-10-23T20:00:00+05:00',timezone='Asia/Qyzylorda',year_explicit=True)
    assert candidate.model_dump()['field']=='due'
    data={'content':[{'type':'text','text':json.dumps({'error':{'code':'SOURCE_CONFLICT','message':'private document text'}})}]}
    assert safe_error_codes(data)==['SOURCE_CONFLICT']
    assert safe_error_codes({'error':{'code':'private text with spaces'}})==[]


def test_adk_checkpoint_survives_service_recreation_without_tool_secrets(tmp_path):
    from relay.agent_sessions import RelaySessionService
    from relay.conversations import conversation
    from google.adk.events import Event
    from google.genai import types
    s=Store(tmp_path/'db'); c=conversation(s,'owner')
    async def scenario():
        service=RelaySessionService(s,'owner',c['id'])
        session=await service.create_session(app_name='campuspulse_relay',user_id='owner',session_id=c['id'])
        await service.append_event(session,Event(author='user',content=types.Content(role='user',parts=[types.Part(text='Compare option two.')])))
        await service.append_event(session,Event(author='campuspulse_relay',content=types.Content(role='model',parts=[types.Part(text='private hidden thought',thought=True),types.Part(text='Option two retains 95 minutes.')])))
        await service.append_event(session,Event(author='tool',content=types.Content(role='user',parts=[types.Part(function_response=types.FunctionResponse(name='read',response={'credential':'NEVER_PERSIST'}))])))
        other=RelaySessionService(Store(tmp_path/'db'),'owner',c['id'])
        restored=await other.get_session(app_name='campuspulse_relay',user_id='owner',session_id=c['id'])
        dump=restored.model_dump_json()
        assert '95 minutes' in dump and 'Compare option two' in dump
        assert 'NEVER_PERSIST' not in dump and 'private hidden thought' not in dump
        with pytest.raises(RelayError):await other.get_session(app_name='campuspulse_relay',user_id='foreign',session_id=c['id'])
        with pytest.raises(RelayError):await other.get_session(app_name='campuspulse_relay',user_id='owner',session_id='guessed')
        s.claim('owner','conversations',c['id'],{'closed':False},{'closed':True})
        with pytest.raises(RelayError):await other.get_session(app_name='campuspulse_relay',user_id='owner',session_id=c['id'])
    asyncio.run(scenario())


def test_free_consent_and_invitation_do_not_grant_calendar_authority(tmp_path,monkeypatch):
    from relay.judge import register_ai,claim
    from relay.service import RelayService
    from relay.alternative_live import authorize_query
    monkeypatch.setenv('RELAY_MODE','alternative_live')
    monkeypatch.setenv('RELAY_JUDGE_ENABLED','true')
    monkeypatch.setenv('RELAY_GITHUB_REPO','NuraliKuzhagaliev/campuspulse-relay-demo')
    s=Store(tmp_path/'db'); token=register_ai(s)
    tenant,expiry=claim(s,token)
    settings=RelayService(s,tenant).settings()
    assert settings['ai_access'] and not settings['calendar_live'] and settings['mode']=='judge_ai'
    assert RelayService(s,tenant).calendar().mode=='illustrative'
    with pytest.raises(RelayError):claim(s,token)
    with pytest.raises(RelayError):authorize_query(settings,False,True)
    with pytest.raises(RelayError):authorize_query(settings,True,False)
    with pytest.raises(RelayError):authorize_query({'mode':'illustrative'},True,True)
    authorize_query(settings,True,True)


def test_model_capacity_counts_each_call_and_honors_backoff(tmp_path,monkeypatch):
    from relay.model_usage import reserve_call,throttle
    monkeypatch.setenv('RELAY_MODEL_CALLS_PER_MINUTE','2')
    s=Store(tmp_path/'db')
    reserve_call(s,'judge','r',100,judge=True)
    reserve_call(s,'judge','r',100,judge=True)
    with pytest.raises(RelayError):reserve_call(s,'judge','r',100,judge=True)
    assert s.get('_server','rate_limits','model-day-'+str(int(time.time()//86400)))['count']==3
    throttle(s)
    with pytest.raises(RelayError):reserve_call(s,'new','r',100,judge=True)


def test_owner_signature_is_exact_idempotent_expiring_and_ai_only(tmp_path,monkeypatch):
    import base64
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from relay.ai_invitations import issue
    private=Ed25519PrivateKey.generate()
    monkeypatch.setenv('RELAY_AI_ADMIN_PUBLIC_KEY',base64.b64encode(private.public_key().public_bytes_raw()).decode())
    monkeypatch.setenv('RELAY_MCP_SERVICE_SECRET','m'*64)
    body=dict(count=2,hours=2,nonce='a'*32,timestamp=int(time.time()))
    signature=base64.b64encode(private.sign(digest(dict(method='POST',path='/internal/ai-invitations',body=body)).encode())).decode()
    s=Store(tmp_path/'db')
    first=issue(s,body,signature)
    assert first==issue(s,body,signature)
    assert len(first['invitations'])==2 and all(not v['calendar_authorized'] for v in first['invitations'])
    assert len(s.list('_server','judge_invites'))==2
    with pytest.raises(RelayError):issue(s,body|{'count':8},signature)
    with pytest.raises(RelayError):issue(s,body|{'timestamp':int(time.time())-70},signature)
    with pytest.raises(RelayError):issue(s,body,'m'*64)
    assert len(s.list('_server','judge_invites'))==2


def test_developer_context_needs_both_machine_and_workspace_credentials(monkeypatch,tmp_path):
    from fastapi.testclient import TestClient
    from relay.mcp_server import app
    from relay.auth import sign_context
    monkeypatch.setenv('RELAY_INFERENCE_PROVIDER','gemini_developer')
    monkeypatch.setenv('RELAY_MCP_URL','http://127.0.0.1:8016/_relay/mcp/')
    monkeypatch.setenv('RELAY_CONTEXT_SECRET','s'*64)
    monkeypatch.setenv('RELAY_MCP_SERVICE_SECRET','m'*64)
    context=sign_context('tenant','http://127.0.0.1:8016/_relay/mcp/','s'*64)
    with TestClient(app) as client:
        for headers in ({},{'Authorization':'Bearer '+'m'*64},{'X-Relay-Context':context}):
            assert client.post('/mcp/',headers=headers,json={}).status_code==403
