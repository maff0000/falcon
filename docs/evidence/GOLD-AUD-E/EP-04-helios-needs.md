# EP-4: HELIOS needs

Sources: falcon `8f218ec1b85b932285b042a7b1ae64dbd11eebee` (registry, schemas, content pack, `docs/architecture/PID07-HELIOS-STAGE1-DISCOVERY.md`), HELIOS `7f7193d55475e40583892b94dd461b1b64d6f1ef` (source and docs read for this audit). "PID07 sN" means that section of the falcon Stage 1 discovery document. Every HELIOS claim below was re-read in HELIOS source unless marked otherwise.

## 1. What HELIOS publishes today

| Fact | Evidence | Label |
|---|---|---|
| One envelope type, `helios.strategy_state/1.0.0`, for atomic and chain results, discriminated by `kind` | HELIOS `docs/CONTRACTS.md` s3 (line 225 on); `docs/INTEGRATION.md` s1.1 | PROVEN |
| Fields: `strategy_id`, `strategy_version`, `chain_id`, `chain_version`, `instrument`, `timeframe`, `semantic_role`, `state` (7 values), `direction`, `strength`, `evidence`, `explanation`, four lifecycle instants, `validity`, `components`, `inputs`; no publication timestamp, sequence or host identity | `docs/CONTRACTS.md` s3 table; `docs/INTEGRATION.md` s1.2 | PROVEN |
| No `evaluation_id` exists anywhere in HELIOS source or docs (`git grep evaluation_id` at the audited SHA returns 0 lines) | HELIOS `7f7193d` | PROVEN |
| No FALCON or Graylog publication code | PID07 s2 (line 64); HELIOS `docs/INTEGRATION.md` line 419: "No FALCON consumer has been connected" | PROVEN |
| Configured sinks are in-memory, stream and file; live deployments are documented as using the stream sink to standard output | HELIOS `helios/publish/sink.py` (lines 90, 125, 171); deployment use per PID07 s5 | PROVEN (code); deployment config UNVERIFIED here |

## 2. Failure semantics: publication is synchronous and fatal

| Step | Evidence |
|---|---|
| `evaluate_once()` calls `self._publisher.publish_all(envelopes)` in the main loop | HELIOS `helios/runtime/service.py:386` |
| `publish_all` iterates `publish`, and `publish` calls `self._sink.emit(payload)` with no catch | `helios/publish/publisher.py:98` and `:81` |
| The program entry catches only `HeliosError`; `run()` failure logs "runtime failed" and returns exit code 1 | `helios/runtime/service.py:613-617` |
| The sink interface is a three-method `Protocol` (`emit`, `flush`, `close`), so a decoupled sink is additive | `helios/publish/sink.py:38-60` |

Label: PROVEN. Consequence: any network sink added synchronously would make a FALCON fault a HELIOS fault. Requirement P-H1 (non-blocking sink, never raises into the evaluation loop) is the first item and is independent of every registry decision.

## 3. Registered versus needed, family by family

Lifecycle stages covered by HELIOS: strategy evaluation and trigger evidence. HELIOS has no claim, risk, order, fill or reconcile stage.

