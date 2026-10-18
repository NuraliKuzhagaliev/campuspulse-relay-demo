import argparse
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from relay.service import RelayService
from relay.store import make_store
from relay.domain import RelayError
p=argparse.ArgumentParser();p.add_argument('--workspace',required=True);p.add_argument('--anchor');args=p.parse_args()
store=make_store()
if store.list(args.workspace,'sources'):
    p.error('Workspace already contains sources. Use a fresh isolated demo workspace ID; existing work is preserved.')
service=RelayService(store,args.workspace);service.seed(args.anchor)
print(json.dumps({'workspace':args.workspace,'mode':'illustrative','sources':len(service.sources())}))
