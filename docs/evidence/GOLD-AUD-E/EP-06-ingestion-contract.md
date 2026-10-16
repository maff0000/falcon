# EP-6: Ingestion contract

Audited SHA: falcon `8f218ec1b85b932285b042a7b1ae64dbd11eebee`. All statements are about the committed definition of the ingestion path. Whether the running system matches is UNVERIFIED (EP-2). No endpoint, address, port or credential location is reproduced here.

## 1. Mechanism (what the repository defines)

| Element | Definition | Evidence | Label |
|---|---|---|---|
| Transport | Producers construct their own FalconEvents and deliver them over an authenticated Graylog-native transport; no bespoke FALCON ingress service, ledger or application-level acknowledgement exists | `docs/governance/FALCON-DECISION-REGISTER.md` Decisions 21, 22, 23 (lines 33 to 50) | PROVEN |
| Identity binding | One dedicated mutual-TLS input per producer identity (5), each with its own trust material; two pipeline rules per input compare the claimed `producer_system_id` and `producer_component_id` with the identity authorised for that input, using `from_input(name: ...)` | `deploy/content-packs/falcon-pid03-ingestion-v1.json` (rules `FALCON - identity check: ...`); `docs/security/FALCON-PRODUCER-AUTHENTICATION.md`; `docs/operations/FALCON-PID04-PRIVILEGED-OPERATIONS-RUNBOOK.md` s6 | PROVEN |
| Spoof handling | A mismatch sets `falcon_identity_mismatch` and a reason, routes to the quarantine stream only, and keeps the claimed (false) value in the indexed fields so the forgery is visible | runbook s6; `tests/fte/last_run_report_pid04.json` | PROVEN |
| Validity routing | Each family has a "route valid" rule excluding every `falcon_*` flag; invalid messages go to quarantine. TRON `*.health` is split to the operational-health stream | content pack rules `FALCON - route valid ...` | PROVEN |
| Required-field enforcement | Envelope fields and per-family payload fields are enforced by rules; the payload JSON is flattened into `payload_*` fields | rules `flag missing required fields`, `flag missing required payload fields`, `Parse payload JSON` | PROVEN |
| Component allow-list | Hard-coded list of 15 component names in `FALCON - flag unknown component`; any other value is flagged `falcon_unknown_component` and not routed as valid | same file | PROVEN |

## 2. The five identities and the test results on record

Identities (input titles in the content pack): HERMES; ARES; HELIOS; TRON `tron.execution_engine`; TRON `tron.discovery_service`.

| Test class | Result | Source |
|---|---|---|
| Valid message through its own dedicated input | 4 of 4 PASS (HERMES, ARES, HELIOS, TRON execution engine) | `tests/fte/last_run_report_pid04.json`, key `valid_via_dedicated_input`, generated 2026-09-29 |
| Identity spoof (input claims another identity) | 4 of 4 PASS | same file, key `identity_spoof` |
| Correct-identity control | 2 of 2 PASS (both TRON identities) | same file, key `correct_identity_control` |
| Connection level: plaintext, no client certificate, untrusted client certificate | 3 cases, status `NEEDS_ROGUE_SERVER_LOG_CONFIRMATION` by design; the runbook records the confirmed exception classes from the delivery team's runs | same file, key `connection_level`; runbook s6 |
| Certificate revocation, restart recovery, delete-and-reinstall reconstruction | procedures and expected results in runbook s7, s8, s11 | runbook |

Label: PROVEN as committed records of 2026-09-29; the HELIOS identity has a proven positive and spoof result but no producer exists to use it; the HERMES-input claiming `helios` spoof case is included in the 4 of 4. Current runtime: UNVERIFIED.

## 3. Gaps against what the target architecture needs

| # | Gap | Evidence | Label | Owner |
|---|---|---|---|---|
| G1 | Binding is to a **fixed component name**, not to a TRON instance. `docs/contracts/TRON-FALCON-CONTRACT.md` lines 105 to 111 say binding the connection to the governed instance identity "is PID-04's responsibility and is not implemented here"; the rule compares to the literal `tron.execution_engine`. A per-instance `producer_component_id` (the doctrine's example is a per-trader name) would be flagged unknown. | contract lines 54 to 111; content pack | PROVEN | T3 + FALCON (P-T2) |
| G2 | The second TRON identity is built for a discovery model that the target architecture drops (EP-10, D-8). | registry; content pack | PROVEN | T3 / PO |
| G3 | Delivery is best-effort with no acknowledgement and no durable buffer in FALCON. A recreated container lost 27 events in about 19.7 s on 2026-10-04, recorded as accepted debt. Producers therefore own durability (EP-9). | `docs/operations/FALCON-PID06-RUNTIME-ACCEPTANCE-EVIDENCE.md` s7, s12 | PROVEN (record) | publishers |
| G4 | Changing a family or component means a new content-pack revision and a privileged live reinstall: delete the diverging rule and the pipeline entity, install, reconnect, remove blind-duplicated streams and inputs. One measured instance had a pipeline-absent window of about 289 ms and no evidence loss. | PID06 evidence s1; runbook s14 | PROVEN (record) | FALCON ops |
| G5 | HELIOS as a producer: the only HELIOS input and component names registered are `helios.evaluation_engine` and `helios.trigger_signer`. The trigger component is registered as the signer; under D-10 (publisher home) the emitting component may differ. | registry; `GOAL-TRIGGER-001` D-10 | PROVEN | PO (D-6) |

## 4. Authorisation path for further producer inputs (documented, not executed)

1. The one authentication pattern is mTLS on a dedicated Graylog input, no per-producer invention, proven against the pinned stack, and independently audited before onboarding (`docs/security/FALCON-PRODUCER-AUTHENTICATION.md`, "Selection gate").
2. Register the component(s) through PID-01 change control (`registry/system_component_registry.v1.json`; for a new family also the family and field registries, a schema, and a valid and an invalid fixture).
3. Add the input, its trust material reference and the two identity rules to a new content-pack revision.
4. Install with the privileged reconciliation procedure (runbook s14), then re-run the identity suite (runbook s6).
5. Provision the producer's client identity by the operations owner. Key custody is not defined for GOAL runtimes at this commit (the candidate trigger contract cites an open operations safety item); this audit does not describe or touch it.
6. Fresh independent audit of the result.

Each step is a separate authorised work order (P-F2 in the work list). This audit authorises none of them.

## 5. Findings feeding the work list

- P-F2 (further producer work) is not "later and trivial": for TRON it is on the critical path of P-T2, because of G1 and G4.
- Registry reshaping for HELIOS (T1) and TRON (T3) should be batched into as few content-pack revisions as possible, because each revision is a privileged live operation (G4). Sequencing note in `MINIMUM-WORK-LIST.md`.
