"""D1-R1 behavioral checks 1-24 for the Ed25519 custody helper v0.

Each test function ``test_cNN_*`` maps one-to-one to D1-R1 negative check NN.
These are attack/negative tests, not source mutations. TEST ONLY material is
generated at runtime inside tmp_path.
"""

from __future__ import annotations

import ast
import getpass
import os
import subprocess
import warnings

import pytest
from conftest import (
    OTHER_PASSPHRASE,
    TEST_PASSPHRASE,
    production_sources,
)
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519

from ed25519_custody_v0 import cli, console, custody, manifest, paths, state, winsec
from ed25519_custody_v0.errors import CustodyError

PW = TEST_PASSPHRASE


def _code(fn, *args):
    with pytest.raises(CustodyError) as info:
        fn(*args)
    return info.value.code


def _test_pem(passphrase: str = PW, key=None):
    """TEST ONLY runtime-ephemeral encrypted PKCS#8 PEM."""
    key = key or ed25519.Ed25519PrivateKey.generate()
    pem = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.BestAvailableEncryption(passphrase.encode("ascii")),
    )
    return key, pem


class WrappedKey(ed25519.Ed25519PrivateKey):
    """TEST ONLY wrapper that can substitute the private serialization result."""

    def __init__(self, inner, private_result=None):
        self._inner = inner
        self._private_result = private_result
        self.calls = []

    def public_key(self):
        return self._inner.public_key()

    def private_bytes(self, encoding, format, encryption_algorithm):
        self.calls.append((encoding, format, type(encryption_algorithm)))
        if self._private_result is not None:
            return self._private_result
        return self._inner.private_bytes(encoding, format, encryption_algorithm)


WrappedKey.__abstractmethods__ = frozenset()


def _patch_generate(monkeypatch, factory):
    monkeypatch.setattr(ed25519.Ed25519PrivateKey, "generate", staticmethod(factory))


def _assert_abandoned(h, err):
    assert "STATE ABANDONED" in err
    assert h.marker() == state.ABANDONED


# 1
def test_c01_reject_noencryption_and_plaintext_serialization(h, monkeypatch):
    for source in production_sources().values():
        assert "NoEncryption" not in source
    inner = ed25519.Ed25519PrivateKey.generate()
    plain = inner.private_bytes(
        serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()
    )
    assert _code(custody.require_encrypted_label, plain) == "SERIALIZATION_REJECTED"
    wrapped = WrappedKey(inner)
    _patch_generate(monkeypatch, lambda: wrapped)
    h.advance(state.EMPTY)
    rc, _out, err = h.run("generate", PW, PW)
    assert rc == 0, err
    assert wrapped.calls == [
        (serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.BestAvailableEncryption)
    ]
    assert h.custody_file(state.PRIVATE).read_bytes().startswith(custody.PEM_BEGIN)
    # A plaintext working container is never accepted: the generation is abandoned.
    h.replace_file(h.custody_file(state.PRIVATE), plain)
    rc, _out, err = h.run("derive-candidate", PW)
    assert rc == 1 and "ERROR SERIALIZATION_REJECTED" in err
    _assert_abandoned(h, err)


def test_c01b_generation_refuses_unencrypted_serialization_result(h, monkeypatch):
    inner = ed25519.Ed25519PrivateKey.generate()
    plain = inner.private_bytes(
        serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()
    )
    _patch_generate(monkeypatch, lambda: WrappedKey(inner, plain))
    h.advance(state.EMPTY)
    rc, _out, err = h.run("generate", PW, PW)
    assert rc == 1 and "ERROR SERIALIZATION_REJECTED" in err
    assert not h.custody_file(state.PRIVATE).exists()
    assert h.marker() == state.EMPTY


# 2
def test_c02_reject_raw_private_serialization(h, monkeypatch):
    for source in production_sources().values():
        assert "private_bytes_raw" not in source
        assert "PrivateFormat.Raw" not in source
        assert "TraditionalOpenSSL" not in source
        assert "OpenSSH" not in source
    inner = ed25519.Ed25519PrivateKey.generate()
    raw_private = inner.private_bytes(
        serialization.Encoding.Raw, serialization.PrivateFormat.Raw, serialization.NoEncryption()
    )
    _patch_generate(monkeypatch, lambda: WrappedKey(inner, raw_private))
    h.advance(state.EMPTY)
    rc, _out, err = h.run("generate", PW, PW)
    assert rc == 1 and "ERROR SERIALIZATION_REJECTED" in err
    assert not h.custody_file(state.PRIVATE).exists()


