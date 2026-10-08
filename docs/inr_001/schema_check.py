"""Strict checker for the small, code-owned INR JSON Schema vocabulary."""
from __future__ import annotations

import re


def check(value, schema, path="$", errors=None):
    errors = [] if errors is None else errors
    types = {"object": dict, "array": list, "string": str, "integer": int,
             "boolean": bool, "null": type(None)}
    kind = schema.get("type")
    if kind and type(value) is not types[kind]:
        errors.append(path + ": wrong type")
        return errors
    if "const" in schema and value != schema["const"]:
        errors.append(path + ": wrong constant")
    if "enum" in schema and value not in schema["enum"]:
        errors.append(path + ": outside enum")
    if type(value) is dict:
        properties = schema.get("properties", {})
        for key in schema.get("required", []):
            if key not in value:
                errors.append(path + ": missing " + key)
        if schema.get("additionalProperties") is False:
            for key in value.keys() - properties.keys():
                errors.append(path + ": unknown " + key)
        for key in value.keys() & properties.keys():
            check(value[key], properties[key], path + "." + key, errors)
    elif type(value) is list:
        if len(value) < schema.get("minItems", 0):
            errors.append(path + ": too few items")
        for i, item in enumerate(value):
            check(item, schema.get("items", {}), path + "[" + str(i) + "]", errors)
    elif type(value) is str:
        if len(value) < schema.get("minLength", 0):
            errors.append(path + ": empty string")
        if "pattern" in schema and re.fullmatch(schema["pattern"], value) is None:
            errors.append(path + ": invalid pattern")
    return errors
