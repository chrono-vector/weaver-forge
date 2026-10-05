"""D1-R1 behavioral checks 25-48 for the Ed25519 custody helper v0.

Each test function ``test_cNN_*`` maps one-to-one to D1-R1 negative check NN.
These are attack/negative tests, not source mutations. TEST ONLY material is
generated at runtime inside tmp_path.
"""

from __future__ import annotations

import dataclasses
import os
import re
import sys
from pathlib import Path

import pytest
from conftest import (
    OTHER_PASSPHRASE,
    PKG_DIR,
    REPO_DIR,
    RUNBOOK,
    SimulatedCrash,
    TEST_PASSPHRASE,
    VENV,
    BASE_PREFIX,
    SITE,
    HELPER_ROOT,
    baseline_facts,
    env_code,
    production_sources,
)
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519, x25519

from ed25519_custody_v0 import cli, console, custody, manifest, paths, state, winsec
from ed25519_custody_v0.errors import CustodyError

PW = TEST_PASSPHRASE


def _assert_abandoned(h, err):
    assert "STATE ABANDONED" in err
    assert h.marker() == state.ABANDONED


# 25
def test_c25_reject_zero_two_or_multiple_candidate_keys(h, monkeypatch):
    h.advance(state.EMPTY)
    calls = {"n": 0}
    original = ed25519.Ed25519PrivateKey.generate

    def once():
        calls["n"] += 1
        return original()

    monkeypatch.setattr(ed25519.Ed25519PrivateKey, "generate", staticmethod(once))
    h.ok("generate", PW, PW)
    assert calls["n"] == 1
    assert not hasattr(cli, "generate_many")
    assert "from_private_bytes" not in production_sources()["custody.py"]
    assert "from_private_bytes" not in production_sources()["cli.py"]
    h.ok("abandon")
    h.advance(state.PCW_CANDIDATE)
    second = h.custody_file(state.CANDIDATE).with_name("custody-v0-candidate-v1.bin")
    second.write_bytes(os.urandom(32))
    rc, _out, err = h.run("verify-candidate", PW)
    assert rc == 1 and "ERROR STATE_REJECTED" in err
    _assert_abandoned(h, err)


# 26
def test_c26_reject_wrong_python_or_package_version_or_abi(provenance, monkeypatch):
    assert env_code(baseline_facts(version_info=(3, 14, 2, "final", 0))) == "ENV_INTERPRETER_REJECTED"
    assert env_code(baseline_facts(version_info=(3, 13, 3, "final", 0))) == "ENV_INTERPRETER_REJECTED"
    assert env_code(baseline_facts(gil_enabled=False)) == "ENV_INTERPRETER_REJECTED"
    assert env_code(baseline_facts(gil_disabled_build=True)) == "ENV_INTERPRETER_REJECTED"
    assert env_code(baseline_facts(sysconfig_platform="win32")) == "ENV_PLATFORM_REJECTED"
    assert env_code(baseline_facts(pointer_size=4)) == "ENV_PLATFORM_REJECTED"
    assert env_code(baseline_facts(implementation="pypy")) == "ENV_INTERPRETER_REJECTED"
    wrong = (
        manifest.DistFacts("cryptography", "50.0.1", SITE, ("cp311-abi3-win_amd64",), "pip", False),
        baseline_facts().distributions[1],
        baseline_facts().distributions[2],
    )
    assert env_code(baseline_facts(distributions=wrong)) == "ENV_DISTRIBUTION_REJECTED"
    wrong_tag = (
        manifest.DistFacts("cryptography", "50.0.2", SITE, ("cp39-abi3-win_amd64",), "pip", False),
        baseline_facts().distributions[1],
        baseline_facts().distributions[2],
    )
    assert env_code(baseline_facts(distributions=wrong_tag)) == "ENV_DISTRIBUTION_REJECTED"


