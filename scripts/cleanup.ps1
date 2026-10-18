param([switch]$RemoveTemporaryFiles)
. "$PSScriptRoot/env.ps1"
$RelayTarget = [IO.Path]::GetFullPath((Join-Path $RelayRoot '.local/tmp'))
$RelayExpected = [IO.Path]::GetFullPath('D:\projects\CampusPulseRELAY\.local\tmp')
if ($RelayTarget -ne $RelayExpected -or !$RelayTarget.StartsWith([IO.Path]::GetFullPath($RelayRoot)+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)) { throw 'Cleanup target failed the absolute workspace boundary check.' }
if ($RemoveTemporaryFiles) {
    Get-ChildItem -LiteralPath $RelayTarget -Force | Remove-Item -Recurse -Force
    Write-Output "Removed only temporary children of $RelayTarget."
} else { Write-Output "Dry run: only temporary children of $RelayTarget would be removed. Pass -RemoveTemporaryFiles when builds and tests have stopped." }
Write-Output 'No cloud, GitHub, Calendar, installed application, source, judging resource, environment or cache was removed.'
