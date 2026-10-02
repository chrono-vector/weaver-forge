"""Classify a candidate verification package without admitting evidence.

Digests and environment fingerprints are recomputed from structured bodies.
Execution ids, observer labels, and provider names do not establish independence.
"""

from __future__ import annotations

import unicodedata
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
_ENV_FIELDS = frozenset({"runner", "os", "runtime", "backend", "dependency_manifest"})
_ENV_OPTIONAL = frozenset({"dependency_manifest_digest"})
_MANIFEST_REQUIRED = frozenset({"components"})
_MANIFEST_OPTIONAL = frozenset({"annotation", "nonce"})
_COMPONENT_FIELDS = frozenset({"name", "version"})
_EVIDENCE_BODY_REQUIRED = frozenset(
    {"claim_id", "input_digest", "result_token", "observation"}
)
_EVIDENCE_BODY_OPTIONAL = frozenset({"annotation", "nonce"})
_OBSERVATION_FIELDS = frozenset({"measured_sha256"})
_INPUT_FIELDS = frozenset({"relative_path", "sha256"})
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


def _reject_noncanonical(value: Any, code: str, label: str) -> str:
    """Reject format characters and compatibility spellings. Do not equate them."""
    if type(value) is not str or not value.strip():
        _fail(code, f"{label} is missing")
    if unicodedata.normalize("NFKC", value) != value:
        _fail(code, f"{label} is not canonical")
    if any(unicodedata.category(char) == "Cf" for char in value):
        _fail(code, f"{label} is not canonical")
    return value


def _identifier_token(token: str) -> bool:
    if not token.isascii() or not token[0].isalnum() or token[0].isupper():
        return False
    previous_separator = False
    for char in token:
        if char.isascii() and char.islower() or char.isascii() and char.isdigit():
            previous_separator = False
            continue
        if char in "._+-" and not previous_separator:
            previous_separator = True
            continue
        return False
    return not previous_separator


def _version_token(token: str) -> bool:
    parts = token.split(".")
    if len(parts) != 3:
        return False
    return all(part.isascii() and part.isdigit() and part == str(int(part)) for part in parts)


def _canonical_os(value: Any) -> str:
    raw = _reject_noncanonical(value, "IVP_ENVIRONMENT_UNBOUND", "os")
    token = raw.strip().casefold()
    if not _identifier_token(token):
        _fail("IVP_ENVIRONMENT_UNBOUND", "os is not canonical")
    return token


def _canonical_runtime(value: Any) -> str:
    raw = _reject_noncanonical(value, "IVP_ENVIRONMENT_UNBOUND", "runtime")
    token = raw.strip()
    if not _version_token(token):
        _fail("IVP_ENVIRONMENT_UNBOUND", "runtime is not canonical")
    return token


def _canonical_label(value: Any, label: str) -> str:
    raw = _reject_noncanonical(value, "IVP_ENVIRONMENT_UNBOUND", label)
    return raw.strip().casefold()


def _bind_manifest(value: Any, supplied_digest: str | None) -> str:
    """Return the recomputed digest of the structured manifest body."""
    code = "IVP_ENVIRONMENT_UNBOUND"
    if type(value) is not dict or not value:
        _fail(code, "dependency manifest is not a structured body")
    _keys(value, _MANIFEST_REQUIRED, _MANIFEST_OPTIONAL, code)
    for key in _MANIFEST_OPTIONAL:
        if key in value and type(value.get(key)) is not str:
            _fail(code, "dependency manifest metadata is not a string")
    components = value.get("components")
    if type(components) is not list or not components:
        _fail(code, "dependency manifest has no components")
    normalized: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in components:
        if type(item) is not dict:
            _fail(code, "dependency manifest component is not a record")
        _keys(item, _COMPONENT_FIELDS, frozenset(), code)
        name = _reject_noncanonical(item.get("name"), code, "component name")
        version = _reject_noncanonical(item.get("version"), code, "component version")
        name_token = name.strip()
        version_token = version.strip()
        if not _identifier_token(name_token) or not _version_token(version_token):
            _fail(code, "dependency manifest component is not canonical")
        if name_token in seen:
            _fail(code, "dependency manifest repeats a component")
        seen.add(name_token)
        normalized.append({"name": name_token, "version": version_token})
    normalized.sort(key=lambda item: item["name"])
    recomputed = _digest({"components": normalized}, code)
    if supplied_digest is not None and supplied_digest != recomputed:
        _fail(code, "dependency manifest digest does not match the body")
    return recomputed


