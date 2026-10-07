# FALCON PID-06 — Runtime Acceptance Evidence

**Purpose:** the durable Git record of HELM's live runtime deployment and acceptance testing for PID-06
(ARES → FALCON `market_status` integration), on which Central Architecture's **PID-06 RUNTIME ACCEPTANCE:
GREEN** decision is based. Written by the Delivery Controller (Rogue) from HELM's reported runtime evidence
and Central Architecture's review of it — HELM performed the runtime work; this document is its closure
record, not a new runbook framework.

**Canonical authorities at time of this evidence:**
- FALCON: `maff0000/falcon` `main` @ `4276e5a193315ee1a450d11531f2cfd4d045c157`
- ARES: `maff0000/trading-ares` `main` @ `6c33621429db2066b7187ebacc268fe9402398be`
- Architecture: PID-06, `AMD-PID06-001-ARES-FOUNDATION-CANONICAL-SERVICE`,
  `AMD-PID06-002-ARES-FOUNDATION-LIVENESS`, `WO-PID06-002-RUNTIME-ACCEPTANCE`

No secrets, private keys, or credential values appear in this document.

---

## 1. FALCON runtime drift correction (content-pack rev 6)

Canonical rev-6 content-pack authority (the Stage 2B `market_status` contract correction — FALCON PR #12)
had to be installed live before runtime acceptance testing could proceed. A narrow first attempt — deleting
only the single diverging pipeline rule — failed safely: Graylog rejected it because the pipeline entity
itself already existed under the title `FALCON Ingestion`, causing a duplicate-title conflict on reinstall.
The rollback restored the original rule byte-identically; no evidence was lost during this failed attempt.

**The procedure that actually worked** (now codified as the authoritative procedure — see
`docs/operations/FALCON-PID04-PRIVILEGED-OPERATIONS-RUNBOOK.md` §14 for the full command-level runbook):

1. Delete the diverging rule.
2. Delete the pipeline entity itself (not just the rule).
3. Install canonical content-pack rev 6 from `deploy/content-packs/falcon-pid03-ingestion-v1.json`.
4. Reconnect the reinstalled pipeline to the Default Stream.
5. Identify and remove blind-duplicated streams/inputs created as a side effect of installation (the same
   `StreamFacade` blind-duplication behaviour already documented for earlier content-pack revisions in the
   PID-04 runbook).

**Measured impact:** HTTP 200 on install; ~250ms installation time; ~289ms pipeline-absent window; zero
Graylog container restart; zero API outage; zero producer events misrouted to the Default stream during the
window; **zero HERMES evidence loss**.

**Post-correction verification:** all 30 live pipeline rules matched canonical rev 6 byte-for-byte; the ARES
`market_status` family now requires only its accepted mandatory payload fields (`instrument_id`,
`market_state`); the obsolete `session_id`/`market_id`/5-value `session_state` fields are confirmed no longer
required anywhere live; `reason_code` remains optional; `quality_state` remains producer-owned, not promoted;
all 5 inputs remained RUNNING throughout; rev 6 recorded 44 entities.

**Runbook correction**: `docs/operations/FALCON-PID04-PRIVILEGED-OPERATIONS-RUNBOOK.md` §14 records this as
the authoritative content-pack reconciliation procedure, correcting the prior documentation's incomplete
instruction to "delete the diverging rule" alone.

## 2. Lossless producer payload ruling

**Architect ruling, recorded here verbatim in substance**: FALCON requires lossless preservation of the
producer-owned evidence payload. It does **not** require binary/base64 encoding where the original JSON can
be preserved losslessly. The live acceptance event (§3) proved this empirically: the authoritative ARES
representation contained 13 keys; FALCON's raw JSON preservation contained all 13 keys with matching values,
including null-valued fields; `quality_state` remained producer-owned and was not promoted to the searchable
envelope; searchable-field promotion remained bounded to the accepted contract; an unknown nested future
field survived the production serializer unchanged in controlled image testing and was not automatically
promoted. Plaintext raw JSON preservation is therefore accepted as sufficient for this ARES event family.

Wording correction applied: `WO-PID06-002-RUNTIME-ACCEPTANCE.md` §5 item 15's prior phrase "FALCON's binary
preservation mechanism" is corrected to "FALCON's lossless producer-owned payload preservation mechanism" —
an architecture-neutral wording clarification of already-accepted architecture, not new application
functionality or a scope change.

## 3. Genuine live acceptance event

| Field | Value |
|---|---|
| FALCON event ID | `d36f91ea-ba23-4fc4-957a-f2cb7bb32a16` |
| Instrument | `XAU_USD` |
| ARES run | `54ca92c5…` |
| `market_state` | `OPEN` |
| `reason_code` | `SESSION_OPEN` |
| `quality_state` (producer-owned, not promoted) | `HEALTHY` |
| `config_digest` | `504feb24…` |
| `observed_at_utc` | `2026-10-06T14:45:21.155895+00:00` |
| Natural identity | `ares:market-status:XAU_USD:2026-10-06T14:45:21Z` |
| `produced_at_utc` | `2026-10-06T14:45:21Z` |
| Graylog ingestion | `2026-10-06T14:45:21.202Z` |
| Classification | **VALID** |
| Authenticated producer | `ares` |
| Input | dedicated ARES input, host port `12412` |
| Stream | `FALCON: ARES evidence` |
| Index | `falcon-evidence_1` |

This single event is the proof point for: correct `instrument`/`market_state`/optional-`reason_code`
semantics; `quality_state` staying producer-owned; full rich-payload preservation (§2); correct natural
identity derivation (`instrument + observed_at_utc + config_digest`); separately-governed
`observed_at_utc`/`produced_at_utc`; valid FALCON event ID; correct authenticated producer attribution; and
`VALID` classification/routing to the correct stream/index.

## 4. mTLS acceptance

- Fresh ARES client identity provisioned and accepted by FALCON's dedicated ARES input.
- Authenticated ARES traffic correctly attributed to producer `ares`.
- No-client-certificate connection: rejected.
- Forged same-subject certificate: rejected.
- HERMES's own certificate presented against the ARES input: rejected.
- Zero negative frames ingested during any of the above tests.

No private-key material is recorded in this document or anywhere in Git, per standing policy.

## 5. Failure-isolation acceptance

**Scoped failure:** ARES Foundation → FALCON `:12412` path only (no other service affected).
**Window:** `2026-10-06T14:49:30Z` → `2026-10-06T14:51:45Z`.

| Signal | During outage | Baseline/outside |
|---|---|---|
| Heartbeat max spacing | 5.145s | 5.152s |
| Scheduler job failures | 0 | — |
| Market-status eval duration | 58ms (affected cycle) | ~41ms |
| Redis publication | 0ms | — |
| Liveness-reader executions | 117/117 healthy | — |
| Max marker age | 5.03s | (stale threshold: 15s) |
| Docker health | remained healthy | — |
| Foundation restart count | 0 | — |
| Publisher transport | bounded failure, 2 attempts exhausted (by design) | — |
| Evidence loss | 1 event, accepted best-effort loss | — |
| Queue-full drops | 0 | — |
| Queue depth | ≤1/5 slots (where inferable) | — |

**Recovery:** the next genuine ARES evaluation (`25da835f-4dd7-4fa3-acf1-f1b468d0def6`) published successfully
on the first transport attempt at approximately `2026-10-06T14:55:22Z`, classified `VALID`, all 13 producer
keys matching authoritative ARES state, no duplicate, no replay, zero Foundation restart.

**Architectural conclusion (major PID-06 acceptance result):** this empirically proves **FALCON evidence
publication is not a runtime dependency of ARES Foundation scheduling** — Foundation's scheduler, SQL/Redis
persistence, and liveness all continued correctly and without degradation throughout a real FALCON-side
outage, exactly as the non-blocking architecture (HERMES-pattern, Stage 2B) was designed to guarantee.

## 6. Replay exclusion

No normal live publication was observed for any event carrying `audit.reconstructed == true`, verified via
the smallest safe runtime inspection available, supplemented by the existing deterministic Stage 2B test
evidence for this boundary (no broad historical replay was run merely to test this).

## 7. HERMES regression guard

- HERMES remained healthy throughout PID-06 runtime deployment and acceptance.
- Host port `12411` remained operational and unchanged throughout.
- The content-pack correction work (§1) caused **zero** HERMES evidence loss.
- No HERMES trust/credential regression. No HERMES implementation change of any kind.

**Retained historical operational evidence (not a PID-06 defect):** on 2026-10-04, an earlier FALCON
container recreation (unrelated to the §1 procedure) lost 27 HERMES evidence events during approximately
19.7 seconds of FALCON downtime. This is recorded as **FALCON resilience/maintenance debt**, not a PID-06
failure: best-effort producer publication means FALCON downtime can create evidence gaps even while producer
applications remain healthy. No resilience implementation is authorised or performed under this closure.

## 8. Finding A — validated for deployed configuration

Observed live market-status cadence: ≈300.05s. Configured/rationale cadence: 300s. Queue size: 5. **The
original Stage 2B queue-sizing rationale is empirically valid for the actually-deployed 300-second cadence.**
This conclusion is **not** generalised to the full configurable 30–3600-second range — that remains open,
unchanged from Stage 2B.

## 9. Finding B — remains open, non-blocking technical debt

Canonical Foundation publisher shutdown behaviour under a genuinely hung publisher has not been observed
end-to-end, and is **not** claimed closed by this runtime acceptance. No new runtime experiment was performed
to force this condition. It does not block PID-06 closure because normal startup/liveness, real runtime
publication, FALCON failure isolation, scheduler independence, and automatic transport recovery are all
separately and directly proven (§3, §5, §6). The remaining open question is bounded-shutdown lifecycle
behaviour specifically, not correctness of the live ARES→FALCON path. Finding B is carried into the ARES
operational/testing backlog with provenance back to PID-06; it is not fixed, generalised, or opportunistically
closed here.

## 10. Other non-blocking debt (recorded, not remediated)

**ARES:**
1. `ares-core` remains on the historical image tag `p0-macro-b694640c` while canonical `ares-foundation` runs
   the canonical PID-06 image — a mixed-image state pending a future ARES Core image-migration decision.
2. `ares-core`/`ares-db`/`ares-cache`'s Compose labels still reference the historical worktree deployment
   path (`/srv-dev-worktrees/trading-ares`) from before canonicalisation.
3. `HERMES_DEPENDENCY_IDENTITY_MISMATCH` remains a pre-existing, unrelated condition.
4. The retained `ares-foundation-manual-pre-pid06` container exists as rollback state; it should receive an
   explicit future retirement decision once rollback confidence permits. It is not deleted by this closure.
5. The `tar-risk-engine` restart loop remains unrelated and untouched throughout PID-06.

**FALCON:**
6. The content-pack reconciliation runbook required the correction recorded in §1/runbook §14.
7. Producer evidence can be lost during FALCON downtime under the accepted best-effort delivery semantics
   (§7); resilience requirements for this are explicitly deferred to separate evaluation, not folded into
   PID-06.

None of these items are remediated in this closure round.

## 11. R2D2 blueprint reference

The current runtime topology (ARES Core/Foundation separation, Foundation scheduler ownership, local
liveness, market-status production path, mTLS boundary, FALCON `12412` path, Graylog contract/routing,
best-effort failure semantics, and the debt items in §10) is recorded by HELM at Memory Fabric key
`helm:blueprint:ares_falcon_runtime_topology:20261006T1457Z`, maintained by HELM/consumed by R2D2 per this
project's existing blueprint doctrine (`docs/governance/FALCON-R2D2-BLUEPRINT.md`). No secrets are stored at
that key. This document is the Git-durable pointer to it; the Fabric key itself is operational/session
evidence, not a substitute for this record.

## 12. Scope — what PID-06 delivered and proved, and what it explicitly did not

**Delivered and proven:** dedicated ARES mTLS Graylog input; fresh ARES producer identity; canonical
`ares-foundation` service; canonical Foundation local liveness mechanism; real live ARES `market_status`
publication; the corrected ARES `market_status` contract (Stage 2A/2B); authenticated FALCON producer
attribution; `VALID` Graylog classification and routing; lossless producer payload preservation; a bounded
searchable envelope; replay exclusion; FALCON failure isolation from ARES Foundation scheduling; automatic
publication recovery after a transport outage; HERMES regression protection; the deployed 300-second
queue-sizing rationale (Finding A, for that cadence only).

**Explicitly not delivered by PID-06:** any other ARES evidence family (Calendar, Liquidity, Macro-USD,
source-quality); `publication.decision` redesign; a generalised queue-sizing proof for the full configurable
30–3600-second range; a durable-delivery/outbox mechanism; a guarantee of zero evidence loss; Finding B
shutdown-hardening proof; ARES Core canonical-image migration; or remediation of any item listed in §10.