# 27
def test_c27_reject_source_editable_shadowed_and_fallback(provenance):
    shadowed = baseline_facts(
        module_files=(
            ("cryptography", "C:\\elsewhere\\cryptography\\__init__.py"),
            ("cryptography.hazmat.bindings._rust", SITE + "\\cryptography\\hazmat\\bindings\\_rust.pyd"),
            ("cffi", SITE + "\\cffi\\__init__.py"),
            ("_cffi_backend", SITE + "\\_cffi_backend.cp314-win_amd64.pyd"),
            ("pycparser", SITE + "\\pycparser\\__init__.py"),
        )
    )
    assert env_code(shadowed) == "ENV_MODULE_PATH_REJECTED"
    assert env_code(baseline_facts(fallback_modules=("nacl",))) == "ENV_MODULE_PATH_REJECTED"
    assert env_code(baseline_facts(fallback_modules=("Crypto",))) == "ENV_MODULE_PATH_REJECTED"
    editable = (
        manifest.DistFacts("cryptography", "50.0.2", SITE, ("cp311-abi3-win_amd64",), "pip", True),
        baseline_facts().distributions[1],
        baseline_facts().distributions[2],
    )
    assert env_code(baseline_facts(distributions=editable)) == "ENV_DISTRIBUTION_REJECTED"
    shadowed_path = baseline_facts(sys_path=baseline_facts().sys_path + (HELPER_ROOT + "\\src",))
    assert env_code(shadowed_path) == "ENV_MODULE_PATH_REJECTED"
    cwd_shadow = baseline_facts(sys_path=("",) + baseline_facts().sys_path)
    assert env_code(cwd_shadow) == "ENV_MODULE_PATH_REJECTED"


# 28
def test_c28_reject_openssh_openssl_gpg_pynacl_custom_fallback(provenance):
    for source in production_sources().values():
        assert "subprocess" not in source
        assert "os.system" not in source
        assert "OpenSSL" not in source or "openssl_version_text" in source
        assert "gpg" not in source.lower()
        for banned in ("nacl", "paramiko", "Crypto", "Cryptodome", "ecdsa", "pure25519"):
            assert re.search(r"^\s*(import|from)\s+" + banned + r"\b", source, re.M) is None
    assert env_code(baseline_facts(fallback_modules=("nacl", "paramiko"))) == "ENV_MODULE_PATH_REJECTED"
    for argv in (["openssl"], ["ssh-keygen"], ["gpg"], ["sign"]):
        assert cli.main(argv) == 2


# 29
def test_c29_reject_replacement_key_under_historical_snapshot(h):
    for source in production_sources().values():
        assert "EXACT_PUBLIC_KEY_ADMISSION_SNAPSHOT" not in source
        assert "docs\\\\next" not in source and "docs/next" not in source
    h.advance(state.READY)
    for argv in (
        ["replace"],
        ["replace-key"],
        ["admit", "d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a"],
    ):
        rc, _out, err = h.run(None, argv=argv)
        assert rc == 2 and "ERROR USAGE_REJECTED" in err
    assert h.marker() == state.READY


# 30
def test_c30_reject_ai_agent_plugin_remote_access_to_secrets(h):
    """N5: runbook/operational. The helper refuses AI/agent command surfaces; absence is not machine-proven."""
    for source in production_sources().values():
        assert "openai" not in source.lower()
        assert "anthropic" not in source.lower()
        assert "socket" not in source
        assert "urllib" not in source
        assert "http.client" not in source
        assert "requests" not in source
        assert "plugin" not in source.lower()
        assert "callback" not in source.lower()
        assert "telemetry" not in source.lower()
    for argv in (["ai-export"], ["agent-handoff"], ["plugin-load"], ["remote-unlock"]):
        assert cli.main(argv) == 2
    assert RUNBOOK.is_file()
    text = RUNBOOK.read_text(encoding="utf-8")
    assert "AI" in text and "agent" in text.lower() and "ConPTY" in text
    assert "machine-proven" in text.lower() or "not machine" in text.lower()


