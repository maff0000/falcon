"""FALCON PID-01 offline contract validator.

Deliberately stdlib-only (no third-party dependency, e.g. no `jsonschema`
package). Rationale (see PID-01 report for full reasoning):

  - a prior related project in this organisation (HELIOS) uses `jsonschema`
    only as a one-off meta-schema sanity check in a test, not as its runtime
    instance validator, which is a signal of house preference for a
    hand-rolled instance validator here too;
  - most of what this PID actually needs to prove (the immutable-identity
    law, decimal-string precision, field-registry cross-checks, family-
    scoped field allow-lists, score/definition pairing, UTC-only timestamps,
    correlation/causation distinctness) is bespoke domain logic that a
    generic JSON Schema library would not express on its own anyway, so
    adding the dependency would only cover a fraction of the required
    checks and CI would still need custom Python for the rest;
  - a stdlib-only validator has zero install step on a plain ubuntu-latest
    GitHub Actions runner (not even `pip install` is required to run the
    whole suite via `python3 -m unittest`), which keeps CI fast and
    dependency-light as requested.

This package implements a small, explicit subset of JSON Schema (type,
required, properties, additionalProperties, enum, pattern, items, minItems,
minLength, minimum) sufficient for every schema in schemas/, plus the
FALCON-specific semantic rules layered on top.
"""
