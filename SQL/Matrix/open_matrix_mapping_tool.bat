@echo off
setlocal
cd /d "%~dp0"
python build_matrix_mapping_tool.py
if errorlevel 1 (
  echo Fehler beim Erzeugen des Mapping-Tools.
  pause
  exit /b 1
)
start "" "matrix_image_mapper.html"
