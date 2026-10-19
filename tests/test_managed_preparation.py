"""Organizer routing/identity/state simulations only: zero real cloud calls."""
import time,json
from datetime import datetime,timezone,timedelta
import pytest
from relay.domain import RelayError
from relay.auth import sign_context
from relay.store import Store
from relay.public_ai import PublicQueue
from relay.managed_state import dispatch,authenticate
from relay.managed_bridge import configuration,signature

def test_off_expired_and_retirement_routes_never_enable_personal_calls(monkeypatch):
    now=datetime.now(timezone.utc)
    for k,v in dict(RELAY_MANAGED_ROUTE_ENABLED='true',RELAY_MANAGED_EXPIRES_AT=(now+timedelta(hours=12)).isoformat(),RELAY_MANAGED_ACTIVATED_AT=now.isoformat(),RELAY_MANAGED_BRIDGE_URL='https://bridge.test',RELAY_MANAGED_RESOURCE='projects/organizer/locations/us-central1/reasoningEngines/one',RELAY_MANAGED_BRIDGE_SECRET='x'*64,RELAY_MANAGED_MODEL='selected-vertex-model',RELAY_MANAGED_REVISION='actual-build').items():monkeypatch.setenv(k,v)
    assert configuration()['resource'].endswith('/one')
    monkeypatch.setenv('RELAY_MANAGED_EXPIRES_AT',(now+timedelta(minutes=30)).isoformat());assert configuration() is None
    monkeypatch.setenv('RELAY_MANAGED_ROUTE_ENABLED','false');assert configuration() is None

def test_managed_checkpoint_and_quota_are_bound_to_existing_public_run(tmp_path):
    from relay.conversations import conversation
    from google.adk.sessions import Session
    store=Store(tmp_path/'shared.sqlite3');tenant='demo-a';store.put('_server','workspaces',tenant,{'id':tenant})
    store.put(tenant,'meta','settings',{'mode':'own_documents','timezone':'Asia/Almaty','anchor':'2026-10-19','calendar_id':'PRIVATE_NOT_EXPORTED'})
    c=conversation(store,tenant)
    queued=PublicQueue(store).submit(tenant,dict(conversation_id=c['id'],request_id='a'*32,message='synthetic check',language='en'),time.time()+3600)
    job=PublicQueue(store).claim_next();assert job and job['run_id']==queued['run_id'];run=job['run_id']
    assert dispatch(store,tenant,dict(op='begin',run_id=run))
    with pytest.raises(RelayError):dispatch(store,tenant,dict(op='begin',run_id=run))
    settings=dispatch(store,tenant,dict(op='get',run_id=run,kind='meta',id='settings'));assert 'calendar_id' not in settings
    session=Session(id=c['id'],app_name='campuspulse_relay',user_id=tenant,state={},last_update_time=time.time()).model_dump(mode='json')
    assert dispatch(store,tenant,dict(op='put',run_id=run,kind='adk_sessions',id=c['id'],value=dict(session=session,revision=0)))
    assert dispatch(store,tenant,dict(op='claim',run_id=run,kind='adk_sessions',id=c['id'],expected={'revision':0},changes=dict(session=session,revision=1)))
    for body in [dict(op='get',run_id=run,kind='private_connections',id='google'),dict(op='get',run_id=run,kind='conversations',id='foreign'),dict(op='get',run_id=run,kind='meta',id='settings',tenant='other'),dict(op='put',run_id=run,kind='adk_sessions',id=c['id'],value=dict(session=session|{'user_id':'foreign'},revision=0))]:
        with pytest.raises(RelayError):dispatch(store,tenant,body)
    with pytest.raises(RelayError):dispatch(store,'foreign',dict(op='get',run_id=run,kind='conversations',id=c['id']))
    info=dispatch(store,tenant,dict(op='reserve',run_id=run,request_bytes=1000));assert info['reserved']
    PublicQueue(store).cancel(tenant,run)
    with pytest.raises(RelayError):dispatch(store,tenant,dict(op='reserve',run_id=run,request_bytes=1000))

