import fs from "node:fs/promises";
import path from "node:path";
import { createRequire } from "node:module";
import { pathToFileURL } from "node:url";
import { spawnSync } from "node:child_process";
const require = createRequire(import.meta.url);
const root = process.cwd();
const releaseVersion=JSON.parse(await fs.readFile(path.join(root,"package.json"),"utf8")).version;
let nativeResult={};
try {nativeResult=JSON.parse(await fs.readFile(path.join(root,"docs/evidence/desktop-native-result.json"),"utf8"));}catch{}
const slideCount=10;
process.env.RELAY_PRESENTATION_SLIDES=String(slideCount);
let publicDeployment={};
try {publicDeployment=JSON.parse(await fs.readFile(path.join(root,`docs/evidence/public-deployment-${releaseVersion}.json`),"utf8"));}catch{}
const publicVerified=publicDeployment.verified===true;
const nativeVerified=nativeResult.status==="passed_with_human_interaction";
const nativeImportVerified=nativeResult.picker?.exact_source_observed===true;
const nativeSummary=nativeVerified?"Real picker import verified. User confirmed the bottom-right Windows banner.":nativeImportVerified?"Real picker import verified. OS notification visibility still pending.":"Picker appearance confirmed. Real import recheck and OS visibility pending.";
const stem=`CampusPulse-RELAY-${releaseVersion}-quality-verified`;
process.env.RELAY_PRESENTATION_STEM=stem;

const runtime =
  "C:/Users/nural/.cache/codex-runtimes/codex-primary-runtime/dependencies";
process.env.RUNTIME_NODE_MODULES = runtime + "/node/node_modules";
process.env.RUNTIME_NODE = runtime + "/node/bin/node.exe";
process.env.RUNTIME_PYTHON = runtime + "/python/python.exe";
const skill =
  "C:/Users/nural/.codex/plugins/cache/openai-primary-runtime/presentations/26.1011.51657/skills/presentations";
const { Presentation, PresentationFile } = await import(
  pathToFileURL(
    require.resolve("@oai/artifact-tool", {
      paths: [runtime + "/node/node_modules"],
    }),
  ).href
);
const output = path.join(root, "release/presentation"),
  build = path.join(root, ".local/presentation-build");
await fs.mkdir(output, { recursive: true });
await fs.mkdir(build, { recursive: true });
const deck = Presentation.create({ slideSize: { width: 1280, height: 720 } });
const C = {
  bg: "#F5F4EF",
  navy: "#10243A",
  ink: "#14243A",
  blue: "#2B59F0",
  mint: "#BDE9D6",
  coral: "#E47757",
  muted: "#586650",
  line: "#DCE2D7",
};
function rect(s, x, y, w, h, fill, radius = false) {
  return s.shapes.add({
    geometry: radius ? "roundRect" : "rect",
    position: { left: x, top: y, width: w, height: h },
    fill,
    line: { fill: "none", width: 0, style: "solid" },
  });
}
function text(s, value, x, y, w, h, size = 26, color = C.ink, bold = false) {
  const shape = s.shapes.add({
    geometry: "textbox",
    position: { left: x, top: y, width: w, height: h },
    fill: "none",
    line: { fill: "none", width: 0, style: "solid" },
  });
  shape.text = value;
  shape.text.style = {
    typeface: "Arial",
    fontSize: size,
    color,
    bold,
    insets: 0,
    autoFit: "none",
    wrap: "square",
  };
  return shape;
}
function slide(title, kicker = "") {
  const s = deck.slides.add();
  s.background.fill = C.bg;
  text(s, "CAMPUSPULSE  /  RELAY", 64, 35, 500, 25, 14, C.muted, true);
  if (kicker) text(s, kicker, 820, 35, 396, 25, 14, C.muted);
  text(s, title, 64, 96, 1130, 120, 49, C.ink, true);
  rect(s, 64, 664, 1152, 1, C.line);
  text(
    s,
    `${String(deck.slides.items.length).padStart(2, "0")}  /   GDG ASTANA / TOPIC 2`,
    64,
    679,
    600,
    20,
    12,
    C.muted,
  );
  return s;
}
function note(s, value) {
  s.speakerNotes.text = value;
}
function line(s, x, y, w, color = C.line) {
  rect(s, x, y, w, 2, color);
}
function tag(s, value, x, y, w = 200, fill = C.mint) {
  rect(s, x, y, w, 32, fill, true);
  text(s, value, x + 12, y + 7, w - 24, 20, 13, C.navy, true);
}

