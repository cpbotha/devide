; devide.nsi - based on example2.nsi
; $Id: devide.nsi,v 1.4 2005/05/23 16:46:19 cpbotha Exp $

;--------------------------------

; The name of the installer
Name "DeVIDE"

; The file to write
OutFile "devidesetup.exe"

; The default installation directory
InstallDir $PROGRAMFILES\DeVIDE

; Registry key to check for directory (so if you install again, it will 
; overwrite the old one automatically)
InstallDirRegKey HKLM SOFTWARE\DeVIDE "Install_Dir"

; The text to prompt the user to enter a directory
ComponentText "Select optional components."

; The text to prompt the user to enter a directory
DirText "Choose the directory where you'd like to install DeVIDE:"

;--------------------------------

; Pages

Page components
Page directory
Page instfiles

UninstPage uninstConfirm
UninstPage instfiles

;--------------------------------

; The stuff to install
Section "DeVIDE (required)"

  SectionIn RO
  
  ; Set output path to the installation directory.
  SetOutPath $INSTDIR
  
  ; take all these files (recursively yay)
  File /r "distdevide\*.*"
  
  ; Write the installation path into the registry
  WriteRegStr HKLM SOFTWARE\DeVIDE "Install_Dir" "$INSTDIR"
  
  ; Write the uninstall keys for Windows
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\DeVIDE" "DisplayName" "DeVIDE (remove only)"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\DeVIDE" "UninstallString" '"$INSTDIR\uninstall.exe"'
  WriteUninstaller "uninstall.exe"
  
SectionEnd

; optional section (can be disabled by the user)
Section "Start Menu Shortcuts"
  CreateDirectory "$SMPROGRAMS\DeVIDE"
  CreateShortCut "$SMPROGRAMS\DeVIDE\DeVIDE.lnk" "$INSTDIR\devide.exe" "" "$INSTDIR\devide.exe" 0
  CreateShortCut "$SMPROGRAMS\DeVIDE\DeVIDE no-itk.lnk" "$INSTDIR\devide.exe" "--no-itk" "$INSTDIR\devide.exe" 0
  CreateShortCut "$SMPROGRAMS\DeVIDE\Uninstall.lnk" "$INSTDIR\uninstall.exe" "" "$INSTDIR\uninstall.exe" 0  
SectionEnd

Section "Desktop Shortcut"
   CreateShortCut "$DESKTOP\DeVIDE.lnk" "$INSTDIR\devide.exe"
   CreateShortCut "$DESKTOP\DeVIDE no-itk.lnk" "$INSTDIR\devide.exe" "--no-itk"
SectionEnd

;--------------------------------

; Uninstaller

UninstallText "This will uninstall DeVIDE. Hit next to continue."

; Uninstall section

Section "Uninstall"
  
  ; remove registry keys
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\DeVIDE"
  DeleteRegKey HKLM SOFTWARE\DeVIDE

  ; remove files and uninstaller
  Delete $INSTDIR\*.*

  ; remove shortcuts, if any
  Delete "$SMPROGRAMS\DeVIDE\*.*"

  ; remove desktop shortcut
  Delete "$DESKTOP\DeVIDE.lnk"
  Delete "$DESKTOP\DeVIDE no-itk.lnk"

  ; remove directories used
  RMDir "$SMPROGRAMS\DeVIDE"

  ; actually this will do a recursive delete on everything
  RMDir /R "$INSTDIR"

SectionEnd



