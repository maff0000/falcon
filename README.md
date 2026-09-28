# FALCON --- THE GOAL Trading Evidence Plane

**Status:** Architecture and build baseline\
**Development authority:** `dell-debian:/srv/falcon`\
**GitHub:** `maff0000/falcon`\
**Time standard:** UTC only\
**Build engineering:** Rogue / FORGE\
**Independent assurance:** R2D2\
**Infrastructure / operations:** HELM

FALCON is THE GOAL's canonical trading-evidence, correlation, search and
operational-observability plane. Graylog is the principal implementation
technology and technical GUI, but Graylog is infrastructure behind
FALCON contracts and owns no trading semantics.

## Active producer/consumer model

``` text
HERMES ─────┐
ARES ───────┼────► FALCON ingress ───► Graylog/Data Node
HELIOS ─────┤              │                  │
TRON ───────┘              │                  ├── technical GUI
                            │                  ├── NEO research
                            │                  └── TRON trigger discovery
                            └── canonical validation/correlation
```

Authority: - **HERMES** --- governed market truth. - **ARES** ---
governed risk/news/event/context truth; advisory unless separately
promoted by architecture. - **HELIOS** --- deterministic
strategy/evaluation/trigger truth; execution-blind. - **TRON** ---
admission, execution, broker, fill, position and outcome truth. -
**FALCON** --- evidence, correlation, search, provenance and
operational-observability truth. - **NEO** --- retrospective
research/review consumer.

define FALCON contracts, and should be retired separately as soon as
remaining dependencies are safely removed.

## Development doctrine

DEV is intentionally safe to break and rebuild. Paper-trading TRON is
used while contracts, latency, retention, sizing, failure behaviour and
operator workflows are proven. Production is a separate purpose-built
environment promoted only after evidence-based sizing and assurance.

## Repository map

-   `docs/architecture/` --- authoritative system architecture.
-   `docs/contracts/` --- cross-system contracts and registries.
-   `docs/security/` --- trust, authentication and signing.
-   `docs/graylog/` --- Graylog implementation and GUI model.
-   `docs/operations/` --- configuration, recovery and observability.
-   `docs/engineering/` --- capacity and production promotion.
-   `docs/governance/` --- Git, testing, R2D2 and decisions.
-   `pids/` --- bounded deployment/build PIDs executed by Rogue/FORGE.
-   `schemas/` --- future machine-readable event schemas.
-   `registry/` --- future machine-readable field/event/component
    registries.
-   `config/` --- version-controlled non-secret configuration templates.
-   `deploy/` --- Docker/Compose deployment assets.
-   `tests/` --- contract, integration, replay and acceptance tests.

## Completion law

A PID, epic, story or work order is not complete because documentation
or code exists. It is complete only when the required behaviour is
running, tested, evidenced, independently audited where required, merged
cleanly, and the authoritative documentation reflects reality.
