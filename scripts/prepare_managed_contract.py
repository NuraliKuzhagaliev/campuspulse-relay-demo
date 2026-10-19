"""Offline SDK/serialization/package rehearsal. Creates no cloud resource."""
import inspect,json,hashlib,os,shutil,sys
from pathlib import Path
from importlib.metadata import version
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from relay.domain import now

def main():
    import cloudpickle
    from relay.agent import RelayRuntime
    from vertexai import types
    from vertexai._genai.agent_engines import AgentEngines
    root=Path(__file__).resolve().parents[1];stage=root/'.local/managed-preparation/package'
    (stage/'relay').mkdir(parents=True,exist_ok=True)
    hashes={}
    for source in sorted((root/'relay').glob('*.py')):
        shutil.copyfile(source,stage/'relay'/source.name);hashes['relay/'+source.name]=hashlib.sha256(source.read_bytes()).hexdigest()
    shutil.copyfile(root/'requirements.cloud.txt',stage/'requirements.cloud.txt')
    runtime=RelayRuntime();serialized=cloudpickle.dumps(runtime)
    assert cloudpickle.loads(serialized).__dict__=={} and callable(cloudpickle.loads(serialized).query)
    for key in ('RELAY_GEMINI_API_KEY','RELAY_CONTEXT_SECRET','RELAY_MCP_SERVICE_SECRET','RELAY_OAUTH_CLIENT_SECRET'):
        if os.getenv(key):assert os.environ[key].encode() not in serialized
    config=types.AgentEngineConfig(display_name='CampusPulse RELAY',requirements=[s for s in (root/'requirements.cloud.txt').read_text().splitlines() if s and not s.startswith('#')],
        extra_packages=[str(stage/'relay')],staging_bucket='gs://pending-organizer-project-relay',service_account='relay-runtime@pending-organizer-project.iam.gserviceaccount.com',
        min_instances=0,max_instances=1,env_vars={'RELAY_MODE':'cloud','RELAY_CONTEXT_SECRET':types.SecretRef(secret='relay-context',version='latest')})
    proof=dict(checked_at=now(),sdk={key:version(key) for key in ('google-cloud-aiplatform','google-adk','google-genai','mcp','cloudpickle')},
        create_signature=str(inspect.signature(AgentEngines.create)),update_signature=str(inspect.signature(AgentEngines.update)),
        query_signature=str(inspect.signature(RelayRuntime.query)),configuration_schema_validated=True,serialization_roundtrip=True,serialized_bytes=len(serialized),
        credentials_clients_eventloops_serialized=False,package_python_files=len(hashes),package_hashes=hashes,requirements_sha256=hashlib.sha256((root/'requirements.cloud.txt').read_bytes()).hexdigest(),
        no_network_calls=True,resources_created=False,actual_project=None,actual_region=None,actual_resource=None,actual_model=None,T0=None,T_expiry=None,
        limitations=['SDK/schema/serialization checks are offline; model/region/IAM/quotas and actual remote import/query require the organizer project.',
          'Firestore domain transaction buffering is unit-simulated; actual managed shared-state/session and cloud-to-MCP acceptance remain pending.',
          'The public Render workspace must remain authoritative or undergo a verified transfer/cutover; never silently fork user progress into an unfinished cloud store.'])
    target=root/'docs/evidence/managed-preparation-0.5.0.json';target.write_text(json.dumps(proof,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in proof.items() if k not in ('package_hashes',)},indent=2))
if __name__=='__main__':main()
