# FALCON Event Family Registry

## Initial families

### HERMES

-   `hermes.market_fact`
-   `hermes.market_state`
-   `hermes.market_quality`
-   `hermes.health`

Exact subtypes are registered from the approved HERMES allow-list. Raw
historical corpus events are not mirrored wholesale.

### ARES

-   `ares.calendar.event_state`
-   `ares.market_status.session_state`
-   `ares.liquidity.state`
-   `ares.macro_usd.breadth_state`
-   `ares.source_quality.transition`
-   `ares.publication.decision` (research/operational)
-   `ares.regime.nowcast` only after SQL-first authority assurance

Reserved but not live until implemented: - unscheduled news; - AI/model
market assessment; - mandatory restriction/veto; - calibrated risk
score.

### HELIOS

-   `helios.strategy_evaluated`
-   `helios.strategy_state`
-   `helios.chain_state`
-   `helios.strategy_trigger`
-   `helios.health`

### TRON

-   `tron.trigger_observed`
-   `tron.admission_decision`
-   `tron.order_intent`
-   `tron.order_submitted`
-   `tron.order_update`
-   `tron.fill`
-   `tron.position_state`
-   `tron.protection_state`
-   `tron.exit`
-   `tron.trade_outcome`
-   `tron.execution_quality`
-   `tron.health`

## Registration gate

No live event family exists until: - schema is versioned; - fields are
registered; - producer/component is registered; - authority class is
explicit; - retention/sensitivity are assigned; - sample fixture
validates; - ingress tests pass.
