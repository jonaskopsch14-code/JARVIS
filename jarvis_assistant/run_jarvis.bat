@echo off
REM Jarvis starten (Sprach-Modus). Fuer den Text-Modus: run_jarvis.bat --text
cd /d "%~dp0"
python -m jarvis.main %*
pause