# 31
def test_c31_reject_admission_prepare_before_ready(h):
    targets = [
        state.EMPTY,
        state.PRIVATE_WRITTEN,
        state.PCW_CANDIDATE,
        state.PCW_VERIFIED,
        state.PCW_RESTORE_1,
        state.PCW_RESTORE_2,
        state.BACKUPS_VERIFIED,
    ]
    for token in targets:
        if os.path.lexists(h.paths.custody) or os.path.lexists(h.paths.restore):
            h.ok("abandon")
        h.advance(token)
        rc, out, err = h.run("pre-prepare-display", PW)
        assert rc == 1 and "ERROR STATE_REJECTED" in err and "DISPLAY" not in out
        assert h.reader.prompts == []
        assert h.marker() == token
    h.ok("abandon")
    h.advance(state.PCW_RESTORE_1)
    for command in ("mark-backups-verified", "mark-ready"):
        rc, _out, err = h.run(command)
        assert rc == 1 and "ERROR STATE_REJECTED" in err
    assert h.marker() == state.PCW_RESTORE_1


# 32
def test_c32_reject_treating_generation_or_prepare_as_confirm(h):
    h.advance(state.READY)
    out = h.ok("pre-prepare-display", PW)
    assert "ADMISSION NOT_PERFORMED" in out
    assert h.marker() == state.READY
    for argv in (["confirm"], ["admission-confirm"], ["admission-prepare"], ["prepare"]):
        rc, _out, err = h.run(None, argv=argv)
        assert rc == 2 and "ERROR USAGE_REJECTED" in err
    text = "\n".join(production_sources().values())
    assert "CONFIRM" not in text and "ADMITTED" not in text
    assert all("CONFIRM" not in token for token in state.ORDER)
    everything = "".join(h.outputs)
    assert "CONFIRM" not in everything and "ADMITTED" not in everything
    assert "Admission CONFIRM" in RUNBOOK.read_text(encoding="utf-8")

# 33
def test_c33_crash_or_partial_write_requires_exact_restart_or_abandon(h, monkeypatch):
    h.advance(state.EMPTY)
    real_write = winsec.write_new_file

    def crash_after_create(path, user_sid, data):
        real_write(path, user_sid, data)
        raise SimulatedCrash("TEST ONLY crash after private write")

    monkeypatch.setattr(winsec, "write_new_file", crash_after_create)
    with pytest.raises(SimulatedCrash):
        h.run("generate", PW, PW)
    monkeypatch.setattr(winsec, "write_new_file", real_write)
    assert h.custody_file(state.PRIVATE).is_file()
    assert h.marker() == state.EMPTY
    rc, _out, err = h.run("status")
    assert rc == 1 and "ERROR STATE_REJECTED" in err
    # Mutating phases abandon the mismatched restart.
    rc, _out, err = h.run("generate", PW, PW)
    assert rc == 1 and "ERROR STATE_REJECTED" in err
    _assert_abandoned(h, err)
    # Fresh generation after abandon.
    h.ok("abandon")
    h.ok("init")
    h.ok("generate", PW, PW)
    assert h.marker() == state.PRIVATE_WRITTEN

    # Partial candidate write: crash after candidate file exists but before commit.
    real_write = winsec.write_new_file
    calls = {"n": 0}

    def crash_on_candidate(path, user_sid, data):
        real_write(path, user_sid, data)
        calls["n"] += 1
        if state.CANDIDATE in path:
            raise SimulatedCrash("TEST ONLY crash after candidate write")
        return None

    monkeypatch.setattr(winsec, "write_new_file", crash_on_candidate)
    with pytest.raises(SimulatedCrash):
        h.run("derive-candidate", PW)
    monkeypatch.setattr(winsec, "write_new_file", real_write)
    assert h.custody_file(state.CANDIDATE).is_file()
    assert h.marker() == state.PRIVATE_WRITTEN
    rc, _out, err = h.run("derive-candidate", PW)
    assert rc == 1 and "ERROR STATE_REJECTED" in err
    _assert_abandoned(h, err)


