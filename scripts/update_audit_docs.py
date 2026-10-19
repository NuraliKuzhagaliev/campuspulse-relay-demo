"""Start an audit release without rewriting any sealed release or its evidence."""
from pathlib import Path
import shutil,json,hashlib
root=Path(__file__).resolve().parents[1];history=root/'docs/history/0.4.1-before-audit'
history.mkdir(parents=True,exist_ok=True)
for name in ['README.md','STATUS.md','REQUIREMENTS.md','BLOCKERS.md','docs/cloud_setup.md','docs/judge_quickstart.md']:
    source=root/name
    if not source.exists():continue
    target=history/name;target.parent.mkdir(parents=True,exist_ok=True)
    if not target.exists():shutil.copyfile(source,target)
readme='''# CampusPulse RELAY · 0.5.0 audit candidate

Public application: **https://campuspulse-relay-demo.onrender.com/**. Source and public synthetic samples are being upgraded from the preserved0.4.1 release. This candidate is **NOT YET NON_GCP_READY**: hosted multilingual Gemini confirmation, current installed/native observations and actual Calendar consent/write/read-back are acceptance gates. Check `docs/audit_U1_U16.md` and current deployment evidence for the exact running commit; a source version is not deployment proof.

Open the ordinary link: no invitation, registration, Google sign-in or visitor API key for AI. Choose **Use my own data** for a clean isolated workspace, or **Open example** for separately labeled illustrative coursework. Switching preserves both temporary workspaces. The owner Gemini key stays on the server. Free-service processing requires the displayed eligibility/non-sensitive data confirmation; no fabricated AI or hidden paid fallback.

## Try with our sample data

Open **https://campuspulse-relay-demo.onrender.com/samples/** for individual downloads, EN/RU/Kazakh instructions, expected results, reference week/timezone and the compact **judge_sample_pack.zip**. Repository copies: `public/samples/README.md` and `public/samples/expected-results.json`. Samples are synthetic and permission-free. Source import, Passport restore and Preflight draft are separate inputs. The public URLs are accepted only after a fresh browser download/unzip/use check on the deployed revision.

PDF(text layer), Markdown, TXT and ICS: maximum2MiB;100PDFpages/250,000extracted characters; no scanned OCR. PDF parsing runs in a disposable CPU/memory/wall-time bounded worker. Plain prose and tables use real Gemini/MCP proposals, exact page quotes and explicit review of each assignment. Unknown dates, effort and academic context remain unknown until clarified. Source45minutes is retained exactly; scheduling rounds allocation up to60. Logged45 and explicitly remaining95 are separate reports, never subtracted automatically.

Planning context has date/time/timezone controls; seven-day timeline supports weekend/overnight/DST geometry. Conflicts retain both sources. Confirmed coursework drives plans/what-if/next actions/Preflight/progress/Passport. Empty or unassessed rubric cannot imply ready. Calendar previews/receipts use the explicitly illustrative adapter unless the visitor separately connects an authorized Calendar and approves exact actions. F1–F5 remain **locally implemented; real Calendar and full enhancement-level Gemini acceptance pending**.

One outstanding AI turn per workspace; a fair shared queue protects observed free API limits and provider backoff. Existing100-session provider simulation is preserved; audit reruns are separately named and spend zero Gemini quota. Anonymous cookie isolation is not a claim to identify every person or defeat distributed abuse. Hosting is the existing Render **Free** service, with no upgrade. It may sleep; polling runs while awake and stops during sleep/restart. Original GitHub fetch time/commit are retained by shared immutable observation caching; upstream429 remains an error, not a fresh read.

Storage is temporary: session lifetime up to2hours and earlier restart/redeploy reset. Export a private Workspace Passport. Secrets, approvals and writable connections are not portable. Existing sealed releases, installer backups and original45/95 data are preserved on D:.

## GCP tomorrow: organizer window, no personal payment

Latest owner-supplied organizer update: tutorial20October2026at10:00 (UTC+5 planning assumption),12hours of access after actual activation. T0 and expiry are **not yet verified**. Tomorrow inspect actual eligible project/principal/billing visibility/coverage/balance where exposed/expiry/model/quotas before provisioning. Do not assume the free AI Studio project is eligible. Personal payment, billing attachment, card/prepayment, paid upgrades and a personal Free Trial are prohibited. Existing personal trial limitations are historical, not the current organizer plan.

Actual Agent Engine remains **pending**. Alternative Gemini is not a `projects/.../reasoningEngines/...` deployment. Read `docs/organizer_window_runbook.md`; preserve evidence outside the lab and retire only owned ledger resources before expiry. Current managed availability and historical acceptance must remain separate.

## Local setup and release history

Everything project-controlled stays under `D:\\projects\\CampusPulseRELAY`: dependencies, caches, downloads, profiles, temp, builds and deliverables. Use `scripts/env.ps1`. Local illustrative development: `powershell.exe -NoProfile -ExecutionPolicy Bypass -File D:\\projects\\CampusPulseRELAY\\scripts\\dev.ps1`. No Google sign-in needed. Server-only free Gemini uses `scripts/run-alternative.ps1`; optional Calendar configuration: `docs/calendar_acceptance_0_5.md`. Never load keys into renderer/desktop builds.

The previous sealed0.4.1manifest/packages/presentation remain intact while the audit candidate is verified. New installer, portable, source/web ZIPs, editable PPTX and PDF will receive a separate versioned manifest after actual checks. Windows binaries are unsigned. New native Open/Cancel/Save/banner/click are human observations, separate from automated contracts and historical0.1.1/0.3 checks.
'''
(root/'README.md').write_text(readme,encoding='utf-8')
(root/'STATUS.md').write_text('# Audit release0.5.0 · acceptance in progress\n\n'+readme.split('## GCP tomorrow:')[0].split('## Try with')[0]+'\nActual local UI: multipage import, per-entity confirmation, own/example isolation, planning, what-if, illustrative receipt, Preflight,45/95, Passport download/restore/reopen and12 language/width AA states passed. These are local results, not deployed Gemini or Google Calendar acceptance.\n\nSee docs/audit_U1_U16.md; managed GCP pending organizer activation tomorrow.\n',encoding='utf-8')
(root/'BLOCKERS.md').write_text('''# Actual external gates · audit0.5.0

- Organizer project/window/covered services are not activated or verified yet. No personal spending allowed. Actual managed resource and cloud-to-MCP acceptance remain pending.
- Calendar app OAuth client/consent/publishing eligibility and real selected-target write/read-back are pending. Technical setup and exact actions: docs/calendar_acceptance_0_5.md. A coding-tool connector is not app consent.
- New installed native picker/cancel/import/save/notification visibility/click observations require the owner when the corrected new package is ready. API/package checks and prior human observations stay separate.
- Hosted audit Gemini/own-document acceptance and current GitHub recovery have not yet run on0.5.0. No readiness claim until those checks pass.
''',encoding='utf-8')
(root/'docs/judge_quickstart.md').write_text('''# Independent public evaluation · audit0.5.0

1. Open https://campuspulse-relay-demo.onrender.com/ in a clean browser. No invite, registration, Google login or personal API key for AI. A free host can cold-start; wait/retry without resubmitting an active question.
2. Choose Use my own data. Open https://campuspulse-relay-demo.onrender.com/samples/ and read the sample README/expected results, or select your own permitted non-sensitive academic document.
3. Import through Connections/Evidence. Prose/tables: confirm free-service processing conditions, then Propose with Gemini. Review exact citations and each assignment independently; clarify missing context/date/effort rather than guess. Confirm this assignment changes only that entity.
4. Set Planning context dates/timezone/availability. Resolve cited conflicts. Repair the week; inspect next action, compare what-if, and check a draft with Preflight. Unassessed requirements do not imply ready.
5. Review and approve explicitly illustrative Calendar effects unless separately authorized real Calendar is connected. Inspect the receipt and execution events. Test45minutes logged and95explicit remaining, export a Passport and restore a fresh copy; approvals/tokens are absent. Switch EN/RU/Kazakh and test mobile/refresh.
6. A second clean browser must see none of the first visitor's documents/history/plans. The example is a separate workspace. Temporary storage may reset on sleep/restart/redeploy; export your work.

Current managed GCP is pending organizer activation20October;12hours start at actual T0, not an assumed tutorial time. No personal trial/payment is authorized. Check current release/deployment evidence, not historical green status. Real Calendar consent/write/read-back and current native physical observations are separate acceptance gates. No codes, judge-count or visit schedule is required.
''',encoding='utf-8')
print('Audit documentation started; prior release documents preserved.')
