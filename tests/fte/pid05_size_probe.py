"""
FALCON PID-05 discovery -- Graylog GELF message-size capacity probe.

Builds SYNTHETIC (never real/production) GELF TCP messages for all four
capacity-testing scenarios PID-05's discovery report documents. Every
scenario is reproducible from this file alone -- no ad-hoc, unsaved
scripts:

  - "standard" (default): the mandate's 6-size suite (16 KiB .. 5 MiB),
    padded to an EXACT target TOTAL ENCODED GELF wire byte size -- the
    complete UTF-8-encoded, null-terminated message that Graylog's
    `LenientDelimiterBasedFrameDecoder` measures against the input's
    `max_message_size` (its `maxFrameLength`) -- confirmed via
    inspection of `graylog.jar` (org.graylog2.inputs.transports.TcpTransport
    wires `max_message_size` directly to `maxFrameLength`; the frame
    decoder operates on the whole null-delimited byte frame, not on any
    individual GELF field). Deliberately NOT the same as "the JSON
    payload size" -- see the PID-05 discovery write-up
    (pids/PID-05-HERMES-INTEGRATION.md) for the full reasoning.
  - "boundary": the OpenSearch/Lucene per-field `keyword`-type term-
    length boundary test (documented result: 32,766 bytes in a single
    field succeeds, 32,767 fails) -- a message with exactly one
    additional field sized to an exact byte count, independent of total
    message size.
  - "realistic": the content-independence half of the same finding -- a
    realistic-shaped (but synthetic) minified-JSON payload (many small
    key/value pairs, matching the documented ~900-pair/~44KB test) in a
    single field, sized to an exact byte count, to prove the boundary
    above is content-independent, not an artifact of uniform filler.
  - "split": the confirmed-working mitigation for the boundary above --
    splits a given total content size across fixed, reused field names
    (`_pid05_split_chunk_00`, `_01`, ...), each individually at or below
    a given per-field chunk size (default: the documented Lucene limit).

*** PID-05 DISCOVERY-PHASE BOUNDARY ***
This delivery is authorised for bounded discovery/contract-verification
only -- implementation is a separate, not-yet-made Architect decision.
This module is PREPARE ONLY: it can build probe messages and (if
explicitly told to) send them, but this delivery must not execute a
--send run against the real DEV stack (same credential/live-execution
boundary already established and upheld throughout PID-04 -- this
delivery does not have, and must not obtain, live Graylog admin API
access). Only Rogue runs this against the real stack. Every payload this
module builds is synthetic filler/fake-shaped data with a unique marker
field -- never real HERMES/ARES/HELIOS/TRON evidence.

Stdlib only, matching this project's existing tests/fte/ convention
(sender.py, run_pid03_tests.py). Reuses sender.py's send_gelf_tcp /
send_gelf_tcp_tls so a probe travels over exactly the same transport
path (including PID-04 mTLS, when a dedicated input's cert/key are
given) a real HERMES producer would use.

Usage (Rogue only, against the real stack):

    # Report-only (no network) -- any mode, prints exact byte sizes,
    # proves the padding math without touching anything:
    python3 tests/fte/pid05_size_probe.py --report-only
    python3 tests/fte/pid05_size_probe.py --mode boundary --report-only
    python3 tests/fte/pid05_size_probe.py --mode realistic --report-only
    python3 tests/fte/pid05_size_probe.py --mode split --split-total-bytes 810000 --report-only

    # Standard 6-size suite, sent over mTLS through HERMES's own
    # dedicated PID-04 input:
    python3 tests/fte/pid05_size_probe.py --send \\
        --gelf-host graylog-falcon --gelf-port 12411 \\
        --client-cert deploy/secrets/pid04-mtls/clients/hermes.crt \\
        --client-key deploy/secrets/pid04-mtls/clients/hermes.key \\
        --server-ca deploy/secrets/pid04-mtls/server/server.crt

    # Boundary test at the documented 32,766/32,767-byte pair (default
    # when --field-bytes is omitted):
    python3 tests/fte/pid05_size_probe.py --mode boundary --send ...(same conn args)

    # Boundary test at a custom single field size:
    python3 tests/fte/pid05_size_probe.py --mode boundary --field-bytes 32767 --send ...

    # Realistic-shaped-payload content-independence test at the
    # documented ~44 KB (default when --realistic-bytes is omitted):
    python3 tests/fte/pid05_size_probe.py --mode realistic --send ...

    # Field-splitting mitigation test, 810,000 bytes of content split
    # across fixed, reused ~32,766-byte fields (default chunk size):
    python3 tests/fte/pid05_size_probe.py --mode split --split-total-bytes 810000 --send ...

    # A single, larger, explicitly-opted-into standard-mode size for
    # controlled escalation beyond the standard suite (e.g. 8 MiB):
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

# Documented OpenSearch/Lucene keyword-field term-length boundary
# (Section 7.2 failure mode 2: 32,766 succeeds, 32,767 fails) -- default
# pair tested by --mode boundary when --field-bytes is not given.
LUCENE_KEYWORD_TERM_LIMIT_BYTES = 32766
DEFAULT_BOUNDARY_FIELD_SIZES: list[int] = [LUCENE_KEYWORD_TERM_LIMIT_BYTES, LUCENE_KEYWORD_TERM_LIMIT_BYTES + 1]

# Default target for --mode realistic when --realistic-bytes is not
# given, matching the documented ~44 KB / ~900-pair test exactly.
DEFAULT_REALISTIC_TARGET_BYTES = 44_000
DEFAULT_REALISTIC_PAIR_COUNT = 900

ESCALATION_CEILING_BYTES = 5 * 1024 * 1024  # standard-suite ceiling; same guard reused across all modes.

FILLER_FIELD = "_pid05_size_probe_filler"
BOUNDARY_FIELD = "_pid05_boundary_filler"
REALISTIC_FIELD = "_pid05_realistic_payload_json"
SPLIT_CHUNK_FIELD_PREFIX = "_pid05_split_chunk_"
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


def build_boundary_message(*, field_bytes: int, marker: str, host: str = "falcon-fte-pid05-boundary") -> dict[str, Any]:
    """PID-05 Section 7.2 failure-mode-2 boundary test: a message with
    exactly ONE additional field (`_pid05_boundary_filler`), whose value
    is exactly `field_bytes` bytes of plain ASCII. Reproduces the
    documented OpenSearch/Lucene per-field keyword term-length boundary
    (32,766 succeeds / 32,767 fails) directly against the field's own
    byte length, independent of total GELF wire size -- this is a
    different axis from build_probe_message's total-message-size target.
    """
    if field_bytes < 0:
        raise ValueError(f"field_bytes must be >= 0, got {field_bytes}")
    return {
        "version": "1.1",
        "host": host,
        "short_message": f"PID-05 boundary probe field_bytes={field_bytes}",
        "timestamp": dt.datetime.now(tz=dt.timezone.utc).timestamp(),
        "_fte_send_marker": marker,
        "_pid05_boundary_field_bytes": field_bytes,
        BOUNDARY_FIELD: FILLER_CHAR * field_bytes,
    }


def build_realistic_payload_json(target_bytes: int, *, pair_count: int = DEFAULT_REALISTIC_PAIR_COUNT) -> str:
    """Builds a small-key/value-pair JSON object (matching the documented
    content-independence test: many small pairs, not uniform filler)
    whose own `json.dumps()` serialization is exactly target_bytes long.
    The final pair's value is padded with FILLER_CHAR to hit the target
    exactly -- the same exact-padding technique used elsewhere in this
    module, applied to one pair's tail rather than the whole payload, so
    the bulk of the structure still looks like many small realistic
    pairs, not one giant field.

    Raises ValueError if `pair_count` small pairs alone already exceed
    target_bytes (reduce pair_count or raise target_bytes) -- fails
    loudly rather than silently building something smaller than asked.
    """
    pairs = {f"k{i}": f"v{i}" for i in range(pair_count)}
    base_len = len(json.dumps(pairs, separators=(",", ":")).encode("utf-8"))
    if base_len > target_bytes:
        raise ValueError(
            f"{pair_count} small key/value pairs alone already serialize to {base_len} bytes, "
            f"larger than target_bytes={target_bytes} -- reduce pair_count or raise target_bytes."
        )
    pad_needed = target_bytes - base_len
    last_key = f"k{pair_count - 1}"
    pairs[last_key] = pairs[last_key] + (FILLER_CHAR * pad_needed)
    serialized = json.dumps(pairs, separators=(",", ":"))
    actual = len(serialized.encode("utf-8"))
    if actual != target_bytes:
        raise AssertionError(
            f"internal padding arithmetic error: built {actual} bytes, wanted {target_bytes} "
            f"(off by {actual - target_bytes}) -- do not trust this probe's sizing until fixed."
        )
    return serialized


def build_realistic_message(*, target_bytes: int, marker: str, pair_count: int = DEFAULT_REALISTIC_PAIR_COUNT, host: str = "falcon-fte-pid05-realistic") -> dict[str, Any]:
    """Wraps build_realistic_payload_json's exact-sized, realistic-shaped
    JSON string into a single GELF additional field
    (`_pid05_realistic_payload_json`), for the content-independence half
    of the Section 7.2 failure-mode-2 boundary finding (uniform filler
    and this realistic shape must fail at the identical byte threshold
    for "content-independent" to hold)."""
    payload_json = build_realistic_payload_json(target_bytes, pair_count=pair_count)
    return {
        "version": "1.1",
        "host": host,
        "short_message": f"PID-05 realistic-payload probe target_bytes={target_bytes}",
        "timestamp": dt.datetime.now(tz=dt.timezone.utc).timestamp(),
        "_fte_send_marker": marker,
        "_pid05_realistic_target_bytes": target_bytes,
        "_pid05_realistic_pair_count": pair_count,
        REALISTIC_FIELD: payload_json,
    }


def build_split_message(*, total_content_bytes: int, chunk_size: int = LUCENE_KEYWORD_TERM_LIMIT_BYTES, marker: str, host: str = "falcon-fte-pid05-split") -> dict[str, Any]:
    """PID-05 Section 7.2 field-splitting mitigation test: splits
    `total_content_bytes` of filler content across fixed, reused field
    names (`_pid05_split_chunk_00`, `_01`, ...), each individually at or
    below `chunk_size` bytes (default: the documented Lucene keyword
    term-length limit, so each chunk individually clears failure mode 2
    by construction). Reproduces the confirmed-working mitigation
    exactly as documented -- fixed/reused field names, not one field per
    message shape.
    """
    if chunk_size <= 0:
        raise ValueError(f"chunk_size must be positive, got {chunk_size}")
    if total_content_bytes < 0:
        raise ValueError(f"total_content_bytes must be >= 0, got {total_content_bytes}")
    msg: dict[str, Any] = {
        "version": "1.1",
        "host": host,
        "short_message": f"PID-05 split probe total={total_content_bytes} chunk_size={chunk_size}",
        "timestamp": dt.datetime.now(tz=dt.timezone.utc).timestamp(),
        "_fte_send_marker": marker,
        "_pid05_split_total_content_bytes": total_content_bytes,
        "_pid05_split_chunk_size": chunk_size,
    }
    remaining = total_content_bytes
    idx = 0
    while remaining > 0:
        this_chunk = min(chunk_size, remaining)
        field_name = f"{SPLIT_CHUNK_FIELD_PREFIX}{idx:02d}"
        msg[field_name] = FILLER_CHAR * this_chunk
        remaining -= this_chunk
        idx += 1
    msg["_pid05_split_chunk_count"] = idx
    return msg


def report_only(target_sizes: list[int]) -> int:
    """Build every requested standard-mode size locally (no network at
    all) and report the exact byte counts achieved. This is what this
    delivery itself ran to prove the padding arithmetic is exact,
    without touching any live stack -- see the PID-05 discovery
    write-up."""
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


def _check_escalation(size_bytes: int, confirm_large: bool) -> bool:
    """Shared >5 MiB escalation guard, reused across every mode's --send
    path -- controlled escalation must always be an explicit, deliberate
    choice, never a default, regardless of which mode is asking."""
    if size_bytes > ESCALATION_CEILING_BYTES and not confirm_large:
        print(
            f"  size={size_bytes} bytes exceeds the documented 5 MiB standard-suite ceiling -- "
            "refusing to send without --i-understand-this-may-exceed-max-message-size "
            "(controlled escalation must be an explicit, deliberate choice, never a default)."
        )
        return False
    return True


def _send_message(msg: dict[str, Any], *, label: str, gelf_host: str, gelf_port: int, client_cert: Path | None, client_key: Path | None, server_ca: Path | None) -> str:
    marker = msg.get("_fte_send_marker", "?")
    print(f"  {label}: sending (marker={marker}) ...")
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
    return client_result


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
        "PID-05 size probe -- SEND mode (standard). This will attempt real network "
        f"sends to {gelf_host}:{gelf_port}.\n"
        "Every payload is synthetic filler data with a unique marker field -- "
        "never real HERMES/ARES/HELIOS/TRON evidence.\n"
    )
    results = []
    for target in sorted(target_sizes):
        if not _check_escalation(target, confirm_large):
            results.append((target, "REFUSED_WITHOUT_EXPLICIT_ESCALATION_FLAG"))
            continue
        marker = uuid.uuid4().hex
        try:
            msg = build_probe_message(target_total_bytes=target, marker=marker)
        except ValueError as exc:
            print(f"  target={target} bytes: SKIPPED (cannot build) -- {exc}")
            results.append((target, f"SKIPPED: {exc}"))
            continue
        client_result = _send_message(
            msg, label=f"target={target} bytes",
            gelf_host=gelf_host, gelf_port=gelf_port,
            client_cert=client_cert, client_key=client_key, server_ca=server_ca,
        )
        results.append((target, f"SENT (marker={msg['_fte_send_marker']}) -- {client_result}"))

    print("\n=== Summary (client-side only -- verify every row server-side before concluding anything) ===")
    for target, outcome in results:
        print(f"  {target:>10} bytes: {outcome}")
    return 0


def run_boundary(field_sizes: list[int], *, send: bool, gelf_host: str, gelf_port: int, client_cert: Path | None, client_key: Path | None, server_ca: Path | None, confirm_large: bool) -> int:
    print(
        f"PID-05 size probe -- boundary mode (OpenSearch/Lucene per-field keyword "
        f"term-length test). Testing field sizes: {field_sizes} bytes "
        f"(documented Lucene keyword term limit: {LUCENE_KEYWORD_TERM_LIMIT_BYTES} bytes).\n"
    )
    for field_bytes in field_sizes:
        marker = uuid.uuid4().hex
        msg = build_boundary_message(field_bytes=field_bytes, marker=marker)
        label = f"field_bytes={field_bytes}"
        if send:
            if not _check_escalation(field_bytes, confirm_large):
                continue
            _send_message(msg, label=label, gelf_host=gelf_host, gelf_port=gelf_port, client_cert=client_cert, client_key=client_key, server_ca=server_ca)
        else:
            print(f"  {label}: built OK, total encoded GELF wire size = {_encoded_gelf_wire_size(msg)} bytes, marker={marker}")
    return 0


def run_realistic(target_bytes: int, *, send: bool, gelf_host: str, gelf_port: int, client_cert: Path | None, client_key: Path | None, server_ca: Path | None, confirm_large: bool) -> int:
    print(
        f"PID-05 size probe -- realistic mode (content-independence test: "
        f"{DEFAULT_REALISTIC_PAIR_COUNT} small key/value pairs, target {target_bytes} bytes).\n"
    )
    marker = uuid.uuid4().hex
    try:
        msg = build_realistic_message(target_bytes=target_bytes, marker=marker)
    except ValueError as exc:
        print(f"  target_bytes={target_bytes}: FAILED TO BUILD -- {exc}")
        return 1
    label = f"target_bytes={target_bytes}"
    if send:
        if not _check_escalation(target_bytes, confirm_large):
            return 0
        _send_message(msg, label=label, gelf_host=gelf_host, gelf_port=gelf_port, client_cert=client_cert, client_key=client_key, server_ca=server_ca)
    else:
        print(f"  {label}: built OK, total encoded GELF wire size = {_encoded_gelf_wire_size(msg)} bytes, marker={marker}")
    return 0


def run_split(total_content_bytes: int, chunk_size: int, *, send: bool, gelf_host: str, gelf_port: int, client_cert: Path | None, client_key: Path | None, server_ca: Path | None, confirm_large: bool) -> int:
    print(
        f"PID-05 size probe -- split mode (field-splitting mitigation test): "
        f"total_content_bytes={total_content_bytes}, chunk_size={chunk_size}.\n"
    )
    marker = uuid.uuid4().hex
    try:
        msg = build_split_message(total_content_bytes=total_content_bytes, chunk_size=chunk_size, marker=marker)
    except ValueError as exc:
        print(f"  FAILED TO BUILD -- {exc}")
        return 1
    chunk_count = msg["_pid05_split_chunk_count"]
    label = f"total={total_content_bytes} chunks={chunk_count}"
    wire_size = _encoded_gelf_wire_size(msg)
    if send:
        if not _check_escalation(wire_size, confirm_large):
            return 0
        _send_message(msg, label=label, gelf_host=gelf_host, gelf_port=gelf_port, client_cert=client_cert, client_key=client_key, server_ca=server_ca)
    else:
        print(f"  {label}: built OK, {chunk_count} fields ({SPLIT_CHUNK_FIELD_PREFIX}00..{chunk_count - 1:02d}), total encoded GELF wire size = {wire_size} bytes, marker={marker}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--mode", choices=["standard", "boundary", "realistic", "split"], default="standard", help="Which PID-05 Section 7.2 scenario to run (default: standard, the mandate's 6-size suite).")
    parser.add_argument("--report-only", action="store_true", help="Build locally, report exact byte counts, send nothing (default if --send is not given).")
    parser.add_argument("--send", action="store_true", help="Actually send over the network. Requires --gelf-host/--gelf-port.")
    parser.add_argument("--target-bytes", type=int, default=None, help="[standard mode] A single custom total-message target size in bytes, instead of the standard 6-size suite.")
    parser.add_argument("--field-bytes", type=int, action="append", default=None, help="[boundary mode] A single field's exact byte size to test; repeatable. Default if omitted: the documented 32766/32767 pair.")
    parser.add_argument("--realistic-bytes", type=int, default=None, help="[realistic mode] Target total byte size for the realistic-shaped JSON field. Default if omitted: 44000 (the documented ~44 KB test).")
    parser.add_argument("--split-total-bytes", type=int, default=None, help="[split mode] REQUIRED in split mode -- total content bytes to split across fixed, reused chunk fields. No default: this is the primary variable under test.")
    parser.add_argument("--split-chunk-size", type=int, default=LUCENE_KEYWORD_TERM_LIMIT_BYTES, help=f"[split mode] Max bytes per chunk field (default: {LUCENE_KEYWORD_TERM_LIMIT_BYTES}, the documented Lucene keyword term-length limit).")
    parser.add_argument("--gelf-host", default="graylog-falcon")
    parser.add_argument("--gelf-port", type=int, default=None, help="Required with --send -- no hidden default port, since this harness is meant to target a specific PID-04 dedicated input, not assumed to be the retired shared input.")
    parser.add_argument("--client-cert", type=Path, default=None, help="PID-04 mTLS client cert (e.g. deploy/secrets/pid04-mtls/clients/hermes.crt) -- enables TLS mode.")
    parser.add_argument("--client-key", type=Path, default=None)
    parser.add_argument("--server-ca", type=Path, default=None)
    parser.add_argument(
        "--i-understand-this-may-exceed-max-message-size", dest="confirm_large", action="store_true",
        help="Required in addition to --send for any size above the standard 5 MiB ceiling, in ANY mode -- controlled escalation must be explicit, never a default.",
    )
    args = parser.parse_args(argv)

    if args.send and args.gelf_port is None:
        raise SystemExit("FATAL: --send requires --gelf-port (no hidden default -- name the exact dedicated input you're targeting).")

    conn_kwargs = dict(
        gelf_host=args.gelf_host, gelf_port=args.gelf_port,
        client_cert=args.client_cert, client_key=args.client_key, server_ca=args.server_ca,
    )

    if args.mode == "standard":
        target_sizes = [args.target_bytes] if args.target_bytes is not None else list(STANDARD_SUITE_BYTES)
        if args.send:
            return send_suite(target_sizes, confirm_large=args.confirm_large, **conn_kwargs)
        return report_only(target_sizes)

    if args.mode == "boundary":
        field_sizes = args.field_bytes if args.field_bytes else list(DEFAULT_BOUNDARY_FIELD_SIZES)
        if args.field_bytes is None:
            print(f"(--field-bytes not given -- defaulting to the documented boundary pair: {field_sizes})\n")
        return run_boundary(field_sizes, send=args.send, confirm_large=args.confirm_large, **conn_kwargs)

    if args.mode == "realistic":
        target_bytes = args.realistic_bytes if args.realistic_bytes is not None else DEFAULT_REALISTIC_TARGET_BYTES
        if args.realistic_bytes is None:
            print(f"(--realistic-bytes not given -- defaulting to the documented ~44 KB test: {target_bytes})\n")
        return run_realistic(target_bytes, send=args.send, confirm_large=args.confirm_large, **conn_kwargs)

    if args.mode == "split":
        if args.split_total_bytes is None:
            raise SystemExit("FATAL: --mode split requires --split-total-bytes (no default -- this is the primary variable under test).")
        return run_split(args.split_total_bytes, args.split_chunk_size, send=args.send, confirm_large=args.confirm_large, **conn_kwargs)

    raise SystemExit(f"FATAL: unknown mode {args.mode!r}")  # unreachable given argparse choices=


if __name__ == "__main__":
    raise SystemExit(main())
