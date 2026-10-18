"""External-browser Google OAuth + explicit one-use desktop pairing.

OAuth credentials are encrypted at rest. This module cannot authorize study writes.
Actual consent/revocation and hosted identity behavior require live account testing.
"""
import hashlib
import json
import os
import secrets
import time
from datetime import datetime,timedelta,time as day_time
from zoneinfo import ZoneInfo
from fastapi import APIRouter,Request
from fastapi.responses import RedirectResponse,HTMLResponse
from pydantic import BaseModel
from cryptography.fernet import Fernet
from .domain import RelayError,digest

router=APIRouter()
SCOPES=['openid','https://www.googleapis.com/auth/userinfo.email','https://www.googleapis.com/auth/userinfo.profile','https://www.googleapis.com/auth/calendar.events','https://www.googleapis.com/auth/calendar.calendarlist.readonly']


def configuration():
    for key in ('RELAY_OAUTH_CLIENT_ID','RELAY_OAUTH_CLIENT_SECRET','RELAY_TOKEN_ENCRYPTION_KEY','RELAY_GATEWAY_URL'):
        if not os.getenv(key):
            raise RelayError('AUTH_REQUIRED',f'Configure {key} on the gateway. Authentication opens in the system browser; never paste tokens in chat.')
    return {'web':{'client_id':os.environ['RELAY_OAUTH_CLIENT_ID'],'client_secret':os.environ['RELAY_OAUTH_CLIENT_SECRET'],'auth_uri':'https://accounts.google.com/o/oauth2/auth','token_uri':'https://oauth2.googleapis.com/token','redirect_uris':[os.environ['RELAY_GATEWAY_URL']+'/auth/callback']}}


def credentials(store,tenant):
    from google.oauth2.credentials import Credentials
    try:
        value=store.get(tenant,'private_connections','google')['ciphertext']
        plaintext=Fernet(os.environ['RELAY_TOKEN_ENCRYPTION_KEY'].encode()).decrypt(value.encode())
        return Credentials.from_authorized_user_info(json.loads(plaintext))
    except Exception as exc:
        raise RelayError('AUTH_REQUIRED','Connect Google in your browser to authorize this workspace Calendar.') from exc


def calendar_list(store,tenant):
    from google.auth.transport.requests import AuthorizedSession
    from .connectors import upstream_error
    session=AuthorizedSession(credentials(store,tenant))
    response=session.get('https://www.googleapis.com/calendar/v3/users/me/calendarList',params={'maxResults':250},timeout=20)
    if response.status_code!=200:
        raise upstream_error(response.status_code)
    return [{'id':c['id'],'name':c.get('summary','Calendar'),'role':c.get('accessRole'),'primary':c.get('primary',False)} for c in response.json().get('items',[]) if c.get('accessRole') in ('owner','writer')]


