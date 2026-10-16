# UNVERIFIED table

Anything this audit could not establish from source or GitHub. Each row has the reason and what would close it. No credential was requested, read or used; no running service was contacted (`AUDIT-LOG.md`).

| # | Item | Why unverified | Closes with |
|---|---|---|---|
| U1 | Whether the FALCON ingestion stack is running and healthy; container names, status, restart policy, health, labels; systemd finding | Lane limit: no inspection of any running service. The PID's own statement of a running stack is an agent assertion here. | Operations-owner read-only export (D-4) |
| U2 | Live input, stream and pipeline configuration equals the content pack at `8f218ec` | Needs the authenticated Graylog API | D-4 export |
| U3 | Message counts, index sizes, per-stream volumes, ingestion lag | Same | D-4 export |
| U4 | Whether HERMES is publishing in steady state, and which HERMES families | Same; PID06 evidence s7 shows HERMES events existed on 2026-10-04 without naming the family | D-4 export |
| U5 | Whether the `payload_trigger_id` field is indexed as an exact-match keyword | Needs the live index mapping | D-4 export or an isolated test pipeline |
| U6 | Whether the committed identity-suite results (2026-09-29) still hold on the running system | Committed report only | rerun of the suite by the operations owner |
| U7 | Code of the HERMES and ARES non-blocking publishers | Producer repositories not read | a follow-on read, or P-H1/P-T1 reuse review |
| U8 | HELIOS deployment configuration (sink, tick interval, fixture replay) | Deployment repositories and running containers not read; PID07 is the secondary source | HELIOS-T2 evidence, or a read of the deployment repository |
| U9 | TRON runtime behaviour; any TRON code outside the branches read | None exists in the sources read; other branches and private repositories were not searched | TRON-T1/T4 delivery |
| U10 | Legacy Falcon Ranger and older Graylog stack (EP-2; `DISPOSITION.md` row 15) | Not described by any file read; no inspection allowed | out-of-lane read |
| U11 | The isolated-FALCON outage rehearsal (EP-9 R-5) | Needs an isolated DEV/test FALCON and a real component under test; not run (lane limit, and none exists yet) | follow-on work (P-H1, P-T1, `GOLD-MVP-001`) |
| U12 | Real event sizes, HERMES cadence, TRON trade count, burst profile (EP-7) | No measurements possible | D-4 export and follow-on items |
| U13 | `GOAL-TRIGGER-001` content after approval | The candidate is not approved and not on GOAL `main`; EP-8 must be re-read if it changes | CA approval and freeze |

## Private file

Out-of-scope observations about pre-existing content are held in a private handback and not reproduced here.
