param(
    [Parameter(Mandatory=$true)][string]$ProjectId,
    [Parameter(Mandatory=$true)][string]$BillingAccountId,
    [Parameter(Mandatory=$true)][decimal]$ConfirmedBalanceUsd,
    [Parameter(Mandatory=$true)][datetimeoffset]$CreditExpiresAt,
    [Parameter(Mandatory=$true)][switch]$ConfirmNonBillableFreeTrial,
    [Parameter(Mandatory=$true)][switch]$ConfirmEligibilityAndCoveredServices,
    [Parameter(Mandatory=$true)][switch]$ConfirmNoPersonalSpending,
    [decimal]$ReserveUsd=0
)
. "$PSScriptRoot/env.ps1"
if (!$ConfirmNonBillableFreeTrial -or !$ConfirmEligibilityAndCoveredServices -or !$ConfirmNoPersonalSpending -or $ConfirmedBalanceUsd -le 0 -or $ReserveUsd -lt 0 -or $CreditExpiresAt -le [datetimeoffset]::UtcNow) {
    throw 'Record only an actual eligible non-billable Free Trial with confirmed coverage, balance and expiry. No payment, upgrade or personal spending is authorized.'
}
$RelayGcloud=Join-Path $RelayLocal 'tools/google-cloud-sdk/bin/gcloud.cmd'
$RelayProjectBilling=& $RelayGcloud billing projects describe $ProjectId --format=json | ConvertFrom-Json
if ($LASTEXITCODE -or !$RelayProjectBilling.billingEnabled) { throw 'Project billing is not active. This script does not attach billing or activate/pay for an account.' }
$RelayBillingName='billingAccounts/'+$BillingAccountId.Replace('billingAccounts/','')
if ($RelayProjectBilling.billingAccountName -ne $RelayBillingName) { throw 'Actual project billing differs from the reviewed account.' }
$RelayBilling=& $RelayGcloud billing accounts describe $RelayBillingName --format=json | ConvertFrom-Json
if ($LASTEXITCODE -or !$RelayBilling.open) { throw 'The reviewed account is not accessible/open.' }
@{
    schema_version=1;source='gcp-free-trial';project_id=$ProjectId;billing_account=$RelayBillingName
    account_type_human_confirmed='free_trial';balance_usd_human_confirmed=$ConfirmedBalanceUsd;reserve_usd=$ReserveUsd
    expires_at_utc=$CreditExpiresAt.ToUniversalTime().ToString('o');checked_at_utc=[datetimeoffset]::UtcNow.ToString('o')
    eligibility_human_confirmed=$true;covered_services_human_confirmed=$true
    billing_open_api_verified=$true;credit_balance_api_verified=$false;no_personal_spending=$true
} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $RelayLocal 'funding-verification.json') -Encoding UTF8
Write-Output 'Read-only project/account checks and distinct owner trial attestations saved on D:. No spend approval, billing change or resource creation was performed.'
