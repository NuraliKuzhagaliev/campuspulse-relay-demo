import asyncio
import hashlib
import os
import secrets
import time
from contextlib import asynccontextmanager, AsyncExitStack
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
from . import alternative_live
from .providers import selected, current_availability

store=make_store()
CLOUD=os.getenv('RELAY_MODE')=='cloud'
PUBLIC_DEMO=public_demo.enabled()
ALTERNATIVE=alternative_live.enabled()
TEMPORARY_WEB=PUBLIC_DEMO or ALTERNATIVE
selected()  # Refuse invalid provider/deployment combinations before serving traffic.
if ALTERNATIVE:
    alternative_live.configuration()
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
            if TEMPORARY_WEB:
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
    async with AsyncExitStack() as stack:
        if ALTERNATIVE:
            from .mcp_server import mcp
            await stack.enter_async_context(mcp.session_manager.run())
        task=asyncio.create_task(poll())
        try:
            yield
        finally:
            task.cancel()


app=FastAPI(title='CampusPulse RELAY',version='0.4.0',lifespan=lifespan,
            docs_url=None if TEMPORARY_WEB else '/docs',redoc_url=None if TEMPORARY_WEB else '/redoc',
            openapi_url=None if TEMPORARY_WEB else '/openapi.json')
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
    if TEMPORARY_WEB:
        allowed_route=alternative_live.route_allowed if ALTERNATIVE else public_demo.route_allowed
        if not allowed_route(request.url.path,request.method):
            return JSONResponse({'error':{'code':'ACCESS_DENIED','message':'This public illustrative demo does not expose Google connections, managed AI, MCP, administrative or test operations. Mandatory GCP acceptance remains pending.'}},status_code=403)
        try:
            public_demo.limit('_global','requests',1200)
        except RelayError as exc:
            return JSONResponse({'error':exc.as_dict()},status_code=429)
        if request.method=='POST' and (request.url.path.startswith('/api/import') or request.url.path.startswith('/api/passport/')):
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
        if TEMPORARY_WEB and (os.getenv('RELAY_GATEWAY_URL') or os.getenv('RENDER_EXTERNAL_URL')):
            allowed={os.getenv('RELAY_GATEWAY_URL') or os.getenv('RENDER_EXTERNAL_URL')}
        if not TEMPORARY_WEB:
            allowed.update({'http://127.0.0.1:5173','http://localhost:5173'})
        if origin and origin not in allowed:
            return JSONResponse({'error':{'code':'ACCESS_DENIED','message':'Request origin is not allowed.'}},status_code=403)
    if TEMPORARY_WEB and request.method=='POST' and not request.url.path.startswith('/_relay/'):
        async with expensive_requests:
            response=await call_next(request)
    else:
        response=await call_next(request)
    response.headers['X-Content-Type-Options']='nosniff'
    response.headers['Referrer-Policy']='no-referrer'
    if TEMPORARY_WEB:
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
    if TEMPORARY_WEB:
        if not record['tenant'].startswith(('demo-','judge-') if ALTERNATIVE else ('demo-',)):
            raise RelayError('ACCESS_DENIED','This session is not a public demo workspace.')
        if request.method not in ('GET','HEAD'):
            public_demo.limit(record['tenant'],'writes',30)
    return record


def service(record=Depends(identity)):
    return RelayService(store,record['tenant'])


def new_session(tenant,expires=None):
    token,csrf=secrets.token_urlsafe(32),secrets.token_urlsafe(24)
    seconds=public_demo.SESSION_SECONDS if TEMPORARY_WEB else 86400
    lifetime=max(1,int(min(expires or time.time()+seconds,time.time()+seconds)-time.time()))
    store.put('_server','sessions',digest(token),dict(tenant=tenant,csrf=csrf,expires=time.time()+lifetime))
    store.put('_server','workspaces',tenant,{'id':tenant},create=True)
    response=JSONResponse(dict(csrf=csrf,tenant=tenant,mode='alternative_live' if ALTERNATIVE else 'public_demo' if PUBLIC_DEMO else 'cloud' if CLOUD else 'local',authenticated=CLOUD or tenant.startswith('judge-')))
    response.set_cookie('relay_session',token,httponly=True,secure=CLOUD or TEMPORARY_WEB,samesite='strict',max_age=lifetime)
    return response


