"""
FALCON PID-03 -- automated positive/negative ingestion proof suite.

*** PID-04 STATUS NOTE (rev 3, FF-LEGACY-INGRESS-01): the bare/default
*** invocation of this module (main(), the "pid03" suite below) targets
*** the shared "FALCON Producer Ingest (GELF TCP)" input on port 12401.
*** That input has been PERMANENTLY REMOVED from the authoritative
*** content pack and the authoritative reconstructed runtime as of
*** PID-04 rev 3 -- port 12401 no longer exists to connect to on a
*** correctly-reconstructed FALCON stack. This suite is RETIRED as a
*** live regression check and kept, unmodified, purely as PID-03's own
*** historical proof (see tests/fte/last_run_report.json and
*** deploy/README.md's PID-03 section). It was never CI-invoked, so
*** retiring it carries no CI risk. THE CURRENT INGESTION REGRESSION
*** AUTHORITY IS main_pid04() below (invoke via
*** `python3 run_pid03_tests.py pid04`) -- see deploy/README.md's
*** "Test-harness modes: pid03 (historical) vs pid04 (current
*** regression authority)" section for the full reasoning.

Runs against the REAL, running graylog-falcon DEV stack (no mocks). It
sends PID-01 fixtures through the real "FALCON Producer Ingest (GELF
TCP)" input using tests/fte/sender.py, then asserts what actually
happened via the real Graylog REST API -- never by asserting internal
FALCON state, since none exists (Graylog itself is authoritative).

Config (fails loudly if missing -- no hidden defaults):
    GRAYLOG_API_BASE   e.g. http://graylog-falcon:9000/api  (falcon-net)
                        or   http://192.168.11.10:9010/api  (host LAN)
    GRAYLOG_USER       Graylog root/admin username
    GRAYLOG_PASSWORD   Graylog root/admin password (never committed)
    GELF_HOST          host/service name of the GELF TCP input (default: graylog-falcon)
    GELF_PORT          port of the GELF TCP input (default: 12401)

Run from a container attached to falcon-net (a real producer would be
on this network too):

    docker run --rm --network falcon-net \\
        -v <worktree>:/repo:ro \\
        -e GRAYLOG_API_BASE=http://graylog-falcon:9000/api \\
        -e GRAYLOG_USER=admin \\
        -e GRAYLOG_PASSWORD=... \\
        python:3.11-slim python3 /repo/tests/fte/run_pid03_tests.py
"""
from __future__ import annotations

import base64
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sender  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
VALID_DIR = REPO_ROOT / "tests" / "fixtures" / "valid"
INVALID_DIR = REPO_ROOT / "tests" / "fixtures" / "invalid"


def _required_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise SystemExit(f"FATAL: required config {name} is not set (no hidden defaults).")
    return value


API_BASE = _required_env("GRAYLOG_API_BASE")
API_USER = _required_env("GRAYLOG_USER")
API_PASS = _required_env("GRAYLOG_PASSWORD")
GELF_HOST = os.environ.get("GELF_HOST", "graylog-falcon")
GELF_PORT = int(os.environ.get("GELF_PORT", "12401"))

# --- PID-04: dedicated mTLS inputs -----------------------------------------
# Ports and certificate layout are fixed, documented project structure (see
# deploy/README.md's PID-04 section), not installation-specific secrets --
# consistent with how GELF_PORT's default above is also a hardcoded, documented
# constant rather than a required env var. The certificate/key material itself
# is never committed (see deploy/secrets/pid04-mtls/.gitignore coverage) but
# its path convention is fixed by this project's own PID-04 delivery.
PID04_DEDICATED_PORTS: dict[str, int] = {
    "hermes": 12411,
    "ares": 12412,
    "helios": 12413,
    "tron_execution_engine": 12414,
    "tron_discovery_service": 12415,
}
PID04_CERTS_DIR = REPO_ROOT / "deploy" / "secrets" / "pid04-mtls"
PID04_SERVER_CA = PID04_CERTS_DIR / "server" / "server.crt"


def _pid04_client_cert(producer: str) -> Path:
    return PID04_CERTS_DIR / "clients" / f"{producer}.crt"


def _pid04_client_key(producer: str) -> Path:
    return PID04_CERTS_DIR / "clients" / f"{producer}.key"


def _auth(req: urllib.request.Request) -> None:
    token = base64.b64encode(f"{API_USER}:{API_PASS}".encode()).decode()
    req.add_header("Authorization", f"Basic {token}")
    req.add_header("X-Requested-By", "pid03-fte")
    req.add_header("Accept", "application/json")


def api_get(path: str) -> dict:
    req = urllib.request.Request(f"{API_BASE}{path}")
    _auth(req)
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read())


