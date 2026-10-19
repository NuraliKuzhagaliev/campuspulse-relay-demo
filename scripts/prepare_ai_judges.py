"""Private AI-only access: the owner key and returned invitations never reach stdout."""
import argparse
import base64
import json
import os
import secrets
import subprocess
import sys
import time
import ssl
from datetime import datetime
from pathlib import Path
import httpx
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from relay.domain import digest


def bounded_server_timestamp(value, started, finished):
    """Allow small owner clock skew; never weaken the server's 60-second signature gate."""
    remote=datetime.fromisoformat(value)
    if remote.tzinfo is None or not 0<=finished-started<=10:
        raise ValueError('A fast timezone-aware HTTPS clock observation is required.')
    epoch=remote.timestamp()
    if abs(epoch-(started+finished)/2)>300:
        raise ValueError('Server/owner clock disagreement exceeds five minutes; verify the clocks.')
    return int(epoch+(finished-started)/2)


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--url',required=True)
    p.add_argument('--count',type=int,default=2,choices=range(1,9))
    p.add_argument('--hours',type=int,default=4,choices=range(1,13))
    p.add_argument('--local-development-ca',action='store_true')
    a=p.parse_args()
    if not a.url.startswith('https://') or os.name!='nt':
        p.error('Use the intended HTTPS host from the owner Windows workspace.')
    root=Path(__file__).resolve().parents[1]
    if root.drive.lower()!='d:':p.error('Owner configuration and private outputs must remain on D:.')
    keypath=root/'.local/private/ai-owner-key.dpapi'
    if not keypath.exists():p.error('Run scripts/configure-ai-owner.ps1 first.')
    from windows_dpapi import unprotect
    raw=unprotect(keypath)
    key=Ed25519PrivateKey.from_private_bytes(base64.b64decode(raw))
    verify=True
    if a.local_development_ca:
        if a.url.rstrip('/')!='https://localhost:8017':p.error('Development CA is only allowed for this project loopback staging URL.')
        verify=ssl.create_default_context(cafile=str(root/'.local/final-integration/tls/cert.pem'))
    started=time.time()
    clock=httpx.get(a.url.rstrip('/')+'/api/health',timeout=75,verify=verify)
    finished=time.time()
    clock.raise_for_status()
    timestamp=bounded_server_timestamp(clock.json()['time'],started,finished)
    body=dict(count=a.count,hours=a.hours,nonce=secrets.token_hex(16),timestamp=timestamp)
    signed=digest(dict(method='POST',path='/internal/ai-invitations',body=body)).encode()
    signature=base64.b64encode(key.sign(signed)).decode()
    response=httpx.post(a.url.rstrip('/')+'/internal/ai-invitations',json=body,headers={'X-Relay-Owner-Signature':signature},timeout=75,verify=verify)
    if response.status_code!=200:
        print('Invitation preparation failed: HTTP '+str(response.status_code)+'. No token is printed.',file=sys.stderr)
        return 1
    private=root/'.local/judge-private';private.mkdir(parents=True,exist_ok=True)
    output=private/('ai-'+body['nonce']+'.json')
    output.write_text(json.dumps(dict(gateway=a.url,**response.json()),indent=2),encoding='utf-8')
    print(json.dumps(dict(private_file=str(output),count=a.count,hours=a.hours,calendar_authorized=False)))
    return 0


if __name__=='__main__':raise SystemExit(main())