@app.get('/api/session')
def session(request:Request):
    if request.cookies.get('relay_session'):
        try:
            record=identity(request)
            return dict(csrf=record['csrf'],tenant=record['tenant'],mode='alternative_live' if ALTERNATIVE else 'public_demo' if PUBLIC_DEMO else 'cloud' if CLOUD else 'local',authenticated=CLOUD or record['tenant'].startswith('judge-'))
        except RelayError:
            pass
    if CLOUD:
        raise RelayError('AUTH_REQUIRED','Sign in through Google in the system browser, or use an owner-issued one-use judge invitation.')
    if TEMPORARY_WEB:
        public_demo.cleanup(store)
        public_demo.limit('_global','new-sessions',60,3600)
        if len(store.list('_server','workspaces'))>=100:
            raise RelayError('UPSTREAM_RATE_LIMITED','Public demo capacity is full. Retry after temporary sessions expire.')
        return new_session('demo-'+secrets.token_hex(16))
    return new_session('local-'+secrets.token_hex(16))


@app.post('/api/demo/reset')
def reset_demo(record=Depends(identity)):
    if not TEMPORARY_WEB:
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
    agent=current_availability(store)
    return dict(ok=True,version=app.version,mode='alternative_live' if ALTERNATIVE else 'public_demo' if PUBLIC_DEMO else 'cloud' if CLOUD else 'local',agent_configured=agent['configured'],agent_verified=agent['verified'],agent=agent,time=now(),
                deployed_commit=os.getenv('RELAY_DEPLOYED_COMMIT') or os.getenv('RENDER_GIT_COMMIT'),
                demo=dict(public_demo.metadata(),gemini='private_invitation_required',mandatory_gcp='exception_pending') if ALTERNATIVE else public_demo.metadata() if PUBLIC_DEMO else None)


@app.get('/api/state')
def state(svc=Depends(service)):
    value=svc.snapshot()
    if TEMPORARY_WEB:
        value['demo']=public_demo.metadata()
    return value


@app.get('/api/events')
def events(after:int=0,svc=Depends(service)):
    return dict(workspace_id=svc.tenant,events=store.events(svc.tenant,max(0,after)))


@app.get('/api/sources/{source_id}')
def source(source_id:str,svc=Depends(service)):
    return store.get(svc.tenant,'sources',source_id)


@app.post('/api/import')
async def import_file(file:UploadFile=File(...),svc=Depends(service)):
    content=await file.read(10*1024*1024+1)
    if TEMPORARY_WEB and len(content)>public_demo.MAX_UPLOAD_BYTES:
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
    if TEMPORARY_WEB and len(content)>public_demo.MAX_UPLOAD_BYTES:
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
    if TEMPORARY_WEB and body.watch_enabled:
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
    public_demo.forget(store,svc.tenant) if TEMPORARY_WEB else store.delete_workspace(svc.tenant)
    return {'deleted':True,'external_resources_deleted':False}


class TaskEdit(BaseModel):
    minutes:int|None=Field(default=None,ge=30,le=10080,multiple_of=30)
    due:str|None=None
    completion:str|None=Field(default=None,pattern='^(planned|worked_on|self_reported)$')
    remaining_minutes:int|None=Field(default=None,ge=0,le=10080,multiple_of=30)
    effort_max:int|None=Field(default=None,ge=30,le=10080,multiple_of=30)


