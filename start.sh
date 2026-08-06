#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

echo "========================================"
echo "  Safe Signal Trader v2 - Starting..."
echo "========================================"

if ! command -v python3 >/dev/null 2>&1; then
  echo "[ERROR] python3 not found"
  exit 1
fi

echo "[1/4] Python: $(python3 --version)"

if [[ ! -d .venv ]]; then
  echo "[2/4] Creating virtual environment..."
  python3 -m venv .venv
else
  echo "[2/4] Virtual environment exists"
fi

# shellcheck disable=SC1091
source .venv/bin/activate

echo "[3/4] Installing / updating dependencies..."
python -m pip install --upgrade pip -q
python -m pip install -e ".[dev]" -q

[[ -f .env ]] || cp .env.example .env

export PYTHONPATH="${PWD}/src${PYTHONPATH:+:$PYTHONPATH}"

echo "[4/4] Starting web app..."
echo ""
echo "  Dashboard : http://127.0.0.1:8000/"
echo "  Health    : http://127.0.0.1:8000/health"
echo "  API Docs  : http://127.0.0.1:8000/docs"
echo ""
echo "Press Ctrl+C to stop."
echo "========================================"

exec python -m signal_bot serve --host 127.0.0.1 --port 8000
