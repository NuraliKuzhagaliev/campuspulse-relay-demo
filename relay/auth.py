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


def tenant_context():
    tenant=workspace_context.get()
    if not tenant:
        raise RelayError('AUTH_REQUIRED','An authenticated workspace context is required.')
    return tenant
