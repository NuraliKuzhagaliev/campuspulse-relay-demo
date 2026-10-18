# CampusPulse RELAY

**See what changed. Know what to do next.** Evidence-linked academic recovery for GDG Astana Topic 2. React web client, real sandboxed Windows Electron application, custom MCP service, deterministic CP-SAT scheduling and a Google ADK managed-agent deployment path.

## Actual release status

**[Open the public CampusPulse RELAY demo](https://campuspulse-relay-demo.onrender.com)** and choose **Enter public demo**. The React frontend and Python backend run together on a Render free web service. New-file import, evidence/conflict review, planning, what-if, explicitly simulated Calendar approvals/receipts, execution visualization, real backend GitHub reads, EN/RU/Kazakh, mobile layout, refresh and visitor isolation passed on the deployed HTTPS URL.

This public illustrative demo is **separate from the mandatory GCP deployment**, which remains pending. No actual Vertex AI Agent Engine resource, successful Gemini call or real Calendar consent/write/read-back has been verified. Organizer credit eligibility/balance/expiration, GCP account/project/billing and OAuth setup remain external gates. No uncovered personal spending is authorized. Read [REQUIREMENTS.md](REQUIREMENTS.md), [BLOCKERS.md](BLOCKERS.md) and [deployment proof](docs/deployment_proof.md) before presenting it.

Each browser session gets an isolated temporary workspace, with Secure/HttpOnly capability cookies and CSRF-protected writes. Sessions expire after two hours; idle spin-down, restarts and redeploys may reset them sooner. Render may need about a minute to wake after 15 minutes idle. Public imports are limited to 2 MiB and 12 sources including examples. Use sample documents. The **Start a fresh demo** control invalidates the old workspace. See [public hosting details](docs/public_demo_hosting.md), [actual deployment evidence](docs/evidence/public-deployment.json) and [browser acceptance](docs/evidence/public-demo-browser.json).

Verified local capabilities include conflicts with exact page/ref evidence, constrained recovery and isolated what-if, durable source polling using the real demo repository, immutable approval/journal/read-back using a clearly labeled local Calendar adapter, and cited next-action packets. No fixture is described as a live Calendar or Gemini result.

### 0.2.0 reliability and differentiation

The continuation fixes cross-course assignment collisions and adjacent-window validation, with explicit course/term/assignment mappings and a deliberate legacy migration. Historical sources/plans/receipts remain traceable; ambiguous old overrides require review. Missing identity is a separate draft, never a guessed merge.

**Judge challenge** exposes three scoped additions: **Minimal Rescue** compares student-permitted time additions with deadline-specific bottlenecks; **Submission Preflight** checks a selected draft's observable structure against exact requirement quotes and proposes extra-effort recovery; visitors can inspect their source versions, tools, plan changes and read-back. Semantic correctness, screenshot validity and grades are not inferred.

Managed-agent preparation includes tenant-owned expiring multi-turn history, idempotent turns, typed complete/partial/failed/unknown outcomes, bounded waiting/context renewal and truthful freshness. The Gemini prose-extraction proposal contract is prepared; actual multilingual model behavior and confirmation UX acceptance remain pending credits. See [defect ledger](docs/defect_ledger.md), [evaluation](docs/evaluation_results.md), [contracts](docs/contract_inventory.md) and [12-scenario live batch](docs/live_acceptance_batch.md). Prior 0.1.0, corrected 0.1.1 and public 0.1.1 artifacts are preserved under `release/versions/`.

## Run on Windows, entirely under D:

Prerequisites: existing Python 3.13, Node.js 22+, npm and Git. Existing runtime executables on C: may be read; project environments and outputs remain on D:. Windows and host applications can make system-managed writes.

```powershell
cd D:\projects\CampusPulseRELAY
.\scripts\bootstrap.ps1
.\scripts\dev.ps1
```

Open [the local web client](http://127.0.0.1:8000). `bootstrap.ps1` installs the exact Python lock and `npm ci` lock. `dev.ps1` serves the built UI and API together. It binds to localhost. Run `.\scripts\run-mcp.ps1` in another terminal for the genuine Streamable HTTP MCP server.

For Electron development, run `.\scripts\env.ps1` followed by `npm.cmd run desktop` while the gateway is running. The packaged application uses a local renderer; cloud credentials never enter it. The verified installed 0.1.1 app and its native fixes remain preserved with the local gateway. The separate public deployment verifies the browser client; hosted desktop OAuth/managed-agent acceptance remains pending.

## Inspect and test

```powershell
. .\scripts\env.ps1
.\.venv\Scripts\python.exe -m pytest tests -q
node node_modules/@playwright/test/cli.js install chromium
node node_modules/@playwright/test/cli.js test
.\.venv\Scripts\python.exe scripts/smoke_mcp.py
.\scripts\package.ps1
node scripts/smoke_desktop.mjs
node scripts/verify_public_demo.mjs https://campuspulse-relay-demo.onrender.com
```

The desktop smoke expects the NSIS installer to have installed to `D:\projects\CampusPulseRELAY\installed\CampusPulse RELAY`. Read [desktop verification](docs/test_results.md) for instrumented-picker and OS notification limitations. Tests use isolated identities and explicitly illustrative calendars, not personal events.

## Cloud access and deployment

Wait for the organizer credit activation instructions before choosing the final GCP project or billing account. Verify the exact eligible project, billing account, credit balance and expiration. `.\scripts\inspect-access.ps1 -Login` provides read-only authentication/access inspection. No dedicated CampusPulse project was found previously; [cloud setup](docs/cloud_setup.md) provides the pending steps. Read the [cost estimate](docs/cost_estimate.md); any uncovered charges need separate approval before deployment.

`scripts/deploy-cloud.ps1` orchestrates separate Cloud Run gateway/MCP services, Firestore, Secret Manager, an Agent Engine `reasoningEngines` resource, and an authenticated Cloud Scheduler job. It is implemented and schema-checked where possible, but **has not been executed against GCP**. `scripts/deploy_reasoning_engine.py` uses the currently documented `vertexai.Client(...).agent_engines.create` compatibility route. Installed SDK 2.5 emits a migration warning for `vertexai.Client`; the legacy resource mapping is documented. Inference uses ADK/Google Gen AI, not removed `vertexai.generative_models` modules.

After deployment, configure the returned OAuth redirect URL, complete real consent in an external browser, select an authorized calendar, run `scripts/smoke_remote.py`, and perform the complete web → gateway → Agent Engine → MCP → external API test. A deployed resource alone does not establish acceptance. No gateway-only agent fallback exists.

## Dedicated external demo resources

- [Owned repository](https://github.com/NuraliKuzhagaliev/campuspulse-relay-demo), `coursework.md` on `main`.
- Calendar name: **CampusPulse RELAY Demo**. Actual returned ID is in `docs/connections.json`; it is not an authorization credential.
- Course material is illustrative. GitHub reads and controlled edits are real. The dedicated Calendar exists; the app does not yet have live access.

Original supplied attachments are preserved locally under `inputs/`, excluded from Git and release source archives. No third-party submission or messaging is automated.

## Layout and artifacts

- `relay/`: typed domain, scheduler + independent validator, evidence, connectors, journals, service, API, MCP, ADK runtime, identity/OAuth and request limits.
- `src/`, `desktop/`: shared UI and restricted Windows bridge.
- `infra/`, `scripts/`: D: environment, bootstrap, deploy, seed, smoke, package, presentation and scoped cleanup.
- `tests/`: deterministic, HTTP, failure, Calendar sync and browser scenarios.
- `docs/`: evidence, security/architecture, judge instructions and actual results.
- `release/`: installer, portable app, source archive, presentation, recording, hashes and manifest. Build output is excluded from source Git.

EN/RU/Kazakh operational UI is translated, including confirmations, errors, receipts, packets, calendar labels and native dialog/tray text. Source quotations, exact event titles and diagnostic data remain verbatim. Live multilingual Gemini acceptance is pending. The remaining limitations include conservative structured text extraction, no scanned OCR, unsigned Windows packages and unverified cloud/Calendar consent. See [known limitations](docs/known_limitations.md) and the [real native Windows check](docs/native_windows_check.md).
