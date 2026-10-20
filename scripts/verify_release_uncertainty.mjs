/** Own synthetic missing/conflicting briefs through the public UI. No AI calls. */
import fs from 'node:fs/promises';import path from 'node:path';import crypto from 'node:crypto';
import assert from 'node:assert/strict';import {chromium,expect as baseExpect} from '@playwright/test';
const expect=baseExpect.configure({timeout:30000}),base='https://campuspulse-relay-demo.onrender.com';
const folder=path.resolve('fixtures/acceptance-0.5.1');await fs.mkdir(folder,{recursive:true});
const proof={at:new Date().toISOString(),base,actual_gemini_calls:0,google_calls:0,checks:{},inputs:[]};
const browser=await chromium.launch({headless:true});
async function visitor(){const context=await browser.newContext({baseURL:base}),page=await context.newPage();await page.goto('/');await expect(page.getByRole('button',{name:'Use my own data',exact:true})).toBeVisible();return page;}
const state=async p=>(await p.request.get('/api/state')).json();
async function upload(page,name,text){const file=path.join(folder,name);await fs.writeFile(file,text);proof.inputs.push({file:'fixtures/acceptance-0.5.1/'+name,sha256:crypto.createHash('sha256').update(text).digest('hex')});await page.locator('input[type=file]').first().setInputFiles(file);await expect(page.getByText(name,{exact:true}).first()).toBeVisible();}
async function confirm(page,name){const pending=page.waitForResponse(r=>new URL(r.url()).pathname.endsWith('/review')&&r.request().method()==='POST');await page.locator('.review-source').filter({hasText:name}).getByRole('button',{name:'Review extracted fields',exact:true}).click();const response=await pending;assert(response.ok(),'Review returned '+response.status());const proposed=await response.json();proof.last_review={status:response.status(),entities:proposed.entities?.length};const form=page.getByTestId('review-entity').first();await expect(form).toBeVisible();await form.getByLabel('I reviewed this assignment and confirm only these fields.').check();await form.getByRole('button',{name:'Confirm this assignment',exact:true}).click();await expect(form).toHaveCount(0);}
try{
 const health=await(await fetch(base+'/api/health')).json();assert.equal(health.version,'0.5.1');proof.deployed_commit=health.deployed_commit;
 for(const [lang,title,course,term,text] of [
  ['en','Orbital mirror journal','Synthetic observation','Autumn 2026','The supervisor will announce the deadline. No workload estimate is supplied.'],
  ['ru','Журнал орбитального зеркала','Синтетическое наблюдение','Осень 2026','Преподаватель объявит срок отдельно. Длительность работы не указана.'],
  ['kk','Орбиталық айна күнделігі','Синтетикалық бақылау','Күз 2026','Мерзімді оқытушы кейін хабарлайды. Жұмыс ұзақтығы көрсетілмеген.'],
 ].filter(()=>!process.env.RELAY_CONFLICT_ONLY)){
  const page=await visitor();await upload(page,'unknown-'+lang+'.md',`Assignment: ${title}\nCourse: ${course}\nTerm: ${term}\nAssignment ID: unknown-${lang}-051\n\n${text}\n`);
  await page.getByRole('button',{name:'Review extracted fields',exact:true}).click();const form=page.getByTestId('review-entity').first();
  await expect(form.getByLabel('Exact effort in minutes',{exact:true})).toHaveValue('');await expect(form.getByLabel(/Deadline in workspace timezone/)).toHaveValue('');
  await form.getByLabel('I reviewed this assignment and confirm only these fields.').check();await form.getByRole('button',{name:'Confirm this assignment',exact:true}).click();await expect(form).toHaveCount(0);
  let s=await state(page);assert.equal(s.tasks[0].minutes,null);assert.equal(s.tasks[0].due,null);assert.equal(s.tasks[0].extraction_origin,'confirmed_semantic_proposal');
  await page.reload();await expect(page.getByRole('button',{name:'Use my own data',exact:true})).toBeVisible();s=await state(page);assert.equal(s.tasks[0].minutes,null);assert.equal(s.tasks[0].due,null);
  proof.checks[lang+'_own_missing_fields_remain_unknown_after_confirmation_and_refresh']=true;await page.context().close();
 }
 const page=await visitor();
 for(const [name,due] of [['conflict-a.md','2026-10-23T18:00:00+05:00'],['conflict-b.md','2026-10-24T18:00:00+05:00']]){
  await upload(page,name,`Assignment: Copper lattice notebook\nTerm: Autumn 2026\nAssignment ID: lattice-051\nCourse: Synthetic materials\nEffort: 45 minutes\nDue: ${due}\n- [ ] Explain the lattice comparison\n`);await confirm(page,name);
 }
 let s=await state(page);assert.equal(s.tasks.length,1);assert.equal(s.conflicts.length,1);assert.equal(s.conflicts[0].status,'unresolved');assert.equal(new Set(s.conflicts[0].facts.map(f=>f.source_id)).size,2);
 await page.getByRole('button',{name:'Evidence',exact:true}).click();await expect(page.locator('.conflict-card')).toHaveCount(1);await page.locator('.conflict-card').getByRole('button',{name:'Use this deadline',exact:true}).first().click();
 await expect.poll(async()=>(await state(page)).conflicts[0].status).toBe('resolved');s=await state(page);assert.equal(s.conflicts[0].facts.length,2);assert(s.conflicts[0].resolution.fact_id);
 proof.checks.own_conflicting_sources_preserved_and_explicit_choice_persisted=true;
 await page.reload();await expect(page.getByRole('button',{name:'Use my own data',exact:true})).toBeVisible();assert.equal((await state(page)).conflicts[0].status,'resolved');proof.checks.conflict_choice_survives_refresh=true;
 proof.passed=true;
}catch(error){proof.passed=false;proof.error=String(error);throw error;}finally{await browser.close();await fs.writeFile('docs/evidence/final-0.5.1-uncertainty-ui.json',JSON.stringify(proof,null,2)+'\n');}
console.log(JSON.stringify(proof));
