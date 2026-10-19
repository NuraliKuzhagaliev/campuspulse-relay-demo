"""Protocol simulations, not live Google consent or a deployed Firestore claim."""
import json,time
from types import SimpleNamespace
from cryptography.fernet import Fernet
from fastapi import FastAPI,Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
import pytest
from relay import oauth
from relay.domain import RelayError,digest
from relay.store import Store,FirestoreWorkspaceTransaction

def test_oauth_binds_same_anonymous_workspace_and_minimum_scopes(tmp_path,monkeypatch):
    store=Store(tmp_path/'oauth.sqlite3');tenant='demo-'+'a'*32
    store.put('_server','workspaces',tenant,{'id':tenant})
    from relay.service import RelayService
    RelayService(store,tenant).create_empty()
    for k,v in dict(RELAY_OAUTH_CLIENT_ID='test.apps.googleusercontent.com',RELAY_OAUTH_CLIENT_SECRET='TEST_ONLY_SECRET',RELAY_TOKEN_ENCRYPTION_KEY=Fernet.generate_key().decode(),RELAY_GATEWAY_URL='https://app.test').items():monkeypatch.setenv(k,v)
    seen={}
    class Flow:
        credentials=SimpleNamespace(id_token='SIMULATED_ID_TOKEN',to_json=lambda:json.dumps({'refresh_token':'SIMULATED_REFRESH','scopes':oauth.SCOPES}))
        @classmethod
        def from_client_config(cls,config,**kwargs):seen.update(kwargs);return cls()
        def authorization_url(self,**kwargs):return 'https://accounts.google.com/fake-test-only',None
        def fetch_token(self,**kwargs):pass
    monkeypatch.setattr('google_auth_oauthlib.flow.Flow',Flow)
    monkeypatch.setattr('google.oauth2.id_token.verify_oauth2_token',lambda *a,**kw:dict(sub='google-account-different-from-tenant',email_verified=True))
    monkeypatch.setattr(oauth,'router',__import__('fastapi').APIRouter())
    def identity(request):
        if request.cookies.get('test_capability')!='owned':raise RelayError('ACCESS_DENIED','invalid')
        return {'tenant':tenant}
    def session(scope):
        assert scope==tenant
        response=JSONResponse({'tenant':scope,'csrf':'SIMULATED_CSRF'});response.set_cookie('test_capability','owned');return response
    app=FastAPI();app.include_router(oauth.install(store,session,identity))
    @app.exception_handler(RelayError)
    async def reject(request,exc):return JSONResponse({'error':{'code':exc.code}},status_code=403)
    with TestClient(app,base_url='https://app.test',follow_redirects=False) as client:
        client.cookies.set('test_capability','owned')
        start=client.get('/api/auth/start');assert start.status_code==200
        connection=client.get('/connect');assert connection.status_code==307
        assert 'Max-Age=900' in connection.headers['set-cookie'] and 'HttpOnly' in connection.headers['set-cookie'] and 'Secure' in connection.headers['set-cookie'] and 'SameSite=lax' in connection.headers['set-cookie']
        assert oauth.SCOPES==seen['scopes'] and 'https://www.googleapis.com/auth/calendar.events' not in seen['scopes']
        state=client.cookies.get('relay_oauth_state');assert state
        callback=client.get('/auth/callback',params={'state':state,'code':'SIMULATED_CODE'})
        assert callback.status_code==303
        private=store.get(tenant,'private_connections','google');assert 'SIMULATED_REFRESH' not in private['ciphertext']
        assert not store.get(tenant,'meta','settings')['calendar_live']
        assert len(store.list('_server','workspaces'))==1
        assert client.get('/auth/callback',params={'state':state,'code':'SIMULATED_CODE'}).status_code==403
        client.cookies.delete('relay_oauth_state')
        browser_error=client.get('/auth/callback',params={'state':state,'code':'DO_NOT_ECHO_CALLBACK_CODE'},headers={'Accept':'text/html'})
        assert browser_error.status_code==403 and 'Начните подключение Calendar заново' in browser_error.text and 'Calendar қосылымын қайта бастаңыз' in browser_error.text
        assert 'DO_NOT_ECHO_CALLBACK_CODE' not in browser_error.text and state not in browser_error.text
        assert browser_error.headers['referrer-policy']=='no-referrer' and browser_error.headers['cache-control']=='no-store'
        assert '<script' not in browser_error.text and 'href="/"' in browser_error.text
        assert len(store.list(tenant,'private_connections'))==1 # no new connection or token exchange

