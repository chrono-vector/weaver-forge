"""Strict schemas, enums, and parsers for WVMA-V1 Batch A1."""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping

from wvma_v1.canonical import canonical_digest, digest_excluding_field

# Omitted optional constructor/parser parameter. Explicit None is PRESENT-invalid.
ABSENT = object()

CATALOG_SCHEMA_VERSION = "wvma_v1.catalog.v1"
RESULT_SCHEMA_VERSION = "wvma_v1.result.v1"
STATUS_SCHEMA_VERSION = "wvma_v1.status.v1"
ORACLE_SCHEMA_VERSION = "wvma_v1.oracle_result.v1"
FINALIZE_INTENT_SCHEMA_VERSION = "wvma_v1.finalize_intent.v1"

ALLOWED_OPERATION_ENUMS = frozenset(
    {
        "SET_JSON_POINTER",
        "DELETE_JSON_POINTER",
        "ADD_DECLARED_FILE",
        "DELETE_DECLARED_FILE",
        "REPLACE_EXACT_BYTES",
        "REBIND_DECLARED_HASHES",
    }
)

ALLOWED_MATERIALITY = frozenset({"MATERIAL", "NON_MATERIAL"})

SET_LIKE_FIELDS = frozenset(
    {
        "target_paths",
        "target_entry_points",
        "critical_case_ids",
        "oracle_observations",
        "blocking_case_ids",
        "filesystem_observations",
        "digest_observations",
        "errors",
        "observations",
    }
)


class SchemaError(ValueError):
    """Strict schema rejection."""


class CatalogError(SchemaError):
    """Catalog-specific schema or digest rejection."""


def _reject_duplicate_json_keys(
    pairs: list[tuple[Any, Any]],
) -> dict[str, Any]:
    """object_pairs_hook: reject duplicate JSON object member names."""
    out: dict[str, Any] = {}
    for key, value in pairs:
        if not isinstance(key, str):
            raise SchemaError(
                f"JSON object keys must be str; got {type(key).__name__}"
            )
        if key in out:
            raise SchemaError(f"duplicate JSON object key: {key}")
        out[key] = value
    return out


def loads_strict_json(text: str) -> Any:
    """Parse JSON text; duplicate object keys are rejected before mapping use."""
    try:
        return json.loads(text, object_pairs_hook=_reject_duplicate_json_keys)
    except json.JSONDecodeError as exc:
        raise SchemaError(f"invalid JSON: {exc}") from exc


def load_strict_json(path: str | Path) -> Any:
    """Load JSON from a path with duplicate-key rejection."""
    with open(path, "r", encoding="utf-8") as fh:
        return loads_strict_json(fh.read())


class ResultClass(str, Enum):
    DETECTED = "DETECTED"
    SURVIVED = "SURVIVED"
    INVALID_MUTANT = "INVALID_MUTANT"
    APPLY_ERROR = "APPLY_ERROR"
    EXECUTION_ERROR = "EXECUTION_ERROR"
    ORACLE_ERROR = "ORACLE_ERROR"
    MISSING_RESULT = "MISSING_RESULT"


class AttemptState(str, Enum):
    NOT_CONFIGURED = "NOT_CONFIGURED"
    CATALOG_SEALED = "CATALOG_SEALED"
    RUN_IN_PROGRESS = "RUN_IN_PROGRESS"
    RUN_COMPLETE = "RUN_COMPLETE"
    RUN_INCOMPLETE = "RUN_INCOMPLETE"
    RUN_INVALID = "RUN_INVALID"


class AttemptVerdict(str, Enum):
    ALL_CRITICAL_DETECTED = "ALL_CRITICAL_DETECTED"
    CRITICAL_SURVIVOR = "CRITICAL_SURVIVOR"


