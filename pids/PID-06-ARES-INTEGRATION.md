# PID-06 — Canonical ARES → FALCON Integration

**Slug:** `ares-integration`
**Owner:** Rogue (FALCON) / Delivery Controller for cross-repo execution
**Producer:** ARES (`maff0000/trading-ares`)
**Assurance:** independent FORGE Auditor, fresh per candidate SHA
**Ops authority for runtime/network/credential work:** HELM
**Time:** UTC only

## Status

**CLOSED GREEN.** Stage 1 (Discovery), Stage 2A (Contract Reconciliation), Stage 2B (First Vertical Slice
Implementation — `market_status`), and Stage 3 (Runtime Acceptance and Canonical Deployment) are all CLOSED
and merged to both repositories' canonical `main`. The original "OPEN... does not close until runtime
acceptance is proven" line above was accurate at the time it was written and is retained in this file's Git
history, not rewritten, per this project's own discipline against silently erasing prior state.

### Acceptance record

- **Accepted by:** Central Architecture, via explicit instruction to the Delivery Controller (Rogue):
  "ROGUE — DELIVERY CONTROLLER / PID-06 — Runtime Acceptance Record and Closure" — "Central Architecture has
  reviewed HELM's final runtime acceptance gate... **PID-06 RUNTIME ACCEPTANCE: GREEN**."
- **Runtime evidence:** HELM performed the governed live deployment and acceptance-testing mandate ("HELM —
  SYSOPS / FALCON PID-06 — ARES → FALCON Runtime Deployment & Acceptance") against canonical FALCON
  `4276e5a193315ee1a450d11531f2cfd4d045c157` and canonical ARES `6c33621429db2066b7187ebacc268fe9402398be`.
  Full evidence: `docs/operations/FALCON-PID06-RUNTIME-ACCEPTANCE-EVIDENCE.md`; corrected content-pack
  reconciliation procedure: `docs/operations/FALCON-PID04-PRIVILEGED-OPERATIONS-RUNBOOK.md` §14; closure
  record: `work-orders/WO-PID06-002-RUNTIME-ACCEPTANCE.md` §29.
- **This status update's own authority:** a Delivery-Controller-level durable-record correction making the
  already-given, already-evidenced Architect acceptance visible in Git, per this project's "no Git record →
  not durable project authority" rule — becomes durable project authority only once this closure candidate
  has itself passed independent audit, PR, and Architect acceptance.

### Delivered and proven

Dedicated ARES mTLS Graylog input; fresh ARES producer identity; canonical `ares-foundation` service
(AMD-PID06-001); canonical Foundation local liveness mechanism (AMD-PID06-002); real live ARES
`market_status` publication; the corrected ARES `market_status` contract (Stage 2A/2B); authenticated FALCON
producer attribution; `VALID` Graylog classification and routing; lossless producer-owned payload
preservation; a bounded searchable envelope; replay exclusion; FALCON failure isolation from ARES Foundation
scheduling (proven empirically under a real bounded outage); automatic publication recovery; HERMES
regression protection; the deployed 300-second queue-sizing rationale (Finding A, for that cadence only).

### Explicitly not delivered by PID-06

Any other ARES evidence family (Calendar, Liquidity, Macro-USD, source-quality); `publication.decision`
redesign; a generalised queue-sizing proof across the full configurable 30–3600-second range; a
durable-delivery/outbox mechanism; a guarantee of zero evidence loss; Finding B shutdown-hardening proof
(remains OPEN, carried to the ARES operational/testing backlog); ARES Core canonical-image migration; or
remediation of any other non-blocking debt item recorded in the evidence document's §10.

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

## Stage 3 — Runtime Acceptance and Canonical Deployment (CLOSED, MERGED, RUNTIME-ACCEPTED)

See Work Order `WO-PID06-002-RUNTIME-ACCEPTANCE` (`work-orders/WO-PID06-002-RUNTIME-ACCEPTANCE.md`).
Covers: FALCON host-port exposure for the ARES GELF/mTLS input (12412,
mirroring the already-proven HERMES 12411 model), provisioning a fresh ARES
producer identity (the original private key is lost and is not recoverable),
canonical-checkout ARES deployment (retiring dependence on the disposable
Stage-1-era worktree deployment path), and live, evidence-backed runtime
proof of the full HERMES-pattern non-blocking failure-isolation guarantee
under real network conditions.

## Amendments

- **AMD-PID06-001 — ARES Foundation Canonical Service** (`pids/amendments/AMD-PID06-001-ARES-FOUNDATION-CANONICAL-SERVICE.md`).
  Resolves the Stage 3 / WO-PID06-002 §26 open architectural finding: ARES has two distinct canonical
  process roles (`ares-core` running `runtime.compose_root`; `ares-foundation` running
  `runtime.foundation`, the sole scheduler for Calendar/Market Status/Liquidity/Macro-USD and Foundation
  housekeeping, required independently of FALCON). `ares-foundation` is to become an explicit,
  Git-governed Compose service using the same image with a different command, with process separation from
  `ares-core` preserved. Architecture/governance only — implementation requires the amended
  `WO-PID06-002-RUNTIME-ACCEPTANCE` (§27) to itself be accepted and merged.

- **AMD-PID06-002 — ARES Foundation Liveness** (`pids/amendments/AMD-PID06-002-ARES-FOUNDATION-LIVENESS.md`).
  Narrowly supersedes AMD-PID06-001's healthcheck constraint only: authorises the minimum new local
  liveness-marker/reader functionality needed for a truthful `ares-foundation` Docker healthcheck, extending
  the existing `JOB_HEARTBEAT` progress signal rather than depending on SQL/Redis/HERMES/FALCON. Liveness
  only, not dependency readiness; no restart/watchdog automation authorised. Architecture/governance only —
  implementation requires the amended `WO-PID06-002-RUNTIME-ACCEPTANCE` (§28) to itself be accepted and
  merged.

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

**MET.** ARES's real, live `market_status` evidence is provably reaching FALCON as `VALID`, with its rich
producer-owned observation intact and its searchable fields matching the accepted contract exactly (event
`d36f91ea-ba23-4fc4-957a-f2cb7bb32a16`), and the non-blocking failure-isolation guarantee has been proven
against real runtime conditions (bounded outage `2026-10-06T14:49:30Z`–`14:51:45Z`, with proven recovery) —
not merely coded, unit-tested, or documented. Full evidence:
`docs/operations/FALCON-PID06-RUNTIME-ACCEPTANCE-EVIDENCE.md`.