@app.post('/api/tasks/{id}/settings')
def edit_task(id:str,body:TaskEdit,svc=Depends(service)):
    task=next((t for t in svc.tasks() if t['id']==id),None)
    if not task:
        raise RelayError('ACCESS_DENIED','Task unavailable.')
    values=body.model_dump(exclude_none=True)
    if body.remaining_minutes==0 and body.completion!='self_reported':
        raise RelayError('PARSE_FAILED','Zero remaining requires deliberate student-confirmed completion.')
    if store.list(svc.tenant,'progress') and any(p['id']==id for p in store.list(svc.tenant,'progress')) and (body.remaining_minutes is not None or body.completion is not None):
        raise RelayError('USE_PROGRESS','Use Progress & Remaining Work to record completion or remaining effort with revision history.')
    if body.minutes is not None and body.effort_max is None:
        values['effort_max']=body.minutes # Explicit point re-estimate; original source range remains in evidence.
    maximum=values.get('effort_max',task.get('effort_max'))
    point=values.get('minutes',task['minutes'])
    if maximum is not None and point is not None and maximum<point:
        raise RelayError('PARSE_FAILED','The effort maximum cannot be below the point estimate.')
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


class StrictBody(BaseModel):
    model_config={'extra':'forbid'}


class RevisionBody(StrictBody):
    request_id:str=Field(pattern='^[a-f0-9]{24,64}$')
    expected_revision:int=Field(ge=0)


class ProgressBody(RevisionBody):
    action:str=Field(pattern='^(start|log|stop|correct|remaining|unknown|complete)$')
    duration_minutes:float|None=Field(default=None,gt=0,le=1440)
    remaining_minutes:float|None=Field(default=None,gt=0,le=10080)
    session_id:str|None=Field(default=None,pattern='^[a-f0-9]{24}$')
    log_id:str|None=Field(default=None,pattern='^[a-f0-9]{24}$')
    log_revision:int|None=Field(default=None,ge=1)
    interruptions:str=Field(default='',max_length=500)
    reason:str=Field(default='',max_length=500)
    checklist:list[str]=Field(default_factory=list,max_length=30)
    evidence_id:str|None=Field(default=None,pattern='^[a-f0-9]{24}$')
    category:str=Field(default='',max_length=80)


@app.get('/api/additions')
def additions(svc=Depends(service)):
    from .progress import view
    from .handoff import list_gates
    return dict(**view(svc),gates=list_gates(svc),notifications=store.list(svc.tenant,'handoff_notifications'))


@app.post('/api/tasks/{id}/progress')
def task_progress(id:str,body:ProgressBody,svc=Depends(service)):
    from .progress import mutate
    return mutate(svc,id,body.model_dump())


class Heartbeat(StrictBody):
    delta_ms:float=Field(ge=0,le=86400000)
    session_revision:int=Field(ge=1)


@app.post('/api/work-sessions/{id}/heartbeat')
def work_heartbeat(id:str,body:Heartbeat,svc=Depends(service)):
    from .progress import heartbeat
    return heartbeat(svc,id,body.delta_ms,body.session_revision)


@app.get('/api/tasks/{id}/estimate-suggestion')
def estimate_suggestion(id:str,svc=Depends(service)):
    from .progress import suggestion
    return suggestion(svc,id)


@app.post('/api/progress/preview')
def progress_preview(svc=Depends(service)):
    proposal=svc.plan(proposal=True)
    store.put(svc.tenant,'progress_proposals',proposal['id'],proposal)
    return proposal


class AdoptBody(StrictBody):
    expected_revision:int=Field(ge=0)


@app.post('/api/progress/{id}/adopt')
def progress_adopt(id:str,body:AdoptBody,svc=Depends(service)):
    from .progress import check_revision
    proposal=store.get(svc.tenant,'progress_proposals',id)
    if proposal['sources']!=svc.source_versions():raise RelayError('STALE_PLAN','Workspace changed after the future-plan preview. Recompute it.')
    def update(tx):
        check_revision(tx,body.expected_revision)
        if proposal['sources']!=svc.source_versions():raise RelayError('STALE_PLAN','The proposal is outdated.')
        tx.put('plans',id,proposal);tx.put('meta','latest_plan',{'id':id})
        return proposal
    return store.atomic(svc.tenant,update)


