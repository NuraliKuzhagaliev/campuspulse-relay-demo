/** Real installed package, authenticated restricted IPC and renderer. No native-picker visibility claim. */
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import asar from '@electron/asar';
import {_electron as electron,expect} from '@playwright/test';
const root=process.cwd(), version=JSON.parse(await fs.readFile('package.json','utf8')).version;
const executable=path.join(root,'installed/CampusPulse RELAY/CampusPulse RELAY.exe');
const profile=path.join(root,'.local/desktop-contract',version+'-'+Date.now().toString(36));
const env={...process.env,RELAY_DESKTOP_DATA:profile};delete env.ELECTRON_RUN_AS_NODE;
const proof={version,checked_at:new Date().toISOString(),executable,profile,checks:{},packaged_files:[],native_picker_used:false,native_picker_substituted:false,native_visibility_checked:false,cloud_calls:0,calendar:'illustrative'};
const archive=path.join(path.dirname(executable),'resources/app.asar');
for(const filename of asar.listPackage(archive).map(n=>n.slice(1)).filter(n=>/^(desktop[\\/].*\.cjs|dist[\\/].*\.(js|html|css))$/.test(n))){
  const bytes=asar.extractFile(archive,filename),source=await fs.readFile(filename);
  assert(bytes.equals(source),filename);proof.packaged_files.push({file:filename,sha256:crypto.createHash('sha256').update(bytes).digest('hex'),matches_current_source:true});
}
let app;
try{
  app=await electron.launch({executablePath:executable,cwd:root,env,timeout:30000});let page=await app.firstWindow();
  await page.getByRole('button',{name:'Explore illustrative workspace'}).click();
  const call=(route,method='GET',body)=>page.evaluate(async({route,method,body})=>window.relay.request('/api'+route,method,body),{route,method,body});
  const security=await app.evaluate(({app,BrowserWindow})=>({version:app.getVersion(),path:app.getPath('userData'),prefs:BrowserWindow.getAllWindows()[0].webContents.getLastWebPreferences()}));
  assert.equal(security.version,version);assert.equal(security.prefs.nodeIntegration,false);assert.equal(security.prefs.contextIsolation,true);assert.equal(security.prefs.sandbox,true);assert.match(security.path,/^D:/i);
  proof.checks.secure_installed_package=true;
  let state=await call('/state');const tenant=state.workspace_id;
  const conflict=state.conflicts[0];await call('/conflicts/'+conflict.id+'/resolve','POST',{fact_id:conflict.facts.toSorted((a,b)=>a.value.localeCompare(b.value))[0].id});
  const task=state.tasks.find(t=>t.title==='ML report');
  await call('/tasks/'+task.id+'/settings','POST',{minutes:task.minutes+30});
  assert.equal((await call('/packets/'+task.id)).task.minutes,task.minutes+30);
  await call('/tasks/'+task.id+'/settings','POST',{minutes:task.minutes});
  let plan=await call('/plan','POST');assert(plan.feasible);
  const scenario=await call('/scenario','POST',{remove_weekday:2});assert(!scenario.feasible);assert.equal((await call('/state')).plan.id,plan.id);
  const date=(day,hour)=>{const d=new Date(state.settings.anchor+'T00:00:00Z');d.setUTCDate(d.getUTCDate()+day);return d.toISOString().slice(0,10)+`T${hour}:00:00+05:00`};
  const rescue=await call('/rescue','POST',{scenario:{remove_weekday:2},additions:[{start:date(1,'16'),end:date(1,'17')},{start:date(4,'17'),end:date(4,'18')}]});
  assert.equal(rescue.bottlenecks.total_shortage_minutes,120);assert(rescue.minimum_proven);
  plan=await call('/rescues/'+rescue.id+'/choose','POST',{remedy_id:rescue.remedies[0].id});assert(plan.feasible);
  const preview=await call('/plans/'+plan.id+'/preview','POST');const receipt=await call('/previews/'+preview.id+'/approve','POST',{digest:preview.digest});
  assert.equal(receipt.status,'verified');assert.equal(receipt.mode,'illustrative');
  assert((await call('/receipts/'+receipt.id+'/verify','POST')).results.every(r=>r.matches));
  assert((await call('/receipts/'+receipt.id+'/undo','POST')).results.every(r=>['removed','preserved_existing'].includes(r.status)));
  proof.checks.task_packet_plan_scenario_rescue_approval_verify_undo=true;
  const source=await call('/sources/security-pdf');assert(source.pages.length);
  assert.equal((await call('/export')).workspace_id,tenant);
  const convo=await call('/conversation');assert.notEqual((await call('/conversation/new','POST')).id,convo.id);
  proof.checks.source_export_conversation_reset=true;
  const text=`Assignment: Submission contract\nCourse: Contract course\nTerm: Verification ${version}\nAssignment ID: submission\nDue: ${date(4,'18')}\nEffort: 60 minutes\nFilename: submission-*.md\nSections: Method;Results\n- [ ] Explain experimental validity`;
  const imported=await call('/import-native','POST',{name:'submission-contract.md',content:Buffer.from(text).toString('base64')});
  const draft=await call('/preflight','POST',{name:'submission-check.md',content:Buffer.from('# Method\nTest method.\n# Results\nObserved facts.').toString('base64'),task_id:imported.drafts[0].id});
  assert.equal(draft.missing_count,0);assert(draft.results.some(r=>r.status==='needs_review'));
  proof.checks.preflight_json_contract=true;
  const missing=await call('/preflight','POST',{name:'wrong.md',content:Buffer.from('# Method\n# Results\nObserved facts.').toString('base64'),task_id:imported.drafts[0].id});
  assert(missing.missing_count>0);
  const base2=await call('/plan','POST');
  const extra=await call('/preflights/'+missing.id+'/recovery','POST',{extra_minutes:30});
  assert.equal(extra.required_minutes,base2.required_minutes+30);assert.equal((await call('/state')).plan.id,base2.id);
  proof.checks.preflight_missing_work_recovery_validated=true;
  await page.reload();await page.getByRole('button',{name:'Judge challenge',exact:true}).click();
  for(const [lang,title] of [['en','Judge challenge'],['ru','Испытание для жюри'],['kk','Қазылар сынағы']]){
    await page.getByTestId('language').selectOption(lang);await expect(page.getByRole('heading',{name:title,level:1})).toBeVisible();
    await app.evaluate(({BrowserWindow})=>BrowserWindow.getAllWindows()[0].setSize(1024,768));
    assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
  }
  await page.screenshot({path:`docs/screenshots/desktop-${version}-1024.png`});
  await app.close();app=null;
  app=await electron.launch({executablePath:executable,cwd:root,env});page=await app.firstWindow();
  await expect(page.locator('html')).toHaveAttribute('lang','kk');
  assert.equal((await page.evaluate(()=>window.relay.request('/api/state'))).workspace_id,tenant);
  proof.checks.locale_and_workspace_persist_after_reopen=true;
  proof.passed=true;
}finally{if(app)await app.close();await fs.writeFile(`docs/evidence/desktop-contract-${version}.json`,JSON.stringify(proof,null,2));}
console.log(JSON.stringify(proof,null,2));
