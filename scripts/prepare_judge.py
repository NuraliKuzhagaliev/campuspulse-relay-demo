"""Owner-only preparation. Reads one explicitly supplied Calendar; provisions no cloud resources."""
import argparse
import json
import os
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from relay.connectors import GoogleCalendar
from relay.domain import RelayError
from relay.judge import register
from relay.store import make_store

p=argparse.ArgumentParser()
p.add_argument('--calendar-id',required=True)
p.add_argument('--hours',type=int,default=4)
p.add_argument('--confirm-exclusive-owned-calendar',action='store_true')
args=p.parse_args()
if not args.confirm_exclusive_owned_calendar or not os.getenv('RELAY_GITHUB_REPO'):
    p.error('Explicit owner confirmation and RELAY_GITHUB_REPO are required. No calendar is created automatically.')
if os.getenv('RELAY_MODE')!='cloud':
    p.error('Use the configured cloud data store after credits, deployment and Calendar access are verified.')
calendar=GoogleCalendar(args.calendar_id)
if any(event.get('status')!='cancelled' for event in calendar.sync()['events']):
    p.error('Calendar is not empty. Use a separate empty calendar reserved for one visitor. Existing data is preserved.')
store=make_store()
token=register(store,args.calendar_id,args.hours)
folder=Path(os.environ['RELAY_DATA_DIR']).parent/'judge-private'
folder.mkdir(parents=True,exist_ok=True)
target=folder/('invitation-'+token[:8]+'.json')
target.write_text(json.dumps({'invitation':token,'gateway':os.environ['RELAY_GATEWAY_URL'],
                            'calendar_id':args.calendar_id,'hours':args.hours},indent=2),encoding='utf-8')
print('One-use invitation saved locally to '+str(target)+'. Do not commit it, record it, or paste it into chat. Share privately with the intended judge only.')
