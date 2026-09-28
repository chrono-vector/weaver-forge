"""Non-authority invariants for R4-A epistemic records.

The sole allowed authority field is top-level:
  authority: false

Reserved authority/decision structural keys are categorically forbidden at any
nested location regardless of value. Matching uses structural-key normalization
(case / separator variants). Do not scan arbitrary prose string contents.
"""

from __future__ import annotations

import re
from typing import Any, Mapping


def _normalize_structural_key(key: str) -> str:
    """Normalize case and separators for structural-key comparison."""
    return re.sub(r"[^a-z0-9]", "", key.lower())


# Reserved authority / decision structural keys (canonical underscore form).
# Presence of the key itself imports an authority/decision namespace.
_RESERVED_AUTHORITY_DECISION_KEYS = frozenset(
    {
        "authority",
        "authorized",
        "execution_authorized",
        "execution_permission",
        "human_final",
        "human_final_status",
        "final_accepted",
        "vector_authorized",
        "eig_authorized",
        "weaver_pass",
        "weaver_fail",
        "weaver_status",
        "final_status",
        "approval",
        "approved",
        # Additional authority-implication keys retained from R4-A contract.
        "authorizes_execution",
        "grants_execution",
        "changes_execution_authorization",
        "creates_human_final",
        "is_human_final",
        "promotes_to_human_final",
        "confidence_authorizes",
        "authorized_by_confidence",
    }
)

_NORMALIZED_RESERVED_KEYS = frozenset(
    _normalize_structural_key(k) for k in _RESERVED_AUTHORITY_DECISION_KEYS
)


class AuthorityViolation(ValueError):
    """Raised when epistemic metadata attempts to claim or imply authority."""


def assert_authority_false(record: Mapping[str, Any], *, field: str = "authority") -> None:
    """R4-A records MUST carry explicit authority:false (Boolean)."""
    if field not in record:
        raise AuthorityViolation(f"missing required {field}=false on epistemic record")
    if record[field] is not False:
        raise AuthorityViolation(
            f"epistemic records require {field}=false; got {record[field]!r}"
        )


def _key_is_reserved_authority_decision(key: Any) -> bool:
    if not isinstance(key, str):
        return False
    return _normalize_structural_key(key) in _NORMALIZED_RESERVED_KEYS


def assert_confidence_cannot_authorize(record: Mapping[str, Any]) -> None:
    """Confidence is advisory only — never an authorization signal."""
    for key in ("confidence_authorizes", "authorized_by_confidence"):
        if key in record:
            raise AuthorityViolation("confidence cannot authorize execution or promotion")
    conf = record.get("confidence")
    if isinstance(conf, Mapping) and (
        "authorizes" in conf or conf.get("authorizes") is True
    ):
        raise AuthorityViolation("confidence cannot authorize execution or promotion")


def assert_epistemic_cannot_create_human_final(record: Mapping[str, Any]) -> None:
    """Epistemic status / metadata must never create Human Final."""
    for key in (
        "creates_human_final",
        "human_final",
        "is_human_final",
        "promotes_to_human_final",
    ):
        if key in record:
            raise AuthorityViolation("epistemic metadata cannot create Human Final")
    status = record.get("epistemic_status")
    if isinstance(status, str) and status.upper() in {"HUMAN_FINAL", "FINAL"}:
        raise AuthorityViolation("epistemic_status cannot be Human Final")


def assert_epistemic_cannot_change_execution_authorization(
    record: Mapping[str, Any],
) -> None:
    """Epistemic metadata must never change execution authorization."""
    for key in (
        "authorizes_execution",
        "execution_authorized",
        "grants_execution",
        "changes_execution_authorization",
        "execution_permission",
    ):
        if key in record:
            raise AuthorityViolation(
                "epistemic metadata cannot change execution authorization"
            )
    if record.get("authority") is True:
        raise AuthorityViolation(
            "epistemic metadata cannot change execution authorization"
        )


def _walk_reject_reserved_keys(node: Any, *, path: str, is_root: bool) -> None:
    if isinstance(node, Mapping):
        for key, value in node.items():
            child_path = f"{path}.{key}" if path else str(key)
            if _key_is_reserved_authority_decision(key):
                # Sole allowed: top-level authority:false.
                if (
                    is_root
                    and isinstance(key, str)
                    and _normalize_structural_key(key) == "authority"
                    and value is False
                ):
                    pass
                else:
                    raise AuthorityViolation(
                        "reserved authority/decision structural key "
                        f"forbidden at {child_path}"
                    )
            if isinstance(value, (Mapping, list, tuple)) and not isinstance(
                value, (str, bytes)
            ):
                _walk_reject_reserved_keys(value, path=child_path, is_root=False)
    elif isinstance(node, (list, tuple)) and not isinstance(node, (str, bytes)):
        for i, item in enumerate(node):
            _walk_reject_reserved_keys(item, path=f"{path}[{i}]", is_root=False)


def enforce_non_authority(record: Mapping[str, Any]) -> None:
    """Run the full non-authority battery, including categorical nested key checks."""
    assert_authority_false(record)
    assert_confidence_cannot_authorize(record)
    assert_epistemic_cannot_create_human_final(record)
    assert_epistemic_cannot_change_execution_authorization(record)
    _walk_reject_reserved_keys(record, path="", is_root=True)
