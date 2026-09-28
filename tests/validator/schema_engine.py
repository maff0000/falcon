"""Minimal, explicit JSON-Schema-subset engine (stdlib only).

Supports exactly the keywords used under schemas/: type, properties,
required, additionalProperties, enum, pattern, items, minItems, minLength,
minimum. This is intentionally not a general-purpose JSON Schema
implementation — it exists to validate this repository's own schemas, and
raises clearly if it meets a keyword/type it does not understand rather than
silently accepting or silently ignoring it.
"""
from __future__ import annotations

import re
from typing import Any, List


_SUPPORTED_TYPES = {"object", "array", "string", "integer", "number", "boolean"}


def validate_instance(instance: Any, schema: dict, path: str = "$") -> List[str]:
    """Validate `instance` against `schema`. Returns a list of human-readable
    error strings; an empty list means the instance is valid."""
    errors: List[str] = []
    t = schema.get("type")

    if t not in _SUPPORTED_TYPES:
        raise ValueError(f"schema_engine: unsupported/missing type {t!r} at {path}")

    if t == "object":
        if not isinstance(instance, dict):
            return [f"{path}: expected object, got {type(instance).__name__}"]
        props = schema.get("properties", {})
        required = schema.get("required", [])
        additional = schema.get("additionalProperties", True)
        for r in required:
            if r not in instance:
                errors.append(f"{path}: missing required field '{r}'")
        for k, v in instance.items():
            if k in props:
                errors.extend(validate_instance(v, props[k], f"{path}.{k}"))
            elif additional is False:
                errors.append(f"{path}: unregistered/unexpected field '{k}'")
        return errors

    if t == "array":
        if not isinstance(instance, list):
            return [f"{path}: expected array, got {type(instance).__name__}"]
        min_items = schema.get("minItems")
        if min_items is not None and len(instance) < min_items:
            errors.append(f"{path}: expected at least {min_items} item(s), got {len(instance)}")
        item_schema = schema.get("items")
        if item_schema is not None:
            for i, item in enumerate(instance):
                errors.extend(validate_instance(item, item_schema, f"{path}[{i}]"))
        return errors

    if t == "string":
        if not isinstance(instance, str):
            return [f"{path}: expected string, got {type(instance).__name__}"]
        min_length = schema.get("minLength")
        if min_length is not None and len(instance) < min_length:
            errors.append(f"{path}: string shorter than minLength {min_length}")
        pattern = schema.get("pattern")
        if pattern is not None and re.fullmatch(pattern, instance) is None:
            errors.append(f"{path}: value {instance!r} does not match required pattern {pattern}")
        enum = schema.get("enum")
        if enum is not None and instance not in enum:
            errors.append(f"{path}: value {instance!r} is not one of the registered values {enum}")
        return errors

    if t == "integer":
        if not isinstance(instance, int) or isinstance(instance, bool):
            return [f"{path}: expected integer, got {type(instance).__name__}"]
        minimum = schema.get("minimum")
        if minimum is not None and instance < minimum:
            errors.append(f"{path}: value {instance} is below minimum {minimum}")
        return errors

    if t == "number":
        if not isinstance(instance, (int, float)) or isinstance(instance, bool):
            return [f"{path}: expected number, got {type(instance).__name__}"]
        return errors

    if t == "boolean":
        if not isinstance(instance, bool):
            errors.append(f"{path}: expected boolean, got {type(instance).__name__}")
        return errors

    raise AssertionError("unreachable")  # pragma: no cover
