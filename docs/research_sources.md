# Sources and scope

All three supplied attachments were read completely: the master implementation specification, the 24-page research report and the 4-page official brief. They are preserved locally under `inputs/`; only Topic 2 governs. Topic 1's city data/POI/YouTube/5–7 minute conditions are excluded. The research is supporting rationale, not evidence that this implementation already existed.

Official technical references rechecked during implementation:

- [Managed ADK quickstart / reasoningEngines mapping](https://docs.cloud.google.com/gemini-enterprise-agent-platform/build/runtime/quickstart-adk)
- [Google model lifecycle](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/learn/model-versions)
- [Generative Vertex SDK migration](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/deprecations/genai-vertexai-sdk)
- [ADK MCP toolsets](https://adk.dev/tools-custom/mcp-tools/) and [deployment](https://adk.dev/tools-custom/mcp-tools/deployment/)
- [MCP tools specification](https://modelcontextprotocol.io/specification/2025-06-18/server/tools)
- [Calendar event creation](https://developers.google.com/workspace/calendar/api/guides/create-events) and [incremental synchronization](https://developers.google.com/workspace/calendar/api/guides/sync)
- [Electron security](https://www.electronjs.org/docs/latest/tutorial/security)
- [OR-Tools CP-SAT](https://developers.google.com/optimization/cp/cp_solver)
- [Official Playwright Electron testing](https://playwright.dev/docs/api/class-electron)
- [Google model prices](https://cloud.google.com/gemini-enterprise-agent-platform/generative-ai/pricing), [Agent Engine pricing update](https://cloud.google.com/blog/products/ai-machine-learning/new-enhanced-tool-governance-in-vertex-ai-agent-builder/) and [Cloud Run prices](https://cloud.google.com/run/pricing)

Primary package metadata was inspected for compatible ADK/FastAPI/telemetry/MCP pins. Official npm registry reports Electron 44.9.0, which is the packaged runtime. No competitor absence, world-first claim, fabricated interview or unsupported award/grade prediction is made.
