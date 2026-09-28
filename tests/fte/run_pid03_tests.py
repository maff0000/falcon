"""
FALCON PID-03 -- automated positive/negative ingestion proof suite.

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
    raise SystemExit(main())
