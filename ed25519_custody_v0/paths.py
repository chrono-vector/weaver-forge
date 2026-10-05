"""Fixed custody paths and location rules for the Ed25519 custody helper v0.

The custody root is never caller-selected. Production derives it from the
Windows known folder for the current account's non-redirected local
application data. The only substitution point is the private module
attribute ``_location_context``, which automated tests replace with an
isolated temporary context. No CLI option or environment variable selects
a root. Environment values are consulted only to add rejection roots.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass

from . import winsec
from .errors import fail

ROOT_NAME = "WeaverForge"
CUSTODY_NAME = "custody-v0"
RESTORE_NAME = "restore-v0"
QUARANTINE_NAME = "abandoned-v0"

_PLAIN_ABSOLUTE = re.compile(r"^[A-Za-z]:\\[^:*?\"<>|/]+$")
_SYNC_COMPONENTS = frozenset(
    {"dropbox", "google drive", "googledrive", "my drive", "icloud drive", "iclouddrive", "box", "box sync"}
)


@dataclass(frozen=True)
class LocationContext:
    local_appdata: str
    profile: str
    roaming: str
    temp_dirs: tuple
    sync_roots: tuple


@dataclass(frozen=True)
class FixedPaths:
    root: str
    custody: str
    restore: str
    quarantine: str

    def custody_file(self, name: str) -> str:
        return self.custody + "\\" + name

    def restore_file(self, name: str) -> str:
        return self.restore + "\\" + name


def _windows_location_context() -> LocationContext:
    local = winsec.known_folder(winsec.FOLDERID_LOCAL_APPDATA)
    profile = winsec.known_folder(winsec.FOLDERID_PROFILE)
    roaming = winsec.known_folder(winsec.FOLDERID_ROAMING_APPDATA)
    temps = [winsec.temp_path()]
    for name in ("TEMP", "TMP"):
        value = os.environ.get(name)
        if value:
            temps.append(value)
    system_root = os.environ.get("SystemRoot") or "C:\\Windows"
    temps.append(system_root + "\\Temp")
    syncs = tuple(
        value for key, value in os.environ.items() if key.upper().startswith("ONEDRIVE") and value
    )
    return LocationContext(local, profile, roaming, tuple(temps), syncs)


# Private seam. Tests replace this attribute; production never does.
_location_context = _windows_location_context


def _norm(path: str) -> str:
    return os.path.normcase(path.rstrip("\\"))


def _is_under(path: str, base: str) -> bool:
    p = _norm(path)
    b = _norm(base)
    return p == b or p.startswith(b + "\\")


def _require_plain_absolute(path: str) -> None:
    if type(path) is not str or not _PLAIN_ABSOLUTE.match(path) or len(path) > 200:
        fail("PATH_REJECTED")
    parts = path[3:].split("\\")
    for part in parts:
        if part in ("", ".", "..") or part != part.strip() or part.endswith("."):
            fail("PATH_REJECTED")


def validate_context(ctx: LocationContext) -> None:
    _require_plain_absolute(ctx.local_appdata)
    _require_plain_absolute(ctx.profile)
    if _norm(ctx.local_appdata) != _norm(ctx.profile + "\\AppData\\Local"):
        fail("PATH_REJECTED")


def validate_location(path: str, ctx: LocationContext) -> None:
    """Reject Git, sync, roaming, temp, network, removable, relative, and reparse locations."""
    _require_plain_absolute(path)
    if not _is_under(path, ctx.local_appdata) or _norm(path) == _norm(ctx.local_appdata):
        fail("PATH_REJECTED")
    if ctx.roaming and _is_under(path, ctx.roaming):
        fail("PATH_REJECTED")
    for temp in ctx.temp_dirs:
        if temp and _is_under(path, temp):
            fail("PATH_REJECTED")
    for sync in ctx.sync_roots:
        if sync and _is_under(path, sync):
            fail("PATH_REJECTED")
    for part in path[3:].split("\\"):
        low = part.lower()
        if low.startswith("onedrive") or low in _SYNC_COMPONENTS:
            fail("PATH_REJECTED")
    if winsec.drive_type(path[:3]) != winsec.DRIVE_FIXED:
        fail("PATH_REJECTED")
    current = path[:2]
    deepest = path[:3]
    for part in path[3:].split("\\"):
        current = current + "\\" + part
        attrs = winsec.file_attributes(current)
        if attrs is None:
            break
        if attrs & winsec.FILE_ATTRIBUTE_REPARSE_POINT:
            fail("PATH_REJECTED")
        if not attrs & winsec.FILE_ATTRIBUTE_DIRECTORY:
            fail("PATH_REJECTED")
        if os.path.lexists(current + "\\.git"):
            fail("PATH_REJECTED")
        deepest = current
    if winsec.sync_root_hresult(deepest) != winsec.HRESULT_NOT_IN_SYNC_ROOT:
        fail("PATH_REJECTED")


def resolve() -> FixedPaths:
    """Return the fixed custody paths after validating every location rule."""
    ctx = _location_context()
    validate_context(ctx)
    root = ctx.local_appdata.rstrip("\\") + "\\" + ROOT_NAME
    fixed = FixedPaths(
        root,
        root + "\\" + CUSTODY_NAME,
        root + "\\" + RESTORE_NAME,
        root + "\\" + QUARANTINE_NAME,
    )
    for path in (fixed.root, fixed.custody, fixed.restore, fixed.quarantine):
        validate_location(path, ctx)
    return fixed
