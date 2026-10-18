import fs from "node:fs/promises";
const live="docs/evidence/desktop-native-interactive.json", output="docs/evidence/desktop-native-result.json";
const previous=JSON.parse(await fs.readFile(output,"utf8"));
const current=JSON.parse(await fs.readFile(live,"utf8"));
if(current.profile!==previous.profile)throw new Error("Native verification workspace changed.");
try{
  const observation=JSON.parse(await fs.readFile(current.profile+"/human-observation.json","utf8"));
  if(observation.profile===current.profile){
    current.human_observation=observation;
    current.picker.import_confirmed_by_user=observation.import_confirmed===true;
    if(observation.notification_visible===true){
      current.notification.visibility_verified=true;
      current.notification.visibility_basis="explicit_user_observation";
      current.notification.location=observation.notification_location;
    }
  }
}catch{}
current.original_incident=previous.original_incident;
current.observed_through=(await fs.stat(live)).mtime.toISOString();
if(current.picker.exact_source_observed&&!current.notification.visibility_verified)
  current.status="native_import_verified_notification_pending";
if(current.picker.exact_source_observed&&current.notification.visibility_verified)
  current.status="passed_with_human_interaction";
try{current.import_trace=(await fs.readFile(current.profile+"/logs/desktop-trace.jsonl","utf8")).trim().split("\n").filter(Boolean).map(JSON.parse);}catch{current.import_trace=[];}
try{current.notification_trace=(await fs.readFile(current.profile+"/logs/native-notifications.jsonl","utf8")).trim().split("\n").filter(Boolean).map(JSON.parse);}catch{current.notification_trace=[];}
current.recheck_required=[...(!current.picker.exact_source_observed?["Import the exact fixture using the real native dialog in the same workspace."]:[]),...(!current.notification.visibility_verified?["Observe and click the actual Windows banner or Notification Center entry; report where it appeared."]:[])];
await fs.writeFile(output,JSON.stringify(current,null,2)+"\n");
console.log(JSON.stringify({status:current.status,picker:current.picker,import:current.import,notification:current.notification}));
