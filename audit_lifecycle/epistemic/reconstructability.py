"""R4-B Reconstructability Report — derived, non-authoritative evidence.

RECONSTRUCTABLE means only that required bounded inputs for reconstruction are
present and internally consistent. It does NOT mean correct, safe,
production-ready, independently validated, Human Final accepted, or authorized.

Canonical verification path:

  strict_parse_report → verify expected path/digest → derive_expected_report
  → exact semantic comparison

Stored text/json alone is not proof. Verifier never executes arbitrary stored
command text; reproduction command templates are code-owned only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

from .authority import enforce_non_authority
from .provenance import (
    INDEPENDENT_EVIDENCE_ADMISSION_STATUS,
    ProvenanceRecord,
    account_independent_origins,
)
from .serialize import ABSENT, canonical_digest, canonical_dumps

SCHEMA_VERSION = "r4.epistemic.reconstructability.v1"
REPORT_FILENAME = "RECONSTRUCTABILITY_REPORT.json"

_ABSENT = ABSENT

REQUIRED_INPUT_KEYS = (
    "AUDIT_REQUEST.json",
    "CLAIM.json",
    "SCOPE.json",
    "PROVENANCE.json",
)

CANONICAL_DIGEST_KEYS = frozenset(
    {
        "AUDIT_REQUEST.json",
        "CLAIM.json",
        "SCOPE.json",
        "PROVENANCE.json",
        "DECISION.json",
    }
)

REPORT_ALLOWED_KEYS = frozenset(
    {
        "schema_version",
        "schema",
        "authority",
        "audit_id",
        "subject_id",
        "run_id",
        "campaign_id",
        "input_refs",
        "required_inputs",
        "missing_inputs",
        "reproduction_commands",
        "unresolved_assumptions",
        "artifact_count",
        "lineage_ids",
        "independent_evidence_count",
        "independent_evidence_admission_status",
        "reconstructable",
        "derived_from",
        "canonical_input_digests",
        "report_digest",
        "extra",
    }
)

COMMAND_ALLOWED_KEYS = frozenset(
    {
        "command_id",
        "module",
        "subcommand",
        "argv_template",
        "derived_from",
    }
)

_SHA256_HEX = frozenset("0123456789abcdef")

_COMMAND_TEMPLATES: tuple[dict[str, Any], ...] = (
    {
        "command_id": "lifecycle_run",
        "module": "audit_lifecycle.cli",
        "subcommand": "run",
        "argv_template": [
            "python",
            "-m",
            "audit_lifecycle.cli",
            "run",
            "--request",
            "{request_path}",
            "--out",
            "{runs_parent}",
        ],
        "derived_from": f"{SCHEMA_VERSION}/command_templates",
    },
    {
        "command_id": "lifecycle_verify",
        "module": "audit_lifecycle.cli",
        "subcommand": "verify",
        "argv_template": [
            "python",
            "-m",
            "audit_lifecycle.cli",
            "verify",
            "--run",
            "{run_dir}",
        ],
        "derived_from": f"{SCHEMA_VERSION}/command_templates",
    },
)


class ReconstructabilityError(ValueError):
    """Malformed reconstructability report or verification failure."""


def _require_nonempty_str(value: Any, *, field_name: str) -> str:
    if not isinstance(value, str):
        raise ReconstructabilityError(
            f"{field_name} must be a nonempty string; got {type(value).__name__}"
        )
    if not value.strip():
        raise ReconstructabilityError(f"{field_name} must be a nonempty string")
    return value


def _require_exact_bool(value: Any, *, field_name: str) -> bool:
    if type(value) is not bool:
        raise ReconstructabilityError(
            f"{field_name} must be a Boolean; got {type(value).__name__}"
        )
    return value


def _require_int(value: Any, *, field_name: str) -> int:
    if type(value) is not int:
        raise ReconstructabilityError(
            f"{field_name} must be an int; got {type(value).__name__}"
        )
    return value


def _require_sha256_or_none(value: Any, *, field_name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ReconstructabilityError(
            f"{field_name} must be null or lowercase sha256; "
            f"got {type(value).__name__}"
        )
    if len(value) != 64 or any(c not in _SHA256_HEX for c in value):
        raise ReconstructabilityError(
            f"{field_name} must be null or lowercase sha256 hex digest"
        )
    return value


def _require_str_list(
    value: Any,
    *,
    field_name: str,
    allow_empty: bool = True,
) -> tuple[str, ...]:
    if isinstance(value, str):
        raise ReconstructabilityError(
            f"{field_name} must be a list/tuple of strings, not a string"
        )
    if not isinstance(value, (list, tuple)):
        raise ReconstructabilityError(
            f"{field_name} must be a list/tuple of strings; "
            f"got {type(value).__name__}"
        )
    out: list[str] = []
    for item in value:
        out.append(_require_nonempty_str(item, field_name=f"{field_name} entry"))
    if not allow_empty and not out:
        raise ReconstructabilityError(f"{field_name} must be nonempty")
    return tuple(sorted(dict.fromkeys(out)))


def _optional_str_list(
    data: Mapping[str, Any],
    key: str,
    *,
    default: tuple[str, ...] = (),
) -> tuple[str, ...]:
    if key not in data:
        return default
    return _require_str_list(data[key], field_name=key)


def _digest_or_none(obj: Any) -> str | None:
    if obj is None:
        return None
    if isinstance(obj, Mapping):
        return canonical_digest(dict(obj))
    return canonical_digest(obj)


def _require_schema_aliases(data: Mapping[str, Any]) -> str:
    has_sv = "schema_version" in data
    has_schema = "schema" in data
    if not has_sv and not has_schema:
        raise ReconstructabilityError("schema_version is required")
    if has_sv:
        sv = data["schema_version"]
        if not isinstance(sv, str):
            raise ReconstructabilityError(
                f"schema_version must be a string; got {type(sv).__name__}"
            )
    else:
        sv = None
    if has_schema:
        schema = data["schema"]
        if not isinstance(schema, str):
            raise ReconstructabilityError(
                f"schema must be a string; got {type(schema).__name__}"
            )
    else:
        schema = None
    if has_sv and has_schema and sv != schema:
        raise ReconstructabilityError(
            "schema_version and schema must be exactly equal when both present"
        )
    resolved = sv if has_sv else schema
    if resolved != SCHEMA_VERSION:
        raise ReconstructabilityError(
            f"schema_version must be {SCHEMA_VERSION!r}"
        )
    return SCHEMA_VERSION


def _parse_reproduction_command(item: Any) -> dict[str, Any]:
    if not isinstance(item, Mapping):
        raise ReconstructabilityError(
            "reproduction_commands entries must be mappings; "
            f"got {type(item).__name__}"
        )
    unknown = set(item) - COMMAND_ALLOWED_KEYS
    if unknown:
        raise ReconstructabilityError(
            f"reproduction_commands entry has unknown fields: {sorted(unknown)}"
        )
    for key in COMMAND_ALLOWED_KEYS:
        if key not in item:
            raise ReconstructabilityError(
                f"reproduction_commands entry missing {key!r}"
            )
    command_id = _require_nonempty_str(item["command_id"], field_name="command_id")
    module = _require_nonempty_str(item["module"], field_name="module")
    subcommand = _require_nonempty_str(item["subcommand"], field_name="subcommand")
    derived_from = _require_nonempty_str(
        item["derived_from"], field_name="derived_from"
    )
    argv = item["argv_template"]
    if isinstance(argv, str):
        raise ReconstructabilityError("argv_template must be a list/tuple of strings")
    if not isinstance(argv, (list, tuple)):
        raise ReconstructabilityError(
            f"argv_template must be a list/tuple of strings; got {type(argv).__name__}"
        )
    argv_out = [
        _require_nonempty_str(x, field_name="argv_template entry") for x in argv
    ]
    return {
        "command_id": command_id,
        "module": module,
        "subcommand": subcommand,
        "argv_template": argv_out,
        "derived_from": derived_from,
    }


def _parse_reproduction_commands(value: Any) -> tuple[dict[str, Any], ...]:
    if isinstance(value, str):
        raise ReconstructabilityError(
            "reproduction_commands must be a list/tuple, not a string"
        )
    if not isinstance(value, (list, tuple)):
        raise ReconstructabilityError(
            "reproduction_commands must be a list/tuple; "
            f"got {type(value).__name__}"
        )
    return tuple(_parse_reproduction_command(item) for item in value)


def _parse_canonical_input_digests(value: Any) -> dict[str, str | None]:
    if not isinstance(value, Mapping):
        raise ReconstructabilityError(
            "canonical_input_digests must be a mapping; "
            f"got {type(value).__name__}"
        )
    unknown = set(value) - CANONICAL_DIGEST_KEYS
    if unknown:
        raise ReconstructabilityError(
            f"canonical_input_digests has unknown keys: {sorted(unknown)}"
        )
    missing = CANONICAL_DIGEST_KEYS - set(value)
    if missing:
        raise ReconstructabilityError(
            f"canonical_input_digests missing keys: {sorted(missing)}"
        )
    return {
        key: _require_sha256_or_none(value[key], field_name=f"canonical_input_digests[{key}]")
        for key in sorted(CANONICAL_DIGEST_KEYS)
    }


def derive_reproduction_commands() -> list[dict[str, Any]]:
    """Canonical reproduction-command representation (derived, not freeform)."""
    return [dict(c) for c in _COMMAND_TEMPLATES]


@dataclass(frozen=True)
class ReconstructabilityInputs:
    """Canonical inputs for reconstructability derivation / recomputation."""

    audit_id: str
    claim: Mapping[str, Any] | None = None
    scope: Mapping[str, Any] | None = None
    audit_request: Mapping[str, Any] | None = None
    provenance_pin: Mapping[str, Any] | None = None
    epistemic_provenance_records: tuple[ProvenanceRecord, ...] = ()
    decision: Mapping[str, Any] | None = None
    execution_manifest: Mapping[str, Any] | None = None
    campaign_id: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.audit_id, str) or not self.audit_id.strip():
            raise ReconstructabilityError("audit_id must be a nonempty string")
        for name in (
            "claim",
            "scope",
            "audit_request",
            "provenance_pin",
            "decision",
            "execution_manifest",
        ):
            value = getattr(self, name)
            if value is not None and not isinstance(value, Mapping):
                raise ReconstructabilityError(
                    f"{name} must be a mapping or None; got {type(value).__name__}"
                )
        if not isinstance(self.epistemic_provenance_records, tuple):
            raise ReconstructabilityError(
                "epistemic_provenance_records must be a tuple; "
                f"got {type(self.epistemic_provenance_records).__name__}"
            )
        if self.campaign_id is not None:
            if not isinstance(self.campaign_id, str) or not self.campaign_id.strip():
                raise ReconstructabilityError(
                    "campaign_id must be a nonempty string when set"
                )

    def present_input_keys(self) -> tuple[str, ...]:
        present: list[str] = []
        if self.audit_request is not None:
            present.append("AUDIT_REQUEST.json")
        if self.claim is not None:
            present.append("CLAIM.json")
        if self.scope is not None:
            present.append("SCOPE.json")
        if self.provenance_pin is not None:
            present.append("PROVENANCE.json")
        if self.decision is not None:
            present.append("DECISION.json")
        return tuple(present)


@dataclass(frozen=True)
class ReconstructabilityReport:
    """Derived reconstructability evidence. authority:false always."""

    schema_version: str
    authority: bool
    audit_id: str
    subject_id: str
    campaign_id: str | None
    input_refs: tuple[str, ...]
    required_inputs: tuple[str, ...]
    missing_inputs: tuple[str, ...]
    reproduction_commands: tuple[Mapping[str, Any], ...]
    unresolved_assumptions: tuple[str, ...]
    artifact_count: int
    lineage_ids: tuple[str, ...]
    independent_evidence_count: int
    independent_evidence_admission_status: str
    reconstructable: bool
    derived_from: tuple[str, ...]
    canonical_input_digests: Mapping[str, str | None]
    report_digest: str = ""
    extra: Mapping[str, Any] = field(default_factory=dict)
    run_id: str | None = None

    def __post_init__(self) -> None:
        if self.authority is not False:
            raise ReconstructabilityError("authority must be false")
        if self.schema_version != SCHEMA_VERSION:
            raise ReconstructabilityError(
                f"schema_version must be {SCHEMA_VERSION!r}"
            )
        if not isinstance(self.audit_id, str) or not self.audit_id.strip():
            raise ReconstructabilityError("audit_id must be a nonempty string")
        if not isinstance(self.subject_id, str) or not self.subject_id.strip():
            raise ReconstructabilityError("subject_id must be a nonempty string")
        for name in (
            "input_refs",
            "required_inputs",
            "missing_inputs",
            "unresolved_assumptions",
            "lineage_ids",
            "derived_from",
        ):
            value = getattr(self, name)
            if not isinstance(value, tuple):
                raise ReconstructabilityError(
                    f"{name} must be a tuple; got {type(value).__name__}"
                )
            for item in value:
                if not isinstance(item, str) or not item.strip():
                    raise ReconstructabilityError(
                        f"{name} entries must be nonempty strings"
                    )
        if not isinstance(self.reproduction_commands, tuple):
            raise ReconstructabilityError(
                "reproduction_commands must be a tuple; "
                f"got {type(self.reproduction_commands).__name__}"
            )
        if type(self.artifact_count) is not int:
            raise ReconstructabilityError("artifact_count must be an int")
        if type(self.reconstructable) is not bool:
            raise ReconstructabilityError("reconstructable must be a Boolean")
        if not isinstance(self.canonical_input_digests, Mapping):
            raise ReconstructabilityError(
                "canonical_input_digests must be a mapping"
            )
        if not isinstance(self.extra, Mapping):
            raise ReconstructabilityError("extra must be a mapping")
        if self.independent_evidence_count != 0:
            raise ReconstructabilityError(
                "independent_evidence_count must be 0 while admission is "
                "NOT_CONFIGURED"
            )
        if (
            self.independent_evidence_admission_status
            != INDEPENDENT_EVIDENCE_ADMISSION_STATUS
        ):
            raise ReconstructabilityError(
                "independent_evidence_admission_status must be "
                f"{INDEPENDENT_EVIDENCE_ADMISSION_STATUS!r}"
            )
        if self.report_digest:
            if not isinstance(self.report_digest, str):
                raise ReconstructabilityError("report_digest must be a string")
            if len(self.report_digest) != 64 or any(
                c not in _SHA256_HEX for c in self.report_digest
            ):
                raise ReconstructabilityError(
                    "report_digest must be lowercase sha256 hex"
                )
        if self.campaign_id is not None:
            if not isinstance(self.campaign_id, str) or not self.campaign_id.strip():
                raise ReconstructabilityError(
                    "campaign_id must be a nonempty string when set"
                )
        if self.run_id is not None:
            if not isinstance(self.run_id, str) or not self.run_id.strip():
                raise ReconstructabilityError(
                    "run_id must be a nonempty string when set"
                )

    def body_dict(self) -> dict[str, Any]:
        """Material body excluding report_digest (digest is over this body)."""
        d: dict[str, Any] = {
            "schema_version": self.schema_version,
            "schema": self.schema_version,
            "authority": False,
            "audit_id": self.audit_id,
            "subject_id": self.subject_id,
            "run_id": self.run_id if self.run_id is not None else self.audit_id,
            "input_refs": list(self.input_refs),
            "required_inputs": list(self.required_inputs),
            "missing_inputs": list(self.missing_inputs),
            "reproduction_commands": [dict(c) for c in self.reproduction_commands],
            "unresolved_assumptions": list(self.unresolved_assumptions),
            "artifact_count": self.artifact_count,
            "lineage_ids": list(self.lineage_ids),
            "independent_evidence_count": self.independent_evidence_count,
            "independent_evidence_admission_status": (
                self.independent_evidence_admission_status
            ),
            "reconstructable": self.reconstructable,
            "derived_from": list(self.derived_from),
            "canonical_input_digests": dict(self.canonical_input_digests),
        }
        if self.campaign_id is not None:
            d["campaign_id"] = self.campaign_id
        if self.extra:
            d["extra"] = dict(self.extra)
        return d

    def to_dict(self) -> dict[str, Any]:
        d = self.body_dict()
        if not self.report_digest:
            raise ReconstructabilityError(
                "report_digest must be set before serialization"
            )
        d["report_digest"] = self.report_digest
        return d

    def canonical_json(self) -> str:
        return canonical_dumps(self.to_dict())

    def compute_digest(self) -> str:
        return canonical_digest(self.body_dict())

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ReconstructabilityReport":
        return strict_parse_report(data)


def strict_parse_report(data: Any) -> ReconstructabilityReport:
    """
    Canonical stored-report parser. NO COERCION.

    FIELD ABSENT: documented optional default may apply.
    FIELD PRESENT: must already have exact valid type/shape.
    Stored report_digest is REQUIRED and never synthesized here.
    """
    if not isinstance(data, Mapping):
        raise ReconstructabilityError(
            f"reconstructability report must be a mapping; got {type(data).__name__}"
        )
    enforce_non_authority(data)
    unknown = set(data) - REPORT_ALLOWED_KEYS
    if unknown:
        raise ReconstructabilityError(
            f"reconstructability report has unknown fields: {sorted(unknown)}"
        )

    _require_schema_aliases(data)
    if "authority" not in data or data["authority"] is not False:
        raise ReconstructabilityError("authority must be Boolean false")

    if "audit_id" not in data:
        raise ReconstructabilityError("audit_id is required")
    audit_id = _require_nonempty_str(data["audit_id"], field_name="audit_id")
    if "run_id" in data:
        run_id = _require_nonempty_str(data["run_id"], field_name="run_id")
    else:
        run_id = audit_id
    if "subject_id" not in data:
        raise ReconstructabilityError("subject_id is required")
    subject_id = _require_nonempty_str(data["subject_id"], field_name="subject_id")

    campaign_id = None
    if "campaign_id" in data:
        campaign_id = _require_nonempty_str(
            data["campaign_id"], field_name="campaign_id"
        )

    if "reproduction_commands" not in data:
        raise ReconstructabilityError("reproduction_commands is required")
    cmds = _parse_reproduction_commands(data["reproduction_commands"])

    if "canonical_input_digests" not in data:
        raise ReconstructabilityError("canonical_input_digests is required")
    digests = _parse_canonical_input_digests(data["canonical_input_digests"])

    if "reconstructable" not in data:
        raise ReconstructabilityError("reconstructable is required")
    reconstructable = _require_exact_bool(
        data["reconstructable"], field_name="reconstructable"
    )

    if "artifact_count" not in data:
        raise ReconstructabilityError("artifact_count is required")
    artifact_count = _require_int(data["artifact_count"], field_name="artifact_count")

    if "independent_evidence_count" not in data:
        raise ReconstructabilityError("independent_evidence_count is required")
    iec = _require_int(
        data["independent_evidence_count"],
        field_name="independent_evidence_count",
    )
    if iec != 0:
        raise ReconstructabilityError(
            "independent_evidence_count must be 0 while admission is NOT_CONFIGURED"
        )

    if "independent_evidence_admission_status" not in data:
        raise ReconstructabilityError(
            "independent_evidence_admission_status is required"
        )
    admission = data["independent_evidence_admission_status"]
    if not isinstance(admission, str):
        raise ReconstructabilityError(
            "independent_evidence_admission_status must be a string"
        )
    if admission != INDEPENDENT_EVIDENCE_ADMISSION_STATUS:
        raise ReconstructabilityError(
            "independent_evidence_admission_status must be "
            f"{INDEPENDENT_EVIDENCE_ADMISSION_STATUS!r}"
        )

    if "report_digest" not in data:
        raise ReconstructabilityError("report_digest is required")
    report_digest = _require_sha256_or_none(
        data["report_digest"], field_name="report_digest"
    )
    if report_digest is None:
        raise ReconstructabilityError("report_digest is required")

    if "required_inputs" not in data:
        raise ReconstructabilityError("required_inputs is required")
    required_inputs = _require_str_list(
        data["required_inputs"], field_name="required_inputs"
    )
    if "missing_inputs" not in data:
        raise ReconstructabilityError("missing_inputs is required")
    missing_inputs = _require_str_list(
        data["missing_inputs"], field_name="missing_inputs"
    )
    if "input_refs" not in data:
        raise ReconstructabilityError("input_refs is required")
    input_refs = _require_str_list(data["input_refs"], field_name="input_refs")
    if "unresolved_assumptions" not in data:
        raise ReconstructabilityError("unresolved_assumptions is required")
    unresolved = _require_str_list(
        data["unresolved_assumptions"], field_name="unresolved_assumptions"
    )
    if "lineage_ids" not in data:
        raise ReconstructabilityError("lineage_ids is required")
    lineage_ids = _require_str_list(data["lineage_ids"], field_name="lineage_ids")
    derived_from = _optional_str_list(data, "derived_from", default=())

    if "extra" in data:
        extra = data["extra"]
        if not isinstance(extra, Mapping):
            raise ReconstructabilityError(
                f"extra must be a mapping when present; got {type(extra).__name__}"
            )
        extra_map = dict(extra)
    else:
        extra_map = {}

    report = ReconstructabilityReport(
        schema_version=SCHEMA_VERSION,
        authority=False,
        audit_id=audit_id,
        subject_id=subject_id,
        campaign_id=campaign_id,
        input_refs=input_refs,
        required_inputs=required_inputs,
        missing_inputs=missing_inputs,
        reproduction_commands=cmds,
        unresolved_assumptions=unresolved,
        artifact_count=artifact_count,
        lineage_ids=lineage_ids,
        independent_evidence_count=0,
        independent_evidence_admission_status=INDEPENDENT_EVIDENCE_ADMISSION_STATUS,
        reconstructable=reconstructable,
        derived_from=derived_from,
        canonical_input_digests=digests,
        report_digest=report_digest,
        extra=extra_map,
        run_id=run_id,
    )
    expected_digest = report.compute_digest()
    if report_digest != expected_digest:
        raise ReconstructabilityError(
            "report_digest does not match canonical body digest"
        )
    return report


def derive_reconstructability_report(
    inputs: ReconstructabilityInputs,
) -> ReconstructabilityReport:
    """
    ONE canonical derivation path: canonical inputs → reconstructability report.

    reconstructable=true only when all REQUIRED_INPUT_KEYS are present and
    internal identity consistency checks pass.
    """
    if not isinstance(inputs.audit_id, str) or not inputs.audit_id.strip():
        raise ReconstructabilityError("audit_id must be nonempty")

    present = set(inputs.present_input_keys())
    missing = tuple(k for k in REQUIRED_INPUT_KEYS if k not in present)
    assumptions: list[str] = []

    if inputs.claim is not None and inputs.audit_request is not None:
        req_claim = inputs.audit_request.get("claim")
        if not isinstance(req_claim, Mapping):
            req_claim = {}
        claim_id = inputs.claim.get("claim_id")
        if claim_id is None:
            claim_id = inputs.claim.get("id")
        req_id = req_claim.get("id") if isinstance(req_claim, Mapping) else None
        if (
            isinstance(claim_id, str)
            and isinstance(req_id, str)
            and claim_id
            and req_id
            and claim_id != req_id
        ):
            assumptions.append("CLAIM_ID_MISMATCH_REQUEST_VS_CLAIM")
    if inputs.decision is not None and "audit_id" in inputs.decision:
        decision_audit = inputs.decision.get("audit_id")
        if decision_audit != inputs.audit_id:
            assumptions.append("AUDIT_ID_MISMATCH_DECISION")

    if inputs.provenance_pin is not None:
        files = inputs.provenance_pin.get("files")
        if files is None:
            assumptions.append("PROVENANCE_PIN_MISSING_FILES_INVENTORY")
        elif not isinstance(files, (list, tuple)):
            assumptions.append("PROVENANCE_PIN_FILES_NOT_A_LIST")

    if inputs.epistemic_provenance_records:
        acct = account_independent_origins(inputs.epistemic_provenance_records)
        artifact_count = acct.artifact_count
        lineage_ids = acct.lineage_ids
    else:
        lineage_ids = ()
        artifact_count = 0
        if inputs.provenance_pin is not None:
            files = inputs.provenance_pin.get("files")
            if isinstance(files, (list, tuple)):
                artifact_count = len(files)

    reconstructable = (not missing) and (not assumptions)

    digests: dict[str, str | None] = {
        "AUDIT_REQUEST.json": _digest_or_none(inputs.audit_request),
        "CLAIM.json": _digest_or_none(inputs.claim),
        "SCOPE.json": _digest_or_none(inputs.scope),
        "PROVENANCE.json": _digest_or_none(inputs.provenance_pin),
        "DECISION.json": _digest_or_none(inputs.decision),
    }

    derived_from = tuple(sorted(k for k in REQUIRED_INPUT_KEYS if k in present))
    if "DECISION.json" in present:
        derived_from = tuple(sorted(derived_from + ("DECISION.json",)))

    body = ReconstructabilityReport(
        schema_version=SCHEMA_VERSION,
        authority=False,
        audit_id=inputs.audit_id,
        subject_id=inputs.audit_id,
        campaign_id=inputs.campaign_id,
        input_refs=tuple(sorted(present)),
        required_inputs=tuple(sorted(REQUIRED_INPUT_KEYS)),
        missing_inputs=tuple(sorted(missing)),
        reproduction_commands=tuple(derive_reproduction_commands()),
        unresolved_assumptions=tuple(sorted(set(assumptions))),
        artifact_count=artifact_count,
        lineage_ids=tuple(sorted(lineage_ids)),
        independent_evidence_count=0,
        independent_evidence_admission_status=INDEPENDENT_EVIDENCE_ADMISSION_STATUS,
        reconstructable=reconstructable,
        derived_from=derived_from,
        canonical_input_digests=digests,
        report_digest="",
        run_id=inputs.audit_id,
    )
    digest = body.compute_digest()
    payload = body.body_dict()
    payload["report_digest"] = digest
    # Factories finish by parsing through the canonical strict parser.
    return strict_parse_report(payload)


def derive_expected_report(
    inputs: ReconstructabilityInputs,
) -> ReconstructabilityReport:
    """Alias for the single canonical derivation path used by verification."""
    return derive_reconstructability_report(inputs)


def _material_view(report: Mapping[str, Any] | ReconstructabilityReport) -> dict[str, Any]:
    if isinstance(report, ReconstructabilityReport):
        data = report.to_dict()
    else:
        data = dict(report)
    keys = (
        "schema_version",
        "authority",
        "audit_id",
        "subject_id",
        "run_id",
        "campaign_id",
        "input_refs",
        "required_inputs",
        "missing_inputs",
        "reproduction_commands",
        "unresolved_assumptions",
        "artifact_count",
        "lineage_ids",
        "independent_evidence_count",
        "independent_evidence_admission_status",
        "reconstructable",
        "derived_from",
        "canonical_input_digests",
        "report_digest",
    )
    out: dict[str, Any] = {}
    for k in keys:
        if k in data:
            out[k] = data[k]
    return out


def verify_reconstructability_report(
    stored: Mapping[str, Any] | ReconstructabilityReport,
    inputs: ReconstructabilityInputs,
) -> dict[str, Any]:
    """
    ONE canonical semantic verifier.

    strict_parse_report → derive_expected_report → exact semantic comparison.
    Outer hash rebinding alone cannot pass if semantic content differs.
    """
    expected = derive_expected_report(inputs)
    if isinstance(stored, ReconstructabilityReport):
        stored_dict = stored.to_dict()
    else:
        stored_dict = dict(stored)

    try:
        parsed = strict_parse_report(stored_dict)
        stored_view = _material_view(parsed.to_dict())
    except (ReconstructabilityError, ValueError) as e:
        return {
            "ok": False,
            "status": "RECONSTRUCTABILITY_VERIFICATION_FAIL",
            "error": f"STORED_REPORT_INVALID:{e}",
            "match": False,
        }

    expected_view = _material_view(expected.to_dict())
    stored_digest = canonical_digest(stored_view)
    expected_digest = canonical_digest(expected_view)
    match = stored_digest == expected_digest

    mismatches: list[str] = []
    if not match:
        for key in sorted(set(stored_view) | set(expected_view)):
            if stored_view.get(key) != expected_view.get(key):
                mismatches.append(key)

    return {
        "ok": match,
        "status": (
            "RECONSTRUCTABILITY_VERIFICATION_PASS"
            if match
            else "RECONSTRUCTABILITY_VERIFICATION_FAIL"
        ),
        "match": match,
        "mismatched_fields": mismatches,
        "expected_report_digest": expected.report_digest,
        "stored_report_digest": stored_view.get("report_digest"),
        "authority": False,
    }


def load_reconstructability_inputs(audit_root: Path) -> ReconstructabilityInputs:
    """Load canonical inputs from an audit run directory (fail-soft on missing)."""
    from audit_lifecycle.request import read_json

    audit_root = audit_root.resolve()
    audit_id = audit_root.name

    def _maybe(name: str) -> Mapping[str, Any] | None:
        path = audit_root / name
        if not path.is_file():
            return None
        obj = read_json(path)
        return obj if isinstance(obj, Mapping) else None

    request = _maybe("AUDIT_REQUEST.json")
    campaign_id = None
    if request is not None:
        cid = request.get("campaign_id")
        if isinstance(cid, str) and cid.strip():
            campaign_id = cid

    return ReconstructabilityInputs(
        audit_id=audit_id,
        claim=_maybe("CLAIM.json"),
        scope=_maybe("SCOPE.json"),
        audit_request=request,
        provenance_pin=_maybe("PROVENANCE.json"),
        epistemic_provenance_records=(),
        decision=_maybe("DECISION.json"),
        execution_manifest=_maybe("EXECUTION_MANIFEST.json"),
        campaign_id=campaign_id,
    )


def emit_reconstructability_report(
    audit_root: Path,
    *,
    inputs: ReconstructabilityInputs | None = None,
) -> ReconstructabilityReport:
    """Derive and write RECONSTRUCTABILITY_REPORT.json under audit_root."""
    from audit_lifecycle.request import write_json

    audit_root = audit_root.resolve()
    if inputs is None:
        inputs = load_reconstructability_inputs(audit_root)
    report = derive_reconstructability_report(inputs)
    write_json(audit_root / REPORT_FILENAME, report.to_dict())
    return report


def verify_reconstructability_at_root(
    audit_root: Path,
    *,
    required: bool = False,
    expected_path: str | None = None,
    expected_digest: str | None = None,
) -> dict[str, Any]:
    """
    Reconstructability verification hook.

    required=False (legacy): absent report => skipped.
    required=True (R4_B_ENABLED): report must exist at exact path/digest and
    semantically recompute.
    """
    from audit_lifecycle.request import read_json

    audit_root = audit_root.resolve()
    path_name = expected_path or REPORT_FILENAME
    path = audit_root / path_name
    if not path.is_file():
        if required:
            return {
                "ok": False,
                "status": "RECONSTRUCTABILITY_VERIFICATION_FAIL",
                "error": "RECONSTRUCTABILITY_REPORT_MISSING",
                "present": False,
                "match": False,
            }
        return {
            "ok": True,
            "status": "RECONSTRUCTABILITY_ABSENT_OPTIONAL",
            "present": False,
            "match": None,
        }
    if path_name != REPORT_FILENAME:
        return {
            "ok": False,
            "status": "RECONSTRUCTABILITY_VERIFICATION_FAIL",
            "error": "RECONSTRUCTABILITY_REPORT_PATH_MISMATCH",
            "present": True,
            "match": False,
        }
    stored = read_json(path)
    inputs = load_reconstructability_inputs(audit_root)
    result = verify_reconstructability_report(stored, inputs)
    result["present"] = True
    if expected_digest is not None and result.get("ok"):
        stored_digest = result.get("stored_report_digest")
        if stored_digest != expected_digest:
            return {
                "ok": False,
                "status": "RECONSTRUCTABILITY_VERIFICATION_FAIL",
                "error": "RECONSTRUCTABILITY_REPORT_DIGEST_MISMATCH",
                "present": True,
                "match": False,
                "expected_digest": expected_digest,
                "stored_report_digest": stored_digest,
            }
    return result