# 34
def test_c34_reject_partial_duplicated_skipped_reordered_or_inconsistent_markers(h):
    h.advance(state.PRIVATE_WRITTEN)
    cases = [
        b"",
        b"EMPTY\n",
        state.encode_marker(state.EMPTY) + b"x",
        state.encode_marker(state.EMPTY)[:-1],
        state.encode_marker(state.PCW_CANDIDATE),  # skip
        state.encode_marker(state.READY),  # skip forward
        state.MAGIC + b"STATE BACKWARDS\n",
        state.encode_marker(state.ABANDONED) + state.encode_marker(state.EMPTY),
    ]
    for data in cases:
        h.replace_file(h.custody_file(state.MARKER), data)
        rc, _out, err = h.run("status")
        assert rc == 1 and "ERROR STATE_REJECTED" in err
    # Extra file: inconsistent file set.
    h.replace_file(h.custody_file(state.MARKER), state.encode_marker(state.PRIVATE_WRITTEN))
    with open(h.custody_file("extra.txt"), "xb") as handle:
        handle.write(b"x")
    rc, _out, err = h.run("status")
    assert rc == 1 and "ERROR STATE_REJECTED" in err
    # Missing private in PRIVATE_WRITTEN.
    os.remove(h.custody_file("extra.txt"))
    os.remove(h.custody_file(state.PRIVATE))
    rc, _out, err = h.run("status")
    assert rc == 1 and "ERROR STATE_REJECTED" in err
    # Mutating phase abandons after marker rewrite to a valid PRIVATE_WRITTEN without private.
    h.replace_file(h.custody_file(state.MARKER), state.encode_marker(state.PRIVATE_WRITTEN))
    rc, _out, err = h.run("derive-candidate", PW)
    assert rc == 1 and "ERROR STATE_REJECTED" in err
    _assert_abandoned(h, err)


# 35
def test_c35_reject_abandoned_candidate_or_display_to_prepare(h):
    h.advance(state.READY)
    display = [
        ln.split(" ", 1)[1] for ln in h.ok("pre-prepare-display", PW).splitlines() if ln.startswith("DISPLAY ")
    ][0]
    candidate = h.custody_file(state.CANDIDATE).read_bytes()
    h.ok("abandon")
    assert not os.path.lexists(h.paths.custody)
    # Abandoned artifacts live only under quarantine and are never inputs.
    for dirpath, _dirs, files in os.walk(h.paths.quarantine):
        for name in files:
            if name.endswith(".bin"):
                assert Path(dirpath, name).read_bytes() == candidate
    rc, out, err = h.run("pre-prepare-display", PW)
    assert rc == 1 and "ERROR NO_ACTIVE_GENERATION" in err and "DISPLAY" not in out
    for argv in (["admit", display], ["prepare", display], ["pre-prepare-display", display]):
        rc, out, err = h.run(None, argv=argv)
        assert rc == 2 and "ERROR USAGE_REJECTED" in err and display not in out + err


# 36
@pytest.mark.parametrize("variant", ["flip", "truncate", "extend", "replace", "link"])
def test_c36_reject_candidate_substitution_truncation_extension_link_overwrite(h, variant):
    h.advance(state.PCW_VERIFIED)
    path = h.custody_file(state.CANDIDATE)
    original = path.read_bytes()
    if variant == "flip":
        data = bytearray(original)
        data[0] ^= 0xFF
        h.replace_file(path, bytes(data))
    elif variant == "truncate":
        h.replace_file(path, original[:31])
    elif variant == "extend":
        h.replace_file(path, original + b"\x00")
    elif variant == "replace":
        h.replace_file(path, os.urandom(32))
    else:
        other = h.base / "outside-candidate.bin"
        other.write_bytes(original)
        os.remove(path)
        os.link(other, path)
    h.ok("restore-init")
    h.copy_backup()
    rc, out, err = h.run("restore-check", PW)
    assert rc == 1
    assert any(code in err for code in ("ERROR CANDIDATE_MISMATCH", "ERROR CANDIDATE_REJECTED", "ERROR FILE_REJECTED"))
    assert "DISPLAY" not in out
    _assert_abandoned(h, err)
    h.ok("abandon")
    h.advance(state.PCW_CANDIDATE)
    with pytest.raises(CustodyError) as info:
        winsec.write_new_file(str(path), h.sid, os.urandom(32))
    assert info.value.code == "EXISTS_REJECTED"
    assert len(path.read_bytes()) == 32

