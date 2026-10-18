import asyncio
import hashlib
import os
import secrets
import time
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request, UploadFile, File, Depends
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, ValidationError
from .domain import RelayError, now, digest, Task
from .store import make_store
from .service import RelayService
from .auth import sign_context
from . import public_demo

store=make_store()
CLOUD=os.getenv('RELAY_MODE')=='cloud'
PUBLIC_DEMO=public_demo.enabled()
if PUBLIC_DEMO:
    public_demo.configuration()
if CLOUD:
    for key in ('GOOGLE_CLOUD_PROJECT','RELAY_AGENT_RESOURCE','RELAY_CONTEXT_SECRET','RELAY_AUTH_AUDIENCE','RELAY_MCP_URL'):
        if not os.getenv(key):
            raise RuntimeError(f'Cloud startup refused: missing {key}')
    if len(os.environ['RELAY_CONTEXT_SECRET'])<32:
        raise RuntimeError('Cloud context secret must contain at least 32 characters.')


@asynccontextmanager
async def lifespan(app):
    async def poll():
        # Local background polling is genuine server-side work, but not hosted autonomy proof.
        while True:
            await asyncio.sleep(max(30,int(os.getenv('RELAY_POLL_SECONDS','60'))))
            if PUBLIC_DEMO:
                await asyncio.to_thread(public_demo.cleanup,store)
                continue
            if CLOUD:
                continue # Authenticated Cloud Scheduler invokes /internal/sync for durable cloud execution.
            for workspace in store.list('_server','workspaces'):
                svc=RelayService(store,workspace['id'])
                try:
                    if svc.settings().get('watch_enabled'):
                        await asyncio.to_thread(svc.sync_repo,False)
                        await asyncio.to_thread(svc.sync_calendar)
                except RelayError as exc:
                    if exc.code!='AUTH_REQUIRED':
                        store.event(workspace['id'],'radar-error','run_failed',summary=exc.message,code=exc.code)
    task=asyncio.create_task(poll())
    yield
    task.cancel()


app=FastAPI(title='CampusPulse RELAY',version='0.1.1',lifespan=lifespan,
            docs_url=None if PUBLIC_DEMO else '/docs',redoc_url=None if PUBLIC_DEMO else '/redoc',
            openapi_url=None if PUBLIC_DEMO else '/openapi.json')
expensive_requests=asyncio.Semaphore(2)


@app.exception_handler(RelayError)
async def relay_error(request,exc):
    status={'AUTH_REQUIRED':401,'ACCESS_DENIED':403,'UPSTREAM_RATE_LIMITED':429,'UPSTREAM_UNAVAILABLE':503}.get(exc.code,409)
    return JSONResponse({'error':exc.as_dict()},status_code=status)


@app.exception_handler(ValidationError)
async def validation_error(request,exc):
    return JSONResponse({'error':{'code':'PARSE_FAILED','message':'The structured input is invalid; review dates, effort and required fields.'}},status_code=422)