class EffortBound(StrictBody):
    task_id:str=Field(pattern='^[a-f0-9]{24}$')
    values:list[int]=Field(min_length=2,max_length=2)


class ClarifyBody(StrictBody):
    request_id:str=Field(pattern='^[a-f0-9]{24,64}$')
    candidate_ids:list[str]=Field(default_factory=list,max_length=3)
    bounds:list[EffortBound]=Field(default_factory=list,max_length=3)
    offered_windows:list[dict]=Field(default_factory=list,max_length=3)


@app.post('/api/clarify')
def clarify(body:ClarifyBody,svc=Depends(service)):
    from .clarify import analyze
    return analyze(svc,body.model_dump())


@app.post('/api/clarify/{id}/cancel')
def cancel_clarify(id:str,svc=Depends(service)):
    from .clarify import cancel
    return cancel(svc,id)


class ClarifyAnswer(RevisionBody):
    candidate_id:str=Field(pattern='^[a-f0-9]{24}$')
    choice:int|None=Field(default=None,ge=0,le=1)


@app.post('/api/clarify/{id}/answer')
def answer_clarify(id:str,body:ClarifyAnswer,svc=Depends(service)):
    from .clarify import answer
    return answer(svc,id,body.model_dump())


class GateBody(RevisionBody):
    task_id:str=Field(pattern='^[a-f0-9]{24}$')
    repo:str=Field(min_length=3,max_length=201)
    number:int=Field(ge=1,le=100000000)
    eta:str|None=None


@app.post('/api/gates')
def link_gate(body:GateBody,svc=Depends(service)):
    from .handoff import link
    return link(svc,body.model_dump())


@app.post('/api/gates/{id}/observe')
def observe_gate(id:str,svc=Depends(service)):
    from .handoff import observe
    return observe(svc,id)


@app.post('/api/gates/{id}/remove')
def remove_gate(id:str,body:RevisionBody,svc=Depends(service)):
    from .handoff import remove
    return remove(svc,id,body.model_dump())


@app.post('/api/gates/notifications/{id}/claim')
def claim_gate_notification(id:str,svc=Depends(service)):
    def update(tx):
        notification=tx.get('handoff_notifications',id)
        if not notification:raise RelayError('ACCESS_DENIED','Notification unavailable in this workspace.')
        if notification.get('dispatch_claimed_at'):return dict(claimed=False)
        tx.put('handoff_notifications',id,dict(notification,dispatch_claimed_at=now()))
        return dict(claimed=True,visibility_verified=False)
    return store.atomic(svc.tenant,update)


@app.post('/api/gates/conditional-preview')
def conditional_gate_preview(svc=Depends(service)):
    from .clarify import payload
    from .handoff import apply_gates
    from .scheduler import build_recovery_plan
    value=payload(svc)
    for task in value['tasks']:task.pop('external_blocked',None);task.pop('release_not_before',None)
    notes=apply_gates(svc,value,conditional=True)
    return dict(build_recovery_plan(value),conditional=True,gate_notes=notes,canonical_workspace_unchanged=True)


class ExportPassport(StrictBody):
    source_ids:list[str]|None=Field(default=None,max_length=12)


@app.post('/api/passport/export')
def export_passport(body:ExportPassport,svc=Depends(service)):
    from .passport import export
    return export(svc,body.source_ids)


@app.post('/api/passport/preview')
def preview_passport(body:NativeFile,svc=Depends(service)):
    import base64
    from .passport import stage
    if not body.name.endswith('.json') or '/' in body.name or '\\' in body.name:raise RelayError('PASSPORT_INVALID','Select a .relay.json portable file or legacy .json snapshot.')
    try:content=base64.b64decode(body.content,validate=True)
    except Exception:raise RelayError('PASSPORT_INVALID','Portable file could not be decoded.')
    return stage(svc,content)


