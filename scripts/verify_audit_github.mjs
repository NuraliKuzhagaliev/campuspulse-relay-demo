/** Live hosted GitHub read and browser-independent polling, zero model calls. */
import fs from 'node:fs/promises';import path from 'node:path';import assert from 'node:assert/strict';
import {chromium,request,expect} from '@playwright/test';
const base='https://campuspulse-relay-demo.onrender.com',folder=path.resolve('.local/audit-github');await fs.mkdir(folder,{recursive:true});
const file=path.join(folder,'private-check.json'),cookie=path.join(folder,'private-session.json');
if(process.argv.includes('--finish')){
 const proof=JSON.parse(await fs.readFile(file,'utf8'));assert(Date.now()-Date.parse(proof.browser_closed_at)>75000,'Allow at least one server poll interval');
 const api=await request.newContext({baseURL:base,storageState:cookie});const health=await(await api.get('/api/health')).json();assert.equal(health.deployed_commit,proof.deployed_commit);
 const state=await(await api.get('/api/state')).json();assert(state.settings.watch_enabled);assert(Date.parse(state.freshness.last_observation_at)>Date.parse(proof.browser_closed_at));assert.equal(state.freshness.commit,proof.initial_commit);assert.equal(state.freshness.source_fetched_at,proof.original_source_fetched_at);
 proof.latest_freshness=state.freshness;proof.server_observation_without_browser=true;proof.immutable_source_time_preserved=true;proof.passed=true;proof.checked_at=new Date().toISOString();await fs.writeFile('docs/evidence/audit-hosted-github.json',JSON.stringify(proof,null,2));await api.dispose();console.log(JSON.stringify(proof));
}else{
 const health=await(await fetch(base+'/api/health')).json();if(process.env.RELAY_EXPECTED_DEPLOY_COMMIT)assert.equal(health.deployed_commit,process.env.RELAY_EXPECTED_DEPLOY_COMMIT);
 const browser=await chromium.launch({headless:true}),context=await browser.newContext({baseURL:base}),page=await context.newPage();
 try{await page.goto('/',{timeout:90000});await expect(page.getByRole('button',{name:'Connections',exact:true})).toBeVisible();await page.getByRole('button',{name:'Connections',exact:true}).click();
 const pending=page.waitForResponse(r=>new URL(r.url()).pathname==='/api/sync'&&r.request().method()==='POST');await page.getByRole('button',{name:'Fetch live course source',exact:true}).click();const response=await pending;const value=await response.json();assert(response.ok(),'Live upstream read failed: '+(value.error?.code||response.status()));
 const s=await(await page.request.get('/api/state')).json(),source=s.sources.find(x=>x.id==='github-coursework');assert(source?.mode==='live_github');assert.equal(source.remote.commit,value.commit);assert(/^[a-f0-9]{40}$/.test(value.commit));
 const watching=page.waitForResponse(r=>new URL(r.url()).pathname==='/api/preferences'&&r.request().method()==='POST');await page.getByRole('checkbox',{name:/Poll every/}).check();assert((await watching).ok());
 await context.storageState({path:cookie});await page.screenshot({path:path.join(folder,'live-github.png'),fullPage:true});
 const proof={at:new Date().toISOString(),deployed_commit:health.deployed_commit,url:base,upstream:'actual GitHub REST from hosted backend',initial_commit:value.commit,original_source_fetched_at:s.freshness.source_fetched_at,initial_freshness:s.freshness,manual_ui_read:true,watch_enabled:true,provider_calls:0,google_writes:0,background_pending:true,limitations:'Free hosting polls only while awake. Cached observations preserve original fetch time; a poll is not claimed a fresh download.'};
 await browser.close();proof.browser_closed_at=new Date().toISOString();await fs.writeFile(file,JSON.stringify(proof,null,2));console.log(JSON.stringify({started:true,browser_closed_at:proof.browser_closed_at,initial_commit:value.commit,finish_command:'node scripts/verify_audit_github.mjs --finish'}));
 }catch(error){await browser.close();throw error;}
}
