# PID-08 --- HELIOS Signed Trade Suggestions

**Slug:** `helios-signed-triggers`\
**Owner:** Rogue/FORGE\
**Assurance:** R2D2\
**Ops authority where applicable:** HELM\
**Time:** UTC only

## Purpose

Introduce cryptographically authentic HELIOS Trade Suggestion evidence
suitable for TRON discovery. A Trade Suggestion is structured FALCON
evidence, optionally signed by HELIOS — it is not a command or an
execution instruction. FALCON preserves the signature as part of the
recorded evidence; FALCON does not itself decide whether TRON should
trust the signature merely to record the event. That trust decision is
TRON's own (see PID-09).

**Terminology note (does not change PID-01's closed contract):**
PID-01's registered event family remains `helios.strategy_trigger`, with
fields including `trigger_id` and `trigger_at_utc` — unchanged and
closed. "Trade Suggestion" is this PID's documentation/framing
clarification of what that registered family *means* conceptually (a
suggestion for TRON to evaluate, not a command it must obey), not a
rename of the registered family or its fields. If a future PID wants to
literally rename the family/fields, that requires separate PID-01
amendment authority and is not decided here — it is flagged as a
follow-up decision for the Architect.

## Dependencies

PID-07, PID-04.

## Scope / deliverables

-   canonical Trade Suggestion schema (the registered
    `helios.strategy_trigger` family);
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
-   expired/not-yet-valid Trade Suggestion;
-   identical search hit cannot bypass signature;
-   no private key leakage.

## Definition of Done

Signed Trade Suggestion evidence is searchable and independently
verifiable by a consumer.

A PID is not complete until its behaviour is running and proven, not
merely coded or documented.
