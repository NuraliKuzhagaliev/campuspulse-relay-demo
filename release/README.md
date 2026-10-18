# CampusPulse RELAY 0.2.1

Public illustrative web: https://campuspulse-relay-demo.onrender.com . Mandatory GCP/Gemini/real Calendar acceptance remains pending organizer credits and access. No uncovered personal spending is authorized. Everything project-controlled is under D:\projects\CampusPulseRELAY.

## Current deliverables

Exact SHA-256 values, source archive commit, deployed runtime commit and limitations are in manifest.json and SHA256SUMS.txt.

- windows/CampusPulse-RELAY-0.2.1-x64-setup.exe
- windows/CampusPulse-RELAY-0.2.1-x64-portable.exe
- source/CampusPulseRELAY-0.2.1-source.zip
- web/CampusPulseRELAY-0.2.1-web-build.zip
- presentation/CampusPulse-RELAY-0.2.1-quality-verified.pptx
- presentation/CampusPulse-RELAY-0.2.1-quality-verified.pdf

The frontend ZIP needs the FastAPI backend; complete Python sources, exact dependencies and Docker configuration are in the source ZIP. The PPTX has ten native editable slides; its PDF uses rendered slide pages. Prior presentation and recording artifacts are retained, not relabeled as this release.

## Run / install

From a fresh checkout, run scripts/bootstrap.ps1, then scripts/dev.ps1 (existing Python3.13, Node22+ and Git required). Controlled environments, caches and temporary outputs use D: through scripts/env.ps1. Open http://127.0.0.1:8000 or the installed Windows app. The desktop does not bundle Python and needs the running local gateway for connected operations. Its offline snapshot mode does not perform writes. RELAY_GATEWAY_URL may select a configured HTTPS gateway.

The NSIS default is D:\projects\CampusPulseRELAY\installed\CampusPulse RELAY. The installed 0.2.1 package is verified against current built main/preload/policy/locales/renderer files. Both import paths, task edits, source/export/conversation, recovery/preflight/approval/read-back/undo and locale/reopen/resized-window checks pass. The package is unsigned. No publisher verification or OS-security bypass is claimed.

To uninstall, close the app via its tray menu and run its D: uninstaller or Windows Installed apps. User data on D: is retained. Review/export it before cleanup; scripts/cleanup.ps1 defaults to dry run and named project-owned targets.

## Preserved releases and native observation

versions/0.1.0, versions/0.1.1 and versions/0.1.1-public-demo retain original artifact hashes/manifests. A separate complete 0.1.1 installed copy is preserved on D:. The old 125.48-second recording is a 0.1.0 local illustrative backup. The real unmodified native picker and actual bottom-right banner were human-verified on corrected 0.1.1. New 0.2.1 automation is recorded separately; no new native appearance/banner/click/focus observation is inferred. Notification click/focus remains unverified. See docs/native_windows_check.md.

Generate this version's metadata with scripts/package_continuation.py after its gates pass. Historical 0.1.1 recorders refuse the new version. Already preserved releases cannot be overwritten by that recorder. No credentials, private uploads, environments or caches belong in source bundles.

## After credits

Verify organizer activation instructions, eligible project, billing account, balance and expiration before funding selection or billable provisioning. See docs/cloud_setup.md and docs/live_acceptance_batch.md. Any uncovered cost needs separate approval. The free public demo and local test counts do not satisfy the mandatory managed-agent requirement.
