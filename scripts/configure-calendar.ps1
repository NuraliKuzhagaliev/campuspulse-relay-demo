. "$PSScriptRoot/env.ps1"
$RelayPrivate=Join-Path $RelayLocal 'private'
New-Item -ItemType Directory -Force -Path $RelayPrivate | Out-Null
$RelayCalendarClient=Read-Host 'OAuth WEB client ID (not an API key)' -AsSecureString
$RelayCalendarSecret=Read-Host 'OAuth WEB client secret (hidden; never paste in chat)' -AsSecureString
if ($RelayCalendarClient.Length -lt 20 -or $RelayCalendarSecret.Length -lt 10) { throw 'Incomplete OAuth client. Nothing was saved.' }
foreach ($RelayEntry in @(@('calendar-client.dpapi',$RelayCalendarClient),@('calendar-secret.dpapi',$RelayCalendarSecret))) {
    ConvertFrom-SecureString $RelayEntry[1] | Set-Content -LiteralPath (Join-Path $RelayPrivate $RelayEntry[0]) -Encoding UTF8 -NoNewline
}
$RelayTokenKeyPath=Join-Path $RelayPrivate 'calendar-token-key.dpapi'
if (!(Test-Path -LiteralPath $RelayTokenKeyPath)) {
    $RelayTokenKey=& (Join-Path $RelayRoot '.venv/Scripts/python.exe') -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'
    if ($LASTEXITCODE) { throw 'Could not generate the local token encryption key.' }
    ConvertFrom-SecureString (ConvertTo-SecureString $RelayTokenKey -AsPlainText -Force) | Set-Content -LiteralPath $RelayTokenKeyPath -Encoding UTF8 -NoNewline
    $RelayTokenKey=$null
}
Write-Output 'OAuth client and token key saved with current-user Windows DPAPI on D:. No Google request, consent, Calendar creation or external write occurred.'
