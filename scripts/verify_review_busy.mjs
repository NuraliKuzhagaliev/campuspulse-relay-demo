import {chromium,expect} from '@playwright/test';import assert from 'node:assert/strict';import fs from 'node:fs/promises';import path from 'node:path';
const browser=await chromium.launch({headless:true});const proof={at:new Date().toISOString(),base:'http://127.0.0.1:8028',provider_calls:0,passed:false};
try{
 const context=await browser.newContext({baseURL:proof.base}),page=await context.newPage();await page.goto('/');await expect(page.getByRole('button',{name:'Use my own data',exact:true})).toBeVisible();
 await page.locator('input[type=file]').first().setInputFiles(path.resolve('public/samples/01-original.md'));await expect(page.getByText('01-original.md',{exact:true}).first()).toBeVisible();
 await page.getByRole('button',{name:'Review extracted fields',exact:true}).click();const form=page.getByTestId('review-entity');await expect(form).toBeVisible();await expect(page.locator('.working')).toHaveCount(0);
 await form.getByLabel('I reviewed this assignment and confirm only these fields.').check();
 let release,observed;const held=new Promise(r=>release=r),started=new Promise(r=>observed=r);
 await page.route('**/api/extraction-proposals',async route=>{observed();await held;await route.continue();});
 await page.getByRole('button',{name:'Refresh proposals',exact:true}).click();await started;
 await expect(form.getByRole('button',{name:'Confirm this assignment',exact:true})).toBeDisabled();proof.confirm_disabled_during_pending_refresh=true;
 release();await expect(form.getByRole('button',{name:'Confirm this assignment',exact:true})).toBeEnabled();
 const response=page.waitForResponse(r=>/\/confirm$/.test(new URL(r.url()).pathname));await form.getByRole('button',{name:'Confirm this assignment',exact:true}).click();assert((await response).ok());
 await expect(form).toHaveCount(0);const s=await(await page.request.get('/api/state')).json();assert.equal(s.tasks[0].extraction_origin,'confirmed_semantic_proposal');proof.confirmation_saved_after_refresh=true;proof.passed=true;
}catch(e){proof.error=String(e);process.exitCode=1;}finally{await browser.close();await fs.writeFile('docs/evidence/audit-review-busy.json',JSON.stringify(proof,null,2));console.log(JSON.stringify(proof));}
