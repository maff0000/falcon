# FALCON Observability

## Required metrics

-   ingress accepted/rejected/duplicate counts;
-   per-producer last accepted UTC;
-   schema/auth/namespace rejection counts;
-   ingestion latency distributions;
-   Graylog journal/backlog;
-   Data Node health/storage;
-   MongoDB health;
-   stream/index growth;
-   query latency;
-   TRON trigger-discovery latency;
-   producer outbox/spool depth where exposed;
-   dead-letter count;
-   backup age;
-   disk capacity/headroom.

## Alerts

Alerts are transition-based, deduplicated, UTC and recovery-aware.
Operational faults must never masquerade as trading context.

## Capacity telemetry

DEV observability must collect the measurements needed by production
sizing rather than adding sizing instrumentation later.
