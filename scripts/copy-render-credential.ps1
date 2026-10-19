param(
    [Parameter(Mandatory=$true)]
    [ValidateSet('TokenEncryptionKey','GitHubToken','ClearClipboard')]
    [string]$Name
)
# Owner-invoked recovery helper. Never prints a secret or controls a browser.
. "$PSScriptRoot/env.ps1"
if($Name -eq 'ClearClipboard') {
    # Windows PowerShell 5.1 rejects an empty string in Set-Clipboard.
    Set-Clipboard -Value '[RELAY clipboard cleared]'
    Write-Output 'Clipboard overwritten with a non-secret placeholder.'
    exit
}
$RelayCredentialFile=if($Name -eq 'TokenEncryptionKey') {'calendar-token-key.dpapi'} else {'github-read.dpapi'}
$RelayCredentialPath=Join-Path $RelayLocal ('private/'+$RelayCredentialFile)
$RelaySecureValue=ConvertTo-SecureString (Get-Content -LiteralPath $RelayCredentialPath -Raw).Trim()
$RelayCredentialPointer=[Runtime.InteropServices.Marshal]::SecureStringToBSTR($RelaySecureValue)
try {
    $RelayValue=[Runtime.InteropServices.Marshal]::PtrToStringBSTR($RelayCredentialPointer)
    if($Name -eq 'TokenEncryptionKey' -and $RelayValue -notmatch '^[A-Za-z0-9_-]{43}=$') {throw 'The protected original is not a Fernet key. No clipboard change.'}
    if($Name -eq 'GitHubToken' -and !$RelayValue.StartsWith('github_pat_')) {throw 'The protected original is not a fine-grained GitHub credential. No clipboard change.'}
    Set-Clipboard -Value $RelayValue
    $RelayTarget=if($Name -eq 'TokenEncryptionKey') {'RELAY_TOKEN_ENCRYPTION_KEY'} else {'RELAY_GITHUB_TOKEN'}
    Write-Output ('Copied protected original for '+$RelayTarget+'. Paste only into that Render Value, then Save only. No value was printed.')
} finally {
    $RelayValue=$null
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($RelayCredentialPointer)
    $RelaySecureValue.Dispose()
}
