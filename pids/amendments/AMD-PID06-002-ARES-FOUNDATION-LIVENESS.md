# Amendment AMD-PID06-002 — ARES Foundation Liveness

**Parent PID:** PID-06 — Canonical ARES → FALCON Integration (`pids/PID-06-ARES-INTEGRATION.md`)
**Supersedes (narrowly):** `AMD-PID06-001-ARES-FOUNDATION-CANONICAL-SERVICE.md` §10 "Healthcheck" — only the
constraint that an existing mechanism must be used; every other provision of AMD-PID06-001 remains in force
unchanged, including §5 (process separation), §7 (no FALCON startup dependency), and §11 (no change to P0
job semantics).
**Resolves:** the STOP raised during the AMD-PID06-001/WO-PID06-002 §27 item 7 implementation attempt — no
existing mechanism in `runtime/foundation.py`, `runtime/health.py`, `runtime/scheduler.py`, or the
`ares:v1:health:summary` Redis surface can truthfully establish Foundation liveness from a fresh
in-container healthcheck process without new application functionality. That finding is accepted as
correct; this amendment authorises the narrow new functionality required to resolve it.
**Status:** ACCEPTED — architecture/governance only. No implementation authorised by this document alone;
implementation requires the amended Work Order (§7 below) to itself be accepted and merged.
**Authority:** Central Architecture, via explicit instruction to the Delivery Controller (Rogue): "ROGUE —
DELIVERY CONTROLLER / PID-06 — FALCON Merge + ARES Foundation Liveness Amendment."

## Governance chain (binding, copied forward per project discipline)

```
Architecture decision → PID/Amendment → Git-tracked Work Order → Delivery Controller → Implementer → Independent Audit → PR → Architect Acceptance → Merge → Closure
```

Hard invariants: **NO PID → NO WORK ORDER.** **NO WORK ORDER → NO IMPLEMENTATION.**
**NO INDEPENDENT AUDIT + ARCHITECT ACCEPTANCE → NO MERGE.** **NO GIT RECORD → NOT DURABLE PROJECT
AUTHORITY.**

## Exact bases this amendment is recorded against

- **FALCON canonical:** `4e6ed3854aa9e14b60b9ec2735af3ef3b24c1afe` (`maff0000/falcon`, `main`) — PR #16
  merged (FALCON 12412 host-port exposure).
- **ARES canonical:** `2525455669ca068fcf5b17592b3d4a9f28ee2185` (`maff0000/trading-ares`, `main`) — PID-06
  Stage 2B merged; unchanged since discovery.

## 1. Objective

Provide Docker with a truthful indication that the `runtime.foundation` process is alive and its
scheduler/event loop is continuing to make progress. This is **liveness only** — not full dependency
health and not business correctness. Dependency/business-health conditions (SQL, Redis, HERMES, FALCON
reachability) remain observable exclusively through ARES's existing health/evidence mechanisms
(`JOB_HEALTH`, `JOB_PUBLICATION_HEALTH`, `ares:v1:health:summary`) and must not be folded into the Docker
liveness signal.

## 2. Grounding — the existing mechanism this amendment extends

`runtime/foundation.py`'s own `JOB_HEARTBEAT` (cadence: `sched_config.heartbeat_interval_s`, from
`ares.config.scheduler_config.load_scheduler_config`) already runs `_heartbeat_job()` on every scheduler
tick, which already records "the REAL heartbeat instant so the selftest can prove the supervisor is alive
from evidence rather than from the fact that a process exists" — today only in-process, via
`clients._last_heartbeat_utc["*"] = beat` (a genuine, governed-UTC `datetime`, written before the
corresponding log line). This amendment extends exactly this existing progress signal to a
container-external, Docker-probeable form. **It does not create a second, independent heartbeat path.**

## 3. Liveness marker (binding)

Foundation maintains a local runtime liveness marker:

