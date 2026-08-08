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
| **6** | Binance Adapter + Testnet (erster Live-Pfad) | **▶ wir sind hier** (Mock + Capabilities + Tests erledigt; real Testnet Client folgt) |
| 7 | Multi-Source parallel | offen |
| 8 | BingX Adapter | offen |
| 9 | WEEX / BloFin Adapter | offen |
| 10 | Control Bot (read-only → writes mit Auth) | offen |
| 11 | Partials + Advanced Trailing / Scale-in | offen |

## Phase 5 – Acceptance (abgeschlossen)

- [x] RiskEngine (limits, lev-cap, exposure, qty + SymbolRules)
- [x] EntryPlanner (deterministische clientOrderIds, late-entry block)
- [x] ProtectionPlanner (safer-stop, never worsen, break-even after TP)
- [x] ConflictResolver (reject_second, scale-in, opposite block, priority, manual_review)
- [x] TradeStateMachine (gültige Übergänge)
- [x] Unit-Tests für alle Core-Module (+ Profiles + Queue Memory)
- [x] Kein Exchange-Live-Code, keine echten Netzcalls

## Phase 6 – Fortschritt (dieser Lauf)

- [x] `BinanceCapabilities` (exchange_id, user-stream, reduce-only, trailing, hedge, max_lev, replace)
- [x] `MockBinanceAdapter` – vollständige Protocol-Implementierung, **0 Netzwerk**, Idempotenz via client_order_id, Position/Balance/Stop Tracking
- [x] Unit-Tests (Protocol conformance, Market/Account/Execution/Protection/Streaming/PnL, Idempotenz)
- [x] Status/Health aktualisiert auf `6-binance-prep`
- [x] ADR-0003: Binance first + Mock-first
- [ ] Real Binance Testnet HTTP Client (signiert, httpx) + No-Network-Guard + Startup-Gate
- [ ] Adapter-Factory / Registry
- [ ] Erster kontrollierter Testnet-Pfad (gated)

## Nächster kleiner Schritt

Real Testnet Client hinter `APP_ENV=TESTNET_DEMO` + Credential-Refs (Env only) + explicit enable; Unit-Tests mit HTTP-Mocks; kein Live.
