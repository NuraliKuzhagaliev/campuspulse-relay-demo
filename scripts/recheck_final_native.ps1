param([switch]$PublicGateway)
. "$PSScriptRoot/env.ps1"
Set-Location -LiteralPath $RelayRoot
$RelayNativeFinal=Join-Path $RelayLocal 'native-verification/0.4.1-final'
New-Item -ItemType Directory -Force -Path $RelayNativeFinal | Out-Null
$RelayNativePassport=Join-Path $RelayNativeFinal 'native-input.relay.json'
if (!(Test-Path -LiteralPath $RelayNativePassport)) { Copy-Item -LiteralPath (Join-Path $RelayRoot 'fixtures/workspace-passport-example.relay.json') -Destination $RelayNativePassport }
$RelayNativeDocument=Join-Path $RelayNativeFinal 'native-optics-0.4.1.md'
if (!(Test-Path -LiteralPath $RelayNativeDocument)) {
    @'
Assignment: Native optics verification 0.4.1
Course: Optics
Term: 2026 Autumn
Assignment ID: native-optics-041
Due: 2026-10-24T19:00:00+05:00
Effort: 30 minutes
- [ ] Explain the observed aberration
'@ | Set-Content -LiteralPath $RelayNativeDocument -Encoding UTF8
}
$env:RELAY_DESKTOP_DATA=Join-Path $RelayNativeFinal 'profile'
$env:RELAY_GATEWAY_URL=if ($PublicGateway) {'https://campuspulse-relay-demo.onrender.com'} else {'http://127.0.0.1:8000'}
Write-Output "Native verification gateway: $env:RELAY_GATEWAY_URL"
Write-Output "Passport file: $RelayNativePassport"
Write-Output "Academic file: $RelayNativeDocument"
Start-Process -FilePath (Join-Path $RelayRoot 'installed/CampusPulse RELAY/CampusPulse RELAY.exe') -WorkingDirectory $RelayRoot -WindowStyle Normal
