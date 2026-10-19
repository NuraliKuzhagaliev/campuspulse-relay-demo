# Free Gemini contingency - explicit alternative hosting

Selected model:`gemini-3.5-flash-lite`, actual metadata version`3.5-flash-lite-07-2026`, Gemini Developer API Free tier in owner-confirmed project`gen-lang-client-0595303951`. A real local protocol smoke performed16-tool discovery, actual Gemini-selected MCP calls, a public GitHub read and a grounded response. Evidence:`evidence/final-gemini-access.json`, `evidence/final-alternative-smoke.json`. This is not managed Agent Engine or hosted browser acceptance.

## Credential and local smoke

The owner ran `scripts/configure-gemini-free.ps1 -ConfirmFreeTierOnly`. The key is encrypted for the current Windows user in `.local/private/gemini-key.dpapi`; the separate server-only `gemini-env.ps1` decrypts it into the current server process. Ordinary `env.ps1`, frontend/desktop builds and tests do not load it. No key belongs in chat, source, renderer, passport, screenshots or public evidence. Source/public archives exclude `.local` and `.env`.

`scripts/run-alternative.ps1` starts an isolated local protocol gateway on8016. It uses the existing ADK reasoning loop, explicit Developer client, same-process signed Streamable HTTP MCP, shared scheduling/evidence services and tenant-owned durable ADK text checkpoints. Full tool payloads, hidden reasoning and credentials are not checkpointed. This local HTTP listener is protocol evidence; secure-cookie browser acceptance needs actual HTTPS staging. No service silently falls back between Vertex and Developer APIs.

## Existing no-cost target and local staging

Authorized Render workspace:`Kuzhagaliev Nurali's workspace`, `tea-d3pt0sbipnbc73a5v810`. Reuse the existing Free service `srv-dbajs73bc2fs73bm9mfg`, `https://campuspulse-relay-demo.onrender.com`, with `infra/Dockerfile.alternative`, one worker and automatic deploys off. Its currently live0.2.1 deployment/commit remains the rollback reference until the verified cutover. No new infrastructure, paid database, disk, background worker, cron or upgrade is selected. Automatic approval review rejected creating a separate service because the previous authorization restricts infrastructure to the existing service; no new service was created.

Local browser staging uses `https://localhost:8017`, a loopback-only Node TLS proxy forwarding to the isolated gateway on8016. `prepare_local_tls.py` saves a development certificate on D: without installing a trust root. Test-only acceptance of this local certificate is explicitly separate from valid public TLS. `verify_final_ui.mjs` makes no inference calls; `verify_final_live*.mjs` records actual model outcomes, including partial failures. Do not use loopback certificate handling on the public deployment.

Required non-secret settings:

```text
RELAY_MODE=alternative_live
RELAY_INFERENCE_PROVIDER=gemini_developer
RELAY_DEPLOYMENT_MODE=alternative_hosted
GOOGLE_GENAI_USE_VERTEXAI=false
RELAY_GEMINI_DEVELOPER_MODEL=gemini-3.5-flash-lite
RELAY_GEMINI_FREE_ONLY=true
RELAY_GITHUB_REPO=NuraliKuzhagaliev/campuspulse-relay-demo
RELAY_JUDGE_ENABLED=true
RELAY_AI_ADMIN_PUBLIC_KEY=<actual public key from .local/private/ai-owner-public.json>
```

Set `RELAY_GEMINI_API_KEY` only in the intended service's private environment configuration. The existing D: key is not automatically permission to expose it in a tool result or UI screenshot. The owner can complete the exact prepared secret field. Docker startup generates distinct ephemeral internal service/context secrets; internal MCP requires both the machine credential and a bounded signed workspace context. The gateway origin comes from the actual Render URL. Startup rejects missing keys or incompatible provider/mode settings.

## Private evaluator access; Calendar remains separate

Anonymous visitors receive only isolated illustrative workflows. They cannot consume Gemini capacity. Live AI is for invited professional/hackathon evaluators aged18+, currently in Kazakhstan, using permitted non-sensitive documents. The UI explicitly confirms this scope and unpaid processing before sending data. Unpaid-service restrictions are not identical to enterprise privacy. No private Calendar details or Calendar mutation tools are offered to this model path. [Terms](https://ai.google.dev/gemini-api/terms), [regions](https://ai.google.dev/gemini-api/docs/available-regions).

The local owner key was generated using `scripts/configure-ai-owner.ps1`; it remains Windows-DPAPI-encrypted on D:. Only its public verification key reaches the host. The narrow `/internal/ai-invitations` operation requires an Ed25519 signature over exact method/path/body, a fresh60-second timestamp and bounded count/duration. It is not a public registration or general administration API. MCP/model credentials cannot issue invitations. The transaction records only token hashes and an idempotent batch; no Calendar lease/permission is granted.

After actual HTTPS deployment and provider smoke, run `scripts/prepare_ai_judges.py --url ACTUAL_HTTPS_URL --count 2 --hours 4` in the D: environment. It saves private invitations under `.local/judge-private/`, prints only the output path/count and keeps signatures/keys/tokens out of logs. The owner privately distributes the invitations; Codex does not send messages. A fresh browser can choose **Use a private AI invitation** at entry or in Ask RELAY. Each token is one-use within the current store, expires and opens a separate workspace. Two AI-only sessions do not imply two authorized Google Calendars.

Default model capacity counts individual inference calls, includes an aggregate judge reserve and records provider token usage. See `cost_estimate.md`. No model keys are needed from judges. External project quota can still be exhausted;429/backoff remains visible. Actual judging count/window is not yet supplied; the initial two-session batch is verification capacity, not unlimited public access.

## Temporary storage and resets

Free Render local SQLite, conversation checkpoints, sessions, approvals and invitation consumption can be lost on idle spin-down/restart/redeploy. No durable hosted persistence or always-running Scheduler is promised. Lost authority fails closed: old sessions/approvals/invitations are unavailable; issue new invitations and validate new proposals. Workspace Passport retains selected non-sensitive evidence/progress, never approval or credentials. A restored copy receives no AI grant from the file; an appropriate new private invitation is required for AI after switching. This limitation must remain visible in the demo.

Real Calendar requires separate app OAuth/scoped service access, the explicitly authorized secondary target and a concrete authenticated UI approval. Prior local-adapter receipts remain illustrative. Current alternative access does not waive the original managed GCP criterion; label it `UNMET / GCP_EXCEPTION_PENDING` until actual deployment or a documented organizer amendment.

## Availability and retention

No synthetic keep-alive traffic is used. A real request may take about a minute to wake a sleeping free service; pending/expired-session recovery must be tested. Confirm remaining quota and privately provision short invitations shortly before the actual judging window. Keep the free service available through that window. Afterwards the owner decides retirement/data retention and any guarded Calendar cleanup; no automated deletion, event clearing or paid upgrade is implied.
