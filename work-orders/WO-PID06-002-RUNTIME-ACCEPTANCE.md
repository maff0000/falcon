# Work Order: WO-PID06-002-RUNTIME-ACCEPTANCE

**Status:** ACCEPTED — Central Architecture has reviewed and accepted this Work Order as durable project
authority, and has authorised dispatch of bounded Implementer mandates against it (see Acceptance record
below). This status supersedes the original "DRAFT — NOT authorised for execution" line this document
carried at merge time (PR #13, `d4ec1b3bf831829b84c2ad9deb886544f745444b`, merged as
`c9002a90e388484ef4d4b0affea7d771e2b7233c`) — that line was accurate at the time it was written and is
retained in this file's Git history, not rewritten, per this project's own discipline against silently
erasing prior state. Acceptance of this WO authorises dispatching Implementer mandates against its exact
scope; it does not itself authorise merging any resulting candidate, deploying anything, or starting
PID-07 — each of those remains independently gated exactly as this WO's own §18-21 and §24 already specify.

## Acceptance record

- **Accepted by:** Central Architecture (the Architect authority for this project), via explicit instruction
  to the Delivery Controller (Rogue).
- **Accepted:** "ROGUE — DELIVERY CONTROLLER / PID-06 — Merge Accepted Runtime Acceptance Work Order" —
  "Central Architecture has reviewed and **ACCEPTED**: `WO-PID06-002-RUNTIME-ACCEPTANCE`" (authorising the
  merge of PR #13, carried out and verified — merge SHA `c9002a90e388484ef4d4b0affea7d771e2b7233c`, parent 2
  `d4ec1b3bf831829b84c2ad9deb886544f745444b`, confirmed present on canonical `main`).
- **Dispatch authorised:** "ROGUE — DELIVERY CONTROLLER / PID-06 — Dispatch Runtime Configuration
  Implementation / WO-PID06-002-RUNTIME-ACCEPTANCE" — "Central Architecture accepts the Work Order as
  durable authority... Dispatch: FORGE — IMPLEMENTER against `WO-PID06-002-RUNTIME-ACCEPTANCE`", scoped
  explicitly to the durable, non-secret configuration items in §5 FALCON item 1-2 / ARES item 7-8, with
  HELM's own subsequent runtime-mutation mandate explicitly withheld pending separate authorisation.
