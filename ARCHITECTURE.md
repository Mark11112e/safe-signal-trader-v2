# Zielarchitektur – Safe Signal Trader v2

**Stand:** 2026-08-06  
**Status:** Phase 1 – Foundation

Siehe [docs/ROADMAP.md](./docs/ROADMAP.md) für Fortschritt.

## 12 Architekturprinzipien

1. Core kennt keine exchange-spezifischen Felder/Codes.
2. Exchange nur über Adapter-Contract.
3. Stabile source_id + versionierte Config pro Quelle.
4. Trade: immutable effective_config_snapshot + Hash + Schema-Version.
5. Keine Credentials in Snapshots/Logs.
6. Aktive Trades ignorieren spätere Config-Updates.
7. Order-Submit idempotent + crash-sicher.
8. Fremde Orders/Positionen nie anfassen.
9. Kein blinder Retry nach unklarer Antwort.
10. Position nie ungeschützt.
11. Nur Tests + kleine Schritte.
12. Production / Demo / Live getrennt.

## Domain + Adapters

Domain-Modelle und Adapter-Protocols liegen unter `src/signal_bot/domain/` und `src/signal_bot/adapters/`.

Live-Trading ist standardmäßig aus. Kein Exchange-Code vor Phase 6.
