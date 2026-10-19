"""Record only actual 0.4.1 public results; preserve the previous release docs."""
import json,shutil
from pathlib import Path
root=Path(__file__).resolve().parents[1]
read=lambda name:json.loads((root/name).read_text(encoding='utf-8'))
live=read('docs/evidence/public-ai-acceptance-0.4.1.json')
load=read('docs/evidence/public-ai-100-simulated.json')
desktop=read('docs/evidence/public-ai-desktop-0.4.1.json')
workflow=read('docs/evidence/public-demo-browser-0.4.1.json')
assert live['verified'] and live['actual_complete_real_gemini_turns']==2 and load['passed'] and desktop['passed'] and workflow['passed']
commit=live['deployed_commit'];url=live['url'];deploy='dep-dbb348mi0phs73bb6u50'
paths=['README.md','STATUS.md','BLOCKERS.md','REQUIREMENTS.md','docs/final_integration_ledger.md','docs/final_judge_guide.md','docs/final_free_path.md','docs/final_cutover_plan.md','docs/cost_estimate.md','docs/final_native_check.md','release/README.md']
history=root/'docs/history/0.4.0-before-public-ai'
history.mkdir(parents=True,exist_ok=True)
for name in paths:
    target=history/name.replace('/','__')
    if not target.exists():shutil.copy2(root/name,target)