@app.middleware('http')
async def protect(request,call_next):
    if PUBLIC_DEMO:
        if not public_demo.route_allowed(request.url.path,request.method):
            return JSONResponse({'error':{'code':'ACCESS_DENIED','message':'This public illustrative demo does not expose Google connections, managed AI, MCP, administrative or test operations. Mandatory GCP acceptance remains pending.'}},status_code=403)
        try:
            public_demo.limit('_global','requests',1200)
        except RelayError as exc:
            return JSONResponse({'error':exc.as_dict()},status_code=429)
        if request.method=='POST' and request.url.path.startswith('/api/import'):
            # Count streamed bytes as well as Content-Length: chunked bodies cannot bypass the limit.
            total=0;chunks=[]
            async for chunk in request.stream():
                total+=len(chunk)
                if total>3*1024*1024:
                    return JSONResponse({'error':{'code':'UNSUPPORTED_INPUT','message':'Public demo upload limit is 2 MiB.'}},status_code=413)
                chunks.append(chunk)
            request._body=b''.join(chunks)
    if request.headers.get('content-length','0').isdigit() and int(request.headers.get('content-length','0'))>11*1024*1024:
        return JSONResponse({'error':{'code':'UNSUPPORTED_INPUT','message':'Upload limit is 10 MiB.'}},status_code=413)
    if request.method not in ('GET','HEAD','OPTIONS') and request.url.path.startswith('/api/'):
        origin=request.headers.get('origin')
        allowed={str(request.base_url).rstrip('/'),os.getenv('RELAY_GATEWAY_URL','')}
        if PUBLIC_DEMO and (os.getenv('RELAY_GATEWAY_URL') or os.getenv('RENDER_EXTERNAL_URL')):
            allowed={os.getenv('RELAY_GATEWAY_URL') or os.getenv('RENDER_EXTERNAL_URL')}
        if not PUBLIC_DEMO:
            allowed.update({'http://127.0.0.1:5173','http://localhost:5173'})
        if origin and origin not in allowed:
            return JSONResponse({'error':{'code':'ACCESS_DENIED','message':'Request origin is not allowed.'}},status_code=403)
    if PUBLIC_DEMO and request.method=='POST':
        async with expensive_requests:
            response=await call_next(request)
    else:
        response=await call_next(request)
    response.headers['X-Content-Type-Options']='nosniff'
    response.headers['Referrer-Policy']='no-referrer'
    if PUBLIC_DEMO:
        response.headers['X-Frame-Options']='DENY'
        response.headers['X-Robots-Tag']='noindex, nofollow'
        response.headers['Content-Security-Policy']="default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; font-src 'self'; img-src 'self' data:; connect-src 'self'; base-uri 'none'; object-src 'none'; frame-ancestors 'none'"
        response.headers['Strict-Transport-Security']='max-age=31536000'
    if request.url.path.startswith('/api'):
        response.headers['Cache-Control']='no-store'
    return response


def identity(request:Request):
    token=request.cookies.get('relay_session')
    if not token:
        raise RelayError('AUTH_REQUIRED','Start a workspace or sign in first.')
    try:
        record=store.get('_server','sessions',digest(token))
    except RelayError:
        raise RelayError('AUTH_REQUIRED','Session expired. Sign in again.')
    if record['expires']<time.time():
        raise RelayError('AUTH_REQUIRED','Session expired. Sign in again.')
    if request.method not in ('GET','HEAD') and request.headers.get('x-relay-csrf')!=record['csrf']:
        raise RelayError('ACCESS_DENIED','Missing workspace request protection.')
    if PUBLIC_DEMO:
        if not record['tenant'].startswith('demo-'):
            raise RelayError('ACCESS_DENIED','This session is not a public demo workspace.')
        if request.method not in ('GET','HEAD'):
            public_demo.limit(record['tenant'],'writes',30)
    return record


def service(record=Depends(identity)):
    return RelayService(store,record['tenant'])


def new_session(tenant,expires=None):
    token,csrf=secrets.token_urlsafe(32),secrets.token_urlsafe(24)
    seconds=public_demo.SESSION_SECONDS if PUBLIC_DEMO else 86400
    lifetime=max(1,int(min(expires or time.time()+seconds,time.time()+seconds)-time.time()))
    store.put('_server','sessions',digest(token),dict(tenant=tenant,csrf=csrf,expires=time.time()+lifetime))
    store.put('_server','workspaces',tenant,{'id':tenant},create=True)
    response=JSONResponse(dict(csrf=csrf,tenant=tenant,mode='public_demo' if PUBLIC_DEMO else 'cloud' if CLOUD else 'local',authenticated=CLOUD))
    response.set_cookie('relay_session',token,httponly=True,secure=CLOUD or PUBLIC_DEMO,samesite='strict',max_age=lifetime)
    return response


@app.get('/api/session')
def session(request:Request):
    if request.cookies.get('relay_session'):
        try:
            record=identity(request)
            return dict(csrf=record['csrf'],tenant=record['tenant'],mode='public_demo' if PUBLIC_DEMO else 'cloud' if CLOUD else 'local',authenticated=CLOUD)
        except RelayError:
            pass
    if CLOUD:
        raise RelayError('AUTH_REQUIRED','Sign in through Google in the system browser, or use an owner-issued one-use judge invitation.')
    if PUBLIC_DEMO:
        public_demo.cleanup(store)
        public_demo.limit('_global','new-sessions',60,3600)
        if len(store.list('_server','workspaces'))>=100:
            raise RelayError('UPSTREAM_RATE_LIMITED','Public demo capacity is full. Retry after temporary sessions expire.')
        return new_session('demo-'+secrets.token_hex(16))
    return new_session('local-'+secrets.token_hex(16))


