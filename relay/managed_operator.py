"""Owner-signed routing configuration, with no restart or visitor data reset.

This is not exposed as an MCP tool. The independent owner signing key is never
stored on the host. Neither this endpoint nor an activation flag verifies GCP.
"""
import base64,os,time,re,hashlib,json
from .domain import RelayError,digest,now,instant
PATH='/internal/managed-route'

def cipher():
    from cryptography.fernet import Fernet
    return Fernet(base64.urlsafe_b64encode(hashlib.sha256((os.environ['RELAY_CONTEXT_SECRET']+'|managed-route-v1').encode()).digest()))

def stored_configuration():
    if os.getenv('RELAY_MODE')!='alternative_live' or not os.getenv('RELAY_MANAGED_OWNER_PUBLIC_KEY'):return None
    from .store import Store
    try:
        record=Store().get('_server','managed_route','current')
        return json.loads(cipher().decrypt(record['ciphertext'].encode()))
    except RelayError:return None
    except Exception as exc:raise RelayError('UPSTREAM_UNAVAILABLE','Managed routing configuration cannot be decrypted; no unknown route is used.') from exc

def operate(store,body,signature):
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
        if not isinstance(body,dict) or set(body)-{'op','timestamp','nonce','recipient_key','configuration','funding_record_sha256'} or abs(time.time()-body['timestamp'])>60 or not re.fullmatch('[a-f0-9]{32}',body['nonce']):raise ValueError()
        key=Ed25519PublicKey.from_public_bytes(base64.b64decode(os.environ['RELAY_MANAGED_OWNER_PUBLIC_KEY'],validate=True))
        key.verify(base64.b64decode(signature,validate=True),digest(dict(method='POST',path=PATH,body=body)).encode())
        op=body['op']
        if op not in ('bootstrap','activate','deactivate'):raise ValueError()
    except Exception as exc:raise RelayError('ACCESS_DENIED','A fresh signature from the dedicated managed-route owner key is required.') from exc
    if op=='bootstrap':
        from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey,X25519PublicKey
        from cryptography.hazmat.primitives.kdf.hkdf import HKDF
        from cryptography.hazmat.primitives import hashes,serialization
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        try:
            recipient=X25519PublicKey.from_public_bytes(base64.b64decode(body['recipient_key'],validate=True));server=X25519PrivateKey.generate()
            shared=server.exchange(recipient);key=HKDF(algorithm=hashes.SHA256(),length=32,salt=None,info=b'relay-managed-owner-bootstrap-v1').derive(shared)
            nonce=os.urandom(12);encrypted=AESGCM(key).encrypt(nonce,os.environ['RELAY_CONTEXT_SECRET'].encode(),digest(body).encode())
        except Exception as exc:raise RelayError('PARSE_FAILED','Invalid owner bootstrap recipient.') from exc
        if not store.put('_server','managed_owner_requests',body['nonce'],{'digest':digest(body),'op':op,'at':now()},create=True):raise RelayError('ACCESS_DENIED','Owner bootstrap request already consumed.')
        return dict(server_key=base64.b64encode(server.public_key().public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw)).decode(),nonce=base64.b64encode(nonce).decode(),ciphertext=base64.b64encode(encrypted).decode(),plaintext_returned=False)
    config=body.get('configuration',{}) if op=='activate' else {'enabled':False}
    if op=='activate':
        try:
            required={'resource','url','secret','model','revision','activation','expiry','principals','audience','mcp_url'}
            if not isinstance(config,dict) or set(config)!=required or not re.fullmatch(r'projects/[A-Za-z0-9_-]+/locations/[a-z0-9-]+/reasoningEngines/[A-Za-z0-9_-]+',config['resource']):raise ValueError()
            from urllib.parse import urlsplit
            url=urlsplit(config['url']);aud=urlsplit(config['audience'])
            if url.scheme!='https' or not url.hostname or url.username or url.password or url.query or url.fragment or url.path not in ('','/'):raise ValueError()
            if aud.scheme!='https' or not aud.hostname or aud.path or aud.query or aud.fragment or aud.username or aud.password:raise ValueError()
            if config['mcp_url']!=config['audience']+'/managed/mcp/' or len(config['secret'])<32 or not re.fullmatch('[a-f0-9]{64}',body.get('funding_record_sha256','')):raise ValueError()
            start=instant(config['activation']).timestamp();end=instant(config['expiry']).timestamp()
            if not start<=time.time()+300 or end-start>12*3600+300 or end<=time.time()+3600:raise ValueError()
            if not isinstance(config['principals'],list) or not 1<=len(config['principals'])<=2 or any(not re.fullmatch(r'[A-Za-z0-9_.-]+@[A-Za-z0-9-]+\.iam\.gserviceaccount\.com',p) for p in config['principals']):raise ValueError()
            if any(not isinstance(config[k],str) or not 1<=len(config[k])<=180 for k in ('model','revision')):raise ValueError()
            config=dict(config,enabled=True,configured_at=now(),funding_record_sha256=body['funding_record_sha256'])
        except (ValueError,TypeError,KeyError,RelayError) as exc:raise RelayError('PARSE_FAILED','Managed route must name one actual organizer resource, bounded window and exact machine audience/principal. Configuration is not deployment proof.') from exc
    encrypted=cipher().encrypt(json.dumps(config,separators=(',',':')).encode()).decode()
    def commit(tx):
        prior=tx.get('managed_owner_requests',body['nonce'])
        if prior:
            if prior['digest']!=digest(body):raise RelayError('ACCESS_DENIED','Owner nonce cannot authorize a different operation.')
            return dict(prior['result'],duplicate=True)
        result=dict(configured=op=='activate',remote_verified=False,visitor_workspaces_reset=False,op=op,at=now())
        tx.put('managed_route','current',{'ciphertext':encrypted,'updated_at':now()})
        tx.put('managed_owner_requests',body['nonce'],{'digest':digest(body),'op':op,'at':now(),'result':result})
        return result
    return store.atomic('_server',commit)
