"""FALCON PID-05 Stage 1 -- hermes.signal_state contract proof suite.

Exercises the new hermes.signal_state event family / hermes.signal_engine
producer component end to end, against the real DEV stack, through
HERMES's own real PID-04 dedicated mTLS input. Reuses this project's
existing, already-proven FTE conventions throughout (sender.py's
send_gelf_tcp_tls/build_gelf_message, the unique _fte_send_marker
pattern, the TLS-1.3-client-lies discipline of never trusting a
client-side send result alone) -- this is explicitly NOT a fresh
capacity-research pass; the 16/64/256/512 KiB checks here are a
functional regression confirmation that this NEW family's payload shape
behaves the same way the already-proven binary-field mechanism does,
not a re-run of PID-05's own discovery-phase capacity investigation.

*** ISOLATED-TEST-FIRST BOUNDARY ***
--stream-name and --quarantine-stream-name default to the REAL
production stream names ("FALCON: HERMES evidence" / "FALCON:
Quarantine") because that is what the approved, committed pipeline
change actually routes to -- but per the Architect's own instruction,
Rogue should run this FIRST against an isolated test setup (mirroring
the binary-field proof's disposable index-set/stream/pipeline pattern),
overriding these two arguments to the isolated stream names, before ever
pointing this suite at the real falcon-evidence_0 index. Nothing in this
script assumes which one you're pointed at; it is your responsibility to
choose deliberately via the CLI arguments below, not a hidden default
behaviour of this script.

This delivery does not execute this suite itself (same credential/
live-execution boundary upheld throughout PID-04/PID-05) -- Rogue runs
it.

Usage:
    python3 tests/fte/pid05_stage1_signal_state_tests.py \\
        --gelf-host graylog-falcon --gelf-port 12411 \\
        --client-cert deploy/secrets/pid04-mtls/clients/hermes.crt \\
        --client-key deploy/secrets/pid04-mtls/clients/hermes.key \\
        --server-ca deploy/secrets/pid04-mtls/server/server.crt \\
        --graylog-api-base http://192.168.11.10:9010/api \\
        --graylog-user admin --graylog-password <password> \\
        --stream-name "PID-05 Stage 1 Isolated Test Stream" \\
        --quarantine-stream-name "PID-05 Stage 1 Isolated Test Stream"
"""
from __future__ import annotations

import argparse
import base64
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sender  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
VALID_DIR = REPO_ROOT / "tests" / "fixtures" / "valid"
INVALID_DIR = REPO_ROOT / "tests" / "fixtures" / "invalid"

# The GELF-wire field naming convention this PID's committed pipeline
# change expects (see the "FALCON - encode hermes signal raw payload to
# binary field" rule): the producer sends the full raw signal JSON as
# additional field _hermes_signal_raw_json; Graylog strips the leading
# underscore on receipt (already-documented PID-03 convention); the
# pipeline base64_encode()s it into hermes_signal_original_payload and
# remove_field()s the original.
RAW_PAYLOAD_FIELD = "_hermes_signal_raw_json"
ENCODED_FIELD = "hermes_signal_original_payload"


class ApiClient:
    def __init__(self, api_base: str, user: str, password: str):
        self.api_base = api_base.rstrip("/")
        self._auth = base64.b64encode(f"{user}:{password}".encode()).decode()

    def get(self, path: str) -> dict:
        req = urllib.request.Request(f"{self.api_base}{path}")
        req.add_header("Authorization", f"Basic {self._auth}")
        req.add_header("X-Requested-By", "pid05-stage1-tests")
        req.add_header("Accept", "application/json")
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())

    def stream_titles(self) -> dict[str, str]:
        data = self.get("/streams")
        return {s["id"]: s["title"] for s in data["streams"]}

    def find_by_marker(self, marker: str, *, tries: int = 15, delay: float = 1.0) -> dict | None:
        for _ in range(tries):
            try:
                result = self.get(
                    f"/search/universal/relative?query={urllib.parse.quote('fte_send_marker:' + marker)}"
                    f"&range=120&limit=5&fields=message"
                )
            except urllib.error.URLError:
                result = {"messages": []}
            if result.get("messages"):
                entry = result["messages"][0]
                return self.get(f"/messages/{entry['index']}/{entry['message']['_id']}")["message"]
            time.sleep(delay)
        return None


