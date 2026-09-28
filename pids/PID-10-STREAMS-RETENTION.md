# PID-10 --- Streams, Indexes and Retention

**Slug:** `streams-retention`\
**Owner:** Rogue/FORGE\
**Assurance:** R2D2\
**Ops authority where applicable:** HELM\
**Time:** UTC only

## Purpose

Implement semantic/security/retention partitioning after real producer
traffic exists.

## Dependencies

PID-05 through PID-09 sufficiently active.

## Scope / deliverables

-   streams/index sets;
-   field mappings;
-   executable-trigger permissions;
-   retention classes;
-   index rotation;
-   measured storage model;
-   licensing constraints where applicable.

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

-   routing correctness;
-   permission isolation;
-   field explosion protection;
-   rotation/retention proof;
-   historical search across rotations.

## Definition of Done

Evidence is correctly partitioned and retained under documented measured
policies.

A PID is not complete until its behaviour is running and proven, not
merely coded or documented.
