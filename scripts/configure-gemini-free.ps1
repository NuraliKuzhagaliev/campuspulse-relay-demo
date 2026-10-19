param([Parameter(Mandatory=$true)][switch]$ConfirmFreeTierOnly)
. "$PSScriptRoot/env.ps1"
if (!$ConfirmFreeTierOnly) { throw 'Confirm this key belongs to an eligible free-tier project with no paid upgrade or prepayment.' }
$RelayPrivate=Join-Path $RelayLocal 'private'
New-Item -ItemType Directory -Force -Path $RelayPrivate | Out-Null
$RelayGeminiKey=Read-Host 'Paste the Gemini Developer API key here (hidden, never in chat)' -AsSecureString
if ($RelayGeminiKey.Length -lt 20) { throw 'Key is missing or too short. Nothing was saved.' }
# Windows DPAPI encrypts this credential for the current Windows user.
$RelayEncrypted=ConvertFrom-SecureString -SecureString $RelayGeminiKey
$RelayEncrypted | Set-Content -LiteralPath (Join-Path $RelayPrivate 'gemini-key.dpapi') -Encoding UTF8 -NoNewline
Write-Output 'Credential encrypted for this Windows user on D:. No API call, billing change or paid upgrade was made. Account tier, quota and a real tool smoke still require verification.'
