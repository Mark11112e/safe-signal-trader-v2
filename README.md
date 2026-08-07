# Safe Signal Trader v2

Modular, safety-first Telegram signal trading bot for futures.

**Status:** ✅ **Phase 5 complete** – Neutral Core + Tests · **Next: Phase 6 Binance Testnet**  
**Python:** ≥ 3.12  
**Stack:** asyncio · Pydantic v2 · SQLAlchemy 2 async · Alembic · PostgreSQL · FastAPI · Jinja2 · structlog

> **Wichtig:** Kein Exchange-Live-Code, keine Live-Verbindungen. Live-Trading ist standardmäßig **aus** und braucht explizite Freigabe + Startup-Gate.

Architektur: [ARCHITECTURE.md](./ARCHITECTURE.md) · Roadmap: [docs/ROADMAP.md](./docs/ROADMAP.md) · ADRs: [docs/adr/](./docs/adr/)

---

## Quick Start (Windows)

1. Python 3.12+ installieren (Haken bei **Add Python to PATH**)
2. Repo klonen / herunterladen
3. Doppelklick auf **`start.bat`**

Dann im Browser:

| URL | Inhalt |
|-----|--------|
| http://127.0.0.1:8000/ | **Dashboard** |
| http://127.0.0.1:8000/docs | OpenAPI Docs |
| http://127.0.0.1:8000/health | Health JSON |
| http://127.0.0.1:8000/status | Status JSON |

### Linux / macOS

```bash
./start.sh
# oder: PYTHONPATH=src python -m signal_bot serve --host 127.0.0.1 --port 8000
```

---

## Projektstruktur

```
src/signal_bot/
├── api/            # Dashboard + Health/Status
├── config/         # Settings + Live-Gate
├── domain/         # Models & Enums
├── parsers/        # SignalParser + Registry + GenericStructured
├── sources/        # SourceConfig + Registry
├── ingestion/      # Pipeline + Dedup + Telegram-Skeleton
├── profiles/       # TradingProfile + Snapshot-Builder
├── core/           # Risk · Entry · Protection · Conflict · Position-SM
├── adapters/       # Exchange Protocols (keine Impl. vor Phase 6)
├── infrastructure/ # DB · Logging · Job-Queue (claim/lease)
├── main.py
└── __main__.py
```

---

## Tests

```bash
pytest tests/unit -v
```

**91 Unit-Tests** (Domain, Config, Health, Parsers, Sources, Ingestion, Profiles, Queue, Core Risk/Entry/Protection/Conflict/SM).

---

## Roadmap

| Phase | Status |
|-------|--------|
| 1 Foundation + Web-UI | ✅ |
| 2 Source + Parser + Ingestion | ✅ |
| 3 Profiles + Snapshots | ✅ |
| 4 Queue + State-Machine | ✅ |
| 5 Neutral Core | ✅ |
| 6 Binance + Testnet | **▶ nächste** |

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
