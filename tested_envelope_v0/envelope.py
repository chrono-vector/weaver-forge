"""Derive a bounded receipt from an existing audit decision.

The receipt copies source tokens. It does not decide, admit evidence,
or record authority history.
"""

from __future__ import annotations

import re
from typing import Any, Mapping

from audit_lifecycle.epistemic.reconstructability import (
    ReconstructabilityError,
    strict_parse_report,
)
from audit_lifecycle.epistemic.serialize import canonical_digest

SCHEMA_VERSION = "tested_envelope.v0"

_SHA256_RE = re.compile(r"\A[0-9a-f]{64}\Z")
_UNPINNED_REVISIONS = frozenset(
    {
        "head",
        "latest",
        "main",
        "master",
        "origin/main",
        "origin/master",
    }
)

# Vector ids already emitted by the accepted decision engine.
_VECTOR_FAMILIES = {
    "POSITIVE_DIGEST_MATCH": "digest_match",
    "NC1_WRONG_DIGEST_REJECTED": "wrong_digest_rejection",
    "T1_TAMPER_CHANGES_DIGEST": "tamper",
    "R1_REHASH_REPRODUCTION": "rehash",
    "BV1_PROTECTED_BOUNDARY_WRITE_DENIED": "boundary",
}

_NON_PASS = frozenset(
    {
        "INCONCLUSIVE",
        "BLOCKED",
        "FAIL",
        "UNKNOWN",
        "INCOMPLETE",
        "NOT_CLAIMED",
        "UNSUPPORTED",
        "MISSING_RESULT",
        "RUN_INCOMPLETE",
        "RUN_INVALID",
        "PARTIAL",
        "DETECTED",
        "SURVIVED",
    }
)

_EXCLUSIONS = (
    "global safety",
    "global content truth",
    "civic truth",
    "independent reproduction",
    "Human Final",
    "Canonical / Published / Deployed state",
)

_INCOMPLETE_REASONS = frozenset(
    {"INCOMPLETE_EVIDENCE", "MISSING_REQUIRED_VECTORS"}
)


