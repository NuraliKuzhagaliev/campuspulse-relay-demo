# Server only. Never load into renderer/desktop builds or print credential values.
foreach ($RelayCalendarEntry in @(@('RELAY_OAUTH_CLIENT_ID','calendar-client.dpapi'),@('RELAY_OAUTH_CLIENT_SECRET','calendar-secret.dpapi'),@('RELAY_TOKEN_ENCRYPTION_KEY','calendar-token-key.dpapi'))) {
    $RelayCalendarPath=Join-Path $RelayLocal ('private/'+$RelayCalendarEntry[1])
    if (!(Test-Path -LiteralPath $RelayCalendarPath)) { continue }
    $RelayCalendarSecure=Get-Content -LiteralPath $RelayCalendarPath -Raw | ConvertTo-SecureString
    $RelayCalendarPointer=[Runtime.InteropServices.Marshal]::SecureStringToBSTR($RelayCalendarSecure)
    try { [Environment]::SetEnvironmentVariable($RelayCalendarEntry[0],[Runtime.InteropServices.Marshal]::PtrToStringBSTR($RelayCalendarPointer),'Process') }
    finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($RelayCalendarPointer) }
}
