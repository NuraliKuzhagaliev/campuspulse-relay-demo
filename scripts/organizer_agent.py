"""Bounded organizer-only SDK deployment/inspection/retirement.

Default `prepare` is offline. Existing covered SA, private staging bucket and
Secret Manager version must be verified in the actual organizer project first.
This never configures personal billing, copies Google refresh tokens, migrates
domain state or activates the public route. All local state stays on D:.
"""
import argparse,json,os,re,sys,subprocess,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from relay.domain import now,RelayError
ROOT=Path(__file__).resolve().parents[1]

def on_d(path):
    value=Path(path).resolve()
    if value.drive.lower()!='d:':raise ValueError('Project paths must stay on D:.')
    return value

def owned_resource(plan,name):
    projects={plan['project']}
    if re.fullmatch(r'\d+',str(plan.get('project_number',''))):projects.add(str(plan['project_number']))
    return isinstance(name,str) and any(re.fullmatch(r'projects/'+re.escape(project)+r'/locations/'+re.escape(plan['region'])+r'/reasoningEngines/[A-Za-z0-9_-]+',name) for project in projects)

def configuration(plan,package):
    """Typed SDK config with secret references, never secret values."""
    from vertexai import types
    project=plan['project'];origin=plan['public_origin'].rstrip('/')
    if not re.fullmatch(r'[a-z][a-z0-9-]{4,61}[a-z0-9]',project):raise ValueError('Use the actual assigned project ID.')
    if not re.fullmatch(r'[a-z]+-[a-z0-9]+\d',plan['region']):raise ValueError('Use the actually enabled region.')
    if origin!='https://campuspulse-relay-demo.onrender.com':raise ValueError('This release uses the existing authoritative HTTPS backend.')
    if not re.fullmatch(r'[a-z][a-z0-9-]{4,26}',plan['owned_prefix']):raise ValueError('Choose a unique owned resource prefix.')
    if not re.fullmatch(r'[a-z][a-z0-9-]{4,28}@'+re.escape(project)+r'\.iam\.gserviceaccount\.com',plan['runtime_service_account']):raise ValueError('Use the actual dedicated runtime SA in the organizer project.')
    if not re.fullmatch(r'gs://[a-z0-9][a-z0-9.-]{2,61}',plan['staging_bucket']):raise ValueError('Use the verified private staging bucket.')
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,200}',plan['context_secret_id']) or not re.fullmatch(r'\d+',str(plan['context_secret_version'])):raise ValueError('Pin an actual context secret ID/version.')
    if not isinstance(plan['model'],str) or not plan['model'] or not re.fullmatch('[a-f0-9]{40}',plan['source_commit']):raise ValueError('Pin the actual Vertex model and source commit.')
    return types.AgentEngineConfig(display_name='CampusPulse RELAY '+plan['owned_prefix'],requirements=[s for s in (ROOT/'requirements.cloud.txt').read_text().splitlines() if s and not s.startswith('#')],extra_packages=[str(package/'relay')],staging_bucket=plan['staging_bucket'],service_account=plan['runtime_service_account'],min_instances=0,max_instances=1,
      env_vars={'RELAY_MODE':'cloud','RELAY_INFERENCE_PROVIDER':'vertex','RELAY_DEPLOYMENT_MODE':'managed_gcp','GOOGLE_GENAI_USE_VERTEXAI':'true',
        'GOOGLE_CLOUD_PROJECT':project,'GOOGLE_CLOUD_LOCATION':plan['region'],'GEMINI_MODEL':plan['model'],'RELAY_AGENT_REVISION':plan['source_commit'],
        'RELAY_MCP_URL':origin+'/managed/mcp/','RELAY_MCP_AUDIENCE':origin,'RELAY_STATE_URL':origin+'/internal/runtime-state','RELAY_STATE_AUDIENCE':origin,
        'RELAY_PUBLIC_AI_ENABLED':'true','RELAY_CONTEXT_SECRET':types.SecretRef(secret=plan['context_secret_id'],version=str(plan['context_secret_version']))})

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('operation',choices=['prepare','deploy','inspect','retire']);parser.add_argument('--plan',required=True);parser.add_argument('--execute',action='store_true');args=parser.parse_args()
    if ROOT.drive.lower()!='d:':parser.error('Run the project on D:.')
    plan_path=on_d(args.plan);plan=json.loads(plan_path.read_text(encoding='utf-8-sig'));folder=on_d(ROOT/'.local/organizer'/plan['owned_prefix']);folder.mkdir(parents=True,exist_ok=True)
    ledger_path=folder/'agent-ledger.json';package=ROOT/'.local/managed-preparation/package';config=configuration(plan,package)
    if args.operation=='prepare':
        config.model_dump(mode='json');print(json.dumps(dict(configuration_valid=True,resources_created=False,live_query_verified=False,package=str(package),ledger=str(ledger_path))));return
    import vertexai
    if args.operation in ('deploy','retire') and not args.execute:parser.error('Mutation requires --execute after actual organizer coverage and ownership verification.')
    if plan.get('personal_spending_authorized_usd')!=0:parser.error('Personal spending is prohibited.')
    if args.operation=='deploy':
        from relay.funding import validate_funding
        record_path=on_d(plan['funding_record']);record=json.loads(record_path.read_text(encoding='utf-8-sig'));validate_funding(record,plan['project'],float(plan['authorized_credit_usage_usd']),int(plan['planned_hours']))
        if not plan.get('covered_prerequisites_verified') or not plan.get('cleanup_reserve_verified') or not isinstance(plan.get('estimated_inclusive_credit_usage_usd'),(int,float)):parser.error('Verify the actual inclusive covered estimate and cleanup reserve before deploying.')
        head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
        if head!=plan['source_commit'] or subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip():parser.error('Deploy the exact clean committed source.')
        # Offline package hashes must correspond to the current source.
        proof=json.loads((ROOT/'docs/evidence/managed-preparation-0.5.0.json').read_text())
        for name,expected in proof['package_hashes'].items():
            if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=expected or (package/name).read_bytes()!=(ROOT/name).read_bytes():parser.error('Refresh the offline package rehearsal first.')
        if ledger_path.exists():parser.error('A deployment attempt is already recorded. Inspect/reconcile it; never blindly create a duplicate after a timeout.')
        ledger=dict(project=plan['project'],region=plan['region'],owned_prefix=plan['owned_prefix'],source_commit=head,started_at=now(),status='creation_requested',resource=None,remote_query_verified=False,funding_record_sha256=hashlib.sha256(record_path.read_bytes()).hexdigest())
        ledger_path.write_text(json.dumps(ledger,indent=2));client=vertexai.Client(project=plan['project'],location=plan['region'])
        from relay.agent import RelayRuntime
        remote=client.agent_engines.create(agent=RelayRuntime(),config=config)
        ledger.update(resource=remote.api_resource.name,status='resource_returned_not_live_acceptance',returned_at=now());ledger_path.write_text(json.dumps(ledger,indent=2));print(json.dumps(ledger));return
    ledger=json.loads(ledger_path.read_text());name=ledger.get('resource')
    if not owned_resource(plan,name):parser.error('Reconcile the exact owned resource from the recorded creation attempt first, including its actual project number.')
    client=vertexai.Client(project=plan['project'],location=plan['region']);remote=client.agent_engines.get(name=name)
    if remote.api_resource.name!=name:parser.error('Resource discovery differs from the ownership ledger.')
    if args.operation=='inspect':
        schemas=remote.operation_schemas();result=dict(resource=name,observed_at=now(),operations=schemas,remote_query_verified=False);(folder/'discovery.json').write_text(json.dumps(result,indent=2,default=str));print(json.dumps(result,default=str));return
    # Cleanup is allowed after expiry too, but only for this exact ledger entry.
    if ledger.get('status')=='delete_requested':parser.error('Deletion is already recorded. Inspect its operation and exact resource absence before retrying.')
    ledger.update(status='delete_requested',retirement_requested_at=now());ledger_path.write_text(json.dumps(ledger,indent=2))
    operation=client.agent_engines.delete(name=name,force=True)
    ledger.update(delete_operation=operation.name,delete_request_returned_at=now());ledger_path.write_text(json.dumps(ledger,indent=2));print(json.dumps(dict(resource=name,delete_requested=True,operation=operation.name,absence_verified=False,unrelated_resources_touched=False)))

if __name__=='__main__':main()
