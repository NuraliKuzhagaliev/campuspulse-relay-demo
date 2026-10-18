import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from relay.service import RelayService
from relay.store import make_store
from relay.domain import now

store=make_store();svc=RelayService(store,'radar-live-demo-v3')
for previous in ('radar-live-demo-v2',):
    try:
        old=RelayService(store,previous);settings=old.settings();settings['watch_enabled']=False;store.put(previous,'meta','settings',settings)
    except Exception:
        pass
svc.settings();initial=svc.sync_repo()
for conflict in svc.current_conflicts():
    svc.resolve(conflict['id'],min(conflict['facts'],key=lambda f:f['value'])['id'])
plan=svc.plan()
settings=svc.settings();settings['watch_enabled']=True
store.put(svc.tenant,'meta','settings',settings)
store.put('_server','workspaces',svc.tenant,{'id':svc.tenant})
proof=dict(workspace=svc.tenant,prepared_at=now(),baseline_commit=initial['commit'],baseline_plan=plan['id'],trigger='server-side 60s polling',cloud_hosted=False,gemini_connected=False)
Path('docs/evidence/radar-prepared.json').write_text(json.dumps(proof,indent=2))
print(json.dumps(proof,indent=2))
