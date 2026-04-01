@echo off
echo ============================================
echo  Fitness Dashboard von Marco Boeker
echo ============================================
echo.

:: Alten Prozess auf Port 8080 beenden falls noch einer laeuft
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8080 " ^| findstr "LISTENING" 2^>nul') do (
    taskkill /PID %%a /F >nul 2>&1
)

echo Starte Server...
echo Oeffne Browser: http://localhost:8080
echo.
echo Zum Beenden: Strg+C druecken
echo.
cd /d "%~dp0"
start "" http://localhost:8080
python -m uvicorn app.main:app --host 127.0.0.1 --port 8080
pause
