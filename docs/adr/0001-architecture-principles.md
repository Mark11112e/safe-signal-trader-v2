# ADR-0001: Architecture Principles & Safety First

**Datum:** 2026-08-06  
**Status:** Accepted  
**Entscheider:** Lead Software Architect

## Kontext

Wir bauen einen modularen Trading-Bot von Grund auf neu. Die Anforderungen betonen Sicherheit, Idempotency, Recovery und Nachvollziehbarkeit höher als Geschwindigkeit oder Funktionsumfang. Es gibt mehrere Telegram-Quellen, mehrere Exchanges und parallele Ausführung.

## Entscheidung

Die 12 Architekturprinzipien aus dem Auftrag werden verbindlich:

1. Core kennt keine exchange-spezifischen Felder/Codes.
2. Jede Exchange über Adapter-Contract.
3. Stabile source_id + versionierte Config pro Quelle.
4. Jeder Trade: unveränderlicher effective_config_snapshot + Hash + Schema-Version.
5. Keine Credentials in Snapshots/Logs.
6. Aktive Trades ändern Verhalten nicht durch Config-Updates.
7. Order-Submit idempotent + crash-sicher.
8. Fremde Orders/Positionen nie anfassen.
9. Kein blinder Retry nach unklarer Antwort.
10. Position nie ungeschützt lassen.
11. Nur Tests + kleine PRs.
12. Production/Demo/Live technisch getrennt.

Zusätzlich:
- Queue über PostgreSQL (SKIP LOCKED + Lease) statt Redis/RabbitMQ.
- Control-Bot startet read-only.
- Live default aus, explizites Enable + Startup-Gate.

## Konsequenzen

- Höherer initialer Aufwand für Domain-Modelle und Contracts.
- Jede Exchange-Erweiterung ist isoliert und testbar.
- Config-Änderungen sind sicher für laufende Trades.
- Manuelle Reviews bei Ambiguität sind der sichere Default.
- Kleine PRs erzwingen hohe Qualität und Reviewbarkeit.

## Alternativen (verworfen)

- Monolithischer Code mit exchange-if/else → Verletzung von Prinzip 1+2.
- Redis/RabbitMQ als Queue → unnötige Ops-Komplexität, Anforderung „kein Broker“.
- Mutable Config für aktive Trades → Verletzung von Prinzip 6.
