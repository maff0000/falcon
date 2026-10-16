# EP-5: TRON needs

Sources: falcon `8f218ec1b85b932285b042a7b1ae64dbd11eebee`; TRON `main` `5577039b5db05e70effef72c7e59df14db408419` (`PID.md`, `scripts/hooks/pre-commit`, `.gitignore`, `.gitleaks.toml` only); TRON branch `wo/WO-TRON-D1` `37d5f009a080d25930eea37cf8c627bb0f3a1ff4` (design documents, JSON schemas, one Python file). `GOAL-TRIGGER-001` candidate at GOAL branch `wo/GOAL-CONTRACT-TRIGGER` `64c843b901d435a17efa56e3b2a1f925ad58c30b`.

## 1. What TRON is, in source

| Fact | Evidence | Label |
|---|---|---|
| TRON `main` holds no runtime or publisher code: a design record (`PID.md`, 1,587 lines) and a pre-commit hook | `git ls-tree` of `main` at `5577039` | PROVEN |
| The design branch holds documents `docs/01` to `docs/12`, config examples and JSON schemas; its only Python file is `tests/test_docs_baseline.py` | `git ls-tree` of `37d5f00` | PROVEN |
| Nothing in TRON emits a FalconEvent. TRON's own event model is `tron.event.v1` with 20 dot-namespaced event types and a mandatory `correlation_id` | `wo/WO-TRON-D1` `docs/09-EVENTS-AND-GRAYLOG.md` s2.1; `docs/05-CONTRACTS.md` s8 (line 97 on) | PROVEN |
| TRON's design is journal first, then spool and ship; a downstream outage "must not cause execution history to disappear"; no execution when the local journal write cannot be made | `PID.md` s14.3 (line 749 on); `docs/09` s1 | PROVEN (design) |
| Where the "Trading Graylog" lives and its transport are undecided (`DEC-OPEN-07`); whether it is FALCON is not stated | `PID.md` line 1033 | PROVEN (open decision) |
| TRON's inbound model in the design is a candidate-action board and `falcon.trade_action.v1`, with stop-loss and take-profit required on OPEN, not FALCON discovery of `helios.strategy_trigger` | `PID.md` s9.2 (line 463), s4.4 (line 201), DEC-OPEN-05 | PROVEN |

So TRON has **three different pictures** of its own evidence and intake: the registered FALCON `tron.*` families (built for a discovery model), the D1 `tron.event.v1` catalogue (built for a board model), and the candidate trigger inbox. The minimum publication work must pick one evidence shape (below).

## 2. Lifecycle gap analysis (CA lifecycle: claim, risk, order, fill, reconcile)

| CA stage | Registered family (closest) | Gap | Label |
|---|---|---|---|
| claim (receipt, claim, disposition) | `tron.trigger_observed` | The family says "observed" (a discovery-poll concept) with `local_trigger_id`, `source_trigger_id`, `signature_status`. No receipt, claim or terminal disposition record, and no closed outcome vocabulary. `GOAL-TRIGGER-001` defines 12 outcomes. | MISSING (disposition) |
| risk / admission | `tron.admission_decision` (2 required fields: `local_trigger_id`, `admission_outcome`) | Closed vocabulary exists but is smaller: `admission_outcome` is `ADMITTED` or `REJECTED`, with an optional `rejection_reason` of `DUPLICATE`, `EXPIRED`, `INVALID_SIGNATURE`, `UNSERVICEABLE`, `CHECK_FAILED`, `OTHER_REJECTED` (6). `GOAL-TRIGGER-001` defines 12 terminal outcomes (REJECTED_KEY, REJECTED_CLOCK, REJECTED_STRATEGY, CONFLICT, SUPERSEDED, EXECUTION_REJECTED, ABANDONED_UNRESOLVED have no equivalent). | PARTIAL |
| order | `tron.order_intent`, `tron.order_submitted`, `tron.order_update` | `order_intent` requires `quantity_decimal` and `order_type` (sizing is TRON-owned, fine). Requires `local_trigger_id`, which has no stable definition under a deterministic `trigger_id` (EP-8). | PARTIAL |
| fill | `tron.fill`, `tron.position_state`, `tron.protection_state`, `tron.exit`, `tron.trade_outcome`, `tron.execution_quality` | Families exist and have fixtures. TRON D1 emits no `exit`, `position_state` or `execution_quality` events (not in the 20-type catalogue), because close, modify and cancel are later capabilities (`docs/09` s2.2). | PARTIAL |
| reconcile | none | TRON emits `reconciliation.completed` and `reconciliation.failed`; no family exists. | MISSING |
| health | `tron.health` | TRON has `system.degraded`, `system.halted`; shape unmapped. | PARTIAL |

