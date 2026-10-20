# Owner-invoked interactive check only. Never started by the agent after Escape.
. "$PSScriptRoot/env.ps1"
$RelayInstalledExecutable=Join-Path $RelayRoot 'installed/CampusPulse RELAY/CampusPulse RELAY.exe'
if (!(Test-Path -LiteralPath $RelayInstalledExecutable)) { throw 'Install the new package manually through release/windows/Install-D.cmd first.' }
if ((Get-Item -LiteralPath $RelayInstalledExecutable).VersionInfo.ProductVersion -notlike '0.5.1*') { throw 'Installed app is not 0.5.1. Install the new package manually first; old profiles are preserved.' }
$RelayVerificationDirectory=Join-Path $RelayRoot '.local/native-verification/0.5.1-owner-check'
New-Item -ItemType Directory -Force -Path $RelayVerificationDirectory | Out-Null
$env:RELAY_DESKTOP_DATA=Join-Path $RelayVerificationDirectory 'profile'
$env:RELAY_GATEWAY_URL='https://campuspulse-relay-demo.onrender.com'
Write-Output 'Separate D-drive verification profile. Original profiles are unchanged. Import public/samples/11-continued-brief.pdf; record 45 logged and 95 remaining separately, then test native Passport Save/import/reopen and notification click/focus. Google consent is not needed for these checks.'
Start-Process -FilePath $RelayInstalledExecutable -WorkingDirectory $RelayRoot -WindowStyle Normal
