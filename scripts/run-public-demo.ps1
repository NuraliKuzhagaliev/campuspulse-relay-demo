param([int]$Port = 8010)
. "$PSScriptRoot/env.ps1"
Set-Location $RelayRoot
# Clear only this child process's live-connection settings. Never edit the user's
# saved environment or the working local/desktop configuration.
foreach ($RelayPublicKey in @('RELAY_AGENT_RESOURCE','GOOGLE_CLOUD_PROJECT','RELAY_OAUTH_CLIENT_ID','RELAY_OAUTH_CLIENT_SECRET','RELAY_TOKEN_ENCRYPTION_KEY','RELAY_MCP_URL')) {
    [Environment]::SetEnvironmentVariable($RelayPublicKey, $null, 'Process')
}
$env:RELAY_MODE = 'public_demo'
$env:RELAY_GATEWAY_URL = "http://127.0.0.1:$Port"
$env:RELAY_DATA_DIR = Join-Path $RelayLocal 'public-mode-test'
& '.local/public-venv/Scripts/python.exe' -m uvicorn relay.gateway:app --host 127.0.0.1 --port $Port --workers 1 --no-access-log
