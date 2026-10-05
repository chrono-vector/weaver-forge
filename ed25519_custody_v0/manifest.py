"""Environment manifest preflight for the Ed25519 custody helper v0.

Production preflight requires the PRE-REAL conditions of the frozen design:
official CPython 3.14.3 amd64 GIL build with a recorded provenance hash,
isolated mode, a dedicated virtual environment without system or user site
packages, the exact hash-locked wheels with verified installed RECORD
content, module paths inside that environment, the expected bundled OpenSSL
runtime, and no Python/OpenSSL injection variables. Passing automated tests
in a temporary test environment does not establish the PRE-REAL environment.
"""

from __future__ import annotations

import base64
import csv
import hashlib
import io
import os
import site
import struct
import sys
import sysconfig
from dataclasses import dataclass

from .errors import fail

_PYTHON_VERSION = (3, 14, 3, "final", 0)
_OPENSSL_VERSION_TEXT = "OpenSSL 4.0.3 29 Sep 2026"
_DISTRIBUTIONS = (
    ("cryptography", "50.0.2", ("cp311-abi3-win_amd64",)),
    ("cffi", "2.1.1", ("cp314-cp314-win_amd64",)),
    ("pycparser", "3.0", ("py3-none-any",)),
)
# SHA-256 over the sorted wheel-origin RECORD rows of each reviewed wheel
# (rows for INSTALLER, REQUESTED, direct_url.json, RECORD, .pyc files, and
# installer-generated files outside site-packages are excluded).
_RECORD_PINS = {
    "cryptography": "533730a776afb901817ab48cb6726bdf97b2e25d929123a805c442d631aa712e",
    "cffi": "01953e3286b3d010c9c91978f2632797e3a0003af722fc59478c571e76174d89",
    "pycparser": "889140660ed2d728f152c34ad338d29f672cad828eafd94adf78f91c11fd20a4",
}
_ALLOWED_SITE_ENTRIES = frozenset(
    {
        "cffi",
        "cffi-2.1.1.dist-info",
        "cryptography",
        "cryptography-50.0.2.dist-info",
        "pycparser",
        "pycparser-3.0.dist-info",
        "_cffi_backend.cp314-win_amd64.pyd",
        "pip",
        "__pycache__",
    }
)
_CHECKED_MODULES = (
    "cryptography",
    "cryptography.hazmat.bindings._rust",
    "cffi",
    "_cffi_backend",
    "pycparser",
)
_FALLBACK_MODULES = ("nacl", "Crypto", "Cryptodome", "ed25519", "pure25519", "ecdsa", "paramiko")
_INJECTION_PREFIXES = ("PYTHON", "OPENSSL", "PIP_", "CRYPTOGRAPHY", "CFFI", "SSL_CERT", "WEAVERFORGE")
_INJECTION_MARKERS = ("PASSPHRASE",)

# Official CPython provenance is a PRE-REAL prerequisite. It is deliberately
# unset: production preflight fails closed until a separately reviewed change
# records the official installer evidence and these interpreter file hashes
# as a tuple of (file name, lowercase SHA-256) pairs.
_INTERPRETER_PROVENANCE = None
_PROVENANCE_FILES = ("python.exe", "python314.dll")


@dataclass(frozen=True)
class DistFacts:
    name: str
    version: str
    location: str
    tags: tuple
    installer: str
    has_direct_url: bool


@dataclass(frozen=True)
class EnvironmentFacts:
    version_info: tuple
    implementation: str
    platform: str
    pointer_size: int
    sysconfig_platform: str
    gil_enabled: bool
    gil_disabled_build: bool
    isolated: bool
    ignore_environment: bool
    no_user_site: bool
    safe_path: bool
    enable_user_site: object
    warnoptions: tuple
    xoptions: tuple
    debug_flags: tuple
    executable: str
    base_executable: str
    prefix: str
    base_prefix: str
    pyvenv_cfg: object
    sys_path: tuple
    helper_root: str
    helper_file: str
    environ_names: tuple
    site_entries: tuple
    distributions: tuple
    module_files: tuple
    fallback_modules: tuple
    record_result: object
    openssl_version_text: str
    interpreter_hashes: tuple