def test_c02b_raw_private_working_container_abandons(h):
    h.advance(state.PRIVATE_WRITTEN)
    h.replace_file(h.custody_file(state.PRIVATE), os.urandom(32))
    rc, _out, err = h.run("derive-candidate", PW)
    assert rc == 1 and "ERROR SERIALIZATION_REJECTED" in err
    _assert_abandoned(h, err)


# 3
def test_c03_reject_passphrase_in_command_line(h):
    h.advance(state.EMPTY)
    for argv in (
        ["generate", PW],
        ["generate", "--passphrase", PW],
        ["generate", "--passphrase=" + PW],
        ["generate=" + PW],
        [PW],
        [],
        ["generate", "generate"],
    ):
        rc, out, err = h.run(None, argv=argv)
        assert rc == 2 and err == "ERROR USAGE_REJECTED\n" and out == ""
        assert PW not in out + err
    assert h.reader.prompts == []
    assert not h.custody_file(state.PRIVATE).exists()


# 4
def test_c04_reject_passphrase_in_environment_file_pipe(h, monkeypatch, tmp_path):
    for name in ("WEAVERFORGE_PASSPHRASE", "CUSTODY_PASSPHRASE", "WeaverForge_Key"):
        from conftest import baseline_facts, env_code

        facts = baseline_facts(environ_names=("PATH", name.upper()))
        assert env_code(facts) == "ENV_INJECTION_REJECTED"
    h.advance(state.EMPTY)
    monkeypatch.setenv("WEAVERFORGE_PASSPHRASE", PW)
    monkeypatch.setenv("PASSPHRASE", PW)
    (tmp_path / "passphrase.txt").write_text(PW)
    rc, _out, err = h.run("generate")  # no hidden answers: env/file values are never consulted
    assert rc == 1 and "ERROR SECRET_INPUT_REJECTED" in err
    assert not h.custody_file(state.PRIVATE).exists()
    piped = console.ConsoleFacts(True, True, False, False, True, True, True, True, True)
    monkeypatch.setattr(console, "_collect_console_facts", lambda: piped)
    rc, _out, err = h.run("generate", PW, PW)
    assert rc == 1 and "ERROR CONSOLE_PREFLIGHT_REJECTED" in err
    assert h.reader.prompts == []
    for name in ("console.py", "custody.py", "cli.py", "state.py"):
        source = production_sources()[name]
        assert "os.environ" not in source and "getenv" not in source
        assert "sys.stdin.read" not in source and "input(" not in source


# 5
def test_c05_reject_noninteractive_echo_fallback_and_getpasswarning(h, monkeypatch):
    h.advance(state.EMPTY)
    redirected = console.ConsoleFacts(False, True, True, True, True, True, True, True, True)
    monkeypatch.setattr(console, "_collect_console_facts", lambda: redirected)
    rc, _out, err = h.run("generate", PW, PW)
    assert rc == 1 and "ERROR CONSOLE_PREFLIGHT_REJECTED" in err and h.reader.prompts == []
    fallback = console.ConsoleFacts(True, True, True, True, True, True, True, True, False)
    monkeypatch.setattr(console, "_collect_console_facts", lambda: fallback)
    rc, _out, err = h.run("generate", PW, PW)
    assert rc == 1 and "ERROR CONSOLE_PREFLIGHT_REJECTED" in err and h.reader.prompts == []
    from conftest import GOOD_CONSOLE

    monkeypatch.setattr(console, "_collect_console_facts", lambda: GOOD_CONSOLE)

    def warn_then_answer(_prompt):
        warnings.warn("echo fallback", getpass.GetPassWarning)
        return PW

    rc, _out, err = h.run("generate", warn_then_answer, PW)
    assert rc == 1 and "ERROR SECRET_INPUT_REJECTED" in err
    assert not h.custody_file(state.PRIVATE).exists()
    assert h.marker() == state.EMPTY


def test_c05b_real_reader_refuses_non_console_getpass(monkeypatch):
    from conftest import REAL

    monkeypatch.setattr(getpass, "getpass", getpass.fallback_getpass)
    assert _code(REAL["hidden_reader"]) == "CONSOLE_PREFLIGHT_REJECTED"