def _stable_item_key(item: Any) -> str:
    if isinstance(item, str):
        return item
    return json.dumps(item, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _normalize_set_like(items: list[Any]) -> list[Any]:
    seen: set[str] = set()
    unique: list[Any] = []
    for item in items:
        key = _stable_item_key(item)
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return sorted(unique, key=_stable_item_key)


def _require_mapping(value: Any, field: str) -> dict[str, Any]:
    if value is None:
        raise SchemaError(f"{field} is PRESENT-invalid: null")
    if isinstance(value, bool) or not isinstance(value, Mapping):
        raise SchemaError(
            f"{field} must be a mapping; got {type(value).__name__}"
        )
    return {str(k): v for k, v in value.items()}


def _reject_unknown(data: Mapping[str, Any], allowed: set[str], label: str) -> None:
    unknown = sorted(set(data.keys()) - allowed)
    if unknown:
        raise SchemaError(f"{label} has unknown fields: {unknown}")


def _require_keys(data: Mapping[str, Any], required: set[str], label: str) -> None:
    missing = sorted(required - set(data.keys()))
    if missing:
        raise SchemaError(f"{label} missing fields: {missing}")


def _require_str(value: Any, field: str) -> str:
    if value is None:
        raise SchemaError(f"{field} is PRESENT-invalid: null")
    if isinstance(value, bool) or not isinstance(value, str):
        raise SchemaError(
            f"{field} must be str; got {type(value).__name__}"
        )
    if value == "":
        raise SchemaError(f"{field} must be non-empty str")
    return value


def _require_bool_exact(value: Any, field: str, expected: bool) -> bool:
    if value is None:
        raise SchemaError(f"{field} is PRESENT-invalid: null")
    if not isinstance(value, bool):
        raise SchemaError(
            f"{field} must be bool; got {type(value).__name__}"
        )
    if value is not expected:
        raise SchemaError(f"{field} must be exactly {expected}")
    return value


def _require_bool(value: Any, field: str) -> bool:
    if value is None:
        raise SchemaError(f"{field} is PRESENT-invalid: null")
    if not isinstance(value, bool):
        raise SchemaError(
            f"{field} must be bool; got {type(value).__name__}"
        )
    return value


def _require_sha256(value: Any, field: str) -> str:
    text = _require_str(value, field)
    if len(text) != 64 or any(c not in "0123456789abcdef" for c in text):
        raise SchemaError(f"{field} must be lowercase sha256 hex")
    return text


def _require_list(value: Any, field: str) -> list[Any]:
    if value is None:
        raise SchemaError(f"{field} is PRESENT-invalid: null")
    if isinstance(value, (str, bytes, bytearray, Mapping)) or not isinstance(
        value, list
    ):
        raise SchemaError(
            f"{field} must be a list; got {type(value).__name__}"
        )
    return list(value)


def _require_str_list(value: Any, field: str, *, set_like: bool) -> list[str]:
    items = _require_list(value, field)
    out: list[str] = []
    for i, item in enumerate(items):
        out.append(_require_str(item, f"{field}[{i}]"))
    if set_like:
        return _normalize_set_like(out)
    return out


def _require_materiality(value: Any, field: str) -> str:
    text = _require_str(value, field)
    if text not in ALLOWED_MATERIALITY:
        raise SchemaError(f"{field} must be one of {sorted(ALLOWED_MATERIALITY)}")
    return text


def _require_authority_false(value: Any) -> bool:
    return _require_bool_exact(value, "authority", False)


@dataclass(frozen=True)
class PropertySpec:
    property_id: str
    invariant: str
    target_paths: tuple[str, ...]
    target_entry_points: tuple[str, ...]
    materiality: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "property_id": self.property_id,
            "invariant": self.invariant,
            "target_paths": list(self.target_paths),
            "target_entry_points": list(self.target_entry_points),
            "materiality": self.materiality,
        }


@dataclass(frozen=True)
class MutationSpec:
    case_id: str
    property_id: str
    critical: bool
    mutation_kind: str
    target_relative_path: str
    expected_preimage_sha256: str
    operation_enum: str
    operation_arguments: dict[str, Any]
    expected_postimage_sha256: str
    mutation_timing: str
    verifier_invocation_id: str
    violation_predicate: str
    expected_rejection_predicate: str
    oracle_observations: tuple[str, ...]
    materiality: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "property_id": self.property_id,
            "critical": self.critical,
            "mutation_kind": self.mutation_kind,
            "target_relative_path": self.target_relative_path,
            "expected_preimage_sha256": self.expected_preimage_sha256,
            "operation_enum": self.operation_enum,
            "operation_arguments": dict(self.operation_arguments),
            "expected_postimage_sha256": self.expected_postimage_sha256,
            "mutation_timing": self.mutation_timing,
            "verifier_invocation_id": self.verifier_invocation_id,
            "violation_predicate": self.violation_predicate,
            "expected_rejection_predicate": self.expected_rejection_predicate,
            "oracle_observations": list(self.oracle_observations),
            "materiality": self.materiality,
        }


@dataclass(frozen=True)
class Catalog:
    schema_version: str
    authority: bool
    catalog_id: str
    catalog_version: str
    product_base_sha: str
    runner_contract_version: str
    oracle_contract_version: str
    properties: tuple[PropertySpec, ...]
    mutations: tuple[MutationSpec, ...]
    critical_case_ids: tuple[str, ...]
    catalog_digest: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "authority": self.authority,
            "catalog_id": self.catalog_id,
            "catalog_version": self.catalog_version,
            "product_base_sha": self.product_base_sha,
            "runner_contract_version": self.runner_contract_version,
            "oracle_contract_version": self.oracle_contract_version,
            "properties": [p.to_dict() for p in self.properties],
            "mutations": [m.to_dict() for m in self.mutations],
            "critical_case_ids": list(self.critical_case_ids),
            "catalog_digest": self.catalog_digest,
        }

    def mutation_by_case_id(self, case_id: str) -> MutationSpec:
        for mutation in self.mutations:
            if mutation.case_id == case_id:
                return mutation
        raise CatalogError(f"unknown case_id: {case_id}")


@dataclass(frozen=True)
class OracleResult:
    schema_version: str
    authority: bool
    case_id: str
    mutation_valid: bool
    property_violated: bool
    verifier_exercised: bool
    expected_rejection_observed: bool
    result_class: ResultClass
    observations: tuple[str, ...]
    errors: tuple[str, ...]
    oracle_result_digest: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "authority": self.authority,
            "case_id": self.case_id,
            "mutation_valid": self.mutation_valid,
            "property_violated": self.property_violated,
            "verifier_exercised": self.verifier_exercised,
            "expected_rejection_observed": self.expected_rejection_observed,
            "result_class": self.result_class.value,
            "observations": list(self.observations),
            "errors": list(self.errors),
            "oracle_result_digest": self.oracle_result_digest,
        }