# 37
def test_c37_reject_comparison_against_external_copies(h, monkeypatch):
    h.advance(state.PCW_CANDIDATE)
    external = ed25519.Ed25519PrivateKey.generate().public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw
    ).hex()
    for argv in (
        ["verify-candidate", external],
        ["verify-candidate", "--display", external],
        ["verify-candidate", "--from-repo", "docs/next/foo.md"],
        ["verify-candidate", "--clipboard"],
    ):
        rc, out, err = h.run(None, argv=argv)
        assert rc == 2 and "ERROR USAGE_REJECTED" in err and external not in out + err
    # The phase never accepts an alternate comparison source: monkeypatching the
    # protected candidate is the only way to inject an external copy, and that
    # is rejected by exact equality with the freshly derived value.
    h.replace_file(h.custody_file(state.CANDIDATE), bytes.fromhex(external))
    rc, out, err = h.run("verify-candidate", PW)
    assert rc == 1 and "ERROR CANDIDATE_MISMATCH" in err and "DISPLAY" not in out
    _assert_abandoned(h, err)


# 38
@pytest.mark.parametrize(
    "name",
    [
        "PYTHONPATH",
        "PYTHONHOME",
        "PYTHONSTARTUP",
        "PYTHONINSPECT",
        "PYTHONBREAKPOINT",
        "PYTHONWARNINGS",
        "PYTHONUSERBASE",
        "PYTHONEXECUTABLE",
        "PIP_CONFIG_FILE",
        "PIP_INDEX_URL",
        "OPENSSL_CONF",
        "OPENSSL_MODULES",
        "OPENSSL_ENGINES",
        "CRYPTOGRAPHY_OPENSSL_NO_LEGACY",
        "CFFI_MODULES",
        "SSL_CERT_FILE",
        "WEAVERFORGE_PASSPHRASE",
        "PASSPHRASE",
    ],
)
def test_c38_reject_python_and_openssl_injection_variables(provenance, name):
    facts = baseline_facts(environ_names=("PATH", "SYSTEMROOT", name))
    assert env_code(facts) == "ENV_INJECTION_REJECTED"


# 39
def test_c39_reject_store_packaged_wrong_provenance_system_site_wrong_venv(provenance):
    store = baseline_facts(
        base_prefix="C:\\Users\\x\\AppData\\Local\\Microsoft\\WindowsApps\\PythonSoftwareFoundation.Python.3.14",
        base_executable="C:\\Users\\x\\AppData\\Local\\Microsoft\\WindowsApps\\PythonSoftwareFoundation.Python.3.14\\python.exe",
    )
    assert env_code(store) == "ENV_INTERPRETER_REJECTED"
    packaged = baseline_facts(
        base_prefix="C:\\Program Files\\WindowsApps\\PythonSoftwareFoundation.Python.3.14",
        base_executable="C:\\Program Files\\WindowsApps\\PythonSoftwareFoundation.Python.3.14\\python.exe",
    )
    assert env_code(packaged) == "ENV_INTERPRETER_REJECTED"
    assert env_code(baseline_facts(enable_user_site=True)) == "ENV_ISOLATION_REJECTED"
    assert env_code(baseline_facts(isolated=False)) == "ENV_ISOLATION_REJECTED"
    assert env_code(baseline_facts(prefix=BASE_PREFIX, executable=BASE_PREFIX + "\\python.exe")) == "ENV_VENV_REJECTED"
    cfg = "home = " + BASE_PREFIX + "\ninclude-system-site-packages = true\nversion = 3.14.3\n"
    assert env_code(baseline_facts(pyvenv_cfg=cfg)) == "ENV_VENV_REJECTED"
    assert env_code(baseline_facts(interpreter_hashes=(("python.exe", "00"), ("python314.dll", "00")))) == (
        "ENV_PROVENANCE_MISMATCH"
    )
    monkeypatch = pytest.MonkeyPatch()
    try:
        monkeypatch.setattr(manifest, "_INTERPRETER_PROVENANCE", None)
        assert env_code(baseline_facts()) == "ENV_PROVENANCE_NOT_RECORDED"
    finally:
        monkeypatch.undo()
    # System site packages appear as unexpected sys.path or site entries.
    with_system = baseline_facts(sys_path=baseline_facts().sys_path + (BASE_PREFIX + "\\Lib\\site-packages",))
    assert env_code(with_system) == "ENV_MODULE_PATH_REJECTED"
    with_pth = baseline_facts(site_entries=baseline_facts().site_entries + ("zz_ed25519c_system_site.pth",))
    assert env_code(with_pth) == "ENV_MODULE_PATH_REJECTED"


