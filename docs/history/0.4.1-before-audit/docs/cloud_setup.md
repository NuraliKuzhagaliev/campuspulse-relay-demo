# Verified funding and account setup - final phase

Organizer credits will not be supplied. Do not wait for them. The original managed Agent Engine path is preferred only if an actual eligible non-billable Free Trial is available. Personal spending, prepayment, paid activation/upgrades and billing attachment remain unauthorized.

## Actual account assessment,19 October2026

The authenticated Console shows an existing **Free trial account**, closed, with a prepayment banner. Credits has no issued entries. The D: gcloud configuration has no active account/ADC. No usable trial balance, expiry, eligible dedicated project or runtime quota is established. No payment was made. This blocks RouteA; it does not establish a Google outage.

AI Studio separately reports Default Gemini Project `gen-lang-client-0595303951` on **Free tier**. The owner securely configured its key on D:. A real metadata request and Gemini/MCP/public GitHub smoke passed. This powers RouteB, not managed Agent Engine. See `final_free_path.md`.

## RouteA preparation; no provisioning currently authorized

1. Only if an existing eligible non-billable trial becomes available, inspect its actual account type/open status, project, covered services, balance, expiration and quotas. Owner sign-in command: `powershell.exe -NoProfile -ExecutionPolicy Bypass -File D:\projects\CampusPulseRELAY\scripts\inspect-access.ps1 -Login`. Browser/Calendar connector login does not authenticate CLI/ADC.
2. Do not make a payment or attach billing. A paid account carrying credits is not a non-billable trial. Owner facts must distinguish Console observations from API-verified project/billing state.
3. `scripts/record-funding.ps1` reads the exact existing billing association/account, records separately labeled owner-confirmed type/eligibility/coverage/balance/expiry and saves `.local/funding-verification.json`. It does not approve a budget or activate funding. The historical organizer-only recorder is retired; no fake organizer record is generated.
4. Review an exact credit-usage envelope, reserve and duration before deployment. `relay/funding.py` rejects stale/future records, mismatched project/account, paid/unverified sources, missing coverage or insufficient balance/expiry. Both deployment entry points require the record plus an explicitly approved positive envelope. USD25/72hours remains an old unapproved estimate, never personal-spend permission.
5. Planned resources remain one managed runtime, dedicated gateway/MCP identities/services, Firestore, private bucket/image/secrets and authenticated Scheduler. No selected funded project exists. Region candidate `us-central1` and Vertex model must be verified against that trial before creation; model names/quota are not inherited from AI Studio.
6. After actual eligible funding and explicit usage authorization, configure cloud-only ADC using `scripts/connect-gcp.ps1`, then run `scripts/preflight.py`. Its new final-phase evidence filename preserves the original record. Deploy only after IAM/API/region/model/store/spend-cap review; no plan is claimed executed.

## Calendar remains independent

The dedicated Calendar ID is in `docs/connections.json`; no primary calendar is selected automatically. Its existence/connector session does not grant app access. Calendar OAuth can be configured without paid Vertex compute: enable the free Calendar API in an owned approved project, prepare a Web application OAuth client with the exact deployed origin and `HTTPS_GATEWAY/auth/callback`, and add the owner as a test user. Client secret/refresh encryption keys stay server-side. Any new consent must be completed by the owner in the system browser; the app cannot accept Google warnings or publishing terms for them.

The current scopes are OpenID identity, Calendar events and calendar-list read-only; app-created-only scope cannot access this previously owner-created calendar. Scope breadth follows the actual existing secondary-calendar operations. Runtime credentials, exact selected target, seven-day Testing refresh-token behavior, read-back and revocation remain live acceptance gates. Real test writes need the actual immutable UI preview and explicit approval. No general chat request substitutes for that approval.

Current public Gemini0.4.1 is automatic and isolated, without invitations. See `public_ai_access.md` and `remaining_actions_0.4.1.md`. Calendar remains a separate optional private gateway consent.
