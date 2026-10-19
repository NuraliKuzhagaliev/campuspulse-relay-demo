"""Simulated OAuth: consent must not transfer a token before desktop approval."""
import json,time
from types import SimpleNamespace
from fastapi import FastAPI,APIRouter,Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from cryptography.fernet import Fernet
from relay import oauth
from relay.store import Store
from relay.service import RelayService
from relay.domain import RelayError,digest

def test_consent_pending_browser_cannot_silently_grant_requesting_desktop(tmp_path,monkeypatch):
    store=Store(tmp_path/'pairing.sqlite3');desktop='local-desktop';store.put('_server','workspaces',desktop,{'id':desktop});RelayService(store,desktop).create_empty()
    for k,v in dict(RELAY_MODE='local',RELAY_OAUTH_CLIENT_ID='test.apps.googleusercontent.com',RELAY_OAUTH_CLIENT_SECRET='SIMULATED_SECRET',RELAY_TOKEN_ENCRYPTION_KEY=Fernet.generate_key().decode(),RELAY_GATEWAY_URL='https://pair.test').items():monkeypatch.setenv(k,v)
    class Flow:
        credentials=SimpleNamespace(id_token='SIMULATED_TOKEN',to_json=lambda:json.dumps({'refresh_token':'SIMULATED_REFRESH'}))
        @classmethod
        def from_client_config(cls,*args,**kwargs):return cls()
        def authorization_url(self,**kwargs):return 'https://accounts.google.com/simulated',None
        def fetch_token(self,**kwargs):pass
    monkeypatch.setattr('google_auth_oauthlib.flow.Flow',Flow);monkeypatch.setattr('google.oauth2.id_token.verify_oauth2_token',lambda *a,**k:dict(sub='consenting-browser',email_verified=True));monkeypatch.setattr(oauth,'router',APIRouter())
    def identity(request):return {'tenant':request.cookies.get('scope',desktop)}
    def new_session(tenant,expires=None):
        store.put('_server','workspaces',tenant,{'id':tenant},create=True)
        response=JSONResponse({'tenant':tenant,'csrf':'SIMULATED_CSRF'});response.set_cookie('scope',tenant);return response
    app=FastAPI();app.include_router(oauth.install(store,new_session,identity))
    @app.exception_handler(RelayError)
    async def reject(request,exc):return JSONResponse({'error':exc.code},status_code=403)
    with TestClient(app,base_url='https://pair.test',follow_redirects=False) as browser:
        start=browser.get('/api/auth/start?desktop=true').json();pair=start['pairing_id']
        browser.get('/connect',params={'pair':pair});state=browser.cookies.get('relay_oauth_state')
        callback=browser.get('/auth/callback',params={'code':'SIMULATED_CODE','state':state});assert callback.status_code==200
        assert '/assets/relay-pair.js' in callback.text and '<script>' not in callback.text
        assert store.list(desktop,'private_connections')==[]
        assert browser.post('/api/auth/poll',json={'pairing_id':pair,'secret':start['secret']}).json()['pending']
        pending=store.get('_server','pairings',pair)['pending_tenant'];assert pending!=desktop and store.get(pending,'private_connections','google')
        # The requesting desktop, by itself, cannot approve on behalf of Google user.
        with TestClient(app,base_url='https://pair.test') as attacker:
            assert attacker.post('/api/auth/pair/approve',json={'pairing_id':pair}).status_code==403
        approved=browser.post('/api/auth/pair/approve',json={'pairing_id':pair});assert approved.status_code==200
        assert approved.json()['tenant']==desktop and store.get(desktop,'private_connections','google')
        assert store.list(pending,'private_connections')==[]
        assert browser.post('/api/auth/poll',json={'pairing_id':pair,'secret':start['secret']}).json()['tenant']==desktop
        assert browser.post('/api/auth/poll',json={'pairing_id':pair,'secret':start['secret']}).status_code==403
