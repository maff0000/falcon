# PID-12 --- Failure, Replay, Backup and Restore

**Slug:** `failure-recovery`\
**Owner:** Rogue/FORGE\
**Assurance:** R2D2\
**Ops authority where applicable:** HELM\
**Time:** UTC only

## Purpose

Prove FALCON is recoverable and producer evidence is not silently lost.

## Dependencies

PID-09, PID-10.

## Scope / deliverables

-   failure matrix;
-   replay tooling/runbook;
-   dead-letter workflow;
-   MongoDB/Data Node/Graylog backup;
-   destructive restore drill;
-   producer replay boundaries.

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

-   deterministic corpus backup/restore;
-   component restart scenarios;
-   producer pending-outbox recovery;
-   event count/hash/query equivalence;
-   RTO/RPO measurements.

## Definition of Done

Destructive recovery has been executed successfully, not merely
documented.

A PID is not complete until its behaviour is running and proven, not
merely coded or documented.
