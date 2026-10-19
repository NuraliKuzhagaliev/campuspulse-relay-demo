"""Update current ledgers, preserving the pre-audit release history."""
from pathlib import Path
import shutil
root=Path(__file__).resolve().parents[1];history=root/'docs/history/0.4.1-before-audit'
for name in ('docs/architecture.md','docs/mcp_catalog.md','DECISIONS.md'):
    path=root/name;target=history/name;target.parent.mkdir(parents=True,exist_ok=True)
    if not target.exists():shutil.copyfile(path,target)
(root/'REQUIREMENTS.md').write_text('''# Requirements and acceptance · 0.5.0 audit candidate

Topic2 GDG Astana CampusPulse AI. **NON_GCP_READY pending** until current hosted own-document/Gemini/sample/Windows/Calendar gates are actually accepted. No source module or old test total substitutes for acceptance.

| Requirement | Current result |
|---|---|
| Own academic documents EN/RU/Kazakh | Unicode/structured/prose drafts, grouped cited semantic proposals and explicit atomic review implemented; new local deterministic/UI checks passed; current hosted real-provider batch pending |
| Evidence/conflicts and identity | Cross-page exact quotes, stable source-local sections and explicit canonical keys; original decisions/history retained; no title-only fuzzy joining |
| Plan/what-if/packets/Preflight/progress/Passport | Full local own-PDF UI sequence passed, including75source→90allocation,45logged/95remaining and fresh-copy restore; empty/unassessed rubric stays unassessed |
| F1–F5 enhancements | Locally implemented; real Calendar and full enhancement-level Gemini acceptance pending; no relabeling of illustrative receipts as Google writes |
| Public independent AI | No invites/registration/Google login/visitor keys; previous0.4.1real acceptance retained;0.5source must pass fresh deployed UI checks |
| Isolation and fair quotas | Tenant/capability/CSRF/one-outstanding-job/FIFO/quota/backoff preserved; audit100provider-simulated HTTP sessions use zero Gemini calls; actual traffic capacity is bounded and not guaranteed |
| File boundary |2MiBraw file,3MiBtransport,100PDFpages/250ktext, disposable bounded PDF worker; near/at/over and expansion checks recorded separately |
| GitHub change radar | Shared singleflight/conditional/immutable cache and awake-server polling implemented; current hosted live recovery/no-browser polling evidence pending |
| Samples |13synthetic cases plus trilingual guide, expected context and ZIP. Local download/unzip/hash and PDF visual checks passed; current public download/use pending |
| Real Calendar | Optional per visitor, required product integration. Narrow app-created-calendar consent, encrypted credentials, separate target/preview/approval and recovery boundaries implemented; actual app client/publishing eligibility/consent/write/read-back/native pairing pending |
| Windows | Original45/95 and sealed packages preserved. New0.5installer/portable/installed/native physical acceptance still to complete |
| Managed GCP | Pending actual organizer T0/project/coverage/model/quotas/IAM/resource/query.12hours after activation; personal payment/trial/billing upgrades prohibited. Offline SDK/shared-state/owner-routing contracts tested, not deployed |
| After-window fallback | Prepared no-restart owner-signed route switch and automatic cutoff, existing backend remains authoritative. Actual GCP-off/expiry full-product acceptance pending real window |
| Presentation/package | Prior0.4.1PDF/PPTX/packages unchanged; new audited0.5versioned package to be sealed from actual results |

See docs/audit_U1_U16.md for per-defect evidence. Current public storage is temporary and may reset on Free host restart/redeploy; no durable/always-on/SLA claim. Public and managed/historical/current-availability statuses remain separate.
''',encoding='utf-8')
(root/'docs/cloud_setup.md').write_text('''# Current cloud preparation · organizer window

The current instructions are `organizer_window_runbook.md`. Latest supplied notice: tutorial20October10:00,12hours after actual activation. No organizer project, T0, expiry, coverage, model/region/quotas or managed resource has yet been verified. Do not infer eligibility of the AI Studio free project or the closed personal trial. No personal spending, paid activation, billing attachment, prepayment or personal Free Trial is authorized.

Read-only SDK/package/serialization and shared-state/session/owner-routing simulations are preparation only. The minimal prepared route uses a managed agent and organizer-covered query bridge with Google service identity to the protected existing MCP/state backend. Public visitors keep their anonymous capability workspace, documents/history/progress, free fallback and separate optional Calendar consent. Store configuration changes do not restart the public host. Real deployment/query/cleanup requires actual organizer coverage and an owned resource ledger.

Historical trial-only instructions are retained under docs/history/0.4.1-before-audit; they do not govern this stage. Actual0.5Calendar client/consent setup is independent of GCP credits: calendar_acceptance_0_5.md. Do not mistake a coding-tool Calendar connector for application consent.
''',encoding='utf-8')
path=root/'DECISIONS.md';old=path.read_text(encoding='utf-8')
prefix='''# Current audit decisions ·19October2026

- The final audit prompt supersedes prior funding notices: actual organizer access is expected tomorrow for12hours after activation. No personal trial/payment/billing upgrade. Actual project/window/coverage and mandatory managed deployment remain pending.
-0.5keeps anonymous public Gemini/MCP access and isolated own/example workspaces. Grouped cited proposals require per-entity explicit atomic review; exact source effort is distinct from rounded solver allocation and reported remaining work.
- Public state remains authoritative outside the temporary lab. A narrow checkpoint/quota RPC, signed machine/workspace boundary and optional organizer query bridge avoid an unfinished data-store fork. Owner routing activation/retirement is signed with a separate DPAPI key and does not reset visitor state. All real GCP evidence is still pending.
- Calendar connection is voluntary per visitor but a required product feature. Default app-created-calendar scopes are separate from optional existing-calendar consent. Consent never approves study writes; desktop credentials are not granted before explicit pairing approval. Real Google acceptance and publishing eligibility are pending.
- Previous decisions below retain historical context only where not superseded. Sealed releases and original45/95 are preserved; new outputs remain on D:.

## Historical decisions

'''
if not old.startswith('# Current audit decisions'):path.write_text(prefix+old,encoding='utf-8')
path=root/'docs/architecture.md';old=path.read_text(encoding='utf-8')
if not old.startswith('# Current0.5'):
 path.write_text('''# Current0.5architecture and trust boundaries

The public React/Electron app uses capability-cookie/CSRF workspace authorization. Own documents and examples have distinct server-generated workspaces; the owner key never enters clients. Source imports have one2MiBcontract, bounded PDF subprocesses and exact page/version quotations. Semantic MCP proposals are untrusted interpretations until one-entity atomic UI review. Progress, source effort and solver allocation remain separate. Passport copies archived untrusted claims, never connection or approval authority.

Anonymous AI jobs share the existing bounded fair quota-aware queue. MCP requires machine transport identity plus a short-lived audience-bound workspace context; tool schemas do not carry tenant authority. Public model tools exclude private Calendar payloads and mutations. Calendar OAuth is voluntary, same-workspace state/PKCE, minimum created-calendar scope by default, encrypted refresh and a separate exact preview/approval/read-back journal. A revoked Calendar leaves files/progress accessible and cannot silently make an empty busy calendar look fresh.

Prepared organizer route (disabled until actual activation): Render remains authoritative for documents/history/progress/plans/ADK checkpoints. An owner-signed no-restart configuration selects one organizer-covered Cloud Run query bridge→actual Agent Engine. The runtime uses its Google service ID token plus bounded workspace context to the existing protected MCP and narrow run-scoped checkpoint/quota RPC. No broad database proxy, approval writer, permanent SA key or copied owner access token. Public safe tool filtering also applies in the managed route. Initial invocation has a durable run claim; unknown outcomes are not replayed automatically on free Gemini. At the actual retirement cutoff the existing free route resumes with the same state; real expiry/cutover acceptance is pending.

Firestore transaction buffering/cross-workspace copy is separately prepared/tested with a fake adapter and is not required for this state-preserving route. Actual Google IAM/resource/session behavior must be verified tomorrow. Older descriptions below are historical and do not imply the new route is deployed.

## Earlier architecture

'''+old,encoding='utf-8')
path=root/'docs/mcp_catalog.md';old=path.read_text(encoding='utf-8')
if not old.startswith('# Current0.5'):
 path.write_text('''# Current0.5MCP additions

Actual alternative-host MCP is protected loopback `/_relay/mcp/`, reached by server-owned transport bearer + signed workspace context. Anonymous visitors cannot call it directly. `read_course_source(source_id,page,offset,limit,search)` exposes bounded continuation/next_offset/page_count and literal search, preserving original offsets/quotes. `propose_academic_extraction` accepts distinct entity_id labels and cited title/course/term/key/due/minutes/rubric/normalized requirement fields; it records proposals only. Per-entity confirmation is a separate capability/CSRF-protected UI operation, never a model tool. Real loopback protocol evidence: docs/evidence/audit-mcp.json; no model/cloud calls in that smoke.

Prepared managed path `/managed/mcp/` additionally verifies actual Google machine principal/audience and organizer window. The narrow `/internal/runtime-state` cannot read private connections or write approvals; it is bound to the existing active public run/conversation. `/internal/managed-route` requires the independent owner's fresh signature and is not a model tool or invitation issuer. These endpoints are disabled by missing actual organizer configuration and do not imply managed acceptance.

The existing public safe tool catalog is reused under both public inference modes. Older catalog notes below are historical; private mutation tools still require pre-existing authenticated UI authorizations and are excluded from public model discovery.

## Earlier tool catalog

'''+old,encoding='utf-8')
print('Current requirement, architecture, funding and MCP ledgers updated; historical copies preserved.')
