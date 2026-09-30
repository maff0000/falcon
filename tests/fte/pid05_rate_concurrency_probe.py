"""FALCON PID-05 follow-up (Architect Section C) -- rate/concurrency
silent-loss characterisation probe.

*** PID-05 DISCOVERY-PHASE BOUNDARY ***
Read-only-against-HERMES/FALCON-code discovery tooling. This module
only ever sends SYNTHETIC filler data with a unique marker field --
never real HERMES/ARES/HELIOS/TRON evidence -- to the real DEV stack,
under the same authorised, bounded empirical-testing scope as
tests/fte/pid05_size_probe.py. It does not implement any part of the
HERMES->FALCON integration itself.

Background: PID-05's discovery phase found that a single isolated send
of a ~841KB multi-field (field-split, each field <=32766 bytes) GELF
message indexes reliably, but repeated similarly-sized sends in quick
succession can fail completely silently (zero trace in any log
checked, including the message-journal's own DEBUG trace) -- ruling out
a clean byte-size ceiling and pointing at a rate- or
concurrency-sensitive failure path instead. This module exists to
characterise that failure path properly, per the Architect's explicit
instructions:

  - test message sizes: 4 KiB, 32 KiB, 128 KiB, 512 KiB, ~800 KiB
  - vary send RATE and CONNECTION REUSE as two SEPARATE, independent
    variables (never conflated in a single run)
  - record, for every attempt: a unique event id, the client-side send
    timestamp, whether it was indexed, and (when indexed) the server's
    own receive timestamp
  - stop escalation immediately on resource pressure or an unexpected
    failure shape
  - the exact failure stage must be determined from evidence gathered
    here (sender vs. transport decode vs. buffering vs. another
    evidenced stage) -- never selected speculatively

Payloads at or above 32 KiB are built using the already-proven
field-splitting mitigation from pid05_size_probe.py (fixed, reused
chunk field names, each <=32766 bytes) so that any loss this probe
observes is never confused with the already-understood, already-fixed
per-field Lucene term-length limit -- every payload built here is, by
construction, indexable if delivered and processed cleanly.

Two connection modes:
  - "fresh": exactly the existing sender.py behaviour -- a brand new
    TCP+TLS connection (and, on the real HERMES input, a fresh mTLS
    handshake) per message.
  - "reused": a single TCP+TLS connection held open across all N sends
    in one run, with each GELF message written as its own
    null-delimited frame on that same connection (GELF TCP's own
    framing already supports multiple messages per connection -- this
    is not a protocol extension).

Usage (Rogue only, against the real stack -- see pid05_size_probe.py's
own module docstring for why FORGE's sandbox must never hold or use a
live Graylog admin credential; this module needs one too, for the
post-send indexed/not-indexed check):

    python3 tests/fte/pid05_rate_concurrency_probe.py \\
        --gelf-host graylog-falcon --gelf-port 12411 \\
        --client-cert deploy/secrets/pid04-mtls/clients/hermes.crt \\
        --client-key deploy/secrets/pid04-mtls/clients/hermes.key \\
        --server-ca deploy/secrets/pid04-mtls/server/server.crt \\
        --graylog-api-base http://192.168.11.10:9010/api \\
        --graylog-user admin --graylog-password <password> \\
        --size-bytes 819200 --count 5 --connection-mode fresh \\
        --interval-ms 0

Prints a per-attempt table (send timestamp, marker, indexed True/False,
server receive timestamp when found) and a summary. Never modifies
Graylog configuration. Never touches IRIS. Uses a bounded --count
(default 5) -- this is deliberately NOT a stress-testing tool; the
Architect's mandate explicitly does not authorise broad stress testing.
"""

from __future__ import annotations

import argparse
import json
import socket
import ssl
import sys
import time
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import sender  # noqa: E402  (existing FTE convention module, reused deliberately)

CHUNK_FIELD_PREFIX = "_pid05_rate_chunk_"
CHUNK_SIZE = 32000  # comfortably under the confirmed 32,766-byte Lucene keyword-term limit


def build_message(*, target_content_bytes: int, marker: str, host: str) -> dict:
    """Builds a GELF message whose additional-field content totals
    target_content_bytes, split across fixed, reused chunk field names
    each <=CHUNK_SIZE bytes -- the already-proven field-splitting
    mitigation, applied here so this probe's own payloads are never
    themselves subject to the already-understood per-field limit."""
    msg = {
        "version": "1.1",
        "host": host,
        "short_message": f"pid05 rate/concurrency probe {marker}",
        "timestamp": time.time(),
        "_fte_send_marker": marker,
        "_pid05_rate_probe_target_bytes": target_content_bytes,
    }
    remaining = target_content_bytes
    i = 0
    while remaining > 0:
        this_chunk = min(CHUNK_SIZE, remaining)
        msg[f"{CHUNK_FIELD_PREFIX}{i:03d}"] = "a" * this_chunk
        remaining -= this_chunk
        i += 1
    return msg


def send_fresh(messages: list[dict], *, gelf_host: str, gelf_port: int,
                client_cert: str, client_key: str, server_ca: str) -> list[str | None]:
    """One brand-new TCP+TLS connection (and mTLS handshake) per message --
    the existing sender.py behaviour, used as-is, unmodified."""
    errors: list[str | None] = []
    for msg in messages:
        try:
            sender.send_gelf_tcp_tls(
                msg, gelf_host=gelf_host, gelf_port=gelf_port,
                client_cert=client_cert, client_key=client_key, server_ca=server_ca,
            )
            errors.append(None)
        except OSError as exc:
            errors.append(f"{type(exc).__name__}: {exc}")
    return errors