def load_stream_titles() -> dict[str, str]:
    """id -> title map for every stream currently on the server (fetched
    live, never hardcoded, since stream IDs are Mongo ObjectIds assigned
    at creation time)."""
    data = api_get("/streams")
    return {s["id"]: s["title"] for s in data["streams"]}


def find_message_by_query(query: str, *, wide_range: int = 604800, tries: int = 12, delay: float = 1.0):
    """Poll the Graylog universal search API until a message matching this
    query is indexed, or give up after `tries` attempts."""
    for _ in range(tries):
        try:
            result = api_get(
                f"/search/universal/relative?query={urllib.parse.quote(query)}"
                f"&range={wide_range}&limit=5&fields=message"
            )
        except urllib.error.URLError:
            result = {"messages": []}
        if result.get("messages"):
            entry = result["messages"][0]
            return {"_id": entry["message"]["_id"], "index": entry["index"]}
        time.sleep(delay)
    return None


def fetch_full_message(index: str, message_id: str) -> dict:
    return api_get(f"/messages/{index}/{message_id}")["message"]


def run_positive(fixture_name: str) -> dict:
    path = VALID_DIR / fixture_name
    event = sender.load_fixture(path)
    marker = uuid.uuid4().hex
    msg = sender.build_gelf_message(event, host="falcon-fte-positive", send_marker=marker)
    sender.send_gelf_tcp(msg, gelf_host=GELF_HOST, gelf_port=GELF_PORT)

    hit = find_message_by_query(f"fte_send_marker:{marker}")
    result = {"fixture": fixture_name, "falcon_event_id": event["falcon_event_id"], "status": "FAIL", "detail": None}
    if hit is None:
        result["detail"] = "message never indexed within timeout"
        return result

    full = fetch_full_message(hit["index"], hit["_id"])
    fields = full["fields"]
    stream_ids = full.get("stream_ids", [])

    checks = {}
    checks["falcon_event_id_intact"] = fields.get("falcon_event_id") == event["falcon_event_id"]
    checks["producer_system_id_intact"] = fields.get("producer_system_id") == event["producer_system_id"]
    checks["evidence_family_intact"] = fields.get("evidence_family") == event["evidence_family"]
    checks["produced_at_utc_intact"] = fields.get("produced_at_utc") == event["produced_at_utc"]
    checks["falcon_ingested_at_utc_present"] = bool(fields.get("falcon_ingested_at_utc"))
    checks["falcon_validity_is_VALID"] = fields.get("falcon_validity") == "VALID"
    if "provenance_ref" in event:
        checks["provenance_ref_upstream_ref_intact"] = (
            fields.get("provenance_ref_upstream_ref") == event["provenance_ref"].get("upstream_ref")
        )
    if "correlation_id" in event:
        checks["correlation_id_intact"] = fields.get("correlation_id") == event["correlation_id"]
    if "causation_id" in event:
        checks["causation_id_intact"] = fields.get("causation_id") == event["causation_id"]

    # decimal-string precision proof: every *_decimal payload field must
    # survive as a JSON/Python string, never int/float.
    decimal_checks = {}
    for key, value in event.get("payload", {}).items():
        if key.endswith("_decimal"):
            got = fields.get(f"payload_{key}")
            decimal_checks[key] = {
                "expected": value,
                "got": got,
                "got_python_type": type(got).__name__,
                "type_preserved_as_string": isinstance(got, str) and got == value,
            }
    checks["decimal_precision_preserved"] = (
        all(v["type_preserved_as_string"] for v in decimal_checks.values()) if decimal_checks else True
    )

    result["decimal_field_detail"] = decimal_checks
    result["field_checks"] = checks
    result["stream_ids"] = stream_ids
    result["all_checks_passed"] = all(checks.values())
    result["status"] = "PASS" if result["all_checks_passed"] else "FAIL"
    result["raw_fields"] = fields
    return result


