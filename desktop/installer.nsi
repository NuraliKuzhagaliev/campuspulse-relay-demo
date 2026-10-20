; CampusPulse RELAY owner-invoked D-drive installer.
; No LocalAppData installer cache, shortcuts, auto-launch or profile deletion.
!include "MUI2.nsh"
Name "CampusPulse RELAY"
RequestExecutionLevel user
InstallDir "D:\projects\CampusPulseRELAY\installed\CampusPulse RELAY"
ShowInstDetails show
ShowUninstDetails show
!define MUI_ABORTWARNING
!insertmacro MUI_PAGE_WELCOME
!define MUI_PAGE_CUSTOMFUNCTION_LEAVE relayValidateDirectory
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "English"

Function .onInit
  !insertmacro relayEnforceD
FunctionEnd

Function relayValidateDirectory
  StrCmp $INSTDIR "D:\projects\CampusPulseRELAY\installed\CampusPulse RELAY" relayDirectoryOK
    MessageBox MB_ICONSTOP "This release must be installed in D:\projects\CampusPulseRELAY\installed\CampusPulse RELAY. No C: installation is permitted."
    Abort
  relayDirectoryOK:
FunctionEnd

Section "Install CampusPulse RELAY" install
  !insertmacro relayEnforceD
  SetOutPath "$INSTDIR"
  File /r "${PROJECT_DIR}\release\windows\win-unpacked\*.*"
  WriteUninstaller "$INSTDIR\Uninstall CampusPulse RELAY.exe"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\CampusPulseRELAY-D" "DisplayName" "CampusPulse RELAY (D:)"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\CampusPulseRELAY-D" "DisplayVersion" "${VERSION}"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\CampusPulseRELAY-D" "InstallLocation" "$INSTDIR"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\CampusPulseRELAY-D" "UninstallString" '"$INSTDIR\Uninstall CampusPulse RELAY.exe"'
  WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\CampusPulseRELAY-D" "NoModify" 1
  WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\CampusPulseRELAY-D" "NoRepair" 1
SectionEnd

Function un.onInit
  ; Validate the resolved program directory before ANY recursive removal.
  StrCmp $INSTDIR "D:\projects\CampusPulseRELAY\installed\CampusPulse RELAY" relayUninstallDirectoryOK
    MessageBox MB_ICONSTOP "Uninstall is limited to the original D-drive program directory. Profiles and project data are preserved."
    Abort
  relayUninstallDirectoryOK:
FunctionEnd

Section "Uninstall"
  StrCmp $INSTDIR "D:\projects\CampusPulseRELAY\installed\CampusPulse RELAY" relayRemoveProgramOnly
    Abort
  relayRemoveProgramOnly:
  RMDir /r "$INSTDIR"
  DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\CampusPulseRELAY-D"
SectionEnd