@app.post('/api/demo/reset')
def reset_demo(record=Depends(identity)):
    if not PUBLIC_DEMO:
        raise RelayError('ACCESS_DENIED','Public demo reset is unavailable in this mode.')
    public_demo.limit('_global','new-sessions',60,3600)
    public_demo.forget(store,record['tenant'])
    return new_session('demo-'+secrets.token_hex(16))


class JudgeInvitation(BaseModel):
    invitation:str=Field(min_length=40,max_length=100)


@app.post('/api/judge/claim')
def judge_claim(body:JudgeInvitation,request:Request):
    from .judge import claim
    from .limits import consume
    # Global bounded attempts plus cryptographic invitations; no URL tokens or public account passwords.
    consume(store,'_server','judge-claim',60,60)
    tenant,expires=claim(store,body.invitation)
    return new_session(tenant,expires)


class GoogleToken(BaseModel):
    credential:str=Field(max_length=10000)


@app.post('/api/auth/google')
def google_auth(body:GoogleToken):
    if not CLOUD:
        raise RelayError('AUTH_REQUIRED','Google sign-in is only enabled on the configured HTTPS gateway.')
    from google.oauth2 import id_token
    from google.auth.transport.requests import Request as GoogleRequest
    try:
        value=id_token.verify_oauth2_token(body.credential,GoogleRequest(),os.environ['RELAY_AUTH_AUDIENCE'])
        if not value.get('email_verified'):
            raise ValueError()
    except Exception as exc:
        raise RelayError('AUTH_REQUIRED','Google identity verification failed.') from exc
    tenant=hashlib.sha256(value['sub'].encode()).hexdigest()
    # Workspace provisioning is intentionally separate from identity verification.
    return new_session(tenant)


@app.get('/api/health')
def health():
    return dict(ok=True,version='0.1.1',mode='public_demo' if PUBLIC_DEMO else 'cloud' if CLOUD else 'local',agent_configured=bool(os.getenv('RELAY_AGENT_RESOURCE')),agent_verified=False,time=now(),
                deployed_commit=os.getenv('RELAY_DEPLOYED_COMMIT') or os.getenv('RENDER_GIT_COMMIT'),
                demo=public_demo.metadata() if PUBLIC_DEMO else None)


@app.get('/api/state')
def state(svc=Depends(service)):
    value=svc.snapshot()
    if PUBLIC_DEMO:
        value['demo']=public_demo.metadata()
    return value


@app.get('/api/events')
def events(after:int=0,svc=Depends(service)):
    return dict(events=store.events(svc.tenant,max(0,after)))


@app.get('/api/sources/{source_id}')
def source(source_id:str,svc=Depends(service)):
    return store.get(svc.tenant,'sources',source_id)


@app.post('/api/import')
async def import_file(file:UploadFile=File(...),svc=Depends(service)):
    content=await file.read(10*1024*1024+1)
    if PUBLIC_DEMO and len(content)>public_demo.MAX_UPLOAD_BYTES:
        raise RelayError('UNSUPPORTED_INPUT','Public demo imports must be at most 2 MiB.')
    return await asyncio.to_thread(svc.import_source,file.filename or 'upload.txt',content)


class NativeFile(BaseModel):
    name:str=Field(max_length=200)
    content:str=Field(max_length=14*1024*1024)


@app.post('/api/import-native')
def import_native(body:NativeFile,svc=Depends(service)):
    import base64
    try:
        content=base64.b64decode(body.content,validate=True)
    except Exception:
        raise RelayError('PARSE_FAILED','The selected file could not be decoded.')
    if PUBLIC_DEMO and len(content)>public_demo.MAX_UPLOAD_BYTES:
        raise RelayError('UNSUPPORTED_INPUT','Public demo imports must be at most 2 MiB.')
    return svc.import_source(body.name,content)


class Resolution(BaseModel):
    fact_id:str