# Every PID-01 invalid fixture asserts exactly one expected outcome --
# this is deliberately NOT a whitelist of "OK to fail" fixtures. A
# fixture missing from this map, or one whose actual outcome does not
# match its declared expectation, is itself a failure (see
# _classify_negative_outcome below) -- so a newly added invalid fixture
# must be classified here before the suite can pass, and a behaviour
# drift on an existing fixture is never silently absorbed.
#
# "QUARANTINED": the load-bearing PID-03 invariant applies in full --
#   this fixture MUST be routed to FALCON: Quarantine, never a trusted
#   producer stream.
# "KNOWN_CAPABILITY_EXCEPTION": a specific, evidence-backed, documented
#   Graylog 7.1.9 pipeline-rule-DSL limitation (see deploy/README.md)
#   -- NOT a bug, NOT worked around with bespoke middleware. The suite
#   asserts this fixture DOES slip through as trusted, precisely so a
#   future change in that behaviour (e.g. a Graylog upgrade adding a
#   map-key-enumeration function) is itself caught and surfaced, rather
#   than silently changing meaning.
EXPECTED_NEGATIVE_OUTCOMES: dict[str, str] = {
    "bad_event_family.json": "QUARANTINED",
    "bad_supersession_self_reference.json": "QUARANTINED",
    "causation_id_misused_as_correlation.json": "QUARANTINED",
    "missing_required_field.json": "QUARANTINED",
    "naive_timestamp.json": "QUARANTINED",
    "non_utc_offset_timestamp.json": "QUARANTINED",
    "payload_field_outside_family.json": "QUARANTINED",
    "unknown_component.json": "QUARANTINED",
    "unknown_producer_system.json": "QUARANTINED",
    "unregistered_score_definition.json": "QUARANTINED",
    "wrong_type.json": "QUARANTINED",
    "unknown_field.json": "KNOWN_CAPABILITY_EXCEPTION",
    "identity_violation_reused_event_id.json": "KNOWN_CAPABILITY_EXCEPTION",
}


def _classify_negative_outcome(fixture_name: str, outcome: str) -> str:
    """Compare the actual outcome against this fixture's single declared
    expectation. Returns one of:
      EXPECTED_QUARANTINED                 -- pass (category 1)
      KNOWN_CAPABILITY_EXCEPTION_CONFIRMED -- pass (category 2)
      UNEXPECTED_SLIPPED_THROUGH           -- FAIL (category 3 -- the
                                               exact invariant violation
                                               this correction exists to
                                               catch)
      UNCLASSIFIED_FIXTURE                 -- FAIL (fixture missing from
                                               EXPECTED_NEGATIVE_OUTCOMES
                                               entirely)
      UNEXPECTED_OUTCOME_FOR_EXPECTATION   -- FAIL (any other mismatch,
                                               e.g. an expected-QUARANTINED
                                               fixture instead landing as
                                               NOT_FOUND_OR_DROPPED, or a
                                               known-exception fixture
                                               unexpectedly starting to
                                               quarantine cleanly -- both
                                               are behaviour drift that
                                               must be investigated and
                                               this map updated
                                               deliberately, never
                                               silently passed)
    """
    expected = EXPECTED_NEGATIVE_OUTCOMES.get(fixture_name)
    if expected is None:
        return "UNCLASSIFIED_FIXTURE"
    if expected == "QUARANTINED":
        if outcome == "QUARANTINED":
            return "EXPECTED_QUARANTINED"
        if outcome == "SLIPPED_THROUGH_AS_TRUSTED":
            return "UNEXPECTED_SLIPPED_THROUGH"
        return "UNEXPECTED_OUTCOME_FOR_EXPECTATION"
    if expected == "KNOWN_CAPABILITY_EXCEPTION":
        if outcome == "SLIPPED_THROUGH_AS_TRUSTED":
            return "KNOWN_CAPABILITY_EXCEPTION_CONFIRMED"
        return "UNEXPECTED_OUTCOME_FOR_EXPECTATION"
    raise AssertionError(f"unreachable: unknown expectation {expected!r} for {fixture_name}")


def run_negative(fixture_name: str, stream_titles: dict[str, str]) -> dict:
    path = INVALID_DIR / fixture_name
    event = sender.load_fixture(path)

    # identity_violation_reused_event_id.json is INVALID only in
    # combination with tests/fixtures/valid/hermes_health_heartbeat_a.json
    # (same falcon_event_id, different payload/payload_hash) -- send the
    # paired valid fixture first, per MANIFEST.json.
    if fixture_name == "identity_violation_reused_event_id.json":
        paired = sender.load_fixture(VALID_DIR / "hermes_health_heartbeat_a.json")
        sender.send_gelf_tcp(
            sender.build_gelf_message(paired, host="falcon-fte-negative-pair", send_marker=uuid.uuid4().hex),
            gelf_host=GELF_HOST, gelf_port=GELF_PORT,
        )
        time.sleep(1.0)

    marker = uuid.uuid4().hex
    msg = sender.build_gelf_message(event, host="falcon-fte-negative", send_marker=marker)
    sender.send_gelf_tcp(msg, gelf_host=GELF_HOST, gelf_port=GELF_PORT)

    falcon_event_id = event.get("falcon_event_id")
    # fte_send_marker is unique per send, eliminating all ambiguity from
    # PID-01 fixtures that intentionally reuse the same falcon_event_id
    # across the valid/invalid corpus (structural mutations of one base
    # event) -- no query-based disambiguation heuristics needed.
    hit = find_message_by_query(f"fte_send_marker:{marker}")

    result = {"fixture": fixture_name, "falcon_event_id": falcon_event_id, "outcome": "NOT_FOUND_OR_DROPPED"}
    if hit is None:
        result["classification"] = _classify_negative_outcome(fixture_name, result["outcome"])
        return result

    full = fetch_full_message(hit["index"], hit["_id"])
    fields = full["fields"]
    stream_ids = full.get("stream_ids", [])
    stream_names = [stream_titles.get(sid, sid) for sid in stream_ids]
    result["falcon_validity"] = fields.get("falcon_validity")
    result["stream_ids"] = stream_ids
    result["stream_names"] = stream_names
    result["in_quarantine"] = "FALCON: Quarantine" in stream_names
    result["in_a_trusted_producer_stream"] = any(
        n.startswith("FALCON:") and n != "FALCON: Quarantine" for n in stream_names
    )
    if fields.get("falcon_validity") == "INVALID":
        result["outcome"] = "QUARANTINED"
    elif fields.get("falcon_validity") == "VALID" and result["in_a_trusted_producer_stream"]:
        result["outcome"] = "SLIPPED_THROUGH_AS_TRUSTED"
    else:
        result["outcome"] = "UNCLASSIFIED_DEFAULT_STREAM_ONLY"
    result["raw_fields"] = fields
    result["classification"] = _classify_negative_outcome(fixture_name, result["outcome"])
    return result


