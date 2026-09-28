# TRON ↔ FALCON Contract

## Inbound trigger discovery

TRON discovers eligible HELIOS triggers through a read-only,
least-privilege FALCON query interface. Search result alone is never
sufficient authority.

TRON: 1. queries a bounded overlap window; 2. validates FALCON
health/ingestion lag; 3. validates event/schema; 4. verifies HELIOS
signature and key status; 5. verifies validity window; 6. performs
durable local dedupe; 7. performs serviceability/admission/hard-risk
checks; 8. sizes and executes if approved.

Suggested MVP polling cadence: - H4/H1: 60 seconds; - M15: 30 seconds; -
M5: 10 seconds.

Cadence remains configurable and must be validated empirically.

## Failure invariant

If FALCON is unavailable or ingestion lag exceeds governed limits: **no
new entries** through this discovery path.

Existing position protection, broker-native SL/TP, local journal, exits
and reconciliation remain independent.

## TRON outbound evidence

TRON writes durable local evidence first and publishes: - trigger
observed; - admission decision; - rejection reason; - order
intent/submission/update; - fills; - position/protection state; -
exits; - trade outcome; - execution quality; - health.

Every observed trigger must eventually have a terminal local outcome,
including duplicate, expired, invalid signature, unserviceable, check
failed, rejected or executed.

## Idempotency

TRON-local durable trigger identity is authoritative for preventing
duplicate execution. FALCON idempotency is additional protection, not a
substitute.
