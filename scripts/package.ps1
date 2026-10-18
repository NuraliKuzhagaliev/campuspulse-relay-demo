. "$PSScriptRoot/env.ps1"
Set-Location $RelayRoot
npm.cmd run package:win
if ($LASTEXITCODE) { throw 'Windows packaging failed.' }
Get-ChildItem 'release/windows' -File | Get-FileHash -Algorithm SHA256 | Select-Object Path,Hash | ConvertTo-Json | Set-Content 'release/windows/SHA256.json'
