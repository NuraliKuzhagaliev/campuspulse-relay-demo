param([ValidateRange(1024,65535)][int]$Port=8016)
. "$PSScriptRoot/gemini-env.ps1"
Set-Location $RelayRoot
if (!$env:RELAY_GEMINI_API_KEY -or $env:RELAY_GEMINI_FREE_ONLY -ne 'true') { throw 'Run configure-gemini-free.ps1 with an eligible free-tier key first. No paid fallback is enabled.' }
$env:RELAY_MODE='alternative_live'
$env:RELAY_INFERENCE_PROVIDER='gemini_developer'
$env:GOOGLE_GENAI_USE_VERTEXAI='false'
$env:RELAY_DEPLOYMENT_MODE='alternative_hosted'
$env:RELAY_MCP_URL="http://127.0.0.1:$Port/_relay/mcp/"
$RelayTransportPath=Join-Path $RelayLocal 'private/mcp-service-secret'
if (!(Test-Path $RelayTransportPath)) { .\.venv\Scripts\python.exe -c "import secrets,pathlib;pathlib.Path('.local/private/mcp-service-secret').write_text(secrets.token_hex(32))" }
$env:RELAY_MCP_SERVICE_SECRET=Get-Content -LiteralPath $RelayTransportPath -Raw
$env:RELAY_DATA_DIR=Join-Path $RelayLocal 'final-integration/alternative-data'
$env:RELAY_GITHUB_REPO='NuraliKuzhagaliev/campuspulse-relay-demo'
$env:RELAY_GATEWAY_URL="https://localhost:$Port"
Write-Output 'Prepared alternative route uses private invitations and consent. Local HTTPS/browser staging must be configured before browser acceptance; HTTP loopback is for protocol smoke only.'
.\.venv\Scripts\python.exe -m uvicorn relay.gateway:app --host 127.0.0.1 --port $Port --no-access-log