def run_malformed_transport_test() -> dict:
    """Send genuinely non-JSON bytes to the GELF TCP input and observe
    what happens (expected: Graylog's GELF codec discards/logs a parse
    error and no message is ever created -- not a FALCON-level check at
    all, this is Graylog's own transport-layer behaviour)."""
    marker = f"not-json-garbage-{time.time()}"
    try:
        sender.send_raw_tcp(marker.encode(), gelf_host=GELF_HOST, gelf_port=GELF_PORT)
        sent_ok = True
    except OSError as exc:
        return {"outcome": "CONNECTION_REJECTED", "detail": str(exc)}
    hit = find_message_by_query(f'message:"{marker}"', tries=5, delay=1.0)
    return {
        "outcome": "INDEXED_AS_MESSAGE" if hit else "NOT_INDEXED_DROPPED_BY_GELF_CODEC",
        "sent_ok": sent_ok,
        "hit": hit,
    }


def _pid04_lookup_indexed_message(marker: str) -> dict | None:
    hit = find_message_by_query(f"fte_send_marker:{marker}")
    if hit is None:
        return None
    return fetch_full_message(hit["index"], hit["_id"])


def pid04_run_valid_via_dedicated_input(producer: str, fixture_name: str) -> dict:
    """PID-04 valid-traffic regression: send a real PID-01 valid fixture
    over mTLS through `producer`'s own dedicated input, then run the exact
    same field-preservation / decimal-precision checks PID-03's own
    run_positive() already established -- proving the secured path is
    functionally identical to the old shared-input path for legitimate
    traffic, not just that "something got through"."""
    path = VALID_DIR / fixture_name
    event = sender.load_fixture(path)
    marker = uuid.uuid4().hex
    msg = sender.build_gelf_message(event, host=f"falcon-fte-pid04-{producer}", send_marker=marker)
    client_error = None
    try:
        sender.send_gelf_tcp_tls(
            msg,
            gelf_host=GELF_HOST,
            gelf_port=PID04_DEDICATED_PORTS[producer],
            client_cert=_pid04_client_cert(producer),
            client_key=_pid04_client_key(producer),
            server_ca=PID04_SERVER_CA,
        )
    except OSError as exc:
        # Recorded, but per the TLS-1.3-client-lies doctrine (see
        # sender.build_mtls_context's docstring) this is NOT the verdict --
        # only the lookup below is.
        client_error = f"{type(exc).__name__}: {exc}"

    result = {
        "producer": producer,
        "fixture": fixture_name,
        "falcon_event_id": event["falcon_event_id"],
        "client_side_send_error": client_error,
        "status": "FAIL",
    }
    full = _pid04_lookup_indexed_message(marker)
    if full is None:
        result["detail"] = "message never indexed within timeout"
        return result

    fields = full["fields"]
    checks = {
        "falcon_event_id_intact": fields.get("falcon_event_id") == event["falcon_event_id"],
        "producer_system_id_intact": fields.get("producer_system_id") == event["producer_system_id"],
        "evidence_family_intact": fields.get("evidence_family") == event["evidence_family"],
        "produced_at_utc_intact": fields.get("produced_at_utc") == event["produced_at_utc"],
        "falcon_ingested_at_utc_present": bool(fields.get("falcon_ingested_at_utc")),
        "falcon_validity_is_VALID": fields.get("falcon_validity") == "VALID",
        "falcon_identity_mismatch_absent_or_false": not fields.get("falcon_identity_mismatch", False),
        "gl2_source_input_present": bool(fields.get("gl2_source_input")),
    }
    if "producer_component_id" in event:
        checks["producer_component_id_intact"] = fields.get("producer_component_id") == event["producer_component_id"]

    decimal_checks = {}
    for key, value in event.get("payload", {}).items():
        if key.endswith("_decimal"):
            got = fields.get(f"payload_{key}")
            decimal_checks[key] = {
                "expected": value, "got": got, "got_python_type": type(got).__name__,
                "type_preserved_as_string": isinstance(got, str) and got == value,
            }
    checks["decimal_precision_preserved"] = (
        all(v["type_preserved_as_string"] for v in decimal_checks.values()) if decimal_checks else True
    )

    result["field_checks"] = checks
    result["decimal_field_detail"] = decimal_checks
    result["stream_ids"] = full.get("stream_ids", [])
    result["raw_fields"] = fields
    result["all_checks_passed"] = all(checks.values())
    result["status"] = "PASS" if result["all_checks_passed"] else "FAIL"
    return result


