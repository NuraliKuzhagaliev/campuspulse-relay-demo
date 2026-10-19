# Server-only credential loading. Do not source this from frontend/desktop builds.
. "$PSScriptRoot/env.ps1"
$RelayGeminiPrivate=Join-Path $RelayLocal 'private/gemini-key.dpapi'
if (!(Test-Path -LiteralPath $RelayGeminiPrivate)) { throw 'Configure the owner-authorized free-tier Gemini credential first; no paid fallback is enabled.' }
$RelayGeminiSecure=Get-Content -LiteralPath $RelayGeminiPrivate -Raw | ConvertTo-SecureString
$RelayGeminiPointer=[Runtime.InteropServices.Marshal]::SecureStringToBSTR($RelayGeminiSecure)
try { $env:RELAY_GEMINI_API_KEY=[Runtime.InteropServices.Marshal]::PtrToStringBSTR($RelayGeminiPointer) }
finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($RelayGeminiPointer) }
$env:RELAY_GEMINI_FREE_ONLY='true'
