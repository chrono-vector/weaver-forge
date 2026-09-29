"""R4-B explicit state / expectation model.

Canonical package states:

  LEGACY_PRE_R4B  — strict complete pre-R4-B EXECUTION_MANIFEST (and matching
                    frozen package when freeze markers exist)
  R4_B_ENABLED    — root r4_b declares enabled expectation with R4-B contract marker

EXECUTION_MANIFEST.json is the SINGLE canonical R4-B expectation source for the
root. Frozen packages additionally cross-bind root, frozen MANIFEST, and
FREEZE_STATUS. State is NEVER inferred from artifact presence/absence alone.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from .reconstructability import REPORT_FILENAME
from .serialize import ABSENT, canonical_digest

EXPECTATION_SCHEMA_VERSION = "r4.epistemic.expectation.v1"

STATE_LEGACY_PRE_R4B = "LEGACY_PRE_R4B"
STATE_R4_B_ENABLED = "R4_B_ENABLED"

LEGACY_LIFECYCLE = "weaver_forge_audit_lifecycle_v0"
R4B_CONTRACT_MARKER = "weaver_forge_audit_lifecycle_r4b_v1"

FREEZE_STATE_PRE = "PRE_FREEZE"
FREEZE_STATE_IN_PROGRESS = "FREEZE_IN_PROGRESS"
FREEZE_STATE_FROZEN = "FROZEN"
FREEZE_STATE_INCOMPLETE = "FREEZE_INCOMPLETE"

# Exact required keys for a genuine historical legacy EXECUTION_MANIFEST.
LEGACY_REQUIRED_KEYS = frozenset(
    {
        "audit_id",
        "lifecycle",
        "stages_completed_through",
        "started_request",
        "claim_id",
        "adapter",
        "decision",
        "claim_result",
        "promoted_to_full",
        "baseline_prior_freeze_ok",
        "provenance_files",
        "timestamp_utc",
    }
)

# Optional keys observed on some historical legacy manifests.
LEGACY_OPTIONAL_KEYS = frozenset(
    {
        "freeze_performed",
        "freeze",
    }
)

LEGACY_ALLOWED_KEYS = LEGACY_REQUIRED_KEYS | LEGACY_OPTIONAL_KEYS

R4B_ALLOWED_KEYS = frozenset(
    {
        "schema_version",
        "enabled",
        "contract_marker",
        "reconstructability_report",
        "expected_disagreement_record_digests",
        "expected_disagreement_chain_heads",
        "finalized_for_freeze",
    }
)

RECON_REF_ALLOWED_KEYS = frozenset({"required", "path", "digest"})

_SHA256_HEX = frozenset("0123456789abcdef")

# Re-export shared absent sentinel for constructors.
_ABSENT = ABSENT


class R4BExpectationError(ValueError):
    """Malformed R4-B expectation / package state classification failure."""


def _require_sha256(value: Any, *, field_name: str) -> str:
    if not isinstance(value, str):
        raise R4BExpectationError(
            f"{field_name} must be a lowercase sha256 hex digest; "
            f"got {type(value).__name__}"
        )
    if len(value) != 64 or any(c not in _SHA256_HEX for c in value):
        raise R4BExpectationError(
            f"{field_name} must be a lowercase sha256 hex digest"
        )
    return value


def _require_nonempty_str(value: Any, *, field_name: str) -> str:
    if not isinstance(value, str):
        raise R4BExpectationError(
            f"{field_name} must be a nonempty string; got {type(value).__name__}"
        )
    if not value.strip():
        raise R4BExpectationError(f"{field_name} must be a nonempty string")
    return value


def _require_exact_bool(value: Any, *, field_name: str) -> bool:
    if type(value) is not bool:
        raise R4BExpectationError(
            f"{field_name} must be a Boolean; got {type(value).__name__}"
        )
    return value


def _require_int(value: Any, *, field_name: str) -> int:
    if type(value) is not int:
        raise R4BExpectationError(
            f"{field_name} must be an int; got {type(value).__name__}"
        )
    return value


def _require_digest_list(value: Any, *, field_name: str) -> tuple[str, ...]:
    if isinstance(value, str):
        raise R4BExpectationError(
            f"{field_name} must be a list/tuple of digests, not a string"
        )
    if not isinstance(value, (list, tuple)):
        raise R4BExpectationError(
            f"{field_name} must be a list/tuple of digests; "
            f"got {type(value).__name__}"
        )
    out: list[str] = []
    seen: set[str] = set()
    for item in value:
        digest = _require_sha256(item, field_name=f"{field_name} entry")
        if digest in seen:
            raise R4BExpectationError(f"{field_name} contains duplicate digest")
        seen.add(digest)
        out.append(digest)
    return tuple(out)


@dataclass(frozen=True)
class ReconstructabilityExpectation:
    required: bool
    path: str
    digest: str

    def __post_init__(self) -> None:
        if type(self.required) is not bool:
            raise R4BExpectationError(
                "reconstructability_report.required must be a Boolean"
            )
        if not isinstance(self.path, str) or not self.path.strip():
            raise R4BExpectationError(
                "reconstructability_report.path must be a nonempty string"
            )
        _require_sha256(self.digest, field_name="reconstructability_report.digest")

    def to_dict(self) -> dict[str, Any]:
        return {
            "required": self.required,
            "path": self.path,
            "digest": self.digest,
        }


@dataclass(frozen=True)
class R4BExpectation:
    """Parsed EXECUTION_MANIFEST.r4_b object."""

    schema_version: str
    enabled: bool
    contract_marker: str
    reconstructability_report: ReconstructabilityExpectation
    expected_disagreement_record_digests: tuple[str, ...]
    expected_disagreement_chain_heads: tuple[str, ...]
    finalized_for_freeze: bool

    def __post_init__(self) -> None:
        if self.schema_version != EXPECTATION_SCHEMA_VERSION:
            raise R4BExpectationError(
                f"r4_b.schema_version must be {EXPECTATION_SCHEMA_VERSION!r}"
            )
        if self.enabled is not True:
            raise R4BExpectationError("r4_b.enabled must be Boolean true when declared")
        if self.contract_marker != R4B_CONTRACT_MARKER:
            raise R4BExpectationError(
                f"r4_b.contract_marker must be {R4B_CONTRACT_MARKER!r}"
            )
        if type(self.finalized_for_freeze) is not bool:
            raise R4BExpectationError("r4_b.finalized_for_freeze must be a Boolean")
        if not isinstance(self.expected_disagreement_record_digests, tuple):
            raise R4BExpectationError(
                "expected_disagreement_record_digests must be a tuple"
            )
        if not isinstance(self.expected_disagreement_chain_heads, tuple):
            raise R4BExpectationError(
                "expected_disagreement_chain_heads must be a tuple"
            )
        if not isinstance(
            self.reconstructability_report, ReconstructabilityExpectation
        ):
            raise R4BExpectationError(
                "reconstructability_report must be ReconstructabilityExpectation"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "enabled": self.enabled,
            "contract_marker": self.contract_marker,
            "reconstructability_report": self.reconstructability_report.to_dict(),
            "expected_disagreement_record_digests": list(
                self.expected_disagreement_record_digests
            ),
            "expected_disagreement_chain_heads": list(
                self.expected_disagreement_chain_heads
            ),
            "finalized_for_freeze": self.finalized_for_freeze,
        }


@dataclass(frozen=True)
class PackageR4BState:
    state: str  # LEGACY_PRE_R4B | R4_B_ENABLED
    expectation: R4BExpectation | None = None
    manifest: Mapping[str, Any] | None = None


def strict_parse_r4b_expectation(value: Any) -> R4BExpectation:
    """Strictly validate the r4_b expectation object. NO COERCION."""
    if not isinstance(value, Mapping):
        raise R4BExpectationError(
            f"r4_b must be a mapping; got {type(value).__name__}"
        )
    unknown = set(value) - R4B_ALLOWED_KEYS
    if unknown:
        raise R4BExpectationError(
            f"r4_b contains unknown fields: {sorted(unknown)}"
        )
    for required in R4B_ALLOWED_KEYS:
        if required not in value:
            raise R4BExpectationError(f"r4_b missing required field {required!r}")

    schema = value["schema_version"]
    if not isinstance(schema, str) or schema != EXPECTATION_SCHEMA_VERSION:
        raise R4BExpectationError(
            f"r4_b.schema_version must be {EXPECTATION_SCHEMA_VERSION!r}"
        )
    enabled = value["enabled"]
    if enabled is not True:
        raise R4BExpectationError("r4_b.enabled must be Boolean true when declared")
    marker = value["contract_marker"]
    if not isinstance(marker, str) or marker != R4B_CONTRACT_MARKER:
        raise R4BExpectationError(
            f"r4_b.contract_marker must be {R4B_CONTRACT_MARKER!r}"
        )
    finalized = value["finalized_for_freeze"]
    if type(finalized) is not bool:
        raise R4BExpectationError("r4_b.finalized_for_freeze must be a Boolean")

    recon_raw = value["reconstructability_report"]
    if not isinstance(recon_raw, Mapping):
        raise R4BExpectationError(
            "r4_b.reconstructability_report must be a mapping; "
            f"got {type(recon_raw).__name__}"
        )
    unknown_recon = set(recon_raw) - RECON_REF_ALLOWED_KEYS
    if unknown_recon:
        raise R4BExpectationError(
            "reconstructability_report contains unknown fields: "
            f"{sorted(unknown_recon)}"
        )
    for key in RECON_REF_ALLOWED_KEYS:
        if key not in recon_raw:
            raise R4BExpectationError(
                f"reconstructability_report missing required field {key!r}"
            )
    required = recon_raw["required"]
    if required is not True:
        raise R4BExpectationError(
            "reconstructability_report.required must be Boolean true for R4-B"
        )
    path = recon_raw["path"]
    if not isinstance(path, str) or path != REPORT_FILENAME:
        raise R4BExpectationError(
            f"reconstructability_report.path must be {REPORT_FILENAME!r}"
        )
    digest = _require_sha256(
        recon_raw["digest"], field_name="reconstructability_report.digest"
    )

    digests = _require_digest_list(
        value["expected_disagreement_record_digests"],
        field_name="expected_disagreement_record_digests",
    )
    heads = _require_digest_list(
        value["expected_disagreement_chain_heads"],
        field_name="expected_disagreement_chain_heads",
    )
    head_set = set(heads)
    digest_set = set(digests)
    if not head_set.issubset(digest_set):
        raise R4BExpectationError(
            "expected_disagreement_chain_heads must be a subset of "
            "expected_disagreement_record_digests"
        )

    return R4BExpectation(
        schema_version=EXPECTATION_SCHEMA_VERSION,
        enabled=True,
        contract_marker=R4B_CONTRACT_MARKER,
        reconstructability_report=ReconstructabilityExpectation(
            required=True,
            path=REPORT_FILENAME,
            digest=digest,
        ),
        expected_disagreement_record_digests=digests,
        expected_disagreement_chain_heads=heads,
        finalized_for_freeze=finalized,
    )


def strict_parse_legacy_manifest(manifest: Any) -> dict[str, Any]:
    """
    Strict complete pre-R4-B EXECUTION_MANIFEST parser.

    Rejects subset-shaped / incomplete manifests and unknown keys.
    Missing r4_b alone is never sufficient for legacy classification.
    """
    if not isinstance(manifest, Mapping):
        raise R4BExpectationError(
            "legacy EXECUTION_MANIFEST must be a mapping; "
            f"got {type(manifest).__name__}"
        )
    if "r4_b" in manifest:
        raise R4BExpectationError(
            "legacy EXECUTION_MANIFEST must not contain r4_b"
        )
    keys = set(manifest)
    unknown = keys - LEGACY_ALLOWED_KEYS
    if unknown:
        raise R4BExpectationError(
            f"legacy EXECUTION_MANIFEST has unknown fields: {sorted(unknown)}"
        )
    missing = LEGACY_REQUIRED_KEYS - keys
    if missing:
        raise R4BExpectationError(
            "legacy EXECUTION_MANIFEST missing required fields: "
            f"{sorted(missing)}"
        )

    audit_id = _require_nonempty_str(manifest["audit_id"], field_name="audit_id")
    lifecycle = manifest["lifecycle"]
    if not isinstance(lifecycle, str) or lifecycle != LEGACY_LIFECYCLE:
        raise R4BExpectationError(
            f"legacy lifecycle must be {LEGACY_LIFECYCLE!r}"
        )
    _require_nonempty_str(
        manifest["stages_completed_through"],
        field_name="stages_completed_through",
    )
    _require_exact_bool(manifest["started_request"], field_name="started_request")
    _require_nonempty_str(manifest["claim_id"], field_name="claim_id")
    adapter = manifest["adapter"]
    if not isinstance(adapter, str) or not adapter.strip():
        raise R4BExpectationError("adapter must be a nonempty string")
    decision = manifest["decision"]
    if not isinstance(decision, str):
        raise R4BExpectationError("decision must be a string")
    claim_result = manifest["claim_result"]
    if not isinstance(claim_result, str):
        raise R4BExpectationError("claim_result must be a string")
    _require_exact_bool(
        manifest["promoted_to_full"], field_name="promoted_to_full"
    )
    _require_exact_bool(
        manifest["baseline_prior_freeze_ok"],
        field_name="baseline_prior_freeze_ok",
    )
    _require_int(manifest["provenance_files"], field_name="provenance_files")
    _require_nonempty_str(manifest["timestamp_utc"], field_name="timestamp_utc")

    if "freeze_performed" in manifest:
        _require_exact_bool(
            manifest["freeze_performed"], field_name="freeze_performed"
        )
    if "freeze" in manifest:
        freeze = manifest["freeze"]
        if not isinstance(freeze, Mapping):
            raise R4BExpectationError(
                f"freeze must be a mapping when present; got {type(freeze).__name__}"
            )

    return dict(manifest)


def is_allowlisted_legacy_manifest(manifest: Mapping[str, Any]) -> bool:
    """Compatibility wrapper — strict legacy parse success only."""
    try:
        strict_parse_legacy_manifest(manifest)
        return True
    except R4BExpectationError:
        return False


def classify_package_r4b_state(manifest: Any) -> PackageR4BState:
    """
    Classify package R4-B state from EXECUTION_MANIFEST only (pre-freeze / root).

    r4_b ABSENT + strict complete legacy shape => LEGACY_PRE_R4B
    r4_b PRESENT => must strict-parse; enabled => R4_B_ENABLED
    Otherwise fail closed.
    """
    if not isinstance(manifest, Mapping):
        raise R4BExpectationError(
            "EXECUTION_MANIFEST must be a mapping for R4-B state classification; "
            f"got {type(manifest).__name__}"
        )
    if "r4_b" not in manifest:
        parsed = strict_parse_legacy_manifest(manifest)
        return PackageR4BState(
            state=STATE_LEGACY_PRE_R4B,
            expectation=None,
            manifest=parsed,
        )

    expectation = strict_parse_r4b_expectation(manifest["r4_b"])
    if expectation.finalized_for_freeze is not True:
        raise R4BExpectationError(
            "r4_b.finalized_for_freeze must be true in frozen/verified R4-B packages"
        )
    return PackageR4BState(
        state=STATE_R4_B_ENABLED,
        expectation=expectation,
        manifest=dict(manifest),
    )


def classify_frozen_r4b_state(
    root_manifest: Any,
    frozen_manifest: Any,
    freeze_status: Any,
) -> PackageR4BState:
    """
    Monotonic frozen-state classification.

    Frozen manifest is the state anchor. Root r4_b must exist and match its
    committed digest when the frozen package declares R4-B. Legacy is allowed
    only when BOTH root and frozen package match a strict complete pre-R4-B
    schema. Missing root r4_b alone is never sufficient. Contradictory markers
    fail closed.
    """
    if not isinstance(root_manifest, Mapping):
        raise R4BExpectationError(
            "root EXECUTION_MANIFEST must be a mapping; "
            f"got {type(root_manifest).__name__}"
        )
    if not isinstance(frozen_manifest, Mapping):
        raise R4BExpectationError(
            "frozen MANIFEST must be a mapping; "
            f"got {type(frozen_manifest).__name__}"
        )
    if not isinstance(freeze_status, Mapping):
        raise R4BExpectationError(
            "FREEZE_STATUS must be a mapping; "
            f"got {type(freeze_status).__name__}"
        )

    status_marker = freeze_status.get("contract_marker")
    frozen_marker = frozen_manifest.get("contract_marker")
    root_has_r4b = "r4_b" in root_manifest
    frozen_has_r4b_binding = (
        frozen_marker == R4B_CONTRACT_MARKER
        or "r4_b_expectation_digest" in frozen_manifest
    )

    # Contradictory markers fail closed.
    if status_marker is not None and frozen_marker is not None:
        if status_marker != frozen_marker:
            raise R4BExpectationError(
                "contradictory contract markers between FREEZE_STATUS and "
                "frozen MANIFEST"
            )

    if frozen_has_r4b_binding or status_marker == R4B_CONTRACT_MARKER:
        if status_marker != R4B_CONTRACT_MARKER:
            raise R4BExpectationError(
                "FREEZE_STATUS.contract_marker must be "
                f"{R4B_CONTRACT_MARKER!r} for frozen R4-B packages"
            )
        if frozen_marker != R4B_CONTRACT_MARKER:
            raise R4BExpectationError(
                "frozen MANIFEST.contract_marker must be "
                f"{R4B_CONTRACT_MARKER!r} for frozen R4-B packages"
            )
        if not root_has_r4b:
            raise R4BExpectationError(
                "frozen R4-B package requires root EXECUTION_MANIFEST.r4_b; "
                "missing r4_b must not downgrade to legacy"
            )
        expectation = strict_parse_r4b_expectation(root_manifest["r4_b"])
        if expectation.finalized_for_freeze is not True:
            raise R4BExpectationError(
                "r4_b.finalized_for_freeze must be true in frozen R4-B packages"
            )
        committed = frozen_manifest.get("r4_b_expectation_digest")
        committed = _require_sha256(
            committed, field_name="frozen MANIFEST.r4_b_expectation_digest"
        )
        actual = expectation_digest(expectation)
        if committed != actual:
            raise R4BExpectationError(
                "root r4_b digest does not match frozen MANIFEST."
                "r4_b_expectation_digest"
            )
        status_exp = freeze_status.get("r4_b_expectation_digest")
        if status_exp is not None:
            status_exp = _require_sha256(
                status_exp, field_name="FREEZE_STATUS.r4_b_expectation_digest"
            )
            if status_exp != actual:
                raise R4BExpectationError(
                    "root r4_b digest does not match FREEZE_STATUS."
                    "r4_b_expectation_digest"
                )
        return PackageR4BState(
            state=STATE_R4_B_ENABLED,
            expectation=expectation,
            manifest=dict(root_manifest),
        )

    # Strict legacy path: BOTH root and frozen package must be pre-R4-B.
    if root_has_r4b:
        raise R4BExpectationError(
            "root declares r4_b but frozen package lacks R4-B contract marker"
        )
    if frozen_marker is not None and frozen_marker != LEGACY_LIFECYCLE:
        raise R4BExpectationError(
            f"unknown frozen MANIFEST.contract_marker: {frozen_marker!r}"
        )
    if status_marker is not None and status_marker != LEGACY_LIFECYCLE:
        raise R4BExpectationError(
            f"unknown FREEZE_STATUS.contract_marker: {status_marker!r}"
        )
    # Marker changed to legacy while residual R4-B bindings remain.
    if "r4_b_expectation_digest" in frozen_manifest:
        raise R4BExpectationError(
            "frozen MANIFEST retains r4_b_expectation_digest under non-R4-B marker"
        )

    strict_parse_legacy_manifest(root_manifest)
    # Frozen legacy MANIFEST must not carry R4-B bindings.
    if any(
        k in frozen_manifest
        for k in ("r4_b", "r4_b_expectation_digest")
    ):
        raise R4BExpectationError(
            "legacy frozen MANIFEST must not carry R4-B expectation bindings"
        )
    return PackageR4BState(
        state=STATE_LEGACY_PRE_R4B,
        expectation=None,
        manifest=dict(root_manifest),
    )


def build_r4b_expectation(
    *,
    reconstructability_report_digest: Any = ABSENT,
    expected_disagreement_record_digests: Any = ABSENT,
    expected_disagreement_chain_heads: Any = ABSENT,
    finalized_for_freeze: Any = ABSENT,
) -> dict[str, Any]:
    """Construct a canonical r4_b expectation mapping (constructor path)."""
    if reconstructability_report_digest is ABSENT:
        raise R4BExpectationError(
            "reconstructability_report_digest is required"
        )
    if expected_disagreement_record_digests is ABSENT:
        raise R4BExpectationError(
            "expected_disagreement_record_digests is required"
        )
    if expected_disagreement_chain_heads is ABSENT:
        raise R4BExpectationError(
            "expected_disagreement_chain_heads is required"
        )
    if finalized_for_freeze is ABSENT:
        finalized_for_freeze = True

    # Validate collections BEFORE any list()/tuple() conversion.
    digests = _require_digest_list(
        expected_disagreement_record_digests,
        field_name="expected_disagreement_record_digests",
    )
    heads = _require_digest_list(
        expected_disagreement_chain_heads,
        field_name="expected_disagreement_chain_heads",
    )
    digest = _require_sha256(
        reconstructability_report_digest,
        field_name="reconstructability_report_digest",
    )
    if type(finalized_for_freeze) is not bool:
        raise R4BExpectationError(
            "finalized_for_freeze must be a Boolean; "
            f"got {type(finalized_for_freeze).__name__}"
        )

    obj = {
        "schema_version": EXPECTATION_SCHEMA_VERSION,
        "enabled": True,
        "contract_marker": R4B_CONTRACT_MARKER,
        "reconstructability_report": {
            "required": True,
            "path": REPORT_FILENAME,
            "digest": digest,
        },
        "expected_disagreement_record_digests": list(digests),
        "expected_disagreement_chain_heads": list(heads),
        "finalized_for_freeze": finalized_for_freeze,
    }
    return strict_parse_r4b_expectation(obj).to_dict()


def load_execution_manifest(audit_root: Path) -> Mapping[str, Any]:
    from audit_lifecycle.request import read_json

    path = audit_root.resolve() / "EXECUTION_MANIFEST.json"
    if not path.is_file():
        raise R4BExpectationError("EXECUTION_MANIFEST.json missing")
    data = read_json(path)
    if not isinstance(data, Mapping):
        raise R4BExpectationError("EXECUTION_MANIFEST.json must be a mapping")
    return data


def classify_audit_root(audit_root: Path) -> PackageR4BState:
    return classify_package_r4b_state(load_execution_manifest(audit_root))


def expectation_digest(expectation: Mapping[str, Any] | R4BExpectation) -> str:
    if isinstance(expectation, R4BExpectation):
        return canonical_digest(expectation.to_dict())
    return canonical_digest(dict(expectation))


def frozen_package_dir(audit_root: Path) -> Path:
    audit_root = audit_root.resolve()
    return audit_root / "freeze" / f"{audit_root.name}_FROZEN"


def resolve_frozen_package_dir(
    audit_root: Path,
    *,
    freeze_status: Mapping[str, Any] | None = None,
) -> Path | None:
    """
    Resolve the frozen package directory.

    Prefer a package under the current audit_root (supports relocated fixture
    copies whose FREEZE_STATUS still records an absolute path from the
    original run). Fall back to the recorded absolute path only when it is
    already under audit_root.
    """
    audit_root = audit_root.resolve()
    freeze_root = audit_root / "freeze"

    def _under_root(path: Path) -> bool:
        try:
            path.resolve().relative_to(audit_root)
            return True
        except ValueError:
            return False

    if isinstance(freeze_status, Mapping) and freeze_status.get("freeze_directory"):
        recorded = Path(str(freeze_status["freeze_directory"]))
        local = freeze_root / recorded.name
        if local.is_dir():
            return local.resolve()
        if recorded.is_dir() and _under_root(recorded):
            return recorded.resolve()

    canonical = frozen_package_dir(audit_root)
    if canonical.is_dir():
        return canonical

    if freeze_root.is_dir():
        found = sorted(
            p
            for p in freeze_root.iterdir()
            if p.is_dir() and p.name.endswith("_FROZEN") and not p.name.startswith(".")
        )
        if len(found) == 1:
            return found[0].resolve()
    return None


def _manifest_claims_freeze(manifest: Mapping[str, Any] | None) -> bool:
    if not isinstance(manifest, Mapping):
        return False
    if manifest.get("freeze_performed") is True:
        return True
    if manifest.get("stages_completed_through") == "FREEZE":
        return True
    if "freeze" in manifest:
        return True
    return False


def validate_freeze_transaction(audit_root: Path) -> dict[str, Any]:
    """
    Three-state freeze transaction validator.

    PRE_FREEZE → FREEZE_IN_PROGRESS → FROZEN

    Incomplete intent/package/status combinations are FREEZE_INCOMPLETE and
    never verify as FROZEN. No automatic inference of completion or legacy.
    """
    from audit_lifecycle.request import read_json, sha256_file

    audit_root = audit_root.resolve()
    audit_id = audit_root.name
    intent_path = audit_root / "FREEZE_INTENT.json"
    status_path = audit_root / "FREEZE_STATUS.json"
    manifest_path = audit_root / "EXECUTION_MANIFEST.json"

    intent = read_json(intent_path) if intent_path.is_file() else None
    status = read_json(status_path) if status_path.is_file() else None
    root_manifest = read_json(manifest_path) if manifest_path.is_file() else None
    package_dir = resolve_frozen_package_dir(
        audit_root,
        freeze_status=status if isinstance(status, Mapping) else None,
    )
    package_present = package_dir is not None and package_dir.is_dir()

    # Detect orphan / partial temporary packages.
    freeze_root = audit_root / "freeze"
    temp_dirs: list[str] = []
    if freeze_root.is_dir():
        for p in freeze_root.iterdir():
            if p.is_dir() and p.name.startswith(".wf_freeze_tmp_"):
                temp_dirs.append(p.name)

    markers_present = any(
        [
            intent is not None,
            status is not None,
            package_present,
            bool(temp_dirs),
            _manifest_claims_freeze(root_manifest)
            if isinstance(root_manifest, Mapping)
            else False,
        ]
    )

    if not markers_present:
        return {
            "ok": True,
            "state": FREEZE_STATE_PRE,
            "verify_ok": True,
            "audit_id": audit_id,
            "package_present": False,
            "status_present": False,
            "intent_present": False,
        }

    def _incomplete(error: str, **extra: Any) -> dict[str, Any]:
        return {
            "ok": False,
            "state": FREEZE_STATE_INCOMPLETE,
            "verify_ok": False,
            "error": error,
            "audit_id": audit_id,
            "package_present": package_present,
            "status_present": status is not None,
            "intent_present": intent is not None,
            "temp_dirs": temp_dirs,
            **extra,
        }

    if temp_dirs:
        return _incomplete("PARTIAL_TEMPORARY_PACKAGE")

    # Status without package / package without status.
    if status is not None and not package_present:
        return _incomplete("STATUS_WITHOUT_PACKAGE", freeze_status=status)
    if package_present and status is None:
        return _incomplete("PACKAGE_WITHOUT_STATUS")

    # Manifest claiming freeze without status/package.
    if (
        isinstance(root_manifest, Mapping)
        and _manifest_claims_freeze(root_manifest)
        and (status is None or not package_present)
    ):
        return _incomplete(
            "MANIFEST_CLAIMS_FREEZE_WITHOUT_STATUS_OR_PACKAGE",
            root_manifest_claims_freeze=True,
        )

    # Intent alone (or intent without completed package/status).
    if intent is not None and (status is None or not package_present):
        return _incomplete(
            "FREEZE_INTENT_WITHOUT_COMPLETED_TRANSACTION",
            freeze_intent=intent,
        )

    # From here: both status and package must be present.
    if not isinstance(status, Mapping):
        return _incomplete("FREEZE_STATUS_NOT_A_MAPPING")

    freeze_performed = status.get("freeze_performed")
    state_field = status.get("state")
    if freeze_performed is not True or state_field != FREEZE_STATE_FROZEN:
        return _incomplete(
            "FREEZE_STATUS_NOT_FROZEN",
            freeze_status=status,
        )

    required_package_files = (
        "FINAL_DECISION.json",
        "FINAL_EVIDENCE_INDEX.json",
        "MANIFEST.json",
        "SHA256SUMS.txt",
        "REPRODUCTION_INSTRUCTIONS.md",
    )
    assert package_dir is not None
    missing_files = [
        name for name in required_package_files if not (package_dir / name).is_file()
    ]
    if missing_files:
        return _incomplete(
            "FROZEN_PACKAGE_INCOMPLETE",
            missing_package_files=missing_files,
        )

    frozen_manifest = read_json(package_dir / "MANIFEST.json")
    if not isinstance(frozen_manifest, Mapping):
        return _incomplete("FROZEN_MANIFEST_NOT_A_MAPPING")

    # Digest bindings on status.
    try:
        recorded_manifest_digest = _require_sha256(
            status.get("frozen_manifest_digest"),
            field_name="FREEZE_STATUS.frozen_manifest_digest",
        )
        recorded_sums_digest = _require_sha256(
            status.get("sha256sums_digest"),
            field_name="FREEZE_STATUS.sha256sums_digest",
        )
    except R4BExpectationError as e:
        return _incomplete(str(e), freeze_status=status)

    actual_manifest_digest = sha256_file(package_dir / "MANIFEST.json")
    actual_sums_digest = sha256_file(package_dir / "SHA256SUMS.txt")
    if recorded_manifest_digest != actual_manifest_digest:
        return _incomplete(
            "FROZEN_MANIFEST_DIGEST_MISMATCH",
            expected=recorded_manifest_digest,
            actual=actual_manifest_digest,
        )
    if recorded_sums_digest != actual_sums_digest:
        return _incomplete(
            "FREEZE_SUMS_DIGEST_MISMATCH",
            expected=recorded_sums_digest,
            actual=actual_sums_digest,
        )

    # Verify freeze SHA256SUMS contents.
    sums_path = package_dir / "SHA256SUMS.txt"
    fail = 0
    for line in sums_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        parts = line.split(None, 1)
        if len(parts) != 2:
            fail += 1
            continue
        digest, name = parts
        p = package_dir / name.strip()
        if not p.is_file() or sha256_file(p) != digest.lower():
            fail += 1
    if fail:
        return _incomplete("FREEZE_SHA256SUMS_VERIFY_FAIL", failed_entries=fail)

    status_marker = status.get("contract_marker")
    frozen_marker = frozen_manifest.get("contract_marker")
    if status_marker != frozen_marker:
        return _incomplete(
            "CONTRACT_MARKER_INCONSISTENT",
            status_marker=status_marker,
            frozen_marker=frozen_marker,
        )

    # Cross-bind R4-B / legacy classification for the frozen package.
    try:
        r4b_state = classify_frozen_r4b_state(
            root_manifest, frozen_manifest, status
        )
    except R4BExpectationError as e:
        return _incomplete(
            f"FROZEN_R4B_STATE:{e}",
            freeze_status=status,
        )

    recorded_dir = status.get("freeze_directory")
    if recorded_dir is not None:
        recorded_path = Path(str(recorded_dir))
        # Accept exact match or same package name under the current audit_root
        # (relocated fixture copies rewrite the absolute prefix).
        if (
            recorded_path.resolve() != package_dir
            and recorded_path.name != package_dir.name
        ):
            return _incomplete(
                "FREEZE_DIRECTORY_MISMATCH",
                recorded=recorded_dir,
                expected=str(package_dir),
            )

    return {
        "ok": True,
        "state": FREEZE_STATE_FROZEN,
        "verify_ok": True,
        "audit_id": audit_id,
        "package_present": True,
        "status_present": True,
        "intent_present": intent is not None,
        "contract_marker": status_marker,
        "r4b_state": r4b_state.state,
        "expectation": (
            r4b_state.expectation.to_dict() if r4b_state.expectation else None
        ),
        "frozen_manifest_digest": recorded_manifest_digest,
        "sha256sums_digest": recorded_sums_digest,
        "freeze_directory": str(package_dir),
        "freeze_status": status,
        "frozen_manifest": dict(frozen_manifest),
    }
