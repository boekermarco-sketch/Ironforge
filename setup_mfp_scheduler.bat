@echo off
REM ─────────────────────────────────────────────────────────────────────────────
REM  MFP Task Scheduler einrichten – täglich 23:00 Uhr
REM  Einmalig als Administrator ausführen.
REM ─────────────────────────────────────────────────────────────────────────────

set SCRIPT_DIR=%~dp0
set PYTHON_EXE=python
set SCRIPT_PATH=%SCRIPT_DIR%run_mfp_fetch.py
set TASK_NAME=IFL_MFP_DailyFetch

echo Richte Task Scheduler ein...
echo Skript: %SCRIPT_PATH%
echo Zeit:   taeglich 23:00 Uhr

schtasks /create ^
  /tn "%TASK_NAME%" ^
  /tr "\"%PYTHON_EXE%\" \"%SCRIPT_PATH%\"" ^
  /sc DAILY ^
  /st 23:00 ^
  /ru "%USERNAME%" ^
  /f

if %ERRORLEVEL% == 0 (
    echo.
    echo Task "%TASK_NAME%" erfolgreich eingerichtet.
    echo MFP-Daten werden taeglich um 23:00 Uhr abgerufen.
) else (
    echo.
    echo FEHLER beim Einrichten. Bitte als Administrator ausfuehren.
)

echo.
pause
