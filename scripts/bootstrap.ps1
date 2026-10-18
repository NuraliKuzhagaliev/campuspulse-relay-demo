. "$PSScriptRoot/env.ps1"
Set-Location $RelayRoot
if (!(Test-Path '.venv/Scripts/python.exe')) { python -m venv .venv }
& '.venv/Scripts/python.exe' -m pip install -r requirements.lock.txt
npm.cmd ci --no-audit --no-fund
npm.cmd run build
