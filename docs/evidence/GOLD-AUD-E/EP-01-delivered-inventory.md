# EP-1: Delivered inventory

Audited SHA: falcon `8f218ec1b85b932285b042a7b1ae64dbd11eebee`. Source of PR numbers and merge SHAs: GitHub read API (`gh api repos/maff0000/falcon/pulls`), re-read for this audit.

## PIDs, merged PRs and state

| PID | Topic | Merged PR(s) (merge SHA, abbreviated) | State at audited SHA | Label |
|---|---|---|---|---|
| PID-00 | repository foundation | #1 (`d149731`) | delivered; `pids/PID-00-REPOSITORY-FOUNDATION.md`, CI at `.github/workflows/ci.yml` | PROVEN |
| PID-01 | contract and registry foundation | #2 (`00d8df4`) | delivered: `registry/` (3 registries), `schemas/`, `tests/fixtures/{valid,invalid}`, `tests/validator/` | PROVEN |
| PID-02 | immutable Graylog DEV stack | #3 (`41be9eb`) | delivered as `deploy/` stack definition | PARTIAL (runtime not inspected, EP-2) |
| PID-03 | ingestion templates | #5 (`30e24d3`) | delivered: content pack `deploy/content-packs/falcon-pid03-ingestion-v1.json` | PROVEN (file); runtime UNVERIFIED |
| PID-04 | producer connection security (mTLS) | #6 (`3aeec47`) | delivered; suite report `tests/fte/last_run_report_pid04.json` | PROVEN (committed report); live state UNVERIFIED |
| PID-05 | HERMES publication | #7 to #11 (`f35b76a`, `5728734`, `b2f27de`, `335f2ae`, `5d89668`) | delivered through Stage 3A; header still reads "implementation NOT yet authorised" | PROVEN (stale status header, below) |
| PID-06 | ARES `market_status` and runtime acceptance | #12 to #18 (`d4644f5` ... `a0ca36a`) | delivered; runtime acceptance record `docs/operations/FALCON-PID06-RUNTIME-ACCEPTANCE-EVIDENCE.md` | PROVEN (as a record); not re-observed |
| (doctrine) | producer contract evolution | #19 (`5edbd3e`) | `docs/architecture/04-PRODUCER-CONTRACT-EVOLUTION-DOCTRINE.md` | PROVEN |
| PID-07 Stage 1 | HELIOS read-only discovery | #20 (`8f218ec`) | discovery document only: `docs/architecture/PID07-HELIOS-STAGE1-DISCOVERY.md`; no implementation | PROVEN |
| PID-07 impl, 08, 10 to 15 | HELIOS publication, signed triggers, TRON integration, streams and retention, GUI, backup, observability, prod engineering, MVP closure | none | design text only in `pids/` | PROVEN (absence of deliveries) |

## Reusable assets (CA item 7)

| Asset | Path | Note |
|---|---|---|
| Event family registry (28 live, 5 reserved names) | `registry/event_family_registry.v1.json` | reproduced in EP-3 |
| Field registry (141 fields) | `registry/field_registry.v1.json` | every field has `retention_class: standard` (EP-7) |
| System and component registry | `registry/system_component_registry.v1.json` | components are a closed list (EP-6) |
| Envelope schema and 28 payload schemas | `schemas/falcon-event-envelope/v1/`, `schemas/payloads/*` | one schema file per family |
| Fixtures | `tests/fixtures/valid` (30 files), `tests/fixtures/invalid` (18 files: 17 fixtures and `MANIFEST.json`) | each of the 28 families has a valid fixture (EP-3) |
| Stdlib validator | `tests/validator/` | CI runs it with `python3 -m unittest discover -s tests -p "test_*.py"` |
| Non-blocking publisher pattern (HERMES, ARES) | described in `docs/operations/FALCON-PID06-RUNTIME-ACCEPTANCE-EVIDENCE.md` s5; implementation lives in the producer repositories, not here | publisher code NOT read by this audit (UNVERIFIED as code; PROVEN only as a recorded result) |

## Stale status header

`pids/PID-05-HERMES-INTEGRATION.md` lines 13 to 18 state "Implementation of the actual HERMES to FALCON integration is NOT yet authorised", while the same file records implemented Stage 1 (from line 2114) and Stage 3A (from line 2618) with live verification. The header is stale. Amendment route: EP-10.

## What CI covers

`.github/workflows/ci.yml`: structure check, manifest cross-check, internal Markdown link check, gitleaks, then the validator suite and a fixture report (jobs `repository-foundation` and `contract-registry-foundation`). It does not run the `tests/fte/` suites (they need a live Graylog) and does not validate that `DISPOSITION`-style or evidence documents are well-formed. PROVEN by reading the workflow.
