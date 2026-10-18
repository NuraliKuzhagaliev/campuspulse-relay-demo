# Decisions

- Topic 2 governs; Topic 1's YouTube and 5-7 minute conditions are excluded.
- Use Google ADK + Google Gen AI for inference, Vertex agent_engines.AdkApp + client.agent_engines.create for managed reasoningEngine deployment. Pin installed versions and test compatibility; no deprecated generative Vertex module.
- Use React/TypeScript/Vite and sandboxed Electron with a local renderer and narrow native bridge.
- Separate deterministic scheduling/approval operations from model interpretation. CP-SAT proves feasible allocation under validated constraints. Never move hard deadlines or manufacture missing dates.
- Local SQLite is explicitly a local development store. Cloud deployment requires Firestore and server-verified identity; production startup must fail closed if configuration is incomplete.
- Offline fixture workspace is openly illustrative. It cannot be counted as cloud or Calendar evidence.
