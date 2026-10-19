. "$PSScriptRoot/env.ps1"
$RelayNativeRoot=Join-Path $RelayRoot '.local/native-verification/0.3.0-passport'
New-Item -ItemType Directory -Force -Path $RelayNativeRoot | Out-Null
$RelayNativeInput=Join-Path $RelayNativeRoot 'native-input.relay.json'
if(!(Test-Path -LiteralPath $RelayNativeInput)) {
    Copy-Item -LiteralPath (Join-Path $RelayRoot 'fixtures/workspace-passport-example.relay.json') -Destination $RelayNativeInput
}
$env:RELAY_DESKTOP_DATA=Join-Path $RelayNativeRoot 'profile'
$env:RELAY_GATEWAY_URL='http://127.0.0.1:8000'
Start-Process -FilePath (Join-Path $RelayRoot 'installed/CampusPulse RELAY/CampusPulse RELAY.exe') -WorkingDirectory $RelayRoot
