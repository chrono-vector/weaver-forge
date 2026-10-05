"""Bounded custody phases for the Ed25519 custody helper v0.

Each phase runs in its own process and terminates. The only generator is
``Ed25519PrivateKey.generate()``; the only private serialization is
encrypted PKCS#8 PEM through ``BestAvailableEncryption``; the only public
extraction is Raw/Raw after encrypted reload. There is no signing, no
arbitrary-message, no Admission, and no caller-selected key, path,
snapshot, or algorithm surface.
"""

from __future__ import annotations

import datetime
import os

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519

from . import console, paths, state, winsec
from .errors import CustodyError, fail

MAX_PEM = 4096
PEM_BEGIN = b"-----BEGIN ENCRYPTED PRIVATE KEY-----\n"
PEM_END = b"-----END ENCRYPTED PRIVATE KEY-----\n"
_HEX = frozenset("0123456789abcdef")
_RESTORE_FOR = {state.PCW_VERIFIED: 1, state.PCW_RESTORE_1: 2}


class Session:
    """Validated account SID and fixed paths for one process."""

    def __init__(self, user_sid: str, fixed: paths.FixedPaths) -> None:
        self.user_sid = user_sid
        self.paths = fixed


def open_session() -> Session:
    user_sid = winsec.check_account()
    fixed = paths.resolve()
    return Session(user_sid, fixed)


# ---------------------------------------------------------------- key material


def require_encrypted_label(data) -> None:
    if type(data) is not bytes or len(data) > MAX_PEM:
        fail("SERIALIZATION_REJECTED")
    if not data.startswith(PEM_BEGIN) or not data.endswith(PEM_END):
        fail("SERIALIZATION_REJECTED")
    if data.count(b"-----BEGIN ") != 1 or data.count(b"-----END ") != 1:
        fail("SERIALIZATION_REJECTED")


def serialize_private(key, passphrase: bytes) -> bytes:
    pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.BestAvailableEncryption(passphrase),
    )
    require_encrypted_label(pem)
    return pem


def load_private(pem: bytes, passphrase: bytes):
    require_encrypted_label(pem)
    try:
        key = serialization.load_pem_private_key(pem, password=passphrase)
    except Exception:
        key = None
        fail("KEY_RELOAD_REJECTED")
    if not isinstance(key, ed25519.Ed25519PrivateKey):
        fail("KEY_TYPE_REJECTED")
    return key


def require_public(raw) -> None:
    if type(raw) is not bytes or len(raw) != 32:
        fail("PUBLIC_OUTPUT_REJECTED")


def raw_public(key) -> bytes:
    try:
        raw = key.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
    except Exception:
        raw = None
    require_public(raw)
    return raw


def require_display(text) -> None:
    if type(text) is not str or len(text) != 64:
        fail("DISPLAY_REJECTED")
    for ch in text:
        if ch not in _HEX:
            fail("DISPLAY_REJECTED")


def canonical_display(raw) -> str:
    require_public(raw)
    text = raw.hex()
    require_display(text)
    return text


# ---------------------------------------------------------------- state files


def _exists(path: str) -> bool:
    return os.path.lexists(path)


def _regular_names(directory: str):
    try:
        entries = winsec.list_entries(directory)
    except OSError:
        return None
    for attrs in entries.values():
        if attrs & (winsec.FILE_ATTRIBUTE_DIRECTORY | winsec.FILE_ATTRIBUTE_REPARSE_POINT):
            return None
    return frozenset(entries)


def _write_marker(directory, name, tmp_name, data, user_sid, replace) -> None:
    tmp = directory + "\\" + tmp_name
    final = directory + "\\" + name
    winsec.write_new_file(tmp, user_sid, data)
    if replace:
        winsec.replace_file(tmp, final)
    else:
        winsec.move_no_replace(tmp, final)
    back, _identity = winsec.read_file(final, user_sid, 256)
    if back != data:
        fail("STATE_REJECTED")


def mark_abandoned(s: Session) -> None:
    winsec.verify_directory(s.paths.custody, s.user_sid)
    _write_marker(
        s.paths.custody,
        state.MARKER,
        state.MARKER_ABANDON_TMP,
        state.encode_marker(state.ABANDONED),
        s.user_sid,
        True,
    )


def integrity_failure(s: Session, token, code: str) -> None:
    """Pre-READY failures become terminal ABANDONED; READY never transitions (N2)."""
    if token == state.READY:
        raise CustodyError(code) from None
    abandoned = False
    try:
        mark_abandoned(s)
        abandoned = True
    except Exception:
        abandoned = False
    raise CustodyError(code, abandoned=abandoned) from None


