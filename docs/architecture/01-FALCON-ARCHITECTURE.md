# FALCON Architecture

## Context

FALCON is not "a log server." It is the governed evidence plane through
which THE GOAL can reconstruct why a trade happened, why it did not
happen, what each authoritative system knew, and what subsequently
occurred.

Graylog provides the principal event/search infrastructure and technical
GUI. Graylog does not define domain semantics.

## Logical topology

``` text
                       ┌──────────── HERMES
                       │ market facts/state
                       │
                       ├──────────── canonical ARES
                       │ events/context/source quality
                       │
                       ├──────────── HELIOS
                       │ evaluation/state/signed Trade Suggestion
                       │
                       └──────────── TRON
                         admission/execution/outcome
                                  │
              each producer constructs its own conformant
              FalconEvent (PID-01 universal envelope + typed
              family schema) and sends it via an authorised
              Graylog-native transport — no bespoke FALCON
              ingress service sits in this path
                                  │
                                  ▼
                           GRAYLOG-FALCON
                inputs → pipelines → streams → journal
                                  │
                                  ▼
                    Data Node + indexes (evidence now exists)
                       + MongoDB metadata
                                  │
             ┌────────────────────┼───────────────────┐
             ▼                    ▼                   ▼
       Graylog technical GUI     NEO         TRON Trade Suggestion
                                              discovery + admission
```

There is no bespoke FALCON middleware box between producers and Graylog.
A message existing in Graylog/Data Node means the event exists as
recorded evidence; it does not by itself mean any consumer (e.g. TRON)
trusts or acts on it — that is the consumer's own governed admission
decision, made independently and recorded back into FALCON as further
evidence (see "Evidence vs. trust" below).

## FALCON-owned capabilities

-   producer message template/contract, via PID-01's registries
    (constructed by the producer itself, not a FALCON ingress service);
-   canonical universal envelope;
-   field/event/component registries;
-   Graylog-native input/pipeline configuration that realises the
    template above (routing, field mapping, FALCON ingestion timestamp
    assignment);
-   namespace isolation (Graylog-native/network-native — see PID-04);
-   idempotent acceptance;
-   Graylog routing/mapping/indexing;
-   cross-system correlation;
-   retention classes;
-   search/query contract;
-   evidence health;
-   production capacity evidence.

## Evidence vs. trust

FALCON records evidence; it does not decide who acts on it. These are
three distinct questions, never conflated:

1.  **Ingress security** — can this source connect/send to FALCON at
    all? (PID-04, Graylog/network-native.)
2.  **Content contract** — does this message conform to its expected
    FALCON structure? (PID-01's contracts, constructed by the producer.)
3.  **Consumer trust** — should another system (e.g. TRON) act upon this
    message? (the consuming system's own governed admission logic, not
    FALCON's.)

A HELIOS Trade Suggestion existing in FALCON, even one with an invalid
signature, is still recorded evidence. TRON's decision to admit or
refuse it is a separate, independent judgement, and that judgement is
itself recorded as FALCON evidence — this is what gives NEO a complete
forensic record.

## Non-goals

-   replace HERMES historical market corpus;
-   become ARES's authoritative database;
-   decide whether HELIOS strategy logic is correct;
-   size or place TRON orders;
-   infer missing provenance;
-   use Graylog message IDs as trading identity;
-   turn arbitrary application logs into trading evidence.

## Causal model

``` text
market/event reality
  → producer source evidence
  → producer normalized/derived state
  → HELIOS evaluation
  → HELIOS signed Trade Suggestion
  → TRON admission decision
  → order/fill/position
  → exit/outcome
  → NEO retrospective review
```

Not every chain contains every producer. Correlation must preserve the
actual causal graph rather than fabricate links.

## Availability

If FALCON is unavailable: - producers retain authoritative domain truth
and durable export evidence; - no new TRON entry may be created from a
Trade Suggestion that cannot be validly discovered/verified through the
governed path; - existing broker-native SL/TP, local protection, exits,
reconciliation and TRON journal remain independent; - recovery uses
idempotent retry/replay.

## DEV/PROD separation

DEV is `/srv/falcon` on dell-debian and may be destructively rebuilt.
PROD is separately provisioned from measured MVP requirements. Promotion
is rebuild/redeploy from approved Git SHA + immutable BOM + external
configuration + secrets + persistent data/backup, not copying an
accidental DEV container state.
