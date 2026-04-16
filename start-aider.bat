@echo off
setlocal enabledelayedexpansion
echo 🚀 Aider + DeepSeek Starter

REM Conda aider prufen
conda info --envs | findstr /C:"aider" >nul
if errorlevel 1 ( echo [ERROR] conda create -n aider python=3.11 && pause && exit )

REM Aktivieren
call conda activate aider

REM Key aus Umgebung oder Eingabe
if not defined DEEPSEEK_API_KEY (
    set /p DEEPSEEK_API_KEY="DeepSeek Key: "
)

REM Git prufen
git rev-parse --git-dir >nul 2>&1
if errorlevel 1 (
    git init
    echo "# AI Project" > README.md
    git add . && git commit -m "AI Init"
)

REM Aider starten
aider --model deepseek/deepseek-chat --edit-format whole --map-tokens 4096

pause