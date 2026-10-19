"""Update current ledgers only after actual hosted and installed acceptance."""
import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
p=json.loads((root/'docs/evidence/public-deployment-0.4.0.json').read_text())
assert p['verified'] and p['real_gemini_verified']
commit=p['deployed_commit'];url=p['public_url']

def edit(name,changes,append=''):
    path=root/name;text=path.read_text(encoding='utf-8-sig')
    for before,after in changes:
        assert before in text,(name,before)
        text=text.replace(before,after)
    path.write_text(text+append,encoding='utf-8')

hosted=f'Actual hosted0.4.0 evidence: `docs/evidence/public-deployment-0.4.0.json`. Existing Render Free service `{p["service_id"]}`, deploy `{p["deploy_id"]}`, commit `{commit}`. Valid public HTTPS was checked without a certificate bypass. Eight complete real browser model turns and {p["actual_complete_installed_turns"]} installed Windows model turns passed. One earlier hosted turn timed out and remains recorded; this sample is not a reliability percentage. Installed demo reset initially failed separately from successful import/chat, then exact IPC route/CSRF repair, reinstall and repeat passed. All Calendar receipts remain illustrative. New native dialog/banner/click observations and mandatory managed GCP acceptance remain separate.'
edit('README.md',[
('Existing public demo: **https://campuspulse-relay-demo.onrender.com**, currently **0.2.1**. Hosted0.4 is pending the owner\'s server-side key save and verified cutover.',f'Public web: **{url}**, verified **0.4.0** on the existing Render Free service. Actual Gemini Developer/ADK/MCP acceptance passed in isolated web and installed Windows sessions.'),
('Use the **existing** Free Render service in the authorized workspace. Review `docs/final_cutover_plan.md`; owner saves `RELAY_GEMINI_API_KEY` using Save only, then publish the exact pushed source with `infra/Dockerfile.alternative`, one worker, auto-deploy off. No new infrastructure/paid upgrade. Run fresh public HTTPS and installed Windows acceptance before marking cutover verified.',f'The **existing** Free Render service was updated using `infra/Dockerfile.alternative`, one worker, auto-deploy off. The owner saved the eligible key privately; its value was never read or logged. Public and installed Windows HTTPS acceptance passed at commit `{commit}`. No new infrastructure or paid upgrade was created.')], '\n## Public0.4 acceptance\n\n'+hosted+'\n')
(root/'STATUS.md').write_text(f'''# CampusPulse RELAY0.4.0: hosted alternative Gemini verified

Public HTTPS: {url}. Existing Render **Free**, deploy `{p['deploy_id']}`, exact deployed commit `{commit}`. Actual browser and installed Windows flows passed. No new hosting resource, billing change or paid GCP resource was created. Personal spending authorization remains USD0.

{hosted}

The public illustrative path supports new file import, exact evidence/conflict choice, deterministic plans, what-if comparison, explicit illustrative approval/read-back receipts, execution events and live GitHub reads. EN/RU/KK and mobile/refresh/isolation were checked. Anonymous visitors cannot consume model quota. Four explicitly authorized one-use invitations were confined to agent-owned test workspaces; no invitations or messages were sent to other people.

Original GCP criterion remains **UNMET / GCP_EXCEPTION_PENDING**, and real Calendar consent/write/read-back remains pending. This is not READY_FOR_SUBMISSION against the unchanged original managed-deployment criterion. F1–F5 remain **locally implemented**, with real Calendar and full Gemini acceptance pending. Free storage can reset on sleep/restart/deployment and is not durable or always running.

Preserved local checks:121 Python pass,13 browser pass/1 public-only skip,4 IPC policy pass, separate localized quota regression. A new two-test owner-clock regression covers the observed83-second skew without widening the server's60-second signature check. Original installed workspace45 logged/95 remaining, old releases and the sealed `0.4.0-local-integration-r1` candidate remain preserved. New native Open/Save/cancel/notification visibility/click observations are still separate human gates.

Deadline reported20October2026 at23:59, organizer timezone unconfirmed. Planning UTC+5, internal freeze20October20:00 local. No entry submitted or organizer/judge message sent. Current release manifest distinguishes exact archived source from the actual deployed runtime commit. All controlled local files, dependencies, profiles, caches and outputs remain on D:.
''',encoding='utf-8')
edit('BLOCKERS.md',[
('1. **Existing Render secret/cutover:** owner must save the free Gemini key to `RELAY_GEMINI_API_KEY` in the prepared Environment row and choose Save only. Current public service is still0.2.1. No hosted0.4 or Windows HTTPS model query has been verified. Exact target/rollback/checks: `docs/final_cutover_plan.md`.',f'1. **Existing Render cutover completed:** public0.4 and installed Windows real Gemini/MCP queries passed at `{commit}`. This clears the former secret/cutover blocker only. Exact results and retained first timeout: `docs/evidence/public-deployment-0.4.0.json`.')])
intro='Baseline0.3.0-r1 and all prior sealed artifacts remain preserved. Current installed/local integration candidate: **0.4.0**. Actual public service remains **0.2.1** at commit `83552161ec22c7cf44746433425d3b2b99e042c4`. This candidate is not READY_FOR_SUBMISSION or a completed hosted0.4 demo.'
for name in ['REQUIREMENTS.md','docs/final_integration_ledger.md']:
 edit(name,[(intro,f'Baseline0.3.0-r1 and every prior sealed release remain preserved. Current installed and public version: **0.4.0**. Existing Render Free deployment `{p["deploy_id"]}` runs commit `{commit}`. Hosted alternative Gemini is verified; original managed GCP remains UNMET / GCP_EXCEPTION_PENDING, so this is not READY_FOR_SUBMISSION against that original criterion.'),
 ('Sleeping free host is not an always-running Scheduler. Full hosted/cloud acceptance pending','Hosted Gemini/MCP acceptance passed; sleeping free host is not an always-running Scheduler. Managed GCP acceptance pending'),
 ('New unmodified native Open/Save/cancel, notification click, public0.4 and Windows HTTPS model query pending','Public0.4 and installed Windows HTTPS model query passed. New unmodified native Open/Save/cancel and notification click remain pending'),
 ('Hosted deployment evidence and judging count/window still unconfirmed','Hosted deployment evidence recorded. Actual judging count/window still unconfirmed'),
 ('Existing Free Render service preserved, no card.0.4 cutover target prepared with rollback, private AI invitation and separate visitor workspaces','Existing Free Render service updated to0.4; actual private Gemini sessions and separate visitor workspaces verified'),
 ('Owner must save eligible free key in existing service, then deploy and test actual HTTPS path. No hosted0.4 success inferred','Owner key saved privately; hosted and installed HTTPS acceptance passed. No judge invitations distributed; judging window/eligibility needs confirmation')], '\n'+hosted+'\n')
