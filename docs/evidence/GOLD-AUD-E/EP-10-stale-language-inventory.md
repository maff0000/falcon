# EP-10: Stale-language inventory

Audited SHA: falcon `8f218ec1b85b932285b042a7b1ae64dbd11eebee`. **Nothing is edited.** Each row is a ruling-ready candidate. The 22 rows `S01` to `S22` are the rows the PID listed (Current state 9); `X01` to `X09` were found by this audit. All 31 rows (22 distinct files) are re-verified mechanically: `python3 docs/evidence/GOLD-AUD-E/verify_stale_lines.py` checks, for each, that the file exists, the line range exists and the quoted needle matches inside that range, and exits non-zero otherwise.

PID line-number check: 21 of the 22 PID rows matched exactly. One was off by one: the stream-design label is on lines **13 to 14** of `docs/graylog/FALCON-STREAM-INDEX-DESIGN.md`, not 14 to 15 (the PID text, row S19).

## Why these rows are stale

The target architecture (CA guidance 2026-10-15, items 2 and 3, as carried in the PID): the transport of a trigger is not Graylog or FALCON; FALCON is an asynchronous evidence consumer; its outage does not block execution. These rows still describe FALCON as the place TRON discovers triggers, or make FALCON's availability a gate on new entries.

## Verdict key

SUPERSEDE: the statement is wrong for the target architecture. RELABEL: the object stays, the wording or metric name changes. RETIRE-CANDIDATE: the object belongs to the dropped discovery model; retirement is decision D-8 and is not authorised here. KEEP-NOTE: still valid as evidence-only language; add a pointer to the supersession.

## Amendment route (all rows)

Delivered, closed documents are not edited in place. Route, using falcon's own precedents: (1) a new numbered Decision appended to `docs/governance/FALCON-DECISION-REGISTER.md` (the register is append-only: Decisions 21 to 32 were added this way; the next free number) superseding the Decision 16 coupling and recording the evidence-only rule; (2) an amendment document under `pids/amendments/` (precedent: `AMD-PID06-001`, `AMD-PID06-002`) that carries the row-by-row text changes for the contract, architecture, PID and governance documents; (3) registry, schema, fixture and content-pack rows go through PID-01 change control and a content-pack revision (a privileged live operation, EP-6 G4), so they are batched with FALCON-T1/T3; (4) `DOCUMENTATION-MANIFEST.json` and the link check updated in the same change. This is work item P-F1 in `MINIMUM-WORK-LIST.md`; docs-only parts may run first.

## Inventory

