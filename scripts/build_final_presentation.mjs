/** Final integration briefing, using the established RELAY typography and palette. */
import fs from 'node:fs/promises';
import path from 'node:path';
import {createRequire} from 'node:module';
import {pathToFileURL} from 'node:url';
import {spawnSync} from 'node:child_process';
import crypto from 'node:crypto';
const root=process.cwd(),require=createRequire(import.meta.url);
const runtime='C:/Users/nural/.cache/codex-runtimes/codex-primary-runtime/dependencies';
const skill='C:/Users/nural/.codex/plugins/cache/openai-primary-runtime/presentations/26.1017.11052/skills/presentations';
process.env.RUNTIME_NODE_MODULES=runtime+'/node/node_modules';process.env.RUNTIME_NODE=runtime+'/node/bin/node.exe';process.env.RUNTIME_PYTHON=runtime+'/python/python.exe';
const {Presentation,PresentationFile}=await import(pathToFileURL(require.resolve('@oai/artifact-tool',{paths:[process.env.RUNTIME_NODE_MODULES]})).href);
let hosted={};try{hosted=JSON.parse(await fs.readFile('docs/evidence/public-deployment-0.4.0.json','utf8'));}catch{}
const live=hosted.verified===true&&hosted.real_gemini_verified===true;
const hostedLive=live?JSON.parse(await fs.readFile(hosted.evidence.live,'utf8')):null;
const hostedMarker=live?[...hostedLive.runs[0].text.matchAll(/Compare compensator models ([a-f0-9]{8})/g)].at(-1)?.[1]:null;
const evidence=JSON.parse(await fs.readFile('docs/evidence/final-verification-0.4.0.json','utf8'));
const revision=process.env.RELAY_PRESENTATION_REVISION||'integration-r1';
const stem='CampusPulse-RELAY-0.4.0-'+revision;
const output=path.join(root,'release/presentation'),build=path.join(root,'.local/presentation-final',revision);
await fs.mkdir(output,{recursive:true});await fs.mkdir(build,{recursive:true});
const deck=Presentation.create({slideSize:{width:1280,height:720}});
const C={bg:'#F5F4EF',navy:'#10243A',ink:'#14243A',blue:'#2B59F0',mint:'#BDE9D6',muted:'#586650',line:'#DCE2D7'};
function txt(s,value,x,y,w,h,size=26,color=C.ink,bold=false){const q=s.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});q.text=value;q.text.style={typeface:'Arial',fontSize:size,color,bold,insets:0,autoFit:'none',wrap:'square'};return q;}
function line(s,x,y,w,color=C.line){s.shapes.add({geometry:'rect',position:{left:x,top:y,width:w,height:1},fill:color,line:{fill:'none',width:0}});}
function slide(title,notes=''){const s=deck.slides.add();s.background.fill=C.bg;txt(s,'CAMPUSPULSE  /  RELAY',64,35,850,25,14,C.muted,true);txt(s,title,64,104,1140,112,48,C.ink,true);line(s,64,664,1152);txt(s,String(deck.slides.items.length).padStart(2,'0')+'  /  GDG ASTANA / TOPIC 2 / 0.4.0',64,680,1100,20,12,C.muted);s.speakerNotes.text=notes;return s;}
function col(s,title,body,x=64,y=255,w=530){txt(s,title,x,y,w,58,31,C.ink,true);txt(s,body,x,y+82,w,Math.min(270,640-y-82),26,C.muted);}
{
 const s=deck.slides.add();s.background.fill=C.navy;
 txt(s,'BUILD WITH AI  /  GDG ASTANA  /  TOPIC 2',64,50,1120,30,16,C.mint,true);
 txt(s,'CampusPulse\nRELAY',64,144,1100,230,92,'#FFFFFF',true);
 txt(s,'See what changed.\nKnow what to do next.',68,408,1100,130,42,C.mint);
 txt(s,'Web and Windows 0.4.0',68,605,1120,34,24,'#BDCED9');
 txt(s,live?'Gemini on the alternative host. Original Agent Engine criterion unmet.':'Real Gemini verified locally over HTTPS. Hosted 0.4.0 cutover pending.',68,664,1130,24,17,'#BDCED9');
 s.speakerNotes.text='Actual mode/status is generated from final verification and public deployment evidence. Official Topic2 brief pages3–4. No managed GCP deployment has been verified.';
}
{
 const s=slide('A revised deadline changes the whole week','Illustrative product scenario, not interview findings. Official Topic2 brief pages3–4 and supplied research report.');
 txt(s,'A PDF says Thursday. A repository says Wednesday.\nThe student has already committed Tuesday evening.',64,242,1120,100,31,C.muted);
 col(s,'Keep the evidence','Retain both quotations and versions.\nThe student selects the authoritative fact.',64,403,530);
 col(s,'Recompute the consequence','Respect actual availability and dependencies.\nShow what moves before approval.',676,403,530);
}
{
 const s=slide('Five enhancements implemented locally','F1–F5: relay/evidence.py, scheduler.py, service.py, actions.py. Genuine Gemini is now separately observed on RouteB. Real Calendar acceptance is pending. No grade or stress improvement has been measured.');
 const rows=[['F1  Evidence','Source, quote, page and version'],['F2  Feasibility','Deterministic scheduling with independent validation'],['F3  Change radar','Observed versions and impact jobs'],['F4  Approved actions','Immutable preview, operation journal and read-back'],['F5  Next action','A cited rubric item and concrete work packet']];
 rows.forEach(([a,b],i)=>{const y=244+i*72;txt(s,a,64,y,300,44,29,C.ink,true);txt(s,b,390,y,805,50,25,C.muted);});
 txt(s,'Real Calendar and full Gemini acceptance remain separate gates',64,621,1140,30,21,C.blue,true);
}
{
 const s=slide('Recovery tools that preserve uncertainty','Recent four additions and D1–D3 are preserved. tests/test_four_additions.py, test_continuation.py, browser/four.spec.ts. Human0.3 close/reopen report verifies45 logged/95 remaining. This is not new0.4 native dialog evidence.');
 col(s,'Progress and clarification','45 logged minutes do not prove completion.\n95 remaining is an explicit student estimate.\nCompare cited alternatives before choosing.',64,244,536);
 col(s,'Handoff and continuity','Read an allowlisted public PR condition.\nA portable passport restores selected facts.\nIt never restores credentials or approvals.',682,244,532);
 txt(s,'Also retained: Minimal Rescue and bounded submission preflight',64,578,1140,70,27,C.ink,true);
}
{
 const s=slide('A feasible plan and a useful failure','Fixed-clock golden fixture. 600 window minutes minus60 protected minutes =540. Requirements240+180+120=540. Removing Wednesday loses120. At least60 added minutes are needed before the Wednesday lab deadline. Independently validated by tests/test_domain.py and test_continuation.py. This numeric example is a deterministic fixture, not a current live forecast.');
 txt(s,'540 min',64,243,500,100,78,C.blue,true);txt(s,'required and initially available',68,350,520,60,28,C.muted);
 txt(s,'420 min',682,243,500,100,78,C.ink,true);txt(s,'available after losing Wednesday',686,350,520,60,28,C.muted);
 line(s,64,449,1152);
 txt(s,'Friday alone cannot repair a Wednesday deadline',64,484,1130,75,35,C.ink,true);
 txt(s,'Minimal Rescue compares only the extra windows the student permits',64,586,1130,60,25,C.muted);
}
{
 const s=slide('Gemini reads an unseen source and keeps context',live?`Actual public browser evidence ${hosted.evidence.live}, deployed ${hosted.deployed_commit}. Eight complete hosted browser turns and ${hosted.actual_complete_installed_turns} installed turns. The first hosted turn timed out; one bounded retry in the same two authorized test workspaces passed. All original failures are retained. No statistical reliability guarantee. RU/KK follow-ups used the same conversation; no Calendar writes.`:'Actual browser evidence final-live-local-mvf8h3vr.json and focused correction final-focus-local-mvf8uiq4.json. First English answer was partial due to an unnecessary failed extraction call. The source-only instruction and typed extraction schema were repaired; two affected real turns completed. RU/KK continuations preserved exact source quotes. This observed sample is not a statistical success guarantee.');
 txt(s,'New synthetic Optics document',64,238,1120,52,32,C.ink,true);
 txt(s,live?`“Due: 2026-10-23T20:00:00+05:00”\n“- [ ] Compare compensator models ${hostedMarker}”`:'“Due: 2026-10-24T18:30:00+05:00”\n“- [ ] Compare two reference surfaces mvf8uiq4”',64,318,1120,104,29,C.blue);
 txt(s,'Actual source/page citations and MCP reads\nRussian and Kazakh follow-ups in the same conversation\nAn ambiguous 03/04 date remains unknown',64,474,1120,152,28,C.muted);
}
{
 const s=slide('Alternative architecture with explicit boundaries','RouteB uses the actual shared ADK agent, Gemini Developer API gemini-3.5-flash-lite, signed MCP, tenant SQLite and deterministic scheduling. Internal MCP requires machine credential plus bounded workspace context. Private operator invitations require a separate Ed25519 owner signature. Public key only on host. No Developer/Vertex fallback. Read docs/final_free_path.md, cost_estimate.md.');
 col(s,'React / installed Electron','An isolated visitor capability and CSRF guard\nPython gateway with durable text checkpoints\nADK selects relevant MCP and solver tools',64,244,536);
 col(s,'Gemini Developer API','gemini-3.5-flash-lite, Free tier\nSelected source and public GitHub evidence\nCalendar mutation tools excluded',682,244,532);
 txt(s,live?'Current host: existing Free Render service, one worker':'Local HTTPS verified. Existing Free Render target prepared.',64,566,1130,45,28,C.blue,true);
 txt(s,'Managed reasoningEngines resource: UNMET / GCP_EXCEPTION_PENDING',64,618,1130,34,22,C.muted);
}
{
 const s=slide('Observed tool results and approval boundaries','Actual local final-features-local-mvf943c1.json; hosted final-features-hosted-mvfbrp3z.json: Gemini chose recommend_clarification, save_validated_plan, get_progress_summary, get_assignment_repo_status and observe_handoff_gate. Repo main commit66fd068bc1cf142f8152e717f662e11c20f96a97 was observed at test time. Flask PR6168 merged with merge SHA728c5e440af704a786384159184f695cf04ecbe7. No GitHub writes. All Calendar receipts in this batch are local-adapter illustrative receipts.');
 col(s,'Actual external reads','Gemini selected useful MCP tools.\nGitHub status includes immutable revision.\nFlask PR #6168 was observed merged.',64,243,536);
 col(s,'Illustrative Calendar','Exact preview and explicit UI approval\nRead-back receipt and idempotent operations\nNo real Google event created by this batch',682,243,532);
 txt(s,'Documents cannot authorize writes or reveal server credentials',64,593,1130,60,29,C.ink,true);
}
{
 const s=slide('Verification and remaining native observations','Final evidence final-verification-0.4.0.json. Tests are this integration execution, not copied historical counts. Installed main/preload/policy/renderer match current source. Hosted actual reset IPC rejection repaired with exact POST route and CSRF refresh; reinstall and affected contracts passed. New IPC suite5 passes, separate owner-clock suite2 passes; the121 Python/13 browser+1skip counts below are the preserved local baseline. Dialog substitutions are explicit; old real picker/banner evidence belongs to0.1.1 and human45/95 persistence to0.3.0. Accessibility fix gives the scrollable execution region keyboard focus.');
 txt(s,String(evidence.python.tests),64,238,480,100,80,C.blue,true);txt(s,'Python regressions passed',68,349,530,50,28,C.ink,true);
 txt(s,'13 + 1',682,238,480,100,80,C.ink,true);txt(s,'browser passes + public-only skip',686,349,530,60,27,C.ink,true);
 txt(s,'Installed package, import and public Gemini/MCP query passed\nHosted EN / RU / KK at 390, 768, 1280 and 1440px\nReal native Open/Save/cancel and new toast click remain separate checks',64,470,1140,155,26,C.muted);
}
{
 const s=slide('Funding and privacy limits','Actual account assessment final-account-assessment.json: GCP Free trial account closed, prepayment required, no visible credits. No payment/billing change. Gemini project free-tier status and actual successful requests observed. https://ai.google.dev/gemini-api/terms and pricing, https://render.com/docs/free rechecked2026-10-19. UI attestation is not independent age/location verification. Free quotas are not a remaining balance or invoice.');
 col(s,'No personal spending','GCP trial activation requires prepayment.\nThat route remains blocked.\nExisting Render Free service has no card.\nGemini free requests use bounded quotas.',64,244,536);
 col(s,'Private evaluation access','Invited adult evaluators in Kazakhstan\nPermitted, non-sensitive documents only\nUnpaid inputs may receive human review.\nNo confidential Calendar data sent to Gemini.',682,244,532);
 txt(s,'Free hosting sleeps and may reset temporary files, sessions and invitations',64,600,1130,50,25,C.blue,true);
}
{
 const s=slide('Judge demonstration','docs/final_judge_guide.md. Owner distributes one-use private invitations outside source/URLs. Current default aggregate ceiling300 model calls/day,100 reserved within that ceiling. Quotas may still throttle and free-host resets invalidate sessions. Recording is a labeled historical local fallback only, not a current live-cloud demonstration.');
 txt(s,'1   Open the HTTPS entry and choose the demo\n2   Import a new permitted brief and inspect its quoted evidence\n3   Compare a plan, change remaining work, inspect the difference\n4   Review an explicitly illustrative Calendar receipt\n5   Enter a private invitation for a real Gemini question',64,236,1140,302,29,C.ink);
 txt(s,'https://campuspulse-relay-demo.onrender.com',64,574,1140,50,30,C.blue,true);
 txt(s,live?'Hosted 0.4.0 Gemini path verified. Private access remains required.':'Public release still 0.2.1. New 0.4.0 hosted Gemini path is pending.',64,629,1140,27,20,C.muted);
}
{
 const s=slide('Submission status and delivery window','Organizer funding/deadline notice supplied by owner. Original organizer screenshot and separately named FINAL brief not attached to this run. Available official Topic2 brief pages3–4 remains the criterion authority. No credit activation is expected. Owner should confirm whether other tools amend mandatory managed deployment and which deadline timezone applies. No organizer message or submission was sent.');
 txt(s,'Original GCP criterion: UNMET / exception pending\nReal Calendar consent, write and read-back: pending\nHosted background autonomy: unavailable on a sleeping free host',64,241,1130,165,30,C.ink,true);
 txt(s,'20 October 2026 at 23:59\nOrganizer timezone unconfirmed',64,461,1120,100,37,C.blue,true);
 txt(s,'Planning assumption UTC+5. Internal freeze 20 October at 20:00 local.\nThe owner decides submission under the allowed-tools notice.',64,591,1130,65,23,C.muted);
}
for(const [i,s] of deck.slides.items.entries())await fs.writeFile(path.join(build,`slide-${String(i+1).padStart(2,'0')}.png`),new Uint8Array(await (await deck.export({slide:s,format:'png',scale:1})).arrayBuffer()));
const candidate=path.join(build,'candidate.pptx');await(await PresentationFile.exportPptx(deck)).save(candidate);
const {finalizePresentation}=await import(pathToFileURL(path.join(skill,'container_tools/artifact_tool_utils.mjs')).href);
const reference=path.join(root,'release/presentation/CampusPulse-RELAY-0.2.1-quality-verified.pptx');
const receipt=await finalizePresentation({workspaceDir:root,candidatePath:candidate,finalPath:path.join(output,stem+'.pptx'),pythonExecutable:runtime+'/python/python.exe',integrityValidatorPath:skill+'/container_tools/inspect_presentation_package_integrity.py',layoutValidatorPath:skill+'/container_tools/inspect_presentation_layout_geometry.py',layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-heading-fit'],explicitTotalSlideCount:deck.slides.items.length,requiredNativeTableOwnerSlides:[],fontPolicy:{basis:'reference',families:['Arial'],referencePath:reference,referenceSha256:crypto.createHash('sha256').update(await fs.readFile(reference)).digest('hex')},verifyArtifactToolImport:true,receiptPath:path.join(build,'validation.json')});
// PDF pages use actual rendered slides. Editable text/shapes remain in PPTX.
const py=spawnSync(path.join(root,'.venv/Scripts/python.exe'),['scripts/final_slides_to_pdf.py',build,path.join(output,stem+'.pdf')],{cwd:root,env:process.env,encoding:'utf8'});if(py.status!==0)throw new Error(py.stderr);
const result={version:'0.4.0',slides:deck.slides.items.length,pptx:path.join(output,stem+'.pptx'),pdf:path.join(output,stem+'.pdf'),renders:build,hosted_gemini_verified:live,editable:true,pdf_kind:'rendered_slide_pages',validation:path.join(build,'validation.json')};
await fs.writeFile('docs/evidence/presentation-0.4.0.json',JSON.stringify(result,null,2));console.log(JSON.stringify(result));