def load_state(s: Session, mutate: bool = True) -> str:
    """Accept only an exact state/file-set combination."""
    p = s.paths
    if not _exists(p.custody):
        fail("NO_ACTIVE_GENERATION")
    token = None
    try:
        winsec.verify_directory(p.custody, s.user_sid)
        data, _identity = winsec.read_file(p.custody_file(state.MARKER), s.user_sid, 256)
        token = state.decode_marker(data)
        if token is None:
            fail("STATE_REJECTED")
        if token == state.ABANDONED:
            return token
        names = _regular_names(p.custody)
        if names is None or names != state.files_for(token):
            fail("STATE_REJECTED")
    except CustodyError as exc:
        if mutate:
            integrity_failure(s, token, exc.code)
        raise
    except Exception:
        if mutate:
            integrity_failure(s, token, "INTERNAL_FAILURE")
        fail("INTERNAL_FAILURE")
    return token


def load_active(s: Session) -> str:
    token = load_state(s)
    if token == state.ABANDONED:
        fail("STATE_ABANDONED")
    return token


def commit(s: Session, current: str, new: str) -> None:
    """Code-owned monotonic transition to the exact successor state."""
    if current not in state.ORDER or state.successor(current) != new:
        fail("STATE_REJECTED")
    names = _regular_names(s.paths.custody)
    if names is None or names != state.files_for(new):
        fail("STATE_REJECTED")
    _write_marker(
        s.paths.custody, state.MARKER, state.MARKER_TMP, state.encode_marker(new), s.user_sid, True
    )
    if load_state(s, mutate=False) != new:
        fail("STATE_REJECTED")


def _guarded(s: Session, token: str, operation):
    try:
        return operation()
    except CustodyError as exc:
        integrity_failure(s, token, exc.code)
    except Exception:
        integrity_failure(s, token, "INTERNAL_FAILURE")


def _read_private(s: Session) -> bytes:
    data, _identity = winsec.read_file(s.paths.custody_file(state.PRIVATE), s.user_sid, MAX_PEM)
    require_encrypted_label(data)
    return data


def _read_candidate(s: Session) -> bytes:
    data, _identity = winsec.read_file(s.paths.custody_file(state.CANDIDATE), s.user_sid, 64)
    if type(data) is not bytes or len(data) != 32:
        fail("CANDIDATE_REJECTED")
    return data


def _ensure_root(s: Session) -> None:
    if _exists(s.paths.root):
        winsec.verify_directory(s.paths.root, s.user_sid)
    else:
        winsec.create_protected_directory(s.paths.root, s.user_sid)


def _ensure_quarantine(s: Session) -> None:
    if _exists(s.paths.quarantine):
        winsec.verify_directory(s.paths.quarantine, s.user_sid)
    else:
        winsec.create_protected_directory(s.paths.quarantine, s.user_sid)


def _require_plain_directory(path: str) -> None:
    attrs = winsec.file_attributes(path)
    if (
        attrs is None
        or attrs & winsec.FILE_ATTRIBUTE_REPARSE_POINT
        or not attrs & winsec.FILE_ATTRIBUTE_DIRECTORY
    ):
        fail("PATH_REJECTED")


def _stamp() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")


# ---------------------------------------------------------------- phases


def phase_preflight(s: Session) -> list:
    if _exists(s.paths.root):
        winsec.verify_directory(s.paths.root, s.user_sid)
    console.console_preflight()
    return ["PREFLIGHT_OK MACHINE_CHECKS_ONLY", "RUNBOOK_DECLARATIONS NOT_MACHINE_PROVEN"]


def phase_init(s: Session) -> list:
    p = s.paths
    if _exists(p.custody) or _exists(p.restore):
        fail("EXISTS_REJECTED")
    _ensure_root(s)
    winsec.create_protected_directory(p.custody, s.user_sid)
    if _regular_names(p.custody) != frozenset():
        fail("STATE_REJECTED")
    _write_marker(p.custody, state.MARKER, state.MARKER_TMP, state.encode_marker(state.EMPTY), s.user_sid, False)
    if load_state(s, mutate=False) != state.EMPTY:
        fail("STATE_REJECTED")
    return ["STATE " + state.EMPTY]


