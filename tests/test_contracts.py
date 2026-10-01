"""FALCON PID-01 contract/registry test suite.

Pure stdlib (unittest). Run with:

    python3 -m unittest discover -s tests -p "test_*.py" -v

from the repository root. No pip install is required.

Covers every proof required by PID-01 section 5.6 / docs/governance/
FALCON-TEST-AND-ACCEPTANCE-PLAN.md:
  - valid fixtures accepted;
  - missing/extra/wrong-type fields rejected;
  - naive timestamps rejected; valid UTC timestamps accepted;
  - unknown system/component/family/field rejected;
  - registered fields in schemas exist in the field registry and vice versa
    (no orphans either direction);
  - family schemas only use fields valid for that family per the field
    registry's allowed_families metadata;
  - revision/supersession structure is validated;
  - correlation_id and causation_id are validated as distinct fields;
  - an unregistered score_definition_id reference is rejected;
  - deterministic (running the suite twice gives identical results).
"""
from __future__ import annotations

import json
import os
import unittest

from tests.validator.registries import load_context
from tests.validator.rules import check_identity_law
from tests.validator.schema_engine import validate_instance
from tests.validator.validate import validate_event

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
VALID_DIR = os.path.join(REPO_ROOT, "tests", "fixtures", "valid")
INVALID_DIR = os.path.join(REPO_ROOT, "tests", "fixtures", "invalid")


def _load_json(path):
    with open(path) as f:
        return json.load(f)


def _load_fixture_dir(directory):
    out = {}
    for name in sorted(os.listdir(directory)):
        if not name.endswith(".json") or name == "MANIFEST.json":
            continue
        out[name] = _load_json(os.path.join(directory, name))
    return out


class ContractTestBase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ctx = load_context(REPO_ROOT)
        cls.valid_fixtures = _load_fixture_dir(VALID_DIR)
        cls.invalid_fixtures = _load_fixture_dir(INVALID_DIR)
        cls.manifest = _load_json(os.path.join(INVALID_DIR, "MANIFEST.json"))


class TestValidFixturesAccepted(ContractTestBase):
    def test_every_valid_fixture_validates_cleanly(self):
        for name, doc in self.valid_fixtures.items():
            with self.subTest(fixture=name):
                ok, errors = validate_event(doc, self.ctx)
                self.assertTrue(ok, f"{name} unexpectedly rejected: {errors}")

    def test_all_27_live_families_have_a_valid_fixture(self):
        families = {doc["evidence_family"] for doc in self.valid_fixtures.values()}
        registered = set(self.ctx.families_by_key.keys())
        self.assertEqual(families, registered)
        self.assertEqual(len(registered), 28)


class TestInvalidFixturesRejected(ContractTestBase):
    def test_manifest_covers_every_invalid_fixture(self):
        fixture_names = set(self.invalid_fixtures.keys())
        self.assertEqual(fixture_names, set(self.manifest.keys()))

    def test_every_invalid_fixture_is_rejected_for_its_documented_reason(self):
        for name, doc in self.invalid_fixtures.items():
            entry = self.manifest[name]
            with self.subTest(fixture=name, reason=entry["reason"]):
                if entry["check"] == "structural":
                    ok, errors = validate_event(doc, self.ctx)
                    self.assertFalse(ok, f"{name} should have been rejected but validated cleanly")
                elif entry["check"] == "identity_law":
                    paired = self.valid_fixtures[entry["paired_with"]]
                    # The fixture must be structurally valid on its own --
                    # it is ONLY invalid in combination with its pair.
                    ok_alone, _ = validate_event(doc, self.ctx)
                    self.assertTrue(ok_alone, f"{name} was expected to be structurally valid alone")
                    id_errors = check_identity_law([(entry["paired_with"], paired), (name, doc)])
                    self.assertTrue(id_errors, f"{name} should have triggered an identity law violation")
                else:
                    self.fail(f"unknown manifest check kind {entry['check']!r} for {name}")

    def test_specific_reason_categories_present(self):
        # sanity: make sure each of the mandated negative-test categories in
        # PID-01 section 5.7 is actually represented in the fixture set.
        required_substrings = [
            "unknown_producer_system.json",
            "unknown_component.json",
            "unknown_field.json",
            "bad_event_family.json",
            "wrong_type.json",
            "naive_timestamp.json",
            "non_utc_offset_timestamp.json",
            "missing_required_field.json",
            "causation_id_misused_as_correlation.json",
            "bad_supersession_self_reference.json",
            "unregistered_score_definition.json",
            "payload_field_outside_family.json",
            "identity_violation_reused_event_id.json",
        ]
        for fname in required_substrings:
            self.assertIn(fname, self.invalid_fixtures, f"missing required negative fixture {fname}")


