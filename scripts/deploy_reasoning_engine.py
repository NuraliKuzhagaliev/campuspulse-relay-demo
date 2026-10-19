"""Create the required managed resource only after explicit budget approval and access checks."""
import argparse
import json
import os
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--approved-budget-usd',type=float,default=0)
    parser.add_argument('--pilot-hours',type=int,default=10)
    args=parser.parse_args()
    if args.approved_budget_usd<0:
        parser.error('Only an actual organizer credit envelope is permitted. No personal spending is authorized.')
    from relay.funding import validate_funding
    from relay.domain import RelayError
    try:
        record=json.loads(Path('.local/funding-verification.json').read_text(encoding='utf-8-sig'))
        validate_funding(record,os.getenv('GOOGLE_CLOUD_PROJECT'),args.approved_budget_usd,args.pilot_hours)
    except (OSError,ValueError,RelayError):
        parser.error('An actual activated organizer project/window/coverage record is required. Personal trials and spending are prohibited.')
    for name in ['GOOGLE_CLOUD_PROJECT','GOOGLE_CLOUD_LOCATION','GEMINI_MODEL','RELAY_STAGING_BUCKET','RELAY_MCP_URL','RELAY_CONTEXT_SECRET','RELAY_RUNTIME_SERVICE_ACCOUNT']:
        if not os.getenv(name):
            parser.error(f'Missing {name}')
    import vertexai
    from relay.agent import RelayRuntime
    client=vertexai.Client(project=os.environ['GOOGLE_CLOUD_PROJECT'],location=os.environ['GOOGLE_CLOUD_LOCATION'])
    # The current agent_engines.create call creates a reasoningEngines resource, satisfying the brief's legacy deployment name.
    remote=client.agent_engines.create(agent=RelayRuntime(),config={
        'display_name':'CampusPulse RELAY',
        'requirements':[line.strip() for line in Path('requirements.cloud.txt').read_text().splitlines() if line.strip() and not line.startswith('#')],
        'extra_packages':['relay'],
        'staging_bucket':os.environ['RELAY_STAGING_BUCKET'],
        'service_account':os.environ['RELAY_RUNTIME_SERVICE_ACCOUNT'],
        'env_vars':{key:os.environ[key] for key in ['GOOGLE_CLOUD_PROJECT','GOOGLE_CLOUD_LOCATION','GEMINI_MODEL','RELAY_MCP_URL']}|{'RELAY_MODE':'cloud','RELAY_CONTEXT_SECRET':vertexai.types.SecretRef(secret='relay-context',version='latest')},
        'min_instances':0,'max_instances':1,
    })
    from relay.domain import now
    proof={'name':remote.api_resource.name,'deployed_at':now(),'approved_budget_usd':args.approved_budget_usd,'remote_query_verified':False}
    Path('docs/evidence').mkdir(parents=True,exist_ok=True)
    Path('docs/evidence/deployment.json').write_text(json.dumps(proof,indent=2))
    print(json.dumps(proof,indent=2))

if __name__=='__main__':
    main()
