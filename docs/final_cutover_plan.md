# Reviewable existing-service cutover

No new Render infrastructure is authorized or needed. Use the already authorized workspace `tea-d3pt0sbipnbc73a5v810`, existing service `srv-dbajs73bc2fs73bm9mfg`, Free Docker Frankfurt, one instance, auto-deploy **off**. Preserve the previous live deployment `dep-dbal14m1egvs73b4fp8g`, source `83552161ec22c7cf44746433425d3b2b99e042c4`, Dockerfile `infra/Dockerfile.public`, branch `main` as the rollback reference. Prior local and sealed release archives are unchanged.

Prepared source branch: `local/final-integration-0.4.0`. Before triggering, record its exact clean pushed commit. Target Dockerfile: `infra/Dockerfile.alternative`, context repository root, health path `/api/health`. The image builds the frontend and actual Python ADK/MCP backend. It does not point the hosted frontend at localhost. Internal loopback MCP is inside that same container and is not a client URL.

The owner must put the eligible free-tier Gemini key in the **existing service's private environment** as `RELAY_GEMINI_API_KEY`, then choose **Save only**. The exact empty row was prepared in the authenticated Render Dashboard. Do not copy a key into chat, a tool output, frontend source, screenshot or invitation. Keep current live deployment until the key is saved and all local reviewable checks/artifacts are ready.

Merge these non-secret variables without replacing other secrets:

```text
RELAY_MODE=alternative_live
RELAY_INFERENCE_PROVIDER=gemini_developer
RELAY_DEPLOYMENT_MODE=alternative_hosted
GOOGLE_GENAI_USE_VERTEXAI=false
RELAY_GEMINI_DEVELOPER_MODEL=gemini-3.5-flash-lite
RELAY_GEMINI_FREE_ONLY=true
RELAY_GITHUB_REPO=NuraliKuzhagaliev/campuspulse-relay-demo
RELAY_GATE_REPOS=pallets/flask
RELAY_JUDGE_ENABLED=true
RELAY_AI_ADMIN_PUBLIC_KEY=UPbLEObv9w0mCyy+3hNR5q68vLx6vqqeSc3LrnuF3w8=
RELAY_MODEL_CALLS_PER_MINUTE=13
RELAY_MODEL_TOKENS_PER_MINUTE=240000
```

`RENDER_EXTERNAL_URL`, commit and port are supplied by Render. The entrypoint generates distinct ephemeral internal context/service keys, binds `0.0.0.0:$PORT`, and starts one worker. Do not set Google Vertex flags, a managed resource ID, real Calendar permission, a local development certificate or a paid tier.

After deployment, verify actual deployID/commit, valid public TLS, health/version, no frontend localhost dependency, fresh anonymous and private sessions, two documents/isolation, actual Gemini/MCP/GitHub query, languages/mobile, illustrative plan/receipt and installed Windows HTTPS query. Record provider/model/runtime/gateway revision and sample latency. Leave0.4 marked pending until these actually pass. A successful Docker build or model metadata request alone is insufficient.

If deployment fails or exceeds included free capacity, preserve evidence and restore the previous settings/deployment without a paid upgrade. No automatic deletion, unrelated resource cleanup or calendar clearing is authorized. Cloud Free Trial remains separately blocked by prepayment and the original managed criterion remains UNMET/EXCEPTION_PENDING.
