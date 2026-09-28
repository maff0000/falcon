# FALCON Failure, Retry and Replay

## Required scenarios

-   producer cannot reach FALCON;
-   FALCON unavailable;
-   Graylog restart;
-   Data Node restart;
-   MongoDB restart;
-   schema rejection;
-   authentication rejection;
-   namespace violation;
-   duplicate delivery;
-   out-of-order delivery;
-   producer restart with pending outbox/spool;
-   dead-letter then corrected replay;
-   excessive TRON query lag.

## Semantics

Transport order is not causal order. Events carry
identity/time/correlation/causation/revision metadata.

Duplicate accepted events return idempotent success without duplicate
evidence.

Permanent schema/auth failures are distinguishable from transient
failures.

Producer domain truth must not be rewritten because FALCON is
unavailable.
