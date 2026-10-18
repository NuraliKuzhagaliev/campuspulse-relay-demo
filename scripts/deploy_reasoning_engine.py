"""Create the required managed resource only after explicit budget approval and access checks."""
import argparse
import json
import os
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--approved-budget-usd',type=float,required=True)
    args=parser.parse_args()
    if args.approved_budget_usd<=0:
        parser.error('A positive user-approved spending limit is required. This flag is a record, not a cloud-enforced spend cap.')
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
        'env_vars':{key:os.environ[key] for key in ['GOOGLE_CLOUD_PROJECT','GOOGLE_CLOUD_LOCATION','GEMINI_MODEL','RELAY_MCP_URL','RELAY_CONTEXT_SECRET']}|{'RELAY_MODE':'cloud'},
        'min_instances':0,'max_instances':2,
    })
    from relay.domain import now
    proof={'name':remote.api_resource.name,'deployed_at':now(),'approved_budget_usd':args.approved_budget_usd,'remote_query_verified':False}
    Path('docs/evidence').mkdir(parents=True,exist_ok=True)
    Path('docs/evidence/deployment.json').write_text(json.dumps(proof,indent=2))
    print(json.dumps(proof,indent=2))

if __name__=='__main__':
    main()
