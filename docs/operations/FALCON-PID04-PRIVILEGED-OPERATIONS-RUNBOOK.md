# FALCON PID-04 — Privileged Operations Runbook

**Audience:** whoever holds working Graylog admin API access for
`graylog-falcon` (this delivery's sandbox is explicitly barred from
holding or using that credential — see the PID-04 forge report's
escalation history). Written to be followed exactly, in order, without
redesigning anything. Every `<password>` below is the live Graylog
admin password; every `<id>` is read live from the API in the step that
finds it, never assumed from this document.

All commands assume a shell on `dell-debian` (`ssh root@192.168.11.10`),
working directory
`/srv/falcon-worktrees/wo-PID-04-producer-connection-security`.

**Status: sections 0-12 below are the historical record of the original
end-to-end execution against content-pack rev 2** — every step passed,
including the reconstruction proof, and the corrections folded into
those sections (steps 2, 3, 7, 10, 11) reflect what that execution
actually found. That execution is also what proved rev 2 itself had a
defect: it left the deprecated shared unauthenticated input defined in
the pack, which the Architect ruled unacceptable (FF-LEGACY-INGRESS-01)
— **section 13 is the current, authoritative procedure**, targeting the
corrected rev 3 pack, and supersedes step 10's "decommission" framing
and step 11(g.1)'s "re-delete after reinstall" step. Read section 13
before executing anything if your goal is proving/using the current
(rev 3) design; sections 0-12 remain here because the platform-behaviour
findings in them (steps 2, 3, 7) are still fully applicable to rev 3 —
only the legacy-input handling in steps 10/11 is superseded.

## 0. Pre-flight — baseline evidence (capture before touching anything)

```bash
curl -su admin:<password> http://192.168.11.10:9010/api/system/lbstatus
ls -la deploy/secrets/pid04-mtls/server deploy/secrets/pid04-mtls/clients deploy/secrets/pid04-mtls/trusted-leafs
docker ps --format '{{.Names}}\t{{.Status}}' | grep -E 'graylog|datanode|mongodb'
```

Record the IRIS containers' (`graylog`, `graylog-mongo`,
`graylog-elasticsearch`) current uptime/health here and again after step
12 — they must be identical/unaffected throughout.

**Confirmed:** `tls_client_auth: "required"` is the correct literal
string — verified via `GET /api/system/inputs/types/
org.graylog2.inputs.gelf.tcp.GELFTCPInput` on the first live execution
of this runbook. No content-pack fix was needed. Still worth a quick
re-check on any future Graylog version bump:

```bash
curl -su admin:<password> http://192.168.11.10:9010/api/system/inputs/types/org.graylog2.inputs.gelf.tcp.GELFTCPInput | python3 -m json.tool
```

If the `tls_client_auth` field's declared allowed values ever differ
from the literal string `"required"` on some future Graylog version,
fix all 5 occurrences in
`deploy/content-packs/falcon-pid03-ingestion-v1.json` before installing,
and note the correction in your evidence.

## 1. Place mTLS certificate material inside `graylog-falcon`

The generated DEV certs live on the host at
`deploy/secrets/pid04-mtls/` (never in Git — confirmed covered by the
existing `**/secrets/**` `.gitignore` rule). They must be copied into
`graylog-falcon`'s own filesystem, under the **already-existing named
volume** `graylog-falcon-journal` (mounted at `/usr/share/graylog/data`)
so they survive a container recreate with **zero `docker-compose.yml`
changes**.

