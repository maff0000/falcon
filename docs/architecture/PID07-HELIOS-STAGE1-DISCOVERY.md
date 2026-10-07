# PID-07 Stage 1 — HELIOS Read-Only Discovery & Contract Reconciliation

**Purpose:** the durable Git record of PID-07 Stage 1: read-only discovery of the real, authoritative HELIOS
implementation, and reconciliation of FALCON's existing (pre-discovery, speculative) HELIOS assumptions
against it. No implementation, no runtime mutation, no HELIOS/FALCON code change accompanies this document.
Governed by `work-orders/WO-PID07-001-HELIOS-DISCOVERY.md`, inheriting the Producer Contract Evolution
Doctrine (`docs/architecture/04-PRODUCER-CONTRACT-EVOLUTION-DOCTRINE.md`, Decision 32).

**Method:** two independent read-only discovery passes (a primary discovery agent and a separate R2D2
independent-auditor pass, each working from scratch without seeing the other's conclusions), plus direct
verification by the Delivery Controller of FALCON's actual machine-readable registries/schemas (not just
prose documentation). The two independent passes converged on every material finding; no unresolved
disagreement between them exists. Where this document states a fact about HELIOS, it reflects that
convergence; items either pass flagged as unresolved are preserved as unresolved here, not guessed at.

## 1. HELIOS authority statement

**Authoritative application repository:** `maff0000/HELIOS`, checked out clean at `/srv/HELIOS` on
dell-debian, `origin/main` = **`7f7193d55475e40583892b94dd461b1b64d6f1ef`** ("Merge PR #1: HELIOS v1 —
independently audited PRODUCT_GREEN boundary"). Independently re-verified by both discovery passes via
`git remote -v`/`git log`, and by tracing the live containers' image digest and OCI labels back to this
repo's own `Dockerfile` (verbatim `LABEL description` match; no other HELIOS Dockerfile on the host declares
that string).

**Deployment/orchestration repository:** `maff0000/GOLD-STRATEGY-RUNTIME`, checked out at
`/srv/GOLD-STRATEGY-RUNTIME`, local HEAD `58914154da0864b0c9e9632b1379224430f9b10f`. Its
`compose/docker-compose.yml` builds the `helios` service image from `/srv/HELIOS`'s own unchanged
Dockerfile, runs `python3 -m helios.runtime`, supplies all `HELIOS_*` configuration externally
(`compose/env/{dev,prod}.env`, fail-loud `${VAR:?...}` syntax), publishes no ports, and uses a local
status-file healthcheck (no socket).

**A separate, related-but-different system:** `maff0000/HSA` ("Helios Strategy Architect") has its own repo
and its own deployed image (`images/hsa`). HELIOS's integration code (`helios/integration/hsa_boundary.py`)
is genuinely designed to consume HSA-shaped strategy packages via a read-only directory handoff — but see §9
below: the content actually loaded in the live dev/prod deployments today is HELIOS's own bundled test
fixtures, not real HSA output.

**Excluded as stale/legacy (confirmed, not authoritative):**
- `maff0000/trading-helios` (private GitHub repo) — last pushed 2026-06-22, no local checkout found, not
  referenced anywhere in the live deployment surface. Superseded by `maff0000/HELIOS`.
