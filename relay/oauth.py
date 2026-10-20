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
SCOPES=['openid','https://www.googleapis.com/auth/userinfo.email','https://www.googleapis.com/auth/calendar.app.created']
EXISTING_SCOPES=['openid','https://www.googleapis.com/auth/userinfo.email','https://www.googleapis.com/auth/calendar.events','https://www.googleapis.com/auth/calendar.calendarlist.readonly']

def consent_failure(request,code,message):
    """A safe browser recovery page; API clients retain typed errors.

    Never echo OAuth query parameters or weaken cookie/state/PKCE validation.
    """
    if 'text/html' not in request.headers.get('accept',''):raise RelayError(code,message)
    html='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Calendar connection needs a new request</title><link rel="stylesheet" href="/assets/relay-oauth.css"><main><h1>Start Calendar connection again</h1><p>This request expired, was cancelled, or did not match this browser. This attempt did not complete a new RELAY connection or write Calendar events.</p><p>Return to RELAY → Connections → Connect Google. Complete the fresh flow in the same browser. Web requests expire after 15 minutes, desktop pairing after 5 minutes. Do not reuse or share a callback address.</p><h2 lang="ru">Начните подключение Calendar заново</h2><p lang="ru">Запрос истёк, отменён или не совпал с этим браузером. Новое подключение RELAY не завершено; эта попытка не записывала события.</p><p lang="ru">Вернитесь в RELAY → Подключения → Подключить Google. Завершите новый поток в том же браузере. Веб-запрос действует 15 минут, сопряжение Windows — 5 минут. Не открывайте повторно и не передавайте адрес callback.</p><h2 lang="kk">Calendar қосылымын қайта бастаңыз</h2><p lang="kk">Сұраудың мерзімі аяқталған, ол тоқтатылған немесе осы браузерге сәйкес келмейді. Бұл әрекет жаңа RELAY қосылымын аяқтамады және күнтізбеге оқиға жазбады.</p><p lang="kk">RELAY → Қосылымдар → Google қосу жолына оралып, жаңа сұрауды сол браузерде аяқтаңыз. Веб-сұрау 15 минут, Windows жұптастыруы 5 минут жарамды. Callback мекенжайын қайта ашпаңыз және бөліспеңіз.</p><a href="/">Return to RELAY / Вернуться в RELAY / RELAY-ге оралу</a></main></html>'''
    return HTMLResponse(html,status_code=403,headers={'Cache-Control':'no-store','Referrer-Policy':'no-referrer'})


def configuration():
    for key in ('RELAY_OAUTH_CLIENT_ID','RELAY_OAUTH_CLIENT_SECRET','RELAY_TOKEN_ENCRYPTION_KEY','RELAY_GATEWAY_URL'):
        if not os.getenv(key):
            raise RelayError('AUTH_REQUIRED',f'Configure {key} on the gateway. Authentication opens in the system browser; never paste tokens in chat.')
    try:Fernet(os.environ['RELAY_TOKEN_ENCRYPTION_KEY'].encode())
    except (ValueError,TypeError) as exc:
        raise RelayError('AUTH_REQUIRED','The gateway Calendar encryption key is invalid. The owner must restore RELAY_TOKEN_ENCRYPTION_KEY; no Google request was started.') from exc
    return {'web':{'client_id':os.environ['RELAY_OAUTH_CLIENT_ID'],'client_secret':os.environ['RELAY_OAUTH_CLIENT_SECRET'],'auth_uri':'https://accounts.google.com/o/oauth2/auth','token_uri':'https://oauth2.googleapis.com/token','redirect_uris':[os.environ['RELAY_GATEWAY_URL']+'/auth/callback']}}


def credentials(store,tenant):
    from google.oauth2.credentials import Credentials
    try:
        record=store.get(tenant,'private_connections','google')
        value=record['ciphertext']
        plaintext=Fernet(os.environ['RELAY_TOKEN_ENCRYPTION_KEY'].encode()).decrypt(value.encode())
        value=Credentials.from_authorized_user_info(json.loads(plaintext))
        if value.expired and value.refresh_token:
            from google.auth.transport.requests import Request
            value.refresh(Request())
            ciphertext=Fernet(os.environ['RELAY_TOKEN_ENCRYPTION_KEY'].encode()).encrypt(value.to_json().encode()).decode()
            store.put(tenant,'private_connections','google',dict(record,ciphertext=ciphertext,type='google_oauth'))
        return value
    except Exception as exc:
        raise RelayError('AUTH_REQUIRED','Connect Google in your browser to authorize this workspace Calendar.') from exc


