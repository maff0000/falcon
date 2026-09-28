# Canonical ARES → FALCON Contract

## Authority

Only canonical Dockerised ARES participates.

ARES remains authoritative for ARES domain state even when FALCON is
unavailable. Export uses a durable ARES-owned transactional outbox.

## Current canonical families

1.  Calendar event state --- first integration candidate.
2.  Market Status session state.
3.  Liquidity state.
4.  Macro/USD breadth state; explicitly not DXY.
5.  Source-quality transition.
6.  Publication decision as research/operational evidence.
7.  Regime nowcast after independent SQL-first authority proof.

Not current canonical authority: unscheduled news, AI market
interpretation, mandatory veto, calibrated risk score.

## Scheduled events

Important future events become FALCON-visible before occurrence.
Material event/revision/lifecycle/assessment/decision changes publish
immediately. Purposeful typed state snapshots/heartbeats may increase
with proximity according to externally configured ARES policy. The
transport adapter does not invent cadence.

## Point-in-time truth

FALCON must reconstruct what ARES knew at UTC T. Provider revisions,
reassessments and later decisions append; they do not rewrite earlier
knowability.

## Outbox

Eligible emitted snapshot + FALCON outbox row must be durable in the
same authoritative transaction where feasible. Delivery state is mutable
in the outbox; domain evidence remains immutable.

Minimum delivery states: PENDING, RETRYING, DELIVERED, DEAD_LETTER.

## Acknowledgement

ARES marks its own outbox row DELIVERED once its governed
Graylog-native transport confirms the emitted evidence was
received. FALCON provides no separate bespoke application-level
acceptance or idempotency service; PID-03 empirically characterises
the selected native mechanism's exact confirmation and replay
behaviour. Schema/auth rejection and transient failure remain
distinct wherever the native mechanism can distinguish them.

## Graylog independence

ARES knows FALCON contracts, never Graylog stream/index/message IDs.
