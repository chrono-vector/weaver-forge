"""R4-B Reconstructability Report — derived, non-authoritative evidence.

RECONSTRUCTABLE means only that required bounded inputs for reconstruction are
present and internally consistent. It does NOT mean correct, safe,
production-ready, independently validated, Human Final accepted, or authorized.

Semantic verification RECOMPUTES the report from canonical inputs and compares
to the stored artifact. Stored text/json alone is not proof.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence

from .authority import enforce_non_authority
from .provenance import (
    INDEPENDENT_EVIDENCE_ADMISSION_STATUS,
    ProvenanceRecord,
    account_independent_origins,
)
from .serialize import canonical_digest, canonical_dumps

SCHEMA_VERSION = "r4.epistemic.reconstructability.v1"
REPORT_FILENAME = "RECONSTRUCTABILITY_REPORT.json"

# Bounded required inputs for reconstructable=true (repo lifecycle artifacts).
REQUIRED_INPUT_KEYS = (
    "AUDIT_REQUEST.json",
    "CLAIM.json",
    "SCOPE.json",
    "PROVENANCE.json",
)

# Derived command templates — never treat freeform stored text as authority.
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
    text = value.strip()
    if not text:
        raise ReconstructabilityError(f"{field_name} must be a nonempty string")
    return text


def _coerce_str_list(value: Any, *, field_name: str) -> tuple[str, ...]:
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
    return tuple(sorted(dict.fromkeys(out)))


def _digest_or_none(obj: Any) -> str | None:
    if obj is None:
        return None
    if isinstance(obj, Mapping):
        return canonical_digest(dict(obj))
    return canonical_digest(obj)


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
        # EXECUTION_MANIFEST.json is intentionally omitted: the lifecycle may
        # rewrite it after decision/freeze; it is not a reconstructability input.
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

    def __post_init__(self) -> None:
        if self.authority is not False:
            raise ReconstructabilityError("authority must be false")
        if self.schema_version != SCHEMA_VERSION:
            raise ReconstructabilityError(
                f"schema_version must be {SCHEMA_VERSION!r}"
            )
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

    def body_dict(self) -> dict[str, Any]:
        """Material body excluding report_digest (digest is over this body)."""
        d: dict[str, Any] = {
            "schema_version": self.schema_version,
            "schema": self.schema_version,
            "authority": False,
            "audit_id": self.audit_id,
            "subject_id": self.subject_id,
            "run_id": self.audit_id,
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
        digest = self.report_digest or canonical_digest(d)
        d["report_digest"] = digest
        return d

    def canonical_json(self) -> str:
        return canonical_dumps(self.to_dict())

    def compute_digest(self) -> str:
        return canonical_digest(self.body_dict())

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ReconstructabilityReport":
        enforce_non_authority(data)
        schema = data.get("schema_version") or data.get("schema")
        if schema != SCHEMA_VERSION:
            raise ReconstructabilityError(
                f"schema_version must be {SCHEMA_VERSION!r}"
            )
        if "authority" not in data or data["authority"] is not False:
            raise ReconstructabilityError("authority must be Boolean false")
        cmds_raw = data.get("reproduction_commands")
        if not isinstance(cmds_raw, (list, tuple)):
            raise ReconstructabilityError(
                "reproduction_commands must be a list/tuple"
            )
        cmds: list[dict[str, Any]] = []
        for item in cmds_raw:
            if not isinstance(item, Mapping):
                raise ReconstructabilityError(
                    "reproduction_commands entries must be mappings"
                )
            cmds.append(dict(item))
        digests_raw = data.get("canonical_input_digests")
        if not isinstance(digests_raw, Mapping):
            raise ReconstructabilityError(
                "canonical_input_digests must be a mapping"
            )
        campaign_id = data.get("campaign_id")
        if campaign_id is not None and (
            not isinstance(campaign_id, str) or not campaign_id.strip()
        ):
            raise ReconstructabilityError(
                "campaign_id must be a nonempty string when set"
            )
        reconstructable = data.get("reconstructable")
        if not isinstance(reconstructable, bool):
            raise ReconstructabilityError("reconstructable must be a Boolean")
        artifact_count = data.get("artifact_count")
        if not isinstance(artifact_count, int) or isinstance(artifact_count, bool):
            raise ReconstructabilityError("artifact_count must be an int")
        iec = data.get("independent_evidence_count")
        if not isinstance(iec, int) or isinstance(iec, bool):
            raise ReconstructabilityError(
                "independent_evidence_count must be an int"
            )
        if iec != 0:
            raise ReconstructabilityError(
                "independent_evidence_count must be 0 while admission is "
                "NOT_CONFIGURED"
            )
        admission = data.get("independent_evidence_admission_status")
        if admission != INDEPENDENT_EVIDENCE_ADMISSION_STATUS:
            raise ReconstructabilityError(
                "independent_evidence_admission_status must be "
                f"{INDEPENDENT_EVIDENCE_ADMISSION_STATUS!r}"
            )
        audit_id = _require_nonempty_str(
            data.get("audit_id") or data.get("run_id"),
            field_name="audit_id",
        )
        subject_id = _require_nonempty_str(
            data.get("subject_id") or audit_id,
            field_name="subject_id",
        )
        derived_from = (
            _coerce_str_list(data["derived_from"], field_name="derived_from")
            if "derived_from" in data
            else ()
        )
        extra = data["extra"] if "extra" in data else {}
        if extra is None:
            extra = {}
        if not isinstance(extra, Mapping):
            raise ReconstructabilityError("extra must be a mapping when set")
        report = cls(
            schema_version=SCHEMA_VERSION,
            authority=False,
            audit_id=audit_id,
            subject_id=subject_id,
            campaign_id=campaign_id,
            input_refs=_coerce_str_list(
                data.get("input_refs", []), field_name="input_refs"
            ),
            required_inputs=_coerce_str_list(
                data.get("required_inputs", list(REQUIRED_INPUT_KEYS)),
                field_name="required_inputs",
            ),
            missing_inputs=_coerce_str_list(
                data.get("missing_inputs", []), field_name="missing_inputs"
            ),
            reproduction_commands=tuple(cmds),
            unresolved_assumptions=_coerce_str_list(
                data.get("unresolved_assumptions", []),
                field_name="unresolved_assumptions",
            ),
            artifact_count=artifact_count,
            lineage_ids=_coerce_str_list(
                data.get("lineage_ids", []), field_name="lineage_ids"
            ),
            independent_evidence_count=0,
            independent_evidence_admission_status=(
                INDEPENDENT_EVIDENCE_ADMISSION_STATUS
            ),
            reconstructable=reconstructable,
            derived_from=derived_from,
            canonical_input_digests={
                str(k): (None if v is None else str(v))
                for k, v in digests_raw.items()
            },
            report_digest=str(data.get("report_digest") or ""),
            extra=dict(extra),
        )
        expected_digest = report.compute_digest()
        stored_digest = data.get("report_digest")
        if stored_digest is not None and stored_digest != expected_digest:
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

    # Identity consistency — never silently invent missing bindings.
    if inputs.claim is not None and inputs.audit_request is not None:
        req_claim = inputs.audit_request.get("claim") or {}
        claim_id = inputs.claim.get("claim_id") or inputs.claim.get("id")
        req_id = req_claim.get("id") if isinstance(req_claim, Mapping) else None
        if claim_id and req_id and str(claim_id) != str(req_id):
            assumptions.append("CLAIM_ID_MISMATCH_REQUEST_VS_CLAIM")
    if inputs.decision is not None and "audit_id" in inputs.decision:
        # Decision docs may omit audit_id; if present it must match.
        if str(inputs.decision.get("audit_id")) != inputs.audit_id:
            assumptions.append("AUDIT_ID_MISMATCH_DECISION")

    # Pin provenance without file inventory is an unresolved assumption.
    if inputs.provenance_pin is not None:
        files = inputs.provenance_pin.get("files")
        if files is None:
            assumptions.append("PROVENANCE_PIN_MISSING_FILES_INVENTORY")
        elif not isinstance(files, (list, tuple)):
            assumptions.append("PROVENANCE_PIN_FILES_NOT_A_LIST")

    # Independent-evidence accounting reuses R4-A zero-count gate.
    # Pin inventory may supply artifact_count when epistemic provenance is absent;
    # that is not an unresolved reconstruction assumption.
    if inputs.epistemic_provenance_records:
        acct = account_independent_origins(inputs.epistemic_provenance_records)
        artifact_count = acct.artifact_count
        lineage_ids = acct.lineage_ids
    else:
        lineage_ids = ()
        artifact_count = 0
        if inputs.provenance_pin is not None:
            files = inputs.provenance_pin.get("files") or []
            if isinstance(files, (list, tuple)):
                artifact_count = len(files)

    # reconstructable requires required inputs present AND no consistency blockers.
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
    )
    digest = body.compute_digest()
    return ReconstructabilityReport(
        schema_version=body.schema_version,
        authority=False,
        audit_id=body.audit_id,
        subject_id=body.subject_id,
        campaign_id=body.campaign_id,
        input_refs=body.input_refs,
        required_inputs=body.required_inputs,
        missing_inputs=body.missing_inputs,
        reproduction_commands=body.reproduction_commands,
        unresolved_assumptions=body.unresolved_assumptions,
        artifact_count=body.artifact_count,
        lineage_ids=body.lineage_ids,
        independent_evidence_count=0,
        independent_evidence_admission_status=INDEPENDENT_EVIDENCE_ADMISSION_STATUS,
        reconstructable=body.reconstructable,
        derived_from=body.derived_from,
        canonical_input_digests=body.canonical_input_digests,
        report_digest=digest,
        extra=body.extra,
    )


def _material_view(report: Mapping[str, Any] | ReconstructabilityReport) -> dict[str, Any]:
    """Project to comparable material fields (includes digest of body)."""
    if isinstance(report, ReconstructabilityReport):
        data = report.to_dict()
    else:
        data = dict(report)
    # Exclude presentation-only aliases that normalize equivalently.
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
    # Normalize set-like via canonical_dumps round-trip comparison path.
    return out


def verify_reconstructability_report(
    stored: Mapping[str, Any] | ReconstructabilityReport,
    inputs: ReconstructabilityInputs,
) -> dict[str, Any]:
    """
    ONE canonical semantic verifier.

    Recompute expected report from inputs; compare to stored. Fail if stored
    was modified, missing_inputs/assumptions removed, reconstructable flipped,
    reproduction commands changed, input digests rebound, or counts differ.
    Outer hash rebinding alone cannot pass if semantic content differs.
    """
    expected = derive_reconstructability_report(inputs)
    if isinstance(stored, ReconstructabilityReport):
        stored_dict = stored.to_dict()
    else:
        stored_dict = dict(stored)

    # Structural non-authority + typing on stored before compare.
    try:
        parsed = ReconstructabilityReport.from_dict(stored_dict)
        stored_view = _material_view(parsed.to_dict())
    except (ReconstructabilityError, ValueError) as e:
        return {
            "ok": False,
            "status": "RECONSTRUCTABILITY_VERIFICATION_FAIL",
            "error": f"STORED_REPORT_INVALID:{e}",
            "match": False,
        }

    expected_view = _material_view(expected.to_dict())
    # Compare via canonical digests of material views (order-normalized).
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


def verify_reconstructability_at_root(audit_root: Path) -> dict[str, Any]:
    """
    Optional R4-B verification hook.

    Absent report => skipped (legacy compatible).
    Present report => must semantically recompute and match.
    """
    from audit_lifecycle.request import read_json

    audit_root = audit_root.resolve()
    path = audit_root / REPORT_FILENAME
    if not path.is_file():
        return {
            "ok": True,
            "status": "RECONSTRUCTABILITY_ABSENT_OPTIONAL",
            "present": False,
            "match": None,
        }
    stored = read_json(path)
    inputs = load_reconstructability_inputs(audit_root)
    result = verify_reconstructability_report(stored, inputs)
    result["present"] = True
    return result
