# Workspace Passport v1

Manual file transfer, not automatic device sync or permanent hosted storage. The local 0.3.0 candidate adds validated restore to the previous download-only snapshot. Public hosting remains on 0.2.1 until a separately authorized replacement.

The `.relay.json` envelope has exactly `format: campuspulse-relay-workspace`, integer `version: 1`, `exported_at`, `payload` and `sha256`. Unsupported versions fail closed. Version 1 is the first restorable format. Previous snapshot JSON is detected and explained: it contains task/settings/receipt summaries but normally omits source pages, so it cannot reconstruct cited coursework. Originals must be re-imported; missing pages are never invented.

## Portable content

Explicitly selected sources include bounded normalized page/text extracts, title, basename, portable identity/version and a historical original-hash claim. Assignments include exact course/term/key and source/section relationships. Exact citations include quote/page/field/value. Explicit estimate overrides, internal prerequisites, work logs/corrections, personal remaining/completion reports, frozen estimate provenance, clarification choices/unknown decisions, configured gate definitions, timezone, availability windows and daily cap travel with the file. Source selection cannot silently drop required evidence or prerequisites: the export fails with a useful explanation.

**Excluded:** original binary files, authentication identities, credentials, tokens/cookies/CSRF, machine paths, Calendar IDs/connections/event descriptions, conversation/session history, live upstream gate observations, approvals, operation journals, actionable receipts and accepted plans. Calendar busy intervals/events must be re-imported or rechecked before meaningful scheduling on the new device. Included source text remains an archived untrusted extracted copy, never proof that an original PDF or a GitHub revision was reverified. Restored gate definitions start unknown and require repository/source revalidation. Historical user decisions retain their origin/time and archived trust label. Imported history is excluded from personalized estimate samples.

## Hashes and trust

`sha256` hashes compact sorted-key UTF-8 JSON of the payload (`ensure_ascii=False`, no NaN/Infinity). Integral floats normalize to integers recursively before hashing, making browser `JSON.parse/stringify` loss of `.0` harmless. Dates remain original strings; exact quotes remain untranslated. This detects accidental changes, not authenticity: anyone can edit a file and recompute its checksum. Imported text and user claims never gain external-write authority.

Historic import `content_hash` used `digest(content.hex())`: SHA-256 of the canonical JSON encoding of the hex string, including JSON string quotes. It was **not** raw-byte SHA-256. Restored extracts use separately named `sha256(canonical_json(extracted_pages))`; the original historical algorithm/value remains a labeled unverified claim. Re-export keeps the correct current extract-hash algorithm. An upstream PR response hash is a different explicitly named raw-response SHA-256 in observation evidence, not a source-file hash.

## Bounds and transaction

Maximum file size 2 MiB; 12 sources; 100 pages and 250,000 text characters per source; 50 assignments/progress/override/clarification records; 500 logs; 1,000 citations; 10 gates; 100 availability intervals; depth 16. Strict envelope/source/assignment fields and reference validation reject unsupported data. Duplicate JSON keys and non-finite numbers are rejected. Source quotes must occur on the included page and facts must be reproducible from the included extracts before commit. Plain embedded markup stays untrusted text and is never rendered as HTML, fetched, executed or indexed.

Restore preview lasts ten minutes, at most five active previews. Validation stages data under the authenticated destination session. A SQLite `BEGIN IMMEDIATE` transaction creates a new server-generated tenant/source namespace, remaps citations/references, records archived claims and marks one stage committed. It also records scope registration atomically. Any failure rolls back the whole copy. Repeated confirmation recovers the same copy. The current workspace stays intact; the session deliberately switches only after successful commit. Public restores retain the original session expiry and public `demo-` scope. Cross-tenant stage IDs fail authorization. A restored file cannot reconnect Google, verify Gemini, apply or undo any previous Calendar action.

SQLite is the verified implementation. Addition transactions in Firestore fail closed (`FEATURE_PENDING`) until the deferred integration phase; no Firestore atomicity is claimed.

## Desktop and browser

Native restore reuses the trusted selected-file handler with the explicit `passport` purpose, JSON-only filter and 2 MiB bound. Academic import keeps its previous file types and `/api/import-native` correction. IPC remains exact method/path allowlisted; no generic proxy or arbitrary renderer path is added. Native save uses a user-selected `.json` path on D:, checks resolved parent and rejects symlinks, then writes a D: temporary sibling and atomically renames. Cancel does not switch or import. Browser download uses its normal download control; choose D: in the browser save dialog. Browser automation explicitly saves all downloads under D:.

Actual evidence: `docs/evidence/four-desktop-0.3.0.json`, `desktop-contract-0.3.0.json`, `desktop-import-regression-0.3.0.json`, Python security/rollback tests, and browser logs. Installed dialog substitutions are explicitly marked; real unmodified Open/Save/cancel observation remains the precise residual native check in `docs/native_passport_check.md`.
