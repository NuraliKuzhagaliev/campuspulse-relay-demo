!macro preInit
  StrCpy $INSTDIR "D:\projects\CampusPulseRELAY\installed\CampusPulse RELAY"
!macroend

; preInit alone is overwritten by electron-builder's later setInstallMode.
; The custom script calls this again at the start of the install section,
; before uninstall/file/link/registry operations, including silent installs.
!macro relayEnforceD
  ${IfNot} ${FileExists} "D:\."
    MessageBox MB_ICONSTOP "CampusPulse RELAY requires drive D:. No installation on C: is permitted."
    SetErrorLevel 2
    Abort
  ${EndIf}
  StrCpy $INSTDIR "D:\projects\CampusPulseRELAY\installed\CampusPulse RELAY"
!macroend

!macro customInit
  !insertmacro relayEnforceD
!macroend
