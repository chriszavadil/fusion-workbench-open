@echo off
cd /d "%~dp0"
py -3.10 tools\build_research_library.py
if errorlevel 1 exit /b 1
echo Reader packets rebuilt. Package the native project to distribute the update.
pause