# 6
@pytest.mark.parametrize(
    "first,second",
    [
        ("", ""),
        ("A" * 23, "A" * 23),
        ("A" * 129, "A" * 129),
        ("A" * 30 + "\x07", "A" * 30 + "\x07"),
        ("A" * 30 + "\t", "A" * 30 + "\t"),
        ("A" * 30 + "\x7f", "A" * 30 + "\x7f"),
        ("A" * 30 + "\u00e9", "A" * 30 + "\u00e9"),
        (PW, OTHER_PASSPHRASE),
    ],
)
def test_c06_reject_invalid_or_mismatched_passphrases(h, first, second):
    h.advance(state.EMPTY)
    rc, _out, err = h.run("generate", first, second)
    assert rc == 1
    assert ("ERROR PASSPHRASE_SHAPE_REJECTED" in err) or ("ERROR PASSPHRASE_MISMATCH" in err)
    assert not h.custody_file(state.PRIVATE).exists()
    assert h.marker() == state.EMPTY


def test_c06b_passphrase_shape_boundaries():
    assert console.validate_passphrase("A" * 24) == b"A" * 24
    assert console.validate_passphrase(" ~" * 64) == b" ~" * 64
    for bad in ("A" * 23, "A" * 129, b"A" * 30, None, "A" * 29 + "\x1f"):
        assert _code(console.validate_passphrase, bad) == "PASSPHRASE_SHAPE_REJECTED"


# 7
def test_c07_reject_destination_inside_or_above_git_tree(h):
    (h.base / "profile" / ".git").mkdir()
    rc, _out, err = h.run("init")
    assert rc == 1 and "ERROR PATH_REJECTED" in err
    assert not os.path.lexists(h.base / "profile" / "AppData" / "Local" / "WeaverForge")


def test_c07b_git_marker_inside_custody_root(h):
    h.advance(state.EMPTY)
    os.mkdir(os.path.join(h.paths.root, ".git"))
    rc, _out, err = h.run("status")
    assert rc == 1 and "ERROR PATH_REJECTED" in err


# 8
def test_c08_reject_sync_roaming_network_removable_temp_relative_paths(h, monkeypatch):
    good = paths._location_context()
    custody_path = paths.resolve().custody
    bad_contexts = [
        paths.LocationContext("\\\\server\\share\\AppData\\Local", "\\\\server\\share", good.roaming, (), ()),
        paths.LocationContext("AppData\\Local", "AppData", good.roaming, (), ()),
        paths.LocationContext(good.local_appdata, good.profile + "\\redirected", good.roaming, (), ()),
    ]
    for ctx in bad_contexts:
        assert _code(paths.validate_context, ctx) == "PATH_REJECTED"
    location_cases = [
        paths.LocationContext(good.local_appdata, good.profile, good.local_appdata, (), ()),
        paths.LocationContext(good.local_appdata, good.profile, good.roaming, (good.local_appdata,), ()),
        paths.LocationContext(good.local_appdata, good.profile, good.roaming, (), (good.profile,)),
    ]
    for ctx in location_cases:
        assert _code(paths.validate_location, custody_path, ctx) == "PATH_REJECTED"
    onedrive = good.local_appdata + "\\OneDrive - Org\\custody-v0"
    assert _code(paths.validate_location, onedrive, good) == "PATH_REJECTED"
    assert _code(paths.validate_location, "C:\\elsewhere\\custody-v0", good) == "PATH_REJECTED"
    assert _code(paths.validate_location, custody_path + "\\..\\x", good) == "PATH_REJECTED"
    monkeypatch.setattr(winsec, "drive_type", lambda root: 2)
    rc, _out, err = h.run("init")
    assert rc == 1 and "ERROR PATH_REJECTED" in err
    monkeypatch.setattr(winsec, "drive_type", lambda root: 4)
    rc, _out, err = h.run("init")
    assert rc == 1 and "ERROR PATH_REJECTED" in err


def test_c08b_cloud_sync_root_api_rejects(h, monkeypatch):
    monkeypatch.setattr(winsec, "sync_root_hresult", lambda path: 0)
    rc, _out, err = h.run("init")
    assert rc == 1 and "ERROR PATH_REJECTED" in err
    assert not os.path.lexists(h.base / "profile" / "AppData" / "Local" / "WeaverForge")


