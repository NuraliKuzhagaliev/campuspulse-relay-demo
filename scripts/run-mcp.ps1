. "$PSScriptRoot/env.ps1"
Set-Location $RelayRoot
& '.venv/Scripts/python.exe' -m uvicorn relay.mcp_server:app --host 127.0.0.1 --port 8001 --no-access-log
