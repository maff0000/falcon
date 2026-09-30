"""
FALCON PID-05 discovery -- Graylog GELF message-size capacity probe.

Builds SYNTHETIC (never real/production) GELF TCP messages, each padded
to an EXACT target TOTAL ENCODED byte size: the size of the complete
UTF-8-encoded, null-terminated GELF wire message that Graylog's
`LenientDelimiterBasedFrameDecoder` actually measures against the
input's `max_message_size` (its `maxFrameLength`) -- confirmed via
inspection of `graylog.jar` (org.graylog2.inputs.transports.TcpTransport
wires `max_message_size` directly to `maxFrameLength`; the frame decoder
operates on the whole null-delimited byte frame, not on any individual
GELF field). This is deliberately NOT the same as "the JSON payload
size" -- see PID-05's discovery write-up (deploy/README.md /
pids/PID-05-HERMES-FALCON-PUBLICATION.md) for the full reasoning and the
worked example of the difference between the two.

*** PID-05 DISCOVERY-PHASE BOUNDARY ***
This delivery is authorised for bounded discovery/contract-verification
only -- implementation is a separate, not-yet-made Architect decision.
This module is PREPARE ONLY: it can build probe messages and (if
explicitly told to) send them, but this delivery must not execute a
--send run against the real DEV stack (same credential/live-execution
boundary already established and upheld throughout PID-04 -- this
delivery does not have, and must not obtain, live Graylog admin API
access). Only Rogue runs this against the real stack. Every payload this
module builds is synthetic filler data with a unique marker field --
never real HERMES/ARES/HELIOS/TRON evidence.

Stdlib only, matching this project's existing tests/fte/ convention
(sender.py, run_pid03_tests.py). Reuses sender.py's send_gelf_tcp /
send_gelf_tcp_tls so a probe travels over exactly the same transport
path (including PID-04 mTLS, when a dedicated input's cert/key are
given) a real HERMES producer would use.

Usage (Rogue only, against the real stack):

    # Report-only (no network) -- prints exact byte sizes for the
    # standard suite, proves the padding math without touching anything:
    python3 tests/fte/pid05_size_probe.py --report-only

    # Send the standard 6-size suite over mTLS through HERMES's own
    # dedicated PID-04 input:
    python3 tests/fte/pid05_size_probe.py --send \\
        --gelf-host graylog-falcon --gelf-port 12411 \\
        --client-cert deploy/secrets/pid04-mtls/clients/hermes.crt \\
        --client-key deploy/secrets/pid04-mtls/clients/hermes.key \\
        --server-ca deploy/secrets/pid04-mtls/server/server.crt

    # A single, larger, explicitly-opted-into size for controlled
    # escalation beyond the standard suite (e.g. 8 MiB):
    python3 tests/fte/pid05_size_probe.py --send --target-bytes 8388608 \\
        --i-understand-this-may-exceed-max-message-size ...(same conn args)
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import uuid
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sender  # noqa: E402  (this project's existing FTE sender module)

# The mandate's own standard suite (bytes, binary/KiB-MiB, not decimal).
STANDARD_SUITE_BYTES: list[int] = [
    16 * 1024,          # 16 KiB
    64 * 1024,          # 64 KiB
    256 * 1024,         # 256 KiB
    1 * 1024 * 1024,    # 1 MiB
    2 * 1024 * 1024,    # 2 MiB  (== this stack's current configured max_message_size)
    5 * 1024 * 1024,    # 5 MiB
]

FILLER_FIELD = "_pid05_size_probe_filler"
FILLER_CHAR = "a"  # plain ASCII, never needs JSON-escaping -- 1 filler char == 1 encoded byte, exactly.


def _encoded_gelf_wire_size(message: dict[str, Any]) -> int:
    """The exact number of bytes actually placed on the wire for this
    message by sender.send_gelf_tcp -- UTF-8-encoded JSON plus the
    trailing null-byte frame delimiter (this project's inputs are all
    configured with use_null_delimiter: true). This is deliberately
    the SAME encoding sender.py itself performs, so a build here and a
    real send later can never silently disagree."""
    return len(json.dumps(message, separators=(",", ":")).encode("utf-8")) + 1  # +1 for b"\x00"


def build_probe_message(*, target_total_bytes: int, marker: str, host: str = "falcon-fte-pid05-probe") -> dict[str, Any]:
    """Build a synthetic GELF message dict whose exact encoded wire size
    (see _encoded_gelf_wire_size) equals target_total_bytes, byte for
    byte. Raises ValueError if target_total_bytes is too small to hold
    the envelope's own fixed overhead (i.e. a negative filler length
    would be required) -- this is a real, useful failure: it tells you
    the minimum viable message size for this exact envelope shape,
    which is itself a piece of size-capacity evidence.

    The marker field (_fte_send_marker, matching this project's existing
    FTE convention) is what lets the eventual sent-and-searched proof
    unambiguously find this exact probe in Graylog, independent of any
    other traffic.
    """
    base = {
        "version": "1.1",
        "host": host,
        "short_message": f"PID-05 size probe target={target_total_bytes}",
        "timestamp": dt.datetime.now(tz=dt.timezone.utc).timestamp(),
        "_fte_send_marker": marker,
        "_pid05_probe_target_bytes": target_total_bytes,
        FILLER_FIELD: "",
    }
    overhead = _encoded_gelf_wire_size(base)
    filler_length = target_total_bytes - overhead
    if filler_length < 0:
        raise ValueError(
            f"target_total_bytes={target_total_bytes} is smaller than this envelope's own "
            f"fixed overhead ({overhead} bytes with an empty filler field) -- cannot build a "
            f"message this small with this shape. Minimum viable size for this shape: {overhead} bytes."
        )
    base[FILLER_FIELD] = FILLER_CHAR * filler_length

    actual = _encoded_gelf_wire_size(base)
    if actual != target_total_bytes:
        # Should be unreachable given FILLER_CHAR is a single, never-escaped
        # ASCII byte -- but never silently accept a size that doesn't match
        # what was asked for; fail loudly instead, per this project's own
        # "no hidden defaults" convention.
        raise AssertionError(
            f"internal padding arithmetic error: built {actual} bytes, wanted {target_total_bytes} "
            f"(off by {actual - target_total_bytes}) -- do not trust this probe's sizing until fixed."
        )
    return base


def report_only(target_sizes: list[int]) -> int:
    """Build every requested size locally (no network at all) and report
    the exact byte counts achieved. This is what this delivery itself
    ran to prove the padding arithmetic is exact, without touching any
    live stack -- see the PID-05 discovery write-up."""
    print("PID-05 size probe -- report-only mode (no network, no live stack touched).\n")
    ok = True
    for target in target_sizes:
        marker = uuid.uuid4().hex
        try:
            msg = build_probe_message(target_total_bytes=target, marker=marker)
        except ValueError as exc:
            print(f"  target={target:>10} bytes: SKIPPED -- {exc}")
            continue
        actual = _encoded_gelf_wire_size(msg)
        payload_only = len(json.dumps({FILLER_FIELD: msg[FILLER_FIELD]}, separators=(",", ":")).encode("utf-8"))
        status = "EXACT MATCH" if actual == target else "MISMATCH"
        if actual != target:
            ok = False
        print(
            f"  target={target:>10} bytes | built(full GELF wire)={actual:>10} bytes "
            f"| filler-field-JSON-alone={payload_only:>10} bytes | {status}"
        )
    print(
        "\nNote the middle column vs the target: the full encoded GELF wire message "
        "(envelope fields + this one filler field + framing) is what's built to the "
        "exact target -- the filler field's own JSON fragment alone is smaller than the "
        "target by exactly the envelope's fixed overhead. This is the documented "
        "'total encoded message vs. JSON payload' distinction from the discovery write-up, "
        "demonstrated arithmetically rather than merely asserted."
    )
    return 0 if ok else 1


def send_suite(
    target_sizes: list[int],
    *,
    gelf_host: str,
    gelf_port: int,
    client_cert: Path | None,
    client_key: Path | None,
    server_ca: Path | None,
    confirm_large: bool,
) -> int:
    print(
        "PID-05 size probe -- SEND mode. This will attempt real network "
        f"sends to {gelf_host}:{gelf_port}.\n"
        "Every payload is synthetic filler data with a unique marker field -- "
        "never real HERMES/ARES/HELIOS/TRON evidence.\n"
    )
    results = []
    for target in sorted(target_sizes):
        if target > 5 * 1024 * 1024 and not confirm_large:
            print(
                f"  target={target} bytes exceeds the documented 5 MiB standard-suite ceiling -- "
                "refusing to send without --i-understand-this-may-exceed-max-message-size "
                "(controlled escalation must be an explicit, deliberate choice, never a default)."
            )
            results.append((target, "REFUSED_WITHOUT_EXPLICIT_ESCALATION_FLAG"))
            continue
        marker = uuid.uuid4().hex
        try:
            msg = build_probe_message(target_total_bytes=target, marker=marker)
        except ValueError as exc:
            print(f"  target={target} bytes: SKIPPED (cannot build) -- {exc}")
            results.append((target, f"SKIPPED: {exc}"))
            continue
        print(f"  sending target={target} bytes, marker={marker} ...")
        try:
            if client_cert or client_key or server_ca:
                sender.send_gelf_tcp_tls(
                    msg, gelf_host=gelf_host, gelf_port=gelf_port,
                    client_cert=client_cert, client_key=client_key, server_ca=server_ca,
                )
            else:
                sender.send_gelf_tcp(msg, gelf_host=gelf_host, gelf_port=gelf_port)
            client_result = "send completed without a client-side exception"
        except OSError as exc:
            client_result = f"client-side exception: {type(exc).__name__}: {exc}"
        print(f"    client-side result: {client_result}")
        print(
            "    REMINDER (per PID-04's own already-proven TLS-1.3-client-lies finding, which "
            "applies equally here): this client-side result is NOT proof of server-side "
            "acceptance or rejection. Confirm via docker logs graylog-falcon and a real "
            f"Graylog search for fte_send_marker:{marker} before drawing any conclusion."
        )
        results.append((target, f"SENT (marker={marker}) -- {client_result}"))

    print("\n=== Summary (client-side only -- verify every row server-side before concluding anything) ===")
    for target, outcome in results:
        print(f"  {target:>10} bytes: {outcome}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--report-only", action="store_true", help="Build every size locally, report exact byte counts, send nothing (default if --send is not given).")
    parser.add_argument("--send", action="store_true", help="Actually send over the network. Requires --gelf-host/--gelf-port.")
    parser.add_argument("--target-bytes", type=int, default=None, help="A single custom target size in bytes, instead of the standard 6-size suite.")
    parser.add_argument("--gelf-host", default="graylog-falcon")
    parser.add_argument("--gelf-port", type=int, default=None, help="Required with --send -- no hidden default port, since this harness is meant to target a specific PID-04 dedicated input, not assumed to be the retired shared input.")
    parser.add_argument("--client-cert", type=Path, default=None, help="PID-04 mTLS client cert (e.g. deploy/secrets/pid04-mtls/clients/hermes.crt) -- enables TLS mode.")
    parser.add_argument("--client-key", type=Path, default=None)
    parser.add_argument("--server-ca", type=Path, default=None)
    parser.add_argument(
        "--i-understand-this-may-exceed-max-message-size", dest="confirm_large", action="store_true",
        help="Required in addition to --send + --target-bytes for any size above the standard 5 MiB ceiling -- controlled escalation must be explicit, never a default.",
    )
    args = parser.parse_args(argv)

    target_sizes = [args.target_bytes] if args.target_bytes is not None else list(STANDARD_SUITE_BYTES)

    if args.send:
        if args.gelf_port is None:
            raise SystemExit("FATAL: --send requires --gelf-port (no hidden default -- name the exact dedicated input you're targeting).")
        return send_suite(
            target_sizes,
            gelf_host=args.gelf_host, gelf_port=args.gelf_port,
            client_cert=args.client_cert, client_key=args.client_key, server_ca=args.server_ca,
            confirm_large=args.confirm_large,
        )
    return report_only(target_sizes)


if __name__ == "__main__":
    raise SystemExit(main())
