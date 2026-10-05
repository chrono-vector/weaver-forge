"""Source-mutation campaign for the Ed25519 custody helper v0.

Not collected by pytest. Run with the test venv interpreter:

    python ed25519_custody_v0/tests/mutation_campaign_v0.py [MUTANT_ID ...]

Each mutant is applied to an isolated copy under %TEMP%\\ed25519c_mut\\<id>;
the repository is never modified. Every edit must match exactly once. The
runner verifies in-process that ``ed25519_custody_v0.__file__`` resolves into
the copy before running the full focused suite. Mapping numbers refer to the
30 planned source mutations of D1-R1; "X" entries are additional mutants.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

PKG = Path(__file__).resolve().parents[1]
REPO = PKG.parent
RUNBOOK_REL = Path("docs") / "next" / "DEDICATED_LOCAL_SOFTWARE_ED25519_CUSTODY_HELPER_RUNBOOK_V0_20261005.md"
BASE = Path(tempfile.gettempdir()).resolve() / "ed25519c_mut"


def M(mid, d1, file, edits, semantic, expect, equivalent=None):
    return {
        "id": mid,
        "d1": d1,
        "file": file,
        "edits": edits,
        "semantic": semantic,
        "expect": expect,
        "equivalent": equivalent,
    }


MUTANTS = [
    M("M01", "1", "custody.py",
      [("encryption_algorithm=serialization.BestAvailableEncryption(passphrase),",
        "encryption_algorithm=serialization.NoEncryption(),")],
      "private container serialized with NoEncryption", "c01,c01b"),
    M("M02", "2", "custody.py",
      [("format=serialization.PrivateFormat.PKCS8,", "format=serialization.PrivateFormat.OpenSSH,")],
      "private format PKCS8 -> OpenSSH", "c01b,c02,c12"),
    M("M02b", "2", "custody.py",
      [("encoding=serialization.Encoding.PEM,", "encoding=serialization.Encoding.DER,")],
      "private encoding PEM -> DER", "c01b,c12"),
    M("M03", "3", "custody.py",
      [('return ["STATE " + state.PRIVATE_WRITTEN]',
        'return ["STATE " + state.PRIVATE_WRITTEN, pem.decode("ascii")]')],
      "encrypted private PEM echoed to stdout after generate", "c22"),
    M("M03b", "3", "custody.py",
      [("        raw = raw_public(load_private(pem, passphrase))\n        winsec.write_new_file(",
        "        os.write(2, load_private(pem, passphrase).private_bytes_raw())\n"
        "        raw = raw_public(load_private(pem, passphrase))\n        winsec.write_new_file(")],
      "raw private seed written to stderr via private_bytes_raw", "c02,c22,c24"),
    M("M04", "4", "console.py",
      [('return validate_passphrase(read_secret("Passphrase (hidden): "))',
        'return validate_passphrase(__import__("os").environ.get("WEAVERFORGE_UNLOCK") '
        'or read_secret("Passphrase (hidden): "))')],
      "unlock passphrase accepted from an environment variable", "c04,x18"),
    M("M04b", "4", "cli.py",
      [("    command = COMMANDS[argv[0]]\n",
        "    command = COMMANDS[argv[0]]\n"
        "    if not sys.stdin.isatty():\n"
        "        __import__('ed25519_custody_v0.console').console._hidden_reader = lambda: "
        "(lambda prompt: sys.stdin.readline().rstrip('\\n'))\n")],
      "passphrase read from a piped stdin when stdin is not a TTY", "c04,c40"),
    M("M05", "5", "console.py",
      [('    if first != second:\n        fail("PASSPHRASE_MISMATCH")\n',
        '    if False:\n        fail("PASSPHRASE_MISMATCH")\n')],
      "mismatched confirmation accepted", "c06"),
    M("M05b", "5,26", "console.py",
      [('        warnings.simplefilter("error", getpass.GetPassWarning)\n'
        '        if not _warning_is_error():\n            fail("CONSOLE_PREFLIGHT_REJECTED")\n',
        '        warnings.simplefilter("ignore", getpass.GetPassWarning)\n')],
      "GetPassWarning suppressed instead of raised", "c05,c40"),
    M("M05c", "5", "console.py",
      [("        and facts.stdin_is_char_device is True\n", "")],
      "non-character-device stdin accepted", "c05,c40"),
    M("M06", "6", "paths.py",
      [('    root = ctx.local_appdata.rstrip("\\\\") + "\\\\" + ROOT_NAME',
        '    root = os.environ.get("WEAVERFORGE_ROOT") or (ctx.local_appdata.rstrip("\\\\") + "\\\\" + ROOT_NAME)')],
      "caller-selected root via environment", "x18"),
    M("M06b", "6", "cli.py",
      [("len(argv) != 1", "len(argv) < 1")],
      "extra arguments (path/options) accepted after the subcommand", "c03,c46,x11"),
    M("M07", "7", "paths.py",
      [('        if os.path.lexists(current + "\\\\.git"):\n', "        if False:\n")],
      "Git marker in any existing ancestor ignored", "c07,c07b"),
    M("M07b", "7", "paths.py",
      [("    if winsec.sync_root_hresult(deepest) != winsec.HRESULT_NOT_IN_SYNC_ROOT:\n", "    if False:\n")],
      "cloud-files sync-root API result ignored", "c08b"),
    M("M07c", "7", "paths.py",
      [("        if attrs & winsec.FILE_ATTRIBUTE_REPARSE_POINT:\n", "        if False:\n")],
      "reparse ancestor component accepted", "c09,c09c"),
    M("M07d", "7", "paths.py",
      [("        if temp and _is_under(path, temp):", "        if False:")],
      "temp location accepted", "c08"),
    M("M07e", "7", "paths.py",
      [("    if ctx.roaming and _is_under(path, ctx.roaming):", "    if False:")],
      "roaming location accepted", "c08"),
    M("M07f", "7", "paths.py",
      [("    if winsec.drive_type(path[:3]) != winsec.DRIVE_FIXED:", "    if False:")],
      "network/removable drive accepted", "c08"),
    M("M07g", "7", "paths.py",
      [('        if low.startswith("onedrive") or low in _SYNC_COMPONENTS:', "        if False:")],
      "sync-provider path component accepted", "c08"),
    M("M07h", "7", "paths.py",
      [("        if sync and _is_under(path, sync):", "        if False:")],
      "known sync root accepted", "c08"),
    M("M08", "8", "winsec.py",
      [("    if not control & SE_DACL_PROTECTED:\n", "    if False:\n")],
      "directory DACL inheritance (unprotected) accepted", "c10,c43b"),
    M("M08b", "8", "winsec.py",
      [("    if sorted(aces) != _expected_aces(user_sid, OBJECT_INHERIT_ACE | CONTAINER_INHERIT_ACE):",
        "    if not set(_expected_aces(user_sid, OBJECT_INHERIT_ACE | CONTAINER_INHERIT_ACE)) <= set(aces):")],
      "extra broad directory ACEs accepted", "c10,c10c"),
    M("M08c", "8", "winsec.py",
      [("    if sorted(aces) != _expected_aces(user_sid, INHERITED_ACE):",
        "    if not set(_expected_aces(user_sid, INHERITED_ACE)) <= set(aces):")],
      "extra explicit file ACEs accepted (N1)", "c10b,x01"),
    M("M08d", "8", "winsec.py",
      [('    """Protected explicit DACL: intended user plus SYSTEM, OICI full access only."""\n'
        "    if owner != user_sid:",
        '    """Protected explicit DACL: intended user plus SYSTEM, OICI full access only."""\n'
        "    if False:")],
      "wrong directory owner accepted", "c10"),
    M("M08e", "8,28", "winsec.py",
      [('"D:P(A;OICI;FA;;;SY)', '"D:(A;OICI;FA;;;SY)')],
      "created directory SDDL leaves inheritance enabled", "c43,x01"),
    M("M09", "9", "winsec.py",
      [("        CREATE_NEW,\n", "        2,\n")],
      "CREATE_NEW -> CREATE_ALWAYS (overwrite existing container)", "c11"),
    M("M10", "10", "custody.py",
      [("def require_encrypted_label(data) -> None:\n", "def require_encrypted_label(data) -> None:\n    return\n")],
      "encrypted-label validation skipped", "c01,c12"),
    M("M10b", "10", "custody.py",
      [('        key = None\n        fail("KEY_RELOAD_REJECTED")\n', "        key = None\n")],
      "reload failure not reported as reload rejection", "c12b,c06"),
    M("M11", "11", "custody.py",
      [("encoding=serialization.Encoding.Raw,\n            format=serialization.PublicFormat.Raw,",
        "encoding=serialization.Encoding.DER,\n            format=serialization.PublicFormat.SubjectPublicKeyInfo,")],
      "public encoding Raw/Raw -> DER/SPKI", "c13,c15"),
    M("M12", "12", "custody.py",
      [("        if ch not in _HEX:", "        if False:")],
      "non-lowercase-hex display accepted", "c16"),
    M("M12b", "12", "custody.py",
      [('    if type(raw) is not bytes or len(raw) != 32:\n        fail("PUBLIC_OUTPUT_REJECTED")',
        '    if type(raw) is not bytes:\n        fail("PUBLIC_OUTPUT_REJECTED")')],
      "public length not enforced", "c15"),
    M("M12c", "12", "custody.py",
      [('    if type(data) is not bytes or len(data) != 32:\n        fail("CANDIDATE_REJECTED")',
        '    if type(data) is not bytes:\n        fail("CANDIDATE_REJECTED")')],
      "candidate file length not enforced", "c36"),
    M("M12d", "12", "custody.py",
      [("    if type(text) is not str or len(text) != 64:", "    if type(text) is not str:")],
      "display length not enforced", "c16"),
    M("M13", "13", "custody.py",
      [("        raw = raw_public(load_private(pem, passphrase))\n        candidate = _read_candidate(s)\n"
        "        if raw != candidate:\n            fail(\"CANDIDATE_MISMATCH\")\n        display_1 = canonical_display(candidate)",
        "        candidate = _read_candidate(s)\n        raw = candidate\n        display_1 = canonical_display(candidate)")],
      "second clean derivation removed (candidate trusted)", "c17"),
    M("M13b", "13", "custody.py",
      [("        if raw != candidate:\n            fail(\"CANDIDATE_MISMATCH\")\n        display_1",
        "        display_1")],
      "derivation-2 exact-byte equality comparison removed", "c17"),
    M("M14", "14", "custody.py",
      [('        if restored != working:\n            fail("RESTORE_REJECTED")\n', "")],
      "backup exact encrypted-byte comparison skipped", "c19"),
    M("M14b", "14", "custody.py",
      [("        passphrase = console.read_unlock_passphrase()\n        raw = raw_public(load_private(restored, passphrase))\n"
        "        candidate = _read_candidate(s)\n        if raw != candidate:\n            fail(\"CANDIDATE_MISMATCH\")\n"
        "        display = canonical_display(raw)\n        if display != canonical_display(candidate):\n"
        "            fail(\"DISPLAY_REJECTED\")\n        winsec.delete_file(artifact)",
        "        candidate = _read_candidate(s)\n        display = canonical_display(candidate)\n"
        "        winsec.delete_file(artifact)")],
      "backup reload and public-key verification skipped", "c20,c21"),
    M("M15", "15", "manifest.py",
      [("        or tuple(facts.version_info) != _PYTHON_VERSION\n", "")],
      "wrong Python version accepted", "c26,x13"),
    M("M15b", "15", "manifest.py",
      [("            or dist.has_direct_url is not False\n", "")],
      "source/editable (direct_url) distribution accepted", "c27,x13"),
    M("M15c", "15", "manifest.py",
      [("        if not _under(filename, site_packages):", "        if False:")],
      "shadowed crypto module path accepted", "c27,x13"),
    M("M15d", "15", "manifest.py",
      [("    if facts.fallback_modules:\n", "    if False:\n")],
      "fallback crypto module accepted", "c27,c28"),
    M("M15e", "15", "manifest.py",
      [("    if facts.record_result is not None:\n", "    if False:\n")],
      "RECORD mismatch ignored", "x13"),
    M("M15f", "15", "manifest.py",
      [("        if entry not in allowed:\n", "        if False:\n")],
      "sys.path whitelist not enforced", "c27,x13"),
    M("M15g", "15", "manifest.py",
      [("                    if full not in listed:\n                        return None\n", "                    pass\n")],
      "unlisted files in a pinned distribution accepted", "x08"),
    M("M15h", "15", "manifest.py",
      [("    if facts.openssl_version_text != _OPENSSL_VERSION_TEXT:", "    if False:")],
      "wrong OpenSSL accepted", "x13"),
    M("M15i", "15,27", "manifest.py",
      [('    if _INTERPRETER_PROVENANCE is None:\n        fail("ENV_PROVENANCE_NOT_RECORDED")\n', "")],
      "unrecorded interpreter provenance no longer fails closed", "c39,x07,x13"),
    M("M16", "16", "cli.py",
      [('    "status": custody.phase_status,\n}', '    "status": custody.phase_status,\n    "sign": custody.phase_status,\n}')],
      "sign subcommand added", "c24"),
    M("M16b", "16", "custody.py",
      [("import datetime\nimport os\n", "import datetime\nimport os\nimport socket\n")],
      "network capability imported", "c24,c30"),
    M("M17", "17", "cli.py",
      [('    except Exception:\n        _emit(sys.stderr, ["ERROR INTERNAL_FAILURE"])',
        '    except Exception as exc:\n        _emit(sys.stderr, ["ERROR INTERNAL_FAILURE " + repr(exc)])')],
      "exception text leaked on stderr", "c23,x19"),
    M("M17b", "17", "cli.py",
      [("    sys.tracebacklimit = 0\n", "")],
      "traceback suppression removed", "c23"),
    M("M17c", "17", "errors.py",
      [("    raise CustodyError(code) from None", "    raise CustodyError(code)")],
      "underlying exception context chained into failures", "x19"),
    M("M18", "18", "custody.py",
      [('return ["STATE " + state.READY, "ADMISSION NOT_PERFORMED"]',
        'return ["STATE " + state.READY, "ADMISSION NOT_PERFORMED", "SNAPSHOT_REUSE historical-v0"]')],
      "historical snapshot referenced for the new key", "c29,x20"),
    M("M19", "19", "custody.py",
      [("        winsec.write_new_file(s.paths.custody_file(state.CANDIDATE), s.user_sid, raw)\n",
        "        winsec.write_new_file(s.paths.custody_file(state.CANDIDATE), s.user_sid, raw)\n"
        '        winsec.write_new_file(s.paths.root + "\\\\public-candidate.bin", s.user_sid, raw)\n')],
      "public candidate also written outside the fixed candidate path", "c36,c37"),
    M("M20", "20", "custody.py",
      [("        candidate = _read_candidate(s)\n        if raw != candidate:\n            fail(\"CANDIDATE_MISMATCH\")\n"
        "        display = canonical_display(raw)\n        if display != canonical_display(candidate):\n"
        "            fail(\"DISPLAY_REJECTED\")\n        return display\n",
        "        candidate = _read_candidate(s)\n        display = canonical_display(candidate)\n        return display\n")],
      "PREPARE display taken from stored candidate without fresh comparison", "c37,x21"),
    M("M21", "21", "custody.py",
      [("    if current not in state.ORDER or state.successor(current) != new:", "    if current not in state.ORDER:")],
      "skip/backward transition accepted by commit", "c34,x22"),
    M("M21b", "21", "custody.py",
      [("        if names is None or names != state.files_for(token):\n            fail(\"STATE_REJECTED\")\n    except",
        "        if names is None:\n            fail(\"STATE_REJECTED\")\n    except")],
      "mismatched state/file set accepted after restart", "c33,c34,c45"),
    M("M21c", "21", "state.py",
      [("    PCW_RESTORE_2,\n    BACKUPS_VERIFIED,\n", "    BACKUPS_VERIFIED,\n")],
      "second restore-check state removed", "x04c,x10"),
    M("M21d", "21", "state.py",
      [("        if data == encode_marker(token):", "        if data.startswith(encode_marker(token)):")],
      "marker with trailing/duplicated content accepted", "c34"),
    M("M22", "22", "custody.py",
      [('    if token == state.ABANDONED:\n        fail("STATE_ABANDONED")\n    return token', "    return token")],
      "ABANDONED generation not rejected as abandoned", "c35,c46,x23"),
    M("M23", "23", "custody.py",
      [('        winsec.move_no_replace(p.custody, p.quarantine + "\\\\custody-v0-" + stamp)\n', "        pass\n"),
       ('    if _exists(p.custody) or _exists(p.restore):\n        fail("STATE_REJECTED")\n    return ["STATE " + state.ABANDONED',
        '    return ["STATE " + state.ABANDONED')],
      "abandon leaves the active custody handoff in place", "c46,x03"),
    M("M23b", "23", "cli.py",
      [("len(argv) != 1", '(len(argv) != 1 and argv[:1] != ["abandon"])')],
      "abandon accepts caller arguments", "c46"),
    M("M24", "24", "cli.py",
      [('    "status": custody.phase_status,\n}', '    "status": custody.phase_status,\n    "report-loss": custody.phase_status,\n}')],
      "ordinary-loss command added", "c41"),
    M("M25", "25", "console.py",
      [("MIN_PASSPHRASE = 24", "MIN_PASSPHRASE = 16")],
      "passphrase shorter than the 128-bit shape floor accepted", "c06b,c47"),
    M("M25b", "25", "console.py",
      [("        if code < 0x20 or code > 0x7E:", "        if code < 0x20:")],
      "non-ASCII passphrase characters accepted", "c06"),
    M("M26", "26", "console.py",
      [("    console_preflight()\n    reader = _hidden_reader()", "    reader = _hidden_reader()")],
      "secret read without console preflight", "c40,x24"),
    M("M26b", "26", "console.py",
      [("        and facts.warnoptions_empty is True\n", "")],
      "warning options not checked before secret read", "c40"),
    M("M27", "27", "manifest.py",
      [("        if upper.startswith(_INJECTION_PREFIXES) or any(m in upper for m in _INJECTION_MARKERS):", "        if False:")],
      "Python/OpenSSL injection variables accepted", "c38"),
    M("M27b", "27", "manifest.py",
      [("        facts.isolated is not True\n        or ", "        ")],
      "non-isolated interpreter accepted", "c38,x13"),
    M("M27c", "27", "manifest.py",
      [('        cfg.get("include-system-site-packages") != "false"\n        or ', "        ")],
      "system site packages accepted", "c39,x13"),
    M("M27d", "27", "manifest.py",
      [("    if _norm(facts.helper_file) != _norm(", "    if False and _norm(facts.helper_file) != _norm(")],
      "helper module loaded from an unverified path accepted", "x13"),
    M("M28", "28", "winsec.py",
      [("        if not _CreateDirectoryW(path, ctypes.byref(attrs)):", "        if not _CreateDirectoryW(path, None):")],
      "directory created with inherited (permissive) DACL", "c43,x01"),
    M("M28b", "28", "winsec.py",
      [("        info = _verify_open_file(handle, path, user_sid)\n        if info.size != 0:\n            fail(\"FILE_REJECTED\")\n", "")],
      "secret written before owner/DACL verification of the new file", "c43,x25"),
    M("M29", "29", "custody.py",
      [("        restored, restored_id = winsec.read_file(artifact, s.user_sid, MAX_PEM)",
        "        restored, restored_id = winsec.read_file(p.custody_file(state.PRIVATE), s.user_sid, MAX_PEM)"),
       ('        if restored_id == working_id:\n            fail("RESTORE_REJECTED")\n', "")],
      "restore check falls back to reading the working original", "c42"),
    M("M29b", "29", "custody.py",
      [('    if not isinstance(key, ed25519.Ed25519PrivateKey):\n        fail("KEY_TYPE_REJECTED")\n    return key',
        "    return key")],
      "exact Ed25519PrivateKey type check skipped", "c20b,c44"),
    M("M29c", "29", "custody.py",
      [("    artifact = p.restore_file(state.RESTORE_ARTIFACT)",
        '    artifact = os.environ.get("WEAVERFORGE_RESTORE") or p.restore_file(state.RESTORE_ARTIFACT)')],
      "caller-selectable restore source via environment", "c42"),
    M("M29d", "29", "custody.py",
      [('        if restored_id == working_id:\n            fail("RESTORE_REJECTED")\n', "")],
      "restore artifact/working identity comparison removed", "c42",
      equivalent=(
          "read_file rejects any file whose link count is not 1, and the artifact and working "
          "container are opened by distinct fixed names in distinct fixed directories; equal "
          "volume/file-index identity therefore cannot occur without a second hard link, which "
          "is already rejected (defense in depth)."
      )),
    M("M30", "30", "custody.py",
      [("def _guarded(", "def sign_record(key, record):\n    return key.sign(record)\n\n\ndef _guarded(")],
      "free-form record signing function added", "c24"),
    M("X01", "N2", "custody.py",
      [("    if token == state.READY:\n        raise CustodyError(code) from None\n", "")],
      "READY failure transitions to ABANDONED (N2 violated)", "x02"),
    M("X02", "acct", "winsec.py",
      [("    if facts.elevated:\n", "    if False:\n")],
      "elevated token accepted", "x06"),
    M("X03", "acct", "winsec.py",
      [("        if group in _FORBIDDEN_GROUP_SIDS:\n", "        if False:\n")],
      "administrator/service group accepted", "x06"),
    M("X04", "N4", "custody.py",
      [("    clean = names is not None and names <= known", "    clean = names is not None")],
      "restore-clear deletes unknown entries instead of quarantining", "x04b"),
    M("X05", "N4", "custody.py",
      [("        if state.decode_restore_marker(marker) != check:", "        if state.decode_restore_marker(marker) is None:")],
      "restore slot marker for the wrong check accepted", "x04,x04c"),
    M("X06", "36", "winsec.py",
      [("    if info.links != 1:", "    if False:")],
      "hard-linked files accepted", "c36,c42"),
    M("X07", "33", "custody.py",
      [("        mark_abandoned(s)\n        abandoned = True\n", "        mark_abandoned(s)\n        abandoned = False\n")],
      "ABANDONED transition not reported", "c33"),
    M("X08", "N3", "custody.py",
      [("    return [\"STATE \" + load_state(s, mutate=False)]", "    return [\"STATE \" + load_state(s)]")],
      "status mutates state on integrity failure", "x09"),
    M("X09", "5", "console.py",
      [("    if getpass.getpass is not getpass.win_getpass:\n        fail(\"CONSOLE_PREFLIGHT_REJECTED\")\n    return getpass.getpass",
        "    return getpass.getpass")],
      "non-console getpass implementation accepted by the real reader", "c05b"),
    M("X10", "36", "winsec.py",
      [("    if not _same_path(info.final_path, path):\n        fail(\"FILE_REJECTED\")",
        "    if False:\n        fail(\"FILE_REJECTED\")")],
      "file final-path (redirection) check removed", "c36,x26"),
]

RUNNER = r"""
import os, sys
copy = os.path.normcase(os.path.abspath(sys.argv[1]))
sys.path.insert(0, sys.argv[1])
import ed25519_custody_v0
loaded = os.path.normcase(os.path.abspath(ed25519_custody_v0.__file__))
if not loaded.startswith(copy + os.sep):
    print("MUTANT_FILE_ESCAPED " + loaded, flush=True)
    sys.exit(97)