@app.post('/api/passport/{id}/restore')
def restore_passport(id:str,record=Depends(identity)):
    from .passport import commit
    svc=RelayService(store,record['tenant'])
    try:result=store.get(svc.tenant,'passport_copies',id)
    except RelayError:
        if TEMPORARY_WEB:
            public_demo.cleanup(store)
            if len(store.list('_server','workspaces'))>=100:raise RelayError('UPSTREAM_RATE_LIMITED','Public demo workspace capacity is full; the original remains unchanged.')
        result=commit(svc,id)
    return new_session(result['tenant'],expires=record['expires'])


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
    if not chosen or chosen.get('primary') or chosen.get('id')=='primary':
        raise RelayError('ACCESS_DENIED','Choose a calendar verified for your Google identity.')
    settings=svc.settings();settings.update(calendar_id=chosen['id'],calendar_live=True,mode='personal')
    store.put(svc.tenant,'meta','settings',settings)
    return {'calendar':chosen}


class Chat(BaseModel):
    message:str=Field(min_length=1,max_length=6000)
    language:str=Field(default='en',pattern='^(en|ru|kk)$')
    conversation_id:str|None=Field(default=None,pattern='^[a-f0-9]{32}$')
    request_id:str|None=Field(default=None,pattern='^[a-zA-Z0-9_-]{16,80}$')
    adult_confirmed:bool=False
    permitted_processing:bool=False
    processing_region:str|None=None


@app.get('/api/conversation')
def get_conversation(svc=Depends(service)):
    from .conversations import conversation
    try:
        id=store.get(svc.tenant,'meta','conversation')['id']
        value=conversation(store,svc.tenant,id)
        try:lease=store.get(svc.tenant,'conversation_leases',id)
        except RelayError:lease={}
        return dict(value,active_run=lease.get('owner') if lease.get('until',0)>time.time() else None)
    except RelayError:
        value=conversation(store,svc.tenant)
        store.put(svc.tenant,'meta','conversation',{'id':value['id']})
        return value


@app.post('/api/conversation/new')
def new_conversation(svc=Depends(service)):
    from .conversations import conversation
    try:
        old=store.get(svc.tenant,'meta','conversation')['id']
        store.claim(svc.tenant,'conversations',old,{'closed':False},{'closed':True})
    except RelayError:pass
    value=conversation(store,svc.tenant)
    store.put(svc.tenant,'meta','conversation',{'id':value['id']})
    return value


@app.post('/api/runs/{id}/cancel')
def cancel_run(id:str,svc=Depends(service)):
    record=store.get(svc.tenant,'agent_runs',id)
    store.claim(svc.tenant,'agent_runs',id,{'status':'running'},{'status':'cancel_requested'})
    return dict(status='cancel_requested',remote_compute_stopped=False,message='Stopped waiting is not proof that remote compute stopped. Inspect events and receipts before retrying.')