def pid04_run_identity_spoof(
    *,
    producer: str,
    base_fixture_dir: Path,
    base_fixture_name: str,
    override_producer_system_id: str | None = None,
    override_producer_component_id: str | None = None,
) -> dict:
    """PID-04 producer-spoofing / TRON-impersonation test (FF-PRODUCER-
    IDENTITY-01, FF-TRON-INGRESS-01): connect via `producer`'s OWN
    legitimate, authorised mTLS client certificate (the TLS/mTLS layer
    itself is deliberately kept correct here -- this test is specifically
    about the PAYLOAD-level claimed identity, isolated from the separately-
    proven TLS layer), but overwrite producer_system_id and/or
    producer_component_id in the message before sending to claim a
    different identity than the one this input is authorised for.

    Asserts: the message is preserved (never dropped), falcon_validity ==
    INVALID, falcon_identity_mismatch == true, falcon_security_reason is
    populated, the message lands ONLY in FALCON: Quarantine (never a
    trusted stream), AND -- the specific FF-PRODUCER-IDENTITY-01 invariant
    -- the indexed producer_system_id/producer_component_id fields still
    show the FALSE claimed value, proving FALCON never repaired/overwrote
    it back to the truth.
    """
    event = sender.load_fixture(base_fixture_dir / base_fixture_name)
    claimed_system = override_producer_system_id or event.get("producer_system_id")
    claimed_component = override_producer_component_id or event.get("producer_component_id")
    if override_producer_system_id:
        event["producer_system_id"] = override_producer_system_id
    if override_producer_component_id:
        event["producer_component_id"] = override_producer_component_id

    marker = uuid.uuid4().hex
    msg = sender.build_gelf_message(event, host=f"falcon-fte-pid04-spoof-{producer}", send_marker=marker)
    client_error = None
    try:
        sender.send_gelf_tcp_tls(
            msg,
            gelf_host=GELF_HOST,
            gelf_port=PID04_DEDICATED_PORTS[producer],
            client_cert=_pid04_client_cert(producer),
            client_key=_pid04_client_key(producer),
            server_ca=PID04_SERVER_CA,
        )
    except OSError as exc:
        client_error = f"{type(exc).__name__}: {exc}"

    result = {
        "scenario": f"{producer}-input claims system={claimed_system} component={claimed_component}",
        "falcon_event_id": event["falcon_event_id"],
        "client_side_send_error": client_error,
        "status": "FAIL",
    }
    full = _pid04_lookup_indexed_message(marker)
    if full is None:
        result["detail"] = "message never indexed within timeout (expected: indexed + quarantined, not dropped)"
        return result

    fields = full["fields"]
    stream_titles = load_stream_titles()
    stream_names = [stream_titles.get(sid, sid) for sid in full.get("stream_ids", [])]
    checks = {
        "falcon_validity_is_INVALID": fields.get("falcon_validity") == "INVALID",
        "falcon_identity_mismatch_true": fields.get("falcon_identity_mismatch") is True,
        "falcon_security_reason_present": bool(fields.get("falcon_security_reason")),
        "routed_to_quarantine_only": stream_names == ["FALCON: Quarantine"],
        "false_claim_preserved_not_overwritten": True,
    }
    if override_producer_system_id:
        checks["false_claim_preserved_not_overwritten"] = fields.get("producer_system_id") == override_producer_system_id
    if override_producer_component_id:
        checks["false_claim_preserved_not_overwritten"] = (
            checks["false_claim_preserved_not_overwritten"]
            and fields.get("producer_component_id") == override_producer_component_id
        )

    result["field_checks"] = checks
    result["stream_names"] = stream_names
    result["falcon_security_reason"] = fields.get("falcon_security_reason")
    result["raw_fields"] = fields
    result["all_checks_passed"] = all(checks.values())
    result["status"] = "PASS" if result["all_checks_passed"] else "FAIL"
    return result


