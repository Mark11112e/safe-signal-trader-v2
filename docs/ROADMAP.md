# Roadmap – Safe Signal Trader v2

**Wahrheit für Fortschritt.** Jeder Lauf aktualisiert den Marker „▶ wir sind hier“.

## Phasenübersicht

| Phase | Inhalt | Status |
|-------|--------|--------|
| **1** | **Foundation:** Scaffold, Models, Config, DB+Alembic, Tests, Logging, Queue-Basis, **Web-Dashboard + start.bat** | ✅ erledigt |
| **2** | **Source Registry + Parser Framework + Ingestion Pipeline + Telegram-Skeleton** | ✅ erledigt |
| **3** | **Profiles + Effective Config Snapshots** | ✅ erledigt |
| **4** | **Queue Worker + State-Machine (Claim/Lease/Heartbeat)** | ✅ erledigt |
| **5** | **Neutral Core (Risk / Entry / Position / Protection / Conflict)** | ✅ erledigt |
| **6** | Binance Adapter + Testnet (erster Live-Pfad) | **▶ wir sind hier (nächste)** |
| 7 | Multi-Source parallel | offen |
| 8 | BingX Adapter | offen |
| 9 | WEEX / BloFin Adapter | offen |
| 10 | Control Bot (read-only → writes mit Auth) | offen |
| 11 | Partials + Advanced Trailing / Scale-in | offen |

## Phase 2 – Acceptance (abgeschlossen)

- [x] SignalParser Protocol + Registry + GenericStructured + Golden-Tests
- [x] SourceConfig + SourceRegistry
- [x] Ingestion Pipeline + Dedup (kein Exchange)
- [x] Telegram-Listener-Skelett (gated OFF, kein Netz)

## Phase 3 – Acceptance

- [x] TradingProfile (frozen, versioniert)
- [x] ProfileRegistry + Default-Profile
- [x] build_snapshot → EffectiveConfigSnapshot + stabiler config_hash
- [x] Unit-Tests

## Phase 4 – Acceptance

- [x] InMemoryJobQueue: enqueue, claim, heartbeat, complete, fail, recover_expired
- [x] Idempotenz über client_order_id
- [x] max_attempts → MANUAL_REVIEW
- [x] Unit-Tests Claim/Lease/Recovery

## Phase 5 – Acceptance

- [x] RiskEngine (limits, lev-cap, exposure, qty + SymbolRules)
- [x] EntryPlanner (deterministische clientOrderIds, late-entry block)
- [x] ProtectionPlanner (safer-stop, never worsen, break-even after TP)
- [x] ConflictResolver (reject_second, scale-in, opposite block, priority, manual_review)
- [x] TradeStateMachine (gültige Übergänge)
- [x] Unit-Tests für alle Core-Module (+ Profiles + Queue Memory)
- [x] Kein Exchange-Live-Code, keine echten Netzcalls

## Nächster Schritt (Phase 6)

Binance Adapter (Testnet) hinter Adapter-Contract, Startup-Gate, No-Network-Guard in Unit-Tests, erster kontrollierter Live-Pfad.
