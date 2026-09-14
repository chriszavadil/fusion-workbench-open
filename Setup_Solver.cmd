@echo off
cd /d "%~dp0"
py -3.10 tools\setup_solver.py --install
pause