print("MUTANT_FILE " + loaded, flush=True)
import pytest
sys.exit(pytest.main(sys.argv[2:]))
"""


def _inside_base(path: Path) -> bool:
    try:
        path.resolve().relative_to(BASE)
    except ValueError:
        return False
    return path.resolve() != BASE


def _prepare(mutant) -> Path:
    target = BASE / mutant["id"]
    if not _inside_base(target):
        raise SystemExit("refusing target outside " + str(BASE))
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(PKG, target / "ed25519_custody_v0", ignore=shutil.ignore_patterns("__pycache__"))
    (target / RUNBOOK_REL).parent.mkdir(parents=True)
    shutil.copyfile(REPO / RUNBOOK_REL, target / RUNBOOK_REL)
    if mutant["file"]:
        source = target / "ed25519_custody_v0" / mutant["file"]
        text = source.read_bytes().decode("utf-8")
        for old, new in mutant["edits"]:
            if text.count(old) != 1:
                raise SystemExit("anchor not unique for " + mutant["id"] + ": " + old[:60])
            text = text.replace(old, new)
        source.write_bytes(text.encode("utf-8"))
    return target


def run(mutant) -> dict:
    target = _prepare(mutant)
    basetemp = BASE / "pt" / mutant["id"]
    cmd = [
        sys.executable, "-c", RUNNER, str(target),
        str(target / "ed25519_custody_v0" / "tests"),
        "-p", "no:cacheprovider", "-q", "-rfE", "--tb=no", "--basetemp=" + str(basetemp),
    ]
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    proc = subprocess.run(cmd, cwd=str(target), env=env, capture_output=True, text=True, timeout=1800)
    out = proc.stdout
    loaded = re.search(r"^MUTANT_FILE (.+)$", out, re.M)
    failed = sorted(set(re.findall(r"^(?:FAILED|ERROR) \S+?::(test_[A-Za-z0-9_]+)", out, re.M)))
    summary = re.findall(r"^=*\s*(.*(?:passed|failed|error).*?)\s*=*$", out, re.M)
    if proc.returncode == 0:
        status = "EQUIVALENT" if mutant["equivalent"] else "SURVIVED"
    elif proc.returncode == 1 and failed and loaded:
        status = "KILLED"
    else:
        status = "INVALID(rc=%d)" % proc.returncode
    return {
        "id": mutant["id"],
        "d1": mutant["d1"],
        "file": mutant["file"],
        "semantic": mutant["semantic"],
        "expect": mutant["expect"],
        "observed": [name[5:] if name.startswith("test_") else name for name in failed],
        "status": status,
        "loaded": loaded.group(1) if loaded else None,
        "summary": summary[-1] if summary else out[-300:],
        "equivalent": mutant["equivalent"],
    }


def main(argv) -> int:
    BASE.mkdir(parents=True, exist_ok=True)
    (BASE / "pt").mkdir(exist_ok=True)
    chosen = [m for m in MUTANTS if not argv or m["id"] in argv]
    baseline = run({"id": "BASELINE", "d1": "-", "file": "", "edits": [], "semantic": "unmutated copy",
                    "expect": "", "equivalent": None})
    print(json.dumps(baseline), flush=True)
    if baseline["status"] not in ("SURVIVED",):
        print("BASELINE_NOT_GREEN")
        return 3
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(run, chosen))
    for result in results:
        print(json.dumps(result), flush=True)
    (BASE / "results.json").write_text(json.dumps([baseline] + results, indent=1), encoding="utf-8")
    counts = {}
    for result in results:
        key = result["status"].split("(")[0]
        counts[key] = counts.get(key, 0) + 1
    print("COUNTS " + json.dumps(counts, sort_keys=True))
    return 0 if all(r["status"] in ("KILLED", "EQUIVALENT") for r in results) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
