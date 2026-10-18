param([switch]$Login)
. "$PSScriptRoot/env.ps1"
$RelayGcloud = Join-Path $RelayLocal 'tools/google-cloud-sdk/bin/gcloud.cmd'
if ($Login) { & $RelayGcloud auth login }
& $RelayGcloud auth list --format='table(account,status)'
& $RelayGcloud projects list --format='table(projectId,name,lifecycleState)'
& $RelayGcloud billing accounts list --format='table(name,displayName,open)'
Write-Output 'This script only reads account/project/billing metadata. Promotional credits must also be checked in Cloud Console > Billing > Credits. No cloud resources are provisioned.'
