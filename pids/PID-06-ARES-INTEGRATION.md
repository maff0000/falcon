# PID-06 — Canonical ARES → FALCON Integration

**Slug:** `ares-integration`
**Owner:** Rogue (FALCON) / Delivery Controller for cross-repo execution
**Producer:** ARES (`maff0000/trading-ares`)
**Assurance:** independent FORGE Auditor, fresh per candidate SHA
**Ops authority for runtime/network/credential work:** HELM
**Time:** UTC only

## Status

**OPEN.** Stage 1 (Discovery), Stage 2A (Contract Reconciliation), and Stage 2B
(First Vertical Slice Implementation — `market_status`) are CLOSED and merged
to both repositories' canonical `main`. PID-06 Runtime Acceptance and
Canonical Deployment is the current, not-yet-executed delivery unit (see its
Work Order, §Work Orders below). PID-06 does not close until runtime
acceptance is proven and accepted by Central Architecture.

## Supersession notice

This document originally (pre-discovery) proposed a materially different,
speculative design: a transactional `ares_falcon_outbox`, simultaneous
expansion across Calendar/Market Status/Liquidity/Macro-USD/source-quality,
and eventual Regime publication. **That design was never implemented and is
superseded by this revision.** Direct inspection of ARES's real, running
source (`maff0000/trading-ares`, not the unrelated legacy `tradingProteus/ares`
pre-extraction code) during Stage 1 discovery found no outbox, no
transactional durability requirement, and a per-family rather than
whole-system delivery model already in use elsewhere in this project
(HERMES, PID-05). The governing design is now the smaller, evidence-based
one recorded below, delivered one real family at a time starting with
`market_status`. The original scope items (outbox, simultaneous
multi-family rollout, Regime) are retired, not merely deferred, pending any
future Architect decision to re-open them under a fresh amendment.

## Dependencies

PID-01 (contract/registry foundation), PID-03 (ingestion pipeline), PID-04
(producer mTLS/identity security) — all CLOSED and reused as-is. No PID-01
contract semantics were reopened except the explicit, evidence-based
`market_status` correction recorded under Stage 2A below.

## Purpose

Add ARES's own best-effort evidence-publication boundary into FALCON,
following the same architecture already proven by HERMES (PID-05): a stable,
FALCON-governed searchable envelope; a producer-owned, extensible rich
message; non-blocking, best-effort delivery that can never make ARES
dependent on FALCON's availability or latency.

## Mandatory engineering law (unchanged from the original PID, reaffirmed)

- no architecture invented by an implementer outside an approved Work Order;
- no config in code; no hidden defaults/fallbacks; required-but-missing
  config fails loudly;
- no secrets in Git/images/events;
- container-compatible;
- UTC-aware canonical timestamps only — no naive `datetime.now()`, no SQL
  `NOW()`/`UTC_TIMESTAMP()`, no implicit timezone conversion;
- bounded branch/PR with clean Git hygiene, independent audit before any
  merge;
- exact SHA/runtime evidence at every stage;
- documentation updated with implementation, never left to drift stale.

## Stage 1 — Discovery (CLOSED)

Established ground truth about the real, currently-deployed ARES system
(standalone repo `maff0000/trading-ares`, not the legacy monorepo code),
its real data flows, its six already-FALCON-registered candidate families,
its genuinely strong existing UTC/identity discipline, its synchronous
scheduler-driven concurrency model, and a real, then-unresolved network gap
(ARES could not reach FALCON's ARES ingress at all — active connection
refusal, not merely a missing credential). Full findings recorded in
Memory Fabric (`rogue:handover:falcon:pid06_ares_discovery:*`) and in this
project's session history; the durable architectural conclusions are
carried forward into this document rather than duplicated here.

## Stage 2A — Contract Reconciliation (CLOSED)

Two of the six pre-existing registered FALCON families for ARES were found
to be speculative, pre-discovery designs with zero real producer or
consumer ever created against them:

- **`ares.market_status.session_state`** registered a 5-value session
  lifecycle (`PRE_OPEN/OPEN/CLOSING/CLOSED/HOLIDAY`) with invented
  `session_id`/`market_id` identity. ARES's real, authoritative model
  (`ares.marketstatus.model.MARKET_STATES`) is a deliberately fail-safe
  3-value model: `OPEN | CLOSED | UNKNOWN`, keyed on `instrument`, with an
  orthogonal `reason_code`. **Corrected** (see Stage 2B).
- **`ares.publication.decision`** registered a research-publication
  workflow (`RESEARCH_PUBLISH`/`PUBLISHED`/`rationale_ref`). ARES's real
  `ares_publication_decisions` table is a technical publish-integrity/
  freshness gate log, a different concept entirely. **Not corrected or
  implemented in PID-06** — recorded as known contract debt; it must not be
  treated as ready for any future family-expansion Work Order without a
  fresh Stage-2A-style reconciliation of its own.