@dataclass(frozen=True)
class CaseResult:
    schema_version: str
    authority: bool
    attempt_id: str
    catalog_digest: str
    case_id: str
    property_id: str
    result_class: ResultClass
    mutation_proof: dict[str, Any]
    violation_proof: dict[str, Any]
    verifier_exercise_proof: dict[str, Any]
    process_observation: dict[str, Any]
    filesystem_observations: tuple[str, ...]
    digest_observations: tuple[str, ...]
    oracle_result: OracleResult
    started_at: str
    completed_at: str
    result_digest: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "authority": self.authority,
            "attempt_id": self.attempt_id,
            "catalog_digest": self.catalog_digest,
            "case_id": self.case_id,
            "property_id": self.property_id,
            "result_class": self.result_class.value,
            "mutation_proof": dict(self.mutation_proof),
            "violation_proof": dict(self.violation_proof),
            "verifier_exercise_proof": dict(self.verifier_exercise_proof),
            "process_observation": dict(self.process_observation),
            "filesystem_observations": list(self.filesystem_observations),
            "digest_observations": list(self.digest_observations),
            "oracle_result": self.oracle_result.to_dict(),
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "result_digest": self.result_digest,
        }


@dataclass(frozen=True)
class WVMAStatus:
    schema_version: str
    authority: bool
    attempt_id: str
    catalog_digest: str
    source_revision: str
    runner_digest: str
    oracle_digest: str
    state: AttemptState
    verdict: AttemptVerdict | None
    baseline_receipt_digest: str
    case_result_digests: tuple[dict[str, str], ...]
    result_counts: dict[str, int]
    blocking_case_ids: tuple[str, ...]
    attempt_root_digest: str
    completed_at: str
    status_digest: str

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "schema_version": self.schema_version,
            "authority": self.authority,
            "attempt_id": self.attempt_id,
            "catalog_digest": self.catalog_digest,
            "source_revision": self.source_revision,
            "runner_digest": self.runner_digest,
            "oracle_digest": self.oracle_digest,
            "state": self.state.value,
            "baseline_receipt_digest": self.baseline_receipt_digest,
            "case_result_digests": [dict(x) for x in self.case_result_digests],
            "result_counts": dict(self.result_counts),
            "blocking_case_ids": list(self.blocking_case_ids),
            "attempt_root_digest": self.attempt_root_digest,
            "completed_at": self.completed_at,
            "status_digest": self.status_digest,
        }
        if self.verdict is not None:
            payload["verdict"] = self.verdict.value
        return payload


@dataclass(frozen=True)
class FinalizeIntent:
    schema_version: str
    authority: bool
    attempt_id: str
    attempt_root_digest: str
    intended_status_digest: str
    result_references: tuple[dict[str, str], ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "authority": self.authority,
            "attempt_id": self.attempt_id,
            "attempt_root_digest": self.attempt_root_digest,
            "intended_status_digest": self.intended_status_digest,
            "result_references": [dict(x) for x in self.result_references],
        }


_PROPERTY_FIELDS = {
    "property_id",
    "invariant",
    "target_paths",
    "target_entry_points",
    "materiality",
}

_MUTATION_FIELDS = {
    "case_id",
    "property_id",
    "critical",
    "mutation_kind",
    "target_relative_path",
    "expected_preimage_sha256",
    "operation_enum",
    "operation_arguments",
    "expected_postimage_sha256",
    "mutation_timing",
    "verifier_invocation_id",
    "violation_predicate",
    "expected_rejection_predicate",
    "oracle_observations",
    "materiality",
}

_CATALOG_FIELDS = {
    "schema_version",
    "authority",
    "catalog_id",
    "catalog_version",
    "product_base_sha",
    "runner_contract_version",
    "oracle_contract_version",
    "properties",
    "mutations",
    "critical_case_ids",
    "catalog_digest",
}

_ORACLE_FIELDS = {
    "schema_version",
    "authority",
    "case_id",
    "mutation_valid",
    "property_violated",
    "verifier_exercised",
    "expected_rejection_observed",
    "result_class",
    "observations",
    "errors",
    "oracle_result_digest",
}

_RESULT_FIELDS = {
    "schema_version",
    "authority",
    "attempt_id",
    "catalog_digest",
    "case_id",
    "property_id",
    "result_class",
    "mutation_proof",
    "violation_proof",
    "verifier_exercise_proof",
    "process_observation",
    "filesystem_observations",
    "digest_observations",
    "oracle_result",
    "started_at",
    "completed_at",
    "result_digest",
}

_STATUS_FIELDS = {
    "schema_version",
    "authority",
    "attempt_id",
    "catalog_digest",
    "source_revision",
    "runner_digest",
    "oracle_digest",
    "state",
    "verdict",
    "baseline_receipt_digest",
    "case_result_digests",
    "result_counts",
    "blocking_case_ids",
    "attempt_root_digest",
    "completed_at",
    "status_digest",
}

