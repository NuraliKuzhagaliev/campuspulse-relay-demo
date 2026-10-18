# Evaluation results · continuation 0.2.0

Input specification: all 190 lines of the supplied continuation prompt read; user preservation, D: storage and pending-credit restrictions take precedence. Baseline d12c276 was clean, included the later public deployment work, and matched remote main. Reviewed d775c403 differs from that baseline by the preserved public-hosting work. No reset or force push was used.

## Observed failure before / pass after

| Input | Expected | Actual before | Actual after |
|---|---|---|---|
| Two Lab 1 briefs in Networks / ML with different due dates | 2 tasks, no false conflict | 1 task, same ID 593ae0e4f7dbd674, false conflict | Separate identities; confirmed course/term/key or explicit mapping; regression passes |
| 120-minute task, adjacent 09–10 / 10–11 windows | Valid 09–11 allocation | AssertionError Outside availability through actual solver entry | Same blocks as one 09–11 window, independent validator passes |
| Overlapping windows / real 30-minute gap / DST fold / busy / pin | Union equivalent; no crossing real gaps; fixed constraints | Baseline risks source-reviewed, not all reproduced as historical failures | End-to-end solver checks and independent rejection of gap-crossing pass |
| Repeated semester / same key rename / missing context / replaced source | Predictable identity; no silent merge | Title-only identity collision risk | Different terms separate; exact key survives rename; missing context is unresolved source draft |
| Legacy collision with one override and a receipt | No duplicated override; immutable receipt retained | Reviewed behavior silently merged tasks | Two tasks, ambiguous old override retained for review, backup/alias ledger, receipt exact-equality preserved |
| 540-minute reference, Wednesday removed | Total shortage 120, before-lab shortage 60; Friday alone fails | Original capacity problem already implemented | Both shortage values correct; Friday-only rejected; permitted early+late remedy validated; zero offered relaxations honestly impossible |
| Draft with correct sections/name vs wrong filename/missing Results | Structural pass vs missing; no semantic grade claim | New scoped capability | Filename/format/section/word checks verified; missing caught; PDF-only page count unknown for TXT; screenshot semantics and filename exceptions need review |
| Two chat turns / duplicate / new conversation / foreign tenant / empty response / failed tool | Bounded continuity and truthful outcomes | Fresh runtime session and unconditional completion source-reviewed | Deterministic gateway/Store doubles pass; actual Gemini behavior remains blocked |
| Snapshot refresh then mocked GitHub 429 | Success timestamp unchanged, failure recorded | Snapshot generation advanced last_sync | Original successful time retained; separate generated/fetched/failed fields |

## Recorded checks and denominators

- Full Python suite: **76/76 passed**, 6.01 seconds in the latest completed run at this stage. Includes two new actual-gateway contract tests with explicit managed-provider doubles and 13 continuation cases (parameterized EN/RU/Kazakh proposals included). No paid model calls or real Calendar writes.
- Browser scope: existing eight scenarios plus two new challenge scenarios. The new two passed, including unseen uploaded brief, explicit mapping, structural preflight, student choice to revalidate and fresh preview, EN/RU/Kazakh, 1440×900 / 1280×720 / 1024×768 / 390×844, and automated AA checks. Final aggregate results are recorded in versioned release evidence rather than inferred from an earlier count.
- Native policy: **3/3 passed**; original import rejection/redaction plus exact workshop and conversation method contracts. Installed-package evidence and hashes are separate, versioned checks. Real 0.1.1 unmodified picker success and user-observed bottom-right toast visibility remain historical human evidence; no new toast click/focus pass is claimed.
- Local browser flow observations captured from ordinary verification: plan 51 ms, rescue 51 ms (n=2 requests, median 51 ms, max 51 ms). These are warm local browser-to-gateway observations, **not** Gemini latency, cloud cold-start measurements or p95. Exact final observations live in release evidence. The local busy indicator appears immediately on dispatch; event polling accelerates to one second during work. A remote first-progress SLA is not verified.
- Dependency integrity: pip check passed. No test results establish complete accessibility certification, a prize outcome or general natural-language understanding.

## Boundaries and remaining acceptance

The current public provider remains Render free, one instance/process with ephemeral storage; two-hour isolated capability sessions and earlier restart/redeploy resets are disclosed. The new public deployed commit, HTTPS/browser acceptance, original fetched GitHub commit/time/cache age and new Windows install/build hashes must be read from the manifest and versioned evidence. Current 0.1.1 public deployment remains the known-good release until the new version is observed live and tested.

General academic prose/table extraction: exact page/quote/version/original-expression/context/assumptions/normalized-field proposal validation is prepared through a genuine MCP tool for Gemini. It cannot silently confirm facts. EN/RU/Kazakh ambiguity and invented-quote rejection pass as local contracts. Real multilingual model extraction, confirmation UX acceptance, provider token renewal/cold start, real Calendar consent/write/read-back/revocation, multi-instance cloud state and an isolated unseen-document judge remain pending. Scanned/encrypted/corrupt inputs return bounded useful errors; OCR is unsupported.

Use docs/live_acceptance_batch.md after organizer credits are verified. No GCP paid resources were provisioned in this continuation and personal spending authorization remains USD 0.