def calendar_list(store,tenant):
    from google.auth.transport.requests import AuthorizedSession
    from .connectors import upstream_error
    creds=credentials(store,tenant)
    session=AuthorizedSession(creds)
    if 'https://www.googleapis.com/auth/calendar.events' not in (creds.scopes or []):
        connection=store.get(tenant,'private_connections','google')
        target=connection.get('app_calendar')
        if not target:return []
        response=session.get('https://www.googleapis.com/calendar/v3/calendars/'+__import__('urllib.parse',fromlist=['quote']).quote(target['id'],safe=''),timeout=20)
        if response.status_code!=200:raise upstream_error(response.status_code)
        actual=response.json()
        return [dict(id=actual['id'],name=actual.get('summary','CampusPulse RELAY'),role='owner',primary=False,timezone=actual.get('timeZone'))]
    response=session.get('https://www.googleapis.com/calendar/v3/users/me/calendarList',params={'maxResults':250},timeout=20)
    if response.status_code!=200:
        raise upstream_error(response.status_code)
    return [{'id':c['id'],'name':c.get('summary','Calendar'),'role':c.get('accessRole'),'primary':c.get('primary',False)} for c in response.json().get('items',[]) if c.get('accessRole') in ('owner','writer')]


def recover_app_calendar(store,tenant,calendar_id):
    """An ID is a hint, never authority. Google verifies the current owner/scope.

    This reads metadata only. Selection and every external write remain separate.
    No identity-to-calendar map survives the temporary workspace's expiry.
    """
    import re
    from urllib.parse import quote
    from google.auth.transport.requests import AuthorizedSession
    from .connectors import upstream_error
    if not isinstance(calendar_id,str) or not re.fullmatch(r'[a-zA-Z0-9_.-]{1,200}@group\.calendar\.google\.com',calendar_id):
        raise RelayError('UNSUPPORTED_INPUT','Enter the ID of a separate calendar previously created by this application, not a URL or a primary calendar.')
    creds=credentials(store,tenant)
    scopes=creds.scopes or []
    if 'https://www.googleapis.com/auth/calendar.app.created' not in scopes or any(scope.startswith('https://www.googleapis.com/auth/calendar') and scope!='https://www.googleapis.com/auth/calendar.app.created' for scope in scopes):
        raise RelayError('ACCESS_DENIED','Reconnect Google using the app-created calendars permission before recovering this calendar.')
    try:
        response=AuthorizedSession(creds).get('https://www.googleapis.com/calendar/v3/calendars/'+quote(calendar_id,safe=''),timeout=20)
    except Exception as exc:
        raise RelayError('UPSTREAM_UNAVAILABLE','Google Calendar metadata is unavailable. No calendar was created or selected; retry the read later.') from exc
    if response.status_code!=200:raise upstream_error(response.status_code)
    actual=response.json()
    if actual.get('id')!=calendar_id:raise RelayError('ACCESS_DENIED','Google did not verify this exact calendar for the current connection.')
    try:ZoneInfo(actual['timeZone'])
    except (KeyError,ValueError):raise RelayError('UNSUPPORTED_INPUT','Google returned a calendar without a supported timezone.')
    calendar=dict(id=calendar_id,name=str(actual.get('summary','CampusPulse RELAY'))[:250],timezone=actual['timeZone'],primary=False,role='owner')
    # Re-read after a possible credential refresh. Never overwrite its new cipher.
    connection=store.get(tenant,'private_connections','google')
    connection.update(app_calendar=calendar,create_status='complete')
    store.put(tenant,'private_connections','google',connection)
    return dict(calendar=calendar,selected=False,events_written=False)