def pid04_run_correct_identity_control(producer: str, fixture_name: str) -> dict:
    """Control case paired with pid04_run_identity_spoof: the SAME producer
    claiming its OWN correct identity over its OWN dedicated input must be
    accepted exactly as pid04_run_valid_via_dedicated_input already proves
    -- included again here, explicitly, so the spoof test's quarantine
    result cannot be dismissed as "everything on this input gets
    quarantined regardless"."""
    return pid04_run_valid_via_dedicated_input(producer, fixture_name)


def pid04_run_connection_level_test(scenario: str, producer: str) -> dict:
    """PID-04 TLS/mTLS connection-level negative tests: plaintext, no
    client cert, untrusted client cert. The client-side outcome recorded
    here is INFORMATIONAL ONLY -- per the discovery-phase finding
    (reproduced and reconfirmed locally against a throwaway openssl
    s_server during this delivery: a client's own "send completed without
    exception" was observed even when the server log showed a hard
    rejection in all three of these scenarios under TLS 1.3). The
    authoritative verdict for every one of these scenarios MUST come from
    `docker logs graylog-falcon` (expect a record-layer/handshake/
    certificate-verify error at the time of the attempt) AND a confirmed
    ABSENCE of any newly-indexed message for this marker -- both of which
    only Rogue's privileged access can check.
    """
    marker = f"pid04-conn-{scenario}-{producer}-{uuid.uuid4().hex}"
    dummy_msg = {"version": "1.1", "host": "should-never-be-indexed", "short_message": marker, "_fte_send_marker": marker}
    port = PID04_DEDICATED_PORTS[producer]
    client_result = None
    try:
        if scenario == "plaintext":
            sender.send_plaintext_to_tls_port(json.dumps(dummy_msg).encode() + b"\x00", gelf_host=GELF_HOST, gelf_port=port)
        elif scenario == "no_client_cert":
            sender.send_gelf_tcp_tls(dummy_msg, gelf_host=GELF_HOST, gelf_port=port, client_cert=None, client_key=None, server_ca=PID04_SERVER_CA)
        elif scenario == "untrusted_client_cert":
            # Deliberately use a DIFFERENT producer's real cert, which is
            # valid mTLS material but not in *this* input's own trust
            # directory -- proves per-input trust isolation, not just
            # "any self-signed cert is rejected".
            other = next(p for p in PID04_DEDICATED_PORTS if p != producer)
            sender.send_gelf_tcp_tls(dummy_msg, gelf_host=GELF_HOST, gelf_port=port, client_cert=_pid04_client_cert(other), client_key=_pid04_client_key(other), server_ca=PID04_SERVER_CA)
        else:
            raise ValueError(f"unknown scenario {scenario}")
        client_result = "send completed without a client-side exception (NOT proof of server-side acceptance -- see docstring)"
    except OSError as exc:
        client_result = f"client-side exception: {type(exc).__name__}: {exc}"

    hit = _pid04_lookup_indexed_message(marker)
    return {
        "scenario": scenario,
        "producer_input": producer,
        "marker": marker,
        "client_side_result": client_result,
        "message_indexed": hit is not None,
        "expected": "message_indexed must be False; docker logs graylog-falcon must show a rejection at this timestamp (verify manually per the PID-04 runbook)",
        "status": "NEEDS_ROGUE_SERVER_LOG_CONFIRMATION",
    }


