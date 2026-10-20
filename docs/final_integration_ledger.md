# Current acceptance ledger · 0.5.2

Primary route: Render Free / server-side Gemini Developer API / actual signed MCP / real workspace and allowlisted GitHub data. Managed GCP is disabled, original criterion unmet. No organizer credits expected. No official waiver or personal spending.

| Check | Actual evidence | Scope / remaining gate |
|---|---|---|
| Five own documents, six complete real turns | evidence/audit-live-mvfmnry1.json, runtime 2f74bdacf4bab56b96dbd2b3350d388634d95142 | EN/RU/KK prose, continued and table PDFs, full review/plan/what-if/illustrative receipt/progress/Passport/reopen |
| Later two-visitor recheck | evidence/audit-live-mvfnvite.json, runtime 1718ff340bdb2b40c5d3e796907000bd6720b80f | Two complete, one partial. Valid proposal after a failed tool call does not erase that failure. |
| Partial diagnosis | evidence/final-0.5.1-partial-diagnosis.json | Historical exact invalid input unavailable. Sticky failed-tool flag explains partial. Typed schema diagnostics and null citation-mode regression added. |
| Full local tests | .local/logs/final-0.5.1-unit.log | 219 passed, 3 subtests. Provider and Calendar failures simulated where appropriate. |
| Actual MCP protocol | evidence/final-0.5.1-mcp.json | Real protected loopback initialize/list/read/propose, typed redacted invalid-schema result and null citation references. Zero model/Google calls. |
| Full local UI | evidence/final-0.5.1-local-ui.json | Continued PDF, explicit review, own/example separation, plan/what-if/illustrative receipt/Preflight,45/95, Passport/reopen,12 EN/RU/KK-width AA states |
|100-session queue/isolation | evidence/final-0.5.1-100-simulated.json | Real HTTP session/upload/queue/history; provider simulated, zero real Gemini. Plan isolation fixtures, no actual MCP in this load test. |
| Session expiry/network | evidence/final-0.5.1-recovery.json | Local controlled capability expiry 401, recovery banner/fresh authority, no mutation replay. Not a forced public restart or real Google revocation. |
| Public GitHub | evidence/audit-hosted-github.json | Actual hosted read + later server observation after test browser closed; original fetch timestamp retained. Current live recheck separately recorded. |
| Public samples/import boundaries | evidence/audit-public-samples.json, audit-hosted-boundaries.json |13 raw files/ZIP/trilingual guide hashes;2MiB parser and3MiB transport boundaries, typed empty/corrupt failures |
| Owner Calendar | evidence/audit-calendar-owner-connected.json, audit-calendar-target-selected.json | Setup/consent/target were real. Latest owner response AUTH_REQUIRED means expired temporary session. Event write/read-back/retry/undo/revocation still pending. |
| Installed/native | evidence/audit-desktop-0.5.0.json, audit-native-observation-0.5.0.json, preserved-native-0.5.0.json | Historical installed0.5.0 equality, Open/Cancel/import+refresh200, original45/95. New0.5.1 installation and physical remaining checks not implied. |
| Managed GCP | prepared guarded scripts, organizer_window_runbook.md | Disabled optional integration. No real Agent Engine/IAM/shared-state acceptance. |

Current publication/runtime results are added to evidence/final-0.5.1-acceptance.json. Older successful, failed and partial evidence stays intact. NON_GCP_READY=false pending actual Calendar and Windows gates. F1–F5 remain locally implemented; real Calendar and full enhancement-level Gemini acceptance are separate. Free storage/quota/latency limits remain visible.

## Final public revision recheck

Runtime7e4098dae61775b5062b2f613192a6abaa3185dc on Render Free, deploy dep-dbbmv949v7es73fov1kg became live2026-10-20T13:43:06Z. Full hosted UI passed (final-0.5.1-hosted-ui.json). Five own-document workflows passed again through the actual UI, six real Gemini/MCP turns:5complete/1partial (audit-live-mvgqi7ei.json). The partial now exposes TOOL_INPUT_INVALID / extra_forbidden: two extra fields in candidate14. The model corrected the call and saved a valid proposal; the original failure remains partial. No additional fake/paid fallback.

