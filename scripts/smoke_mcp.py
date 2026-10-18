"""Exercise actual initialize/tools-list/tools-call over Streamable HTTP, with live GitHub reads."""
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
from relay.service import RelayService
from relay.store import make_store

async def main():
    tenant='mcp-live-smoke'
    store=make_store();svc=RelayService(store,tenant)
    svc.settings()
    url=os.environ['RELAY_MCP_URL']
    context=sign_context(tenant,url,os.environ['RELAY_CONTEXT_SECRET'])
    proof={'checked_at':now(),'transport':'Streamable HTTP','server':url,'calls':[],'cloud_agent':False}
    async with streamablehttp_client(url,headers={'X-Relay-Context':context}) as (read,write,_):
        async with ClientSession(read,write) as session:
            init=await session.initialize()
            proof['protocol_version']=init.protocolVersion
            tools=await session.list_tools()
            proof['tools']=[t.name for t in tools.tools]
            for name,args in [('list_course_sources',{}),('get_assignment_repo_status',{}),('read_assignment_repo_file',{'path':'coursework.md'}),('read_course_source',{'source_id':'security-pdf','page':1})]:
                result=await session.call_tool(name,args)
                assert not result.isError
                for content in result.content:
                    if content.type=='text':
                        assert 'error' not in json.loads(content.text), content.text
                proof['calls'].append({'tool':name,'is_error':result.isError,'content':[c.model_dump() for c in result.content]})
    Path('docs/evidence').mkdir(parents=True,exist_ok=True)
    Path('docs/evidence/mcp-smoke.json').write_text(json.dumps(proof,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps({k:v for k,v in proof.items() if k!='calls'},indent=2))
    print('Actual tools/call results saved, with modes and provenance. This is local MCP proof, not cloud-agent proof.')

if __name__=='__main__':
    asyncio.run(main())
