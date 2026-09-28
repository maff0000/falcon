# FALCON --- THE GOAL Trading Evidence Plane

**Status:** Architecture and build baseline\
**Development authority:** `dell-debian:/srv/falcon`\
**GitHub:** `maff0000/falcon`\
**Time standard:** UTC only\
**Build engineering:** Rogue / FORGE\
**Independent assurance:** FORGE Auditor (R2D2 by exception)\
**Infrastructure / operations:** HELM

## Repository identity — read before any FALCON work

The canonical FALCON identity triplet is:

```text
DEV HOST:  dell-debian
DEV PATH:  /srv/falcon
GITHUB:    maff0000/falcon
```

**There is an unrelated, older repository at the identical-looking path
`/srv/falcon` on Trinity.** That path there holds `maff0000/trading-falcon`
— a different, legacy implementation with its own application code,
migrations and history. It is not this project and must not be touched
during FALCON work.

Never infer repository identity from the path `/srv/falcon` alone — the
same path means two different projects on two different hosts. Before any
FALCON action, verify all three:

```bash
hostname            # must be dell-debian
git remote -v        # must be https://github.com/maff0000/falcon.git
git rev-parse HEAD   # compare against the known canonical SHA
```

FALCON is THE GOAL's canonical trading-evidence, correlation, search and
operational-observability plane. Graylog is the principal implementation
technology and technical GUI, but Graylog is infrastructure behind
FALCON contracts and owns no trading semantics.

## Active producer/consumer model

``` text
HERMES ──────┐
ARES ────────┤
HELIOS ──────┼──── structured FALCON events ────► Graylog-FALCON
TRON ────────┘                                      │
                                                    ├── inputs
                                                    ├── pipelines
                                                    ├── streams
                                                    ├── journal
                                                    ├── Data Node
                                                    ├── indexes
                                                    ├── search
                                                    ├── alerts
                                                    ├── dashboards
                                                    └── API
                                                         │
                                    ┌────────────────────┼───────────────────┐
                                    ▼                    ▼                   ▼
                            technical GUI            NEO research    TRON Trade Suggestion
                                                                        discovery + admission
```

Each producer constructs its own conformant FalconEvent (PID-01's
universal envelope + typed family schema) and sends it via an
authorised Graylog-native transport. There is no bespoke FALCON
middleware service standing between producers and Graylog.

Authority: - **HERMES** --- governed market truth. - **ARES** ---
governed risk/news/event/context truth; advisory unless separately
promoted by architecture. - **HELIOS** --- deterministic
strategy/evaluation/Trade Suggestion truth; execution-blind. - **TRON**
--- admission, execution, broker, fill, position and outcome truth. -
**FALCON** --- evidence, correlation, search, provenance and
operational-observability truth. - **NEO** --- retrospective
research/review consumer.

Legacy or non-canonical ARES implementations (including the prior tradingRisk-fleet ARES) do not
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
