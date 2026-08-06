# Safe Signal Trader v2

Modular, safety-first Telegram signal trading bot for futures.

**Status:** ▶ **Phase 2 – Source Registry + Parser + Ingestion Pipeline**  
**Python:** ≥ 3.12  
**Stack:** asyncio · Pydantic v2 · SQLAlchemy 2 async · Alembic · PostgreSQL · FastAPI · Jinja2 · structlog

> **Wichtig:** Kein Exchange-Live-Code, keine Live-Verbindungen. Live-Trading ist standardmäßig **aus** und braucht explizite Freigabe + Startup-Gate.

Architektur: [ARCHITECTURE.md](./ARCHITECTURE.md) · Roadmap: [docs/ROADMAP.md](./docs/ROADMAP.md) · ADRs: [docs/adr/](./docs/adr/)

---

## Quick Start (Windows)

1. Python 3.12+ installieren (Haken bei **Add Python to PATH**)
2. Repo klonen / herunterladen
3. Doppelklick auf **`start.bat`**

Beim ersten Start:
- wird `.venv` angelegt
- Dependencies werden installiert (kann 1–2 Minuten dauern)
- der Server startet

Dann im Browser öffnen:

| URL | Inhalt |
|-----|--------|
| http://127.0.0.1:8000/ | **Dashboard (Web-Oberfläche)** |
| http://127.0.0.1:8000/docs | OpenAPI Docs |
| http://127.0.0.1:8000/health | Health JSON |
| http://127.0.0.1:8000/status | Status JSON |

Stoppen: `Ctrl+C` im Fenster.

### Manuell (Terminal)

```bat
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
copy .env.example .env
set PYTHONPATH=%CD%\src
python -m signal_bot serve --host 127.0.0.1 --port 8000
```

### Linux / macOS

```bash
./start.sh
# oder:
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
PYTHONPATH=src python -m signal_bot serve --host 127.0.0.1 --port 8000
```

---

## Was die Web-Oberfläche zeigt

- Service-Status (Online / Offline)
- Environment (`UNIT` / …)
- Live-Trading-Gate (standardmäßig OFF)
- Komponenten-Status (API, Config, Adapters, Queue, **Parsers**, **Source Registry**, **Ingestion**)
- Links zu Docs / Health / Status

---

## Projektstruktur

```
src/signal_bot/
├── api/
│   ├── dashboard.py      # Web-UI /
│   ├── health.py         # /health /ready /status
│   └── templates/        # HTML Dashboard
├── config/               # Settings + Live-Gate
├── domain/               # Models & Enums
├── parsers/              # SignalParser Protocol + Registry + GenericStructured
├── sources/              # SourceConfig + SourceRegistry
├── ingestion/            # RawInboundMessage + Dedup + Pipeline (kein Exchange)
├── adapters/             # Exchange Protocols (keine Impl.)
├── infrastructure/       # DB, Logging, Queue
├── main.py
└── __main__.py           # python -m signal_bot serve
```

---

## Tests

```bash
pytest tests/unit -v
```

Aktuell: **54+** Unit-Tests (Domain, Config, Health, Dashboard, Adapters, Queue, **Parsers Golden**, **Source Registry**, **Ingestion Pipeline + Dedup**).

---

## Roadmap

| Phase | Status |
|-------|--------|
| 1 Foundation + Web-UI | ✅ erledigt |
| 2 Source + Parser + Ingestion | **▶ wir sind hier** |
| 3 Profiles + Snapshots | offen |
| 4 Queue + State-Machine | offen |
| 5 Neutral Core | offen |
| 6 Binance + Testnet | offen |

---

## Sicherheit (Kurz)

1. Core exchange-agnostisch  
2. Immutable Config-Snapshots pro Trade  
3. Fremde Orders/Positionen nie anfassen  
4. Kein blinder Retry  
5. Position nie ungeschützt  
6. Live default aus  

## Lizenz

MIT (vorläufig)
