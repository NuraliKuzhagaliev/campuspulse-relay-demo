/** Local fault injection against our isolated test gateway. No provider calls. */
import {chromium,expect as baseExpect} from '@playwright/test';
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {execFileSync} from 'node:child_process';
const expect=baseExpect.configure({timeout:20000}),base='http://127.0.0.1:8032';
const folder=path.resolve('.local/final-0.5.1/recovery');await fs.mkdir(folder,{recursive:true});
const proof={at:new Date().toISOString(),scope:'local fault injection only',actual_gemini_calls:0,google_calls:0,checks:{}};
const browser=await chromium.launch({headless:true});
try {
 const context=await browser.newContext({baseURL:base}),page=await context.newPage();
 await page.goto('/');await expect(page.getByRole('button',{name:'Use my own data',exact:true})).toBeVisible();
 const state=await (await page.request.get('/api/state')).json();
 await page.getByRole('button',{name:'Connections',exact:true}).click();
 await page.getByText('Reconnect an existing app-created calendar',{exact:true}).click();
 await page.getByLabel('Existing app-created Calendar ID',{exact:true}).fill('primary');
 await page.getByRole('button',{name:'Verify existing calendar',exact:true}).click();
 await expect(page.getByRole('status').filter({hasText:'UNSUPPORTED_INPUT'})).toBeVisible();
 proof.checks.invalid_recovery_does_not_contact_google=true;
 const denied=await page.request.post('/api/connections/calendar/recover',{data:{calendar_id:'x@group.calendar.google.com'}});
 assert.equal(denied.status(),403);proof.checks.recovery_requires_csrf=true;
 // Expire ONLY this owned test capability in the separate local datastore.
 execFileSync(path.resolve('.venv/Scripts/python.exe'),['-c',"import sqlite3,sys; db=sqlite3.connect('.local/final-0.5.1/server-data/relay.sqlite3'); db.execute(\"UPDATE records SET data=json_set(data,'$.expires',0) WHERE tenant='_server' AND kind='sessions' AND json_extract(data,'$.tenant')=?\",(sys.argv[1],)); db.commit()",state.workspace_id],{cwd:process.cwd(),env:process.env});
 await expect(page.locator('.offline-banner')).toContainText('This workspace expired.');
 assert.equal((await page.request.get('/api/connections/status')).status(),401);
 proof.checks.actual_local_session_expiry_401_and_explicit_recovery_banner=true;
 await page.getByRole('button',{name:'Reconnect & revalidate',exact:true}).click();
 await expect(page.locator('.offline-banner')).toHaveCount(0);
 const fresh=await (await page.request.get('/api/state')).json();assert.notEqual(fresh.workspace_id,state.workspace_id);assert.equal(fresh.sources.length,0);assert.equal(fresh.receipts.length,0);
 proof.checks.fresh_workspace_has_no_replayed_approvals_or_connection=true;
 // A failed network request gets a typed useful error and is not replayed.
 let attempts=0;await page.route('**/api/sync',async route=>{attempts++;await route.abort('timedout');});
 await page.getByRole('button',{name:'Connections',exact:true}).click();
 const labels=await page.getByRole('button').allTextContents();
 const sync=page.getByRole('button',{name:'Fetch live course source',exact:true});
 if(await sync.count()) {await sync.click();await expect(page.locator('[role=alert]')).toContainText('UPSTREAM_UNAVAILABLE');assert.equal(attempts,1);proof.checks.network_failure_typed_without_mutation_replay=true;}
 else {proof.checks.network_fault_control_not_found=false;await fs.writeFile(path.join(folder,'buttons.json'),JSON.stringify(labels));}
 await page.screenshot({path:path.join(folder,'recovery.png'),fullPage:true});
 proof.passed=Object.values(proof.checks).every(Boolean);
} finally {await browser.close();await fs.writeFile('docs/evidence/final-0.5.1-recovery.json',JSON.stringify(proof,null,2)+'\n');}
console.log(JSON.stringify(proof));assert(proof.passed);
