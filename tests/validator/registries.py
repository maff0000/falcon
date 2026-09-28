"""Loading of the FALCON registries and schemas from disk."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional


def _load_json(path: str) -> dict:
    with open(path, "r") as f:
        return json.load(f)


def _repo_root_from_here() -> str:
    # tests/validator/registries.py -> repo root is two levels up.
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.abspath(os.path.join(here, "..", ".."))


@dataclass
class Context:
    repo_root: str
    envelope_schema: dict
    systems: List[str]
    components: Dict[str, List[str]]
    component_shape_pattern: str
    fields_by_name: Dict[str, dict]
    families_by_key: Dict[str, dict]
    payload_schemas: Dict[str, dict] = field(default_factory=dict)

    def payload_schema_for(self, family_key: str) -> Optional[dict]:
        if family_key in self.payload_schemas:
            return self.payload_schemas[family_key]
        entry = self.families_by_key.get(family_key)
        if entry is None:
            return None
        schema_path = os.path.join(self.repo_root, "schemas", entry["schema_file"])
        schema = _load_json(schema_path)
        self.payload_schemas[family_key] = schema
        return schema


def load_context(repo_root: Optional[str] = None) -> Context:
    root = repo_root or _repo_root_from_here()

    envelope_schema = _load_json(
        os.path.join(root, "schemas", "falcon-event-envelope", "v1", "envelope.schema.json")
    )

    sysreg = _load_json(os.path.join(root, "registry", "system_component_registry.v1.json"))
    fieldreg = _load_json(os.path.join(root, "registry", "field_registry.v1.json"))
    famreg = _load_json(os.path.join(root, "registry", "event_family_registry.v1.json"))

    fields_by_name = {f["name"]: f for f in fieldreg["fields"]}
    families_by_key = {fam["family"]: fam for fam in famreg["live_families"]}

    return Context(
        repo_root=root,
        envelope_schema=envelope_schema,
        systems=sysreg["systems"],
        components=sysreg["components"],
        component_shape_pattern=sysreg["component_naming_rule"]["shape_pattern"],
        fields_by_name=fields_by_name,
        families_by_key=families_by_key,
    )
