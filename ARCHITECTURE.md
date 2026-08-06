# Zielarchitektur – Modular Telegram Signal Trading Bot

**Stand:** 06.08.2026  
**Rolle:** Lead Software Architect & Senior Python Engineer  
**Status:** Phase 0 – Architektur & Scaffold (keine Exchange-Implementierung, keine Live-Verbindungen)

Dieses Dokument erfüllt den ersten Arbeitsauftrag und dient als verbindliche Grundlage für alle weiteren PRs. Alle Entscheidungen sind nachvollziehbar dokumentiert (siehe auch `docs/adr/`).

---

## 1. Zielarchitektur + Datenflüsse

### 1.1 High-Level Komponenten

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────────┐
│  Telegram       │     │  Control Bot     │     │  FastAPI            │
│  Sources        │     │  (Bot-API)       │     │  (Health/Status)    │
│  (Telethon)     │     │  read-only zuerst│     │                     │
└────────┬────────┘     └────────┬─────────┘     └──────────┬──────────┘
         │                       │                          │
         ▼                       ▼                          ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        Core Application (asyncio)                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │
│  │ Ingestion    │→ │ Parser       │→ │ Validation / │               │
│  │ (parallel,   │  │ Registry     │  │ Routing +    │               │
│  │  Dedup)      │  │ (versioned)  │  │ Snapshot     │               │
│  └──────────────┘  └──────────────┘  └──────┬───────┘               │
│                                             │                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────▼───────┐               │
│  │ Risk Engine  │← │ Entry Engine │← │ Order Job     │               │
│  │ (neutral)    │  │              │  │ Worker        │               │
│  └──────────────┘  └──────────────┘  └──────┬───────┘               │
│                                             │                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────▼───────┐               │
│  │ Position     │← │ Protection   │← │ Adapter      │               │
│  │ Manager      │  │ Engine       │  │ Layer        │               │
│  │ (State-Mach.)│  │              │  │ (Contracts)  │               │
│  └──────────────┘  └──────────────┘  └──────┬───────┘               │
│                                             │                        │
│  ┌──────────────┐                           │                        │
│  │ Reconciliation│ ←────────────────────────┘                        │
│  │ + Watchdog   │                                                    │
│  └──────────────┘                                                    │
└─────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────┐     ┌──────────────────┐
│  PostgreSQL     │     │  Exchanges       │
│  (Queue + State │     │  (via Adapters)  │
│   + Snapshots)  │     │  Binance → ...   │
└─────────────────┘     └──────────────────┘
```

### 1.2 Datenflüsse (kritische Pfade)

1. **Signal-Ingestion**  
   Telegram-Nachricht → Dedup (message_id + source_id + edit_date) → `signal_messages` (raw + metadata) → Parser aufrufen (nur wenn `can_parse`).

2. **Parsing & Validation**  
   `NormalizedSignal` (symbol, side, entry, SL, TPs[1-5], leverage, parser_version, content_hash) → Symbol-Normalisierung → Limits prüfen → `effective_config_snapshot` erzeugen (immutable + Hash + schema_version) → atomar speichern in `parsed_signals` + Snapshot.

3. **Risk → Entry**  
   Risk Engine (neutral, nur Snapshot) entscheidet Size/Leverage/Safer-SL → Entry Engine erzeugt deterministische `client_order_id` → Order Job in Queue (SELECT FOR UPDATE SKIP LOCKED).

4. **Order Job Worker**  
   Claim mit Lease + Heartbeat → Adapter.submit (idempotent) → bei unklarer Antwort: `manual_review`, **kein blinder Retry**.

5. **Position Lifecycle**  
   Fill → `managed_positions` (State-Machine) → Protection Engine (initial Stop) → TP-Stages / Trailing aus Snapshot → Partials optional → Archive + PnL.

6. **Reconciliation (periodisch + on-reconnect)**  
   DB ↔ Exchange (nur bot-owned Orders/Positions) → missing/stale/ambiguous → `manual_review` oder single-symbol confirm (bei Zero).

7. **Control Bot**  
   Read-only Queries auf Health, Trades, Jobs, Reviews, PnL, Status. Später Writes nur mit Auth + Confirm + Audit + Idempotency.

**Wichtige Invariante:** Aktive Trades ändern ihr Verhalten **niemals** durch Config-Updates. Nur der `effective_config_snapshot` zum Trade-Zeitpunkt gilt.

---

## 2. Repo-Struktur

```
safe-signal-trader/
├── ARCHITECTURE.md              # Dieses Dokument
├── README.md
├── pyproject.toml               # Python ≥3.12, deps, tool configs
├── Dockerfile
├── docker-compose.yml           # Postgres + App (dev)
├── .env.example
├── .gitignore
├── alembic.ini
├── alembic/
│   └── versions/
├── docs/
│   └── adr/                     # Architecture Decision Records
├── src/
│   └── signal_bot/
│       ├── __init__.py
│       ├── main.py              # Entry point (uvicorn + workers)
│       ├── config/              # Pydantic Settings + Source/Profile loading
│       ├── domain/
│       │   ├── models/          # Domain entities (Pydantic + SQLAlchemy)
│       │   ├── signals/         # NormalizedSignal, Parser contracts
│       │   ├── risk/
│       │   ├── entry/
│       │   ├── position/        # State machine
│       │   ├── protection/
│       │   └── reconciliation/
│       ├── adapters/            # Exchange Adapter Interfaces + later implementations
│       ├── infrastructure/
│       │   ├── db/              # SQLAlchemy async, session, models
│       │   ├── logging/         # Structured JSON + Correlation-ID
│       │   ├── queue/           # PG-based job queue (SKIP LOCKED + Lease)
│       │   └── observability/   # Metrics, Health
│       ├── services/            # Application services (orchestration)
│       ├── api/                 # FastAPI routes (health, status)
│       └── control/             # Control-Bot (Telethon/Bot-API)
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── golden/                  # Signal golden files
│   ├── conformance/             # Adapter conformance tests
│   └── conftest.py
└── scripts/
```

**Prinzipien der Struktur:**
- Core kennt **keine** exchange-spezifischen Felder.
- Jede Exchange nur über Adapter-Contract.
- Domain-Modelle sind exchange-agnostisch.
- Tests liegen parallel und nutzen keine echten Netzaufrufe.

---

## 3. Domain Models + Adapter Interfaces

Siehe Source-Code unter `src/signal_bot/domain/models/` und `src/signal_bot/adapters/interfaces.py`.

Kern-Modelle: NormalizedSignal, EffectiveConfigSnapshot (immutable + Hash), Trade, ManagedPosition, OrderJob, ManualReview, SymbolRules.

Adapter-Contracts: MarketDataAdapter, AccountAdapter, ExecutionAdapter, ProtectionAdapter, StreamingAdapter, PnLAdapter, ExchangeCapabilities.

---

## 4. PostgreSQL-Modell (high-level)

Tabellen: signal_sources, signal_messages (Dedup), parsed_signals, exchange_accounts, profiles (versioniert), effective_config_snapshots (immutable), trades, order_jobs (Queue + Lease), manual_reviews, …

Queue: SELECT FOR UPDATE SKIP LOCKED + Lease + Heartbeat.

---

## 5. Config-Struktur

Sources → Account-Ref + Profile-IDs + Conflict-Policy + Limits.
Profiles versioniert & immutable.
TP: 1–5 Levels, last_tp.mode = trailing|take_profit|none.
Default: max Loss ≈10 USDT, TP1 break-even, Last TP Trailing, keine Auto-Partials.

---

## 6. Safety-Invarianten

1–12 wie im Auftrag. Zusätzlich: Live default aus, Control-Bot read-only, kein blinder Retry, Position nie ungeschützt.

---

## 7. Detaillierte kleine-PR-Roadmap

Phase 1 (dieses PR): Scaffold, Models, Config, DB, Logging, Health, Tests.
Phase 2–11: Source+Parser → Profiles+Snapshots → Queue → Neutral Core → Binance Adapter → Multi-Source → BingX → WEEX/BloFin → Control Bot → Partials.

Jeder PR: Branch, Tests zuerst, Draft-PR, Self-Review, kein Auto-Merge.

---

## 8. Acceptance Criteria Phase 1

- [x] Repo auf GitHub
- [x] pyproject.toml Python ≥3.12 + deps
- [x] Domain-Modelle + Unit-Tests
- [x] Adapter Interfaces (keine Implementierungen)
- [x] SQLAlchemy + Alembic Migration
- [x] Config + Live-Gate
- [x] JSON-Logging + Correlation-ID
- [x] FastAPI Health/Ready
- [x] Docker-Compose Postgres
- [x] .env.example ohne Secrets
- [x] 20 Unit-Tests grün, keine Netzaufrufe
- [x] ARCHITECTURE.md + 2 ADRs
- [x] Kein Exchange-Code, keine Live-Verbindung

---

## 9. Offene Entscheidungen (mit Begründung)

Siehe Tabelle in vollständiger ARCHITECTURE.md (Queue=PG, Default Conflict=reject_second, Live default aus, etc.).

---

## 10. Non-Goals aktueller Stand

Kein Exchange-Code, keine Live-/Testnet-Verbindungen, keine Credentials im Repo, keine Worker-Implementierung, keine Control-Bot-Writes.
