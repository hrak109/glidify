; Custom NSIS Hooks for SmoothScroll Windows Installer
!macro customInstall
  DetailPrint "Configuring SmoothScroll Windows 11 integration..."
!macroend

!macro customUnInstall
  DetailPrint "Cleaning up registry and running processes..."
  ; Stop any running instances before uninstalling
  nsExec::Exec 'taskkill /F /IM SmoothScroll.exe'
  DeleteRegValue HKCU "Software\Microsoft\Windows\CurrentVersion\Run" "SmoothScroll"
!macroend
