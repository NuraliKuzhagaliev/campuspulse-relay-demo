/** Reproduce both installed renderer import paths. Picker substitution is explicit;
 * this regression does not claim real native-picker or notification verification. */
import fs from "node:fs/promises";
import path from "node:path";
import assert from "node:assert/strict";
import crypto from "node:crypto";
import asar from "@electron/asar";
import { _electron as electron } from "playwright";

const root=process.cwd();
const environment={...process.env,RELAY_DESKTOP_DATA:path.join(root,".local/import-diagnostic",Date.now().toString(36))};
delete environment.ELECTRON_RUN_AS_NODE;
const fixture=path.join(root,".local/native-verification/0.1.1-mvebaaui/native-picker-mvebaaui.md");
const original=process.argv.includes("--expect-rejection");
const proof={checked_at:new Date().toISOString(),picker_substituted:true,requests:[],stages:[],packaged_files:[]};
const packed=path.join(root,"installed/CampusPulse RELAY/resources/app.asar");
for(const filename of asar.listPackage(packed).map(x=>x.slice(1)).filter(x=>/^(desktop\\(main|preload|request-policy)\.cjs|dist\\.*\.(js|html))$/.test(x))){
  const bytes=asar.extractFile(packed,filename);
  const current=await fs.readFile(filename).catch(()=>null);
  proof.packaged_files.push({file:filename,sha256:crypto.createHash("sha256").update(bytes).digest("hex"),matches_current_source:!!current&&bytes.equals(current)});
}
const app=await electron.launch({executablePath:path.join(root,"installed/CampusPulse RELAY/CampusPulse RELAY.exe"),cwd:root,env:environment});
try {
  // Preserve the installed handler and its sender/route validation. Observe only
  // method, redacted route and result; never retain arguments or response bodies.
  await app.evaluate(({ipcMain})=>{
    const original=ipcMain._invokeHandlers.get("relay:request");
    globalThis.importDiagnostic=[];
    ipcMain.removeHandler("relay:request");
    ipcMain.handle("relay:request",async(event,p,m,...rest)=>{
      const record={method:["GET","POST","DELETE"].includes(m)?m:"[redacted]",path:["/api/session","/api/state","/api/import-native","/api/import"].includes(p)?p:"[redacted]"};
      try {const value=await original(event,p,m,...rest);record.result="succeeded";return value;}
      catch(error){record.result=String(error).includes("Unsupported application request")?"allowlist-rejected":"gateway-or-other-failure";throw error;}
      finally {globalThis.importDiagnostic.push(record);}
    });
  });
  const window=await app.firstWindow();
  await window.getByRole("button",{name:"Explore illustrative workspace"}).click();
  await window.getByRole("button",{name:"Connections",exact:true}).click();
  await app.evaluate(({dialog})=>{dialog.showOpenDialog=async()=>({canceled:true,filePaths:[]});});
  await window.getByRole("button",{name:"Import a file",exact:true}).click();
  await window.waitForTimeout(200);
  proof.stages.push({path:"native-cancel",error:await window.locator(".diagnostic code").allTextContents()});
  assert.equal(await window.locator(".error-banner").count(),0);
  await app.evaluate(({dialog},fixture)=>{dialog.showOpenDialog=async()=>({canceled:false,filePaths:[fixture]});},fixture);
  await window.getByRole("button",{name:"Import a file",exact:true}).click();
  await window.getByText(path.basename(fixture),{exact:true}).waitFor();
  proof.stages.push({path:"native-selected-file",source_visible:true,error:await window.locator(".diagnostic code").allTextContents()});
  assert.equal(await window.locator(".error-banner").count(),0);
  const second=path.join(root,".local/tmp/input-route-diagnostic.md");
  await fs.writeFile(second,"Assignment: File input regression\nDue: 2026-11-13T18:00:00+05:00\nEffort: 30 minutes\n");
  await window.locator('input[type="file"]').setInputFiles(second);
  await window.waitForTimeout(500);
  proof.stages.push({path:"renderer-file-input",source_visible:await window.getByText(path.basename(second),{exact:true}).count()>0,error:await window.locator(".diagnostic code").allTextContents()});
  proof.requests=await app.evaluate(()=>globalThis.importDiagnostic);
  const rejected=proof.requests.filter(r=>r.result==="allowlist-rejected");
  if(original){
    assert.deepEqual(rejected,[{method:"POST",path:"/api/import",result:"allowlist-rejected"}]);
    assert.match(proof.stages.at(-1).error.join(" "),/Unsupported application request/);
    proof.conclusion="Renderer File input POST /api/import was rejected before upload. The native dialog import POST /api/import-native and following GET /api/state succeeded. The original human attempt lacked request tracing, so attribution of that incident remains unconfirmed.";
  } else {
    assert.deepEqual(rejected,[]);
    assert.equal(proof.stages.at(-1).source_visible,true);
    assert.deepEqual(proof.stages.at(-1).error,[]);
    // Read back actual source bytes through the installed preload and gateway.
    for(const name of [path.basename(fixture),path.basename(second)]){
      const exact=await window.evaluate(async(name)=>{
        const state=await window.relay.request("/api/state");
        const source=state.sources.find(s=>s.filename===name);
        const full=await window.relay.request("/api/sources/"+source.id);
        return full.pages.map(p=>p.text).join("\n");
      },name);
      assert.equal(exact,await fs.readFile(name===path.basename(fixture)?fixture:second,"utf8"));
    }
    // The rejected endpoint remains closed after the renderer fix.
    for(const [p,m] of [["/api/import","POST"],["/api/state","DELETE"],["/api/unknown?token=never-log-this","GET"]])
      assert.match(await window.evaluate(async([p,m])=>{try{await window.relay.request(p,m);return "unexpected success";}catch(e){return String(e);}},[p,m]),/Unsupported application request/);
    const trace=await fs.readFile(path.join(environment.RELAY_DESKTOP_DATA,"logs/desktop-trace.jsonl"),"utf8");
    assert(!trace.includes("never-log-this"));
    const rows=trace.trim().split("\n").map(JSON.parse);
    const nativeId=rows.find(r=>r.stage==="picker-selected").id;
    assert.deepEqual(rows.filter(r=>r.id===nativeId).map(r=>r.stage),["picker-opened","picker-selected","file-read-started","file-read-completed","import-request-started","import-request-completed","state-refresh-started","state-refresh-completed","snapshot-save-completed"]);
    proof.trace=rows;
    proof.conclusion="Both desktop selection paths import exact file contents and refresh/cache state. POST /api/import and unsupported methods/paths remain blocked. Real native interaction and OS notification visibility are separate checks.";
  }
  proof.passed=true;
} finally {await app.close();await fs.writeFile(original?"docs/evidence/desktop-import-original.json":"docs/evidence/desktop-import-regression.json",JSON.stringify(proof,null,2));}
console.log(JSON.stringify(proof,null,2));