```bash
D=/srv/falcon-worktrees/wo-PID-04-producer-connection-security/deploy/secrets/pid04-mtls

for dir in server trust/hermes trust/ares trust/helios trust/tron_execution_engine trust/tron_discovery_service; do
  docker exec -u root graylog-falcon mkdir -p /usr/share/graylog/data/pid04-mtls/$dir
done

docker cp "$D/server/server.crt" graylog-falcon:/usr/share/graylog/data/pid04-mtls/server/server.crt
docker cp "$D/server/server.key" graylog-falcon:/usr/share/graylog/data/pid04-mtls/server/server.key
docker cp "$D/trusted-leafs/hermes.crt" graylog-falcon:/usr/share/graylog/data/pid04-mtls/trust/hermes/hermes.crt
docker cp "$D/trusted-leafs/ares.crt" graylog-falcon:/usr/share/graylog/data/pid04-mtls/trust/ares/ares.crt
docker cp "$D/trusted-leafs/helios.crt" graylog-falcon:/usr/share/graylog/data/pid04-mtls/trust/helios/helios.crt
docker cp "$D/trusted-leafs/tron_execution_engine.crt" graylog-falcon:/usr/share/graylog/data/pid04-mtls/trust/tron_execution_engine/tron_execution_engine.crt
docker cp "$D/trusted-leafs/tron_discovery_service.crt" graylog-falcon:/usr/share/graylog/data/pid04-mtls/trust/tron_discovery_service/tron_discovery_service.crt

# graylog-falcon's process runs as uid 1100 (graylog), confirmed via
# `docker exec graylog-falcon id`. docker cp writes as root, so fix
# ownership/permissions as root inside the container:
docker exec -u root graylog-falcon chown -R graylog:graylog /usr/share/graylog/data/pid04-mtls
docker exec -u root graylog-falcon chmod 700 /usr/share/graylog/data/pid04-mtls/server
docker exec -u root graylog-falcon chmod 600 /usr/share/graylog/data/pid04-mtls/server/server.key
docker exec -u root graylog-falcon chmod 644 /usr/share/graylog/data/pid04-mtls/server/server.crt
docker exec -u root graylog-falcon chmod 755 /usr/share/graylog/data/pid04-mtls/trust /usr/share/graylog/data/pid04-mtls/trust/*
docker exec -u root graylog-falcon chmod 644 /usr/share/graylog/data/pid04-mtls/trust/*/*.crt

# Verify readability as the ACTUAL runtime user (not root) before proceeding:
docker exec graylog-falcon sh -c 'test -r /usr/share/graylog/data/pid04-mtls/server/server.key && test -r /usr/share/graylog/data/pid04-mtls/trust/hermes/hermes.crt && echo READABLE_OK'
```

Do not proceed past this step until `READABLE_OK` prints.

## 2. Install the content pack (revision 2)

`deploy/content-packs/falcon-pid03-ingestion-v1.json` has been edited
IN PLACE by this delivery: same top-level content-pack `id`
(`c3461561-229e-45af-b59f-171f8f026d47` — **read it from the file, don't
trust this copy**), `rev` bumped `1 -> 2`. This is a revision of the
already-installed PID-03 pack, not a new/second pack.

**Confirmed via live execution — mandatory pre-install step.** Graylog's
`PipelineRuleFacade.findExisting()` does a cross-revision title+source
comparison and refuses to silently overwrite a rule whose source
diverges from what's already live (`DivergingEntityConfigurationException`).
Rev 2 modifies the pipeline entity's own source (its stage-1 rule list)
and 7 existing stage-2 rules' source (each gains the
`falcon_identity_mismatch` OR-condition) — every one of those 8 entities
must be deleted **before** installing rev 2, or the install will fail
outright on the first diverged rule it hits. Only these 8; the other 21
already-installed pipeline_rule entities are byte-identical between rev
1 and rev 2 and match/reuse cleanly with no deletion needed.

```bash
cd /srv/falcon-worktrees/wo-PID-04-producer-connection-security
PACK_ID=$(python3 -c "import json; print(json.load(open('deploy/content-packs/falcon-pid03-ingestion-v1.json'))['id'])")

# Pre-install: delete the pipeline entity + the 7 stage-2 rules whose
# source actually changed (titles are stable and match the content pack):
curl -su admin:<password> http://192.168.11.10:9010/api/system/pipelines/pipeline \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print([p['id'] for p in d if p['title']=='FALCON Ingestion'][0])"
# -> $OLD_PIPELINE_ID; then:
curl -su admin:<password> -X DELETE "http://192.168.11.10:9010/api/system/pipelines/pipeline/$OLD_PIPELINE_ID" -H 'X-Requested-By: pid04-rogue'

curl -su admin:<password> http://192.168.11.10:9010/api/system/pipelines/rule \
  | python3 -c "
import json,sys
titles = {
  'FALCON - route INVALID to Quarantine','FALCON - route valid HERMES evidence',
  'FALCON - route valid ARES evidence','FALCON - route valid HELIOS evidence',
  'FALCON - route valid HELIOS Trade Suggestions','FALCON - route valid TRON evidence',
  'FALCON - route valid Operational Health evidence',
}
d = json.load(sys.stdin)
print('\n'.join(r['id'] for r in d if r['title'] in titles))
" > /tmp/pid04_diverging_rule_ids.txt
while read -r rid; do
  curl -su admin:<password> -X DELETE "http://192.168.11.10:9010/api/system/pipelines/rule/$rid" -H 'X-Requested-By: pid04-rogue'
done < /tmp/pid04_diverging_rule_ids.txt

# Now install rev 2:
curl -su admin:<password> -X POST http://192.168.11.10:9010/api/system/content_packs \
  -H 'Content-Type: application/json' -H 'X-Requested-By: pid04-rogue' \
  --data-binary @deploy/content-packs/falcon-pid03-ingestion-v1.json

# Body MUST be wrapped as {"entity": {...}} -- a bare {"parameters": {},
# "comment": "..."} 400s with "entity cannot be null" (the same gotcha
# this file's own PID-02 section already documents near the top; applies
# identically to this installations endpoint, confirmed via live
# execution -- hit literally, first try, before this fix).
curl -su admin:<password> -X POST \
  "http://192.168.11.10:9010/api/system/content_packs/${PACK_ID}/2/installations" \
  -H 'Content-Type: application/json' -H 'X-Requested-By: pid04-rogue' \
  -d '{"entity": {"parameters": {}, "comment": "PID-04: dedicated mTLS inputs + identity enforcement"}}'
```

