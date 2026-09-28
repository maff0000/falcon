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

## Many-producer, many-consumer model

FALCON/Graylog is not architected around a single TRON consumer, or
around any single consumer:

``` text
HERMES
ARES
HELIOS
TRON instances
      │
      ▼
FALCON / Graylog
      │
      ├── Graylog GUI
      ├── NEO
      ├── TRON instance 1
      ├── TRON instance 2
      ├── TRON instance N
      ├── AI trading agents (read-only, governed)
      └── future governed consumers
```

Each consumer accesses only the evidence/query surfaces it is
authorised to read. Graylog's own governed search/API surface remains
the default read plane for every consumer — a custom query API is not
introduced merely because there may be many consumers.

AI trading agents may be granted governed read-only access to
structured evidence (HERMES signals/state, ARES news/risk/economic
events, HELIOS evaluations/Trade Suggestions, TRON execution/outcome
evidence). This is a read-side consumer capability only — not authority
to publish or execute unless separately authorised — and requires no
bespoke AI query service at this stage.

Where a producer runs as multiple simultaneous instances (TRON, most
immediately), each instance must remain individually attributable in
the evidence — see `docs/contracts/TRON-FALCON-CONTRACT.md`'s Instance
identity (FF-TRON-IDENTITY-01) section.

## FALCON-owned capabilities

-   producer message template/contract, via PID-01's registries
    (constructed by the producer itself, not a FALCON ingress service);
-   canonical universal envelope;
-   field/event/component registries;
-   Graylog-native input/pipeline configuration that realises the
    template above (routing, field mapping, FALCON ingestion timestamp
    assignment);
-   namespace isolation (Graylog-native/network-native — see PID-04);
-   Graylog routing/mapping/indexing;
-   cross-system correlation;
-   retention classes;
-   search/query contract;
-   evidence health;
-   production capacity evidence.

Producer delivery retries preserve canonical event identity where
applicable. PID-03 will empirically characterise and prove the
selected Graylog-native ingestion/replay behaviour. FALCON currently
provides no separate bespoke application-level acceptance or
idempotency service. Consumers requiring action-level deduplication,
including TRON, retain their own governed durable dedupe.

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
reconciliation and TRON journal remain independent; - recovery relies on producer-side retry (preserving canonical event identity where applicable) plus the selected Graylog-native replay mechanism, which PID-03 empirically characterises — FALCON provides no separate bespoke application-level acceptance or idempotency service of its own.

## DEV/PROD separation

DEV is `/srv/falcon` on dell-debian and may be destructively rebuilt.
PROD is separately provisioned from measured MVP requirements. Promotion
is rebuild/redeploy from approved Git SHA + immutable BOM + external
configuration + secrets + persistent data/backup, not copying an
accidental DEV container state.
