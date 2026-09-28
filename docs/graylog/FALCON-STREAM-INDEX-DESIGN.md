# FALCON Stream and Index Design

## Principle

Streams/index sets follow semantic/security/retention boundaries, not
arbitrary producer convenience.

## Initial logical streams

-   HERMES market evidence
-   ARES context/event evidence
-   HELIOS strategy/evaluation evidence
-   HELIOS Trade Suggestions (the registered `helios.strategy_trigger`
    family)
-   TRON execution/outcome evidence
-   FALCON operational/security evidence

HELIOS Trade Suggestions receive the strictest read/write permissions.

## Indexing

Only registered searchable fields are mapped. Avoid uncontrolled field
explosion. Decimal-string audit values may have numeric mirror fields
for aggregation.

## Retention

Retention is assigned by FALCON registry class, not hard-coded by
producer.

Initial classes: - `PERMANENT_TRADING_EVIDENCE` -
`LONG_RESEARCH_EVIDENCE` - `MEDIUM_OPERATIONAL_EVIDENCE` -
`SHORT_HEALTH_TELEMETRY`

Exact durations are established by PID-10 using measured volume,
research value, licensing and production cost.