def test_managed_machine_identity_context_audience_and_window_are_separate(monkeypatch):
    now=datetime.now(timezone.utc);secret='s'*64
    for k,v in dict(RELAY_MANAGED_PRINCIPALS='runtime@organizer.iam.gserviceaccount.com',RELAY_MANAGED_AUDIENCE='https://public.test',RELAY_MANAGED_MCP_URL='https://public.test/managed/mcp/',RELAY_MANAGED_ACTIVATED_AT=now.isoformat(),RELAY_MANAGED_EXPIRES_AT=(now+timedelta(hours=12)).isoformat(),RELAY_CONTEXT_SECRET=secret).items():monkeypatch.setenv(k,v)
    monkeypatch.setattr('google.oauth2.id_token.verify_oauth2_token',lambda token,request,audience:dict(email='runtime@organizer.iam.gserviceaccount.com',email_verified=True))
    headers={'authorization':'Bearer '+'SIMULATED_TOKEN_'*10,'x-relay-context':sign_context('demo-a','https://public.test/managed/mcp/',secret)}
    assert authenticate(headers)=='demo-a'
    with pytest.raises(RelayError):authenticate(headers|{'x-relay-context':sign_context('demo-a','https://wrong.test',secret)})
    monkeypatch.setenv('RELAY_MANAGED_PRINCIPALS','another@organizer.iam.gserviceaccount.com')
    with pytest.raises(RelayError):authenticate(headers)

def test_bridge_accepts_only_fixed_resource_fresh_owner_signature(monkeypatch):
    from relay.bridge_server import validate,_nonces
    now=datetime.now(timezone.utc);secret='b'*64;context='c'*64;resource='projects/organizer/locations/us-central1/reasoningEngines/one'
    for k,v in dict(RELAY_MANAGED_BRIDGE_SECRET=secret,RELAY_AGENT_RESOURCE=resource,RELAY_MANAGED_ACTIVATED_AT=now.isoformat(),RELAY_MANAGED_EXPIRES_AT=(now+timedelta(hours=12)).isoformat(),RELAY_MCP_URL='https://public.test/managed/mcp/',RELAY_CONTEXT_SECRET=context).items():monkeypatch.setenv(k,v)
    body=dict(resource=resource,arguments=dict(user_id='demo-a',message='synthetic check',context_token=sign_context('demo-a','https://public.test/managed/mcp/',context),run_id='a'*32,conversation_id='b'*32,language='en',history=[]))
    stamp=int(time.time());nonce='d'*32;headers={'x-relay-time':str(stamp),'x-relay-nonce':nonce,'x-relay-signature':signature(body,stamp,nonce,secret)};_nonces.clear()
    assert validate(body,headers)['user_id']=='demo-a'
    with pytest.raises(RelayError):validate(body,headers)
    with pytest.raises(RelayError):validate(body|{'resource':resource+'other'},headers|{'x-relay-nonce':'e'*32})

@pytest.mark.parametrize('change',[{}, {'managed_resource':'projects/foreign/locations/us-central1/reasoningEngines/other'}, {'runtime_revision':'different-build'}])
def test_gateway_verifies_exact_managed_response_resource_revision(monkeypatch,change):
    from relay import managed_bridge
    secret='c'*64;url='https://public.test/_relay/mcp/'
    config=dict(mcp_url='https://public.test/managed/mcp/',url='https://bridge.test',resource='projects/123/locations/us-central1/reasoningEngines/456',revision='actual-build',secret='b'*64)
    monkeypatch.setenv('RELAY_MCP_URL',url);monkeypatch.setenv('RELAY_CONTEXT_SECRET',secret)
    monkeypatch.setattr(managed_bridge,'configuration',lambda:config)
    payload=dict(provider='vertex',deployment_mode='managed_gcp',managed_resource=config['resource'],runtime_revision=config['revision'])|change
    calls=[]
    class Response:
        status_code=200
        def json(self):return payload
    def post(*args,**kw):calls.append(args[0]);return Response()
    monkeypatch.setattr('httpx.post',post)
    args=dict(user_id='demo-a',context_token=sign_context('demo-a',url,secret),message='Synthetic query',run_id='a'*32,conversation_id='b'*32)
    if change:
        with pytest.raises(RelayError) as error:managed_bridge.invoke(**args)
        assert error.value.code=='UPSTREAM_UNAVAILABLE'
    else:assert managed_bridge.invoke(**args)==payload
    assert calls==['https://bridge.test/query']