def install(store,new_session,identity):
    @router.get('/api/auth/start')
    def start(desktop:bool=False):
        configuration()
        gateway=os.environ['RELAY_GATEWAY_URL']
        if not gateway.startswith('https://'):
            raise RelayError('AUTH_REQUIRED','Hosted OAuth requires the configured HTTPS gateway.')
        if not desktop:
            return {'url':gateway+'/connect'}
        pairing_id,secret=secrets.token_urlsafe(24),secrets.token_urlsafe(32)
        store.put('_server','pairings',pairing_id,{'id':pairing_id,'secret_hash':digest(secret),'expires':time.time()+300,'status':'pending'})
        return {'url':gateway+'/connect?pair='+pairing_id,'pairing_id':pairing_id,'secret':secret}

    @router.get('/connect')
    def connect(pair:str|None=None):
        from google_auth_oauthlib.flow import Flow
        config=configuration()
        state=secrets.token_urlsafe(32)
        verifier=secrets.token_urlsafe(64)
        if pair:
            pairing=store.get('_server','pairings',pair)
            if pairing['expires']<time.time() or pairing['status']!='pending':
                raise RelayError('AUTH_REQUIRED','Desktop pairing expired. Start again in the app.')
        store.put('_server','oauth_states',digest(state),{'expires':time.time()+300,'verifier':verifier,'pair':pair,'status':'pending'})
        flow=Flow.from_client_config(config,scopes=SCOPES,state=state,code_verifier=verifier)
        flow.redirect_uri=os.environ['RELAY_GATEWAY_URL']+'/auth/callback'
        url,_=flow.authorization_url(access_type='offline',include_granted_scopes='true',prompt='consent')
        return RedirectResponse(url)

    @router.get('/auth/callback')
    def callback(request:Request,code:str|None=None,state:str|None=None,error:str|None=None):
        if error or not code or not state:
            raise RelayError('AUTH_REQUIRED','Google consent was cancelled or did not return a valid authorization code.')
        record=store.get('_server','oauth_states',digest(state))
        if record['expires']<time.time() or not store.claim('_server','oauth_states',digest(state),{'status':'pending'},{'status':'consumed'}):
            raise RelayError('AUTH_REQUIRED','OAuth state expired or was already used.')
        from google_auth_oauthlib.flow import Flow
        from google.oauth2 import id_token
        from google.auth.transport.requests import Request as GoogleRequest
        flow=Flow.from_client_config(configuration(),scopes=SCOPES,state=state,code_verifier=record['verifier'])
        flow.redirect_uri=os.environ['RELAY_GATEWAY_URL']+'/auth/callback'
        try:
            flow.fetch_token(code=code)
            info=id_token.verify_oauth2_token(flow.credentials.id_token,GoogleRequest(),os.environ['RELAY_OAUTH_CLIENT_ID'])
            if not info.get('email_verified'):
                raise ValueError()
        except Exception as exc:
            raise RelayError('AUTH_REQUIRED','Google authorization could not be verified. Review consent settings.') from exc
        tenant=hashlib.sha256(info['sub'].encode()).hexdigest()
        cipher=Fernet(os.environ['RELAY_TOKEN_ENCRYPTION_KEY'].encode()).encrypt(flow.credentials.to_json().encode()).decode()
        store.put(tenant,'private_connections','google',{'ciphertext':cipher,'type':'google_oauth'})
        try:
            store.get(tenant,'meta','settings')
        except RelayError:
            zone=ZoneInfo('Asia/Almaty');today=datetime.now(zone).date();monday=today+timedelta(days=(7-today.weekday())%7)
            windows=[{'start':datetime.combine(monday+timedelta(days=i),day_time(18),zone).isoformat(),'end':datetime.combine(monday+timedelta(days=i),day_time(20),zone).isoformat()} for i in range(5)]
            store.put(tenant,'meta','settings',dict(mode='personal',timezone='Asia/Almaty',anchor=monday.isoformat(),windows=windows,daily_cap_minutes=240,calendar_id=None,calendar_live=False,github_repo=os.getenv('RELAY_GITHUB_REPO','NuraliKuzhagaliev/campuspulse-relay-demo'),github_ref='main',github_path='coursework.md',watch_enabled=False,availability_assumption='Default draft windows: weekdays 18:00-20:00. Confirm before planning.'))
        response=new_session(tenant)
        if record.get('pair'):
            csrf=json.loads(response.body)['csrf'];pair=record['pair']
            # A deliberate second click binds this browser identity to the requesting desktop.
            html='<!doctype html><html lang="en"><meta name="viewport" content="width=device-width"><title>Connect CampusPulse RELAY desktop</title><body style="font:18px Arial;padding:64px;background:#f5f4ef;color:#14243a"><h1>Connect this Windows desktop?</h1><p>You signed in with Google. Only approve if you just requested this connection in CampusPulse RELAY.</p><button id="approve" style="padding:16px;background:#2b59f0;color:white;border:0;border-radius:8px">Connect this desktop</button><p id="result"></p><script>document.getElementById("approve").onclick=async()=>{const r=await fetch("/api/auth/pair/approve",{method:"POST",headers:{"Content-Type":"application/json","X-Relay-CSRF":'+json.dumps(csrf)+'},body:JSON.stringify({pairing_id:'+json.dumps(pair)+'})});document.getElementById("result").textContent=r.ok?"Connected. Return to CampusPulse RELAY.":"Could not connect. Restart pairing in the app.";};</script></body></html>'
            result=HTMLResponse(html)
        else:
            result=RedirectResponse('/',status_code=303)
        result.raw_headers.extend(h for h in response.raw_headers if h[0].lower()==b'set-cookie')
        result.headers['Referrer-Policy']='no-referrer';result.headers['Cache-Control']='no-store'
        return result

    class PairApproval(BaseModel):
        pairing_id:str

    @router.post('/api/auth/pair/approve')
    def approve_pair(body:PairApproval,request:Request):
        user=identity(request)
        pairing=store.get('_server','pairings',body.pairing_id)
        if pairing['expires']<time.time() or not store.claim('_server','pairings',body.pairing_id,{'status':'pending'},{'status':'approved','tenant':user['tenant']}):
            raise RelayError('AUTH_REQUIRED','Pairing expired or already consumed.')
        return {'approved':True}

    class PairPoll(BaseModel):
        pairing_id:str
        secret:str

    @router.post('/api/auth/poll')
    def poll_pair(body:PairPoll):
        pairing=store.get('_server','pairings',body.pairing_id)
        if not secrets.compare_digest(digest(body.secret),pairing['secret_hash']) or pairing['expires']<time.time():
            raise RelayError('ACCESS_DENIED','Invalid or expired desktop pairing.')
        if pairing['status']=='pending':
            return {'pending':True}
        if not store.claim('_server','pairings',body.pairing_id,{'status':'approved'},{'status':'consumed'}):
            raise RelayError('ACCESS_DENIED','Pairing was already consumed.')
        return new_session(pairing['tenant'])

    return router