# 9
def test_c09_reject_junction_and_reparse_paths(h):
    import _winapi

    target = h.base / "elsewhere"
    target.mkdir()
    link = h.base / "profile" / "AppData" / "Local" / "WeaverForge"
    _winapi.CreateJunction(str(target), str(link))
    rc, _out, err = h.run("init")
    assert rc == 1 and "ERROR PATH_REJECTED" in err
    assert list(target.iterdir()) == []


def test_c09b_custody_directory_junction_rejected(h):
    import _winapi

    h.advance(state.EMPTY)
    h.ok("abandon")
    target = h.base / "elsewhere2"
    target.mkdir()
    _winapi.CreateJunction(str(target), h.paths.root + "\\custody-v0")
    rc, _out, err = h.run("init")
    assert rc == 1 and "ERROR PATH_REJECTED" in err
    assert list(target.iterdir()) == []


def test_c09c_reparse_attribute_on_any_component_rejected(h, monkeypatch):
    real = winsec.file_attributes
    root = os.path.normcase(paths.resolve().root)

    def fake(path):
        attrs = real(path)
        if os.path.normcase(path) == os.path.normcase(str(h.base / "profile")):
            return (attrs or winsec.FILE_ATTRIBUTE_DIRECTORY) | winsec.FILE_ATTRIBUTE_REPARSE_POINT
        return attrs

    assert root
    monkeypatch.setattr(winsec, "file_attributes", fake)
    rc, _out, err = h.run("init")
    assert rc == 1 and "ERROR PATH_REJECTED" in err


# 10
def test_c10_reject_broad_inherited_acl_wrong_owner_principals(h):
    sid = h.sid
    sy = winsec.SYSTEM_SID
    full = winsec.FILE_ALL_ACCESS
    dir_ok = ((0, 3, full, sy), (0, 3, full, sid))
    winsec.evaluate_directory_acl(sid, winsec.SE_DACL_PROTECTED, dir_ok, sid)
    bad_dirs = [
        ("S-1-5-32-544", winsec.SE_DACL_PROTECTED, dir_ok),
        (sid, 0, dir_ok),
        (sid, winsec.SE_DACL_PROTECTED, ((0, 0x13, full, sy), (0, 0x13, full, sid))),
        (sid, winsec.SE_DACL_PROTECTED, dir_ok + ((0, 3, 0x1200A9, "S-1-1-0"),)),
        (sid, winsec.SE_DACL_PROTECTED, dir_ok + ((0, 3, full, "S-1-5-32-544"),)),
        (sid, winsec.SE_DACL_PROTECTED, ((0, 3, full, sy), (0, 3, 0x1200A9, sid))),
        (sid, winsec.SE_DACL_PROTECTED, ((0, 3, full, sy),)),
        (sid, winsec.SE_DACL_PROTECTED, dir_ok + ((1, 3, 0, ""),)),
        (sid, winsec.SE_DACL_PROTECTED, ((0, 3, full, "S-1-5-11"), (0, 3, full, sid))),
    ]
    for owner, control, aces in bad_dirs:
        assert _code(winsec.evaluate_directory_acl, owner, control, aces, sid) == "ACL_REJECTED"
    file_ok = ((0, 0x10, full, sy), (0, 0x10, full, sid))
    winsec.evaluate_file_acl(sid, 0, file_ok, sid)
    bad_files = [
        ("S-1-5-32-544", 0, file_ok),
        (sid, winsec.SE_DACL_PROTECTED, file_ok),
        (sid, 0, ((0, 0, full, sy), (0, 0, full, sid))),
        (sid, 0, file_ok + ((0, 0x10, 0x1200A9, "S-1-5-32-545"),)),
        (sid, 0, ((0, 0x10, full, sid),)),
    ]
    for owner, control, aces in bad_files:
        assert _code(winsec.evaluate_file_acl, owner, control, aces, sid) == "ACL_REJECTED"


def test_c10b_real_explicit_ace_on_private_file_abandons(h):
    h.advance(state.PRIVATE_WRITTEN)
    subprocess.run(
        ["icacls", str(h.custody_file(state.PRIVATE)), "/grant", "*S-1-1-0:(R)"],
        check=True,
        capture_output=True,
    )
    rc, _out, err = h.run("derive-candidate", PW)
    assert rc == 1 and "ERROR ACL_REJECTED" in err
    _assert_abandoned(h, err)
    assert not h.custody_file(state.CANDIDATE).exists()


