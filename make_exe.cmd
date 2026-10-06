@echo off
setlocal
cd /d "%~dp0"

set "BUILD_PYTHON=python"
if not "%~1"=="" set "BUILD_PYTHON=%~1"

"%BUILD_PYTHON%" -m PyInstaller app.py --clean -F -n MinGui-youtube-dl --add-data "amanita_logo_16x16.png;." --add-data "assets/amanita_banner.txt;assets"
if errorlevel 1 exit /b 1

xcopy "docs\*.md" "dist\docs\" /I /Y
if errorlevel 1 exit /b 1

copy /Y ".settings.example.json" "dist\.settings.example.json" >nul
if errorlevel 1 exit /b 1

echo Build ready: dist\MinGui-youtube-dl.exe
