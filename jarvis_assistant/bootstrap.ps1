# Jarvis — Ein-Befehl-Einrichtung fuer Windows.
# Ausfuehren:  Rechtsklick -> "Mit PowerShell ausfuehren"
#           oder in einer PowerShell:  ./bootstrap.ps1
#
# Macht alles Noetige und startet zum Schluss den Text-Modus zum Testen.

$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $here

function Info($m){ Write-Host "`n>> $m" -ForegroundColor Cyan }
function Warn($m){ Write-Host "!! $m" -ForegroundColor Yellow }

# 1) Python pruefen
Info "Pruefe Python ..."
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Warn "Python fehlt. Bitte installieren: https://www.python.org/downloads/ (Haken 'Add to PATH')."
    exit 1
}
python --version

# 2) Abhaengigkeiten
Info "Installiere Python-Abhaengigkeiten (kann ein paar Minuten dauern) ..."
python -m pip install --upgrade pip | Out-Null
python -m pip install -r requirements.txt

# 3) Ollama + Modell
Info "Pruefe Ollama ..."
if (Get-Command ollama -ErrorAction SilentlyContinue) {
    $model = "qwen2.5:7b-instruct"
    Info "Lade Modell $model (einmalig, mehrere GB) ..."
    ollama pull $model
} else {
    Warn "Ollama nicht gefunden. Installiere es von https://ollama.com und fuehre danach aus:"
    Warn "    ollama pull qwen2.5:7b-instruct"
}

# 4) Konfiguration
if (-not (Test-Path "config.json")) {
    Copy-Item "config.example.json" "config.json"
    Info "config.json angelegt. Bitte oeffnen und ElevenLabs-Key + Stadt eintragen."
    Warn "Ohne ElevenLabs-Key spricht Jarvis mit der Windows-Stimme (funktioniert trotzdem)."
} else {
    Info "config.json existiert bereits."
}

# 5) Optionaler Autostart
$ans = Read-Host "Soll Jarvis mit Windows starten? (j/n)"
if ($ans -eq "j") { ./install_autostart.ps1 }

# 6) Erster Test im Text-Modus (kein Mikrofon noetig)
Info "Starte den Text-Modus zum Testen. Tippe z. B.: Was steht heute an?  (Beenden: 'exit')"
python -m jarvis.main --text
