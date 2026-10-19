# Exact residual Windows observations

Installed0.4.0 is unsigned. Source, sandbox/context isolation, allowlist rejection, both import paths, exact read-back/cache and passport transfer/restart have passed installed automated contracts. Those tests substitute Open/Save dialogs. They do not establish an actual new Windows picker, save/cancel UI, banner or click callback. Earlier0.1.1 real picker/banner and user-confirmed0.3 restored45/95 after reopening are preserved as historical results.

Current native automation surface is unavailable; the previous supported helper failed at kernel-assets initialization. No Windows settings, root certificate or permanent execution policy needs changing.

Run in a normal PowerShell window (not the script editor):

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "D:\projects\CampusPulseRELAY\scripts\recheck_final_native.ps1"
```

The separate0.4 verification profile is on D:. The current8000 gateway serves the preserved local datastore; the launcher uses a dedicated desktop profile and a separate workspace. Do not overwrite that datastore. To run a different local backend later, use `scripts/dev.ps1` with a separate `RELAY_DATA_DIR`, preserving existing data. No Google login is required for these local checks.

1. Explore the illustrative workspace. Connections → Import a file. Observe the real Windows picker and Cancel. Record appearance and cancellation separately.
2. Import again, select `D:\projects\CampusPulseRELAY\.local\native-verification\0.4.0-final\native-optics-0.4.0.md`. Confirm the source appears and open its original text. If it fails, copy only the Original diagnostic. No document contents or credentials need to be pasted into chat.
3. Progress & continuity → Workspace Passport → Choose portable workspace. Cancel once, then choose `D:\projects\CampusPulseRELAY\.local\native-verification\0.4.0-final\native-input.relay.json`. Review the restore preview and explicitly choose the fresh-copy import. Check45 logged/95 remaining. Save/export with the actual Save dialog to a new file on D:, then close/reopen and confirm persistence. Appearance, save, restore and restart are distinct results.
4. Connections → Send test notification. Observe the actual Windows banner or Notification Center entry, click it and record whether RELAY focused the intended workspace. No notification-settings change is requested. Visibility and click/focus remain separate results.

Public0.4 and the installed Windows HTTPS Gemini/MCP query have now passed automated acceptance. For a separate human repetition, relaunch this script with `-PublicGateway`, enter a privately issued AI invitation in the app, confirm eligible processing and ask about a new permitted document. Record actual HTTPS gateway revision/model/tool outcome. A local contract or browser run cannot substitute for this installed Windows live query. Keep tokens/keys out of screenshots and reports.
