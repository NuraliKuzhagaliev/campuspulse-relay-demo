"""Managed-runtime access to the existing authoritative workspace backend.

Disabled until actual organizer SA/audience/window configuration is installed.
Machine Google identity and a bounded signed workspace/run are separate checks.
No client-supplied tenant, general database proxy or approval authority.
"""
import os,time
from .domain import RelayError,now
from .auth import verify_context

def authenticate(headers):
    from .managed_operator import stored_configuration
    stored=stored_configuration()
    principals={v.strip() for v in os.getenv('RELAY_MANAGED_PRINCIPALS','').split(',') if v.strip()}
    audience=os.getenv('RELAY_MANAGED_AUDIENCE','');context_audience=os.getenv('RELAY_MANAGED_MCP_URL','')
    if stored:
        if not stored.get('enabled'):raise RelayError('ACCESS_DENIED','Managed service access was retired.')
        principals=set(stored['principals']);audience=stored['audience'];context_audience=stored['mcp_url']
    bearer=headers.get('authorization','')
    if not principals or not audience.startswith('https://') or not context_audience.startswith(audience+'/') or not bearer.startswith('Bearer ') or len(bearer)<100:
        raise RelayError('ACCESS_DENIED','Managed machine identity is not configured or valid.')
    from .domain import instant
    if not instant(stored['activation'] if stored else os.getenv('RELAY_MANAGED_ACTIVATED_AT')).timestamp()<=time.time()<instant(stored['expiry'] if stored else os.getenv('RELAY_MANAGED_EXPIRES_AT')).timestamp():
        raise RelayError('ACCESS_DENIED','The actual organizer window is inactive.')
    try:
        from google.oauth2.id_token import verify_oauth2_token
        from google.auth.transport.requests import Request
        claims=verify_oauth2_token(bearer[7:],Request(),audience)
        if claims.get('email') not in principals or claims.get('email_verified') is not True:raise ValueError()
    except Exception as exc:raise RelayError('ACCESS_DENIED','Managed service identity was not verified.') from exc
    return verify_context(headers.get('x-relay-context',''),context_audience,os.environ['RELAY_CONTEXT_SECRET'])

def dispatch(store,tenant,body):
    from .public_ai import PublicQueue,QuotaGate
    if not isinstance(body,dict) or set(body)-{'op','run_id','kind','id','value','create','expected','changes','event_type','fields','request_bytes'}:
        raise RelayError('ACCESS_DENIED','Unsupported managed state operation.')
    run_id=body.get('run_id','');job=store.get('_server','public_ai_jobs',PublicQueue.key(tenant,run_id))
    if job['tenant']!=tenant or job['expires']<=time.time() or job['status'] not in ('running','quota_wait'):
        raise RelayError('REQUEST_CANCELLED','The originating workspace/run is inactive or expired.')
    store.get('_server','workspaces',tenant)
    op=body.get('op');kind=body.get('kind');id=body.get('id');conversation=job['conversation_id']
    if op=='begin':
        if not store.claim('_server','public_ai_jobs',job['id'],{'managed_runtime_started':None},{'managed_runtime_started':now()}):
            raise RelayError('RUN_IN_PROGRESS','This managed run was already invoked. Unknown outcomes are never replayed automatically.')
        return True
    if op=='reserve':
        size=body.get('request_bytes')
        if type(size) is not int or not 0<size<=110000:raise RelayError('UPSTREAM_RATE_LIMITED','Managed model context exceeds its bounded allowance.')
        info=QuotaGate(store).try_reserve(tenant,run_id,size)
        if not info['reserved']:store.claim('_server','public_ai_jobs',job['id'],{'status':'running'},{'status':'quota_wait'})
        else:store.claim('_server','public_ai_jobs',job['id'],{'status':'quota_wait'},{'status':'running'})
        return info
    if op=='event':
        event_type=body.get('event_type');fields=body.get('fields',{})
        if event_type not in ('tool_started','tool_finished','tool_failed','model_usage') or not isinstance(fields,dict) or set(fields)-{'tool','duration_ms','summary','input_tokens','output_tokens','thinking_tokens','total_tokens','observed_at'}:
            raise RelayError('ACCESS_DENIED','Unsupported managed event metadata.')
        if any(not isinstance(v,(str,int,float)) or len(str(v))>500 for v in fields.values()):raise RelayError('PARSE_FAILED','Managed event metadata is too large.')
        return store.event(tenant,run_id,event_type,**fields)
    if kind=='meta' and op=='get' and id=='settings':
        settings=store.get(tenant,'meta','settings')
        return {k:settings[k] for k in ('mode','timezone','anchor') if k in settings}
    if kind not in ('conversations','adk_sessions') or id!=conversation or op not in ('get','put','claim'):
        raise RelayError('ACCESS_DENIED','Managed state access is limited to this run conversation/checkpoint.')
    if op=='get':return store.get(tenant,kind,id)
    if kind!='adk_sessions':raise RelayError('ACCESS_DENIED','The managed runtime cannot rewrite conversation history or leases.')
    value=body.get('value') if op=='put' else body.get('changes')
    try:
        from google.adk.sessions import Session
        if not isinstance(value,dict) or set(value)!={'session','revision'} or type(value['revision']) is not int or value['revision']<0:raise ValueError()
        session=Session.model_validate(value['session'])
        if session.id!=conversation or session.user_id!=tenant or session.app_name!='campuspulse_relay' or session.state or len(session.events)>16:raise ValueError()
        if any(not getattr(part,'text',None) or getattr(part,'thought',False) or part.function_call or part.function_response for event in session.events for part in getattr(event.content,'parts',[]) or []):raise ValueError()
        if len(session.model_dump_json())>220000:raise ValueError()
        if op=='claim' and (set(body.get('expected',{}))!={'revision'} or value['revision']!=body['expected']['revision']+1):raise ValueError()
    except Exception as exc:raise RelayError('PARSE_FAILED','Managed ADK checkpoint has invalid identity, revision or non-public content.') from exc
    if op=='put':return store.put(tenant,kind,id,value,create=True)
    return store.claim(tenant,kind,id,body['expected'],value)