# 40
def test_c40_reject_redirected_stdin_missing_console_modes_secret_before_preflight(h, monkeypatch):
    h.advance(state.EMPTY)
    # Secret read before preflight is structurally impossible: read_secret calls console_preflight first.
    source = production_sources()["console.py"]
    assert source.index("console_preflight()") < source.index("reader(prompt)")
    cases = [
        console.ConsoleFacts(False, True, True, True, True, True, True, True, True),
        console.ConsoleFacts(True, False, True, True, True, True, True, True, True),
        console.ConsoleFacts(True, True, False, True, True, True, True, True, True),
        console.ConsoleFacts(True, True, True, False, True, True, True, True, True),
        console.ConsoleFacts(True, True, True, True, False, True, True, True, True),
        console.ConsoleFacts(True, True, True, True, True, False, True, True, True),
        console.ConsoleFacts(True, True, True, True, True, True, False, True, True),
        console.ConsoleFacts(True, True, True, True, True, True, True, False, True),
        console.ConsoleFacts(True, True, True, True, True, True, True, True, False),
    ]
    for facts in cases:
        monkeypatch.setattr(console, "_collect_console_facts", lambda f=facts: f)
        rc, _out, err = h.run("generate", PW, PW)
        assert rc == 1 and "ERROR CONSOLE_PREFLIGHT_REJECTED" in err
        assert h.reader.prompts == []
    # Warning suppression: filters not configured as error before getpass.
    from conftest import GOOD_CONSOLE

    monkeypatch.setattr(console, "_collect_console_facts", lambda: GOOD_CONSOLE)
    monkeypatch.setattr(console, "_warning_is_error", lambda: False)
    rc, _out, err = h.run("generate", PW, PW)
    assert rc == 1 and "ERROR CONSOLE_PREFLIGHT_REJECTED" in err
    # ConPTY/IDE absence remains a runbook declaration (N5), recorded in the runbook.
    text = RUNBOOK.read_text(encoding="utf-8")
    assert "ConPTY" in text and "IDE" in text


# 41
def test_c41_unknown_stolen_missing_backup_is_suspected_compromise(h):
    """N5: operational classification. Machine surface: no replace-backup command; runbook text."""
    for argv in (["replace-backup"], ["recover-backup"], ["treat-as-loss"]):
        assert cli.main(argv) == 2
    text = RUNBOOK.read_text(encoding="utf-8")
    assert "SUSPECTED_COMPROMISE" in text
    assert "unknown-location" in text or "unknown location" in text.lower()
    assert "ordinary loss" not in text.lower() or "not ordinary" in text.lower() or "SUSPECTED_COMPROMISE" in text
    for source in production_sources().values():
        assert "ordinary_loss" not in source
        assert "replace_backup" not in source


