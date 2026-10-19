# CampusPulse RELAY0.3.0-r1 — reviewable local candidate

The four additions are implemented and independently verified locally/installed: Progress & Remaining Work, Clarify First, Handoff Radar and Workspace Passport. Real unmodified native passport Open/Save/cancel interaction remains a human gate; see `docs/native_passport_check.md`. Installed automated dialogs were explicitly substituted. This is not a published GitHub release or a complete live GCP submission.

## Artifacts on D:

- `windows/CampusPulse-RELAY-0.3.0-x64-setup.exe`: unsigned NSIS x64 installer; install only under D:.
- `windows/CampusPulse-RELAY-0.3.0-x64-portable.exe`: unsigned portable app. Set `RELAY_DESKTOP_DATA` to a D: profile. Connected functionality needs the actual local backend on localhost8000; Python is not embedded.
- `web/CampusPulseRELAY-0.3.0-r1-web-app.zip`: complete built React client **and actual Python backend**, minimal requirements, sample fixtures and D: launcher. Extract under D: and run `scripts/run-web-bundle.ps1` using existing Python3.13. Dependencies/temp/cache/data are created under that D: directory. It is a local illustrative web package, not an independently hosted URL.
- `source/CampusPulseRELAY-0.3.0-r1-source.zip`: committed local source, locks, tests, evidence, docs and full future deployment infrastructure. Source revision/branch recorded in manifest and archive metadata. Not pushed/published.
- `manifest.json`, `SHA256SUMS.txt`: actual artifact hashes and verification/pending boundaries. Sealed copies under `versions/0.3.0-r1/` cannot be overwritten by the recorder.

Prior0.1.0, corrected0.1.1, public0.1.1, superseded0.2.0 and public0.2.1 artifacts are preserved with original hashes under `versions/`. The installed0.2.1 directory is separately retained as `D:\projects\CampusPulseRELAY\installed\preserved-0.2.1`.

## Public deployment and presentation

https://campuspulse-relay-demo.onrender.com still serves verified0.2.1 at83552161ec22c7cf44746433425d3b2b99e042c4. Render remains free with automatic deployment disabled. No replacement deployment was performed for0.3.0. Public sessions/storage remain temporary, maximum two hours and potentially earlier reset.

The preserved ten-slide prior-release presentation remains at `presentation/CampusPulse-RELAY-0.2.1-quality-verified.pptx` and `.pdf`. It was not regenerated or relabeled as0.3.0/live GCP acceptance. Its hashes remain in the preserved0.2.1 manifest. The new combined demonstration is documented in `docs/four_additions_design.md`.

## Verified and pending

111 Python tests;13 local browser workflows plus one public-only skip;4 local public-mode workflows including two-tab reset;4 desktop route-policy tests; installed both-import-path and feature/approval/language/persistence gates; bidirectional web/installed passport semantic comparison;14 actual signed local MCP tools and real read-only public PR metadata. Three operational languages and four viewport widths checked. Detailed evidence: `docs/four_additions_acceptance.md` and `docs/evidence/four-evaluation-0.3.0.json`.

Passport files are unencrypted untrusted archived extracts/personal claims. They exclude original binaries, Calendar busy details/connections, approvals/journals and accepted plans. Re-import/reconnect/recompute before operational use. They are manual transfer, not automatic sync or durable hosting. No credentials belong in the file.

Gemini/Agent Engine, cloud-to-MCP identity, real Calendar consent/write/readback and hosted authenticated unseen-document judge acceptance remain deferred. Organizer credit eligible project/billing/balance/expiration are unconfirmed; no uncovered personal spending is authorized. No new model request, Calendar write, GCP provisioning, PR/issue/comment or GitHub release was performed.
