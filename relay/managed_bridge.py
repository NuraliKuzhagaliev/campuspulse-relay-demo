"""Optional organizer-window query bridge. No personal credentials or auto replay."""
import hashlib,hmac,json,os,time,secrets
from .domain import RelayError,instant
from .auth import verify_context,sign_context,RunAuthorization

def configuration(for_intake=True):
    try:
        from .managed_operator import stored_configuration
        stored=stored_configuration()
        if stored is not None:
            if not stored.get('enabled'):return None
            value=dict(stored,expiry=instant(stored['expiry']).timestamp(),activation=instant(stored['activation']).timestamp())
        else:
            if os.getenv('RELAY_MANAGED_ROUTE_ENABLED')!='true':return None
            value=dict(expiry=instant(os.environ['RELAY_MANAGED_EXPIRES_AT']).timestamp(),activation=instant(os.environ['RELAY_MANAGED_ACTIVATED_AT']).timestamp(),
                url=os.environ['RELAY_MANAGED_BRIDGE_URL'],resource=os.environ['RELAY_MANAGED_RESOURCE'],secret=os.environ['RELAY_MANAGED_BRIDGE_SECRET'],model=os.environ['RELAY_MANAGED_MODEL'],revision=os.environ['RELAY_MANAGED_REVISION'],
                mcp_url=os.environ.get('RELAY_MANAGED_MCP_URL'),audience=os.environ.get('RELAY_MANAGED_AUDIENCE'),principals=os.environ.get('RELAY_MANAGED_PRINCIPALS','').split(','))
        if not value['activation']<=time.time()<value['expiry']-(3600 if for_intake else 0) or not value['url'].startswith('https://') or not value['resource'].startswith('projects/') or len(value['secret'])<32:return None
        return value
    except (KeyError,RelayError):return None

def signature(body,stamp,nonce,secret):
    payload=json.dumps(body,sort_keys=True,separators=(',',':')).encode()
    return hmac.new(secret.encode(),str(stamp).encode()+b'.'+nonce.encode()+b'.'+hashlib.sha256(payload).hexdigest().encode(),hashlib.sha256).hexdigest()

def invoke(**args):
    config=configuration()
    if not config:raise RelayError('AUTH_REQUIRED','The authorized managed intake window is inactive. No remote call was made.')
    tenant=verify_context(args['context_token'],os.environ['RELAY_MCP_URL'],os.environ['RELAY_CONTEXT_SECRET'])
    if tenant!=args['user_id']:raise RelayError('ACCESS_DENIED','Managed route workspace mismatch.')
    authorization=RunAuthorization(args['context_token'],os.environ['RELAY_MCP_URL'],os.environ['RELAY_CONTEXT_SECRET'],seconds=600)
    args=dict(args,context_token=sign_context(tenant,config['mcp_url'],os.environ['RELAY_CONTEXT_SECRET'],seconds=max(1,int(authorization.until-time.time()))))
    body=dict(resource=config['resource'],arguments=args);stamp=int(time.time());nonce=secrets.token_hex(16)
    import httpx
    try:
        response=httpx.post(config['url'].rstrip('/')+'/query',json=body,headers={'X-Relay-Time':str(stamp),'X-Relay-Nonce':nonce,'X-Relay-Signature':signature(body,stamp,nonce,config['secret'])},timeout=605)
        result=response.json()
    except Exception as exc:raise RelayError('UPSTREAM_UNAVAILABLE','Managed query outcome is unknown. It was not replayed on an unpaid provider.') from exc
    if response.status_code!=200:raise RelayError(result.get('error',{}).get('code','UPSTREAM_UNAVAILABLE'),'The managed query bridge rejected or could not complete this request.')
    if result.get('provider')!='vertex' or result.get('deployment_mode')!='managed_gcp':raise RelayError('UPSTREAM_UNAVAILABLE','Managed response provenance does not match the selected route.')
    return result