| ID | File | Lines | What it says | Verdict | Note |
|---|---|---|---|---|---|
| S01 | `docs/contracts/FALCON-TRON-TRIGGER-DISCOVERY.md` | 1 to 33 (whole file) | FALCON to TRON Trade Suggestion discovery contract: query scope, overlap windows, filters, health | SUPERSEDE | whole document |
| S02 | `docs/contracts/TRON-FALCON-CONTRACT.md` | 3 to 30 | inbound discovery steps, polling cadence, "FALCON unavailable ... no new entries" | SUPERSEDE | lines 31 on (outbound evidence, idempotency, instance identity) stay |
| S03 | `docs/governance/FALCON-DECISION-REGISTER.md` | 23 to 24 | Decision 16: FALCON outage or lag blocks new entries when FALCON is the discovery dependency | SUPERSEDE | by a later Decision; do not edit history |
| S04 | `docs/architecture/01-FALCON-ARCHITECTURE.md` | 45 | diagram label "TRON Trade Suggestion discovery + admission" | RELABEL | |
| S05 | `docs/architecture/01-FALCON-ARCHITECTURE.md` | 169 to 170 | "no new TRON entry may be created from a Trade Suggestion that cannot be validly discovered" | SUPERSEDE | failure behaviour |
| S06 | `README.md` | 63 | same diagram label | RELABEL | |
| S07 | `pids/PID-05-HERMES-INTEGRATION.md` | 99 | "TRON discovers relevant HELIOS suggestions from FALCON" | SUPERSEDE | delivered PID: add a supersession note, keep text |
| S08 | `pids/PID-08-HELIOS-SIGNED-TRIGGERS.md` | 12 | purpose: evidence "suitable for TRON discovery" | SUPERSEDE | undelivered PID: rewrite before use |
| S09 | `pids/PID-08-HELIOS-SIGNED-TRIGGERS.md` | 68 | Definition of Done: searchable and verifiable by a consumer | SUPERSEDE | |
| S10 | `pids/PID-09-TRON-PAPER-INTEGRATION.md` | 1 | title "Discovery, Admission and Execution Evidence" | SUPERSEDE | |
| S11 | `pids/PID-09-TRON-PAPER-INTEGRATION.md` | 11 | goal: TRON discovers Trade Suggestions | SUPERSEDE | |
| S12 | `pids/PID-09-TRON-PAPER-INTEGRATION.md` | 32 | scope: overlap polling | SUPERSEDE | |
| S13 | `pids/PID-09-TRON-PAPER-INTEGRATION.md` | 34 | scope: ingestion-lag gate | SUPERSEDE | |
| S14 | `pids/PID-09-TRON-PAPER-INTEGRATION.md` | 62 | acceptance: FALCON unavailable or lag means no new entry | SUPERSEDE | contradicts R-10 |
| S15 | `docs/operations/FALCON-OBSERVABILITY.md` | 14 | metric "TRON trigger-discovery latency" | RELABEL | replace with publisher spool depth and drop counters (R-2) |
| S16 | `docs/engineering/FALCON-CAPACITY-MODEL.md` | 22 | measure "TRON discovery latency" | RELABEL | |
| S17 | `pids/PID-13-OBSERVABILITY-CAPACITY.md` | 24 | same | RELABEL | |
| S18 | `docs/engineering/FALCON-PROD-PROMOTION-GATES.md` | 8 | gate 4 "paper TRON trigger discovery/execution green" | SUPERSEDE | gate wording |
| S19 | `docs/graylog/FALCON-STREAM-INDEX-DESIGN.md` | 13 to 14 | stream "HELIOS Trade Suggestions" | KEEP-NOTE | stream name is in the content pack; renaming is a content-pack revision; keep the stream as the home of trigger evidence and amend the description. (PID cited 14 to 15.) |
| S20 | `registry/system_component_registry.v1.json` | 35 | component `tron.discovery_service` | RETIRE-CANDIDATE | D-8; registry change control |
| S21 | `registry/field_registry.v1.json` | 1960 | `valid_from_utc` described "for TRON discovery" | RELABEL | description only |
| S22 | `registry/field_registry.v1.json` | 1979 | `valid_until_utc` same | RELABEL | |
| X01 | `docs/architecture/00-FALCON-PID.md` | 81 | MVP definition: signed Trade Suggestions "can be discovered by paper TRON through FALCON" | SUPERSEDE | audit-found |
| X02 | `docs/governance/FALCON-R2D2-BLUEPRINT.md` | 10 | blueprint must record "TRON trigger discovery" | RELABEL | audit-found |
| X03 | `docs/governance/FALCON-TEST-AND-ACCEPTANCE-PLAN.md` | 15 | test list "TRON discovery/dedupe tests" | RELABEL | audit-found; replace with the R-1 to R-10 tests |
| X04 | `docs/contracts/HELIOS-FALCON-CONTRACT.md` | 29 | Trade Suggestion carries "semantic SL/TP/invalidation/target" | SUPERSEDE | audit-found; not transport language but conflicts with the candidate trigger contract (T-2) and HELIOS's execution blindness |
| X05 | `tests/fixtures/valid/tron_trigger_observed.json` | 6 | producer component `tron.discovery_service` | RETIRE-CANDIDATE | audit-found; tied to D-8 |
| X06 | `tests/fixtures/valid/tron_admission_decision.json` | 6 | same | RETIRE-CANDIDATE | audit-found |
| X07 | `deploy/content-packs/falcon-pid03-ingestion-v1.json` | 1466 | input title names `tron.discovery_service` | RETIRE-CANDIDATE | audit-found; content-pack revision; the two identity-check rules for this input (lines 1122 to 1158) also name it |
| X08 | `docs/governance/FALCON-DECISION-REGISTER.md` | 56 to 58 | Decision 25: Trade Suggestions framed as structured, optionally signed evidence | KEEP-NOTE | audit-found; the evidence framing survives; Decision 26 (lines 63 to 68) implies discovery and needs the same pointer |
| X09 | `pids/PID-05-HERMES-INTEGRATION.md` | 15 to 18 | status "Implementation ... is NOT yet authorised" while Stages 1 and 3A are implemented | SUPERSEDE | audit-found; a stale status, not transport language; add a status note |

## Composition of the 31 rows, and what is not inventoried

The 31 rows are not all the same kind. X04 (execution vocabulary against the candidate trigger contract) and X09 (stale PID-05 status) are not transport language. S20, X05, X06 and X07 are component-retirement candidates (D-8). S19 and X08 are KEEP-NOTE. The remainder (SUPERSEDE or RELABEL) is the transport and gating language proper.

Remnants of `tron.discovery_service` and discovery language **not inventoried** as rows (listed so a later pass can add them): `docs/operations/FALCON-PID04-PRIVILEGED-OPERATIONS-RUNBOOK.md` (lines 219, 274), `docs/governance/FALCON-DECISION-REGISTER.md` Decision 26 (lines 63 to 68), `docs/architecture/04-PRODUCER-CONTRACT-EVOLUTION-DOCTRINE.md` (line 77), further remnants in `deploy/README.md` and `pids/PID-05-HERMES-INTEGRATION.md` (to be located by the later pass), and the rule titles in the content pack other than X07.

## Not changed, listed for completeness

`docs/security/FALCON-HELIOS-TRIGGER-SIGNING.md` (lines 3 to 8, 28 to 36) correctly says a search hit is not an executable instruction and that TRON verifies independently; its verification list assumes a consumer reading from FALCON. KEEP-NOTE with the others; no row is added because no line states the transport.
