"""Verify the actual extracted web ZIP with the existing minimal Python environment."""
import base64
import hashlib
import json
import os
import sys
from datetime import datetime,timezone
from pathlib import Path
root=Path(__file__).resolve().parents[1]
stage=root/('.local/final-integration/web-bundle-'+os.getenv('RELAY_WEB_BUNDLE_REVISION','r2'))
os.environ['RELAY_MODE']='local';os.environ['RELAY_DATA_DIR']=str(root/'.local/final-integration/web-bundle-0.5.1-data')
for key in ('RELAY_GEMINI_API_KEY','RELAY_INFERENCE_PROVIDER','RELAY_DEPLOYMENT_MODE','RELAY_AGENT_RESOURCE'):os.environ.pop(key,None)
sys.path.insert(0,str(stage));os.chdir(stage)
from fastapi.testclient import TestClient
from relay.gateway import app
assert Path(sys.modules['relay.gateway'].__file__).is_relative_to(stage)
proof=dict(checked_at=datetime.now(timezone.utc).isoformat(),version='0.5.1',environment=sys.executable,extracted_root=str(stage),checks={},model_calls=0,real_calendar_writes=0)
with TestClient(app) as c:
    session=c.get('/api/session').json();headers={'X-Relay-CSRF':session['csrf']}
    def post(route,value=None):
        r=c.post('/api'+route,json=value or {},headers=headers)
        assert r.status_code==200,(route,r.status_code,r.text[:200])
        return r.json()
    assert c.get('/').status_code==200
    assert c.get('/api/health').json()['version']=='0.5.1'
    state=c.get('/api/state').json();conflict=state['conflicts'][0]
    post('/conflicts/'+conflict['id']+'/resolve',{'fact_id':sorted(conflict['facts'],key=lambda f:f['value'])[0]['id']})
    plan=post('/plan');assert plan['feasible']
    scenario=post('/scenario',dict(remove_weekday=2));assert not scenario['feasible']
    preview=post('/plans/'+plan['id']+'/preview');receipt=post('/previews/'+preview['id']+'/approve',dict(digest=preview['digest']))
    assert receipt['status']=='verified' and receipt['mode']=='illustrative'
    assert all(r['matches'] for r in post('/receipts/'+receipt['id']+'/verify')['results'])
    proof['checks']['plan_whatif_illustrative_approval_readback']=True
    text='Assignment: Unseen bundle optics note\nCourse: Optics\nTerm: 2026 Autumn\nAssignment ID: bundle-optics\nDue: 2026-10-24T19:00:00+05:00\nEffort: 30 minutes\n- [ ] Explain aberration evidence'
    imported=post('/import-native',dict(name='unseen-bundle.md',content=base64.b64encode(text.encode()).decode()))
    observed=c.get('/api/sources/'+imported['id']).json()
    assert observed['pages'][0]['text']==text
    proof['checks']['new_file_exact_readback_no_google']=True
    passport=post('/passport/export');assert passport['file']['format']=='campuspulse-relay-workspace'
    proof['checks']['portable_export_without_authority']=True
    assert c.post('/api/chat',headers=headers,json={'message':'Use real Gemini'}).status_code==401
    proof['checks']['unavailable_ai_is_not_canned']=True
proof['runtime_files']={p.relative_to(stage).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(stage.rglob('*')) if p.is_file() and '__pycache__' not in p.relative_to(stage).parts and '.local' not in p.relative_to(stage).parts}
assert 'relay/gateway.py' in proof['runtime_files'] and 'dist/index.html' in proof['runtime_files']
proof['passed']=True
(root/'docs/evidence/final-web-bundle-0.5.1.json').write_text(json.dumps(proof,indent=2)+'\n')
print(json.dumps(dict(passed=True,checks=len(proof['checks']),minimal_environment=sys.executable)))
