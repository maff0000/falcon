"""Standalone CLI entry point: validate every fixture in tests/fixtures and
print a report. Usable by a developer directly, and is what CI invokes.

Usage: python3 -m tests.validator.cli
Exit code 0 iff every valid/ fixture passes AND every invalid/ fixture fails
(for the reason recorded in tests/fixtures/invalid/MANIFEST.json), and the
cross-fixture identity law holds over tests/fixtures/valid.
"""
from __future__ import annotations

import json
import os
import sys

from .registries import load_context
from .rules import check_identity_law
from .validate import validate_event


def _repo_root() -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.abspath(os.path.join(here, "..", ".."))


def _load_fixtures(directory: str):
    out = []
    for name in sorted(os.listdir(directory)):
        if not name.endswith(".json") or name == "MANIFEST.json":
            continue
        with open(os.path.join(directory, name)) as f:
            out.append((name, json.load(f)))
    return out


def _load_manifest(invalid_dir: str) -> dict:
    with open(os.path.join(invalid_dir, "MANIFEST.json")) as f:
        return json.load(f)


def main() -> int:
    root = _repo_root()
    ctx = load_context(root)

    valid_dir = os.path.join(root, "tests", "fixtures", "valid")
    invalid_dir = os.path.join(root, "tests", "fixtures", "invalid")

    valid_fixtures = _load_fixtures(valid_dir)
    invalid_fixtures = _load_fixtures(invalid_dir)
    manifest = _load_manifest(invalid_dir)
    valid_by_name = dict(valid_fixtures)

    failures = 0

    print(f"== valid fixtures ({len(valid_fixtures)}) ==")
    for name, doc in valid_fixtures:
        ok, errors = validate_event(doc, ctx)
        status = "PASS" if ok else "FAIL"
        if not ok:
            failures += 1
        print(f"[{status}] {name}")
        for e in errors:
            print(f"    - {e}")

    print(f"\n== identity law over valid fixtures ==")
    id_errors = check_identity_law(valid_fixtures)
    if id_errors:
        failures += len(id_errors)
        for e in id_errors:
            print(f"[FAIL] {e}")
    else:
        print("[PASS] no identity violations among valid fixtures")

    print(f"\n== invalid fixtures ({len(invalid_fixtures)}) — each MUST be rejected ==")
    for name, doc in invalid_fixtures:
        entry = manifest.get(name, {})
        check_kind = entry.get("check", "structural")

        if check_kind == "structural":
            ok, errors = validate_event(doc, ctx)
            rejected = not ok
        elif check_kind == "identity_law":
            paired_name = entry["paired_with"]
            paired_doc = valid_by_name[paired_name]
            errors = check_identity_law([(paired_name, paired_doc), (name, doc)])
            rejected = len(errors) > 0
        else:
            raise ValueError(f"unknown manifest check kind {check_kind!r} for {name}")

        status = "PASS (correctly rejected)" if rejected else "FAIL (should have been rejected but was accepted)"
        if not rejected:
            failures += 1
        print(f"[{status}] {name} :: {entry.get('reason', '(no reason recorded)')}")
        for e in errors:
            print(f"    - {e}")

    print(f"\n{'ALL CHECKS PASSED' if failures == 0 else f'{failures} CHECK(S) FAILED'}")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
