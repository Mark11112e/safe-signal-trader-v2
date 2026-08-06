# Safe Signal Trader

Modular, safety-first Telegram signal trading bot.

**Status:** Phase 1 – Foundation (Scaffold only)  
**Python:** ≥ 3.12  
**Stack:** asyncio · Pydantic v2 · SQLAlchemy 2 async · Alembic · PostgreSQL · FastAPI · structlog

> **Wichtig:** Dieses Repository enthält **keinen** Exchange-Code und stellt **keine** Live-Verbindungen her. Live-Trading ist standardmäßig deaktiviert und erfordert explizite Freigabe + Startup-Gate.

## Architektur

Siehe [ARCHITECTURE.md](./ARCHITECTURE.md) für die vollständige Zielarchitektur, Datenflüsse, Safety-Invarianten und Roadmap.

Architecture Decision Records liegen unter [`docs/adr/`](./docs/adr/).

## Quick Start (Development)

```bash
# 1. Clone
git clone https://github.com/Mark11112e/safe-signal-trader-v2.git
cd safe-signal-trader-v2

# 2. Python environment
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# 3. Environment
cp .env.example .env
# .env anpassen (mindestens DATABASE_URL)

# 4. Database
docker compose up -d postgres
alembic upgrade head

# 5. Tests
pytest -m unit
# oder: PYTHONPATH=src pytest tests/unit -v

# 6. Health endpoint (optional)
uvicorn signal_bot.main:app --reload
# → http://localhost:8000/health
```

## Projektstruktur

```
src/signal_bot/
├── config/          # Pydantic Settings
├── domain/          # Domain models, Risk, Entry, Position, Protection, …
├── adapters/        # Exchange Adapter Interfaces (Contracts)
├── infrastructure/  # DB, Logging, Queue, Observability
├── services/        # Application services
├── api/             # FastAPI
└── control/         # Control-Bot (read-only in early phases)
```

## Safety Principles (Kurzfassung)

1. Core ist exchange-agnostisch.
2. Jeder Trade speichert einen unveränderlichen Config-Snapshot.
3. Fremde Orders/Positionen werden nie angefasst.
4. Kein blinder Retry bei unklaren Exchange-Antworten.
5. Positionen bleiben nie ungeschützt.
6. Live-Trading ist standardmäßig aus.

Vollständige Liste siehe ARCHITECTURE.md §6.

## Entwicklung

- **Nie** direkt auf `main` committen.
- Branch → kleine PRs → Tests → Draft-PR.
- PR-Template: Summary / Why / Scope / Non-goals / Safety / DB-Impact / Tests / Risks / Rollback.
- Alle wichtigen Entscheidungen als ADR dokumentieren.

## Lizenz

MIT (vorläufig)
