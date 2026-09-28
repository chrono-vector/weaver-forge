"""Non-authority invariants for R4-A epistemic records.

Top-level authority:false is mandatory.
Authority-like assertions are rejected at any nested depth by field/key semantics
(not by scanning arbitrary prose string contents).
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence

# Reserved keys that may assert authority / Human Final / execution permission.
# Matched on mapping keys only — not on free-text values of unrelated fields.
_AUTHORITY_LIKE_KEYS = frozenset(
    {
        "authority",
        "execution_authorized",
        "authorized",
        "human_final",
        "human_final_status",
        "final_accepted",
        "approval",
        "approved",
        "execution_permission",
        "vector_authorized",
        "eig_authorized",
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

_AUTHORITY_TRUE_STRINGS = frozenset(
    {
        "TRUE",
        "GRANT",
        "ALLOW",
        "AUTHORIZED",
        "APPROVED",
        "FINAL",
        "HUMAN_FINAL",
        "ACCEPTED",
        "YES",
    }
)


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


def _key_is_authority_like(key: Any) -> bool:
    if not isinstance(key, str):
        return False
    return key in _AUTHORITY_LIKE_KEYS or key.lower() in {
        k.lower() for k in _AUTHORITY_LIKE_KEYS
    }


def _value_asserts_authority(key: str, value: Any) -> bool:
    """Return True when an authority-like key carries an affirmative assertion."""
    lk = key.lower()
    # Nested authority:false is allowed (reinforces non-authority).
    if lk == "authority":
        return value is not False

    if value is True:
        return True
    if value is False or value is None:
        return False
    if isinstance(value, (int, float)) and value == 0:
        return False
    if isinstance(value, str):
        return value.strip().upper() in _AUTHORITY_TRUE_STRINGS
    # Non-false structured payload under an authority-like key is an assertion.
    if isinstance(value, (Mapping, Sequence)) and not isinstance(value, (str, bytes)):
        return True
    return bool(value)


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
        if val is True or (
            isinstance(val, str) and val.upper() in {"GRANT", "ALLOW", "AUTHORIZED"}
        ):
            raise AuthorityViolation(
                "epistemic metadata cannot change execution authorization"
            )
    if record.get("authority") is True:
        raise AuthorityViolation(
            "epistemic metadata cannot change execution authorization"
        )


def _walk_reject_authority_like(node: Any, *, path: str, is_root: bool) -> None:
    if isinstance(node, Mapping):
        for key, value in node.items():
            child_path = f"{path}.{key}" if path else str(key)
            if _key_is_authority_like(key):
                # Top-level authority already enforced as mandatory false.
                if is_root and str(key).lower() == "authority":
                    continue
                if _value_asserts_authority(str(key), value):
                    raise AuthorityViolation(
                        f"nested authority-like assertion forbidden at {child_path}"
                    )
            if isinstance(value, (Mapping, list, tuple)) and not isinstance(
                value, (str, bytes)
            ):
                _walk_reject_authority_like(value, path=child_path, is_root=False)
    elif isinstance(node, (list, tuple)) and not isinstance(node, (str, bytes)):
        for i, item in enumerate(node):
            _walk_reject_authority_like(item, path=f"{path}[{i}]", is_root=False)


def enforce_non_authority(record: Mapping[str, Any]) -> None:
    """Run the full non-authority battery, including nested key checks."""
    assert_authority_false(record)
    assert_confidence_cannot_authorize(record)
    assert_epistemic_cannot_create_human_final(record)
    assert_epistemic_cannot_change_execution_authorization(record)
    _walk_reject_authority_like(record, path="", is_root=True)