def install(store,new_session,identity):
    @router.get('/api/auth/start')
    def start(request:Request,desktop:bool=False,existing:bool=False):
        owner=identity(request)
        configuration()
        gateway=os.environ['RELAY_GATEWAY_URL']
        if not gateway.startswith('https://'):
            raise RelayError('AUTH_REQUIRED','Hosted OAuth requires the configured HTTPS gateway.')
        if not desktop:
            return {'url':gateway+('/connect?existing=true' if existing else '/connect')}
        pairing_id,secret=secrets.token_urlsafe(24),secrets.token_urlsafe(32)
        store.put('_server','pairings',pairing_id,{'id':pairing_id,'secret_hash':digest(secret),'expires':time.time()+300,'status':'pending','workspace':owner['tenant']})
        return {'url':gateway+'/connect?pair='+pairing_id+('&existing=true' if existing else ''),'pairing_id':pairing_id,'secret':secret}

    @router.get('/connect')
    def connect(request:Request,pair:str|None=None,existing:bool=False):
        from google_auth_oauthlib.flow import Flow
        config=configuration()
        state=secrets.token_urlsafe(32)
        browser_binding=secrets.token_urlsafe(32)
        verifier=secrets.token_urlsafe(64)
        if pair:
            pairing=store.get('_server','pairings',pair)
            if pairing['expires']<time.time() or pairing['status']!='pending':
                raise RelayError('AUTH_REQUIRED','Desktop pairing expired. Start again in the app.')
            tenant=pairing['workspace']
        else:tenant=identity(request)['tenant']
        scopes=EXISTING_SCOPES if existing else SCOPES
        ttl=300 if pair else 900
        store.put('_server','oauth_states',digest(state),{'expires':time.time()+ttl,'verifier':verifier,'pair':pair,'status':'pending','workspace':tenant,'scopes':scopes,'browser_binding_hash':digest(browser_binding)})
        flow=Flow.from_client_config(config,scopes=scopes,state=state,code_verifier=verifier)
        flow.redirect_uri=os.environ['RELAY_GATEWAY_URL']+'/auth/callback'
        url,_=flow.authorization_url(access_type='offline',include_granted_scopes='true',prompt='consent')
        response=RedirectResponse(url)
        # The private browser cookie is independent of state in the URL. Knowing
        # a callback URL must not let another browser reconstruct this binding.
        response.set_cookie('relay_oauth_state',browser_binding,httponly=True,secure=True,samesite='lax',max_age=ttl)
        return response

    @router.get('/auth/callback')
    def callback(request:Request,code:str|None=None,state:str|None=None,error:str|None=None):
        if error or not code or not state:
            return consent_failure(request,'AUTH_REQUIRED','Google consent was cancelled or did not return a valid authorization code.')
        try:record=store.get('_server','oauth_states',digest(state))
        except RelayError:return consent_failure(request,'ACCESS_DENIED','OAuth callback is not bound to an available request in this browser. Start a new connection.')
        if not secrets.compare_digest(digest(request.cookies.get('relay_oauth_state','')),record.get('browser_binding_hash','')):
            return consent_failure(request,'ACCESS_DENIED','OAuth callback is not bound to the browser that initiated it.')
        if record['expires']<time.time() or not store.claim('_server','oauth_states',digest(state),{'status':'pending'},{'status':'consumed'}):
            return consent_failure(request,'AUTH_REQUIRED','OAuth state expired or was already used.')
        from google_auth_oauthlib.flow import Flow
        from google.oauth2 import id_token
        from google.auth.transport.requests import Request as GoogleRequest
        flow=Flow.from_client_config(configuration(),scopes=record['scopes'],state=state,code_verifier=record['verifier'])
        flow.redirect_uri=os.environ['RELAY_GATEWAY_URL']+'/auth/callback'
        try:
            flow.fetch_token(code=code)
            info=id_token.verify_oauth2_token(flow.credentials.id_token,GoogleRequest(),os.environ['RELAY_OAUTH_CLIENT_ID'])
            if not info.get('email_verified'):
                raise ValueError()
        except Exception as exc:
            raise RelayError('AUTH_REQUIRED','Google authorization could not be verified. Review consent settings.') from exc
        tenant=record['workspace']
        store.get('_server','workspaces',tenant)
        cipher=Fernet(os.environ['RELAY_TOKEN_ENCRYPTION_KEY'].encode()).encrypt(flow.credentials.to_json().encode()).decode()
        try:old=store.get(tenant,'private_connections','google')
        except RelayError:old={}
        same=old.get('identity_hash')==digest(info['sub'])
        connection={'ciphertext':cipher,'type':'google_oauth','identity_hash':digest(info['sub']),**({'app_calendar':old['app_calendar']} if same and old.get('app_calendar') else {})}
        if same and old.get('create_status')=='pending':connection['create_status']='pending'
        if record.get('pair'):
            # Do not grant credentials to the requesting desktop before the
            # consenting browser explicitly approves that pairing.
            from . import public_demo
            tenant=('demo-' if public_demo.temporary_enabled() else 'local-')+secrets.token_hex(16)
            from .service import RelayService
            RelayService(store,tenant).create_empty()
            store.claim('_server','pairings',record['pair'],{'status':'pending'},{'pending_tenant':tenant})
        store.put(tenant,'private_connections','google',connection)
        try:
            store.get(tenant,'meta','settings')
        except RelayError:
            zone=ZoneInfo('Asia/Almaty');today=datetime.now(zone).date();monday=today+timedelta(days=(7-today.weekday())%7)
            windows=[{'start':datetime.combine(monday+timedelta(days=i),day_time(18),zone).isoformat(),'end':datetime.combine(monday+timedelta(days=i),day_time(20),zone).isoformat()} for i in range(5)]
            store.put(tenant,'meta','settings',dict(mode='personal',timezone='Asia/Almaty',anchor=monday.isoformat(),windows=windows,daily_cap_minutes=240,calendar_id=None,calendar_live=False,github_repo=os.getenv('RELAY_GITHUB_REPO','NuraliKuzhagaliev/campuspulse-relay-demo'),github_ref='main',github_path='coursework.md',watch_enabled=False,availability_assumption='Default draft windows: weekdays 18:00-20:00. Confirm before planning.'))
        response=new_session(tenant,expires=time.time()+300) if record.get('pair') else new_session(tenant)
        # Consent never silently selects a target or preserves an old write
        # authorization across scope/account changes.
        settings=store.get(tenant,'meta','settings');settings.update(calendar_live=False,calendar_connection=None,calendar_id='local-illustrative-calendar')
        store.put(tenant,'meta','settings',settings)
        from .service import RelayService
        RelayService(store,tenant).invalidate_plans()
        if record.get('pair'):
            csrf=json.loads(response.body)['csrf'];pair=record['pair']
            # A deliberate second click binds this browser identity to the requesting desktop.
            from html import escape
            html='<!doctype html><html lang="en"><meta name="viewport" content="width=device-width"><title>Connect CampusPulse RELAY desktop</title><body style="font:18px Arial;padding:40px;max-width:800px;background:#f5f4ef;color:#14243a"><h1>Connect this Windows desktop?<br>Подключить это приложение?<br>Осы қолданбаны қосу керек пе?</h1><p>Approve only if you just requested this connection in RELAY. Consent alone has not connected the desktop.</p><p>Подтвердите, только если вы только что запросили подключение в RELAY. Само согласие Google ещё не подключает приложение.</p><p>RELAY ішінде осы қосылымды жаңа ғана сұраған болсаңыз ғана растаңыз. Google келісімі қолданбаны әлі қоспайды.</p><button id="approve" data-pair="'+escape(pair,quote=True)+'" data-csrf="'+escape(csrf,quote=True)+'" style="padding:16px;background:#2b59f0;color:white;border:0;border-radius:8px">Connect / Подключить / Қосу</button><p id="result" role="status"></p><script src="/assets/relay-pair.js" defer></script></body></html>'
            result=HTMLResponse(html)
        else:
            result=RedirectResponse('/',status_code=303)
        result.raw_headers.extend(h for h in response.raw_headers if h[0].lower()==b'set-cookie')
        result.delete_cookie('relay_oauth_state',secure=True,samesite='lax')
        result.headers['Referrer-Policy']='no-referrer';result.headers['Cache-Control']='no-store'
        return result

    class PairApproval(BaseModel):
        pairing_id:str

    @router.post('/api/auth/pair/approve')
    def approve_pair(body:PairApproval,request:Request):
        user=identity(request)
        pairing=store.get('_server','pairings',body.pairing_id)
        if pairing['expires']<time.time() or pairing.get('pending_tenant')!=user['tenant']:
            raise RelayError('ACCESS_DENIED','Only the consenting browser can approve this exact desktop pairing.')
        connection=store.get(user['tenant'],'private_connections','google');target=pairing['workspace']
        from .service import RelayService
        RelayService(store,target).settings()
        def commit(tx):
            p=tx.get('pairings',body.pairing_id);workspace=tx.get('workspaces',target)
            if not workspace or workspace.get('expires',time.time()+1)<=time.time() or p['status']!='pending' or p['expires']<time.time():raise RelayError('AUTH_REQUIRED','Pairing or destination expired.')
            destination=tx.workspace(target);destination.put('private_connections','google',connection)
            settings=destination.get('meta','settings');settings.update(calendar_live=False,calendar_connection=None,calendar_id='local-illustrative-calendar');destination.put('meta','settings',settings);destination.advance()
            tx.workspace(user['tenant']).delete('private_connections','google')
            tx.put('pairings',body.pairing_id,dict(p,status='approved',tenant=target))
        store.atomic('_server',commit)
        if store.get('_server','pairings',body.pairing_id)['status']!='approved':
            raise RelayError('AUTH_REQUIRED','Pairing expired or already consumed.')
        return new_session(target)

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
