. "$PSScriptRoot/env.ps1"
$RelayReadToken=Read-Host 'Dedicated fine-grained GitHub token (hidden; never paste in chat)' -AsSecureString
$RelayReadPointer=[Runtime.InteropServices.Marshal]::SecureStringToBSTR($RelayReadToken)
try {
    $RelayReadValue=[Runtime.InteropServices.Marshal]::PtrToStringBSTR($RelayReadPointer)
    if(!$RelayReadValue.StartsWith('github_pat_') -or $RelayReadValue.Length -lt 50){throw 'Use a dedicated fine-grained read-only token, not a classic or account-wide token.'}
} finally {
    $RelayReadValue=$null
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($RelayReadPointer)
}
$RelayReadDestination=Join-Path $RelayLocal 'private/github-read.dpapi'
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $RelayReadDestination) | Out-Null
ConvertFrom-SecureString $RelayReadToken | Set-Content -LiteralPath $RelayReadDestination -Encoding UTF8 -NoNewline
$RelayReadToken.Dispose()
Write-Output 'Dedicated read credential saved with current-user DPAPI on D:. No credential was printed, uploaded or used. Verify repository/permissions before server configuration.'
