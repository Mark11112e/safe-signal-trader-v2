# Roadmap – Safe Signal Trader v2

**Wahrheit für Fortschritt.** Jeder Lauf aktualisiert den Marker „▶ wir sind hier“.

## Phasenübersicht

| Phase | Inhalt | Status |
|-------|--------|--------|
| **1** | **Foundation:** Scaffold, Models, Config, DB+Alembic, Tests, Logging, Queue-Basis, **Web-Dashboard + start.bat** | **▶ wir sind hier** |
| 2 | Source Registry + Parser Framework | offen |
| 3 | Profiles + Effective Config Snapshots | offen |
| 4 | Queue Worker + State-Machine (Claim/Lease/Heartbeat) | offen |
| 5 | Neutral Core (Risk / Entry / Position / Protection) | offen |
| 6 | Binance Adapter + Testnet (erster Live-Pfad) | offen |
| 7 | Multi-Source parallel | offen |
| 8 | BingX Adapter | offen |
| 9 | WEEX / BloFin Adapter | offen |
| 10 | Control Bot (read-only → writes mit Auth) | offen |
| 11 | Partials + Advanced Trailing / Scale-in | offen |

## Phase 1 – Acceptance Criteria

- [x] Repo-Struktur + pyproject.toml (Python ≥3.12)
- [x] Domain-Modelle (NormalizedSignal, Snapshot, Trade, OrderJob, …)
- [x] Adapter-Interfaces (Protocols, keine Implementierungen)
- [x] SQLAlchemy 2 async Modelle + Alembic vorbereitet
- [x] Config + Live-Trading-Gate (default aus)
- [x] JSON-Logging + Correlation-ID
- [x] FastAPI Health / Ready / Status / Docs
- [x] Web-Dashboard unter `/` (HTML UI)
- [x] start.bat + start.sh + `python -m signal_bot serve`
- [x] Docker-Compose Postgres
- [x] .env.example ohne Secrets
- [x] Unit-Tests (Domain, Config, Health, Adapters, Queue-Helpers)
- [x] ARCHITECTURE.md + ADRs + diese ROADMAP
- [x] Kein Exchange-Live-Code, keine echten Netzcalls

## Nächster Schritt (Phase 2)

Source Registry + Parser-Interface (`can_parse` / `parse` / `validate`) mit Golden-Tests.
