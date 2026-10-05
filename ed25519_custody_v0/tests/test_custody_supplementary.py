"""Supplementary tests: N1-N4 absorption, real Windows/manifest probes, CLI shape.

These are additional attack/regression tests beyond the 48 frozen checks.
TEST ONLY material is generated at runtime inside tmp_path.
"""

from __future__ import annotations

import ast
import dataclasses
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest
from conftest import (
    GOOD_CONSOLE,
    OTHER_PASSPHRASE,
    PKG_DIR,
    REAL,
    TEST_PASSPHRASE,
    baseline_facts,
    env_code,
    production_sources,
)
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519

from ed25519_custody_v0 import cli, console, custody, errors, manifest, paths, state, winsec
from ed25519_custody_v0.errors import CODES, CustodyError

PW = TEST_PASSPHRASE


def _code(fn, *args):
    with pytest.raises(CustodyError) as info:
        fn(*args)
    return info.value.code


def test_x01_n1_real_protected_directory_and_inherited_file_acl(h):
    h.advance(state.PRIVATE_WRITTEN)
    winsec.verify_directory(h.paths.custody, h.sid)
    winsec.verify_directory(h.paths.root, h.sid)
    data, _identity = winsec.read_file(h.paths.custody_file(state.PRIVATE), h.sid, custody.MAX_PEM)
    assert data.startswith(custody.PEM_BEGIN)
    # A file created by a plain open() inside the protected directory inherits only the two ACEs.
    probe = Path(h.paths.custody) / "probe.bin"
    probe.write_bytes(b"x")
    assert winsec.read_file(str(probe), h.sid, 8)[0] == b"x"
    probe.unlink()


def test_x02_n2_ready_failures_do_not_transition(h):
    h.advance(state.READY)
    rc, out, err = h.run("pre-prepare-display", OTHER_PASSPHRASE)
    assert rc == 1 and "ERROR KEY_RELOAD_REJECTED" in err and "STATE ABANDONED" not in err
    assert h.marker() == state.READY and "DISPLAY" not in out
    original = h.custody_file(state.CANDIDATE).read_bytes()
    h.replace_file(h.custody_file(state.CANDIDATE), original[:31])
    rc, _out, err = h.run("pre-prepare-display", PW)
    assert rc == 1 and "ERROR CANDIDATE_REJECTED" in err and "STATE ABANDONED" not in err
    assert h.marker() == state.READY
    h.replace_file(h.custody_file(state.CANDIDATE), original)
    with open(h.custody_file("stray.txt"), "xb") as handle:
        handle.write(b"x")
    rc, _out, err = h.run("pre-prepare-display", PW)
    assert rc == 1 and "ERROR STATE_REJECTED" in err and "STATE ABANDONED" not in err
    assert h.marker() == state.READY
    os.remove(h.custody_file("stray.txt"))
    out = h.ok("pre-prepare-display", PW)
    assert "DISPLAY " + original.hex() in out
    # Explicit Human abandon of a READY generation remains available.
    h.ok("abandon")
    assert not os.path.lexists(h.paths.custody)


def test_x03_n3_quarantine_is_fixed_protected_and_tombstoned(h):
    h.advance(state.PCW_VERIFIED)
    h.ok("restore-init")
    pem = h.custody_file(state.PRIVATE).read_bytes()
    out = h.ok("abandon")
    assert out.splitlines() == ["STATE ABANDONED", "ACTIVE_HANDOFF NONE", "PHYSICAL_ERASURE NOT_CLAIMED"]
    quarantine = Path(h.paths.quarantine)
    assert quarantine.parent == Path(h.paths.root) and quarantine.name == "abandoned-v0"
    winsec.verify_directory(str(quarantine), h.sid)
    names = sorted(p.name for p in quarantine.iterdir())
    assert len(names) == 3
    custody_dirs = [n for n in names if n.startswith("custody-v0-")]
    restore_dirs = [n for n in names if n.startswith("restore-v0-")]
    tombstones = [n for n in names if n.endswith(".abandoned")]
    assert len(custody_dirs) == len(restore_dirs) == len(tombstones) == 1
    moved = quarantine / custody_dirs[0]
    winsec.verify_directory(str(moved), h.sid)
    assert (moved / state.PRIVATE).read_bytes() == pem
    assert state.decode_marker((moved / state.MARKER).read_bytes()) == state.ABANDONED
    assert state.decode_marker((quarantine / tombstones[0]).read_bytes()) == state.ABANDONED
    assert not os.path.lexists(h.paths.custody) and not os.path.lexists(h.paths.restore)
    rc, _out, err = h.run("abandon")
    assert rc == 1 and "ERROR NO_ACTIVE_GENERATION" in err


