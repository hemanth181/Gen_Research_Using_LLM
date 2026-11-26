@echo off
setlocal
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
  echo Dependencies not installed. Run setup.bat first.
  pause
  exit /b 1
)
if not exist .env copy .env.example .env >nul
call .venv\Scripts\python.exe -m streamlit run app\main.py