def phase_generate(s: Session) -> list:
    console.console_preflight()
    token = load_active(s)
    if token != state.EMPTY:
        fail("STATE_REJECTED")
    passphrase = console.read_new_passphrase()
    key = ed25519.Ed25519PrivateKey.generate()
    if not isinstance(key, ed25519.Ed25519PrivateKey):
        fail("KEY_TYPE_REJECTED")
    pem = serialize_private(key, passphrase)
    del key
    path = s.paths.custody_file(state.PRIVATE)
    try:
        winsec.write_new_file(path, s.user_sid, pem)
        if _read_private(s) != pem:
            fail("FILE_REJECTED")
        commit(s, state.EMPTY, state.PRIVATE_WRITTEN)
    except Exception as exc:
        code = exc.code if isinstance(exc, CustodyError) else "INTERNAL_FAILURE"
        if _exists(path):
            integrity_failure(s, state.EMPTY, code)
        raise CustodyError(code) from None
    return ["STATE " + state.PRIVATE_WRITTEN]


def phase_derive_candidate(s: Session) -> list:
    console.console_preflight()
    token = load_active(s)
    if token != state.PRIVATE_WRITTEN:
        fail("STATE_REJECTED")

    def operation():
        pem = _read_private(s)
        passphrase = console.read_unlock_passphrase()
        raw = raw_public(load_private(pem, passphrase))
        winsec.write_new_file(s.paths.custody_file(state.CANDIDATE), s.user_sid, raw)
        back = _read_candidate(s)
        if back != raw:
            fail("CANDIDATE_MISMATCH")
        canonical_display(back)
        commit(s, state.PRIVATE_WRITTEN, state.PCW_CANDIDATE)

    _guarded(s, token, operation)
    return ["STATE " + state.PCW_CANDIDATE]


def phase_verify_candidate(s: Session) -> list:
    console.console_preflight()
    token = load_active(s)
    if token != state.PCW_CANDIDATE:
        fail("STATE_REJECTED")

    def operation():
        pem = _read_private(s)
        passphrase = console.read_unlock_passphrase()
        raw = raw_public(load_private(pem, passphrase))
        candidate = _read_candidate(s)
        if raw != candidate:
            fail("CANDIDATE_MISMATCH")
        display_1 = canonical_display(candidate)
        display_2 = canonical_display(raw)
        if display_1 != display_2:
            fail("DISPLAY_REJECTED")
        commit(s, state.PCW_CANDIDATE, state.PCW_VERIFIED)
        return display_1

    display = _guarded(s, token, operation)
    return ["DISPLAY " + display, "STATE " + state.PCW_VERIFIED]


def phase_restore_init(s: Session) -> list:
    token = load_active(s)
    check = _RESTORE_FOR.get(token)
    if check is None:
        fail("STATE_REJECTED")
    p = s.paths
    if _exists(p.restore):
        fail("EXISTS_REJECTED")
    _ensure_root(s)
    winsec.create_protected_directory(p.restore, s.user_sid)
    if _regular_names(p.restore) != frozenset():
        fail("RESTORE_SLOT_REJECTED")
    _write_marker(
        p.restore,
        state.RESTORE_MARKER,
        state.RESTORE_MARKER_TMP,
        state.encode_restore_marker(check),
        s.user_sid,
        False,
    )
    return ["RESTORE_SLOT_READY FOR_CHECK " + str(check), "STATE " + token]


def phase_restore_check(s: Session) -> list:
    console.console_preflight()
    token = load_active(s)
    check = _RESTORE_FOR.get(token)
    if check is None:
        fail("STATE_REJECTED")
    p = s.paths
    artifact = p.restore_file(state.RESTORE_ARTIFACT)
    if not _exists(p.restore) or not _exists(artifact):
        fail("RESTORE_SLOT_REJECTED")

    def operation():
        winsec.verify_directory(p.restore, s.user_sid)
        if _regular_names(p.restore) != frozenset({state.RESTORE_MARKER, state.RESTORE_ARTIFACT}):
            fail("RESTORE_SLOT_REJECTED")
        marker, _identity = winsec.read_file(p.restore_file(state.RESTORE_MARKER), s.user_sid, 256)
        if state.decode_restore_marker(marker) != check:
            fail("RESTORE_SLOT_REJECTED")
        restored, restored_id = winsec.read_file(artifact, s.user_sid, MAX_PEM)
        working, working_id = winsec.read_file(p.custody_file(state.PRIVATE), s.user_sid, MAX_PEM)
        if restored_id == working_id:
            fail("RESTORE_REJECTED")
        require_encrypted_label(restored)
        if restored != working:
            fail("RESTORE_REJECTED")
        passphrase = console.read_unlock_passphrase()
        raw = raw_public(load_private(restored, passphrase))
        candidate = _read_candidate(s)
        if raw != candidate:
            fail("CANDIDATE_MISMATCH")
        display = canonical_display(raw)
        if display != canonical_display(candidate):
            fail("DISPLAY_REJECTED")
        winsec.delete_file(artifact)
        winsec.delete_file(p.restore_file(state.RESTORE_MARKER))
        winsec.remove_directory(p.restore)
        commit(s, token, state.successor(token))
        return display

    display = _guarded(s, token, operation)
    return [
        "DISPLAY " + display,
        "RESTORE_CHECK_PASSED " + str(check),
        "STATE " + state.successor(token),
    ]


