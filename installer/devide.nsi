; devide.nsi - based on example2.nsi
; $Id: devide.nsi,v 1.1 2004/01/15 19:57:22 cpbotha Exp $

;--------------------------------

; The name of the installer
Name "DeVIDE"

; The file to write
OutFile "devidesetup.exe"

; The default installation directory
InstallDir $PROGRAMFILES\devide

; Registry key to check for directory (so if you install again, it will 
; overwrite the old one automatically)
InstallDirRegKey HKLM SOFTWARE\devide "Install_Dir"

; The text to prompt the user to enter a directory
ComponentText "Select optional components."

; The text to prompt the user to enter a directory
DirText "Choose the directory where you'd like to install devide:"

;--------------------------------

; The stuff to install
Section "devide (required)"

  SectionIn RO
  
  ; Set output path to the installation directory.
  SetOutPath $INSTDIR
  
  ; take all these files (recursively yay)
  File /r "distdevide\*.*"
  
  ; Write the installation path into the registry
  WriteRegStr HKLM SOFTWARE\devide "Install_Dir" "$INSTDIR"
  
  ; Write the uninstall keys for Windows
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\devide" "DisplayName" "devide (remove only)"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\devide" "UninstallString" '"$INSTDIR\uninstall.exe"'
  WriteUninstaller "uninstall.exe"
  
SectionEnd

; optional section (can be disabled by the user)
Section "Start Menu Shortcuts"

  CreateDirectory "$SMPROGRAMS\devide"
  CreateShortCut "$SMPROGRAMS\devide\Uninstall.lnk" "$INSTDIR\uninstall.exe" "" "$INSTDIR\uninstall.exe" 0
  CreateShortCut "$SMPROGRAMS\devide\devide.lnk" "$INSTDIR\devide.exe" "" "$INSTDIR\devide.exe" 0
  
SectionEnd

Section "Desktop Shortcut"
   CreateShortCut "$DESKTOP\devide.lnk" "$INSTDIR\devide.exe"
SectionEnd

;--------------------------------

; Uninstaller

UninstallText "This will uninstall devide. Hit next to continue."

; Uninstall section

Section "Uninstall"
  
  ; remove registry keys
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\devide"
  DeleteRegKey HKLM SOFTWARE\devide

  ; remove files and uninstaller
  Delete $INSTDIR\*.*

  ; remove shortcuts, if any
  Delete "$SMPROGRAMS\devide\*.*"

  ; remove desktop shortcut
  Delete "$DESKTOP\devide.lnk"

  ; remove directories used
  RMDir "$SMPROGRAMS\devide"
  RMDir "$INSTDIR"

SectionEnd