_STATUS_REQUIRED_ALWAYS = _STATUS_FIELDS - {"verdict"}

_FINALIZE_INTENT_FIELDS = {
    "schema_version",
    "authority",
    "attempt_id",
    "attempt_root_digest",
    "intended_status_digest",
    "result_references",
}

_MUTATION_PROOF_FIELDS = {"applied"}
_VIOLATION_PROOF_FIELDS = {"observed"}
_VERIFIER_EXERCISE_PROOF_FIELDS = {"invoked"}


def _parse_exact_bool_proof(
    value: Any,
    field: str,
    required_key: str,
    allowed: set[str],
) -> dict[str, bool]:
    data = _require_mapping(value, field)
    _reject_unknown(data, allowed, field)
    _require_keys(data, allowed, field)
    return {required_key: _require_bool(data[required_key], f"{field}.{required_key}")}


def _enforce_detected_proof_invariant(
    *,
    result_class: ResultClass,
    mutation_proof: Mapping[str, Any],
    violation_proof: Mapping[str, Any],
    verifier_exercise_proof: Mapping[str, Any],
    oracle: OracleResult,
) -> None:
    if result_class != ResultClass.DETECTED:
        return
    if mutation_proof.get("applied") is not True:
        raise SchemaError("DETECTED requires mutation_proof.applied == True")
    if violation_proof.get("observed") is not True:
        raise SchemaError("DETECTED requires violation_proof.observed == True")
    if verifier_exercise_proof.get("invoked") is not True:
        raise SchemaError(
            "DETECTED requires verifier_exercise_proof.invoked == True"
        )
    if oracle.mutation_valid is not True:
        raise SchemaError("DETECTED requires oracle_result.mutation_valid == True")
    if oracle.property_violated is not True:
        raise SchemaError(
            "DETECTED requires oracle_result.property_violated == True"
        )
    if oracle.verifier_exercised is not True:
        raise SchemaError(
            "DETECTED requires oracle_result.verifier_exercised == True"
        )
    if oracle.expected_rejection_observed is not True:
        raise SchemaError(
            "DETECTED requires oracle_result.expected_rejection_observed == True"
        )


def _parse_property(value: Any, index: int) -> PropertySpec:
    data = _require_mapping(value, f"properties[{index}]")
    _reject_unknown(data, _PROPERTY_FIELDS, f"properties[{index}]")
    _require_keys(data, _PROPERTY_FIELDS, f"properties[{index}]")
    return PropertySpec(
        property_id=_require_str(data["property_id"], f"properties[{index}].property_id"),
        invariant=_require_str(data["invariant"], f"properties[{index}].invariant"),
        target_paths=tuple(
            _require_str_list(
                data["target_paths"],
                f"properties[{index}].target_paths",
                set_like=True,
            )
        ),
        target_entry_points=tuple(
            _require_str_list(
                data["target_entry_points"],
                f"properties[{index}].target_entry_points",
                set_like=True,
            )
        ),
        materiality=_require_materiality(
            data["materiality"], f"properties[{index}].materiality"
        ),
    )


def _parse_mutation(value: Any, index: int) -> MutationSpec:
    data = _require_mapping(value, f"mutations[{index}]")
    _reject_unknown(data, _MUTATION_FIELDS, f"mutations[{index}]")
    _require_keys(data, _MUTATION_FIELDS, f"mutations[{index}]")
    operation = _require_str(
        data["operation_enum"], f"mutations[{index}].operation_enum"
    )
    if operation not in ALLOWED_OPERATION_ENUMS:
        raise SchemaError(
            f"mutations[{index}].operation_enum unsupported: {operation}"
        )
    args = _require_mapping(
        data["operation_arguments"], f"mutations[{index}].operation_arguments"
    )
    return MutationSpec(
        case_id=_require_str(data["case_id"], f"mutations[{index}].case_id"),
        property_id=_require_str(
            data["property_id"], f"mutations[{index}].property_id"
        ),
        critical=_require_bool(data["critical"], f"mutations[{index}].critical"),
        mutation_kind=_require_str(
            data["mutation_kind"], f"mutations[{index}].mutation_kind"
        ),
        target_relative_path=_require_str(
            data["target_relative_path"],
            f"mutations[{index}].target_relative_path",
        ),
        expected_preimage_sha256=_require_sha256(
            data["expected_preimage_sha256"],
            f"mutations[{index}].expected_preimage_sha256",
        ),
        operation_enum=operation,
        operation_arguments=dict(args),
        expected_postimage_sha256=_require_sha256(
            data["expected_postimage_sha256"],
            f"mutations[{index}].expected_postimage_sha256",
        ),
        mutation_timing=_require_str(
            data["mutation_timing"], f"mutations[{index}].mutation_timing"
        ),
        verifier_invocation_id=_require_str(
            data["verifier_invocation_id"],
            f"mutations[{index}].verifier_invocation_id",
        ),
        violation_predicate=_require_str(
            data["violation_predicate"],
            f"mutations[{index}].violation_predicate",
        ),
        expected_rejection_predicate=_require_str(
            data["expected_rejection_predicate"],
            f"mutations[{index}].expected_rejection_predicate",
        ),
        oracle_observations=tuple(
            _require_str_list(
                data["oracle_observations"],
                f"mutations[{index}].oracle_observations",
                set_like=True,
            )
        ),
        materiality=_require_materiality(
            data["materiality"], f"mutations[{index}].materiality"
        ),
    )


