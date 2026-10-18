# Deployment proof: required gate not met

**No actual Vertex AI Agent Engine / reasoningEngines deployment has been verified. No public web URL or successful local/remote Gemini call is claimed.** Localhost, the Electron package, a repository link, the Cloud Console page and live GitHub calls are not substitutes for that gate.

Read-only inspection on 19 October 2026 (Asia/Qyzylorda): portable Google Cloud CLI 589.0.0 is under `.local/tools` on D:. `gcloud auth list` returned no accounts; project listing failed because no account was active. ADC preflight returned DefaultCredentialsError. No billable resources were provisioned.

The already signed-in browser account exposed two projects: `gen-lang-client-0595303951` (Default Gemini Project) and `algebraic-scholar-bjq9c`. Neither is a dedicated CampusPulse project. The linked billing page showed: “Your free trial requires a prepayment.” No payment, new billing attachment or credit balance was assumed. Credit availability remains unconfirmed.

SDK compatibility checked locally: google-cloud-aiplatform 2.5.0, google-adk 2.12.0, google-genai 2.31.0, MCP 1.30.0, FastAPI 0.135.1 and OR-Tools 9.15.6755. Imports, toolset header-provider signature, RunConfig and AgentEngineConfig fields were checked; `pip check` passed. `vertexai.Client` emits a migration warning toward `agentplatform.Client`; the current documented compatibility route is retained consistently. Actual managed deployment compatibility remains unverified.

The official brief's legacy `ReasoningEngine.create` is mapped to the documented `client.agent_engines.create(agent=..., config=...)`, which creates a `reasoningEngines` resource. Inference uses ADK/Gen AI rather than removed generative Vertex modules. Candidate model `gemini-3.5-flash` appears in the official active model table and ADK quickstart; availability/quotas in the chosen project/region still require real smoke calls.

The release must acquire all of the following evidence before changing this status: actual resource/revision/time; successful bounded local and remote model calls; public web → authenticated gateway → that resource → genuine MCP → external observation; machine token renewal/restart; real Calendar approval/write/read-back; isolated judge session and unseen-file question. Store redacted proof under `docs/evidence/`. Never store tokens, authorization codes or raw private student documents there.

Primary references: [Google managed ADK quickstart](https://docs.cloud.google.com/gemini-enterprise-agent-platform/build/runtime/quickstart-adk), [model lifecycle](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/learn/model-versions), [MCP deployment](https://adk.dev/tools-custom/mcp-tools/deployment/).
