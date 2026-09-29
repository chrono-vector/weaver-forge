"""R4-B explicit state / expectation model.

Canonical states (exactly two):

  LEGACY_PRE_R4B  — allowlisted legacy EXECUTION_MANIFEST without r4_b
  R4_B_ENABLED    — EXECUTION_MANIFEST.r4_b declares enabled expectation

EXECUTION_MANIFEST.json is the SINGLE canonical R4-B expectation source.
State is NEVER inferred from artifact presence/absence alone.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from .reconstructability import REPORT_FILENAME
from .serialize import canonical_digest

EXPECTATION_SCHEMA_VERSION = "r4.epistemic.expectation.v1"

STATE_LEGACY_PRE_R4B = "LEGACY_PRE_R4B"
STATE_R4_B_ENABLED = "R4_B_ENABLED"

LEGACY_LIFECYCLE = "weaver_forge_audit_lifecycle_v0"

# Explicit allowlisted legacy EXECUTION_MANIFEST keys (shape/version gate).
LEGACY_ALLOWED_KEYS = frozenset(
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
        "freeze_performed",
        "freeze",
    }
)

R4B_ALLOWED_KEYS = frozenset(
    {
        "schema_version",
        "enabled",
        "reconstructability_report",
        "expected_disagreement_record_digests",
        "expected_disagreement_chain_heads",
        "finalized_for_freeze",
    }
)

RECON_REF_ALLOWED_KEYS = frozenset({"required", "path", "digest"})

_SHA256_HEX = frozenset("0123456789abcdef")


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
    reconstructability_report: ReconstructabilityExpectation
    expected_disagreement_record_digests: tuple[str, ...]
    expected_disagreement_chain_heads: tuple[str, ...]
    finalized_for_freeze: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "enabled": self.enabled,
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
    digest = _require_sha256(recon_raw["digest"], field_name="reconstructability_report.digest")

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
        reconstructability_report=ReconstructabilityExpectation(
            required=True,
            path=REPORT_FILENAME,
            digest=digest,
        ),
        expected_disagreement_record_digests=digests,
        expected_disagreement_chain_heads=heads,
        finalized_for_freeze=finalized,
    )


def is_allowlisted_legacy_manifest(manifest: Mapping[str, Any]) -> bool:
    """Explicit legacy shape/version gate. Absence of artifacts is irrelevant."""
    if not isinstance(manifest, Mapping):
        return False
    if "r4_b" in manifest:
        return False
    unknown = set(manifest) - LEGACY_ALLOWED_KEYS
    if unknown:
        return False
    lifecycle = manifest.get("lifecycle")
    if lifecycle != LEGACY_LIFECYCLE:
        return False
    audit_id = manifest.get("audit_id")
    if not isinstance(audit_id, str) or not audit_id.strip():
        return False
    return True


def classify_package_r4b_state(manifest: Any) -> PackageR4BState:
    """
    Classify package R4-B state from EXECUTION_MANIFEST only.

    r4_b ABSENT + allowlisted legacy shape => LEGACY_PRE_R4B
    r4_b PRESENT => must strict-parse; enabled => R4_B_ENABLED
    Otherwise fail closed.
    """
    if not isinstance(manifest, Mapping):
        raise R4BExpectationError(
            "EXECUTION_MANIFEST must be a mapping for R4-B state classification; "
            f"got {type(manifest).__name__}"
        )
    if "r4_b" not in manifest:
        if not is_allowlisted_legacy_manifest(manifest):
            raise R4BExpectationError(
                "EXECUTION_MANIFEST lacks r4_b and is not an allowlisted "
                "legacy manifest shape/version"
            )
        return PackageR4BState(
            state=STATE_LEGACY_PRE_R4B,
            expectation=None,
            manifest=dict(manifest),
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


def build_r4b_expectation(
    *,
    reconstructability_report_digest: str,
    expected_disagreement_record_digests: Sequence[str],
    expected_disagreement_chain_heads: Sequence[str],
    finalized_for_freeze: bool = True,
) -> dict[str, Any]:
    """Construct a canonical r4_b expectation mapping (constructor path)."""
    obj = {
        "schema_version": EXPECTATION_SCHEMA_VERSION,
        "enabled": True,
        "reconstructability_report": {
            "required": True,
            "path": REPORT_FILENAME,
            "digest": reconstructability_report_digest,
        },
        "expected_disagreement_record_digests": list(
            expected_disagreement_record_digests
        ),
        "expected_disagreement_chain_heads": list(expected_disagreement_chain_heads),
        "finalized_for_freeze": finalized_for_freeze,
    }
    # Validate via the same strict parser constructors must share.
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
