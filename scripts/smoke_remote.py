"""Bounded real local Gemini and remote Agent Engine smoke; writes redacted evidence only."""
import argparse
import json
import os
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

def main():
    p=argparse.ArgumentParser();p.add_argument('--workspace',required=True);p.add_argument('--approve-model-call',action='store_true');args=p.parse_args()
    if not args.approve_model_call:
        p.error('This sends two bounded paid model requests; --approve-model-call requires existing budget authorization.')
    from google import genai
    from google.genai import types
    import vertexai
    from relay.auth import sign_context
    from relay.domain import now
    client=genai.Client(vertexai=True,project=os.environ['GOOGLE_CLOUD_PROJECT'],location=os.environ['GOOGLE_CLOUD_LOCATION'])
    local=client.models.generate_content(model=os.environ['GEMINI_MODEL'],contents='Reply with READY only.',config=types.GenerateContentConfig(max_output_tokens=20,temperature=0))
    remote=vertexai.Client(project=os.environ['GOOGLE_CLOUD_PROJECT'],location=os.environ['GOOGLE_CLOUD_LOCATION']).agent_engines.get(name=os.environ['RELAY_AGENT_RESOURCE'])
    context=sign_context(args.workspace,os.environ['RELAY_MCP_URL'],os.environ['RELAY_CONTEXT_SECRET'])
    response=remote.query(user_id=args.workspace,message='List the approved course sources, then read repository status. Report the real modes and commit.',context_token=context,language='en',run_id='release-smoke')
    result={'checked_at':now(),'resource':os.environ['RELAY_AGENT_RESOURCE'],'model':os.environ['GEMINI_MODEL'],'local_model_response':local.text,'remote_response':response}
    Path('docs/evidence/remote-smoke.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))

if __name__=='__main__':
    main()