def test_c10c_real_broad_directory_ace_rejected(h):
    h.advance(state.PRIVATE_WRITTEN)
    subprocess.run(
        ["icacls", h.paths.custody, "/grant", "*S-1-5-32-545:(OI)(CI)(R)"],
        check=True,
        capture_output=True,
    )
    rc, _out, err = h.run("status")
    assert rc == 1 and "ERROR ACL_REJECTED" in err
    rc, _out, err = h.run("derive-candidate", PW)
    assert rc == 1 and "ERROR ACL_REJECTED" in err
    assert h.reader.prompts == []


# 11
def test_c11_reject_existing_destinations_and_overwrite(h):
    h.advance(state.PRIVATE_WRITTEN)
    before = h.custody_file(state.PRIVATE).read_bytes()
    assert _code(winsec.write_new_file, str(h.custody_file(state.PRIVATE)), h.sid, b"x") == "EXISTS_REJECTED"
    rc, _out, err = h.run("generate", PW, PW)
    assert rc == 1 and "ERROR STATE_REJECTED" in err
    rc, _out, err = h.run("init")
    assert rc == 1 and "ERROR EXISTS_REJECTED" in err
    assert h.custody_file(state.PRIVATE).read_bytes() == before
    assert h.marker() == state.PRIVATE_WRITTEN


# 12
def test_c12_reject_output_without_encrypted_pkcs8_label(h):
    _key, pem = _test_pem()
    custody.require_encrypted_label(pem)
    body = pem[len(custody.PEM_BEGIN) : -len(custody.PEM_END)]
    bad = [
        b"-----BEGIN PRIVATE KEY-----\n" + body + b"-----END PRIVATE KEY-----\n",
        b"-----BEGIN OPENSSH PRIVATE KEY-----\n" + body + b"-----END OPENSSH PRIVATE KEY-----\n",
        pem[:-1],
        pem + b"\n",
        pem + pem,
        custody.PEM_BEGIN + body,
        pem.decode("ascii"),
        custody.PEM_BEGIN + b"A" * 5000 + custody.PEM_END,
        b"",
    ]
    for value in bad:
        assert _code(custody.require_encrypted_label, value) == "SERIALIZATION_REJECTED"


def test_c12b_corrupt_encrypted_body_fails_reload_and_abandons(h):
    h.advance(state.PRIVATE_WRITTEN)
    pem = h.custody_file(state.PRIVATE).read_bytes()
    lines = pem.split(b"\n")
    lines[2] = bytes(reversed(lines[2]))
    h.replace_file(h.custody_file(state.PRIVATE), b"\n".join(lines))
    rc, _out, err = h.run("derive-candidate", PW)
    assert rc == 1 and "ERROR KEY_RELOAD_REJECTED" in err
    _assert_abandoned(h, err)


class _FakePublic:
    def __init__(self, result=None):
        self.calls = []
        self._result = result

    def public_bytes(self, encoding, format):
        self.calls.append((encoding, format))
        if self._result is not None:
            return self._result
        real = ed25519.Ed25519PrivateKey.generate().public_key()
        if (encoding, format) == (serialization.Encoding.Raw, serialization.PublicFormat.Raw):
            return real.public_bytes(encoding, format)
        return real.public_bytes(serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo)


class _FakeKey:
    def __init__(self, public):
        self._public = public

    def public_key(self):
        return self._public


# 13
def test_c13_reject_wrong_public_encoding_or_format(h, monkeypatch):
    fake = _FakePublic()
    assert len(custody.raw_public(_FakeKey(fake))) == 32
    assert fake.calls == [(serialization.Encoding.Raw, serialization.PublicFormat.Raw)]
    der = ed25519.Ed25519PrivateKey.generate().public_key().public_bytes(
        serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo
    )
    assert _code(custody.raw_public, _FakeKey(_FakePublic(der))) == "PUBLIC_OUTPUT_REJECTED"
    h.advance(state.PRIVATE_WRITTEN)
    monkeypatch.setattr(custody, "load_private", lambda pem, pw: _FakeKey(_FakePublic(der)))
    rc, _out, err = h.run("derive-candidate", PW)
    assert rc == 1 and "ERROR PUBLIC_OUTPUT_REJECTED" in err
    _assert_abandoned(h, err)
    assert not h.custody_file(state.CANDIDATE).exists()


