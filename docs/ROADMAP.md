# Roadmap – Safe Signal Trader v2

**Wahrheit für Fortschritt.** Jeder Lauf aktualisiert den Marker „▶ wir sind hier“.

## Phasenübersicht

| Phase | Inhalt | Status |
|-------|--------|--------|
| **1** | **Foundation:** Scaffold, Models, Config, DB+Alembic, Tests, Logging, Queue-Basis, **Web-Dashboard + start.bat** | ✅ erledigt |
| **2** | **Source Registry + Parser Framework + Ingestion Pipeline** | **▶ wir sind hier** |
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

## Phase 2 – Acceptance Criteria (aktueller Lauf)

- [x] `SignalParser` Protocol (`can_parse` / `parse` / `validate`)
- [x] `ParserRegistry` + Default-Registry
- [x] `GenericStructuredParser` v1.0.0 (deterministisch, Golden-Tests)
- [x] Golden-Tests: 1–5 TPs, malformed, market/limit, size_pct, Symbol-Norm
- [x] `SourceConfig` Domain-Model (frozen)
- [x] `SourceRegistry` (in-memory, enable/disable, example seed)
- [x] Status/Dashboard zeigen Phase 2 + Parser/Source-Komponenten
- [x] **Ingestion Pipeline + Dedup** (RawInboundMessage → NormalizedSignal, kein Exchange)
- [x] Parser an Source gebunden (source.parser_id → ParserRegistry)
- [x] Unit-Tests Ingestion: happy path, duplicate, disabled, unknown, garbage, hash (54+)
- [ ] Telegram-Listener (Telethon) Skelett – nächster kleiner Schritt
- [ ] Persistente Source-Registry aus DB

## Nächster Schritt

Telegram-Listener-Skelett (reconnect-safe, gated, kein Auto-Start in `serve`) + optional DB-persistierte Sources; danach Phase 3 Profiles/Snapshots.
