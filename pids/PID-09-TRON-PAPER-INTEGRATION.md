# PID-09 --- Paper TRON Discovery, Admission and Execution Evidence

**Slug:** `tron-paper`\
**Owner:** Rogue/FORGE\
**Assurance:** R2D2\
**Ops authority where applicable:** HELM\
**Time:** UTC only

## Purpose

Connect paper-trading TRON to FALCON so it can discover appropriate
HELIOS Trade Suggestions (the registered `helios.strategy_trigger`
family — see PID-08's terminology note) and return complete execution
evidence. TRON independently validates each candidate Trade Suggestion
(correct template, correct producer, signature validity, freshness,
supported instrument, correct context, execution rules, risk/admission
rules) and makes its own accept/refuse decision. Where accepted and
permitted, TRON paper-executes; either way — accepted-and-executed, or
refused-with-reason — the outcome is written back into FALCON as
evidence. Invalid or untrusted does not mean invisible: for example, a
Trade Suggestion with an invalid signature is still recorded, and TRON's
refusal of it is still recorded, preserving the full forensic record for
future NEO review.

## Dependencies

PID-08, PID-03, PID-04.

## Scope / deliverables

-   read-only Trade Suggestion query identity;
-   overlap polling;
-   configurable per-timeframe cadence;
-   ingestion-lag gate;
-   local durable dedupe;
-   terminal outcome model, distinguishing accepted-and-executed from
    refused-with-reason;
-   TRON evidence emitter/spool;
-   a stable governed `tron_instance_id` (`producer_component_id`) and
    `tron_hostname` (`producer_instance_id`) carried on every outbound
    FalconEvent, per FF-TRON-IDENTITY-01
    (`docs/contracts/TRON-FALCON-CONTRACT.md`);
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

-   one Trade Suggestion executes once;
-   duplicate Trade Suggestion does not re-execute;
-   expired/bad signature/unserviceable/check-failed outcomes;
-   FALCON unavailable/lag =\> no new entry;
-   existing paper position protection remains independent;
-   full Trade-Suggestion→admission-decision→outcome timeline, including
    refused (not just executed) Trade Suggestions;
-   every emitted event carries a stable `tron_instance_id` unchanged
    across a restart, and all evidence for that instance is
    attributable via an ordinary Graylog search/API query on it.

## Definition of Done

Paper TRON safely consumes signed Trade Suggestions, independently
admits or refuses each one, and every observed Trade Suggestion has a
forensic terminal outcome recorded in FALCON — whether executed or
refused.

A PID is not complete until its behaviour is running and proven, not
merely coded or documented.