- A file on a container-local writable runtime location (not a new persistent Docker volume — this is
  ephemeral runtime state; a container restart naturally recreates it). The exact path is an implementation
  detail, selected by the Implementer using existing ARES/container filesystem conventions (e.g. the
  existing `tmpfs: ["/tmp"]` mount already used by both `ares-core` and the prospective `ares-foundation`
  service under AMD-PID06-001 §9's hardening model).
- Written from inside the existing `_heartbeat_job()` hook (§2) — the same point that already updates
  `clients._last_heartbeat_utc`, not a new thread or job.
- Timestamp stored as governed aware UTC (§8).
- Written atomically where practical (e.g. write-to-temp-then-rename within the same filesystem), so a
  reader never observes a partially-written marker.
- Owned/readable only as required by the existing non-root ARES process user (`10001:10001`, per
  AMD-PID06-001 §9) — no new privilege is introduced.

## 4. What updates the marker (binding)

Only the existing Foundation heartbeat/scheduler-progress path (§2) may update the marker. No second,
independent heartbeat thread may be created merely to satisfy Docker. The marker must only advance when the
real Foundation scheduler is making progress — a process that has started but whose scheduler has wedged
must eventually present as unhealthy, not evergreen.

## 5. Healthcheck reader (binding)

A small, local, dependency-free healthcheck command/module:

1. Reads the liveness marker.
2. Validates its timestamp strictly.
3. Compares it using governed UTC (§8).
4. Exits `0` when sufficiently fresh (§6).
5. Exits non-zero when: missing; malformed; future-invalid beyond reasonable clock tolerance; or stale.

No network calls. No SQL. No Redis. No HERMES. No FALCON. No Graylog. No log parsing. The reader must be
able to run and return a verdict using only the local filesystem and the local clock.

## 6. Staleness threshold — derived, not hardcoded (binding)

The threshold must be derived from the actual Foundation heartbeat cadence
(`sched_config.heartbeat_interval_s`), using a bounded multiplier/tolerance sufficient to absorb normal
scheduling jitter without causing false-unhealthy transitions, and the derivation must be documented in code
and covered by a test asserting the relationship (not merely asserting a literal number). No arbitrary fixed
constant (e.g. a bare "60 seconds") may be hardcoded independently of the real configured cadence. **If the
existing cadence configuration cannot support a deterministic bounded threshold (for example because it is
unbounded, absent, or not available to the healthcheck reader at the point it needs it): STOP → CENTRAL
ARCHITECTURE** — do not pick an arbitrary number to make this requirement go away.

## 7. Startup semantics (binding)

Docker's `start_period` must accommodate legitimate Foundation initialisation before the first liveness
marker is expected to exist. **No fake/placeholder marker may be written at container start merely to make
Docker report green.** Health becomes true only after genuine first heartbeat-job progress.

## 8. UTC protocol (binding)

All marker timestamps and comparisons use governed UTC exactly as already enforced elsewhere in this
codebase (ARES's existing aware-UTC doctrine, matching `clients._last_heartbeat_utc`'s own real `datetime`).
No naive `datetime.now()`, no local-time timestamp, no SQL `NOW()`/`UTC_TIMESTAMP()`, no implicit timezone
conversion. A malformed or non-aware timestamp in the marker must fail closed (treated as invalid, per §5
item 5), never silently coerced.

## 9. Failure semantics (binding)

The healthcheck answers only "is the Foundation runtime alive and progressing?" Therefore: FALCON
unavailable → Foundation can remain healthy; HERMES temporarily unavailable → Foundation can remain healthy
if scheduler progress continues; Redis unavailable → must not automatically fail the Docker health signal
solely on that basis; SQL unavailable → must not automatically fail the Docker health signal solely on that
basis. Whole-system/dependency readiness is not Docker liveness's job under this amendment.

## 10. No restart/watchdog automation (binding)

Docker Compose health status must not be wired, under this amendment, to any new automatic restart
controller or watchdog. Existing `restart: unless-stopped` semantics remain exactly as they are. Health
here is observability for operators/orchestration only.

## 11. Explicit exclusions (binding)

This amendment does not authorise: a general health API; an HTTP health server; a new Redis health schema;
SQL health persistence; a new monitoring platform; scheduler redesign; cadence redesign; Finding A or
Finding B remediation; evidence-publisher redesign; any other ARES→FALCON family; any change to
`ares-core`/`runtime.compose_root`; HERMES, HELIOS, or TRON changes; `tar-risk-engine`; PID-07.

## 12. Findings A and B (unchanged, explicitly not resolved here)

- **Finding A** — Stage 2B evidence-publisher queue-sizing rationale does not cover the full valid
  30–3600-second configuration range.
- **Finding B** — Stage 2B shutdown wiring lacks a dedicated end-to-end hung-publisher integration test.

Neither is touched, referenced, or incidentally affected by this amendment.

## 13. Next durable authority

`work-orders/WO-PID06-002-RUNTIME-ACCEPTANCE.md` is amended alongside this document (new §28) to record
that AMD-PID06-002 is now the controlling decision for Foundation healthcheck implementation, narrowly
superseding §27 item 7's previous "existing mechanism only" constraint, and to explicitly authorise the
bounded future implementation (marker writer, local reader, deterministic tests, compose healthcheck
wiring) once this amended WO is itself independently audited, Architect-accepted, and merged. PID-06 remains
the parent of both documents.
