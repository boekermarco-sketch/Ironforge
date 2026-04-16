@echo off
echo ============================================
echo  Fitness Dashboard von Marco Boeker
echo ============================================
echo.

:: Alte Python-Prozesse beenden
echo Beende alte Server-Prozesse...
taskkill /IM python.exe /F >nul 2>&1
taskkill /IM python3.exe /F >nul 2>&1
timeout /t 2 /nobreak >nul

cd /d "%~dp0"

:: .env laden
if exist ".env" (
    for /f "usebackq tokens=1,* delims==" %%A in (".env") do set "%%A=%%B"
)

echo Starte Server...
echo Oeffne Browser: http://localhost:8080
echo.
echo Daten abrufen: http://localhost:8080/import/
echo Zum Beenden:   Strg+C druecken
echo.

:: Browser nach 3 Sekunden im Hintergrund oeffnen
start /min "" cmd /c "timeout /t 3 /nobreak >nul && start http://localhost:8080"

:: Server im Vordergrund starten (Logs sichtbar)
python -m uvicorn app.main:app --host 127.0.0.1 --port 8080 --reload
pause
