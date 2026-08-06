# Safe Signal Trader v2

Modular, safety-first Telegram signal trading bot for futures.

**Status:** ▶ **Phase 1 – Foundation** (Scaffold)  
**Python:** ≥ 3.12  
**Stack:** asyncio · Pydantic v2 · SQLAlchemy 2 async · Alembic · PostgreSQL · FastAPI · structlog

> **Wichtig:** Dieses Repository enthält **keinen** Exchange-Live-Code und stellt **keine** Live-Verbindungen her. Live-Trading ist standardmäßig deaktiviert und erfordert explizite Freigabe + Startup-Gate.

Vollständige Architektur: [ARCHITECTURE.md](./ARCHITECTURE.md)  
Fortschritt & nächste Schritte: [docs/ROADMAP.md](./docs/ROADMAP.md)  
ADRs: [docs/adr/](./docs/adr/)

---

## Quick Start

```bash
# 1. Clone
git clone https://github.com/Mark11112e/safe-signal-trader-v2.git
cd safe-signal-trader-v2

# 2. Virtualenv + Install
python -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate
pip install -e ".[dev]"

# 3. Environment
cp .env.example .env

# 4. Database (optional für reine Unit-Tests)
docker compose up -d postgres
alembic upgrade head

# 5. Tests
pytest -m unit -v

# 6. Web-App starten
python -m signal_bot serve
# → http://localhost:8000/health
# → http://localhost:8000/docs
# → http://localhost:8000/status

# Windows: start.bat
# Linux/macOS: ./start.sh
```

---

## Projektstruktur

```
src/signal_bot/
├── config/           # Pydantic Settings + Live-Gate
├── domain/           # Enums, Models (NormalizedSignal, Snapshot, Trade, …)
├── adapters/         # Exchange Adapter Interfaces (Protocols only)
├── infrastructure/
│   ├── db/           # SQLAlchemy models, session
│   ├── queue/        # PG SKIP LOCKED claim helpers
│   └── logging.py    # JSON + Correlation-ID
├── api/              # FastAPI Health / Status
├── main.py           # App factory
└── __main__.py       # CLI: python -m signal_bot serve
```

---

## Safety Principles (Kurz)

1. Core ist exchange-agnostisch.  
2. Jeder Trade speichert einen unveränderlichen Config-Snapshot.  
3. Fremde Orders/Positionen werden nie angefasst.  
4. Kein blinder Retry bei unklaren Exchange-Antworten.  
5. Positionen bleiben nie ungeschützt.  
6. Live-Trading ist standardmäßig aus.

Vollständige Liste: ARCHITECTURE.md §2 und ADR-0001.

---

## Roadmap-Marker

| Phase | Status |
|-------|--------|
| 1 Foundation | **▶ wir sind hier** |
| 2 Source + Parser | offen |
| 3 Profiles + Snapshots | offen |
| 4 Queue + State-Machine | offen |
| 5 Neutral Core | offen |
| 6 Binance + Testnet | offen |
| … | siehe docs/ROADMAP.md |

---

## Entwicklung

- Alles auf `main`, kleine Commits.
- Tests first, bestehende Tests grün halten.
- Kein Exchange-Live-Code vor Phase 6.
- Erklärungen DE; Code / IDs / Dateien / Errors EN.

## Lizenz

MIT (vorläufig)