class TestTemporalLaw(ContractTestBase):
    def test_naive_timestamp_rejected(self):
        doc = self.invalid_fixtures["naive_timestamp.json"]
        ok, errors = validate_event(doc, self.ctx)
        self.assertFalse(ok)
        self.assertTrue(any("produced_at_utc" in e for e in errors), errors)

    def test_non_utc_offset_rejected(self):
        doc = self.invalid_fixtures["non_utc_offset_timestamp.json"]
        ok, errors = validate_event(doc, self.ctx)
        self.assertFalse(ok)
        self.assertTrue(any("produced_at_utc" in e for e in errors), errors)

    def test_valid_utc_z_and_offset_forms_both_accepted(self):
        base = self.valid_fixtures["hermes_market_fact.json"]
        for value in ("2026-09-28T08:00:00Z", "2026-09-28T08:00:00+00:00", "2026-09-28T08:00:00.123456Z"):
            doc = dict(base)
            doc["produced_at_utc"] = value
            errors = validate_instance(doc, self.ctx.envelope_schema)
            self.assertEqual(errors, [], f"{value} should be accepted: {errors}")


class TestRegistryConsistency(ContractTestBase):
    """Static consistency checks over the schemas/registry artefacts
    themselves (not any single instance fixture)."""

    def _all_schema_field_names(self):
        names = set(self.ctx.envelope_schema["properties"].keys())
        for fam, entry in self.ctx.families_by_key.items():
            schema = self.ctx.payload_schema_for(fam)
            names |= set(schema["properties"].keys())
        return names

    def test_every_schema_field_is_registered(self):
        schema_fields = self._all_schema_field_names()
        registered = set(self.ctx.fields_by_name.keys())
        missing = schema_fields - registered
        self.assertEqual(missing, set(), f"fields used in schemas but not registered: {missing}")

    def test_every_registered_field_is_used_by_some_schema(self):
        schema_fields = self._all_schema_field_names()
        registered = set(self.ctx.fields_by_name.keys())
        orphans = registered - schema_fields
        self.assertEqual(orphans, set(), f"registered fields never used by any schema: {orphans}")

    def test_family_schemas_only_use_fields_allowed_for_that_family(self):
        for fam, entry in self.ctx.families_by_key.items():
            schema = self.ctx.payload_schema_for(fam)
            for field_name in schema["properties"].keys():
                info = self.ctx.fields_by_name[field_name]
                allowed = info.get("allowed_families") or []
                with self.subTest(family=fam, field=field_name):
                    self.assertTrue(
                        "*" in allowed or fam in allowed,
                        f"field '{field_name}' used by payload schema for '{fam}' but "
                        f"field registry only allows {allowed}",
                    )

    def test_no_duplicate_field_names_across_scopes(self):
        # every field name in the registry must be unique (no accidental
        # duplicate registrations of the same canonical name).
        fieldreg_path = os.path.join(REPO_ROOT, "registry", "field_registry.v1.json")
        raw = _load_json(fieldreg_path)
        names = [f["name"] for f in raw["fields"]]
        self.assertEqual(len(names), len(set(names)), "duplicate field name(s) in field registry")

    def test_reserved_not_live_families_are_not_registered(self):
        raw = _load_json(os.path.join(REPO_ROOT, "registry", "event_family_registry.v1.json"))
        live = {f["family"] for f in raw["live_families"]}
        for reserved in raw["reserved_not_live"]:
            with self.subTest(family=reserved):
                self.assertNotIn(reserved, live)
        self.assertIn("ares.regime.nowcast", raw["reserved_not_live"])

    def test_required_payload_fields_matches_schema_required(self):
        # PID-05 Stage 3A governed invariant: event_family_registry.v1.json's
        # required_payload_fields now drives LIVE quarantine behaviour (via
        # deploy/generate_payload_requirements_rule.py), while each family's
        # payload JSON Schema `required` array independently drives the
        # offline PID-01 validator. These are two representations of the
        # same fact and must never silently disagree -- a registry edit
        # without updating its schema (or vice versa) must fail here, not
        # ship as a live/offline semantic split. Order-independent
        # (set equality): both representations declare an unordered set of
        # mandatory field names, not a sequence.
        for fam, entry in self.ctx.families_by_key.items():
            registry_required = set(entry.get("required_payload_fields") or [])
            schema_required = set(self.ctx.payload_schema_for(fam).get("required") or [])
            with self.subTest(family=fam):
                self.assertEqual(
                    registry_required, schema_required,
                    f"family '{fam}': registry required_payload_fields {sorted(registry_required)} "
                    f"!= schema required {sorted(schema_required)} -- these two authorities have "
                    f"drifted apart; live enforcement and offline PID-01 validation would silently "
                    f"disagree on what this family's payload must contain",
                )