def test_x04_n4_restore_marker_and_slot_rules(h):
    h.advance(state.PCW_VERIFIED)
    h.ok("restore-init")
    assert state.decode_restore_marker(h.restore_file(state.RESTORE_MARKER).read_bytes()) == 1
    rc, _out, err = h.run("restore-init")
    assert rc == 1 and "ERROR EXISTS_REJECTED" in err
    h.replace_file(h.restore_file(state.RESTORE_MARKER), state.encode_restore_marker(2))
    h.copy_backup()
    rc, _out, err = h.run("restore-check", PW)
    assert rc == 1 and "ERROR RESTORE_SLOT_REJECTED" in err
    assert "STATE ABANDONED" in err and h.marker() == state.ABANDONED


def test_x04b_restore_slot_extra_file_and_clear(h):
    h.advance(state.PCW_VERIFIED)
    h.ok("restore-init")
    h.copy_backup()
    out = h.ok("restore-clear")
    assert "RESTORE_SLOT_CLEARED" in out and not os.path.lexists(h.paths.restore)
    assert h.marker() == state.PCW_VERIFIED
    h.ok("restore-init")
    h.copy_backup()
    with open(h.restore_file("other.pem"), "xb") as handle:
        handle.write(b"x")
    rc, _out, err = h.run("restore-check", PW)
    assert rc == 1 and "ERROR RESTORE_SLOT_REJECTED" in err and h.marker() == state.ABANDONED
    out = h.ok("restore-clear")
    assert not os.path.lexists(h.paths.restore)
    moved = [p.name for p in Path(h.paths.quarantine).iterdir() if p.name.startswith("restore-v0-")]
    assert len(moved) == 1


def test_x04c_second_restore_requires_fresh_slot_and_order(h):
    h.advance(state.PCW_RESTORE_1)
    assert not os.path.lexists(h.paths.restore)
    h.ok("restore-init")
    assert state.decode_restore_marker(h.restore_file(state.RESTORE_MARKER).read_bytes()) == 2
    h.copy_backup()
    out = h.ok("restore-check", PW)
    assert "RESTORE_CHECK_PASSED 2" in out and h.marker() == state.PCW_RESTORE_2
    rc, _out, err = h.run("restore-init")
    assert rc == 1 and "ERROR STATE_REJECTED" in err
    os.mkdir(h.paths.restore)
    rc, _out, err = h.run("mark-backups-verified")
    assert rc == 1 and "ERROR RESTORE_SLOT_REJECTED" in err
    assert h.marker() == state.PCW_RESTORE_2


_X05_PROBE = r"""
import sys
sys.path.insert(0, sys.argv[1])
from ed25519_custody_v0 import paths
from ed25519_custody_v0.errors import CustodyError
try:
    ctx = paths._windows_location_context()
    paths.validate_context(ctx)
except CustodyError as exc:
    print("REJECTED", exc.code)
else:
    print("CONTEXT", ctx.local_appdata)
"""


