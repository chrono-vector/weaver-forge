"""Non-authority invariants for R4-A epistemic records."""

from __future__ import annotations

from typing import Any, Mapping


class AuthorityViolation(ValueError):
    """Raised when epistemic metadata attempts to claim or imply authority."""


def assert_authority_false(record: Mapping[str, Any], *, field: str = "authority") -> None:
    """R4-A records MUST carry explicit authority:false."""
    if field not in record:
        raise AuthorityViolation(f"missing required {field}=false on epistemic record")
    if record[field] is not False:
        raise AuthorityViolation(
            f"epistemic records require {field}=false; got {record[field]!r}"
        )


def assert_confidence_cannot_authorize(record: Mapping[str, Any]) -> None:
    """Confidence is advisory only — never an authorization signal."""
    if record.get("confidence_authorizes") is True:
        raise AuthorityViolation("confidence cannot authorize execution or promotion")
    if record.get("authorized_by_confidence") is True:
        raise AuthorityViolation("confidence cannot authorize execution or promotion")
    conf = record.get("confidence")
    if isinstance(conf, Mapping) and conf.get("authorizes") is True:
        raise AuthorityViolation("confidence cannot authorize execution or promotion")


def assert_epistemic_cannot_create_human_final(record: Mapping[str, Any]) -> None:
    """Epistemic status / metadata must never create Human Final."""
    forbidden_true = (
        "creates_human_final",
        "human_final",
        "is_human_final",
        "promotes_to_human_final",
    )
    for key in forbidden_true:
        if record.get(key) is True:
            raise AuthorityViolation("epistemic metadata cannot create Human Final")
    status = str(record.get("epistemic_status") or "")
    if status.upper() in {"HUMAN_FINAL", "FINAL"}:
        raise AuthorityViolation("epistemic_status cannot be Human Final")


def assert_epistemic_cannot_change_execution_authorization(
    record: Mapping[str, Any],
) -> None:
    """Epistemic metadata must never change execution authorization."""
    forbidden_true = (
        "authorizes_execution",
        "execution_authorized",
        "grants_execution",
        "changes_execution_authorization",
        "execution_permission",
    )
    for key in forbidden_true:
        val = record.get(key)
        if val is True or (isinstance(val, str) and val.upper() in {"GRANT", "ALLOW", "AUTHORIZED"}):
            raise AuthorityViolation(
                "epistemic metadata cannot change execution authorization"
            )
    if record.get("authority") is True:
        raise AuthorityViolation(
            "epistemic metadata cannot change execution authorization"
        )


def enforce_non_authority(record: Mapping[str, Any]) -> None:
    """Run the full non-authority battery."""
    assert_authority_false(record)
    assert_confidence_cannot_authorize(record)
    assert_epistemic_cannot_create_human_final(record)
    assert_epistemic_cannot_change_execution_authorization(record)
