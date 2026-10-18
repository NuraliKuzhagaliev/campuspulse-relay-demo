# CampusPulse RELAY

**See what changed. Know what to do next.** Evidence-linked academic recovery for GDG Astana Topic 2. React web client, real sandboxed Windows Electron application, custom MCP service, deterministic CP-SAT scheduling and a Google ADK managed-agent deployment path.

## Actual release status

This is a **local release candidate**, not a completed cloud submission. The required Vertex AI Agent Engine resource, live Gemini call, public web deployment and live Calendar write/read-back are **not verified**. Google Cloud account/project/billing and OAuth setup remain external gates. Read [REQUIREMENTS.md](REQUIREMENTS.md), [BLOCKERS.md](BLOCKERS.md) and [deployment proof](docs/deployment_proof.md) before presenting it.

Verified local capabilities include conflicts with exact page/ref evidence, constrained recovery and isolated what-if, durable source polling using the real demo repository, immutable approval/journal/read-back using a clearly labeled local Calendar adapter, and cited next-action packets. No fixture is described as a live Calendar or Gemini result.

## Run on Windows, entirely under D:

Prerequisites: existing Python 3.13, Node.js 22+, npm and Git. Existing runtime executables on C: may be read; project environments and outputs remain on D:. Windows and host applications can make system-managed writes.

```powershell
cd D:\projects\CampusPulseRELAY
.\scripts\bootstrap.ps1
.\scripts\dev.ps1
```

Open [the local web client](http://127.0.0.1:8000). `bootstrap.ps1` installs the exact Python lock and `npm ci` lock. `dev.ps1` serves the built UI and API together. It binds to localhost. Run `.\scripts\run-mcp.ps1` in another terminal for the genuine Streamable HTTP MCP server.

For Electron development, run `.\scripts\env.ps1` followed by `npm.cmd run desktop` while the gateway is running. The packaged application uses a local renderer; cloud credentials never enter it. Set `RELAY_GATEWAY_URL` to the actual verified HTTPS deployment when available. Its default is the local gateway until cloud deployment is completed.

## Inspect and test

```powershell
. .\scripts\env.ps1
.\.venv\Scripts\python.exe -m pytest tests -q
node node_modules/@playwright/test/cli.js install chromium
node node_modules/@playwright/test/cli.js test
.\.venv\Scripts\python.exe scripts/smoke_mcp.py
.\scripts\package.ps1
node scripts/smoke_desktop.mjs
```

The desktop smoke expects the NSIS installer to have installed to `D:\projects\CampusPulseRELAY\installed\CampusPulse RELAY`. Read [desktop verification](docs/test_results.md) for instrumented-picker and OS notification limitations. Tests use isolated identities and explicitly illustrative calendars, not personal events.

## Cloud access and deployment

First run `.\scripts\inspect-access.ps1 -Login`, then inspect accessible projects and billing. No dedicated CampusPulse project was found at inspection; [cloud setup](docs/cloud_setup.md) provides exact creation/authentication steps. Read the [cost estimate](docs/cost_estimate.md) and obtain a specific spending limit **before** running deployment.

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

The engineering limitations are deliberate and visible: conservative structured text extraction, no scanned OCR claim, partial language coverage, unsigned installer, and unverified cloud/personal-consent behavior. See [known limitations](docs/known_limitations.md).
