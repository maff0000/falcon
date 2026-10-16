# EP-3: Registry matrix (28 families)

Audited SHA: falcon `8f218ec1b85b932285b042a7b1ae64dbd11eebee`.

**The matrix is generated, not typed.** `regenerate_ep3.py` reads `registry/event_family_registry.v1.json`, the payload schemas, `tests/fixtures/valid/*.json` and the live-pipeline rule `FALCON - flag missing required payload fields` in `deploy/content-packs/falcon-pid03-ingestion-v1.json`, and prints the table committed as [`EP-03-registry-matrix.table.md`](EP-03-registry-matrix.table.md). `python3 docs/evidence/GOLD-AUD-E/regenerate_ep3.py --check` exits 0 only if the regenerated table equals the committed one (row count asserted by the table itself: 28). Only the `emitting` and `owner` columns are hand-assigned; they are constants at the top of the script, each with its source.

## Reading the columns

| Column | Meaning |
|---|---|
| required payload fields (registry / schema) | count in the family registry versus the payload schema `required` list; `(MISMATCH)` if different |
| valid fixture (retention_class in fixture) | a file under `tests/fixtures/valid` whose `evidence_family` equals the family |
| pipeline enforces required payload fields | the family appears in the content-pack rule that flags a message missing a required payload field |
| emitting | whether any producer emits the family. `YES (point-in-time)` is a recorded runtime acceptance, not a current observation |
| owner | `T1` FALCON-T1 (HERMES/ARES/HELIOS reconciliation), `T3` FALCON-T3 (trigger and `tron.*` freeze), or `no gap raised by E` |

## Findings from the generated table

| # | Finding | Label | Owner |
|---|---|---|---|
| 1 | All 28 families have a registered schema file, a valid fixture, and registry and schema agree on the required payload field count. | PROVEN | none |
| 2 | All 28 families are enforced by the live pipeline's required-payload-field rule as defined in the content pack. (This closes the gap recorded in `pids/PID-05-HERMES-INTEGRATION.md` line 2481, closed by Stage 3A at line 2618.) Whether the live pipeline equals the content pack is UNVERIFIED (EP-2). | PROVEN (definition) | none |
| 3 | "Live" means schema registered, not producer emitting. One family has a recorded runtime acceptance (`ares.market_status.session_state`). The other four HERMES families and `hermes.signal_state` are UNVERIFIED as to steady state. The five other ARES families, all five HELIOS families and all twelve TRON families have no emitting producer evidenced. | PROVEN (absence in source); steady state UNVERIFIED | T1 / T3 / new |
| 4 | Every valid fixture carries `retention_class: standard`; the field registry has 141 fields, all `standard`. The four named retention classes of `docs/graylog/FALCON-STREAM-INDEX-DESIGN.md` are not values of the envelope `retention_class` enum (`standard`, `extended`, `short`). | PROVEN | PID-10 (retention), noted in EP-7 |
| 5 | The pipeline contains a hard-coded allow-list of 15 component names (`FALCON - flag unknown component`) and per-input identity rules. A registry change that adds a component or reshapes a family is also a content-pack revision and a privileged live reinstall (`docs/operations/FALCON-PID04-PRIVILEGED-OPERATIONS-RUNBOOK.md` s14). | PROVEN | T1 / T3 sequencing (EP-6) |
| 6 | Five names are reserved, not live (`ares.regime.nowcast`, `ares.unscheduled_news`, `ares.model_market_assessment`, `ares.mandatory_restriction_veto`, `ares.calibrated_risk_score`). Not in scope. | PROVEN | none |
| 7 | The registry names `tron.discovery_service` as a TRON component, and the valid fixtures `tron_trigger_observed.json` and `tron_admission_decision.json` use it as the producer. Under the target architecture there is no discovery service (EP-10, D-8). | PROVEN | T3 |

## Mismatches that the matrix cannot show (see EP-4, EP-5, EP-8)

Schema agreement is internal. Agreement with the real producers is a separate question: HELIOS (EP-4), TRON (EP-5) and the candidate trigger contract (EP-8) disagree with the registered shapes in the ways listed there.
