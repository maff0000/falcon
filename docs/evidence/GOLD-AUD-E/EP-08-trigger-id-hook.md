# EP-8: Trigger-id hook

This audit **designs nothing** here. `GOAL-TRIGGER-001` alone owns signed-trigger, outbox and inbox semantics. This part records, field by field, how the candidate's evidence-relevant fields line up with what FALCON has registered, and which conflicts a later item must resolve.

Sources: falcon `8f218ec1b85b932285b042a7b1ae64dbd11eebee` (`schemas/payloads/helios/strategy_trigger.v1.schema.json`, `schemas/payloads/tron/trigger_observed.v1.schema.json`, `registry/field_registry.v1.json`, the content pack); `GOAL-TRIGGER-001` **candidate**, GOAL branch `wo/GOAL-CONTRACT-TRIGGER` `64c843b901d435a17efa56e3b2a1f925ad58c30b`, `pids/GOAL-TRIGGER-001.md`, section "Proposed design" signed-fields table. The candidate is **not approved and not on GOAL `main`** (`ceaf0291`); if it changes the trigger id or evidence-event names this EP must be re-read (PID stop condition). Status labels here are mapping labels; every row is PROVEN by reading both sides.

## 1. Field-level mapping: candidate signed fields to the registered `helios.strategy_trigger` payload

Legend: MATCH = same name and compatible; RENAME = same concept, different registered name; MISSING = no registered counterpart; CONFLICT = registered counterpart exists and disagrees (format, value domain, source or enum).

| # | Candidate field | Registered counterpart | Status | Detail |
|---|---|---|---|---|
| 1 | `schema` | none in payload (`payload_schema_version` is an envelope field) | MISSING | |
| 2 | `trigger_id` | `trigger_id` | CONFLICT | registered: any string, `minLength: 1` (fixture value `helios-trigger-0001`); candidate: `trg1_` plus 64 lowercase hex of SHA-256 of the occurrence key |
| 3 | `strategy_id` | `strategy_id` | MATCH | |
| 4 | `strategy_version` | `strategy_version` | MATCH | |
| 5 | `strategy_fingerprint` | `semantic_fingerprint` (required) | RENAME | HELIOS does not publish its fingerprint today (falcon PID07 s12 row 5) |
| 6 | `binding_id` | `parameter_set_id` (required) | RENAME | concept equivalence is an assumption; HELIOS has no distinct parameter-set id (PID07 s12 row 6) |
| 7 | `execution_policy_ref` | none | MISSING | |
| 8 | `instrument_id` | `instrument_id` | CONFLICT | value domain: valid fixtures use the compact form, the candidate's example and the recorded ARES acceptance use the underscore form; no registry rule fixes one |
| 9 | `timeframe` | `timeframe` (enum of 8 tokens) | MATCH | |
| 10 | `signal_class` | none (`action_type` is the nearest) | MISSING | |
| 11 | `output_direction` | `direction` | CONFLICT | registered enum includes `FLAT`, which the candidate removes |
| 12 | `state_from` | none in this family (`state_before` exists in `helios.strategy_evaluated`) | MISSING | |
| 13 | `state_to` | none in this family (`state_after` likewise) | MISSING | |
| 14 | `setup_origin_bar_utc` | none | MISSING | |
| 15 | `bar_close_utc` | none (`trigger_at_utc` is the nearest) | MISSING | mapping not specified by either side |
| 16 | `valid_from_utc` | `valid_from_utc` | CONFLICT | registered pattern allows 0 to 9 fractional digits and `Z` or `+00:00`; candidate is fixed width |
| 17 | `valid_until_utc` | `valid_until_utc` | CONFLICT | same |
| 18 | `evaluation_id` | `evaluation_id` (required) | CONFLICT | source: HELIOS source and docs contain no `evaluation_id` (EP-4) |
| 19 | `input_snapshot_id` | `input_snapshot_id` (required) | CONFLICT | source: HELIOS has no snapshot id; its input record is timestamp-based freshness (PID07 s12 row 7) |
| 20 | `input_snapshot_hash` | `input_snapshot_hash` (required, `sha256:` pattern) | CONFLICT | source: not a content hash in HELIOS today |
| 21 | `reference_levels` (list of role and value) | `reference_price_*`, `stop_loss_*`, `take_profit_*`, `invalidation_*`, `target_*` | CONFLICT | the candidate forbids stop-loss and take-profit names; `reference_price_decimal` is required in the registered schema |
| 22 | `signing_key_id` | `signing_key_id` | MATCH | |
| 23 | `signature` | `signature` | MATCH | field exists; canonical form and algorithm are owned by the candidate |

Totals: 23 candidate fields. **5 MATCH, 2 RENAME, 7 MISSING, 9 CONFLICT.** Only 5 fields carry over unchanged. The 9 CONFLICT rows split into two kinds. Schema-compatible narrowing (the registered schema would accept the candidate value; 4 rows): `trigger_id`, `output_direction`, `valid_from_utc`, `valid_until_utc`. Incompatible, unsupplied or convention conflicts (5 rows): `instrument_id` (the schema accepts any string; the value-domain convention differs), `evaluation_id`, `input_snapshot_id`, `input_snapshot_hash` (not published by HELIOS), `reference_levels` (different structure and forbidden names).

