# ADR-0002: PostgreSQL-based Job Queue with Leases

**Datum:** 2026-08-06  
**Status:** Accepted  
**Entscheider:** Lead Software Architect

## Kontext

Order-Jobs, Reconciliation-Jobs und Protection-Aktionen müssen persistent, crash-sicher und concurrent-safe verarbeitet werden. Die Anforderung lautet explizit: „Queue: PostgreSQL mit SELECT FOR UPDATE SKIP LOCKED, Leases, Heartbeat (kein Broker nötig)“.

## Entscheidung

Wir verwenden die Tabelle `order_jobs` (und ggf. weitere Job-Tabellen) als Queue:

- Atomic Claim: `SELECT ... FOR UPDATE SKIP LOCKED`
- Lease mit Timeout + Heartbeat (Worker erneuert Lease periodisch)
- Ownership-Feld (worker_id)
- Status-Maschine: pending → claimed → in_progress → completed / failed / manual_review
- Bei Lease-Ablauf: automatische Re-Claim-Fähigkeit durch andere Worker
- Idempotency über deterministische client_order_id und Job-Key

## Konsequenzen

- Eine Datenbank für State + Queue → einfachere Transaktionen und Recovery.
- Keine zusätzliche Infrastruktur (Redis/Rabbit).
- Ausreichend für die erwartete Last (Telegram-Signale sind nicht high-frequency).
- Später austauschbar gegen echten Broker, falls nötig (Interface bleibt).

## Alternativen (verworfen)

- Redis Streams / RQ / Celery → zusätzliche Komponente, Ops-Overhead, Anforderung verletzt.
- In-Memory Queue → nicht crash-sicher.
