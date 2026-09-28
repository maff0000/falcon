# PID-06 --- Canonical ARES → FALCON Integration

**Slug:** `ares-integration`\
**Owner:** Rogue/FORGE\
**Assurance:** R2D2\
**Ops authority where applicable:** HELM\
**Time:** UTC only

## Purpose

Add the generic durable ARES export boundary, beginning with Calendar .

## Dependencies

PID-01, PID-03, PID-04.

## Scope / deliverables

-   ARES identity/correlation/causation/revision extensions;
-   transactional `ares_falcon_outbox`;
-   Calendar dark export then DEV delivery;
-   configured pre-event snapshots;
-   Market Status, Liquidity, Macro/USD and source-quality expansion
    after Calendar proof;
-   Regime only after SQL-first assurance.

## Mandatory engineering law

-   no config in code;
-   no hidden defaults/fallbacks;
-   required missing config fails loudly;
-   no secrets in Git/images/events;
-   container-compatible;
-   UTC-aware canonical timestamps only;
-   bounded branch/PR with clean Git hygiene;
-   exact SHA/runtime evidence;
-   documentation updated with implementation;

## Required tests/evidence

-   exact UTC/as-of reconstruction;
-   revision does not rewrite history;
-   duplicate/retry/restart/dead-letter/replay;
-   FALCON outage leaves ARES truth intact;
-   pre-event GUI visibility;
-   no legacy bridge.

## Definition of Done

Canonical ARES evidence is reconstructable at UTC T in FALCON and
survives outage/replay.

A PID is not complete until its behaviour is running and proven, not
merely coded or documented.
