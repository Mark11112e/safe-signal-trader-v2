# ADR-0002: PostgreSQL-based Job Queue with Leases

**Datum:** 2026-08-06  
**Status:** Accepted  

## Entscheidung

Tabelle `order_jobs` als Queue: SELECT FOR UPDATE SKIP LOCKED, Lease + Heartbeat, Status-Maschine, Idempotency über client_order_id.
