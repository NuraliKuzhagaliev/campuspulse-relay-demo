# Current0.5MCP additions

Actual alternative-host MCP is protected loopback `/_relay/mcp/`, reached by server-owned transport bearer + signed workspace context. Anonymous visitors cannot call it directly. `read_course_source(source_id,page,offset,limit,search)` exposes bounded continuation/next_offset/page_count and literal search, preserving original offsets/quotes. `propose_academic_extraction` accepts distinct entity_id labels and cited title/course/term/key/due/minutes/rubric/normalized requirement fields; it records proposals only. Per-entity confirmation is a separate capability/CSRF-protected UI operation, never a model tool. Real loopback protocol evidence: docs/evidence/audit-mcp.json; no model/cloud calls in that smoke.

Prepared managed path `/managed/mcp/` additionally verifies actual Google machine principal/audience and organizer window. The narrow `/internal/runtime-state` cannot read private connections or write approvals; it is bound to the existing active public run/conversation. `/internal/managed-route` requires the independent owner's fresh signature and is not a model tool or invitation issuer. These endpoints are disabled by missing actual organizer configuration and do not imply managed acceptance.

The existing public safe tool catalog is reused under both public inference modes. Older catalog notes below are historical; private mutation tools still require pre-existing authenticated UI authorizations and are excluded from public model discovery.

## Earlier tool catalog

# Custom MCP catalog

Server: `relay/mcp_server.py`; local endpoint `http://127.0.0.1:8001/mcp/`. Transport: genuine MCP Streamable HTTP via the official Python SDK. Actual initialize/discovery/call evidence is in `docs/evidence/mcp-smoke.json`. Cloud-agent discovery remains unverified.

Every request needs `X-Relay-Context`, a backend-signed short-lived token bound to the MCP audience and verified workspace. Cloud additionally requires a Google machine ID token accepted by private Cloud Run. These headers are not model arguments. Tool annotations never authorize actions.

| Tool | Input | Purpose / side effect |
|---|---|---|
| list_course_sources | none | Approved IDs, versions, mode and freshness; read only |
| read_course_source | source_id, page | Bounded exact page text; read only |
| get_assignment_repo_status | none | Server-selected repository commit and issues; live read |
| read_assignment_repo_file | bounded relative text path | Immutable commit + original text; live read; no arbitrary URL or execution |
| get_calendar_window | none | Owned/approved calendar and configured horizon; read only |
| get_workspace_plan_inputs | none | Confirmed task facts, windows, timezone and unresolved conflicts |
| save_validated_plan | payload (overrides ignored) | Computes/persists a plan from server facts; no external write |
| preview_study_blocks | plan_id | Immutable exact create/keep/delete set; no external mutation |
| apply_approved_study_blocks | approval_id | Only pre-existing UI authorization; journaled writes and verification |
| verify_study_blocks | receipt_id | External read-back against intended fields |
| undo_owned_study_blocks | receipt_id | Only an authorized, unchanged owned compensation; model cannot authorize undo |
| build_next_action_packet | task_id | Cited rubric, small next action, checklist and completion origin |

Direct ADK function tools: `build_recovery_plan(payload)` and `compare_plan_scenarios(baseline, scenario)`. They validate typed inputs, compute deterministically and have no external side effects.

Examples: a source question discovers/reads a page; repository status reads a real commit and issue list; planning reads facts/availability then calls the solver; applying requires a UI-issued authorization ID unknown to the model. A document instructing the model to approve writes is retained as untrusted text and grants no permission.

Typed application errors: AUTH_REQUIRED, ACCESS_DENIED, SOURCE_CONFLICT, PARSE_FAILED, UNSUPPORTED_INPUT, UPSTREAM_RATE_LIMITED, UPSTREAM_UNAVAILABLE, INFEASIBLE, STALE_PLAN, APPROVAL_REQUIRED, PARTIAL_APPLY, VERIFICATION_MISMATCH. Connector reconciliation also uses internal NOT_FOUND, ALREADY_EXISTS and SYNC_TOKEN_EXPIRED. MCP returns structured errors; consumers must inspect the error field as well as the protocol `isError` flag.

Boundaries: 10 MiB upload, 100 text PDF pages, 250,000 extracted characters, 50 tasks/plan, 1,500 planning slots and 5-second solve. These are documented implementation limits, not hackathon rules. Private-repository user consent and streamed long-document extraction are not implemented.