class TestIdentityLaw(ContractTestBase):
    def test_identical_payload_distinct_event_ids_both_legitimate(self):
        a = self.valid_fixtures["hermes_health_heartbeat_a.json"]
        b = self.valid_fixtures["hermes_health_heartbeat_b.json"]
        self.assertNotEqual(a["falcon_event_id"], b["falcon_event_id"])
        self.assertEqual(a["payload"], b["payload"])
        self.assertEqual(a["payload_hash"], b["payload_hash"])
        ok_a, _ = validate_event(a, self.ctx)
        ok_b, _ = validate_event(b, self.ctx)
        self.assertTrue(ok_a and ok_b)
        errors = check_identity_law([
            ("hermes_health_heartbeat_a.json", a),
            ("hermes_health_heartbeat_b.json", b),
        ])
        self.assertEqual(errors, [], "identical payload + distinct ids must NOT be an identity violation")

    def test_reused_event_id_with_different_payload_is_a_violation(self):
        a = self.valid_fixtures["hermes_health_heartbeat_a.json"]
        bad = self.invalid_fixtures["identity_violation_reused_event_id.json"]
        self.assertEqual(a["falcon_event_id"], bad["falcon_event_id"])
        self.assertNotEqual(a["payload"], bad["payload"])
        errors = check_identity_law([
            ("hermes_health_heartbeat_a.json", a),
            ("identity_violation_reused_event_id.json", bad),
        ])
        self.assertTrue(errors)

    def test_full_valid_corpus_has_no_identity_violations(self):
        events = list(self.valid_fixtures.items())
        errors = check_identity_law(events)
        self.assertEqual(errors, [])


class TestCorrelationVsCausation(ContractTestBase):
    def test_causation_id_must_be_a_falcon_event_id_shape(self):
        doc = self.invalid_fixtures["causation_id_misused_as_correlation.json"]
        ok, errors = validate_event(doc, self.ctx)
        self.assertFalse(ok)
        self.assertTrue(any("causation_id" in e for e in errors), errors)

    def test_correlation_and_causation_can_coexist_with_distinct_shapes(self):
        doc = self.valid_fixtures["helios_strategy_trigger.json"]
        self.assertIn("correlation_id", doc)
        self.assertIn("causation_id", doc)
        self.assertNotEqual(doc["correlation_id"], doc["causation_id"])
        ok, errors = validate_event(doc, self.ctx)
        self.assertTrue(ok, errors)


