"""Actual signed local MCP protocol and public PR read; no cloud/model claim."""
import asyncio
import json
import os
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from relay.auth import sign_context
from relay.domain import now
from relay.store import make_store
from relay.service import RelayService
from relay.handoff import link
from relay.progress import revision


async def main():
    store=make_store();service=RelayService(store,'four-mcp-verification');service.settings()
    gate=link(service,dict(task_id=service.tasks()[0]['id'],repo='pallets/flask',number=6168,request_id='e'*24,expected_revision=revision(service)))['gate']
    url=os.environ['RELAY_MCP_URL'];proof=dict(checked_at=now(),transport='actual Streamable HTTP',server=url,managed_agent=False,model_calls=0,github_writes=0)
    async with streamablehttp_client(url,headers={'X-Relay-Context':sign_context(service.tenant,url,os.environ['RELAY_CONTEXT_SECRET'])}) as (read,write,_):
        async with ClientSession(read,write) as session:
            await session.initialize();catalog=await session.list_tools();proof['tools']=[t.name for t in catalog.tools]
            tool=next(t for t in catalog.tools if t.name=='observe_handoff_gate')
            assert set(tool.inputSchema['properties'])=={'gate_id'}
            result=await session.call_tool('observe_handoff_gate',{'gate_id':gate['id']})
            value=json.loads(next(c.text for c in result.content if c.type=='text'))
            assert 'error' not in value and value['status']=='condition_observed',value
            proof['observation']=value['observation'];proof['schema_excludes_tenant_repository_and_authority']=True
    async with streamablehttp_client(url,headers={'X-Relay-Context':sign_context('four-mcp-other',url,os.environ['RELAY_CONTEXT_SECRET'])}) as (read,write,_):
        async with ClientSession(read,write) as session:
            await session.initialize();result=await session.call_tool('observe_handoff_gate',{'gate_id':gate['id']})
            value=json.loads(next(c.text for c in result.content if c.type=='text'))
            assert value['error']['code']=='ACCESS_DENIED';proof['foreign_tenant_denied']=True
    proof['passed']=True
    Path('docs/evidence/four-mcp.json').write_text(json.dumps(proof,indent=2),encoding='utf-8')
    print(json.dumps(proof,indent=2))


if __name__=='__main__':asyncio.run(main())
