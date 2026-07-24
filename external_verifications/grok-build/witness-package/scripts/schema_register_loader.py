#!/usr/bin/env python3
"""Canonical schema-register loader for Phase 4-S1 (rc5 remediation path).

Loads the committed plain-JSON register under witness-package/schemas/ and
exposes fail-closed structural accessors for the validator and tests.

This module is the machine-readable schema authority loader. It does not
generate executable code from the register and uses only the Python standard
library.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SUPPORTED_REGISTER_VERSIONS = frozenset({"rc5-phase4-s1.1"})
DEFAULT_REGISTER_RELATIVE = Path("schemas") / "canonical_schema_register_rc5_phase4_s1.json"
LEGAL_LIFECYCLE_MODES = frozenset({"host-preliminary", "final-submission"})
LEGAL_ACTIVATIONS = frozenset(
    {
        "enforced_current_compatible",
        "defined_future_s2_writer_alignment",
        "defined_future_s3_manifest_completeness",
        "defined_structural_only_s1",
    }
)
LEGAL_FIELD_REQUIREMENTS = frozenset({"required", "optional", "conditional"})
LEGAL_EXACT_POLICIES = frozenset(
    {
        "exact",
        "required_subset_allowed",
        "raw_stream",
        "manifest_grammar",
        "open_append_log_current",
    }
)
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
        "lifecycle_modes",
        "default_mode_compatibility_alias",
        "mode_required_file_sets",
        "mode_accepted_supporting_files",
        "closed_aux_evidence_files",
        "run_id_policy",
        "evidence_completeness_inventory",
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
        "manifest_grammar",
        "activation_detail",
        "location",
    }
)

FIELD_KEYS = frozenset({"name", "requirement", "legal_values", "note", "activation"})


class SchemaRegisterError(ValueError):
    """Fail-closed schema register structural error."""


def default_register_path() -> Path:
    """Committed register path relative to the witness-package root."""
    scripts_dir = Path(__file__).resolve().parent
    return scripts_dir.parent / DEFAULT_REGISTER_RELATIVE


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
    classif = _require_mapping(art.get("required_file_classification"), f"{artifact_id}.required_file_classification")
    for mode, value in classif.items():
        if mode not in LEGAL_LIFECYCLE_MODES:
            raise SchemaRegisterError(f"{artifact_id}: unknown classification mode {mode!r}")
        if value not in LEGAL_FILE_CLASSIFICATIONS:
            raise SchemaRegisterError(f"{artifact_id}: unknown classification {value!r}")
    fields = _validate_field_list(_require_list(art.get("fields", []), f"{artifact_id}.fields"), f"{artifact_id}.fields")
    optional = _validate_field_list(
        _require_list(art.get("optional_fields", []), f"{artifact_id}.optional_fields"),
        f"{artifact_id}.optional_fields",
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
                    # Allow shared multi-mode entries; reject only true duplicates.
                    existing = self._index[key]
                    if existing is not art and existing.get("artifact_id") != art.get("artifact_id"):
                        # Mode-specific entries (filename@mode) intentionally share filename.
                        if "@" not in art["artifact_id"] and "@" not in existing["artifact_id"]:
                            raise SchemaRegisterError(
                                f"duplicate artifact/mode definition for {art['filename']!r} mode {mode!r}"
                            )
                # Prefer mode-specific artifact_id when present.
                if key not in self._index or "@" in art["artifact_id"]:
                    self._index[key] = art

    @property
    def raw(self) -> dict[str, Any]:
        return self._data

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

    def compatibility_file_required_fields(self) -> dict[str, tuple[str, ...]]:
        """Projection used as validator compatibility field map (not a second authority).

        Builds required-field tuples for currently enforced structured evidence
        files from the register. Mode-specific DEVIATIONS entries share one
        compatibility tuple when their required fields match.
        """
        result: dict[str, tuple[str, ...]] = {}
        for art in self._artifacts:
            if art.get("activation") != "enforced_current_compatible":
                continue
            if art.get("exact_field_set_policy") in ("raw_stream", "manifest_grammar"):
                continue
            filename = art["filename"]
            if filename in ("HOST_OUTCOME_INGESTION.txt",):
                continue
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
    _require_mapping(data.get("supersession"), "supersession")
    artifacts = _require_list(data.get("artifacts"), "artifacts")
    if not artifacts:
        raise SchemaRegisterError("artifacts must be a non-empty array")
    seen_ids: set[str] = set()
    mode_file_pairs: set[tuple[str, str]] = set()
    for idx, raw in enumerate(artifacts):
        art = _validate_artifact(raw, idx)
        aid = art["artifact_id"]
        if aid in seen_ids:
            raise SchemaRegisterError(f"duplicate artifact_id: {aid!r}")
        seen_ids.add(aid)
        for mode in art["lifecycle_modes"]:
            pair = (art["filename"], mode)
            # Multiple entries may share (filename, mode) only when one is a
            # shared multi-mode shell and another is mode-specific (@). Reject
            # two mode-specific or two shared duplicates.
            if pair in mode_file_pairs and "@" in aid:
                # Check whether an existing mode-specific entry already claims this.
                for other in artifacts[:idx]:
                    if not isinstance(other, dict):
                        continue
                    if other.get("filename") == art["filename"] and mode in other.get("lifecycle_modes", []):
                        if "@" in str(other.get("artifact_id", "")) and other.get("artifact_id") != aid:
                            raise SchemaRegisterError(
                                f"duplicate artifact/mode definition for {art['filename']!r} mode {mode!r}"
                            )
            mode_file_pairs.add(pair)


def load_canonical_register(path: Path | None = None) -> CanonicalSchemaRegister:
    """Deterministically load and structurally validate the committed register."""
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
    return CanonicalSchemaRegister(data, source_path=register_path.resolve())
