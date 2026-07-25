#!/usr/bin/env python3
"""Canonical schema-register loader for the rc6 remediation path.

Loads committed plain-JSON registers under witness-package/schemas/ and
exposes fail-closed structural accessors for the validator and tests.

RC6-R4: the active default register is rc6.3
(canonical_schema_register_rc6.json). Frozen rc6.2, rc6.1, rc5 Phase-4 S2, and
S1 registers remain explicitly loadable for historical compatibility only and
are not competing active authorities. Evidence content cannot select schema
authority; unsupported versions fail closed.

This module does not generate executable code from the register and uses only
the Python standard library.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

ACTIVE_REGISTER_VERSION = "rc6.3"
HISTORICAL_RC62_REGISTER_VERSION = "rc6.2"
HISTORICAL_RC61_REGISTER_VERSION = "rc6.1"
HISTORICAL_S2_REGISTER_VERSION = "rc5-phase4-s2.1"
HISTORICAL_S1_REGISTER_VERSION = "rc5-phase4-s1.1"
HISTORICAL_REGISTER_VERSIONS = frozenset(
    {
        HISTORICAL_RC62_REGISTER_VERSION,
        HISTORICAL_RC61_REGISTER_VERSION,
        HISTORICAL_S2_REGISTER_VERSION,
        HISTORICAL_S1_REGISTER_VERSION,
    }
)
SUPPORTED_REGISTER_VERSIONS = frozenset(
    {ACTIVE_REGISTER_VERSION} | HISTORICAL_REGISTER_VERSIONS
)
DEFAULT_REGISTER_RELATIVE = Path("schemas") / "canonical_schema_register_rc6.json"
HISTORICAL_RC62_REGISTER_RELATIVE = (
    Path("schemas") / "canonical_schema_register_rc6.2.json"
)
HISTORICAL_RC61_REGISTER_RELATIVE = (
    Path("schemas") / "canonical_schema_register_rc6.1.json"
)
HISTORICAL_S2_REGISTER_RELATIVE = (
    Path("schemas") / "canonical_schema_register_rc5_phase4_s2.json"
)
HISTORICAL_S1_REGISTER_RELATIVE = (
    Path("schemas") / "canonical_schema_register_rc5_phase4_s1.json"
)
LEGAL_LIFECYCLE_MODES = frozenset({"host-preliminary", "final-submission"})
LEGAL_ACTIVATIONS = frozenset(
    {
        "enforced_current_compatible",
        "enforced_s2_writer_aligned",
        "enforced_s2_ownership_cross_binding",
        "enforced_s3_manifest_completeness",
        "defined_future_s2_writer_alignment",
        "defined_future_s3_manifest_completeness",
        "defined_structural_only_s1",
        "historical_s1_compatibility",
        "available_read_only_s2",
    }
)
LEGAL_FIELD_REQUIREMENTS = frozenset({"required", "optional", "conditional"})
LEGAL_EXACT_POLICIES = frozenset(
    {
        "exact",
        "required_subset_allowed",  # historical S1/S2 documents only
        "raw_stream",
        "manifest_grammar",
        "open_append_log_current",
        "append_entry_grammar",
        "exact_when_s2_shaped_else_historical_subset",
    }
)
ACTIVE_FORBIDDEN_EXACT_POLICIES = frozenset({"required_subset_allowed"})
LEGAL_FILE_CLASSIFICATIONS = frozenset(
    {
        "required",
        "accepted_supporting",
        "closed_aux_optional",
        "outside_evidence_dir",
        "not_in_required_set",
        "not_applicable_to_this_entry",
    }
)

REGISTER_TOP_LEVEL_KEYS = frozenset(
    {
        "schema_register_version",
        "family",
        "evidence_schema_version",
        "supported_register_versions",
        "supersession",
        "historical_compatibility",
        "lifecycle_modes",
        "default_mode_compatibility_alias",
        "mode_required_file_sets",
        "mode_accepted_supporting_files",
        "closed_aux_evidence_files",
        "run_id_policy",
        "evidence_completeness_inventory",
        "recursive_inventory_helper",
        "nested_evidence_classes",
        "artifacts",
    }
)

ARTIFACT_KEYS = frozenset(
    {
        "artifact_id",
        "filename",
        "owner",
        "lifecycle_modes",
        "required_file_classification",
        "activation",
        "field_order_normative",
        "exact_field_set_policy",
        "fields",
        "optional_fields",
        "conditional_variants",
        "run_id_required",
        "note",
        "legal_values",
        "no_deviation_state",
        "empty_ok_fields",
        "future_alignment_fields",
        "s1_future_alignment_record",
        "historical_compatibility_required_fields",
        "append_entry_grammar",
        "manifest_grammar",
        "activation_detail",
        "location",
    }
)

FIELD_KEYS = frozenset({"name", "requirement", "legal_values", "note", "activation"})

S2_PACKAGE_IDENTITY_MARKERS = frozenset(
    {
        "weaver_forge_tag_ref",
        "weaver_forge_tag_raw_object_type_required",
        "weaver_forge_tag_raw_object_type_observed",
        "weaver_forge_tag_peeled_commit",
    }
)
S2_PRELIM_DEVIATIONS_MARKERS = frozenset({"deviation_count", "automated_summary"})
S2_FINAL_DEVIATIONS_MARKERS = frozenset({"deviation_count"})
HOST_RUN_METADATA_ENTRY_BEGIN = "BEGIN_HOST_RUN_METADATA_ENTRY"
HOST_RUN_METADATA_ENTRY_END = "END_HOST_RUN_METADATA_ENTRY"
HOST_RUN_METADATA_ENTRY_KEYS = (
    "evidence_schema_version",
    "run_id",
    "witness_id",
    "entry_kind",
    "entry_utc",
    "payload",
)


class SchemaRegisterError(ValueError):
    """Fail-closed schema register structural error."""


def schemas_dir() -> Path:
    scripts_dir = Path(__file__).resolve().parent
    return scripts_dir.parent / "schemas"


def default_register_path() -> Path:
    """Active (rc6.3) committed register path."""
    return schemas_dir() / DEFAULT_REGISTER_RELATIVE.name


def historical_rc62_register_path() -> Path:
    """Frozen rc6.2 historical register path."""
    return schemas_dir() / HISTORICAL_RC62_REGISTER_RELATIVE.name


def historical_rc61_register_path() -> Path:
    """Frozen rc6.1 historical register path."""
    return schemas_dir() / HISTORICAL_RC61_REGISTER_RELATIVE.name


def historical_s2_register_path() -> Path:
    """Frozen S2 historical register path."""
    return schemas_dir() / HISTORICAL_S2_REGISTER_RELATIVE.name


def historical_s1_register_path() -> Path:
    """Frozen S1 historical register path."""
    return schemas_dir() / HISTORICAL_S1_REGISTER_RELATIVE.name


def register_path_for_version(version: str) -> Path:
    """Deterministic path lookup by explicit register version. No content guessing."""
    if version == ACTIVE_REGISTER_VERSION:
        return default_register_path()
    if version == HISTORICAL_RC62_REGISTER_VERSION:
        return historical_rc62_register_path()
    if version == HISTORICAL_RC61_REGISTER_VERSION:
        return historical_rc61_register_path()
    if version == HISTORICAL_S2_REGISTER_VERSION:
        return historical_s2_register_path()
    if version == HISTORICAL_S1_REGISTER_VERSION:
        return historical_s1_register_path()
    raise SchemaRegisterError(f"unsupported schema_register_version: {version!r}")


def _require_mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise SchemaRegisterError(f"{label} must be a JSON object")
    return value


def _require_list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise SchemaRegisterError(f"{label} must be a JSON array")
    return value


def _reject_unknown_keys(obj: dict[str, Any], allowed: frozenset[str], label: str) -> None:
    unknown = sorted(set(obj) - allowed)
    if unknown:
        raise SchemaRegisterError(f"{label}: unknown key(s): {unknown}")


def _validate_field_list(fields: list[Any], label: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for idx, raw in enumerate(fields):
        entry = _require_mapping(raw, f"{label}[{idx}]")
        _reject_unknown_keys(entry, FIELD_KEYS, f"{label}[{idx}]")
        name = entry.get("name")
        if not isinstance(name, str) or not name:
            raise SchemaRegisterError(f"{label}[{idx}]: field name must be a non-empty string")
        if name in seen:
            raise SchemaRegisterError(f"{label}: duplicate field name {name!r}")
        seen.add(name)
        req = entry.get("requirement", "required")
        if req not in LEGAL_FIELD_REQUIREMENTS:
            raise SchemaRegisterError(f"{label}/{name}: unknown requirement {req!r}")
        out.append(entry)
    return out


def _validate_artifact(raw: Any, idx: int) -> dict[str, Any]:
    art = _require_mapping(raw, f"artifacts[{idx}]")
    _reject_unknown_keys(art, ARTIFACT_KEYS, f"artifacts[{idx}]")
    artifact_id = art.get("artifact_id")
    filename = art.get("filename")
    if not isinstance(artifact_id, str) or not artifact_id:
        raise SchemaRegisterError(f"artifacts[{idx}]: artifact_id must be a non-empty string")
    if not isinstance(filename, str) or not filename:
        raise SchemaRegisterError(f"artifacts[{idx}]: filename must be a non-empty string")
    modes = art.get("lifecycle_modes")
    if not isinstance(modes, list) or not modes:
        raise SchemaRegisterError(f"{artifact_id}: lifecycle_modes must be a non-empty array")
    for mode in modes:
        if mode not in LEGAL_LIFECYCLE_MODES:
            raise SchemaRegisterError(f"{artifact_id}: unknown lifecycle mode {mode!r}")
    activation = art.get("activation")
    if activation not in LEGAL_ACTIVATIONS:
        raise SchemaRegisterError(f"{artifact_id}: unknown activation {activation!r}")
    policy = art.get("exact_field_set_policy")
    if policy not in LEGAL_EXACT_POLICIES:
        raise SchemaRegisterError(f"{artifact_id}: unknown exact_field_set_policy {policy!r}")
    if not isinstance(art.get("field_order_normative"), bool):
        raise SchemaRegisterError(f"{artifact_id}: field_order_normative must be a boolean")
    classif = _require_mapping(
        art.get("required_file_classification"), f"{artifact_id}.required_file_classification"
    )
    for mode, value in classif.items():
        if mode not in LEGAL_LIFECYCLE_MODES:
            raise SchemaRegisterError(f"{artifact_id}: unknown classification mode {mode!r}")
        if value not in LEGAL_FILE_CLASSIFICATIONS:
            raise SchemaRegisterError(f"{artifact_id}: unknown classification {value!r}")
    fields = _validate_field_list(
        _require_list(art.get("fields", []), f"{artifact_id}.fields"), f"{artifact_id}.fields"
    )
    optional = _validate_field_list(
        _require_list(art.get("optional_fields", []), f"{artifact_id}.optional_fields"),
        f"{artifact_id}.optional_fields",
    )
    if "historical_compatibility_required_fields" in art:
        _validate_field_list(
            _require_list(
                art.get("historical_compatibility_required_fields"),
                f"{artifact_id}.historical_compatibility_required_fields",
            ),
            f"{artifact_id}.historical_compatibility_required_fields",
        )
    required_names = {f["name"] for f in fields if f.get("requirement") == "required"}
    optional_names = {f["name"] for f in optional}
    overlap = sorted(required_names & optional_names)
    if overlap:
        raise SchemaRegisterError(
            f"{artifact_id}: contradictory required/optional definitions for {overlap}"
        )
    for f in fields:
        if f.get("requirement") == "optional" and f["name"] in required_names:
            raise SchemaRegisterError(
                f"{artifact_id}: field {f['name']!r} cannot be both required and optional"
            )
    variants = art.get("conditional_variants", [])
    if variants is None:
        variants = []
    _require_list(variants, f"{artifact_id}.conditional_variants")
    for vidx, variant in enumerate(variants):
        vmap = _require_mapping(variant, f"{artifact_id}.conditional_variants[{vidx}]")
        vact = vmap.get("activation")
        if vact is not None and vact not in LEGAL_ACTIVATIONS:
            raise SchemaRegisterError(
                f"{artifact_id}.conditional_variants[{vidx}]: unknown activation {vact!r}"
            )
    return art


class CanonicalSchemaRegister:
    """Parsed, fail-closed canonical schema register."""

    def __init__(self, data: dict[str, Any], *, source_path: Path) -> None:
        self._data = data
        self.source_path = source_path
        self.schema_register_version = str(data["schema_register_version"])
        self.evidence_schema_version = str(data["evidence_schema_version"])
        self.lifecycle_modes = tuple(data["lifecycle_modes"])
        self.default_mode_compatibility_alias = str(data["default_mode_compatibility_alias"])
        self._artifacts: list[dict[str, Any]] = list(data["artifacts"])
        self._by_id = {a["artifact_id"]: a for a in self._artifacts}
        self._index: dict[tuple[str, str], dict[str, Any]] = {}
        for art in self._artifacts:
            for mode in art["lifecycle_modes"]:
                key = (art["filename"], mode)
                if key in self._index:
                    existing = self._index[key]
                    if existing is not art and existing.get("artifact_id") != art.get("artifact_id"):
                        if "@" not in art["artifact_id"] and "@" not in existing["artifact_id"]:
                            raise SchemaRegisterError(
                                f"duplicate artifact/mode definition for {art['filename']!r} mode {mode!r}"
                            )
                if key not in self._index or "@" in art["artifact_id"]:
                    self._index[key] = art

    @property
    def raw(self) -> dict[str, Any]:
        return self._data

    @property
    def is_active_authority(self) -> bool:
        return self.schema_register_version == ACTIVE_REGISTER_VERSION

    @property
    def is_historical_rc62(self) -> bool:
        return self.schema_register_version == HISTORICAL_RC62_REGISTER_VERSION

    @property
    def is_historical_rc61(self) -> bool:
        return self.schema_register_version == HISTORICAL_RC61_REGISTER_VERSION

    @property
    def is_historical_s2(self) -> bool:
        return self.schema_register_version == HISTORICAL_S2_REGISTER_VERSION

    @property
    def is_historical_s1(self) -> bool:
        return self.schema_register_version == HISTORICAL_S1_REGISTER_VERSION

    def nested_evidence_classes(self) -> dict[str, Any] | None:
        raw = self._data.get("nested_evidence_classes")
        if raw is None:
            return None
        return dict(raw)

    def nested_class_records(self) -> tuple[dict[str, Any], ...]:
        block = self.nested_evidence_classes()
        if not block:
            return ()
        classes = block.get("classes") or []
        return tuple(dict(c) for c in classes if isinstance(c, dict))

    def nested_class_by_id(self, class_id: str) -> dict[str, Any] | None:
        for rec in self.nested_class_records():
            if rec.get("class_id") == class_id:
                return dict(rec)
        return None

    def resolve_nested_class_for_path(self, rel_path: str) -> dict[str, Any] | None:
        """Return the unique registered class for a nested relative path, or None.

        Caller must fail closed on None for active authority. Overlaps fail closed.
        """
        if "/" not in rel_path:
            return None
        matches: list[dict[str, Any]] = []
        for rec in self.nested_class_records():
            prefix = str(rec.get("allowed_path_prefix") or "")
            if prefix and rel_path.startswith(prefix):
                matches.append(rec)
        if len(matches) == 1:
            return dict(matches[0])
        if len(matches) > 1:
            raise SchemaRegisterError(
                f"nested path {rel_path!r} matches multiple nested evidence classes: "
                f"{sorted(m.get('class_id', '') for m in matches)}"
            )
        return None

    def enforces_typed_nested_classes(self) -> bool:
        return self.is_active_authority and bool(self.nested_class_records())

    def enforces_empty_directory_rejection(self) -> bool:
        block = self.nested_evidence_classes() or {}
        return self.is_active_authority and block.get("empty_directory_policy") == "reject_all"

    def require_mode(self, mode: str) -> str:
        if mode not in LEGAL_LIFECYCLE_MODES:
            raise SchemaRegisterError(f"unknown lifecycle mode: {mode!r}")
        return mode

    def required_files(self, mode: str) -> tuple[str, ...]:
        mode = self.require_mode(mode)
        files = self._data["mode_required_file_sets"][mode]
        return tuple(files)

    def accepted_supporting_files(self, mode: str) -> frozenset[str]:
        mode = self.require_mode(mode)
        return frozenset(self._data["mode_accepted_supporting_files"].get(mode, []))

    def closed_aux_evidence_files(self) -> frozenset[str]:
        return frozenset(self._data["closed_aux_evidence_files"])

    def lookup(self, filename: str, mode: str) -> dict[str, Any]:
        mode = self.require_mode(mode)
        key = (filename, mode)
        if key not in self._index:
            raise SchemaRegisterError(f"no artifact schema for filename={filename!r} mode={mode!r}")
        return self._index[key]

    def ordered_fields(self, filename: str, mode: str) -> tuple[str, ...]:
        art = self.lookup(filename, mode)
        return tuple(f["name"] for f in art.get("fields", []))

    def required_field_names(self, filename: str, mode: str) -> tuple[str, ...]:
        art = self.lookup(filename, mode)
        return tuple(
            f["name"] for f in art.get("fields", []) if f.get("requirement", "required") == "required"
        )

    def optional_field_names(self, filename: str, mode: str) -> tuple[str, ...]:
        art = self.lookup(filename, mode)
        names = [f["name"] for f in art.get("optional_fields", [])]
        names.extend(
            f["name"] for f in art.get("fields", []) if f.get("requirement") == "optional"
        )
        return tuple(names)

    def historical_compatibility_required_field_names(
        self, filename: str, mode: str
    ) -> tuple[str, ...] | None:
        art = self.lookup(filename, mode)
        hist = art.get("historical_compatibility_required_fields")
        if hist is None:
            return None
        return tuple(f["name"] for f in hist if f.get("requirement", "required") == "required")

    def exact_field_set_policy(self, filename: str, mode: str) -> str:
        return str(self.lookup(filename, mode)["exact_field_set_policy"])

    def field_order_normative(self, filename: str, mode: str) -> bool:
        return bool(self.lookup(filename, mode)["field_order_normative"])

    def legal_values(self, filename: str, mode: str) -> dict[str, tuple[str, ...]]:
        art = self.lookup(filename, mode)
        out: dict[str, tuple[str, ...]] = {}
        top = art.get("legal_values") or {}
        if isinstance(top, dict):
            for key, values in top.items():
                if isinstance(values, list):
                    out[key] = tuple(values)
        for field in art.get("fields", []):
            lv = field.get("legal_values")
            if isinstance(lv, list):
                out[field["name"]] = tuple(lv)
        return out

    def activation(self, filename: str, mode: str) -> str:
        return str(self.lookup(filename, mode)["activation"])

    def is_enforced_current_compatible(self, filename: str, mode: str) -> bool:
        return self.activation(filename, mode) == "enforced_current_compatible"

    def is_enforced_for_validation(self, filename: str, mode: str) -> bool:
        act = self.activation(filename, mode)
        return act in (
            "enforced_current_compatible",
            "enforced_s2_writer_aligned",
            "enforced_s2_ownership_cross_binding",
            "enforced_s3_manifest_completeness",
        )

    def evidence_completeness_inventory(self) -> dict[str, Any]:
        return dict(self._data.get("evidence_completeness_inventory") or {})

    def completeness_activation(self) -> str:
        return str(self.evidence_completeness_inventory().get("activation", ""))

    def is_s3_manifest_completeness_enforced(self) -> bool:
        return self.completeness_activation() == "enforced_s3_manifest_completeness"

    def recursive_inventory_helper(self) -> dict[str, Any]:
        return dict(self._data.get("recursive_inventory_helper") or {})

    def compatibility_file_required_fields(self) -> dict[str, tuple[str, ...]]:
        """Projection used as validator compatibility field map (not a second authority).

        For artifacts that declare historical_compatibility_required_fields, those
        fields are projected so historical fixtures remain accepted. Full active
        fields are enforced separately when S2 identity markers are present.
        """
        result: dict[str, tuple[str, ...]] = {}
        for art in self._artifacts:
            act = art.get("activation")
            if act not in (
                "enforced_current_compatible",
                "enforced_s2_writer_aligned",
                "enforced_s2_ownership_cross_binding",
                "enforced_s3_manifest_completeness",
            ):
                continue
            if art.get("exact_field_set_policy") in (
                "raw_stream",
                "manifest_grammar",
                "append_entry_grammar",
                "open_append_log_current",
            ):
                continue
            filename = art["filename"]
            if filename in ("HOST_OUTCOME_INGESTION.txt",):
                continue
            hist = art.get("historical_compatibility_required_fields")
            if isinstance(hist, list) and hist:
                fields = tuple(
                    f["name"]
                    for f in hist
                    if f.get("requirement", "required") == "required"
                )
            else:
                fields = tuple(
                    f["name"]
                    for f in art.get("fields", [])
                    if f.get("requirement", "required") == "required"
                )
            if not fields:
                continue
            if filename in result and result[filename] != fields:
                raise SchemaRegisterError(
                    f"compatibility projection conflict for {filename}: {result[filename]} vs {fields}"
                )
            result[filename] = fields
        return result

    def compatibility_host_outcome_fields(self) -> tuple[str, ...]:
        art = self.lookup("HOST_OUTCOME_INGESTION.txt", "host-preliminary")
        return tuple(f["name"] for f in art.get("fields", []))

    def run_id_policy(self) -> dict[str, Any]:
        return dict(self._data["run_id_policy"])

    def supersession(self) -> dict[str, Any]:
        return dict(self._data.get("supersession") or {})

    def historical_compatibility(self) -> dict[str, Any]:
        return dict(self._data.get("historical_compatibility") or {})


def _validate_nested_evidence_classes(block: dict[str, Any]) -> None:
    """Fail-closed structural validation for active typed nested class authority."""
    required_top = {
        "activation",
        "policy",
        "empty_directory_policy",
        "path_normalization",
        "unknown_prefix_policy",
        "unknown_class_policy",
        "overlap_policy",
        "manifest_inclusion",
        "classes",
        "note",
    }
    _reject_unknown_keys(block, required_top, "nested_evidence_classes")
    if block.get("activation") != "enforced_rc6_r4_typed_nested":
        raise SchemaRegisterError(
            "nested_evidence_classes.activation must be 'enforced_rc6_r4_typed_nested'"
        )
    if block.get("policy") != "exact_registered_class_only":
        raise SchemaRegisterError(
            "nested_evidence_classes.policy must be 'exact_registered_class_only'"
        )
    if block.get("empty_directory_policy") != "reject_all":
        raise SchemaRegisterError(
            "nested_evidence_classes.empty_directory_policy must be 'reject_all'"
        )
    for key in (
        "unknown_prefix_policy",
        "unknown_class_policy",
        "overlap_policy",
    ):
        if block.get(key) != "fail_closed":
            raise SchemaRegisterError(f"nested_evidence_classes.{key} must be 'fail_closed'")
    classes = _require_list(block.get("classes"), "nested_evidence_classes.classes")
    if not classes:
        raise SchemaRegisterError("nested_evidence_classes.classes must be non-empty")
    class_keys = frozenset(
        {
            "class_id",
            "purpose",
            "owner",
            "allowed_path_prefix",
            "filename_grammar",
            "lifecycle_modes",
            "presence",
            "load_bearing_provenance",
            "provenance_rule",
            "exact_field_set_policy",
            "fields",
            "legal_values",
            "note",
        }
    )
    seen_ids: set[str] = set()
    seen_prefixes: set[str] = set()
    for idx, raw in enumerate(classes):
        rec = _require_mapping(raw, f"nested_evidence_classes.classes[{idx}]")
        _reject_unknown_keys(rec, class_keys, f"nested_evidence_classes.classes[{idx}]")
        class_id = rec.get("class_id")
        if not isinstance(class_id, str) or not class_id:
            raise SchemaRegisterError(
                f"nested_evidence_classes.classes[{idx}]: class_id must be non-empty"
            )
        if class_id in seen_ids:
            raise SchemaRegisterError(f"duplicate nested class_id {class_id!r}")
        seen_ids.add(class_id)
        prefix = rec.get("allowed_path_prefix")
        if not isinstance(prefix, str) or not prefix or not prefix.endswith("/"):
            raise SchemaRegisterError(
                f"{class_id}: allowed_path_prefix must be a non-empty POSIX prefix ending with '/'"
            )
        if "\\" in prefix or prefix.startswith("/") or ".." in prefix.split("/"):
            raise SchemaRegisterError(f"{class_id}: allowed_path_prefix is unsafe: {prefix!r}")
        if prefix in seen_prefixes:
            raise SchemaRegisterError(f"duplicate nested allowed_path_prefix {prefix!r}")
        # Reject overlapping prefixes (one is prefix of another).
        for other in seen_prefixes:
            if prefix.startswith(other) or other.startswith(prefix):
                raise SchemaRegisterError(
                    f"overlapping nested allowed_path_prefix {prefix!r} vs {other!r}"
                )
        seen_prefixes.add(prefix)
        grammar = rec.get("filename_grammar")
        if not isinstance(grammar, str) or not grammar:
            raise SchemaRegisterError(f"{class_id}: filename_grammar must be a non-empty string")
        try:
            re.compile(grammar)
        except re.error as exc:
            raise SchemaRegisterError(
                f"{class_id}: filename_grammar is not a valid regex: {exc}"
            ) from exc
        modes = rec.get("lifecycle_modes")
        if not isinstance(modes, list) or not modes:
            raise SchemaRegisterError(f"{class_id}: lifecycle_modes must be a non-empty array")
        for mode in modes:
            if mode not in LEGAL_LIFECYCLE_MODES:
                raise SchemaRegisterError(f"{class_id}: unknown lifecycle mode {mode!r}")
        if rec.get("presence") not in ("optional", "conditional", "mandatory"):
            raise SchemaRegisterError(
                f"{class_id}: presence must be optional|conditional|mandatory"
            )
        if not isinstance(rec.get("load_bearing_provenance"), bool):
            raise SchemaRegisterError(f"{class_id}: load_bearing_provenance must be boolean")
        if rec.get("exact_field_set_policy") != "exact":
            raise SchemaRegisterError(f"{class_id}: exact_field_set_policy must be 'exact'")
        fields = _validate_field_list(
            _require_list(rec.get("fields"), f"{class_id}.fields"), f"{class_id}.fields"
        )
        required_names = {f["name"] for f in fields if f.get("requirement", "required") == "required"}
        for need in ("evidence_schema_version", "class_id", "purpose", "owner", "run_id"):
            if need not in required_names:
                raise SchemaRegisterError(f"{class_id}: fields must require {need}")
        legal = _require_mapping(rec.get("legal_values"), f"{class_id}.legal_values")
        for key in ("class_id", "purpose", "owner"):
            values = legal.get(key)
            if not isinstance(values, list) or not values:
                raise SchemaRegisterError(f"{class_id}.legal_values.{key} must be a non-empty array")
            if key == "class_id" and values != [class_id]:
                raise SchemaRegisterError(
                    f"{class_id}.legal_values.class_id must equal [{class_id!r}]"
                )


def validate_register_document(data: dict[str, Any]) -> None:
    _reject_unknown_keys(data, REGISTER_TOP_LEVEL_KEYS, "register")
    version = data.get("schema_register_version")
    if version not in SUPPORTED_REGISTER_VERSIONS:
        raise SchemaRegisterError(f"unsupported schema_register_version: {version!r}")
    supported = data.get("supported_register_versions")
    if not isinstance(supported, list) or version not in supported:
        raise SchemaRegisterError("supported_register_versions must include schema_register_version")
    if data.get("evidence_schema_version") != "1":
        raise SchemaRegisterError("evidence_schema_version must be '1' for this register family")
    modes = data.get("lifecycle_modes")
    if list(modes) != ["host-preliminary", "final-submission"]:
        raise SchemaRegisterError("lifecycle_modes must be [host-preliminary, final-submission]")
    alias = data.get("default_mode_compatibility_alias")
    if alias != "final-submission":
        raise SchemaRegisterError("default_mode_compatibility_alias must be final-submission")
    req_sets = _require_mapping(data.get("mode_required_file_sets"), "mode_required_file_sets")
    for mode in LEGAL_LIFECYCLE_MODES:
        if mode not in req_sets or not isinstance(req_sets[mode], list) or not req_sets[mode]:
            raise SchemaRegisterError(f"mode_required_file_sets.{mode} must be a non-empty array")
    acc = _require_mapping(data.get("mode_accepted_supporting_files"), "mode_accepted_supporting_files")
    for mode, files in acc.items():
        if mode not in LEGAL_LIFECYCLE_MODES:
            raise SchemaRegisterError(f"unknown mode in mode_accepted_supporting_files: {mode!r}")
        _require_list(files, f"mode_accepted_supporting_files.{mode}")
    _require_list(data.get("closed_aux_evidence_files"), "closed_aux_evidence_files")
    _require_mapping(data.get("run_id_policy"), "run_id_policy")
    _require_mapping(data.get("evidence_completeness_inventory"), "evidence_completeness_inventory")
    supersession = _require_mapping(data.get("supersession"), "supersession")
    if version == ACTIVE_REGISTER_VERSION:
        if data.get("family") != "rc6_remediation_canonical_schema":
            raise SchemaRegisterError(
                "active rc6 register family must be 'rc6_remediation_canonical_schema'"
            )
        if supersession.get("supersedes") != HISTORICAL_RC62_REGISTER_VERSION:
            raise SchemaRegisterError(
                "rc6 register supersession.supersedes must be "
                f"{HISTORICAL_RC62_REGISTER_VERSION!r}"
            )
        hist = _require_mapping(data.get("historical_compatibility"), "historical_compatibility")
        if hist.get("not_a_second_schema_authority") is not True:
            raise SchemaRegisterError(
                "historical_compatibility.not_a_second_schema_authority must be true"
            )
        if hist.get("active_authority") != ACTIVE_REGISTER_VERSION:
            raise SchemaRegisterError(
                f"historical_compatibility.active_authority must be {ACTIVE_REGISTER_VERSION!r}"
            )
        if hist.get("immediate_predecessor_version") != HISTORICAL_RC62_REGISTER_VERSION:
            raise SchemaRegisterError(
                "historical_compatibility.immediate_predecessor_version must be "
                f"{HISTORICAL_RC62_REGISTER_VERSION!r}"
            )
        if hist.get("earlier_historical_compatibility_version") != HISTORICAL_RC61_REGISTER_VERSION:
            raise SchemaRegisterError(
                "historical_compatibility.earlier_historical_compatibility_version must be "
                f"{HISTORICAL_RC61_REGISTER_VERSION!r}"
            )
        if hist.get("prior_historical_compatibility_version") != HISTORICAL_S2_REGISTER_VERSION:
            raise SchemaRegisterError(
                "historical_compatibility.prior_historical_compatibility_version must be "
                f"{HISTORICAL_S2_REGISTER_VERSION!r}"
            )
        if hist.get("earliest_historical_compatibility_version") != HISTORICAL_S1_REGISTER_VERSION:
            raise SchemaRegisterError(
                "historical_compatibility.earliest_historical_compatibility_version must be "
                f"{HISTORICAL_S1_REGISTER_VERSION!r}"
            )
        hist_versions = hist.get("historical_register_versions")
        if not isinstance(hist_versions, list) or set(hist_versions) != set(
            HISTORICAL_REGISTER_VERSIONS
        ):
            raise SchemaRegisterError(
                "historical_compatibility.historical_register_versions must list exactly "
                f"{sorted(HISTORICAL_REGISTER_VERSIONS)}"
            )
        _require_mapping(data.get("recursive_inventory_helper"), "recursive_inventory_helper")
        _validate_nested_evidence_classes(
            _require_mapping(data.get("nested_evidence_classes"), "nested_evidence_classes")
        )
    elif version == HISTORICAL_RC62_REGISTER_VERSION:
        if data.get("family") != "rc6_remediation_canonical_schema":
            raise SchemaRegisterError(
                "historical rc6.2 register family must be 'rc6_remediation_canonical_schema'"
            )
        hist = _require_mapping(data.get("historical_compatibility"), "historical_compatibility")
        if hist.get("not_a_second_schema_authority") is not True:
            raise SchemaRegisterError(
                "historical rc6.2 register historical_compatibility.not_a_second_schema_authority "
                "must be true"
            )
        _require_mapping(data.get("recursive_inventory_helper"), "recursive_inventory_helper")
        if "nested_evidence_classes" in data:
            raise SchemaRegisterError(
                "historical rc6.2 register must not declare nested_evidence_classes "
                "(typed nested authority is active rc6.3 only)"
            )
    elif version == HISTORICAL_RC61_REGISTER_VERSION:
        # Frozen rc6.1 documents retain their freeze-time historical_compatibility
        # block naming rc6.1 as active_authority; they are never the loader default.
        if data.get("family") != "rc6_remediation_canonical_schema":
            raise SchemaRegisterError(
                "historical rc6.1 register family must be 'rc6_remediation_canonical_schema'"
            )
        hist = _require_mapping(data.get("historical_compatibility"), "historical_compatibility")
        if hist.get("not_a_second_schema_authority") is not True:
            raise SchemaRegisterError(
                "historical rc6.1 register historical_compatibility.not_a_second_schema_authority "
                "must be true"
            )
        _require_mapping(data.get("recursive_inventory_helper"), "recursive_inventory_helper")
    elif version == HISTORICAL_S2_REGISTER_VERSION:
        # Frozen S2 documents retain their own historical_compatibility block naming
        # S2 as active_authority at freeze time; they must not be treated as the
        # loader's active default.
        hist = _require_mapping(data.get("historical_compatibility"), "historical_compatibility")
        if hist.get("not_a_second_schema_authority") is not True:
            raise SchemaRegisterError(
                "historical S2 register historical_compatibility.not_a_second_schema_authority "
                "must be true"
            )
        _require_mapping(data.get("recursive_inventory_helper"), "recursive_inventory_helper")
    elif version == HISTORICAL_S1_REGISTER_VERSION:
        # Frozen S1 documents must not claim to be the active authority.
        if "historical_compatibility" in data:
            raise SchemaRegisterError(
                "historical S1 register must not declare historical_compatibility block"
            )
        if "recursive_inventory_helper" in data:
            raise SchemaRegisterError(
                "historical S1 register must not declare recursive_inventory_helper"
            )
    artifacts = _require_list(data.get("artifacts"), "artifacts")
    if not artifacts:
        raise SchemaRegisterError("artifacts must be a non-empty array")
    seen_ids: set[str] = set()
    mode_file_pairs: set[tuple[str, str]] = set()
    for idx, raw in enumerate(artifacts):
        art = _validate_artifact(raw, idx)
        if version == ACTIVE_REGISTER_VERSION:
            policy = art.get("exact_field_set_policy")
            if policy in ACTIVE_FORBIDDEN_EXACT_POLICIES:
                raise SchemaRegisterError(
                    f"active rc6 register forbids exact_field_set_policy={policy!r} "
                    f"on {art['artifact_id']}"
                )
        aid = art["artifact_id"]
        if aid in seen_ids:
            raise SchemaRegisterError(f"duplicate artifact_id: {aid!r}")
        seen_ids.add(aid)
        for mode in art["lifecycle_modes"]:
            pair = (art["filename"], mode)
            if pair in mode_file_pairs and "@" in aid:
                for other in artifacts[:idx]:
                    if not isinstance(other, dict):
                        continue
                    if other.get("filename") == art["filename"] and mode in other.get(
                        "lifecycle_modes", []
                    ):
                        if "@" in str(other.get("artifact_id", "")) and other.get("artifact_id") != aid:
                            raise SchemaRegisterError(
                                f"duplicate artifact/mode definition for {art['filename']!r} mode {mode!r}"
                            )
            mode_file_pairs.add(pair)


def load_canonical_register(
    path: Path | None = None,
    *,
    version: str | None = None,
) -> CanonicalSchemaRegister:
    """Deterministically load and structurally validate a committed register.

    Default (no args): active rc6.1 register.
    Explicit version=S2/S1 or path to historical file: historical compatibility load.
    Unsupported versions fail closed. Path/version mismatch fails closed.
    Evidence content never selects the register.
    """
    if version is not None and path is not None:
        expected = register_path_for_version(version)
        if path.resolve() != expected.resolve():
            raise SchemaRegisterError(
                f"path/version mismatch: version={version!r} expects {expected}, got {path}"
            )
    if version is not None and path is None:
        path = register_path_for_version(version)
    register_path = path if path is not None else default_register_path()
    if not register_path.is_file():
        raise SchemaRegisterError(f"schema register not found: {register_path}")
    try:
        text = register_path.read_text(encoding="utf-8")
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise SchemaRegisterError(f"schema register JSON parse error: {exc}") from exc
    if not isinstance(data, dict):
        raise SchemaRegisterError("schema register root must be a JSON object")
    validate_register_document(data)
    if version is not None and data.get("schema_register_version") != version:
        raise SchemaRegisterError(
            f"loaded register version {data.get('schema_register_version')!r} "
            f"does not match requested {version!r}"
        )
    return CanonicalSchemaRegister(data, source_path=register_path.resolve())


def load_active_register() -> CanonicalSchemaRegister:
    """Load the single active rc6.3 canonical authority."""
    reg = load_canonical_register(version=ACTIVE_REGISTER_VERSION)
    if not reg.is_active_authority:
        raise SchemaRegisterError("active register load did not yield rc6.3 authority")
    return reg


def load_historical_register(version: str) -> CanonicalSchemaRegister:
    """Explicit historical-version load (compatibility only; never the default).

    Accepts only the fixed historical versions:
    rc6.2, rc6.1, rc5-phase4-s2.1, and rc5-phase4-s1.1. Unsupported versions
    fail closed. Evidence content cannot select the active/historical authority.
    """
    if version not in HISTORICAL_REGISTER_VERSIONS:
        raise SchemaRegisterError(
            f"unsupported historical schema_register_version: {version!r} "
            f"(accepted: {sorted(HISTORICAL_REGISTER_VERSIONS)})"
        )
    reg = load_canonical_register(version=version)
    if version == HISTORICAL_RC62_REGISTER_VERSION and not reg.is_historical_rc62:
        raise SchemaRegisterError("historical rc6.2 load did not yield rc6.2 register")
    if version == HISTORICAL_RC61_REGISTER_VERSION and not reg.is_historical_rc61:
        raise SchemaRegisterError("historical rc6.1 load did not yield rc6.1 register")
    if version == HISTORICAL_S2_REGISTER_VERSION and not reg.is_historical_s2:
        raise SchemaRegisterError("historical S2 load did not yield S2 register")
    if version == HISTORICAL_S1_REGISTER_VERSION and not reg.is_historical_s1:
        raise SchemaRegisterError("historical S1 load did not yield S1 register")
    if reg.is_active_authority:
        raise SchemaRegisterError("historical load must not yield active authority")
    return reg


def load_historical_rc62_register() -> CanonicalSchemaRegister:
    """Convenience wrapper for explicit rc6.2 historical load."""
    return load_historical_register(HISTORICAL_RC62_REGISTER_VERSION)


def load_historical_rc61_register() -> CanonicalSchemaRegister:
    """Convenience wrapper for explicit rc6.1 historical load."""
    return load_historical_register(HISTORICAL_RC61_REGISTER_VERSION)


def load_historical_s1_register() -> CanonicalSchemaRegister:
    """Convenience wrapper for explicit S1 historical load."""
    return load_historical_register(HISTORICAL_S1_REGISTER_VERSION)


def load_historical_s2_register() -> CanonicalSchemaRegister:
    """Convenience wrapper for explicit S2 historical load."""
    return load_historical_register(HISTORICAL_S2_REGISTER_VERSION)


def is_s2_shaped_package_identity(fields: dict[str, str]) -> bool:
    return any(key in fields for key in S2_PACKAGE_IDENTITY_MARKERS)


def is_s2_shaped_preliminary_deviations(fields: dict[str, str]) -> bool:
    return any(key in fields for key in S2_PRELIM_DEVIATIONS_MARKERS)


def is_s2_shaped_final_deviations(fields: dict[str, str]) -> bool:
    return "deviation_count" in fields


def is_s2_not_applicable_terminal(fields: dict[str, str]) -> bool:
    return fields.get("status") == "NOT_APPLICABLE" and "applicability" in fields


def is_s2_host_run_metadata(text: str) -> bool:
    return HOST_RUN_METADATA_ENTRY_BEGIN in text