# 14
def test_c14_reject_public_output_not_exact_bytes(h, monkeypatch):
    class BytesSub(bytes):
        pass

    for value in (bytearray(32), BytesSub(b"\x01" * 32), memoryview(b"\x01" * 32), "a" * 32):
        assert _code(custody.require_public, value) == "PUBLIC_OUTPUT_REJECTED"
        assert _code(custody.raw_public, _FakeKey(_FakePublic(value))) == "PUBLIC_OUTPUT_REJECTED"
    h.advance(state.PRIVATE_WRITTEN)
    monkeypatch.setattr(custody, "load_private", lambda pem, pw: _FakeKey(_FakePublic(bytearray(32))))
    rc, _out, err = h.run("derive-candidate", PW)
    assert rc == 1 and "ERROR PUBLIC_OUTPUT_REJECTED" in err
    _assert_abandoned(h, err)


# 15
def test_c15_reject_public_output_length_not_32(h, monkeypatch):
    for value in (b"", b"\x01" * 31, b"\x01" * 33, b"\x01" * 64):
        assert _code(custody.require_public, value) == "PUBLIC_OUTPUT_REJECTED"
        assert _code(custody.canonical_display, value) == "PUBLIC_OUTPUT_REJECTED"
    h.advance(state.PRIVATE_WRITTEN)
    monkeypatch.setattr(custody, "load_private", lambda pem, pw: _FakeKey(_FakePublic(b"\x01" * 31)))
    rc, _out, err = h.run("derive-candidate", PW)
    assert rc == 1 and "ERROR PUBLIC_OUTPUT_REJECTED" in err


# 16
def test_c16_reject_noncanonical_display(h):
    raw = bytes(range(32))
    assert custody.canonical_display(raw) == raw.hex()

    class StrSub(str):
        pass

    for value in (
        raw.hex().upper(),
        raw.hex()[:63],
        raw.hex() + "0",
        "g" + raw.hex()[1:],
        " " + raw.hex()[1:],
        StrSub(raw.hex()),
        raw.hex().encode("ascii"),
    ):
        assert _code(custody.require_display, value) == "DISPLAY_REJECTED"
    h.advance(state.PCW_VERIFIED)
    out = h.outputs[-1]
    line = [ln for ln in out.splitlines() if ln.startswith("DISPLAY ")][0]
    display = line.split(" ", 1)[1]
    assert display == h.custody_file(state.CANDIDATE).read_bytes().hex()


# 17
def test_c17_reject_mismatch_between_two_derivations(h):
    h.advance(state.PCW_CANDIDATE)
    _key, other = _test_pem()
    h.replace_file(h.custody_file(state.PRIVATE), other)
    rc, out, err = h.run("verify-candidate", PW)
    assert rc == 1 and "ERROR CANDIDATE_MISMATCH" in err
    assert "DISPLAY" not in out + err
    _assert_abandoned(h, err)


# 18
def test_c18_reject_manually_paired_or_caller_supplied_public_key(h):
    h.advance(state.PCW_CANDIDATE)
    caller_key = ed25519.Ed25519PrivateKey.generate().public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw
    )
    rc, _out, err = h.run(None, argv=["verify-candidate", caller_key.hex()])
    assert rc == 2 and "ERROR USAGE_REJECTED" in err
    assert h.marker() == state.PCW_CANDIDATE
    h.replace_file(h.custody_file(state.CANDIDATE), caller_key)
    rc, out, err = h.run("verify-candidate", PW)
    assert rc == 1 and "ERROR CANDIDATE_MISMATCH" in err and "DISPLAY" not in out
    _assert_abandoned(h, err)


# 19
@pytest.mark.parametrize("variant", ["flip", "truncate", "extend", "reencrypt"])
def test_c19_reject_altered_or_truncated_backup_bytes(h, variant):
    h.advance(state.PCW_VERIFIED)
    h.ok("restore-init")
    pem = h.custody_file(state.PRIVATE).read_bytes()
    if variant == "flip":
        data = bytearray(pem)
        data[60] ^= 0x01
        data = bytes(data)
    elif variant == "truncate":
        data = pem[:-40]
    elif variant == "extend":
        data = pem[:-len(custody.PEM_END)] + b"QUFB\n" + custody.PEM_END
    else:
        key = serialization.load_pem_private_key(pem, password=PW.encode("ascii"))
        _key, data = _test_pem(PW, key)
        assert data != pem
    with open(h.restore_file(state.RESTORE_ARTIFACT), "xb") as handle:
        handle.write(data)
    rc, out, err = h.run("restore-check", PW)
    assert rc == 1
    assert ("ERROR RESTORE_REJECTED" in err) or ("ERROR SERIALIZATION_REJECTED" in err)
    assert "DISPLAY" not in out
    _assert_abandoned(h, err)