If the POST to `/content_packs` 4xxs because revision 2 already exists
from a prior attempt, skip straight to the installations call. Confirmed
via live execution: the plain reinstall `POST` works directly in every
case tested (original install and the step-11 reconstruction cycle) —
no stale-installation-record removal is needed.

## 3. Post-install verification and fixups

**Confirmed via live execution: a revision update does NOT re-disable or
re-point streams whose content is unchanged** — `StreamFacade` leaves
them alone, so PID-03's original fresh-install stream fixups are not
needed here. **But `StreamFacade` (and `InputFacade`) also do no
cross-revision matching at all**, so installing rev 2 blindly creates a
duplicate of every one of the 7 streams (disabled, wrong index set) and
a duplicate of the old shared input (port-conflicting, FAILED state) —
confirmed, and it happens on every install/reinstall of this pack, not
just the first one. Check and clean these up every time:

```bash
curl -su admin:<password> http://192.168.11.10:9010/api/streams | python3 -m json.tool > /tmp/streams_after_install.json
# For each of the 7 "FALCON: ..." stream TITLES, confirm exactly ONE
# stream exists with that title, "disabled": false, and index_set_id
# equal to the real "FALCON Evidence" index set id (get that id via:
#   curl -su admin:<password> http://192.168.11.10:9010/api/system/indices/index_sets )
# If a title has TWO streams (the original + a fresh disabled/mis-pointed
# duplicate), DELETE the duplicate (DELETE /api/streams/{dup_id}) and
# keep the original. Only if the ORIGINAL itself is somehow disabled or
# mis-pointed (shouldn't happen per the above, but check), repeat PID-03's
# own fixup: POST /api/streams/{id}/resume ; PUT /api/streams/{id} with
# the correct index_set_id.

curl -su admin:<password> http://192.168.11.10:9010/api/system/inputs | python3 -m json.tool > /tmp/inputs_after_install.json
# Confirm exactly ONE input titled "FALCON Producer Ingest (GELF TCP)"
# (the old shared input) is RUNNING on port 12401; DELETE any duplicate/
# FAILED-state copy with the same title.

curl -su admin:<password> http://192.168.11.10:9010/api/system/pipelines/pipeline | python3 -m json.tool > /tmp/pipeline_after_install.json
# Note the "FALCON Ingestion" pipeline's real id, call it $PIPELINE_ID.
# The route GET /api/system/pipelines/connections/to_stream/{id} 404s
# unconditionally in this Graylog version -- NOT a valid route (confirmed
# live). Use the list-all route instead:
curl -su admin:<password> http://192.168.11.10:9010/api/system/pipelines/connections | python3 -m json.tool
# Check whether $PIPELINE_ID appears in the entry for
# stream_id "000000000000000000000001". If not:
curl -su admin:<password> -X POST http://192.168.11.10:9010/api/system/pipelines/connections/to_stream \
  -H 'Content-Type: application/json' -H 'X-Requested-By: pid04-rogue' \
  -d "{\"stream_id\": \"000000000000000000000001\", \"pipeline_ids\": [\"$PIPELINE_ID\"]}"
```

## 4. Confirm the 5 dedicated inputs exist and are RUNNING

```bash
curl -su admin:<password> http://192.168.11.10:9010/api/system/inputs | python3 -m json.tool
```

Confirm all 5 titles present (`FALCON Producer Ingest — HERMES` / `—
ARES` / `— HELIOS` / `— TRON (tron.execution_engine)` / `— TRON
(tron.discovery_service)`), note each real `id` (call these
`$HERMES_INPUT_ID` etc. — informational/correlation use only, never
needed by any rule since `from_input(name:)` resolves by title).