Full reconciliation record: `rogue:handover:falcon:pid06_ares_contract_reconciliation:*`.

## Stage 2B — First Vertical Slice: `market_status` (CLOSED, MERGED)

**FALCON** (`maff0000/falcon`, PR #12, merged as `d4644f548de98e5371e8519b391fde422157ce54`):
corrected `ares.market_status.session_state`'s registry/schema/fixtures to
the real ARES contract — `instrument_id` + `market_state`
(`OPEN|CLOSED|UNKNOWN`) required, `reason_code` optional
(`SESSION_OPEN|EARLY_CLOSE_SESSION|MARKET_CLOSED_WEEKEND|MARKET_CLOSED_HOLIDAY|MARKET_CLOSED_SESSION_BREAK|SCHEDULE_COVERAGE_MISSING|EVALUATION_FAILED`),
`quality_state` deliberately not promoted to the searchable envelope. The
obsolete `session_id`/`market_id`/5-value `session_state` fields were
removed from the registry entirely.

**ARES** (`maff0000/trading-ares`, PR #86, merged as
`2525455669ca068fcf5b17592b3d4a9f28ee2185`): added a HERMES-pattern,
non-blocking evidence publisher — a pure, in-memory event builder
(`ares.marketstatus.evidence.build_evidence_event`) handing off via a
bounded `queue.Queue` (sized from ARES's real measured market-status
volume, not copied from HERMES) to a single background daemon thread
owning all GELF TCP + mTLS transport. Natural identity:
`(instrument, observed_at_utc, config_digest)`, taken directly from the
real `MarketStatusObservationRow`. A fresh `falcon_event_id`/`produced_at_utc`
per publish invocation, reused only across that invocation's own bounded
transport retries. `audit.reconstructed == true` is the binding replay-
exclusion boundary. The non-blocking boundary was independently measured
three separate times (implementer, Rogue, fresh Auditor) with converging
results. Full implementation/audit record:
`rogue:handover:falcon:pid06_stage2b_market_status:*`,
`rogue:merge:falcon:pid06_stage2b:*`, `rogue:merge:ares:pid06_stage2b:*`.

Two non-blocking findings were accepted and carried forward (not fixed in
Stage 2B, not to be silently fixed in any later stage without their own
Work Order if the fix is non-trivial):

- **Finding A** — the queue-sizing rationale assumed ARES's default
  300-second market-status evaluation interval and does not establish
  capacity across the full valid 30–3600-second configuration range.
- **Finding B** — the shutdown wiring (`runtime/foundation.py`'s `run()`)
  is supported by code inspection and component-level tests but lacks its
  own dedicated end-to-end integration test exercising a hung publisher
  through the real supervisor shutdown path.

## Stage 3 — Runtime Acceptance and Canonical Deployment (OPEN, NOT YET EXECUTED)

See Work Order `WO-PID06-002-RUNTIME-ACCEPTANCE` (`work-orders/WO-PID06-002-RUNTIME-ACCEPTANCE.md`).
Covers: FALCON host-port exposure for the ARES GELF/mTLS input (12412,
mirroring the already-proven HERMES 12411 model), provisioning a fresh ARES
producer identity (the original private key is lost and is not recoverable),
canonical-checkout ARES deployment (retiring dependence on the disposable
Stage-1-era worktree deployment path), and live, evidence-backed runtime
proof of the full HERMES-pattern non-blocking failure-isolation guarantee
under real network conditions.

## Explicit scope boundaries (reaffirmed, apply to every future PID-06 stage)

Not authorised under PID-06 without a fresh amendment: Calendar, Liquidity,
Macro-USD, or source-quality evidence publication; any `publication.decision`
redesign; source-quality SQL persistence; the pre-existing, unrelated
macro_usd HERMES-identity-fingerprint operational issue; general FALCON
OpenSearch authentication remediation; Mongo credential rotation; any
HERMES/HELIOS/TRON code change; general Docker/network redesign beyond the
single narrow ARES↔FALCON path; `tar-risk-engine` (confirmed unrelated,
untouched throughout PID-06 to date).

## Definition of Done

PID-06 is not complete until ARES's real, live `market_status` evidence is
provably and repeatably reaching FALCON as `VALID`, with its rich
producer-owned observation intact and its searchable fields matching the
accepted contract exactly, and until the non-blocking failure-isolation
guarantee has been proven against real (not merely simulated/unit-tested)
runtime conditions — not merely coded, unit-tested, or documented.
