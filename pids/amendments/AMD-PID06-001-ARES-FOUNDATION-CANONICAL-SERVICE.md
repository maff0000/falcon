# Amendment AMD-PID06-001 — ARES Foundation Canonical Service

**Parent PID:** PID-06 — Canonical ARES → FALCON Integration (`pids/PID-06-ARES-INTEGRATION.md`)
**Resolves:** `work-orders/WO-PID06-002-RUNTIME-ACCEPTANCE.md` §26 (open architectural finding)
**Status:** ACCEPTED — architecture/governance only. No implementation authorised by this document alone;
implementation requires the amended Work Order (see §10 below) to be itself accepted and merged.
**Authority:** Central Architecture, via explicit instruction to the Delivery Controller (Rogue):
"ROGUE — DELIVERY CONTROLLER / PID-06 — ARES Canonical Foundation Service / Architecture Amendment + WO
Amendment ONLY."

## Governance chain (binding, copied forward per project discipline)

```
Architecture decision → PID/Amendment → Git-tracked Work Order → Delivery Controller → Implementer → Independent Audit → PR → Architect Acceptance → Merge → Closure
```

Hard invariants: **NO PID → NO WORK ORDER.** **NO WORK ORDER → NO IMPLEMENTATION.**
**NO INDEPENDENT AUDIT + ARCHITECT ACCEPTANCE → NO MERGE.** **NO GIT RECORD → NOT DURABLE PROJECT
AUTHORITY.**

## Exact bases this amendment is recorded against

- **FALCON canonical:** `d319eeb27e281a66c5115f46e72c522dba887c95` (`maff0000/falcon`, `main`) — PR #14
  merged.
- **ARES canonical:** `2525455669ca068fcf5b17592b3d4a9f28ee2185` (`maff0000/trading-ares`, `main`) — PID-06
  Stage 2B merged.

## 1. Background — the finding this amendment resolves

A read-only topology discovery (authorised by Central Architecture after WO-PID06-002 §26 was raised)
established, directly from the canonical repository and the live deployment, the following facts:

- `runtime/foundation.py` (`python -m runtime.foundation`) is the **sole scheduler and sole call site** in
  the entire ARES repository for the Calendar, Market Status, Liquidity, and Macro/USD P0 evaluation
  cycles, in addition to its own Foundation housekeeping jobs (health-evaluation,
  publication-health-evaluation, redis-retention-trim, runtime-heartbeat). None of this scheduling exists
  in or is reachable from `runtime/compose_root.py`.
- `runtime/compose_root.py` (`python -m runtime.compose_root`, the canonical `ares-core` service's entry
  point) owns a structurally separate set of responsibilities (live emitter, risk engine, trader-surface
  projection, briefs, telemetry bus) and does not import `runtime.foundation`.
- The canonical, Git-tracked deployment (`docker/docker-compose.ares.yaml` + `docker/Dockerfile.live`)
  defines exactly three services — `ares-db`, `ares-cache`, `ares-core` — and never defines a service
  running `runtime.foundation`.
- The live environment already runs both roles as two separate, long-lived containers (`ares-core` and
  `ares-foundation`) from the **same** application image, on the same `ares-net` network, both with
  `unless-stopped` restart policy, both reboot-proven (confirmed via a host-reboot census showing
  `ares-foundation` survived with 0 restarts), and `ares-foundation` is already treated as legitimate,
  continuously-monitored infrastructure by existing HELM operational tooling (soak/baseline scripts reading
  its `SCHED_JOB_OK` job-health log lines). No record was found of `ares-foundation` ever being created via
  `docker compose`; it carries no compose labels and is missing one hardening flag
  (`no-new-privileges`) relative to `ares-core`.

## 2. Architecture decision

ARES has **two distinct canonical application process roles**:

1. `ares-core` — entry point `python -m runtime.compose_root`.
2. `ares-foundation` — entry point `python -m runtime.foundation`.

**`ares-foundation` shall become an explicit, canonical, Git-governed service in ARES's Docker Compose
deployment.** `runtime.foundation` is **not** absorbed into `runtime.compose_root`. This decision formalises
the process architecture already present in ARES's code and already proven in the live environment. **It
does not create a FALCON-specific ARES process** — Foundation's P0 scheduling responsibilities (Calendar,
Market Status, Liquidity, Macro/USD) exist and are required independently of FALCON; FALCON's Stage 2B
evidence publisher is one small, optional, best-effort output that this process happens to also own.

**The defect this amendment corrects:** the real ARES process architecture was never completely promoted
into the canonical Git-tracked Compose deployment. PID-06 exposed this defect; PID-06 did not create it.

## 3. Canonical service topology (binding)

ARES canonical deployment comprises: `ares-db`, `ares-cache`, `ares-core`, **`ares-foundation`**. This
amendment concerns only formalising `ares-foundation`; it does not otherwise redesign ARES.

## 4. Shared image, separate command (binding)

`ares-foundation` uses the same canonical ARES application image as `ares-core` unless implementation
evidence proves that impossible. Its command is `python -m runtime.foundation`. No second application image
may be created merely to change the entry point.

