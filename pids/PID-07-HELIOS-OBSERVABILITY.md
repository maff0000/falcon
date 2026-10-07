# PID-07 --- HELIOS Evaluation and State Evidence

**Slug:** `helios-observability`\
**Owner:** Rogue/FORGE\
**Assurance:** R2D2\
**Ops authority where applicable:** HELM\
**Time:** UTC only

## Status

**STAGE 1 (DISCOVERY) CLOSED. IMPLEMENTATION NOT STARTED.** This document originally (pre-discovery)
proposed a comprehensive HELIOS evaluation/state schema directly in its Scope/deliverables section below.
**That approach is superseded**, per the Producer Contract Evolution Doctrine (Decision 32,
`docs/architecture/04-PRODUCER-CONTRACT-EVOLUTION-DOCTRINE.md` §12): "HELIOS is not mature enough for FALCON
to freeze a detailed HELIOS evidence schema." The original scope text below is retained, not rewritten, per
this project's discipline against silently erasing prior state — it is no longer the governing scope for how
PID-07 proceeds.

### Stage 1 — HELIOS Read-Only Discovery & Contract Reconciliation (CLOSED)

Governed by `work-orders/WO-PID07-001-HELIOS-DISCOVERY.md`. Full findings:
`docs/architecture/PID07-HELIOS-STAGE1-DISCOVERY.md`. Established the authoritative HELIOS repository
(`maff0000/HELIOS` @ `7f7193d55475e40583892b94dd461b1b64d6f1ef`), the real strategy/evaluation/evidence model,
a full reconciliation of FALCON's existing (pre-discovery, speculative) registry entries and contract
documentation against real HELIOS behaviour, confirmed the PID-07/PID-08 conceptual boundary is already
clean in the real implementation, and proposed (not registered) a minimum candidate publication contract.

### What Stage 1 found, in brief

HELIOS v1 is a deterministic, execution-blind, stateless-between-cycles strategy-evaluation engine with a
textbook-clean UTC implementation and fail-loud configuration discipline. It publishes one real envelope
schema (`helios.strategy_state/1.0.0`) for both atomic strategies and chains, on every evaluation cycle,
regardless of match status. FALCON's existing registered `helios.strategy_evaluated`/`helios.chain_state`/
`helios.health` event families and their schemas are speculative, pre-discovery registrations that do not
match real HELIOS behaviour (enum mismatches, a false three-family split, a forbidden-to-exist
`evaluation_id` field) — the same situation PID-06 Stage 2A found and corrected for ARES. HELIOS currently has
no FALCON/Graylog publication path at all, and its current publication mechanism is fully
synchronous/blocking (a sink failure kills the whole evaluation loop) — the opposite of the non-blocking
principle PID-05/PID-06 established, and a required fix before any network sink is added. The live "prod"/
"dev" HELIOS deployments are independently confirmed to be replaying a static synthetic fixture dataset on an
infinite loop since 2026-09-07, not evaluating live HERMES/HSA data — a pre-existing environment gap outside
this PID's scope, flagged separately.

### What remains before implementation can begin

A **PID-07 Stage 2 — Contract Reconciliation** (mirroring PID-06 Stage 2A exactly) must correct the
speculative registry entries/schemas identified in Stage 1 before any publisher is implemented, and Central
Architecture must separately rule on the blocking-publisher finding and the live-fixture-replay finding.
**Neither Stage 2 nor implementation is authorised by this document.**

## Dependencies

PID-01, PID-03, PID-04. Also now inherits the Producer Contract Evolution Doctrine (Decision 32) in full,
including its HELIOS-specific non-freezing ruling.

## Original scope / deliverables (pre-discovery, superseded — retained for history, not current authority)

-   strategy evaluation schema;
-   strategy/chain state schema;
-   input snapshot/hash references;
-   decline/block/near-miss reasons;
-   strategy fingerprint/version/parameter identity;
-   health.

## Mandatory engineering law (unchanged, reaffirmed)

-   no config in code;
-   no hidden defaults/fallbacks;
-   required missing config fails loudly;
-   no secrets in Git/images/events;
-   container-compatible;
-   UTC-aware canonical timestamps only;
-   bounded branch/PR with clean Git hygiene;
-   exact SHA/runtime evidence;
-   documentation updated with implementation.

## Required tests/evidence (for a future implementation stage, not Stage 1)

-   fired/declined/blocked/near-miss fixtures;
-   exact HERMES/ARES input references;
-   point-in-time reconstruction;
-   no execution authority fields.

## PID-07 / PID-08 boundary (confirmed by Stage 1 discovery)

PID-07 concerns HELIOS strategy evaluation/state evidence only. PID-08 concerns HELIOS signed trade
suggestions (the registered `helios.strategy_trigger` family). Stage 1 confirmed the real HELIOS
implementation already keeps these cleanly separate — zero signing/execution-authority code exists anywhere
in HELIOS today, and `StrategyStateEnvelope` carries no trigger/trade-suggestion fields. PID-08 remains wholly
additive, future, unstarted work.

## Definition of Done

Unchanged in substance, now understood in light of Stage 1: Graylog can explain why a strategy fired or did
not fire from governed HELIOS evidence, using a contract reconciled against real HELIOS behaviour (Stage 2),
published through a non-blocking mechanism, and running against genuinely live HERMES/HSA data rather than a
static fixture replay.

A PID is not complete until its behaviour is running and proven, not merely coded or documented.
