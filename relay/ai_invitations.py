"""Owner-signed AI-only invitations. The host never holds the private owner key."""
import base64
import hashlib
import hmac
import os
import time
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from .domain import RelayError, digest


def issue(store, body, signature):
    try:
        if abs(time.time()-body['timestamp'])>60:
            raise ValueError()
        key=Ed25519PublicKey.from_public_bytes(base64.b64decode(os.environ['RELAY_AI_ADMIN_PUBLIC_KEY'],validate=True))
        key.verify(base64.b64decode(signature,validate=True),digest(dict(method='POST',path='/internal/ai-invitations',body=body)).encode())
        if not 1<=body['count']<=8 or not 1<=body['hours']<=12:
            raise ValueError()
    except Exception:
        raise RelayError('ACCESS_DENIED','A fresh owner signature for this exact bounded AI-only operation is required.')
    secret=os.environ['RELAY_MCP_SERVICE_SECRET'].encode()
    tokens=[base64.urlsafe_b64encode(hmac.new(secret,f'judge-ai:{body["nonce"]}:{i}'.encode(),hashlib.sha256).digest()).rstrip(b'=').decode() for i in range(body['count'])]
    expires=body['timestamp']+body['hours']*3600
    def commit(tx):
        prior=tx.get('ai_invitation_batches',body['nonce'])
        stamp=digest([body,digest(secret.hex())])
        if prior and prior['digest']!=stamp:
            raise RelayError('ACCESS_DENIED','This operator request changed or the service restarted. Prepare a new signed request.')
        if not prior:
            for token in tokens:
                tx.put('judge_invites',digest(token),dict(kind='read_only_ai',status='pending',expires=expires,lifetime_seconds=body['hours']*3600))
            tx.put('ai_invitation_batches',body['nonce'],dict(digest=stamp,expires=expires))
        return dict(invitations=[dict(token=t,expires=expires,calendar_authorized=False,scope='adult_evaluator_KZ_non_sensitive_ai_only') for t in tokens],temporary_storage=True)
    return store.atomic('_server',commit)