class Ref:
    def __init__(self,data,tenant,kind,id=None):self.data,self.tenant,self.kind,self.id=data,tenant,kind,id
    def document(self,id):return Ref(self.data,self.tenant,self.kind,id)
    def get(self,transaction=None):
        key=(self.tenant,self.kind,self.id);exists=key in self.data
        return SimpleNamespace(exists=exists,to_dict=lambda:{'value':self.data[key]})
    def stream(self,transaction=None):
        return [SimpleNamespace(id=id,to_dict=lambda value=value:{'value':value}) for (tenant,kind,id),value in self.data.items() if tenant==self.tenant and kind==self.kind]
class FakeFirestore:
    def __init__(self):self.data={}
    def collection(self,tenant,kind):return Ref(self.data,tenant,kind)

def test_firestore_transaction_contract_buffers_cross_workspace_writes_and_revision():
    store=FakeFirestore();store.data[('a','progress','t')]={'id':'t','remaining_minutes':95}
    changes={};tx=FirestoreWorkspaceTransaction(store,object(),'a',changes)
    tx.put('progress','t',dict(id='t',remaining_minutes=75));assert tx.get('progress','t')['remaining_minutes']==75
    tx.workspace('copy').put('progress','t',dict(id='t',remaining_minutes=95))
    tx.workspace('_server').put('workspaces','copy',{'id':'copy'})
    assert tx.list('progress')[0]['remaining_minutes']==75 and tx.advance()==1
    assert store.data[('a','progress','t')]['remaining_minutes']==95 # no backend writes before commit
    assert ('copy','progress','t') in changes and ('_server','workspaces','copy') in changes
    tx.delete('progress','t');assert tx.get('progress','t') is None and tx.list('progress')==[]

def test_organizer_window_does_not_invent_hidden_billing():
    from datetime import datetime,timezone,timedelta
    from relay.funding import validate_funding
    now=datetime.now(timezone.utc)
    record=dict(source='organizer-lab',project_id='organizer-owned',organizer_project_ownership_verified=True,eligible_project_verified=True,service_coverage_verified=True,no_personal_spending=True,no_personal_billing_attached=True,activation_verified=True,organizer_terms_verified=True,
                activated_at_utc=now.isoformat(),expires_at_utc=(now+timedelta(hours=12)).isoformat(),checked_at_utc=now.isoformat(),instruction_reference='TEST simulated organizer instruction',billing_visibility='hidden_by_organizer_lab')
    actual=validate_funding(record,'organizer-owned',0,10,at=now)
    assert actual['credit_balance_usd'] is None and actual['personal_spending_authorized_usd']==0
    for change in [dict(project_id='personal-project'),dict(activation_verified=False),dict(no_personal_billing_attached=False),dict(expires_at_utc=(now+timedelta(hours=24)).isoformat()),dict(instruction_reference='')]:
        with pytest.raises(RelayError):validate_funding(record|change,'organizer-owned',0,10,at=now)

def test_revoked_calendar_does_not_lock_sources_progress_or_workspace(tmp_path,monkeypatch):
    from relay.service import RelayService
    svc=RelayService(Store(tmp_path/'revoked.sqlite3'),'demo-a');svc.create_empty()
    svc.import_source('brief.md',b'Assignment: Brief\nCourse: Optics\nTerm: Autumn 2026\nDue: 2026-10-23T18:00:00+05:00\nEffort: 45 minutes')
    s=svc.settings();s['windows']=[dict(start='2026-10-21T18:00:00+05:00',end='2026-10-21T20:00:00+05:00')];svc.store.put(svc.tenant,'meta','settings',s)
    original=svc.plan()
    def revoked():raise RelayError('AUTH_REQUIRED','Calendar consent was revoked; reconnect or disconnect explicitly.')
    monkeypatch.setattr(svc,'calendar',revoked)
    snapshot=svc.snapshot();assert len(snapshot['tasks'])==1 and snapshot['calendar_mode']=='unavailable' and snapshot['calendar_error']['code']=='AUTH_REQUIRED'
    assert snapshot['plan']['invalidated'] and not svc.latest_plan().get('invalidated')
    with pytest.raises(RelayError):svc.plan()
