"""FALCON-specific semantic rules that plain structural schema validation
cannot express (identity law, component-id shape, family-scoped fields,
score/definition pairing, supersession self-reference).
"""
from __future__ import annotations

import re
from typing import Dict, Iterable, List, Tuple

_HEX_ONLY_RE = re.compile(r"^[0-9a-f]{8,}$")


def check_component_id_shape(component_id: str, shape_pattern: str) -> List[str]:
    errors = []
    if not re.match(shape_pattern, component_id):
        errors.append(
            f"$.producer_component_id: '{component_id}' does not match the required "
            f"'system.component_name' shape ({shape_pattern})"
        )
    bare = component_id.replace(".", "").replace("_", "")
    if _HEX_ONLY_RE.match(bare):
        errors.append(
            f"$.producer_component_id: '{component_id}' looks like a hex/container "
            f"id, not a stable semantic component identity"
        )
    if "graylog" in component_id.lower():
        errors.append(
            f"$.producer_component_id: '{component_id}' must not reference Graylog "
            f"internals (stream/index/message ids are forbidden as producer identity)"
        )
    return errors


def check_no_self_supersession(doc: dict) -> List[str]:
    sup = doc.get("supersedes_event_id")
    if sup is not None and sup == doc.get("falcon_event_id"):
        return [f"$.supersedes_event_id: an event cannot supersede itself ('{sup}')"]
    return []


def check_family_field_scope(family_key: str, payload: dict, fields_by_name: Dict[str, dict]) -> List[str]:
    """Every key actually present in `payload` must be registered for this
    family in the field registry's allowed_families (or globally, '*')."""
    errors = []
    for key in payload.keys():
        info = fields_by_name.get(key)
        if info is None:
            continue  # unregistered-field case is reported by schema_engine (additionalProperties)
        allowed = info.get("allowed_families") or []
        if "*" in allowed:
            continue
        if family_key not in allowed:
            errors.append(
                f"$.payload.{key}: field is registered for {allowed}, not for family "
                f"'{family_key}' (field registry allowed_families violation)"
            )
    return errors


def check_score_definition(payload: dict, fields_by_name: Dict[str, dict]) -> List[str]:
    if "score_value" not in payload:
        return []
    errors = []
    sdid = payload.get("score_definition_id")
    if not sdid:
        errors.append(
            "$.payload.score_definition_id: required whenever $.payload.score_value "
            "is present (a score is never ungoverned)"
        )
        return errors
    allowed = (fields_by_name.get("score_definition_id") or {}).get("enum") or []
    if sdid not in allowed:
        errors.append(
            f"$.payload.score_definition_id: '{sdid}' is not a registered score "
            f"definition (registered: {allowed})"
        )
    return errors


def check_identity_law(events: Iterable[Tuple[str, dict]]) -> List[str]:
    """Cross-event identity law: falcon_event_id is immutable identity, not a
    payload hash. Two events sharing a falcon_event_id must carry identical
    payload/payload_hash (legitimate retry of the SAME evidence). Two events
    with different falcon_event_id may freely carry identical payload
    (legitimate distinct heartbeats/facts) — that case is NOT an error.
    """
    errors: List[str] = []
    seen: Dict[str, Tuple[str, object, object]] = {}
    for name, doc in events:
        eid = doc.get("falcon_event_id")
        if eid is None:
            continue
        phash = doc.get("payload_hash")
        payload = doc.get("payload")
        if eid in seen:
            prev_name, prev_hash, prev_payload = seen[eid]
            if prev_payload != payload or prev_hash != phash:
                errors.append(
                    f"identity violation: falcon_event_id '{eid}' is reused by "
                    f"'{prev_name}' and '{name}' with different payload/payload_hash. "
                    f"payload_hash is integrity data, not event identity — a reused "
                    f"falcon_event_id must always carry the same payload."
                )
        else:
            seen[eid] = (name, phash, payload)
    return errors
