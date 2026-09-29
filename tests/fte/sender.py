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
import ssl
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
    used for the PID-03 malformed-transport-payload negative test AND
    (PID-04) the "plaintext to a TLS-enabled input" negative test: a
    dedicated input has tls_enable=true, so any plaintext TCP payload
    (GELF-shaped or not) sent to it is a TLS record-layer violation, not
    a GELF/JSON parsing question. Not used for any conformant fixture."""
    with socket.create_connection((gelf_host, gelf_port), timeout=timeout) as sock:
        sock.sendall(raw_bytes + b"\x00")


def build_mtls_context(
    *,
    client_cert: Path | None = None,
    client_key: Path | None = None,
    server_ca: Path | None = None,
    verify_server: bool = True,
) -> ssl.SSLContext:
    """Build a client-side TLS/mTLS SSLContext for a PID-04 dedicated
    input.

    client_cert/client_key: this producer's own leaf cert/key (from
        deploy/secrets/pid04-mtls/clients/<producer>.*). Omit both to test
        the "no client certificate offered" negative case -- the dedicated
        input's tls_client_auth=required setting means the server should
        reject the handshake.
    server_ca: path to the dedicated inputs' shared server cert
        (deploy/secrets/pid04-mtls/server/server.crt), used to verify the
        server's identity. Since this is a DEV self-signed leaf (not a CA),
        it is loaded directly as a trust anchor via load_verify_locations --
        that is sufficient for a self-signed cert to validate itself.
    verify_server: set False only for a deliberate "don't bother verifying
        the server" test; PID-04's own default posture verifies it.

    IMPORTANT (discovery-phase finding, carried into PID-04): under TLS
    1.3, this client's own apparent "handshake OK" / "sendall() didn't
    raise" is NOT proof the server accepted anything -- the client's
    write can locally succeed before or independent of a server-side
    rejection being observable at this layer. The only two ways to
    actually verify what happened are examining the server's own log
    (`docker logs graylog-falcon`) and checking real message
    presence/absence via the Graylog search API. Every caller of this
    function (see run_pid03_tests.py's PID-04 mTLS scenarios) must treat
    this function's return/exception behaviour as informational only,
    never as the test's pass/fail verdict.
    """
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    if verify_server and server_ca is not None:
        context.load_verify_locations(cafile=str(server_ca))
        context.check_hostname = False  # DEV: connect by IP/container-name, not by a name-matched CA-issued cert
        context.verify_mode = ssl.CERT_REQUIRED
    else:
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
    if client_cert is not None and client_key is not None:
        context.load_cert_chain(certfile=str(client_cert), keyfile=str(client_key))
    return context


def send_gelf_tcp_tls(
    message: dict[str, Any],
    *,
    gelf_host: str,
    gelf_port: int,
    client_cert: Path | None = None,
    client_key: Path | None = None,
    server_ca: Path | None = None,
    verify_server: bool = True,
    timeout: float = 5.0,
) -> None:
    """TLS/mTLS equivalent of send_gelf_tcp, for a PID-04 dedicated input.

    Raises ssl.SSLError / OSError on a client-observable failure (refused
    connection, handshake alert, etc.) -- callers must still confirm the
    real outcome server-side (see build_mtls_context's docstring); a raised
    exception here is useful corroborating evidence for an expected
    rejection, but a *lack* of an exception is never sufficient evidence
    of acceptance.
    """
    payload = json.dumps(message, separators=(",", ":")).encode("utf-8") + b"\x00"
    context = build_mtls_context(
        client_cert=client_cert, client_key=client_key, server_ca=server_ca, verify_server=verify_server
    )
    with socket.create_connection((gelf_host, gelf_port), timeout=timeout) as raw_sock:
        with context.wrap_socket(raw_sock, server_hostname=gelf_host if context.check_hostname else None) as tls_sock:
            tls_sock.sendall(payload)


def send_plaintext_to_tls_port(raw_bytes: bytes, *, gelf_host: str, gelf_port: int, timeout: float = 5.0) -> None:
    """PID-04 negative test: send plaintext (non-TLS) bytes directly at a
    dedicated input's TLS-enabled port. Thin, honestly-named wrapper
    around send_raw_tcp so the PID-04 test suite's intent is explicit at
    the call site."""
    send_raw_tcp(raw_bytes, gelf_host=gelf_host, gelf_port=gelf_port, timeout=timeout)


def load_fixture(path: Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fixture", type=Path, help="Path to a PID-01/PID-03 fixture JSON file")
    parser.add_argument("--gelf-host", default="graylog-falcon")
    parser.add_argument("--gelf-port", type=int, default=12401)
    parser.add_argument("--producer-host", default="falcon-fte", help="GELF 'host' field to report")
    parser.add_argument("--client-cert", type=Path, default=None, help="PID-04: this producer's mTLS client cert (enables TLS mode)")
    parser.add_argument("--client-key", type=Path, default=None, help="PID-04: this producer's mTLS client key")
    parser.add_argument("--server-ca", type=Path, default=None, help="PID-04: dedicated-input server cert to verify against")
    parser.add_argument("--no-verify-server", action="store_true", help="PID-04: skip server certificate verification")
    args = parser.parse_args(argv)

    event = load_fixture(args.fixture)
    message = build_gelf_message(event, host=args.producer_host)
    if args.client_cert or args.client_key or args.server_ca:
        send_gelf_tcp_tls(
            message,
            gelf_host=args.gelf_host,
            gelf_port=args.gelf_port,
            client_cert=args.client_cert,
            client_key=args.client_key,
            server_ca=args.server_ca,
            verify_server=not args.no_verify_server,
        )
    else:
        send_gelf_tcp(message, gelf_host=args.gelf_host, gelf_port=args.gelf_port)
    print(f"SENT {args.fixture.name} falcon_event_id={event.get('falcon_event_id')} OK (client-side only -- verify server-side per PID-04 doctrine)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
