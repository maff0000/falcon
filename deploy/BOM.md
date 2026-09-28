# FALCON PID-02 — Immutable Bill of Materials (BOM)

Approved UTC: 2026-09-28T00:00:00Z (this dispatch)
Host: dell-debian
Docker: 28.5.2
Docker Compose: v2.40.3

No `latest`, no floating major/minor tag, no automatic updater. Images are
referenced **by digest** in `deploy/docker-compose.yml`; the tag is carried
alongside purely for human readability and is not authoritative.

| Component | Image | Tag | Digest (sha256) |
|---|---|---|---|
| Graylog server | `graylog/graylog` | `7.1.9` | `598bd41fefd5d65d05bb6a14f53d063fd717ea907a0764609413e7b89bae7406` |
| Graylog Data Node | `graylog/graylog-datanode` | `7.1.9` | `a6d545b159527b5137db041041aa0f4649119fbba29bb49b0fc8aa2a0712b6f3` |
| MongoDB | `mongo` | `8.0.32` | `4968f22d0c6c10ef29952f3e807f62872ba22b3312f25803564fbfc08255efc2` |

Full pull references:

```
graylog/graylog@sha256:598bd41fefd5d65d05bb6a14f53d063fd717ea907a0764609413e7b89bae7406
graylog/graylog-datanode@sha256:a6d545b159527b5137db041041aa0f4649119fbba29bb49b0fc8aa2a0712b6f3
mongo@sha256:4968f22d0c6c10ef29952f3e807f62872ba22b3312f25803564fbfc08255efc2
```

## Compatibility evidence

- Graylog 7.1.9 + Data Node 7.1.9 is Graylog's own documented matched pair
  (Data Node release train tracks the Graylog server minor version); no
  mixed-version pairing was used.
- MongoDB 8.0.32 is within Graylog 7.1's documented supported MongoDB range
  (Graylog 6.0+ supports MongoDB up to the 8.0 series).
- Platform: all three images were pulled `--platform linux/amd64` and run
  natively on dell-debian's amd64 host — no emulation.
- Host prerequisite `vm.max_map_count >= 262144` was independently verified
  already raised and persisted on dell-debian (HELM-owned; not re-verified
  by this PID beyond observing Data Node started cleanly with no
  memory-map related failure — see acceptance evidence in the PID-02
  report).
- All three images were present locally on dell-debian prior to this PID
  (pre-pulled) and were re-verified here with `docker inspect` /
  `docker images --digests` against the digests above before use.

## Upgrade policy

Any change to any of the three digests/tags above requires a new governed
BOM entry, updated compatibility evidence, and a fresh restore/contract
proof cycle — see `docs/graylog/FALCON-GRAYLOG-ARCHITECTURE.md`.
