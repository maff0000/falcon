# EP-2: Running ingestion record

## Position of this audit

The PID allows read-only container-state reads (state, restart policy, health, labels; unit listing). The dispatch for this lane is stricter: **do not run, modify, stop or connect to any Graylog, FALCON or other running service; inspection of a running system is recorded UNVERIFIED.** This audit therefore ran **no runtime command of any kind** against any host service (`AUDIT-LOG.md` lists every command; all are git, GitHub-read or local file operations).

Consequence: this audit does **not** independently verify that the FALCON ingestion stack is running. Statements about running state elsewhere (for example in the PID text, written 2026-10-15 from a separate read) are an agent assertion for the purposes of this audit and are not carried forward as PROVEN.

## What source and committed evidence do establish

| Claim | Evidence (path, SHA `8f218ec`) | Label |
|---|---|---|
| A single content pack defines the ingestion configuration: 5 inputs, 7 streams, 1 pipeline, 30 rules, 1 stream-title entity (44 entities) | `deploy/content-packs/falcon-pid03-ingestion-v1.json`; entity counts regenerated for this audit by parsing the file | PROVEN (definition); live match UNVERIFIED |
| The five inputs are one per producer identity: HERMES, ARES, HELIOS, TRON execution engine, TRON discovery service | same file, input entities | PROVEN (definition) |
| The seven streams are HERMES, ARES, HELIOS, HELIOS Trade Suggestions, TRON, Operational Health, Quarantine | same file, stream entities | PROVEN (definition) |
| Identity-spoof suite: 4 of 4 scenarios PASS; correct-identity control 2 of 2 PASS; 4 of 4 valid-via-dedicated-input PASS; three connection-level cases are not auto-verdicted (they need server-log confirmation) | `tests/fte/last_run_report_pid04.json` (generated 2026-09-29), parsed for this audit | PROVEN as a committed historical report; says nothing about today's runtime |
| An earlier runtime acceptance of the ARES path and a failure-isolation window were recorded by the delivery team on 2026-10-06 | `docs/operations/FALCON-PID06-RUNTIME-ACCEPTANCE-EVIDENCE.md` s3 to s5 | PROVEN as a record; not re-observed |
| A FALCON container recreation on 2026-10-04 lost 27 HERMES events over about 19.7 s | same record, s7 | PROVEN as a record |
| Stack versions are frozen in a bill of materials | `deploy/BOM.md` | PROVEN (file exists); runtime match UNVERIFIED |

## Items the PID asked EP-2 to carry

| Item | Result |
|---|---|
| Container names, status, restart policy, health, labels | UNVERIFIED. Reason: lane limit (no inspection of running services). A private operations record is held by the maintainers; its content is not reproduced here. |
| systemd finding | UNVERIFIED. Same reason. |
| Legacy-stack exclusion | PARTIAL, from source: `README.md` lines 21 to 23 state that an older, unrelated repository at an identical-looking path is a different legacy implementation and not this one. The Falcon Ranger and the older Graylog stack named in the PID are not described by any file read here; they are not assessed beyond that, and the PID statement that they are separate is UNVERIFIED by this audit. |
| Whether HERMES is publishing in steady state | UNVERIFIED (needs the authenticated Graylog API). |
| Message counts, live input and stream configuration, index sizes | UNVERIFIED (needs authenticated access; none was requested or used). |

## Decision D-4 status

D-4 (authenticated read-only Graylog access, or an export run by the operations owner) is still open. Without it EP-2's runtime half stays UNVERIFIED. A read-only export produced by the operations owner (stream list, input list, per-stream message counts for a stated window) would close every UNVERIFIED row in this file without this audit touching the service.
