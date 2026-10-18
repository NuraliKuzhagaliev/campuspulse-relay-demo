import base64
import hashlib
import hmac
import json
import os
import time
from contextvars import ContextVar
from .domain import RelayError

workspace_context = ContextVar('workspace_context',default=None)


def sign_context(tenant,audience,secret,seconds=120):
    value={'sub':tenant,'aud':audience,'exp':int(time.time())+seconds,'scope':'relay:workspace'}
    encoded=base64.urlsafe_b64encode(json.dumps(value,separators=(',',':')).encode()).rstrip(b'=').decode()
    signature=hmac.new(secret.encode(),encoded.encode(),hashlib.sha256).hexdigest()
    return encoded+'.'+signature


def verify_context(token,audience,secret):
    try:
        encoded,signature=token.split('.')
        expected=hmac.new(secret.encode(),encoded.encode(),hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature,expected):
            raise ValueError()
        value=json.loads(base64.urlsafe_b64decode(encoded+'='*(-len(encoded)%4)))
        if value['aud']!=audience or value['exp']<=time.time() or value.get('scope')!='relay:workspace' or not value['sub'] or '/' in value['sub']:
            raise ValueError()
        return value['sub']
    except Exception as exc:
        raise RelayError('ACCESS_DENIED','Invalid, expired or wrong-audience workspace context.') from exc


class RunAuthorization:
    """Renew transport context only within the initially verified signed run lifetime."""
    def __init__(self,token,audience,secret,seconds=85):
        self.tenant=verify_context(token,audience,secret)
        encoded=token.split('.')[0]
        claims=json.loads(base64.urlsafe_b64decode(encoded+'='*(-len(encoded)%4)))
        self.until=min(claims['exp'],time.time()+seconds)
        self.audience,self.secret=audience,secret

    def context(self):
        remaining=int(self.until-time.time())
        if remaining<=0:raise RelayError('AUTH_REQUIRED','This run authorization expired; start a new authenticated request.')
        return sign_context(self.tenant,self.audience,self.secret,seconds=min(120,remaining))


def tenant_context():
    tenant=workspace_context.get()
    if not tenant:
        raise RelayError('AUTH_REQUIRED','An authenticated workspace context is required.')
    return tenant
