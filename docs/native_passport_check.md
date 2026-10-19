# Exact residual native check — installed 0.3.0

## Human follow-up — 2026-10-19

The user's screenshot confirms the restored Web Engineering · Web project displays **45 actual logged minutes** and **95 explicit remaining minutes**. After closing and reopening the installed app in the same dedicated profile, the user explicitly confirmed: “yes, it still shows 45 minutes logged and 95 remaining after reopening”. **Restored progress display and restart persistence pass.** See `docs/evidence/four-native-human-followup-0.3.0.json`.

The direct launcher command initially failed because PowerShell execution policy blocked the script before execution. The inspected launcher was subsequently run with a one-process override; no persistent Windows policy setting was changed. Do not repeat the passport import to test restart persistence.

Real Open/Save dialog visibility, their cancel behavior, a human-saved output file and new notification visibility/click focus remain separate unconfirmed results. The original pending evidence and sealed release manifests/packages describe their earlier observation time and are preserved unchanged.

## Original check procedure and evidence boundary

The supported Windows control helper was initialized via `@oai/sky` and failed before exposing apps/windows: `failed to write kernel assets: Системе не удается найти указанный путь. (os error 3)`. No alternate Windows UI automation was used. This is a control-environment limitation, not successful native acceptance.

The real installed executable, packaged/source byte comparison, restricted IPC, selected-file reads, JSON validation, save writes, cancel result, cross-device round trip, retry and restart persistence passed with explicit Open/Save dialog substitutions. The later human confirmation above additionally establishes restored progress display and restart persistence in the unmodified app. Genuine unmodified dialog appearance/interaction remains separate. Prior real 0.1.1 academic picker/import and bottom-right banner proof is retained; no new banner or click/focus claim is made.

With the candidate backend running on localhost8000, run `scripts/recheck_passport_native.ps1`. It opens the actual installed executable with a dedicated D: profile and does **not** replace or intercept any native dialog.

1. If shown, choose **Explore illustrative workspace**. Expand **Progress & continuity → Workspace Passport → Choose portable workspace**. Confirm a real Windows Open dialog appears, then **Cancel**. No workspace switch/restore preview should appear.
2. Choose again. In File name use `D:\projects\CampusPulseRELAY\.local\native-verification\0.3.0-passport\native-input.relay.json`. Open, inspect the restore preview and choose **Import as fresh copy and switch**.
3. Expand **Progress & continuity → Progress & Remaining Work**, choose **Web Engineering · Web project**. Check **45** actual logged minutes and **95** explicit remaining minutes (solver rounds up to120); both remain personal reports. Two distinct Lab1 assignments in History/Ethics and archived source labels remain.
4. **Workspace Passport → Preview portable workspace → Download .relay.json**. Confirm a real native Save dialog appears. Save to `D:\projects\CampusPulseRELAY\.local\native-verification\0.3.0-passport\native-roundtrip.relay.json`. Canceling Save should leave the workspace unchanged; repeat and save if checking both.
5. Close the application, run the same script again, and verify the same restored workspace/progress remains. No Google login, cloud resource, Windows setting or notification change is needed.

Report Open-dialog visibility, Open cancel, restore success, Save-dialog visibility/actual saved file and restart persistence separately. On failure provide Original diagnostic only; logs contain sanitized method/path/status, never file contents or credentials. These are the only residual human checks for the new native passport path.
