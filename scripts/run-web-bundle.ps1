$ErrorActionPreference='Stop'
$RelayBundleRoot=Split-Path -Parent $PSScriptRoot
if($RelayBundleRoot -notmatch '^[dD]:[\\/]'){throw 'Extract the web bundle on D: before running it.'}
Set-Location -LiteralPath $RelayBundleRoot
foreach($RelayPart in @('.local/tmp','.local/cache/pip','.local/cache/pycache','.local/data')){New-Item -ItemType Directory -Force -Path $RelayPart | Out-Null}
$env:TEMP=Join-Path $RelayBundleRoot '.local/tmp';$env:TMP=$env:TEMP;$env:TMPDIR=$env:TEMP
$env:PIP_CACHE_DIR=Join-Path $RelayBundleRoot '.local/cache/pip'
$env:PYTHONPYCACHEPREFIX=Join-Path $RelayBundleRoot '.local/cache/pycache'
$env:PYTHONUTF8='1';$env:PYTHONIOENCODING='utf-8'
$env:RELAY_DATA_DIR=Join-Path $RelayBundleRoot '.local/data'
$env:RELAY_MODE='local'
if(!(Test-Path -LiteralPath '.local/web-venv/Scripts/python.exe')){python -m venv .local/web-venv;if($LASTEXITCODE){throw 'Could not create the D: Python environment.'}}
& .local/web-venv/Scripts/python.exe -m pip install -r requirements.public.lock.txt
if($LASTEXITCODE){throw 'Minimal web dependencies could not be installed.'}
& .local/web-venv/Scripts/python.exe -m uvicorn relay.gateway:app --host 127.0.0.1 --port 8000
