"""Reconcile actual audit evidence; pending human/cloud checks never become passes."""
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
import httpx

ROOT=Path(__file__).resolve().parents[1]
def read(name):return json.loads((ROOT/name).read_text(encoding='utf-8-sig'))
def write(name,value):
    (ROOT/name).write_text(value if isinstance(value,str) else json.dumps(value,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def main():
    assert ROOT.drive.lower()=='d:'
    health=httpx.get('https://campuspulse-relay-demo.onrender.com/api/health',timeout=60).raise_for_status().json()
    live=read('docs/evidence/audit-live-mvfmnry1.json')
    assert live['passed'] and len(live['cases'])==5 and len(live['runs'])==6
    github=read('docs/evidence/audit-hosted-github.json') if (ROOT/'docs/evidence/audit-hosted-github.json').exists() else {}
    samples=read('docs/evidence/audit-public-samples.json') if (ROOT/'docs/evidence/audit-public-samples.json').exists() else {}
    proof=dict(checked_at=datetime.now(timezone.utc).isoformat(),version='0.5.0',public_url='https://campuspulse-relay-demo.onrender.com/',
        deployed_commit=health['deployed_commit'],NON_GCP_READY=False,
        tests=dict(python_passed=209,subtests_passed=3,ipc_passed=7,
            full_run_log_sha256=hashlib.sha256((ROOT/'.local/logs/audit-final-unit-r11.log').read_bytes()).hexdigest(),
            simulated_100='docs/evidence/audit-100-simulated.json',actual_gemini_calls_in_100=0),
        documents=dict(verified_cases=5,real_turns=6,all_turns_complete=True,evidence='docs/evidence/audit-live-mvfmnry1.json',acceptance_commit=live['deployed_commit'],
            cases=[dict(file=c['file'],sha256=c['sha256'],passed=c['passed']) for c in live['cases']],statistical_reliability_claimed=False),
        calendar=dict(operations_verified=False,oauth_client_configured=True,api_enabled_owner_confirmed=True,audience_production_owner_confirmed=True,
            callback_attempt_rejected=True,owner_report='Authorization link copied into another browser/window; source session cookie does not transfer with URL.',
            consent_token_exchange_verified=False,real_write_readback_retry_undo_revocation_verified=False,
            owner_action='Start from ordinary RELAY homepage in the working browser, then connect and finish there without transferring authorization/callback URLs.'),
        native=dict(full_visibility_verified=False,unmodified_picker_appearance=True,cancel_observed=True,owner_selected_import=True,import_and_refresh_both_http_200=True,
            observed_build='docs/evidence/audit-native-observation-0.5.0.json',final_installed_contract='docs/evidence/audit-desktop-0.5.0.json',
            original_45_logged_95_remaining_preserved=True,save_dialog_and_reimport_verified=False,notification_visibility_click_focus_verified=False,
            windows_control_stopped_by_owner_escape=True),
        github=dict(background_verified=bool(github.get('passed') and github.get('server_observation_without_browser')),evidence='docs/evidence/audit-hosted-github.json' if github else None,
            dedicated_credential_locally_read_validated=True,server_configuration_verified=bool(github),prior_upstream_error='UPSTREAM_RATE_LIMITED',
            deployment_guard='Do not deploy until owner restores RELAY_TOKEN_ENCRYPTION_KEY and stores GitHub token separately in RELAY_GITHUB_TOKEN.' if not github else None),
        samples=dict(files=13,public_downloads_verified=bool(samples.get('passed')),evidence='docs/evidence/audit-public-samples.json' if samples else None,
            url='https://campuspulse-relay-demo.onrender.com/samples/'),
        managed=dict(MANAGED_GCP_VERIFIED_IN_AUTHORIZED_WINDOW=False,PUBLIC_RELEASE_READY_AFTER_WINDOW=False,actual_resource=None,
            preparation='docs/evidence/managed-preparation-0.5.0.json',organizer_t0_project_coverage_expiry_verified=False,personal_spending_authorized_usd=0),
        limitations=['Render Free storage is temporary (up to two hours; earlier restart/redeploy reset). Export Passport.',
            'Free host can sleep. Polling runs while awake, and cached observations retain original source fetch time.',
            'Real Gemini Developer API/MCP is alternative hosting, not managed Agent Engine.',
            'Google Calendar protocol fault simulations and illustrative receipts are not actual Google writes.',
            'Five-document batch is evidence, not a statistical reliability or latency guarantee. Earlier failed/partial attempts remain recorded.',
            'Native observations belong to their recorded build; final installed contracts do not prove a Save dialog or notification was visible.'])
    write('docs/evidence/non-gcp-0.5.0.json',proof)
    summary=f'''# CampusPulse RELAY · 0.5.0 audit candidate

Public app: **https://campuspulse-relay-demo.onrender.com/** · [Source](https://github.com/NuraliKuzhagaliev/campuspulse-relay-demo) · [13-file sample pack and EN/RU/Kazakh instructions](https://campuspulse-relay-demo.onrender.com/samples/).

**NON_GCP_READY = false.** Real multilingual document/Gemini workflows are verified. Actual Google Calendar operations and the remaining physical Windows checks still block complete acceptance. Current runtime: `{health['deployed_commit']}`. See `docs/evidence/non-gcp-0.5.0.json` for separate evidence revisions and unresolved gates.

Open the ordinary HTTPS link: an isolated visitor workspace is created automatically, without invitations, registration, Google sign-in or visitor API keys. Choose **Use my own data**, upload permitted non-sensitive PDF/MD/TXT/ICS, review exact page citations and confirm each assignment separately. Choose your period/timezone/availability, resolve conflicts, plan, compare what-if, inspect next actions/Preflight, record progress and export a Passport. The example workspace and local-adapter Calendar previews/receipts are explicitly illustrative. Real Calendar is a separate voluntary consent and exact-action approval flow.

The five independent EN/RU/Kazakh prose, continued PDF and table PDF workflows completed through the full hosted UI: upload → real Gemini/MCP proposal → per-assignment review → plan/what-if → illustrative approved receipt → progress45/95 → Passport → reopen. Six real turns completed, including a same-conversation follow-up. Evidence: `docs/evidence/audit-live-mvfmnry1.json`, runtime `{live['deployed_commit']}`. Earlier failed/partial/correction runs remain recorded. This is a verified batch, not a reliability or latency guarantee. The100-session isolation/queue test uses a simulated provider and zero actual Gemini calls.

Latest complete local run: **209 Python tests,3 subtests;7 narrow IPC checks**. The actual installed0.5.0 main/preload/renderer match source and retain sandbox/context isolation. Native Open/Cancel and a real owner-selected import succeeded; trace confirms import **and subsequent refresh**200. Original preserved workspace retains45logged/95explicitly remaining. Native Save/reimport and notification visibility/click-focus remain unverified after the owner stopped Windows control using Escape. See `docs/remaining_actions_0.5.0.md`.

F1–F5 stay **locally implemented; real Calendar and full enhancement-level Gemini acceptance pending**. Configured OAuth client, enabled API and Production audience do not prove consent/write/read-back/undo/revocation. Public AI excludes private Calendar payloads and mutation tools.

Raw file limit2MiB; text PDFs ≤100pages/250,000extracted characters with a disposable CPU/memory/wall-time bounded parser. No scanned OCR. Exact45/75minute source estimates remain distinct from30minute solver allocations60/90. Missing context/year/timezone/requirements stay unknown or unassessed. Logged time never automatically reduces explicit remaining work.

Existing Render **Free** service; server-only secrets, capability cookies, CSRF/tenant authorization, one outstanding turn per workspace,2workers and fair per-call quota tickets. Provider429/backoff is authoritative. Storage lasts up to2hours and may reset earlier on restart/redeploy; hosting can sleep and polling runs while awake. Export a Passport. No durable/always-on promise. GitHub cache/backoff and real hosted acceptance have separate evidence; unavailable integrations show typed errors.

## Organizer window on20October: no personal spending

Supplied notice: tutorial20October2026at10:00;12hours from **actual activation**, deadline20October23:59 (UTC+5 planning assumption). Actual T0/project/principal/coverage/balance/expiry/model/region/quotas remain unverified. No personal trial, card, prepayment, billing attachment or paid upgrade. Actual Agent Engine and cloud-to-MCP/shared-state acceptance remain pending. `docs/organizer_window_runbook.md` contains the prepared minimal, guarded deploy/query/retire sequence. Offline SDK checks create no resources and do not satisfy managed acceptance.

## D-drive setup and preserved releases

Everything project-controlled stays under `D:/projects/CampusPulseRELAY`: dependencies, caches, temp, profiles, downloads, builds and deliverables. Start with `scripts/env.ps1`. Local illustrative development: `powershell.exe -NoProfile -ExecutionPolicy Bypass -File "D:/projects/CampusPulseRELAY/scripts/dev.ps1"`. Real server-only Gemini uses `scripts/run-alternative.ps1`. Never put keys in the renderer or desktop build.

Prior sealed releases and original data remain preserved. New0.5.0 packages are a separately versioned audit candidate; read the manifest for exact source/runtime commits and checksums. Windows binaries are unsigned. A complete local illustrative React+Python ZIP is distinct from the configured real public Gemini service. Full user answers, private screenshots, credentials and cookies stay outside Git on D:.
'''
    write('README.md',summary)
    write('STATUS.md',f'''# Actual acceptance · 0.5.0

Public runtime `{health['deployed_commit']}`. **NON_GCP_READY=false**. Latest complete local suite209tests+3subtests; IPC7. Five real document workflows and6realGemini/MCP turns passed at `{live['deployed_commit']}`;100sessions separately use a simulated provider. Current installed contracts and preserved45/95 passed. Actual Open/Cancel/import+refresh passed on the recorded native build.

Remaining gates: real Calendar consent/target/write/read-back/retry/undo/revocation and independent consent; native Save/reimport/reopen and visible notification/click-focus; Windows real Gemini acceptance. GitHub background verified: **{proof['github']['background_verified']}**. Public sample downloads verified: **{proof['samples']['public_downloads_verified']}**. All source/deploy/test distinctions are retained in `docs/evidence/non-gcp-0.5.0.json` and `docs/audit_U1_U16.md`.

Managed GCP and after-window complete public acceptance remain pending actual organizer T0/project/coverage. No personal spending or provisioning. Windows control was stopped with Escape and has not resumed.
''')
    write('BLOCKERS.md','''# Actual remaining gates · 0.5.0

- Calendar Console/client/API/Production setup is completed. Real consent has not completed. Owner copied an authorization link into another browser/window; restart from the ordinary homepage in the working browser. Keep private cookie/state/PKCE binding. Actual selected target/write/read-back/retry/undo/revocation and independent-user acceptance remain unverified.
- Native Open/Cancel/owner-selected import and both import/refresh200 are recorded. Save/reimport/reopen and notification visibility/click-focus remain human checks. Owner stopped Windows control using Escape; no further control attempted. Windows real Gemini acceptance also remains pending.
- Hosted GitHub earlier returned shared-quota429. Dedicated fine-grained credential passed local read-only contents/issues requests. Restore the original encryption key if overwritten; GitHub belongs in RELAY_GITHUB_TOKEN. A saved variable is not live read/background acceptance. See the evidence ledger for later actual results.
- Actual organizer T0, principal/project, coverage/expiry/model/quotas are unknown. Agent Engine, authenticated cloud-to-MCP/shared state, remote multi-turn/Windows and managed-off/expiry acceptance require that real window. No personal payment/trial/billing change is authorized.

Exact steps: `docs/remaining_actions_0.5.0.md`. Machine-readable truth: `docs/evidence/non-gcp-0.5.0.json`. Do not mark NON_GCP_READY or either managed status true while their gates remain.
''')
    write('REQUIREMENTS.md','''# Requirements and acceptance · 0.5.0

Topic2 GDG Astana CampusPulse AI. **NON_GCP_READY=false**; per-check status is not waived by GCP preparation.

| Requirement | Actual result |
|---|---|
| EN/RU/Kazakh own documents | Five independent prose/PDF full hosted UI workflows and6realGemini/MCP turns passed; frozen inputs and earlier failures retained |
| Evidence and conflict identity | Cross-page source/version/page citations, explicit per-assignment canonical confirmation, source conflict decisions; missing context remains unknown |
| Planning and continuity | Hosted plan/what-if/illustrative receipt/Preflight/progress45/95/Passport/reopen passed; exact effort distinct from solver allocation |
| Five core enhancements | Locally implemented; real Calendar and full enhancement-level Gemini acceptance pending |
| Public access and isolation | Automatic anonymous workspace, no invitations/registration/Google login/visitor keys; two actual visitors plus100simulated-provider HTTP sessions; zero real model calls in load test |
| Limits and protection |2MiBraw/3MiBtransport, bounded PDF subprocess, typed errors, CSRF/tenant checks, narrow IPC and protected internal/admin/MCP operations |
| GitHub change radar | Cache/singleflight/conditional304/backoff tests passed. Real read and browser-independent observation have separately dated evidence; shared upstream429 retained |
| Samples |13synthetic files, trilingual guide/context/expected results and ZIP. Public hashes and current runtime recorded separately |
| Calendar | Technical client/API/Production setup done; real consent/target/write/read-back/retry/undo/revocation and independent user acceptance pending |
| Windows | Installed0.5contracts/source match and original45/95 passed. Actual Open/Cancel/import+refresh passed; Save/reimport/banner/click and real Gemini pending |
| Managed GCP | Guarded SDK/package/bridge/shared-state/owner-routing preparation only. Actual organizer activation/project/coverage/resources/query still pending |
| After-window fallback | Existing public state remains authoritative. Actual managed-off/expiry complete-product acceptance pending real window |
| Package and presentation | Preserve every prior sealed revision; new candidate manifest records exact source/runtime and evidence limitations |

See `docs/audit_U1_U16.md`, `docs/final_integration_ledger.md` and `docs/evidence/non-gcp-0.5.0.json`. Temporary Free hosting is not durable or always-on. Personal spending remains0.
''')
    write('docs/final_integration_ledger.md',f'''# Requirement and evidence ledger · 0.5.0

Public HTTPS https://campuspulse-relay-demo.onrender.com/ · Render Free `srv-dbajs73bc2fs73bm9mfg` · current runtime `{health['deployed_commit']}`. **NON_GCP_READY=false**. Prior release/history evidence is retained.

| Check | Actual evidence | Limit / remaining gate |
|---|---|---|
| Five own documents,6real turns | audit-live-mvfmnry1.json; all complete; source/runtime `{live['deployed_commit']}` | Not a statistical success guarantee; prior failed/partial attempts retained |
| Hosted complete UI | audit-hosted-ui.json; actual PDF review/plan/what-if/illustrative receipt/Preflight/Passport/isolation/12language-width AA states | No real Google writes |
|100visitors/queue | audit-100-simulated.json | Provider simulated, zero real Gemini; plan objects are isolation fixtures |
| Bounded imports/errors | audit-hosted-boundaries.json; actual2MiBPDF,+1limit,empty/corrupt,chunked3MiB,health and OAuth recovery | Parser permits text PDFs only; no OCR |
| Source citations/MCP | audit-mcp.json; protected real loopback initialize/list/read continuation/search/proposals | Separate from actual cloud IAM acceptance |
| Installed Windows | audit-desktop-0.5.0.json, preserved-native-0.5.0.json | Contract/source equality and45/95, no model calls |
| Physical native | audit-native-observation-0.5.0.json | Actual recorded build Open/Cancel/import+refresh200; Save/banner/click pending after owner Escape |
| Public samples | audit-public-samples.json when present |13raw/ZIP hashes and trilingual instructions; not assumed from repository bytes |
| GitHub | audit-hosted-github.json when present | Only actual successful hosted read+later observation count; original fetch time retained |
| Calendar | calendar_acceptance_0_5.md | Setup done; actual consent/operations and independent visitor pending |
| Managed GCP | managed-preparation-0.5.0.json and organizer_window_runbook.md | Offline preparation only, no deployed resource; T0/coverage unknown |

Latest complete local suite209tests+3subtests;7IPC checks. Logs remain private on D:; non-gcp-0.5.0.json records the full-run log hash. F1–F5 remain locally implemented with real Calendar/full enhancement-level Gemini acceptance pending. Public current availability, alternative Gemini, managed historical acceptance and after-window readiness are separate statuses. No personal payment, card, trial, paid upgrade or contest submission.
''')
    print(json.dumps({'deployed_commit':health['deployed_commit'],'NON_GCP_READY':False,'github_background':proof['github']['background_verified'],'samples_public':proof['samples']['public_downloads_verified']}))

if __name__=='__main__':main()