def _bind_environment(record: Any) -> tuple[str, str, str]:
    """Return fingerprint, substantive digest, and recomputed manifest digest."""
    if type(record) is not dict:
        _fail("IVP_ENVIRONMENT_UNBOUND", "environment is not a record")
    _keys(
        record,
        frozenset({"record"}),
        frozenset({"fingerprint", "label"}),
        "IVP_ENVIRONMENT_UNBOUND",
    )
    env = record.get("record")
    if type(env) is not dict or not env:
        _fail("IVP_ENVIRONMENT_UNBOUND", "environment record is not structured")
    if set(env) - _ENV_FIELDS - _ENV_OPTIONAL:
        _fail("IVP_ENVIRONMENT_UNBOUND", "environment record has an unsupported field")
    if not _ENV_FIELDS <= set(env):
        _fail("IVP_ENVIRONMENT_UNBOUND", "environment record is missing a required field")
    if "label" in record and type(record.get("label")) is not str:
        _fail("IVP_SOURCE_INVALID", "environment label is not a string")
    supplied = None
    if "dependency_manifest_digest" in env:
        supplied = _sha256(env.get("dependency_manifest_digest"), "IVP_ENVIRONMENT_UNBOUND")
    manifest_digest = _bind_manifest(env.get("dependency_manifest"), supplied)
    normalized = {
        "backend": _canonical_label(env.get("backend"), "backend"),
        "dependency_manifest_digest": manifest_digest,
        "os": _canonical_os(env.get("os")),
        "runner": _canonical_label(env.get("runner"), "runner"),
        "runtime": _canonical_runtime(env.get("runtime")),
    }
    fingerprint = _digest(normalized, "IVP_ENVIRONMENT_UNBOUND")
    if "fingerprint" in record and record.get("fingerprint") != fingerprint:
        _fail("IVP_ENVIRONMENT_UNBOUND", "fingerprint does not match the environment record")
    substantive = _digest(
        {
            "dependency_manifest_digest": manifest_digest,
            "os": normalized["os"],
            "runtime": normalized["runtime"],
        },
        "IVP_ENVIRONMENT_UNBOUND",
    )
    return fingerprint, substantive, manifest_digest


def _expected_measurement(claim: Mapping[str, Any], revision: Mapping[str, Any]) -> str:
    """Return the cited content digest a reproduction is required to measure.

    Only pin.expected_sha256 and claim.adapter_params.expected_sha256 are
    accepted. A decision token is not treated as a hash claim.
    """
    cited: list[str] = []
    if "expected_sha256" in revision:
        cited.append(_sha256(revision.get("expected_sha256"), "IVP_BINDING_UNAVAILABLE"))
    if "adapter_params" in claim:
        params = claim.get("adapter_params")
        if type(params) is not dict:
            _fail("IVP_BINDING_UNAVAILABLE", "adapter_params is not a record")
        if "expected_sha256" in params:
            cited.append(_sha256(params.get("expected_sha256"), "IVP_BINDING_UNAVAILABLE"))
    if not cited:
        _fail("IVP_BINDING_UNAVAILABLE", "measured result is not bound to a cited digest")
    expected = cited[0]
    if any(item != expected for item in cited):
        _fail("IVP_BINDING_UNAVAILABLE", "cited expected digests disagree")
    return expected


def _bind_reproduction_evidence(
    record: Any,
    *,
    claim_id: str,
    input_digest: str,
    cited_result: str,
    expected: str,
) -> tuple[str, str]:
    """Return the evidence-core digest and the execution result token.

    measured_sha256 must equal the cited expected content digest. Agreement is
    required for a reproduction and is not independence evidence. Annotation
    and nonce are caller metadata and are not part of the result core.
    """
    code = "IVP_EVIDENCE_DIGEST_INVALID"
    if type(record) is not dict:
        _fail(code, "evidence is not a record")
    _keys(record, frozenset({"body"}), frozenset({"digest", "label"}), code)
    body = record.get("body")
    if type(body) is not dict or not body:
        _fail(code, "evidence body is not a record")
    _keys(body, _EVIDENCE_BODY_REQUIRED, _EVIDENCE_BODY_OPTIONAL, code)
    for key in _EVIDENCE_BODY_OPTIONAL:
        if key in body and type(body.get(key)) is not str:
            _fail(code, "evidence metadata is not a string")
    if "label" in record and type(record.get("label")) is not str:
        _fail("IVP_SOURCE_INVALID", "evidence label is not a string")
    observation = body.get("observation")
    if type(observation) is not dict or not observation:
        _fail(code, "evidence observation is not a record")
    _keys(observation, _OBSERVATION_FIELDS, frozenset(), code)
    measured = _sha256(observation.get("measured_sha256"), code)
    evidence_claim = _nonempty(body.get("claim_id"), "IVP_CLAIM_MISMATCH", "claim_id")
    if evidence_claim != claim_id:
        _fail("IVP_CLAIM_MISMATCH", "evidence claim_id does not match the cited claim")
    evidence_input = _sha256(body.get("input_digest"), "IVP_BINDING_UNAVAILABLE")
    if evidence_input != input_digest:
        _fail("IVP_BINDING_UNAVAILABLE", "evidence input_digest does not match the input record")
    evidence_result = _nonempty(
        body.get("result_token"),
        "IVP_BINDING_UNAVAILABLE",
        "result_token",
    )
    if evidence_result != cited_result:
        _fail("IVP_BINDING_UNAVAILABLE", "evidence result_token does not match the cited decision")
    if measured != expected:
        _fail("IVP_BINDING_UNAVAILABLE", "measured result does not match the cited digest")
    core = {
        "claim_id": evidence_claim,
        "input_digest": evidence_input,
        "result_token": evidence_result,
        "observation": {"measured_sha256": measured},
    }
    recomputed = _digest(core, code)
    if "digest" in record and record.get("digest") != recomputed:
        _fail(code, "evidence digest does not match the body")
    return recomputed, evidence_result


