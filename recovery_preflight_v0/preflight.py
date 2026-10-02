"""Derive a non-authoritative statement that recovery is not established.

The receipt copies structured source facts. It does not restore, roll back,
or treat a decision, a digest match, or a resume as recovery.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from audit_lifecycle.epistemic.authority import AuthorityViolation
from audit_lifecycle.epistemic.reconstructability import (
    ReconstructabilityError,
    strict_parse_report,
)
from audit_lifecycle.epistemic.serialize import canonical_digest

SCHEMA_VERSION = "recovery_preflight.v0"
_LEAF_TYPES = (str, bool, int, float)
_SHA256_WIDTH = 64

_CALLER_ASSERTION_KEYS = frozenset(
    {
        "recovered",
        "restored",
        "verified_restore",
        "rollback_complete",
        "rejected_terminals",
        "digest_observation",
        "classification",
        "revalidation_observation",
    }
)
_EMBEDDED_ASSERTION_KEYS = frozenset(
    {
        "recovered",
        "restored",
        "verified_restore",
        "rollback_complete",
        "digest_observation",
        "classification",
        "revalidation_observation",
    }
)
_RESUME_KEYS = frozenset(
    {
        "campaign_resume",
        "resume",
        "resume_result",
    }
)
_REVALIDATION_REQUIRED = frozenset(
    {
        "integrity_digest_matched",
        "rejected_terminals",
        "validated_reuse_claims",
    }
)
_REVALIDATION_OPTIONAL = frozenset(
    {
        "note",
        "prior_integrity_digest",
        "state_integrity",
    }
)
# revalidate_prior_claim_states records prior_state only for these
# evidence-backed terminals. Recovery-success tokens are not in that set.
_PRIOR_STATES = frozenset({"PASS", "FAIL"})
_INTEGRITY_ALGORITHM = "sha256"
_INTEGRITY_COVERS = ("claims", "evidence_register.entries")
_HEX = frozenset("0123456789abcdef")
_LIMITATIONS = (
    "restore execution",
    "verified restore",
    "rollback completion",
    "recovered state",
    "independent reproduction",
    "operational hardening",
    "Human Final",
    "Canonical / Published / Deployed state",
)


class RecoveryError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


def _fail(code: str, message: str) -> None:
    raise RecoveryError(code, message)


def _snapshot(value: Any, depth: int = 0) -> Any:
    """Copy caller values once into exact built-in containers and leaves."""
    if depth > 32:
        _fail("RECOVERY_SOURCE_INVALID", "input is nested too deeply")
    if value is None or type(value) in _LEAF_TYPES:
        return value
    if isinstance(value, Mapping):
        copied: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                _fail("RECOVERY_SOURCE_INVALID", "mapping key must be a string")
            if key in copied:
                _fail("RECOVERY_SOURCE_INVALID", "mapping repeats a key")
            copied[key] = _snapshot(item, depth + 1)
        return copied
    if type(value) is list or type(value) is tuple:
        return [_snapshot(item, depth + 1) for item in value]
    _fail("RECOVERY_SOURCE_INVALID", "input is not plain JSON data")


def _require_mapping(value: Any, label: str) -> Mapping[str, Any]:
    if isinstance(value, bool) or not isinstance(value, Mapping):
        _fail("RECOVERY_SOURCE_INVALID", f"{label} must be a mapping")
    return value


def _reject_forbidden(forbidden: Mapping[str, Any]) -> None:
    if not forbidden:
        return
    names = set(forbidden)
    if names & _CALLER_ASSERTION_KEYS:
        _fail("RECOVERY_ASSERTION_FORBIDDEN", "caller cannot assert recovery facts")
    if names & _RESUME_KEYS:
        _fail("RECOVERY_SCOPE_VIOLATION", "resume is not recovery evidence")
    _fail("RECOVERY_SOURCE_INVALID", "unexpected recovery input")


def _reject_embedded_assertions(record: Mapping[str, Any]) -> None:
    names = set(record)
    if names & _EMBEDDED_ASSERTION_KEYS:
        _fail("RECOVERY_ASSERTION_FORBIDDEN", "caller cannot assert recovery facts")
    if names & _RESUME_KEYS:
        _fail("RECOVERY_SCOPE_VIOLATION", "resume is not recovery evidence")


def _nonempty_str(value: Any, label: str, code: str) -> str:
    if type(value) is not str or not value.strip():
        _fail(code, f"{label} is missing")
    return value


def _bind_decision(decision: Mapping[str, Any], report: Any) -> dict[str, str]:
    if (
        report.reconstructable is not True
        or len(report.missing_inputs) != 0
        or len(report.unresolved_assumptions) != 0
    ):
        _fail("RECOVERY_BINDING_UNAVAILABLE", "decision citation is incomplete")
    stated = report.canonical_input_digests.get("DECISION.json")
    if type(stated) is not str or len(stated) != _SHA256_WIDTH:
        _fail("RECOVERY_BINDING_UNAVAILABLE", "decision digest is not bound")
    try:
        actual = canonical_digest(decision)
    except (TypeError, ValueError) as exc:
        if isinstance(exc, RecoveryError):
            raise
        _fail("RECOVERY_BINDING_UNAVAILABLE", "decision digest is not bound")
    if actual != stated:
        _fail("RECOVERY_BINDING_UNAVAILABLE", "decision does not match the cited digest")
    _reject_embedded_assertions(decision)
    claim_id = _nonempty_str(decision.get("claim_id"), "claim_id", "RECOVERY_SOURCE_INVALID")
    token = _nonempty_str(decision.get("decision"), "decision", "RECOVERY_SOURCE_INVALID")
    cited = {"claim_id": claim_id, "decision": token}
    if "claim_result" in decision:
        cited["claim_result"] = _nonempty_str(
            decision.get("claim_result"),
            "claim_result",
            "RECOVERY_SOURCE_INVALID",
        )
    return cited


def _sha256_hex(value: Any) -> str:
    if type(value) is not str or len(value) != _SHA256_WIDTH:
        _fail("RECOVERY_REVALIDATION_UNBOUND", "integrity digest is not bound")
    if any(char not in _HEX for char in value):
        _fail("RECOVERY_REVALIDATION_UNBOUND", "integrity digest is not bound")
    return value


def _claim_in_scope(value: str, claim_id: str, label: str) -> None:
    if value != claim_id:
        _fail("RECOVERY_REVALIDATION_UNBOUND", f"{label} is outside the cited claim")


def _copy_terminals(raw: Any, claim_id: str) -> list[dict[str, str]]:
    if type(raw) is not list:
        _fail("RECOVERY_SOURCE_INVALID", "rejected_terminals must be a list")
    copied: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in raw:
        if type(item) is not dict:
            _fail("RECOVERY_REVALIDATION_UNBOUND", "rejected terminal is not a record")
        allowed = {"claim_id", "prior_state", "reason"}
        if set(item) != allowed:
            _fail("RECOVERY_REVALIDATION_UNBOUND", "rejected terminal is not bound")
        terminal_claim = _nonempty_str(
            item.get("claim_id"),
            "rejected claim_id",
            "RECOVERY_REVALIDATION_UNBOUND",
        )
        _claim_in_scope(terminal_claim, claim_id, "rejected terminal")
        if terminal_claim in seen:
            _fail("RECOVERY_REVALIDATION_UNBOUND", "rejected terminal repeats a claim")
        seen.add(terminal_claim)
        prior_state = _nonempty_str(
            item.get("prior_state"),
            "prior_state",
            "RECOVERY_REVALIDATION_UNBOUND",
        )
        if prior_state not in _PRIOR_STATES:
            _fail("RECOVERY_REVALIDATION_UNBOUND", "prior_state is not a revalidated terminal")
        copied.append(
            {
                "claim_id": terminal_claim,
                "prior_state": prior_state,
                "reason": _nonempty_str(
                    item.get("reason"),
                    "rejection reason",
                    "RECOVERY_REVALIDATION_UNBOUND",
                ),
            }
        )
    return copied


def _copy_reuse(raw: Any, claim_id: str) -> list[str]:
    if type(raw) is not list:
        _fail("RECOVERY_SOURCE_INVALID", "validated_reuse_claims must be a list")
    copied: list[str] = []
    seen: set[str] = set()
    for item in raw:
        reuse_claim = _nonempty_str(
            item,
            "validated reuse claim",
            "RECOVERY_REVALIDATION_UNBOUND",
        )
        _claim_in_scope(reuse_claim, claim_id, "validated reuse claim")
        if reuse_claim in seen:
            _fail("RECOVERY_REVALIDATION_UNBOUND", "validated reuse repeats a claim")
        seen.add(reuse_claim)
        copied.append(reuse_claim)
    return copied


def _bind_digest_evidence(record: Mapping[str, Any], matched: Any) -> dict[str, Any] | None:
    """Emit a digest observation only from a bound subject and both digests."""
    has_prior = "prior_integrity_digest" in record
    has_state = "state_integrity" in record
    if not has_prior and not has_state:
        return None
    if has_prior is not has_state:
        _fail("RECOVERY_REVALIDATION_UNBOUND", "integrity digest evidence is incomplete")
    state = record.get("state_integrity")
    if type(state) is not dict or set(state) != {"algorithm", "covers", "digest"}:
        _fail("RECOVERY_REVALIDATION_UNBOUND", "integrity digest subject is not bound")
    if state.get("algorithm") != _INTEGRITY_ALGORITHM:
        _fail("RECOVERY_REVALIDATION_UNBOUND", "integrity digest subject is not bound")
    covers = state.get("covers")
    if type(covers) is not list or covers != list(_INTEGRITY_COVERS):
        _fail("RECOVERY_REVALIDATION_UNBOUND", "integrity digest subject is not bound")
    expected = _sha256_hex(record.get("prior_integrity_digest"))
    actual = _sha256_hex(state.get("digest"))
    recomputed = expected == actual
    if type(matched) is not bool or matched is not recomputed:
        _fail("RECOVERY_REVALIDATION_UNBOUND", "integrity digest match is not bound")
    return {
        "algorithm": _INTEGRITY_ALGORITHM,
        "covers": list(_INTEGRITY_COVERS),
        "prior_integrity_digest": expected,
        "digest": actual,
        "integrity_digest_matched": recomputed,
    }


def _bind_revalidation(record: Mapping[str, Any], claim_id: str) -> dict[str, Any]:
    _reject_embedded_assertions(record)
    unknown = set(record) - _REVALIDATION_REQUIRED - _REVALIDATION_OPTIONAL
    if unknown:
        _fail("RECOVERY_SOURCE_INVALID", "revalidation has an unsupported field")
    if not _REVALIDATION_REQUIRED <= set(record):
        _fail("RECOVERY_REVALIDATION_UNBOUND", "revalidation result is not structured")
    matched = record.get("integrity_digest_matched")
    if matched is not None and type(matched) is not bool:
        _fail("RECOVERY_SOURCE_INVALID", "integrity_digest_matched is not a boolean")
    digest_observation = _bind_digest_evidence(record, matched)
    terminals = _copy_terminals(record.get("rejected_terminals"), claim_id)
    reuse = _copy_reuse(record.get("validated_reuse_claims"), claim_id)
    if {item["claim_id"] for item in terminals} & set(reuse):
        _fail(
            "RECOVERY_REVALIDATION_UNBOUND",
            "a claim cannot be both rejected and reused",
        )
    note = None
    if "note" in record:
        note = record.get("note")
        if type(note) is not str:
            _fail("RECOVERY_SOURCE_INVALID", "revalidation note must be a string")
    return {
        "observation": {"validated_reuse_claims": reuse},
        "rejected_terminals": terminals,
        "digest_observation": digest_observation,
        "note": note,
    }


def build_recovery_preflight(
    decision: Mapping[str, Any],
    *,
    reconstructability: Mapping[str, Any],
    revalidation: Mapping[str, Any] | None = None,
    annotation: str | None = None,
    **forbidden: Any,
) -> dict[str, Any]:
    """Return a receipt whose classification is NOT_RECOVERED.

    ``annotation`` is stored as text. It does not bind revalidation or recovery.
    """
    _reject_forbidden(forbidden)
    if annotation is not None and type(annotation) is not str:
        _fail("RECOVERY_SOURCE_INVALID", "annotation must be a string")
    decision_map = _snapshot(_require_mapping(decision, "decision"))
    report_map = _snapshot(_require_mapping(reconstructability, "reconstructability"))
    revalidation_map = None
    if revalidation is not None:
        revalidation_map = _snapshot(_require_mapping(revalidation, "revalidation"))

    try:
        report = strict_parse_report(report_map)
    except (ReconstructabilityError, AuthorityViolation) as exc:
        _fail("RECOVERY_SOURCE_INVALID", str(exc))

    cited = _bind_decision(decision_map, report)
    receipt: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "authority": False,
        "recovered": False,
        "classification": "NOT_RECOVERED",
        "cited_decision": cited,
        "limitations": list(_LIMITATIONS),
    }
    notes: dict[str, Any] = {}
    if revalidation_map is not None:
        bound = _bind_revalidation(revalidation_map, cited["claim_id"])
        receipt["revalidation_observation"] = bound["observation"]
        receipt["rejected_terminals"] = bound["rejected_terminals"]
        if bound["digest_observation"] is not None:
            receipt["digest_observation"] = bound["digest_observation"]
        if bound["note"] is not None:
            notes["revalidation_note"] = bound["note"]
    if annotation is not None:
        notes["annotation"] = annotation
    if notes:
        notes["authority"] = False
        receipt["annotations"] = notes
    return receipt
