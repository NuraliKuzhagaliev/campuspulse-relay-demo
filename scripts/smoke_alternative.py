"""Small owner-authorized free Gemini -> authenticated MCP -> public GitHub smoke.

Run after scripts/run-alternative.ps1. Uses synthetic/public material only.
No cookie, invitation, key, context signature or personal Calendar data is saved.
"""
import asyncio
import hashlib
import json
import os
import secrets
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from relay.domain import now
from relay.store import Store
from relay.service import RelayService
from relay.conversations import conversation
from relay.auth import sign_context


def configure(port=8016):
    root=Path(__file__).resolve().parents[1]
    os.environ.update(RELAY_MODE='alternative_live',RELAY_INFERENCE_PROVIDER='gemini_developer',GOOGLE_GENAI_USE_VERTEXAI='false',
                      RELAY_DEPLOYMENT_MODE='alternative_hosted',RELAY_DATA_DIR=str(root/'.local/final-integration/alternative-data'),
                      RELAY_MCP_URL=f'http://127.0.0.1:{port}/_relay/mcp/',
                      RELAY_MCP_SERVICE_SECRET=(root/'.local/private/mcp-service-secret').read_text(encoding='utf-8-sig').strip(),
                      RELAY_GITHUB_REPO='NuraliKuzhagaliev/campuspulse-relay-demo')


async def discovery(token):
    import httpx
    from mcp import ClientSession
    from mcp.client.streamable_http import streamable_http_client
    async with httpx.AsyncClient(headers={'Authorization':'Bearer '+os.environ['RELAY_MCP_SERVICE_SECRET'],'X-Relay-Context':token},timeout=25) as http:
        async with streamable_http_client(os.environ['RELAY_MCP_URL'],http_client=http) as (read,write,_):
            async with ClientSession(read,write) as client:
                await client.initialize()
                tools=await client.list_tools()
                return [t.name for t in tools.tools]


def main():
    configure()
    from relay.agent import RelayRuntime
    from relay.providers import selected
    from relay.alternative_live import configuration
    configuration()
    s=Store();tenant='judge-'+secrets.token_hex(24);svc=RelayService(s,tenant);svc.seed()
    settings=svc.settings();settings.update(mode='judge_ai',ai_access=True,calendar_live=False,judge_expires=__import__('time').time()+7200)
    s.put(tenant,'meta','settings',settings)
    conv=conversation(s,tenant);run=secrets.token_hex(16)
    token=sign_context(tenant,os.environ['RELAY_MCP_URL'],os.environ['RELAY_CONTEXT_SECRET'])
    proof=dict(checked_at=now(),route='alternative_hosted_local_protocol_smoke',provider='gemini_developer',
               model=selected()['model'],managed_agent_engine=False,source_revision='working_tree_not_yet_released',
               public_web_acceptance=False,calendar_actions='not_called',personal_spending_authorized_usd=0,
               account_free_tier_owner_confirmed=True,synthetic_public_material_only=True)
    try:
        proof['mcp_tools']=asyncio.run(discovery(token))
        answer=RelayRuntime().query(user_id=tenant,message='Use the MCP tools get_assignment_repo_status and get_progress_summary. Report the actual repository name and immutable commit and whether student work has been logged. Keep live repository observations separate from illustrative coursework. Do not change any data or call Calendar. Answer briefly in English.',context_token=token,language='en',run_id=run,conversation_id=conv['id'])
        proof['result']=answer
        proof['events']=s.events(tenant)
        proof['passed']=answer['status']=='complete' and any(e.get('tool')=='get_assignment_repo_status' and e['type']=='tool_finished' for e in proof['events'])
    except Exception as e:
        proof.update(passed=False,error_type=type(e).__name__,error_code=str(getattr(e,'code','unavailable')))
        proof['events']=s.events(tenant)
    path=Path('docs/evidence/final-alternative-smoke.json')
    path.write_text(json.dumps(proof,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps({k:v for k,v in proof.items() if k!='events'},indent=2,ensure_ascii=False))
    return 0 if proof['passed'] else 1


if __name__=='__main__':raise SystemExit(main())