@app.post('/api/chat')
async def chat(body:Chat,svc=Depends(service)):
    config=selected()
    resource=config['resource']
    if not config['configured']:
        raise RelayError('AUTH_REQUIRED','The real Gemini Agent Engine is not connected. Local planning and evidence tools remain available.')
    if config['provider']=='gemini_developer':
        alternative_live.authorize_query(svc.settings(),body.adult_confirmed,body.permitted_processing,body.processing_region)
    from .conversations import begin_run, finish_run, conversation, RUN_SECONDS
    body.conversation_id=body.conversation_id or get_conversation(svc)['id']
    body.request_id=body.request_id or secrets.token_hex(16)
    record,created=begin_run(store,svc.tenant,body.conversation_id,body.request_id,body.message)
    if not created:
        return record.get('result',dict(status=record['status'],text='',run_id=record['id'],remote_compute_stopped=False))
    run=record['id']
    store.event(svc.tenant,run,'run_started',summary='Sending your request to the selected Gemini route.',resource=resource,provider=config['provider'],deployment_mode=config['deployment_mode'])
    token=sign_context(svc.tenant,os.environ['RELAY_MCP_URL'],os.environ['RELAY_CONTEXT_SECRET'])
    try:
        invoke=invoke_alternative_query if config['provider']=='gemini_developer' else invoke_managed_query
        result=await asyncio.wait_for(asyncio.to_thread(invoke,resource,user_id=svc.tenant,message=body.message,context_token=token,language=body.language,run_id=run,
            conversation_id=body.conversation_id,history=conversation(store,svc.tenant,body.conversation_id)['turns']),timeout=RUN_SECONDS)
    except asyncio.TimeoutError:
        result=dict(status='unknown',text='',reason='The gateway wait timed out. Remote compute may still be running. Review events and receipts before retrying.',remote_compute_stopped=False)
    except Exception as exc:
        code=getattr(exc,'code',None)
        limited=code in (429,'RESOURCE_EXHAUSTED','UPSTREAM_RATE_LIMITED')
        if limited:
            from .model_usage import throttle
            throttle(store)
        result=dict(status='failed',text='',code='UPSTREAM_RATE_LIMITED' if limited else 'UPSTREAM_UNAVAILABLE',reason='Gemini rate limit reached. Retry after the allowance resets.' if limited else 'The selected Gemini route could not complete this request. Check account access and service configuration.')
    result=finish_run(store,svc.tenant,record,body.message,result)
    kind={'complete':'run_completed','partial':'run_partial','failed':'run_failed','unknown':'run_unknown','cancelled':'run_cancelled'}.get(result['status'],'run_unknown')
    store.event(svc.tenant,run,kind,summary='Agent outcome',resource=resource,provider=config['provider'],deployment_mode=config['deployment_mode'])
    if result['status']=='complete':
        store.put('_server','agent_evidence',digest(resource),dict(resource=resource,run_id=run,revision=config['revision'] or 'unreported',observed_at=now(),expires=time.time()+300,provider=config['provider'],deployment_mode=config['deployment_mode'],model=config['model']))
    else:
        store.put('_server','agent_failures',digest(resource),dict(failed_at=now(),run_id=run,status=result['status'],code=result.get('code')))
    return result


def invoke_managed_query(resource,**kwargs):
    """Keep discovery/cold-start/network I/O outside ASGI and within the wait budget."""
    import vertexai
    client=vertexai.Client(project=os.environ['GOOGLE_CLOUD_PROJECT'],location=os.environ['GOOGLE_CLOUD_LOCATION'])
    return client.agent_engines.get(name=resource).query(**kwargs)


def invoke_alternative_query(resource,**kwargs):
    from .agent import RelayRuntime
    return RelayRuntime().query(**kwargs)


class AssignmentMapping(BaseModel):
    section_key:str=Field(pattern='^[a-f0-9]{24}$')
    course:str=Field(default='',max_length=180)
    term:str=Field(default='',max_length=100)
    assignment_key:str=Field(default='',max_length=180)
    target_id:str|None=Field(default=None,pattern='^[a-f0-9]{24}$')


@app.post('/api/sources/{id}/mapping')
def assignment_mapping(id:str,body:AssignmentMapping,svc=Depends(service)):
    return svc.map_assignment(id,body.section_key,body.course,body.term,body.assignment_key,body.target_id)


class RescueBody(BaseModel):
    scenario:Scenario|None=None
    additions:list[dict]=Field(default_factory=list,max_length=5)


@app.post('/api/rescue')
def rescue(body:RescueBody,svc=Depends(service)):
    from .rescue import minimal_rescue
    baseline=svc.plan(body.scenario.model_dump(exclude_none=True)) if body.scenario else svc.plan()
    result=minimal_rescue(baseline,body.additions)
    id=secrets.token_hex(16)
    value=dict(result,id=id,sources=svc.source_versions(),baseline_id=baseline['id'],created_at=now())
    store.put(svc.tenant,'rescues',id,value)
    return value


class RescueChoice(BaseModel):
    remedy_id:str=Field(pattern='^[a-f0-9]{24}$')


