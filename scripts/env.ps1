$ErrorActionPreference = 'Stop'
$RelayRoot = Split-Path -Parent $PSScriptRoot
$RelayLocal = Join-Path $RelayRoot '.local'
foreach ($part in @('tmp','cache/pip','cache/npm','cache/uv','cache/electron','cache/electron-builder','cache/playwright','gcloud','data','logs','downloads','desktop')) {
    New-Item -ItemType Directory -Force -Path (Join-Path $RelayLocal $part) | Out-Null
}
$env:TEMP = Join-Path $RelayLocal 'tmp'
$env:TMP = $env:TEMP
$env:TMPDIR = $env:TEMP
$env:PIP_CACHE_DIR = Join-Path $RelayLocal 'cache/pip'
$env:npm_config_cache = Join-Path $RelayLocal 'cache/npm'
$env:UV_CACHE_DIR = Join-Path $RelayLocal 'cache/uv'
$env:ELECTRON_CACHE = Join-Path $RelayLocal 'cache/electron'
$env:ELECTRON_BUILDER_CACHE = Join-Path $RelayLocal 'cache/electron-builder'
$env:PLAYWRIGHT_BROWSERS_PATH = Join-Path $RelayLocal 'cache/playwright'
$env:CLOUDSDK_CONFIG = Join-Path $RelayLocal 'gcloud'
$env:CLOUDSDK_PYTHON = 'C:\Users\nural\AppData\Local\Programs\Python\Python313\python.exe'
$env:PYTHONPYCACHEPREFIX = Join-Path $RelayLocal 'cache/pycache'
$env:RELAY_DATA_DIR = Join-Path $RelayLocal 'data'
$env:RELAY_DESKTOP_DATA = Join-Path $RelayLocal 'desktop'
$env:HF_HOME = Join-Path $RelayLocal 'cache/huggingface'
$env:XDG_CACHE_HOME = Join-Path $RelayLocal 'cache'
$env:GOOGLE_APPLICATION_CREDENTIALS = Join-Path $RelayLocal 'gcloud/application_default_credentials.json'
if (Test-Path (Join-Path $RelayRoot '.env')) {
    foreach ($line in Get-Content -LiteralPath (Join-Path $RelayRoot '.env')) {
        if ($line -match '^([A-Z][A-Z0-9_]*)=(.*)$') {
            [Environment]::SetEnvironmentVariable($Matches[1], $Matches[2].Trim('"').Trim("'"), 'Process')
        }
    }
}
if (!$env:RELAY_CONTEXT_SECRET -and $env:RELAY_MODE -ne 'cloud') {
    $RelaySecretFile = Join-Path $RelayLocal 'context-secret'
    if (!(Test-Path $RelaySecretFile)) {
        [Convert]::ToHexString([Security.Cryptography.RandomNumberGenerator]::GetBytes(32)) | Set-Content -LiteralPath $RelaySecretFile -NoNewline
    }
    $env:RELAY_CONTEXT_SECRET = Get-Content -LiteralPath $RelaySecretFile -Raw
}
