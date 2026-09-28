# FALCON Master PID

## 1. Mission

Build FALCON as THE GOAL's canonical trading-evidence, correlation,
search and operational-observability plane, using a Dockerised Graylog
stack as its primary ingestion/search/GUI infrastructure while keeping
all trading semantics governed by FALCON contracts rather than Graylog
internals.

## 2. Development location

-   Host: `dell-debian`
-   Canonical DEV path: `/srv/falcon`
-   GitHub: `maff0000/falcon`
-   Default branch: `main`
-   DEV execution: Docker Compose
-   Trading integration during MVP: paper-trading TRON only

DEV is disposable and rebuildable. Production will be a separate bespoke
environment.

## 3. Authority model

  ---------------------------------------------------------------------
  System                             Authority
  ---------------------------------- ----------------------------------
  HERMES                             Market facts/state and governed
                                     market provenance

  ARES                               Risk, scheduled events, context,
                                     source quality, future typed
                                     news/assessment evidence

  HELIOS                             Deterministic strategy evaluation,
                                     chain state and signed strategy
                                     triggers

  TRON                               Admission, sizing, broker
                                     execution, fills, positions, exits
                                     and outcomes

  FALCON                             Canonical evidence contract,
                                     validation, correlation, search,
                                     retention and technical GUI

  NEO                                Research, review, effectiveness
                                     analysis
  ---------------------------------------------------------------------

FALCON does not reinterpret producer domain truth.

## 4. Core invariants

1.  UTC-only canonical time. Naive timestamps are invalid.
2.  Stable machine identities; never depend on ambiguous display names.
3.  Small universal envelope + typed versioned payloads.
4.  Strict field/event registries; no arbitrary dynamic producer fields.
5.  Immutable evidence; revisions/supersession append rather than
    overwrite history.
6.  Point-in-time knowability: FALCON must answer what was knowable at
    UTC T.
7.  Correlation and causation are distinct.
8.  Producer authentication and namespace isolation are mandatory.
9.  HELIOS executable triggers require cryptographic authenticity.
10. Producer outages and FALCON outages fail loudly and remain
    semantically distinct from market state.
11. Producer durable truth must not depend on FALCON availability.
12. FALCON/Graylog is a dependency for discovery of **new** entries if
    TRON uses it as the trigger source; existing position
    protection/exits must remain independent.
13. No secrets in Git, images or FalconEvents.
14. No config in code and no silent fallback.
15. Container images and production dependencies are immutable/version
    pinned. architecture.

## 5. Target MVP

MVP is achieved when: - Dockerised FALCON/Graylog stack runs on
dell-debian. - HERMES, canonical ARES, HELIOS and paper TRON can publish
governed evidence. - HELIOS signed triggers can be discovered by paper
TRON through FALCON. - Full trigger-to-outcome forensic timelines are
queryable in Graylog GUI. - ARES scheduled events are visible before
occurrence with point-in-time history. - retries, duplicates, outage,
replay, schema rejection and auth rejection are proven. - capacity
telemetry exists for production sizing. - backup/restore is proven. -
R2D2 independently verifies the running architecture.

## 6. Delivery sequence

Execute `pids/PID-00` through `PID-15` in dependency order unless the
Master PID explicitly approves parallel work.

## 7. Roles

### Rogue/FORGE

Build engineering. Implements bounded PIDs, tests, evidence and PRs.
Must not silently alter architecture.

### R2D2

Independent assurance. Maintains FALCON blueprint, verifies exact
SHA/runtime evidence and reports deviations. R2D2 is not the
implementer.

### HELM

Infrastructure/sysops authority. Owns host readiness, Docker/runtime
constraints, backups, networking, secrets placement and production
operational design. All platform timestamps remain governed UTC;
host-local time, naive `datetime.now()`, database
`NOW()`/`UTC_TIMESTAMP()` or similar runtime sources must not become
canonical timestamps without explicit approved handling.

### FALCON Architect / PO

Owns contract, field registry, authority boundaries, PID sequencing and
acceptance rulings.

## 8. Handover law

At major stopping points, agents write a concise but technically
sufficient handover into Memory Fabric: canonical SHA, branch/PR,
running state, tests, unresolved issues, decisions, evidence locations
and exact next action.
