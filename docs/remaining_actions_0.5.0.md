# Exact remaining actions · 0.5.0

All project-controlled assets stay in `D:\projects\CampusPulseRELAY`. Current public access needs no invitation or Google sign-in. Read `docs/evidence/non-gcp-0.5.0.json` for actual evidence/status, not an implied all-ready claim.

## Calendar owner step

The owner enabled Calendar API, created/configured the web OAuth client and published Audience to Production. Server secrets and exact HTTPS gateway are configured. The earlier real callback was rejected before a new connection completed; the owner reports copying the authorization link into another browser/window. The source browser binding does not transfer with a URL, and an earlier request also expired. Web requests now last15minutes, with an independent private browser nonce, state, PKCE and one-use server claim. Desktop pairing still expires after5minutes. Expired/cancelled/mismatched browser callbacks show a trilingual recovery page without echoing codes or tokens. These protocol checks are simulated; actual Google consent still needs completion.

When ready, open the ordinary public homepage in the browser that works for you, then start a NEW flow there. Do not transfer a Google authorization link or callback address between browser sessions:

1. Open https://campuspulse-relay-demo.onrender.com/ in one browser → Подключения / Connections → Подключить Google в системном браузере.
2. Select the intended Google account. Continue, then grant only the shown app-created-calendar permission. Complete within15minutes and wait for RELAY. Report any payment, policy/verification warning or broader requested access; never send an API key, client secret, callback URL or authorization code here.
3. Consent alone grants no study-block approval. Choose **Create a separate study calendar**. Record its actual returned Calendar ID privately. Existing unrelated calendars are not public write targets.
4. The remaining verification is a synthetic plan → exact immutable preview → explicit real-action approval → Google event ID/ETag/link read-back → safe retry without duplicates → guarded undo → disconnect/revocation, cancellation and permission-loss behavior. We will record each real result separately. No actual Calendar event was claimed by simulated tests.

Browser-control rules require the owner to grant new persistent Google access. Console setup and Production status do not replace this consent or operation acceptance.

## Dedicated GitHub read credential or quota recovery

The hosted backend returned `UPSTREAM_RATE_LIMITED` from shared GitHub public quota. Singleflight caching, conditional reads, immutable content reuse and backoff passed locally. A token from a broad account login is not copied into the app.

If the public quota does not recover, create a fine-grained token at https://github.com/settings/personal-access-tokens/new: name **CampusPulse RELAY demo read**, expiry7days, **Only select repositories → campuspulse-relay-demo**, repository permissions **Contents Read-only**, **Issues Read-only**, **Metadata Read-only**, no account permissions. Save it through the hidden prompt:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "D:\projects\CampusPulseRELAY\scripts\configure-github-read.ps1"
```

The owner has saved the dedicated credential locally and local contents/issues read requests returned200. A Render field mix-up placed or proposed the token under the Calendar encryption variable: restore the protected original with `scripts/copy-render-credential.ps1 -Name TokenEncryptionKey`, paste only into RELAY_TOKEN_ENCRYPTION_KEY and Save only. Then use `-Name GitHubToken` for the separate RELAY_GITHUB_TOKEN field and Save only. `-Name ClearClipboard` overwrites the clipboard with a non-secret placeholder (Windows PowerShell rejects an empty string). Do not deploy until both fields are confirmed. No value is printed. The secret stays in current-user DPAPI on D: until an authorized direct transfer to the existing Free Render backend. Then verify an actual hosted read and a later server observation with the browser closed, retaining the original immutable fetch time. Creating/configuring a credential is not itself that acceptance.

## Current native observations

The actual0.5.0 Windows picker appeared; Cancel and the owner-selected Markdown import passed. Sanitized desktop trace confirms selection → file read → `POST /api/import-native`200 → `GET /api/state`200 → saved snapshot. The original preserved local profile still reads45logged/95remaining. Current rebuilt installed package main/preload/renderer and every required runtime asset match source. Native Save and notification results are not inferred from IPC tests or historical0.1.1 evidence.

Windows control was stopped by the owner using Escape. It will not resume without a new request. For a later manual recheck, the prepared launcher is:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "D:\projects\CampusPulseRELAY\scripts\recheck_audit_native.ps1"
```

It opens the same separate D: verification profile using the public gateway. The accessibility launch flag does not replace or modify Windows dialogs. If hosting reset the temporary workspace, reimport `D:\projects\CampusPulseRELAY\.local\native-verification\0.5.0-audit\native-audit-0.5.0.md` through the real picker.

Remaining observations: Passport preview → Download → actual native Save dialog → Cancel; reopen and save on D: → actual Passport picker/reimport → reopen and verify restored values. Separately, Connections → Send test notification → observe the actual Windows banner or Notification Center entry → click it and verify RELAY focus/evidence. Report appearance, successful action, persistence and click/focus separately. No Windows security/privacy setting change is required.

## Organizer T0

Read `docs/organizer_window_runbook.md`. Supply the actual activation instructions, assigned principal/project, expiry and coverage. Inspect billing/credit fields where visible and retain unknown/hidden fields honestly. Do not activate a personal trial, attach personal billing or pay. Only then create the minimal owned covered resources, deploy/discover the exact Agent Engine, activate the authenticated shared-state bridge, run actual remote multi-turn/isolation/Windows acceptance, and retire only owned ledger resources before expiry. An offline SDK package or alternative Gemini answer does not satisfy the managed requirement.
