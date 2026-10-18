. "$PSScriptRoot/env.ps1"
Set-Location $RelayRoot
if (!(Test-Path '.venv/Scripts/python.exe')) { throw 'Run scripts/bootstrap.ps1 first.' }
if (!(Test-Path 'dist/index.html')) { npm.cmd run build; if ($LASTEXITCODE) { throw 'Web build failed.' } }
& '.venv/Scripts/python.exe' -m uvicorn relay.gateway:app --host 127.0.0.1 --port 8000 --no-access-log