## 5. Process separation (binding)

`runtime.compose_root` is not modified to absorb Foundation. The two process lifecycles are not merged. No
supervisor may be introduced to run both processes inside one container. One process role per container
remains the intended model.

## 6. Foundation enablement (binding)

The canonical Foundation service must explicitly enable its existing activation mechanism
(`ARES_FOUNDATION_RUNTIME_ENABLED`) via the existing governed ARES configuration mechanism. No hidden
default may make the service appear enabled. Missing required configuration must fail loudly, per existing
ARES doctrine.

## 7. Dependencies (binding)

Use only the dependencies actually required by `runtime.foundation`: `ares-db`, `ares-cache`, and HERMES
contract access where required by enabled jobs. FALCON is **not** added as an ARES startup dependency. ARES
Foundation must remain able to perform its primary ARES responsibilities when FALCON is unavailable.

## 8. FALCON evidence publisher (binding)

The already-merged Stage 2B evidence publisher remains an optional, best-effort output owned by the
Foundation process. Its failure must not become Foundation failure. Its configuration belongs on the
canonical `ares-foundation` service, not inertly on `ares-core`.

## 9. Security/hardening (binding)

The canonical service inherits the established ARES container-hardening model, including as applicable:
non-root user, read-only root filesystem, capability drop, `no-new-privileges`, the existing secret
mechanism, `ares-net` only, and a restart policy consistent with ARES runtime doctrine. The existing
manually-created container's missing `no-new-privileges` is deployment drift to be corrected through
canonicalisation — it is not preserved merely because the manual container currently lacks it.

## 10. Healthcheck (binding)

The canonical `ares-foundation` service must have a meaningful healthcheck. `ares-core`'s readiness probe
must not be blindly copied if it does not prove Foundation health. Before implementing the healthcheck, the
Implementer must inspect existing ARES health facilities and Foundation's own heartbeat/job-health
mechanisms and use the smallest truthful existing mechanism. **If no existing mechanism can truthfully
establish Foundation readiness/liveness without new application functionality: STOP → CENTRAL
ARCHITECTURE.** No large health subsystem may be invented under this amendment.

## 11. Existing P0 jobs (binding)

Canonicalisation must not alter the business semantics, cadence, or enablement rules of: Calendar, Market
Status, Liquidity, Macro/USD, Foundation health, publication health, retention trim, or heartbeat. This is
deployment canonicalisation, not scheduler redesign.

## 12. Canonical source (binding)

Deployment must ultimately originate from canonical `maff0000/trading-ares` — not
`/srv-dev-worktrees/trading-ares` and not a manual `docker run` command. The current manually-created
`ares-foundation` container is evidence/rollback context only.

## 13. Documentation drift (recorded, not corrected here)

The discovery found that `runtime/foundation.py`'s own module docstring describes an older,
Foundation-housekeeping-only scope ("F3 foundation ONLY — no P0 business jobs"), while the implementation
beneath it has, over a sequence of prior Work Orders, also come to own the four P0 scheduler families. This
is recorded here as documentation drift. It is not corrected by this architecture-only amendment; any
application-source documentation correction belongs in the implementation candidate authorised by the
amended Work Order, if that WO's scope is read to cover it.

## 14. Findings A and B (unchanged, explicitly not resolved here)

- **Finding A** — the Stage 2B evidence-publisher queue-sizing rationale assumed ARES's default 300-second
  market-status evaluation interval and does not establish capacity across the full valid 30–3600-second
  configuration range.
- **Finding B** — the Stage 2B shutdown wiring (`runtime/foundation.py`'s `run()`) is supported by code
  inspection and component-level tests but lacks its own dedicated end-to-end integration test exercising a
  hung publisher through the real supervisor shutdown path.

Neither finding is resolved by canonicalising Foundation. Canonicalisation must not opportunistically fix
either finding.

## 15. UTC protocol

All durable timestamps remain governed UTC. No SQL `NOW()`/`UTC_TIMESTAMP()`, naive `datetime.now()`,
local-time platform timestamps, or implicit timezone conversion may be introduced. Europe/London remains
presentation-only where appropriate.

## 16. Explicit exclusions

This amendment does not authorise: implementation; live deployment; container creation; container
replacement; stopping the existing manual `ares-foundation`; certificate generation; port 12412 exposure;
FALCON runtime mutation; scheduler redesign; moving Foundation into Core; new scheduler jobs; changes to
existing P0 business semantics; Calendar, Liquidity, or Macro/USD FALCON publication; source-quality
publication; `publication.decision` redesign; HERMES changes; HELIOS changes; TRON changes;
`tar-risk-engine`; PID-07.

## 17. Next durable authority

`work-orders/WO-PID06-002-RUNTIME-ACCEPTANCE.md` is amended alongside this document (new §27) to record
that §26 is now architecturally resolved by this amendment, and to explicitly authorise the bounded future
implementation described there. PID-06 remains the parent of both documents.
