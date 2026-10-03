"""Derive a non-authoritative receipt over an externally completed recovery.

The receipt binds stop, isolation, restore target, actions, and post-restore
checks by digest. It does not restore, roll back, mutate hosts, or create
Human Final. Local classification may be RECOVERED_BOUNDED; recovered stays false.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from audit_lifecycle.epistemic.serialize import canonical_digest

SCHEMA_VERSION = "recovery_execution_receipt.v0"
_LEAF_TYPES = (str, bool, int, float)
_SHA256_WIDTH = 64
_HEX = frozenset("0123456789abcdef")
_UNPINNED = frozenset(
    {
        "head",
        "latest",
        "main",
        "master",
        "origin/main",
        "origin/master",
        "current",
        "same as above",
        "production",
    }
)
_SCOPES = frozenset({"ARTIFACT_ONLY", "CONFIG", "SERVICE_RUNTIME"})
_OBSERVED = frozenset(
    {"OBSERVED_PASS", "OBSERVED_FAIL", "NOT_OBSERVED", "NOT_APPLICABLE"}
)
_ACTION_RESULTS = frozenset({"OBSERVED_PASS", "OBSERVED_FAIL", "NOT_OBSERVED"})
_ACTION_TYPES = frozenset({"RESTORE", "ROLLBACK"})
_BINDING_KINDS = frozenset({"content_digest", "git_commit", "immutable_version"})
_PRE_KINDS = frozenset(
    {"ARTIFACT", "CONFIG", "FREEZE_SHA256SUMS", "CAMPAIGN_INTEGRITY", "OTHER_BOUNDED"}
)
_CHECK_KINDS = frozenset(
    {
        "CONTENT_DIGEST_MATCH",
        "CONFIG_DIGEST_MATCH",
        "DATA_INTEGRITY",
        "AUTHORITY_BOUNDARY_CHECK",
        "SERVICE_HEALTH",
        "FUNCTIONAL_PROBE",
        "SIGNATURE_CHECK",
    }
)
_DIGEST_CHECKS = frozenset(
    {"CONTENT_DIGEST_MATCH", "CONFIG_DIGEST_MATCH", "DATA_INTEGRITY", "SIGNATURE_CHECK"}
)
_RUNTIME_CHECKS = frozenset({"SERVICE_HEALTH", "FUNCTIONAL_PROBE"})
_SEVERITIES = frozenset({"CRITICAL", "NONCRITICAL"})
_RISK_STATUSES = frozenset({"OPEN", "RESOLVED"})
_REVIEW_OUTCOMES = frozenset({"ACCEPT", "REJECT", "REQUEST_MORE_CHECKS"})
_IV_SOURCE_KINDS = frozenset(
    {
        "INDEPENDENT_VERIFICATION_PREFLIGHT",
        "EXTERNAL_WITNESS",
        "OTHER_BOUNDED",
    }
)
_AUTHORITY_FACTS = {
    "authority": False,
    "independent_evidence_admitted": False,
    "human_final": False,
    "r4_vector_eig_mutated": False,
}
_RECORD_REQUIRED = frozenset(
    {
        "recovery_session_id",
        "target_scope",
        "target_artifact_id",
        "target_environment",
        "pre_state",
        "stop",
        "isolation",
        "restore_target",
        "attempts",
    }
)
_RECORD_OPTIONAL = frozenset({"independent_verification_refs", "human_review"})
_PRE_REQUIRED = frozenset(
    {"evidence_id", "evidence_kind", "body", "event_order"}
)
_PRE_OPTIONAL = frozenset({"digest", "incident_note"})
_STOP_REQUIRED = frozenset(
    {"stop_id", "mechanism_kind", "body", "result", "event_order"}
)
_STOP_OPTIONAL = frozenset({"body_digest"})
_ISOLATION_REQUIRED = frozenset(
    {"isolation_id", "isolation_kind", "result", "event_order"}
)
_ISOLATION_OPTIONAL = frozenset({"body", "justification", "evidence_digest"})
_TARGET_REQUIRED = frozenset(
    {"target_id", "binding_kind", "binding_value", "source", "event_order"}
)
_TARGET_OPTIONAL = frozenset(
    {"body", "expected_digest", "approval_ref", "independent_verification_ref"}
)
_ATTEMPT_REQUIRED = frozenset(
    {
        "attempt_id",
        "action_type",
        "target_id",
        "target_binding_kind",
        "target_binding_value",
        "executor_id",
        "event_order",
        "result_token",
        "action_result",
        "changed_object_refs",
        "verification_checks",
    }
)
_ATTEMPT_OPTIONAL = frozenset(
    {"action_output_body", "action_output_digest", "unresolved_risks"}
)
_CHECK_REQUIRED = frozenset(
    {
        "check_id",
        "check_kind",
        "target",
        "expected",
        "result",
        "critical",
        "event_order",
    }
)
_CHECK_OPTIONAL = frozenset({"observed", "evidence_body", "evidence_digest"})
_RISK_REQUIRED = frozenset(
    {"risk_id", "statement", "severity", "status", "introduced_event_order"}
)
_RISK_OPTIONAL = frozenset({"resolved_event_order", "resolution_ref"})
_IV_REQUIRED = frozenset({"ref_id", "source_kind", "claim"})
_IV_OPTIONAL = frozenset({"receipt_digest", "evidence_digest"})
_REVIEW_REQUIRED = frozenset(
    {"selector_is_human", "review_target_digest", "review_outcome"}
)
_REVIEW_OPTIONAL = frozenset({"selection_note", "authority"})
_LIMITATIONS = (
    "restore execution",
    "rollback completion",
    "global recovered state",
    "independent verification not established",
    "independent evidence admission",
    "Human Final",
    "human verification",
    "key custody / ACL not established",
    "canonical status",
    "published status",
    "deployed status",
    "host mutation",
    "secret rotation",
)
_COT_ALIASES = frozenset(
    {
        "chainofthought",
        "privatereasoning",
        "hiddenreasoning",
        "scratchpad",
    }
)
_FORBIDDEN_ALIASES = frozenset(
    {
        "recovered",
        "restored",
        "verifiedrestore",
        "rollbackcomplete",
        "classification",
        "independentevidencecount",
        "admissionstatus",
        "structuralcandidate",
        "verificationkind",
        "claimsiwacceptance",
        "claimsindependentwitness",
        "humanfinal",
        "humanfinalstatus",
        "ishumanfinal",
        "createshumanfinal",
        "verified",
        "canonical",
        "published",
        "deployed",
        "vector",
        "eig",
        "knowngood",
        "proventrue",
        "humanreviewaccepted",
    }
)


class RecoveryExecutionError(ValueError):
    """Closed failure while deriving a recovery execution receipt."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