def write(name,text):(root/name).write_text(text.strip()+'\n',encoding='utf-8')
summary=f'''Public HTTPS **{url}** runs **0.4.1**, existing Render **Free** service `srv-dbajs73bc2fs73bm9mfg`, deploy `{deploy}`, runtime commit `{commit}`. No new infrastructure, paid upgrade, billing activation or personal payment was used.'''
verification='''Two originally clean automatic anonymous workspaces uploaded separate unseen synthetic documents and each completed a real Gemini/ADK/signed-MCP answer. No invitation, registration, Google login or visitor API key was used. Refresh resumed the same run. A later non-model test stage initially attempted planning before resolving the fixture conflict; its precondition was corrected and the remaining checks passed in the same two owned workspaces with zero additional model calls. This reuse is recorded explicitly, not counted as another pair of fresh visitors.

Actual first batch: one complete answer and one Google `504 DEADLINE_EXCEEDED`; that failure remains recorded. The next pair completed both questions. No hidden model retry, paid fallback, statistical success rate or latency guarantee is claimed. Published evidence contains metadata/hashes only; full answers, document citations, cookies and content screenshots remain in ignored private D: folders.

Separately, 100 real HTTP capability sessions/uploads/queue/history paths ran with the provider simulated: unique workspaces, foreign source/run/history/plan authorization, one outstanding turn per workspace, two workers, FIFO/fair quota tickets and 15-RPM rolling accounting passed. Plan objects in this load test are explicitly seeded isolation fixtures, not 100 solver or real-model acceptances. Zero actual Gemini calls. Final local suite:132 Python tests and3 subtests passed;6 IPC policy tests; queue refresh/cancel/reset and localized quota UI regressions passed.

The full hosted illustrative workflow passed: import, original evidence, explicit assignment mapping/conflict resolution, validated plan, what-if, illustrative approval/read-back receipt, execution events, real backend GitHub read, EN/RU/Kazakh, mobile, refresh and reset/isolation. Nine additional language/width states and automated AA checks passed in the real-AI workspaces. Installed0.4.1 main/preload/policy/renderer match source; anonymous public import/read-back/refresh, polling route authorization, reopen and CSRF reset passed with zero model calls. The original native profile still reads45 logged/95 explicitly remaining.'''
limits='''One outstanding question per workspace; FIFO queue with two workers and fair tickets before each actual model call. The account's observed limits are15RPM/250,000TPM/500RPD, not a remaining balance. Conservative context reservations, Pacific-midnight daily reset and authoritative provider429/backoff protect shared free capacity. No judge-specific reserve, number of codes or visit schedule. Normal anti-abuse and bounded queue/session capacity still apply. Anonymous cookie creation cannot independently identify people or defeat every distributed attacker.

Automatic sessions last up to two hours; Render Free can sleep and lose temporary SQLite/uploads/history/queue earlier on restart/redeploy. No durability or always-on Scheduler guarantee. Export a Workspace Passport for portable non-secret data. Reset/expiry removes documents, history and globally queued text/results; late results cannot recreate a deleted workspace. Active remote work is not claimed stopped merely because the browser stops waiting.'''
pending='''Original managed GCP Agent Engine criterion remains **UNMET / GCP_EXCEPTION_PENDING**. The existing trial is closed, prepayment is required, no usable credits were established, and D: CLI/ADC authentication is absent. Alternative Gemini hosting does not satisfy a deployed `projects/.../reasoningEngines/...` requirement. Organizer credits will not arrive; no personal spending or paid billing attachment is authorized.

Real Calendar remains separate and optional. The dedicated secondary target exists (`docs/connections.json`), but app OAuth client/runtime consent and real write/read-back are not accepted. Public Gemini grants no Calendar authority and does not receive private event data or Calendar mutation tools. External writes require separate user consent, exact target, fresh immutable preview and authenticated UI approval. Current public Calendar receipts are explicitly illustrative.

New0.4.1 unmodified native Open/Cancel/Save visibility, real import through that picker, notification banner and click/focus remain human observations. Automated import/API/policy contracts and historical0.1.1 picker/banner plus0.3 human45/95 restart evidence are separate. Current installed original-profile45/95 read-back is verified, not a new human picker claim.'''
evidence='''- `docs/evidence/public-ai-acceptance-0.4.1.json`: combined real public acceptance, with original clean-session evidence and explicit zero-model follow-up.
- `docs/evidence/public-ai-live-mvfe1dk2.json`: two actual complete Gemini/MCP outcomes, response hashes and retained later harness precondition failure.
- `docs/evidence/public-ai-first-provider-failure.json`: actual first Google504, retained separately.
- `docs/evidence/public-ai-100-simulated.json`:100-session simulated-provider queue/isolation.
- `docs/evidence/public-demo-browser-0.4.1.json`: hosted operational workflow and actual GitHub commit/read.
- `docs/evidence/public-ai-desktop-0.4.1.json`, `preserved-native-0.4.1.json`: actual installed source/IPC/session checks and original45/95.
- `docs/public_ai_access.md`: queue, security, processing conditions and limitations.'''
write('README.md',f'''# CampusPulse RELAY · 0.4.1

{summary}

Open the link: an isolated workspace is created automatically. Upload a permitted document, confirm free-service processing conditions, then ask RELAY. There is **no access code, registration, Google login or visitor API key**. The owner key remains on the server. Public AI access is independent of optional personal Calendar consent.

The free-service confirmation is for adult professional/hackathon evaluation in an eligible region outside EEA/UK/Switzerland, using permitted non-sensitive material. It is self-attestation, not registration or independent age/location verification. Unpaid inputs may be used for improvement and human review. [Gemini terms](https://ai.google.dev/gemini-api/terms).

RELAY retains source/page/version quotations and disagreements, validates CP-SAT plans, compares what-if/Minimal Rescue changes, previews illustrative Calendar effects and records read-back receipts. Progress & Remaining Work, Clarify First, Handoff Radar, Workspace Passport and EN/RU/Kazakh remain supported. **F1–F5 stay labeled locally implemented; real Calendar and full enhancement-level Gemini acceptance remain pending.** Actual source-grounded public Gemini acceptance is reported separately.

## Verified results

{verification}

## Shared free capacity

{limits}

## Run and release on D:

All controlled local dependencies, caches, profiles, temp and outputs stay under `D:\\projects\\CampusPulseRELAY`. Read/use `scripts/env.ps1`. Illustrative local development: `powershell.exe -NoProfile -ExecutionPolicy Bypass -File D:\\projects\\CampusPulseRELAY\\scripts\\dev.ps1`. No Google account is required. Server-only alternative Gemini: `scripts/run-alternative.ps1`, private DPAPI key configuration and HTTPS staging; never put keys in the frontend or desktop app. No permanent execution-policy or trust-root change is required.

Versioned installer/portable, full local frontend+Python illustrative bundle, exact source archive, editable presentation/PDF and checksums are indexed in `release/manifest.json` and `submission/0.4.1-public-ai-r1`. The manifest distinguishes archived source from the deployed runtime commit. Earlier sealed releases and installed0.4.0 backup remain unchanged. Binaries are unsigned. Read `release/README.md`.

## Remaining gates

{pending}

{evidence}

Deadline supplied by owner:20October2026,23:59; organizer timezone remains unconfirmed. Planning assumes UTC+5. No entry, organizer message or judge invitation was sent. Historical private-access documentation is preserved under `docs/history/0.4.0-before-public-ai` and does not describe current public access.
''')
write('STATUS.md',f'# CampusPulse RELAY0.4.1 · public queued Gemini verified\n\n{summary}\n\n{verification}\n\n{limits}\n\n{pending}\n\n{evidence}')
write('BLOCKERS.md',f'''# Remaining acceptance gates · 0.4.1

Public access is complete for the supported scope: **no invitation, registration, Google login or visitor API key**. {summary}

{pending}

For the public demo no owner action, judge count or visit window is required. Optional native/Calendar/managed-route steps are in `docs/remaining_actions_0.4.1.md`. Do not activate billing or pay to clear a gate.

{limits}

Automatic approval review rejected publishing a new evidence file containing complete generated-document answers/citations. The safer publication includes only metadata and response hashes; complete diagnostics remain privately on D:. The earlier separate Render-service creation rejection also remains respected: no new service was created. No workaround publishes the rejected content or creates that infrastructure.
''')
ledger=f'''# Requirement and evidence ledger · 0.4.1

{summary}

| Requirement | Actual result | Evidence / remaining gate |
|---|---|---|
| Public real Gemini/MCP | Two clean automatic anonymous sessions, independent unseen uploads and actual source-grounded answers. No codes, registration, Google login or visitor keys | public-ai-acceptance-0.4.1.json; actual alternative Gemini, not managed GCP |
| Isolation / authorization | Own documents, conversations, runs and plans; foreign access denied; internal/admin/test/invitation routes protected | Two actual workspaces plus100 simulated-provider HTTP workspaces |
| Shared fair queue | One outstanding turn per workspace, FIFO,2 workers, fair tickets per model call, observed quota ceilings, Pacific daily reset, provider backoff | test_public_ai_queue.py; zero actual Gemini in100-session load |
| Supported web operations | Import/evidence/conflict, plan/what-if, illustrative approved receipts, events, actual hosted GitHub read | public-demo-browser-0.4.1.json |
| EN/RU/Kazakh and mobile | Operational translations,9 extra language-width states, refresh, automated AA | Actual hosted browser evidence; no manual universal accessibility guarantee |
| Windows0.4.1 | Installed main/preload/policy/renderer match source; HTTPS anonymous import/read-back/refresh, poll authorization, reopen/reset/CSRF | public-ai-desktop-0.4.1.json;0 model calls; original45/95 remains |
| F1–F5 | **Locally implemented** | Real Calendar and full enhancement-level Gemini acceptance pending |
| Four additions / D1–D3 | Preserved Progress, Clarify, Handoff, Passport, Minimal Rescue, Preflight and independent challenge | Current132 Python suite plus historical detailed feature/live evidence |
| Original managed GCP | **UNMET / GCP_EXCEPTION_PENDING** | Trial closed/prepayment/no usable credits; no personal spend. No actual managed resource or managed cloud-to-MCP acceptance |
| Real Calendar | Dedicated secondary target exists; optional app/runtime consent and actual writes/read-back pending | docs/connections.json; illustrative receipts are not Google writes |
| Native interactions | Package/API contracts passed; original45/95 read-back passed | Actual new Open/Save/cancel/import/banner/click observations require the owner |
| Source / presentation / history | Public source, versioned manifest/archive and editable12-slide deck/PDF | Manifest records exact archived and deployed commits separately; prior releases hash-preserved |

{verification}

{evidence}
'''
write('REQUIREMENTS.md',ledger);write('docs/final_integration_ledger.md',ledger)
write('docs/final_judge_guide.md',f'''# Public demonstration guide · 0.4.1

Open **{url}**. A separate temporary workspace is created automatically; no invitation, registration, Google login or user API key. No visit schedule or expected judge count is required.

1. Choose EN/RU/Kazakh and import a permitted non-sensitive academic document. Inspect its original quoted evidence.
2. Confirm assignment identity/mapping where needed and explicitly resolve any deadline conflict. Generate a plan, compare what-if, then return to the baseline.
3. Review and explicitly approve the **illustrative local Calendar** preview. Inspect its receipt and execution events. It creates no Google event.
4. Confirm the adult eligible-region free-processing statement and ask Gemini about your uploaded source. Inspect actual tool events and source/page/version. Inputs may be used for improvement/human review; no confidential or personal material.
5. Refresh: the same queued run/history resumes without resubmitting it. A new browser profile receives a different workspace. Export a Workspace Passport before temporary state resets.

{limits}

{verification}

{pending}

Historical private test invitations are retired on this public host. Do not issue or distribute codes. The public AI path itself grants no Calendar permission. The unsigned Windows0.4.1 app uses this same HTTPS gateway; native settings and user files remain on D:. Current evidence and presentation paths are in the release manifest. No entry was submitted by Codex.
''')
write('docs/final_free_path.md',f'''# Free Gemini contingency · current public route

{summary}

Gemini Developer API Free tier project `gen-lang-client-0595303951`, model `gemini-3.5-flash-lite`, observed metadata `3.5-flash-lite-07-2026`. This is shared ADK + signed loopback Streamable HTTP MCP on the existing Free container, not Agent Engine.11 safe read/planning MCP tools are exposed to this model path; Calendar mutations and private Calendar details are excluded.

Non-secret production settings:

```text
RELAY_MODE=alternative_live
RELAY_INFERENCE_PROVIDER=gemini_developer
RELAY_DEPLOYMENT_MODE=alternative_hosted
GOOGLE_GENAI_USE_VERTEXAI=false
RELAY_GEMINI_DEVELOPER_MODEL=gemini-3.5-flash-lite
RELAY_GEMINI_FREE_ONLY=true
RELAY_PUBLIC_AI_ENABLED=true
RELAY_JUDGE_ENABLED=false
RELAY_MODEL_CALLS_PER_MINUTE=15
RELAY_MODEL_TOKENS_PER_MINUTE=250000
RELAY_MODEL_CALLS_PER_DAY=500
```

Keep `RELAY_GEMINI_API_KEY` only in the intended host secret environment. Local key decryption is server-only through `scripts/gemini-env.ps1`, separate from ordinary builds. Distinct server transport/context secrets, per-workspace signed bounded context, Secure capability cookies and CSRF remain enforced. Invitation/admin/test endpoints are closed publicly. API keys, cookies, uploaded documents and complete model answers are excluded from new public evidence.

{limits}

{verification}

See `public_ai_access.md`, `final_judge_guide.md` and `remaining_actions_0.4.1.md`. Historical private-invitation instructions are retained only in the versioned history; they are superseded.
''')
write('docs/final_cutover_plan.md',f'''# Completed public AI cutover · 0.4.1

{summary}

Branch `local/final-integration-0.4.0` and public `main` retain fast-forward history. Auto-deploy remains off. Existing `infra/Dockerfile.alternative`, one Free instance and server-only key are preserved. Public flag/quota values were merged without retrieving or logging the secret. The first deployment ran6f776da; the final runtime is `{commit}`. No new hosting resource or paid setting.

{verification}

New source-only documentation/test/evidence commits after the runtime commit may be archived in the release. The packager checks the deployed frontend/backend/runtime files are identical to archived source. No implicit deployment of documentation-only metadata is claimed.

{pending}
''')
write('docs/cost_estimate.md',f'''# Actual no-personal-spending route · 0.4.1

Personal spending authorization: **USD0**. No paid GCP resource, upgrade, card/prepayment or billing activation was used. No organizer credits are expected. Existing GCP trial is closed/prepayment-required and shows no usable credits; this is a blocker, not permission to pay. No account invoice or remaining balance is inferred from test tokens.

{summary}

Observed selected-model Free limits:15RPM,250,000TPM,500RPD. These are shared project limits, not a guaranteed remaining allowance; other clients consume the same project quota. Every actual model call reserves conservative context/output headroom. Max8 model calls/turn,3,000 output tokens/call, bounded600-second running phase; waiting jobs retain their two-hour temporary session deadline. SDK automatic retry attempts1. Provider429/backoff is authoritative; failures are visible and no paid fallback or silent replay occurs. [Rate limits](https://ai.google.dev/gemini-api/docs/rate-limits).

There is no private judge reserve or schedule.100-session load uses an injected simulated provider and spends **0 actual Gemini calls**. The accepted real public batch contains2 complete turns; a prior batch retains one Google504. Actual test samples are not a cost forecast, SLA or percentage.

The existing Render workspace was inspected as Hobby/no card. Keep Free compute, one instance, auto-deploy off, no additional database/disk/worker/cron/scaling. Dated previous included-usage observations are not a current guaranteed balance. Free service limits may suspend the service; do not pay to remove them. No keep-alive traffic is scheduled. [Render Free behavior](https://render.com/docs/free).

{limits}

Free-service professional/adult/eligible-region and non-sensitive-input conditions remain visible. [Gemini terms](https://ai.google.dev/gemini-api/terms). Real Calendar is optional and separate. Managed deployment requires verified eligible funding, coverage, balance, expiration and actual service quotas before any approval; budget alerts cannot guarantee a spending cap. The current managed route remains blocked. See `cloud_setup.md`.
''')
write('docs/remaining_actions_0.4.1.md',r'''# Exact remaining optional acceptance actions

**Public Gemini/MCP: no owner action is required.** Open the normal public link, upload permitted non-sensitive material, confirm free-processing conditions and ask. No invitations, judge count, registration, Google login or visitor API key.

## Native Windows observations

The installed0.4.1 package and original45 logged/95 remaining were verified. Actual new native dialog visibility and notification visibility/click are still separate human checks because the supported native automation helper failed initialization. No Windows setting or permanent execution policy change is needed.

Run in normal PowerShell:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "D:\projects\CampusPulseRELAY\scripts\recheck_final_native.ps1"
```

1. Connections → Import a file: observe the real Windows picker, then Cancel. Record picker appearance and cancellation separately.
2. Import again and select `D:\projects\CampusPulseRELAY\.local\native-verification\0.4.1-final\native-optics-0.4.1.md`. Confirm the source appears and its original text opens; this is the actual import result, separate from picker appearance.
3. Progress & continuity → Workspace Passport: Cancel once, then select `D:\projects\CampusPulseRELAY\.local\native-verification\0.4.1-final\native-input.relay.json`; review and explicitly import as fresh copy. Check45 logged/95 remaining. Export with the real Save dialog to a new D: file, close/reopen and check again. Keep Save/restore/reopen results separate.
4. Connections → Send test notification: observe the Windows banner or Notification Center entry, click it and report whether the intended RELAY window focuses. Visibility and click/focus are separate. No Google login or settings change.

The launcher creates only a separate D: verification profile; the original backend/profile is preserved. `-PublicGateway` instead uses the public queue and needs no invitation.

## Optional personal Calendar

The dedicated secondary calendar exists and connector read access was reverified; app OAuth is not configured. Current public actions are illustrative. If the owner voluntarily chooses this separate acceptance:

1. Use an owned project with the standard Calendar API available without activating paid billing; create a Web OAuth client for the intended **private HTTPS** gateway. Add its exact `/auth/callback` redirect and the owner as a Testing user. Do not add payment to enable an unrelated service.
2. Configure `RELAY_OAUTH_CLIENT_ID`, `RELAY_OAUTH_CLIENT_SECRET`, a new Fernet `RELAY_TOKEN_ENCRYPTION_KEY` and exact `RELAY_GATEWAY_URL` privately in that normal gateway. Never paste secrets here. Do not enable Google connection routes or send private events through the anonymous unpaid-Gemini host.
3. Open Connect Google in system browser, review actual Google scopes and grant consent personally. Browser/connector login does not authorize the application automatically.
4. Select the dedicated non-primary Calendar named in `docs/connections.json`. Review the actual immutable event preview and explicitly approve it in the authenticated application UI. Only then verify real write/read-back, idempotent retry and guarded compensation. This general chat instruction does not approve a future unseen write.

## Original managed Agent Engine

The trial is closed/prepayment-required, credits unavailable, D: gcloud/ADC unauthenticated. No personal payment or billing activation is permitted. No action here requires the owner to pay. Without an existing eligible non-billable trial covering the intended resources, this criterion remains UNMET. If such an account independently becomes available, sign in with `scripts/inspect-access.ps1 -Login`, verify exact project/account/coverage/balance/expiry/quotas, then review a bounded credit-only deployment envelope before provisioning. Otherwise the owner can seek an explicit organizer exception; no message or contest submission has been sent by Codex.
''')
write('docs/final_native_check.md','# Native0.4.1 residual observations\n\nSee `remaining_actions_0.4.1.md` for the exact sequence. Current package/import/poll/reset/reopen contracts and original45/95 are verified; actual new unmodified Open/Save/cancel and notification/banner/click remain human observations. Historical results are preserved separately. Public Gemini access requires no invitation or Google login.')
write('release/README.md',f'''# CampusPulse RELAY0.4.1 · public AI release

{summary}

Manifest/checksums name exact archived source, separately deployed runtime, unsigned Windows installer/portable, complete local React+Python illustrative bundle and editable12-slide PPTX/PDF. New revision: `0.4.1-public-ai-r1`. Earlier sealed releases and installed0.4.0-hosted backup retain verified hashes.

Use adjacent `windows/Install-D.cmd` / `windows/Launch-Portable-D.cmd`: installer/portable extraction TEMP/TMP/TMPDIR and user profile stay on D:. Installer destination is fixed to `D:\\projects\\CampusPulseRELAY\\installed\\CampusPulse RELAY`; shortcuts on C: are disabled. For local illustrative use override only the launch process with `RELAY_GATEWAY_URL=http://127.0.0.1:8000` and keep its backend running. Full live server dependencies/configuration are in the source archive; never put the key in Electron.

The web ZIP includes frontend assets and actual Python backend, uses `scripts/run-web-bundle.ps1` and minimal locked dependencies on D:. It provides the local illustrative path without Google credentials; the public live Gemini service is deployed from the full server source. No static localhost-calling frontend is presented as the hosted demo.

{verification}

{pending}

PPTX retains editable text/shapes; PDF uses reviewed slide renders. Native PowerPoint opening is not claimed. New public evidence excludes complete model answers, uploaded documents/citations, cookies and content screenshots; these remain privately on D:. No credentials or generated grants are packaged. Read the manifest and `docs/remaining_actions_0.4.1.md`.
''')
proof=dict(version='0.4.1',public_url=url,provider='Render',plan='Free',service_id='srv-dbajs73bc2fs73bm9mfg',deploy_id=deploy,deployed_commit=commit,live_finished_at='2026-10-19T15:08:14.089958Z',verified=True,real_gemini_verified=True,public_access='automatic_anonymous_isolated_queue',personal_spending_authorized_usd=0,new_resources_created=False,paid_upgrade=False,mandatory_managed_gcp='UNMET_GCP_EXCEPTION_PENDING',real_calendar='pending_optional_separate_consent',new_native_dialog_banner_click='pending_human',evidence=dict(real_public='docs/evidence/public-ai-acceptance-0.4.1.json',simulated_100='docs/evidence/public-ai-100-simulated.json',workflow='docs/evidence/public-demo-browser-0.4.1.json',installed='docs/evidence/public-ai-desktop-0.4.1.json',preserved_native='docs/evidence/preserved-native-0.4.1.json'),previous_failures_retained=True,complete_answers_or_documents_published=False)
write('docs/evidence/public-deployment-0.4.1.json',json.dumps(proof,indent=2))
print(json.dumps(dict(updated_docs=len(paths)+2,deployed_commit=commit,public_real_turns=2,simulated_sessions=100)))
