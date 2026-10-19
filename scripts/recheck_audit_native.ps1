. "$PSScriptRoot/env.ps1"
Set-Location -LiteralPath $RelayRoot
$RelayAuditNative=Join-Path $RelayLocal 'native-verification/0.5.0-audit'
New-Item -ItemType Directory -Force -Path $RelayAuditNative | Out-Null
foreach($RelaySamplePair in @(@('public/samples/01-original.md','native-audit-0.5.0.md'),@('public/samples/09-workspace.relay.json','native-audit-0.5.0.relay.json'))){
 $RelayAuditTarget=Join-Path $RelayAuditNative $RelaySamplePair[1]
 if(!(Test-Path -LiteralPath $RelayAuditTarget)){Copy-Item -LiteralPath (Join-Path $RelayRoot $RelaySamplePair[0]) -Destination $RelayAuditTarget}
}
$env:RELAY_DESKTOP_DATA=Join-Path $RelayAuditNative 'profile'
$env:RELAY_GATEWAY_URL='https://campuspulse-relay-demo.onrender.com'
Start-Process -FilePath (Join-Path $RelayRoot 'installed/CampusPulse RELAY/CampusPulse RELAY.exe') -ArgumentList '--force-renderer-accessibility' -WorkingDirectory $RelayRoot -WindowStyle Normal
Write-Output ('Native verification workspace: '+$RelayAuditNative)
Write-Output 'The normal Windows Open/Save dialogs and notifications are unchanged. The accessibility launch flag exposes controls to the approved UI helper.'
Write-Output 'Actual visibility, successful import, Save/reimport and notification click/focus must be recorded separately.'
