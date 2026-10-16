#!/usr/bin/env python3
"""Re-verify the EP-10 stale-language inventory against the working tree.

For every row: the file exists, the named line range exists, and the regex
needle matches inside that range. Exit 1 on any mismatch. Read-only, stdlib only.
Run at the audited SHA (the evidence branch adds only docs/evidence/GOLD-AUD-E/ files,
so every row below is identical on the evidence branch).
"""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[3]

# id, file, first line, last line, needle, group
ROWS = [
    ("S01", "docs/contracts/FALCON-TRON-TRIGGER-DISCOVERY.md", 1, 33, r"Discovery|Windowing", "PID"),
    ("S02", "docs/contracts/TRON-FALCON-CONTRACT.md", 3, 30, r"discovery|no new entries", "PID"),
    ("S03", "docs/governance/FALCON-DECISION-REGISTER.md", 23, 24, r"blocks new entries", "PID"),
    ("S04", "docs/architecture/01-FALCON-ARCHITECTURE.md", 45, 45, r"discovery", "PID"),
    ("S05", "docs/architecture/01-FALCON-ARCHITECTURE.md", 169, 170, r"discovered|no new TRON entry", "PID"),
    ("S06", "README.md", 63, 63, r"discovery", "PID"),
    ("S07", "pids/PID-05-HERMES-INTEGRATION.md", 99, 99, r"TRON discovers", "PID"),
    ("S08", "pids/PID-08-HELIOS-SIGNED-TRIGGERS.md", 12, 12, r"discovery", "PID"),
    ("S09", "pids/PID-08-HELIOS-SIGNED-TRIGGERS.md", 68, 68, r"Signed Trade Suggestion evidence", "PID"),
    ("S10", "pids/PID-09-TRON-PAPER-INTEGRATION.md", 1, 1, r"Discovery", "PID"),
    ("S11", "pids/PID-09-TRON-PAPER-INTEGRATION.md", 11, 11, r"discover", "PID"),
    ("S12", "pids/PID-09-TRON-PAPER-INTEGRATION.md", 32, 32, r"overlap polling", "PID"),
    ("S13", "pids/PID-09-TRON-PAPER-INTEGRATION.md", 34, 34, r"ingestion-lag gate", "PID"),
    ("S14", "pids/PID-09-TRON-PAPER-INTEGRATION.md", 62, 62, r"no new entry", "PID"),
    ("S15", "docs/operations/FALCON-OBSERVABILITY.md", 14, 14, r"trigger-discovery latency", "PID"),
    ("S16", "docs/engineering/FALCON-CAPACITY-MODEL.md", 22, 22, r"TRON discovery latency", "PID"),
    ("S17", "pids/PID-13-OBSERVABILITY-CAPACITY.md", 24, 24, r"TRON discovery latency", "PID"),
    ("S18", "docs/engineering/FALCON-PROD-PROMOTION-GATES.md", 8, 8, r"trigger discovery", "PID"),
    ("S19", "docs/graylog/FALCON-STREAM-INDEX-DESIGN.md", 13, 14, r"HELIOS Trade Suggestions", "PID"),
    ("S20", "registry/system_component_registry.v1.json", 35, 35, r"tron\.discovery_service", "PID"),
    ("S21", "registry/field_registry.v1.json", 1960, 1960, r"TRON discovery", "PID"),
    ("S22", "registry/field_registry.v1.json", 1979, 1979, r"TRON discovery", "PID"),
    ("X01", "docs/architecture/00-FALCON-PID.md", 81, 81, r"discovered", "AUDIT-FOUND"),
    ("X02", "docs/governance/FALCON-R2D2-BLUEPRINT.md", 10, 10, r"TRON trigger discovery", "AUDIT-FOUND"),
    ("X03", "docs/governance/FALCON-TEST-AND-ACCEPTANCE-PLAN.md", 15, 15, r"TRON discovery/dedupe", "AUDIT-FOUND"),
    ("X04", "docs/contracts/HELIOS-FALCON-CONTRACT.md", 29, 29, r"SL/TP", "AUDIT-FOUND"),
    ("X05", "tests/fixtures/valid/tron_trigger_observed.json", 6, 6, r"tron\.discovery_service", "AUDIT-FOUND"),
    ("X06", "tests/fixtures/valid/tron_admission_decision.json", 6, 6, r"tron\.discovery_service", "AUDIT-FOUND"),
    ("X07", "deploy/content-packs/falcon-pid03-ingestion-v1.json", 1466, 1466, r"tron\.discovery_service", "AUDIT-FOUND"),
    ("X08", "docs/governance/FALCON-DECISION-REGISTER.md", 56, 58, r"Trade Suggestions", "AUDIT-FOUND"),
    ("X09", "pids/PID-05-HERMES-INTEGRATION.md", 15, 18, r"NOT yet authorised", "AUDIT-FOUND"),
]


def main():
    bad = 0
    for rid, f, a, b, needle, grp in ROWS:
        p = ROOT / f
        if not p.is_file():
            print(f"{rid} MISSING FILE {f}")
            bad += 1
            continue
        lines = p.read_text(errors="ignore").splitlines()
        if b > len(lines):
            print(f"{rid} LINE RANGE {a}-{b} beyond end ({len(lines)}) in {f}")
            bad += 1
            continue
        seg = "\n".join(lines[a - 1:b])
        if not re.search(needle, seg):
            print(f"{rid} NEEDLE /{needle}/ not in {f}:{a}-{b}")
            bad += 1
    if bad == 0:
        print(f"EP-10 check PASSED: {len(ROWS)} rows, all line ranges and needles verified")
    S01 = (ROOT / "docs/contracts/FALCON-TRON-TRIGGER-DISCOVERY.md").read_text().splitlines()
    if len(S01) != 33:
        print(f"S01 whole-file claim wrong: file has {len(S01)} lines")
        bad += 1
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