def load_fixture(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def build_signal_state_event(
    *,
    marker: str,
    instrument_id: str | None = "XAUUSD",
    timeframe: str | None = "M5",
    regime: str | None = "BULL_TREND",
    session: str | None = "london",
    signal_type: str | None = "indicator_regime_snapshot",
) -> dict[str, Any]:
    """Builds a real hermes.signal_state FalconEvent, starting from the
    committed valid fixture (never fabricated ad hoc) and overriding only
    the optional searchable fields under test -- None means "omit this
    optional field entirely", never "send an empty/default value"."""
    base = load_fixture(VALID_DIR / "hermes_signal_state.json")
    base["falcon_event_id"] = str(uuid.uuid5(uuid.NAMESPACE_URL, f"pid05-test:{marker}"))
    payload = dict(base["payload"])
    for key, value in (
        ("instrument_id", instrument_id),
        ("timeframe", timeframe),
        ("regime", regime),
        ("session", session),
        ("signal_type", signal_type),
    ):
        if value is None:
            payload.pop(key, None)
        else:
            payload[key] = value
    base["payload"] = payload
    return base


def send_event(event: dict, marker: str, *, host: str, extra_fields: dict | None, gelf_host: str, gelf_port: int,
                client_cert: Path, client_key: Path, server_ca: Path) -> str | None:
    msg = sender.build_gelf_message(event, host=host, send_marker=marker)
    if extra_fields:
        msg.update(extra_fields)
    try:
        sender.send_gelf_tcp_tls(msg, gelf_host=gelf_host, gelf_port=gelf_port,
                                  client_cert=client_cert, client_key=client_key, server_ca=server_ca)
        return None
    except OSError as exc:
        return f"{type(exc).__name__}: {exc}"


def run_all(args) -> int:
    api = ApiClient(args.graylog_api_base, args.graylog_user, args.graylog_password)
    conn = dict(gelf_host=args.gelf_host, gelf_port=args.gelf_port,
                client_cert=args.client_cert, client_key=args.client_key, server_ca=args.server_ca)
    results: list[tuple[str, bool, str]] = []

    def record(name: str, ok: bool, detail: str = "") -> None:
        results.append((name, ok, detail))
        print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f" -- {detail}" if detail else ""))

    stream_titles = api.stream_titles()

    # 1. Valid signal accepted, correct family/producer identity, instrument/timeframe searchable.
    marker = uuid.uuid4().hex
    event = build_signal_state_event(marker=marker)
    err = send_event(event, marker, host="falcon-fte-pid05-stage1", extra_fields=None, **conn)
    msg = api.find_by_marker(marker)
    if msg is None:
        record("valid signal accepted and indexed", False, f"never indexed (client err: {err})")
    else:
        f = msg["fields"]
        ok = (
            f.get("falcon_validity") == "VALID"
            and f.get("producer_system_id") == "hermes"
            and f.get("producer_component_id") == "hermes.signal_engine"
            and f.get("evidence_family") == "hermes.signal_state"
            and f.get("payload_instrument_id") == "XAUUSD"
            and f.get("payload_timeframe") == "M5"
        )
        record("valid signal accepted, correct identity, instrument/timeframe searchable", ok, json.dumps(f, default=str)[:300])
        names = [stream_titles.get(sid, sid) for sid in msg.get("stream_ids", [])]
        record("routed to FALCON: HERMES evidence (reused stream)", args.stream_name in names, str(names))

    # 2. Optional regime/session searchable when supplied.
    marker2 = uuid.uuid4().hex
    event2 = build_signal_state_event(marker=marker2, regime="TRANSITION", session="newyork")
    send_event(event2, marker2, host="falcon-fte-pid05-stage1", extra_fields=None, **conn)
    msg2 = api.find_by_marker(marker2)
    if msg2 is None:
        record("regime/session searchable when supplied", False, "never indexed")
    else:
        f2 = msg2["fields"]
        record("regime/session searchable when supplied", f2.get("payload_regime") == "TRANSITION" and f2.get("payload_session") == "newyork", json.dumps(f2, default=str)[:200])

    # 3. Missing optional context (regime/session/signal_type/timeframe/instrument_id all omitted) accepted, not rejected.
    marker3 = uuid.uuid4().hex
    event3 = build_signal_state_event(marker=marker3, instrument_id=None, timeframe=None, regime=None, session=None, signal_type=None)
    send_event(event3, marker3, host="falcon-fte-pid05-stage1", extra_fields=None, **conn)
    msg3 = api.find_by_marker(marker3)
    if msg3 is None:
        record("missing optional context accepted (not rejected)", False, "never indexed -- optional-field omission must never cause rejection")
    else:
        record("missing optional context accepted (not rejected)", msg3["fields"].get("falcon_validity") == "VALID", json.dumps(msg3["fields"], default=str)[:200])

    # 4. Missing mandatory payload identity field (signal_natural_key) rejected/quarantined per existing policy.
    marker4 = uuid.uuid4().hex
    invalid_event = load_fixture(INVALID_DIR / "missing_signal_natural_key.json")
    send_event(invalid_event, marker4, host="falcon-fte-pid05-stage1-negative", extra_fields={"_fte_send_marker": marker4}, **conn)
    msg4 = api.find_by_marker(marker4)
    if msg4 is None:
        record("missing mandatory payload identity field quarantined", False, "expected quarantine, message never indexed at all")
    else:
        f4 = msg4["fields"]
        names4 = [stream_titles.get(sid, sid) for sid in msg4.get("stream_ids", [])]
        record(
            "missing mandatory payload identity field quarantined",
            f4.get("falcon_validity") == "INVALID" and args.quarantine_stream_name in names4,
            f"validity={f4.get('falcon_validity')} streams={names4}",
        )

    # 5. Spoofed producer identity quarantined (reuses the PID-04 spoof-test pattern: legitimate
    #    mTLS cert for HERMES's own dedicated input, but the message CLAIMS a different producer_system_id).
    marker5 = uuid.uuid4().hex
    spoof_event = build_signal_state_event(marker=marker5)
    spoof_event["producer_system_id"] = "ares"
    send_event(spoof_event, marker5, host="falcon-fte-pid05-stage1-spoof", extra_fields=None, **conn)
    msg5 = api.find_by_marker(marker5)
    if msg5 is None:
        record("spoofed producer identity quarantined", False, "expected quarantine, message never indexed at all")
    else:
        f5 = msg5["fields"]
        names5 = [stream_titles.get(sid, sid) for sid in msg5.get("stream_ids", [])]
        record(
            "spoofed producer identity quarantined, false claim preserved",
            f5.get("falcon_identity_mismatch") is True and f5.get("producer_system_id") == "ares" and args.quarantine_stream_name in names5,
            f"identity_mismatch={f5.get('falcon_identity_mismatch')} claimed={f5.get('producer_system_id')} streams={names5}",
        )

    # 6. Complete original JSON preserved via the binary-field mechanism; base64 round-trip exact.
    raw_payload = {
        "instrument": "XAUUSD", "timeframe": "M5", "rsi_14": 62.4, "atr_14": 3.21,
        "regime": "BULL_TREND", "ema_9": 3871.2, "ema_21": 3865.8,
        "note": "synthetic PID-05 Stage 1 test payload, never real HERMES data",
    }
    marker6 = uuid.uuid4().hex
    event6 = build_signal_state_event(marker=marker6)
    raw_json_str = json.dumps(raw_payload, separators=(",", ":"))
    send_event(event6, marker6, host="falcon-fte-pid05-stage1-binary", extra_fields={RAW_PAYLOAD_FIELD: raw_json_str}, **conn)
    msg6 = api.find_by_marker(marker6)
    if msg6 is None:
        record("original JSON preserved via binary field, base64 round-trip exact", False, "never indexed")
    else:
        f6 = msg6["fields"]
        encoded = f6.get(ENCODED_FIELD)
        original_field_gone = "hermes_signal_raw_json" not in f6
        roundtrip_ok = False
        if encoded:
            try:
                decoded = base64.b64decode(encoded).decode("utf-8")
                roundtrip_ok = decoded == raw_json_str
            except Exception:
                roundtrip_ok = False
        record(
            "original JSON preserved via binary field, base64 round-trip exact, original field removed",
            bool(encoded) and roundtrip_ok and original_field_gone,
            f"encoded_present={bool(encoded)} roundtrip_exact={roundtrip_ok} original_field_removed={original_field_gone}",
        )

    # 7. 16/64/256/512 KiB payload behaviour -- functional regression using the already-proven
    #    methodology/harness code (pid05_size_probe.py's exact-byte builder), NOT a fresh capacity investigation.
    import importlib
    size_probe = importlib.import_module("pid05_size_probe")
    for target_bytes in (16 * 1024, 64 * 1024, 256 * 1024, 512 * 1024):
        marker_n = uuid.uuid4().hex
        event_n = build_signal_state_event(marker=marker_n)
        # Build exact-size raw JSON content via the already-proven padding technique.
        # (build_realistic_payload_json already returns a serialized JSON string --
        # do not re-json.dumps() it, that would double-encode it.)
        raw_json_n = size_probe.build_realistic_payload_json(target_bytes)
        send_event(event_n, marker_n, host=f"falcon-fte-pid05-stage1-{target_bytes}", extra_fields={RAW_PAYLOAD_FIELD: raw_json_n}, **conn)
        msg_n = api.find_by_marker(marker_n)
        ok_n = msg_n is not None and bool(msg_n["fields"].get(ENCODED_FIELD))
        record(f"{target_bytes} byte raw payload indexed via binary field", ok_n, "" if ok_n else "not indexed or encoded field missing")

    # 8. Existing evidence families remain functional -- quick regression, not a full re-audit.
    for fixture_name, family in (("hermes_market_fact.json", "hermes.market_fact"), ("ares_calendar_event_state.json", "ares.calendar.event_state")):
        marker_r = uuid.uuid4().hex
        event_r = load_fixture(VALID_DIR / fixture_name)
        send_event(event_r, marker_r, host="falcon-fte-pid05-stage1-regression", extra_fields={"_fte_send_marker": marker_r}, **conn)
        msg_r = api.find_by_marker(marker_r)
        ok_r = msg_r is not None and msg_r["fields"].get("falcon_validity") == "VALID" and msg_r["fields"].get("evidence_family") == family
        record(f"existing family regression: {family}", ok_r, "" if ok_r else "regressed")

    print("\n=== Summary ===")
    passed = sum(1 for _, ok, _ in results if ok)
    for name, ok, detail in results:
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
                    help="Expected stream for a VALID signal_state event. Override to your isolated "
                         "test stream name when running against an isolated setup (recommended first).")
    p.add_argument("--quarantine-stream-name", default="FALCON: Quarantine",
                    help="Expected stream for an INVALID/spoofed event. Override for isolated testing.")
    args = p.parse_args()
    return run_all(args)


if __name__ == "__main__":
    raise SystemExit(main())