def main_pid04() -> int:
    """PID-04 producer-connection-security suite. Requires the 5 dedicated
    mTLS inputs, the extended pipeline/rules, and the cert material at
    deploy/secrets/pid04-mtls/ to already be installed/present -- see the
    PID-04 runbook. Distinct from main() (PID-03 regression), run
    separately so a PID-03-only regression check never depends on PID-04
    being installed yet."""
    report: dict = {"generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}

    print("[pid04] valid-traffic regression via dedicated inputs ...")
    report["valid_via_dedicated_input"] = [
        pid04_run_valid_via_dedicated_input("hermes", "hermes_market_fact.json"),
        pid04_run_valid_via_dedicated_input("ares", "ares_calendar_event_state.json"),
        pid04_run_valid_via_dedicated_input("helios", "helios_strategy_trigger.json"),
        pid04_run_valid_via_dedicated_input("tron_execution_engine", "tron_fill.json"),
    ]

    print("[pid04] producer-spoofing scenarios ...")
    report["identity_spoof"] = [
        pid04_run_identity_spoof(
            producer="hermes", base_fixture_dir=VALID_DIR, base_fixture_name="hermes_market_fact.json",
            override_producer_system_id="helios",
        ),
        pid04_run_identity_spoof(
            producer="ares", base_fixture_dir=VALID_DIR, base_fixture_name="ares_calendar_event_state.json",
            override_producer_system_id="hermes",
        ),
        pid04_run_identity_spoof(
            producer="tron_execution_engine", base_fixture_dir=VALID_DIR, base_fixture_name="tron_fill.json",
            override_producer_component_id="tron.discovery_service",
        ),
        pid04_run_identity_spoof(
            producer="tron_discovery_service", base_fixture_dir=VALID_DIR, base_fixture_name="tron_fill.json",
            override_producer_component_id="tron.execution_engine",
        ),
    ]

    print("[pid04] correct-identity control cases (paired with the spoof tests above) ...")
    report["correct_identity_control"] = [
        pid04_run_correct_identity_control("tron_execution_engine", "tron_fill.json"),
        # NOT tron_fill.json here -- that fixture's producer_component_id is
        # "tron.execution_engine" (confirmed: tests/fixtures/valid/tron_fill.json
        # line 6), so sending it via the tron_discovery_service input is
        # itself a genuine identity mismatch, not a control case. Bug found
        # during Rogue's live step-6 run: the tron_discovery_service control
        # correctly failed (falcon_identity_mismatch fired as designed) but
        # for the wrong reason -- a test-fixture bug, not an enforcement bug.
        # Fixed by using tron_trigger_observed.json, whose
        # producer_component_id is genuinely "tron.discovery_service"
        # (confirmed: tests/fixtures/valid/tron_trigger_observed.json line 6;
        # tron_admission_decision.json also qualifies -- both were verified,
        # tron_trigger_observed.json was preferred since "discovery" and
        # "trigger observation" pair thematically).
        pid04_run_correct_identity_control("tron_discovery_service", "tron_trigger_observed.json"),
    ]

    print("[pid04] connection-level TLS/mTLS negative tests (client-side observation only -- see docstring) ...")
    report["connection_level"] = [
        pid04_run_connection_level_test("plaintext", "hermes"),
        pid04_run_connection_level_test("no_client_cert", "hermes"),
        pid04_run_connection_level_test("untrusted_client_cert", "hermes"),
    ]

    print("\n=== PID-04 REPORT ===")
    print(json.dumps(report, indent=2, default=str))

    valid_pass = sum(1 for r in report["valid_via_dedicated_input"] if r["status"] == "PASS")
    spoof_pass = sum(1 for r in report["identity_spoof"] if r["status"] == "PASS")
    control_pass = sum(1 for r in report["correct_identity_control"] if r["status"] == "PASS")

    print(f"\nValid-via-dedicated-input: {valid_pass}/{len(report['valid_via_dedicated_input'])} PASS")
    print(f"Identity spoof (must all quarantine + preserve false claim): {spoof_pass}/{len(report['identity_spoof'])} PASS")
    print(f"Correct-identity controls (must all accept normally): {control_pass}/{len(report['correct_identity_control'])} PASS")
    print("Connection-level tests: NOT auto-verdicted -- see each result's 'expected' field; confirm manually via docker logs + search API per the runbook.")

    out_path = REPO_ROOT / "tests" / "fte" / "last_run_report_pid04.json"
    try:
        with open(out_path, "w") as f:
            json.dump(report, f, indent=2, default=str)
        print(f"\nFull PID-04 report written to {out_path}")
    except OSError as exc:
        print(f"\n(report file not written: {exc} -- full report is in stdout above)")

    all_auto_verdicted_ok = (
        valid_pass == len(report["valid_via_dedicated_input"])
        and spoof_pass == len(report["identity_spoof"])
        and control_pass == len(report["correct_identity_control"])
    )
    return 0 if all_auto_verdicted_ok else 1


def main() -> int:
    report = {"positive": [], "negative": [], "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}

    positive_fixtures = [
        "hermes_market_fact.json",
        "ares_calendar_event_state.json",
        "helios_strategy_trigger.json",
        "tron_fill.json",
    ]
    for fixture_name in positive_fixtures:
        print(f"[positive] sending {fixture_name} ...")
        report["positive"].append(run_positive(fixture_name))

    stream_titles = load_stream_titles()
    negative_cases = [f.name for f in sorted(INVALID_DIR.glob("*.json")) if f.name != "MANIFEST.json"]
    for fixture_name in negative_cases:
        print(f"[negative] sending {fixture_name} ...")
        report["negative"].append(run_negative(fixture_name, stream_titles))
        time.sleep(0.3)

    print("[transport] sending malformed non-JSON payload ...")
    report["malformed_transport"] = run_malformed_transport_test()

    print("\n=== REPORT ===")
    print(json.dumps(report, indent=2, default=str))

    pos_pass = sum(1 for r in report["positive"] if r["status"] == "PASS")

    expected_quarantined = [r["fixture"] for r in report["negative"] if r["classification"] == "EXPECTED_QUARANTINED"]
    known_exceptions_confirmed = [r["fixture"] for r in report["negative"] if r["classification"] == "KNOWN_CAPABILITY_EXCEPTION_CONFIRMED"]
    unexpected_slipped_through = [r["fixture"] for r in report["negative"] if r["classification"] == "UNEXPECTED_SLIPPED_THROUGH"]
    unclassified_fixtures = [r["fixture"] for r in report["negative"] if r["classification"] == "UNCLASSIFIED_FIXTURE"]
    unexpected_other = [r["fixture"] for r in report["negative"] if r["classification"] == "UNEXPECTED_OUTCOME_FOR_EXPECTATION"]

    # Every negative fixture must fall into exactly one of the two
    # PASSING categories. Anything else -- including a fixture this
    # suite doesn't even recognise -- fails the run. This is what makes
    # "return 0" actually mean the load-bearing invariant held, not just
    # that the four positive fixtures worked.
    neg_ok = (len(expected_quarantined) + len(known_exceptions_confirmed)) == len(report["negative"])

    report["negative_summary"] = {
        "expected_quarantined": expected_quarantined,
        "known_capability_exceptions_confirmed": known_exceptions_confirmed,
        "unexpected_slipped_through_INVARIANT_VIOLATION": unexpected_slipped_through,
        "unclassified_fixtures_missing_from_expectation_map": unclassified_fixtures,
        "unexpected_outcome_for_declared_expectation": unexpected_other,
        "all_negative_fixtures_accounted_for_and_ok": neg_ok,
    }

    print(f"\nPositive: {pos_pass}/{len(report['positive'])} PASS")
    print(f"Negative: {len(report['negative'])} fixtures sent")
    print(f"  expected-quarantined, confirmed:            {len(expected_quarantined)}  {expected_quarantined}")
    print(f"  known capability exceptions, confirmed:      {len(known_exceptions_confirmed)}  {known_exceptions_confirmed}")
    print(f"  UNEXPECTED slipped-through (INVARIANT VIOLATION): {len(unexpected_slipped_through)}  {unexpected_slipped_through}")
    print(f"  unclassified (missing from expectation map): {len(unclassified_fixtures)}  {unclassified_fixtures}")
    print(f"  unexpected outcome for its own expectation:  {len(unexpected_other)}  {unexpected_other}")
    print(f"  negative suite result: {'OK' if neg_ok else 'FAIL'}")

    out_path = REPO_ROOT / "tests" / "fte" / "last_run_report.json"
    try:
        with open(out_path, "w") as f:
            json.dump(report, f, indent=2, default=str)
        print(f"\nFull report written to {out_path}")
    except OSError as exc:
        # The repo is often mounted read-only when this runs from a
        # disposable container (see this file's own docstring usage
        # example) -- the report is already on stdout above, so a
        # failure to also persist it to disk must not mask the real
        # positive/negative test outcome in the exit code.
        print(f"\n(report file not written: {exc} -- full report is in stdout above)")
    return 0 if (pos_pass == len(report["positive"]) and neg_ok) else 1


if __name__ == "__main__":
    # Backward compatible: no args (or "pid03") runs exactly the original
    # PID-03 suite unchanged, against the shared input, for regression
    # proof. RETIRED as of PID-04 rev 3 (FF-LEGACY-INGRESS-01): that
    # input no longer exists in the authoritative reconstructed runtime,
    # so this mode now only works against a historical/pre-rev-3
    # environment; kept for PID-03 historical-proof reproducibility, not
    # deleted. "pid04" runs the dedicated-input/mTLS/identity suite
    # (requires PID-04's inputs+pipeline+certs to already be installed)
    # -- THIS is the current ingestion regression authority. "all" runs
    # both, PID-03 first (will fail its connection step on a
    # correctly-reconstructed rev-3-or-later environment -- expected).
    suite = sys.argv[1] if len(sys.argv) > 1 else "pid03"
    if suite == "pid03":
        raise SystemExit(main())
    elif suite == "pid04":
        raise SystemExit(main_pid04())
    elif suite == "all":
        pid03_rc = main()
        pid04_rc = main_pid04()
        raise SystemExit(pid03_rc or pid04_rc)
    else:
        raise SystemExit(f"FATAL: unknown suite '{suite}' -- expected pid03, pid04 or all")