# 20
def test_c20_reject_backup_restore_failure_or_wrong_type(h, monkeypatch):
    h.advance(state.PCW_VERIFIED)
    h.ok("restore-init")
    h.copy_backup()
    rc, _out, err = h.run("restore-check", OTHER_PASSPHRASE)
    assert rc == 1 and "ERROR KEY_RELOAD_REJECTED" in err
    _assert_abandoned(h, err)


def test_c20b_restore_wrong_loaded_type(h, monkeypatch):
    from cryptography.hazmat.primitives.asymmetric import x25519

    h.advance(state.PCW_VERIFIED)
    h.ok("restore-init")
    h.copy_backup()
    monkeypatch.setattr(
        serialization, "load_pem_private_key", lambda data, password: x25519.X25519PrivateKey.generate()
    )
    rc, _out, err = h.run("restore-check", PW)
    assert rc == 1 and "ERROR KEY_TYPE_REJECTED" in err
    _assert_abandoned(h, err)


# 21
def test_c21_reject_backup_derived_public_mismatch(h):
    h.advance(state.PCW_VERIFIED)
    h.ok("restore-init")
    h.copy_backup()
    h.replace_file(h.custody_file(state.CANDIDATE), os.urandom(32))
    rc, out, err = h.run("restore-check", PW)
    assert rc == 1 and "ERROR CANDIDATE_MISMATCH" in err and "DISPLAY" not in out
    _assert_abandoned(h, err)


# 22
def test_c22_no_secret_content_on_stdout_or_stderr(h):
    h.advance(state.READY)
    h.ok("pre-prepare-display", PW)
    h.run("pre-prepare-display", OTHER_PASSPHRASE)
    pem = h.custody_file(state.PRIVATE).read_bytes().decode("ascii")
    body_lines = [ln for ln in pem.splitlines() if ln and not ln.startswith("-----")]
    everything = "".join(h.outputs)
    assert PW not in everything and OTHER_PASSPHRASE not in everything
    assert "PRIVATE KEY" not in everything
    for line in body_lines:
        assert line not in everything
    for prompt in h.reader.prompts:
        assert PW not in prompt


# 23
def test_c23_no_secret_in_logs_traceback_telemetry_or_clipboard(h, monkeypatch):
    h.advance(state.PRIVATE_WRITTEN)

    def boom(pem, pw):
        raise RuntimeError("boom " + pw.decode("ascii") + " " + pem.decode("ascii"))

    monkeypatch.setattr(custody, "load_private", boom)
    rc, out, err = h.run("derive-candidate", PW)
    assert rc == 1 and err == "ERROR INTERNAL_FAILURE\nSTATE ABANDONED\n" and out == ""
    assert "Traceback" not in err and PW not in out + err
    import sys

    assert sys.tracebacklimit == 0
    forbidden_imports = {"logging", "traceback", "faulthandler", "socket", "http", "urllib", "ssl", "smtplib"}
    for name, source in production_sources().items():
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                assert not {a.name.split(".")[0] for a in node.names} & forbidden_imports, name
            if isinstance(node, ast.ImportFrom) and node.module:
                assert node.module.split(".")[0] not in forbidden_imports, name
        assert "user32" not in source and "Clipboard" not in source and "print(" not in source


# 24
def test_c24_reject_generic_or_arbitrary_message_signing(h):
    assert set(cli.COMMANDS) == {
        "preflight",
        "init",
        "generate",
        "derive-candidate",
        "verify-candidate",
        "restore-init",
        "restore-check",
        "restore-clear",
        "mark-backups-verified",
        "mark-ready",
        "pre-prepare-display",
        "abandon",
        "status",
    }
    for name, source in production_sources().items():
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                assert "sign" not in node.name.lower(), (name, node.name)
            if isinstance(node, ast.Attribute):
                assert node.attr != "sign", name
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                assert node.value.lower() not in {"sign", "sign-message", "sign-record"}, name
    for argv in (["sign"], ["sign", "message"], ["sign-message"]):
        rc, _out, err = h.run(None, argv=argv)
        assert rc == 2 and "ERROR USAGE_REJECTED" in err
