# UI / gateway / native contracts

All /api writes require the authenticated workspace cookie/capability and CSRF; objects are looked up inside that tenant. Public mode has its own allowlist and refuses Google/GCP/agent configuration. Electron additionally validates trusted sender/frame and an exact method-specific route set. No multipart body crosses native IPC.

| UI action | Gateway contract | Electron |
|---|---|---|
| Session/state/reconnect | GET session, state, events?after=N | GET only; bounded query |
| Browser upload / native selections | POST import multipart / POST import-native JSON base64 | Only import-native; both desktop selection paths use it |
| Source/packet | GET sources/:id, packets/:id | GET only |
| Explicit assignment mapping | POST sources/:id/mapping | POST only |
| Task inputs/progress | POST tasks/:id/settings | POST only; semantic validation on gateway |
| Conflict choice | POST conflicts/:id/resolve | POST only |
| Plan/isolated what-if | POST plan, scenario | POST only |
| Minimal Rescue / student choice | POST rescue, rescues/:id/choose | POST only; version check and fresh busy read |
| Selected draft / extra effort scenario | POST preflight, preflights/:id/recovery | POST only; selected bytes; no execution/submission |
| Preview / approval / read-back / undo | POST plans/:id/preview, previews/:id/approve, receipts/:id/verify or undo | POST only; unchanged immutable approval and journal validation |
| Conversation/new/stop waiting | GET conversation; POST conversation/new, chat, runs/:id/cancel | Exact methods; server owns conversation and run IDs |
| Challenge evidence / export | GET challenge, export | GET only; current visitor only |
| Browser public reset | POST demo/reset | Public browser only; no desktop reset button is offered |
| Workspace deletion API | DELETE workspace | Not exposed by desktop UI/IPC; public HTTP authorization/expiry/reset tested |
| Google connections | OAuth + allowlisted calendar routes | Existing external-browser pairing; disabled on public demo; real consent still pending |

The temporary Render demo intentionally has one process/instance and local ephemeral state. It is not a multi-instance persistent deployment. Shared durable Store/Firestore atomic claims and restart/isolation are exercised through local contracts; real multi-instance Firestore/IAM/token renewal remain in the live batch. Polls read events and never consume model allowance. Model requests are deduplicated by authenticated conversation/request IDs; source changes are versioned and GitHub rate limits back off.
# 0.3.0 additive contracts

- GET`/api/additions`, GET`/api/tasks/{id}/estimate-suggestion`: own revision, logs, sessions, gates and eligible local history.
- POST`/api/tasks/{id}/progress`: typed start/log/stop/correct/remaining/unknown/complete, expected revision and idempotency body; POST`/api/work-sessions/{id}/heartbeat`: session revision plus monotonic delta, not attention proof.
- POST`/api/progress/preview`, POST`/api/progress/{id}/adopt`: separate future proposal and fingerprint/revision-checked adoption. No Calendar write authority.
- POST`/api/clarify`, POST`/api/clarify/{id}/cancel|answer`: bounded copied branches, cited/user-offered alternatives, no hidden canonical changes.
- POST`/api/gates`, POST`/api/gates/{id}/observe|remove`, POST`/api/gates/conditional-preview`: configured public PR merged gates, retained observations, explicit local removal and conditional ETA. POST`/api/gates/notifications/{id}/claim`: atomic once-only dispatch attempt, never visibility proof.
- POST`/api/passport/export|preview`, POST`/api/passport/{id}/restore`: selected strict untrusted file, bounded validation, atomic fresh namespace, new session/CSRF; no imported tenant authorization or executable history.
- Native `importFile('passport')`: JSON-only2MiB selected-file IO; `savePassport(value)`: native Save with D: resolved parent/symlink checks and atomic sibling replacement. Existing academic import and exact route/method policy remain intact; multipart IPC still denied.
- MCP`observe_handoff_gate(gate_id)` shares the same service. Signed server context selects tenant/repository; no model-supplied identity or external-write tool parameter. Actual local14-tool protocol proof: `docs/evidence/four-mcp.json`. No managed-agent call is claimed.