{
  const s = deck.slides.add();
  s.background.fill = C.navy;
  text(
    s,
    "BUILD WITH AI  /  GDG ASTANA  /  TOPIC 2",
    64,
    50,
    1100,
    30,
    16,
    C.mint,
    true,
  );
  text(s, "CampusPulse\nRELAY", 64, 145, 790, 240, 92, "#FFFFFF", true);
  text(
    s,
    "See what changed.\nKnow what to do next.",
    68,
    408,
    760,
    130,
    42,
    C.mint,
  );
  rect(s, 973, 160, 190, 190, C.mint, true);
  text(s, "R/", 995, 177, 155, 150, 115, C.navy, true);
  text(
    s,
    "Web + Windows /  Evidence -> feasible plan -> approved action -> verification",
    68,
    608,
    1120,
    35,
    20,
    "#BDCED9",
  );
  text(
    s,
    publicVerified?"Public illustrative web demo / mandatory GCP acceptance remains pending":"Local release candidate /  cloud acceptance gate remains blocked",
    68,
    664,
    1120,
    24,
    14,
    "#BDCED9",
  );
  note(
    s,
    "When a deadline changes, RELAY connects evidence, constraints and approved effects. The public illustrative Render deployment is separate from the required managed GCP deployment. Do not imply Gemini or real Calendar acceptance. Sources: supplied Topic 2 brief pages 3-4, docs/deployment_proof.md, docs/evidence/public-deployment.json.",
  );
}
{
  const s = slide(
    "One revised deadline.\nAn entire week out of date.",
    "THE STUDENT PROBLEM",
  );
  text(
    s,
    "A PDF says Thursday. The course repository says Wednesday.\nA calendar commitment has already consumed an hour.",
    64,
    250,
    1090,
    85,
    28,
    C.muted,
  );
  line(s, 64, 370, 1152);
  text(s, "Evidence", 64, 411, 330, 50, 32, C.ink, true);
  text(
    s,
    "Keep both passages and the\nversion that supports each fact.",
    64,
    472,
    320,
    100,
    24,
    C.muted,
  );
  text(s, "Constraints", 466, 411, 330, 50, 32, C.ink, true);
  text(
    s,
    "Use the time the student\nactually has before each deadline.",
    466,
    472,
    320,
    100,
    24,
    C.muted,
  );
  text(s, "Agency", 862, 411, 330, 50, 32, C.ink, true);
  text(
    s,
    "Approve concrete changes,\nthen verify the external result.",
    862,
    472,
    330,
    100,
    24,
    C.muted,
  );
  note(
    s,
    "The course content is illustrative. This is a problem scenario, not a claim from fabricated interviews. Source conflict and feasibility are implemented and covered by deterministic tests. Primary problem framing: supplied official brief, Topic 2, pages 3-4. Research supporting the positioning: supplied 24-page research report, pages 7-8.",
  );
}
{
  const s = slide(
    "Five enhancements, implemented locally.",
    "FIVE LOCAL ENHANCEMENTS",
  );
  const steps = [
    ["01", "Evidence", "F1 /  quote, page, ref, version"],
    ["02", "Feasibility", "F2 /  deterministic constraints"],
    ["03", "Change radar", "F3 /  real source polling"],
    ["04", "Approved actions", "F4 /  journal + read-back"],
    ["05", "Next action", "F5 /  rubric-linked packet"],
  ];
  steps.forEach(([n, title, caption], i) => {
    const x = 64 + i * 235;
    rect(s, x, 254, 213, 178, i === 3 ? C.navy : "#E7EDE1", true);
    text(s, n, x + 17, 270, 170, 37, 25, i === 3 ? C.mint : C.muted, true);
    text(s, title, x + 17, 323, 185, 60, 25, i === 3 ? "#FFFFFF" : C.ink, true);
    text(s, caption, x, 454, 215, 82, 19, C.muted);
    if (i < 4) text(s, "->", x + 215, 319, 25, 36, 24, C.muted);
  });
  text(
    s,
    "No guessed deadlines. No silent calendar rewrites. No fabricated tool progress.",
    64,
    572,
    1130,
    56,
    26,
    C.ink,
  );
  note(
    s,
    "Demonstrate one coherent workflow. F1 retains contradictory evidence; F2 independently validates schedules; F3 records actual repository changes; F4 binds approval to an immutable digest and returns per-operation outcomes; F5 opens a concrete cited work packet. Calendar live acceptance and managed-agent execution remain pending authentication. Code: relay/evidence.py, scheduler.py, service.py, actions.py; src/App.tsx.",
  );
}
{
  const s = slide(
    "Managed-agent path prepared; live gate pending.",
    "ARCHITECTURE & TRUST",
  );
  const boxes = [
    {
      x: 64,
      w: 260,
      label: "React + Electron",
      sub: "Local renderer / narrow bridge",
      fill: C.mint,
    },
    {
      x: 392,
      w: 325,
      label: "Authenticated gateway",
      sub: "Verified identity / durable events",
      fill: "#E2E7DD",
    },
    {
      x: 785,
      w: 430,
      label: "Agent Engine + ADK / Gemini",
      sub: "reasoningEngines resource /  pending",
      fill: "#DEE6FC",
    },
  ];
  boxes.forEach((b, i) => {
    rect(s, b.x, 248, b.w, 113, b.fill, true);
    text(s, b.label, b.x + 18, 267, b.w - 36, 42, 24, C.ink, true);
    text(s, b.sub, b.x + 18, 316, b.w - 36, 30, 17, C.muted);
    if (i < 2) text(s, "->", b.x + b.w + 18, 279, 40, 40, 30, C.muted);
  });
  rect(s, 392, 416, 325, 126, C.navy, true);
  text(s, "Custom MCP service", 411, 437, 285, 37, 26, "#FFFFFF", true);
  text(
    s,
    "Audience-bound workspace context\nRefreshed machine identity",
    411,
    481,
    285,
    60,
    18,
    C.mint,
  );
  text(s, "v", 978, 375, 40, 35, 29, C.muted);
  text(s, "<-", 738, 455, 43, 35, 29, C.muted);
  text(s, "Approved sources", 64, 435, 270, 34, 24, C.ink, true);
  text(
    s,
    "Selected files\nAllowlisted GitHub\nAuthorized Calendar",
    64,
    481,
    280,
    110,
    21,
    C.muted,
  );
  text(
    s,
    "Cloud target: Firestore / GCS / private Cloud Run MCP.\nVerified today: local SQLite / actual MCP protocol / live GitHub reads.",
    785,
    430,
    430,
    150,
    23,
    C.muted,
  );
  note(
    s,
    "Cloud boxes describe implemented deployment paths, not deployed services. No Gemini call runs in the gateway as a hidden fallback. The Agent Engine runtime uses Google ADK and Gen AI; the gateway invokes the remote resource. Cloud Run MCP is private and also verifies a signed short-lived workspace context. Google quickstart: https://docs.cloud.google.com/gemini-enterprise-agent-platform/build/runtime/quickstart-adk ; MCP deployment: https://adk.dev/tools-custom/mcp-tools/deployment/ .",
  );
}
{
  const s = slide(
    "Feasibility is computed, not improvised.",
    "A KNOWN, INDEPENDENTLY CHECKED CASE",
  );
  text(s, "540 min", 64, 240, 420, 90, 72, C.blue, true);
  text(s, "estimated work", 69, 331, 390, 40, 26, C.muted);
  text(s, "540 min", 665, 240, 450, 90, 72, C.ink, true);
  text(
    s,
    "capacity after a protected commitment",
    670,
    331,
    530,
    65,
    26,
    C.muted,
  );
  line(s, 64, 418, 1152);
  text(s, "Lose Wednesday afternoon", 64, 452, 650, 55, 34, C.ink, true);
  rect(s, 64, 535, 750, 35, C.mint);
  rect(s, 64, 535, (750 * 420) / 540, 35, C.blue);
  text(
    s,
    "420 min available / 540 min required",
    64,
    589,
    780,
    40,
    26,
    C.muted,
  );
  text(s, ">=120 min\nshortfall", 900, 472, 300, 120, 44, "#8B422C", true);
  note(
    s,
    "This is the fixed-clock golden test, not the current live repository revision. Windows total 600 minutes; Tuesday protected event removes 60. Tasks require 240 + 180 + 120 = 540. Removing Wednesday removes 120, leaving 420. At least 60 minutes of the lab shortage must be added before its Wednesday deadline; Friday-only extra time does not solve that constraint. CP-SAT and an independent interval validator enforce deadlines, no overlap, dependencies, pins and daily caps. Tests: tests/test_domain.py. OR-Tools: https://developers.google.com/optimization/cp/cp_solver .",
  );
}
{
  const s=slide("Restore feasibility with a permitted change.","D1 / MINIMAL RESCUE");
  tag(s,"120 MIN TOTAL SHORTAGE",64,238,305);
  tag(s,"60 MIN BEFORE LAB DEADLINE",405,238,390);
  text(s,"Friday alone cannot fix Wednesday.",64,308,1130,70,40,C.ink,true);
  const cards=[['01 / OFFER','Student permits Tuesday 16–17 and Friday 17–18. No protected commitment or deadline changes.'],['02 / COMPARE','Bounded deterministic combinations. Minimum claimed only within a completed offered search.'],['03 / CHOOSE','Show added time and accepted-block movement. Read current busy state; require a fresh approval.']];
  cards.forEach(([title,body],i)=>{const x=64+i*388;rect(s,x,414,360,184,i===2?C.navy:'#E7EDE1',true);text(s,title,x+18,432,324,36,22,i===2?C.mint:C.ink,true);text(s,body,x+18,480,324,100,21,i===2?'#D3E0E7':C.muted)});
  note(s,'Reference fixture: Lab240 due Wednesday18, ML180 Friday18, Web120 Friday20. Removing Wednesday leaves420 capacity and120 total shortage; only180 minutes remain before the lab deadline, so lab shortage60. Friday-only additions cannot help. The bounded search covers up to five student-offered windows; no global minimum outside those candidates is claimed. Tests: tests/test_continuation.py and tests/browser/challenge.spec.ts. All Calendar writes remain illustrative until real consent/read-back acceptance.');
}
{
  const s=slide("A draft you can check. A judge who can explore.","D2 / SUBMISSION PREFLIGHT · D3 / JUDGE CHALLENGE");
  text(s,"Observable requirements",64,243,540,48,32,C.ink,true);
  text(s,"Filename / format / named sections\nWord bounds / actual PDF page counts\nExact requirement -> observed metadata",64,314,540,140,25,C.muted);
  tag(s,"VERIFIED / MISSING / REVIEW / UNKNOWN",64,489,536);
  text(s,"Structure is not semantic correctness.\nNo grade prediction or auto-submission.",64,553,540,72,23,C.muted);
  rect(s,672,234,544,387,C.navy,true);
  text(s,"Try your own\npermitted brief.",699,262,488,76,33,C.mint,true);
  text(s,"Own visitor workspace and source versions\nExplicit course / term / assignment mapping\nChange a constraint and compare a rescue\nFresh approval -> read-back evidence\nEN / RU / Kazakh throughout",699,365,482,204,24,'#D3E0E7');
  note(s,'Preflight checks selected text PDF, Markdown or TXT against cited structured requirements. Heading/image presence never proves correctness. Exceptions and semantics need review. Missing work may become an extra-effort scenario with a student-provided estimate. Judge route is independently verified with a new brief; mandatory unscripted Gemini/real Calendar judge acceptance remains blocked on organizer credits. Source identity migration and conversation contracts are verified locally, not substituted for cloud requirements.');
}
{
  const s = slide(
    "Real tools. Inspectable observations.",
    "LOCAL PROTOCOL + LIVE EXTERNAL EVIDENCE",
  );
  tag(s, "ACTUAL MCP TRANSPORT", 64, 235, 250);
  text(
    s,
    "initialize -> tools/list -> tools/call",
    64,
    291,
    1140,
    65,
    38,
    C.ink,
    true,
  );
  line(s, 64, 382, 1152);
  text(s, "Live GitHub", 64, 423, 450, 40, 31, C.ink, true);
  text(
    s,
    "13 tools discovered; final calls pass.\nLive status + immutable repository file read.",
    64,
    479,
    525,
    95,
    25,
    C.muted,
  );
  text(s, "Historical local change", 685, 423, 490, 40, 31, C.ink, true);
  text(
    s,
    "19.62 seconds /  one impact run\nDuplicate refresh: no second run.",
    685,
    479,
    525,
    95,
    25,
    C.muted,
  );
  text(
    s,
    "This proves local MCP + public API reads + server polling. Cloud-agent calls remain unverified.",
    64,
    607,
    1150,
    30,
    19,
    C.muted,
  );
  note(
    s,
    "Evidence: docs/evidence/mcp-smoke-0.2.0.json and radar-live-proof.json. Latency uses a same-host monotonic clock from connector-write dispatch to server source observation; it includes connector request latency and is one observation, not a median or p95. The source is the dedicated owned demonstration repository: https://github.com/NuraliKuzhagaliev/campuspulse-relay-demo . Do not describe illustrative material as real coursework or local polling as hosted autonomy.",
  );
}
{
  const s = slide(
    "A product a judge can inspect.",
    "VERIFICATION, NOT A SUCCESS ANIMATION",
  );
  text(s, "78", 64, 239, 330, 100, 84, C.blue, true);
  text(s, "Python tests passed", 69, 349, 400, 42, 28, C.ink, true);
  text(
    s,
    "Evidence, constraints, identity isolation,\nstale approvals, retries and guarded undo.",
    69,
    406,
    470,
    90,
    24,
    C.muted,
  );
  text(s, publicVerified?"10 + 2":"10", 690, 239, 330, 100, 84, C.ink, true);
  text(s, publicVerified?"Local flows + hosted gates":"Browser scenarios passed", 695, 349, 480, 42, 28, C.ink, true);
  text(
    s,
    "EN / RU / Kazakh operational workflows,\noriginal quotes, errors and automated AA rules.",
    695,
    406,
    490,
    90,
    24,
    C.muted,
  );
  text(
    s,
    publicVerified?`Windows ${releaseVersion}: installed contracts, both imports and persistence pass.\n0.1.1 human picker / banner proof retained; click/focus remains unverified.\nPublic demo: import, what-if, receipts, languages and visitor isolation verified.\nGemini/Agent Engine and real Calendar acceptance remain pending.`:`Windows ${releaseVersion}: both import paths, refresh and cache pass regression.\n0.1.1 human picker/banner proof retained; click/focus remains unverified.\nLive Google consent, Calendar and Agent Engine acceptance remain pending.`,
    64,
    563,
    1150,
    88,
    19,
    C.muted,
  );
  note(
    s,
    "Counts come from the actual local suite and may be updated in docs/test_results.md. Three native IPC policy/redaction/method-contract tests passed. New desktop checks do not establish a new human toast observation. Installed original failure: renderer file input sent POST /api/import, rejected before upload. Both desktop paths now use /api/import-native. The original human incident lacked route tracing, so its attribution remains unconfirmed. The regression explicitly substitutes the native picker. The actual unmodified picker import and OS notification visibility are recorded separately in docs/evidence/desktop-native-result.json. No live Gemini, Calendar, statistical reliability or zero-defect claim follows from local tests. Accessibility covers an automated subset at 1440x900, 1280x720, 1024x768 and 390x844.",
  );
}
{
  const s = slide(
    "What works. What still needs proof.",
    "HONEST RELEASE READINESS",
  );
  text(s, publicVerified?"Public demo + Windows":"Working locally", 64, 236, 500, 50, 33, C.ink, true);
  text(
    s,
    publicVerified?"File import + cited evidence\nValidated planning and what-if\nReal hosted GitHub reads\nSimulated Calendar + receipts\nEN / RU / Kazakh + visitor isolation":"Evidence and conflict resolution\nValidated recovery and what-if\nServer change radar + real GitHub\nApproved local actions + receipts\nCited packets + Windows continuity",
    64,
    309,
    540,
    260,
    28,
    C.muted,
  );
  rect(s, 670, 232, 546, 341, C.navy, true);
  text(
    s,
    "Mandatory GCP gate: PENDING",
    697,
    262,
    493,
    72,
    31,
    C.mint,
    true,
  );
  text(
    s,
    "Google authentication + dedicated project\nOrganizer credit activation + eligibility\nCalendar consent + judge runtime access\nReal managed resource and remote smoke\nLive Calendar write / read-back proof",
    697,
    357,
    487,
    182,
    23,
    "#D3E0E7",
  );
  if(publicVerified){
    text(s,publicDeployment.public_url,64,598,1145,30,24,C.blue,true);
    text(s,"Temporary sessions and storage. Calendar simulated. Managed AI remains pending.",64,635,1145,24,17,C.muted);
  }else text(
    s,
    "Next: verify organizer credits and project eligibility, then deploy and test the actual managed path.",
    64,
    604,
    1145,
    44,
    23,
    C.ink,
  );
  note(
    s,
    "Do not present this local release candidate as a completed hackathon cloud submission. Earlier read-only Cloud Console inspection showed a trial prepayment requirement; organizer credits remain unconfirmed. The user declined personal spending. Wait for organizer credit activation, exact project eligibility, balance and expiration; explain uncovered costs before requesting approval. No new billing account or payment was attached. Student value is a hypothesis, not a measured grade or stress improvement. Full release ledger: REQUIREMENTS.md.",
  );
}

