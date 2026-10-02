# Work Order: WO-PID06-002-RUNTIME-ACCEPTANCE

**Status:** DRAFT — awaiting Central Architecture acceptance. **NOT authorised for execution.**

## 1. Governance chain (binding on every mandate derived from this WO)

```
Architecture decision → PID/Amendment → Git-tracked Work Order → Delivery Controller → Implementer → Independent Audit → PR → Architect Acceptance → Merge → Closure
```

Hard invariants:

- **NO PID → NO WORK ORDER.**
- **NO WORK ORDER → NO IMPLEMENTATION.**
- **NO INDEPENDENT AUDIT + ARCHITECT ACCEPTANCE → NO MERGE.**
- **NO GIT RECORD → NOT DURABLE PROJECT AUTHORITY.**

The Architect owns architecture, PIDs, amendments, sequencing, and acceptance. The Delivery Controller owns bounded execution and may dispatch implementation only against an approved Git-tracked Work Order. Implementers work only inside this WO, must not invent architecture, and must not widen scope. **If implementation exposes architectural ambiguity: STOP AND RETURN TO CENTRAL ARCHITECTURE. Do not improvise.** Corrections/follow-up implementation require the same governed WO process. Git/GitHub is durable project authority; chat and Memory Fabric are control/continuity surfaces, not substitutes for Git. These governance rules must be copied into every subsequent Delivery Controller and Implementer mandate derived from this WO.

## 2. Identifier and parent

- **WO identifier:** `WO-PID06-002-RUNTIME-ACCEPTANCE`
- **Parent PID:** PID-06 — Canonical ARES → FALCON Integration (`pids/PID-06-ARES-INTEGRATION.md`)
- **Applicable amendments:** none beyond PID-06's own Stage 2A contract reconciliation (`market_status` correction) and the Stage 2B architectural decisions it already encodes (non-blocking publisher boundary, `audit.reconstructed` replay exclusion, `(instrument, observed_at_utc, config_digest)` natural identity). No new architecture is introduced by this WO; it governs deployment and runtime proof of already-accepted, already-merged architecture only.

## 3. Exact base SHAs (binding)

- **FALCON canonical base:** `d4644f548de98e5371e8519b391fde422157ce54` (`maff0000/falcon`, main)
- **ARES canonical base:** `2525455669ca068fcf5b17592b3d4a9f28ee2185` (`maff0000/trading-ares`, main)

If either canonical `main` moves before this WO is executed, the Delivery Controller must determine whether updating the WO's recorded base SHA is safe (i.e. the move is unrelated/additive and does not touch anything this WO depends on) before proceeding, and must record that determination in Git. **Do not silently implement against an unapproved replacement base.**

## 4. Objective

Prove, with real runtime evidence, that the already-merged PID-06 Stage 2B vertical slice (ARES `market_status` → FALCON evidence publication) works end-to-end in the real environment: ARES can reach FALCON's dedicated ingress, authenticate with a freshly-provisioned identity, publish a real live observation that FALCON indexes as `VALID` with its full producer-owned message and corrected searchable contract intact — and that FALCON's unavailability/latency provably does not materially interfere with ARES's primary operation, under real (not merely unit-simulated) network conditions.

## 5. Scope

The smallest set of runtime/configuration changes required to prove the above:

### FALCON
1. Expose FALCON's existing dedicated ARES GELF/mTLS input on host port `12412`, mirroring the already-proven HERMES `12411` model exactly (same Docker publish pattern, same bind-to-LAN-IP-not-`0.0.0.0` discipline, same no-general-bridge discipline).
2. Add the required governed environment/configuration entry for this exposure.
3. Provision/update FALCON-side trust material for the newly generated ARES client identity (§7).
4. Build/deploy from canonical merged FALCON main (`d4644f548de98e5371e8519b391fde422157ce54`) only.
5. Recreate only the minimum necessary FALCON component (expected: `graylog-falcon`, following the exact same minimal-recreate discipline already proven across every prior PID-05 deployment stage).

### ARES
6. Provision a fresh ARES producer client identity (private key + certificate) outside Git, in an ARES-owned runtime secret location, following ARES's own existing `_FILE` configuration convention (mirroring `ARES_DB_APP_PASSWORD_FILE`). **The original ARES client private key is lost and is not recoverable — do not attempt key recovery.**
7. Add the explicit runtime configuration required by the already-merged evidence publisher (`ARES_FALCON_PUBLISH_ENABLED`-equivalent flag, host/port, cert/key/CA `_FILE` paths) to ARES's real deployment configuration (its manifest-based config system, not a new convention).
8. Build/deploy from canonical merged ARES main (`2525455669ca068fcf5b17592b3d4a9f28ee2185`) only.
9. Deploy only the minimum necessary ARES component(s) (expected: `ares-foundation`, since the market-status scheduler job runs there — confirm against the real deployment topology before assuming).
10. The resulting runtime must no longer depend on the disposable/stale worktree deployment path discovered during Stage 1 (`/srv-dev-worktrees/trading-ares`). The canonical deployment source must be the governed canonical ARES checkout.

