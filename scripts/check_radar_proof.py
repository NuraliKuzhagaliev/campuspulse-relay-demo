import json
import sys
from pathlib import Path
from datetime import datetime
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from relay.store import make_store
from relay.service import RelayService
from relay.domain import now,instant
from relay.connectors import GitHub

before=json.loads(Path('docs/evidence/radar-prepared.json').read_text())
store=make_store();svc=RelayService(store,before['workspace'])
source=store.get(svc.tenant,'sources','github-coursework')
remote=source['remote'];events=store.events(svc.tenant)
if not remote.get('committed_at'):
    remote['committed_at']=GitHub(svc.settings()['github_repo']).get('commits/'+remote['commit'])['commit']['committer']['date']
triggered=[e for e in events if e['type']=='run_started' and e.get('commit')==remote['commit']]
proof=dict(checked_at=now(),baseline_commit=before['baseline_commit'],observed_commit=remote['commit'],changed=before['baseline_commit']!=remote['commit'],
           observed_at=source['fetched_at'],committed_at=remote.get('committed_at'),triggered_runs=len(triggered),cloud_hosted=False,gemini_connected=False,
           events=[e for e in events if e['run_id']=='change-'+source['version']])
if Path('.local/radar-trigger.json').exists() and source.get('observed_monotonic_ns'):
    trigger=json.loads(Path('.local/radar-trigger.json').read_text())
    proof['observed_latency_seconds']=round((source['observed_monotonic_ns']-trigger['monotonic_ns'])/1e9,3)
    proof['latency_method']='Same-host monotonic time from connector-write dispatch to server source observation; includes connector request latency.'
elif remote.get('committed_at'):
    proof['observed_latency_seconds']=None
    proof['latency_note']='Cross-host clock disagreement prevents a defensible wall-clock latency measurement.'
proof['duplicate_refresh']=svc.sync_repo()
proof['passes']=proof['changed'] and len(triggered)==1 and not proof['duplicate_refresh']['changed']
Path('docs/evidence/radar-live-proof.json').write_text(json.dumps(proof,indent=2))
print(json.dumps(proof,indent=2))
raise SystemExit(0 if proof['passes'] else 1)
