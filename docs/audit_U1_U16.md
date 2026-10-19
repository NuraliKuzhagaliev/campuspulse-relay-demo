# U1–U16 audit and acceptance · 0.5.0 candidate

**NON_GCP_READY = pending.** Current source changes are not hosted/live-provider/physical acceptance. Original reproduction metadata: `docs/evidence/audit-u-before.json`, baseline12a9eb0. Original0.4.1docs/releases/data are preserved. Tests below were run during this audit; previous132-test totals are not borrowed as current acceptance.

| Audit | Implemented correction | Actual evidence / remaining gate |
|---|---|---|
| U1 | Correct Unicode EN/RU/Kazakh markers, exact structured observations, prose review drafts + actual MCP proposal path |37new deterministic tests passed; deployed genuine EN/RU/KK prose batch pending |
| U2 | Document-wide entity grouping with original per-page quotes |Real2-page PDF through full local UI passed; hosted/table Gemini batch pending |
| U3 | Grouped proposals/list/review/explicit atomic per-entity confirmation; version/hash/tenant checks; canonical facts and portable reviewed interpretations |One-entity/neighbor/stale/duplicate/foreign tests, local UI confirmation/plan/Passport passed; live semantic acceptance pending |
| U4 | Bounded timestamp type boundary; null=unknown, wrong type=invalid, malformed string=ambiguous |None/int/bool/dict/string tests passed; no AttributeError |
| U5 | Source-local context/occurrence section identities; legacy title mapping only when unambiguous; no automatic progress reassignment |Same-title2course mapping test passed; prior original45/95 not modified |
| U6 | Exact45/75minute estimates retained; separate30minute allocation rounds60/90; bold/indent/shuffled fields |EN/RU/KK9format cases + local PDF75→90plan passed; explicit45/95 through UI/Passport passed |
| U7 | Unified2MiB source/native/draft contract,3MiB transport envelope and streamed public body bound |Raw/multipart/base64 near/at/over boundaries and PDF expansion guard passed locally; hosted bound/health rerun pending |
| U8 | MCP page offset/limit/next_offset/page_count/search; exact source/version retained |Actual authenticated loopback MCP continuation and search beyond20,000characters passed; hosted Gemini use pending |
| U9 | Whitespace rejected EMPTY_CONTENT; nonacademic evidence retained with no fabricated task; typed PDF failures; disposable bounded PDF worker |Empty/nonacademic/corrupt/encrypted/scan tests and real PDF UI passed; deployed resource-bound health test pending |
| U10 | Clean own workspace and separate example; switching retains data; visible confirmed/partial plan scope |Fresh visitor/own→example→own/source isolation/full local scenario passed; hosted rerun pending |
| U11 | Current Monday rather than next Monday; user period/timezone/availability controls; missing availability has own error |Local full UI context→plan passed; unknown/past dates remain distinct |
| U12 |7days/navigation, clipped cross-midnight segments, actual timezone/DST day geometry, keyboard focusable scroll |12language/width states no page overflow/AA issues; overnight/DST deterministic tests; hosted rerun pending |
| U13 | Imports use actual workspace timezone/horizon; explicit offsets retained, incomplete dates unknown |NYall-dayICS, offsets and DST tests passed |
| U14 | Shared bounded singleflight public GitHub observations in all access paths, conditionalETag/Last-Modified and immutable commit cache; server polling while awake |Concurrent cache, conditional304 and typed backoff tests passed; actual hosted recovery/background proof pending. Free hosting sleep remains a limitation |
| U15 |13synthetic samples, EN/RU/KK guide/expected results, public index and ZIP, distinct Source/Passport/Preflight workflows |Local browser ZIPdownload/unzip/hash13files passed; all3PDFpages visually reviewed. Actual public download/newvisitor proof pending |
| U16 | Firestore atomic buffering/cross-workspace transaction abstraction; shared runtime session contract retained; offline SDK/package rehearsal |Simulated transaction test passed. Actual managed shared authoritative state/no-login cloud bridge and remote acceptance pending organizer project; do not switch public data to an empty store |

Local UI evidence: `docs/evidence/audit-local-ui.json` (no model calls); complete raw diagnostics/screenshots remain under `.local/audit-ui/verification` on D:. The initial failures and corrections are not claimed as green on first attempt. Full suite initially162passed/7failed after adding37tests; affected regressions were corrected and88targeted cases then passed. A subsequent full run passed184tests and3subtests. Later focused parser/revoked-Calendar cases passed91/58targeted checks. The latest complete run passed188tests and3subtests in42.63seconds; no totals are added across overlapping runs. Native IPC7checks and locale catalog1check also passed.

Actual protected loopback MCP initialize/discovery/call passed after a short-search fragment boundary was corrected: continuation/search returned a quote past20,000characters; null due stayed unknown and unapplied. `docs/evidence/audit-mcp.json`, zero model/GCP calls. A startup smoke also caught an operator route registered before app creation; fixed before publication. Raw request bodies, credentials and model transcripts are not published.

Calendar: source implementation includes optional same-workspace state/PKCE, minimum app-created-calendar scope, encrypted credentials, explicit returned target and narrow write approval. Protocol tests are simulated. Client configuration, actual Google publishing/verification eligibility, consent/write/read-back/undo/revocation and independent public use remain pending. Native new picker/save/banner/click observations also need the owner after a rebuilt installed package is ready. These are not GCP blockers and are not waived by tomorrow's credits.

Managed statuses remain pending; organizer T0/expiry/project/coverage are unverified. No personal payment, trial, paid upgrade, account billing change or billable provisioning occurred during this audit.
