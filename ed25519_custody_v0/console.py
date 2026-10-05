"""Console preflight and hidden passphrase input for the Ed25519 custody helper v0.

Every machine-enforceable console check runs before any secret read and
fails closed. The passphrase is read only through ``getpass.getpass`` in a
preflighted Windows console with ``GetPassWarning`` configured as an error.
There is no command-line, environment, file, pipe, clipboard, or chat
transport. Absence of an AI, agent, IDE capture, ConPTY relay, recorder,
or transcript is a Human runbook declaration, not a machine-proven fact.
"""

from __future__ import annotations

import ctypes
import getpass
import sys
import warnings
from ctypes import wintypes
from dataclasses import dataclass

from .errors import fail

MIN_PASSPHRASE = 24
MAX_PASSPHRASE = 128
_FILE_TYPE_CHAR = 0x0002

_k32 = ctypes.WinDLL("kernel32", use_last_error=True)
_GetFileType = _k32.GetFileType
_GetFileType.restype = wintypes.DWORD
_GetFileType.argtypes = [wintypes.HANDLE]
_GetConsoleMode = _k32.GetConsoleMode
_GetConsoleMode.restype = wintypes.BOOL
_GetConsoleMode.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
_CreateFileW = _k32.CreateFileW
_CreateFileW.restype = wintypes.HANDLE
_CreateFileW.argtypes = [
    wintypes.LPCWSTR,
    wintypes.DWORD,
    wintypes.DWORD,
    ctypes.c_void_p,
    wintypes.DWORD,
    wintypes.DWORD,
    wintypes.HANDLE,
]
_CloseHandle = _k32.CloseHandle
_CloseHandle.restype = wintypes.BOOL
_CloseHandle.argtypes = [wintypes.HANDLE]
_INVALID_HANDLE = ctypes.c_void_p(-1).value


@dataclass(frozen=True)
class ConsoleFacts:
    stdin_is_original: bool
    stderr_is_original: bool
    stdin_is_char_device: bool
    stdin_console_mode: bool
    stderr_console_mode: bool
    conin_console_mode: bool
    conout_console_mode: bool
    warnoptions_empty: bool
    getpass_is_console_impl: bool


def _handle_is_console(handle) -> bool:
    mode = wintypes.DWORD()
    return bool(handle) and handle != _INVALID_HANDLE and bool(_GetConsoleMode(handle, ctypes.byref(mode)))


def _fd_facts(stream):
    import msvcrt

    try:
        handle = msvcrt.get_osfhandle(stream.fileno())
    except Exception:
        return False, False
    return _GetFileType(handle) == _FILE_TYPE_CHAR, _handle_is_console(handle)


def _device_is_console(name: str) -> bool:
    handle = _CreateFileW(name, 0x80000000 | 0x40000000, 0x1 | 0x2, None, 3, 0, None)
    if handle is None or handle == _INVALID_HANDLE:
        return False
    try:
        return _handle_is_console(handle)
    finally:
        _CloseHandle(handle)


def _collect_console_facts() -> ConsoleFacts:
    stdin = sys.stdin
    stderr = sys.stderr
    stdin_original = stdin is not None and stdin is sys.__stdin__
    stderr_original = stderr is not None and stderr is sys.__stderr__
    stdin_char, stdin_console = _fd_facts(stdin) if stdin_original else (False, False)
    _err_char, stderr_console = _fd_facts(stderr) if stderr_original else (False, False)
    return ConsoleFacts(
        stdin_original,
        stderr_original,
        stdin_char,
        stdin_console,
        stderr_console,
        _device_is_console("CONIN$"),
        _device_is_console("CONOUT$"),
        not sys.warnoptions,
        getpass.getpass is getpass.win_getpass,
    )


def evaluate_console(facts: ConsoleFacts) -> None:
    if not (
        facts.stdin_is_original is True
        and facts.stderr_is_original is True
        and facts.stdin_is_char_device is True
        and facts.stdin_console_mode is True
        and facts.stderr_console_mode is True
        and facts.conin_console_mode is True
        and facts.conout_console_mode is True
        and facts.warnoptions_empty is True
        and facts.getpass_is_console_impl is True
    ):
        fail("CONSOLE_PREFLIGHT_REJECTED")


def console_preflight() -> None:
    evaluate_console(_collect_console_facts())


def _hidden_reader():
    """Return the Windows console getpass implementation. Tests replace this seam."""
    if getpass.getpass is not getpass.win_getpass:
        fail("CONSOLE_PREFLIGHT_REJECTED")
    return getpass.getpass


def _warning_is_error() -> bool:
    if not warnings.filters:
        return False
    action, _message, category, _module, _lineno = warnings.filters[0]
    return action == "error" and category is getpass.GetPassWarning


def read_secret(prompt: str) -> str:
    """Preflight the console, then read one hidden value. Fails closed."""
    console_preflight()
    reader = _hidden_reader()
    with warnings.catch_warnings():
        warnings.simplefilter("error", getpass.GetPassWarning)
        if not _warning_is_error():
            fail("CONSOLE_PREFLIGHT_REJECTED")
        try:
            value = reader(prompt)
        except Exception:
            value = None
    if type(value) is not str:
        fail("SECRET_INPUT_REJECTED")
    return value


def validate_passphrase(value) -> bytes:
    """Enforce shape only: 24..128 printable ASCII characters, ASCII-encoded."""
    if type(value) is not str:
        fail("PASSPHRASE_SHAPE_REJECTED")
    if len(value) < MIN_PASSPHRASE or len(value) > MAX_PASSPHRASE:
        fail("PASSPHRASE_SHAPE_REJECTED")
    for ch in value:
        code = ord(ch)
        if code < 0x20 or code > 0x7E:
            fail("PASSPHRASE_SHAPE_REJECTED")
    return value.encode("ascii")


def read_new_passphrase() -> bytes:
    first = validate_passphrase(read_secret("New passphrase (hidden): "))
    second = validate_passphrase(read_secret("Repeat passphrase (hidden): "))
    if first != second:
        fail("PASSPHRASE_MISMATCH")
    return first


def read_unlock_passphrase() -> bytes:
    return validate_passphrase(read_secret("Passphrase (hidden): "))
