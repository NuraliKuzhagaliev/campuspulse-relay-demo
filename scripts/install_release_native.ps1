# Run interactively by the owner. Does not close or launch RELAY.
. "$PSScriptRoot/env.ps1"
$RelayReleaseVersion=(Get-Content -LiteralPath (Join-Path $RelayRoot 'package.json') -Raw | ConvertFrom-Json).version
$RelayInstaller=Join-Path $RelayRoot ("release/windows/CampusPulse-RELAY-"+$RelayReleaseVersion+"-x64-setup.exe")
if (!(Test-Path -LiteralPath $RelayInstaller)) { throw "The $RelayReleaseVersion installer has not been built." }
Write-Output 'Close RELAY manually, then complete this installer. Its destination is D:/projects/CampusPulseRELAY/installed/CampusPulse RELAY. Project temporary files are on D:. Previous profiles remain unchanged.'
$RelayInstallerProcess=Start-Process -FilePath $RelayInstaller -ArgumentList @("/currentuser", "/D=D:\projects\CampusPulseRELAY\installed\CampusPulse RELAY") -WorkingDirectory $RelayRoot -WindowStyle Normal -Wait -PassThru
$RelayInstalledFile=Join-Path $RelayRoot 'installed/CampusPulse RELAY/CampusPulse RELAY.exe'
if ($RelayInstallerProcess.ExitCode -ne 0 -or !(Test-Path -LiteralPath $RelayInstalledFile) -or (Get-Item -LiteralPath $RelayInstalledFile).VersionInfo.ProductVersion -notlike ($RelayReleaseVersion+'*')) {
    throw "Installation did not complete as $RelayReleaseVersion. Close RELAY manually and complete the installer before running the native recheck. Existing profiles are preserved."
}
Write-Output "Installed $RelayReleaseVersion detected on D:. Run scripts/recheck_release_native.ps1 when ready for your manual check."