@app.post('/api/conflicts/{conflict_id}/resolve')
def resolve(conflict_id:str,body:Resolution,svc=Depends(service)):
    return svc.resolve(conflict_id,body.fact_id)


@app.post('/api/plan')
def plan(svc=Depends(service)):
    return svc.plan()


class Scenario(BaseModel):
    remove_weekday:int|None=Field(default=None,ge=0,le=6)
    extra_minutes:int|None=Field(default=None,ge=30,le=600,multiple_of=30)
    task_id:str|None=None


@app.post('/api/scenario')
def scenario(body:Scenario,svc=Depends(service)):
    return svc.plan(body.model_dump(exclude_none=True))


@app.post('/api/plans/{id}/preview')
def preview(id:str,svc=Depends(service)):
    return svc.actions().preview(store.get(svc.tenant,'plans',id))


class ApprovalBody(BaseModel):
    digest:str


@app.post('/api/previews/{id}/approve')
def approve(id:str,body:ApprovalBody,record=Depends(identity)):
    svc=RelayService(store,record['tenant'])
    authorization=svc.actions().authorize(id,body.digest,record['tenant'])
    return svc.actions().apply(authorization)


@app.post('/api/receipts/{id}/verify')
def verify(id:str,svc=Depends(service)):
    return svc.actions().verify(id)


@app.post('/api/receipts/{id}/undo')
def undo(id:str,svc=Depends(service)):
    return svc.actions().undo(id)


@app.get('/api/packets/{id}')
def packet(id:str,svc=Depends(service)):
    return svc.packet(id)


class Preferences(BaseModel):
    watch_enabled:bool|None=None
    timezone:str|None=None
    daily_cap_minutes:int|None=Field(default=None,ge=30,le=720,multiple_of=30)
    windows:list[dict]|None=Field(default=None,max_length=100)


@app.post('/api/preferences')
def preferences(body:Preferences,svc=Depends(service)):
    if PUBLIC_DEMO and body.watch_enabled:
        raise RelayError('ACCESS_DENIED','The public demo supports manual GitHub refresh. Durable background execution requires the pending GCP deployment.')
    s=svc.settings()
    if body.timezone:
        from zoneinfo import ZoneInfo
        try:
            ZoneInfo(body.timezone)
        except Exception:
            raise RelayError('PARSE_FAILED','Use an IANA timezone, such as Asia/Almaty.')
    if body.windows is not None:
        from .domain import Interval,instant
        for window in body.windows:
            value=Interval.model_validate(window)
            if instant(value.end)<=instant(value.start):
                raise RelayError('PARSE_FAILED','Availability end must follow start.')
    s.update(body.model_dump(exclude_none=True))
    store.put(svc.tenant,'meta','settings',s)
    return s


@app.post('/api/sync')
def sync(svc=Depends(service)):
    return svc.sync_repo()


@app.get('/api/export')
def export(svc=Depends(service)):
    return svc.snapshot()


@app.delete('/api/workspace')
def delete_workspace(svc=Depends(service)):
    public_demo.forget(store,svc.tenant) if PUBLIC_DEMO else store.delete_workspace(svc.tenant)
    return {'deleted':True,'external_resources_deleted':False}


class TaskEdit(BaseModel):
    minutes:int|None=Field(default=None,ge=30,le=10080,multiple_of=30)
    due:str|None=None
    completion:str|None=Field(default=None,pattern='^(planned|worked_on|self_reported)$')


@app.post('/api/tasks/{id}/settings')
def edit_task(id:str,body:TaskEdit,svc=Depends(service)):
    task=next((t for t in svc.tasks() if t['id']==id),None)
    if not task:
        raise RelayError('ACCESS_DENIED','Task unavailable.')
    values=body.model_dump(exclude_none=True)
    Task.model_validate(dict(task,**values))
    try:
        old=store.get(svc.tenant,'task_overrides',id)['values']
    except RelayError:
        old={}
    store.put(svc.tenant,'task_overrides',id,dict(id=id,values=dict(old,**values),origin='explicit_user_input',updated_at=now()))
    for plan in store.list(svc.tenant,'plans'):
        if any(t['id']==id for t in plan['input']['tasks']):
            plan['invalidated']=True;store.put(svc.tenant,'plans',plan['id'],plan)
    return svc.packet(id)


