"""PID-05 Stage 3A -- deterministic generator for the
"FALCON - flag missing required payload fields" Graylog pipeline rule.

Root cause this exists to close: the live "FALCON Ingestion" pipeline's
"FALCON - flag missing required fields" rule only checks 6 hardcoded
ENVELOPE fields. It has never checked any family's own
`required_payload_fields` (registry/event_family_registry.v1.json) at
the payload level -- a real, pre-existing, universal gap affecting every
live family, not something specific to any one producer (see
pids/PID-05-HERMES-INTEGRATION.md, "MAJOR FINDING" under the Stage 1
live-verification section, and the new "Stage 3A" section appended to
that same document).

Graylog 7.1.9's pipeline rule DSL cannot read external JSON files at
message-processing time (confirmed empirically during PID-04/PID-05),
so there is no way for a live rule to consult the registry directly at
runtime. The only correct, drift-proof fix is to generate the DSL
literally, ahead of time, from the registry -- this module is that
generator. It must never be hand-duplicated: `deploy/content-packs/
falcon-pid03-ingestion-v1.json`'s "FALCON - flag missing required
payload fields" rule's `source` is expected to always be byte-identical
to this module's current output (enforced by
tests/test_generated_payload_requirements_rule.py).

Usage (standalone):

    python3 deploy/generate_payload_requirements_rule.py

prints the current generated rule source to stdout. Also importable:
`generate_rule_source()` / `families_with_required_fields()` are called
directly by the drift-guard test, with no subprocess involved.

Determinism: family order is the registry's own declared order in
`live_families` (registry/event_family_registry.v1.json is a single,
committed, ordered JSON array) -- not re-sorted alphabetically. Re-
running this generator against an unchanged registry always produces
byte-identical output.
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

RULE_TITLE = "FALCON - flag missing required payload fields"
RULE_DESCRIPTION = (
    "PID-05 Stage 3A: flags a message whose declared evidence_family has one "
    "or more registered required_payload_fields (registry/"
    "event_family_registry.v1.json) that are not present among this "
    "message's stage-0-derived payload_* fields. Generated deterministically "
    "from the registry by deploy/generate_payload_requirements_rule.py -- "
    "never hand-maintained; see that module and pids/"
    "PID-05-HERMES-INTEGRATION.md's Stage 3A section for the full "
    "root-cause/architecture writeup."
)
FLAG_FIELD = "falcon_missing_required_payload_field"


def _repo_root_from_here() -> str:
    # deploy/generate_payload_requirements_rule.py -> repo root is one level up.
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.abspath(os.path.join(here, ".."))


def load_registry(repo_root: Optional[str] = None) -> dict:
    root = repo_root or _repo_root_from_here()
    path = os.path.join(root, "registry", "event_family_registry.v1.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def families_with_required_fields(registry: dict) -> List[Dict[str, Any]]:
    """Live families with a non-empty `required_payload_fields` list, in
    the registry's own declared `live_families` order. A family whose
    `required_payload_fields` is missing or empty is deliberately
    excluded -- it must never get a clause, let alone a vacuous/
    always-false one (there would be nothing to check)."""
    out = []
    for entry in registry["live_families"]:
        fields = entry.get("required_payload_fields") or []
        if fields:
            out.append(entry)
    return out


def _field_check_clause(fields: List[str]) -> str:
    """The has_field-negation clause for one family's required payload
    fields. A single required field is emitted bare (no redundant extra
    parens); two or more are OR'd together inside one set of parens."""
    checks = [f'!has_field("payload_{name}")' for name in fields]
    if len(checks) == 1:
        return checks[0]
    return "(" + " || ".join(checks) + ")"


def _family_clause(family: str, fields: List[str]) -> str:
    return (
        f'(to_string($message.evidence_family) == "{family}" && '
        f'{_field_check_clause(fields)})'
    )


def generate_rule_source(registry: Optional[dict] = None, repo_root: Optional[str] = None) -> str:
    """Builds the complete Graylog pipeline rule DSL source for
    "FALCON - flag missing required payload fields", deterministically,
    from the registry. Does not touch the committed content pack file --
    callers (the drift-guard test, or a future re-embed script) decide
    what to do with the returned string."""
    if registry is None:
        registry = load_registry(repo_root)
    families = families_with_required_fields(registry)
    clauses = [_family_clause(entry["family"], entry["required_payload_fields"]) for entry in families]
    when_body = " ||\n    ".join(clauses)
    return (
        f'rule "{RULE_TITLE}"\n'
        f'when\n'
        f'    {when_body}\n'
        f'then\n'
        f'    set_field("{FLAG_FIELD}", true);\n'
        f'end'
    )


def main() -> int:
    print(generate_rule_source())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
