# PID-09 --- Paper TRON Discovery, Admission and Execution Evidence

**Slug:** `tron-paper`\
**Owner:** Rogue/FORGE\
**Assurance:** R2D2\
**Ops authority where applicable:** HELM\
**Time:** UTC only

## Purpose

Connect paper-trading TRON to FALCON for bounded trigger discovery and
return complete execution evidence.

## Dependencies

PID-08, PID-03, PID-04.

## Scope / deliverables

-   read-only trigger query identity;
-   overlap polling;
-   configurable per-timeframe cadence;
-   ingestion-lag gate;
-   local durable dedupe;
-   terminal outcome model;
-   TRON evidence emitter/spool;
-   paper execution only.

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

-   one trigger executes once;
-   duplicate trigger does not re-execute;
-   expired/bad signature/unserviceable/check-failed outcomes;
-   FALCON unavailable/lag =\> no new entry;
-   existing paper position protection remains independent;
-   full trigger→outcome timeline.

## Definition of Done

Paper TRON safely consumes signed triggers and every observed trigger
has a forensic terminal outcome.

A PID is not complete until its behaviour is running and proven, not
merely coded or documented.
