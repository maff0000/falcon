# EP-7: Volume and retention

**Everything numeric in this document is an ESTIMATE derived from design cadence and fixture sizes. It is not a measurement.** Measurement needs the running system and is UNVERIFIED (EP-2). The capacity model itself contains no numbers: `docs/engineering/FALCON-CAPACITY-MODEL.md` is a metric list and ends "No production server size is guessed before measurements exist."

Audited SHA: falcon `8f218ec1b85b932285b042a7b1ae64dbd11eebee`; HELIOS `7f7193d55475e40583892b94dd461b1b64d6f1ef`.

## 1. Inputs used

| Input | Value | Source | Label |
|---|---|---|---|
| Mean serialised FalconEvent size in the valid fixtures | HERMES 877 B, ARES 840 B, HELIOS 1,135 B, TRON 884 B (compact JSON) | computed from `tests/fixtures/valid/*.json` for this audit | PROVEN for the fixtures; real events are larger (ARES carries a 13-key raw payload; a HELIOS envelope carries components and inputs). A 5x pessimistic multiplier is applied below. |
| ARES `market_status` cadence | about 300 s (observed 300.05 s, configured 300 s) | PID06 evidence s8 | PROVEN as a record |
| HELIOS units evaluated per cycle | 5 (4 bound atoms and 1 reference chain), every unit published every cycle | falcon PID07 s2, s3, s4; HELIOS `docs/INTEGRATION.md` s1 | PARTIAL (deployment count is from PID07; the chain count is inferred from "shipped reference chain") |
| HELIOS cycle interval | `HELIOS_RUNTIME_TICK_SECONDS`, no default in source | HELIOS `helios/runtime/config.py:65` | UNMEASURED |
| HERMES cadence and volumes | no production cadence in the repository (PID-05 section C characterised synthetic rates) | `pids/PID-05-HERMES-INTEGRATION.md` s7 and Section C | UNMEASURED |
| TRON events per trade | counted from the registered lifecycle families | EP-5 | estimate |

## 2. Events per day per producer (ESTIMATE)

| Producer | Basis | Events per day | Bytes per day at fixture size | At 5x |
|---|---|---|---|---|
| ARES `market_status.session_state` | 86,400 / 300 | 288 | 0.24 MB | 1.2 MB |
| ARES other five families | not delivered | 0 today | 0 | 0 |
| HERMES (5 families) | UNMEASURED | UNMEASURED | UNMEASURED | UNMEASURED |
| HELIOS, publish every cycle, tick 60 s | 5 x 1,440 | 7,200 | 8.2 MB | 41 MB |
| HELIOS, publish every cycle, tick 300 s | 5 x 288 | 1,440 | 1.6 MB | 8.2 MB |
| HELIOS, publish on state change only (design option, P-H2) | one event per state transition | UNMEASURED (bounded above by the rows above) | UNMEASURED | UNMEASURED |
| TRON, per executed trade | about 14 events (trigger, admission, intent, submitted, 2 updates, 1 fill, 2 position states, 2 protection states, exit, outcome, quality) | 14 per trade | 12 KB per trade | 62 KB per trade |
| TRON, per refused trigger | 2 events (trigger, admission) | 2 per refusal | 1.8 KB | 9 KB |
| TRON health | UNMEASURED | UNMEASURED | UNMEASURED | UNMEASURED |

Reading: HELIOS publish-every-cycle dominates TRON trade events by one to two orders of magnitude (about 10x to 68x for up to ten trades a day in the table above), but at megabyte-per-day scale. The open decisions are the HELIOS publication policy (every cycle versus on change, with a periodic keyframe) and the HELIOS tick; both are inputs for P-H2 and for PID-10. Event-day bursts, index expansion, and journal growth are UNMEASURED.

## 3. Retention class per family

Facts:

- The envelope `retention_class` enum is `standard`, `extended`, `short` (`schemas/falcon-event-envelope/v1/envelope.schema.json`). Every one of the 141 fields in `registry/field_registry.v1.json` is `standard`, and every valid fixture carries `standard` (EP-3). PROVEN.
- The four classes named in the stream design (`PERMANENT_TRADING_EVIDENCE`, `LONG_RESEARCH_EVIDENCE`, `MEDIUM_OPERATIONAL_EVIDENCE`, `SHORT_HEALTH_TELEMETRY`) are not values of that enum, and "exact durations are established by PID-10" (`docs/graylog/FALCON-STREAM-INDEX-DESIGN.md`). PROVEN. No durations exist anywhere in the repository.
- The family registry does not carry a retention class per family. PROVEN (field absent from `registry/event_family_registry.v1.json`).

Proposal (audit opinion, for PID-10, labelled as such; it decides nothing):

| Proposed class | Families |
|---|---|
| `PERMANENT_TRADING_EVIDENCE` | `helios.strategy_trigger`; `tron.trigger_observed`, `tron.admission_decision`, `tron.order_intent`, `tron.order_submitted`, `tron.order_update`, `tron.fill`, `tron.position_state`, `tron.protection_state`, `tron.exit`, `tron.trade_outcome`, `tron.execution_quality`; plus any added disposition and reconciliation types |
| `LONG_RESEARCH_EVIDENCE` | `helios.strategy_state` (and the families it absorbs), `hermes.market_fact`, `hermes.market_state`, `hermes.market_quality`, `hermes.signal_state`, `ares.calendar.event_state`, `ares.market_status.session_state`, `ares.liquidity.state`, `ares.macro_usd.breadth_state`, `ares.publication.decision` |
| `MEDIUM_OPERATIONAL_EVIDENCE` | `ares.source_quality.transition` |
| `SHORT_HEALTH_TELEMETRY` | `hermes.health`, `tron.health` (and `helios.health` if kept) |

Because the durable record of every trade decision is the local journal of the publisher and TRON (EP-9), a FALCON retention shorter than the trading horizon does not lose the record; it loses the convenience copy.

## 4. UNMEASURED list

HERMES cadence and volume; HELIOS tick and publication policy; TRON trade count and health cadence; real event sizes; burst profile around scheduled events; index expansion factor; journal growth; query load; backup size; retention durations. Each needs either the running system's counters (D-4) or the follow-on items' measurements.