def _fail(code: str, message: str) -> None:
    raise RecoveryExecutionError(code, message)


def _alias(name: str) -> str:
    return "".join(char for char in name.lower() if char.isalnum())


def _snapshot(value: Any, depth: int = 0) -> Any:
    if depth > 32:
        _fail("RER_SOURCE_INVALID", "input is nested too deeply")
    if value is None or type(value) in _LEAF_TYPES:
        return value
    if isinstance(value, Mapping):
        copied: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                _fail("RER_SOURCE_INVALID", "mapping key must be a string")
            if key in copied:
                _fail("RER_SOURCE_INVALID", "mapping repeats a key")
            copied[key] = _snapshot(item, depth + 1)
        return copied
    if type(value) is list or type(value) is tuple:
        return [_snapshot(item, depth + 1) for item in value]
    _fail("RER_SOURCE_INVALID", "input is not plain JSON data")


def _require_mapping(value: Any, label: str) -> Mapping[str, Any]:
    if isinstance(value, bool) or not isinstance(value, Mapping):
        _fail("RER_SOURCE_INVALID", f"{label} must be a mapping")
    return value


def _keys(
    record: Mapping[str, Any],
    required: frozenset[str],
    optional: frozenset[str],
    code: str,
) -> None:
    unknown = set(record) - required - optional
    if unknown:
        _fail(code, "record has an unsupported field")
    if not required <= set(record):
        _fail(code, "record is missing a required field")


def _nonempty(value: Any, code: str, label: str) -> str:
    if type(value) is not str or not value.strip():
        _fail(code, f"{label} is missing")
    return value


def _unpinned(value: Any) -> bool:
    return type(value) is str and value.strip().lower() in _UNPINNED


def _identity(value: Any, code: str, label: str) -> str:
    text = _nonempty(value, code, label)
    if _unpinned(text):
        _fail(code, f"{label} is not a bound identity")
    return text


def _sha256(value: Any, code: str) -> str:
    if type(value) is not str or len(value) != _SHA256_WIDTH:
        _fail(code, "digest is not a bound sha256")
    if any(char not in _HEX for char in value):
        _fail(code, "digest is not a bound sha256")
    return value


def _digest(record: Any, code: str) -> str:
    try:
        return canonical_digest(record)
    except (TypeError, ValueError) as exc:
        if isinstance(exc, RecoveryExecutionError):
            raise
        _fail(code, "record cannot be canonicalized")
        raise AssertionError("closed") from exc


def _order(value: Any, code: str, label: str) -> int:
    if type(value) is not int:
        _fail(code, f"{label} is not an exact int")
    if value < 0:
        _fail(code, f"{label} is not a bound order")
    return value


def _plain_list(value: Any, code: str, label: str) -> list[Any]:
    if type(value) is not list:
        _fail(code, f"{label} must be a list")
    return value


def _bool(value: Any, code: str, label: str) -> bool:
    if type(value) is not bool:
        _fail(code, f"{label} is not an exact bool")
    return value


def _observed(value: Any, code: str, label: str) -> str:
    if value not in _OBSERVED:
        _fail(code, f"{label} is not a closed observation")
    return value