class RemoteStore:
    """Small ADK checkpoint adapter; domain writes stay in the backend/MCP."""
    def __init__(self,tenant,run_id,authorization):
        self.tenant,self.run_id,self.authorization=tenant,run_id,authorization

    def call(self,op,**fields):
        from google.auth.transport.requests import Request
        from google.oauth2.id_token import fetch_id_token
        import httpx
        url=os.environ['RELAY_STATE_URL'];audience=os.environ['RELAY_STATE_AUDIENCE']
        if not url.startswith(audience+'/') or not audience.startswith('https://'):raise RelayError('ACCESS_DENIED','Invalid managed state audience.')
        try:
            response=httpx.post(url,json=dict(op=op,run_id=self.run_id,**fields),headers={'Authorization':'Bearer '+fetch_id_token(Request(),audience),'X-Relay-Context':self.authorization.context()},timeout=20)
            value=response.json()
        except Exception as exc:raise RelayError('UPSTREAM_UNAVAILABLE','Authoritative workspace backend is unavailable; no alternate store was created.') from exc
        if response.status_code!=200:
            error=value.get('error',{});raise RelayError(error.get('code','ACCESS_DENIED'),error.get('message','Managed state request rejected.'))
        return value['result']

    def scope(self,tenant):
        if tenant!=self.tenant:raise RelayError('ACCESS_DENIED','Managed checkpoint scope differs from signed workspace.')
    def get(self,tenant,kind,id):self.scope(tenant);return self.call('get',kind=kind,id=id)
    def put(self,tenant,kind,id,value,create=False):self.scope(tenant);return self.call('put',kind=kind,id=id,value=value,create=create)
    def claim(self,tenant,kind,id,expected,changes):self.scope(tenant);return self.call('claim',kind=kind,id=id,expected=expected,changes=changes)
    def event(self,tenant,run_id,type,**fields):
        self.scope(tenant)
        if run_id!=self.run_id:raise RelayError('ACCESS_DENIED','Wrong managed run.')
        return self.call('event',event_type=type,fields=fields)
    def reserve(self,request_bytes):return self.call('reserve',request_bytes=request_bytes)
    def begin(self):return self.call('begin')
