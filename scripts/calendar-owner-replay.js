/* Advanced owner-only acceptance, pasted after reading into the SAME site's
 * browser console. Requires ONE already verified real synthetic test event.
 * Credentials/digests stay in that browser. No tokens or payloads are printed.
 * This repeats only the original approved request, then performs read-back.
 * It never creates a plan, new preview, new permission or undo authorization.
 */
(async () => {
  if (location.origin !== "https://campuspulse-relay-demo.onrender.com")
    throw new Error("Open the ordinary RELAY site in the consenting browser first.");
  const read = async (path) => {
    const response = await fetch(path, { credentials: "same-origin" });
    if (!response.ok) throw new Error("Session/read unavailable: HTTP " + response.status);
    return response.json();
  };
  const session = await read("/api/session");
  const state = await read("/api/state");
  if (state.tasks.length !== 1 || state.tasks[0].title !== "RELAY Calendar acceptance check")
    throw new Error("Use a separate workspace containing only the synthetic Calendar acceptance task.");
  const receipts = state.receipts.filter(r => r.mode === "live" && r.status === "verified");
  if (receipts.length !== 1) throw new Error("Exactly one previously verified real test receipt is required.");
  const receipt = receipts[0];
  if (receipt.outcomes.length !== 1 || receipt.outcomes[0].operation !== "create" ||
      receipt.calendar_id !== state.settings.calendar_id || !state.settings.calendar_live ||
      !/^[a-f0-9]{32}$/.test(receipt.id))
    throw new Error("The original one-event approval does not match the current selected calendar.");
  if (!confirm("Repeat ONLY the already approved synthetic test request for this calendar?\n" + receipt.calendar_id +
      "\nThis must return the same receipt without creating another event. Cancel if unsure."))
    return { cancelled: true, request_sent: false };
  const response = await fetch("/api/previews/" + receipt.id + "/approve", {
    method: "POST", credentials: "same-origin",
    headers: { "Content-Type": "application/json", "X-Relay-CSRF": session.csrf },
    body: JSON.stringify({ digest: receipt.digest }),
  });
  if (!response.ok) throw new Error("Original request replay did not succeed: HTTP " + response.status + ". Inspect the operation; do not create a new preview or retry automatically.");
  const again = await response.json();
  const verification = await fetch("/api/receipts/" + receipt.id + "/verify", {
    method: "POST", credentials: "same-origin", headers: { "X-Relay-CSRF": session.csrf },
  });
  if (!verification.ok) throw new Error("Replay returned, but fresh read-back failed: HTTP " + verification.status);
  const checked = await verification.json();
  return {
    original_approved_request_replayed: true,
    same_receipt: again.id === receipt.id,
    same_event: again.outcomes?.length === 1 && again.outcomes[0].event_id === receipt.outcomes[0].event_id,
    status: again.status,
    fresh_read_back_matches: checked.results?.length === 1 && checked.results[0].matches === true,
    google_calendar_event_count_still_one: "Owner must confirm visually in Google Calendar",
    credentials_or_approval_payload_printed: false,
  };
})();