```bash
curl -su admin:<password> http://192.168.11.10:9010/api/system/inputstates | python3 -m json.tool
```

All 5 should show `RUNNING`. All 5 were created with `"global": true`,
avoiding PID-02's own documented "non-global input silently never
launches without an explicit node id" gotcha — but confirm anyway.

## 5. PID-03 regression suite (must still pass via the OLD shared input) — HISTORICAL as of rev 3

**This step is only meaningful against a rev-1/rev-2 environment where
port 12401 still exists.** As of content-pack rev 3
(FF-LEGACY-INGRESS-01), the shared input this step targets is gone from
the authoritative design entirely — running this against a genuinely
rev-3-reconstructed environment will fail to connect at all (expected,
not a regression). It is kept below as the historical procedure that
was actually run during the original rev-2 delivery. Step 6 (`pid04`
mode) is the current ingestion regression authority — see
`deploy/README.md`'s "Test-harness modes" section.

```bash
docker run --rm --network falcon-net \
  -v /srv/falcon-worktrees/wo-PID-04-producer-connection-security:/repo:ro \
  -e GRAYLOG_API_BASE=http://graylog-falcon:9000/api \
  -e GRAYLOG_USER=admin -e GRAYLOG_PASSWORD='<password>' \
  python:3.11-slim python3 /repo/tests/fte/run_pid03_tests.py pid03
```

Expected: exit code 0, identical to PID-03's own recorded result — 4/4
positive PASS; of 13 negative fixtures, 11 `EXPECTED_QUARANTINED` + 2
`KNOWN_CAPABILITY_EXCEPTION_CONFIRMED`, 0 unexpected/unclassified. This
proves the pipeline extension didn't change PID-03's own documented
behaviour (the 2 DSL capability exceptions, the 10 other structural
flags, UTC/decimal handling) at all.

## 6. PID-04 mTLS + identity suite

```bash
docker run --rm --network falcon-net \
  -v /srv/falcon-worktrees/wo-PID-04-producer-connection-security:/repo:ro \
  -e GRAYLOG_API_BASE=http://graylog-falcon:9000/api \
  -e GRAYLOG_USER=admin -e GRAYLOG_PASSWORD='<password>' \
  python:3.11-slim python3 /repo/tests/fte/run_pid03_tests.py pid04
```

Expected, all auto-verdicted by the script's own exit code:
- `valid_via_dedicated_input`: 4/4 PASS (HERMES/ARES/HELIOS/TRON-exec,
  each via mTLS through its own dedicated input, full field +
  decimal-precision preservation, `falcon_identity_mismatch` absent).
- `identity_spoof`: 4/4 PASS — HERMES-input claims helios,
  ARES-input claims hermes, TRON-execution_engine-input claims
  tron.discovery_service, TRON-discovery_service-input claims
  tron.execution_engine. Each must show `falcon_validity=INVALID`,
  `falcon_identity_mismatch=true`, a populated
  `falcon_security_reason`, routed **only** to `FALCON: Quarantine`,
  and — the specific FF-PRODUCER-IDENTITY-01 proof — the indexed
  `producer_system_id`/`producer_component_id` field still shows the
  **false claimed value**, never repaired back to the truth.
- `correct_identity_control`: 2/2 PASS (both TRON identities, own
  input, own correct id, accepted normally) — proves the spoof
  quarantines above are identity-specific, not "everything on this
  input is quarantined regardless."

The 3 `connection_level` results are **not** auto-verdicted (their
`status` is always `NEEDS_ROGUE_SERVER_LOG_CONFIRMATION` by design —
see `pid04_run_connection_level_test`'s docstring in
`tests/fte/run_pid03_tests.py`). For each of `plaintext`,
`no_client_cert`, `untrusted_client_cert`:

1. Note the wall-clock time immediately before this suite ran.
2. `docker logs graylog-falcon --since <time>` — **confirmed exact
   exception class names** (reproduced identically across 3 separate
   live runs — initial, post-bugfix, post-reconstruction), the canonical
   reference shapes for this Graylog version:
   - `plaintext` → `NotSslRecordException: not an SSL/TLS record`
   - `no_client_cert` → `OpenSslHandshakeException: ...
     PEER_DID_NOT_RETURN_A_CERTIFICATE`
   - `untrusted_client_cert` → `SSLHandshakeException: General
     OpenSslEngine problem` (a generic Netty/OpenSSL wrapper message —
     it does not say "certificate verify failed" the way this delivery's
     local `openssl s_server` self-test did for the same underlying
     condition; that's a real wording difference between two TLS
     stacks, not a bug).
