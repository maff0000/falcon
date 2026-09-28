# FALCON Test and Acceptance Plan

## Test layers

-   schema/registry unit tests;
-   canonical fixture validation;
-   ingress auth/namespace tests;
-   idempotency tests;
-   producer contract tests;
-   Graylog mapping/search tests;
-   causal reconstruction tests;
-   point-in-time tests;
-   trigger-signature tests;
-   TRON discovery/dedupe tests;
-   failure/replay tests;
-   backup/restore tests;
-   performance/capacity tests;
-   security negative tests.

## Cross-system golden scenario

At minimum prove one deterministic scenario:

``` text
ARES scheduled event known
+ HERMES market evidence
→ HELIOS evaluation
→ signed HELIOS trigger
→ paper TRON observes
→ TRON admission
→ paper order/fill
→ position/outcome
→ complete FALCON timeline
```

Also prove a rejected/suppressed scenario.

## Definition of Done

Code merged without runtime proof is not done. Documentation without
running implementation is not done. Tests must run against the exact
candidate SHA/runtime and evidence must be retained.
