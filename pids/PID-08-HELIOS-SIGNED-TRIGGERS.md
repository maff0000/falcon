# PID-08 --- HELIOS Signed Executable Triggers

**Slug:** `helios-signed-triggers`\
**Owner:** Rogue/FORGE\
**Assurance:** R2D2\
**Ops authority where applicable:** HELM\
**Time:** UTC only

## Purpose

Introduce cryptographically authentic HELIOS trigger evidence suitable
for TRON discovery.

## Dependencies

PID-07, PID-04.

## Scope / deliverables

-   canonical trigger schema;
-   Ed25519 canonical signing representation;
-   key ID;
-   DEV key generation/storage/rotation/revocation;
-   signature verification fixtures;
-   validity-window semantics;
-   semantic SL/TP and governed score semantics.

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

-   valid signature;
-   tampered payload;
-   unknown/revoked key;
-   expired/not-yet-valid trigger;
-   identical search hit cannot bypass signature;
-   no private key leakage.

## Definition of Done

Signed trigger evidence is searchable and independently verifiable by a
consumer.

A PID is not complete until its behaviour is running and proven, not
merely coded or documented.
