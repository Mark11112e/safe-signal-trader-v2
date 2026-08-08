# ADR-0003: Binance Adapter first (Testnet + Mock)

**Datum:** 2026-08-08  
**Status:** Accepted  

## Kontext

Phase 6 beginnt. Erster Exchange-Pfad soll Binance USD-M Futures sein (Referenz laut Auftrag).

## Entscheidung

1. **Mock zuerst:** `MockBinanceAdapter` implementiert alle Adapter-Protocols vollständig in-memory, **ohne jegliche Netzcalls**. Ermöglicht Unit-Tests, Offline-Demo und Simulation unter `APP_ENV=TESTNET_DEMO`.
2. **Capabilities:** `BinanceCapabilities` als frozen Dataclass, exchange_id = `binance_futures`.
3. **Echter HTTP-Client später:** Nur hinter explizitem Gate (`APP_ENV=TESTNET_DEMO` oder `LIVE` + `LIVE_TRADING_ENABLED=true` + Startup-Gate). Kein Default-Live.
4. **Kein Core-Change:** Core bleibt exchange-agnostisch; Factory/Registry liefert Adapter.
5. **Idempotenz & Safety:** Mock respektiert client_order_id (Idempotent), reduce_only, never-worsen Prinzipien werden in Core getestet.

## Konsequenzen

- Sofort testbar, 0 Netzwerk-Risiko.
- Real Testnet kann in kleinem Folgeschritt (ccxt oder raw httpx + sign) hinzugefügt werden.
- Weitere Exchanges (BingX …) folgen dem gleichen Pattern.
