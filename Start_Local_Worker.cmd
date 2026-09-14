@echo off
cd /d "%~dp0"
py -3.10 app\server.py --port 18765
pause
