# PID-03 --- Canonical Graylog Ingestion & Producer Message Templates

**Slug:** `graylog-ingestion-templates`\
**Owner:** Rogue/FORGE\
**Assurance:** FORGE Auditor (R2D2 by exception)\
**Ops authority where applicable:** HELM\
**Time:** UTC only

## Purpose

Prove that HERMES, ARES, HELIOS and TRON can each construct a conformant
FalconEvent (per PID-01's existing universal envelope, field, event-family
and component registries) and deliver it into `graylog-falcon` through
Graylog's own native ingestion machinery, with no bespoke FALCON
middleware standing between producer and Graylog.

A bespoke ingress architecture (a custom `ingress-falcon` service, a
MongoDB durable acceptance ledger, and a custom ACK state machine with
states such as `DURABLY_ACCEPTED`/`PROJECTED`) was proposed during
preflight and has been **withdrawn by the Architect** as unnecessary
complexity. Do not build around Graylog. Use Graylog.

**Dormant registry note (does not change PID-01's closed contract):**
PID-01's closed `registry/system_component_registry.v1.json` registers
a component named `falcon.ingress_gateway` under the `falcon` system's
component list — a literal echo of the architecture withdrawn above.
It is a dormant, placeholder-governed name (no live components exist
yet per PID-01's own scope), not something this PID builds merely
because it is registered, and not something this PID amends. See
`docs/governance/FALCON-DECISION-REGISTER.md` decision 27.

## Dependencies

PID-01, PID-02.

## Scope / deliverables

-   canonical producer message templates for HERMES, ARES, HELIOS and
    TRON, built directly on PID-01's existing registries/schemas
    (used as-is, at their existing per-family granularity — not
    collapsed into a small number of generic schemas);
-   a native Graylog structured input (or inputs) proven against the
    pinned Graylog 7.1.9 stack, selecting the specific supported
    mechanism (e.g. GELF, a Graylog HTTP/TCP/UDP input type) by
    evidence at implementation time rather than by assumption;
-   transport guidance applied per event class: TCP (or another
    reliable-delivery transport) preferred wherever the message is
    trading evidence that matters; UDP reserved only for explicitly
    disposable telemetry where loss is acceptable;
-   one real fixture each for HERMES/ARES/HELIOS/TRON, from PID-01's
    existing fixture corpus, accepted through the real ingestion path
    and made searchable in Graylog;
-   proof that structured fields, event-family routing, UTC
    preservation and correlation/causation/provenance fields survive
    ingestion unchanged;
-   malformed/template-negative fixtures proven to never silently
    become trusted canonical evidence — proven empirically rejected,
    quarantined/separately routed, or visibly classified/alerted as
    invalid, per what the pinned Graylog 7.1.9 stack actually
    supports (not assumed), with no central FALCON service that
    repairs a malformed producer event — a bad producer is corrected
    at its source, not patched in flight;
-   FTE (FALCON Test Engine) bootstrap: the minimum fixture-sender
    needed to send known structured fixtures through the real Graylog
    ingestion path and assert the results above (full FTE
    productionisation remains out of scope here and requires separate
    authorisation to create `maff0000/falcon-test-engine`);
-   restart/recovery proof that relies on Graylog's own native
    journal/Data Node durability, not a bespoke FALCON recovery
    mechanism;
-   evidence retrieval proven via both the Graylog API/search and the
    GUI where appropriate.

Explicitly excluded from this PID:

-   no custom `ingress-falcon` (or equivalently named) service;
-   no MongoDB event-acceptance ledger separate from Graylog's own
    MongoDB metadata store;
-   no Redis dependency;
-   no second/custom GUI;
-   no upstream producer application code changes (HERMES/ARES/
    HELIOS/TRON integration work belongs to PID-05 through PID-09);
-   no real PID-04 producer-connection-security implementation (this
    PID may use DEV-adequate placeholders where Graylog requires
    something to accept a connection, but does not implement PID-04);
-   no PID-08 signature implementation;
-   no TRON execution.

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

-   canonical producer templates render conformant PID-01 fixtures for
    HERMES, ARES, HELIOS and TRON;
-   the chosen native Graylog input mechanism is proven against the
    pinned Graylog 7.1.9 stack, with the supported mechanism recorded
    as evidence rather than assumed;
-   each of the four producer fixtures is accepted and searchable in
    Graylog with correct structured fields, correct event-family
    routing, correct UTC preservation and correct
    correlation/causation/provenance fields;
-   malformed/template-negative fixtures are proven to never
    silently become trusted canonical evidence — proven rejected,
    quarantined, separately routed, or visibly classified/alerted as
    invalid, per what the pinned Graylog 7.1.9 stack actually
    supports;
-   FTE bootstrap fixture-sender exists and exercises the positive and
    negative cases above through the real ingestion path;
-   restart/recovery proof uses Graylog's own journal/Data Node
    mechanisms;
-   evidence is retrievable via Graylog API/search and, where
    appropriate, GUI.

## Definition of Done

Canonical producer templates (PID-01's existing registries, used as-is)
are proven end-to-end against the real, pinned Graylog 7.1.9 stack: each
of the HERMES/ARES/HELIOS/TRON fixtures is accepted through a native
Graylog input, is structured/searchable/correctly routed with UTC and
correlation/provenance intact, and template-negative fixtures are
proven to never silently become trusted canonical evidence — with
no bespoke ingress service, no Mongo event ledger, no Redis and no
second GUI anywhere in the path.

A PID is not complete until its behaviour is running and proven, not
merely coded or documented.

## Closure evidence — pointer

Full delivery evidence (transport decision, pipeline design and its two
non-obvious Graylog 7.1.9 execution-order mechanics, the content-pack
round-trip finding for `route_to_stream` and its fix, restart/recovery
proof, and the FTE bootstrap) lives in `deploy/README.md`'s "PID-03 —
Canonical Graylog Ingestion Path" section, not here (Fabric/README is
the evidence trail; this file stays the spec). Automated positive/negative
suite: `tests/fte/run_pid03_tests.py`, latest machine-readable output at
`tests/fte/last_run_report.json` (4/4 positive PASS; 11/13 negative
classes natively quarantined; 2 documented exceptions —
`unknown_field.json` is a genuine Graylog 7.1.9 native-capability
hard-stop for that one negative class, no map-key-enumeration function
exists in the pipeline rule DSL; `identity_violation_reused_event_id.json`
is by design per decision 22, consumer-side dedupe). Content pack:
`deploy/content-packs/falcon-pid03-ingestion-v1.json`, round-trip-verified
twice via full delete-and-reinstall.