3. Confirm `message_indexed: false` in the script's JSON output for all
   three (already checked automatically).
4. **Do not** treat `client_side_result` as the verdict. Expect it to
   say "completed without a client-side exception" for at least
   `plaintext` and `no_client_cert` even though the server rejected
   them — this is the TLS-1.3-client-lies behaviour discovery already
   found and this delivery's own local self-test reproduced three times
   in a row; it is expected, not a bug in the test harness.

## 7. Certificate revocation test

**Confirmed via live execution: this takes effect immediately.** No
input restart, config-apply, or any other refresh trigger is needed —
Graylog re-reads the `tls_client_auth_cert_file` trust directory on
every new TLS handshake attempt, unlike a full input-config change
(which does cause the documented STOPPING→RUNNING cycle for other
settings). The first confirmed run: the very next connection attempt
using the just-revoked `ares` cert, made immediately with no restart of
any kind, was rejected — `docker logs graylog-falcon` showed an
immediate `SSLHandshakeException` for that attempt, and it is
confirmed-absent from the search index.

```bash
docker exec -u root graylog-falcon rm /usr/share/graylog/data/pid04-mtls/trust/ares/ares.crt

# Immediately (no restart, no config-apply) attempt a connection with
# ares's now-revoked cert and check per step 6's rules (docker logs +
# message-indexed check) -- expect rejection on this very first attempt.
```

Then:
- Confirm ares is rejected (docker logs + absent from search).
- Confirm hermes/helios/tron-exec/tron-disc are **unaffected** — send
  one valid fixture through each (`pid04_run_valid_via_dedicated_input`
  logic, or a manual `sender.py` mTLS call) and confirm normal
  acceptance. This proves per-producer revocation with zero CA reissue
  and zero collateral impact on the other 4 producers.
- Your call whether to restore `ares.crt` afterward to leave the
  environment fully working for whoever picks this up next — note
  whichever you choose in the evidence.

## 8. Restart/recovery test

```bash
docker restart graylog-falcon
# wait for: docker inspect graylog-falcon --format '{{.State.Health.Status}}' == healthy
docker restart datanode-falcon
# wait for healthy
```

Then: `GET /api/system/inputs` (all 5 dedicated + the still-present old
shared input, unless step 9 already ran), `GET /api/system/inputstates`
(all RUNNING), and re-send one valid fixture through each of the 4
producer paths to prove ingestion resumes normally. Confirm the IRIS
containers' uptime/health is unaffected (compare against step 0's
baseline) throughout.

## 9. Re-run step 5 once more (post-restart non-regression)

Confirm an identical result to step 5's pre-restart run.

## 10. Decommission the old shared input (HISTORICAL — superseded by rev 3, see section 13)

