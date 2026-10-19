param([switch]$Login)
. "$PSScriptRoot/env.ps1"
$RelayGcloud = Join-Path $RelayLocal 'tools/google-cloud-sdk/bin/gcloud.cmd'
if ($Login) { & $RelayGcloud auth login }
$RelayAccounts=& $RelayGcloud auth list --format=json | ConvertFrom-Json
if ($LASTEXITCODE -or !$RelayAccounts) {
    Write-Output 'No D: gcloud account is authenticated. Browser and Calendar connector sessions do not authenticate CLI/ADC. No resources were provisioned.'
    exit 1
}
$RelayAccounts | Select-Object account,status | Format-Table
& $RelayGcloud projects list --format='table(projectId,name,lifecycleState)'
& $RelayGcloud billing accounts list --format='table(name,displayName,open)'
Write-Output 'This script only reads account/project/billing metadata. Promotional credits must also be checked in Cloud Console > Billing > Credits. No cloud resources are provisioned.'
