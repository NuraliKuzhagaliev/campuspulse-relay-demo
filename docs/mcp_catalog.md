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
