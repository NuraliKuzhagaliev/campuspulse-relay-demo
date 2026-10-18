# Installed Windows native check — human interaction recorded separately

The automated installed regression in `desktop-smoke.json` uses an instrumented picker. It does not establish real native-picker interaction or notification visibility. The separate result is `desktop-native-result.json`; never infer visibility from `Notification.isSupported`, dispatch, or an OS show event alone.

Windows Computer Use failed twice, including after a kernel reset, with `failed to write kernel assets (os error 3)`. No alternative OS input automation was used. The observation harness launches the installed executable and reads metadata, native callback logs and the imported source. It never replaces `dialog.showOpenDialog` or `Notification`, and never synthesizes clicks. All picker input and the OS notification click are human actions.

To repeat on the prepared D: machine:

```powershell
cd D:\projects\CampusPulseRELAY
. .\scripts\env.ps1
node scripts/verify_native_interactive.mjs
```

The local gateway must be running (`scripts/dev.ps1` in another terminal). The harness prints a unique fixture path under `.local/native-verification/` on D: and opens the installed app with a separate D: profile. It waits up to thirty minutes and saves actual outcomes, including incomplete checks. To reopen the original workspace after the import correction, use:

```powershell
node scripts/verify_native_interactive.mjs --profile 'D:\projects\CampusPulseRELAY\.local\native-verification\0.1.1-mvebaaui\profile' --fixture 'D:\projects\CampusPulseRELAY\.local\native-verification\0.1.1-mvebaaui\native-picker-mvebaaui.md'
```

The user confirmed picker appearance. The reported unsupported-request error was reproduced on the renderer file-input path and corrected; see `docs/desktop_import_fix.md`. The original incident's rejected method/path were not logged and cannot be recovered retroactively. The real unmodified picker recheck succeeded in the same profile at 2026-10-18 21:21:11 UTC: file read, upload, refresh and snapshot save completed, and independent read-back matched the fixture exactly. The user then confirmed successful operation and actual notification visibility as a bottom-right Windows banner. Dispatch and OS show events are also recorded, but human observation establishes visibility. No click callback was observed, so click/focus behavior is unverified. The new installed build records sanitized rejected requests and selection/read/upload/refresh/cache stages in `profile/logs/desktop-trace.jsonl`. No local upload needs Google authentication.

1. In the installed app, enter **Explore illustrative workspace**, then **Connections**. Use English for these exact button names, or choose Russian/Kazakh equivalents.
2. Click **Import a file**. Observe the real Windows picker. Click **Cancel**. The app records actual native open/cancel callbacks.
3. Click **Import a file** again. Paste the exact fixture path printed by this run into **File name**, then click **Open**. Confirm the unique `native-picker-…md` source appears. The harness compares the actual imported page with the file's exact contents.
4. Return to **Connections → Send test notification**. Observe the actual Windows banner or its entry in Notification Center, and report where it appeared. Optionally click the OS notification to test focus restoration; record clicking separately. The in-app “notification requested” notice is not the Windows notification. Visibility may be verified by an actual click or explicit human observation, never by dispatch/show callbacks alone.
5. Report which native window appeared, whether import succeeded, and whether the notification was visible as a banner or in Notification Center. If none appeared, record that failure. No Google connection, Calendar write, Windows security/privacy setting change, or cloud call is needed.

The installer and portable app are unsigned. Notification registration uses the application's `dev.campuspulse.relay` AppUserModelID and the installed shortcut; this follows [Electron's Windows notification guidance](https://www.electronjs.org/docs/latest/tutorial/notifications#windows). The completed run's actual visibility was confirmed by the user. OS dialog buttons follow the Windows display language; app-controlled picker titles, filters, tray items and notification text follow the selected EN/RU/Kazakh UI language. Native callback logs contain IDs, event types, language and timestamps, without private document text or filesystem paths.

No native UI screenshot was obtained through the failed helper. Renderer screenshots are labeled as renderer evidence. Google consent, real Calendar write/read-back and Gemini/Agent Engine acceptance remain pending organizer credits and verified account access.
