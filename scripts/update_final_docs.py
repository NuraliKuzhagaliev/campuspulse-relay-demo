"""Write the current evidence view; preserve previous ledgers as dated history."""
import hashlib
import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
history=root/'docs/history/before-final-integration-0.4.0'
history.mkdir(parents=True,exist_ok=True)
paths=['README.md','STATUS.md','BLOCKERS.md','REQUIREMENTS.md','docs/deployment_proof.md','docs/test_results.md','release/README.md','docs/final_integration_ledger.md']
for name in paths:
    target=history/name.replace('/','__')
    if not target.exists():target.write_bytes((root/name).read_bytes())

ledger='''# Final integration requirement and evidence ledger

Baseline0.3.0-r1 and all prior sealed artifacts remain preserved. Current installed/local integration candidate: **0.4.0**. Actual public service remains **0.2.1** at commit `83552161ec22c7cf44746433425d3b2b99e042c4`. This candidate is not READY_FOR_SUBMISSION or a completed hosted0.4 demo.

| Criterion / addition | Actual result | Evidence | Outstanding gate |
|---|---|---|---|
| C1 MCP/tools | Genuine ADK/Gemini tool choice, signed MCP transport,16 server tools, real GitHub status and Flask PR reads | `evidence/final-alternative-smoke.json`, `evidence/final-features-local-mvf943c1.json` | Managed-agent MCP and real Calendar observations not performed |
| C2 original managed GCP/API | **UNMET / GCP_EXCEPTION_PENDING** | `evidence/final-account-assessment.json`, `organizer_update.md` | Existing trial closed, prepayment required, no credits established. No payment permitted. Other-tools notice does not explicitly replace this criterion |
| C3 logic/autonomy | Actual unseen questions, conflict comparison, server-validated plan, explicit remaining, same-session EN/RU/KK and checkpoint after server restart | `evidence/final-verification-0.4.0.json` and correlated runs | Sleeping free host is not an always-running Scheduler. Full hosted/cloud acceptance pending |
| C4 UX | Local browser13 pass/1 public-only skip; installed0.4 source/IPC/import/passport contracts pass;12 language/width states; keyboard scroll-region fix | `evidence/desktop-contract-0.4.0.json`, `four-desktop-0.4.0.json`, `final-ui-local-mvf8xcqp.json` | New unmodified native Open/Save/cancel, notification click, public0.4 and Windows HTTPS model query pending |
| C5 architecture/presentation | Explicit provider/deployment route, no paid fallback, tenant checkpoint, protected owner-only AI issuer, bounded calls/tokens, reproducible source and12-slide editable PPTX/PDF | `final_free_path.md`, `cost_estimate.md`, `evidence/presentation-0.4.0.json`, release manifest | Hosted deployment evidence and judging count/window still unconfirmed |
| F1–F5 | **Locally implemented**: evidence, feasibility, change radar, approved effects, next action | Preserved domain/fault tests and current121-test suite | Real Calendar and full Gemini acceptance remain pending |
| A1 Progress & Remaining Work | Explicit45 logged/95 remaining retained; solver uses120 minutes. Actual Gemini follow-up identifies these as student reports | `evidence/final-semantics-local-mvf9*.json`, installed contracts and historical human0.3 follow-up | No attention, learning or submission proof inferred |
| A2 Clarify First | Cited alternatives and bounded solver branches observed through actual model/MCP | `evidence/final-features-local-mvf943c1.json` | Difference count is removed-plus-added entries, not distinct moved blocks. No global relevance/probability claim |
| A3 Handoff Radar | Actual public `pallets/flask#6168` merged observation, explicit live provenance, no GitHub writes | Same feature evidence | Demand-driven allowlisted public reads. Background cloud detection and new banner click unverified |
| A4 Workspace Passport | Installed/web transfer, exact semantic restoration, D: writes, restart, cross-tenant/approval boundary tested | `evidence/four-desktop-0.4.0.json`, test_four_additions | Dialog substitutions are explicit. Restored archive cannot grant AI/Calendar authority or freshness |
| D1–D3 | Minimal Rescue, bounded draft preflight, independent illustrative challenge remain supported | Current browser and installed contracts | Preflight metadata does not prove semantic correctness or predict a grade |
| Real Calendar | Dedicated secondary target exists. No app/runtime consent or real writes accepted | `connections.json`, deterministic Calendar action/sync tests | Owner OAuth setup/consent plus exact authenticated UI preview approval required. Current alternative route intentionally excludes this authority |
| Public and judges | Existing Free Render service preserved, no card.0.4 cutover target prepared with rollback, private AI invitation and separate visitor workspaces | `final_cutover_plan.md`, `final_judge_guide.md` | Owner must save eligible free key in existing service, then deploy and test actual HTTPS path. No hosted0.4 success inferred |

The observed local browser sample contains11 real model turns:10 complete and1 initial partial. The unnecessary extraction call and actual accessibility defect were corrected and affected paths rechecked. The original failed extraction arguments were intentionally not stored, so its precise rejected field is unknown. A later progress wording issue was corrected and actually rechecked. There is no statistical100% success or zero-defect guarantee. Provider responses retained in the isolated local store total31 model responses,110461 reported tokens at collection, including development smoke/failures. This is not a remaining quota balance or invoice.

Status vocabulary: implemented, deterministic/local verified, installed contract verified, genuinely live verified through local gateway, not run, blocked/partial. Neither local HTTPS nor remote Gemini inference is public hosting or managed Agent Engine proof. All project-controlled local dependencies, profiles, caches, temporary files and outputs remain on D:.
'''
(root/'docs/final_integration_ledger.md').write_text(ledger,encoding='utf-8')
(root/'REQUIREMENTS.md').write_text(ledger.replace('# Final integration requirement and evidence ledger','# Requirements and current acceptance')+'\nHistorical detailed criterion ledger: `docs/history/before-final-integration-0.4.0/REQUIREMENTS.md`. Earlier release ledgers remain inside their sealed archives.\n',encoding='utf-8')
(root/'STATUS.md').write_text('''# CampusPulse RELAY0.4.0: local Gemini verified, hosted cutover pending

Updated2026-10-19. Started from0.3.0-r1, preserved prior fixes/history and installed a separate verified0.4.0 candidate. Public URL remains https://campuspulse-relay-demo.onrender.com at0.2.1 until the verified cutover. The original managed GCP requirement remains **UNMET / GCP_EXCEPTION_PENDING**. This is not READY_FOR_SUBMISSION.

Actual free route: owner-configured `gen-lang-client-0595303951`, Gemini Developer API `gemini-3.5-flash-lite`, metadata version `3.5-flash-lite-07-2026`. ADK selected genuine signed MCP calls and live public GitHub/Handoff observations.11 actual frontend turns were observed over local HTTPS, including EN/RU/KK, unseen documents, separate visitors, explicit progress and follow-up after server restart. One initial partial and later wording imprecision were retained and affected paths rechecked after fixes. No fake/cached AI response substituted for a live result.

Current local results:121 Python pass,13 browser pass/1 public-only skip,4 exact IPC policy pass. Installed0.4 source, narrow IPC, both import paths and cross-device passport/restart contracts pass. Dialog substitutions are explicit. New actual native Open/Save/cancel and notification click still require observation. Historical0.1.1 real picker/banner and0.3 human45/95 persistence evidence are preserved separately.

No personal spending or paid resources authorized. Existing GCP Free trial account is closed and requires prepayment, with no credits shown. No billing change/payment was made. Existing Render Hobby/Free workspace has no card, and its included usage was checked. Anonymous traffic gets isolated illustrative workflows. Private AI invitations require adult Kazakhstan evaluator consent and permitted non-sensitive material. Unpaid Gemini privacy limits are disclosed. Real Calendar remains pending consent and exact UI approval.

Current blocker for public0.4: save the eligible free Gemini key in the prepared private `RELAY_GEMINI_API_KEY` row of the existing Render service and choose **Save only**. The request is pending. No new service was created. Local checks, Windows artifacts, presentation, source/package preparation and reviewable rollback/cutover plan are complete independently. After the key is saved, execute and verify actual hosting and installed Windows HTTPS query before changing the readiness label.

Deadline supplied by owner:20October2026 at23:59, organizer timezone unconfirmed. Planning assumption Asia/Qyzylorda UTC+5, internal freeze20October20:00 local. See `docs/organizer_update.md`. No organizer submission or unsolicited messages were sent.

Current evidence: `docs/evidence/final-verification-0.4.0.json`, `docs/final_integration_ledger.md`, `docs/final_judge_guide.md`, `release/manifest.json`. All controlled local files/caches/builds are on D:. Earlier status is archived under `docs/history/before-final-integration-0.4.0/STATUS.md` and preserved release directories.
''',encoding='utf-8')
(root/'BLOCKERS.md').write_text('''# Outstanding acceptance gates

1. **Existing Render secret/cutover:** owner must save the free Gemini key to `RELAY_GEMINI_API_KEY` in the prepared Environment row and choose Save only. Current public service is still0.2.1. No hosted0.4 or Windows HTTPS model query has been verified. Exact target/rollback/checks: `docs/final_cutover_plan.md`.
2. **Original GCP requirement UNMET / exception pending:** read-only inspection found a closed Free trial account requiring prepayment, no visible credits and unauthenticated D: gcloud/ADC. No personal expenses/payment/billing activation is authorized. Organizer credits will not be supplied. Do not keep waiting for them or treat alternative hosting as Agent Engine. Owner may seek explicit criterion/timezone clarification using the draft in `docs/organizer_update.md`; no message sent by Codex.
3. **Real Calendar:** dedicated secondary calendar exists, but application OAuth/runtime consent and real apply/read-back/retry/guarded compensation are not accepted. An exact immutable preview needs authenticated UI approval before writes. The alternative free-Gemini route intentionally exposes neither Calendar mutation tools nor private event details. No primary-calendar path is permitted.
4. **Actual native interactions:**0.4 installed contract/import/passport checks passed with explicitly substituted dialogs. Human Open/Save/cancel observations and new notification visibility/click/focus remain separate. Supported native automation was unavailable after the recorded helper initialization failure. Earlier0.1.1 picker/banner and0.3 human45/95 restart evidence remain valid historical evidence.
5. **Free-host limits/judging:** temporary SQLite/uploads/sessions/invitation consumption may reset on sleep/restart/deploy. No durable persistence or always-on background Scheduler is claimed. Judge count, location/age eligibility and actual availability window are not independently confirmed. Issue short private invitations near the confirmed window, within actual free quota; no automatic keep-alive or paid upgrade.
6. **Prepared managed route limitations:** live SDK/IAM/Firestore addition transactions, actual managed resource and cloud-to-MCP identity/renewal remain unverified. Funding scripts fail closed for paid accounts, stale/wrong trial records, insufficient coverage and missing positive reserve. No service has been provisioned through these scripts.

Automatic approval review rejected a separate Render staging service because prior hosting authorization restricts infrastructure to the existing free service. No new service was created. Local HTTPS staging and the prepared existing-service cutover provide the supported path; do not retry creation indirectly.

Observed local defects (extraction contract/instruction, execution-region keyboard focus, remaining-estimate wording) were corrected and affected checks rerun. Exact evidence and honest limitations are in `docs/evidence/final-verification-0.4.0.json`. Historical blockers are retained in `docs/history/before-final-integration-0.4.0/BLOCKERS.md`.
''',encoding='utf-8')
(root/'README.md').write_text('''# CampusPulse RELAY

Evidence-linked academic recovery for GDG Astana Topic2. Current installed/local candidate **0.4.0** starts from preserved0.3.0-r1. Existing public demo: **https://campuspulse-relay-demo.onrender.com**, currently **0.2.1**. Hosted0.4 is pending the owner's server-side key save and verified cutover. Original managed Agent Engine criterion: **UNMET / GCP_EXCEPTION_PENDING**.

RELAY imports selected academic documents, retains page/version quotations and disagreements, computes independently validated CP-SAT plans, compares what-if/Minimal Rescue changes, previews explicitly approved effects and records read-back receipts. Progress & Remaining Work, Clarify First, Handoff Radar and Workspace Passport preserve student control. F1–F5 remain **locally implemented**, with real Calendar and full Gemini acceptance pending. EN/RU/Kazakh operational UI is preserved.

## Actual Gemini contingency

The owner configured a Free-tier Gemini key for `gen-lang-client-0595303951`. Actual model: `gemini-3.5-flash-lite`, observed metadata version `3.5-flash-lite-07-2026`. The shared ADK agent performed real signed MCP calls, source-grounded EN/RU/KK answers, GitHub/PR observations and a follow-up after server restart through a local HTTPS browser.11 observed turns include an initial partial that was retained and corrected. This is **alternative Gemini hosting**, not a deployed `projects/.../reasoningEngines/...` resource.

Anonymous hosted visitors receive isolated illustrative workspaces and cannot spend model quota. Real AI access requires a private one-use invitation and adult Kazakhstan evaluator confirmation. Unpaid-service processing/human-review limits are disclosed; use only permitted non-sensitive documents. Keys remain server-side. No Calendar mutation tools or private event details enter this unpaid model path. See `docs/final_free_path.md`, `docs/final_judge_guide.md`, `docs/tool_catalog_final.md` and `docs/cost_estimate.md`.

## Run on D:

Project root: `D:\\projects\\CampusPulseRELAY`. Read `scripts/env.ps1` before setup. It routes controlled Python/Node/Electron/Playwright/gcloud/HF caches, temp, data and profiles to D:. Use the existing locked environments/dependencies or `scripts/bootstrap.ps1`; do not install project dependencies/cache on C:.

```powershell
Set-Location D:\\projects\\CampusPulseRELAY
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\\scripts\\dev.ps1
```

The local illustrative gateway serves `http://127.0.0.1:8000`. It works without Google authentication. For the installed local path set `RELAY_GATEWAY_URL` to that URL in the launch process. The0.4 app defaults to the public HTTPS gateway, whose deployment version must be checked before expecting0.4 features. Native user data remains on D:. ExecutionPolicy Bypass is per process, not a system policy change.

The owner-only live local route uses `scripts/run-alternative.ps1` on8016 and a loopback HTTPS proxy on8017. `scripts/prepare_local_tls.py` creates a development certificate on D: without a trust-root change. Only explicit local test contexts accept that development certificate. Public TLS must validate normally. The separate `scripts/gemini-env.ps1` decrypts the Windows-DPAPI key only in the server process; ordinary environment setup/builds do not load it.

## Verification and release

Actual current local evidence:121 Python tests,13 browser passes/1 public-only skip,4 IPC policy tests and installed0.4 source/import/passport contracts.12 language/width combinations and the post-agent keyboard/AA defect were checked.11 real frontend model turns and provider-reported usage are indexed in `docs/evidence/final-verification-0.4.0.json`. Small samples do not establish a statistical success rate. Dialog substitution is not real native dialog/notification evidence.

Windows installer/portable, complete frontend+Python web bundle, source archive, editable12-slide PPTX/PDF and candid manifest/checksums are under `release/` and the versioned D: submission directory. The manifest names the exact source commit and actual public deployment separately. All previous releases, hashes and human native evidence remain preserved. Windows binaries are unsigned. Read `release/README.md` before installation.

## Deployment and required gates

Use the **existing** Free Render service in the authorized workspace. Review `docs/final_cutover_plan.md`; owner saves `RELAY_GEMINI_API_KEY` using Save only, then publish the exact pushed source with `infra/Dockerfile.alternative`, one worker, auto-deploy off. No new infrastructure/paid upgrade. Run fresh public HTTPS and installed Windows acceptance before marking cutover verified. Free storage/session reset and cold starts are disclosed; no fake always-on autonomy.

The GCP Free Trial account is closed, requires prepayment and has no visible credits. No personal expenses or billing changes are authorized. Organizer credits will not arrive. Prepared funding/deployment guards remain separate from actual managed acceptance. Real Calendar also needs separate app consent/scoped runtime access and concrete authenticated UI approval. Current receipts are illustrative. See `REQUIREMENTS.md`, `BLOCKERS.md`, `docs/cloud_setup.md` and `docs/organizer_update.md`.

Deadline:20October2026,23:59, organizer timezone unconfirmed. Planning assumes UTC+5, internal freeze20:00 local. Owner decides and submits the contest entry. No organizer/judge messages or submission were sent. Historical README: `docs/history/before-final-integration-0.4.0/README.md`.
''',encoding='utf-8')
(root/'release/README.md').write_text('''# CampusPulse RELAY0.4.0 integration candidate

The manifest/checksums name the exact committed source, installed Windows candidate, complete local web bundle and12-slide presentation. This is a local Gemini-verified candidate, not a completed hosted0.4 or managed-GCP submission. Current public service remains0.2.1 until verified cutover. Read `docs/final_cutover_plan.md` and `docs/final_judge_guide.md`.

Keep extraction, installer, portable profile, dependencies, caches and data on D:. Installer and portable binaries are unsigned. Installed location: `D:\\projects\\CampusPulseRELAY\\installed\\CampusPulse RELAY`.0.3 installation was hash-checked and copied to `installed/preserved-0.3.0`; prior sealed archives/manifests remain untouched. Install/uninstall does not mean cloud or native dialog acceptance.

The0.4 desktop defaults to the public HTTPS gateway. Until the0.4 backend cutover, use the explicit local launch environment `RELAY_GATEWAY_URL=http://127.0.0.1:8000` with a running0.4 local gateway for all new features. No GCP/Google authentication is needed for illustrative file import/planning. API keys never belong in Electron, renderer, passport or source archives.

The complete web ZIP contains built React assets and the actual Python backend. Extract on D: and use `scripts/run-web-bundle.ps1`. Its minimal dependency environment stays on D: and supports the illustrative flow. The full source archive contains locked ADK/Gemini dependencies and alternative deployment scripts for server-only live use.

Native checks requiring a human: real Open/Cancel/file import; real Passport Save/restore with45 logged/95 remaining after reopening; actual notification banner and click/focus. Automated installed tests explicitly substitute dialogs. Historical0.1.1 real picker/banner and0.3 human persistence reports remain separately dated.

The PDF consists of visually inspected rendered pages. The PPTX retains editable text/shapes and passed structural/font/geometry/import checks. Native PowerPoint opening is not claimed. The historical0.1.0 local recording remains a separate labeled fallback. Private judge invitations, keys, cookies, uploads, caches and local credentials are excluded from public/source packages.
''',encoding='utf-8')
(root/'docs/deployment_proof.md').write_text('''# Actual deployment evidence

On2026-10-19 the retained public HTTPS health endpoint returned200 and version0.2.1, commit `83552161ec22c7cf44746433425d3b2b99e042c4`. URL: https://campuspulse-relay-demo.onrender.com . Existing service `srv-dbajs73bc2fs73bm9mfg`, previous live deployment `dep-dbal14m1egvs73b4fp8g`. See `evidence/final-public-preserved.json` and historical `evidence/public-deployment-0.2.1.json`.

0.4 has real Gemini/ADK/signed MCP verification through **local** HTTPS staging and a remote Gemini Developer endpoint. It is not yet deployed on public Render. Owner key-save is pending. Exact reviewable target and rollback: `final_cutover_plan.md`. Neither a pushed branch nor a local model call is hosted deployment proof. No new Render service was created.

GCP account/trial inspection: `evidence/final-account-assessment.json`. Managed Agent Engine resource/API remains UNMET / GCP_EXCEPTION_PENDING. Cloud-to-MCP Google service identity, real Calendar consent/write/read-back, hosted background detection and Windows public model query remain unverified. No personal spending/payment/billing change was authorized or performed.

Historical deployment narrative is preserved under `history/before-final-integration-0.4.0/docs__deployment_proof.md`. It is not the current0.4 acceptance result.
''',encoding='utf-8')
(root/'docs/test_results.md').write_text('''#0.4.0 integration verification

Actual executions on2026-10-19, all controlled paths on D:. Full Python121 pass in9.654s, with one upstream Starlette/httpx deprecation warning. After sanitized revision metadata changes, affected final-integration/judge tests14 pass in2.17s. Browser13 pass/1 public-only skip in36.044s. Exact Node IPC4 pass in82.4866ms. Production TS/Vite build and unsigned NSIS/portable build pass. Installed0.4 ASAR main/preload/policy/renderer match source, secure Electron settings, import/read-back/cache, local planning/what-if/receipt/undo and cross-device passport/restart contracts pass. Dialog substitutions are explicit.

Real Gemini browser sample:11 turns,10 complete and1 initial partial, plus earlier protocol smoke. Retained isolated-store provider usage31 responses,106088 input/4373 output/0 thinking/110461 total tokens at collection. No invoice or remaining-quota claim. Actual source/page answers and EN/RU/KK continuations, ambiguous date, consent denial, two-visitor foreign-source403, conflict comparison, validated plan, explicit progress, actual GitHub/Flask PR MCP reads and checkpoint after server restart observed. Corrected extraction, keyboard region and report-semantics defects were rechecked with affected real/UI runs.

Post-answer Axe initially found `scrollable-region-focusable` on `.run-events`. Named region/tabIndex/translated label fixed it. Recheck used the existing real-run state with zero extra inference.12 language/width states fit. Automated AA subset passes, not a full accessibility certification. Original failed extraction arguments were not persisted; exact rejected field is unknown. Typed candidate schema and goal-specific extraction instruction now pass separate actual model source-read/proposal checks. Later progress wording is corrected and explicitly rechecked.

Native Open/Save/cancel/banner/click need separate real observation. Historical0.1.1 picker/banner and0.3 human45/95 reopening are retained, not relabeled0.4 checks. Public remains0.2.1; hosted0.4, installed Windows public query, real Calendar, managed GCP and always-running hosted autonomy have not passed.

Machine-readable index: `evidence/final-verification-0.4.0.json`. Historical test narrative is under `history/before-final-integration-0.4.0/docs__test_results.md`. All partial/failing development evidence remains retained and no failed run is overwritten into a pass.
''',encoding='utf-8')
(root/'docs/tool_catalog_final.md').write_text('''# Actual tool catalog for0.4.0

FastMCP exposes16 tenant-bound tools. Model arguments never select identity, context signing keys or Calendar ownership. MCP Streamable HTTP verifies both machine transport and bounded signed workspace context on the Developer route. The original managed route uses Cloud Run Google identity plus signed workspace context, not live verified yet.

Developer-model allowlist (11): `list_course_sources`, `read_course_source`, `get_assignment_repo_status`, `read_assignment_repo_file`, `get_workspace_plan_inputs`, `get_progress_summary`, `recommend_clarification`, `observe_handoff_gate`, `build_next_action_packet`, `propose_academic_extraction`, `save_validated_plan`. The last builds from server facts; model payload overrides are ignored. Extraction proposes exact cited fields and cannot confirm/apply them. Progress is a student report, not independently validated completion. Clarification removed-plus-added differences may count a moved block twice.

Five additional MCP tools are deliberately unavailable to the unpaid Developer model: `get_calendar_window`, `preview_study_blocks`, `apply_approved_study_blocks`, `verify_study_blocks`, `undo_owned_study_blocks`. Even where enabled for the managed path, writes/undo require concrete existing authenticated UI authority and ownership/version checks. Current real Calendar acceptance is pending.

Two pure function tools are separate from the16 MCP tools: `build_recovery_plan` and `compare_plan_scenarios`. The server independently validates schedule intervals, deadlines, dependencies, busy/pinned blocks and caps. No model-written schedule is accepted as feasible without validation.

Actual16-tool discovery and relevant real model calls are in `evidence/final-alternative-smoke.json` and `final-features-local-mvf943c1.json`. Each result records tool status/hash, relevant source/version provenance and finite typed error codes. Full tool payloads, private chain-of-thought, credentials and approval data are not exposed as execution telemetry. `/internal/ai-invitations` is not a model tool; only a short-lived exact Ed25519 owner signature can issue bounded AI-only invitations.
''',encoding='utf-8')
print('Updated current ledgers; preserved previous narrative under '+str(history))