Registered fields **required** by the schema and by the live-pipeline rule that the candidate does not provide: `action_type`, `trigger_at_utc`, `reference_price_decimal`, and (under the renames) `semantic_fingerprint`, `parameter_set_id`. An event conforming to the candidate would be flagged `falcon_missing_required_payload_field` and quarantined under the current pipeline definition (rule source in the content pack). PROVEN by rule source; live behaviour UNVERIFIED.

## 2. The same for `tron.trigger_observed`

Registered payload: `local_trigger_id`, `source_trigger_id`, `instrument_id`, `signature_status` (`VALID`, `INVALID`, `EXPIRED_KEY`, `UNKNOWN`), all required.

| Aspect | Status | Detail |
|---|---|---|
| Identity | CONFLICT | `local_trigger_id` (a TRON-minted id) and `source_trigger_id` (the HELIOS id) were built for a discovery model with two ids. Under a deterministic `trigger_id` there is one id. `trigger_id` itself is registered **only** for `helios.strategy_trigger` (`allowed_families`), so a TRON event carrying `trigger_id` would be flagged as a payload field outside its family. |
| Outcome | CONFLICT | `signature_status` has 4 values; the candidate has 12 terminal outcomes (EP-5) |
| Instance attribution | MISSING as a field | doctrine maps the instance identity onto `producer_component_id`, which is allow-listed (EP-6 G1) |

## 3. Hook requirements from the PID, checked

| # | Requirement | Finding | Label |
|---|---|---|---|
| H1 | Every trigger-related evidence event carries `trigger_id` as a registered, searchable, exact-match field | Registered only for `helios.strategy_trigger`; `local_trigger_id` is registered for three TRON families. The pipeline flattens payload JSON into `payload_*` fields, so a registered `trigger_id` would be searchable as `payload_trigger_id`; whether the index maps it as an exact-match keyword is UNVERIFIED (needs the index mapping). | PARTIAL / UNVERIFIED |
| H2 | `tron_instance_id` where the event is TRON-side | Not a registered field. The doctrine maps the governed instance identity onto the envelope field `producer_component_id` and the hostname onto `producer_instance_id` (`docs/contracts/TRON-FALCON-CONTRACT.md` lines 54 to 111). The pipeline accepts only two TRON component names. | PARTIAL |
| H3 | `signing_key_id` | Registered payload field for `helios.strategy_trigger` only | PARTIAL |
| H4 | Full signed envelope preserved losslessly as producer-owned payload (Decision 32 pattern) | Mechanism exists and is proven for ARES (`ares_market_status_raw_json`, `docs/architecture/04-PRODUCER-CONTRACT-EVOLUTION-DOCTRINE.md` s1; PID06 evidence s2). No family-named raw-preservation field exists for HELIOS or TRON. | MISSING |
| H5 | FALCON assigns its own `falcon_event_id`, and never mints, derives or validates `trigger_id` | **Correction to the hook wording:** `falcon_event_id` is **producer-assigned** in the current design (`registry/field_registry.v1.json`, `falcon_event_id`: `authoritative_producer: producer`, "stable across producer retry", "never derived solely from payload content"; Decisions 22 and 23: producers construct their own events). FALCON itself sets only `falcon_ingested_at_utc` (rule `FALCON - Set falcon_ingested_at_utc`). The substantive invariant holds: FALCON does not mint or derive `trigger_id`, and no rule validates it beyond presence. | CONFLICT (wording), invariant PROVEN |
| H6 | Evidence idempotent on `(trigger_id, event_kind, tron_instance_id)` at the reader; FALCON no dedupe authority | FALCON provides none (Decision 15; `docs/contracts/TRON-FALCON-CONTRACT.md` lines 45 to 52). `event_kind` has a natural home in the envelope `evidence_type` (`allowed_families: *`), but the candidate's `trigger_emitted`, `trigger_received`, `trigger_disposed` are not registered types. | PARTIAL |

## 4. What a later item must decide (owners)

| Decision | Owner |
|---|---|
| Pick which side moves: the candidate's evidence fields, or a new registered payload for the frozen contract (the candidate cannot change HELIOS's refusal of execution vocabulary) | FALCON-T3 after the contract freeze |
| Allow `trigger_id`, `signing_key_id` and a raw-preservation field for `tron.*` and for new disposition types | FALCON-T3 |
| Resolve `evaluation_id`, `input_snapshot_id`, `input_snapshot_hash` between the candidate (signed linkage) and HELIOS (which emits none today) | CA (contract) with HELIOS owner |
| Fix the instrument naming form across fixtures, producers and the contract | CA / FALCON-T1 |
| Fix the `falcon_event_id` wording in the hook | PO, on this EP |
