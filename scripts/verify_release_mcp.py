"""Actual protected loopback MCP protocol, including long-tail reads; zero models."""
import os,sys,json,asyncio,secrets,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from relay.store import Store
from relay.service import RelayService
from relay.auth import sign_context
from relay.domain import now
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

async def main():
    url='http://127.0.0.1:8032/_relay/mcp/';os.environ['RELAY_MODE']='alternative_live';os.environ['RELAY_PUBLIC_AI_ENABLED']='true'
    store=Store('.local/final-0.5.1/server-data/relay.sqlite3');tenant='demo-'+secrets.token_hex(16);store.put('_server','workspaces',tenant,{'id':tenant})
    svc=RelayService(store,tenant);svc.create_empty()
    source=svc.import_source('long-field-notes.txt',('A course report introduction. '*1200+'\nAppendix: discuss lithic density and uncertainty.').encode())
    header={'Authorization':'Bearer '+Path('.local/private/mcp-service-secret').read_text().strip(),'X-Relay-Context':sign_context(tenant,url,os.environ['RELAY_CONTEXT_SECRET'])}
    proof=dict(checked_at=now(),transport='actual MCP Streamable HTTP',model_calls=0,cloud_calls=0,checks={})
    def value(result):
        assert not result.isError
        data=json.loads(next(c.text for c in result.content if c.type=='text'));assert 'error' not in data,data.get('error');return data
    async with streamablehttp_client(url,headers=header) as (read,write,_):
        async with ClientSession(read,write) as session:
            await session.initialize();catalog=await session.list_tools();tool=next(t for t in catalog.tools if t.name=='read_course_source');assert {'offset','limit','search'}<=set(tool.inputSchema['properties'])
            first=value(await session.call_tool('read_course_source',{'source_id':source['id'],'limit':12000}));assert first['next_offset']==12000 and first['truncated']
            assert first['quote_lines'] and all(line in first['text'] for line in first['quote_lines'])
            assert first['citation_refs'] and all(c['quote'] in source['pages'][0]['text'] for c in first['citation_refs'])
            tail=value(await session.call_tool('read_course_source',{'source_id':source['id'],'search':'lithic density','limit':200}));assert tail['offset']>20000 and 'lithic density' in tail['text']
            proof['checks']['bounded_continuation_search_tail']=True
            quote=source['pages'][0]['text'][-50:]
            proposal=value(await session.call_tool('propose_academic_extraction',{'source_id':source['id'],'candidates':[{'entity_id':'tail','field':'due','value':None,'page':1,'quote':quote,'original_expression':quote}]}))
            assert proposal['entities'][0]['fields'][0]['validation_status']=='unknown' and not proposal['applied'];proof['checks']['null_due_grouped_unapplied']=True
            assert store.get(tenant,'extraction_proposals',proposal['id'])['source_version']==source['version']
            batch=value(await session.call_tool('propose_academic_extraction',{'source_id':source['id'],'candidates':[
                {'entity_id':'tail','field':'title','value':'Lithic density discussion','page':1,'quote':quote,'original_expression':quote},
                {'entity_id':'tail','field':'rubric','value':['Invented criterion'],'page':1,'quote':'This quotation does not exist','original_expression':'This quotation does not exist'}]}))
            assert batch['status']=='partial' and batch['validation_issues'][0]['field']=='rubric'
            assert {f['field'] for f in batch['fields']}=={'due','title'} and not batch['applied']
            proof['checks']['actual_protocol_partial_batch_preserves_valid_unapplied_fields']=True
            reference=next(c for c in tail['citation_refs'] if 'lithic density' in c['quote'])
            cited=value(await session.call_tool('propose_academic_extraction',{'source_id':source['id'],'candidates':[{'entity_id':'tail','field':'rubric','value':['Discuss lithic density and uncertainty'],'page':1,'citation_id':reference['citation_id']}]}))
            field=next(f for f in cited['fields'] if f['field']=='rubric');assert field['quote']==reference['quote'] and field['original_expression']==reference['quote'] and not cited['applied']
            proof['checks']['actual_reference_protocol_keeps_exact_unconfirmed_multiline_quote']=True
            rejected=await session.call_tool('propose_academic_extraction',{'source_id':source['id'],'candidates':[{'field':'PRIVATE_INPUT_MUST_NOT_APPEAR','value':'PRIVATE_INPUT_MUST_NOT_APPEAR','page':1}]})
            raw=json.loads(next(c.text for c in rejected.content if c.type=='text'))
            assert raw['error']['code']=='TOOL_INPUT_INVALID' and 'PRIVATE_INPUT_MUST_NOT_APPEAR' not in json.dumps(raw)
            proof['checks']['actual_protocol_redacted_typed_schema_failure']=True
            null_cited=value(await session.call_tool('propose_academic_extraction',{'source_id':source['id'],'candidates':[{'entity_id':'tail','field':'title','value':'Lithic density discussion','page':1,'citation_id':reference['citation_id'],'quote':None,'original_expression':None}]}))
            assert null_cited['fields'] and not null_cited['applied'];proof['checks']['actual_protocol_nullable_reference_mode']=True
    proof['passed']=True;Path('docs/evidence/final-0.5.1-mcp.json').write_text(json.dumps(proof,indent=2),encoding='utf-8');print(json.dumps(proof,indent=2))
if __name__=='__main__':asyncio.run(main())
