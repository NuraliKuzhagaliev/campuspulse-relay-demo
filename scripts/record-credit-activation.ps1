param(
    [Parameter(Mandatory=$true)][string]$ProjectId,
    [Parameter(Mandatory=$true)][string]$BillingAccountId,
    [Parameter(Mandatory=$true)][decimal]$ConfirmedBalanceUsd,
    [Parameter(Mandatory=$true)][datetime]$CreditExpiresAt,
    [Parameter(Mandatory=$true)][switch]$ConfirmOrganizerEligibility
)
. "$PSScriptRoot/env.ps1"
if (!$ConfirmOrganizerEligibility -or $ConfirmedBalanceUsd -le 0 -or $CreditExpiresAt.ToUniversalTime() -le [datetime]::UtcNow) {
    throw 'Confirm organizer eligibility, a positive actual balance, and a future expiration from the activation instructions. Credits are not inferred.'
}
$RelayGcloud=Join-Path $RelayLocal 'tools/google-cloud-sdk/bin/gcloud.cmd'
$RelayFunding=& $RelayGcloud billing projects describe $ProjectId --format=json | ConvertFrom-Json
if ($LASTEXITCODE -or !$RelayFunding.billingEnabled) { throw 'Existing project billing is not active. No billing account was attached or payment made.' }
$RelayBillingName='billingAccounts/'+$BillingAccountId.Replace('billingAccounts/','')
if ($RelayFunding.billingAccountName -ne $RelayBillingName) { throw 'Actual project billing differs from the organizer-approved billing account. Stop and inspect eligibility.' }
$RelayBilling=& $RelayGcloud billing accounts describe $RelayBillingName --format=json | ConvertFrom-Json
if ($LASTEXITCODE -or !$RelayBilling.open) { throw 'The approved billing account is not accessible/open.' }
@{
    source='organizer-credits';project_id=$ProjectId;billing_account=$RelayBillingName
    balance_usd_human_confirmed=$ConfirmedBalanceUsd
    expires_at_utc=$CreditExpiresAt.ToUniversalTime().ToString('o')
    eligibility_human_confirmed=$true;checked_at_utc=[datetime]::UtcNow.ToString('o')
    credit_balance_api_verified=$false;personal_spending_authorized=$false
} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $RelayLocal 'credit-activation.json')
Write-Output 'Read-only billing/project checks complete. Human-confirmed credit metadata saved on D:. No resources were provisioned. This is not authorization to spend or an API-verified credit balance.'
