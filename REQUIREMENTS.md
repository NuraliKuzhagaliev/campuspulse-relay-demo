# Requirement → implementation → evidence ledger

Statuses distinguish local implementation from actual cloud/external acceptance. **The project is not yet a complete Topic 2 cloud submission.**

| Gate | Code / UI entry | Meaningful verification | Live evidence / current status |
|---|---|---|---|
| R01 autonomous academic support | relay/service.py, agent.py; Week / Connections | deterministic source impact and planning tests | Real GitHub edit → one server-side impact run, 19.62s observed; hosted Gemini autonomy BLOCKED |
| R02 Gemini core | relay/agent.py; assistant composer | pinned SDK imports, ADK/RunConfig/toolset signatures | No actual local/remote Gemini call: BLOCKED on GCP |
| R03 custom function tools + MCP | scheduler.py, mcp_server.py; inspector | actual initialize/list/call; solver invariants | Genuine local MCP with 12 discovered tools; final live GitHub status and immutable file calls pass after quota reset; source change proof retained; cloud-agent MCP calls BLOCKED |
| R04 real reasoningEngine/API | scripts/deploy_reasoning_engine.py, deploy-cloud.ps1 | local SDK schema checks | No deployed resource/revision/API: BLOCKED |
| R05 web → remote agent visualization | gateway.py /api/chat, src/App.tsx | complete local browser workflow and disconnected-agent failure | Local UI works; public URL/remote path BLOCKED |
| R06 source/reproducibility | full repo, locks, infra, scripts, README | builds, tests, local smoke | GitHub source publication tracked in release/manifest.json; cloud scripts unexecuted |
| R07 presentation | scripts/build_presentation.mjs; release/presentation | eight-slide editable PPTX, package/font/geometry validation, slide renders/PDF | Local presentation artifact; cloud status disclosed |
| R08 five evaluation criteria | this matrix, architecture, tool catalog, proof and test docs | no invented judging weights | Evidence indexed; cloud criterion remains unmet |
| U01 web + real Windows | React + sandboxed Electron / NSIS + portable | installed executable smoke; source/import/cache checks | See docs/evidence/desktop-smoke.json; default gateway localhost, cloud connection pending |
| U02 F1-F5 | rows below | targeted tests + local UI | Local implementation verified; external gates remain |
| U03 autonomous AI coding / honesty | status/evidence/journal/scripts | actual measurements, no fabricated model output | Human account consent and spending approval still required |
| U04 visual design | tokenized CSS, bundled Inter, icons, responsive views | 1440/1280/1024/mobile screenshots, keyboard palette, reduced motion, automated AA primary states | Real screenshots, not concept artwork; complete certification not claimed |
| F1 evidence/conflict inbox — locally implemented | evidence.py/service.py; Evidence | real text PDF quote/page; both dates; unknown/ambiguous/irrelevant/corrupt inputs; scoped invalidation | Original illustrative PDF and real repo fetch supported; conflict policy is explicit user choice |
| F2 feasibility/what-if — locally implemented | scheduler.py; Week / Recovery | 540-min feasible case; lost-Wednesday >=120-min shortfall; caps, dependencies, pins, no overlap | CP-SAT + independent validator pass; what-if leaves baseline/calendar unchanged |
| F3 change radar — locally implemented | service.py sync_repo/sync_calendar; Connections | real repository edit, durable watermark, duplicate coalescing; Calendar 410/pagination test | Local server polling proven once (19.62s); hosted trigger, live Calendar sync and Gemini explanation BLOCKED |
| F4 approval/receipts — locally implemented | actions.py; Recovery preview / Activity | no approval, stale source/calendar, double retry, timeout after success, partial apply/mismatch, guarded undo, recovery keep/delete | Local adapter passed; real Calendar write/read-back BLOCKED |
| F5 next-action packets — locally implemented | service.py packet; study block/task; navigable evidence chain | exact rubric/quotes, original page navigation, explicit inputs and progress origin | Working locally; external completion signals are not inferred from learning |
| F6 desktop continuity | desktop/main.cjs + preload; Connections | selected-file IO, notification dispatch, reopen/cache/reconnect; bounded opt-in watch; installed route-mismatch regression | Real unmodified picker import, exact-content read-back, upload, refresh and snapshot save verified in the same profile. User confirmed the visible bottom-right Windows notification. Click/focus callback unverified. Installed regression and retained route/method guards pass; see desktop-native-result.json and docs/desktop_import_fix.md |
| F7 languages/timezones | language selector, ADK prompt language, domain/ICS | EN/RU/Kazakh operational flows, placeholders, original quotes/titles, errors, persistence, responsive views and automated AA checks; IANA/DST tests | Operational UI translated and locally verified; actual multilingual Gemini responses remain pending |
| F8 judge inspector | RunRail / Activity | durable ordered events and actual durations | Local execution is real and labeled; no remote revision is invented |

Do not turn a blocked live row green because a local fixture, recording, deployment script or Cloud Console screenshot exists. Update this ledger only from actual results.