def test_x05_real_location_context_ignores_environment_overrides(tmp_path):
    """Known-folder lookup may expand %USERPROFILE% from the process environment when
    uncached. A redirect must never produce a usable context: it either resolves to the
    real profile or the profile/local cross-check rejects it (fail closed)."""
    assert REAL["location_context"] is paths._windows_location_context
    ctx = REAL["location_context"]()
    paths.validate_context(ctx)
    assert ctx.local_appdata.lower().endswith("\\appdata\\local")
    assert os.path.normcase(tempfile.gettempdir()) in [os.path.normcase(t) for t in ctx.temp_dirs]
    real_local = os.path.normcase(ctx.local_appdata)
    existing = tmp_path / "evil"
    (existing / "AppData" / "Local").mkdir(parents=True)
    (existing / "AppData" / "Roaming").mkdir(parents=True)
    for target in (existing, tmp_path / "missing"):
        env = dict(os.environ)
        env.update(
            USERPROFILE=str(target),
            LOCALAPPDATA=str(target / "AppData" / "Local"),
            APPDATA=str(target / "AppData" / "Roaming"),
            WEAVERFORGE_ROOT=str(target),
            PYTHONDONTWRITEBYTECODE="1",
        )
        result = subprocess.run(
            [sys.executable, "-c", _X05_PROBE, str(PKG_DIR.parent)],
            env=env,
            capture_output=True,
            text=True,
            timeout=60,
        )
        line = result.stdout.strip()
        assert result.returncode == 0, result.stderr
        if line.startswith("CONTEXT "):
            assert os.path.normcase(line[len("CONTEXT "):]) == real_local
        else:
            assert line == "REJECTED PATH_REJECTED"
        assert str(tmp_path).lower() not in line.lower()


def test_x06_account_evaluation(h):
    good = winsec.TokenFacts("S-1-5-21-1-2-3-1001", False, 1, ("S-1-1-0", "S-1-5-32-545"), False)
    assert winsec.evaluate_account(good) == "S-1-5-21-1-2-3-1001"
    bad = [
        winsec.TokenFacts("S-1-5-21-1-2-3-1001", True, 1, (), False),
        winsec.TokenFacts("S-1-5-21-1-2-3-1001", False, 2, (), False),
        winsec.TokenFacts("S-1-5-21-1-2-3-1001", False, 3, (), False),
        winsec.TokenFacts("S-1-5-21-1-2-3-1001", False, 1, (), True),
        winsec.TokenFacts("S-1-5-21-1-2-3-1001", False, 1, ("S-1-5-32-544",), False),
        winsec.TokenFacts("S-1-5-21-1-2-3-1001", False, 1, ("S-1-5-114",), False),
        winsec.TokenFacts("S-1-5-21-1-2-3-1001", False, 1, ("S-1-5-6",), False),
        winsec.TokenFacts("S-1-5-21-1-2-3-1001", False, 1, ("S-1-5-32-551",), False),
        winsec.TokenFacts("S-1-5-21-1-2-3-1001", False, 1, ("S-1-5-21-9-9-9-512",), False),
        winsec.TokenFacts("S-1-5-18", False, 1, (), False),
        winsec.TokenFacts("S-1-5-20", False, 1, (), False),
    ]
    for facts in bad:
        assert _code(winsec.evaluate_account, facts) == "ACCOUNT_REJECTED"
    real = winsec._token_facts()
    assert real.user_sid.startswith("S-1-5-21-")
    try:
        assert REAL["check_account"]() == real.user_sid
    except CustodyError as exc:
        assert exc.code == "ACCOUNT_REJECTED"


def test_x07_real_test_venv_is_not_the_prereal_environment(h):
    facts = manifest.collect_facts()
    venv_site = os.path.normcase(os.path.join(sys.prefix, "Lib", "site-packages"))
    files = dict(facts.module_files)
    assert os.path.normcase(files["cryptography"]).startswith(venv_site)
    assert os.path.normcase(files["cffi"]).startswith(venv_site)
    assert os.path.normcase(files["pycparser"]).startswith(venv_site)
    assert facts.openssl_version_text == manifest._OPENSSL_VERSION_TEXT
    assert facts.record_result is None
    assert _code(REAL["run_preflight"]) != "ACCEPTED"
    assert manifest._INTERPRETER_PROVENANCE is None


def test_x08_record_verification_real_and_tampered(tmp_path):
    site = os.path.join(sys.prefix, "Lib", "site-packages")
    assert manifest.verify_records(site) is None
    import shutil

    copy = tmp_path / "site"
    copy.mkdir()
    shutil.copytree(os.path.join(site, "pycparser"), copy / "pycparser")
    shutil.copytree(os.path.join(site, "pycparser-3.0.dist-info"), copy / "pycparser-3.0.dist-info")
    assert manifest.record_origin_digest(str(copy), "pycparser", "3.0") == manifest._RECORD_PINS["pycparser"]
    (copy / "pycparser" / "injected.py").write_text("x = 1\n")
    assert manifest.record_origin_digest(str(copy), "pycparser", "3.0") is None
    (copy / "pycparser" / "injected.py").unlink()
    target = copy / "pycparser" / "c_lexer.py"
    target.write_bytes(target.read_bytes() + b"\n# tampered\n")
    assert manifest.record_origin_digest(str(copy), "pycparser", "3.0") is None
    assert manifest.verify_records(str(copy)) == "ENV_RECORD_MISMATCH"


