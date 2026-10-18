. "$PSScriptRoot/env.ps1"
$RelayArchive = Join-Path $RelayLocal 'downloads/google-cloud-cli-windows-x86_64.zip'
$RelayTools = Join-Path $RelayLocal 'tools'
New-Item -ItemType Directory -Force -Path $RelayTools | Out-Null
if (!(Test-Path $RelayArchive)) { Invoke-WebRequest 'https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-cli-windows-x86_64.zip' -OutFile $RelayArchive }
if (!(Test-Path "$RelayTools/google-cloud-sdk/bin/gcloud.cmd")) { Expand-Archive -LiteralPath $RelayArchive -DestinationPath $RelayTools }
& "$RelayTools/google-cloud-sdk/bin/gcloud.cmd" version