def check_indexed(marker: str, *, api_base: str, user: str, password: str, timeout_s: float = 8.0) -> dict | None:
    import base64

    auth = base64.b64encode(f"{user}:{password}".encode()).decode()
    query = urllib.parse.urlencode({
        "query": f"fte_send_marker:{marker}",
        "range": "120",
        "fields": "fte_send_marker,gl2_receive_timestamp,timestamp",
    })
    req = urllib.request.Request(
        f"{api_base}/search/universal/relative?{query}",
        headers={"Authorization": f"Basic {auth}", "X-Requested-By": "pid05-rate-probe", "Accept": "application/json"},
    )
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read())
        except urllib.error.URLError:
            data = {"messages": []}
        if data.get("messages"):
            fields = data["messages"][0]["message"]
            return {"gl2_receive_timestamp": fields.get("gl2_receive_timestamp"), "timestamp": fields.get("timestamp")}
        time.sleep(0.5)
    return None


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--size-bytes", type=int, required=True, help="Target additional-field content size (e.g. 4096, 32768, 131072, 524288, 819200).")
    p.add_argument("--count", type=int, default=5, help="Number of messages to send in this run (default 5 -- deliberately small; this is not a stress tool).")
    p.add_argument("--connection-mode", choices=["fresh", "reused"], required=True)
    p.add_argument("--interval-ms", type=int, default=0, help="Delay between sends in milliseconds (0 = as fast as possible). Independent of --connection-mode.")
    p.add_argument("--gelf-host", required=True)
    p.add_argument("--gelf-port", type=int, required=True)
    p.add_argument("--client-cert", required=True)
    p.add_argument("--client-key", required=True)
    p.add_argument("--server-ca", required=True)
    p.add_argument("--graylog-api-base", required=True)
    p.add_argument("--graylog-user", required=True)
    p.add_argument("--graylog-password", required=True)
    args = p.parse_args()

    if args.count > 20:
        print(f"REFUSING: --count {args.count} exceeds this tool's own safety ceiling of 20 -- "
              "the Architect's mandate does not authorise broad stress testing. Run multiple "
              "smaller invocations instead if more data points are genuinely needed.", file=sys.stderr)
        return 2

    markers = [uuid.uuid4().hex for _ in range(args.count)]
    messages = [build_message(target_content_bytes=args.size_bytes, marker=m, host=f"falcon-fte-pid05-rate-{args.connection_mode}") for m in markers]

    print(f"PID-05 rate/concurrency probe -- size={args.size_bytes} bytes, count={args.count}, "
          f"connection_mode={args.connection_mode}, interval_ms={args.interval_ms}")
    print("Every payload is synthetic filler data with a unique marker field -- never real evidence.\n")

    send_timestamps = []
    if args.connection_mode == "fresh" and args.interval_ms == 0:
        # send_fresh has no per-message hook for an interval; loop here so both
        # modes honour --interval-ms identically and independently of connection reuse.
        errors = []
        for msg in messages:
            send_timestamps.append(time.time())
            errors.extend(send_fresh([msg], gelf_host=args.gelf_host, gelf_port=args.gelf_port,
                                      client_cert=args.client_cert, client_key=args.client_key, server_ca=args.server_ca))
    elif args.connection_mode == "fresh":
        errors = []
        for msg in messages:
            send_timestamps.append(time.time())
            errors.extend(send_fresh([msg], gelf_host=args.gelf_host, gelf_port=args.gelf_port,
                                      client_cert=args.client_cert, client_key=args.client_key, server_ca=args.server_ca))
            time.sleep(args.interval_ms / 1000.0)
    else:
        # reused: still honour --interval-ms between writes on the same connection.
        context = sender.build_mtls_context(client_cert=args.client_cert, client_key=args.client_key, server_ca=args.server_ca)
        errors = []
        with socket.create_connection((args.gelf_host, args.gelf_port), timeout=10.0) as raw_sock:
            with context.wrap_socket(raw_sock, server_hostname=args.gelf_host if context.check_hostname else None) as tls_sock:
                for msg in messages:
                    send_timestamps.append(time.time())
                    try:
                        payload = json.dumps(msg, separators=(",", ":")).encode("utf-8") + b"\x00"
                        tls_sock.sendall(payload)
                        errors.append(None)
                    except OSError as exc:
                        errors.append(f"{type(exc).__name__}: {exc}")
                    if args.interval_ms:
                        time.sleep(args.interval_ms / 1000.0)

    print("Client-side send phase complete. Checking indexed status for each marker "
          "(this is NOT proof of anything by itself if it reports an error -- see "
          "pid05_size_probe.py's own TLS-1.3-client-lies note; the search-API check below "
          "is the authoritative signal)...\n")

    results = []
    for marker, ts, err in zip(markers, send_timestamps, errors):
        indexed = check_indexed(marker, api_base=args.graylog_api_base, user=args.graylog_user, password=args.graylog_password)
        results.append({"marker": marker, "send_ts": ts, "client_error": err, "indexed": indexed})

    print(f"{'marker':<34} {'send_ts':<18} {'client_error':<20} {'indexed':<8} {'server_receive_ts'}")
    ok = 0
    for r in results:
        indexed_str = "YES" if r["indexed"] else "NO"
        if r["indexed"]:
            ok += 1
        print(f"{r['marker']:<34} {r['send_ts']:<18.3f} {str(r['client_error']):<20} {indexed_str:<8} "
              f"{r['indexed']['gl2_receive_timestamp'] if r['indexed'] else '-'}")

    print(f"\nIndexed: {ok}/{len(results)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