- **This correction's own authority:** this status update is itself a Delivery-Controller-level durable-record
  correction (not new architecture, not implementation against the WO's technical scope) — making the
  already-given, already-acted-upon Architect acceptance visible in Git, per this WO's own §19 requirement
  that Architect acceptance of the WO itself precede any implementer dispatch, and per the project's own
  "no Git record → not durable project authority" rule. It was prompted by a FORGE Implementer correctly
  refusing to proceed against the stale DRAFT/NOT-AUTHORISED line still present in Git at dispatch time —
  exactly the STOP-on-ambiguity discipline this WO requires, working as intended.

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

- **FALCON canonical base:** `c9002a90e388484ef4d4b0affea7d771e2b7233c` (`maff0000/falcon`, main) — updated
  from the original `d4644f548de98e5371e8519b391fde422157ce54` recorded when this WO was first drafted;
  the Delivery Controller has determined this advance is safe: the only commit in between is `d4ec1b3`
  (merged as `c9002a9` via PR #13), which is this WO document and its parent PID correction themselves —
  a documentation-only, self-referential advance that touches nothing this WO's technical scope depends on.
- **ARES canonical base:** `2525455669ca068fcf5b17592b3d4a9f28ee2185` (`maff0000/trading-ares`, main)

If either canonical `main` moves again before this WO is fully executed, the Delivery Controller must determine whether updating the WO's recorded base SHA is safe (i.e. the move is unrelated/additive and does not touch anything this WO depends on) before proceeding, and must record that determination in Git exactly as above. **Do not silently implement against an unapproved replacement base.**

## 4. Objective

Prove, with real runtime evidence, that the already-merged PID-06 Stage 2B vertical slice (ARES `market_status` → FALCON evidence publication) works end-to-end in the real environment: ARES can reach FALCON's dedicated ingress, authenticate with a freshly-provisioned identity, publish a real live observation that FALCON indexes as `VALID` with its full producer-owned message and corrected searchable contract intact — and that FALCON's unavailability/latency provably does not materially interfere with ARES's primary operation, under real (not merely unit-simulated) network conditions.

## 5. Scope

The smallest set of runtime/configuration changes required to prove the above:

### FALCON
1. Expose FALCON's existing dedicated ARES GELF/mTLS input on host port `12412`, mirroring the already-proven HERMES `12411` model exactly (same Docker publish pattern, same bind-to-LAN-IP-not-`0.0.0.0` discipline, same no-general-bridge discipline).
2. Add the required governed environment/configuration entry for this exposure.
3. Provision/update FALCON-side trust material for the newly generated ARES client identity (§7).
4. Build/deploy from canonical merged FALCON main (`c9002a90e388484ef4d4b0affea7d771e2b7233c`, per §3) only.
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

## 26. Open architectural finding — ARES canonical deployment topology (recorded, not resolved by this WO)

Execution of this WO's §5 ARES items 7-10 surfaced a real architectural gap, STOPPED on rather than
improvised past, per §23: the canonical, Git-tracked, CI-hardened ARES deployment
(`docker/docker-compose.ares.yaml` + `docker/Dockerfile.live`, `maff0000/trading-ares`) defines exactly
three services — `ares-db`, `ares-cache`, `ares-core` — and `ares-core`'s image `CMD` is exactly
`python -m runtime.compose_root`. **No service anywhere in the canonical deployment runs
`runtime.foundation`** — the module hosting the market-status scheduler job (`JOB_MARKET_STATUS`) and the
now-merged Stage 2B evidence-publisher wiring (`_publish_market_status_evidence`). Confirmed exhaustively:
no second Dockerfile, no entrypoint/supervisor script bundling both processes, no other compose file in the
repository references `foundation` at all. The `ares-foundation` container that actually executes this code
today exists only in the disposable Stage-1-era worktree deployment path (`/srv-dev-worktrees/trading-ares`)
this WO explicitly intends to retire dependence on (§10).

**Consequence**: adding the evidence-publisher's runtime configuration to `ares-core`'s environment (this
WO's §5 item 7 as originally scoped) would be inert in the canonical deployment — nothing in that topology
would ever read or act on it, since the process that needs it is not part of the canonical service set.
Making the merged Stage 2B capability real on the canonical deployment path requires adding a new service
to `docker/docker-compose.ares.yaml` (image/CMD reference, healthcheck, any required secrets/volume wiring)
— a materially broader deployment change than "durable, non-secret configuration," and therefore outside
this WO's own §5/§23 narrow-scope boundary as drafted.

**Disposition**: not resolved here. Returned to Central Architecture for a ruling on one of: (a) amend this
WO (or issue a successor WO) to explicitly authorise adding an `ares-foundation`-equivalent service to the
canonical ARES compose; (b) direct that `ares-core`'s own process should instead absorb the P0 scheduler
jobs (a different, and likely larger, architectural change to `runtime.compose_root` itself); (c) some other
resolution Central Architecture prefers. No ARES-side implementation has been dispatched or performed
pending this ruling.

## 27. §26 resolution — ARES Foundation canonicalisation (AMD-PID06-001)

Central Architecture has reviewed the read-only topology discovery referenced in §26 and issued a binding
architecture decision, recorded in full at `pids/amendments/AMD-PID06-001-ARES-FOUNDATION-CANONICAL-SERVICE.md`.
**§26 is resolved, not left open**, as follows:

ARES has two distinct canonical application process roles — `ares-core` (`python -m runtime.compose_root`)
and `ares-foundation` (`python -m runtime.foundation`). `ares-foundation` shall become an explicit, canonical,
Git-governed service in ARES's Docker Compose deployment, using the same application image as `ares-core`
with a different command, preserving full process separation (no absorption of Foundation into Core, no
shared-container supervisor). This formalises the process architecture already present in ARES's code and
already proven in the live environment; it does not create a FALCON-specific ARES process — Foundation's P0
scheduling responsibilities (Calendar, Market Status, Liquidity, Macro/USD) exist and are required
independently of FALCON.

This Work Order's scope is hereby amended: **§5 ARES item 9's "expected: `ares-foundation`" is confirmed**,
and is now explicitly understood to mean *canonicalising* `ares-foundation` as a new compose service — not
merely redeploying an already-canonical one. Once this amended Work Order itself has been independently
reviewed, Architect-accepted, and merged, FORGE is authorised to make the smallest tracked ARES deployment
change required to:

1. add canonical `ares-foundation` to `docker/docker-compose.ares.yaml`;
2. use the existing ARES application image (no second image);
3. run `python -m runtime.foundation` as its command;
4. provide the correct existing config/secret mounts (mirroring `ares-core`'s pattern);
5. configure the existing Foundation activation mechanism (`ARES_FOUNDATION_RUNTIME_ENABLED`), explicitly
   set, no hidden default;
6. add appropriate existing-style hardening (non-root user, read-only rootfs, capability drop,
   `no-new-privileges`, `ares-net` only, consistent restart policy) — correcting the existing manual
   container's missing `no-new-privileges` as deployment drift, not preserving it;
7. add the smallest truthful healthcheck, derived from existing ARES health facilities / Foundation's own
   heartbeat/job-health mechanisms only — if no existing mechanism can truthfully establish Foundation
   readiness/liveness without new application functionality, STOP → CENTRAL ARCHITECTURE rather than
   inventing one;
8. provide the Stage 2B FALCON evidence-publisher configuration (§5 item 7 of this WO) to the canonical
   `ares-foundation` service, where it is live rather than inert;
9. remove dependence on the manually-created Foundation runtime during the eventual HELM deployment covered
   by this WO's §9/§10 (the existing manual `ares-foundation` container itself remains untouched by this
   amendment and by any Delivery-Controller-level mandate — its retirement is a HELM-authorised runtime
   mutation, separately gated exactly as this WO's §9 already requires);
10. preserve `ares-core` as a fully separate process — no merged lifecycle, no shared supervisor.

AMD-PID06-001's binding constraints (§3–§16 of that document) govern this implementation exactly as if
reproduced here: shared image/separate command; no absorption into `compose_root`; no FALCON startup
dependency; Findings A and B remain open and must not be opportunistically fixed; no change to existing P0
job business semantics, cadence, or enablement rules; canonical source only
(`maff0000/trading-ares`, never `/srv-dev-worktrees/trading-ares` or a manual `docker run`); UTC protocol
unchanged; the same explicit exclusions reaffirmed (no PID-07, no Calendar/Liquidity/Macro-USD/source-quality
publication, no `publication.decision` redesign, no HERMES/HELIOS/TRON/`tar-risk-engine` change).

This section is itself documentation/governance only. It does not dispatch FORGE or HELM, and does not
authorise any implementation until this amended Work Order has itself passed independent audit, PR, and
Architect acceptance, per §1's governance chain.

## 28. Foundation healthcheck — AMD-PID06-002 supersedes §27 item 7

Attempted implementation of §27 item 7 (the canonical `ares-foundation` healthcheck) correctly hit a STOP:
no existing ARES mechanism (`runtime/health.py`, in-memory scheduler/heartbeat state, heartbeat log lines,
or the `ares:v1:health:summary` Redis surface) can truthfully establish Foundation liveness from a fresh
in-container healthcheck process without new application functionality — and `AMD-PID06-001` §10 required
an existing mechanism only. Central Architecture has reviewed this finding and ruled that the narrow new
functionality required is authorised, under a dedicated amendment:
`pids/amendments/AMD-PID06-002-ARES-FOUNDATION-LIVENESS.md`.

**§27 item 7 is superseded exactly as follows**: wherever §27 required "the smallest truthful *existing*
mechanism," it now additionally permits — and AMD-PID06-002 binds the specifics of — the smallest *new*
local liveness-marker mechanism described there, extending the existing `JOB_HEARTBEAT` progress signal
(`clients._last_heartbeat_utc`) to a container-external, Docker-probeable file, read by a small local,
dependency-free healthcheck command. No other item of §27, and no other provision of AMD-PID06-001, is
affected by this supersession.

Once this amended Work Order is itself independently audited, Architect-accepted, and merged, FORGE is
authorised to implement, strictly per AMD-PID06-002:

1. the minimal local liveness-marker writer, integrated into Foundation's existing `_heartbeat_job()` path
   (no second heartbeat thread);
2. the minimal local liveness reader/CLI (no network/SQL/Redis/HERMES/FALCON/Graylog calls);
3. a staleness threshold deterministically derived from `sched_config.heartbeat_interval_s`, documented and
   tested — not a hardcoded constant;
4. deterministic unit/component tests covering: fresh marker → healthy; missing marker → unhealthy;
   malformed marker → unhealthy; stale marker → unhealthy; valid UTC parsing; future-invalid marker →
   unhealthy; heartbeat progress updates the marker; stopped progress eventually yields stale state;
   dependency failure (Redis/SQL/HERMES/FALCON) does not directly control local liveness; startup does not
   report healthy before genuine first heartbeat progress — using deterministic clock injection, not
   sleep-heavy wall-clock tests;
5. the canonical Compose `healthcheck:` block for `ares-foundation` invoking this local reader, with a
   `start_period` sized to legitimate Foundation initialisation.

Nothing broader than this list, and nothing in AMD-PID06-001's other provisions (process separation, no
FALCON startup dependency, canonical source, existing P0 job semantics), is reopened by this section.

This section is itself documentation/governance only. It does not dispatch FORGE or HELM, and does not
authorise any implementation until this amended Work Order has itself passed independent audit, PR, and
Architect acceptance, per §1's governance chain.
