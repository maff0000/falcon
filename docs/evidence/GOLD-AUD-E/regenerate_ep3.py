#!/usr/bin/env python3
"""Regenerate the EP-3 registry matrix of GOLD-AUD-E from repository sources.

Usage (from anywhere; paths resolve from this file's location):
    python3 docs/evidence/GOLD-AUD-E/regenerate_ep3.py            # print the table
    python3 docs/evidence/GOLD-AUD-E/regenerate_ep3.py --check    # diff vs committed table, exit 1 if different

Read-only. Stdlib only. Inputs: registry/event_family_registry.v1.json,
schemas/payloads/**, tests/fixtures/valid/*.json, and the pipeline rule
"FALCON - flag missing required payload fields" in
deploy/content-packs/falcon-pid03-ingestion-v1.json.
The 'emitting' and 'owner' columns are NOT derivable from the repository; they are
fixed annotations below, each with the source that supports it, and are the only
hand-maintained part of the table.
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
HERE = pathlib.Path(__file__).resolve().parent
COMMITTED = HERE / "EP-03-registry-matrix.table.md"

# family -> (emitting, emitting source, reconciliation owner)
EMITTING = {
    "ares.market_status.session_state": ("YES (point-in-time)", "docs/operations/FALCON-PID06-RUNTIME-ACCEPTANCE-EVIDENCE.md s3, s5"),
}
HERMES_NOTE = ("UNVERIFIED", "HERMES evidence existed on 2026-10-04 (PID06 evidence s7); family not named; steady state not verifiable from source")
HELIOS_NOTE = ("NO", "docs/architecture/PID07-HELIOS-STAGE1-DISCOVERY.md s2 (no FALCON publication code) and s10")
TRON_NOTE = ("NO", "no TRON publisher code found: tron main holds PID.md and a hook only; wo/WO-TRON-D1 holds design docs and schemas, and its event design is tron.event.v1, not the FalconEvent envelope (docs/09)")
ARES_OTHER = ("NO EVIDENCE", "PID06 evidence s12: no other ARES family delivered")

OWNER = {
    "helios.strategy_evaluated": "T1 (collapse, P-H2)",
    "helios.strategy_state": "T1 (survivor candidate, P-H2)",
    "helios.chain_state": "T1 (collapse, P-H2)",
    "helios.health": "T1 (ruling, P-H3)",
    "helios.strategy_trigger": "T3 (reshape to GOAL-TRIGGER-001, P-H4)",
}


def load():
    reg = json.loads((ROOT / "registry/event_family_registry.v1.json").read_text())
    fams = reg["live_families"]
    fixtures = {}
    for p in sorted((ROOT / "tests/fixtures/valid").glob("*.json")):
        d = json.loads(p.read_text())
        fixtures.setdefault(d.get("evidence_family"), []).append((p.name, d.get("retention_class")))
    cp = json.loads((ROOT / "deploy/content-packs/falcon-pid03-ingestion-v1.json").read_text())
    rule_src = ""
    for e in cp["entities"]:
        t = e.get("data", {}).get("title")
        t = t.get("@value") if isinstance(t, dict) else t
        if t == "FALCON - flag missing required payload fields":
            s = e["data"]["source"]
            rule_src = s.get("@value") if isinstance(s, dict) else s
    enforced = set(re.findall(r'evidence_family\) == "([a-z0-9_.]+)"', rule_src))
    return reg, fams, fixtures, enforced


def table():
    reg, fams, fixtures, enforced = load()
    rows = []
    hdr = ("| # | family | system | types | schema file present | required payload fields (registry / schema) | "
           "valid fixture (retention_class in fixture) | pipeline enforces required payload fields | emitting | emitting source | owner |")
    sep = "|---|---|---|---|---|---|---|---|---|---|---|"
    rows += [hdr, sep]
    for i, f in enumerate(fams, 1):
        fam, sysn = f["family"], f["system"]
        sp = ROOT / "schemas" / f["schema_file"]
        sch = json.loads(sp.read_text()) if sp.is_file() else {}
        n_reg = len(f.get("required_payload_fields", []))
        n_sch = len(sch.get("required", []))
        if fam in EMITTING:
            em, src = EMITTING[fam]
        elif sysn == "hermes":
            em, src = HERMES_NOTE
        elif sysn == "helios":
            em, src = HELIOS_NOTE
        elif sysn == "tron":
            em, src = TRON_NOTE
        else:
            em, src = ARES_OTHER
        owner = OWNER.get(fam)
        if owner is None:
            owner = "T3 (freeze or new, P-T2)" if sysn == "tron" else "no gap raised by E"
        rows.append("| {} | `{}` | {} | {} | {} | {} / {}{} | {} | {} | {} | {} | {} |".format(
            i, fam, sysn, ", ".join(f["registered_types"]),
            "yes" if sp.is_file() else "NO",
            n_reg, n_sch, "" if n_reg == n_sch else " (MISMATCH)",
            ("yes (" + ",".join(sorted({r for _, r in fixtures[fam]})) + ")") if fam in fixtures else "NO",
            "yes" if fam in enforced else "NO",
            em, src, owner))
    return "\n".join(rows) + "\n", len(fams)


def main():
    out, n = table()
    if "--check" in sys.argv:
        if not COMMITTED.is_file():
            print("committed table missing")
            return 1
        if COMMITTED.read_text() == out:
            print("EP-3 check PASSED: regenerated table equals committed table ({} rows)".format(n))
            return 0
        import difflib
        sys.stdout.writelines(difflib.unified_diff(COMMITTED.read_text().splitlines(1), out.splitlines(1), "committed", "regenerated"))
        return 1
    sys.stdout.write(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