## 3. TRON D1 events mapped to FALCON families

| TRON D1 event (`docs/09` s2.1) | FALCON family | Mapping status |
|---|---|---|
| `action.received` | `tron.trigger_observed` | semantic match only if the intake model is the inbox, not the board |
| `action.rejected`, `action.expired`, `action.duplicate` | none | MISSING: needs a disposition type (FALCON-T3) |
| `action.selected` | none | not a terminal; candidate for the disposition family or omit |
| `intent.created` | `tron.order_intent` | PARTIAL |
| `check.stage.completed`, `check.failed` | `tron.admission_decision` | PARTIAL (one decision versus per-check records) |
| `execution.submitted` | `tron.order_submitted` | match |
| `execution.accepted`, `execution.rejected`, `execution.partial_fill`, `execution.filled` | `tron.order_update`, `tron.fill` | match, with `execution_id` to `fill_id` and `order_id` to `broker_order_id` renames |
| `protection.verified`, `protection.failed` | `tron.protection_state` | match |
| `reconciliation.completed`, `reconciliation.failed` | none | MISSING |
| `trade.completed` | `tron.trade_outcome` | PARTIAL (registered outcome requires `realised_pnl_decimal` and `outcome_classification`) |
| `system.degraded`, `system.halted` | `tron.health` | PARTIAL |
| none | `tron.position_state`, `tron.exit`, `tron.execution_quality` | registered, no TRON D1 source event |

Counts, by reading the table above (not generated): of the 20 D1 events, 8 map to a registered family (`action.received`, `execution.submitted`, `execution.accepted`, `execution.rejected`, `execution.partial_fill`, `execution.filled`, `protection.verified`, `protection.failed`), 6 map partially (`intent.created`, `check.stage.completed`, `check.failed`, `trade.completed`, `system.degraded`, `system.halted`) and 6 have no family (`action.rejected`, `action.expired`, `action.duplicate`, `action.selected`, `reconciliation.completed`, `reconciliation.failed`).

## 4. Missing families (candidates for FALCON-T3 to rule on, not decided here)

1. **Trigger disposition** (`trigger_received`, `trigger_disposed` with the closed outcome vocabulary of `GOAL-TRIGGER-001`). Decision: a new type inside `tron.trigger_observed`, or a new family. Recommendation for T3 to weigh: new types under one family, to avoid a new input and stream (EP-6).
2. **Broker reconciliation result** (completed, failed, scope: lineage or sweep).
3. A stable **instance attribution** field: today attribution relies on `producer_component_id` carrying a per-instance value (`docs/contracts/TRON-FALCON-CONTRACT.md` lines 54 to 111). The live pipeline rejects any component name not in its allow-list, so a per-instance name is quarantined until the allow-list and component registry are revised (EP-6). PROVEN from the rule source in the content pack.

## 5. Needs, minimum (feeds `MINIMUM-WORK-LIST.md`)

| Need | Why | Work item |
|---|---|---|
| Evidence emitter: local journal first, then bounded asynchronous emission through a local spool; nothing in the decision path reads FALCON | TRON's own design already requires journal-first and spool-then-ship (`PID.md` s14.3). The FALCON side needs the shape and the non-blocking guarantees. | P-T1 |
| One evidence shape for FALCON: either an adapter that renders each D1 event into a FalconEvent, or a FALCON registry change that adopts the D1 catalogue | Avoids two parallel TRON evidence models | P-T2 (decision in FALCON-T3) |
| Lifecycle events carry `trigger_id` and the instance identity | Correlation (EP-8) | P-T2 |
| Per-instance component registration and a matching ingestion input and identity rule | EP-6 | P-T2 (FALCON side) |

## 6. UNVERIFIED in this EP

TRON runtime behaviour (none exists in the source read); whether other TRON branches or private repositories hold publisher code (only the branches listed were read).