EN/RU/KK missing fields survived confirmation/refresh (first/second uncertainty evidence retains those successes), and a separately rerun own conflicting pair preserved both quotes and its explicit decision (final-0.5.1-uncertainty-ui.json). Earlier harness selector/timing failures are retained; the corrected harness waits for the actual review POST response. Supplemental synthetic inputs and trilingual expected instructions are in fixtures/acceptance-0.5.1 and the release sample addendum.

Actual current GitHub manual read and later server observation with test browser closed passed, original source time unchanged (final-0.5.1-hosted-github.json). All13 public files/ZIP/guide hashes passed again. Actual local process restart with retained SQLite and an empty-store replacement/Passport restore passed (final-0.5.1-restart.json); public Render was not restarted to avoid discarding the owner's new Google connection.

Full final suite219passed+3subtests,8IPC checks. A previous full run encountered a minute-boundary race in the quota TEST; freezing its test clock fixed the nondeterminism, and the full rerun passed. This was not a provider or production change. Logs and hashes are in final acceptance metadata.

Owner has now renewed Google consent: configured=true,connected=true,calendar_live=false. Recovery of the supplied previous target returned Google404. No repeated login or calendar creation is requested; owner is checking actual account/Calendar settings ID. No actual event writes claimed. New Windows0.5.1 package11runtime files match source, installer/portable hashes verified; no installation, launch or native GUI control performed. Owner manual acceptance is requested separately.


### Installer and independent-guide follow-up, 20 October

Owner reported the 0.5.1 installer chose C: without a D: option. Read-only file inspection confirmed C:0.5.1.0 and D:0.5.0.0. Root cause: default NSIS initMultiUser overwrites early preInit; the owner helper omitted /D, and default NSIS caches the installer in LocalAppData. Replaced with a fixed-D custom NSIS script, guarded exact-path uninstall, separate D registration, no LocalAppData cache; added explicit /D to the helper. Corrected package compiled; 11 runtime files match source; 3 structural regression tests and 5 mocked owner-replay helper checks passed. These are not native installation/Calendar acceptance. The prior bad binaries and failed compile logs are preserved. No Windows control or C cleanup was performed. Owner reinstall and physical checks remain pending.

The full Russian independent website plan is docs/independent_website_test_ru.txt. It covers all agreed non-GCP features, 13 samples, own EN/RU/KK documents and continued/table PDFs, uncertainty, real Gemini/MCP, isolation, recovery and separate voluntary owner Calendar consent/preview/write/read-back/replay/undo. A calendar-connected workspace must not be switched after consent. The guide is a procedure, not evidence of an independent pass.


### 0.5.2 timezone, localization and distribution update

The user reproduced arbitrary text in the timezone datalist, KK instead of KZ, and a Russian native date popup in an English interface. Workspace choices are now closed selects for Kazakhstan/Asia-Almaty, Moscow/Europe-Moscow and UTC, with server-side validation in both write routes. Original evidence zones remain separate. Legacy Passport restore previews supported-zone migration and preserves absolute windows/source timestamps.

The native date/time fields were replaced with an application-owned calendar and 24-hour controls. Explicit EN/RU/Kazakh month/day dictionaries also cover browsers lacking Kazakh ICU data (the first Intl implementation returned M10). Visual review caught a CSS class collision with the existing weekly calendar; the date-picker classes are now distinct and geometry is checked, not inferred from no page overflow. Escape focus restoration was repaired. Nine language/width states and three actual upload/review/confirm flows passed in a Russian-locale headless browser, with unchanged quoted source and deadline instant. Example badge/avatar decorative text no longer conflicts with their accessible names.

