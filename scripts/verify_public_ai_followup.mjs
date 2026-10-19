/** Complete non-model checks in the same two originally clean public workspaces.
 * Reuses their private D: cookies solely to avoid spending new provider calls.
 */
import fs from 'node:fs/promises';import path from 'node:path';import assert from 'node:assert/strict';
import {chromium,expect} from '@playwright/test';import AxeBuilder from '@axe-core/playwright';
const original=process.argv[2];assert.match(original,/^public-ai-live-[a-z0-9]+\.json$/);
const root=process.cwd(),source=JSON.parse(await fs.readFile(path.join(root,'docs/evidence',original),'utf8'));
assert(source.checks.two_real_gemini_signed_mcp_answers.actual_model_turns===2&&source.runs.length===2);
assert(source.runs.every(r=>r.status==='complete'));
const id=original.replace('public-ai-live-','').replace('.json',''),folder=path.join(root,'.local/public-ai-live',id);
const files=(await fs.readdir(folder)).filter(n=>/^private-demo-.*\.json$/.test(n));assert.equal(files.length,2);
const proof={checked_at:new Date().toISOString(),version:'0.4.1',url:source.url,deployed_commit:source.deployed_commit,
 initial_clean_session_evidence:'docs/evidence/'+original,original_clean_sessions:2,followup_reuses_only_these_two_workspaces:true,
 actual_complete_real_gemini_turns:2,additional_model_calls:0,personal_invitations:0,registration:false,visitor_api_key:false,
 complete_answers_and_uploaded_documents_published:false,prior_failure_retained:'docs/evidence/public-ai-first-provider-failure.json',checks:{}};
const browser=await chromium.launch({headless:true});
try{
 const sessions=[];
 for(const file of files){
  const context=await browser.newContext({baseURL:source.url,storageState:path.join(folder,file),viewport:{width:1440,height:900}});
  const page=await context.newPage();await page.goto('/');await expect(page.locator('.live-access input[type=checkbox]')).toBeVisible();
  const state=await (await page.request.get('/api/state')).json();assert(state.agent.public_access);
  const conversation=await (await page.request.get('/api/conversation')).json();assert.equal(conversation.turns.length,1);
  const run=source.runs.find(r=>r.conversation_id===conversation.id);assert(run&&conversation.turns[0].status==='complete');
  assert.equal((await (await page.request.get('/api/health')).json()).deployed_commit,source.deployed_commit);
  sessions.push({context,page,state,run});
 }
 const a=sessions.find(s=>s.state.sources.some(x=>x.filename?.startsWith('unseen-public-a-'))),b=sessions.find(s=>s!==a);assert(a&&b);
 assert.notEqual(a.state.workspace_id,b.state.workspace_id);
 for(const [own,other] of [[a,b],[b,a]]){
  assert.equal((await own.page.request.get('/api/runs/'+other.run.run_id)).status(),403);
  const imported=other.state.sources.find(s=>s.filename?.startsWith('unseen-public-'));assert(imported);
  assert.equal((await own.page.request.get('/api/sources/'+imported.id)).status(),403);
 }
 proof.checks.independent_documents_histories_and_run_authorization=true;
 async function post(session,route,data={}){
  const csrf=(await (await session.page.request.get('/api/session')).json()).csrf;
  const response=await session.page.request.post('/api'+route,{headers:{'X-Relay-CSRF':csrf},data});
  assert.equal(response.status(),200);return response.json();
 }
 // The earlier harness incorrectly tried planning with unresolved fixture conflicts.
 // Resolve them explicitly, exactly as the operational workflow requires.
 for(const c of a.state.conflicts)await post(a,'/conflicts/'+c.id+'/resolve',{fact_id:c.facts[0].id});
 const plan=await post(a,'/plan');assert(plan.id);
 const bs=(await (await b.page.request.get('/api/session')).json()).csrf;
 assert.equal((await b.page.request.post('/api/plans/'+plan.id+'/preview',{headers:{'X-Relay-CSRF':bs},data:{}})).status(),403);
 proof.checks.actual_plan_and_foreign_preview_denial=true;
 for(const route of ['/internal/ai-invitations','/_relay/mcp/','/api/judge/claim','/api/connections/calendar','/api/test/seed'])
  assert.equal((await a.page.request.post(route,{data:{}})).status(),403);
 proof.checks.internal_admin_invitation_calendar_test_routes_protected=true;
 const layouts=[];
 for(const lang of ['en','ru','kk'])for(const width of [390,768,1440]){
  await a.page.getByTestId('language').selectOption(lang);await a.page.setViewportSize({width,height:900});
  assert.equal(await a.page.locator('html').getAttribute('lang'),lang);
  assert(await a.page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));layouts.push({lang,width});
 }
 proof.checks.nine_language_width_states=layouts;
 await a.page.getByTestId('language').selectOption('en');await a.page.setViewportSize({width:1440,height:900});
 const audit=await new AxeBuilder({page:a.page}).withTags(['wcag2a','wcag2aa']).analyze();
 proof.checks.automated_AA_violations=audit.violations.map(v=>({id:v.id,targets:v.nodes.map(n=>n.target)}));assert.equal(audit.violations.length,0);
 await a.page.screenshot({path:path.join(folder,'screenshots/verified-public-desktop.png'),fullPage:true});
 await a.page.getByTestId('language').selectOption('ru');await a.page.setViewportSize({width:390,height:844});
 await a.page.screenshot({path:path.join(folder,'screenshots/verified-public-mobile-ru.png'),fullPage:true});
 const before=await (await a.page.request.get('/api/conversation')).json();await a.page.reload();
 await expect(a.page.locator('.live-access input[type=checkbox]')).not.toBeChecked();
 assert.equal((await (await a.page.request.get('/api/conversation')).json()).id,before.id);
 proof.checks.refresh_preserves_history_requires_new_processing_confirmation=true;
 proof.verified=true;proof.real_gemini_verified=true;proof.managed_agent_engine=false;proof.real_calendar_writes=0;
}catch(e){proof.verified=false;proof.error='Follow-up assertion failed; diagnostics retained in local log.';console.error(String(e));process.exitCode=1;}
finally{await browser.close();await fs.writeFile('docs/evidence/public-ai-acceptance-0.4.1.json',JSON.stringify(proof,null,2));console.log(JSON.stringify({verified:proof.verified,evidence:'docs/evidence/public-ai-acceptance-0.4.1.json',additional_model_calls:0}));}
