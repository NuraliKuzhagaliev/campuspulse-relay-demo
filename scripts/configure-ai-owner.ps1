. "$PSScriptRoot/env.ps1"
$RelayPrivatePath=Join-Path $RelayLocal 'private/ai-owner-key.dpapi'
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $RelayPrivatePath) | Out-Null
if (!(Test-Path $RelayPrivatePath)) {
    $RelayPrivateRaw=& (Join-Path $RelayRoot '.venv/Scripts/python.exe') -c "import base64;from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey;print(base64.b64encode(Ed25519PrivateKey.generate().private_bytes_raw()).decode())"
    if ($LASTEXITCODE) { throw 'Owner key generation failed.' }
    $RelayPrivateSecure=ConvertTo-SecureString -String $RelayPrivateRaw.Trim() -AsPlainText -Force
    ConvertFrom-SecureString -SecureString $RelayPrivateSecure | Set-Content -LiteralPath $RelayPrivatePath -Encoding UTF8 -NoNewline
    $RelayPrivateRaw=$null
}
$RelayOwnerSecure=Get-Content -LiteralPath $RelayPrivatePath -Raw | ConvertTo-SecureString
$RelayOwnerPointer=[Runtime.InteropServices.Marshal]::SecureStringToBSTR($RelayOwnerSecure)
try {
    $RelayOwnerRaw=[Runtime.InteropServices.Marshal]::PtrToStringBSTR($RelayOwnerPointer)
    $RelayPublicKey=$RelayOwnerRaw | & (Join-Path $RelayRoot '.venv/Scripts/python.exe') -c "import sys,base64;from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey;k=Ed25519PrivateKey.from_private_bytes(base64.b64decode(sys.stdin.read().strip()));print(base64.b64encode(k.public_key().public_bytes_raw()).decode())"
    $RelayOwnerRaw=$null
} finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($RelayOwnerPointer) }
@{public_key=$RelayPublicKey.Trim();private_key_storage='Windows DPAPI on D:';scope='bounded AI-only invitations; no Calendar authority'} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $RelayLocal 'private/ai-owner-public.json') -Encoding UTF8
Write-Output 'Owner signing key is encrypted on D:. Public verification metadata is prepared; no invitation or external permission was created.'