def test_x09_status_is_read_only(h):
    h.advance(state.PRIVATE_WRITTEN)
    with open(h.custody_file("stray.txt"), "xb") as handle:
        handle.write(b"x")
    rc, _out, err = h.run("status")
    assert rc == 1 and "ERROR STATE_REJECTED" in err
    assert h.marker() == state.PRIVATE_WRITTEN


def test_x10_full_flow_display_matches_independent_derivation(h):
    h.advance(state.READY)
    out = h.ok("pre-prepare-display", PW)
    pem = h.custody_file(state.PRIVATE).read_bytes()
    key = serialization.load_pem_private_key(pem, password=PW.encode("ascii"))
    raw = key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    assert out.splitlines() == [
        "DISPLAY " + raw.hex(),
        "CANDIDATE_MATCH EXACT",
        "STATE " + state.READY,
        "ADMISSION NOT_PERFORMED",
    ]
    assert h.custody_file(state.CANDIDATE).read_bytes() == raw
    assert sorted(p.name for p in Path(h.paths.custody).iterdir()) == sorted(state.files_for(state.READY))
    assert not os.path.lexists(h.paths.restore)


def test_x11_entry_script_rejects_arguments_without_touching_any_root(tmp_path):
    env = {k: v for k, v in os.environ.items() if not k.upper().startswith("PYTHON")}
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    for args in (["generate", PW], [], ["--help"]):
        proc = subprocess.run(
            [sys.executable, str(PKG_DIR / "__main__.py"), *args],
            capture_output=True,
            text=True,
            cwd=str(tmp_path),
            env=env,
            timeout=60,
        )
        assert proc.returncode == 2
        assert proc.stdout == "" and proc.stderr == "ERROR USAGE_REJECTED\n"


def test_x12_error_vocabulary_is_closed():
    assert CustodyError("NOT_A_CODE").code == "INTERNAL_FAILURE"
    assert repr(CustodyError("PATH_REJECTED")) == "CustodyError(PATH_REJECTED)"
    for code in CODES:
        assert code.isupper() and " " not in code


