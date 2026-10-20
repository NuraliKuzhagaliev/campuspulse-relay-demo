"""Regression guards for the observed default-C installation, not native UI proof."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DESTINATION = r'D:\projects\CampusPulseRELAY\installed\CampusPulse RELAY'


def test_release_uses_own_installer_instead_of_default_local_appdata_path():
    config = json.loads((ROOT / 'package.json').read_text())['build']['nsis']
    assert config['script'] == 'desktop/installer.nsi'
    script = (ROOT / config['script']).read_text()
    install = script.split('Section "Install CampusPulse RELAY"', 1)[1].split('SectionEnd', 1)[0]
    assert install.index('!insertmacro relayEnforceD') < install.index('SetOutPath') < install.index('File /r')
    assert f'InstallDir "{DESTINATION}"' in script
    assert '$LOCALAPPDATA' not in script and 'initMultiUser' not in script
    assert 'WriteUninstaller "$INSTDIR\\Uninstall CampusPulse RELAY.exe"' in install
    assert 'CampusPulseRELAY-D' in install  # Preserve the old C registration for owner cleanup.


def test_owner_helper_sets_d_environment_and_explicit_nsis_destination():
    script = (ROOT / 'scripts/install_release_native.ps1').read_text()
    assert script.index('. "$PSScriptRoot/env.ps1"') < script.index('Start-Process')
    assert f'"/D={DESTINATION}"' in script
    assert '-Wait -PassThru' in script
    assert 'ProductVersion' in script and 'ExitCode -ne 0' in script
    assert 'Stop-Process' not in script


def test_uninstaller_guards_exact_d_program_path_before_recursive_removal():
    script = (ROOT / 'desktop/installer.nsi').read_text()
    uninstall = script.split('Section "Uninstall"', 1)[1]
    assert uninstall.index(f'StrCmp $INSTDIR "{DESTINATION}"') < uninstall.index('RMDir /r "$INSTDIR"')
    assert 'Abort' in uninstall[:uninstall.index('RMDir')]
    assert script.count('RMDir /r') == 1
    assert '.local' not in uninstall and '$APPDATA' not in uninstall
