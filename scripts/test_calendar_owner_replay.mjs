/** Isolated tests of the owner helper; no browser, network or Calendar writes. */
import fs from 'node:fs/promises';
import vm from 'node:vm';
import assert from 'node:assert/strict';
const code=await fs.readFile(new URL('./calendar-owner-replay.js',import.meta.url),'utf8');
const id='a'.repeat(32),secret='test-only-approval-never-printed';
const original={id,mode:'live',status:'verified',calendar_id:'synthetic-owned-calendar',digest:secret,outcomes:[{operation:'create',event_id:'synthetic-event'}]};
async function execute({origin='https://campuspulse-relay-demo.onrender.com',title='RELAY Calendar acceptance check',receipts=[original],accept=true}={}) {
  const calls=[];
  const fetch=async (url,options={})=>{
    calls.push({url,options});
    const value=url==='/api/session'?{csrf:'test-only-csrf'}:url==='/api/state'?{tasks:[{title}],receipts,settings:{calendar_id:original.calendar_id,calendar_live:true}}:url.endsWith('/approve')?original:{results:[{matches:true}]};
    return {ok:true,status:200,json:async()=>value};
  };
  const result=await vm.runInNewContext(code,{location:{origin},fetch,confirm:()=>accept});
  return {result,calls};
}
await assert.rejects(execute({origin:'https://other.example'}),/ordinary RELAY/);
await assert.rejects(execute({title:'Personal coursework'}),/synthetic Calendar/);
await assert.rejects(execute({receipts:[]}),/previously verified/);
const cancelled=await execute({accept:false});
assert.equal(cancelled.result.request_sent,false);assert.equal(cancelled.calls.length,2);
const passed=await execute();
assert.deepEqual(passed.calls.map(x=>x.url),['/api/session','/api/state',`/api/previews/${id}/approve`,`/api/receipts/${id}/verify`]);
assert.equal(JSON.parse(passed.calls[2].options.body).digest,secret);
assert.equal(passed.calls[2].options.headers['X-Relay-CSRF'],'test-only-csrf');
assert.equal(passed.result.same_receipt,true);assert.equal(passed.result.same_event,true);
assert.equal(passed.result.fresh_read_back_matches,true);
assert(!JSON.stringify(passed.result).includes(secret));
console.log(JSON.stringify({passed:true,checks:5,scope:'isolated helper guards and same-approved-request replay; mocked fetch; zero real Calendar operations'}));