def test_x13_manifest_baseline_accepts_and_every_axis_rejects(provenance):
    assert env_code(baseline_facts()) == "ACCEPTED"
    assert env_code(baseline_facts(record_result="ENV_RECORD_MISMATCH")) == "ENV_RECORD_MISMATCH"
    assert env_code(baseline_facts(openssl_version_text="OpenSSL 3.5.0 1 Apr 2025")) == "ENV_OPENSSL_REJECTED"
    assert env_code(baseline_facts(xoptions=("faulthandler",))) == "ENV_ISOLATION_REJECTED"
    assert env_code(baseline_facts(debug_flags=(0, 1, 0, 0, 0))) == "ENV_ISOLATION_REJECTED"
    assert env_code(baseline_facts(warnoptions=("ignore",))) == "ENV_ISOLATION_REJECTED"
    assert env_code(baseline_facts(safe_path=False)) == "ENV_ISOLATION_REJECTED"
    assert env_code(baseline_facts(no_user_site=False)) == "ENV_ISOLATION_REJECTED"
    assert env_code(baseline_facts(ignore_environment=False)) == "ENV_ISOLATION_REJECTED"
    assert env_code(baseline_facts(platform="linux")) == "ENV_PLATFORM_REJECTED"
    assert env_code(baseline_facts(distributions=baseline_facts().distributions[:2])) == "ENV_DISTRIBUTION_REJECTED"
    dup = baseline_facts().distributions + (baseline_facts().distributions[0],)
    assert env_code(baseline_facts(distributions=dup)) == "ENV_DISTRIBUTION_REJECTED"
    other_loc = (
        manifest.DistFacts("cryptography", "50.0.2", "C:\\other", ("cp311-abi3-win_amd64",), "pip", False),
    ) + baseline_facts().distributions[1:]
    assert env_code(baseline_facts(distributions=other_loc)) == "ENV_DISTRIBUTION_REJECTED"
    not_pip = (
        manifest.DistFacts("cryptography", "50.0.2", baseline_facts().prefix + "\\Lib\\site-packages", ("cp311-abi3-win_amd64",), "conda", False),
    ) + baseline_facts().distributions[1:]
    assert env_code(baseline_facts(distributions=not_pip)) == "ENV_DISTRIBUTION_REJECTED"
    assert env_code(baseline_facts(helper_file="C:\\other\\ed25519_custody_v0\\__init__.py")) == "ENV_MODULE_PATH_REJECTED"
    assert env_code(baseline_facts(module_files=baseline_facts().module_files[:4])) == "ENV_MODULE_PATH_REJECTED"
    assert env_code(baseline_facts(base_executable="C:\\other\\python.exe")) == "ENV_INTERPRETER_REJECTED"
    assert env_code(baseline_facts(executable="C:\\other\\python.exe")) == "ENV_VENV_REJECTED"
    cfg_home = "home = C:\\other\ninclude-system-site-packages = false\nversion = 3.14.3\n"
    assert env_code(baseline_facts(pyvenv_cfg=cfg_home)) == "ENV_VENV_REJECTED"
    cfg_ver = "home = " + baseline_facts().base_prefix + "\ninclude-system-site-packages = false\nversion = 3.14.2\n"
    assert env_code(baseline_facts(pyvenv_cfg=cfg_ver)) == "ENV_VENV_REJECTED"
    assert env_code(baseline_facts(pyvenv_cfg=None)) == "ENV_VENV_REJECTED"
    reordered = baseline_facts().sys_path[-1:] + baseline_facts().sys_path[:-1]
    assert env_code(baseline_facts(sys_path=reordered)) == "ENV_MODULE_PATH_REJECTED"


def test_x14_derive_requires_exact_previous_state_and_fresh_processes(h):
    h.advance(state.PRIVATE_WRITTEN)
    rc, _out, err = h.run("verify-candidate", PW)
    assert rc == 1 and "ERROR STATE_REJECTED" in err and h.marker() == state.PRIVATE_WRITTEN
    h.ok("derive-candidate", PW)
    rc, _out, err = h.run("derive-candidate", PW)
    assert rc == 1 and "ERROR STATE_REJECTED" in err and h.marker() == state.PCW_CANDIDATE
    out = h.ok("verify-candidate", PW)
    assert out.startswith("DISPLAY ")
    rc, _out, err = h.run("verify-candidate", PW)
    assert rc == 1 and "ERROR STATE_REJECTED" in err and h.marker() == state.PCW_VERIFIED


def test_x15_preflight_reads_no_secret_and_writes_nothing(h):
    out = h.ok("preflight")
    assert out.splitlines() == ["PREFLIGHT_OK MACHINE_CHECKS_ONLY", "RUNBOOK_DECLARATIONS NOT_MACHINE_PROVEN"]
    assert h.reader.prompts == []
    assert not os.path.lexists(h.paths.root)


def test_x16_real_console_preflight_rejects_pytest_streams():
    with pytest.raises(CustodyError) as info:
        console.evaluate_console(REAL["collect_console"]())
    assert info.value.code == "CONSOLE_PREFLIGHT_REJECTED"


def test_x17_abandon_requires_no_passphrase(h):
    h.advance(state.PCW_CANDIDATE)
    h.ok("abandon")
    assert h.reader.prompts == []


# ---------------------------------------------------------------------------
# Remediation tests added after source-mutation round 1 (see mutation_campaign_v0).

_ENV_ALLOWED = {"paths.py": {"_windows_location_context"}, "manifest.py": {"collect_facts"}}


