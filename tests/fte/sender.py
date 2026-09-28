"""
FALCON PID-03 -- FTE (FALCON Test Engine) bootstrap sender.

Loads an existing PID-01 fixture (or a small PID-03 sequence-scenario
fixture) and forwards it into the real graylog-falcon GELF TCP input
(the canonical Graylog-native FALCON producer transport chosen by this
PID -- see docs/graylog evidence in the PID-03 delivery report).

This is NOT a producer application. It only loads and forwards existing
FalconEvent-shaped JSON. It implements no HERMES/ARES/HELIOS/TRON
business logic whatsoever. Full FTE productionisation is out of scope
for PID-03 (see pids/PID-03-GRAYLOG-INGESTION-TEMPLATES.md).

Stdlib only -- no third-party dependencies, matching PID-01's
tests/validator convention.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import socket
import sys
from pathlib import Path
from typing import Any


def _flatten_envelope_to_gelf(event: dict[str, Any]) -> dict[str, Any]:
    """Build the additional-field map for a single GELF message from a
    FalconEvent dict, without renaming any canonical PID-01 field.

    GELF's wire format only supports flat string/number additional
    fields (leading "_" is stripped by Graylog on receipt -- confirmed
    empirically against this running Graylog 7.1.9 GELF TCP input, see
    the PID-03 delivery report). Nested JSON (objects/arrays) has no
    native GELF representation, so `payload`, `provenance_ref` and
    `instrument_ids` are carried as JSON-encoded string fields
    (`_payload_json`, `_provenance_ref_json`, `_instrument_ids_json`)
    and un-flattened back into individual structured fields inside
    Graylog by the "FALCON Ingestion" pipeline's parse_json() rules --
    a native Graylog capability, not a bespoke FALCON service.
    """
    fields: dict[str, Any] = {}
    for key, value in event.items():
        if key in ("payload", "provenance_ref", "instrument_ids"):
            continue
        # GELF additional fields must be scalar (string or number).
        fields[f"_{key}"] = value

    if "payload" in event:
        fields["_payload_json"] = json.dumps(event["payload"], separators=(",", ":"))
    if "provenance_ref" in event:
        fields["_provenance_ref_json"] = json.dumps(event["provenance_ref"], separators=(",", ":"))
    if "instrument_ids" in event:
        fields["_instrument_ids_json"] = json.dumps(event["instrument_ids"], separators=(",", ":"))

    return fields


def _gelf_timestamp_for(event: dict[str, Any]) -> float:
    """Use produced_at_utc for GELF's own message timestamp where present
    and parseable, else current time. This is purely Graylog's own
    message-time field for ordering/GUI display -- FALCON's canonical
    produced_at_utc/falcon_ingested_at_utc fields are carried separately
    and are never overwritten by this."""
    raw = event.get("produced_at_utc")
    if isinstance(raw, str):
        try:
            normalized = raw.replace("Z", "+00:00")
            parsed = dt.datetime.fromisoformat(normalized)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=dt.timezone.utc)
            return parsed.timestamp()
        except ValueError:
            pass
    return dt.datetime.now(tz=dt.timezone.utc).timestamp()


def build_gelf_message(event: dict[str, Any], *, host: str, send_marker: str | None = None) -> dict[str, Any]:
    """send_marker is an FTE-only test-harness traceability field (NOT part
    of the FalconEvent contract): several PID-01 fixtures intentionally
    reuse the same falcon_event_id across the valid/invalid corpus
    (structural mutations of one base event), which makes falcon_event_id
    alone ambiguous for a test harness resending fixtures repeatedly. When
    given, it is carried as the extra GELF field `_fte_send_marker` so an
    automated test can look up the exact message this exact send produced,
    independent of any fixture content collision."""
    msg = {
        "version": "1.1",
        "host": host,
        "short_message": (
            f"FalconEvent {event.get('evidence_family', '?')}/"
            f"{event.get('evidence_type', '?')} from {event.get('producer_system_id', '?')}"
        ),
        "timestamp": _gelf_timestamp_for(event),
    }
    msg.update(_flatten_envelope_to_gelf(event))
    if send_marker:
        msg["_fte_send_marker"] = send_marker
    return msg


def send_gelf_tcp(message: dict[str, Any], *, gelf_host: str, gelf_port: int, timeout: float = 5.0) -> None:
    payload = json.dumps(message, separators=(",", ":")).encode("utf-8") + b"\x00"
    with socket.create_connection((gelf_host, gelf_port), timeout=timeout) as sock:
        sock.sendall(payload)


def send_raw_tcp(raw_bytes: bytes, *, gelf_host: str, gelf_port: int, timeout: float = 5.0) -> None:
    """Send raw (potentially non-GELF / non-JSON) bytes to the input --
    used only for the deliberate malformed-transport-payload negative
    test. Not used for any conformant fixture."""
    with socket.create_connection((gelf_host, gelf_port), timeout=timeout) as sock:
        sock.sendall(raw_bytes + b"\x00")


def load_fixture(path: Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fixture", type=Path, help="Path to a PID-01/PID-03 fixture JSON file")
    parser.add_argument("--gelf-host", default="graylog-falcon")
    parser.add_argument("--gelf-port", type=int, default=12401)
    parser.add_argument("--producer-host", default="falcon-fte", help="GELF 'host' field to report")
    args = parser.parse_args(argv)

    event = load_fixture(args.fixture)
    message = build_gelf_message(event, host=args.producer_host)
    send_gelf_tcp(message, gelf_host=args.gelf_host, gelf_port=args.gelf_port)
    print(f"SENT {args.fixture.name} falcon_event_id={event.get('falcon_event_id')} OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