class TestRevisionSupersession(ContractTestBase):
    def test_self_supersession_rejected(self):
        doc = self.invalid_fixtures["bad_supersession_self_reference.json"]
        ok, errors = validate_event(doc, self.ctx)
        self.assertFalse(ok)
        self.assertTrue(any("supersedes_event_id" in e for e in errors), errors)

    def test_well_formed_supersession_accepted(self):
        import copy
        doc = copy.deepcopy(self.valid_fixtures["hermes_market_quality.json"])
        doc["falcon_event_id"] = "00000000-0000-4000-8000-0000000000ff"
        doc["supersedes_event_id"] = self.valid_fixtures["hermes_market_quality.json"]["falcon_event_id"]
        ok, errors = validate_event(doc, self.ctx)
        self.assertTrue(ok, errors)


class TestScoreDefinitionGovernance(ContractTestBase):
    def test_unregistered_score_definition_rejected(self):
        doc = self.invalid_fixtures["unregistered_score_definition.json"]
        ok, errors = validate_event(doc, self.ctx)
        self.assertFalse(ok)
        self.assertTrue(any("score_definition_id" in e for e in errors), errors)

    def test_registered_score_definition_accepted(self):
        doc = self.valid_fixtures["helios_strategy_trigger.json"]
        self.assertIn("score_value", doc["payload"])
        self.assertIn(doc["payload"]["score_definition_id"], ["helios.entry_confidence.v1", "helios.exit_confidence.v1"])
        ok, errors = validate_event(doc, self.ctx)
        self.assertTrue(ok, errors)


class TestCompatibilityVersioning(ContractTestBase):
    def test_all_fixtures_declare_v1_envelope_and_payload_schema_version(self):
        for name, doc in {**self.valid_fixtures, **self.invalid_fixtures}.items():
            with self.subTest(fixture=name):
                if "envelope_version" in doc:
                    self.assertEqual(doc["envelope_version"], "v1")
                if "payload_schema_version" in doc:
                    self.assertEqual(doc["payload_schema_version"], "v1")

    def test_every_payload_schema_file_lives_under_its_declared_v1_directory(self):
        raw = _load_json(os.path.join(REPO_ROOT, "registry", "event_family_registry.v1.json"))
        for entry in raw["live_families"]:
            with self.subTest(family=entry["family"]):
                self.assertTrue(entry["schema_file"].endswith(".v1.schema.json"))
                self.assertTrue(os.path.isfile(os.path.join(REPO_ROOT, "schemas", entry["schema_file"])))


class TestDeterminism(ContractTestBase):
    def test_full_suite_validation_is_deterministic(self):
        def run_once():
            results = {}
            for name, doc in self.valid_fixtures.items():
                results[name] = validate_event(doc, self.ctx)
            for name, doc in self.invalid_fixtures.items():
                entry = self.manifest[name]
                if entry["check"] == "structural":
                    results[name] = validate_event(doc, self.ctx)
            results["__identity__"] = tuple(check_identity_law(list(self.valid_fixtures.items())))
            return results

        first = run_once()
        second = run_once()
        self.assertEqual(first, second)


class TestComponentIdShape(ContractTestBase):
    def test_hostname_or_container_shaped_component_id_rejected(self):
        import copy
        doc = copy.deepcopy(self.valid_fixtures["hermes_market_fact.json"])
        doc["producer_component_id"] = "a1b2c3d4e5f6"  # docker-style hex id, no registry entry either
        ok, errors = validate_event(doc, self.ctx)
        self.assertFalse(ok)

    def test_graylog_referencing_component_id_rejected(self):
        import copy
        doc = copy.deepcopy(self.valid_fixtures["hermes_market_fact.json"])
        doc["producer_component_id"] = "hermes.graylog_stream_42"
        ok, errors = validate_event(doc, self.ctx)
        self.assertFalse(ok)
        self.assertTrue(any("graylog" in e.lower() for e in errors), errors)


if __name__ == "__main__":
    unittest.main()