def strict_parse_catalog(value: Any) -> Catalog:
    data = _require_mapping(value, "catalog")
    _reject_unknown(data, _CATALOG_FIELDS, "catalog")
    _require_keys(data, _CATALOG_FIELDS, "catalog")

    schema_version = _require_str(data["schema_version"], "schema_version")
    if schema_version != CATALOG_SCHEMA_VERSION:
        raise CatalogError(
            f"schema_version must be {CATALOG_SCHEMA_VERSION}; got {schema_version}"
        )
    authority = _require_authority_false(data["authority"])
    catalog_id = _require_str(data["catalog_id"], "catalog_id")
    catalog_version = _require_str(data["catalog_version"], "catalog_version")
    product_base_sha = _require_sha256(data["product_base_sha"], "product_base_sha")
    runner_contract_version = _require_str(
        data["runner_contract_version"], "runner_contract_version"
    )
    oracle_contract_version = _require_str(
        data["oracle_contract_version"], "oracle_contract_version"
    )

    raw_properties = _require_list(data["properties"], "properties")
    properties = tuple(
        _parse_property(item, i) for i, item in enumerate(raw_properties)
    )
    property_ids = [p.property_id for p in properties]
    if len(property_ids) != len(set(property_ids)):
        raise CatalogError("duplicate property_id values")

    raw_mutations = _require_list(data["mutations"], "mutations")
    mutations = tuple(
        _parse_mutation(item, i) for i, item in enumerate(raw_mutations)
    )
    case_ids = [m.case_id for m in mutations]
    if len(case_ids) != len(set(case_ids)):
        raise CatalogError("duplicate case_id values")

    property_id_set = set(property_ids)
    for mutation in mutations:
        if mutation.property_id not in property_id_set:
            raise CatalogError(
                f"mutation {mutation.case_id} references unknown property_id "
                f"{mutation.property_id}"
            )

    critical_case_ids = tuple(
        _require_str_list(data["critical_case_ids"], "critical_case_ids", set_like=True)
    )
    case_id_set = set(case_ids)
    for case_id in critical_case_ids:
        if case_id not in case_id_set:
            raise CatalogError(f"critical_case_ids references unknown case_id: {case_id}")
        mutation = next(m for m in mutations if m.case_id == case_id)
        if mutation.critical is not True:
            raise CatalogError(
                f"critical case {case_id} must have critical exactly true"
            )
    critical_set = set(critical_case_ids)
    for mutation in mutations:
        if mutation.critical is True and mutation.case_id not in critical_set:
            raise CatalogError(
                f"mutation {mutation.case_id} is critical but missing from "
                "critical_case_ids"
            )

    stored_digest = _require_sha256(data["catalog_digest"], "catalog_digest")
    expected = digest_excluding_field(data, "catalog_digest")
    if stored_digest != expected:
        raise CatalogError("catalog_digest mismatch")

    return Catalog(
        schema_version=schema_version,
        authority=authority,
        catalog_id=catalog_id,
        catalog_version=catalog_version,
        product_base_sha=product_base_sha,
        runner_contract_version=runner_contract_version,
        oracle_contract_version=oracle_contract_version,
        properties=properties,
        mutations=mutations,
        critical_case_ids=critical_case_ids,
        catalog_digest=stored_digest,
    )


def _parse_result_class(value: Any, field: str) -> ResultClass:
    text = _require_str(value, field)
    try:
        return ResultClass(text)
    except ValueError as exc:
        raise SchemaError(f"{field} unsupported: {text}") from exc


def strict_parse_oracle_result(value: Any) -> OracleResult:
    data = _require_mapping(value, "oracle_result")
    _reject_unknown(data, _ORACLE_FIELDS, "oracle_result")
    _require_keys(data, _ORACLE_FIELDS, "oracle_result")
    schema_version = _require_str(data["schema_version"], "oracle_result.schema_version")
    if schema_version != ORACLE_SCHEMA_VERSION:
        raise SchemaError(
            f"oracle_result.schema_version must be {ORACLE_SCHEMA_VERSION}"
        )
    result_class = _parse_result_class(data["result_class"], "oracle_result.result_class")
    stored = _require_sha256(
        data["oracle_result_digest"], "oracle_result.oracle_result_digest"
    )
    expected = digest_excluding_field(data, "oracle_result_digest")
    if stored != expected:
        raise SchemaError("oracle_result_digest mismatch")
    return OracleResult(
        schema_version=schema_version,
        authority=_require_authority_false(data["authority"]),
        case_id=_require_str(data["case_id"], "oracle_result.case_id"),
        mutation_valid=_require_bool(
            data["mutation_valid"], "oracle_result.mutation_valid"
        ),
        property_violated=_require_bool(
            data["property_violated"], "oracle_result.property_violated"
        ),
        verifier_exercised=_require_bool(
            data["verifier_exercised"], "oracle_result.verifier_exercised"
        ),
        expected_rejection_observed=_require_bool(
            data["expected_rejection_observed"],
            "oracle_result.expected_rejection_observed",
        ),
        result_class=result_class,
        observations=tuple(
            _require_str_list(
                data["observations"], "oracle_result.observations", set_like=True
            )
        ),
        errors=tuple(
            _require_str_list(data["errors"], "oracle_result.errors", set_like=True)
        ),
        oracle_result_digest=stored,
    )


