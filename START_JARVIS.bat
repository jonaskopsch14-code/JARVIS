@echo off
REM JARVIS V6 - Doppelklick-Starter fuer Windows.
REM Startet die Web-Oberflaeche und oeffnet sie im Browser.
REM Dieses Fenster offen lassen, solange JARVIS laufen soll.

title JARVIS V6
cd /d "%~dp0jarvis_v6"
if errorlevel 1 (
  echo [FEHLER] Ordner jarvis_v6 nicht gefunden neben dieser Datei.
  pause
  exit /b 1
)

set "PY="
where py >nul 2>&1 && set "PY=py -3"
if not defined PY where python >nul 2>&1 && set "PY=python"
if not defined PY (
  echo [FEHLER] Python ist nicht installiert.
  echo Bitte installieren: https://www.python.org/downloads/
  echo Beim Installieren "Add python.exe to PATH" anhaken, dann erneut starten.
  pause
  exit /b 1
)

if not defined JARVIS_WEB_PORT set "JARVIS_WEB_PORT=8765"
set "PYTHONIOENCODING=utf-8"

echo.
echo ================================================
echo   JARVIS V6 startet ...
echo   Browser: http://127.0.0.1:%JARVIS_WEB_PORT%
echo   Dieses Fenster OFFEN lassen!
echo ================================================
echo.

REM Browser nach kurzer Wartezeit oeffnen (Server braucht einen Moment).
start "" /b cmd /c "timeout /t 3 >nul & start http://127.0.0.1:%JARVIS_WEB_PORT%"

%PY% webapp.py

echo.
echo JARVIS wurde beendet (oder ist mit einem Fehler abgestuerzt, siehe oben).
pause
