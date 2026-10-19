# Actual tool catalog for0.4.0

FastMCP exposes16 tenant-bound tools. Model arguments never select identity, context signing keys or Calendar ownership. MCP Streamable HTTP verifies both machine transport and bounded signed workspace context on the Developer route. The original managed route uses Cloud Run Google identity plus signed workspace context, not live verified yet.

Developer-model allowlist (11): `list_course_sources`, `read_course_source`, `get_assignment_repo_status`, `read_assignment_repo_file`, `get_workspace_plan_inputs`, `get_progress_summary`, `recommend_clarification`, `observe_handoff_gate`, `build_next_action_packet`, `propose_academic_extraction`, `save_validated_plan`. The last builds from server facts; model payload overrides are ignored. Extraction proposes exact cited fields and cannot confirm/apply them. Progress is a student report, not independently validated completion. Clarification removed-plus-added differences may count a moved block twice.

Five additional MCP tools are deliberately unavailable to the unpaid Developer model: `get_calendar_window`, `preview_study_blocks`, `apply_approved_study_blocks`, `verify_study_blocks`, `undo_owned_study_blocks`. Even where enabled for the managed path, writes/undo require concrete existing authenticated UI authority and ownership/version checks. Current real Calendar acceptance is pending.

Two pure function tools are separate from the16 MCP tools: `build_recovery_plan` and `compare_plan_scenarios`. The server independently validates schedule intervals, deadlines, dependencies, busy/pinned blocks and caps. No model-written schedule is accepted as feasible without validation.

Actual16-tool discovery and relevant real model calls are in `evidence/final-alternative-smoke.json` and `final-features-local-mvf943c1.json`. Each result records tool status/hash, relevant source/version provenance and finite typed error codes. Full tool payloads, private chain-of-thought, credentials and approval data are not exposed as execution telemetry. `/internal/ai-invitations` is not a model tool; only a short-lived exact Ed25519 owner signature can issue bounded AI-only invitations.