### Runtime acceptance (both systems)
11. Produce a genuine live ARES `market_status` observation through the real, unmodified scheduler path.
12. Prove ARES's existing authoritative SQL/Redis representation of that observation remains correct and unchanged by the presence of evidence publication.
13. Prove the corresponding evidence reaches FALCON.
14. Prove FALCON classifies/routes it as `VALID` (not `INVALID`/Quarantine).
15. Prove the full rich producer-owned observation survives intact in FALCON's binary preservation mechanism.
16. Prove the searchable envelope/payload fields match the accepted Stage 2A/2B contract exactly (`instrument_id`, `market_state` ∈ `{OPEN,CLOSED,UNKNOWN}`, optional `reason_code` only when genuinely present, no `quality_state` in the searchable payload).
17. Prove the natural identity corresponds exactly to `instrument + observed_at_utc + config_digest`.
18. Prove a reconstructed/replayed ARES event (`audit.reconstructed == true`) is not accidentally published during this proof.
19. Prove no unexpected searchable-field/schema explosion occurred (FALCON's registry/schema remain exactly as merged in Stage 2B — no ad-hoc live edits).
20. Prove FALCON indexing remains healthy throughout (cluster green, no indexer failures, no "immense term" errors).

## 6. Failure-isolation acceptance (bounded, mandatory)

Demonstrate, with real runtime evidence (not a repeat of the already-closed unit/component test suite), that **FALCON unavailability/latency does not materially stall ARES market-status processing.** Use the smallest safe mechanism — **do not reproduce a large, destructive, multi-minute outage merely because HERMES's own runtime acceptance used one.** The test must establish that real runtime behaviour agrees with the already-audited non-blocking architecture (bounded `queue.Queue` + single background worker; max 2 transport attempts; bounded shutdown). Capture and report: ARES scheduler behaviour (cadence, health) during the induced condition; queue depth/behaviour; transport failure/retry evidence; recovery once FALCON becomes reachable again; at least one successful post-recovery publication; ARES container restart counts (must remain 0 due to this test); relevant measured latency (scheduler cycle duration during vs. outside the induced condition). **Do not deliberately overflow the queue unless Central Architecture separately authorises that specific sub-test** — a brief, bounded connection-refused-or-timeout condition is sufficient to prove the isolation guarantee without needing to fill 5 queue slots at ARES's real ~5-minute observation cadence.

## 7. Credential provisioning requirements

- Fresh private key + fresh ARES client certificate, correct `clientAuth` extended key usage.
- FALCON-side trust material updated to the new ARES identity (replacing/supplementing the existing, now-orphaned `ares.crt` trust anchor whose matching private key was lost).
- Private key material never committed to Git, never printed in evidence/logs/chat, never transmitted outside the privileged operator's own channel.
- ARES-owned runtime secret location (not a path under FALCON's own secrets tree), read-only runtime mount, least-necessary filesystem permissions.
- `_FILE`-suffixed configuration convention used on the ARES side wherever applicable, matching the already-established pattern.
- This provisioning step is privileged/live and must be performed by whichever actor holds the appropriate privileged-operations role for each side (FALCON-side trust update vs. ARES-side key generation/mount) under this project's existing credential-boundary doctrine — no implementer subagent may hold or generate real key material.

## 8. Network requirements

- ARES publishes to `192.168.11.10:12412`.
- FALCON must expose this via host-port publication only (`12412 → 12412`), bound to the LAN IP, never `0.0.0.0` beyond what the existing Graylog input configuration already requires.
- ARES remains on `ares-net`. **ARES must not join `falcon-net`.** No general bridge between `ares-net` and `falcon-net`.
- No exposure of OpenSearch, Mongo, Data Node internals, or any unnecessary Graylog management/API surface as a side effect of this work.
- The exact mechanism for how a container on `ares-net` reaches the host's published `falcon-net`-adjacent port must be established and documented as part of this WO's execution (Stage 1 discovery found this reachability was not automatic — an explicit `ECONNREFUSED`, not a timeout, was observed; the previous network-preflight discovery mandate addressed to HELM covers the investigative groundwork, if completed, and should be read before execution).

## 9. Deployment requirements

- Minimum-necessary component recreation only on each side (no blanket `docker compose up` across unrelated services).
- No IRIS mutation, no restart, no reconfiguration, at any point.
- No HELIOS/TRON/NEO mutation.
- Pre-mutation state capture required on both sides before any live change (container identity/image/health/restart-count; FALCON cluster/index/stream/input state; ARES scheduler/SQL/Redis state) — mirroring the exact discipline already proven across every PID-05 deployment stage.

## 10. Canonical-checkout requirements

- FALCON: deploy from the canonical `maff0000/falcon` checkout at the exact approved base SHA, not any worktree.
- ARES: deploy from the canonical `maff0000/trading-ares` checkout at the exact approved base SHA — explicitly **not** `/srv-dev-worktrees/trading-ares` (confirmed stale during Stage 1 discovery) and not the legacy `tradingProteus/ares` tree (confirmed unrelated pre-extraction code).

## 11. UTC protocol

All platform timestamps use governed UTC semantics. Do not introduce SQL `NOW()`, `UTC_TIMESTAMP()`, naive `datetime.now()`, local-time-derived platform timestamps, or implicit timezone conversions anywhere in this WO's execution. ARES's existing aware-UTC discipline (`require_utc()`-equivalent enforcement) must be preserved exactly as merged in Stage 2B. Display/local presentation may use Europe/London where genuinely appropriate for human-facing output, but durable platform truth remains UTC throughout.

## 12. Regression requirements

- Existing FALCON/HERMES evidence ingestion (the already-closed PID-05 path) must remain healthy and unaffected — verify the HERMES 12411 path still functions correctly after the 12412 exposure work.
- Existing ARES operation (scheduler cadence, SQL persistence, Redis projection for `market_status` and all other P0 surfaces) must remain healthy and byte-identical in behaviour to pre-WO state.
- HELIOS/IRIS or other adjacent runtime should be observed only sufficiently to demonstrate no unintended impact where genuinely relevant (e.g. IRIS health snapshot before/after, as already standard practice) — this WO does not authorise any investigation beyond that minimal confirmation.

## 13. Test requirements

### FALCON
- Compose/config validation for the new 12412 publication.
- Dedicated 12412 exposure confirmed reachable from the expected ARES network path.
- Existing 12411 HERMES path confirmed unaffected (regression).
- ARES input confirmed state `RUNNING`.
- mTLS required and enforced; a connection with no client identity, or the wrong/stale client identity, is rejected.
- A connection with the newly-provisioned, correct ARES client identity is accepted.
- `market_status` contract validation: a genuinely valid event is accepted as `VALID`; a deliberately malformed one (e.g. missing `market_state`, or the old retired `PRE_OPEN` value) is correctly quarantined — reusing the already-merged Stage 2B fixtures/registry, not inventing new contract tests.
- FALCON indexing confirmed healthy throughout; quarantine behaviour confirmed correct for the deliberately-invalid case.

### ARES
- Configuration validation: the new evidence-publish config is loaded correctly; a deliberately malformed enabled-config fails loudly at startup exactly as already proven in the merged unit tests, now confirmed against the real deployment's actual startup sequence.
- Secret path/read permissions confirmed correct (file exists, correct mode/ownership, readable by the running process, not world-readable).
- Evidence publisher confirmed enabled and its background worker confirmed running.
- ARES scheduler confirmed healthy (no restart loop, no fault state) before, during, and after this WO's execution.
- Existing ARES persistence/state (SQL rows, Redis keys for all P0 surfaces, not just `market_status`) confirmed unaffected.
- A live `market_status` cycle confirmed to continue correctly with evidence publication enabled.
- Reconstructed evidence confirmed excluded from publication (if a reconstruction event can be safely and non-destructively triggered during this WO's window; if not practically triggerable without violating §9's deployment-safety constraints, rely on the already-merged, already-audited unit/component proof and record that explicitly rather than inventing a risky live trigger).
- Publisher failure confirmed unable to block the scheduler (§6).
- Recovery after a transient FALCON outage confirmed to work (§6).

## 14. Security requirements

- No secret value (private key, certificate private material, Redis/DB credentials) ever appears in Git, logs, chat, or Memory Fabric.
- Gitleaks (or equivalent) run on any newly Git-tracked configuration/documentation change produced by this WO's execution.
- No broadening of network exposure beyond the single, narrow ARES→FALCON:12412 path.
- No credential reuse across producers (the new ARES identity is distinct from HERMES's existing identity and from any future HELIOS/TRON identity).

## 15. Required evidence

For every live/privileged step: exact command, exact timestamp (UTC), exact before/after state, exact resulting container/image identity, exact SHA deployed on each side. For the runtime acceptance proof: exact FALCON event ID, natural key, `produced_at_utc`, routing/validity result, and a byte-level or hash-level confirmation that the rich producer-owned message round-trips intact. For the failure-isolation proof: exact induced-condition method, exact start/end UTC, exact queue/retry/recovery evidence, exact ARES restart count before and after (must be unchanged).

## 16. Rollback

- FALCON: revert to content-pack state prior to the 12412 exposure change (the existing, already-proven delete-diverging-entities-then-reinstall procedure, or a simple compose/env revert if no Graylog entity-level change was needed); no stored evidence/indices are ever rolled back or deleted.
- ARES: revert to the prior deployment (image/compose/config) with evidence publication disabled; no SQL/Redis state is ever rolled back or deleted.
- Credential rollback: if the newly-provisioned ARES identity must be revoked, remove only the new FALCON-side trust entry and the new ARES-side secret; do not touch any other producer's identity.
- Rollback authority and execution follow the same privileged-operations boundary as the original provisioning (§7).

## 17. Independent audit requirement

Any newly Git-tracked code/configuration produced in service of this WO (e.g. compose file changes, config manifest additions, documentation) must receive a fresh, independent FORGE Auditor review bound to its exact candidate SHA before any PR is accepted, following the identical discipline already proven across every PID-05 and PID-06 Stage 2A/2B round in this project: the Auditor independently re-verifies claims rather than trusting the implementer's report, and the verdict is explicitly bound to the exact SHA under review.

## 18. PR requirements for tracked changes

- Isolated branch/worktree per repository touched; no direct commits to either `main`.
- Focused, logically separated commits.
- PR description accurately reflects the change, references this WO identifier and its parent PID.
- CI green (each repository's existing CI, unmodified in its gating logic by this WO).
- No merge without Central Architecture's explicit acceptance of the exact candidate SHA(s), exactly as practiced throughout PID-05 and PID-06 Stage 2A/2B.

## 19. Architect acceptance gate

Central Architecture must explicitly accept: (a) this Work Order itself before any implementer/sysops mandate is dispatched against it; (b) each exact candidate SHA produced during execution, after independent audit, before merge; (c) the final runtime-acceptance evidence package before PID-06 is considered closed. No step in this chain may be skipped or combined without explicit instruction to do so.

## 20. Merge rules for any newly required tracked changes

True merge commits only; no squash; no rebase-merge; exact-head-match protection used where supported; merge order and any cross-repository sequencing constraints to be specified by Central Architecture at acceptance time if more than one repository requires a tracked change during execution (mirroring the FALCON-before-ARES sequencing already used for Stage 2B, pending Architect confirmation of whether the same ordering applies here).

## 21. Runtime closure criteria

PID-06 Stage 3 (this WO) is closed only when: both canonical deployments are confirmed running from their approved exact SHAs with no dependency on any disposable worktree; the real-event acceptance test (§5, items 11–20) has passed with recorded evidence; the failure-isolation test (§6) has passed with recorded evidence; all regression checks (§12) are confirmed green; Findings A and B remain explicitly recorded as open, non-blocking, carried-forward items (not silently resolved); and Central Architecture has explicitly accepted the full evidence package.

## 22. Memory Fabric handover requirement

A durable handover record must be written on completion of execution (not merely planning), under a key such as `rogue:handover:falcon:pid06_stage3_runtime_acceptance:<UTC>`, containing: exact deployed SHAs on both sides, exact credential-provisioning summary (never including secret values), exact network-path mechanism used, full runtime-acceptance evidence summary, full failure-isolation evidence summary, confirmation of regression results, and confirmation that Findings A and B remain open and recorded. GitHub remains the durable engineering authority; this Fabric record is operational continuity only.

## 23. STOP conditions (binding on every implementer/sysops mandate derived from this WO)

Stop and return to Central Architecture, without improvising, if: the canonical base SHA on either side has moved in a way that is not clearly safe to proceed against; the real ARES-to-FALCON network path requires a mechanism broader than a single narrow port-forward/firewall-allow (e.g. anything resembling a general bridge between `ares-net` and `falcon-net`); the credential-provisioning step cannot be completed without violating the privileged-operations/credential boundary; any test in §13 fails and the cause is not immediately, narrowly, and safely correctable within this WO's exact scope; the failure-isolation test (§6) reveals the real runtime does *not* match the already-audited non-blocking architecture; or any ambiguity arises about whether a given action is inside or outside this WO's authorised scope.

## 24. PID-07 prohibition

PID-07 is explicitly not authorised by this WO and must not be started, referenced as a dependency, or prepared for under any mandate derived from this WO.

## 25. Explicit exclusions (reaffirmed from PID-06 itself, binding on this WO specifically)

This WO does not authorise, and any mandate derived from it must not perform: PID-07 (see §24); Calendar, Liquidity, Macro-USD, or source-quality evidence publication; any `publication.decision` family redesign; source-quality SQL persistence work; remediation of the pre-existing, unrelated macro_usd HERMES-identity-fingerprint issue; general FALCON OpenSearch authentication remediation; Mongo credential rotation; any HERMES, HELIOS, or TRON code change; general Docker/network redesign beyond the single narrow ARES↔FALCON:12412 path described in §8; any `tar-risk-engine` repair or investigation.
