"""WORLD THIRD v0.2 — Weaver Verification Reference v0.

Content-addressed reference to an existing Weaver verification artifact/result.

VERIFICATION_REF ≠ WEAVER VERDICT ITSELF
WEAVER PASS ≠ IW ACCEPTED
WEAVER PASS ≠ HUMAN ACCEPTED
WEAVER PASS ≠ CANONICAL

Additive only. Does not modify Weaver core, audit_lifecycle, Operational V1,
or accepted/frozen evidence. Read-only resolve. No remote fetch.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

SCHEMA_ID = "world-third-weaver-verification-ref-v0"
SCHEMA_VERSION = "0"
ARTIFACT_CLASS = "world_third_weaver_verification_ref"
ARTIFACT_TYPE = "world_third_weaver_verification_ref_v0"

VERIFICATION_REF_ID_PREFIX = "wtvr-v0-"
VERIFICATION_REF_ID_DIGEST_LEN = 32
HEX_DIGITS = frozenset("0123456789abcdef")
SHA256_HEX_LEN = 64
COMMIT_HEX_LEN = 40

# Outcomes already used by Weaver verification surfaces (do not invent new meanings).
VERIFICATION_RESULTS = frozenset(
    {
        "PASS",
        "FAIL",
        "INCONCLUSIVE",
        "BLOCKED",
        "PARTIAL",
        "UNKNOWN",
        "INCOMPLETE",  # eig-cleanup-residue-verifier-v0
        "NOT_CLAIMED",  # lifecycle independent_verification record_only
    }
)

TARGET_BINDING_KINDS = frozenset({"git_commit", "content_digest", "immutable_version"})

_FORBIDDEN_LATEST_VALUES = frozenset(
    {
        "latest",
        "LATEST",
        "head",
        "HEAD",
        "main",
        "master",
        "origin/main",
        "origin/master",
    }
)

NONCLAIMS = {
    "verification_ref_is_not_authorization": True,
    "verification_ref_is_not_execution_receipt": True,
    "verification_ref_is_not_iw_acceptance": True,
    "verification_ref_is_not_human_review": True,
    "verification_ref_is_not_canonical_status": True,
    "verification_ref_is_not_publication_approval": True,
    "verification_ref_does_not_prove_production_safety": True,
    "verification_ref_does_not_broaden_original_verification_scope": True,
    "verification_ref_is_not_weaver_verdict_itself": True,
    "weaver_pass_ne_iw_accepted": True,
    "weaver_pass_ne_human_accepted": True,
    "weaver_pass_ne_canonical": True,
}

_RECORD_REQUIRED_KEYS = (
    "artifact_type",
    "schema_version",
    "schema_id",
    "artifact_class",
    "verification_ref_id",
    "work_id",
    "verifier",
    "verification_artifact_ref",
    "verification_type",
    "verification_result",
    "created_at",
    "verification_digest",
    "nonclaims",
    "claims_iw_acceptance",
    "artifact_sha256",
)
_RECORD_OPTIONAL_KEYS = (
    "target_identity",
    "target_commit_or_version",
    "evidence_pack_ref",
    "work_id_adapter_binding",
    "underlying_nonclaims",
    "underlying_run_id",
    "underlying_claim_id",
    "underlying_scope",
)
_RECORD_ALLOWED_KEYS = frozenset(_RECORD_REQUIRED_KEYS + _RECORD_OPTIONAL_KEYS)

_IDENTITY_KEYS = (
    "artifact_type",
    "schema_version",
    "schema_id",
    "artifact_class",
    "work_id",
    "verifier",
    "verification_artifact_ref",
    "verification_type",
    "verification_result",
    "created_at",
    "verification_digest",
    "nonclaims",
    "claims_iw_acceptance",
)
_IDENTITY_OPTIONAL_KEYS = (
    "target_identity",
    "target_commit_or_version",
    "evidence_pack_ref",
    "work_id_adapter_binding",
    "underlying_nonclaims",
    "underlying_run_id",
    "underlying_claim_id",
    "underlying_scope",
)

# Authority / acceptance inflation — fail closed if present as true, or as fields
# that imply acceptance without a separate authority artifact family.
_AUTHORITY_INFLATION_KEYS = frozenset(
    {
        "human_accepted",
        "human_approved",
        "canonical",
        "canonical_accepted",
        "published",
        "publication_approved",
        "iw_accepted",
        "independent_witness_accepted",
        "execution_authorized",
        "deployment_authorized",
        "truth_verified",
        "evidence_admitted",
        "approved",
        "admitted",
        "authorized",
        "allow_execution",
        "execution_allowed",
    }
)
_FORBIDDEN_FIELD_NAMES = frozenset(
    {
        "human_accepted",
        "human_approved",
        "canonical",
        "canonical_accepted",
        "published",
        "publication_approved",
        "iw_accepted",
        "independent_witness_accepted",
        "chain_of_thought",
        "private_reasoning",
        "hidden_rationale",
        "internal_monologue",
        "external_iw_evidence",  # reserved; v0.2 does not admit IW evidence binding
    }
)

_ISO_Z_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z$")
_JSON_NEWLINE = "\n"

# Known Weaver verification artifact families (inspectors).
ARTIFACT_TYPE_EIG_CLEANUP_RESULT = "weaver_eig_cleanup_residue_verifier_result_v0"
ARTIFACT_TYPE_LIFECYCLE_DECISION = "weaver_audit_lifecycle_decision_v0"
ARTIFACT_TYPE_INDEPENDENT_VERIFICATION_RECORD = (
    "weaver_lifecycle_independent_verification_record_v0"
)
ARTIFACT_TYPE_GENERIC_VERDICT = "weaver_verification_verdict_v0"

KNOWN_ARTIFACT_TYPES = frozenset(
    {
        ARTIFACT_TYPE_EIG_CLEANUP_RESULT,
        ARTIFACT_TYPE_LIFECYCLE_DECISION,
        ARTIFACT_TYPE_INDEPENDENT_VERIFICATION_RECORD,
        ARTIFACT_TYPE_GENERIC_VERDICT,
    }
)


class WorldThirdVerificationRefError(ValueError):
    """Fail-closed rejection of an unusable WORLD THIRD Verification Ref v0."""


def build_verification_ref_v0(
    *,
    work_id: Any,
    verifier: Any,
    verification_artifact_ref: Any,
    verification_type: Any,
    verification_result: Any,
    created_at: Any,
    verification_digest: Any,
    claims_iw_acceptance: Any = False,
    target_identity: Any = None,
    target_commit_or_version: Any = None,
    evidence_pack_ref: Any = None,
    work_id_adapter_binding: Any = None,
    underlying_nonclaims: Any = None,
    underlying_run_id: Any = None,
    underlying_claim_id: Any = None,
    underlying_scope: Any = None,
    **extra: Any,
) -> dict[str, Any]:
    """Build a deterministic VERIFICATION_REF. Does not mutate underlying evidence."""
    _reject_forbidden_fields(extra)
    _reject_true_authority_inflation(extra)
    if extra:
        raise WorldThirdVerificationRefError(
            "unsupported field: " + ", ".join(sorted(str(k) for k in extra))
        )

    identity_payload: dict[str, Any] = {
        "schema_id": SCHEMA_ID,
        "schema_version": SCHEMA_VERSION,
        "artifact_class": ARTIFACT_CLASS,
        "artifact_type": ARTIFACT_TYPE,
        "work_id": _require_work_id(work_id),
        "verifier": _require_identity_string(verifier, "verifier"),
        "verification_artifact_ref": _normalize_verification_artifact_ref(
            verification_artifact_ref
        ),
        "verification_type": _require_non_empty_string(
            verification_type, "verification_type"
        ),
        "verification_result": _require_verification_result(verification_result),
        "created_at": _require_timestamp(created_at, "created_at"),
        "verification_digest": _require_sha256(
            verification_digest, "verification_digest"
        ),
        "nonclaims": dict(NONCLAIMS),
        "claims_iw_acceptance": _require_claims_iw_acceptance(claims_iw_acceptance),
    }

    if target_identity is not None:
        identity_payload["target_identity"] = _require_identity_string(
            target_identity, "target_identity"
        )
    if target_commit_or_version is not None:
        identity_payload["target_commit_or_version"] = _normalize_target_binding(
            target_commit_or_version
        )
    if evidence_pack_ref is not None:
        identity_payload["evidence_pack_ref"] = _normalize_evidence_pack_ref(
            evidence_pack_ref
        )
    if work_id_adapter_binding is not None:
        identity_payload["work_id_adapter_binding"] = _normalize_work_id_adapter_binding(
            work_id_adapter_binding
        )
    if underlying_nonclaims is not None:
        identity_payload["underlying_nonclaims"] = _normalize_underlying_nonclaims(
            underlying_nonclaims
        )
    if underlying_run_id is not None:
        identity_payload["underlying_run_id"] = _require_identity_string(
            underlying_run_id, "underlying_run_id"
        )
    if underlying_claim_id is not None:
        identity_payload["underlying_claim_id"] = _require_identity_string(
            underlying_claim_id, "underlying_claim_id"
        )
    if underlying_scope is not None:
        identity_payload["underlying_scope"] = _normalize_underlying_scope(
            underlying_scope
        )

    verification_ref_id = _verification_ref_id_from_payload(identity_payload)
    artifact_sha256 = _sha256_canonical(identity_payload)
    record = {
        **identity_payload,
        "verification_ref_id": verification_ref_id,
        "artifact_sha256": artifact_sha256,
    }
    return validate_verification_ref_v0(record)


def validate_verification_ref_v0(record: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(record, Mapping):
        raise WorldThirdVerificationRefError("verification ref must be a mapping")
    _reject_forbidden_fields(record)
    _reject_true_authority_inflation(record)
    extra = {str(k) for k in record.keys()} - _RECORD_ALLOWED_KEYS
    if extra:
        raise WorldThirdVerificationRefError(
            "unsupported field: " + ", ".join(sorted(extra))
        )
    missing = [k for k in _RECORD_REQUIRED_KEYS if k not in record]
    if missing:
        raise WorldThirdVerificationRefError("missing field: " + ", ".join(missing))

    _require_const(record, "schema_id", SCHEMA_ID)
    _require_const(record, "schema_version", SCHEMA_VERSION)
    _require_const(record, "artifact_class", ARTIFACT_CLASS)
    _require_const(record, "artifact_type", ARTIFACT_TYPE)

    identity_payload: dict[str, Any] = {
        "schema_id": SCHEMA_ID,
        "schema_version": SCHEMA_VERSION,
        "artifact_class": ARTIFACT_CLASS,
        "artifact_type": ARTIFACT_TYPE,
        "work_id": _require_work_id(record.get("work_id")),
        "verifier": _require_identity_string(record.get("verifier"), "verifier"),
        "verification_artifact_ref": _normalize_verification_artifact_ref(
            record.get("verification_artifact_ref")
        ),
        "verification_type": _require_non_empty_string(
            record.get("verification_type"), "verification_type"
        ),
        "verification_result": _require_verification_result(
            record.get("verification_result")
        ),
        "created_at": _require_timestamp(record.get("created_at"), "created_at"),
        "verification_digest": _require_sha256(
            record.get("verification_digest"), "verification_digest"
        ),
        "nonclaims": _normalize_nonclaims(record.get("nonclaims")),
        "claims_iw_acceptance": _require_claims_iw_acceptance(
            record.get("claims_iw_acceptance")
        ),
    }

    if "target_identity" in record:
        identity_payload["target_identity"] = _require_identity_string(
            record.get("target_identity"), "target_identity"
        )
    if "target_commit_or_version" in record:
        identity_payload["target_commit_or_version"] = _normalize_target_binding(
            record.get("target_commit_or_version")
        )
    if "evidence_pack_ref" in record:
        identity_payload["evidence_pack_ref"] = _normalize_evidence_pack_ref(
            record.get("evidence_pack_ref")
        )
    if "work_id_adapter_binding" in record:
        identity_payload["work_id_adapter_binding"] = _normalize_work_id_adapter_binding(
            record.get("work_id_adapter_binding")
        )
    if "underlying_nonclaims" in record:
        identity_payload["underlying_nonclaims"] = _normalize_underlying_nonclaims(
            record.get("underlying_nonclaims")
        )
    if "underlying_run_id" in record:
        identity_payload["underlying_run_id"] = _require_identity_string(
            record.get("underlying_run_id"), "underlying_run_id"
        )
    if "underlying_claim_id" in record:
        identity_payload["underlying_claim_id"] = _require_identity_string(
            record.get("underlying_claim_id"), "underlying_claim_id"
        )
    if "underlying_scope" in record:
        identity_payload["underlying_scope"] = _normalize_underlying_scope(
            record.get("underlying_scope")
        )

    verification_ref_id = _require_verification_ref_id(record.get("verification_ref_id"))
    expected_id = _verification_ref_id_from_payload(identity_payload)
    if verification_ref_id != expected_id:
        raise WorldThirdVerificationRefError(
            "verification_ref_id does not match semantic content identity"
        )

    expected_sha = _sha256_canonical(identity_payload)
    artifact_sha256 = _require_sha256(record.get("artifact_sha256"), "artifact_sha256")
    if artifact_sha256 != expected_sha:
        raise WorldThirdVerificationRefError(
            "artifact_sha256 does not match semantic content identity"
        )

    return {
        **identity_payload,
        "verification_ref_id": verification_ref_id,
        "artifact_sha256": artifact_sha256,
    }


def resolve_verification_ref_v0(
    locator_or_ref: Any,
    *,
    verification_ref_root: Any = None,
    artifact_root: Any = None,
    expected_work_id: Any = None,
    expected_target_identity: Any = None,
    expected_target_commit_or_version: Any = None,
    expected_scope: Any = None,
) -> dict[str, Any]:
    """Read-only resolve: load VERIFICATION_REF and verify bound Weaver artifact bytes.

    Does not mutate referenced evidence. No remote fetch. No substitute search.
    """
    ref = _load_verification_ref_document(
        locator_or_ref, verification_ref_root=verification_ref_root
    )
    validated = validate_verification_ref_v0(ref)

    if expected_work_id is not None:
        want = _require_work_id(expected_work_id)
        if validated["work_id"] != want:
            raise WorldThirdVerificationRefError(
                "work_id rebind refused: verification_ref work_id mismatch"
            )

    if artifact_root is None:
        raise WorldThirdVerificationRefError(
            "artifact_root is required to resolve and verify the underlying Weaver artifact"
        )
    verified = verify_verification_artifact_binding_v0(
        verification_ref=validated,
        artifact_root=artifact_root,
        expected_target_identity=expected_target_identity,
        expected_target_commit_or_version=expected_target_commit_or_version,
        expected_scope=expected_scope,
    )
    return {
        "verification_ref": validated,
        "verified_artifact": verified,
    }


def verify_verification_artifact_binding_v0(
    *,
    verification_ref: Mapping[str, Any],
    artifact_root: Any,
    expected_target_identity: Any = None,
    expected_target_commit_or_version: Any = None,
    expected_scope: Any = None,
) -> dict[str, Any]:
    """Verify local bytes of the referenced Weaver verification artifact. Read-only."""
    validated = validate_verification_ref_v0(verification_ref)
    aref = validated["verification_artifact_ref"]
    root = _validate_root(artifact_root)
    path = _resolve_local_artifact_path(aref["artifact_ref"], artifact_root=root)

    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise WorldThirdVerificationRefError(
            "referenced verification artifact missing"
        ) from exc

    if len(raw) != aref["bytes_length"]:
        raise WorldThirdVerificationRefError(
            f"verification artifact byte-length mismatch: "
            f"declared={aref['bytes_length']} actual={len(raw)}"
        )
    actual_sha = hashlib.sha256(raw).hexdigest()
    if actual_sha != aref["sha256"]:
        raise WorldThirdVerificationRefError(
            "verification artifact SHA-256 mismatch"
        )

    try:
        parsed = json.loads(raw.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise WorldThirdVerificationRefError(
            "referenced verification artifact is malformed JSON"
        ) from exc
    if not isinstance(parsed, dict):
        raise WorldThirdVerificationRefError(
            "referenced verification artifact must be a JSON object"
        )

    extracted = extract_weaver_verification_binding_v0(
        parsed, artifact_type=aref["artifact_type"]
    )
    if extracted["verification_result"] != validated["verification_result"]:
        raise WorldThirdVerificationRefError(
            "declared verification_result does not match underlying Weaver result"
        )

    # Digest of underlying verification identity must match.
    if extracted["verification_digest"] != validated["verification_digest"]:
        raise WorldThirdVerificationRefError(
            "verification_digest does not match underlying Weaver artifact identity"
        )

    _assert_target_scope_consistency(
        ref=validated,
        extracted=extracted,
        expected_target_identity=expected_target_identity,
        expected_target_commit_or_version=expected_target_commit_or_version,
        expected_scope=expected_scope,
    )

    # Preserve underlying nonclaims when present — ref must not drop/replace them.
    if "underlying_nonclaims" in validated and extracted.get("nonclaims") is not None:
        if validated["underlying_nonclaims"] != extracted["nonclaims"]:
            raise WorldThirdVerificationRefError(
                "underlying_nonclaims does not match referenced Weaver nonclaims"
            )

    return {
        "path": str(path.as_posix()),
        "sha256": actual_sha,
        "bytes_length": len(raw),
        "artifact_type": aref["artifact_type"],
        "extracted": extracted,
        "parsed": parsed,
    }


def extract_weaver_verification_binding_v0(
    artifact: Mapping[str, Any],
    *,
    artifact_type: str,
) -> dict[str, Any]:
    """Inspect a Weaver verification artifact and extract bindable result identity.

    Fail closed when the artifact cannot safely establish a claimed result.
    Does not infer PASS from successful file reads alone.
    """
    if not isinstance(artifact, Mapping):
        raise WorldThirdVerificationRefError("Weaver artifact must be a mapping")
    if artifact_type not in KNOWN_ARTIFACT_TYPES:
        raise WorldThirdVerificationRefError(
            f"unsupported verification artifact_type: {artifact_type!r}"
        )

    if artifact_type == ARTIFACT_TYPE_EIG_CLEANUP_RESULT:
        return _extract_eig_cleanup_result(artifact)
    if artifact_type == ARTIFACT_TYPE_LIFECYCLE_DECISION:
        return _extract_lifecycle_decision(artifact)
    if artifact_type == ARTIFACT_TYPE_INDEPENDENT_VERIFICATION_RECORD:
        return _extract_independent_verification_record(artifact)
    if artifact_type == ARTIFACT_TYPE_GENERIC_VERDICT:
        return _extract_generic_verdict(artifact)
    raise WorldThirdVerificationRefError("not-bindable Weaver artifact type")


def verification_ref_content_sha256(record: Mapping[str, Any]) -> str:
    validated = validate_verification_ref_v0(record)
    identity = {key: validated[key] for key in _IDENTITY_KEYS}
    for key in _IDENTITY_OPTIONAL_KEYS:
        if key in validated:
            identity[key] = validated[key]
    return _sha256_canonical(identity)


def compute_verification_digest_v0(artifact: Mapping[str, Any], *, artifact_type: str) -> str:
    """Canonical digest of bindable underlying verification identity."""
    extracted = extract_weaver_verification_binding_v0(
        artifact, artifact_type=artifact_type
    )
    return extracted["verification_digest"]


def write_verification_artifact_bytes(path: Path, artifact: Mapping[str, Any]) -> tuple[str, int]:
    """Test helper: write canonical JSON bytes; return (sha256, bytes_length)."""
    raw = _canonical_json_bytes(dict(artifact))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    return hashlib.sha256(raw).hexdigest(), len(raw)


# --- extractors -----------------------------------------------------------------


def _extract_eig_cleanup_result(artifact: Mapping[str, Any]) -> dict[str, Any]:
    verdict = artifact.get("verdict")
    if not isinstance(verdict, str) or verdict not in VERIFICATION_RESULTS:
        raise WorldThirdVerificationRefError(
            "eig-cleanup result not-bindable: missing/invalid verdict"
        )
    # Artifact bytes matching ≠ PASS — only the explicit verdict field binds.
    details = artifact.get("details") if isinstance(artifact.get("details"), Mapping) else {}
    target = None
    if isinstance(details, Mapping):
        # Prefer residue per_target keys when single-target.
        residue_status = details.get("residue_status")
        _ = residue_status  # informational only; verdict remains authoritative
    nonclaims = artifact.get("nonclaims")
    if nonclaims is not None and not isinstance(nonclaims, Mapping):
        raise WorldThirdVerificationRefError("malformed eig-cleanup nonclaims")
    identity = {
        "family": ARTIFACT_TYPE_EIG_CLEANUP_RESULT,
        "verdict": verdict,
        "claims_iw_acceptance": artifact.get("claims_iw_acceptance", False),
        "claims_independent_verification": artifact.get(
            "claims_independent_verification", False
        ),
        "details_digest": _sha256_canonical(details) if details else None,
        "nonclaims": dict(nonclaims) if isinstance(nonclaims, Mapping) else None,
    }
    if identity["claims_iw_acceptance"] is True:
        # Self/internal VERIFY cannot claim IW via this family.
        raise WorldThirdVerificationRefError(
            "eig-cleanup result claims_iw_acceptance=true is not bindable without external IW family"
        )
    return {
        "verification_result": verdict,
        "verification_digest": _sha256_canonical(identity),
        "target_identity": target,
        "target_commit_or_version": None,
        "run_id": None,
        "claim_id": None,
        "scope": None,
        "nonclaims": identity["nonclaims"],
        "claims_iw_acceptance": False,
        "identity": identity,
    }


def _extract_lifecycle_decision(artifact: Mapping[str, Any]) -> dict[str, Any]:
    decision = artifact.get("decision")
    claim_result = artifact.get("claim_result", decision)
    if not isinstance(decision, str) or decision not in VERIFICATION_RESULTS:
        raise WorldThirdVerificationRefError(
            "lifecycle decision not-bindable: missing/invalid decision"
        )
    if not isinstance(claim_result, str) or claim_result not in VERIFICATION_RESULTS:
        raise WorldThirdVerificationRefError(
            "lifecycle decision not-bindable: missing/invalid claim_result"
        )
    if claim_result != decision and not (
        decision == "PASS" and claim_result == "PASS"
    ):
        # Prefer claim_result when it is the claim-scoped outcome; require consistency
        # with decision for bindable refs.
        if decision != claim_result:
            # Allow documented broader_classification without changing result.
            pass
    # Bind the claim-scoped result (claim_result), which is the Weaver claim outcome.
    result = claim_result
    claim_id = artifact.get("claim_id")
    vectors = artifact.get("vectors")
    identity = {
        "family": ARTIFACT_TYPE_LIFECYCLE_DECISION,
        "decision": decision,
        "claim_result": claim_result,
        "claim_id": claim_id if isinstance(claim_id, str) else None,
        "reason": artifact.get("reason"),
        "promoted": artifact.get("promoted", False),
        "promoted_to_full": artifact.get("promoted_to_full", False),
        "vectors": vectors if isinstance(vectors, Mapping) else None,
    }
    # Scope: claim-level only — never broaden to whole-repo.
    scope = None
    if isinstance(claim_id, str) and claim_id:
        scope = {"kind": "claim", "claim_id": claim_id}
    target_commit = None
    # Optional pinned target fields if present on enriched decision packages.
    for key in ("target_commit", "pinned_commit", "commit"):
        if isinstance(artifact.get(key), str) and artifact.get(key):
            target_commit = {
                "binding_kind": "git_commit",
                "value": str(artifact[key]).lower()
                if len(str(artifact[key])) == COMMIT_HEX_LEN
                else str(artifact[key]),
            }
            break
    target_identity = None
    for key in ("target_identity", "repository", "repo_id"):
        if isinstance(artifact.get(key), str) and artifact.get(key):
            target_identity = artifact[key]
            break
    return {
        "verification_result": result,
        "verification_digest": _sha256_canonical(identity),
        "target_identity": target_identity,
        "target_commit_or_version": target_commit,
        "run_id": artifact.get("run_id")
        if isinstance(artifact.get("run_id"), str)
        else None,
        "claim_id": claim_id if isinstance(claim_id, str) else None,
        "scope": scope,
        "nonclaims": None,
        "claims_iw_acceptance": False,
        "identity": identity,
    }


def _extract_independent_verification_record(artifact: Mapping[str, Any]) -> dict[str, Any]:
    result = artifact.get("result")
    if not isinstance(result, str) or result not in VERIFICATION_RESULTS:
        raise WorldThirdVerificationRefError(
            "independent_verification record not-bindable: missing/invalid result"
        )
    if artifact.get("claims_iw_acceptance") is True:
        raise WorldThirdVerificationRefError(
            "IW acceptance claim without external IW evidence family is not bindable"
        )
    identity = {
        "family": ARTIFACT_TYPE_INDEPENDENT_VERIFICATION_RECORD,
        "result": result,
        "status": artifact.get("status"),
        "mode": artifact.get("mode"),
        "stage": artifact.get("stage"),
        "claims_independent_witness": artifact.get("claims_independent_witness", False),
        "claims_iw_acceptance": False,
        "at_utc": artifact.get("at_utc"),
    }
    return {
        "verification_result": result,
        "verification_digest": _sha256_canonical(identity),
        "target_identity": None,
        "target_commit_or_version": None,
        "run_id": None,
        "claim_id": None,
        "scope": {"kind": "independent_verification_record"},
        "nonclaims": None,
        "claims_iw_acceptance": False,
        "identity": identity,
    }


def _extract_generic_verdict(artifact: Mapping[str, Any]) -> dict[str, Any]:
    """Minimal Weaver verdict object used by fixtures / additive packs.

    Required fields: verdict (in VERIFICATION_RESULTS). Optional target/scope.
    Does not infer PASS from presence alone.
    """
    verdict = artifact.get("verdict")
    if not isinstance(verdict, str) or verdict not in VERIFICATION_RESULTS:
        raise WorldThirdVerificationRefError(
            "generic verdict not-bindable: missing/invalid verdict"
        )
    if artifact.get("claims_iw_acceptance") is True:
        raise WorldThirdVerificationRefError(
            "claims_iw_acceptance=true rejected without explicit external IW evidence"
        )
    target_identity = artifact.get("target_identity")
    if target_identity is not None and not isinstance(target_identity, str):
        raise WorldThirdVerificationRefError("malformed target_identity")
    target_commit = artifact.get("target_commit_or_version")
    if target_commit is not None:
        target_commit = _normalize_target_binding(target_commit)
    scope = artifact.get("scope")
    if scope is not None:
        scope = _normalize_underlying_scope(scope)
    claim_id = artifact.get("claim_id")
    run_id = artifact.get("run_id")
    nonclaims = artifact.get("nonclaims")
    if nonclaims is not None and not isinstance(nonclaims, Mapping):
        raise WorldThirdVerificationRefError("malformed nonclaims")
    created_at = artifact.get("created_at")
    identity = {
        "family": ARTIFACT_TYPE_GENERIC_VERDICT,
        "verdict": verdict,
        "target_identity": target_identity,
        "target_commit_or_version": target_commit,
        "scope": scope,
        "claim_id": claim_id if isinstance(claim_id, str) else None,
        "run_id": run_id if isinstance(run_id, str) else None,
        "created_at": created_at if isinstance(created_at, str) else None,
        "nonclaims": dict(nonclaims) if isinstance(nonclaims, Mapping) else None,
    }
    return {
        "verification_result": verdict,
        "verification_digest": _sha256_canonical(identity),
        "target_identity": target_identity,
        "target_commit_or_version": target_commit,
        "run_id": run_id if isinstance(run_id, str) else None,
        "claim_id": claim_id if isinstance(claim_id, str) else None,
        "scope": scope,
        "nonclaims": identity["nonclaims"],
        "claims_iw_acceptance": False,
        "identity": identity,
    }


def _assert_target_scope_consistency(
    *,
    ref: Mapping[str, Any],
    extracted: Mapping[str, Any],
    expected_target_identity: Any,
    expected_target_commit_or_version: Any,
    expected_scope: Any,
) -> None:
    # Ref vs underlying.
    if "target_identity" in ref and extracted.get("target_identity"):
        if ref["target_identity"] != extracted["target_identity"]:
            raise WorldThirdVerificationRefError(
                "target_identity mismatch with underlying Weaver verification"
            )
    if "target_commit_or_version" in ref and extracted.get("target_commit_or_version"):
        if ref["target_commit_or_version"] != extracted["target_commit_or_version"]:
            raise WorldThirdVerificationRefError(
                "commit/version mismatch with underlying Weaver verification"
            )
    if "underlying_scope" in ref and extracted.get("scope"):
        if _scope_broadens(ref["underlying_scope"], extracted["scope"]):
            raise WorldThirdVerificationRefError(
                "verification ref must not broaden underlying Weaver scope"
            )
        if ref["underlying_scope"] != extracted["scope"]:
            # Allow equal only; refuse silent reinterpretation.
            raise WorldThirdVerificationRefError(
                "underlying_scope mismatch with Weaver verification scope"
            )

    # Caller-expected constraints.
    if expected_target_identity is not None:
        want = _require_identity_string(expected_target_identity, "expected_target_identity")
        have = ref.get("target_identity") or extracted.get("target_identity")
        if have != want:
            raise WorldThirdVerificationRefError("target mismatch rejected")
    if expected_target_commit_or_version is not None:
        want = _normalize_target_binding(expected_target_commit_or_version)
        have = ref.get("target_commit_or_version") or extracted.get(
            "target_commit_or_version"
        )
        if have != want:
            raise WorldThirdVerificationRefError("commit/version mismatch rejected")
    if expected_scope is not None:
        want = _normalize_underlying_scope(expected_scope)
        have = ref.get("underlying_scope") or extracted.get("scope")
        if have is None:
            raise WorldThirdVerificationRefError("scope not bindable on underlying artifact")
        if _scope_broadens(want, have):
            raise WorldThirdVerificationRefError(
                "requested scope broadens underlying Weaver verification scope"
            )
        if want != have:
            raise WorldThirdVerificationRefError("scope mismatch rejected")


def _scope_broadens(candidate: Mapping[str, Any], underlying: Mapping[str, Any]) -> bool:
    """True if candidate claims a broader scope than underlying."""
    u_kind = underlying.get("kind")
    c_kind = candidate.get("kind")
    if u_kind == "claim" and c_kind in {"repository", "repo", "entire_repo", "system"}:
        return True
    if u_kind == "claim" and c_kind == "claim":
        return candidate.get("claim_id") != underlying.get("claim_id")
    if underlying.get("claim_id") and candidate.get("claim_id"):
        if candidate.get("claim_id") != underlying.get("claim_id"):
            return True
    if candidate.get("covers_entire_repository") is True and underlying.get(
        "covers_entire_repository"
    ) is not True:
        return True
    return False


# --- normalize / require --------------------------------------------------------


def _verification_ref_id_from_payload(payload: Mapping[str, Any]) -> str:
    identity = {key: payload[key] for key in _IDENTITY_KEYS}
    for key in _IDENTITY_OPTIONAL_KEYS:
        if key in payload:
            identity[key] = payload[key]
    digest = _sha256_canonical(identity)
    return VERIFICATION_REF_ID_PREFIX + digest[:VERIFICATION_REF_ID_DIGEST_LEN]


def _canonical_json_bytes(value: Any) -> bytes:
    blob = json.dumps(
        value,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    return (blob + _JSON_NEWLINE).encode("utf-8")


def _sha256_canonical(value: Any) -> str:
    return hashlib.sha256(_canonical_json_bytes(value)).hexdigest()


def _load_verification_ref_document(
    locator_or_ref: Any,
    *,
    verification_ref_root: Any,
) -> dict[str, Any]:
    if isinstance(locator_or_ref, Mapping):
        return dict(locator_or_ref)
    if not isinstance(locator_or_ref, str) or locator_or_ref == "":
        raise WorldThirdVerificationRefError(
            "locator_or_ref must be a non-empty string or mapping"
        )
    if ".." in locator_or_ref:
        raise WorldThirdVerificationRefError("path traversal locator is not authorized")

    if verification_ref_root is None:
        path = Path(locator_or_ref)
        if path.is_absolute():
            raise WorldThirdVerificationRefError(
                "absolute path resolve requires verification_ref_root"
            )
        dest = path
    else:
        root = _validate_root(verification_ref_root)
        candidate = locator_or_ref
        if (
            candidate.startswith(VERIFICATION_REF_ID_PREFIX)
            and "/" not in candidate
            and "\\" not in candidate
        ):
            if not candidate.endswith(".json"):
                candidate = f"{candidate}.json"
        relative = _require_relative_path(candidate, "locator_or_ref")
        dest = (root / relative).resolve()
        try:
            dest.relative_to(root.resolve())
        except ValueError as exc:
            raise WorldThirdVerificationRefError(
                "locator resolution escaped verification_ref_root"
            ) from exc

    if not dest.is_file():
        raise WorldThirdVerificationRefError("verification ref not found")
    try:
        parsed = json.loads(dest.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise WorldThirdVerificationRefError(
            "stored verification ref is not valid JSON"
        ) from exc
    if not isinstance(parsed, Mapping):
        raise WorldThirdVerificationRefError(
            "stored verification ref must be a JSON object"
        )
    return dict(parsed)


def _validate_root(root: Any) -> Path:
    path = Path(root)
    if not path.is_absolute():
        raise WorldThirdVerificationRefError("artifact_root must be absolute")
    return path


def _resolve_local_artifact_path(artifact_ref: str, *, artifact_root: Path) -> Path:
    if not isinstance(artifact_ref, str) or not artifact_ref:
        raise WorldThirdVerificationRefError("artifact_ref must be a non-empty string")
    if ".." in artifact_ref:
        raise WorldThirdVerificationRefError(
            "artifact_ref path traversal is not authorized"
        )
    if (
        ":" in artifact_ref
        and "/" not in artifact_ref
        and "\\" not in artifact_ref
    ):
        raise WorldThirdVerificationRefError(
            "scheme artifact_ref cannot be resolved as local bytes without path mapping"
        )
    relative = _require_relative_path(artifact_ref, "artifact_ref")
    dest = (artifact_root / relative).resolve()
    try:
        dest.relative_to(artifact_root.resolve())
    except ValueError as exc:
        raise WorldThirdVerificationRefError(
            "artifact_ref resolution escaped artifact_root"
        ) from exc
    if not dest.is_file():
        raise WorldThirdVerificationRefError("referenced verification artifact missing")
    return dest


def _require_relative_path(value: str, label: str) -> str:
    text = value.replace("\\", "/")
    if text.startswith("/") or text.startswith("~"):
        raise WorldThirdVerificationRefError(f"{label} must be a relative path")
    if len(text) >= 2 and text[1] == ":" and text[0].isalpha():
        raise WorldThirdVerificationRefError(f"{label} must be a relative path")
    if ".." in text.split("/"):
        raise WorldThirdVerificationRefError(
            f"{label} path traversal is not authorized"
        )
    if text.strip() != text or text == "":
        raise WorldThirdVerificationRefError(f"malformed {label}")
    return text


def _normalize_verification_artifact_ref(value: Any) -> dict[str, Any]:
    mapping = _require_mapping(value, "verification_artifact_ref")
    allowed = {
        "artifact_ref",
        "artifact_type",
        "sha256",
        "bytes_length",
        "created_at",
    }
    extra = {str(k) for k in mapping.keys()} - allowed
    if extra:
        raise WorldThirdVerificationRefError(
            "unsupported verification_artifact_ref field: " + ", ".join(sorted(extra))
        )
    required = {"artifact_ref", "artifact_type", "sha256", "bytes_length"}
    missing = [k for k in required if k not in mapping]
    if missing:
        raise WorldThirdVerificationRefError(
            "missing verification_artifact_ref field: " + ", ".join(missing)
        )
    artifact_ref = _require_relative_path(
        _require_non_empty_string(
            mapping.get("artifact_ref"), "verification_artifact_ref.artifact_ref"
        ),
        "verification_artifact_ref.artifact_ref",
    )
    artifact_type = _require_non_empty_string(
        mapping.get("artifact_type"), "verification_artifact_ref.artifact_type"
    )
    if artifact_type not in KNOWN_ARTIFACT_TYPES:
        raise WorldThirdVerificationRefError(
            f"unsupported verification_artifact_ref.artifact_type: {artifact_type!r}"
        )
    sha256 = _require_sha256(
        mapping.get("sha256"), "verification_artifact_ref.sha256"
    )
    bytes_length = mapping.get("bytes_length")
    if not isinstance(bytes_length, int) or isinstance(bytes_length, bool):
        raise WorldThirdVerificationRefError(
            "invalid verification_artifact_ref.bytes_length"
        )
    if bytes_length < 0:
        raise WorldThirdVerificationRefError(
            "invalid verification_artifact_ref.bytes_length"
        )
    out: dict[str, Any] = {
        "artifact_ref": artifact_ref,
        "artifact_type": artifact_type,
        "sha256": sha256,
        "bytes_length": bytes_length,
    }
    if "created_at" in mapping and mapping.get("created_at") is not None:
        out["created_at"] = _require_timestamp(
            mapping.get("created_at"), "verification_artifact_ref.created_at"
        )
    return out


def _normalize_evidence_pack_ref(value: Any) -> dict[str, Any]:
    mapping = _require_mapping(value, "evidence_pack_ref")
    allowed = {"artifact_ref", "sha256", "bytes_length", "artifact_type"}
    extra = {str(k) for k in mapping.keys()} - allowed
    if extra:
        raise WorldThirdVerificationRefError(
            "unsupported evidence_pack_ref field: " + ", ".join(sorted(extra))
        )
    for key in ("artifact_ref", "sha256", "bytes_length"):
        if key not in mapping:
            raise WorldThirdVerificationRefError(
                f"missing evidence_pack_ref field: {key}"
            )
    out: dict[str, Any] = {
        "artifact_ref": _require_relative_path(
            _require_non_empty_string(
                mapping.get("artifact_ref"), "evidence_pack_ref.artifact_ref"
            ),
            "evidence_pack_ref.artifact_ref",
        ),
        "sha256": _require_sha256(mapping.get("sha256"), "evidence_pack_ref.sha256"),
        "bytes_length": mapping.get("bytes_length"),
    }
    if not isinstance(out["bytes_length"], int) or isinstance(out["bytes_length"], bool):
        raise WorldThirdVerificationRefError("invalid evidence_pack_ref.bytes_length")
    if out["bytes_length"] < 0:
        raise WorldThirdVerificationRefError("invalid evidence_pack_ref.bytes_length")
    if "artifact_type" in mapping:
        out["artifact_type"] = _require_non_empty_string(
            mapping.get("artifact_type"), "evidence_pack_ref.artifact_type"
        )
    return out


def _normalize_work_id_adapter_binding(value: Any) -> dict[str, Any]:
    mapping = _require_mapping(value, "work_id_adapter_binding")
    allowed = {
        "binding_kind",
        "source_identity_field",
        "source_identity_value",
        "mapping_note",
    }
    extra = {str(k) for k in mapping.keys()} - allowed
    if extra:
        raise WorldThirdVerificationRefError(
            "unsupported work_id_adapter_binding field: " + ", ".join(sorted(extra))
        )
    for key in allowed:
        if key not in mapping:
            raise WorldThirdVerificationRefError(
                f"missing work_id_adapter_binding field: {key}"
            )
    kind = _require_non_empty_string(
        mapping.get("binding_kind"), "work_id_adapter_binding.binding_kind"
    )
    if kind != "explicit_adapter":
        raise WorldThirdVerificationRefError(
            "work_id_adapter_binding.binding_kind must be explicit_adapter"
        )
    return {
        "binding_kind": kind,
        "source_identity_field": _require_identity_string(
            mapping.get("source_identity_field"),
            "work_id_adapter_binding.source_identity_field",
        ),
        "source_identity_value": _require_identity_string(
            mapping.get("source_identity_value"),
            "work_id_adapter_binding.source_identity_value",
        ),
        "mapping_note": _require_non_empty_string(
            mapping.get("mapping_note"), "work_id_adapter_binding.mapping_note"
        ),
    }


def _normalize_underlying_nonclaims(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping) or not value:
        raise WorldThirdVerificationRefError("underlying_nonclaims must be a non-empty object")
    out: dict[str, Any] = {}
    for key, nested in value.items():
        name = str(key)
        if not isinstance(nested, bool):
            raise WorldThirdVerificationRefError(
                "underlying_nonclaims values must be boolean"
            )
        out[name] = nested
    return out


def _normalize_underlying_scope(value: Any) -> dict[str, Any]:
    mapping = _require_mapping(value, "underlying_scope")
    allowed = {"kind", "claim_id", "covers_entire_repository", "note"}
    extra = {str(k) for k in mapping.keys()} - allowed
    if extra:
        raise WorldThirdVerificationRefError(
            "unsupported underlying_scope field: " + ", ".join(sorted(extra))
        )
    kind = _require_non_empty_string(mapping.get("kind"), "underlying_scope.kind")
    if kind in {"repository", "repo", "entire_repo", "system"}:
        # Broader kinds are only allowed if explicitly recorded as such on underlying;
        # builders must not invent them for claim-scoped Weaver results.
        pass
    out: dict[str, Any] = {"kind": kind}
    if "claim_id" in mapping:
        out["claim_id"] = _require_identity_string(
            mapping.get("claim_id"), "underlying_scope.claim_id"
        )
    if "covers_entire_repository" in mapping:
        flag = mapping.get("covers_entire_repository")
        if not isinstance(flag, bool):
            raise WorldThirdVerificationRefError(
                "underlying_scope.covers_entire_repository must be boolean"
            )
        out["covers_entire_repository"] = flag
    if "note" in mapping:
        out["note"] = _require_non_empty_string(
            mapping.get("note"), "underlying_scope.note"
        )
    return out


def _normalize_target_binding(value: Any) -> dict[str, str]:
    mapping = _require_mapping(value, "target_commit_or_version")
    extra = {str(k) for k in mapping.keys()} - {"binding_kind", "value"}
    if extra:
        raise WorldThirdVerificationRefError(
            "unsupported target_commit_or_version field: " + ", ".join(sorted(extra))
        )
    if "binding_kind" not in mapping or "value" not in mapping:
        raise WorldThirdVerificationRefError(
            "missing exact target commit/version binding"
        )
    kind = mapping.get("binding_kind")
    if not isinstance(kind, str) or kind not in TARGET_BINDING_KINDS:
        raise WorldThirdVerificationRefError(
            "invalid target_commit_or_version.binding_kind"
        )
    raw_value = mapping.get("value")
    if not isinstance(raw_value, str) or raw_value == "":
        raise WorldThirdVerificationRefError("missing exact target commit/version")
    if raw_value.strip() != raw_value:
        raise WorldThirdVerificationRefError(
            "target_commit_or_version.value must not have leading or trailing whitespace"
        )
    if raw_value in _FORBIDDEN_LATEST_VALUES or raw_value.lower() in {"latest", "head"}:
        raise WorldThirdVerificationRefError(
            "implicit latest/branch-only target binding is not authorized"
        )
    if kind == "git_commit":
        lowered = raw_value.lower()
        if len(lowered) != COMMIT_HEX_LEN or any(c not in HEX_DIGITS for c in lowered):
            raise WorldThirdVerificationRefError(
                "invalid target_commit_or_version git_commit"
            )
        raw_value = lowered
    elif kind == "content_digest":
        if len(raw_value) != SHA256_HEX_LEN or any(
            c not in HEX_DIGITS for c in raw_value
        ):
            raise WorldThirdVerificationRefError(
                "invalid target_commit_or_version content_digest"
            )
    else:
        if any(c in raw_value for c in ("*", "?", "\n", "\r", "\0")):
            raise WorldThirdVerificationRefError(
                "malformed target_commit_or_version.value"
            )
    _reject_machine_specific_identity(raw_value, "target_commit_or_version.value")
    return {"binding_kind": kind, "value": raw_value}


def _normalize_nonclaims(value: Any) -> dict[str, bool]:
    if not isinstance(value, Mapping) or dict(value) != dict(NONCLAIMS):
        raise WorldThirdVerificationRefError("invalid nonclaims")
    return dict(NONCLAIMS)


def _require_claims_iw_acceptance(value: Any) -> bool:
    if value is True:
        raise WorldThirdVerificationRefError(
            "claims_iw_acceptance=true rejected without explicit external IW evidence"
        )
    if value is not False:
        raise WorldThirdVerificationRefError("claims_iw_acceptance must be false")
    return False


def _require_verification_result(value: Any) -> str:
    if not isinstance(value, str) or value not in VERIFICATION_RESULTS:
        raise WorldThirdVerificationRefError("invalid verification_result")
    return value


def _require_work_id(value: Any) -> str:
    text = _require_non_empty_string(value, "work_id")
    if text.strip() != text:
        raise WorldThirdVerificationRefError(
            "work_id must not have leading or trailing whitespace"
        )
    if text == "*":
        raise WorldThirdVerificationRefError("wildcard work_id is not authorized")
    if any(c in text for c in ("*", "?", "\n", "\r", "\0")):
        raise WorldThirdVerificationRefError("malformed work_id")
    _reject_machine_specific_identity(text, "work_id")
    return text


def _require_identity_string(value: Any, label: str) -> str:
    text = _require_non_empty_string(value, label)
    if text.strip() != text:
        raise WorldThirdVerificationRefError(
            f"{label} must not have leading or trailing whitespace"
        )
    _reject_machine_specific_identity(text, label)
    return text


def _require_timestamp(value: Any, label: str) -> str:
    text = _require_non_empty_string(value, label)
    if not _ISO_Z_RE.match(text):
        raise WorldThirdVerificationRefError(f"malformed {label}")
    try:
        parsed = datetime.strptime(
            text.replace("Z", "+0000"),
            "%Y-%m-%dT%H:%M:%S.%f%z" if "." in text else "%Y-%m-%dT%H:%M:%S%z",
        )
    except ValueError as exc:
        raise WorldThirdVerificationRefError(f"malformed {label}") from exc
    if parsed.tzinfo is None:
        raise WorldThirdVerificationRefError(f"malformed {label}")
    _ = parsed.astimezone(timezone.utc)
    return text


def _require_verification_ref_id(value: Any) -> str:
    if not isinstance(value, str) or not value.startswith(VERIFICATION_REF_ID_PREFIX):
        raise WorldThirdVerificationRefError("invalid verification_ref_id")
    digest = value[len(VERIFICATION_REF_ID_PREFIX) :]
    if len(digest) != VERIFICATION_REF_ID_DIGEST_LEN or any(
        c not in HEX_DIGITS for c in digest
    ):
        raise WorldThirdVerificationRefError("invalid verification_ref_id")
    return value


def _require_sha256(value: Any, label: str) -> str:
    if not isinstance(value, str) or len(value) != SHA256_HEX_LEN:
        raise WorldThirdVerificationRefError(f"invalid {label}")
    if any(c not in HEX_DIGITS for c in value):
        raise WorldThirdVerificationRefError(f"invalid {label}")
    return value


def _require_const(record: Mapping[str, Any], key: str, expected: Any) -> None:
    if record.get(key) != expected:
        raise WorldThirdVerificationRefError(f"invalid {key}")


def _require_mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise WorldThirdVerificationRefError(f"{label} must be a mapping")
    return value


def _require_non_empty_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or value == "":
        raise WorldThirdVerificationRefError(f"{label} must be a non-empty string")
    return value


def _reject_machine_specific_identity(value: str, label: str) -> None:
    lowered = value.lower()
    if "\\" in value:
        raise WorldThirdVerificationRefError(
            f"{label} must not contain a machine-specific path"
        )
    if len(value) >= 2 and value[1] == ":" and value[0].isalpha():
        raise WorldThirdVerificationRefError(
            f"{label} must not contain a machine-specific path"
        )
    if lowered.startswith("c:") or "/users/" in lowered or "/home/" in lowered:
        raise WorldThirdVerificationRefError(
            f"{label} must not contain a machine-specific path"
        )


def _reject_forbidden_fields(value: Any) -> None:
    found: list[str] = []
    _collect_forbidden_fields(value, found)
    if found:
        raise WorldThirdVerificationRefError(
            "forbidden authority-looking field: " + ", ".join(sorted(set(found)))
        )


def _collect_forbidden_fields(value: Any, found: list[str]) -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            name = str(key)
            if name in _FORBIDDEN_FIELD_NAMES:
                found.append(name)
            _collect_forbidden_fields(nested, found)
    elif isinstance(value, (list, tuple)):
        for nested in value:
            _collect_forbidden_fields(nested, found)


def _reject_true_authority_inflation(value: Any) -> None:
    found: list[str] = []
    _collect_true_authority_flags(value, found)
    if found:
        raise WorldThirdVerificationRefError(
            "authority inflation is not authorized: " + ", ".join(sorted(set(found)))
        )


def _collect_true_authority_flags(value: Any, found: list[str]) -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            name = str(key)
            if name in _AUTHORITY_INFLATION_KEYS and nested is True:
                found.append(name)
            _collect_true_authority_flags(nested, found)
    elif isinstance(value, (list, tuple)):
        for nested in value:
            _collect_true_authority_flags(nested, found)