def test_x18_no_environment_channel_for_secrets_paths_or_restore(h, monkeypatch, tmp_path):
    """D1 checks 4/6/42: environment is read only to ADD rejections or record names."""
    for name, source in production_sources().items():
        tree = ast.parse(source)
        for stmt in tree.body:
            owner = stmt.name if isinstance(stmt, (ast.FunctionDef, ast.ClassDef)) else "<module>"
            for node in ast.walk(stmt):
                if isinstance(node, ast.Attribute):
                    ident = node.attr
                elif isinstance(node, ast.Name):
                    ident = node.id
                else:
                    continue
                if ident in ("environ", "environb", "getenv", "putenv"):
                    assert owner in _ENV_ALLOWED.get(name, set()), (name, owner)
                assert ident not in ("__import__", "importlib", "eval", "exec"), (name, owner)
    evil = tmp_path / "evil-caller-root"
    for var in ("WEAVERFORGE_ROOT", "WEAVERFORGE_RESTORE", "CUSTODY_ROOT"):
        monkeypatch.setenv(var, str(evil))
    for var in ("WEAVERFORGE_UNLOCK", "WEAVERFORGE_PASSPHRASE", "PASSPHRASE", "CUSTODY_PASSPHRASE"):
        monkeypatch.setenv(var, OTHER_PASSPHRASE)
    h.advance(state.PCW_VERIFIED)
    assert h.reader.prompts == ["Passphrase (hidden): "]
    assert not evil.exists()
    assert paths.resolve().root.startswith(str(h.base))


def test_x19_unexpected_exception_outside_phases_prints_only_fixed_code(h, monkeypatch):
    """D1 check 23: no exception text or chained context leaves the helper."""

    def boom():
        raise RuntimeError("TEST-ONLY-LEAK " + PW)

    monkeypatch.setattr(custody, "open_session", boom)
    rc, out, err = h.run("status")
    assert (rc, out, err) == (1, "", "ERROR INTERNAL_FAILURE\n")
    with pytest.raises(CustodyError) as info:
        try:
            raise ValueError("TEST-ONLY-LEAK " + PW)
        except ValueError:
            errors.fail("FILE_REJECTED")
    assert info.value.__cause__ is None
    assert info.value.__suppress_context__ is True
    assert PW not in repr(info.value) and PW not in str(info.value)


def test_x20_phase_outputs_are_exact_closed_lines(h):
    """D1 checks 18/29/32: no extra output (key, snapshot, admission) beyond fixed lines."""
    assert h.ok("init").splitlines() == ["STATE EMPTY"]
    assert h.ok("generate", PW, PW).splitlines() == ["STATE PRIVATE_WRITTEN"]
    assert h.ok("derive-candidate", PW).splitlines() == ["STATE " + state.PCW_CANDIDATE]
    display = custody.canonical_display(h.custody_file(state.CANDIDATE).read_bytes())
    assert h.ok("verify-candidate", PW).splitlines() == ["DISPLAY " + display, "STATE " + state.PCW_VERIFIED]
    for check, after in ((1, state.PCW_RESTORE_1), (2, state.PCW_RESTORE_2)):
        before = h.marker()
        assert h.ok("restore-init").splitlines() == ["RESTORE_SLOT_READY FOR_CHECK %d" % check, "STATE " + before]
        h.copy_backup()
        assert h.ok("restore-check", PW).splitlines() == [
            "DISPLAY " + display,
            "RESTORE_CHECK_PASSED %d" % check,
            "STATE " + after,
        ]
    assert h.ok("mark-backups-verified").splitlines() == ["STATE BACKUPS_VERIFIED"]
    assert h.ok("mark-ready").splitlines() == ["STATE " + state.READY, "ADMISSION NOT_PERFORMED"]
    assert h.ok("pre-prepare-display", PW).splitlines() == [
        "DISPLAY " + display,
        "CANDIDATE_MATCH EXACT",
        "STATE " + state.READY,
        "ADMISSION NOT_PERFORMED",
    ]
    assert h.ok("status").splitlines() == ["STATE " + state.READY]
    for text in h.outputs:
        assert "SNAPSHOT" not in text.upper() and "BEGIN" not in text


def test_x21_prepare_rejects_candidate_changed_after_ready_without_transition(h):
    """D1 check 37 + N2: PREPARE compares a fresh derivation to the protected exact bytes."""
    h.advance(state.READY)
    other = custody.raw_public(ed25519.Ed25519PrivateKey.generate())  # TEST ONLY, ephemeral
    h.replace_file(h.custody_file(state.CANDIDATE), other)
    rc, out, err = h.run("pre-prepare-display", PW)
    assert (rc, out, err) == (1, "", "ERROR CANDIDATE_MISMATCH\n")
    assert h.marker() == state.READY