def _scan_cot(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if _alias(key) in _COT_ALIASES:
                _fail("RER_COT_FORBIDDEN", "hidden chain-of-thought is not stored")
            _scan_cot(item)
        return
    if type(value) is list:
        for item in value:
            _scan_cot(item)


def _reject_forbidden_names(names: set[str], code: str) -> None:
    for name in names:
        alias = _alias(name)
        if alias in _COT_ALIASES:
            _fail("RER_COT_FORBIDDEN", "hidden chain-of-thought is not stored")
        if alias in _FORBIDDEN_ALIASES:
            _fail(code, "caller cannot set recovery or authority assertions")


def _reject_record_forbidden(record: Mapping[str, Any]) -> None:
    _reject_forbidden_names(set(record), "RER_SCOPE_VIOLATION")


def _git_commit(value: Any) -> str:
    text = _identity(value, "RER_UNBOUND", "git_commit")
    if len(text) not in {40, 64} or any(char not in _HEX for char in text):
        _fail("RER_UNBOUND", "git_commit is not an immutable hex id")
    return text


def _register_order(orders: set[int], value: int) -> None:
    if value in orders:
        _fail("RER_LINEAGE_INVALID", "event_order repeats")
    orders.add(value)


def _bind_pre_state(raw: Any, orders: set[int]) -> list[dict[str, Any]]:
    rows = _plain_list(raw, "RER_SOURCE_INVALID", "pre_state")
    bound: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in rows:
        mapping = _require_mapping(item, "pre_state")
        _reject_record_forbidden(mapping)
        _keys(mapping, _PRE_REQUIRED, _PRE_OPTIONAL, "RER_SOURCE_INVALID")
        evidence_id = _identity(mapping.get("evidence_id"), "RER_UNBOUND", "evidence_id")
        if evidence_id in seen:
            _fail("RER_REPLAY", "pre_state evidence_id repeats")
        seen.add(evidence_id)
        kind = mapping.get("evidence_kind")
        if kind not in _PRE_KINDS:
            _fail("RER_SOURCE_INVALID", "pre_state evidence_kind is not closed")
        body = mapping.get("body")
        if body is None:
            _fail("RER_UNBOUND", "pre_state body is required")
        digest = _digest(body, "RER_UNBOUND")
        if "digest" in mapping:
            stated = _sha256(mapping.get("digest"), "RER_UNBOUND")
            if stated != digest:
                _fail("RER_UNBOUND", "pre_state digest does not match")
        event_order = _order(mapping.get("event_order"), "RER_LINEAGE_INVALID", "event_order")
        _register_order(orders, event_order)
        record = {
            "evidence_id": evidence_id,
            "evidence_kind": kind,
            "body": body,
            "digest": digest,
            "event_order": event_order,
        }
        if "incident_note" in mapping:
            record["incident_note"] = _nonempty(
                mapping.get("incident_note"),
                "RER_SOURCE_INVALID",
                "incident_note",
            )
        bound.append(record)
    return bound


def _bind_stop(raw: Any, orders: set[int]) -> dict[str, Any]:
    mapping = _require_mapping(raw, "stop")
    _reject_record_forbidden(mapping)
    _keys(mapping, _STOP_REQUIRED, _STOP_OPTIONAL, "RER_SOURCE_INVALID")
    body = mapping.get("body")
    if body is None:
        _fail("RER_UNBOUND", "stop body is required")
    digest = _digest(body, "RER_UNBOUND")
    if "body_digest" in mapping:
        stated = _sha256(mapping.get("body_digest"), "RER_UNBOUND")
        if stated != digest:
            _fail("RER_UNBOUND", "stop digest does not match")
    event_order = _order(mapping.get("event_order"), "RER_LINEAGE_INVALID", "event_order")
    _register_order(orders, event_order)
    return {
        "stop_id": _identity(mapping.get("stop_id"), "RER_UNBOUND", "stop_id"),
        "mechanism_kind": _nonempty(
            mapping.get("mechanism_kind"),
            "RER_SOURCE_INVALID",
            "mechanism_kind",
        ),
        "body": body,
        "body_digest": digest,
        "result": _observed(mapping.get("result"), "RER_SOURCE_INVALID", "stop result"),
        "event_order": event_order,
    }


def _bind_isolation(
    raw: Any,
    *,
    scope: str,
    stop_digest: str,
    orders: set[int],
) -> dict[str, Any]:
    mapping = _require_mapping(raw, "isolation")
    _reject_record_forbidden(mapping)
    _keys(mapping, _ISOLATION_REQUIRED, _ISOLATION_OPTIONAL, "RER_SOURCE_INVALID")
    result = _observed(mapping.get("result"), "RER_SOURCE_INVALID", "isolation result")
    event_order = _order(mapping.get("event_order"), "RER_LINEAGE_INVALID", "event_order")
    _register_order(orders, event_order)
    bound: dict[str, Any] = {
        "isolation_id": _identity(
            mapping.get("isolation_id"),
            "RER_UNBOUND",
            "isolation_id",
        ),
        "isolation_kind": _nonempty(
            mapping.get("isolation_kind"),
            "RER_SOURCE_INVALID",
            "isolation_kind",
        ),
        "result": result,
        "event_order": event_order,
    }
    if "body" in mapping:
        body = mapping.get("body")
        if body is None:
            _fail("RER_UNBOUND", "isolation body is invalid")
        digest = _digest(body, "RER_UNBOUND")
        if digest == stop_digest:
            _fail("RER_LINEAGE_INVALID", "stop and isolation cannot share one body")
        if "evidence_digest" in mapping:
            stated = _sha256(mapping.get("evidence_digest"), "RER_UNBOUND")
            if stated != digest:
                _fail("RER_UNBOUND", "isolation digest does not match")
        bound["body"] = body
        bound["evidence_digest"] = digest
    elif "evidence_digest" in mapping:
        _fail("RER_UNBOUND", "isolation digest requires a body")
    if "justification" in mapping:
        bound["justification"] = _nonempty(
            mapping.get("justification"),
            "RER_SOURCE_INVALID",
            "justification",
        )
    if result == "NOT_APPLICABLE":
        if scope == "SERVICE_RUNTIME":
            _fail("RER_LINEAGE_INVALID", "SERVICE_RUNTIME isolation cannot be N/A")
        if "justification" not in bound:
            _fail("RER_SOURCE_INVALID", "isolation N/A requires justification")
    if result == "OBSERVED_PASS" and "body" not in bound:
        _fail("RER_UNBOUND", "isolation PASS requires a body")
    return bound


def _bind_restore_target(raw: Any, orders: set[int]) -> dict[str, Any]:
    mapping = _require_mapping(raw, "restore_target")
    _reject_record_forbidden(mapping)
    _keys(mapping, _TARGET_REQUIRED, _TARGET_OPTIONAL, "RER_SOURCE_INVALID")
    kind = mapping.get("binding_kind")
    if kind not in _BINDING_KINDS:
        _fail("RER_SOURCE_INVALID", "binding_kind is not closed")
    event_order = _order(mapping.get("event_order"), "RER_LINEAGE_INVALID", "event_order")
    _register_order(orders, event_order)
    bound: dict[str, Any] = {
        "target_id": _identity(mapping.get("target_id"), "RER_UNBOUND", "target_id"),
        "binding_kind": kind,
        "source": _nonempty(mapping.get("source"), "RER_SOURCE_INVALID", "source"),
        "event_order": event_order,
    }
    if "approval_ref" in mapping:
        bound["approval_ref"] = _nonempty(
            mapping.get("approval_ref"),
            "RER_SOURCE_INVALID",
            "approval_ref",
        )
    if "independent_verification_ref" in mapping:
        bound["independent_verification_ref"] = _nonempty(
            mapping.get("independent_verification_ref"),
            "RER_SOURCE_INVALID",
            "independent_verification_ref",
        )
    if kind == "content_digest":
        if "body" not in mapping:
            _fail("RER_UNBOUND", "content_digest target requires a body")
        body = mapping.get("body")
        digest = _digest(body, "RER_UNBOUND")
        value = _sha256(mapping.get("binding_value"), "RER_UNBOUND")
        if value != digest:
            _fail("RER_UNBOUND", "restore target digest does not match")
        if "expected_digest" in mapping:
            expected = _sha256(mapping.get("expected_digest"), "RER_UNBOUND")
            if expected != digest:
                _fail("RER_UNBOUND", "expected_digest does not match")
        else:
            expected = digest
        bound["body"] = body
        bound["binding_value"] = digest
        bound["expected_digest"] = expected
    elif kind == "git_commit":
        bound["binding_value"] = _git_commit(mapping.get("binding_value"))
        if "body" in mapping:
            body = mapping.get("body")
            digest = _digest(body, "RER_UNBOUND")
            expected = _sha256(mapping.get("expected_digest"), "RER_UNBOUND")
            if expected != digest:
                _fail("RER_UNBOUND", "git_commit body digest does not match")
            bound["body"] = body
            bound["expected_digest"] = digest
        elif "expected_digest" in mapping:
            bound["expected_digest"] = _sha256(
                mapping.get("expected_digest"),
                "RER_UNBOUND",
            )
    else:
        bound["binding_value"] = _identity(
            mapping.get("binding_value"),
            "RER_UNBOUND",
            "immutable_version",
        )
        if "body" in mapping:
            body = mapping.get("body")
            digest = _digest(body, "RER_UNBOUND")
            expected = _sha256(mapping.get("expected_digest"), "RER_UNBOUND")
            if expected != digest:
                _fail("RER_UNBOUND", "immutable_version body digest does not match")
            bound["body"] = body
            bound["expected_digest"] = digest
        elif "expected_digest" in mapping:
            bound["expected_digest"] = _sha256(
                mapping.get("expected_digest"),
                "RER_UNBOUND",
            )
    return bound


def _derive_check_result(
    kind: str,
    *,
    expected: Any,
    observed: Any,
    body: Any,
    stated_result: str,
    pre_digests: set[str],
) -> tuple[str, Any, Any, str | None]:
    if kind == "AUTHORITY_BOUNDARY_CHECK":
        derived_observed = dict(_AUTHORITY_FACTS)
        if body is not None and body != derived_observed:
            _fail("RER_UNBOUND", "AUTHORITY_BOUNDARY_CHECK body is not code-derived")
        if observed is not None and observed != derived_observed:
            _fail("RER_UNBOUND", "AUTHORITY_BOUNDARY_CHECK cannot be forced by text")
        if expected is not None and expected != derived_observed:
            _fail("RER_UNBOUND", "AUTHORITY_BOUNDARY_CHECK cannot be forced by text")
        if stated_result == "OBSERVED_FAIL":
            return "OBSERVED_FAIL", derived_observed, derived_observed, _digest(
                derived_observed, "RER_UNBOUND"
            )
        if stated_result in {"NOT_OBSERVED", "NOT_APPLICABLE"}:
            return stated_result, expected, derived_observed, None
        return (
            "OBSERVED_PASS",
            derived_observed,
            derived_observed,
            _digest(derived_observed, "RER_UNBOUND"),
        )
    evidence_digest = None
    if body is not None:
        evidence_digest = _digest(body, "RER_UNBOUND")
        if evidence_digest in pre_digests:
            _fail("RER_LINEAGE_INVALID", "pre-state evidence cannot be reused as post-check")
    if kind in _DIGEST_CHECKS:
        if body is None:
            if stated_result == "OBSERVED_PASS":
                _fail("RER_UNBOUND", "digest check PASS requires a body")
            return stated_result, expected, observed, evidence_digest
        actual = evidence_digest
        expected_digest = expected
        if type(expected) is str:
            expected_digest = _sha256(expected, "RER_UNBOUND")
        else:
            _fail("RER_UNBOUND", "digest check expected must be sha256")
        if observed is not None:
            stated_obs = _sha256(observed, "RER_UNBOUND")
            if stated_obs != actual:
                _fail("RER_UNBOUND", "observed digest does not match body")
        derived = "OBSERVED_PASS" if actual == expected_digest else "OBSERVED_FAIL"
        if stated_result == "OBSERVED_PASS" and derived != "OBSERVED_PASS":
            _fail("RER_UNBOUND", "caller cannot force OBSERVED_PASS")
        if stated_result in {"NOT_OBSERVED", "NOT_APPLICABLE"}:
            return stated_result, expected_digest, actual, evidence_digest
        return derived, expected_digest, actual, evidence_digest
    if kind in _RUNTIME_CHECKS:
        if stated_result == "OBSERVED_PASS":
            if body is None:
                _fail("RER_UNBOUND", "runtime PASS requires a body")
            if observed != expected:
                _fail("RER_UNBOUND", "runtime observed does not match expected")
            return "OBSERVED_PASS", expected, observed, evidence_digest
        if stated_result == "NOT_OBSERVED":
            return "NOT_OBSERVED", expected, observed, evidence_digest
        return stated_result, expected, observed, evidence_digest
    return stated_result, expected, observed, evidence_digest


def _bind_check(
    raw: Mapping[str, Any],
    *,
    attempt_order: int,
    known_ids: set[str],
    check_replays: dict[tuple[str, str, str], str],
    pre_digests: set[str],
    orders: set[int],
    known_digests: set[str],
) -> dict[str, Any]:
    _reject_record_forbidden(raw)
    _keys(raw, _CHECK_REQUIRED, _CHECK_OPTIONAL, "RER_SOURCE_INVALID")
    check_id = _identity(raw.get("check_id"), "RER_UNBOUND", "check_id")
    if check_id in known_ids:
        _fail("RER_REPLAY", "check_id repeats")
    known_ids.add(check_id)
    kind = raw.get("check_kind")
    if kind not in _CHECK_KINDS:
        _fail("RER_SOURCE_INVALID", "check_kind is not closed")
    stated = _observed(raw.get("result"), "RER_SOURCE_INVALID", "check result")
    event_order = _order(raw.get("event_order"), "RER_LINEAGE_INVALID", "event_order")
    if event_order <= attempt_order:
        _fail("RER_LINEAGE_INVALID", "verification cannot precede restore")
    _register_order(orders, event_order)
    critical = _bool(raw.get("critical"), "RER_SOURCE_INVALID", "critical")
    target = _nonempty(raw.get("target"), "RER_SOURCE_INVALID", "check target")
    body = raw.get("evidence_body") if "evidence_body" in raw else None
    result, expected, observed, evidence_digest = _derive_check_result(
        kind,
        expected=raw.get("expected"),
        observed=raw.get("observed") if "observed" in raw else None,
        body=body,
        stated_result=stated,
        pre_digests=pre_digests,
    )
    if "evidence_digest" in raw:
        stated_digest = _sha256(raw.get("evidence_digest"), "RER_UNBOUND")
        if evidence_digest is None or stated_digest != evidence_digest:
            _fail("RER_UNBOUND", "check evidence digest does not match")
    if evidence_digest is not None:
        replay_key = (kind, target, evidence_digest)
        if replay_key in check_replays:
            _fail("RER_REPLAY", "check evidence repeats under a new identity")
        check_replays[replay_key] = check_id
        known_digests.add(evidence_digest)
    bound: dict[str, Any] = {
        "check_id": check_id,
        "check_kind": kind,
        "target": target,
        "expected": expected,
        "observed": observed,
        "result": result,
        "critical": critical,
        "event_order": event_order,
    }
    if body is not None:
        bound["evidence_body"] = body
    if evidence_digest is not None:
        bound["evidence_digest"] = evidence_digest
    return bound


def _bind_risk(
    raw: Mapping[str, Any],
    *,
    known_ids: set[str],
    known_digests: set[str],
    prior_open: Mapping[str, Mapping[str, Any]],
    attempt_order: int,
) -> dict[str, Any]:
    _reject_record_forbidden(raw)
    _keys(raw, _RISK_REQUIRED, _RISK_OPTIONAL, "RER_SOURCE_INVALID")
    risk_id = _identity(raw.get("risk_id"), "RER_UNBOUND", "risk_id")
    if risk_id in known_ids:
        _fail("RER_REPLAY", "risk_id repeats")
    known_ids.add(risk_id)
    severity = raw.get("severity")
    if severity not in _SEVERITIES:
        _fail("RER_SOURCE_INVALID", "risk severity is not closed")
    status = raw.get("status")
    if status not in _RISK_STATUSES:
        _fail("RER_SOURCE_INVALID", "risk status is not closed")
    introduced = _order(
        raw.get("introduced_event_order"),
        "RER_LINEAGE_INVALID",
        "introduced_event_order",
    )
    record: dict[str, Any] = {
        "risk_id": risk_id,
        "statement": _nonempty(raw.get("statement"), "RER_SOURCE_INVALID", "statement"),
        "severity": severity,
        "status": status,
        "introduced_event_order": introduced,
    }
    if status == "RESOLVED":
        resolved = _order(
            raw.get("resolved_event_order"),
            "RER_LINEAGE_INVALID",
            "resolved_event_order",
        )
        if resolved < introduced or resolved > attempt_order:
            _fail("RER_LINEAGE_INVALID", "risk resolution is not causal")
        ref = _sha256(raw.get("resolution_ref"), "RER_UNBOUND")
        if ref not in known_digests:
            _fail("RER_UNBOUND", "resolution_ref is not a known digest")
        record["resolved_event_order"] = resolved
        record["resolution_ref"] = ref
        if risk_id not in prior_open and introduced == resolved:
            pass
    else:
        if "resolved_event_order" in raw or "resolution_ref" in raw:
            _fail("RER_SOURCE_INVALID", "OPEN risk cannot name a resolver")
    return record


def _carry_risks(
    current: dict[str, dict[str, Any]],
    prior_open: Mapping[str, Mapping[str, Any]],
) -> None:
    missing = set(prior_open) - set(current)
    if missing:
        _fail("RER_RISK_DROPPED", "open risk was silently dropped")


def _action_material(record: Mapping[str, Any]) -> dict[str, Any]:
    material = {
        "action_type": record["action_type"],
        "target_binding_kind": record["target_binding_kind"],
        "target_binding_value": record["target_binding_value"],
        "result_token": record["result_token"],
        "changed_object_refs": record["changed_object_refs"],
        "action_result": record["action_result"],
    }
    if "action_output_digest" in record:
        material["action_output_digest"] = record["action_output_digest"]
    return material


def _bind_attempt(
    raw: Mapping[str, Any],
    *,
    restore_target: Mapping[str, Any],
    pre_digests: set[str],
    pre_max_order: int | None,
    stop_order: int,
    isolation_order: int,
    target_order: int,
    prior_open: dict[str, dict[str, Any]],
    attempt_ids: set[str],
    action_replays: dict[str, str],
    orders: set[int],
    known_digests: set[str],
) -> dict[str, Any]:
    _reject_record_forbidden(raw)
    _keys(raw, _ATTEMPT_REQUIRED, _ATTEMPT_OPTIONAL, "RER_SOURCE_INVALID")
    attempt_id = _identity(raw.get("attempt_id"), "RER_UNBOUND", "attempt_id")
    if attempt_id in attempt_ids:
        _fail("RER_REPLAY", "attempt_id repeats")
    attempt_ids.add(attempt_id)
    action_type = raw.get("action_type")
    if action_type not in _ACTION_TYPES:
        _fail("RER_SOURCE_INVALID", "action_type is not closed")
    action_result = raw.get("action_result")
    if action_result not in _ACTION_RESULTS:
        _fail("RER_SOURCE_INVALID", "action_result is not closed")
    event_order = _order(raw.get("event_order"), "RER_LINEAGE_INVALID", "event_order")
    _register_order(orders, event_order)
    if pre_max_order is not None and event_order <= pre_max_order:
        _fail("RER_LINEAGE_INVALID", "pre_state must precede restore")
    if event_order <= stop_order or event_order <= isolation_order:
        _fail("RER_LINEAGE_INVALID", "stop/isolation must precede restore")
    if event_order <= target_order:
        _fail("RER_LINEAGE_INVALID", "restore target must precede restore")
    target_id = _identity(raw.get("target_id"), "RER_UNBOUND", "target_id")
    if target_id != restore_target["target_id"]:
        _fail("RER_UNBOUND", "attempt target_id drifted")
    kind = raw.get("target_binding_kind")
    value = raw.get("target_binding_value")
    if kind != restore_target["binding_kind"]:
        _fail("RER_UNBOUND", "attempt target binding drifted")
    if value != restore_target["binding_value"]:
        _fail("RER_UNBOUND", "attempt target digest drifted")
    refs_raw = _plain_list(
        raw.get("changed_object_refs"),
        "RER_SOURCE_INVALID",
        "changed_object_refs",
    )
    refs = [
        _nonempty(item, "RER_SOURCE_INVALID", "changed_object_ref") for item in refs_raw
    ]
    bound: dict[str, Any] = {
        "attempt_id": attempt_id,
        "action_type": action_type,
        "target_id": target_id,
        "target_binding_kind": kind,
        "target_binding_value": restore_target["binding_value"],
        "executor_id": _nonempty(raw.get("executor_id"), "RER_SOURCE_INVALID", "executor_id"),
        "event_order": event_order,
        "result_token": _nonempty(
            raw.get("result_token"),
            "RER_SOURCE_INVALID",
            "result_token",
        ),
        "action_result": action_result,
        "changed_object_refs": refs,
    }
    if "action_output_body" in raw:
        output = raw.get("action_output_body")
        digest = _digest(output, "RER_UNBOUND")
        if "action_output_digest" in raw:
            stated = _sha256(raw.get("action_output_digest"), "RER_UNBOUND")
            if stated != digest:
                _fail("RER_UNBOUND", "action output digest does not match")
        bound["action_output_body"] = output
        bound["action_output_digest"] = digest
        known_digests.add(digest)
    elif "action_output_digest" in raw:
        _fail("RER_UNBOUND", "action output digest requires a body")
    material = _digest(_action_material(bound), "RER_UNBOUND")
    if material in action_replays:
        _fail("RER_REPLAY", "action record repeats under a new identity")
    action_replays[material] = attempt_id
    bound["action_digest"] = material
    known_digests.add(material)
    check_rows = _plain_list(
        raw.get("verification_checks"),
        "RER_SOURCE_INVALID",
        "verification_checks",
    )
    checks: list[dict[str, Any]] = []
    check_ids: set[str] = set()
    check_replays: dict[tuple[str, str, str], str] = {}
    for item in check_rows:
        checks.append(
            _bind_check(
                _require_mapping(item, "check"),
                attempt_order=event_order,
                known_ids=check_ids,
                check_replays=check_replays,
                pre_digests=pre_digests,
                orders=orders,
                known_digests=known_digests,
            )
        )
    checks.sort(key=lambda item: item["event_order"])
    bound["verification_checks"] = checks
    risk_rows = []
    if "unresolved_risks" in raw:
        risk_rows = _plain_list(
            raw.get("unresolved_risks"),
            "RER_SOURCE_INVALID",
            "unresolved_risks",
        )
    risks: dict[str, dict[str, Any]] = {}
    risk_ids: set[str] = set()
    for item in risk_rows:
        record = _bind_risk(
            _require_mapping(item, "risk"),
            known_ids=risk_ids,
            known_digests=known_digests,
            prior_open=prior_open,
            attempt_order=event_order,
        )
        risks[record["risk_id"]] = record
    _carry_risks(risks, prior_open)
    bound["unresolved_risks"] = list(risks.values())
    return bound


def _bind_iv_refs(raw: Any, known_ids: set[str]) -> list[dict[str, Any]]:
    if raw is None:
        return []
    rows = _plain_list(raw, "RER_SOURCE_INVALID", "independent_verification_refs")
    bound: list[dict[str, Any]] = []
    for item in rows:
        mapping = _require_mapping(item, "independent_verification_ref")
        _reject_record_forbidden(mapping)
        _keys(mapping, _IV_REQUIRED, _IV_OPTIONAL, "RER_SOURCE_INVALID")
        ref_id = _identity(mapping.get("ref_id"), "RER_UNBOUND", "ref_id")
        if ref_id in known_ids:
            _fail("RER_REPLAY", "independent verification ref_id repeats")
        known_ids.add(ref_id)
        source_kind = mapping.get("source_kind")
        if source_kind not in _IV_SOURCE_KINDS:
            _fail("RER_SOURCE_INVALID", "independent verification source_kind is not closed")
        receipt_digest = None
        evidence_digest = None
        if "receipt_digest" in mapping:
            receipt_digest = _sha256(mapping.get("receipt_digest"), "RER_UNBOUND")
        if "evidence_digest" in mapping:
            evidence_digest = _sha256(mapping.get("evidence_digest"), "RER_UNBOUND")
        if receipt_digest is None and evidence_digest is None:
            _fail("RER_UNBOUND", "independent verification label is not a bound digest")
        if (
            receipt_digest is not None
            and evidence_digest is not None
            and receipt_digest != evidence_digest
        ):
            _fail("RER_UNBOUND", "independent verification digests conflict")
        record = {
            "ref_id": ref_id,
            "source_kind": source_kind,
            "claim": _nonempty(mapping.get("claim"), "RER_SOURCE_INVALID", "claim"),
        }
        if receipt_digest is not None:
            record["receipt_digest"] = receipt_digest
        if evidence_digest is not None:
            record["evidence_digest"] = evidence_digest
        bound.append(record)
    return bound


def _required_kinds(scope: str) -> set[str]:
    required = {"CONTENT_DIGEST_MATCH", "AUTHORITY_BOUNDARY_CHECK"}
    if scope == "CONFIG":
        required.add("CONFIG_DIGEST_MATCH")
    return required


def _runtime_satisfied(checks: list[Mapping[str, Any]]) -> str | None:
    for item in checks:
        if (
            item["check_kind"] in _RUNTIME_CHECKS
            and item["critical"] is True
            and item["result"] == "OBSERVED_PASS"
        ):
            return "PASS"
        if (
            item["check_kind"] in _RUNTIME_CHECKS
            and item["critical"] is True
            and item["result"] == "OBSERVED_FAIL"
        ):
            return "FAIL"
    return None


def _signature_state(checks: list[Mapping[str, Any]]) -> str | None:
    for item in checks:
        if item["check_kind"] == "SIGNATURE_CHECK":
            return item["result"]
    return None


def _open_risks(attempts: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    if not attempts:
        return []
    return [
        dict(item)
        for item in attempts[-1]["unresolved_risks"]
        if item["status"] == "OPEN"
    ]


def _classify(
    *,
    scope: str,
    pre_state: list[Mapping[str, Any]],
    stop: Mapping[str, Any],
    isolation: Mapping[str, Any],
    attempts: list[Mapping[str, Any]],
) -> str:
    if not pre_state or not attempts:
        return "NOT_RECOVERED"
    latest = attempts[-1]
    if latest["action_result"] != "OBSERVED_PASS":
        return "RESTORE_ATTEMPTED"
    if stop["result"] == "OBSERVED_FAIL" or isolation["result"] == "OBSERVED_FAIL":
        return "VERIFICATION_FAILED"
    if stop["result"] != "OBSERVED_PASS":
        return "RESTORED_UNVERIFIED"
    if scope == "SERVICE_RUNTIME":
        if isolation["result"] != "OBSERVED_PASS":
            return "RESTORED_UNVERIFIED"
    elif isolation["result"] not in {"OBSERVED_PASS", "NOT_APPLICABLE"}:
        return "RESTORED_UNVERIFIED"
    checks = latest["verification_checks"]
    by_kind: dict[str, list[Mapping[str, Any]]] = {}
    for item in checks:
        by_kind.setdefault(item["check_kind"], []).append(item)
    required = _required_kinds(scope)
    for kind in required:
        rows = by_kind.get(kind) or []
        critical_rows = [item for item in rows if item["critical"] is True]
        if any(item["result"] == "OBSERVED_FAIL" for item in critical_rows):
            return "VERIFICATION_FAILED"
        if not critical_rows or any(
            item["result"] != "OBSERVED_PASS" for item in critical_rows
        ):
            return "RESTORED_UNVERIFIED"
    if any(
        item["critical"] is True and item["result"] == "OBSERVED_FAIL" for item in checks
    ):
        return "VERIFICATION_FAILED"
    if scope == "SERVICE_RUNTIME":
        runtime = _runtime_satisfied(checks)
        if runtime == "FAIL":
            return "VERIFICATION_FAILED"
        if runtime != "PASS":
            return "RESTORED_UNVERIFIED"
        signature = _signature_state(checks)
        if signature == "OBSERVED_FAIL":
            return "VERIFICATION_FAILED"
        if signature != "OBSERVED_PASS":
            if not any(
                item["severity"] == "CRITICAL" and item["status"] == "OPEN"
                for item in latest["unresolved_risks"]
            ):
                return "RESTORED_UNVERIFIED"
    if any(
        item["severity"] == "CRITICAL" and item["status"] == "OPEN"
        for item in latest["unresolved_risks"]
    ):
        return "RESTORED_UNVERIFIED"
    return "RECOVERED_BOUNDED"


def _review_target(
    *,
    latest: Mapping[str, Any] | None,
    classification: str,
    open_critical: list[Mapping[str, Any]],
) -> str:
    checks = []
    attempt_digest = None
    attempt_id = None
    if latest is not None:
        attempt_id = latest["attempt_id"]
        attempt_digest = latest["action_digest"]
        checks = [
            {
                "check_id": item["check_id"],
                "check_kind": item["check_kind"],
                "result": item["result"],
                "evidence_digest": item.get("evidence_digest"),
            }
            for item in latest["verification_checks"]
        ]
    payload = {
        "latest_attempt_id": attempt_id,
        "latest_attempt_digest": attempt_digest,
        "verification_summary_digest": _digest(checks, "RER_UNBOUND"),
        "unresolved_critical_risk_summary_digest": _digest(
            [
                {
                    "risk_id": item["risk_id"],
                    "statement": item["statement"],
                    "severity": item["severity"],
                }
                for item in open_critical
            ],
            "RER_UNBOUND",
        ),
        "classification": classification,
    }
    return _digest(payload, "RER_UNBOUND")


def _bind_human_review(
    raw: Any,
    *,
    expected_digest: str,
) -> dict[str, Any] | None:
    if raw is None:
        return None
    mapping = _require_mapping(raw, "human_review")
    _reject_record_forbidden(mapping)
    _keys(mapping, _REVIEW_REQUIRED, _REVIEW_OPTIONAL, "RER_SOURCE_INVALID")
    if mapping.get("authority", False) is not False:
        _fail("RER_SCOPE_VIOLATION", "human review cannot carry authority")
    if mapping.get("selector_is_human") is not True or type(
        mapping.get("selector_is_human")
    ) is not bool:
        _fail("RER_UNBOUND", "selector_is_human must be true")
    stated = _sha256(mapping.get("review_target_digest"), "RER_UNBOUND")
    if stated != expected_digest:
        _fail("RER_UNBOUND", "review_target_digest does not match")
    outcome = mapping.get("review_outcome")
    if outcome not in _REVIEW_OUTCOMES:
        _fail("RER_SOURCE_INVALID", "review_outcome is not closed")
    bound: dict[str, Any] = {
        "selector_is_human": True,
        "review_target_digest": expected_digest,
        "review_outcome": outcome,
        "authority": False,
    }
    if "selection_note" in mapping:
        note = mapping.get("selection_note")
        if type(note) is not str:
            _fail("RER_SOURCE_INVALID", "selection_note must be a string")
        bound["selection_note"] = note
    return bound


def _environment(raw: Any) -> dict[str, Any]:
    mapping = _require_mapping(raw, "target_environment")
    _reject_record_forbidden(mapping)
    copied = dict(mapping)
    copied["environment_digest"] = _digest(mapping, "RER_UNBOUND")
    return copied


def build_recovery_execution_receipt(
    record: Mapping[str, Any],
    **forbidden: Any,
) -> dict[str, Any]:
    """Return a non-authoritative recovery execution receipt.

    recovered remains false. Bounded success lives only in classification.
    """
    if forbidden:
        _reject_forbidden_names(set(forbidden), "RER_SCOPE_VIOLATION")
        _fail("RER_SOURCE_INVALID", "unexpected recovery execution input")
    mapping = _snapshot(_require_mapping(record, "record"))
    _scan_cot(mapping)
    _reject_forbidden_names(set(mapping), "RER_SCOPE_VIOLATION")
    _keys(mapping, _RECORD_REQUIRED, _RECORD_OPTIONAL, "RER_SOURCE_INVALID")
    session_id = _nonempty(
        mapping.get("recovery_session_id"),
        "RER_SOURCE_INVALID",
        "recovery_session_id",
    )
    scope = mapping.get("target_scope")
    if scope not in _SCOPES:
        _fail("RER_SOURCE_INVALID", "target_scope is not closed")
    artifact_id = _nonempty(
        mapping.get("target_artifact_id"),
        "RER_SOURCE_INVALID",
        "target_artifact_id",
    )
    environment = _environment(mapping.get("target_environment"))
    orders: set[int] = set()
    pre_state = _bind_pre_state(mapping.get("pre_state"), orders)
    pre_state.sort(key=lambda item: item["event_order"])
    stop = _bind_stop(mapping.get("stop"), orders)
    isolation = _bind_isolation(
        mapping.get("isolation"),
        scope=scope,
        stop_digest=stop["body_digest"],
        orders=orders,
    )
    restore_target = _bind_restore_target(mapping.get("restore_target"), orders)
    attempt_rows = _plain_list(mapping.get("attempts"), "RER_SOURCE_INVALID", "attempts")
    pending: list[tuple[int, Mapping[str, Any]]] = []
    for item in attempt_rows:
        attempt_map = _require_mapping(item, "attempt")
        pending.append(
            (
                _order(
                    attempt_map.get("event_order"),
                    "RER_LINEAGE_INVALID",
                    "event_order",
                ),
                attempt_map,
            )
        )
    pending.sort(key=lambda pair: pair[0])
    attempts: list[dict[str, Any]] = []
    attempt_ids: set[str] = set()
    action_replays: dict[str, str] = {}
    known_digests = {item["digest"] for item in pre_state}
    known_digests.add(stop["body_digest"])
    if "evidence_digest" in isolation:
        known_digests.add(isolation["evidence_digest"])
    if "expected_digest" in restore_target:
        known_digests.add(restore_target["expected_digest"])
    prior_open: dict[str, dict[str, Any]] = {}
    pre_max = max((item["event_order"] for item in pre_state), default=None)
    pre_digests = {item["digest"] for item in pre_state}
    for _, item in pending:
        bound = _bind_attempt(
            _require_mapping(item, "attempt"),
            restore_target=restore_target,
            pre_digests=pre_digests,
            pre_max_order=pre_max,
            stop_order=stop["event_order"],
            isolation_order=isolation["event_order"],
            target_order=restore_target["event_order"],
            prior_open=prior_open,
            attempt_ids=attempt_ids,
            action_replays=action_replays,
            orders=orders,
            known_digests=known_digests,
        )
        if scope == "SERVICE_RUNTIME" and bound["action_result"] == "OBSERVED_PASS":
            if _signature_state(bound["verification_checks"]) != "OBSERVED_PASS":
                has_critical_open = any(
                    risk["severity"] == "CRITICAL" and risk["status"] == "OPEN"
                    for risk in bound["unresolved_risks"]
                )
                has_custody_id = any(
                    risk["risk_id"] == "custody-gap" for risk in bound["unresolved_risks"]
                )
                if not has_critical_open and not has_custody_id:
                    bound["unresolved_risks"].append(
                        {
                            "risk_id": "custody-gap",
                            "statement": "key custody / ACL / signing not established",
                            "severity": "CRITICAL",
                            "status": "OPEN",
                            "introduced_event_order": bound["event_order"],
                        }
                    )
        attempts.append(bound)
        prior_open = {
            item["risk_id"]: item
            for item in bound["unresolved_risks"]
            if item["status"] == "OPEN"
        }
    if orders and sorted(orders) != list(range(len(orders))):
        _fail("RER_LINEAGE_INVALID", "event_order is not contiguous from 0")
    attempts.sort(key=lambda item: item["event_order"])
    classification = _classify(
        scope=scope,
        pre_state=pre_state,
        stop=stop,
        isolation=isolation,
        attempts=attempts,
    )
    latest = attempts[-1] if attempts else None
    open_all = _open_risks(attempts)
    open_critical = [item for item in open_all if item["severity"] == "CRITICAL"]
    review_digest = _review_target(
        latest=latest,
        classification=classification,
        open_critical=open_critical,
    )
    human_review = _bind_human_review(
        mapping.get("human_review"),
        expected_digest=review_digest,
    )
    iv_refs = _bind_iv_refs(mapping.get("independent_verification_refs"), set())
    limitations = list(_LIMITATIONS)
    if iv_refs:
        limitations = [
            item
            for item in limitations
            if item != "independent verification not established"
        ]
        limitations.append("independent verification cited but not admitted")
    for item in open_all:
        if item["severity"] == "NONCRITICAL":
            note = f"noncritical open risk: {item['statement']}"
            if note not in limitations:
                limitations.append(note)
    receipt: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "authority": False,
        "recovered": False,
        "recovery_session_id": session_id,
        "target_scope": scope,
        "target_artifact_id": artifact_id,
        "target_environment": environment,
        "pre_state": pre_state,
        "stop": stop,
        "isolation": isolation,
        "restore_target": restore_target,
        "attempts": attempts,
        "independent_verification_refs": iv_refs,
        "unresolved_risks": open_all,
        "classification": classification,
        "limitations": limitations,
    }
    if human_review is not None:
        receipt["human_review"] = human_review
    receipt["receipt_digest"] = _digest(
        {key: value for key, value in receipt.items()},
        "RER_SOURCE_INVALID",
    )
    return receipt