- Every `tradingProteus/helios`/`tradingProteus/helios_v3` path under `/srv-dev`, `/srv-dev-worktrees`,
  `/srv-operational` (dozens of worktree copies) — the legacy monorepo's own `RETIRED.md` (dated 2026-04-29)
  states explicitly: "Status: RETIRED — do not run, do not deploy, do not import," naming a different
  architecture entirely (a fabric-keyed daemon writing `tradingScalp.helios_v3_decisions` DB rows and
  `helios:state:XAU_USD` fabric keys — structurally nothing like current HELIOS's file/stream-sink model).
- `/etc/systemd/system/helios-v3.service` — confirmed `inactive (dead)`, `masked`, syntactically broken (no
  `ExecStart=`), dead cruft, not a competing deployment.
- `/root/.helios_legacy_staging`, `/srv/backup/helios_legacy_archive_20260904T193301Z` — archival only.

No other live, recently-active, or competing HELIOS deployment was found on the host (broad search across
all compose projects, all running containers, all recently-modified `*helios*` paths).

## 2. HELIOS architecture / topology (implemented-vs-planned)

| Capability | Status |
|---|---|
| Single-process replay-driven evaluation loop (`helios/runtime/service.py`) | **Implemented, running** |
| In-process `ThreadPoolExecutor` for atomic-strategy concurrency (deterministic ordering) | **Implemented, running** |
| HERMES live client/connection | **Not implemented** — "HELIOS v1 ships no live HERMES client," confirmed via dependency manifest (`pydantic`+`PyYAML` only, no DB/HTTP/socket library anywhere; mechanically enforced by the execution-blindness import guard) |
| HERMES data contract (file-based fact ingestion, freshness/schema checks) | **Implemented, running** — against a directory handoff (`HELIOS_RUNTIME_FEED_DIR`), not a live connection |
| Redis usage | **None** — no client, no dependency |
| SQL/persistence | **None** — stateless by design; only in-memory last-published-envelope state carried between cycles |
| Configuration (fail-loud, no in-code defaults for required settings) | **Implemented, running**, independently verified at `helios/config.py`/`helios/runtime/config.py` (file:line evidence in §8 below) |
| FALCON/Graylog publication | **Not implemented** — zero GELF/Graylog code anywhere; "FALCON" appears only as a documentation/fixture-naming reference to the downstream consumer |
| Execution-blindness (no trade/order/broker/account concept reachable) | **Implemented, running, mechanically enforced** — `tests/test_execution_blind.py` AST-scans every module under `helios/` for forbidden vocabulary and forbidden network imports |

## 3. Strategy model (HELIOS's own terminology, not FALCON's)

- **Strategy identity**: `StrategyIdentity(strategy_id, strategy_version)` — canonical form `golden_cross@1.0.0`, `strategy_id` pattern `^[a-z][a-z0-9_]{2,63}$`, `strategy_version` strict `major.minor.patch`.
- **Atomic strategy**: implements a `StrategyEvaluator` protocol; 6 proof atoms exist, 4 bound in the live deployment (`golden_cross`, `range_breakout`, `rejection_wick`, `swing_proximity`).
- **Composition/chain**: `ChainEngine` over `ALL`/`ANY`/`SEQUENCE`/`CONTEXT_TRIGGER` primitives, atomic-strategies-only in v1 (chain-of-chain explicitly refused pending future architecture authority).
- **"Trigger/fire"** → HELIOS's real term is **`MATCHED`** (the match edge — condition became true on this evaluation).
- **"Decline"** → no such term; a non-match is `DORMANT`/`FORMING`, always published with explanation, never omitted.
- **"Block/veto"** → does not exist as a concept. No strategy blocks another; chains express required-state composition, not veto.
- **"Near-miss"** → no formal state. `FORMING` (a declared precondition holds, full condition doesn't yet) is the nearest analogue; chains publish explicit per-component pass/fail explanation strings.
- **Strategy state**: a 7-value enum — `DORMANT, FORMING, MATCHED, ACTIVE, WEAKENING, INVALID, EXPIRED` — with a fully code-enforced legal-transition table (no illegal state jump possible).
- **Timeframe model**: the 4H/CONTEXT-1H/LOCATION-15M/CONFIRMATION-5M/TRIGGER template is genuinely implemented as the shipped reference chain (`gold_continuous_sequence`), but is **per-strategy-package configuration, not a global rule** — `SemanticRole`/`timeframe` are open tokens per input. A single *atomic* evaluation is bound to exactly one timeframe; a *chain* evaluation genuinely spans multiple timeframe contexts simultaneously by combining per-timeframe atomic components. Do not assume a single global `timeframe` field is sufficient for a chain-level event.

## 4. Strategy evaluation lifecycle

One call to `StrategyEvaluator.evaluate(EvaluationContext)` produces one `StrategyStateEnvelope`. Every bound
unit (atomic or chain) publishes on **every** cycle regardless of match status — a non-match is not omitted,
it is published as `DORMANT`/`FORMING` with full explanation. A raised exception during evaluation is
contained per-strategy (`_void_envelope`) and republished as an explicit `INVALID` envelope with
`evidence={"contained_failure_type": ...}`; sibling strategies are unaffected. **Chain evaluation is
explicitly not wrapped in the same per-atom containment** — this is self-disclosed, non-blocking technical
debt in HELIOS's own delivery evidence, proven only by fuzz-testing 3,136 combinations rather than by a
structural guarantee.

## 5. Evidence/reason model

Every envelope carries: `state`, `direction`, optional `strength` (0–1 decimal — HELIOS's real analogue of a
"quality" concept, under a different name), a flat scalar `evidence` map (strategy-declared, no nested
structure by design), a free-text `explanation` (chains spell out exactly which components satisfied/failed
and why), per-component `ComponentProvenance` for chains, per-input `InputFreshness` (timeframe, source,
schema version, age, freshness/completeness verdict — timestamp-based, **not** a content hash), and lifecycle
timestamps (`first_matched_at_utc`, `last_matched_at_utc`, `active_since_utc`, `last_evaluated_at_utc`,
`validity.valid_from_utc`/`valid_until_utc`). There is no separate "trigger event" record distinct from the
state envelope.

**Durability finding:** in both live deployments today, `HELIOS_PUBLICATION_SINK=STREAM` /
`HELIOS_PUBLICATION_STREAM=STDOUT` — published envelopes reach only the container's stdout, captured solely
by Docker's bounded `json-file` log driver (~100MB rolling cap). **No durable, append-only evidence record
exists on disk today**; a fully-implemented, tested `FileSink` exists in code but is not the configured sink
in either environment. This is a deployment-configuration fact, not a code defect.

## 6. HERMES dependency/input model

HELIOS identifies the facts behind an evaluation by `(instrument, timeframe, bar-open timestamp_utc)` plus a
`Provenance(source, schema_version, observed_at_utc, ingested_at_utc)` tuple — there is **no event ID,
natural key, Redis key, or dedicated correlation/signal ID** anywhere in the fact model. **Whether "what did
HELIOS know when it evaluated" is durably and tamper-evidently reconstructible is UNRESOLVED**: it depends
entirely on HERMES-side immutability of historical facts by `(instrument, timeframe, timestamp_utc)` as a
natural key, which HELIOS neither guarantees nor can verify from its own side — HELIOS captures no
independent hash/snapshot of the actual values it consumed.

## 7. Identity model

| Concept | Identity | Stability |
|---|---|---|
| Strategy | `(strategy_id, strategy_version)` | Immutable once promoted — mechanically enforced via a SHA-256 `definition_fingerprint()` over canonicalized behavioral content; a logic change without a version bump, or vice versa, raises `IdentityError` |
| Chain | `(chain_id, chain_version)` | Same immutability guarantee, structurally distinct type from strategy identity |
| Evaluation | **None** | No evaluation ID, UUID, or sequence number is ever minted — a deliberate design choice so runs are byte-diffable; identified only extrinsically by `(strategy_id@version, instrument, last_evaluated_at_utc)` |
| Trigger | **None distinct** | A "match" is just `state=MATCHED` on an envelope with no evaluation ID |
| Trade suggestion | **Does not exist** | Zero code, zero concept — confirmed by targeted grep across the entire repo |
| Runtime occurrence state | N/A | Explicitly **not persisted**; reset to cold start on every restart and on every feed-replay-loop boundary (deliberate, tested determinism property) |

A dedicated architectural rule actively **forbids** HELIOS from minting certain identifiers at all:
`helios/integration/cer_boundary.py` defines `CER_OWNED_IDENTITY_FIELDS = ("experiment_id", "run_id",
"evidence_id", "artifact_id")`, mechanically enforced by `assert_publishes_no_cer_owned_field` — these
identities belong to a separate evidence-store system (CER) and must originate there or at FALCON's own
ingestion boundary, not from HELIOS. **This directly argues against FALCON expecting a HELIOS-minted
`evaluation_id` field (see §13).**

## 8. UTC audit

**Fully compliant — a textbook-clean implementation, independently verified twice.**

- `helios/clock.py:20-22` `utc_now()` — the sole wall-clock source used throughout the service
  (`StrategyRuntime`, health, `serve()`), always `datetime.now(timezone.utc)`.
- `helios/clock.py:25-42` `ensure_utc()` — raises `ContractViolationError` on any naive datetime; converts
  aware-non-UTC datetimes via `.astimezone(timezone.utc)` rather than reinterpreting silently.
- `helios/clock.py:44-68` fixed-width `YYYY-MM-DDTHH:MM:SS.ffffffZ` serialization; parsing rejects any string
  lacking a UTC offset.
- `helios/contracts/_fields.py`'s `UtcDatetime` pydantic type enforces the same rule at every model boundary.
- Zero occurrences of naive `datetime.now()`/`datetime.utcnow()` found anywhere else in the tree.
- Independently audited by HELIOS's own PRODUCT_GREEN process via a 241-object reachability sweep plus
  hostile-environment testing (varying `TZ`, `PYTHONHASHSEED`, `LC_ALL`, decimal context) asserting
  byte-identical output. Nothing found in this discovery contradicts that audit.

No findings of concern; no severity items to report.

## 9. Configuration audit

**Fully compliant for all required settings**, independently verified twice at `helios/config.py` (400+
lines) and `helios/runtime/config.py`: every required setting is collected into a `problems` list if absent
(no fallback value in source), and `ConfigurationError` reports every missing/invalid setting at once, not
one restart at a time. The deployment layer reinforces this with `${VAR:?...}` Compose syntax.

**One self-disclosed, real exception**: HELIOS's own PRODUCT_GREEN delivery evidence states configuration is
"the one input surface that is not closed-world" — unknown keys and *optional* settings are silently ignored
rather than refused (confirmed in code: absent `OPTIONAL_SETTINGS` resolve to `None`). A misspelled optional
env var would be silently ignored unless later required by `.runtime()`. No hardcoded behavioral trading
constants exist in `config.py` itself; strategy-level parameters come from HSA package files, not HELIOS
source.

## 10. Failure semantics

| Condition | Behaviour |
|---|---|
| HERMES unavailable | Not a live scenario (no HERMES client exists). Missing/empty/inconsistent feed directory → loud `ContractViolationError` at startup, exit code 2 |
| Fact stale | `StaleFactError` on use, contained per-strategy → republished as `INVALID` for that strategy only, logged `WARNING` pre-evaluation, recorded in every envelope's `inputs` |
| Strategy config invalid | `StrategySpecError` at startup, before any evaluation — exit code 2 ("wrong at startup, not three hours in") |
| Evaluation throws (atomic) | Contained, republished as `INVALID` with `contained_failure_type`, logged `ERROR`, siblings unaffected |
| Evaluation throws (chain) | **Not structurally contained** — holds only by fuzz-test proof, not by design guarantee (self-disclosed follow-up) |
| Publish-sink failure | **Not caught anywhere** — propagates through `publish_all()` → `evaluate_once()` → `_loop()` → `run()` → `serve()`, logged `CRITICAL`, **process exits 1**. **Publication is currently fully synchronous/blocking, not best-effort.** |
| Existing FALCON/Graylog path | None exists |

**Structural readiness for a future non-blocking publisher**: `PublicationSink` is a small `Protocol`
(`emit`/`flush`/`close`); three sink implementations already exist and are selected purely by configuration.
Adding a Graylog-native sink is additive, not a rearchitecture — **but** `evaluate_once()` calls
`publish_all()` synchronously inside the main loop today, so a naive network sink implementation would
reproduce exactly the anti-pattern PID-05/PID-06 ruled must never happen. **This is the single most important
engineering note for the future PID-07 implementation stage: any network/Graylog sink must be
async/buffered/decoupled from the evaluation loop's critical path, not a direct synchronous call.** No
structural obstacle prevents this; it is simply not built yet.

## 11. Security/signing current state

No producer identity, signing mechanism, certificate, or key-management code exists anywhere in HELIOS
(confirmed by grep across the entire repository and by the execution-blindness import guard, which forbids
any networking library in `helios/`). No credential surface exists — HELIOS's own config module docstring
states explicitly it reads no secret. Dockerfile hardening is strong: digest-pinned base image, multi-stage
build, non-root user (`10001:10001`, no login shell), single writable volume, no bound port. No secret values
were read or reported at any point in this discovery.

## 12. Existing FALCON contract mismatches — reconciliation table

**Registry-level verification (performed directly against FALCON's machine-readable registries, not just
prose docs):** `helios.strategy_evaluated`, `helios.chain_state`, `helios.strategy_trigger`, and
`helios.health` are all **genuinely registered** in `registry/event_family_registry.v1.json`, with associated
fields (including a registered `evaluation_id`) in `registry/field_registry.v1.json`, and dedicated JSON
Schemas exist at `schemas/payloads/helios/{chain_state,health,strategy_evaluated,strategy_state,
strategy_trigger}.v1.schema.json`. This is **exactly the same situation PID-06 Stage 2A found and corrected**
for ARES's pre-discovery `market_status` registration: e.g. the registered `helios.chain_state` schema
requires a speculative 4-value `chain_state` enum (`PENDING/ACTIVE/COMPLETED/ABORTED`) that does not match
real HELIOS's actual 7-value `state` enum at all, and splits `strategy_evaluated`/`chain_state`/`strategy_state`
into three families where real HELIOS publishes exactly **one** schema (`helios.strategy_state/1.0.0`) for
both atomic and chain results, discriminated by an internal `EnvelopeKind` field. **These registry entries are
dormant/placeholder-governed, consistent with this project's own precedent (Decision Register 27) — they are
not live, not implemented against, and this discovery does not correct them. A future contract-reconciliation
stage, mirroring PID-06 Stage 2A exactly, is required before any PID-07 implementation begins.**

| # | FALCON assumption (source) | Class | Evidence |
|---|---|---|---|
| 1 | `helios.strategy_evaluated` as distinct from strategy state (registry; `HELIOS-FALCON-CONTRACT.md`) | **D** | Real HELIOS publishes one schema, `helios.strategy_state/1.0.0`, for everything; `EnvelopeKind` is a field discriminator, not two schemas |
| 2 | `helios.chain_state` as a distinct family with its own enum | **D** | Same single schema; registered schema's 4-value enum doesn't match real 7-value `state` enum at all |
| 3 | `evaluation_id` (registered field; `HELIOS-FALCON-CONTRACT.md`) | **D** | No such field exists; HELIOS is architecturally **forbidden** from minting CER-owned identity fields (`experiment_id/run_id/evidence_id/artifact_id`) — an `evaluation_id` would conflict with this doctrine. If needed, FALCON/CER should assign it at ingestion. |
| 4 | strategy ID / strategy version identity | **A** | Fully real, immutable, strictly validated, stable since v1 |
| 5 | "semantic fingerprint" | **C** | Real internally (`definition_fingerprint()`, SHA-256) but **not published** on any envelope today — producer-owned, immature exposure |
| 6 | "parameter-set identity" | **C** | No distinct ID; implicitly covered by the unpublished whole-package fingerprint above |
| 7 | "input snapshot ID/hash references" | **C** | A related, different, already-implemented mechanism exists and IS published (`InputFreshness`: timestamp/age/source-based), but it is not a content hash as the doc assumes |
| 8 | instrument / timeframe | **A** | Real, stable, strictly typed, mandatory on every atomic envelope |
| 9 | "state before/after" | **B** | The transition mechanism is real and rigorous (`LEGAL_TRANSITIONS`, `StateTransition` dataclass) but is **not published** — only current `state` is; "before" is reconstructable only by diffing consecutive envelopes |
| 10 | "conditions satisfied/failed" explainability | **C** | Real capability (every envelope explainable), but deliberately unstructured free-text `explanation` + flat scalar `evidence` map — the shape is producer-owned, not a frozen field set |
| 11 | "quality" | **B** | No field named `quality`; real analogue is `strength` (0–1 decimal), named differently |
| 12 | "produced/available UTC" | **A** (with note) | `last_evaluated_at_utc` is real and mandatory; `StatePublisher` deliberately adds no publication timestamp of its own (determinism guarantee) — FALCON's own ingestion-time stamp correctly fills this role, not a HELIOS field |
| 13 | Declines/blocks/near-misses explainable (PID-07 DoD) | **A** | Core, stable, proven design — every cycle publishes every bound unit's full envelope regardless of match status, contained failures included |
| 14 | "near-miss" as a distinct named concept | **D** | Does not exist; `FORMING` is the nearest but different concept. Notably, the Producer Contract Evolution Doctrine §3 itself already names "near-miss evidence" as something HELIOS "may later add" — FALCON's own doctrine authors already treat this as speculative/future |
| 15 | Decision 13 — "HELIOS remains execution-blind" | **A** | Extremely stable, mechanically enforced via AST import/vocabulary scanning, not just convention |
| 16 | Decision 14 / PID-08 — signed executable triggers | **F** | Correctly PID-08's lane; zero signing code exists anywhere in HELIOS, confirmed |
| 17 | `helios.strategy_trigger` / Trade Suggestion family | **F** | PID-08 territory by the PID documents' own text; confirmed unimplemented (no trigger/SL/TP/signing fields anywhere) |
| 18 | `helios.health` as a Graylog-publishable event family | **D** | Conflicts with HELIOS's deliberate, enforced architecture: no network sink, no bound port, health is a local atomically-written status file read only by the container's own local healthcheck probe. The registered family currently describes something that cannot occur under the present design without a new, explicitly-added side channel. |
| 19 | HSA strategy-package consumption as HELIOS's versioned input | **A for the mechanism / caveat on current content** | The integration code (`hsa_boundary.py`) is real, strict, and correctly wired via a read-only bind mount — genuinely answers "yes, designed to work this way." But see §9 below: the content actually loaded in both live deployments is HELIOS's own bundled fixture scenario, byte-identical to its test fixtures, not real HSA output. |

## 13. PID-07/PID-08 boundary assessment

**Factually confirmed clean separation, not conflated.** `StrategyStateEnvelope` (the only thing HELIOS
currently publishes) has no trigger/trade-suggestion fields at all (no SL/TP, no validity-for-execution, no
signing fields, no `trigger_id`). The execution-blindness test and the runtime service's own docstring assert
this categorically: HELIOS has no knowledge of downstream trading. PID-08's entire scope (signing, trigger
schema, SL/TP semantics) is **completely unbuilt** today — confirmed by the total absence of signing code and
of the registered `helios.strategy_trigger` family's fields anywhere in the real source. There is no risk of
PID-07 and PID-08 work colliding on existing code; PID-08 would be wholly additive, net-new surface.

## 14. Major finding — the live "prod"/"dev" HELIOS deployments are not evaluating live data

Both `gold-strategy-dev-helios-1` and `gold-strategy-prod-helios-1` have been running
`HELIOS_RUNTIME_ON_FEED_END=REPEAT` against a **static, synthetic fixture dataset** continuously since
2026-09-07 — independently confirmed by both discovery passes:

- The fact files at `/etc/gold-strategy/{dev,prod}/facts/*.json` carry a literal `"source": "hermes_prod"`
  string field **inside the static file itself** — this is not live-connection evidence, it is a label on a
  fixture. `docker logs` shows `evaluated_at_utc` cycling through one fixed historical window
  (`2026-09-06T22:xx–23:xxZ` in prod) hundreds of thousands of times (`cycles_completed`: 174,164+ in prod,
  518,412+ in dev, as of this discovery) while real wall-clock time advances into October.
- `/etc/gold-strategy/{dev,prod}/strategies/*` (what HELIOS actually loads via `hsa_boundary.py`) is
  byte-for-byte identical to HELIOS's own bundled test fixtures at
  `/srv/HELIOS/fixtures/strategy_packages/scenario/` — **not** output from the separate `/srv/HSA` repo/service.
  `GOLD-STRATEGY-RUNTIME`'s own `docs/evidence/dev-prod/setup-host-inputs.sh` confirms this explicitly in its
  own comments, and separately re-dates the fixture facts purely "because HELIOS's fixtures are dated
  2026-03-02 and would be correctly judged DATA_STALE" otherwise.
- `HELIOS_PUBLICATION_SINK=STREAM`/`STDOUT` in both environments — published envelopes reach only a
  Docker-local, rotation-bounded log file; there is no wiring from HELIOS to the separate `cer` (durable
  evidence store) service that also runs in this topology, and no Graylog ingestion of any kind.

**This is a scripted end-to-end deployment proof, not a production trading evaluation pipeline, and is a
pre-existing environment/integration gap independent of HELIOS's own code (HELIOS is faithfully doing exactly
what its configuration tells it to do).** It is recorded here as a factual finding, not remediated — flagging
it explicitly because any future PID-07 design assuming "HELIOS prod currently reflects live gold market
state" would be building on a false premise today.