@app.post('/api/rescues/{id}/choose')
def choose_rescue(id:str,body:RescueChoice,svc=Depends(service)):
    record=store.get(svc.tenant,'rescues',id)
    if record['sources']!=svc.source_versions():
        raise RelayError('STALE_PLAN','The comparison is outdated. Compare offered additions again.')
    remedy=next((r for r in record['remedies'] if r['id']==body.remedy_id),None)
    if not remedy:raise RelayError('ACCESS_DENIED','Choose a remedy from your own comparison.')
    settings=svc.settings()
    settings['windows']=remedy['plan']['input']['windows']
    store.put(svc.tenant,'meta','settings',settings)
    svc.invalidate_plans()
    return svc.plan() # Reads current busy state again. Still no write without a fresh immutable preview.


class SubmissionBody(NativeFile):
    task_id:str=Field(pattern='^[a-f0-9]{24}$')
    exceptions:dict[str,str]=Field(default_factory=dict,max_length=20)
    present_files:list[str]=Field(default_factory=list,max_length=30)


@app.post('/api/preflight')
def submission_preflight(body:SubmissionBody,svc=Depends(service)):
    import base64
    from .preflight import check_submission
    task=svc.packet(body.task_id)['task']
    try:content=base64.b64decode(body.content,validate=True)
    except Exception:raise RelayError('PARSE_FAILED','The selected draft could not be decoded.')
    if TEMPORARY_WEB and len(content)>public_demo.MAX_UPLOAD_BYTES:
        raise RelayError('UNSUPPORTED_INPUT','Public demo draft limit is 2 MiB.')
    facts=[f for f in svc.current_facts() if f['task_id']==body.task_id]
    result=check_submission(body.name,content,facts,body.exceptions,body.present_files)
    result.update(task_id=body.task_id,source_versions=svc.source_versions())
    store.put(svc.tenant,'preflights',result['id'],result)
    return result


class PreflightRecovery(BaseModel):
    extra_minutes:int=Field(ge=30,le=600,multiple_of=30)


@app.post('/api/preflights/{id}/recovery')
def preflight_recovery(id:str,body:PreflightRecovery,svc=Depends(service)):
    record=store.get(svc.tenant,'preflights',id)
    if not record['missing_count']:raise RelayError('SOURCE_CONFLICT','No structurally missing requirement was observed.')
    if record['source_versions']!=svc.source_versions():raise RelayError('STALE_PLAN','Requirements changed; check the draft again.')
    return svc.plan(dict(task_id=record['task_id'],extra_minutes=body.extra_minutes))


@app.get('/api/challenge')
def challenge(svc=Depends(service)):
    snapshot=svc.snapshot()
    return dict(workspace_id=svc.tenant,mode=snapshot['settings']['mode'],calendar_mode=snapshot['calendar_mode'],
        sources=[dict(id=s['id'],version=s['version'],fetched_at=s['fetched_at'],mode=s['mode']) for s in snapshot['sources']],
        tasks=snapshot['tasks'],plan=snapshot['plan'],events=snapshot['events'],receipts=snapshot['receipts'],
        preflights=store.list(svc.tenant,'preflights'),reset_scope='this visitor only',
        live_acceptance='pending',agent=snapshot['agent'])


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

if ALTERNATIVE:
    class AIInvitationBatch(StrictBody):
        count:int=Field(ge=1,le=8)
        hours:int=Field(ge=1,le=12)
        timestamp:int
        nonce:str=Field(pattern='^[a-f0-9]{32}$')

    @app.post('/internal/ai-invitations')
    def ai_invitation_batch(body:AIInvitationBatch,request:Request):
        from .ai_invitations import issue
        return issue(store,body.model_dump(),request.headers.get('x-relay-owner-signature',''))

    from .mcp_server import app as internal_mcp_app
    app.mount('/_relay',internal_mcp_app)

dist=Path(__file__).parent.parent/'dist'
if dist.exists():
    app.mount('/assets',StaticFiles(directory=dist/'assets'),name='assets')
    @app.get('/')
    def index():
        return FileResponse(dist/'index.html')
