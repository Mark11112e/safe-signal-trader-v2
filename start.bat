@echo off
setlocal
cd /d "%~dp0"
if not exist .venv python -m venv .venv
call .venv\Scripts\activate.bat
pip install -e ".[dev]" -q
if not exist .env copy .env.example .env
echo Starting FastAPI...
python -m signal_bot serve