def strict_parse_case_result(value: Any) -> CaseResult:
    data = _require_mapping(value, "case_result")
    _reject_unknown(data, _RESULT_FIELDS, "case_result")
    _require_keys(data, _RESULT_FIELDS, "case_result")
    schema_version = _require_str(data["schema_version"], "schema_version")
    if schema_version != RESULT_SCHEMA_VERSION:
        raise SchemaError(f"schema_version must be {RESULT_SCHEMA_VERSION}")
    result_class = _parse_result_class(data["result_class"], "result_class")
    oracle = strict_parse_oracle_result(data["oracle_result"])
    if oracle.case_id != _require_str(data["case_id"], "case_id"):
        raise SchemaError("oracle_result.case_id must match case_id")
    if oracle.result_class != result_class:
        raise SchemaError("oracle_result.result_class must match result_class")
    mutation_proof = _parse_exact_bool_proof(
        data["mutation_proof"],
        "mutation_proof",
        "applied",
        _MUTATION_PROOF_FIELDS,
    )
    violation_proof = _parse_exact_bool_proof(
        data["violation_proof"],
        "violation_proof",
        "observed",
        _VIOLATION_PROOF_FIELDS,
    )
    verifier_exercise_proof = _parse_exact_bool_proof(
        data["verifier_exercise_proof"],
        "verifier_exercise_proof",
        "invoked",
        _VERIFIER_EXERCISE_PROOF_FIELDS,
    )
    _enforce_detected_proof_invariant(
        result_class=result_class,
        mutation_proof=mutation_proof,
        violation_proof=violation_proof,
        verifier_exercise_proof=verifier_exercise_proof,
        oracle=oracle,
    )
    stored = _require_sha256(data["result_digest"], "result_digest")
    expected = digest_excluding_field(data, "result_digest")
    if stored != expected:
        raise SchemaError("result_digest mismatch")
    return CaseResult(
        schema_version=schema_version,
        authority=_require_authority_false(data["authority"]),
        attempt_id=_require_str(data["attempt_id"], "attempt_id"),
        catalog_digest=_require_sha256(data["catalog_digest"], "catalog_digest"),
        case_id=_require_str(data["case_id"], "case_id"),
        property_id=_require_str(data["property_id"], "property_id"),
        result_class=result_class,
        mutation_proof=dict(mutation_proof),
        violation_proof=dict(violation_proof),
        verifier_exercise_proof=dict(verifier_exercise_proof),
        process_observation=dict(
            _require_mapping(data["process_observation"], "process_observation")
        ),
        filesystem_observations=tuple(
            _require_str_list(
                data["filesystem_observations"],
                "filesystem_observations",
                set_like=True,
            )
        ),
        digest_observations=tuple(
            _require_str_list(
                data["digest_observations"], "digest_observations", set_like=True
            )
        ),
        oracle_result=oracle,
        started_at=_require_str(data["started_at"], "started_at"),
        completed_at=_require_str(data["completed_at"], "completed_at"),
        result_digest=stored,
    )


def _parse_finalize_result_references(
    value: Any,
) -> tuple[dict[str, str], ...]:
    items = _require_list(value, "result_references")
    parsed: list[dict[str, str]] = []
    seen_cases: set[str] = set()
    for i, item in enumerate(items):
        entry = _require_mapping(item, f"result_references[{i}]")
        allowed = {"case_id", "result_digest"}
        _reject_unknown(entry, allowed, f"result_references[{i}]")
        _require_keys(entry, allowed, f"result_references[{i}]")
        case_id = _require_str(entry["case_id"], f"result_references[{i}].case_id")
        digest = _require_sha256(
            entry["result_digest"], f"result_references[{i}].result_digest"
        )
        if case_id in seen_cases:
            raise SchemaError(f"duplicate result_references case_id: {case_id}")
        seen_cases.add(case_id)
        parsed.append({"case_id": case_id, "result_digest": digest})
    expected = sorted(parsed, key=lambda x: x["case_id"])
    if parsed != expected:
        raise SchemaError("result_references must be canonically sorted by case_id")
    return tuple(parsed)


