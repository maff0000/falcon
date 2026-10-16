# GOLD-AUD-E: FALCON evidence audit and minimum HELIOS/TRON publication set

**Work order:** `GOLD-AUD-E` (GOLD MVP Lane E). **Branch:** `wo/GOLD-AUD-E-evidence`. **Nature:** read-only research audit. Docs only.
**Status of this evidence:** DRAFT for independent audit. The independent audit verdict is **pending independent audit by ROGUE** (see `VERDICT.md`). Nothing here is an approval, a contract freeze or a retirement.

## Audited scope (quoted from the approved PID, `pids/GOLD-AUD-E.md` in `maff0000/GOAL`)

> Execute CA directive for Lane E: review the delivered FALCON/Graylog event registry and verified running ingestion; define the minimum remaining HELIOS and TRON event-publication work; keep FALCON outside the executable trigger-delivery path. The output is evidence and a bounded work list, not an implementation.

## Source revisions audited (full SHAs)

| Source | Revision | Used for |
|---|---|---|
| `maff0000/falcon` `main` (audit base) | `8f218ec1b85b932285b042a7b1ae64dbd11eebee` | registry, schemas, fixtures, content pack, CI, documents (all falcon paths below are at this SHA) |
| `maff0000/HELIOS` `main` | `7f7193d55475e40583892b94dd461b1b64d6f1ef` | publication surface, failure semantics (source read) |
| `maff0000/tron` `main` | `5577039b5db05e70effef72c7e59df14db408419` | design record (`PID.md`) |
| `maff0000/tron` branch `wo/WO-TRON-D1` | `37d5f009a080d25930eea37cf8c627bb0f3a1ff4` | design documents and event catalogue |
| `maff0000/GOAL` `main` | `ceaf0291a43d029b1a47b1c192a62ff147f05ac0` | the PID, portfolio and decision register |
| `maff0000/GOAL` branch `wo/GOAL-CONTRACT-TRIGGER` | `64c843b901d435a17efa56e3b2a1f925ad58c30b` | `GOAL-TRIGGER-001` candidate (not approved; not on `main`) |

falcon `main` was re-checked against GitHub at the start of this audit and had not moved from `8f218ec`.

## Labels

Every finding carries one of: **PROVEN** (read in source at the cited path, SHA and line, or reproduced by the script in this directory), **PARTIAL**, **UNVERIFIED** (could not be established from source or GitHub; reason given), **MISSING** (looked for, not found). Nothing is taken from an agent assertion or from Fabric as fact.

## Map: PID evidence parts, CA evidence numbering, files

| Part | File | CA item(s) |
|---|---|---|
| EP-1 delivered inventory | `EP-01-delivered-inventory.md` | 1, 2, 3 |
| EP-2 running ingestion record | `EP-02-running-ingestion-record.md` | 3, 9 |
| EP-3 registry matrix (28 rows) | `EP-03-registry-matrix.md`, `EP-03-registry-matrix.table.md`, `regenerate_ep3.py` | 2, 3, 6 |
| EP-4 HELIOS needs | `EP-04-helios-needs.md` | 3, 4, 6 |
| EP-5 TRON needs | `EP-05-tron-needs.md` | 3, 4, 6 |
| EP-6 ingestion contract | `EP-06-ingestion-contract.md` | 4, 9 |
| EP-7 volume and retention | `EP-07-volume-and-retention.md` | 9 |
| EP-8 trigger-id hook | `EP-08-trigger-id-hook.md` | 4, 6 |
| EP-9 outside-the-path requirements | `EP-09-outside-the-path.md`, `ep09_reference_model.py` | 5, 7 |
| EP-10 stale-language inventory | `EP-10-stale-language-inventory.md`, `verify_stale_lines.py` | 2, 6 |
| Minimum publication work list | `MINIMUM-WORK-LIST.md` | 8 |
| Disposition table | `DISPOSITION.md` | 7, 8 |
| UNVERIFIED table | `UNVERIFIED.md` | 3 |
| Audit log of commands | `AUDIT-LOG.md` | 5, 9 |
| Independent verdict (pending) | `VERDICT.md` | 10 |

CA's ten items, in CA numbering: (1) PID/WO identifier and exact scope: this file and EP-1. (2) Sources, revisions, references: this file, EP-1, EP-3, EP-10. (3) Existing implementation proven / partial / unverified / missing: EP-1 to EP-5, `UNVERIFIED.md`. (4) Actual versus expected contract: EP-4, EP-5, EP-6, EP-8. (5) Tests, fixtures, evidence references: EP-9, scripts, `AUDIT-LOG.md`. (6) Defects and compatibility gaps: EP-3, EP-4, EP-5, EP-8, EP-10. (7) Reusable code and documentation: EP-1, EP-9, `DISPOSITION.md`. (8) Minimum recommended changes: `MINIMUM-WORK-LIST.md`. (9) Safety and deployment constraints: EP-2, EP-6, EP-7, `AUDIT-LOG.md`. (10) Independent verdict: `VERDICT.md` (pending).

## Reproduce

From the repository root, stdlib Python only, no network, no service access:

```
python3 docs/evidence/GOLD-AUD-E/regenerate_ep3.py --check      # EP-3: regenerated table equals committed table, 28 rows
python3 docs/evidence/GOLD-AUD-E/verify_stale_lines.py          # EP-10: every file/line/needle re-verified
python3 docs/evidence/GOLD-AUD-E/ep09_reference_model.py        # EP-9: reference-model tests
```

## Headline findings

1. **FALCON publication from HELIOS and TRON does not exist.** HELIOS has no FALCON publication code and its publish path is synchronous and fatal on sink failure. TRON has no publisher code in the repositories read, and its design emits a different event model. (PROVEN, EP-4, EP-5.)
2. **Registry debt is larger than the PID listed.** The live ingestion pipeline hard-codes component names and per-family required payload fields, so any registry reshape is also a content-pack change (EP-3, EP-6). A per-instance TRON identity is not admitted by the pipeline as written (EP-6).
3. **Only 5 of the 23 `GOAL-TRIGGER-001` candidate signed fields carry over unchanged to the registered trigger family**: 9 conflict (4 are schema-compatible narrowing, 5 incompatible or unsupplied), 7 are missing, 2 need renaming (EP-8). `evaluation_id` appears in the candidate's signed fields but HELIOS source contains no `evaluation_id` at all (EP-4, EP-8).
4. **The stale "FALCON as trigger transport" language is 31 rows in 22 files** (EP-10): the 22 rows the PID listed (one line reference corrected) and 9 found by the audit.
5. **No row of the minimum work list makes FALCON a precondition of any HELIOS or TRON decision** (`MINIMUM-WORK-LIST.md`). The outside-the-path requirements are mechanically testable (EP-9). The FALCON-outage rehearsal itself is NOT run here: it needs an isolated DEV/test FALCON and is specified for the follow-on work.
6. **Running ingestion was not inspected by this audit** (lane limits). It is UNVERIFIED here; see EP-2 and `UNVERIFIED.md`.
7. Out-of-scope observations about pre-existing content are held privately; not listed here.
