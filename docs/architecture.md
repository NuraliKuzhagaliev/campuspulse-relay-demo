# Current0.5architecture and trust boundaries

The public React/Electron app uses capability-cookie/CSRF workspace authorization. Own documents and examples have distinct server-generated workspaces; the owner key never enters clients. Source imports have one2MiBcontract, bounded PDF subprocesses and exact page/version quotations. Semantic MCP proposals are untrusted interpretations until one-entity atomic UI review. Progress, source effort and solver allocation remain separate. Passport copies archived untrusted claims, never connection or approval authority.

Anonymous AI jobs share the existing bounded fair quota-aware queue. MCP requires machine transport identity plus a short-lived audience-bound workspace context; tool schemas do not carry tenant authority. Public model tools exclude private Calendar payloads and mutations. Calendar OAuth is voluntary, same-workspace state/PKCE, minimum created-calendar scope by default, encrypted refresh and a separate exact preview/approval/read-back journal. A revoked Calendar leaves files/progress accessible and cannot silently make an empty busy calendar look fresh.

Prepared organizer route (disabled until actual activation): Render remains authoritative for documents/history/progress/plans/ADK checkpoints. An owner-signed no-restart configuration selects one organizer-covered Cloud Run query bridge→actual Agent Engine. The runtime uses its Google service ID token plus bounded workspace context to the existing protected MCP and narrow run-scoped checkpoint/quota RPC. No broad database proxy, approval writer, permanent SA key or copied owner access token. Public safe tool filtering also applies in the managed route. Initial invocation has a durable run claim; unknown outcomes are not replayed automatically on free Gemini. At the actual retirement cutoff the existing free route resumes with the same state; real expiry/cutover acceptance is pending.

Firestore transaction buffering/cross-workspace copy is separately prepared/tested with a fake adapter and is not required for this state-preserving route. Actual Google IAM/resource/session behavior must be verified tomorrow. Older descriptions below are historical and do not imply the new route is deployed.

## Earlier architecture

# Architecture and data flow

0.3.0 adds focused domain services `progress.py`, `clarify.py`, `handoff.py` and `passport.py`, used by the same FastAPI/web/Electron boundaries. The PR observation service is also the genuine authenticated MCP tool implementation. `Continuity.tsx` contains focused feature panels rather than expanding the main week's intertwined branches. There is no new stack or paid service.

`Store.atomic` uses `BEGIN IMMEDIATE` and a tenant-scoped transaction interface for multi-record progress commands, history, invalidation and portable copy commit. A bound additions revision plus source/settings/decision/progress/gate fingerprints protects comparisons, plan previews and approvals. Idempotency keys compare command bodies before optimistic revision checks; old IDs cannot change payload. Portable commit generates a fresh server namespace and source/fact references, never trusts imported tenant authority. Source identity migrations/history from0.2.1 remain intact. New Firestore transactions fail closed until a real integration test.

Clarification runs bounded pure branches off the API event loop with one job/workspace and two global jobs; model-build guards and solver deadlines/cancellation keep unknown outcomes explicit. PR observations use a bounded shared immutable cache/ETag/backoff and no arbitrary fetch URL. Native restore/save adds exact purpose/routes, keeps sandbox/context isolation and the corrected academic import allowlist, and verifies D: resolved save destinations. No restoration or progress operation can authorize Calendar; that remains a fresh independent preview/approval/journal boundary.

```mermaid
flowchart LR
  UI[React web / packaged Electron renderer] --> GW[Authenticated FastAPI gateway]
  GW --> AE[Remote reasoningEngine / ADK / Gemini]
  AE --> FN[Deterministic function tools]
  AE --> MCP[Private Streamable HTTP MCP]
  MCP --> GH[Allowlisted GitHub]
  MCP --> CAL[Authorized Calendar]
  MCP --> FILES[Selected source versions]
  GW --> DB[Firestore in cloud / SQLite locally]
  MCP --> DB
  SCHED[Authenticated Scheduler / local server polling] --> GW
```

Cloud components in this diagram are **implemented deployment targets, not verified running resources**. The local gateway serves real HTTP requests and persists state in SQLite. A model request is refused when `RELAY_AGENT_RESOURCE` is absent. There is no local-model or gateway-hosted-agent success fallback.

`RelayRuntime` is deployed with `client.agent_engines.create`; its `query` method creates an ADK agent for the verified scope and dynamically selects custom MCP and deterministic function tools. Google Gen AI performs inference. The installed Vertex client is a compatibility entry point and emits a migration warning; no deprecated `vertexai.generative_models` inference code is used.

Identity is server-verified Google identity in cloud mode; a random HttpOnly local session identifies an explicitly illustrative development workspace. The gateway signs short-lived audience-bound workspace context. Tool schemas contain no `user_id` or arbitrary `calendar_id`. Cloud Run additionally requires service identity on MCP. The ADK header provider fetches a machine ID token for fresh MCP sessions. Token renewal and restart are designed but not cloud-tested.

OAuth uses the system browser, state, PKCE, verified ID-token subject, encrypted refresh credentials, and explicit one-use desktop pairing. Calendar selection is checked against that user's authorized list. Live OAuth/consent/revocation testing and isolated judge access remain blocked. A service account never automatically acquires personal Calendar access.

State: workspace settings/connections, source versions, exact extracted facts, task overrides, conflict decisions, plan versions/blocks, ordered run events, immutable previews, approvals, operation journal, receipts and sync cursors. SQLite provides transactions locally; Firestore provides create-once and compare-and-set transactions in cloud mode. Firestore, service IAM and cloud concurrency have not been integration-tested.

Scheduling consumes validated 30-minute units, deadlines, windows, busy intervals, dependencies, daily caps, baseline blocks and pins. CP-SAT returns a status; an independent interval validator checks the result. Incomplete allocation is never accepted as feasible. What-if scenarios neither replace the baseline nor write to Calendar.

Actions are immutable previews bound to identity, target, source versions, settings/overrides, plan and action digest. Before applying, the backend re-reads Calendar and source preconditions. Each operation has a deterministic Calendar ID and durable journal entry. Retries reconcile unknown outcomes. Recovery previews distinguish create/keep/delete; edited/unowned events are preserved. Undo removes only unchanged events created by that receipt; restoring deleted prior blocks requires a fresh preview, which is disclosed.

Events use persisted sequence IDs and authenticated polling. The inspector shows short operational summaries, actual calls, durations and failures. It never exposes hidden chain-of-thought or fabricated progress.
