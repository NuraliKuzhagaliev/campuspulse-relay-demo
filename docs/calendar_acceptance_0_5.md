# Calendar: actual setup and remaining acceptance · 0.5.0

**Technical setup completed; real connection observed by owner; event operations NOT verified.** Public real Gemini remains available without Google login, invitations or visitor API keys. Calendar connection is voluntary and separate. A coding-environment connector is not app consent.

Completed by the owner: Google API User Data Policy acceptance/brand; web OAuth client “CampusPulse RELAY public web”; hidden local DPAPI credential configuration; Calendar API enabled; Audience In production. Console displayed openid/email/calendar.app.created as non-sensitive. Exact callback: https://campuspulse-relay-demo.onrender.com/auth/callback. The ordinary free project gen-lang-client-0595303951 is not assumed eligible for organizer GCP. No personal billing/trial/payment was activated. Server OAuth ID/secret, Fernet encryption key and exact HTTPS gateway are configured. The owner restored the protected original Fernet key and saved the dedicated GitHub token separately. Actual deployed OAuth configuration, PKCE,15-minute private cookie and copied-URL rejection passed; no real Google consent or event call was made by that boundary check.

Default scopes: openid, email and calendar.app.created, limited to separate app-created calendars/events. No shared public write target or private personal Calendar payloads in free Gemini. Existing-calendar access is a separate explicit scope flow and requires its own review; it is not accepted here. The historical calendar in docs/connections.json is not assigned to anonymous visitors.

Implemented boundary: existing isolated workspace → state + independent private HttpOnly Secure Lax cookie + PKCE → one-use server claim → verified Google identity in the SAME workspace → encrypted credentials → explicit separate calendar creation/authorized target → immutable exact preview → explicit approval → deterministic event IDs/ETag/read-back/guarded undo. Web requests expire after15minutes; desktop pairing after5minutes and a second explicit pairing confirmation. Consent alone never approves events. Unknown create outcomes block duplicate retry. Disconnect deletes local credentials and attempts revocation while preserving events. Hosting restart can erase credentials sooner than the session limit, requiring reconnection.

Actual callback attempts failed before completion. Earlier requests expired; the owner now reports copying the authorization URL into a different working browser/window. The private browser binding does not transfer with a URL. Do not remove that check. Expired/cancelled/mismatched callbacks show an EN/RU/Kazakh recovery page with no code/token echo. Protocol successes/failures are simulated test evidence, not actual Google consent.

Owner sequence:

1. Open the ordinary public homepage https://campuspulse-relay-demo.onrender.com/ directly in the browser that works. Start Connections → Connect Google THERE. Finish entirely in the same browser session within15minutes. Do not copy the Google or callback URL from another session, reuse an old callback, or bypass a Google warning.
2. Confirm only the displayed app-created-calendar permission if acceptable. On return verify Google is connected and the original documents/history remain in the same workspace. Report the result without sending callback URLs/codes/secrets.
3. Choose Create a separate study calendar. Retain its actual returned ID privately. Creation is a separate owner action, and no event approval is implied.
4. Remaining actual acceptance: synthetic current plan → immutable real preview → explicit approval → independent Google event ID/ETag/link read-back → idempotent retry → guarded undo → disconnect/revocation. Also check cancellation, lost permission and an independent permitted user. No unrelated calendar/events may change.
5. Desktop browser pairing and actual installed Gemini/Calendar flow remain separate acceptance. Native Save/banner checks are separate again; Windows control was stopped by owner Escape.

No Google event write, real read-back, retry, undo or revocation is claimed. Source implementation and local fault-injection tests cannot turn these gates green. Personal expenses remain prohibited.

Primary references: [Calendar scopes](https://developers.google.com/workspace/calendar/api/auth), [OAuth web flow](https://developers.google.com/identity/protocols/oauth2/web-server), [OAuth security](https://www.rfc-editor.org/rfc/rfc9700.html).

Owner connection update: actual status screenshot confirms configured=true, connected=true, calendar_live=false at that observation. The owner subsequently reports selecting the created calendar; exact returned target/live status and actual event operations remain to verify. No additional browser transfer/reconnect is needed. Evidence: audit-calendar-owner-connected.json (image hash only, no credentials).