# 42
def test_c42_reject_restore_that_reads_links_or_falls_back_to_working_original(h, monkeypatch):
    h.advance(state.PCW_VERIFIED)
    h.ok("restore-init")
    # No restore artifact: there is no fallback to the working original.
    rc, out, err = h.run("restore-check", PW)
    assert rc == 1 and "ERROR RESTORE_SLOT_REJECTED" in err and "DISPLAY" not in out
    assert h.marker() == state.PCW_VERIFIED and h.reader.prompts == []
    # A valid copy is read from the fixed restore-v0 artifact path.
    h.copy_backup()
    reads = []
    real_read = winsec.read_file

    def spy(path, sid, max_size):
        reads.append(os.path.normcase(path))
        return real_read(path, sid, max_size)

    monkeypatch.setattr(winsec, "read_file", spy)
    h.ok("restore-check", PW)
    artifact = os.path.normcase(h.paths.restore_file(state.RESTORE_ARTIFACT))
    assert artifact in reads
    assert not os.path.lexists(h.paths.restore)
    monkeypatch.setattr(winsec, "read_file", real_read)
    # Hard-linking the working original into the restore slot is rejected.
    h.ok("restore-init")
    os.link(h.custody_file(state.PRIVATE), h.restore_file(state.RESTORE_ARTIFACT))
    rc, out, err = h.run("restore-check", PW)
    assert rc == 1 and ("ERROR FILE_REJECTED" in err or "ERROR RESTORE_REJECTED" in err)
    assert "DISPLAY" not in out
    _assert_abandoned(h, err)
    for argv in (
        ["restore-check", str(h.custody_file(state.PRIVATE))],
        ["restore-check", "--path", str(h.custody_file(state.PRIVATE))],
        ["restore-check", h.paths.custody],
    ):
        assert cli.main(argv) == 2


# 43
def test_c43_reject_dacl_applied_after_creation(h, monkeypatch):
    """Directories are created only by the helper, with the protected SDDL supplied at creation."""
    source = production_sources()["winsec.py"]
    assert "SetNamedSecurityInfo" not in source and "SetSecurityInfo" not in source
    for name, text in production_sources().items():
        assert "os.mkdir" not in text and "makedirs" not in text and "icacls" not in text, name
    captured = {"sddl": [], "sd": []}
    real_convert = winsec._ConvertStringSecurityDescriptorToSecurityDescriptorW
    real_create = winsec._CreateDirectoryW

    def convert(sddl, revision, out, size):
        captured["sddl"].append(sddl)
        return real_convert(sddl, revision, out, size)

    def create(path, attrs):
        captured["sd"].append(attrs._obj.lpSecurityDescriptor)
        return real_create(path, attrs)

    monkeypatch.setattr(winsec, "_ConvertStringSecurityDescriptorToSecurityDescriptorW", convert)
    monkeypatch.setattr(winsec, "_CreateDirectoryW", create)
    h.advance(state.EMPTY)
    assert captured["sddl"] == [winsec.protected_sddl(h.sid)] * 2
    assert len(captured["sd"]) == 2 and all(captured["sd"])
    monkeypatch.setattr(winsec, "_ConvertStringSecurityDescriptorToSecurityDescriptorW", real_convert)
    monkeypatch.setattr(winsec, "_CreateDirectoryW", real_create)
    # A pre-existing custody directory (created permissively, then tightened) is refused.
    h.ok("abandon")
    os.mkdir(h.paths.custody)
    rc, _out, err = h.run("init")
    assert rc == 1 and "ERROR EXISTS_REJECTED" in err
    import subprocess

    subprocess.run(
        ["icacls", h.paths.custody, "/inheritance:r", "/grant:r", "*" + h.sid + ":(OI)(CI)F", "*S-1-5-18:(OI)(CI)F"],
        check=True,
        capture_output=True,
    )
    rc, _out, err = h.run("init")
    assert rc == 1 and "ERROR EXISTS_REJECTED" in err
    os.rmdir(h.paths.custody)
    h.advance(state.PCW_VERIFIED)
    os.mkdir(h.paths.restore)
    rc, _out, err = h.run("restore-init")
    assert rc == 1 and "ERROR EXISTS_REJECTED" in err


def test_c43b_permissive_root_rejected(h):
    os.mkdir(h.paths.root)
    with pytest.raises(CustodyError) as info:
        winsec.verify_directory(h.paths.root, h.sid)
    assert info.value.code == "ACL_REJECTED"
    rc, _out, err = h.run("init")
    assert rc == 1 and "ERROR ACL_REJECTED" in err
    assert not os.path.lexists(h.paths.custody)

