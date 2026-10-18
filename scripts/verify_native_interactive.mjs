/** Installed-app observation harness. No dialog/Notification overrides and no OS input automation. */
import fs from "node:fs/promises";
import path from "node:path";
import assert from "node:assert/strict";
import { _electron as electron } from "playwright";

const root=process.cwd(), version=JSON.parse(await fs.readFile("package.json","utf8")).version;
const arg=(name)=>{const i=process.argv.indexOf(name);return i>=0?process.argv[i+1]:null;};
const run=Date.now().toString(36), folder=path.join(root,".local","native-verification",version+"-"+run);
const profile=path.resolve(arg("--profile")||path.join(folder,"profile")), fixture=path.resolve(arg("--fixture")||path.join(folder,"native-picker-"+run+".md"));
for(const file of [profile,fixture])assert(file.toLowerCase().startsWith(path.join(root,".local/native-verification").toLowerCase()+path.sep));
await fs.mkdir(profile,{recursive:true});
let contents;
try{contents=await fs.readFile(fixture,"utf8");}catch{contents=`Assignment: Native picker check ${run}\nCourse: RELAY local verification\nDue: 2026-11-12T18:00:00+05:00\nEffort: 60 minutes\nRubric:\n- [ ] Confirm import through the real unmodified Windows picker\n`;await fs.writeFile(fixture,contents,"utf8");}
const output=path.join(root,"docs/evidence/desktop-native-interactive.json");
let previous={};
try{previous=JSON.parse(await fs.readFile("docs/evidence/desktop-native-result.json","utf8"));}catch{}
const proof={version,checked_at:new Date().toISOString(),status:"awaiting_human_interaction",executable:path.join(root,"installed","CampusPulse RELAY","CampusPulse RELAY.exe"),profile,fixture,
  picker:{unmodified:true,opened:false,appearance_confirmed_by_user:previous.profile===profile&&previous.picker?.appearance_confirmed_by_user===true,canceled:false,selected:false,exact_source_observed:false},
  import:{request_completed:false,state_refresh_completed:false,snapshot_saved:false},
  original_incident:previous.original_incident||null,
  notification:{dispatch_observed:false,os_show_event:false,actual_click_observed:false,visibility_verified:false},
  automation_helper:{available:false,error:"failed to write kernel assets (os error 3), repeated after kernel reset"},
  method:"Installed executable launched and observed read-only. Native picker input and notification click must be performed by the human; no API replacement or synthetic OS events.",
  no_cloud_calls:true,no_calendar_writes:true};
const save=async()=>{await fs.writeFile(output+".tmp",JSON.stringify(proof,null,2));await fs.rename(output+".tmp",output);};
const logs=async(name)=>{
  try{return (await fs.readFile(path.join(profile,"logs",name),"utf8")).trim().split("\n").filter(Boolean).map(x=>JSON.parse(x));}catch{return [];}
};
await save();
const environment={...process.env,RELAY_DESKTOP_DATA:profile};delete environment.ELECTRON_RUN_AS_NODE;
const app=await electron.launch({executablePath:proof.executable,cwd:root,env:environment,timeout:30000});
const window=await app.firstWindow();
const installed=await app.evaluate(({app,BrowserWindow})=>({version:app.getVersion(),preferences:BrowserWindow.getAllWindows()[0].webContents.getLastWebPreferences(),data:app.getPath("userData")}));
assert.equal(installed.version,version);assert.equal(installed.preferences.contextIsolation,true);assert.equal(installed.preferences.sandbox,true);assert.equal(installed.preferences.nodeIntegration,false);assert.match(installed.data,/^D:/i);
console.log(JSON.stringify({status:"ready_for_your_interaction",version,fixture,steps:[
  "In the installed app, enter Explore illustrative workspace, then Connections.",
  "Click Import a file. Confirm the real Windows picker appears, then click Cancel.",
  "Click Import a file again. Paste the fixture path into File name and click Open. The source library should show the unique native-picker filename.",
  "Return to Connections and click Send test notification. Click the actual Windows notification banner or its entry in Notification Center.",
  "Do not change Windows security/privacy settings or connect Google. Tell Codex whether the native picker and notification were visible."
]},null,2));
const deadline=Date.now()+30*60*1000;
try {
  while(Date.now()<deadline){
    const pick=await logs("native-picker.jsonl"), events=await logs("native-notifications.jsonl"), trace=await logs("desktop-trace.jsonl");
    proof.rejected_requests=trace.filter(e=>e.stage==="request-rejected");
    proof.import.request_completed=trace.some(e=>e.stage==="import-request-completed");
    proof.import.state_refresh_completed=trace.some(e=>e.stage==="state-refresh-completed");
    proof.import.snapshot_saved=trace.some(e=>e.stage==="snapshot-save-completed");
    proof.picker.opened=pick.some(e=>e.event==="opened");
    proof.picker.canceled=pick.some(e=>e.event==="canceled");
    proof.picker.selected=pick.some(e=>e.event==="selected");
    if(proof.picker.selected&&proof.import.snapshot_saved&&!proof.picker.exact_source_observed){
      try {
        const data=await window.evaluate(()=>window.relay.request("/api/state"));
        const source=data.sources.find(s=>s.filename===path.basename(fixture));
        if(source){
          const full=await window.evaluate(id=>window.relay.request("/api/sources/"+id),source.id);
          proof.picker.exact_source_observed=full.pages.some(p=>p.text===contents);
          proof.picker.source_id=source.id;
        }
      } catch {}
    }
    proof.notification.dispatch_observed=events.some(e=>e.event==="dispatch-requested");
    proof.notification.os_show_event=events.some(e=>e.event==="os-show-event");
    proof.notification.actual_click_observed=events.some(e=>e.event==="clicked");
    proof.notification.visibility_verified=proof.notification.actual_click_observed;
    try{
      const observation=JSON.parse(await fs.readFile(path.join(profile,"human-observation.json"),"utf8"));
      if(observation.profile===profile&&observation.notification_visible===true){
        proof.notification.visibility_verified=true;
        proof.notification.visibility_basis="explicit_user_observation";
        proof.notification.location=observation.notification_location;
        proof.human_observation=observation;
      }
    }catch{}
    const done=proof.picker.canceled&&proof.picker.selected&&proof.picker.exact_source_observed&&proof.notification.visibility_verified;
    if(done){proof.status="passed_with_human_interaction";proof.completed_at=new Date().toISOString();await save();console.log("Native picker cancel/import and actual notification visibility verified by native click or explicit human observation. No visibility claim derives from dispatch alone.");break;}
    await save();await new Promise(resolve=>setTimeout(resolve,1000));
  }
  if(proof.status!=="passed_with_human_interaction"){
    proof.status="human_checks_pending";proof.pending=[...(!proof.picker.exact_source_observed?["Use the actual native picker to import the exact fixture."]:[]),...(!proof.picker.canceled?["Cancel the native picker once."]:[]),...(!proof.notification.actual_click_observed?["Observe and click the actual Windows notification banner or Notification Center entry."]:[])];
  }
} finally {await save();await app.close();console.log(output);}
