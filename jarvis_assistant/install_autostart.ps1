# Legt eine Verknuepfung in den Windows-Autostart, damit Jarvis mit Windows startet.
# Ausfuehren:  Rechtsklick -> "Mit PowerShell ausfuehren"  (oder in einer PS-Konsole)

$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$startup = [System.Environment]::GetFolderPath("Startup")
$lnkPath = Join-Path $startup "Jarvis.lnk"

$ws = New-Object -ComObject WScript.Shell
$lnk = $ws.CreateShortcut($lnkPath)
$lnk.TargetPath = "pythonw.exe"          # pythonw = ohne Konsolenfenster
$lnk.Arguments = "-m jarvis.main"
$lnk.WorkingDirectory = $here
$lnk.WindowStyle = 7                       # minimiert
$lnk.Description = "Jarvis Sprach-Assistent"
$lnk.Save()

Write-Host "Autostart-Verknuepfung angelegt:" $lnkPath
Write-Host "Zum Entfernen einfach diese .lnk-Datei loeschen."
