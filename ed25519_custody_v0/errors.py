"""Fixed public error vocabulary for the Ed25519 custody helper v0.

Error codes are closed constants. They never carry values, paths,
usernames, passphrase lengths, key material, or exception text.
"""

from __future__ import annotations

CODES = frozenset(
    {
        "USAGE_REJECTED",
        "INTERNAL_FAILURE",
        "ENV_PLATFORM_REJECTED",
        "ENV_INTERPRETER_REJECTED",
        "ENV_ISOLATION_REJECTED",
        "ENV_INJECTION_REJECTED",
        "ENV_VENV_REJECTED",
        "ENV_MODULE_PATH_REJECTED",
        "ENV_DISTRIBUTION_REJECTED",
        "ENV_RECORD_MISMATCH",
        "ENV_OPENSSL_REJECTED",
        "ENV_PROVENANCE_NOT_RECORDED",
        "ENV_PROVENANCE_MISMATCH",
        "ACCOUNT_REJECTED",
        "PATH_REJECTED",
        "ACL_REJECTED",
        "EXISTS_REJECTED",
        "FILE_REJECTED",
        "NO_ACTIVE_GENERATION",
        "STATE_REJECTED",
        "STATE_ABANDONED",
        "CONSOLE_PREFLIGHT_REJECTED",
        "SECRET_INPUT_REJECTED",
        "PASSPHRASE_SHAPE_REJECTED",
        "PASSPHRASE_MISMATCH",
        "SERIALIZATION_REJECTED",
        "KEY_RELOAD_REJECTED",
        "KEY_TYPE_REJECTED",
        "PUBLIC_OUTPUT_REJECTED",
        "DISPLAY_REJECTED",
        "CANDIDATE_REJECTED",
        "CANDIDATE_MISMATCH",
        "RESTORE_SLOT_REJECTED",
        "RESTORE_REJECTED",
    }
)


class CustodyError(Exception):
    """Closed helper failure carrying one fixed public code."""

    def __init__(self, code: str, abandoned: bool = False) -> None:
        if code not in CODES:
            code = "INTERNAL_FAILURE"
        self.code = code
        self.abandoned = bool(abandoned)
        super().__init__(code)

    def __repr__(self) -> str:
        return "CustodyError(" + self.code + ")"

    def __str__(self) -> str:
        return self.code


def fail(code: str) -> None:
    """Raise one closed failure without chaining any underlying exception."""
    raise CustodyError(code) from None
