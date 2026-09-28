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
                       │ evaluation/state/signed trigger
                       │
                       └──────────── TRON
                         admission/execution/outcome
                                  │
                                  ▼
                        FALCON INGESTION
                    auth → validate → registry
                         → idempotency
                         → ingestion UTC
                                  │
                                  ▼
                              GRAYLOG
                       + Graylog Data Node
                       + MongoDB metadata
                                  │
             ┌────────────────────┼───────────────────┐
             ▼                    ▼                   ▼
       Graylog technical GUI     NEO           TRON discovery
```

## FALCON-owned capabilities

-   ingress protocol;
-   producer identity/authentication;
-   canonical universal envelope;
-   field/event/component registries;
-   schema validation;
-   namespace isolation;
-   idempotent acceptance;
-   FALCON ingestion timestamp;
-   Graylog routing/mapping/indexing;
-   cross-system correlation;
-   retention classes;
-   search/query contract;
-   evidence health;
-   production capacity evidence.

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
  → HELIOS signed trigger
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
trigger that cannot be validly discovered/verified through the governed
path; - existing broker-native SL/TP, local protection, exits,
reconciliation and TRON journal remain independent; - recovery uses
idempotent retry/replay.

## DEV/PROD separation

DEV is `/srv/falcon` on dell-debian and may be destructively rebuilt.
PROD is separately provisioned from measured MVP requirements. Promotion
is rebuild/redeploy from approved Git SHA + immutable BOM + external
configuration + secrets + persistent data/backup, not copying an
accidental DEV container state.
