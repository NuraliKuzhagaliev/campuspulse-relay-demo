. "$PSScriptRoot/env.ps1"
Set-Location $RelayRoot
if (!(Test-Path '.venv/Scripts/python.exe')) { python -m venv .venv }
& '.venv/Scripts/python.exe' -m pip install -r requirements.lock.txt
if ($LASTEXITCODE) { throw 'Python dependency installation failed.' }
npm.cmd ci --no-audit --no-fund
if ($LASTEXITCODE) { throw 'Node dependency installation failed.' }
npm.cmd run build
if ($LASTEXITCODE) { throw 'Web build failed.' }
