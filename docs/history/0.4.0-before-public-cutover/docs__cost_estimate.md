# Final phase: zero personal spending

Organizer credits are not supplied. The prior USD8-15 / USD25 pilot proposal is superseded and was never approved. The actual GCP trial requires prepayment and has no issued credit entries; therefore no GCP resource is provisioned and no GCP spend envelope is authorized. Trial-credit advertisements do not fund Gemini Developer API usage.

## Selected free contingency

Account: owner-confirmed Gemini Developer API Free tier, project `gen-lang-client-0595303951`. Selected model: `gemini-3.5-flash-lite`; exact API metadata version `3.5-flash-lite-07-2026`. Standard unpaid input/output are free under the current offering; no paid model fallback, search grounding, caching purchase or batch job is enabled. The owner must not activate billing/prepay. [Official model prices](https://ai.google.dev/gemini-api/docs/pricing).

Actual account quota table:15RPM,250,000TPM,500RPD. The historical peak chart is not remaining quota. Other project users can consume it. Default application controls count **each model call**, not only frontend turns:13 model calls/minute,240,000 conservatively reserved tokens/minute,300/day aggregate,100/day/workspace,100/day reserved within that total for judges. A run has at most8 model calls,3,000 output tokens/call and85seconds runtime; gateway waiting90seconds. Retries are not hidden. Provider429 stops the run and establishes backoff. Conservative UTF-8 request-byte reservations include schema/output headroom; actual input/output/thinking/total usage is separately recorded. These counters persist in the current store; the temporary free host may reset them. Google's actual free quota still applies; remaining judge capacity must be checked near judging.

Measured first local real smoke:3 model calls,6,357 input tokens,130 output tokens,0 reported thinking tokens;6,487 total. Agent duration19.019seconds,one sample, not a latency guarantee. Public GitHub reads were real; Calendar was not called. This is not an invoice.

| Scenario | Model allowance | Funding consequence |
|---|---|---|
| Focused integration testing | About30 model calls; actual tool turns/context vary | Free quota only; stop on limits |
| Initial judge reserve |100 model calls, shared by private adult evaluators | Free quota only; verify remaining project capacity before invitations |
| Higher application usage | Up to300 model calls/day; hypothetical25k input +3k output/call =7.5M input +0.9M output | Unpaid quota only. At published paid rates this would be aboutUSD4.50 model-only; paid usage is prohibited and never selected |

Render workspace is Hobby with **no card on file**, USD0 unbilled/projected at inspection. Included usage:28.28/750 instance-hours,23/500 pipeline minutes,54MB/5GB bandwidth. Select only Free compute, one worker, no paid disk/database/cron/upgrade. A short free staging service plus the retained illustrative fallback fit current included hours; verify actual usage again before scaling tests. No installed binaries are served through Render bandwidth. [Free service behavior](https://render.com/docs/free).

Free hosting can sleep after15minutes and lose local files/state on spin-down/restart/deploy; it has no always-running Scheduler guarantee. It may suspend on free-quota exhaustion. No card/prepayment is added to remove limits. The serving process uses a private authenticated internal MCP transport; no second paid compute service is required.

## Managed path, if real eligible trial access later exists

Before selecting RouteA, recalculate current regional Vertex model/context/output/thinking, Agent Runtime vCPU/RAM, two Cloud Run services, Firestore reads/writes/storage, bucket/build/image/secret/Scheduler/log/network SKUs from current official prices and actual remaining free allowances. No funded project/region/quotas exist now, so no invented all-inclusive price is presented as approved. The existing plan uses min0/bounded max instances; these are not dollar caps. [Agent Platform pricing](https://cloud.google.com/gemini-enterprise-agent-platform/generative-ai/pricing), [Cloud Run pricing](https://cloud.google.com/run/pricing).

Current service-specific spend caps must be checked for the exact project/service and trial eligibility. Caps use monthly gross estimates before credits, may enforce late and allow in-flight/fixed/uncovered costs; ordinary budgets only alert. Neither authorizes personal spending or guarantees zero uncovered cost. Never lift/reset a cap automatically. [Spend cap limitations](https://docs.cloud.google.com/billing/docs/how-to/budgets-spend-caps).