def strict_parse_finalize_intent(
    value: Any,
    *,
    expected_attempt_id: str | None = None,
) -> FinalizeIntent:
    data = _require_mapping(value, "finalize_intent")
    _reject_unknown(data, _FINALIZE_INTENT_FIELDS, "finalize_intent")
    _require_keys(data, _FINALIZE_INTENT_FIELDS, "finalize_intent")
    schema_version = _require_str(data["schema_version"], "schema_version")
    if schema_version != FINALIZE_INTENT_SCHEMA_VERSION:
        raise SchemaError(
            f"schema_version must be {FINALIZE_INTENT_SCHEMA_VERSION}; "
            f"got {schema_version}"
        )
    authority = _require_authority_false(data["authority"])
    attempt_id = _require_str(data["attempt_id"], "attempt_id")
    if expected_attempt_id is not None and attempt_id != expected_attempt_id:
        raise SchemaError(
            f"finalize_intent.attempt_id foreign: {attempt_id} != {expected_attempt_id}"
        )
    return FinalizeIntent(
        schema_version=schema_version,
        authority=authority,
        attempt_id=attempt_id,
        attempt_root_digest=_require_sha256(
            data["attempt_root_digest"], "attempt_root_digest"
        ),
        intended_status_digest=_require_sha256(
            data["intended_status_digest"], "intended_status_digest"
        ),
        result_references=_parse_finalize_result_references(
            data["result_references"]
        ),
    )


def _parse_case_result_digest_entries(value: Any) -> tuple[dict[str, str], ...]:
    items = _require_list(value, "case_result_digests")
    parsed: list[dict[str, str]] = []
    seen_cases: set[str] = set()
    for i, item in enumerate(items):
        entry = _require_mapping(item, f"case_result_digests[{i}]")
        allowed = {"case_id", "result_digest"}
        _reject_unknown(entry, allowed, f"case_result_digests[{i}]")
        _require_keys(entry, allowed, f"case_result_digests[{i}]")
        case_id = _require_str(entry["case_id"], f"case_result_digests[{i}].case_id")
        digest = _require_sha256(
            entry["result_digest"], f"case_result_digests[{i}].result_digest"
        )
        if case_id in seen_cases:
            raise SchemaError(f"duplicate case_result_digests case_id: {case_id}")
        seen_cases.add(case_id)
        parsed.append({"case_id": case_id, "result_digest": digest})
    parsed.sort(key=lambda x: x["case_id"])
    return tuple(parsed)


def _parse_result_counts(value: Any) -> dict[str, int]:
    data = _require_mapping(value, "result_counts")
    out: dict[str, int] = {}
    for key, raw in data.items():
        _parse_result_class(key, f"result_counts[{key}]")
        if isinstance(raw, bool) or not isinstance(raw, int):
            raise SchemaError(
                f"result_counts[{key}] must be int; got {type(raw).__name__}"
            )
        if raw < 0:
            raise SchemaError(f"result_counts[{key}] must be >= 0")
        out[key] = raw
    return dict(sorted(out.items()))


def strict_parse_status(value: Any) -> WVMAStatus:
    data = _require_mapping(value, "status")
    present = set(data.keys())
    unknown = sorted(present - _STATUS_FIELDS)
    if unknown:
        raise SchemaError(f"status has unknown fields: {unknown}")
    missing = sorted(_STATUS_REQUIRED_ALWAYS - present)
    if missing:
        raise SchemaError(f"status missing fields: {missing}")

    schema_version = _require_str(data["schema_version"], "schema_version")
    if schema_version != STATUS_SCHEMA_VERSION:
        raise SchemaError(f"schema_version must be {STATUS_SCHEMA_VERSION}")

    state_text = _require_str(data["state"], "state")
    try:
        state = AttemptState(state_text)
    except ValueError as exc:
        raise SchemaError(f"state unsupported: {state_text}") from exc
    if state not in {
        AttemptState.RUN_COMPLETE,
        AttemptState.RUN_INCOMPLETE,
        AttemptState.RUN_INVALID,
    }:
        raise SchemaError(
            "status.state must be RUN_COMPLETE, RUN_INCOMPLETE, or RUN_INVALID"
        )

    verdict: AttemptVerdict | None = None
    if "verdict" in data:
        if state != AttemptState.RUN_COMPLETE:
            raise SchemaError("verdict is forbidden outside RUN_COMPLETE")
        verdict_text = _require_str(data["verdict"], "verdict")
        try:
            verdict = AttemptVerdict(verdict_text)
        except ValueError as exc:
            raise SchemaError(f"verdict unsupported: {verdict_text}") from exc
        if verdict not in {
            AttemptVerdict.ALL_CRITICAL_DETECTED,
            AttemptVerdict.CRITICAL_SURVIVOR,
        }:
            raise SchemaError("RUN_COMPLETE permits only ALL_CRITICAL_DETECTED or CRITICAL_SURVIVOR")
    elif state == AttemptState.RUN_COMPLETE:
        raise SchemaError("RUN_COMPLETE requires verdict")

    stored = _require_sha256(data["status_digest"], "status_digest")
    expected = digest_excluding_field(data, "status_digest")
    if stored != expected:
        raise SchemaError("status_digest mismatch")

    return WVMAStatus(
        schema_version=schema_version,
        authority=_require_authority_false(data["authority"]),
        attempt_id=_require_str(data["attempt_id"], "attempt_id"),
        catalog_digest=_require_sha256(data["catalog_digest"], "catalog_digest"),
        source_revision=_require_sha256(data["source_revision"], "source_revision"),
        runner_digest=_require_sha256(data["runner_digest"], "runner_digest"),
        oracle_digest=_require_sha256(data["oracle_digest"], "oracle_digest"),
        state=state,
        verdict=verdict,
        baseline_receipt_digest=_require_sha256(
            data["baseline_receipt_digest"], "baseline_receipt_digest"
        ),
        case_result_digests=_parse_case_result_digest_entries(
            data["case_result_digests"]
        ),
        result_counts=_parse_result_counts(data["result_counts"]),
        blocking_case_ids=tuple(
            _require_str_list(
                data["blocking_case_ids"], "blocking_case_ids", set_like=True
            )
        ),
        attempt_root_digest=_require_sha256(
            data["attempt_root_digest"], "attempt_root_digest"
        ),
        completed_at=_require_str(data["completed_at"], "completed_at"),
        status_digest=stored,
    )


