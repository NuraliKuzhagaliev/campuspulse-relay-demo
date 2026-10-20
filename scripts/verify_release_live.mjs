/** Full public UI acceptance. Real Gemini/MCP; model transcripts remain private on D:. */
import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import {chromium,expect as baseExpect} from '@playwright/test';
const expect=baseExpect.configure({timeout:30000});
const base='https://campuspulse-relay-demo.onrender.com';
const resumeFolder=process.argv[2];const resumed=resumeFolder?JSON.parse(await fs.readFile(path.join(resumeFolder,'private-evidence.json'),'utf8')):null;
const id=Date.now().toString(36),folder=path.resolve('.local/audit-live',id);
await fs.mkdir(folder,{recursive:true});
const frozen=JSON.parse(await fs.readFile('.local/audit-holdouts/frozen.json','utf8'));
const cases=frozen.files.map(f=>({...f,path:path.resolve('.local/audit-holdouts',f.file)}));
cases.push({file:'11-continued-brief.pdf',path:path.resolve('public/samples/11-continued-brief.pdf'),expected:[{key:'polar-16',minutes:75,due:'2026-10-23T18:00:00+05:00'}]},
 {file:'12-table-brief.pdf',path:path.resolve('public/samples/12-table-brief.pdf'),expected:[{key:'soil-31',minutes:45,due:'2026-10-23T18:00:00+05:00'},{key:'mineral-32',minutes:75,due:'2026-10-23T20:00:00+05:00'}]});