for (let i = 0; i < deck.slides.items.length; i++) {
  const slide = deck.slides.items[i];
  await fs.writeFile(
    path.join(build, `slide-${String(i + 1).padStart(2, "0")}.png`),
    new Uint8Array(
      await (
        await deck.export({ slide, format: "png", scale: 1 })
      ).arrayBuffer(),
    ),
  );
}
// The bundled PDF exporter lacks its standard-font data. Use the verified slide renders for the PDF;
// the PPTX below retains native editable text and shapes.
const pdfResult = spawnSync(
  path.join(root, ".venv/Scripts/python.exe"),
  ["scripts/slides_to_pdf.py"],
  { cwd: root, env: process.env, encoding: "utf8" },
);
if (pdfResult.status !== 0)
  throw new Error(pdfResult.stderr || "Slide PDF export failed.");
const candidate = path.join(build, "candidate.pptx");
await (await PresentationFile.exportPptx(deck)).save(candidate);
const { finalizePresentation } = await import(
  pathToFileURL(path.join(skill, "container_tools/artifact_tool_utils.mjs"))
    .href
);
const result = await finalizePresentation({
  workspaceDir: root,
  candidatePath: candidate,
  finalPath: path.join(output, stem+".pptx"),
  pythonExecutable: runtime + "/python/python.exe",
  integrityValidatorPath:
    skill + "/container_tools/inspect_presentation_package_integrity.py",
  layoutValidatorPath:
    skill + "/container_tools/inspect_presentation_layout_geometry.py",
  layoutArgs: [
    "--expected-slide-size-emu",
    "12192000,6858000",
    "--validate-heading-fit",
  ],
  explicitTotalSlideCount: slideCount,
  requiredNativeTableOwnerSlides: [],
  fontPolicy: { basis: "design", families: ["Arial"] },
  verifyArtifactToolImport: true,
  receiptPath: path.join(build, `validation-${stem}.json`),
});
console.log(
  JSON.stringify(
    {
      slides: slideCount,
      pdf: path.join(output, stem+".pdf"),
      pptx: path.join(output, stem+".pptx"),
      validation: result,
    },
    null,
    2,
  ),
);

await fs.writeFile(path.join(root,`docs/evidence/presentation-${releaseVersion}.json`), JSON.stringify({version:releaseVersion,slides:slideCount,native_status:nativeResult.status||"pending",native_human_proof_release:"0.1.1",public_demo_verified:publicVerified,public_url:publicDeployment.public_url||null,pptx:path.join(output,stem+".pptx"),pdf:path.join(output,stem+".pdf"),validation:path.join(build,`validation-${stem}.json`)},null,2));