**This step's instruction is obsolete as of content-pack rev 3.** It is
kept below exactly as executed because it's the historical record that
led to the rev-3 fix (see the "Content-pack revision-install semantics"
finding 2 in `deploy/README.md`'s PID-04 section) — do not follow
"re-run this step after every future reinstall" (its own last paragraph,
below) against a rev-3-or-later environment; section 13 replaces it
with a structural fix instead of a remembered manual step.

**Only after steps 5, 6, 8 and 9 all pass clean.** A shared,
unauthenticated input left running alongside 5 authenticated dedicated
ones would defeat the entire point of this PID — see the PID-04 forge
report's explicit reasoning on this.

```bash
OLD_INPUT_ID=$(curl -su admin:<password> http://192.168.11.10:9010/api/system/inputs \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print([i['id'] for i in d['inputs'] if i['title']=='FALCON Producer Ingest (GELF TCP)'][0])")

curl -su admin:<password> -X DELETE "http://192.168.11.10:9010/api/system/inputs/${OLD_INPUT_ID}" \
  -H 'X-Requested-By: pid04-rogue'
```

Verify `GET /api/system/inputs` now shows exactly 5 inputs. Re-run step
5's suite one final time — **expect it to now fail to connect at all**
(connection refused on port 12401, since that input no longer exists).
This is the desired end state, not a regression: record it as such, and
note that PID-03's original regression suite is retired/superseded by
PID-04's own equivalent proof (step 6) from this point forward.

**Confirmed via live execution — this deletion is NOT durable against a
future content-pack reinstall.** The old shared input entity is still
defined, byte-for-byte, inside `falcon-pid03-ingestion-v1.json` rev 2
(a deliberate choice — see `deploy/README.md`'s "Content pack: extended
in place, not duplicated" section). Deleting it live only removes the
*current* object; the content pack itself still defines it, so it
**will reappear** (as a fresh entity, new id) the next time this exact
pack is reinstalled — confirmed directly: it reappeared during step 11's
reconstruction proof and had to be deleted a second time. **This exact
finding is what the Architect ruled on**: security must not rest on
remembering to re-run this step after every future reinstall —
FF-LEGACY-INGRESS-01 (section 13) removes the entity from the pack
itself instead, so rev 3 and later never create it at all.

## 11. Content-pack delete-and-reinstall reconstruction proof

**This is the single most important proof in this PID — do not skip or
shortcut it.** It proves the whole point of using `from_input(name:)`
instead of any hardcoded input id: that identity enforcement survives
the 5 inputs and the pipeline getting brand-new Mongo ObjectIds.

```bash
# (a) Record current (pre-delete) ids for comparison:
curl -su admin:<password> http://192.168.11.10:9010/api/system/inputs > /tmp/pid04_inputs_before.json
curl -su admin:<password> http://192.168.11.10:9010/api/system/pipelines/pipeline > /tmp/pid04_pipeline_before.json

# (b) Delete all 5 dedicated inputs (use the ids from step 4/(a)):
for id in $HERMES_INPUT_ID $ARES_INPUT_ID $HELIOS_INPUT_ID $TRON_EXEC_INPUT_ID $TRON_DISC_INPUT_ID; do
  curl -su admin:<password> -X DELETE "http://192.168.11.10:9010/api/system/inputs/$id" -H 'X-Requested-By: pid04-rogue'
done

# (c) Delete the pipeline (before its rules, dependency order):
curl -su admin:<password> -X DELETE "http://192.168.11.10:9010/api/system/pipelines/pipeline/$PIPELINE_ID" -H 'X-Requested-By: pid04-rogue'

# (d) Delete all 28 FALCON pipeline_rule objects (list ids via
# GET /api/system/pipelines/rule, filter titles starting "FALCON - "):
curl -su admin:<password> http://192.168.11.10:9010/api/system/pipelines/rule \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print('\n'.join(r['id'] for r in d if r['title'].startswith('FALCON - ')))" > /tmp/pid04_rule_ids.txt
while read -r rid; do
  curl -su admin:<password> -X DELETE "http://192.168.11.10:9010/api/system/pipelines/rule/$rid" -H 'X-Requested-By: pid04-rogue'
done < /tmp/pid04_rule_ids.txt

# (e) No lookup table / data adapter exists in this design (from_input(name:)
# needs none) -- nothing to delete here. This is a deliberate, documented
# deviation from a generic "delete the lookup table too" instruction; see
# deploy/README.md's PID-04 section for why.

# (f) Confirm empty:
curl -su admin:<password> http://192.168.11.10:9010/api/system/inputs | python3 -m json.tool
curl -su admin:<password> http://192.168.11.10:9010/api/system/pipelines/pipeline | python3 -m json.tool
curl -su admin:<password> http://192.168.11.10:9010/api/system/pipelines/rule | python3 -m json.tool
```

Note: because (b)/(c)/(d) above already deleted all 5 dedicated inputs,
the pipeline, and all 28 rules, there is nothing left for
`PipelineRuleFacade.findExisting()` to diverge against — this reinstall
does **not** hit the `DivergingEntityConfigurationException` from step
2 (that only applies when modifying an entity that's still live).

```bash
# (g) Reinstall from the SAME content pack file (rev 2). Confirmed via
# live execution (both here and in step 2): the plain reinstall POST
# works directly -- no stale-installation-record removal is ever
# needed, for either an initial install or this delete-then-reinstall
# cycle.
curl -su admin:<password> -X POST \
  "http://192.168.11.10:9010/api/system/content_packs/${PACK_ID}/2/installations" \
  -H 'Content-Type: application/json' -H 'X-Requested-By: pid04-rogue' \
  -d '{"entity": {"parameters": {}, "comment": "PID-04 reconstruction proof"}}'
```

**Confirmed via live execution — two more things happen here, exactly
as they did on the very first install (step 2/3), and must be redone.
(g.1) is HISTORICAL — this exact resurrection, against rev 2, is the
finding that produced the FF-LEGACY-INGRESS-01 fix in rev 3 (section
13). Against rev 3 or later, (g.1) does not apply — the entity is gone
from the pack, so it is never recreated in the first place; (g.2)
(stream duplication) still applies, since the 7 streams remain
unchanged and pack-defined:**

```bash
# (g.1) [rev 2 ONLY -- historical] The old shared "FALCON Producer
# Ingest (GELF TCP)" input reappears (fresh entity, new id) because it
# is still defined, unchanged, in the content pack -- even though step
# 10 already deleted it once. Re-delete it:
OLD_INPUT_ID_2=$(curl -su admin:<password> http://192.168.11.10:9010/api/system/inputs \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print([i['id'] for i in d['inputs'] if i['title']=='FALCON Producer Ingest (GELF TCP)'][0])")
curl -su admin:<password> -X DELETE "http://192.168.11.10:9010/api/system/inputs/${OLD_INPUT_ID_2}" -H 'X-Requested-By: pid04-rogue'

# (g.2) All 7 "FALCON: ..." streams get a fresh disabled/wrong-index-set
# duplicate again (StreamFacade does no cross-revision matching -- same
# as step 3). Clean these up the same way as step 3: for each of the 7
# titles, keep the original (enabled, correctly-indexed) stream, delete
# the new duplicate.
curl -su admin:<password> http://192.168.11.10:9010/api/streams | python3 -m json.tool
```

```bash
# (h) Verify NEW ids assigned (must differ from /tmp/pid04_inputs_before.json / pid04_pipeline_before.json):
curl -su admin:<password> http://192.168.11.10:9010/api/system/inputs > /tmp/pid04_inputs_after.json
curl -su admin:<password> http://192.168.11.10:9010/api/system/pipelines/pipeline > /tmp/pid04_pipeline_after.json
diff <(python3 -c "import json; print('\n'.join(sorted(i['id'] for i in json.load(open('/tmp/pid04_inputs_before.json'))['inputs'])))") \
     <(python3 -c "import json; print('\n'.join(sorted(i['id'] for i in json.load(open('/tmp/pid04_inputs_after.json'))['inputs'])))")
# expect: totally different id sets for the 5 dedicated inputs (proves
# the point) -- note them in your evidence. The old shared input's id
# will also differ from before, per (g.1) above, but that one gets
# deleted again anyway.

# (i) Confirm cert material is still present (it lives in the persistent
# volume, untouched by any Graylog-object deletion) -- re-run step 1's
# READABLE_OK check; only re-copy if genuinely missing.
docker exec graylog-falcon sh -c 'test -r /usr/share/graylog/data/pid04-mtls/server/server.key && test -r /usr/share/graylog/data/pid04-mtls/trust/hermes/hermes.crt && echo READABLE_OK'

# (j) Re-run step 3's fixups in full, including the (g.2) stream-
# duplicate cleanup above if not already done: streams' CONTENT is
# untouched so no resume/re-point is needed once duplicates are removed,
# but the pipeline is brand new so it will definitely need
# re-connecting to the Default Stream again (use the corrected
# GET /api/system/pipelines/connections route from step 3, not the
# 404ing /connections/to_stream/{id} route).

# (k) Re-run step 5 (PID-03 regression -- N/A if step 10 already
# decommissioned the old input; skip) and step 6 (PID-04 suite) IN FULL
# against the new ids. Expected: identical PASS results to the original
# run in steps 5/6, now proving from_input(name:) resolved correctly
# against Graylog-assigned ids it has never seen before. Confirmed live:
# this reproduced identically (4/4 + 4/4 + 2/2, exit 0) pre-restart,
# post-restart, and post-reconstruction.
```

## 12. Evidence to compile

- Every request/response from steps 0-11 (curl `-s` output or a capture
  script).
- `docker logs graylog-falcon` excerpts bracketing each step-6
  connection-level test and the step-7 revocation test — confirmed
  exact exception class names per producer/scenario (see step 6).
- `tests/fte/last_run_report.json` and
  `tests/fte/last_run_report_pid04.json` from both the pre-reconstruction
  (steps 5-6) and post-reconstruction (step 11k) runs — 4 files total,
  rename/copy each before it gets overwritten by the next run.
- IRIS container uptime/health snapshots from step 0 and step 12,
  showing no change.
- The confirmed `tls_client_auth` string (`"required"`, step 0).
- The `DivergingEntityConfigurationException` encountered on the first
  install attempt (step 2) and the pre-delete fix that resolved it.
- Every stream/input duplicate found and deleted, both after the
  initial install (step 3) and again after the reconstruction reinstall
  (step 11 g.1/g.2) — counts and ids.
- The old shared input's two separate deletions (step 10, then step
  11 g.1) and why the second was necessary (content-pack-defined
  entities are not durably deletable live).
- Confirmation that certificate revocation took effect on the very next
  connection attempt with no restart (step 7).
- Confirmation that the plain content-pack reinstall POST worked
  directly both times, with no stale-installation-record removal ever
  needed (steps 2 and 11g).

## 13. Rev 3 — remove the legacy input from the authoritative pack (FF-LEGACY-INGRESS-01)

**This section is the current, authoritative procedure — supersedes
step 10 and step 11(g.1)'s legacy-input handling.** Context: sections
0-12 above document the original delivery and proof against
content-pack rev 2, which left the deprecated shared unauthenticated
`FALCON Producer Ingest (GELF TCP)` input defined in the pack (byte-for-
byte unchanged), reasoning that its removal from the live server was a
separate, deliberate, manual step. Step 11's own reconstruction proof
showed that reasoning was wrong: the entity reappeared on reinstall,
because the pack still defined it. The Architect's ruling on review:
**do not rely on post-install deletion for security.** Rev 3 removes
the entity from `deploy/content-packs/falcon-pid03-ingestion-v1.json`
entirely — see `deploy/README.md`'s PID-04 section (FF-LEGACY-INGRESS-01
and the "Content-pack revision-install semantics" finding 2) for the
full reasoning and the from-scratch-vs-in-place-upgrade distinction.

### 13.1 One-time migration cleanup (this specific dell-debian environment only)

This environment currently has a live copy of the legacy input
(recreated during the rev-2 reconstruction test, step 11 g.1, and never
re-deleted since). Installing rev 3 will **not** retroactively remove
it — dropping an entity from a revision does not delete an
already-installed live copy (the same asymmetry documented for
stream/input duplication in step 3/11). Delete it once, explicitly,
before or as part of the reconstruction below:

```bash
curl -su admin:<password> http://192.168.11.10:9010/api/system/inputs \
  | python3 -c "import json,sys; d=json.load(sys.stdin); m=[i['id'] for i in d['inputs'] if i['title']=='FALCON Producer Ingest (GELF TCP)']; print(m[0] if m else '')"
# if a non-empty id printed:
curl -su admin:<password> -X DELETE "http://192.168.11.10:9010/api/system/inputs/<that id>" -H 'X-Requested-By: pid04-rogue'
```

A genuinely fresh environment that never had rev 1/rev 2 installed does
not need this step at all — reconstructing directly from rev 3 never
creates the legacy input in the first place, which is the entire point
of this fix.

### 13.2 Full delete-everything-and-reinstall-from-rev-3 proof

Identical procedure to step 11(a)-(k), with these differences:
- Also ensure the legacy input is gone (13.1) as part of teardown, if
  not already handled.
- `PACK_ID` is unchanged; reinstall targets **revision 3**, not 2:
  `POST .../content_packs/${PACK_ID}/3/installations` (same body shape
  as before: `{"entity": {"parameters": {}, "comment": "..."}}`).
- Step 11(g.1) does not apply here (see the historical/rev-3 split
  already noted at that step) — after reinstalling from rev 3, do
  **not** expect the legacy input to reappear, and confirm it doesn't.
- Step 11(g.2) (stream duplication) still applies — the 7 streams are
  unchanged in rev 3 and remain subject to the same `StreamFacade`
  blind-duplication behaviour; clean up per step 3.

**The proof this section exists to produce:** immediately after
reinstalling from rev 3, `GET /api/system/inputs` must show **exactly 5
inputs** — no `FALCON Producer Ingest (GELF TCP)`, no listener on port
12401 at all, at any point. This is the difference between "absent
because it was deleted" and "absent because it was never defined" —
only the latter is what FF-LEGACY-INGRESS-01 requires, and only a
genuine from-scratch reconstruction from rev 3 proves it.

Then: re-run the full PID-04 adversarial suite (step 6) against the
fresh ids — expect identical results to every prior run
(4/4 + 4/4 + 2/2, exit 0). Do **not** re-run step 5 (`pid03` mode) as a
pass/fail check — it targets port 12401, which by design no longer
exists; if run anyway (e.g. via `all` mode for historical comparison),
expect it to fail to connect, and record that as confirmation of the
fix, not a defect.

### 13.3 Additional evidence for this section

- `GET /api/system/inputs` output immediately after the rev-3
  reconstruction, showing exactly 5 entries and their titles.
- Confirmation of whether 13.1's one-time migration cleanup found an
  existing legacy input to delete (it should, on this environment) or
  found none (which would itself be worth noting, in case an earlier
  step already removed it).
- The `pid04` suite's full result against the rev-3 ids.
- IRIS unaffected, confirmed once more at this final checkpoint.