if(process.env.RELAY_AUDIT_CASES){const chosen=process.env.RELAY_AUDIT_CASES.split(',');for(let i=cases.length-1;i>=0;i--)if(!chosen.includes(cases[i].file))cases.splice(i,1);assert(cases.length>=2,'Isolation acceptance needs at least two independently uploaded documents');}
const proof={at:new Date().toISOString(),url:base,version:'0.5.1',provider_substitution:false,google_login:false,invitations:false,personal_spending:0,checks:{},cases:[],runs:[]};
if(resumed)proof.resumes_owned_sessions_from={evidence:path.basename(resumeFolder),original_at:resumed.at,original_status:resumed.runs[0]?.status,original_fresh_sessions:resumed.checks.two_clean_automatic_workspaces};
const hash=v=>crypto.createHash('sha256').update(v).digest('hex');
const browser=await chromium.launch({headless:true});
const visitors=[];
async function save(){
 await fs.writeFile(path.join(folder,'private-evidence.json'),JSON.stringify(proof,null,2));
 const safe=structuredClone(proof);safe.runs=safe.runs.map(({text,reason,...r})=>({...r,answer_sha256:hash(text||''),answer_characters:(text||'').length}));
 for(const c of safe.cases){delete c.proposals;delete c.tasks;if(c.error)c.error='Assertion failed; private diagnostics retained on D:.';}
 if(safe.error)safe.error='Acceptance assertion failed; private diagnostics retained on D:.';
 await fs.writeFile(path.resolve('docs/evidence',`audit-live-${id}.json`),JSON.stringify(safe,null,2)+'\n');
}
const state=async v=>(await v.page.request.get('/api/state')).json();
async function open(storageState){
 const context=await browser.newContext({baseURL:base,viewport:{width:1440,height:1000},...(storageState?{storageState}:{})}),page=await context.newPage();
 const v={context,page};visitors.push(v);await page.goto('/',{waitUntil:'domcontentloaded',timeout:90000});
 await expect(page.getByRole('button',{name:'Use my own data',exact:true})).toBeVisible({timeout:45000});
 const s=await state(v);if(!storageState){assert.equal(s.sources.length,0);assert.equal(s.tasks.length,0);}assert(s.agent.configured&&s.agent.public_access);
 v.workspace=s.workspace_id;const cookie=(await context.cookies()).find(c=>c.name==='relay_session');assert(cookie?.secure&&cookie.httpOnly&&cookie.sameSite==='Strict');await context.storageState({path:path.join(folder,'private-session-'+v.workspace+'.json')});
 return v;
}
async function run(v,start){
 await v.page.locator('.live-access input[type=checkbox]').check();
 const pending=v.page.waitForResponse(r=>new URL(r.url()).pathname==='/api/chat'&&r.request().method()==='POST');
 const began=Date.now();await start();const response=await pending;assert.equal(response.status(),202);let result=await response.json();
 const deadline=Date.now()+660000;
 while(['queued','running','quota_wait','cancel_requested'].includes(result.status)&&Date.now()<deadline){await new Promise(r=>setTimeout(r,3000));result=await (await v.page.request.get('/api/runs/'+result.run_id)).json();}
 result.observed_latency_ms=Date.now()-began;proof.runs.push(result);await save();assert(['complete','partial'].includes(result.status));assert.equal(result.provider,'gemini_developer');
 assert.equal(result.runtime_revision,proof.deployed_commit);assert.equal(result.gateway_revision,proof.deployed_commit);
 await expect(v.page.locator('.answer pre')).toHaveText(result.text,{timeout:20000});return result;
}
async function ask(v,message){return run(v,async()=>{await v.page.locator('.assistant input[maxlength="6000"]').fill(message);await v.page.locator('.assistant > form button').click();});}
async function documentCase(c,index){
 const v=index<2?visitors[index]:await open();const item={file:c.file,sha256:hash(await fs.readFile(c.path)),passed:false};proof.cases.push(item);
 if(c.sha256)assert.equal(item.sha256,c.sha256);
 try{
  if(!(await state(v)).sources.some(s=>s.filename===c.file))await v.page.locator('input[type=file]').first().setInputFiles(c.path);
  else await v.page.getByRole('button',{name:'Evidence',exact:true}).click();
  await expect(v.page.getByText(c.file,{exact:true}).first()).toBeVisible();
  const source=(await state(v)).sources.find(s=>s.filename===c.file);item.source_id=source.id;item.source_version=source.version;
  const answer=index===0&&resumed?resumed.runs[0]:await run(v,()=>v.page.getByRole('button',{name:'Propose with Gemini',exact:true}).click());
  if(index===0&&resumed){proof.runs.push(answer);await save();}item.actual_answer_status=answer.status;
  assert(answer.tool_observations?.some(t=>t.tool==='read_course_source'&&t.status==='observed'));
  await v.page.getByRole('button',{name:'Refresh proposals',exact:true}).click();
  let proposals=(await (await v.page.request.get('/api/extraction-proposals')).json()).proposals.filter(p=>p.source_id===source.id);item.proposals=proposals;
  // A genuinely partial batch retains good fields and is conservatively marked
  // failed by the execution inspector. Do not confuse that with no saved data.
  // Permit exactly one ordinary UI follow-up, without feeding expected answers.
  if(proposals.some(p=>p.validation_issues?.length)){
   item.initial_validation_issues=proposals.flatMap(p=>p.validation_issues||[]);
   const repair=await ask(v,`The saved proposal for source ${source.id} lists rejected fields under validation_issues. Re-read the exact original source pages and quote_lines, then use propose_academic_extraction to correct those rejected fields for their existing entity_id. Shared document course/term context may be cited using its exact original quote. Preserve other valid fields; do not invent missing information or confirm facts. Report anything still unresolved.`);
   item.repair_run_id=repair.run_id;await v.page.getByRole('button',{name:'Refresh proposals',exact:true}).click();
   proposals=(await (await v.page.request.get('/api/extraction-proposals')).json()).proposals.filter(p=>p.source_id===source.id);item.proposals=proposals;
  }
  assert(proposals.length,'No actual saved extraction proposal');
  assert(proposals.every(p=>!p.validation_issues?.length),'Cited fields still have unresolved rejection diagnostics');
  const entities=proposals.flatMap(p=>p.entities);assert.equal(entities.length,c.expected.length);
  for(const expected of c.expected){
   const entity=entities.find(e=>e.fields.some(f=>f.field==='assignment_key'&&String(f.value).toLowerCase()===expected.key.toLowerCase()));assert(entity,'Missing entity '+expected.key);
   assert.equal(entity.fields.find(f=>f.field==='minutes')?.value,expected.minutes);
   assert(['title','course','term','assignment_key'].every(key=>entity.fields.some(f=>f.field===key&&f.value&&f.validation_status==='needs_confirmation')),'Missing cited assignment identity');
   const due=entity.fields.find(f=>f.field==='due');assert(due?.value&&Date.parse(due.value)===Date.parse(expected.due),'Incorrect cited due for '+expected.key);
   assert.equal(due.validation_status,'needs_confirmation');
   if(entity.applied)continue;
   await expect(v.page.locator('.working')).toHaveCount(0);
   const forms=v.page.getByTestId('review-entity');let form;
   for(let i=0;i<await forms.count();i++)if((await forms.nth(i).getByLabel('Assignment key',{exact:true}).inputValue()).toLowerCase()===expected.key.toLowerCase()){form=forms.nth(i);break;}
   assert(form);await form.locator('summary').click();await expect(form.locator('blockquote').first()).toBeVisible();
   await form.getByLabel('I reviewed this assignment and confirm only these fields.').check();
   const changed=v.page.waitForResponse(r=>/\/confirm$/.test(new URL(r.url()).pathname)&&r.request().method()==='POST');await form.getByRole('button',{name:'Confirm this assignment',exact:true}).click();assert((await changed).ok());
  }
  await v.page.reload();await expect(v.page.getByRole('button',{name:'Use my own data',exact:true})).toBeVisible();
  let s=await state(v);item.tasks=s.tasks;assert.equal(s.tasks.length,c.expected.length);assert(s.tasks.every(t=>t.extraction_origin==='confirmed_semantic_proposal'));
  await v.page.getByLabel('Workspace timezone',{exact:true}).fill('Asia/Almaty');
  await v.page.getByLabel('Range starts',{exact:true}).fill('2026-10-19');await v.page.getByLabel('Range ends',{exact:true}).fill('2026-10-25');
  await v.page.getByRole('button',{name:'Save planning context',exact:true}).click();await expect.poll(async()=>(await state(v)).settings.windows.length).toBe(5);
  await v.page.getByRole('button',{name:'Repair my week',exact:true}).click();await expect.poll(async()=>(await state(v)).plan?.feasible,{timeout:15000}).toBe(true);
  s=await state(v);const baseline=s.plan.id;item.plan={id:baseline,required_minutes:s.plan.required_minutes,feasible:s.plan.feasible,scope_complete:s.plan.scope.complete};assert(s.plan.scope.complete);
  await v.page.getByRole('button',{name:'Recovery',exact:true}).click();await v.page.getByRole('button',{name:'One hour more effort',exact:true}).click();await expect(v.page.getByText('What-if · baseline unchanged',{exact:true})).toBeVisible();assert.equal((await state(v)).plan.id,baseline);
  await v.page.getByRole('button',{name:'Return to baseline',exact:true}).click();await v.page.getByRole('button',{name:'Review calendar actions',exact:true}).click();await v.page.getByRole('button',{name:'Approve illustrative local actions',exact:true}).click();await expect.poll(async()=>(await state(v)).receipts.length).toBe(1);
  const receipt=(await state(v)).receipts[0];assert.equal(receipt.mode,'illustrative');assert.equal(receipt.status,'verified');item.receipt={id:receipt.id,status:receipt.status,mode:receipt.mode};
  await v.page.getByRole('button',{name:'My week',exact:true}).click();await v.page.locator('.continuity-toggle').click();
  const panel=v.page.getByTestId('progress-panel');await panel.getByLabel('Actual minutes to record',{exact:true}).fill('45');await panel.getByRole('button',{name:'Log work manually',exact:true}).click();
  await panel.getByLabel('Remaining minutes',{exact:true}).fill('95');await panel.getByRole('button',{name:'Save remaining estimate',exact:true}).click();await expect(panel.locator('.effort-comparison')).toContainText('95');
  await v.page.getByRole('button',{name:'Workspace Passport',exact:true}).click();await v.page.getByRole('button',{name:'Preview portable workspace',exact:true}).click();
  const pending=v.page.waitForEvent('download');await v.page.getByRole('button',{name:'Download .relay.json',exact:true}).click();await (await pending).saveAs(path.join(folder,c.file+'.relay.json'));
  await v.page.reload();await expect(v.page.getByRole('button',{name:'Use my own data',exact:true})).toBeVisible();assert((await state(v)).tasks.some(t=>t.progress?.remaining_minutes===95));
  item.confirmation_plan_whatif_illustrative_receipt_progress_passport_refresh=true;item.passed=true;v.source=source;await save();
  await v.page.screenshot({path:path.join(folder,c.file+'.png'),fullPage:true});return v;
 }catch(e){item.error=String(e);await save();await v.page.screenshot({path:path.join(folder,c.file+'-failure.png'),fullPage:true});throw e;}
}
try{
 const health=await (await fetch(base+'/api/health')).json();assert.equal(health.version,'0.5.1');if(process.env.RELAY_EXPECTED_DEPLOY_COMMIT)assert.equal(health.deployed_commit,process.env.RELAY_EXPECTED_DEPLOY_COMMIT);proof.deployed_commit=health.deployed_commit;
 if(resumed){for(const f of (await fs.readdir(resumeFolder)).filter(n=>n.startsWith('private-session-')))await open(path.join(resumeFolder,f));if(!(await state(visitors[0])).sources.length)visitors.reverse();assert.equal(proof.deployed_commit,resumed.deployed_commit);}
 else {await open();await open();}assert.notEqual(visitors[0].workspace,visitors[1].workspace);proof.checks.two_clean_automatic_workspaces=resumed?resumed.checks.two_clean_automatic_workspaces:true;await save();
 for(let i=0;i<cases.length;i++)await documentCase(cases[i],i);
 const [a,b]=visitors;assert.equal((await b.page.request.get('/api/sources/'+a.source.id)).status(),403);assert.equal((await a.page.request.get('/api/sources/'+b.source.id)).status(),403);
 assert.equal((await b.page.request.get('/api/runs/'+proof.runs[0].run_id)).status(),403);proof.checks.documents_history_runs_plans_isolated=true;
 const follow=await ask(a,'Use get_progress_summary and my confirmed workspace facts. What are the actual logged minutes and my explicitly stated remaining minutes for the coursework I updated? Distinguish them, do not subtract logged time automatically, and refer to our earlier document.');
 assert(follow.tool_observations?.some(t=>t.tool==='get_progress_summary'&&t.status==='observed'));assert(follow.text.includes('45')&&follow.text.includes('95'));assert.equal(follow.conversation_id,proof.runs[0].conversation_id);proof.checks.followup_same_real_conversation_and_canonical_progress=true;
 for(const route of ['/_relay/mcp/','/managed/mcp/','/internal/runtime-state','/internal/managed-route','/api/test/seed'])assert.equal((await a.page.request.post(route,{data:{}})).status(),403);
 proof.checks.internal_routes_protected=true;proof.passed=true;await save();console.log(JSON.stringify({passed:true,evidence:`docs/evidence/audit-live-${id}.json`,private_folder:folder,real_turns:proof.runs.length}));
}catch(e){proof.passed=false;proof.error=String(e);await save();console.error(JSON.stringify({passed:false,error:String(e),private_folder:folder}));process.exitCode=1;}
finally{await browser.close();}
