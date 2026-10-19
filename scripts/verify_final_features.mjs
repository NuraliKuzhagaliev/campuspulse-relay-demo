/** Bounded real-agent feature batch. API setup is labeled separately from browser actions. */
import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import {chromium,expect} from '@playwright/test';
const [url,invitationFile,index='0']=process.argv.slice(2),local=url==='https://localhost:8017';
assert(url?.startsWith('https://')&&invitationFile);
const token=JSON.parse(await fs.readFile(invitationFile,'utf8')).invitations[Number(index)].token;
const id=Date.now().toString(36),out=`docs/evidence/final-features-${local?'local':'hosted'}-${id}.json`;
const proof={checked_at:new Date().toISOString(),url,development_certificate_only:local,provider:'gemini_developer',managed_agent_engine:false,calendar:'illustrative',checks:{},runs:[],setup:'Own isolated workspace API setup for explicit windows, progress and a public PR gate. Model turns and plan/what-if/approval are browser actions.'};
async function save(){await fs.writeFile(out,JSON.stringify(proof,null,2));}
async function step(name,fn){try{proof.checks[name]=await fn()??true;await save();}catch(error){proof.checks[name]={failed:true,error:String(error).replaceAll(token,'[invitation redacted]')};await save();throw new Error(name+' failed');}}
const browser=await chromium.launch({headless:true});
try{
 const context=await browser.newContext({baseURL:url,ignoreHTTPSErrors:local,viewport:{width:1440,height:900}}),page=await context.newPage();
 await page.goto('/');await page.getByText('Use a private AI invitation',{exact:true}).click();await page.getByLabel('Owner-issued one-use judge invitation').fill(token);
 await Promise.all([page.waitForNavigation({waitUntil:'load'}),page.getByRole('button',{name:'Open isolated demo',exact:true}).click()]);
 await page.locator('.live-access input[type=checkbox]').check();
 const privateFolder=path.join(process.cwd(),'.local/final-features',id);await fs.mkdir(privateFolder,{recursive:true});await context.storageState({path:path.join(privateFolder,'private-state.json')});
 const session=await (await page.request.get('/api/session')).json();
 async function api(route,data){const r=data===undefined?await page.request.get('/api'+route):await page.request.post('/api'+route,{headers:{'X-Relay-CSRF':session.csrf},data});const value=await r.json();assert.equal(r.status(),200,'Setup HTTP '+r.status()+' '+value.error?.code);return value;}
 async function ask(message){const pending=page.waitForResponse(r=>new URL(r.url()).pathname==='/api/chat'&&r.request().method()==='POST',{timeout:110000});await page.locator('.assistant input[maxlength="6000"]').fill(message);await page.locator('.assistant > form button').click();const r=await pending,value=await r.json();proof.runs.push(value);await save();assert.equal(r.status(),200);assert.equal(value.status,'complete');assert(value.text?.trim());return value;}
 let state=await api('/state'),conflict=state.conflicts.find(c=>c.status==='unresolved');
 const windows=structuredClone(state.settings.windows);windows[0]={start:state.settings.anchor+'T20:00:00+05:00',end:state.settings.anchor+'T22:00:00+05:00'};await api('/preferences',{windows});
 await step('real_conflict_and_bounded_clarification',async()=>{
   const r=await ask('Inspect the conflicting Network Security lab deadlines in my current workspace. Compare the cited alternatives and recommend which clarification matters. Do not choose the correct deadline for me or mutate a resolution.');
   assert(r.tool_observations.some(t=>t.tool==='recommend_clarification'&&t.status==='observed'));assert((await api('/state')).conflicts.some(c=>c.status==='unresolved'));
 });
 // The explicit chosen citation resolves only this synthetic workspace's fixture conflict.
 await api('/conflicts/'+conflict.id+'/resolve',{fact_id:conflict.facts.toSorted((a,b)=>a.value.localeCompare(b.value))[0].id});await page.reload();await page.locator('.live-access input[type=checkbox]').check();
 await step('real_agent_saves_server_validated_feasible_plan',async()=>{
   const r=await ask('Please build and save my recovery plan using the current confirmed workspace facts and availability. Use the server validator. State whether it is feasible, and label this workspace Calendar as illustrative.');
   assert(r.tool_observations.some(t=>t.tool==='save_validated_plan'&&t.status==='observed'));const s=await api('/state');assert(s.plan.feasible);proof.baseline_plan=s.plan;
 });
 await step('browser_infeasible_whatif_and_illustrative_receipt',async()=>{
   await page.getByRole('button',{name:'Recovery',exact:true}).click();
   await page.getByRole('button',{name:'Lose Wednesday',exact:false}).click();
   await expect(page.getByText('What-if · baseline unchanged',{exact:true})).toBeVisible();assert.equal((await api('/state')).plan.id,proof.baseline_plan.id);
   // Return to baseline before an exact local-adapter approval.
   await page.getByRole('button',{name:'Return to baseline',exact:true}).click();
   await page.getByRole('button',{name:'Review calendar actions',exact:true}).click();
   await page.getByRole('button',{name:'Approve illustrative local actions',exact:true}).click();
   await expect.poll(async()=>(await api('/state')).receipts.length).toBeGreaterThan(0);
   const receipt=(await api('/state')).receipts[0];assert.equal(receipt.mode,'illustrative');assert.equal(receipt.status,'verified');proof.receipt=receipt;
 });
 state=await api('/state');const task=state.tasks.find(t=>t.title==='Web project');
 async function command(route,data){const revision=(await api('/additions')).revision;return api(route,{...data,request_id:crypto.randomBytes(16).toString('hex'),expected_revision:revision});}
 await command('/tasks/'+task.id+'/progress',{action:'log',duration_minutes:45});await command('/tasks/'+task.id+'/progress',{action:'remaining',remaining_minutes:95});
 await step('real_progress_followup_keeps_explicit_remaining',async()=>{
   const r=await ask('For Web project, I logged 45 minutes and explicitly reported 95 minutes remaining. Inspect the progress records. What does that mean for future allocation and completion? Refer to our current plan, without subtracting logged time again.');
   assert(r.tool_observations.some(t=>t.tool==='get_progress_summary'&&t.status==='observed'));assert(r.text.includes('95'));assert(r.conversation_id===proof.runs[0].conversation_id);
 });
 const gate=await command('/gates',{task_id:task.id,repo:'pallets/flask',number:6168});
 await step('real_github_and_handoff_mcp_observations',async()=>{
   const r=await ask(`Read the current configured coursework repository status, then observe my linked handoff gate ${gate.gate.id}. Report actual repository revision and public PR state with provenance. Is this managed Agent Engine or the alternative host? Do not write to GitHub or Calendar.`);
   assert(r.tool_observations.some(t=>t.tool==='get_assignment_repo_status'&&t.status==='observed'));assert(r.tool_observations.some(t=>t.tool==='observe_handoff_gate'&&t.status==='observed'));assert.equal(r.deployment_mode,'alternative_hosted');
   const gates=(await api('/additions')).gates;assert.equal(gates.find(g=>g.id===gate.gate.id).status,'condition_observed');proof.handoff=gates.find(g=>g.id===gate.gate.id).observation;
 });
 proof.passed=true;await save();console.log(JSON.stringify({passed:true,evidence:out,runs:proof.runs.length}));
}catch(error){proof.passed=false;proof.error=String(error).replaceAll(token,'[invitation redacted]');await save();console.error(JSON.stringify({passed:false,evidence:out}));process.exitCode=1;}
finally{await browser.close();}
