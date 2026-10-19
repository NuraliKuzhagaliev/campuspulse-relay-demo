/** Installed Electron -> native restricted IPC -> real public Gemini/MCP.
 * No native dialogs/notifications are invoked or substituted in this check.
 */
import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import asar from '@electron/asar';
import {_electron as electron,expect} from '@playwright/test';
const [url,invites,index='3',resumeProfile]=process.argv.slice(2);
assert(url==='https://campuspulse-relay-demo.onrender.com'&&invites);
const token=JSON.parse(await fs.readFile(invites,'utf8')).invitations[Number(index)].token;
const root=process.cwd(),id=Date.now().toString(36),folder=path.join(root,'.local/final-desktop-hosted',id);
await fs.mkdir(folder,{recursive:true});
const profile=resumeProfile||path.join(folder,'profile'),executable=path.join(root,'installed/CampusPulse RELAY/CampusPulse RELAY.exe');
assert.match(profile,/^D:/i);
const env={...process.env,RELAY_DESKTOP_DATA:profile,RELAY_GATEWAY_URL:url};delete env.ELECTRON_RUN_AS_NODE;
const proof={checked_at:new Date().toISOString(),url,version:'0.4.0',executable,profile,checks:{},real_native_picker:false,native_picker_substitution:false,notification_visibility_checked:false,calendar:'illustrative_only'};
const out=`docs/evidence/final-desktop-hosted-${id}.json`;
proof.packaged_files=[];
const archive=path.join(path.dirname(executable),'resources/app.asar');
for(const name of asar.listPackage(archive).map(n=>n.slice(1)).filter(n=>/^(desktop[\\/].*\.cjs|dist[\\/].*\.(js|html|css))$/.test(n))){
 const bytes=asar.extractFile(archive,name);assert(bytes.equals(await fs.readFile(name)),name);
 proof.packaged_files.push({file:name,sha256:crypto.createHash('sha256').update(bytes).digest('hex'),matches_current_source:true});
}
let app;
try{
 app=await electron.launch({executablePath:executable,cwd:root,env,timeout:45000});let page=await app.firstWindow();
 if(!resumeProfile){
 await page.getByText('Use a private AI invitation',{exact:true}).click();
 await page.getByLabel('Owner-issued one-use judge invitation').fill(token);
 await page.getByRole('button',{name:'Open isolated demo',exact:true}).click();
 }
 await expect(page.locator('.live-access input[type=checkbox]')).toBeVisible({timeout:45000});
 const call=(route,method='GET',body)=>page.evaluate(async({route,method,body})=>window.relay.request('/api'+route,method,body),{route,method,body});
 const security=await app.evaluate(({app,BrowserWindow})=>({version:app.getVersion(),path:app.getPath('userData'),prefs:BrowserWindow.getAllWindows()[0].webContents.getLastWebPreferences()}));
 assert.equal(security.version,'0.4.0');assert.equal(security.path,profile);assert.equal(security.prefs.nodeIntegration,false);assert(security.prefs.contextIsolation&&security.prefs.sandbox);
 proof.checks.installed_package_and_D_profile=true;
 const health=await call('/health');assert.equal(health.version,'0.4.0');assert.equal(health.mode,'alternative_live');proof.health=health;
 const marker=crypto.randomBytes(4).toString('hex'),name=`desktop-optics-${marker}.md`;
 const text=`Assignment: Desktop optics ${marker}\nCourse: Optics\nTerm: Autumn 2026\nAssignment ID: desktop-${marker}\nDue: 2026-10-24T18:00:00+05:00\nEffort: 60 minutes\nRubric:\n- [ ] Explain wavelength uncertainty ${marker}\n`;
 // Exact native import request and subsequent state refresh; file selection is a separate human gate.
 const imported=await call('/import-native','POST',{name,content:Buffer.from(text).toString('base64')});
 const state=await call('/state');assert(state.sources.some(s=>s.id===imported.id||s.filename===name));
 const source=state.sources.find(s=>s.filename===name);assert(source);assert.equal((await call('/sources/'+source.id)).pages[0].text.trim(),text.trim());
 const tenant=state.workspace_id;proof.checks.real_import_request_and_exact_readback=true;
 await page.reload();await page.locator('.live-access input[type=checkbox]').check();
 await page.locator('.assistant input[maxlength="6000"]').fill(`Read my new Desktop optics ${marker} source. Quote its exact deadline and rubric item with source/page citations. Is this the alternative host or managed Agent Engine? Do not write to Calendar.`);
 await page.locator('.assistant > form button').click();
 await expect(page.locator('.answer pre')).toContainText(marker,{timeout:110000});
 const answer=await page.locator('.answer pre').innerText();
 assert(/2026-10-24|24.*October|October.*24/i.test(answer));assert(/wavelength uncertainty/i.test(answer));
 const conversation=await call('/conversation');assert.equal(conversation.turns.at(-1).status,'complete');
 const after=await call('/state');assert(after.events.some(e=>e.type==='tool_finished'&&e.tool==='read_course_source'));
 proof.checks.actual_installed_UI_to_public_gemini_MCP=true;proof.answer=answer;proof.run_id=conversation.turns.at(-1).run_id;proof.gateway_revision=health.deployed_commit;
 await page.screenshot({path:path.join(folder,'installed-public-gemini.png'),fullPage:true});
 await app.close();app=null;
 app=await electron.launch({executablePath:executable,cwd:root,env});page=await app.firstWindow();
 await expect(page.locator('.live-access input[type=checkbox]')).not.toBeChecked();
 const reopened=await page.evaluate(()=>window.relay.request('/api/state'));assert.equal(reopened.workspace_id,tenant);assert(reopened.sources.some(s=>s.filename===name));
 const reopenedConversation=await page.evaluate(()=>window.relay.request('/api/conversation'));assert.equal(reopenedConversation.id,conversation.id);assert.equal(reopenedConversation.turns.at(-1).assistant,answer);
 proof.checks.reopen_keeps_hosted_workspace_and_conversation=true;
 await page.getByRole('button',{name:'Start a fresh demo',exact:true}).click();
 await expect(page.getByRole('button',{name:'Enter public demo',exact:true})).toBeVisible();
 const reset=await page.evaluate(()=>window.relay.request('/api/state'));assert.notEqual(reset.workspace_id,tenant);assert(!reset.settings.ai_access);
 await page.getByRole('button',{name:'Enter public demo',exact:true}).click();
 // A new mutation must use the refreshed native CSRF, not the retired session's token.
 await page.evaluate(()=>window.relay.request('/api/preferences','POST',{timezone:'Asia/Almaty'}));
 proof.checks.native_reset_rotates_workspace_and_csrf=true;proof.passed=true;
}catch(error){proof.passed=false;proof.error=String(error).replaceAll(token,'[private invitation redacted]');process.exitCode=1;}
finally{if(app)await app.close();await fs.writeFile(out,JSON.stringify(proof,null,2));console.log(JSON.stringify({passed:proof.passed,evidence:out}));}
