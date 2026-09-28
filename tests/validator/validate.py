"""Orchestration: validate a single FalconEvent document end to end."""
from __future__ import annotations

from typing import List, Tuple

from . import rules
from .registries import Context
from .schema_engine import validate_instance


def validate_event(doc: dict, ctx: Context) -> Tuple[bool, List[str]]:
    errors: List[str] = []

    errors.extend(validate_instance(doc, ctx.envelope_schema))

    producer_system_id = doc.get("producer_system_id")
    producer_component_id = doc.get("producer_component_id")
    evidence_family = doc.get("evidence_family")
    evidence_type = doc.get("evidence_type")
    payload = doc.get("payload")

    if isinstance(producer_system_id, str) and producer_system_id not in ctx.systems:
        errors.append(
            f"$.producer_system_id: '{producer_system_id}' is not a registered "
            f"FALCON system (registered: {ctx.systems})"
        )

    if isinstance(producer_component_id, str):
        errors.extend(rules.check_component_id_shape(producer_component_id, ctx.component_shape_pattern))
        known_components = ctx.components.get(producer_system_id, [])
        if producer_component_id not in known_components:
            errors.append(
                f"$.producer_component_id: '{producer_component_id}' is not registered "
                f"for system '{producer_system_id}' (registered: {known_components})"
            )

    family_entry = ctx.families_by_key.get(evidence_family) if isinstance(evidence_family, str) else None
    if family_entry is None:
        errors.append(
            f"$.evidence_family: '{evidence_family}' is not a registered live FALCON "
            f"event family"
        )
    else:
        registered_types = family_entry.get("registered_types", [])
        if evidence_type not in registered_types:
            errors.append(
                f"$.evidence_type: '{evidence_type}' is not a registered type for "
                f"family '{evidence_family}' (registered: {registered_types})"
            )
        if isinstance(payload, dict):
            payload_schema = ctx.payload_schema_for(evidence_family)
            if payload_schema is not None:
                errors.extend(validate_instance(payload, payload_schema, "$.payload"))
                errors.extend(rules.check_family_field_scope(evidence_family, payload, ctx.fields_by_name))
                if evidence_family == "helios.strategy_trigger":
                    errors.extend(rules.check_score_definition(payload, ctx.fields_by_name))

    errors.extend(rules.check_no_self_supersession(doc))

    return (len(errors) == 0, errors)
