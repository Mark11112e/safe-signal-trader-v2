#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if [[ ! -d .venv ]]; then python3 -m venv .venv; fi
source .venv/bin/activate
pip install -e ".[dev]" -q
[[ -f .env ]] || cp .env.example .env
echo "Starting FastAPI..."
python -m signal_bot serve
