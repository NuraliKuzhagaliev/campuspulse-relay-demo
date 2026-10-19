"""Private AI-only access: the owner key and returned invitations never reach stdout."""
import argparse
import base64
import json
import os
import secrets
import subprocess
import sys
import time
from pathlib import Path
import httpx
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from relay.domain import digest


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--url',required=True)
    p.add_argument('--count',type=int,default=2,choices=range(1,9))
    p.add_argument('--hours',type=int,default=4,choices=range(1,13))
    a=p.parse_args()
    if not a.url.startswith('https://') or os.name!='nt':
        p.error('Use the intended HTTPS host from the owner Windows workspace.')
    root=Path(__file__).resolve().parents[1]
    if root.drive.lower()!='d:':p.error('Owner configuration and private outputs must remain on D:.')
    keypath=root/'.local/private/ai-owner-key.dpapi'
    if not keypath.exists():p.error('Run scripts/configure-ai-owner.ps1 first.')
    command="$s=Get-Content -LiteralPath '"+str(keypath).replace("'","''")+"' -Raw | ConvertTo-SecureString;$p=[Runtime.InteropServices.Marshal]::SecureStringToBSTR($s);try{[Console]::Out.Write([Runtime.InteropServices.Marshal]::PtrToStringBSTR($p))}finally{[Runtime.InteropServices.Marshal]::ZeroFreeBSTR($p)}"
    raw=subprocess.check_output(['powershell.exe','-NoProfile','-Command',command],env=os.environ,stderr=subprocess.DEVNULL)
    key=Ed25519PrivateKey.from_private_bytes(base64.b64decode(raw))
    body=dict(count=a.count,hours=a.hours,nonce=secrets.token_hex(16),timestamp=int(time.time()))
    signed=digest(dict(method='POST',path='/internal/ai-invitations',body=body)).encode()
    signature=base64.b64encode(key.sign(signed)).decode()
    response=httpx.post(a.url.rstrip('/')+'/internal/ai-invitations',json=body,headers={'X-Relay-Owner-Signature':signature},timeout=75)
    if response.status_code!=200:
        print('Invitation preparation failed: HTTP '+str(response.status_code)+'. No token is printed.',file=sys.stderr)
        return 1
    private=root/'.local/judge-private';private.mkdir(parents=True,exist_ok=True)
    output=private/('ai-'+body['nonce']+'.json')
    output.write_text(json.dumps(dict(gateway=a.url,**response.json()),indent=2),encoding='utf-8')
    print(json.dumps(dict(private_file=str(output),count=a.count,hours=a.hours,calendar_authorized=False)))
    return 0


if __name__=='__main__':raise SystemExit(main())
