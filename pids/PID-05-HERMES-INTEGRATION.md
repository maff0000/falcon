# PID-05 --- HERMES → FALCON Integration

**Slug:** `hermes-integration`\
**Owner:** Rogue/FORGE\
**Assurance:** R2D2\
**Ops authority where applicable:** HELM\
**Time:** UTC only

## Purpose

Publish the approved bounded HERMES decision-relevant evidence surface
without duplicating the historical corpus.

## Dependencies

PID-01, PID-03, PID-04.

## Scope / deliverables

-   approved HERMES allow-list;
-   emitter/adapter;
-   market fact/state/quality schemas;
-   provenance and `available_at_utc`;
-   durable retry/spool according to HERMES authority;
-   DEV fixtures and live-dark proof.

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

-   causal timing;
-   stale/quality handling;
-   FALCON outage/retry;
-   idempotency;
-   no raw-corpus flood;
-   Graylog search.

## Definition of Done

Approved HERMES evidence is live in DEV FALCON with provenance and
point-in-time semantics.

A PID is not complete until its behaviour is running and proven, not
merely coded or documented.
