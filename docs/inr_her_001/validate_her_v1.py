"""Strict r4 schema gate for INR-HER-001 Phase 1.

Schemas may use only the keys enforced by the accepted ``schema_check`` vocabulary.
Every ``const`` carries a ``type``, so boolean and integer values do not coerce.
"""

from __future__ import annotations

import json
from pathlib import Path

from docs.inr_001.schema_check import check as schema_check

SCHEMA_DIR = Path(__file__).resolve().parent / "schema"
SCHEMA_FILES = {
    "inr.event.v0.r4": "inr_event_v0_r4.schema.json",
    "inr.supervisor.result.v0.r4": "inr_supervisor_result_v0_r4.schema.json",
    "inr.her.surface_record.v0": "inr_her_surface_record_v0.schema.json",
    "inr.her.predicate_result.v0": "inr_her_predicate_result_v0.schema.json",
}
ALLOWED_SCHEMA_KEYS = frozenset({
    "type", "const", "enum", "properties", "required", "additionalProperties",
    "items", "minItems", "minLength", "pattern",
})
R3_SCHEMA_VERSIONS = frozenset({
    "inr.event.v0.r3",
    "inr.supervisor.result.v0.r3",
    "inr.target_profile.v0",
    "inr.origin_reference_set.v0",
})
EVENT_SCHEMA_VERSION = "inr.event.v0.r4"


class HerSchemaContractError(ValueError):
    """A HER schema document is outside the Phase 1 vocabulary."""


class DuplicateJsonKey(ValueError):
    """JSON object repeats a key."""


def _pairs(pairs: list[tuple[object, object]]) -> dict:
    seen: set[object] = set()
    obj: dict = {}
    for key, value in pairs:
        if key in seen:
            raise DuplicateJsonKey(str(key))
        seen.add(key)
        obj[key] = value
    return obj


def parse_json(raw: str | bytes) -> object:
    """Parse strict JSON and reject duplicate object keys."""
    if isinstance(raw, bytes):
        text = raw.decode("utf-8")
    else:
        text = raw
    return json.loads(text, object_pairs_hook=_pairs, parse_constant=lambda _value: (_ for _ in ()).throw(ValueError("non-finite number")))


def assert_schema_contract(schema: object, path: str = "$") -> None:
    """Reject ignored keywords and untyped constants."""
    if type(schema) is not dict:
        raise HerSchemaContractError(path + ": schema node must be an object")
    extra = set(schema) - ALLOWED_SCHEMA_KEYS
    if extra:
        raise HerSchemaContractError(path + ": unsupported schema keys " + ",".join(sorted(extra)))
    if "const" in schema and "type" not in schema:
        raise HerSchemaContractError(path + ": const requires type")
    if "enum" in schema and "type" not in schema:
        raise HerSchemaContractError(path + ": enum requires type")
    if "pattern" in schema and schema.get("type") != "string":
        raise HerSchemaContractError(path + ": pattern requires type string")
    kind = schema.get("type")
    if kind == "object":
        if schema.get("additionalProperties") is not False:
            raise HerSchemaContractError(path + ": object requires additionalProperties false")
        properties = schema.get("properties", {})
        if type(properties) is not dict:
            raise HerSchemaContractError(path + ": properties must be an object")
        for name, child in properties.items():
            assert_schema_contract(child, path + "." + name)
    if "items" in schema:
        assert_schema_contract(schema["items"], path + "[]")


def load_schemas() -> dict[str, dict]:
    """Load the four role-separated r4 schemas."""
    loaded: dict[str, dict] = {}
    for schema_id, name in SCHEMA_FILES.items():
        text = (SCHEMA_DIR / name).read_text(encoding="utf-8")
        document = json.loads(text, object_pairs_hook=_pairs)
        assert_schema_contract(document)
        version = document["properties"]["schema_version"]["const"]
        if version != schema_id:
            raise HerSchemaContractError(name + ": schema_version const mismatch")
        loaded[schema_id] = document
    return loaded


def schema_errors(document: object) -> list[str]:
    """Return schema_check errors for one r4 event, including nested roles."""
    schemas = load_schemas()
    errors = schema_check(document, schemas[EVENT_SCHEMA_VERSION])
    if type(document) is not dict:
        return errors
    supervisor = document.get("supervisor_result")
    errors.extend(
        schema_check(supervisor, schemas["inr.supervisor.result.v0.r4"], "$.supervisor_result")
    )
    records = document.get("surface_records")
    if type(records) is list:
        for index, record in enumerate(records):
            errors.extend(
                schema_check(record, schemas["inr.her.surface_record.v0"], "$.surface_records[" + str(index) + "]")
            )
    return errors


def output_errors(result: object) -> list[str]:
    """Validate a derived predicate result against its schema."""
    return schema_check(result, load_schemas()["inr.her.predicate_result.v0"])
