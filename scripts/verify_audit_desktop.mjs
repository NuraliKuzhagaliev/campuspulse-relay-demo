/** Installed 0.5.0 public-session/import/poll-policy/reset contracts. Zero model calls.
 * No native Open/Save dialog or notification visibility is claimed.
 */
import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import asar from '@electron/asar';
import {_electron as electron,expect} from '@playwright/test';
const root=process.cwd(),id=Date.now().toString(36),profile=path.join(root,'.local/public-ai-desktop',id,'profile');
const executable=path.join(root,'installed/CampusPulse RELAY/CampusPulse RELAY.exe');
const env={...process.env,RELAY_DESKTOP_DATA:profile,RELAY_GATEWAY_URL:'https://campuspulse-relay-demo.onrender.com'};delete env.ELECTRON_RUN_AS_NODE;
const proof={checked_at:new Date().toISOString(),version:'0.5.0',model_calls:0,real_calendar_writes:0,native_dialog_visibility_checked:false,notification_visibility_checked:false,checks:{},packaged_files:[]};
const archive=path.join(path.dirname(executable),'resources/app.asar');
for(const name of asar.listPackage(archive).map(n=>n.slice(1)).filter(n=>/^(desktop[\\/].*\.cjs|dist[\\/].*\.(js|html|css))$/.test(n))){
 const bytes=asar.extractFile(archive,name);assert(bytes.equals(await fs.readFile(name)),name);
 proof.packaged_files.push({file:name,sha256:crypto.createHash('sha256').update(bytes).digest('hex'),matches_current_source:true});
}
let app;
try{
 app=await electron.launch({executablePath:executable,cwd:root,env,timeout:45000});let page=await app.firstWindow();
 await expect(page.locator('.live-access input[type=checkbox]')).toBeVisible({timeout:45000});
 await expect(page.getByText('Use a private AI invitation',{exact:true})).toHaveCount(0);
 await expect(page.getByRole('link',{name:'Sample documents and instructions',exact:true})).toHaveAttribute('href','https://campuspulse-relay-demo.onrender.com/samples/');
 const security=await app.evaluate(({app,BrowserWindow})=>({version:app.getVersion(),profile:app.getPath('userData'),prefs:BrowserWindow.getAllWindows()[0].webContents.getLastWebPreferences()}));
 assert.equal(security.version,'0.5.0');assert.equal(security.profile,profile);assert(security.prefs.sandbox&&security.prefs.contextIsolation&&!security.prefs.nodeIntegration);
 proof.checks.package_matches_source_and_sandboxed_D_profile=true;
 const call=(route,method='GET',body)=>page.evaluate(({route,method,body})=>window.relay.request('/api'+route,method,body),{route,method,body});
 let state=await call('/state');const tenant=state.workspace_id;assert(state.agent.public_access&&!state.settings.calendar_live);
 proof.deployed_commit=(await call('/health')).deployed_commit;
 const text='Assignment: Installed public contract\nCourse: Optics\nTerm: Autumn 2026\nAssignment ID: installed-public\nDue: 2026-10-24T18:00:00+05:00\nEffort: 30 minutes\n- [ ] Explain the observed aberration';
 const source=await call('/import-native','POST',{name:'installed-public-contract.md',content:Buffer.from(text).toString('base64')});
 assert.equal((await call('/sources/'+source.id)).pages[0].text,text);
 assert((await call('/state')).sources.some(s=>s.id===source.id));
 proof.checks.native_import_request_readback_and_refresh=true;
 let rejected='';try{await call('/runs/'+'a'.repeat(32));}catch(e){rejected=String(e);}
 assert(rejected.includes('ACCESS_DENIED')&&!rejected.includes('Unsupported application request'));
 proof.checks.poll_route_reaches_tenant_authorization_not_IPC_rejection=true;
 await app.close();app=null;app=await electron.launch({executablePath:executable,cwd:root,env});page=await app.firstWindow();
 await expect(page.locator('.live-access input[type=checkbox]')).toBeVisible();
 state=await page.evaluate(()=>window.relay.request('/api/state'));assert.equal(state.workspace_id,tenant);assert(state.sources.some(s=>s.id===source.id));
 proof.checks.reopen_keeps_own_workspace=true;
 await page.getByRole('button',{name:'Start a fresh demo',exact:true}).click();
 await expect(page.locator('.working')).toHaveCount(0);
 await expect.poll(async()=>{
   try{return await page.evaluate(()=>window.relay.request('/api/state').then(s=>s.workspace_id));}
   catch(e){if(String(e).includes('AUTH_REQUIRED'))return tenant;throw e;}
 }).not.toBe(tenant);
 await expect(page.getByRole('button',{name:'Enter public demo',exact:true})).toHaveCount(0);
 await page.evaluate(()=>window.relay.request('/api/preferences','POST',{timezone:'Asia/Almaty'}));
 proof.checks.reset_rotates_workspace_and_native_CSRF_without_entry_gate=true;
 proof.passed=true;
}catch(e){proof.passed=false;proof.error=String(e);process.exitCode=1;}
finally{if(app)await app.close();await fs.writeFile('docs/evidence/audit-desktop-0.5.0.json',JSON.stringify(proof,null,2));console.log(JSON.stringify({passed:proof.passed,evidence:'docs/evidence/audit-desktop-0.5.0.json'}));}