def _bind_execution(
    record: Any,
    *,
    claim_id: str,
    input_digest: str,
    cited_result: str,
    expected: str,
) -> dict[str, str]:
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
    fingerprint, substantive, manifest_digest = _bind_environment(record.get("environment"))
    evidence_digest, result_token = _bind_reproduction_evidence(
        record.get("evidence"),
        claim_id=claim_id,
        input_digest=input_digest,
        cited_result=cited_result,
        expected=expected,
    )
    record_digest = _digest(
        {
            "execution_id": execution_id,
            "substantive_environment": substantive,
            "dependency_manifest_digest": manifest_digest,
            "input_digest": input_digest,
            "result_core": evidence_digest,
        },
        "IVP_EXECUTION_INVALID",
    )
    return {
        "execution_id": execution_id,
        "environment_fingerprint": fingerprint,
        "substantive_environment": substantive,
        "evidence_digest": evidence_digest,
        "record_digest": record_digest,
        "result_token": result_token,
    }


def _bind_input(candidate: Mapping[str, Any], revision: Mapping[str, Any]) -> tuple[str, str]:
    record = candidate.get("input_record")
    if type(record) is not dict or not record:
        _fail("IVP_BINDING_UNAVAILABLE", "input record is not bound")
    _keys(record, _INPUT_FIELDS, frozenset(), "IVP_BINDING_UNAVAILABLE")
    relative = record.get("relative_path")
    if type(relative) is not str or not relative.strip():
        _fail("IVP_BINDING_UNAVAILABLE", "input record is not bound")
    digest = _sha256(record.get("sha256"), "IVP_BINDING_UNAVAILABLE")
    matched = False
    for entry in revision["files"]:
        if entry["relative_path"] == relative and entry["sha256"] == digest:
            matched = True
            break
    if not matched:
        _fail("IVP_BINDING_UNAVAILABLE", "input record is not a cited pin file")
    recomputed = _digest(
        {"relative_path": relative, "sha256": digest},
        "IVP_BINDING_UNAVAILABLE",
    )
    if "input_digest" in candidate and candidate.get("input_digest") != recomputed:
        _fail("IVP_BINDING_UNAVAILABLE", "input digest does not match the input record")
    return recomputed, digest


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
    replay = (
        source["execution_id"] == independent["execution_id"]
        or source["substantive_environment"] == independent["substantive_environment"]
        or source["record_digest"] == independent["record_digest"]
        or len(package) != len(set(package))
    )
    if replay:
        return "DUPLICATE", False
    if source["evidence_digest"] != independent["evidence_digest"]:
        _fail("IVP_BINDING_UNAVAILABLE", "semantic result cores do not agree")
    if result_token != cited_result:
        _fail("IVP_BINDING_UNAVAILABLE", "result_token does not match the cited decision")
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
        if len(report.unresolved_assumptions) != 0:
            _fail("IVP_BINDING_UNAVAILABLE", "unresolved assumptions block reproduction")
        _keys(candidate_map, _REPRODUCTION_REQUIRED, _REPRODUCTION_OPTIONAL, "IVP_SOURCE_INVALID")
        input_digest, content_sha = _bind_input(candidate_map, revision)
        expected = _expected_measurement(claim_map, revision)
        if expected != content_sha:
            _fail(
                "IVP_BINDING_UNAVAILABLE",
                "expected measurement does not match the bound input",
            )
        source = _bind_execution(
            candidate_map.get("source_execution"),
            claim_id=claim_id,
            input_digest=input_digest,
            cited_result=cited_result,
            expected=expected,
        )
        independent = _bind_execution(
            candidate_map.get("independent_execution"),
            claim_id=claim_id,
            input_digest=input_digest,
            cited_result=cited_result,
            expected=expected,
        )
        result_token = _nonempty(
            candidate_map.get("result_token"),
            "IVP_SOURCE_INVALID",
            "result_token",
        )
        if (
            result_token != cited_result
            or result_token != source["result_token"]
            or result_token != independent["result_token"]
        ):
            _fail(
                "IVP_BINDING_UNAVAILABLE",
                "result_token does not match the cited decision",
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
