import {chromium,expect as baseExpect} from '@playwright/test';
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import AxeBuilder from '@axe-core/playwright';
const base=process.argv[2]||'http://127.0.0.1:8024';
const expect=baseExpect.configure({timeout:30000});
const folder=path.resolve(process.argv[3]||'.local/audit-ui/verification');await fs.mkdir(folder,{recursive:true});
const browser=await chromium.launch({headless:true});
const context=await browser.newContext({baseURL:base,viewport:{width:1440,height:1000}});const page=await context.newPage();
const proof={at:new Date().toISOString(),base,provider_calls:0,checks:{}};
async function step(name,fn){try{proof.checks[name]=(await fn())??true;}catch(e){proof.checks[name]={failed:true,error:String(e)};throw e;}finally{await fs.writeFile(path.join(folder,'results.json'),JSON.stringify(proof,null,2));}}
const state=async()=> (await page.request.get('/api/state')).json();
try{
 await page.goto('/',{waitUntil:'domcontentloaded'});await expect(page.getByRole('button',{name:'Use my own data',exact:true})).toBeVisible();
 await step('clean_own_workspace',async()=>{const s=await state();assert.equal(s.tasks.length,0);assert.equal(s.sources.length,0);assert.equal(s.calendar_events.length,0);return true;});
 await step('sample_download_and_index',async()=>{const response=await page.request.get('/samples/judge_sample_pack.zip');assert(response.ok());const zip=await response.body();assert(zip.length>10000);await fs.writeFile(path.join(folder,'downloaded-sample-pack.zip'),zip);assert((await page.request.get('/samples/')).ok());});
 await page.locator('input[type=file]').first().setInputFiles(path.resolve('public/samples/11-continued-brief.pdf'));
 await expect(page.getByText('11-continued-brief.pdf',{exact:true}).first()).toBeVisible();
 await step('multipage_import',async()=>{const s=await state();assert.equal(s.tasks.length,1);assert.equal(s.tasks[0].minutes,75);assert(s.sources[0].facts.some(f=>f.field==='due'&&f.page===2));});
 await page.getByRole('button',{name:'Review extracted fields',exact:true}).click();
 const form=page.getByTestId('review-entity').first();await expect(form).toBeVisible();
 await expect(form.getByLabel('Assignment title',{exact:true})).toHaveValue('Polarization memo');
 await form.getByLabel('I reviewed this assignment and confirm only these fields.').check();
 await form.getByRole('button',{name:'Confirm this assignment',exact:true}).click();
 await expect(form).toHaveCount(0);
 await step('explicit_review_persisted',async()=>{const s=await state();assert.equal(s.tasks[0].extraction_origin,'confirmed_semantic_proposal');assert.equal(s.tasks[0].minutes,75);await page.reload();await expect(page.getByRole('button',{name:'Use my own data',exact:true})).toBeVisible();assert.equal((await state()).tasks[0].minutes,75);});
 await page.getByRole('button',{name:'Open example',exact:true}).click();await expect(page.getByText('Example workspace',{exact:true})).toBeVisible();
 await step('example_separate',async()=>{const s=await state();assert(s.tasks.length>=3);assert(!s.sources.some(s=>s.filename==='11-continued-brief.pdf'));});
 await page.getByRole('button',{name:'Use my own data',exact:true}).click();await expect(page.getByText('Your own documents',{exact:true})).toBeVisible();
 await step('switch_preserves_own',async()=>assert.equal((await state()).tasks[0].minutes,75));
 await step('planning_through_ui',async()=>{
   await page.getByLabel('Workspace timezone',{exact:true}).fill('Asia/Almaty');
   await page.getByLabel('Range starts',{exact:true}).fill('2026-10-19');await page.getByLabel('Range ends',{exact:true}).fill('2026-10-25');
   await page.getByRole('button',{name:'Save planning context',exact:true}).click();
   await expect.poll(async()=>(await state()).settings.windows.length).toBe(5);
   await page.getByRole('button',{name:'Repair my week',exact:true}).click();await expect.poll(async()=>(await state()).plan?.required_minutes).toBe(90);
   const s=await state();assert(s.plan.feasible&&s.plan.scope.complete);assert.equal(await page.locator('.seven-day-grid .day-header').count(),7);
 });
 await step('whatif_and_illustrative_receipt',async()=>{
   const original=(await state()).plan.id;await page.getByRole('button',{name:'Recovery',exact:true}).click();await page.getByRole('button',{name:'One hour more effort',exact:true}).click();
   await expect(page.getByText('What-if · baseline unchanged',{exact:true})).toBeVisible();assert.equal((await state()).plan.id,original);
   await page.getByRole('button',{name:'Return to baseline',exact:true}).click();await page.getByRole('button',{name:'Review calendar actions',exact:true}).click();await page.getByRole('button',{name:'Approve illustrative local actions',exact:true}).click();
   await expect.poll(async()=>(await state()).receipts.length).toBe(1);const receipt=(await state()).receipts[0];assert.equal(receipt.status,'verified');assert.equal(receipt.mode,'illustrative');
 });
 await step('preflight_own_draft',async()=>{
   const file=path.join(folder,'polarization-audit.md');await fs.writeFile(file,'# Method\nTwo synthetic filters were calibrated against a reference.\n# Results\nBoth readings were compared and a difference recorded.\n# Limitations\nUncertainty remains a human review question.\n');
   await page.getByRole('button',{name:'Judge challenge',exact:true}).click();const wait=page.waitForResponse(r=>new URL(r.url()).pathname==='/api/preflight'&&r.request().method()==='POST');
   await page.locator('input[accept=".pdf,.md,.txt"]').setInputFiles(file);const r=await wait;assert(r.ok());const p=await r.json();assert.equal(p.missing_count,0);assert.equal(p.assessment_status,'human_review_required');assert(p.results.length>=3);
 });
 await page.getByRole('button',{name:'My week',exact:true}).click();await page.locator('.continuity-toggle').click();
 await step('progress_and_explicit_remaining',async()=>{
   const p=page.getByTestId('progress-panel');await p.getByLabel('Actual minutes to record',{exact:true}).fill('45');await p.getByRole('button',{name:'Log work manually',exact:true}).click();await expect(p.locator('.effort-comparison')).toContainText('Unknown');
   await p.getByLabel('Remaining minutes',{exact:true}).fill('95');await p.getByRole('button',{name:'Save remaining estimate',exact:true}).click();await expect(p.locator('.effort-comparison')).toContainText('95');const s=await state();assert.equal(s.tasks[0].progress.remaining_minutes,95);
 });
 await step('passport_download_restore_reopen',async()=>{
   await page.getByRole('button',{name:'Workspace Passport',exact:true}).click();await page.getByRole('button',{name:'Preview portable workspace',exact:true}).click();await expect(page.getByRole('button',{name:'Download .relay.json',exact:true})).toBeVisible();
   const pending=page.waitForEvent('download');await page.getByRole('button',{name:'Download .relay.json',exact:true}).click();const downloaded=await pending;const target=path.join(folder,'own-audit.relay.json');await downloaded.saveAs(target);
   await page.getByLabel('Portable workspace file',{exact:true}).setInputFiles(target);await expect(page.getByRole('button',{name:'Import as fresh copy and switch',exact:true})).toBeVisible();
   await page.getByRole('button',{name:'Import as fresh copy and switch',exact:true}).click();await expect.poll(async()=>(await state()).settings.portable_origin).toBe('untrusted_manual_copy');
   await page.reload();await expect(page.getByRole('button',{name:'Use my own data',exact:true})).toBeVisible();const s=await state();assert.equal(s.tasks[0].progress.remaining_minutes,95);assert.equal(s.tasks[0].minutes,75);assert.equal(s.receipts.length,0);
 });
 // The seven-day control is in Week and Recovery; choose the navigation label observed in the app.
 const names=await page.getByRole('button').allTextContents();await fs.writeFile(path.join(folder,'button-labels.json'),JSON.stringify(names));
 await page.screenshot({path:path.join(folder,'own-review.png'),fullPage:true});
 await step('languages_and_responsive_aa',async()=>{
   const results=[];
   for(const language of ['en','ru','kk'])for(const width of [390,768,1280,1440]){
     await page.setViewportSize({width,height:1000});await page.locator('[aria-label="Language"],[aria-label="Язык"],[aria-label="Тіл"]').first().selectOption(language);
     await expect.poll(()=>page.locator('html').getAttribute('lang')).toBe(language);
     assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),'page overflow '+language+'/'+width);
     const a11y=await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa']).analyze();assert.equal(a11y.violations.length,0,JSON.stringify(a11y.violations.map(v=>({id:v.id,nodes:v.nodes.length}))));
     await page.screenshot({path:path.join(folder,`${language}-${width}.png`),fullPage:true});results.push({language,width,aa_violations:0});
   }return results;
 });
 await step('visitor_isolation',async()=>{const other=await browser.newContext({baseURL:base});const p=await other.newPage();await p.goto('/');await expect(p.getByRole('button',{name:'Use my own data',exact:true})).toBeVisible();const s=await (await p.request.get('/api/state')).json();assert.equal(s.sources.length,0);const foreign=await p.request.get('/api/sources/'+(await state()).sources[0].id);assert.equal(foreign.status(),403);await other.close();});
 console.log(JSON.stringify(proof,null,2));
}catch(e){await page.screenshot({path:path.join(folder,'failure.png'),fullPage:true});console.error(String(e));process.exitCode=1;}finally{await browser.close();}
