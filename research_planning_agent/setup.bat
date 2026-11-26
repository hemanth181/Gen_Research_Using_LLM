@echo off
setlocal
cd /d "%~dp0"
echo [1/4] Checking Python...
where py >nul 2>nul
if errorlevel 1 (
  echo Python launcher not found. Install Python 3.11 or 3.12 from https://www.python.org/downloads/ and enable Add Python to PATH.
  pause
  exit /b 1
)
py -3.11 --version >nul 2>nul
if errorlevel 1 (
  py -3.12 --version >nul 2>nul
  if errorlevel 1 (
    echo Please install Python 3.11 or 3.12.
    pause
    exit /b 1
  ) else (set PYVER=3.12)
) else (set PYVER=3.11)
if not exist .venv (
  echo [2/4] Creating virtual environment...
  py -%PYVER% -m venv .venv
)
echo [3/4] Upgrading pip and installing requirements...
call .venv\Scripts\python.exe -m pip install --upgrade pip
if errorlevel 1 goto failed
call .venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto failed
if not exist .env copy .env.example .env >nul
echo [4/4] Setup complete. Edit .env if you want to configure a real LLM.
echo Next: double-click run.bat
pause
exit /b 0
:failed
echo Installation failed. Check the error above and your internet connection.
pause
exit /b 1
