# FALCON PID-05 Stage 1 — HELM Handover Brief

**Purpose:** four precise, bounded privileged-infrastructure actions
HELM needs to perform (or explicitly decide not to yet) to bring
PID-05 Stage 1's committed contract/pipeline changes fully live.
Written to be followed exactly, mirroring
`docs/operations/FALCON-PID04-PRIVILEGED-OPERATIONS-RUNBOOK.md`'s own
rigor — every command is precise, every `<password>`/`<id>` is read
live from the API, nothing here should require redesigning anything.
None of these four actions has been executed by this delivery or by
Rogue as of this brief — they are handed over, not done.

All commands assume a shell on `dell-debian` (`ssh root@192.168.11.10`).

---

## 1. Connectivity — publish HERMES's dedicated input port to the host

**Status: proposed design, ready for a bounded work order — not yet
applied.**

**Change:** add exactly one new line to `deploy/docker-compose.yml`'s
`graylog-falcon` service, in its existing `ports:` block:

```yaml
    ports:
      - "${FALCON_GRAYLOG_HOST_BIND_IP:?FALCON_GRAYLOG_HOST_BIND_IP is required}:${FALCON_GRAYLOG_HOST_PORT:?FALCON_GRAYLOG_HOST_PORT is required}:9000"
      - "${FALCON_GRAYLOG_HOST_BIND_IP:?FALCON_GRAYLOG_HOST_BIND_IP is required}:${FALCON_HERMES_INPUT_HOST_PORT:?FALCON_HERMES_INPUT_HOST_PORT is required}:12411"
```

Add `FALCON_HERMES_INPUT_HOST_PORT=12411` to `deploy/.env.example` (with
a comment, non-secret) and to the real `deploy/.env` (canonical
checkout). Reuses the existing `FALCON_GRAYLOG_HOST_BIND_IP` — do not
introduce a second bind-IP variable, every published port is on the same
host. Apply with `docker compose -p falcon up -d graylog-falcon`
(recreates only that one container).

**Explicitly do NOT publish ports 12412-12415** (ARES/HELIOS/both TRON
identities) — each needs its own separate authorisation once that
producer's own integration is actually being implemented.

**Acceptance criteria:**
- `docker compose -p falcon config` shows exactly one new published
  port (12411), bound to `192.168.11.10`, never `0.0.0.0`.
- Compose refuses to start if `FALCON_HERMES_INPUT_HOST_PORT` is unset
  (fail-loud, matching every other required variable in this file).
- `docker port graylog-falcon` shows only `9010` and `12411` — ports
  12412-12415 remain unpublished.
- A real mTLS connection from a HERMES-reachable network path to
  `192.168.11.10:12411` succeeds exactly as it already does from
  `falcon-net` directly (no behavioural change to the input itself).
- IRIS confirmed unaffected before and after (same checkpoint
  discipline as every prior privileged change in this project).

---

## 2. Storage — apply the Custom Field Mapping to the live evidence index

**Status: the mechanism is proven (PID-05's isolated native
large-payload DEV test) and the pipeline-side half is committed in this
same PR (the `base64_encode()`+`remove_field()` rule) — but the actual
OpenSearch-level mapping on the real `falcon-evidence_0` index set has
deliberately NOT been applied yet. Without this step, `hermes_signal_
original_payload` is indexed as an ordinary, unmapped `keyword` field —
functionally correct for content up to 32,766 bytes, but silently
subject to the already-documented failure mode 2 above that.**

**Exact action, mirroring the proven DEV test precisely — this is the
live-confirmed field-name syntax, not an inferred one.** An earlier draft
of this brief used `"index_set_ids"` and `"rotate_immediately"`; those
names were tried live during the isolated DEV test and the API rejected
them (`"Unable to map property index_set_id..."`). The correct,
confirmed-working field names are `"index_sets"` (plural, still a list)
and `"rotate"`:

```bash
curl -su admin:<password> -X PUT http://192.168.11.10:9010/api/system/indices/mappings \
  -H 'Content-Type: application/json' -H 'X-Requested-By: pid05-helm' \
  -d '{"index_sets": ["<the real FALCON Evidence index set id>"], "field": "hermes_signal_original_payload", "type": "binary", "rotate": false}'
```

Success response shape: `{"<index_set_id>":{"field_name":"hermes_signal_original_payload","type":"binary","origin":"OVERRIDDEN_INDEX","is_reserved":false}}`.

(Field/type names must match the pipeline rule's own literal
`set_field("hermes_signal_original_payload", ...)` call exactly — see
`deploy/content-packs/falcon-pid03-ingestion-v1.json` rev 4's new rule,
"FALCON - encode hermes signal raw payload to binary field".)

