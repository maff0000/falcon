# PID-07 --- HELIOS Evaluation and State Evidence

**Slug:** `helios-observability`\
**Owner:** Rogue/FORGE\
**Assurance:** R2D2\
**Ops authority where applicable:** HELM\
**Time:** UTC only

## Purpose

Publish deterministic HELIOS evaluation/state/chain evidence before
executable trigger dependence.

## Dependencies

PID-01, PID-03, PID-04.

## Scope / deliverables

-   strategy evaluation schema;
-   strategy/chain state schema;
-   input snapshot/hash references;
-   decline/block/near-miss reasons;
-   strategy fingerprint/version/parameter identity;
-   health.

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

-   fired/declined/blocked/near-miss fixtures;
-   exact HERMES/ARES input references;
-   point-in-time reconstruction;
-   no execution authority fields.

## Definition of Done

Graylog can explain why a strategy fired or did not fire from governed
HELIOS evidence.

A PID is not complete until its behaviour is running and proven, not
merely coded or documented.