| Registered family | HELIOS can supply it? | Gap (evidence) | Disposition proposed |
|---|---|---|---|
| `helios.strategy_state` | **Yes, nearly.** Required: `strategy_id`, `instrument_id`, `state_value` (3). HELIOS has `state` (rename), `strategy_id`, `instrument`. Optional `timeframe`, `previous_state_value` (HELIOS does not publish the previous state; PID07 s12 row 9). The payload schema has `additionalProperties: false`, so `strength`, `evidence`, `explanation`, `components`, `inputs` need the raw-preservation field of the producer evolution doctrine (`docs/architecture/04-PRODUCER-CONTRACT-EVOLUTION-DOCTRINE.md` s1, line 43 on). The doctrine's example field is ARES's; no equivalent for HELIOS is registered. | Survivor family; add a family-named raw-preservation field; 7-value `state` | T1 / P-H2 |
| `helios.strategy_evaluated` | **No.** 13 required payload fields in the schema and in the live-pipeline rule. HELIOS supplies 4 (`strategy_id`, `strategy_version`, `instrument`, `state` as `state_after`); `timeframe` only for atomics (chains may state neither, `docs/CONTRACTS.md` line 238); 8 are not published by HELIOS (HELIOS computes an internal `definition_fingerprint()` that it does not publish, and `state_before` is derivable by diffing consecutive envelopes, PID07 s12 rows 5 and 9): `evaluation_id`, `semantic_fingerprint`, `parameter_set_id`, `input_snapshot_id`, `input_snapshot_hash`, `state_before`, `conditions_satisfied`, `conditions_failed`. A real HELIOS event sent to this family would be quarantined as missing required payload fields. | Collapse into `helios.strategy_state` | T1 / P-H2 |
| `helios.chain_state` | **No.** Requires `chain_id` and a 4-value `chain_state` (`PENDING`, `ACTIVE`, `COMPLETED`, `ABORTED` per PID07 s12 row 2) that does not match the 7-value HELIOS `state`. | Collapse | T1 / P-H2 |
| `helios.strategy_trigger` | **No.** HELIOS has no trigger concept, no signing, no `trigger_id` (PID07 s7, s13; HELIOS `docs/INTEGRATION.md` s1.2). Registered payload carries `stop_loss_*`, `take_profit_*`, `action_type` ENTRY/EXIT/ADJUST, `direction` incl. `FLAT`, free-string `trigger_id`, which the candidate trigger contract removes (EP-8). HELIOS forbids execution vocabulary mechanically (`tests/test_execution_blind.py`). | Reshape to the frozen trigger contract; owner of emission is open (D-6) | T3 / P-H4 |
| `helios.health` | **No.** HELIOS has no network sink and no bound port; health is a local status file for the container's own check (PID07 s10, s11). | Ruling needed (below) | T1 / P-H3 |

## 4. `helios.health` ruling options (P-H3)

| Option | Effect | Cost | Fit |
|---|---|---|---|
| (a) Retire the family | Health stays local; FALCON gets liveness only from the absence of state events | Registry removal (T1 delta; also a content-pack change if the pipeline rules name it) | Matches HELIOS design; recommended as the MVP default |
| (b) Keep family, define emission from the same non-blocking sink | One extra envelope kind or a separate health record through the P-H1 sink | New publisher surface in HELIOS; contract with `HELIOS` repo owner | Possible later; not needed for MVP evidence |
| (c) Keep the family unimplemented | Registered but never emitted | None now; permanent "live but not emitting" debt | Worst for the matrix honesty (EP-3 finding 3) |

Recommendation (labelled as an audit opinion for the FALCON architect, not a decision): (a). `evaluation_id` ruling: HELIOS mints none and `evaluation_id` is not in HELIOS's CER-owned tuple (`helios/contracts/identity.py:45-50` lists `experiment_id`, `run_id`, `evidence_id`, `artifact_id`), so the PID07 s12 row 3 statement that it "conflicts with doctrine" is an inference, not a source fact (PARTIAL). The facts are only: HELIOS emits none, and its runs are deliberately byte-diffable. If a correlation id is wanted, FALCON assigns it at ingestion or it is derived outside HELIOS (EP-8 shows the candidate trigger contract already lists `evaluation_id` as signed evidence linkage, which HELIOS cannot supply today: an open conflict for CA).

## 5. Other HELIOS facts that bound the work

| Fact | Evidence | Label |
|---|---|---|
| Live "dev" and "prod" HELIOS were reported to replay a fixed fixture window on loop, not live data | PID07 s14 (read from running containers by the falcon discovery team) | PARTIAL: PID07 is a source document; not re-observed here. Any evidence event from HELIOS must be labelled replay or fixture until HELIOS-T2 delivers a live feed, so replay is excluded from evidence (P-H2). |
| Published bytes are deterministic by design | HELIOS `docs/INTEGRATION.md` s1.2; `docs/CONTRACTS.md` s3.3 | PROVEN |
| Cycle interval is configuration (`HELIOS_RUNTIME_TICK_SECONDS`); no default in source | `helios/runtime/config.py:65` | PROVEN |
| No durable evidence record exists in the documented deployment (stdout only) | PID07 s5 | PARTIAL (deployment, not re-observed) |
| Chain evaluation is not wrapped in per-unit containment (self-disclosed debt) | PID07 s4 | PARTIAL |

## 6. What HELIOS must emit, minimum (feeds `MINIMUM-WORK-LIST.md`)

1. One state envelope per evaluated unit, losslessly, through a bounded non-blocking sink (P-H1, P-H2).
2. Replay and fixture-feed events marked so they cannot be mistaken for evidence of a live decision (P-H2).
3. Trigger evidence only after the trigger contract is frozen and the durable outbox commit has happened (P-H4); emitted by the publisher component, not by the pure engine (D-6 open).
