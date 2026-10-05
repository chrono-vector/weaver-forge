"""Shared fixtures for Ed25519 custody helper v0 tests.

TEST ONLY. Every key used by these tests is generated at runtime inside
pytest tmp_path and discarded. The passphrases below are public, non-secret
TEST ONLY strings. No test touches the real %LOCALAPPDATA%\\WeaverForge root:
the private ``paths._location_context`` seam is replaced with a context
under tmp_path, and a guard fails any test whose resolved root escapes it.
"""

from __future__ import annotations

import dataclasses
import os
import sys
from pathlib import Path

import pytest

from ed25519_custody_v0 import cli, console, custody, manifest, paths, state, winsec

TEST_PASSPHRASE = "TEST-ONLY-custody-passphrase-0123456789"  # TEST ONLY, public
OTHER_PASSPHRASE = "TEST-ONLY-other-passphrase-9876543210-xyz"  # TEST ONLY, public

PKG_DIR = Path(custody.__file__).resolve().parent
REPO_DIR = PKG_DIR.parent
RUNBOOK = REPO_DIR / "docs" / "next" / "DEDICATED_LOCAL_SOFTWARE_ED25519_CUSTODY_HELPER_RUNBOOK_V0_20261005.md"

GOOD_CONSOLE = console.ConsoleFacts(True, True, True, True, True, True, True, True, True)

REAL = {
    "check_account": winsec.check_account,
    "run_preflight": manifest.run_preflight,
    "collect_console": console._collect_console_facts,
    "hidden_reader": console._hidden_reader,
    "location_context": paths._location_context,
}


class SimulatedCrash(BaseException):
    """Process death injected by tests; never caught by the helper."""


def real_weaverforge_root() -> str:
    return winsec.known_folder(winsec.FOLDERID_LOCAL_APPDATA) + "\\" + paths.ROOT_NAME


def _snapshot(root: str):
    if not os.path.lexists(root):
        return None
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        out.append((dirpath, sorted(dirnames), sorted(filenames)))
    return out


@pytest.fixture(scope="session", autouse=True)
def real_root_untouched():
    root = real_weaverforge_root()
    before = _snapshot(root)
    yield
    assert _snapshot(root) == before, "real WeaverForge root changed"


def _inside(path: str, base: Path) -> bool:
    p = os.path.normcase(os.path.abspath(path))
    b = os.path.normcase(str(base))
    return p.startswith(b + os.sep)


class FakeReader:
    """TEST ONLY hidden-input replacement installed through the private seam."""

    def __init__(self) -> None:
        self.answers = []
        self.prompts = []
        self.unexpected = 0

    def __call__(self, prompt):
        self.prompts.append(prompt)
        if not self.answers:
            self.unexpected += 1
            return None
        answer = self.answers.pop(0)
        if callable(answer):
            return answer(prompt)
        return answer


class Harness:
    def __init__(self, base: Path, reader: FakeReader, capsys, sid: str) -> None:
        self.base = base
        self.reader = reader
        self.capsys = capsys
        self.sid = sid
        self.outputs = []

    @property
    def paths(self) -> paths.FixedPaths:
        return paths.resolve()

    def session(self) -> custody.Session:
        return custody.Session(self.sid, self.paths)

    def custody_file(self, name: str) -> Path:
        return Path(self.paths.custody_file(name))

    def restore_file(self, name: str) -> Path:
        return Path(self.paths.restore_file(name))

    def run(self, command, *answers, argv=None):
        self.reader.answers = list(answers)
        self.reader.prompts = []
        rc = cli.main(argv if argv is not None else [command])
        out, err = self.capsys.readouterr()
        self.outputs.append(out + err)
        return rc, out, err

    def ok(self, command, *answers):
        rc, out, err = self.run(command, *answers)
        assert rc == 0, (command, out, err)
        return out

    def marker(self):
        return state.decode_marker(self.custody_file(state.MARKER).read_bytes())

    def copy_backup(self) -> None:
        data = self.custody_file(state.PRIVATE).read_bytes()
        with open(self.restore_file(state.RESTORE_ARTIFACT), "xb") as handle:
            handle.write(data)

    def restore_once(self) -> None:
        self.ok("restore-init")
        self.copy_backup()
        self.ok("restore-check", TEST_PASSPHRASE)

    def advance(self, target: str) -> None:
        pw = TEST_PASSPHRASE
        steps = [
            (state.EMPTY, lambda: self.ok("init")),
            (state.PRIVATE_WRITTEN, lambda: self.ok("generate", pw, pw)),
            (state.PCW_CANDIDATE, lambda: self.ok("derive-candidate", pw)),
            (state.PCW_VERIFIED, lambda: self.ok("verify-candidate", pw)),
            (state.PCW_RESTORE_1, self.restore_once),
            (state.PCW_RESTORE_2, self.restore_once),
            (state.BACKUPS_VERIFIED, lambda: self.ok("mark-backups-verified")),
            (state.READY, lambda: self.ok("mark-ready")),
        ]
        for token, step in steps:
            step()
            assert self.marker() == token
            if token == target:
                return
        raise AssertionError("unknown target")

    def replace_file(self, path: Path, data: bytes) -> None:
        """TEST ONLY: delete and recreate a file inside a protected directory (inherits DACL)."""
        if os.path.lexists(path):
            os.remove(path)
        with open(path, "xb") as handle:
            handle.write(data)


