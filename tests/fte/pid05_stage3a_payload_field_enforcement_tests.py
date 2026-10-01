"""FALCON PID-05 Stage 3A -- payload-field-enforcement contract proof suite.

Exercises the new "FALCON - flag missing required payload fields"
pipeline rule end to end, against the real DEV stack, through HERMES's
own real PID-04 dedicated mTLS input. Reuses this project's existing,
already-proven FTE conventions throughout -- this file does not
reimplement sender.py's GELF/mTLS plumbing or
pid05_stage1_signal_state_tests.py's ApiClient/signal-state event
builder; it imports and reuses them directly (same reuse pattern
pid05_stage1_signal_state_tests.py itself already established for
pid05_size_probe.py's build_realistic_payload_json()).

Root cause under test (see pids/PID-05-HERMES-INTEGRATION.md's "MAJOR
FINDING" under Stage 1 live verification, and its "Stage 3A" section):
the live pipeline's "FALCON - flag missing required fields" rule only
ever checked 6 hardcoded ENVELOPE fields. It never checked any family's
own `required_payload_fields` (registry/event_family_registry.v1.json)
at the payload level -- a universal, pre-existing gap, not specific to
HERMES or to any one family. The new rule this suite proves is
generated deterministically from the registry by
deploy/generate_payload_requirements_rule.py (see
tests/test_generated_payload_requirements_rule.py for the offline CI
drift guard) and wired into stage 2's quarantine router and all 6
"route valid <X> evidence" rules.

*** ISOLATED-TEST-FIRST BOUNDARY ***
--stream-name and --quarantine-stream-name default to the REAL
production stream names ("FALCON: HERMES evidence" / "FALCON:
Quarantine") because that is what the approved, committed content-pack
rev 5 actually routes to -- but per this project's own established
precedent (pid05_stage1_signal_state_tests.py), Rogue should run this
FIRST against an isolated test setup (disposable index-set/stream/
pipeline, mirroring the binary-field proof's pattern), overriding these
two arguments to the isolated stream names, before ever pointing this
suite at the real falcon-evidence_0 index. Nothing in this script
assumes which one you're pointed at.

This delivery does not execute this suite itself (same credential/
live-execution boundary upheld throughout PID-04/PID-05) -- Rogue runs
it, with real credentials this script never holds or requests.

Usage:
    python3 tests/fte/pid05_stage3a_payload_field_enforcement_tests.py \\
        --gelf-host graylog-falcon --gelf-port 12411 \\
        --client-cert deploy/secrets/pid04-mtls/clients/hermes.crt \\
        --client-key deploy/secrets/pid04-mtls/clients/hermes.key \\
        --server-ca deploy/secrets/pid04-mtls/server/server.crt \\
        --graylog-api-base http://192.168.11.10:9010/api \\
        --graylog-user admin --graylog-password <password> \\
        --stream-name "PID-05 Stage 3A Isolated Test Stream" \\
        --quarantine-stream-name "PID-05 Stage 3A Isolated Test Stream"
"""
from __future__ import annotations

import argparse
import base64
import copy
import importlib
import json
import sys
import uuid
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sender  # noqa: E402

# Reused directly, never re-implemented: ApiClient (search-by-marker over
# the real Graylog API), build_signal_state_event(), load_fixture(),
# send_event(), and the hermes.signal_state binary-field field-name
# convention (RAW_PAYLOAD_FIELD / ENCODED_FIELD).
stage1 = importlib.import_module("pid05_stage1_signal_state_tests")

REPO_ROOT = Path(__file__).resolve().parents[2]
VALID_DIR = REPO_ROOT / "tests" / "fixtures" / "valid"
INVALID_DIR = REPO_ROOT / "tests" / "fixtures" / "invalid"

NEW_FLAG = "falcon_missing_required_payload_field"


