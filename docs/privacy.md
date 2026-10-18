# Privacy and boundaries

Only selected files and the explicitly chosen repository/calendar are used. No arbitrary disk indexing, repo execution, invitations, outgoing messages or coursework submission occurs. The selected-folder watcher is opt-in, bounded and non-recursive; it announces changes and requires explicit file import rather than silently uploading them.

Cloud identity is derived from verified Google subject, never model-supplied IDs. MCP context is short-lived and audience-bound; machine identity is distinct from user Calendar consent. OAuth uses state/PKCE and an external browser. Refresh credentials are encrypted server-side; secrets belong in Secret Manager/.env, excluded from Git and release bundles. Cloud IAM, real OAuth revocation and isolated judge access still need live validation.

Application records retain selected extracted source text/quotes, versions, plans and action receipts to make decisions auditable. Run logs contain operational summaries rather than complete student documents or private reasoning. Local snapshots are scoped to workspace identity and labeled offline; authenticated failures must not fall back to another workspace's cache. Device caches rely on the Windows account's protection and are not a general encrypted document vault.

Export is available in Connections and through `/api/export`. `/api/workspace` DELETE removes that verified workspace's application records, including stored connection material; it does not delete GitHub repositories or Calendar resources. This prototype has no automatic retention/purge policy. Local device snapshots can be removed under `.local/desktop` after closing the application; browser site data can also be cleared. Google connection access can be revoked under the Google account's third-party connections. Live revocation behavior remains unverified.

Documents, repository text and tool output are untrusted data. Their contents cannot approve writes, change application policy or select another tenant. URL/path/size validation and typed errors contain the supported workflows; this is not a comprehensive external security audit.
