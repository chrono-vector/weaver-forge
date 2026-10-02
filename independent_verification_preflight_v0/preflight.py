"""Classify a candidate verification package without admitting evidence.

Digests and environment fingerprints are recomputed from structured bodies.
Execution ids, observer labels, and provider names do not establish independence.
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

SCHEMA_VERSION = "independent_verification_preflight.v0"
ADMISSION_STATUS = "NOT_CONFIGURED"
_LEAF_TYPES = (str, bool, int, float)
_SHA256_WIDTH = 64
_HEX = frozenset("0123456789abcdef")
_UNPINNED_REVISIONS = frozenset(
    {
        "head",
        "latest",
        "main",
        "master",
        "origin/main",
        "origin/master",
        "current",
        "same as above",
    }
)
_KINDS = frozenset({"REPRODUCTION", "CHALLENGE"})
_DESCRIPTIVE_BASES = frozenset(
    {
        "DISTINCT_OBSERVER",
        "INDEPENDENT_REPRODUCTION",
        "DISTINCT_CUSTODY_CHAIN",
        "DISTINCT_INSTRUMENT",
        "DISTINCT_METHOD",
        "EXTERNAL_WITNESS_RECEIPT",
        "SELF_DECLARED",
    }
)
_ENV_FIELDS = frozenset(
    {"runner", "os", "runtime", "backend", "dependency_manifest_digest"}
)
_ENV_STRINGS = frozenset({"runner", "os", "runtime", "backend"})
_SCOPE_KEYS = frozenset(
    {
        "structural_candidate",
        "classification",
        "admission_status",
        "independent_evidence_count",
        "claims_iw_acceptance",
        "claims_independent_witness",
        "authority",
        "independent",
        "independence_score",
        "human_final",
        "human_final_status",
        "is_human_final",
        "creates_human_final",
        "promotes_to_human_final",
    }
)
_REPRODUCTION_REQUIRED = frozenset(
    {
        "verification_kind",
        "claim_id",
        "input_record",
        "result_token",
        "source_execution",
        "independent_execution",
    }
)
_REPRODUCTION_OPTIONAL = frozenset(
    {
        "input_digest",
        "observer_id",
        "observer_basis",
        "backend_provider",
        "model",
        "annotation",
        "package_entries",
    }
)
_CHALLENGE_REQUIRED = frozenset(
    {
        "verification_kind",
        "claim_id",
        "challenge_evidence",
        "assumptions_attacked",
        "counterexample_present",
    }
)
_CHALLENGE_OPTIONAL = frozenset(
    {
        "counterexample",
        "observer_id",
        "observer_basis",
        "backend_provider",
        "model",
        "annotation",
    }
)
_LIMITATIONS = (
    "admitted independent evidence",
    "accepted independent reproduction",
    "truth",
    "global safety",
    "observer authority",
    "Human Final",
    "canonical status",
    "published status",
    "deployed status",
    "recovery",
    "rollback",
    "external witness admission",
)


class IndependentVerificationPreflightError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


def _fail(code: str, message: str) -> None:
    raise IndependentVerificationPreflightError(code, message)


def _snapshot(value: Any, depth: int = 0) -> Any:
    """Copy caller values once into exact built-in containers and leaves."""
    if depth > 32:
        _fail("IVP_SOURCE_INVALID", "input is nested too deeply")
    if value is None or type(value) in _LEAF_TYPES:
        return value
    if isinstance(value, Mapping):
        copied: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                _fail("IVP_SOURCE_INVALID", "mapping key must be a string")
            if key in copied:
                _fail("IVP_SOURCE_INVALID", "mapping repeats a key")
            copied[key] = _snapshot(item, depth + 1)
        return copied
    if type(value) is list or type(value) is tuple:
        return [_snapshot(item, depth + 1) for item in value]
    _fail("IVP_SOURCE_INVALID", "input is not plain JSON data")


def _require_mapping(value: Any, label: str) -> Mapping[str, Any]:
    if isinstance(value, bool) or not isinstance(value, Mapping):
        _fail("IVP_SOURCE_INVALID", f"{label} must be a mapping")
    return value


def _reject_scope(names: set[str]) -> None:
    if names & _SCOPE_KEYS:
        _fail("IVP_SCOPE_VIOLATION", "caller cannot set admission or authority")


def _keys(record: Mapping[str, Any], required: frozenset[str], optional: frozenset[str], code: str) -> None:
    unknown = set(record) - required - optional
    if unknown:
        _fail(code, "record has an unsupported field")
    if not required <= set(record):
        _fail(code, "record is missing a required field")


def _nonempty(value: Any, code: str, label: str) -> str:
    if type(value) is not str or not value.strip():
        _fail(code, f"{label} is missing")
    return value


def _sha256(value: Any, code: str) -> str:
    if type(value) is not str or len(value) != _SHA256_WIDTH:
        _fail(code, "digest is not a bound sha256")
    if any(char not in _HEX for char in value):
        _fail(code, "digest is not a bound sha256")
    return value


def _unpinned(value: Any) -> bool:
    return type(value) is str and value.strip().lower() in _UNPINNED_REVISIONS


def _digest(record: Any, code: str) -> str:
    try:
        return canonical_digest(record)
    except (TypeError, ValueError) as exc:
        if isinstance(exc, IndependentVerificationPreflightError):
            raise
        _fail(code, "record cannot be canonicalized")
        raise AssertionError("closed")


def _relative_name(value: Any) -> str:
    if type(value) is not str or not value or value in {".", ".."}:
        _fail("IVP_REVISION_UNBOUND", "pin path is not a relative file name")
    if _unpinned(value) or "\\" in value or value.startswith("/") or ":" in value:
        _fail("IVP_REVISION_UNBOUND", "pin path is not a relative file name")
    parts = value.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        _fail("IVP_REVISION_UNBOUND", "pin path is not a relative file name")
    return value


def _file_sha(value: Any) -> str:
    if _unpinned(value):
        _fail("IVP_REVISION_UNBOUND", "revision is not a pinned digest")
    return _sha256(value, "IVP_REVISION_UNBOUND")


def _bound_revision(pin: Mapping[str, Any]) -> dict[str, Any]:
    files = pin.get("files")
    if type(files) is not list or not files:
        _fail("IVP_REVISION_UNBOUND", "pin has no file digest")
    copied: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in files:
        if type(item) is not dict:
            _fail("IVP_REVISION_UNBOUND", "pin file entry is not a record")
        rel = _relative_name(item.get("relative_path"))
        if rel in seen:
            _fail("IVP_REVISION_UNBOUND", "pin repeats a relative path")
        seen.add(rel)
        copied.append({"relative_path": rel, "sha256": _file_sha(item.get("sha256"))})
    revision: dict[str, Any] = {"files": copied}
    if "expected_sha256" in pin and pin.get("expected_sha256") is not None:
        bound = _file_sha(pin.get("expected_sha256"))
        if bound not in {entry["sha256"] for entry in copied}:
            _fail("IVP_REVISION_UNBOUND", "expected_sha256 does not match a pinned file")
        revision["expected_sha256"] = bound
    return revision


def _stated_digest(report: Any, name: str, code: str) -> str:
    stated = report.canonical_input_digests.get(name)
    if type(stated) is not str:
        _fail(code, f"{name} is not bound")
    return _sha256(stated, code)


def _bind_citation(
    decision: Mapping[str, Any],
    claim: Mapping[str, Any],
    pin: Mapping[str, Any],
    report: Any,
) -> tuple[str, str, dict[str, Any]]:
    if report.reconstructable is not True or len(report.missing_inputs) != 0:
        _fail("IVP_BINDING_UNAVAILABLE", "reconstructability evidence is incomplete")
    claim_digest = _stated_digest(report, "CLAIM.json", "IVP_CLAIM_MISMATCH")
    decision_digest = _stated_digest(report, "DECISION.json", "IVP_BINDING_UNAVAILABLE")
    pin_digest = _stated_digest(report, "PROVENANCE.json", "IVP_REVISION_UNBOUND")
    if _digest(claim, "IVP_CLAIM_MISMATCH") != claim_digest:
        _fail("IVP_CLAIM_MISMATCH", "claim does not match the cited digest")
    if _digest(decision, "IVP_BINDING_UNAVAILABLE") != decision_digest:
        _fail("IVP_BINDING_UNAVAILABLE", "decision does not match the cited digest")
    if _digest(pin, "IVP_REVISION_UNBOUND") != pin_digest:
        _fail("IVP_REVISION_UNBOUND", "pin does not match the cited digest")
    claim_id = _nonempty(claim.get("claim_id"), "IVP_CLAIM_MISMATCH", "claim_id")
    if decision.get("claim_id") != claim_id:
        _fail("IVP_CLAIM_MISMATCH", "decision claim_id does not match the claim")
    result_token = _nonempty(decision.get("decision"), "IVP_BINDING_UNAVAILABLE", "decision")
    return claim_id, result_token, _bound_revision(pin)


def _bind_evidence(record: Any, code: str) -> tuple[str, dict[str, Any]]:
    if type(record) is not dict:
        _fail(code, "evidence is not a record")
    _keys(record, frozenset({"body"}), frozenset({"digest", "label"}), code)
    body = record.get("body")
    if type(body) is not dict:
        _fail(code, "evidence body is not a record")
    if "label" in record and type(record.get("label")) is not str:
        _fail("IVP_SOURCE_INVALID", "evidence label is not a string")
    recomputed = _digest(body, code)
    if "digest" in record and record.get("digest") != recomputed:
        _fail(code, "evidence digest does not match the body")
    return recomputed, body


def _bind_environment(record: Any) -> str:
    if type(record) is not dict:
        _fail("IVP_ENVIRONMENT_UNBOUND", "environment is not a record")
    _keys(
        record,
        frozenset({"record"}),
        frozenset({"fingerprint", "label"}),
        "IVP_ENVIRONMENT_UNBOUND",
    )
    env = record.get("record")
    if type(env) is not dict:
        _fail("IVP_ENVIRONMENT_UNBOUND", "environment record is not structured")
    if set(env) - _ENV_FIELDS:
        _fail("IVP_ENVIRONMENT_UNBOUND", "environment record has an unsupported field")
    if "label" in record and type(record.get("label")) is not str:
        _fail("IVP_SOURCE_INVALID", "environment label is not a string")
    normalized: dict[str, str] = {}
    for key, value in env.items():
        if key in _ENV_STRINGS:
            normalized[key] = _nonempty(value, "IVP_ENVIRONMENT_UNBOUND", key)
        elif key == "dependency_manifest_digest":
            normalized[key] = _sha256(value, "IVP_ENVIRONMENT_UNBOUND")
    recomputed = _digest(normalized, "IVP_ENVIRONMENT_UNBOUND")
    if "fingerprint" in record and record.get("fingerprint") != recomputed:
        _fail("IVP_ENVIRONMENT_UNBOUND", "fingerprint does not match the environment record")
    return recomputed


def _bind_execution(record: Any) -> dict[str, str]:
    if type(record) is not dict:
        _fail("IVP_EXECUTION_INVALID", "execution is not a record")
    _keys(
        record,
        frozenset({"execution_id", "environment", "evidence"}),
        frozenset(),
        "IVP_EXECUTION_INVALID",
    )
    execution_id = _nonempty(
        record.get("execution_id"),
        "IVP_EXECUTION_INVALID",
        "execution_id",
    )
    fingerprint = _bind_environment(record.get("environment"))
    evidence_digest, body = _bind_evidence(record.get("evidence"), "IVP_EVIDENCE_DIGEST_INVALID")
    record_digest = _digest(
        {
            "execution_id": execution_id,
            "environment_fingerprint": fingerprint,
            "evidence": body,
        },
        "IVP_EXECUTION_INVALID",
    )
    return {
        "execution_id": execution_id,
        "environment_fingerprint": fingerprint,
        "evidence_digest": evidence_digest,
        "record_digest": record_digest,
    }


def _bind_input(candidate: Mapping[str, Any]) -> str:
    record = candidate.get("input_record")
    if type(record) is not dict:
        _fail("IVP_BINDING_UNAVAILABLE", "input record is not bound")
    recomputed = _digest(record, "IVP_BINDING_UNAVAILABLE")
    if "input_digest" in candidate and candidate.get("input_digest") != recomputed:
        _fail("IVP_BINDING_UNAVAILABLE", "input digest does not match the input record")
    return recomputed


def _package_digests(raw: Any) -> list[str]:
    if type(raw) is not list:
        _fail("IVP_SOURCE_INVALID", "package entries are not a list")
    return [
        _bind_evidence(item, "IVP_EVIDENCE_DIGEST_INVALID")[0]
        for item in raw
    ]


def _reproduction_outcome(
    source: Mapping[str, str],
    independent: Mapping[str, str],
    result_token: str,
    cited_result: str,
    package: list[str],
) -> tuple[str, bool]:
    evidence = [source["evidence_digest"], independent["evidence_digest"], *package]
    replay = (
        source["execution_id"] == independent["execution_id"]
        or source["evidence_digest"] == independent["evidence_digest"]
        or source["environment_fingerprint"] == independent["environment_fingerprint"]
        or source["record_digest"] == independent["record_digest"]
        or len(evidence) != len(set(evidence))
    )
    if replay:
        return "DUPLICATE", False
    if result_token != cited_result:
        return "NOT_INDEPENDENT", False
    return "BOUND_CANDIDATE", True


def _summary(bound: Mapping[str, str], input_digest: str, result_token: str) -> dict[str, str]:
    return {
        "execution_id": bound["execution_id"],
        "environment_fingerprint": bound["environment_fingerprint"],
        "evidence_digest": bound["evidence_digest"],
        "input_digest": input_digest,
        "result_token": result_token,
    }


def _allowed_assumption_digests(
    decision: Mapping[str, Any],
    claim: Mapping[str, Any],
    pin: Mapping[str, Any],
    revision: Mapping[str, Any],
    report: Any,
) -> set[str]:
    allowed = {
        _digest(decision, "IVP_CHALLENGE_INVALID"),
        _digest(claim, "IVP_CHALLENGE_INVALID"),
        _digest(pin, "IVP_CHALLENGE_INVALID"),
    }
    for entry in revision["files"]:
        allowed.add(_digest(entry, "IVP_CHALLENGE_INVALID"))
    for item in report.unresolved_assumptions:
        if type(item) is str:
            allowed.add(_digest(item, "IVP_CHALLENGE_INVALID"))
    return allowed


def _bind_challenge(
    candidate: Mapping[str, Any],
    allowed: set[str],
) -> dict[str, Any]:
    evidence_digest, _body = _bind_evidence(
        candidate.get("challenge_evidence"),
        "IVP_EVIDENCE_DIGEST_INVALID",
    )
    raw = candidate.get("assumptions_attacked")
    if type(raw) is not list or not raw:
        _fail("IVP_CHALLENGE_INVALID", "assumptions_attacked is not bound")
    assumptions: list[str] = []
    seen: set[str] = set()
    for item in raw:
        if type(item) is not str or _unpinned(item):
            _fail("IVP_CHALLENGE_INVALID", "assumptions_attacked is not a cited digest")
        digest = _sha256(item, "IVP_CHALLENGE_INVALID")
        if digest not in allowed or digest in seen:
            _fail("IVP_CHALLENGE_INVALID", "assumptions_attacked is not a cited digest")
        seen.add(digest)
        assumptions.append(digest)
    present = candidate.get("counterexample_present")
    if type(present) is not bool:
        _fail("IVP_CHALLENGE_INVALID", "counterexample_present is not a boolean")
    has_object = "counterexample" in candidate
    if present and not has_object:
        _fail("IVP_CHALLENGE_INVALID", "counterexample object is required")
    if has_object and not present:
        _fail("IVP_CHALLENGE_INVALID", "counterexample object is not allowed")
    summary: dict[str, Any] = {
        "counterexample_present": present,
    }
    if present:
        counter = candidate.get("counterexample")
        digest, body = _bind_evidence(counter, "IVP_CHALLENGE_INVALID")
        summary["counterexample_digest"] = digest
        summary["counterexample_body"] = body
    return {
        "evidence_digest": evidence_digest,
        "assumptions_attacked": assumptions,
        "counterexample": summary,
    }


def _descriptive(candidate: Mapping[str, Any]) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    observer: dict[str, Any] = {}
    if "observer_id" in candidate:
        observer["observer_id"] = _nonempty(
            candidate.get("observer_id"),
            "IVP_SOURCE_INVALID",
            "observer_id",
        )
    if "observer_basis" in candidate:
        basis = candidate.get("observer_basis")
        if type(basis) is not str or basis not in _DESCRIPTIVE_BASES:
            _fail("IVP_SOURCE_INVALID", "observer_basis is not a descriptive token")
        observer["observer_basis"] = basis
    descriptive: dict[str, Any] = {}
    for key in ("backend_provider", "model"):
        if key in candidate:
            descriptive[key] = _nonempty(candidate.get(key), "IVP_SOURCE_INVALID", key)
    if observer:
        observer["authority"] = False
    if descriptive:
        descriptive["authority"] = False
    return (observer or None), (descriptive or None)


def _annotation(candidate: Mapping[str, Any]) -> str | None:
    if "annotation" not in candidate:
        return None
    note = candidate.get("annotation")
    if type(note) is not str:
        _fail("IVP_SOURCE_INVALID", "annotation must be a string")
    return note


def _finish(
    *,
    kind: str,
    claim_id: str,
    revision: dict[str, Any],
    classification: str,
    structural_candidate: bool,
    source_summary: dict[str, Any],
    independent_summary: dict[str, Any],
    candidate: Mapping[str, Any],
) -> dict[str, Any]:
    if kind == "CHALLENGE" and structural_candidate is not False:
        _fail("IVP_SCOPE_VIOLATION", "a challenge cannot be a reproduction candidate")
    if structural_candidate is True and classification != "BOUND_CANDIDATE":
        _fail("IVP_SCOPE_VIOLATION", "structural candidate is not bound")
    if structural_candidate is not True and classification == "BOUND_CANDIDATE":
        _fail("IVP_SCOPE_VIOLATION", "bound candidate flag is inconsistent")
    receipt: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "authority": False,
        "admission_status": ADMISSION_STATUS,
        "verification_kind": kind,
        "claim_id": claim_id,
        "artifact_revision_binding": revision,
        "classification": classification,
        "structural_candidate": structural_candidate,
        "source_execution_summary": source_summary,
        "independent_execution_summary": independent_summary,
        "limitations": list(_LIMITATIONS),
    }
    observer, descriptive = _descriptive(candidate)
    if observer is not None:
        receipt["observer"] = observer
    if descriptive is not None:
        receipt["descriptive"] = descriptive
    note = _annotation(candidate)
    if note is not None:
        receipt["annotations"] = {"annotation": note, "authority": False}
    return receipt


def build_independent_verification_preflight(
    decision: Mapping[str, Any],
    claim: Mapping[str, Any],
    pin: Mapping[str, Any],
    reconstructability_report: Mapping[str, Any],
    candidate: Mapping[str, Any],
    **forbidden: Any,
) -> dict[str, Any]:
    """Return a non-authoritative preflight receipt.

    ``structural_candidate`` true means a future admission review could inspect
    this reproduction. It does not admit independent evidence.
    """
    if forbidden:
        _reject_scope(set(forbidden))
        _fail("IVP_SOURCE_INVALID", "unexpected preflight input")
    decision_map = _snapshot(_require_mapping(decision, "decision"))
    claim_map = _snapshot(_require_mapping(claim, "claim"))
    pin_map = _snapshot(_require_mapping(pin, "pin"))
    report_map = _snapshot(_require_mapping(reconstructability_report, "reconstructability"))
    candidate_map = _snapshot(_require_mapping(candidate, "candidate"))
    _reject_scope(set(candidate_map))
    try:
        report = strict_parse_report(report_map)
    except (ReconstructabilityError, AuthorityViolation) as exc:
        _fail("IVP_SOURCE_INVALID", str(exc))
    claim_id, cited_result, revision = _bind_citation(
        decision_map,
        claim_map,
        pin_map,
        report,
    )
    kind = candidate_map.get("verification_kind")
    if type(kind) is not str or kind not in _KINDS:
        _fail("IVP_SOURCE_INVALID", "verification_kind is not closed")
    if candidate_map.get("claim_id") != claim_id:
        _fail("IVP_CLAIM_MISMATCH", "candidate claim_id does not match the cited claim")
    if kind == "REPRODUCTION":
        _keys(candidate_map, _REPRODUCTION_REQUIRED, _REPRODUCTION_OPTIONAL, "IVP_SOURCE_INVALID")
        source = _bind_execution(candidate_map.get("source_execution"))
        independent = _bind_execution(candidate_map.get("independent_execution"))
        input_digest = _bind_input(candidate_map)
        result_token = _nonempty(
            candidate_map.get("result_token"),
            "IVP_SOURCE_INVALID",
            "result_token",
        )
        package = []
        if "package_entries" in candidate_map:
            package = _package_digests(candidate_map.get("package_entries"))
        classification, structural_candidate = _reproduction_outcome(
            source,
            independent,
            result_token,
            cited_result,
            package,
        )
        return _finish(
            kind=kind,
            claim_id=claim_id,
            revision=revision,
            classification=classification,
            structural_candidate=structural_candidate,
            source_summary=_summary(source, input_digest, result_token),
            independent_summary=_summary(independent, input_digest, result_token),
            candidate=candidate_map,
        )
    _keys(candidate_map, _CHALLENGE_REQUIRED, _CHALLENGE_OPTIONAL, "IVP_SOURCE_INVALID")
    challenge = _bind_challenge(
        candidate_map,
        _allowed_assumption_digests(decision_map, claim_map, pin_map, revision, report),
    )
    return _finish(
        kind=kind,
        claim_id=claim_id,
        revision=revision,
        classification="CHALLENGE_RECORDED",
        structural_candidate=False,
        source_summary={
            "claim_id": claim_id,
            "evidence_digest": challenge["evidence_digest"],
            "assumptions_attacked": challenge["assumptions_attacked"],
        },
        independent_summary=challenge["counterexample"],
        candidate=candidate_map,
    )
