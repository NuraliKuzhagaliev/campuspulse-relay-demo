param(
    [Parameter(Mandatory=$true)][decimal]$ApprovedBudgetUsd,
    [Parameter(Mandatory=$true)][switch]$AcknowledgeBillableResources,
    [ValidateRange(1,72)][int]$PilotHours=72
)
. "$PSScriptRoot/env.ps1"
Set-Location $RelayRoot
if (!$AcknowledgeBillableResources -or $ApprovedBudgetUsd -le 0) { throw 'A specific human-approved budget is required. This is not a cloud-enforced dollar cap.' }
foreach ($key in @('GOOGLE_CLOUD_PROJECT','GOOGLE_CLOUD_LOCATION','RELAY_AUTH_AUDIENCE','RELAY_OAUTH_CLIENT_ID','RELAY_OAUTH_CLIENT_SECRET','RELAY_TOKEN_ENCRYPTION_KEY','RELAY_CONTEXT_SECRET','RELAY_GITHUB_REPO')) {
    if (![Environment]::GetEnvironmentVariable($key)) { throw "Missing $key. Review docs/cloud_setup.md." }
}
$RelayGcloud = Join-Path $RelayLocal 'tools/google-cloud-sdk/bin/gcloud.cmd'
$RelayProject = $env:GOOGLE_CLOUD_PROJECT
$RelayRegion = $env:GOOGLE_CLOUD_LOCATION
$RelayFundingPath=Join-Path $RelayLocal 'credit-activation.json'
if (!(Test-Path $RelayFundingPath)) { throw 'Organizer credits are pending. Run record-credit-activation.ps1 only after actual activation/eligibility confirmation. Personal spending is not authorized.' }
$RelayFunding=Get-Content -LiteralPath $RelayFundingPath -Raw | ConvertFrom-Json
if ($RelayFunding.project_id -ne $RelayProject -or !$RelayFunding.eligibility_human_confirmed -or $RelayFunding.source -ne 'organizer-credits') { throw 'Credit eligibility is not confirmed for this exact project.' }
if ($RelayFunding.balance_usd_human_confirmed -lt $ApprovedBudgetUsd -or [datetime]::Parse($RelayFunding.expires_at_utc).ToUniversalTime() -le [datetime]::UtcNow.AddHours($PilotHours)) { throw 'Confirmed credits do not cover the proposed amount/duration. Explain uncovered cost and obtain separate approval before proceeding.' }
function Invoke-Cloud { & $RelayGcloud @args; if ($LASTEXITCODE) { throw 'Google Cloud command failed. Read the diagnostic; no further resources will be created.' } }
$RelayBilling = & $RelayGcloud billing projects describe $RelayProject --format=json | ConvertFrom-Json
if (!$RelayBilling.billingEnabled) { throw 'Existing billing is not enabled. This script does not attach a billing account or make a payment.' }
if ($RelayBilling.billingAccountName -ne $RelayFunding.billing_account) { throw 'Billing changed since the credit review. Stop and recheck organizer eligibility.' }
Invoke-Cloud services enable aiplatform.googleapis.com run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com firestore.googleapis.com storage.googleapis.com secretmanager.googleapis.com cloudscheduler.googleapis.com calendar-json.googleapis.com --project=$RelayProject
$RelayAuthLogFilter='resource.type="cloud_run_revision" AND resource.labels.service_name="relay-gateway" AND httpRequest.requestUrl:"/auth/callback"'
$RelayDefaultSink=& $RelayGcloud logging sinks describe _Default --project=$RelayProject --format=json | ConvertFrom-Json
if ($RelayDefaultSink.exclusions.name -contains 'relay-oauth-callback') {
    Invoke-Cloud logging sinks update _Default --project=$RelayProject --update-exclusion="name=relay-oauth-callback,filter=$RelayAuthLogFilter"
} else {
    Invoke-Cloud logging sinks update _Default --project=$RelayProject --add-exclusion="name=relay-oauth-callback,filter=$RelayAuthLogFilter,description=Exclude OAuth callback request URLs containing one-use codes"
}
# Dedicated identities and resources only. Grant roles to these service identities, never to allUsers on MCP.
foreach ($identity in @('relay-gateway','relay-mcp','relay-runtime','relay-scheduler')) {
    & $RelayGcloud iam service-accounts describe "$identity@$RelayProject.iam.gserviceaccount.com" --project=$RelayProject *> $null
    if ($LASTEXITCODE) { Invoke-Cloud iam service-accounts create $identity --display-name="CampusPulse RELAY $identity" --project=$RelayProject }
}
foreach ($identity in @('relay-gateway','relay-mcp','relay-runtime')) {
    Invoke-Cloud projects add-iam-policy-binding $RelayProject --member="serviceAccount:$identity@$RelayProject.iam.gserviceaccount.com" --role=roles/datastore.user --condition=None
}
Invoke-Cloud projects add-iam-policy-binding $RelayProject --member="serviceAccount:relay-gateway@$RelayProject.iam.gserviceaccount.com" --role=roles/aiplatform.user --condition=None
Invoke-Cloud projects add-iam-policy-binding $RelayProject --member="serviceAccount:relay-runtime@$RelayProject.iam.gserviceaccount.com" --role=roles/aiplatform.user --condition=None
foreach ($pair in @(@('relay-context','RELAY_CONTEXT_SECRET'),@('relay-token-key','RELAY_TOKEN_ENCRYPTION_KEY'),@('relay-oauth-client','RELAY_OAUTH_CLIENT_SECRET'))) {
    $RelaySecretName=$pair[0];$RelaySecretVar=$pair[1];$RelaySecretPath=Join-Path $RelayLocal "tmp/$RelaySecretName.secret"
    [IO.File]::WriteAllText($RelaySecretPath,[Environment]::GetEnvironmentVariable($RelaySecretVar))
    & $RelayGcloud secrets describe $RelaySecretName --project=$RelayProject *> $null
    if ($LASTEXITCODE) { Invoke-Cloud secrets create $RelaySecretName --replication-policy=automatic --project=$RelayProject }
    Invoke-Cloud secrets versions add $RelaySecretName --data-file=$RelaySecretPath --project=$RelayProject
    Remove-Item -LiteralPath $RelaySecretPath
    $RelaySecretReaders = if ($RelaySecretName -eq 'relay-context') { @('relay-gateway','relay-mcp','relay-runtime') } elseif ($RelaySecretName -eq 'relay-token-key') { @('relay-gateway','relay-mcp') } else { @('relay-gateway') }
    foreach ($identity in $RelaySecretReaders) {
        Invoke-Cloud secrets add-iam-policy-binding $RelaySecretName --member="serviceAccount:$identity@$RelayProject.iam.gserviceaccount.com" --role=roles/secretmanager.secretAccessor --project=$RelayProject
    }
}
& $RelayGcloud firestore databases describe --project=$RelayProject *> $null
if ($LASTEXITCODE) { Invoke-Cloud firestore databases create --location=$RelayRegion --type=firestore-native --project=$RelayProject }
$RelayBucket="$RelayProject-relay-staging"
& $RelayGcloud storage buckets describe "gs://$RelayBucket" *> $null
if ($LASTEXITCODE) { Invoke-Cloud storage buckets create "gs://$RelayBucket" --location=$RelayRegion --uniform-bucket-level-access --project=$RelayProject }
& $RelayGcloud artifacts repositories describe relay --location=$RelayRegion --project=$RelayProject *> $null
if ($LASTEXITCODE) { Invoke-Cloud artifacts repositories create relay --repository-format=docker --location=$RelayRegion --project=$RelayProject }
$RelayImage="$RelayRegion-docker.pkg.dev/$RelayProject/relay/app:0.1.0"
Invoke-Cloud builds submit --config=infra/cloudbuild.yaml --substitutions="_IMAGE=$RelayImage" --project=$RelayProject
Invoke-Cloud run deploy relay-mcp --image=$RelayImage --region=$RelayRegion --project=$RelayProject --service-account="relay-mcp@$RelayProject.iam.gserviceaccount.com" --no-allow-unauthenticated --min-instances=0 --max-instances=2 --memory=1Gi --cpu=1 --concurrency=8 --set-env-vars="RELAY_SERVICE=mcp,RELAY_MODE=cloud,GOOGLE_CLOUD_PROJECT=$RelayProject,RELAY_GITHUB_REPO=$env:RELAY_GITHUB_REPO" --set-secrets='RELAY_CONTEXT_SECRET=relay-context:latest,RELAY_TOKEN_ENCRYPTION_KEY=relay-token-key:latest'
$RelayMcpOrigin=& $RelayGcloud run services describe relay-mcp --region=$RelayRegion --project=$RelayProject --format='value(status.url)'
$env:RELAY_MCP_URL="$RelayMcpOrigin/mcp/"
Invoke-Cloud run services update relay-mcp --region=$RelayRegion --project=$RelayProject --update-env-vars="RELAY_MCP_URL=$env:RELAY_MCP_URL"
Invoke-Cloud run services add-iam-policy-binding relay-mcp --region=$RelayRegion --project=$RelayProject --member="serviceAccount:relay-runtime@$RelayProject.iam.gserviceaccount.com" --role=roles/run.invoker
$env:RELAY_STAGING_BUCKET="gs://$RelayBucket"
$env:RELAY_RUNTIME_SERVICE_ACCOUNT="relay-runtime@$RelayProject.iam.gserviceaccount.com"
& '.venv/Scripts/python.exe' scripts/deploy_reasoning_engine.py --approved-budget-usd $ApprovedBudgetUsd
if ($LASTEXITCODE) { throw 'Managed Agent Engine deployment failed. Gateway will not bypass it.' }
$RelayProof=Get-Content 'docs/evidence/deployment.json' -Raw | ConvertFrom-Json
$env:RELAY_AGENT_RESOURCE=$RelayProof.name
Invoke-Cloud run deploy relay-gateway --image=$RelayImage --region=$RelayRegion --project=$RelayProject --service-account="relay-gateway@$RelayProject.iam.gserviceaccount.com" --allow-unauthenticated --min-instances=0 --max-instances=2 --memory=1Gi --cpu=1 --concurrency=16 --timeout=180 --set-env-vars="RELAY_SERVICE=gateway,RELAY_MODE=cloud,GOOGLE_CLOUD_PROJECT=$RelayProject,GOOGLE_CLOUD_LOCATION=$RelayRegion,RELAY_MCP_URL=$env:RELAY_MCP_URL,RELAY_AGENT_RESOURCE=$env:RELAY_AGENT_RESOURCE,RELAY_AUTH_AUDIENCE=$env:RELAY_AUTH_AUDIENCE,RELAY_OAUTH_CLIENT_ID=$env:RELAY_OAUTH_CLIENT_ID,RELAY_GITHUB_REPO=$env:RELAY_GITHUB_REPO" --set-secrets='RELAY_CONTEXT_SECRET=relay-context:latest,RELAY_TOKEN_ENCRYPTION_KEY=relay-token-key:latest,RELAY_OAUTH_CLIENT_SECRET=relay-oauth-client:latest'
$RelayGatewayUrl=& $RelayGcloud run services describe relay-gateway --region=$RelayRegion --project=$RelayProject --format='value(status.url)'
$env:RELAY_GATEWAY_URL=$RelayGatewayUrl
$env:RELAY_SCHEDULER_IDENTITY="relay-scheduler@$RelayProject.iam.gserviceaccount.com"
Invoke-Cloud run services update relay-gateway --region=$RelayRegion --project=$RelayProject --update-env-vars="RELAY_GATEWAY_URL=$RelayGatewayUrl,RELAY_SCHEDULER_IDENTITY=$env:RELAY_SCHEDULER_IDENTITY"
& $RelayGcloud scheduler jobs describe relay-source-sync --location=$RelayRegion --project=$RelayProject *> $null
if ($LASTEXITCODE) {
    Invoke-Cloud scheduler jobs create http relay-source-sync --location=$RelayRegion --project=$RelayProject --schedule='* * * * *' --time-zone=UTC --uri="$RelayGatewayUrl/internal/sync" --http-method=POST --oidc-service-account-email=$env:RELAY_SCHEDULER_IDENTITY --oidc-token-audience=$RelayGatewayUrl
}
$RelayEndpoints=@{gateway=$RelayGatewayUrl;mcp=$env:RELAY_MCP_URL;agent=$env:RELAY_AGENT_RESOURCE;approved_budget_usd=$ApprovedBudgetUsd;remote_smoke_verified=$false}
$RelayEndpoints | ConvertTo-Json | Set-Content 'docs/evidence/cloud-endpoints.json'
Write-Output 'Deployment commands completed. Configure OAuth redirect URI using the returned gateway URL, then sign in and run scripts/smoke_remote.py. No live verification is implied by this message.'
