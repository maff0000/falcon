# TRON ↔ FALCON Contract

## Inbound Trade Suggestion discovery

TRON discovers eligible HELIOS Trade Suggestions (the registered
`helios.strategy_trigger` family) through a read-only, least-privilege
FALCON query interface. Search result alone is never sufficient
authority — a Trade Suggestion existing in FALCON means the evidence
exists, not that TRON trusts or must act on it.

TRON: 1. queries a bounded overlap window; 2. validates FALCON
health/ingestion lag; 3. validates event/schema; 4. verifies HELIOS
signature and key status; 5. verifies validity window; 6. performs
durable local dedupe; 7. performs serviceability/admission/hard-risk
checks; 8. sizes and executes if approved, or records a refusal with
reason if not.

Suggested MVP polling cadence: - H4/H1: 60 seconds; - M15: 30 seconds; -
M5: 10 seconds.

Cadence remains configurable and must be validated empirically.

## Failure invariant

If FALCON is unavailable or ingestion lag exceeds governed limits: **no
new entries** through this discovery path.

Existing position protection, broker-native SL/TP, local journal, exits
and reconciliation remain independent.

## TRON outbound evidence

TRON writes durable local evidence first and publishes: - Trade
Suggestion observed (`tron.trigger_observed`); - admission decision; -
rejection reason; - order intent/submission/update; - fills; -
position/protection state; - exits; - trade outcome; - execution
quality; - health. Both outcomes — admitted-and-executed and
refused-with-reason — are published as FALCON evidence; a refusal is not
left unrecorded.

Every observed Trade Suggestion must eventually have a terminal local
outcome, including duplicate, expired, invalid signature, unserviceable,
check failed, rejected or executed.

## Idempotency

TRON-local durable Trade Suggestion identity is authoritative for
preventing duplicate execution. FALCON currently provides no
separate bespoke application-level acceptance or idempotency
service; TRON's own durable dedupe is authoritative and
self-sufficient, not a backstop for a FALCON-side layer that does
not exist.

## Instance identity (FF-TRON-IDENTITY-01)

> Every TRON trading entity/instance MUST possess a globally unique,
> stable governed trader identity and a unique operational hostname.
> Every item of evidence produced by that TRON MUST carry enough
> identity information to attribute its decisions, refusals, orders,
> fills, positions, exits and outcomes unambiguously to that specific
> TRON entity.

Two distinct concepts, not one:

-   `tron_instance_id` — the canonical governed trader identity. This
    maps onto PID-01's existing, closed `producer_component_id`
    envelope field, registered per TRON trading entity (for example
    `tron.vantage_xau_01`), not per Docker container or host — the
    system/component registry already prohibits a component identity
    being a hostname or an ephemeral container name, which is exactly
    the stability this identity requires.
-   `tron_hostname` — the unique operational hostname/runtime
    placement. This maps onto PID-01's existing, closed, optional
    `producer_instance_id` envelope field ("runtime instance identity,
    separate from the stable component identity").

They may be similarly named in practice but are not semantically
identical, and must never be conflated.

### Stability

-   restart does not change `tron_instance_id`;
-   redeployment does not change `tron_instance_id` unless
    intentionally creating a new TRON trader;
-   infrastructure migration may change `tron_hostname`/placement
    without changing the governed `tron_instance_id`;
-   cloning a VM/container MUST NOT silently duplicate an existing
    `tron_instance_id` — a clone that will run as an independent
    trader MUST be registered under its own new `tron_instance_id`
    before it publishes evidence;
-   two simultaneously active TRON entities MUST NOT claim the same
    governed `tron_instance_id`;
-   every outbound TRON FalconEvent must carry both fields.

### Attribution

The evidence model must support forensic/analytical queries such as:
all evidence from a given `tron_instance_id`; all trades, refusals,
fills and outcomes from a given TRON; comparing the same HELIOS Trade
Suggestion, or strategy performance, across multiple TRON instances.
These are ordinary Graylog searches/API queries filtered on the
registered `producer_component_id` — no bespoke attribution service is
required.

### Security seam (PID-04)

Where technically supported, the authenticated FALCON producer identity
for a TRON connection must be bound to the governed `tron_instance_id`
it is allowed to claim — a TRON connection must not be able to submit
evidence claiming another TRON instance's identity. This binding is
PID-04's responsibility and is not implemented here.

### PID-01 note

This section documents doctrine and a field-mapping onto PID-01's
existing, already-closed envelope fields (`producer_component_id`,
`producer_instance_id`) — it introduces no new registered field, no
schema change and no registry amendment. Registering real per-trader
`producer_component_id` values (for example `tron.vantage_xau_01`)
happens when a real TRON entity is onboarded (PID-09 and beyond), via
the registry's own existing, governed change-control process — not in
this documentation-only work.