(root/'docs/deployment_proof.md').write_text(f'''# Actual public deployment evidence

{hosted}

The owner saved `RELAY_GEMINI_API_KEY` privately in the existing service. Non-secret settings were merged without pulling secret values into tool output. That API update unexpectedly triggered old branch build `dep-dbb212tg1s2s73dvhe1g`, which was canceled before publication. Then branch `local/final-integration-0.4.0`, Dockerfile `infra/Dockerfile.alternative`, health `/api/health` and auto-deploy off were verified. Standard deployment `{p['deploy_id']}` became live at `{p['deploy_finished_at']}`. Previous deployment `dep-dbal14m1egvs73b4fp8g` / source `83552161ec22c7cf44746433425d3b2b99e042c4` is the historical rollback reference; no new service was created.

The frontend requested only its own public origin during the complete anonymous test. Python backend, ADK and authenticated MCP run in the same existing container. Model `gemini-3.5-flash-lite` returned runtime and gateway revision `{commit}`. Server-side GitHub read observed the configured repository default-branch commit separately; it is not the deployment commit.

Owner invitation issuance initially returned403 because the local clock lagged about83seconds. The local issuer now obtains a normal-TLS HTTPS server timestamp, requires RTT<=10seconds and skew<=300seconds, and preserves the server60-second signature window. Two deterministic regressions passed. Only the four specifically approved test invitations were issued; no Calendar authority was granted.

The first hosted model run timed out after a real tool observation. One bounded repeat in the same two authorized test workspaces completed; the original failure is retained. Public browser entry, uploads, conflict, plan, what-if, illustrative receipt, EN/RU/KK/mobile/refresh/isolation, protected routes, real model turns/GitHub and installed Windows HTTPS query are indexed in the machine-readable evidence. No statistical success/SLA or cold-start guarantee is inferred.

GCP account inspection remains `evidence/final-account-assessment.json`: closed trial, prepayment required, no visible credit balance/expiry. No payment or billing change was authorized/performed. Managed Agent Engine/cloud-to-MCP Google identity and real Calendar remain unverified. Previous local0.4 documentation is retained in `history/0.4.0-before-public-cutover/`; previous public0.2 evidence remains unchanged.
''',encoding='utf-8')
edit('docs/final_judge_guide.md',[
('Until the0.4 cutover is verified, the public service remains the preserved0.2.1 illustrative demo. A prepared0.4 build or local real Gemini run does not change that fact.',f'Public0.4.0 and actual alternative Gemini/MCP were verified at commit `{commit}`. Original managed GCP and real Calendar are still pending.'),
('## Private real Gemini evaluation after0.4 cutover','## Private real Gemini evaluation'),
('Do not infer that current public0.2.1 supplies every0.4 addition before cutover.','Installed0.4.0 was checked against the actual public HTTPS backend and retained its test workspace/conversation after reopening.')], '\nThe four invitations used for implementation acceptance were authorized solely for agent-owned tests. Do not distribute them to judges. Obtain the owner\'s explicit authorization for the intended judge count/window before issuing and distributing new private access. The owner issuer uses the authenticated HTTPS server clock within bounded skew; server signature validation remains60seconds.\n')
edit('docs/final_free_path.md',[
('Its currently live0.2.1 deployment/commit remains the rollback reference until the verified cutover.','Actual0.4.0 public cutover and real Gemini/MCP acceptance are recorded in `evidence/public-deployment-0.4.0.json`. The former0.2.1 deployment remains the historical rollback reference.'),
('The owner can complete the exact prepared secret field.','The owner completed the private secret field before the verified deployment; its value was never read or logged.')], '\nHosted0.4 acceptance is now complete for the documented alternative route; it does not amend the managed GCP criterion. Four AI-only invitations were issued with explicit owner authorization for these agent-owned tests only. Initial owner-clock skew and first model timeout are retained in deployment evidence.\n')
edit('docs/cost_estimate.md',[
('A short free staging service plus the retained illustrative fallback fit current included hours; verify actual usage again before scaling tests.','No separate staging service was created; the existing Free service was updated. Reported included usage is a dated observation, not a fresh remaining balance. Verify actual usage again before any additional work or scaling.')], '\nActual public0.4 tests used the existing Free container and free Gemini path only; one early timeout remains recorded. No invoice or final remaining quota balance has been inferred. No paid fallback was enabled.\n')
edit('docs/test_results.md',[
('Public remains0.2.1; hosted0.4, installed Windows public query, real Calendar, managed GCP and always-running hosted autonomy have not passed.','Public0.4 and installed Windows public query now pass separately in `evidence/public-deployment-0.4.0.json`. Real Calendar, managed GCP, always-running hosted autonomy and new native visibility/click checks remain unverified.')], '\n'+hosted+'\n')
edit('release/README.md',[
('This is a local Gemini-verified candidate, not a completed hosted0.4 or managed-GCP submission. Current public service remains0.2.1 until verified cutover.','Public0.4 alternative Gemini acceptance is now verified, including the installed Windows HTTPS path. Managed GCP and real Calendar remain pending; this is not a completed managed-GCP submission.'),
('Until the0.4 backend cutover, use the explicit local launch environment','For local offline-independent illustrative work, use the explicit local launch environment')], '\n'+hosted+'\n')
edit('docs/final_native_check.md',[
('Only after public0.4 Gemini cutover is verified, relaunch this script with `-PublicGateway`,','Public0.4 and the installed Windows HTTPS Gemini/MCP query have now passed automated acceptance. For a separate human repetition, relaunch this script with `-PublicGateway`,')])
cutover=root/'docs/final_cutover_plan.md'
text=cutover.read_text();cutover.write_text('> Executed on2026-10-19: existing-service0.4 cutover verified. See `evidence/public-deployment-0.4.0.json`. The following is the retained reviewable plan; its key-save/verification steps have been completed. Original managed GCP and real Calendar remain pending.\n\n'+text,encoding='utf-8')
print('Updated current hosted ledgers from actual passing evidence; preserved pre-cutover history.')
