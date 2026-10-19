"""Owner-only no-restart managed cutover. No provisioning, no invitations.

Init generates a dedicated current-user DPAPI signing key on D:. Bootstrap
receives the existing context secret encrypted to an ephemeral X25519 recipient;
only DPAPI ciphertext is saved. Activate requires an actual fresh funding record.
"""
import argparse,base64,json,os,secrets,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization,hashes
from relay.domain import digest
from relay.managed_operator import PATH
from windows_dpapi import protect,unprotect
root=Path(__file__).resolve().parents[1];private=root/'.local/private';keyfile=private/'managed-owner.dpapi'

def main():
    parser=argparse.ArgumentParser();parser.add_argument('operation',choices=['init','bootstrap','activate','deactivate']);parser.add_argument('--url',default='https://campuspulse-relay-demo.onrender.com');parser.add_argument('--configuration');parser.add_argument('--funding-record',default=str(root/'.local/funding-verification.json'));args=parser.parse_args()
    if root.drive.lower()!='d:' or not args.url.startswith('https://'):parser.error('Private owner operations require D: and the exact HTTPS app origin.')
    if args.operation=='init':
        if not keyfile.exists():
            key=Ed25519PrivateKey.generate();protect(base64.b64encode(key.private_bytes(serialization.Encoding.Raw,serialization.PrivateFormat.Raw,serialization.NoEncryption())).decode(),keyfile)
        key=Ed25519PrivateKey.from_private_bytes(base64.b64decode(unprotect(keyfile)))
        public=base64.b64encode(key.public_key().public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw)).decode()
        (private/'managed-owner-public.json').write_text(json.dumps({'public_key':public,'purpose':'managed_route_only'}),encoding='utf-8')
        print(json.dumps({'public_key':public,'private_key_encrypted_on_D':True,'cloud_calls':0}));return
    key=Ed25519PrivateKey.from_private_bytes(base64.b64decode(unprotect(keyfile)));body=dict(op=args.operation,timestamp=int(time.time()),nonce=secrets.token_hex(16));ephemeral=None
    if args.operation=='bootstrap':
        from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
        ephemeral=X25519PrivateKey.generate();body['recipient_key']=base64.b64encode(ephemeral.public_key().public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw)).decode()
    elif args.operation=='activate':
        if not args.configuration:parser.error('A private actual-resource configuration on D: is required.')
        path=Path(args.configuration).resolve()
        if path.drive.lower()!='d:':parser.error('Configuration must remain on D:.')
        config=json.loads(path.read_text(encoding='utf-8-sig'))
        record_path=Path(args.funding_record).resolve();record=json.loads(record_path.read_text(encoding='utf-8-sig'))
        from relay.funding import validate_funding
        # The actual project is part of the discovered resource, not supplied by a visitor.
        project=config['resource'].split('/')[1]
        if project not in (record['project_id'],str(record.get('project_number'))):parser.error('Resource and organizer funding project differ.')
        validate_funding(record,record['project_id'],float(record.get('authorized_credit_usage_usd',0)),1)
        if config['activation']!=record['activated_at_utc'] or config['expiry']!=record['expires_at_utc']:parser.error('Actual organizer window differs from route configuration.')
        body.update(configuration=config,funding_record_sha256=__import__('hashlib').sha256(record_path.read_bytes()).hexdigest())
    signed=base64.b64encode(key.sign(digest(dict(method='POST',path=PATH,body=body)).encode())).decode()
    import httpx
    response=httpx.post(args.url.rstrip('/')+PATH,json=body,headers={'X-Relay-Owner-Signature':signed},timeout=30)
    if response.status_code!=200:raise SystemExit('Owner route operation failed (HTTP '+str(response.status_code)+'). No secret response was printed.')
    result=response.json()
    if ephemeral:
        from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PublicKey
        from cryptography.hazmat.primitives.kdf.hkdf import HKDF
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        shared=ephemeral.exchange(X25519PublicKey.from_public_bytes(base64.b64decode(result['server_key'])))
        derived=HKDF(algorithm=hashes.SHA256(),length=32,salt=None,info=b'relay-managed-owner-bootstrap-v1').derive(shared)
        value=AESGCM(derived).decrypt(base64.b64decode(result['nonce']),base64.b64decode(result['ciphertext']),digest(body).encode()).decode()
        protect(value,private/'managed-context.dpapi');value=None
        print(json.dumps({'context_received_encrypted':True,'saved_with_windows_dpapi_on_D':True,'cloud_calls':0}));return
    print(json.dumps(result))
if __name__=='__main__':main()
