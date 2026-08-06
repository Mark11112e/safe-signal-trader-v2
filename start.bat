@echo off
setlocal EnableExtensions
cd /d "%~dp0"

title Safe Signal Trader v2
echo.
echo ========================================
echo   Safe Signal Trader v2 - Starting...
echo ========================================
echo.

REM Prefer py launcher (Windows), fall back to python
where py >nul 2>&1
if %ERRORLEVEL%==0 (
  set "PY=py -3"
) else (
  where python >nul 2>&1
  if %ERRORLEVEL%==0 (
    set "PY=python"
  ) else (
    echo [ERROR] Python 3.12+ not found.
    echo Install from https://www.python.org/downloads/
    echo Make sure "Add Python to PATH" is checked.
    pause
    exit /b 1
  )
)

echo [1/4] Python found
%PY% --version
if errorlevel 1 (
  echo [ERROR] Could not run Python.
  pause
  exit /b 1
)

if not exist .venv (
  echo [2/4] Creating virtual environment...
  %PY% -m venv .venv
  if errorlevel 1 (
    echo [ERROR] Failed to create .venv
    pause
    exit /b 1
  )
) else (
  echo [2/4] Virtual environment exists
)

call .venv\Scripts\activate.bat
if errorlevel 1 (
  echo [ERROR] Failed to activate .venv
  pause
  exit /b 1
)

echo [3/4] Installing / updating dependencies (first run can take a minute)...
python -m pip install --upgrade pip -q
python -m pip install -e ".[dev]" -q
if errorlevel 1 (
  echo [ERROR] pip install failed. Check output above.
  pause
  exit /b 1
)

if not exist .env (
  copy .env.example .env >nul
  echo Created .env from .env.example
)

set PYTHONPATH=%CD%\src;%PYTHONPATH%

echo [4/4] Starting web app...
echo.
echo   Dashboard : http://127.0.0.1:8000/
echo   Health    : http://127.0.0.1:8000/health
echo   API Docs  : http://127.0.0.1:8000/docs
echo.
echo Press Ctrl+C to stop.
echo ========================================
echo.

python -m signal_bot serve --host 127.0.0.1 --port 8000
if errorlevel 1 (
  echo.
  echo [ERROR] Server exited with an error.
  pause
  exit /b 1
)
pause
