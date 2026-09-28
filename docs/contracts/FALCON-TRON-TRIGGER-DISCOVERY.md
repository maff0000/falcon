# FALCON → TRON Trigger Discovery Contract

## Query scope

TRON credentials are read-only and restricted to the HELIOS
executable-trigger surface required by that TRON deployment.

## Windowing

Use overlap windows rather than exact last-poll boundaries. MVP default
design target is 10 minutes of overlap, subject to empirical
latency/volume testing. Local durable dedupe makes overlap safe.

## Required filters

At minimum: - registered `helios.strategy_trigger`; - supported
instrument; - supported environment; - validity window; - ingestion lag
within policy; - schema supported.

## Response

FALCON returns evidence; it does not tell TRON "execute." TRON
independently verifies trigger signature and applies admission/execution
authority.

## Health

TRON must distinguish: - FALCON unreachable; - query/auth failure; -
excessive ingestion lag; - no matching trigger; - invalid/untrusted
trigger.

"No result" must never conceal infrastructure failure.
