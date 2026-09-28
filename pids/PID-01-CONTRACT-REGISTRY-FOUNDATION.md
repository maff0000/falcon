# PID-01 --- Universal Contract and Registries

**Slug:** `contract-registry`\
**Owner:** Rogue/FORGE\
**Assurance:** R2D2\
**Ops authority where applicable:** HELM\
**Time:** UTC only

## Purpose

Turn the approved Markdown contract into machine-readable
schema/field/event/component registries.

## Dependencies

PID-00.

## Scope / deliverables

-   versioned FalconEvent JSON Schema;
-   machine-readable field registry;
-   event-family registry;
-   system/component registry;
-   compatibility/versioning rules;
-   canonical fixtures for HERMES/ARES/HELIOS/TRON;
-   validation library/service boundary.

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

-   valid fixtures accepted;
-   missing/extra/wrong-type fields rejected;
-   naive timestamps rejected;
-   unknown family/component rejected;
-   compatibility tests;
-   deterministic ID fixtures.

## Definition of Done

Registries and schema are executable, tested and become the only
accepted contract authority.

A PID is not complete until its behaviour is running and proven, not
merely coded or documented.
