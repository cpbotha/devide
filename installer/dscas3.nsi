; dscas3.nsi - based on example2.nsi
; $Id: dscas3.nsi,v 1.2 2003/05/01 22:47:29 cpbotha Exp $

;--------------------------------

; The name of the installer
Name "DSCAS3"

; The file to write
OutFile "dscas3setup.exe"

; The default installation directory
InstallDir $PROGRAMFILES\dscas3

; Registry key to check for directory (so if you install again, it will 
; overwrite the old one automatically)
InstallDirRegKey HKLM SOFTWARE\dscas3 "Install_Dir"

; The text to prompt the user to enter a directory
ComponentText "Select optional components."

; The text to prompt the user to enter a directory
DirText "Choose the directory where you'd like to install dscas3:"

;--------------------------------

; The stuff to install
Section "dscas3 (required)"

  SectionIn RO
  
  ; Set output path to the installation directory.
  SetOutPath $INSTDIR
  
  ; take all these files (recursively yay)
  File /r "distdscas3\*.*"
  
  ; Write the installation path into the registry
  WriteRegStr HKLM SOFTWARE\dscas3 "Install_Dir" "$INSTDIR"
  
  ; Write the uninstall keys for Windows
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\dscas3" "DisplayName" "dscas3 (remove only)"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\dscas3" "UninstallString" '"$INSTDIR\uninstall.exe"'
  WriteUninstaller "uninstall.exe"
  
SectionEnd

; optional section (can be disabled by the user)
Section "Start Menu Shortcuts"

  CreateDirectory "$SMPROGRAMS\dscas3"
  CreateShortCut "$SMPROGRAMS\dscas3\Uninstall.lnk" "$INSTDIR\uninstall.exe" "" "$INSTDIR\uninstall.exe" 0
  CreateShortCut "$SMPROGRAMS\dscas3\dscas3.lnk" "$INSTDIR\dscas3.exe" "" "$INSTDIR\dscas3.exe" 0
  
SectionEnd

Section "Desktop Shortcut"
   CreateShortCut "$DESKTOP\dscas3.lnk" "$INSTDIR\dscas3.exe"
SectionEnd

;--------------------------------

; Uninstaller

UninstallText "This will uninstall dscas3. Hit next to continue."

; Uninstall section

Section "Uninstall"
  
  ; remove registry keys
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\dscas3"
  DeleteRegKey HKLM SOFTWARE\dscas3

  ; remove files and uninstaller
  Delete $INSTDIR\*.*

  ; remove shortcuts, if any
  Delete "$SMPROGRAMS\dscas3\*.*"

  ; remove desktop shortcut
  Delete "$DESKTOP\dscas3.lnk"

  ; remove directories used
  RMDir "$SMPROGRAMS\dscas3"
  RMDir "$INSTDIR"

SectionEnd