def phase_restore_clear(s: Session) -> list:
    p = s.paths
    if not _exists(p.restore):
        fail("RESTORE_SLOT_REJECTED")
    _ensure_root(s)
    _require_plain_directory(p.restore)
    known = {state.RESTORE_MARKER, state.RESTORE_MARKER_TMP, state.RESTORE_ARTIFACT}
    names = _regular_names(p.restore)
    clean = names is not None and names <= known
    if clean:
        try:
            winsec.verify_directory(p.restore, s.user_sid)
        except CustodyError:
            clean = False
    if clean:
        for name in sorted(names):
            winsec.delete_file(p.restore_file(name))
        winsec.remove_directory(p.restore)
    else:
        _ensure_quarantine(s)
        winsec.move_no_replace(p.restore, p.quarantine + "\\restore-v0-" + _stamp())
    return ["RESTORE_SLOT_CLEARED", "PHYSICAL_ERASURE NOT_CLAIMED"]


def phase_mark_backups_verified(s: Session) -> list:
    token = load_active(s)
    if token != state.PCW_RESTORE_2:
        fail("STATE_REJECTED")
    if _exists(s.paths.restore):
        fail("RESTORE_SLOT_REJECTED")

    def operation():
        _read_private(s)
        _read_candidate(s)
        commit(s, state.PCW_RESTORE_2, state.BACKUPS_VERIFIED)

    _guarded(s, token, operation)
    return ["STATE " + state.BACKUPS_VERIFIED]


def phase_mark_ready(s: Session) -> list:
    token = load_active(s)
    if token != state.BACKUPS_VERIFIED:
        fail("STATE_REJECTED")
    if _exists(s.paths.restore):
        fail("RESTORE_SLOT_REJECTED")

    def operation():
        _read_private(s)
        _read_candidate(s)
        commit(s, state.BACKUPS_VERIFIED, state.READY)

    _guarded(s, token, operation)
    return ["STATE " + state.READY, "ADMISSION NOT_PERFORMED"]


def phase_pre_prepare_display(s: Session) -> list:
    console.console_preflight()
    token = load_active(s)
    if token != state.READY:
        fail("STATE_REJECTED")

    def operation():
        pem = _read_private(s)
        passphrase = console.read_unlock_passphrase()
        raw = raw_public(load_private(pem, passphrase))
        candidate = _read_candidate(s)
        if raw != candidate:
            fail("CANDIDATE_MISMATCH")
        display = canonical_display(raw)
        if display != canonical_display(candidate):
            fail("DISPLAY_REJECTED")
        return display

    display = _guarded(s, state.READY, operation)
    return [
        "DISPLAY " + display,
        "CANDIDATE_MATCH EXACT",
        "STATE " + state.READY,
        "ADMISSION NOT_PERFORMED",
    ]


def phase_abandon(s: Session) -> list:
    p = s.paths
    has_custody = _exists(p.custody)
    has_restore = _exists(p.restore)
    if not (has_custody or has_restore):
        fail("NO_ACTIVE_GENERATION")
    _ensure_root(s)
    if has_custody:
        _require_plain_directory(p.custody)
    if has_restore:
        _require_plain_directory(p.restore)
    _ensure_quarantine(s)
    stamp = _stamp()
    if has_custody:
        try:
            mark_abandoned(s)
        except Exception:
            pass
        winsec.move_no_replace(p.custody, p.quarantine + "\\custody-v0-" + stamp)
    if has_restore:
        winsec.move_no_replace(p.restore, p.quarantine + "\\restore-v0-" + stamp)
    winsec.write_new_file(
        p.quarantine + "\\generation-" + stamp + ".abandoned",
        s.user_sid,
        state.encode_marker(state.ABANDONED),
    )
    if _exists(p.custody) or _exists(p.restore):
        fail("STATE_REJECTED")
    return ["STATE " + state.ABANDONED, "ACTIVE_HANDOFF NONE", "PHYSICAL_ERASURE NOT_CLAIMED"]


def phase_status(s: Session) -> list:
    return ["STATE " + load_state(s, mutate=False)]