def build_oracle_result(
    *,
    case_id: str,
    mutation_valid: bool,
    property_violated: bool,
    verifier_exercised: bool,
    expected_rejection_observed: bool,
    result_class: ResultClass,
    observations: list[str] | None = None,
    errors: list[str] | None = None,
) -> OracleResult:
    body: dict[str, Any] = {
        "schema_version": ORACLE_SCHEMA_VERSION,
        "authority": False,
        "case_id": case_id,
        "mutation_valid": mutation_valid,
        "property_violated": property_violated,
        "verifier_exercised": verifier_exercised,
        "expected_rejection_observed": expected_rejection_observed,
        "result_class": result_class.value,
        "observations": _normalize_set_like(list(observations or [])),
        "errors": _normalize_set_like(list(errors or [])),
    }
    body["oracle_result_digest"] = digest_excluding_field(body, "oracle_result_digest")
    return strict_parse_oracle_result(body)


def build_case_result(
    *,
    attempt_id: str,
    catalog_digest: str,
    case_id: str,
    property_id: str,
    result_class: ResultClass,
    oracle_result: OracleResult,
    started_at: str,
    completed_at: str,
    mutation_proof: dict[str, Any] | None = None,
    violation_proof: dict[str, Any] | None = None,
    verifier_exercise_proof: dict[str, Any] | None = None,
    process_observation: dict[str, Any] | None = None,
    filesystem_observations: list[str] | None = None,
    digest_observations: list[str] | None = None,
) -> CaseResult:
    # Defaults are ABSENT-only; never synthesize via falsey `x or default`.
    if mutation_proof is None:
        mutation_proof = {"applied": True}
    if violation_proof is None:
        violation_proof = {"observed": True}
    if verifier_exercise_proof is None:
        verifier_exercise_proof = {"invoked": True}
    if process_observation is None:
        process_observation = {"exit_code": 0}
    if filesystem_observations is None:
        filesystem_observations = []
    if digest_observations is None:
        digest_observations = []
    body: dict[str, Any] = {
        "schema_version": RESULT_SCHEMA_VERSION,
        "authority": False,
        "attempt_id": attempt_id,
        "catalog_digest": catalog_digest,
        "case_id": case_id,
        "property_id": property_id,
        "result_class": result_class.value,
        "mutation_proof": dict(mutation_proof),
        "violation_proof": dict(violation_proof),
        "verifier_exercise_proof": dict(verifier_exercise_proof),
        "process_observation": dict(process_observation),
        "filesystem_observations": _normalize_set_like(
            list(filesystem_observations)
        ),
        "digest_observations": _normalize_set_like(list(digest_observations)),
        "oracle_result": oracle_result.to_dict(),
        "started_at": started_at,
        "completed_at": completed_at,
    }
    body["result_digest"] = digest_excluding_field(body, "result_digest")
    return strict_parse_case_result(body)


def build_status(
    *,
    attempt_id: str,
    catalog_digest: str,
    source_revision: str,
    runner_digest: str,
    oracle_digest: str,
    state: AttemptState,
    baseline_receipt_digest: str,
    case_result_digests: list[dict[str, str]],
    result_counts: dict[str, int],
    blocking_case_ids: list[str],
    attempt_root_digest: str,
    completed_at: str,
    verdict: AttemptVerdict | None = ABSENT,
) -> WVMAStatus:
    body: dict[str, Any] = {
        "schema_version": STATUS_SCHEMA_VERSION,
        "authority": False,
        "attempt_id": attempt_id,
        "catalog_digest": catalog_digest,
        "source_revision": source_revision,
        "runner_digest": runner_digest,
        "oracle_digest": oracle_digest,
        "state": state.value,
        "baseline_receipt_digest": baseline_receipt_digest,
        "case_result_digests": sorted(
            [dict(x) for x in case_result_digests], key=lambda x: x["case_id"]
        ),
        "result_counts": dict(sorted(result_counts.items())),
        "blocking_case_ids": _normalize_set_like(list(blocking_case_ids)),
        "attempt_root_digest": attempt_root_digest,
        "completed_at": completed_at,
    }
    if verdict is not ABSENT:
        if verdict is None:
            raise SchemaError("verdict PRESENT-invalid: null")
        if not isinstance(verdict, AttemptVerdict):
            raise SchemaError("verdict must be AttemptVerdict")
        body["verdict"] = verdict.value
    body["status_digest"] = digest_excluding_field(body, "status_digest")
    return strict_parse_status(body)


def critical_acceptance_blocks(result_class: ResultClass) -> bool:
    """Only DETECTED satisfies critical acceptance."""
    return result_class != ResultClass.DETECTED