Testing Moscow/UTC uncovered a genuine existing source-review failure: deterministic candidates incorrectly used the workspace timezone for an ISO source deadline with its own offset. Review now carries that explicit cited offset; nine regressions preserve the instant and quote. Strict model offset validation is unchanged. Full local result252 tests+3subtests,8IPC checks;100 simulated-provider sessions still make zero Gemini calls. Early harness navigation/work-completion races and failed checks are retained on D:; they are not recorded as successful runs.

Version0.5.2 adds stable GitHub latest-download links and a full rewritten README. Windows packaging is separate from physical installation; Windows control after Escape remains stopped. Original managed-GCP criterion and real Calendar/native acceptance gates remain unmet/pending. Public release and Render results are appended only after observation.


### Observed publication — 0.5.2, 20 October

GitHub release v0.5.2 was published as latest, with 13 assets. Every full SHA-256 matches the GitHub asset API; anonymous strict-HTTPS latest-download checks redirected to v0.5.2 and read matching bounded byte ranges for both Windows executables. The source/tag/runtime commit is 0cb787885df570b4083d0b041e828e14394ed0f0. The source ZIP contains that exact commit; a later documentation-only commit records these publication results.

Render Free deploy dep-dbbph7gae00c73ada4l0 reached terminal live at 2026-10-20T16:37:58Z. Public health reports 0.5.2, the exact commit, public Gemini Developer access and managed Agent Engine disabled. Two fresh visitor sessions were distinct; arbitrary timezone API input returned UNSUPPORTED_TIMEZONE without changing settings; all three branding assets match source; the header points to the latest Windows installer.

Actual public UI rechecks passed nine EN/RU/KZ × desktop/tablet/mobile states with Russian browser locale, translated October/октябрь/қазан, no overflow and no AA violations. Three own-document upload/review/confirm flows preserved quotations and deadline instants; both timezone controls have exactly the three permitted values; saved dates/hours/days survive refresh. Four additional public edge flows passed: invalid-date correction plus rapid keyboard selection; incomplete deadline blocked and clearing unknown allowed; Moscow planning/what-if with baseline preservation and an explicitly illustrative receipt; legacy Passport migration disclosure and a fresh copy without Google consent/old approval authority. No real Calendar writes or new Gemini calls were made by these checks.

Evidence: evidence/public-deployment-0.5.2.json, public-locale-0.5.2.json, public-edges-0.5.2.json, release-distribution-0.5.2.json. Full local suite 252 tests + 3 subtests; 8 IPC checks. Sixteen packaged Windows runtime/branding files match current source/build and actual ProductVersion is 0.5.2.0. Native installation/control was not performed. Prior 14 releases / 112 artifacts were independently rehashed before sealing this release; all matched. Calendar event acceptance, physical current-version Windows checks and original managed-GCP criterion remain separately pending/unmet. NON_GCP_READY=false; no paid resource/upgrade/billing activation.


### Presentation refresh for 0.5.2

Replaced the current briefing with a new 14-slide Russian design using the owner's unchanged original JPG and genuine 0.5.2 synthetic-workspace captures. New source review shows exact 53 minutes; current progress capture confirms 45 logged / 95 remaining. The Calendar image is a single explicitly illustrative, unapproved event preview with no approval digest. It does not claim a Google write. Dated historical real AI results remain 5 complete / 1 partial on six turns and five own documents. Managed GCP and real Calendar/current native gates retain their actual pending/unmet status.

Every slide in the final PPTX was rendered and visually reviewed. Three native tables and editable text remain. Original logo bytes are embedded unchanged. The direct bundled PDF exporter failed on missing #standard-fonts/Helvetica; the delivered PDF instead embeds the reviewed high-resolution slide renders. All 14 embedded page images match those renders pixel for pixel; two public links are annotated. Native PowerPoint was not opened. Finalizer found zero structural/layout findings or warnings. Prior decks and sealed releases are preserved. Publication adds the new PPTX/PDF/checksum assets without changing the original 13 release files or restarting Render.
