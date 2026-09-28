# PID-03 --- Canonical FALCON Ingress

**Slug:** `falcon-ingress`\
**Owner:** Rogue/FORGE\
**Assurance:** R2D2\
**Ops authority where applicable:** HELM\
**Time:** UTC only

## Purpose

Implement the Graylog-independent producer boundary that authenticates,
validates, idempotently accepts and routes FalconEvents.

## Dependencies

PID-01, PID-02.

## Scope / deliverables

-   ingress endpoint/protocol;
-   universal envelope validation;
-   family schema validation;
-   namespace enforcement;
-   idempotency;
-   FALCON-owned ingestion UTC;
-   Graylog mapping;
-   accepted/duplicate/schema-rejected/auth-rejected/transient
    responses;
-   operational evidence.

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

-   all response classes;
-   duplicate replay;
-   unregistered field rejection;
-   namespace spoof rejection;
-   out-of-order acceptance;
-   Graylog searchable evidence;
-   ingestion latency measurement.

## Definition of Done

Four producer fixture families can be accepted/rejected
deterministically and queried in Graylog.

A PID is not complete until its behaviour is running and proven, not
merely coded or documented.
