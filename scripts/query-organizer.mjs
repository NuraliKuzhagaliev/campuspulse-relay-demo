/** Actual T0 acceptance only. Default is offline, never a deployment claim. */
import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import {spawnSync} from 'node:child_process';
import {chromium,expect as baseExpect} from '@playwright/test';
const argv=process.argv.slice(2),option=n=>argv[argv.indexOf(n)+1];
if(!argv.includes('--execute')){console.log(JSON.stringify({offline:true,resources_created:false,remote_query_verified:false,action:'After actual deployment, pass --execute --plan D:/...actual-plan.json --resource projects/.../locations/.../reasoningEngines/...',planned_real_turns:3}));process.exit(0);}
assert(argv.includes('--plan')&&argv.includes('--resource'),'Actual plan and discovered resource required');
const planPath=path.resolve(option('--plan'));assert(/^D:[\\/]/i.test(planPath));
const plan=JSON.parse(await fs.readFile(planPath,'utf8')),resource=option('--resource');
assert.equal(plan.personal_spending_authorized_usd,0);assert(plan.covered_prerequisites_verified&&plan.cleanup_reserve_verified);
const parts=resource.split('/');assert.equal(parts.length,6);assert.equal(parts[0],'projects');assert([plan.project,String(plan.project_number)].includes(parts[1]));assert.equal(parts[2],'locations');assert.equal(parts[3],plan.region);assert.equal(parts[4],'reasoningEngines');assert(/^[a-f0-9]{40}$/.test(plan.source_commit));
const guard=spawnSync(path.resolve('.venv/Scripts/python.exe'),['scripts/check-funding.py','--record',plan.funding_record,'--project',plan.project,'--budget',String(plan.authorized_credit_usage_usd),'--hours',String(plan.planned_hours)],{stdio:'pipe'});
assert.equal(guard.status,0,'Actual funding/window guard failed; no query sent');
const base='https://campuspulse-relay-demo.onrender.com',id=Date.now().toString(36),folder=path.resolve('.local/organizer',plan.owned_prefix,'query-'+id);
await fs.mkdir(folder,{recursive:true});const expect=baseExpect.configure({timeout:45000});
const proof={at:new Date().toISOString(),resource,project:plan.project,region:plan.region,model:plan.model,source_commit:plan.source_commit,url:base,personal_spending:0,invitations:false,provider_substitution:false,checks:{},runs:[]};
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');const browser=await chromium.launch({headless:true});const visitors=[];
const state=async v=>(await v.page.request.get('/api/state')).json();
async function save(){await fs.writeFile(path.join(folder,'private-query.json'),JSON.stringify(proof,null,2));const safe=structuredClone(proof);safe.runs=safe.runs.map(({text,...r})=>({...r,answer_sha256:hash(text||''),answer_characters:(text||'').length}));if(safe.error)safe.error='Acceptance failed; private diagnostics retained on D:.';await fs.writeFile('docs/evidence/managed-query-'+id+'.json',JSON.stringify(safe,null,2));}
async function ask(v,message){
 await v.page.locator('.live-access input[type=checkbox]').check();await v.page.locator('.assistant input[maxlength="6000"]').fill(message);
 const pending=v.page.waitForResponse(r=>new URL(r.url()).pathname==='/api/chat'&&r.request().method()==='POST');await v.page.locator('.assistant > form button').click();const response=await pending;assert.equal(response.status(),202);let result=await response.json();const until=Date.now()+660000;
 while(['queued','running','quota_wait','cancel_requested'].includes(result.status)&&Date.now()<until){await new Promise(r=>setTimeout(r,3000));result=await(await v.page.request.get('/api/runs/'+result.run_id)).json();}
 proof.runs.push(result);await save();assert(['complete','partial'].includes(result.status)&&result.text);assert.equal(result.provider,'vertex');assert.equal(result.deployment_mode,'managed_gcp');assert.equal(result.managed_resource,resource);assert.equal(result.runtime_revision,plan.source_commit);assert.equal(result.gateway_revision,plan.source_commit);await expect(v.page.locator('.answer pre')).toHaveText(result.text);return result;
}
try{
 const health=await(await fetch(base+'/api/health')).json();assert.equal(health.deployed_commit,plan.source_commit);
 for(let i=0;i<2;i++){
  const context=await browser.newContext({baseURL:base,viewport:{width:1440,height:1000}}),page=await context.newPage(),v={context,page};visitors.push(v);await page.goto('/',{timeout:90000});await expect(page.getByRole('button',{name:'Use my own data',exact:true})).toBeVisible();
  let s=await state(v);assert.equal(s.sources.length,0);assert.equal(s.agent.provider,'vertex');assert(s.agent.public_access);v.workspace=s.workspace_id;
  const code=crypto.randomBytes(6).toString('hex'),filename='unseen-organizer-'+code+'.md';v.code=code;
  const document=`Course: Independent optics\nTerm: Autumn 2026\nAssignment: Calibration ${code}\nAssignment ID: cal-${code}\nDue: 2026-10-24T18:00:00+05:00\nEffort: 45 minutes\n- [ ] Explain instrument drift\nVerification phrase: ${code}\n`;
  await fs.writeFile(path.join(folder,filename),document);await page.locator('input[type=file]').first().setInputFiles(path.join(folder,filename));await expect(page.getByText(filename,{exact:true}).first()).toBeVisible();s=await state(v);v.source=s.sources.find(x=>x.filename===filename);assert(v.source);
  await context.storageState({path:path.join(folder,'private-session-'+i+'.json')});
  const answer=await ask(v,`Read source ${v.source.id} using read_course_source. Quote its exact verification phrase and stated effort with source/page citations. Do not change facts or call Calendar.`);assert(answer.text.includes(code)&&answer.text.includes('45'));assert(answer.tool_observations.some(t=>t.tool==='read_course_source'&&t.status==='observed'));v.run=answer;
  await page.screenshot({path:path.join(folder,'visitor-'+i+'.png'),fullPage:true});
 }
 assert.notEqual(visitors[0].workspace,visitors[1].workspace);for(const [a,b] of [[visitors[0],visitors[1]],[visitors[1],visitors[0]]]){assert.equal((await b.page.request.get('/api/sources/'+a.source.id)).status(),403);assert.equal((await b.page.request.get('/api/runs/'+a.run.run_id)).status(),403);}
 proof.checks.two_uninvited_visitors_documents_runs_isolated=true;
 const a=visitors[0];await a.page.getByRole('button',{name:'My week',exact:true}).click();await a.page.locator('.continuity-toggle').click();const panel=a.page.getByTestId('progress-panel');await panel.getByLabel('Actual minutes to record',{exact:true}).fill('45');await panel.getByRole('button',{name:'Log work manually',exact:true}).click();await panel.getByLabel('Remaining minutes',{exact:true}).fill('95');await panel.getByRole('button',{name:'Save remaining estimate',exact:true}).click();await expect(panel.locator('.effort-comparison')).toContainText('95');
 const follow=await ask(a,'Use get_progress_summary. State my actual logged minutes and explicit remaining minutes separately, and relate them to our earlier calibration document. Do not subtract automatically.');assert.equal(follow.conversation_id,a.run.conversation_id);assert(follow.text.includes('45')&&follow.text.includes('95'));assert(follow.tool_observations.some(t=>t.tool==='get_progress_summary'&&t.status==='observed'));
 await a.page.reload();await expect(a.page.getByRole('button',{name:'Use my own data',exact:true})).toBeVisible();assert((await state(a)).tasks.some(t=>t.progress?.remaining_minutes===95));proof.checks.same_authoritative_workspace_followup_progress_refresh=true;
 for(const route of ['/managed/mcp/','/internal/runtime-state','/internal/managed-route'])assert.equal((await a.page.request.post(route,{data:{}})).status(),403);proof.checks.internal_operations_remain_protected=true;proof.remote_query_verified=true;proof.passed=true;await save();console.log(JSON.stringify({passed:true,evidence:'docs/evidence/managed-query-'+id+'.json',resource,actual_turns:proof.runs.length}));
}catch(error){proof.error=String(error);proof.passed=false;await save();console.error(JSON.stringify({passed:false,private_diagnostics:folder}));process.exitCode=1;}finally{await browser.close();}