## 15. Proposed minimum candidate PID-07 publication contract

Following Decision 32 (§4/§12: payload first, promotion later) and the reconciliation table above, the
smallest reasonable future contract starts from the universal FALCON envelope plus only the fields classified
**A** above:

**Stable universal envelope** (already governed by PID-01, no HELIOS-specific change needed): `falcon_event_id`,
authenticated producer (`helios`), `evidence_family` (a single family — see note below), `produced_at_utc`
(FALCON/ingestion-assigned, not HELIOS-originated, per item 12's finding), `payload_schema_version`.

**Candidate optional promoted (searchable) dimensions — only where genuinely stable (class A)**:
`instrument`, `timeframe` (noting §3's multi-timeframe-per-chain caveat — likely needs to be an array or
per-component structure, not a single scalar, for chain events), `strategy_id`, possibly `strategy_version`,
`state` (the real 7-value enum), `last_evaluated_at_utc`. **These are candidates for a future
contract-reconciliation stage to formally register — this document does not register them.**

**Single family, not three**: given real HELIOS publishes one schema for both atomic and chain results, a
future contract-reconciliation stage should strongly consider collapsing the registered
`helios.strategy_evaluated`/`helios.chain_state`/`helios.strategy_state` three-way split into a single
family mirroring HELIOS's own `EnvelopeKind` discriminator — this is a recommendation for that future stage,
not a change made here.

**Everything else stays producer-owned payload** (class B/C items and beyond): `strength`, `explanation`,
`evidence` map, `ComponentProvenance`, `InputFreshness` detail, the unpublished `definition_fingerprint`, and
any future HELIOS additions (chain strength, near-miss diagnostics, alignment metrics, rejection reasoning,
experimental attributes) — per doctrine §1, preserved losslessly via the same proven raw-preservation-field
pattern already used for ARES (PID-06), not individually schema'd.

## 16. Producer-owned payload recommendation

HELIOS's `StrategyStateEnvelope` (full JSON: identity, state, direction, strength, evidence map, explanation,
per-component provenance, per-input freshness, lifecycle timestamps, validity window) is the complete,
losslessly-preservable producer-owned object — generically serializable the same way ARES's row was
(PID-06's `_serialize_row_raw` pattern), tolerating future HELIOS additions with zero FALCON contract changes
per doctrine §3.

## 17. Forward-compatibility assessment

Not implemented or tested in this discovery round (correctly out of scope — "do not implement this test yet
unless purely documentation/fixture analysis"). What a future implementation stage will need to prove,
per doctrine §11: an unknown future HELIOS payload field (e.g. a hypothetical future "chain_strength" or
"near_miss_distance") survives serialization and FALCON preservation unchanged, is not rejected merely for
being unknown, and is not automatically promoted into the searchable envelope. HELIOS's own envelope model
(flat scalar `evidence` map, generically serializable dataclass-like structure) is structurally compatible
with this requirement — no blocker identified, nothing proven yet either.

## 18. Gaps/blockers requiring architecture decisions (before PID-07 implementation)

1. **Registry/schema contract debt** (§12): `helios.strategy_evaluated`/`helios.chain_state`/`helios.health`
   registry entries and their schemas are speculative and materially wrong (enum mismatch, false
   three-family split, a field FALCON would need HELIOS to never mint). Requires a Stage-2A-style
   reconciliation before implementation, exactly as PID-06 required for ARES's `market_status`.
2. **Publication is currently fully synchronous/blocking** (§10): must be redesigned (new sink + decoupling
   from the evaluation loop's critical path) before any network/Graylog sink is added, to avoid making FALCON
   availability a runtime dependency of HELIOS's evaluation cadence — directly contrary to the PID-05/PID-06
   non-blocking principle.
3. **No durable evidence record exists today in the live deployment** (§5): `STDOUT`/`STREAM` sink only,
   bounded by Docker log rotation. A `FileSink` already exists in code but isn't configured; this is a
   deployment-configuration decision, not a code gap.
4. **Live "prod"/"dev" HELIOS is evaluating synthetic fixture data on an infinite replay loop, not live
   HERMES/HSA output** (§14) — a pre-existing environment/integration gap outside PID-07's discovery scope,
   flagged for the Architect/HELM's separate awareness.
5. **Multi-timeframe chain evidence** (§3/§15): a single scalar `timeframe` searchable field is likely
   insufficient for chain-level events spanning multiple timeframe contexts — needs explicit design in a
   future contract-reconciliation stage, not assumed from the existing registry.
6. **Tamper-evident HERMES-input traceability is unresolved** (§6): depends on HERMES-side immutability
   guarantees HELIOS cannot itself verify; needs an explicit architecture decision on whether this matters
   enough to require a future mechanism, or is accepted as a known limitation.

## 19. R2D2 independent findings

R2D2's independent pass converged with the primary discovery on every material finding (repo authority, the
synthetic-fixture-replay finding, the blocking-publish-path finding, UTC/config cleanliness, execution-blind
confirmation) and additionally: directly traced the live containers' image digest and `org.opencontainers`
labels back to `/srv/HELIOS`'s Dockerfile itself (not just the repo's existence); found and confirmed
`/etc/systemd/system/helios-v3.service` as dead, masked, non-functional legacy cruft not previously flagged;
and produced the full reconciliation table in §12 above as its primary deliverable, independently verified
against both the HELIOS source and FALCON's machine-readable registries (not just prose documentation).

## 20. R2D2 blueprint reference

A durable R2D2 blueprint record (topology, data flow, identity model, evidence model, dependencies, known
gaps) has been produced and is referenced at Memory Fabric key
`r2d2:blueprint:helios_falcon_pid07_stage1_discovery:20261007` (operational/session evidence; this Git
document remains the durable authority per this project's doctrine).

## Scope note

This document records discovery findings only. It does not modify any PID-01 registry, schema, or validator;
does not modify `docs/contracts/HELIOS-FALCON-CONTRACT.md`; does not modify HELIOS or FALCON application
code; and does not authorise any PID-07 implementation. A future contract-reconciliation stage (PID-07 Stage
2, mirroring PID-06 Stage 2A) is required before implementation begins, per §18 item 1.