@app.get('/api/connections/calendar-list')
def list_calendars(svc=Depends(service)):
    from .oauth import calendar_list
    return {'calendars':calendar_list(store,svc.tenant)}


class CalendarSelection(BaseModel):
    calendar_id:str


@app.post('/api/connections/calendar')
def select_calendar(body:CalendarSelection,svc=Depends(service)):
    if svc.settings().get('mode')=='judge':
        raise RelayError('ACCESS_DENIED','Judge sessions remain bound to their exclusive owner-approved demo calendar.')
    from .oauth import calendar_list
    calendars=calendar_list(store,svc.tenant)
    chosen=next((c for c in calendars if c['id']==body.calendar_id),None)
    if not chosen:
        raise RelayError('ACCESS_DENIED','Choose a calendar verified for your Google identity.')
    settings=svc.settings();settings.update(calendar_id=chosen['id'],calendar_live=True,mode='personal')
    store.put(svc.tenant,'meta','settings',settings)
    return {'calendar':chosen}


class Chat(BaseModel):
    message:str=Field(min_length=1,max_length=6000)
    language:str=Field(default='en',pattern='^(en|ru|kk)$')


@app.post('/api/chat')
async def chat(body:Chat,svc=Depends(service)):
    resource=os.getenv('RELAY_AGENT_RESOURCE')
    if not resource:
        raise RelayError('AUTH_REQUIRED','The real Gemini Agent Engine is not connected. Local planning and evidence tools remain available.')
    from .limits import model_request
    model_request(store,svc.tenant,judge=svc.settings().get('mode')=='judge')
    import vertexai
    client=vertexai.Client(project=os.environ['GOOGLE_CLOUD_PROJECT'],location=os.environ['GOOGLE_CLOUD_LOCATION'])
    remote=client.agent_engines.get(name=resource)
    run=secrets.token_hex(16)
    store.event(svc.tenant,run,'run_started',summary='Sending your request to the managed Gemini agent.',resource=resource)
    token=sign_context(svc.tenant,os.environ['RELAY_MCP_URL'],os.environ['RELAY_CONTEXT_SECRET'])
    try:
        result=await asyncio.to_thread(remote.query,user_id=svc.tenant,message=body.message,context_token=token,language=body.language,run_id=run)
    except Exception as exc:
        store.event(svc.tenant,run,'run_failed',summary='Remote agent request failed. No success is inferred.')
        raise RelayError('UPSTREAM_UNAVAILABLE','The managed agent could not complete this request. Check deployment and consent.') from exc
    store.event(svc.tenant,run,'run_completed',summary='Managed agent returned.',resource=resource)
    return result


@app.post('/internal/sync')
async def scheduled_sync(request:Request):
    if not CLOUD:
        raise RelayError('ACCESS_DENIED','Cloud scheduler endpoint is disabled locally.')
    from google.oauth2 import id_token
    from google.auth.transport.requests import Request as GoogleRequest
    try:
        value=id_token.verify_oauth2_token(request.headers.get('Authorization','').removeprefix('Bearer '),GoogleRequest(),os.environ['RELAY_GATEWAY_URL'])
        if value.get('email')!=os.environ['RELAY_SCHEDULER_IDENTITY']:
            raise ValueError()
    except Exception:
        raise RelayError('ACCESS_DENIED','Authenticated scheduler identity is required.')
    results=[]
    for workspace in store.list('_server','workspaces'):
        svc=RelayService(store,workspace['id'])
        try:
            if svc.settings().get('watch_enabled'):
                results.append(await asyncio.to_thread(svc.sync_repo,False))
                results.append(await asyncio.to_thread(svc.sync_calendar))
        except RelayError as exc:
            if exc.code!='AUTH_REQUIRED':
                results.append(exc.as_dict())
    return dict(results=results)


from .oauth import install as install_oauth
app.include_router(install_oauth(store,new_session,identity))

dist=Path(__file__).parent.parent/'dist'
if dist.exists():
    app.mount('/assets',StaticFiles(directory=dist/'assets'),name='assets')
    @app.get('/')
    def index():
        return FileResponse(dist/'index.html')