def test_x22_commit_rejects_skip_and_backward_transitions_with_matching_file_sets(h):
    """D1 check 34: only the exact code-owned successor can be committed."""
    h.advance(state.PCW_CANDIDATE)
    for new in (state.PCW_RESTORE_1, state.PCW_RESTORE_2, state.BACKUPS_VERIFIED, state.READY, state.PCW_CANDIDATE):
        with pytest.raises(CustodyError) as info:
            custody.commit(h.session(), state.PCW_CANDIDATE, new)
        assert info.value.code == "STATE_REJECTED"
        assert h.marker() == state.PCW_CANDIDATE
    h.ok("verify-candidate", PW)
    with pytest.raises(CustodyError) as info:
        custody.commit(h.session(), state.PCW_VERIFIED, state.PCW_CANDIDATE)
    assert info.value.code == "STATE_REJECTED"
    assert h.marker() == state.PCW_VERIFIED


def test_x23_every_mutating_command_on_abandoned_reports_state_abandoned(h):
    """D1 checks 35/46: an ABANDONED generation is never repaired, resumed, or used."""
    h.advance(state.PRIVATE_WRITTEN)
    rc, _out, err = h.run("derive-candidate", OTHER_PASSPHRASE)
    assert rc == 1 and "STATE ABANDONED" in err and h.marker() == state.ABANDONED
    for command, answers in (
        ("generate", (PW, PW)),
        ("derive-candidate", (PW,)),
        ("verify-candidate", (PW,)),
        ("restore-init", ()),
        ("restore-check", (PW,)),
        ("mark-backups-verified", ()),
        ("mark-ready", ()),
        ("pre-prepare-display", (PW,)),
    ):
        rc, out, err = h.run(command, *answers)
        assert (rc, out, err) == (1, "", "ERROR STATE_ABANDONED\n"), command
        assert h.reader.prompts == [], command
        assert h.marker() == state.ABANDONED
    assert h.ok("status").splitlines() == ["STATE ABANDONED"]
    assert sorted(os.listdir(h.paths.custody)) == sorted([state.MARKER, state.PRIVATE])


def test_x24_read_secret_preflights_console_before_any_reader_call(h, monkeypatch):
    """D1 check 40: no hidden reader is obtained or called before the console preflight."""
    bad = dataclasses.replace(GOOD_CONSOLE, conin_console_mode=False)
    monkeypatch.setattr(console, "_collect_console_facts", lambda: bad)
    calls = []

    def reader_factory():
        calls.append("reader")
        return lambda prompt: calls.append(prompt) or PW

    monkeypatch.setattr(console, "_hidden_reader", reader_factory)
    with pytest.raises(CustodyError) as info:
        console.read_secret("TEST-ONLY prompt: ")
    assert info.value.code == "CONSOLE_PREFLIGHT_REJECTED"
    assert calls == []


def test_x25_new_file_is_verified_before_any_content_is_written(h, tmp_path):
    """D1 check 43: owner/DACL of a new file are verified before the first byte is written."""
    plain = tmp_path / "inherits-broad-acl"
    plain.mkdir()
    target = plain / "f.bin"
    with pytest.raises(CustodyError) as info:
        winsec.write_new_file(str(target), h.sid, b"TEST-ONLY-NOT-A-SECRET")
    assert info.value.code == "ACL_REJECTED"
    assert target.stat().st_size == 0


def test_x26_file_reached_through_a_junctioned_parent_is_rejected(h, tmp_path):
    """D1 checks 9/36: a file opened through a redirected parent is never trusted."""
    import _winapi

    h.advance(state.PRIVATE_WRITTEN)
    link = tmp_path / "custody-alias"
    _winapi.CreateJunction(h.paths.custody, str(link))
    try:
        with pytest.raises(CustodyError) as info:
            winsec.read_file(str(link / state.PRIVATE), h.sid, custody.MAX_PEM)
        assert info.value.code == "FILE_REJECTED"
        with pytest.raises(CustodyError) as info:
            winsec.write_new_file(str(link / "custody-v0-extra.bin"), h.sid, b"TEST-ONLY")
        assert info.value.code == "FILE_REJECTED"
    finally:
        os.rmdir(link)
