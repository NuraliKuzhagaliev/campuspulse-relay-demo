param([Parameter(Mandatory=$true)][string]$ProjectId)
. "$PSScriptRoot/env.ps1"
$RelayGcloud = Join-Path $RelayRoot '.local/tools/google-cloud-sdk/bin/gcloud.cmd'
if (!(Test-Path $RelayGcloud)) { throw 'Run scripts/bootstrap-gcloud.ps1 first.' }
& $RelayGcloud auth login
if ($LASTEXITCODE) { throw 'Google Cloud account login failed.' }
& $RelayGcloud config set project $ProjectId
& $RelayGcloud auth application-default login --scopes=https://www.googleapis.com/auth/cloud-platform,https://www.googleapis.com/auth/calendar.events,https://www.googleapis.com/auth/calendar.calendarlist.readonly
if ($LASTEXITCODE) { throw 'ADC consent failed. Calendar scopes may require an approved OAuth client.' }
& $RelayGcloud auth application-default set-quota-project $ProjectId
Write-Output 'Authentication stored on D:. Set GOOGLE_CLOUD_PROJECT in .env; then run scripts/preflight.py. No resources were provisioned.'
