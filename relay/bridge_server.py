"""Minimal organizer-covered Cloud Run bridge; application auth is mandatory.

Render has no Google SA key. This narrow signed query entrypoint uses the Cloud
Run service identity to invoke exactly one configured managed Agent Engine.
"""
import asyncio,os,re,time,threading
from collections import OrderedDict
from fastapi import FastAPI,Request
from fastapi.responses import JSONResponse
from .domain import RelayError,instant
from .managed_bridge import signature
from .auth import verify_context
app=FastAPI(docs_url=None,redoc_url=None,openapi_url=None)
_nonces=OrderedDict();_lock=threading.Lock();_slots=asyncio.Semaphore(2)

@app.exception_handler(RelayError)
async def error(request,exc):return JSONResponse({'error':{'code':exc.code,'message':exc.message}},status_code=403 if exc.code=='ACCESS_DENIED' else 503)

def validate(body,headers):
    import hmac
    secret=os.getenv('RELAY_MANAGED_BRIDGE_SECRET','')
    if len(secret)<32:raise RelayError('ACCESS_DENIED','Bridge is not configured.')
    try:
        stamp=int(headers.get('x-relay-time',''));nonce=headers.get('x-relay-nonce','')
        active=instant(os.environ['RELAY_MANAGED_ACTIVATED_AT']).timestamp();expiry=instant(os.environ['RELAY_MANAGED_EXPIRES_AT']).timestamp()
        if not active<=time.time()<expiry-3600 or abs(time.time()-stamp)>60 or not re.fullmatch('[a-f0-9]{32}',nonce):raise ValueError()
        if not isinstance(body,dict) or set(body)!={'resource','arguments'} or body['resource']!=os.environ['RELAY_AGENT_RESOURCE']:raise ValueError()
        if not hmac.compare_digest(headers.get('x-relay-signature',''),signature(body,stamp,nonce,secret)):raise ValueError()
        args=body['arguments']
        if set(args)-{'user_id','message','context_token','language','run_id','conversation_id','history'}:raise ValueError()
        tenant=verify_context(args['context_token'],os.environ['RELAY_MCP_URL'],os.environ['RELAY_CONTEXT_SECRET'])
        if tenant!=args['user_id'] or not re.fullmatch('[a-f0-9]{32}',args['run_id']) or not re.fullmatch('[a-f0-9]{32}',args['conversation_id']) or not isinstance(args['message'],str) or len(args['message'])>6000:raise ValueError()
    except (ValueError,TypeError,KeyError,RelayError) as exc:raise RelayError('ACCESS_DENIED','Invalid, expired or wrong-scope bridge request.') from exc
    with _lock:
        for key,at in list(_nonces.items()):
            if at<time.time()-120:_nonces.pop(key,None)
        if nonce in _nonces:raise RelayError('ACCESS_DENIED','Bridge request already consumed.')
        if len(_nonces)>=1024:raise RelayError('UPSTREAM_RATE_LIMITED','Bridge admission is full.')
        _nonces[nonce]=time.time()
    return args

@app.get('/health')
def health():return dict(ok=True,role='managed_query_bridge',configured=bool(os.getenv('RELAY_AGENT_RESOURCE')),remote_query_verified=False)

@app.post('/query')
async def query(request:Request):
    total=0;chunks=[]
    async for chunk in request.stream():
        total+=len(chunk)
        if total>256000:raise RelayError('ACCESS_DENIED','Bridge body exceeds its bounded limit.')
        chunks.append(chunk)
    import json
    try:body=json.loads(b''.join(chunks))
    except ValueError as exc:raise RelayError('ACCESS_DENIED','Invalid bridge JSON.') from exc
    args=validate(body,request.headers)
    def invoke():
        import vertexai
        client=vertexai.Client(project=os.environ['GOOGLE_CLOUD_PROJECT'],location=os.environ['GOOGLE_CLOUD_LOCATION'])
        remote=client.agent_engines.get(name=os.environ['RELAY_AGENT_RESOURCE'])
        if remote.api_resource.name!=os.environ['RELAY_AGENT_RESOURCE']:raise RelayError('ACCESS_DENIED','Managed discovery differs from configured resource.')
        result=remote.query(**args)
        if not isinstance(result,dict):raise RelayError('UPSTREAM_UNAVAILABLE','Managed query returned an unusable result.')
        return dict(result,managed_resource=remote.api_resource.name)
    async with _slots:
        try:return await asyncio.wait_for(asyncio.to_thread(invoke),timeout=600)
        except RelayError:raise
        except Exception as exc:raise RelayError('UPSTREAM_UNAVAILABLE','Managed invocation failed or has an unknown outcome; no alternate provider was invoked.') from exc
