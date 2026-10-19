param([Parameter(Mandatory=$true)][string]$PlanPath,[switch]$Execute)
. "$PSScriptRoot/env.ps1"
Set-Location -LiteralPath $RelayRoot
$RelayPlanFile=[IO.Path]::GetFullPath($PlanPath)
if($RelayPlanFile -notmatch '^[dD]:[\\/]'){throw 'The actual organizer plan must stay on D:.'}
$RelayPlan=Get-Content -LiteralPath $RelayPlanFile -Raw | ConvertFrom-Json
if($RelayPlan.project -notmatch '^[a-z][a-z0-9-]{4,61}[a-z0-9]$' -or $RelayPlan.owned_prefix -notmatch '^[a-z][a-z0-9-]{4,26}$'){throw 'Use the actual project and unique owned prefix.'}
$RelayBridgeName=$RelayPlan.owned_prefix+'-bridge'
$RelayAgentLedger=Join-Path $RelayLocal ('organizer/'+$RelayPlan.owned_prefix+'/agent-ledger.json')
$RelayFunding=Get-Content -LiteralPath $RelayPlan.funding_record -Raw | ConvertFrom-Json
$RelayLedger=Get-Content -LiteralPath $RelayAgentLedger -Raw | ConvertFrom-Json
if(!$RelayLedger.resource -or $RelayLedger.project -ne $RelayPlan.project){throw 'Deploy/discover the exact owned Agent Engine first.'}
$RelayBridgePlan=Join-Path $RelayLocal ('organizer/'+$RelayPlan.owned_prefix+'/bridge-env.yaml')
$RelayBridgeLedger=Join-Path $RelayLocal ('organizer/'+$RelayPlan.owned_prefix+'/bridge-ledger.json')
if(!$Execute){Write-Output ('Prepared bridge target: '+$RelayBridgeName+'. No resource was created. Existing covered image, service identity and pinned secrets must be verified at T0.');return}
if(!$RelayPlan.covered_prerequisites_verified -or !$RelayPlan.cleanup_reserve_verified -or $RelayPlan.personal_spending_authorized_usd -ne 0){throw 'Actual organizer coverage and zero personal spending are required.'}
& .venv/Scripts/python.exe scripts/check-funding.py --record $RelayPlan.funding_record --project $RelayPlan.project --budget $RelayPlan.authorized_credit_usage_usd --hours $RelayPlan.planned_hours
if($LASTEXITCODE){throw 'Actual funding/window guard failed; no bridge was deployed.'}
if($RelayPlan.bridge_image -notmatch ('^'+[regex]::Escape($RelayPlan.region)+'-docker.pkg.dev/'+[regex]::Escape($RelayPlan.project)+'/[a-z0-9-]+/[a-z0-9-]+@sha256:[a-f0-9]{64}$')){throw 'Use the actual immutable covered bridge image digest.'}
if($RelayPlan.bridge_service_account -notmatch ('^[a-z][a-z0-9-]+@'+[regex]::Escape($RelayPlan.project)+'\.iam\.gserviceaccount\.com$')){throw 'Use the dedicated bridge service identity.'}
foreach($RelaySecretPart in @('context_secret_id','bridge_secret_id')){if($RelayPlan.$RelaySecretPart -notmatch '^[A-Za-z0-9_-]{1,200}$'){throw 'Use actual owned Secret Manager IDs.'}}
foreach($RelaySecretPart in @('context_secret_version','bridge_secret_version')){if([string]$RelayPlan.$RelaySecretPart -notmatch '^\d+$'){throw 'Pin numeric secret versions.'}}
if(Test-Path -LiteralPath $RelayBridgeLedger){throw 'A bridge attempt is recorded. Inspect/reconcile it before another deployment.'}
$RelayGcloud=Join-Path $RelayLocal 'tools/google-cloud-sdk/bin/gcloud.cmd'
$RelayExisting=& $RelayGcloud run services list --project=$($RelayPlan.project) --region=$($RelayPlan.region) --filter="metadata.name=$RelayBridgeName" --format='value(metadata.name)'
if($LASTEXITCODE -or $RelayExisting){throw 'The target could not be verified absent. Do not modify another service.'}
$RelayBridgeEnv=@{GOOGLE_CLOUD_PROJECT=$RelayPlan.project;GOOGLE_CLOUD_LOCATION=$RelayPlan.region;RELAY_AGENT_RESOURCE=$RelayLedger.resource;RELAY_MCP_URL=($RelayPlan.public_origin+'/managed/mcp/');RELAY_MANAGED_ACTIVATED_AT=$RelayFunding.activated_at_utc;RELAY_MANAGED_EXPIRES_AT=$RelayFunding.expires_at_utc}
$RelayYaml=($RelayBridgeEnv.GetEnumerator() | Sort-Object Name | ForEach-Object { $_.Name+': '+(ConvertTo-Json -InputObject ([string]$_.Value) -Compress) }) -join "`n"
[IO.File]::WriteAllText($RelayBridgePlan,$RelayYaml,[Text.UTF8Encoding]::new($false))
@{status='deployment_requested';service=$RelayBridgeName;project=$RelayPlan.project;region=$RelayPlan.region;image=$RelayPlan.bridge_image;agent=$RelayLedger.resource} | ConvertTo-Json | Set-Content -LiteralPath $RelayBridgeLedger -Encoding UTF8
# Public HTTPS transport is required for Render, but every query is HMAC- and
# workspace-authenticated. Administrative APIs and raw MCP are never exposed here.
& $RelayGcloud run deploy $RelayBridgeName --project=$($RelayPlan.project) --region=$($RelayPlan.region) --image=$($RelayPlan.bridge_image) --service-account=$($RelayPlan.bridge_service_account) --min-instances=0 --max-instances=1 --concurrency=2 --cpu=1 --memory=512Mi --timeout=600 --allow-unauthenticated --env-vars-file=$RelayBridgePlan --set-secrets="RELAY_CONTEXT_SECRET=$($RelayPlan.context_secret_id):$($RelayPlan.context_secret_version),RELAY_MANAGED_BRIDGE_SECRET=$($RelayPlan.bridge_secret_id):$($RelayPlan.bridge_secret_version)" --quiet
if($LASTEXITCODE){throw 'Bridge deployment failed or has an unknown outcome. Inspect its recorded name; do not blindly create a replacement.'}
$RelayDescription=& $RelayGcloud run services describe $RelayBridgeName --project=$($RelayPlan.project) --region=$($RelayPlan.region) --format=json | ConvertFrom-Json
if($LASTEXITCODE){throw 'Bridge discovery failed. The deployment ledger is retained.'}
@{status='discovered_not_live_acceptance';service=$RelayBridgeName;project=$RelayPlan.project;region=$RelayPlan.region;url=$RelayDescription.status.url;image=$RelayPlan.bridge_image;agent=$RelayLedger.resource;remote_query_verified=$false} | ConvertTo-Json | Set-Content -LiteralPath $RelayBridgeLedger -Encoding UTF8
Write-Output ('Actual bridge URL: '+$RelayDescription.status.url+'. Remote query and shared-state/MCP acceptance remain pending.')
