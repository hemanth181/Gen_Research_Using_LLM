@echo off
setlocal
cd /d "%~dp0"
if "%~1"=="" (
 echo Usage: run_cli.bat "Your research question"
 pause
 exit /b 1
)
.venv\Scripts\python.exe run_cli.py %*
pause