@pytest.fixture(autouse=True)
def h(tmp_path, monkeypatch, capsys):
    base = tmp_path.resolve()
    profile = base / "profile"
    local = profile / "AppData" / "Local"
    local.mkdir(parents=True)
    (profile / "AppData" / "Roaming").mkdir()
    ctx = paths.LocationContext(
        str(local),
        str(profile),
        str(profile / "AppData" / "Roaming"),
        (str(base / "faketemp"),),
        (str(base / "fakesync"),),
    )

    def provider():
        return ctx

    monkeypatch.setattr(paths, "_location_context", provider)
    sid = winsec._token_facts().user_sid
    monkeypatch.setattr(winsec, "check_account", lambda: sid)
    monkeypatch.setattr(manifest, "run_preflight", lambda: None)
    monkeypatch.setattr(console, "_collect_console_facts", lambda: GOOD_CONSOLE)
    reader = FakeReader()
    monkeypatch.setattr(console, "_hidden_reader", lambda: reader)
    monkeypatch.setattr(sys, "tracebacklimit", getattr(sys, "tracebacklimit", 1000), raising=False)
    assert _inside(paths.resolve().root, base)
    harness = Harness(base, reader, capsys, sid)
    yield harness
    assert paths._location_context is provider, "location seam replaced by test"
    current = paths._location_context()
    assert _inside(current.local_appdata + "\\" + paths.ROOT_NAME, base), "resolved root escaped tmp_path"


# ---------------------------------------------------------------- manifest baseline

BASE_PREFIX = "C:\\PyCustody\\pythoncore-3.14-64"
VENV = "C:\\CustodyEnv\\venv"
SITE = VENV + "\\Lib\\site-packages"
HELPER_ROOT = "C:\\CustodyHelper"


def baseline_facts(**overrides) -> manifest.EnvironmentFacts:
    dists = (
        manifest.DistFacts("cryptography", "50.0.2", SITE, ("cp311-abi3-win_amd64",), "pip", False),
        manifest.DistFacts("cffi", "2.1.1", SITE, ("cp314-cp314-win_amd64",), "pip", False),
        manifest.DistFacts("pycparser", "3.0", SITE, ("py3-none-any",), "pip", False),
    )
    modules = (
        ("cryptography", SITE + "\\cryptography\\__init__.py"),
        ("cryptography.hazmat.bindings._rust", SITE + "\\cryptography\\hazmat\\bindings\\_rust.pyd"),
        ("cffi", SITE + "\\cffi\\__init__.py"),
        ("_cffi_backend", SITE + "\\_cffi_backend.cp314-win_amd64.pyd"),
        ("pycparser", SITE + "\\pycparser\\__init__.py"),
    )
    facts = manifest.EnvironmentFacts(
        version_info=(3, 14, 3, "final", 0),
        implementation="cpython",
        platform="win32",
        pointer_size=8,
        sysconfig_platform="win-amd64",
        gil_enabled=True,
        gil_disabled_build=False,
        isolated=True,
        ignore_environment=True,
        no_user_site=True,
        safe_path=True,
        enable_user_site=False,
        warnoptions=(),
        xoptions=(),
        debug_flags=(0, 0, 0, 0, 0),
        executable=VENV + "\\Scripts\\python.exe",
        base_executable=BASE_PREFIX + "\\python.exe",
        prefix=VENV,
        base_prefix=BASE_PREFIX,
        pyvenv_cfg="home = " + BASE_PREFIX + "\ninclude-system-site-packages = false\nversion = 3.14.3\n",
        sys_path=(
            BASE_PREFIX + "\\python314.zip",
            BASE_PREFIX + "\\DLLs",
            BASE_PREFIX + "\\Lib",
            BASE_PREFIX,
            VENV,
            SITE,
            HELPER_ROOT,
        ),
        helper_root=HELPER_ROOT,
        helper_file=HELPER_ROOT + "\\ed25519_custody_v0\\__init__.py",
        environ_names=("PATH", "SYSTEMROOT", "USERNAME"),
        site_entries=tuple(sorted(manifest._ALLOWED_SITE_ENTRIES | {"pip-25.3.dist-info"})),
        distributions=dists,
        module_files=modules,
        fallback_modules=(),
        record_result=None,
        openssl_version_text="OpenSSL 4.0.3 29 Sep 2026",
        interpreter_hashes=(("python.exe", "a" * 64), ("python314.dll", "b" * 64)),
    )
    return dataclasses.replace(facts, **overrides)


@pytest.fixture
def provenance(monkeypatch):
    monkeypatch.setattr(manifest, "_INTERPRETER_PROVENANCE", baseline_facts().interpreter_hashes)


def env_code(facts) -> str:
    from ed25519_custody_v0.errors import CustodyError

    try:
        manifest.evaluate(facts)
    except CustodyError as exc:
        return exc.code
    return "ACCEPTED"


def production_sources() -> dict:
    return {p.name: p.read_text(encoding="utf-8") for p in sorted(PKG_DIR.glob("*.py"))}
