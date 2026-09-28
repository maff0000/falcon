# PID-13 --- Observability and Production Capacity Evidence

**Slug:** `capacity`\
**Owner:** Rogue/FORGE\
**Assurance:** R2D2\
**Ops authority where applicable:** HELM\
**Time:** UTC only

## Purpose

Collect enough measured evidence to size the bespoke production
environment.

## Dependencies

Stable MVP producer traffic through PID-12.

## Scope / deliverables

-   metrics/dashboards;
-   event rate/size/storage;
-   CPU/RAM/heap/IOPS;
-   query latency/concurrency;
-   TRON discovery latency;
-   backup/restore duration;
-   event-day burst tests;
-   NEO-like research query load;
-   production sizing report.

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

-   repeatable load scenarios;
-   measured p50/p95/p99;
-   storage growth projection;
-   bottleneck evidence;
-   headroom calculation.

## Definition of Done

A defensible production capacity model exists with no guessed server
size.

A PID is not complete until its behaviour is running and proven, not
merely coded or documented.
