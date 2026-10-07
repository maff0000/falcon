# Work Order: WO-PID07-001-HELIOS-DISCOVERY

**Status:** ACCEPTED — Central Architecture authorised this discovery mandate directly ("ROGUE — DELIVERY
CONTROLLER / FALCON PID-07 — Stage 1: HELIOS Read-Only Discovery & Contract Reconciliation"); the discovery
work this WO governs is now **COMPLETE**, recorded at
`docs/architecture/PID07-HELIOS-STAGE1-DISCOVERY.md`. This WO does not itself authorise any PID-07
implementation — only the discovery/documentation work described below.

## 1. Governance chain (binding, copied forward per project discipline)

```
Architecture decision → PID/Amendment → Git-tracked Work Order → Delivery Controller → Implementer → Independent Audit → PR → Architect Acceptance → Merge → Closure
```

Hard invariants: **NO PID → NO WORK ORDER.** **NO WORK ORDER → NO IMPLEMENTATION.** **NO INDEPENDENT AUDIT +
ARCHITECT ACCEPTANCE → NO MERGE.** **NO GIT RECORD → NOT DURABLE PROJECT AUTHORITY.** For this WO,
"implementation" means the governed discovery/documentation work described in §3 below — no application
code, schema, or runtime change is authorised by this WO.

## 2. Identifier and parent

- **WO identifier:** `WO-PID07-001-HELIOS-DISCOVERY`
- **Parent PID:** PID-07 — HELIOS Evaluation and State Evidence (`pids/PID-07-HELIOS-OBSERVABILITY.md`),
  reconciled alongside this WO to introduce its Stage 1.
- **Applicable doctrine authority:** Producer Contract Evolution Doctrine, Decision 32
  (`docs/architecture/04-PRODUCER-CONTRACT-EVOLUTION-DOCTRINE.md`) — binding on every finding and
  recommendation in this WO's output, in particular §12 (HELIOS-specific non-freezing ruling: discover the
  smallest stable surface, do not design a comprehensive fixed schema).

## 3. Exact base SHAs (binding)

- **FALCON canonical base:** `5edbd3eccff0b20a343b693522073ed0b2e7a9ac` (`maff0000/falcon`, `main`).
- **HELIOS canonical base, established by this WO's own discovery:**
  `7f7193d55475e40583892b94dd461b1b64d6f1ef` (`maff0000/HELIOS`, `main`) — independently verified twice (see
  the discovery document §1) as the authoritative source actually running live, excluding `trading-helios`
  and all legacy `tradingProteus/helios*` paths.
- **Deployment/orchestration repository referenced (read-only, not a build target of this WO):**
  `maff0000/GOLD-STRATEGY-RUNTIME`, local HEAD `58914154da0864b0c9e9632b1379224430f9b10f`.

## 4. Scope

Read-only discovery and documentation only:

1. Establish authoritative HELIOS repository/runtime identity, excluding legacy/stale candidates.
2. Inspect HELIOS source, tests, documentation, configuration, Docker/Compose, and safely-observable live
   runtime state (logs, `docker inspect`, read-only `docker exec` of non-secret files) — never mutating
   anything.
3. Document real architecture/topology, strategy model, evidence/reasoning model, HERMES dependency model,
   identity model, UTC handling, configuration handling, failure semantics, and security/signing state.
4. Reconcile FALCON's existing PID-01 registry entries, schemas, and prose contract documentation
   (`docs/contracts/HELIOS-FALCON-CONTRACT.md`, PID-07, PID-08) against the real HELIOS implementation,
   producing an explicit A–F classification table.
5. Confirm or correct the PID-07/PID-08 conceptual boundary against real evidence.
6. Propose a minimum candidate PID-07 publication contract and a producer-owned-payload boundary —
   proposals only, not registered.
7. Record all gaps/blockers requiring a future architecture decision before implementation.
8. Produce a durable R2D2 independent blueprint record.

## 5. Exclusions (binding)

This WO does not authorise, and no mandate derived from it may perform: any HELIOS code change; any FALCON
application/registry/schema change; any Graylog/runtime mutation; any container restart, config change, or
data mutation; certificate or signing-key creation; package installation; publisher/validator implementation;
Redis/SQL changes; trade-suggestion design; PID-08 work of any kind; remediation of the live
fixture-replay/non-live-data finding (§14 of the discovery document, HELM/Architect's to action separately);
remediation of any unrelated ARES/FALCON backlog; `tar-risk-engine` investigation.

## 6. Evidence requirements

Two independent read-only discovery passes (a primary discovery pass and a separate R2D2 independent-auditor
pass, run without cross-coordination), converging or explicitly flagging disagreement on every material
finding; direct verification by the Delivery Controller of FALCON's actual machine-readable
registry/schema files (not prose documentation alone) before any contract-mismatch claim is finalised; exact
repository/commit evidence for HELIOS authority; file:line citations for every UTC/configuration/security
finding; a Memory Fabric blueprint record from R2D2.

## 7. Tests/documentation checks

Standard FALCON documentation gate: offline unit test suite, `tests.validator.cli`, `DOCUMENTATION-MANIFEST.json`
cross-check, internal Markdown link check, gitleaks — all must pass clean on the resulting documentation
candidate. No application test suite is run or required (no application code is touched).

## 8. Acceptance criteria

Central Architecture can answer, from the discovery document alone: what HELIOS actually is today; which
repository/runtime is authoritative; what HELIOS actually evaluates and publishes; what evidence it currently
produces and how durable it is; which current FALCON registry/schema/doc assumptions are wrong (and why);
what belongs to PID-07 versus PID-08; what minimum contract could survive HELIOS's continued evolution; what
must be resolved (in HELIOS, in FALCON's registries, or architecturally) before PID-07 implementation begins;
and whether FALCON publication can remain non-blocking relative to HELIOS's evaluation loop if added later.
Every item this WO's discovery could not answer with evidence is marked UNRESOLVED in the discovery document,
not guessed at.

## 9. Disposition

**Discovery complete.** Full findings: `docs/architecture/PID07-HELIOS-STAGE1-DISCOVERY.md`. PID-07 itself is
reconciled alongside this WO (see `pids/PID-07-HELIOS-OBSERVABILITY.md`'s new Status/Stage 1 sections) to
record that Stage 1 is closed and that implementation remains **not started**, pending a future
contract-reconciliation stage (PID-07 Stage 2) and a separate architecture decision on the blocking-publisher
and live-fixture-replay findings. No implementation is authorised by this WO or its output.
