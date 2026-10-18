# GCP pilot estimate — organizer credits pending, personal spending declined

The user has **not authorized USD 25 of personal/out-of-pocket spending**. Organizer credit activation instructions are expected tomorrow, but availability, eligible project/billing account, balance and expiration are unconfirmed. Wait for those instructions before selecting the final billing account/project or provisioning billable resources. Do not assume an existing project is eligible.

The earlier USD 25 / 72-hour envelope is an estimate for review only, not approval. After activation, re-estimate within the actual eligible credit balance and expiration, run two bounded smoke calls first, and explain any uncovered cost for separate approval. Taxes, currency conversion and account prepayment are separate human decisions. This estimate is not a guarantee or a cloud-enforced spending cap.

Use one managed runtime (min 0 / max 2 instances), two small Cloud Run services (min 0 / max 2), one Firestore database, a staging/upload bucket, Artifact Registry image, Secret Manager and one minute-level Scheduler job. No GPU, Memory Bank, vector database, paid search or additional model layers are planned.

At the checked standard regional Gemini 3.5 Flash rates, an illustrative **aggregate** 1M input + 200k output token pilot is about **USD 3.63** ($1.65 + $1.98), excluding additional reasoning/output tokens and all infrastructure. It is not a per-request estimate. Repeated tool turns re-send context, so measure total usage. [Official model prices](https://cloud.google.com/gemini-enterprise-agent-platform/generative-ai/pricing).

Google's published Agent Engine update lists runtime $0.0864/vCPU-hour and $0.0090/GiB-hour. At 1 vCPU + 4 GiB, 10 active instance-hours would be about **USD 1.22**; 72 hours with two continuously active instances would be roughly **USD 17.63** for that runtime alone. Actual regional SKUs and billing granularity must be rechecked before provisioning. [Official pricing update](https://cloud.google.com/blog/products/ai-machine-learning/new-enhanced-tool-governance-in-vertex-ai-agent-builder/).

Allow a provisional **USD 3–10** for builds/images, Cloud Run, Firestore, storage, Scheduler, secrets, logs and network in a small pilot. This allowance is an engineering estimate, not a quoted bundle. Expected small-pilot total is roughly **USD 8–15**, with USD 25 proposed as an initial stop-and-review envelope. Sustained traffic or idle allocations can exceed it. [Cloud Run prices](https://cloud.google.com/run/pricing).

The gateway has configurable durable request allowances (8/min/user, 100/day/user, 300/day total by default); ADK permits at most 8 model turns/run and 3,000 output tokens/turn. These request limits do not directly guarantee a dollar cap. Before judging, set allowances to the approved measured envelope and reserve capacity; do not silently exhaust it with development loops. Check Billing after the first pilot and before increasing usage. Budget alerts are not an immediate spend stop; no unlimited commitment is implied.

No paid GCP calls, resources, plan upgrades, billing attachment or payment have been executed in this build session.
