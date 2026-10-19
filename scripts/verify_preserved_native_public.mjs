/** Read original native workspace through the corrected installed app; no mutation. */
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {_electron as electron,expect} from '@playwright/test';
const root=process.cwd(),profile=path.join(root,'.local/native-verification/0.3.0-passport/profile');
const env={...process.env,RELAY_DESKTOP_DATA:profile,RELAY_GATEWAY_URL:'http://127.0.0.1:8000'};delete env.ELECTRON_RUN_AS_NODE;
const app=await electron.launch({executablePath:path.join(root,'installed/CampusPulse RELAY/CampusPulse RELAY.exe'),cwd:root,env});
try{
 const page=await app.firstWindow();await expect.poll(()=>page.evaluate(()=>!!window.relay)).toBe(true);
 const state=await page.evaluate(()=>window.relay.request('/api/state'));
 const additions=await page.evaluate(()=>window.relay.request('/api/additions'));
 const task=state.tasks.find(t=>t.title==='Web project');assert(task);
 const remaining=additions.progress.find(p=>p.id===task.id).remaining_minutes;
 const logged=additions.logs.filter(p=>p.task_id===task.id).reduce((n,p)=>n+p.duration_minutes,0);
 assert.equal(logged,45);assert.equal(remaining,95);
 const proof={checked_at:new Date().toISOString(),version:await app.evaluate(({app})=>app.getVersion()),profile,workspace_id:state.workspace_id,logged_minutes:logged,reported_remaining_minutes:remaining,source:'Original preserved native profile/datastore; corrected installed main/preload IPC read only',native_dialog_opened:false,native_dialog_substituted:false,notification_visibility_observed:false,model_calls:0,passed:true};
 await fs.writeFile('docs/evidence/preserved-native-0.4.1.json',JSON.stringify(proof,null,2));console.log(JSON.stringify(proof));
}finally{await app.close();}