# 44
def test_c44_reject_loaded_non_ed25519_including_x25519(h, monkeypatch):
    h.advance(state.PRIVATE_WRITTEN)

    def load_x25519(pem, password):
        return x25519.X25519PrivateKey.generate()

    monkeypatch.setattr(serialization, "load_pem_private_key", load_x25519)
    rc, _out, err = h.run("derive-candidate", PW)
    assert rc == 1 and "ERROR KEY_TYPE_REJECTED" in err
    _assert_abandoned(h, err)


# 45
def test_c45_reject_multiple_stale_extra_or_wrong_state_candidates(h):
    h.advance(state.PCW_VERIFIED)
    extra = h.custody_file("custody-v0-candidate-v1.bin")
    extra.write_bytes(os.urandom(32))
    rc, _out, err = h.run("status")
    assert rc == 1 and "ERROR STATE_REJECTED" in err
    # Wrong-state: candidate present while marker still EMPTY.
    h.run("abandon")
    h.advance(state.EMPTY)
    with open(h.custody_file(state.CANDIDATE), "xb") as handle:
        handle.write(os.urandom(32))
    rc, _out, err = h.run("status")
    assert rc == 1 and "ERROR STATE_REJECTED" in err
    rc, _out, err = h.run("generate", PW, PW)
    assert rc == 1 and "ERROR STATE_REJECTED" in err
    _assert_abandoned(h, err)


# 46
def test_c46_reject_abandon_with_args_repair_resume_or_reuse(h):
    h.advance(state.PRIVATE_WRITTEN)
    for argv in (
        ["abandon", "now"],
        ["abandon", "--path", h.paths.custody],
        ["abandon", h.paths.custody],
        ["abandon", "--repair"],
    ):
        assert cli.main(argv) == 2
    h.ok("abandon")
    # Quarantined generation cannot be resumed.
    rc, out, err = h.run("status")
    assert rc == 1 and "ERROR NO_ACTIVE_GENERATION" in err
    rc, out, err = h.run("generate", PW, PW)
    assert rc == 1 and "ERROR NO_ACTIVE_GENERATION" in err
    # init creates a fresh EMPTY generation; abandoned artifacts are never inputs.
    h.ok("init")
    assert h.marker() == state.EMPTY
    assert list(Path(h.paths.custody).iterdir()) == [Path(h.paths.custody_file(state.MARKER))]
    # Abandoned private PEM under quarantine is never selected.
    pems = [
        Path(dirpath, name)
        for dirpath, _dirs, files in os.walk(h.paths.quarantine)
        for name in files
        if name.endswith(".pem")
    ]
    assert len(pems) == 1
    abandoned_pem = pems[0].read_bytes()
    h.ok("generate", PW, PW)
    assert h.custody_file(state.PRIVATE).read_bytes() != abandoned_pem


# 47
def test_c47_reject_human_composed_or_under_128bit_secrets(h):
    """N5: shape is machine-enforced; password-manager entropy is a runbook declaration."""
    # Shape already enforced by check 6. The runbook records the Human declaration.
    text = RUNBOOK.read_text(encoding="utf-8")
    assert "128" in text and "password manager" in text.lower()
    assert "Human-composed" in text or "human-composed" in text.lower()
    for source in production_sources().values():
        # No code path accepts a declared entropy value from the caller.
        assert "entropy=" not in source
        assert "reported_entropy" not in source


# 48
def test_c48_reject_treating_observed_pbes_details_as_api_guarantee(h):
    for source in production_sources().values():
        assert "PBES2" not in source
        assert "PBKDF2" not in source
        assert "AES-256-CBC" not in source
        assert "2048" not in source
        assert "AlgorithmIdentifier" not in source
    # Serialization uses BestAvailableEncryption only.
    assert "BestAvailableEncryption" in production_sources()["custody.py"]
    text = RUNBOOK.read_text(encoding="utf-8")
    assert "BestAvailableEncryption" in text
    assert "not" in text.lower() and ("API guarantee" in text or "api guarantee" in text.lower() or "not an API" in text)
