param([Parameter(Mandatory=$true)][string]$PlanPath,[switch]$Execute)
. "$PSScriptRoot/env.ps1"
Set-Location -LiteralPath $RelayRoot
$RelayPlanFile=[IO.Path]::GetFullPath($PlanPath)
if($RelayPlanFile -notmatch '^[dD]:[\\/]'){throw 'The actual organizer plan must remain on D:.'}
$RelayPlan=Get-Content -LiteralPath $RelayPlanFile -Raw | ConvertFrom-Json
if($RelayPlan.project -notmatch '^[a-z][a-z0-9-]{4,61}[a-z0-9]$' -or $RelayPlan.owned_prefix -notmatch '^[a-z][a-z0-9-]{4,26}$'){throw 'Invalid project or ownership prefix.'}
$RelayBridgePath=Join-Path $RelayLocal ('organizer/'+$RelayPlan.owned_prefix+'/bridge-ledger.json')
$RelayBridge=Get-Content -LiteralPath $RelayBridgePath -Raw | ConvertFrom-Json
if($RelayBridge.project -ne $RelayPlan.project -or $RelayBridge.service -ne ($RelayPlan.owned_prefix+'-bridge')){throw 'The exact bridge ownership ledger does not match.'}
if(!$Execute){Write-Output 'No change. Execute will first retire public managed routing, then delete only the exact ledger bridge and agent. Other owned prerequisites require their separate reconciled resource ledger.';return}
& .venv/Scripts/python.exe scripts/manage_route.py deactivate
if($LASTEXITCODE){throw 'Public cutover did not confirm. Stop and reconcile before deleting the serving path.'}
$RelayGcloud=Join-Path $RelayLocal 'tools/google-cloud-sdk/bin/gcloud.cmd'
& $RelayGcloud run services delete $RelayBridge.service --project=$($RelayBridge.project) --region=$($RelayBridge.region) --quiet
if($LASTEXITCODE){throw 'Bridge deletion did not confirm. No unrelated service was selected.'}
$RelayBridge.status='delete_returned';$RelayBridge | ConvertTo-Json | Set-Content -LiteralPath $RelayBridgePath -Encoding UTF8
& .venv/Scripts/python.exe scripts/organizer_agent.py retire --plan $RelayPlanFile --execute
if($LASTEXITCODE){throw 'Agent deletion did not confirm. Inspect the exact ownership ledger.'}
Write-Output 'Bridge/agent delete operations returned. Verify absence, drain unknown operations and reconcile any separately recorded staging buckets/images/secrets/identities before declaring cleanup complete.'
