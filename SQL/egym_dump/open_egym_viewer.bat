@echo off
setlocal
cd /d "%~dp0"
python view_egym_sql.py
if errorlevel 1 (
  echo.
  echo Fehler beim Starten. Ist Python installiert?
  pause
)