def build_market_fact_event(*, marker: str, omit_fields: tuple[str, ...] = ()) -> dict[str, Any]:
    """Builds a real hermes.market_fact FalconEvent, starting from the
    committed valid fixture (never fabricated ad hoc) and optionally
    stripping named payload fields -- used to prove the new rule covers
    an *existing* family, not just the new hermes.signal_state one."""
    base = copy.deepcopy(stage1.load_fixture(VALID_DIR / "hermes_market_fact.json"))
    base["falcon_event_id"] = str(uuid.uuid5(uuid.NAMESPACE_URL, f"pid05-stage3a-test:{marker}"))
    payload = dict(base["payload"])
    for field_name in omit_fields:
        payload.pop(field_name, None)
    base["payload"] = payload
    return base


def run_all(args) -> int:
    api = stage1.ApiClient(args.graylog_api_base, args.graylog_user, args.graylog_password)
    conn = dict(gelf_host=args.gelf_host, gelf_port=args.gelf_port,
                client_cert=args.client_cert, client_key=args.client_key, server_ca=args.server_ca)
    results: list[tuple[str, bool, str]] = []

    def record(name: str, ok: bool, detail: str = "") -> None:
        results.append((name, ok, detail))
        print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f" -- {detail}" if detail else ""))

    stream_titles = api.stream_titles()

    def stream_names_for(msg: dict | None) -> list[str]:
        if msg is None:
            return []
        return [stream_titles.get(sid, sid) for sid in msg.get("stream_ids", [])]

    # 1. hermes.signal_state valid (signal_natural_key present) -> VALID,
    #    and the new flag correctly absent/false.
    marker1 = uuid.uuid4().hex
    event1 = stage1.build_signal_state_event(marker=marker1)
    stage1.send_event(event1, marker1, host="falcon-fte-pid05-stage3a", extra_fields=None, **conn)
    msg1 = api.find_by_marker(marker1)
    if msg1 is None:
        record("hermes.signal_state valid (signal_natural_key present) -> VALID", False, "never indexed")
    else:
        f1 = msg1["fields"]
        ok1 = f1.get("falcon_validity") == "VALID" and not f1.get(NEW_FLAG, False)
        record("hermes.signal_state valid (signal_natural_key present) -> VALID", ok1, json.dumps(f1, default=str)[:200])

    # 2. hermes.signal_state missing signal_natural_key (the PID-05-new
    #    family's only required payload field) -> NOT VALID, quarantine,
    #    with the new flag set.
    marker2 = uuid.uuid4().hex
    invalid_signal_event = stage1.load_fixture(INVALID_DIR / "missing_signal_natural_key.json")
    stage1.send_event(invalid_signal_event, marker2, host="falcon-fte-pid05-stage3a-negative",
                       extra_fields={"_fte_send_marker": marker2}, **conn)
    msg2 = api.find_by_marker(marker2)
    if msg2 is None:
        record("hermes.signal_state missing signal_natural_key -> quarantined", False, "never indexed")
    else:
        f2 = msg2["fields"]
        names2 = stream_names_for(msg2)
        ok2 = (
            f2.get("falcon_validity") == "INVALID"
            and f2.get(NEW_FLAG) is True
            and args.quarantine_stream_name in names2
        )
        record("hermes.signal_state missing signal_natural_key -> quarantined", ok2,
               f"validity={f2.get('falcon_validity')} {NEW_FLAG}={f2.get(NEW_FLAG)} streams={names2}")

    # 3. hermes.signal_state valid with signal_natural_key present but every
    #    OPTIONAL field (regime/session/instrument_id/timeframe/signal_type)
    #    absent -> still VALID. Optional-field regression: the new rule
    #    must never treat an optional field as required.
    marker3 = uuid.uuid4().hex
    event3 = stage1.build_signal_state_event(
        marker=marker3, instrument_id=None, timeframe=None, regime=None, session=None, signal_type=None,
    )
    stage1.send_event(event3, marker3, host="falcon-fte-pid05-stage3a-optional", extra_fields=None, **conn)
    msg3 = api.find_by_marker(marker3)
    if msg3 is None:
        record("hermes.signal_state valid with all optional fields absent -> still VALID", False, "never indexed")
    else:
        f3 = msg3["fields"]
        ok3 = f3.get("falcon_validity") == "VALID" and not f3.get(NEW_FLAG, False)
        record("hermes.signal_state valid with all optional fields absent -> still VALID", ok3,
               json.dumps(f3, default=str)[:200])

    # 4. hermes.market_fact (pre-existing family, not touched by PID-05)
    #    missing one of its own registered required payload fields
    #    (fact_id) -> NOT VALID, quarantine. Proves the gap-fix is
    #    universal, not HERMES/PID-05-signal_state-specific.
    marker4 = uuid.uuid4().hex
    event4 = build_market_fact_event(marker=marker4, omit_fields=("fact_id",))
    stage1.send_event(event4, marker4, host="falcon-fte-pid05-stage3a-marketfact-negative",
                       extra_fields={"_fte_send_marker": marker4}, **conn)
    msg4 = api.find_by_marker(marker4)
    if msg4 is None:
        record("hermes.market_fact missing fact_id -> quarantined (existing-family regression)", False, "never indexed")
    else:
        f4 = msg4["fields"]
        names4 = stream_names_for(msg4)
        ok4 = (
            f4.get("falcon_validity") == "INVALID"
            and f4.get(NEW_FLAG) is True
            and args.quarantine_stream_name in names4
        )
        record("hermes.market_fact missing fact_id -> quarantined (existing-family regression)", ok4,
               f"validity={f4.get('falcon_validity')} {NEW_FLAG}={f4.get(NEW_FLAG)} streams={names4}")

    # 4b. Control for #4: the SAME family, fully valid (all required
    #     fields present) -> VALID. Proves #4's rejection is specifically
    #     about the missing field, not a blanket market_fact regression.
    marker4b = uuid.uuid4().hex
    event4b = build_market_fact_event(marker=marker4b, omit_fields=())
    stage1.send_event(event4b, marker4b, host="falcon-fte-pid05-stage3a-marketfact-control",
                       extra_fields={"_fte_send_marker": marker4b}, **conn)
    msg4b = api.find_by_marker(marker4b)
    if msg4b is None:
        record("hermes.market_fact fully valid -> VALID (control for #4)", False, "never indexed")
    else:
        f4b = msg4b["fields"]
        names4b = stream_names_for(msg4b)
        ok4b = f4b.get("falcon_validity") == "VALID" and not f4b.get(NEW_FLAG, False) and args.stream_name in names4b
        record("hermes.market_fact fully valid -> VALID (control for #4)", ok4b,
               f"validity={f4b.get('falcon_validity')} streams={names4b}")

    # 5. Envelope regression: a compulsory ENVELOPE field (produced_at_utc)
    #    missing remains invalid via the pre-existing envelope rule,
    #    unchanged by and independent of the new payload-level rule.
    marker5 = uuid.uuid4().hex
    event5 = build_market_fact_event(marker=marker5, omit_fields=())
    del event5["produced_at_utc"]
    stage1.send_event(event5, marker5, host="falcon-fte-pid05-stage3a-envelope-negative",
                       extra_fields={"_fte_send_marker": marker5}, **conn)
    msg5 = api.find_by_marker(marker5)
    if msg5 is None:
        record("missing envelope field (produced_at_utc) -> still quarantined (envelope regression)", False, "never indexed")
    else:
        f5 = msg5["fields"]
        names5 = stream_names_for(msg5)
        ok5 = (
            f5.get("falcon_validity") == "INVALID"
            and f5.get("falcon_missing_required_field") is True
            and args.quarantine_stream_name in names5
        )
        record("missing envelope field (produced_at_utc) -> still quarantined (envelope regression)", ok5,
               f"validity={f5.get('falcon_validity')} falcon_missing_required_field={f5.get('falcon_missing_required_field')} streams={names5}")

    # 6. Producer identity (PID-04) regression: a spoofed producer_system_id
    #    claim (legitimate HERMES mTLS cert, false claim) is still
    #    quarantined via falcon_identity_mismatch, unaffected by the new
    #    rule -- reuses the exact spoof pattern already proven in
    #    pid05_stage1_signal_state_tests.py (and, before that, PID-04).
    marker6 = uuid.uuid4().hex
    spoof_event = stage1.build_signal_state_event(marker=marker6)
    spoof_event["producer_system_id"] = "ares"
    stage1.send_event(spoof_event, marker6, host="falcon-fte-pid05-stage3a-spoof", extra_fields=None, **conn)
    msg6 = api.find_by_marker(marker6)
    if msg6 is None:
        record("spoofed producer identity -> still quarantined (PID-04 regression)", False, "never indexed")
    else:
        f6 = msg6["fields"]
        names6 = stream_names_for(msg6)
        ok6 = (
            f6.get("falcon_identity_mismatch") is True
            and f6.get("producer_system_id") == "ares"
            and args.quarantine_stream_name in names6
        )
        record("spoofed producer identity -> still quarantined (PID-04 regression)", ok6,
               f"identity_mismatch={f6.get('falcon_identity_mismatch')} claimed={f6.get('producer_system_id')} streams={names6}")

    # 7. Large-payload regression: the existing HERMES binary-field
    #    mechanism (hermes_signal_raw_json -> base64 ->
    #    hermes_signal_original_payload, with remove_field()) still works
    #    unaffected -- the new rule only inspects payload_* fields
    #    (stage-0-derived from the structured JSON payload), never the
    #    raw/binary field, so it must never evaluate or care about it.
    marker7 = uuid.uuid4().hex
    raw_payload = {
        "instrument": "XAUUSD", "timeframe": "M5", "rsi_14": 58.1, "atr_14": 2.97,
        "regime": "BULL_TREND", "ema_9": 3881.4, "ema_21": 3874.2,
        "note": "synthetic PID-05 Stage 3A test payload, never real HERMES data",
    }
    event7 = stage1.build_signal_state_event(marker=marker7)
    raw_json_str = json.dumps(raw_payload, separators=(",", ":"))
    stage1.send_event(event7, marker7, host="falcon-fte-pid05-stage3a-binary",
                       extra_fields={stage1.RAW_PAYLOAD_FIELD: raw_json_str}, **conn)
    msg7 = api.find_by_marker(marker7)
    if msg7 is None:
        record("binary-field mechanism unaffected by new rule (large-payload regression)", False, "never indexed")
    else:
        f7 = msg7["fields"]
        encoded = f7.get(stage1.ENCODED_FIELD)
        original_field_gone = "hermes_signal_raw_json" not in f7
        roundtrip_ok = False
        if encoded:
            try:
                roundtrip_ok = base64.b64decode(encoded).decode("utf-8") == raw_json_str
            except Exception:
                roundtrip_ok = False
        ok7 = (
            f7.get("falcon_validity") == "VALID"
            and not f7.get(NEW_FLAG, False)
            and bool(encoded)
            and roundtrip_ok
            and original_field_gone
        )
        record("binary-field mechanism unaffected by new rule (large-payload regression)", ok7,
               f"validity={f7.get('falcon_validity')} {NEW_FLAG}={f7.get(NEW_FLAG)} "
               f"encoded_present={bool(encoded)} roundtrip_exact={roundtrip_ok} original_field_removed={original_field_gone}")

    print("\n=== Summary ===")
    passed = sum(1 for _, ok, _ in results if ok)
    for name, ok, _detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
    print(f"\n{passed}/{len(results)} passed")
    print("\nReminder: confirm IRIS (graylog/graylog-mongo/graylog-elasticsearch) unaffected "
          "before and after this run -- this script does not check that itself.")
    return 0 if passed == len(results) else 1


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--gelf-host", required=True)
    p.add_argument("--gelf-port", type=int, required=True)
    p.add_argument("--client-cert", type=Path, required=True)
    p.add_argument("--client-key", type=Path, required=True)
    p.add_argument("--server-ca", type=Path, required=True)
    p.add_argument("--graylog-api-base", required=True)
    p.add_argument("--graylog-user", required=True)
    p.add_argument("--graylog-password", required=True)
    p.add_argument("--stream-name", default="FALCON: HERMES evidence",
                    help="Expected stream for a VALID hermes event (both hermes.signal_state and "
                         "hermes.market_fact route here). Override to your isolated test stream name "
                         "when running against an isolated setup (recommended first).")
    p.add_argument("--quarantine-stream-name", default="FALCON: Quarantine",
                    help="Expected stream for an INVALID/spoofed event. Override for isolated testing.")
    args = p.parse_args()
    return run_all(args)


if __name__ == "__main__":
    raise SystemExit(main())
