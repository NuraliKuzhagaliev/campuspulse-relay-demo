# Exact account actions

All project-controlled tools/configuration remain on D:. Do not paste credentials in chat. The user declined personal spending. **Wait for the organizer activation instructions before final project/billing selection or any billable provisioning.** Credits are not confirmed and may require a new eligible project. The steps below are a prepared sequence, not authorization to execute paid actions.

1. Open PowerShell and run:

```powershell
cd D:\projects\CampusPulseRELAY
.\scripts\inspect-access.ps1 -Login
```

Complete Google sign-in yourself in the browser. This script reads accounts, projects and billing accounts. It does not create cloud resources. Existing browser sign-in is not CLI ADC.

2. After the organizer instructions arrive, confirm whether they require a new project or organization/billing account. Follow that exact activation path. If a dedicated project must be created, use name **CampusPulse RELAY** and an available ID. Do not presume either existing project is eligible. Return the actual eligible project ID, not a secret.

3. In **Billing**, inspect the existing account's activation state and **Credits** page. The inspected account displayed a prepayment requirement. Any payment or billing activation is a human action; no available credit is established. Do not create or attach a new billing account automatically.

4. Verify credit eligibility for the exact project/billing account, actual balance, expiration, covered SKUs and usage conditions. Review `docs/cost_estimate.md` within that envelope. The earlier USD 25 / 72-hour estimate is **not approved personal spending**. Explain any uncovered cost and obtain separate approval. `scripts/record-credit-activation.ps1` records human-confirmed balance/expiry and checks actual existing project billing read-only; it never activates credits, attaches billing or verifies a credit balance through an API.

5. Set the actual project in `.env`, then authenticate ADC:

```powershell
.\scripts\connect-gcp.ps1 -ProjectId YOUR_ACTUAL_PROJECT_ID
. .\scripts\env.ps1
.\.venv\Scripts\python.exe scripts/preflight.py
```

The ADC command may reject Calendar scopes under Google's built-in CLI OAuth client. Cloud-only ADC is sufficient for deployment: run the D: CLI's `auth application-default login` with cloud-platform scope and set-quota-project. Calendar consent uses the application's separate OAuth client below; an AI Studio key is insufficient for Agent Engine.

6. Create/configure the project's **Google Auth Platform** consent screen and **Web application OAuth client**. Select only the required test users until publishing is appropriate. Set authorized origin to the actual HTTPS gateway and redirect URI to `ACTUAL_GATEWAY_URL/auth/callback`. These values become available after initial hosting; configure consent before testing. Store client ID/secret in `.env` on D:, never chat. Generate a Fernet key locally for `RELAY_TOKEN_ENCRYPTION_KEY`; deployment places secrets in Secret Manager. The desktop opens the system browser and asks for explicit pairing, never embedded Google login.

7. Only after activated eligible funding and an approved specific usage envelope, run `scripts/deploy-cloud.ps1` with that amount and duration. It requires `.local/credit-activation.json`, matching project/billing, sufficient confirmed balance/expiry, and `-AcknowledgeBillableResources`. It refuses missing/disabled funding; it does not make payments or link billing. The orchestration is **unexecuted and requires live repair/verification**. Start with bounded local/remote model smoke, inspect actual spend, and reserve judge capacity before expanding. No claim of deployment follows from a script alone.

8. Configure the actual gateway URL in `.env` and desktop environment, complete Google consent in the browser, select **CampusPulse RELAY Demo** from the verified Calendar list, and perform actual UI-approved actions. The dedicated Calendar ID is in `docs/connections.json`. Sharing it with a runtime service identity is an alternative explicit owner action; service accounts have no automatic access.

9. Run `scripts/smoke_remote.py --workspace VERIFIED_WORKSPACE_ID --approve-model-call` only within the approved budget. Reserve judge capacity, verify request allowances, test clean sessions/consent revocation/restart/token renewal, and keep the deployment available through the actual judging window. That window was not supplied.

For sustained GitHub reads, create a fine-grained repository-scoped credential for the dedicated demo repository with Contents: read, Issues: read and required metadata access. Enter it only into D: .env as RELAY_GITHUB_TOKEN. The Codex connector credential is not forwarded to the deployed app. Public unauthenticated reads back off when GitHub quota is exhausted.