class EnvelopeError(ValueError):
    """Closed failure while deriving a tested envelope."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


def _fail(code: str, message: str) -> None:
    raise EnvelopeError(code, message)


def _reject_forbidden(forbidden: Mapping[str, Any]) -> None:
    if not forbidden:
        return
    names = set(forbidden)
    if names & {"authority_before", "authority_after"}:
        _fail(
            "ENVELOPE_AUTHORITY_INVALID",
            "authority history is not present in the source",
        )
    if "independent_evidence_count" in names:
        _fail(
            "ENVELOPE_AUTHORITY_INVALID",
            "independent evidence count cannot be injected",
        )
    if "artifact_revision" in names:
        _fail(
            "ENVELOPE_REVISION_UNBOUND",
            "revision cannot be selected by the caller",
        )
    if "unresolved_assumptions" in names:
        _fail(
            "ENVELOPE_ASSUMPTION_DROPPED",
            "assumptions cannot be replaced by the caller",
        )
    if names & {"result", "broader_classification", "exclusions", "source_result"}:
        _fail("ENVELOPE_PROMOTION", "the caller cannot set the result")
    if "counterexample_count" in names:
        _fail(
            "ENVELOPE_SOURCE_INVALID",
            "counterexample_count cannot be supplied separately from the decision",
        )
    _fail("ENVELOPE_SOURCE_INVALID", "unexpected envelope input")


def _require_mapping(value: Any, label: str) -> Mapping[str, Any]:
    if isinstance(value, bool) or not isinstance(value, Mapping):
        _fail("ENVELOPE_SOURCE_INVALID", f"{label} must be a mapping")
    return value


_SNAPSHOT_LEAVES = (str, bool, int, float)


def _snapshot(value: Any, depth: int = 0) -> Any:
    """Copy JSON values once. Later reads must not use the caller's mapping.

    Leaves must be exact built-ins. ``bool`` is listed separately because it
    is a subclass of ``int``. ``None`` is the JSON null leaf.
    """
    if depth > 32:
        _fail("ENVELOPE_SOURCE_INVALID", "input is nested too deeply")
    if value is None or type(value) in _SNAPSHOT_LEAVES:
        return value
    if isinstance(value, Mapping):
        copied: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                _fail("ENVELOPE_SOURCE_INVALID", "mapping key must be a string")
            if key in copied:
                _fail("ENVELOPE_SOURCE_INVALID", "mapping repeats a key")
            copied[key] = _snapshot(item, depth + 1)
        return copied
    if isinstance(value, (list, tuple)):
        return [_snapshot(item, depth + 1) for item in value]
    _fail("ENVELOPE_SOURCE_INVALID", "input is not plain JSON data")


def _authority_false_or_absent(record: Mapping[str, Any], label: str) -> None:
    if "authority_before" in record or "authority_after" in record:
        _fail(
            "ENVELOPE_AUTHORITY_INVALID",
            f"{label} carries fabricated authority history",
        )
    if "authority" in record and record["authority"] is not False:
        _fail("ENVELOPE_AUTHORITY_INVALID", f"{label} authority is not false")


def _sha256(value: Any) -> str:
    if not isinstance(value, str) or value.strip().lower() in _UNPINNED_REVISIONS:
        _fail("ENVELOPE_REVISION_UNBOUND", "revision is not a bound digest")
    if _SHA256_RE.fullmatch(value) is None:
        _fail("ENVELOPE_REVISION_UNBOUND", "revision is not a bound digest")
    return value


def _relative_name(value: Any) -> str:
    if not isinstance(value, str) or not value or value in {".", ".."}:
        _fail("ENVELOPE_REVISION_UNBOUND", "pin path is not a relative file name")
    if "\\" in value or value.startswith("/") or ":" in value:
        _fail("ENVELOPE_REVISION_UNBOUND", "pin path is not a relative file name")
    parts = value.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        _fail("ENVELOPE_REVISION_UNBOUND", "pin path is not a relative file name")
    return value


def _bound_revision(pin: Mapping[str, Any]) -> dict[str, Any]:
    """Copy the pin file inventory. Absolute roots and byte counts stay out."""
    files = pin.get("files")
    if not isinstance(files, list) or not files:
        _fail("ENVELOPE_REVISION_UNBOUND", "pin has no file digest")
    copied: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in files:
        if not isinstance(item, Mapping):
            _fail("ENVELOPE_REVISION_UNBOUND", "pin file entry is not a record")
        rel = _relative_name(item.get("relative_path"))
        if rel in seen:
            _fail("ENVELOPE_REVISION_UNBOUND", "pin repeats a relative path")
        seen.add(rel)
        copied.append({"relative_path": rel, "sha256": _sha256(item.get("sha256"))})
    revision: dict[str, Any] = {"files": copied}
    expected = pin.get("expected_sha256", None)
    if expected is not None:
        bound = _sha256(expected)
        if bound not in {entry["sha256"] for entry in copied}:
            _fail(
                "ENVELOPE_REVISION_UNBOUND",
                "expected_sha256 does not match a pinned file",
            )
        revision["expected_sha256"] = bound
    return revision


def _digest_matches(record: Mapping[str, Any], stated: Any, label: str, code: str) -> str:
    if not isinstance(stated, str) or _SHA256_RE.fullmatch(stated) is None:
        _fail(code, f"{label} digest is not bound")
    try:
        actual = canonical_digest(record)
    except (TypeError, ValueError) as exc:
        if isinstance(exc, EnvelopeError):
            raise
        _fail(code, f"{label} digest is not bound")
    if actual != stated:
        _fail(code, f"{label} does not match the reconstructability digest")
    return stated


def _claim_id(decision: Mapping[str, Any], claim: Mapping[str, Any]) -> str:
    found = decision.get("claim_id")
    if not isinstance(found, str) or not found.strip():
        _fail("ENVELOPE_SOURCE_INVALID", "decision claim_id is missing")
    if claim.get("claim_id") != found:
        _fail("ENVELOPE_SCOPE_UNBOUND", "claim_id does not match the claim record")
    return found


def _scope_ready(scope: Mapping[str, Any]) -> None:
    boundary = scope.get("allowed_write_boundary")
    if not isinstance(boundary, list) or not boundary:
        _fail("ENVELOPE_SCOPE_UNBOUND", "scope has no allowed_write_boundary")
    if any(not isinstance(item, str) or not item for item in boundary):
        _fail("ENVELOPE_SCOPE_UNBOUND", "scope boundary is not a list of strings")


def _families(
    vectors: Mapping[str, Any], requested: tuple[str, ...] | None
) -> list[str]:
    supported = {
        family
        for vector_id, family in _VECTOR_FAMILIES.items()
        if vector_id in vectors and isinstance(vectors[vector_id], str)
    }
    if requested is None:
        return sorted(supported)
    if not isinstance(requested, tuple):
        _fail("ENVELOPE_FAMILY_UNSUPPORTED", "detector_families must be a tuple")
    chosen: list[str] = []
    for family in requested:
        if not isinstance(family, str) or family not in supported:
            _fail("ENVELOPE_FAMILY_UNSUPPORTED", f"unsupported family {family!r}")
        if family not in chosen:
            chosen.append(family)
    return chosen


def _missing_observations(decision: Mapping[str, Any]) -> list[str]:
    raw = decision.get("missing")
    found: list[str] = []
    if raw is not None:
        if not isinstance(raw, list):
            _fail("ENVELOPE_SOURCE_INVALID", "missing observations must be a list")
        for item in raw:
            if not isinstance(item, str) or not item:
                _fail("ENVELOPE_SOURCE_INVALID", "missing observation is not a string")
            if item not in found:
                found.append(item)
    reason = decision.get("reason")
    if isinstance(reason, str) and reason in _INCOMPLETE_REASONS and reason not in found:
        found.append(reason)
    return found


def _reject_independent_claim(decision: Mapping[str, Any]) -> None:
    record = decision.get("independent_verification")
    if record is None:
        return
    if isinstance(record, bool) or not isinstance(record, Mapping):
        _fail("ENVELOPE_SOURCE_INVALID", "independent_verification must be a record")
    if record.get("claims_iw_acceptance") is True or record.get("claims_independent_witness") is True:
        _fail(
            "ENVELOPE_AUTHORITY_INVALID",
            "independent verification acceptance is not admitted",
        )
    if "authority" in record and record["authority"] is not False:
        _fail(
            "ENVELOPE_AUTHORITY_INVALID",
            "independent verification authority is not false",
        )


def _require_complete_reconstructability(report: Any) -> None:
    missing = report.missing_inputs
    if report.reconstructable is not True or len(missing) != 0:
        _fail(
            "ENVELOPE_MISSING_OBSERVATION",
            "reconstructability evidence is incomplete",
        )


def _counterexample(decision: Mapping[str, Any]) -> int | None:
    if "counterexample_count" not in decision:
        return None
    value = decision["counterexample_count"]
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        _fail("ENVELOPE_SOURCE_INVALID", "counterexample_count is not a count")
    return value


def build_tested_envelope(
    decision: Mapping[str, Any],
    *,
    claim: Mapping[str, Any],
    scope: Mapping[str, Any],
    provenance_pin: Mapping[str, Any],
    reconstructability: Mapping[str, Any],
    scope_note: str | None = None,
    detector_families: tuple[str, ...] | None = None,
    **forbidden: Any,
) -> dict[str, Any]:
    """Return a non-authoritative receipt bound to the cited records.

    ``scope_note`` is stored as an annotation. It is not the scope binding.
    """
    _reject_forbidden(forbidden)
    decision_map = _snapshot(_require_mapping(decision, "decision"))
    claim_map = _snapshot(_require_mapping(claim, "claim"))
    scope_map = _snapshot(_require_mapping(scope, "scope"))
    pin_map = _snapshot(_require_mapping(provenance_pin, "provenance_pin"))
    report_map = _snapshot(_require_mapping(reconstructability, "reconstructability"))
    _authority_false_or_absent(decision_map, "decision")
    _authority_false_or_absent(claim_map, "claim")
    _authority_false_or_absent(scope_map, "scope")
    _authority_false_or_absent(pin_map, "provenance")
    _reject_independent_claim(decision_map)

    if scope_note is not None and not isinstance(scope_note, str):
        _fail("ENVELOPE_SOURCE_INVALID", "scope_note must be a string")

    try:
        report = strict_parse_report(report_map)
    except ReconstructabilityError as exc:
        _fail("ENVELOPE_SOURCE_INVALID", str(exc))

    if report.independent_evidence_count != 0:
        _fail("ENVELOPE_AUTHORITY_INVALID", "independent evidence count is not zero")
    if report.independent_evidence_admission_status != "NOT_CONFIGURED":
        _fail("ENVELOPE_AUTHORITY_INVALID", "independent evidence admission is closed")
    _require_complete_reconstructability(report)

    digests = report.canonical_input_digests
    _digest_matches(
        decision_map,
        digests.get("DECISION.json"),
        "DECISION.json",
        "ENVELOPE_REVISION_UNBOUND",
    )
    _digest_matches(
        pin_map,
        digests.get("PROVENANCE.json"),
        "PROVENANCE.json",
        "ENVELOPE_REVISION_UNBOUND",
    )
    scope_digest = _digest_matches(
        scope_map,
        digests.get("SCOPE.json"),
        "SCOPE.json",
        "ENVELOPE_SCOPE_UNBOUND",
    )
    _digest_matches(
        claim_map,
        digests.get("CLAIM.json"),
        "CLAIM.json",
        "ENVELOPE_SCOPE_UNBOUND",
    )
    _scope_ready(scope_map)
    claim_id = _claim_id(decision_map, claim_map)
    revision = _bound_revision(pin_map)

    source_result = decision_map.get("decision")
    if not isinstance(source_result, str) or not source_result:
        _fail("ENVELOPE_SOURCE_INVALID", "decision token is missing")
    vectors = decision_map.get("vectors")
    if not isinstance(vectors, Mapping):
        _fail("ENVELOPE_SOURCE_INVALID", "vectors must be a mapping")
    families = _families(vectors, detector_families)
    missing = _missing_observations(decision_map)

    broader = decision_map.get("broader_classification")
    if broader is not None and broader != "CLAIM_SUPPORTED_PARTIAL":
        _fail("ENVELOPE_PROMOTION", "broader classification cannot be strengthened")
    for flag in ("promoted", "promoted_to_full"):
        if flag in decision_map and decision_map[flag] is not False:
            _fail("ENVELOPE_PROMOTION", "source records a promotion")

    if source_result == "PASS":
        if missing or any(name not in vectors for name in _VECTOR_FAMILIES):
            _fail("ENVELOPE_MISSING_OBSERVATION", "missing observations block PASS")
        if any(value != "PASS" for value in vectors.values()):
            _fail("ENVELOPE_PROMOTION", "PASS decision cites a vector that is not PASS")
        if broader != "CLAIM_SUPPORTED_PARTIAL":
            _fail("ENVELOPE_PROMOTION", "PASS is not a partial classification")
        if decision_map.get("claim_result") != "PASS":
            _fail("ENVELOPE_PROMOTION", "claim_result is not PASS")
    elif source_result not in _NON_PASS:
        _fail("ENVELOPE_SOURCE_INVALID", f"unsupported decision token {source_result!r}")

    receipt: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "authority": False,
        "claim_id": claim_id,
        "artifact_revision": revision,
        "source_result": source_result,
        "result": source_result,
        "detector_families": families,
        "scope_binding": {"claim_id": claim_id, "scope_digest": scope_digest},
        "exclusions": list(_EXCLUSIONS),
        "unresolved_assumptions": list(report.unresolved_assumptions),
        "missing_observations": missing,
    }
    if broader is not None:
        receipt["broader_classification"] = broader
    count = _counterexample(decision_map)
    if count is not None:
        receipt["counterexample_count"] = count
    if scope_note is not None:
        receipt["annotations"] = {"scope_note": scope_note, "authority": False}
    return receipt
