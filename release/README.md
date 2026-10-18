# CampusPulse RELAY 0.1.1 — local release candidate

All project-controlled files are under D:\projects\CampusPulseRELAY. This package is not a completed cloud submission. Agent Engine/Gemini/public web/live Calendar verification is pending organizer credit activation and account access. Personal cloud spending is not authorized.

## Open and run

Run `scripts/dev.ps1` from the project root, then open http://127.0.0.1:8000. For a clean source checkout, run `scripts/bootstrap.ps1` first (Python 3.13 and Node 22+ prerequisites). Dependencies/caches/temp/builds use D: through `scripts/env.ps1`.

Install `windows/CampusPulse-RELAY-0.1.1-x64-setup.exe`, or run the portable executable. Default installation is D:\projects\CampusPulseRELAY\installed\CampusPulse RELAY. The desktop uses the same running local gateway; it does not bundle a Python server. A verified future HTTPS gateway can be selected with RELAY_GATEWAY_URL. The installer is unsigned; do not claim publisher verification or bypass OS security policies.

To uninstall, close the app from its tray menu and run the uninstaller in its D: installation folder or Windows Installed apps. User data on D: is retained. Review/export it before any cleanup. `scripts/cleanup.ps1` defaults to a dry run and only targets explicitly named project-owned locations.

## Deliverables and evidence

- Windows setup and portable executables; actual hashes are in manifest.json.
- Source ZIP at the pinned source commit, excluding credentials, input attachments, environments and caches. Generated manifest/test-summary rollups are distributed alongside the archive to avoid circular hashes or stale embedded metadata; detailed test evidence remains in its docs/ folder.
- Eight-slide editable PowerPoint and rendered PDF under presentation/.
- Recorded local walkthrough under recordings/ (125.48 seconds). It labels the illustrative Calendar and disconnected cloud state.
- docs/evidence/: tests, installed Windows smoke, real background source-change proof, current/historical MCP traces and artifact validation.
- README.md, REQUIREMENTS.md, BLOCKERS.md and docs/judge_quickstart.md provide implementation entries, independent local steps and exact pending gates.

After organizer activation arrives, verify the exact eligible project, billing account, balance and expiration before selecting funding or provisioning. Follow docs/cloud_setup.md. Deployment scripts include credit-metadata preflight; no personal/out-of-pocket authorization is implied. Any uncovered paid cost needs separate approval.

Release 0.1.0 is preserved with verified original artifact hashes under versions/0.1.0. The retained 2:05 recording was captured on 0.1.0; it remains labeled a local illustrative backup. The 0.1.1 presentation and manifest identify current translation and native-check results. Repeat the real picker/notification check with docs/native_windows_check.md; unperformed human checks are not marked passed.

The corrected installed 0.1.1 build passes both desktop import routes, exact-content read-back, state refresh/cache and rejection guards. The real unmodified picker import also passed in the original verification profile, and the user confirmed the actual bottom-right Windows banner. A notification click/focus callback was not observed. Details and sanitized trace stages are in docs/desktop_import_fix.md and docs/evidence/desktop-native-result.json. EN/RU/Kazakh operational UI translations are complete and locally tested; original evidence and exact action titles remain verbatim.
