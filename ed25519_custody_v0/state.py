"""Closed custody state machine vocabulary for the Ed25519 custody helper v0.

Frozen states: EMPTY -> PRIVATE_WRITTEN -> PUBLIC_CANDIDATE_WRITTEN ->
BACKUPS_VERIFIED -> READY_FOR_ADMISSION_HANDOFF, plus terminal ABANDONED.
Within PUBLIC_CANDIDATE_WRITTEN the marker records only non-secret
completion of derivation 2 and of each fixed restore-v0 check. These are
progress records inside one frozen state, not additional states.
"""

from __future__ import annotations

MAGIC = b"WEAVERFORGE-ED25519-CUSTODY-V0\n"

MARKER = "custody-v0-state-v0"
MARKER_TMP = "custody-v0-state-v0.tmp"
MARKER_ABANDON_TMP = "custody-v0-state-v0.abandon.tmp"
PRIVATE = "custody-v0-private-v0.pem"
CANDIDATE = "custody-v0-candidate-v0.bin"
RESTORE_MARKER = "restore-v0-state-v0"
RESTORE_MARKER_TMP = "restore-v0-state-v0.tmp"
RESTORE_ARTIFACT = "restore-v0-artifact-v0.pem"

EMPTY = "EMPTY"
PRIVATE_WRITTEN = "PRIVATE_WRITTEN"
PCW_CANDIDATE = "PUBLIC_CANDIDATE_WRITTEN DERIVATION_1"
PCW_VERIFIED = "PUBLIC_CANDIDATE_WRITTEN DERIVATION_2"
PCW_RESTORE_1 = "PUBLIC_CANDIDATE_WRITTEN RESTORE_CHECK_1"
PCW_RESTORE_2 = "PUBLIC_CANDIDATE_WRITTEN RESTORE_CHECK_2"
BACKUPS_VERIFIED = "BACKUPS_VERIFIED"
READY = "READY_FOR_ADMISSION_HANDOFF"
ABANDONED = "ABANDONED"

ORDER = (
    EMPTY,
    PRIVATE_WRITTEN,
    PCW_CANDIDATE,
    PCW_VERIFIED,
    PCW_RESTORE_1,
    PCW_RESTORE_2,
    BACKUPS_VERIFIED,
    READY,
)


def files_for(token: str) -> frozenset:
    if token == EMPTY:
        return frozenset({MARKER})
    if token == PRIVATE_WRITTEN:
        return frozenset({MARKER, PRIVATE})
    if token in ORDER:
        return frozenset({MARKER, PRIVATE, CANDIDATE})
    raise ValueError("state")


def encode_marker(token: str) -> bytes:
    if token not in ORDER and token != ABANDONED:
        raise ValueError("state")
    return MAGIC + b"STATE " + token.encode("ascii") + b"\n"


def decode_marker(data):
    if type(data) is not bytes:
        return None
    for token in ORDER + (ABANDONED,):
        if data == encode_marker(token):
            return token
    return None


def successor(token: str):
    index = ORDER.index(token)
    if index + 1 >= len(ORDER):
        return None
    return ORDER[index + 1]


def encode_restore_marker(check: int) -> bytes:
    if check not in (1, 2):
        raise ValueError("restore")
    return MAGIC + b"RESTORE_EMPTY FOR_CHECK " + str(check).encode("ascii") + b"\n"


def decode_restore_marker(data):
    if type(data) is not bytes:
        return None
    for check in (1, 2):
        if data == encode_restore_marker(check):
            return check
    return None