Get the real `FALCON Evidence` index set id first —
`GET /api/system/indices/index_sets` — never assume it.

**Whether to set `rotate: true` is HELM's own operational call**, not
prescribed here: an immediate rotation applies the mapping right away but
creates a new physical index sooner than the natural rotation schedule
would; leaving it `false` means the mapping applies correctly (per
PID-05's own proven, live-confirmed finding) at the next natural
rotation, with existing indexed data unaffected either way (a mapping
change is never retroactive to already-indexed documents, confirmed in
the DEV test).

**Verification (mirrors the DEV test exactly):** send one real (or FTE
synthetic) `hermes.signal_state` event carrying a raw payload over
32,766 bytes via `_hermes_signal_raw_json`, confirm it indexes without
an "immense term" error, retrieve it via the API, base64-decode
`hermes_signal_original_payload`, confirm it matches the original
byte-for-byte.

**Do not apply this mapping to any field on any other producer's
family** — it is scoped to this one field name, which is itself scoped
(via the pipeline rule's own `has_field()` guard) to only messages
carrying the designated raw-payload field.

---

## 3. Credentials — durable mTLS storage (implemented for HERMES; three producers still pending)

**Status: implemented for HERMES, confirmed live** (see this PID's own
discovery-phase Section E.1, now marked IMPLEMENTED): `dell-debian:
/srv/falcon/deploy/secrets/pid04-mtls/` durably holds HERMES's client
cert+key and a copy of the server cert, on the canonical, non-worktree
checkout — confirmed correct permissions (`clients/hermes.key` 600,
`clients/hermes.crt` 644, `server/server.crt` 644, directories `700`
throughout) and confirmed `.gitignore` coverage
(`**/secrets/**` matches, verified via `git check-ignore -v` against
`/srv/falcon`'s own working copy, not a worktree). **No action needed
from HELM for HERMES specifically.**

**Standing action item, not part of PID-05's own scope, but handed over
here since it's the same root cause:** ARES, HELIOS, and both TRON
identities' mTLS client keys (generated during PID-04) still exist only
inside their now-deleted originating worktree's history — i.e. they are
almost certainly **already lost**, the exact same way HERMES's was,
twice. **HELM should regenerate fresh keypairs for all four (matching
PID-04's own exact generation convention — CN=`<producer>`,
O=FALCON-DEV, OU=producer, clientAuth EKU, RSA 2048, 3650-day validity —
see `deploy/README.md`'s PID-04 certificate section) and place them
directly at `dell-debian:/srv/falcon/deploy/secrets/pid04-mtls/clients/`
from the start**, never inside a worktree, before any of those four
producers are actually integrated — there is no reason to repeat this
exact lesson a third and fourth time.

---

## 4. Security finding — OpenSearch unauthenticated on `falcon-net`

**Status: a confirmed, live finding from PID-05's discovery phase
(Section E.2), handed to HELM as a standing, FALCON-wide item — not
something PID-05 itself is scoped to fix.**

`datanode-falcon`'s OpenSearch REST API is completely unauthenticated
over plain HTTP on `falcon-net`: `GET http://datanode-falcon:9200/
_cluster/health` and `GET .../_cat/indices`, from a throwaway container
on that network, both returned full, real data with zero credentials —
including a direct listing of the live `falcon-evidence_0` index (450
documents, at the time this was checked). No write/delete was
attempted, but nothing about an unauthenticated REST API distinguishes
read from write/delete at the network layer. **MongoDB on the same
network is confirmed properly authenticated** (`db.adminCommand(
{listDatabases:1})` correctly returns `MongoServerError: Command
listDatabases requires authentication`) — this finding is specifically
and only about OpenSearch.

**Why this matters for Stage 1 specifically:** it is the direct reason
the "attach a producer container to `falcon-net` as a second network"
connectivity option (an alternative to section 1's host-port-publishing
approach above) was rejected, not merely reviewed — anything on
`falcon-net` today has direct, unauthenticated access to the raw
evidence store, completely bypassing every layer of authentication and
validation this project has built (PID-04's mTLS, PID-03's pipeline).

**Handed to HELM as an open question, not a directive:** whether to
enable OpenSearch authentication on `falcon-net` (Data Node's own
security features, or a network-layer control) is an infrastructure
decision outside this PID's scope and authority. Recorded here
precisely so it doesn't have to be rediscovered, and so any future
producer-connectivity decision (this one or a later one) is made with
this fact in hand, not without it.

---

## Evidence trail

Full reasoning, live evidence, and cross-references for all four items
above live in `pids/PID-05-HERMES-INTEGRATION.md` — this brief is the
action-oriented summary for execution, that document is the
authoritative record of how each conclusion was reached. Memory Fabric
and any other handover record should point to this file for execution
steps and to the PID-05 doc for the "why."
