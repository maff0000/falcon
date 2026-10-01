"""PID-05 Stage 3A -- CI drift guard for the generated
"FALCON - flag missing required payload fields" pipeline rule.

This is the enforced invariant that makes "the content pack's payload-
required-field rule tracks the registry, not a hand-maintained copy of
it" an actual CI fact rather than a convention someone can quietly
drift away from: if a future change edits a family's
`required_payload_fields` in registry/event_family_registry.v1.json
without regenerating and re-embedding the rule into
deploy/content-packs/falcon-pid03-ingestion-v1.json
(deploy/generate_payload_requirements_rule.py), this test fails.

Pure stdlib (unittest), run as part of the normal suite:

    python3 -m unittest discover -s tests -p "test_*.py" -v

No pip install, no live Graylog stack required -- this only reads
static repo files.
"""
from __future__ import annotations

import json
import os
import unittest

import deploy.generate_payload_requirements_rule as gen

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CONTENT_PACK_PATH = os.path.join(
    REPO_ROOT, "deploy", "content-packs", "falcon-pid03-ingestion-v1.json"
)
REGISTRY_PATH = os.path.join(REPO_ROOT, "registry", "event_family_registry.v1.json")


def _load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _find_pipeline_rule_entity(content_pack: dict, title: str) -> dict:
    matches = []
    for entity in content_pack["entities"]:
        if entity.get("type", {}).get("name") != "pipeline_rule":
            continue
        data = entity.get("data", {})
        entity_title = data.get("title", {})
        tval = entity_title.get("@value") if isinstance(entity_title, dict) else entity_title
        if tval == title:
            matches.append(entity)
    return matches


class TestGeneratedPayloadRequirementsRuleNoDrift(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = _load_json(REGISTRY_PATH)
        cls.content_pack = _load_json(CONTENT_PACK_PATH)

    def test_exactly_one_rule_entity_with_the_expected_title(self):
        matches = _find_pipeline_rule_entity(self.content_pack, gen.RULE_TITLE)
        self.assertEqual(
            len(matches), 1,
            f"expected exactly one pipeline_rule entity titled {gen.RULE_TITLE!r}, found {len(matches)}",
        )

    def test_committed_rule_source_matches_generator_output_byte_for_byte(self):
        """The whole point of the generator: the registry is the single
        source of truth, and the committed content pack must always be
        its current, regenerated projection -- never hand-edited out of
        sync with it."""
        expected = gen.generate_rule_source(registry=self.registry)
        [entity] = _find_pipeline_rule_entity(self.content_pack, gen.RULE_TITLE)
        actual = entity["data"]["source"]["@value"]
        self.assertEqual(
            actual, expected,
            "committed 'FALCON - flag missing required payload fields' rule source has "
            "drifted from what deploy/generate_payload_requirements_rule.py currently "
            "produces from the registry -- regenerate and re-embed it.",
        )

    def test_pipeline_wires_the_new_rule_into_stage_1(self):
        [pipeline] = [
            e for e in self.content_pack["entities"]
            if e.get("type", {}).get("name") == "pipeline"
        ]
        pipeline_source = pipeline["data"]["source"]["@value"]
        self.assertIn(f'rule "{gen.RULE_TITLE}"', pipeline_source)

    def test_flag_wired_into_quarantine_router_and_every_valid_routing_rule(self):
        """falcon_missing_required_payload_field must gate quarantine AND
        be negated as a precondition in every one of the 6 'route valid
        <X> evidence' rules -- missing even one would let that
        producer's otherwise-invalid events through."""
        flag_check = (
            f'(has_field("{gen.FLAG_FIELD}") && to_bool($message.{gen.FLAG_FIELD}))'
        )
        routing_titles = [
            "FALCON - route INVALID to Quarantine",
            "FALCON - route valid HERMES evidence",
            "FALCON - route valid ARES evidence",
            "FALCON - route valid HELIOS evidence",
            "FALCON - route valid HELIOS Trade Suggestions",
            "FALCON - route valid TRON evidence",
            "FALCON - route valid Operational Health evidence",
        ]
        for title in routing_titles:
            with self.subTest(rule=title):
                matches = _find_pipeline_rule_entity(self.content_pack, title)
                self.assertEqual(len(matches), 1, f"expected exactly one rule titled {title!r}")
                source = matches[0]["data"]["source"]["@value"]
                self.assertIn(
                    flag_check, source,
                    f"{title!r} does not check {gen.FLAG_FIELD} -- a message missing a "
                    f"required payload field could be routed as if it were valid",
                )

    def test_every_live_family_has_a_clause_iff_it_has_required_payload_fields(self):
        """No vacuous/always-false clause for a family with zero required
        payload fields, and no silently-missing clause for a family that
        does have some."""
        [entity] = _find_pipeline_rule_entity(self.content_pack, gen.RULE_TITLE)
        rule_source = entity["data"]["source"]["@value"]
        for family_entry in self.registry["live_families"]:
            family = family_entry["family"]
            required_fields = family_entry.get("required_payload_fields") or []
            family_mentioned = f'"{family}"' in rule_source
            with self.subTest(family=family):
                self.assertEqual(
                    family_mentioned, bool(required_fields),
                    f"family {family!r} has required_payload_fields={required_fields!r} but "
                    f"{'is missing its clause' if required_fields else 'unexpectedly has a clause'} "
                    f"in the generated rule",
                )

    def test_generator_output_is_deterministic(self):
        first = gen.generate_rule_source(registry=self.registry)
        second = gen.generate_rule_source(registry=self.registry)
        self.assertEqual(first, second)

    def test_content_pack_rev_is_at_least_5(self):
        self.assertGreaterEqual(
            self.content_pack["rev"], 5,
            "content pack rev was not bumped for the Stage 3A payload-field-enforcement change",
        )


if __name__ == "__main__":
    unittest.main()