def _norm(path: str) -> str:
    return os.path.normcase(os.path.abspath(path)) if path else ""


def _under(path: str, base: str) -> bool:
    p = _norm(path)
    b = _norm(base)
    return bool(p) and bool(b) and p.startswith(b + os.sep)


def _site_packages(prefix: str) -> str:
    return os.path.join(prefix, "Lib", "site-packages")


def _sha256_file(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _record_hash(data: bytes) -> str:
    return "sha256=" + base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b"=").decode("ascii")


def _origin_row(path: str, dist_info: str) -> bool:
    if path.startswith("../") or path.endswith(".pyc"):
        return False
    return path not in (
        dist_info + "/RECORD",
        dist_info + "/INSTALLER",
        dist_info + "/REQUESTED",
        dist_info + "/direct_url.json",
    )


def record_origin_digest(site_packages: str, name: str, version: str):
    """Verify one installed RECORD against file content; return the origin digest or None."""
    dist_info = name + "-" + version + ".dist-info"
    record_path = os.path.join(site_packages, dist_info, "RECORD")
    try:
        with open(record_path, "rb") as handle:
            text = handle.read().decode("utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    listed = set()
    origin = []
    tops = set()
    for row in csv.reader(io.StringIO(text, newline="")):
        if len(row) != 3:
            return None
        path, digest, size = row
        parts = path.split("/")
        if not path or path.startswith("/") or ":" in path or "\\" in path:
            return None
        if path.startswith("../"):
            if parts[:2] != ["..", ".."] or parts[2] != "Scripts" or len(parts) != 4:
                return None
        elif ".." in parts:
            return None
        full = os.path.normpath(os.path.join(site_packages, *parts))
        listed.add(os.path.normcase(full))
        if not path.startswith("../"):
            tops.add(parts[0])
        if digest == "":
            if path == dist_info + "/RECORD" or path.endswith(".pyc"):
                continue
            return None
        if not digest.startswith("sha256="):
            return None
        try:
            with open(full, "rb") as handle:
                data = handle.read()
        except OSError:
            return None
        if _record_hash(data) != digest or str(len(data)) != size:
            return None
        if _origin_row(path, dist_info):
            origin.append(path + "," + digest + "," + size)
    for top in tops:
        base = os.path.join(site_packages, top)
        if os.path.isdir(base):
            for dirpath, dirnames, filenames in os.walk(base):
                dirnames[:] = [d for d in dirnames if d != "__pycache__"]
                for filename in filenames:
                    full = os.path.normcase(os.path.join(dirpath, filename))
                    if full not in listed:
                        return None
    return hashlib.sha256("\n".join(sorted(origin)).encode("utf-8")).hexdigest()


def verify_records(site_packages: str):
    """Return None when every pinned distribution matches, otherwise a closed code."""
    for name, version, _tags in _DISTRIBUTIONS:
        digest = record_origin_digest(site_packages, name, version)
        if digest is None or digest != _RECORD_PINS[name]:
            return "ENV_RECORD_MISMATCH"
    return None


def _read_text(path: str):
    try:
        with open(path, "rb") as handle:
            return handle.read().decode("utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def collect_facts() -> EnvironmentFacts:
    import importlib.metadata as metadata

    import _cffi_backend
    import cffi
    import cryptography
    import pycparser
    from cryptography.hazmat.backends.openssl.backend import backend
    from cryptography.hazmat.bindings import _rust

    loaded = {
        "cryptography": cryptography,
        "cryptography.hazmat.bindings._rust": _rust,
        "cffi": cffi,
        "_cffi_backend": _cffi_backend,
        "pycparser": pycparser,
    }
    names = {name for name, _version, _tags in _DISTRIBUTIONS}
    dists = []
    for dist in metadata.distributions():
        name = (dist.metadata["Name"] or "").lower()
        if name not in names:
            continue
        path = getattr(dist, "_path", None)
        wheel = dist.read_text("WHEEL") or ""
        tags = tuple(sorted(line[5:].strip() for line in wheel.splitlines() if line.startswith("Tag: ")))
        dists.append(
            DistFacts(
                name,
                dist.version,
                str(path.parent) if path is not None else "",
                tags,
                (dist.read_text("INSTALLER") or "").strip(),
                dist.read_text("direct_url.json") is not None,
            )
        )
    site_packages = _site_packages(sys.prefix)
    try:
        site_entries = tuple(sorted(os.listdir(site_packages)))
    except OSError:
        site_entries = ()
    hashes = []
    for filename in _PROVENANCE_FILES:
        try:
            hashes.append((filename, _sha256_file(os.path.join(sys.base_prefix, filename))))
        except OSError:
            hashes.append((filename, ""))
    helper_file = os.path.abspath(sys.modules[__package__].__file__)
    return EnvironmentFacts(
        version_info=tuple(sys.version_info),
        implementation=sys.implementation.name,
        platform=sys.platform,
        pointer_size=struct.calcsize("P"),
        sysconfig_platform=sysconfig.get_platform(),
        gil_enabled=bool(sys._is_gil_enabled()),
        gil_disabled_build=bool(sysconfig.get_config_var("Py_GIL_DISABLED")),
        isolated=bool(sys.flags.isolated),
        ignore_environment=bool(sys.flags.ignore_environment),
        no_user_site=bool(sys.flags.no_user_site),
        safe_path=bool(sys.flags.safe_path),
        enable_user_site=site.ENABLE_USER_SITE,
        warnoptions=tuple(sys.warnoptions),
        xoptions=tuple(sorted(sys._xoptions)),
        debug_flags=(
            sys.flags.debug,
            sys.flags.inspect,
            sys.flags.interactive,
            sys.flags.verbose,
            int(sys.flags.dev_mode),
        ),
        executable=sys.executable,
        base_executable=getattr(sys, "_base_executable", ""),
        prefix=sys.prefix,
        base_prefix=sys.base_prefix,
        pyvenv_cfg=_read_text(os.path.join(sys.prefix, "pyvenv.cfg")),
        sys_path=tuple(sys.path),
        helper_root=os.path.dirname(os.path.dirname(helper_file)),
        helper_file=helper_file,
        environ_names=tuple(sorted(os.environ.keys())),
        site_entries=site_entries,
        distributions=tuple(dists),
        module_files=tuple((name, getattr(mod, "__file__", "") or "") for name, mod in loaded.items()),
        fallback_modules=tuple(name for name in _FALLBACK_MODULES if name in sys.modules),
        record_result=verify_records(site_packages),
        openssl_version_text=backend.openssl_version_text(),
        interpreter_hashes=tuple(hashes),
    )


def _pyvenv_values(text) -> dict:
    values = {}
    if type(text) is not str:
        return values
    for line in text.splitlines():
        key, sep, value = line.partition("=")
        if sep:
            values[key.strip().lower()] = value.strip()
    return values


def evaluate(facts: EnvironmentFacts) -> None:
    """Fail closed unless every PRE-REAL environment condition holds."""
    if (
        facts.platform != "win32"
        or facts.pointer_size != 8
        or facts.sysconfig_platform != "win-amd64"
    ):
        fail("ENV_PLATFORM_REJECTED")
    if (
        facts.implementation != "cpython"
        or tuple(facts.version_info) != _PYTHON_VERSION
        or facts.gil_enabled is not True
        or facts.gil_disabled_build is not False
    ):
        fail("ENV_INTERPRETER_REJECTED")
    base = facts.base_prefix
    for candidate in (base, facts.base_executable, facts.executable):
        low = _norm(candidate)
        if "\\windowsapps\\" in low or "\\packages\\" in low or "\\microsoft\\windowsapps" in low:
            fail("ENV_INTERPRETER_REJECTED")
    if _norm(facts.base_executable) != _norm(os.path.join(base, "python.exe")):
        fail("ENV_INTERPRETER_REJECTED")
    if (
        facts.isolated is not True
        or facts.ignore_environment is not True
        or facts.no_user_site is not True
        or facts.safe_path is not True
        or facts.enable_user_site is not False
        or facts.warnoptions
        or facts.xoptions
        or tuple(facts.debug_flags) != (0, 0, 0, 0, 0)
    ):
        fail("ENV_ISOLATION_REJECTED")
    for name in facts.environ_names:
        upper = name.upper()
        if upper.startswith(_INJECTION_PREFIXES) or any(m in upper for m in _INJECTION_MARKERS):
            fail("ENV_INJECTION_REJECTED")
    prefix = facts.prefix
    if _norm(prefix) == _norm(base) or not prefix:
        fail("ENV_VENV_REJECTED")
    cfg = _pyvenv_values(facts.pyvenv_cfg)
    if (
        cfg.get("include-system-site-packages") != "false"
        or cfg.get("version") != "3.14.3"
        or _norm(cfg.get("home", "")) != _norm(base)
    ):
        fail("ENV_VENV_REJECTED")
    if _norm(facts.executable) != _norm(os.path.join(prefix, "Scripts", "python.exe")):
        fail("ENV_VENV_REJECTED")
    site_packages = _site_packages(prefix)
    allowed = {
        _norm(os.path.join(base, "python314.zip")),
        _norm(os.path.join(base, "DLLs")),
        _norm(os.path.join(base, "Lib")),
        _norm(base),
        _norm(prefix),
        _norm(site_packages),
    }
    entries = [_norm(entry) for entry in facts.sys_path]
    if not entries or entries[-1] != _norm(facts.helper_root) or entries[-1] in allowed:
        fail("ENV_MODULE_PATH_REJECTED")
    for entry in entries[:-1]:
        if entry not in allowed:
            fail("ENV_MODULE_PATH_REJECTED")
    if _norm(facts.helper_file) != _norm(
        os.path.join(facts.helper_root, "ed25519_custody_v0", "__init__.py")
    ):
        fail("ENV_MODULE_PATH_REJECTED")
    for name, filename in facts.module_files:
        if not _under(filename, site_packages):
            fail("ENV_MODULE_PATH_REJECTED")
    if tuple(n for n, _f in facts.module_files) != _CHECKED_MODULES:
        fail("ENV_MODULE_PATH_REJECTED")
    if facts.fallback_modules:
        fail("ENV_MODULE_PATH_REJECTED")
    for entry in facts.site_entries:
        if entry not in _ALLOWED_SITE_ENTRIES and not (
            entry.startswith("pip-") and entry.endswith(".dist-info")
        ):
            fail("ENV_MODULE_PATH_REJECTED")
    expected = {(n, v, t) for n, v, t in _DISTRIBUTIONS}
    seen = set()
    for dist in facts.distributions:
        key = (dist.name, dist.version, tuple(dist.tags))
        if (
            key not in expected
            or key in seen
            or _norm(dist.location) != _norm(site_packages)
            or dist.installer != "pip"
            or dist.has_direct_url is not False
        ):
            fail("ENV_DISTRIBUTION_REJECTED")
        seen.add(key)
    if seen != expected:
        fail("ENV_DISTRIBUTION_REJECTED")
    if facts.record_result is not None:
        fail("ENV_RECORD_MISMATCH")
    if facts.openssl_version_text != _OPENSSL_VERSION_TEXT:
        fail("ENV_OPENSSL_REJECTED")
    if _INTERPRETER_PROVENANCE is None:
        fail("ENV_PROVENANCE_NOT_RECORDED")
    if tuple(facts.interpreter_hashes) != tuple(_INTERPRETER_PROVENANCE):
        fail("ENV_PROVENANCE_MISMATCH")


def run_preflight() -> None:
    evaluate(collect_facts())
