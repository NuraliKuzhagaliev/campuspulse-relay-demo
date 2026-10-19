import base64,json,time
from datetime import datetime,timezone,timedelta
import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey,X25519PublicKey
from cryptography.hazmat.primitives import serialization,hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from relay.managed_operator import operate,PATH
from relay.domain import digest,RelayError
from relay.store import Store

def test_signed_no_restart_cutover_preserves_visitor_and_never_returns_plain_context(tmp_path,monkeypatch):
    key=Ed25519PrivateKey.generate();public=base64.b64encode(key.public_key().public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw)).decode()
    for k,v in dict(RELAY_MODE='alternative_live',RELAY_DATA_DIR=str(tmp_path),RELAY_MANAGED_OWNER_PUBLIC_KEY=public,RELAY_CONTEXT_SECRET='PRIVATE_TEST_CONTEXT',RELAY_INFERENCE_PROVIDER='gemini_developer',RELAY_DEPLOYMENT_MODE='alternative_hosted',RELAY_GEMINI_API_KEY='INERT_TEST_ONLY',RELAY_GEMINI_FREE_ONLY='true').items():monkeypatch.setenv(k,v)
    store=Store();store.put('demo-a','progress','coursework',dict(logged=45,remaining=95));nonce=[0]
    def call(op,**fields):
        nonce[0]+=1;body=dict(op=op,timestamp=int(time.time()),nonce=f'{nonce[0]:032x}',**fields)
        signature=base64.b64encode(key.sign(digest(dict(method='POST',path=PATH,body=body)).encode())).decode()
        return body,operate(store,body,signature)
    ephemeral=X25519PrivateKey.generate();body,encrypted=call('bootstrap',recipient_key=base64.b64encode(ephemeral.public_key().public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw)).decode())
    assert 'PRIVATE_TEST_CONTEXT' not in json.dumps(encrypted)
    shared=ephemeral.exchange(X25519PublicKey.from_public_bytes(base64.b64decode(encrypted['server_key'])))
    derived=HKDF(algorithm=hashes.SHA256(),length=32,salt=None,info=b'relay-managed-owner-bootstrap-v1').derive(shared)
    assert AESGCM(derived).decrypt(base64.b64decode(encrypted['nonce']),base64.b64decode(encrypted['ciphertext']),digest(body).encode()).decode()=='PRIVATE_TEST_CONTEXT'
    now=datetime.now(timezone.utc)
    config=dict(resource='projects/organizer/locations/us-central1/reasoningEngines/one',url='https://bridge.test',secret='SECRET_BRIDGE_CANARY_'*3,model='actual-vertex-model',revision='actual-build',activation=now.isoformat(),expiry=(now+timedelta(hours=12)).isoformat(),principals=['runtime@organizer.iam.gserviceaccount.com'],audience='https://public.test',mcp_url='https://public.test/managed/mcp/')
    _,result=call('activate',configuration=config,funding_record_sha256='f'*64);assert not result['remote_verified'] and not result['visitor_workspaces_reset']
    from relay.providers import selected
    assert selected()['provider']=='vertex' and selected()['managed_agent_engine']
    assert 'SECRET_BRIDGE_CANARY' not in json.dumps(store.list('_server','managed_route'))
    assert store.get('demo-a','progress','coursework')==dict(logged=45,remaining=95)
    with pytest.raises(RelayError):operate(store,{'op':'deactivate','timestamp':time.time(),'nonce':'a'*32},'not-a-signature')
    call('deactivate');assert selected()['provider']=='gemini_developer'
    assert store.get('demo-a','progress','coursework')['remaining']==95
