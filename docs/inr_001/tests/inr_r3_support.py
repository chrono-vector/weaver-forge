"""Shared helpers for the INR-001 r3 tests (not a test module).

Every temporary directory is created with the ``inr001_r3_t_`` prefix and every test
ledger lives in such a directory (never the per-user default ledger).
"""
from __future__ import annotations

import base64
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
from unittest import mock

REPO = Path(__file__).resolve().parents[3]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from docs.inr_001 import capture_inr_v0 as capture  # noqa: E402
from docs.inr_001 import supervisor_inr_v0 as sup  # noqa: E402

TMP_PREFIX = "inr001_r3_t_"
HF = "PSM_NEG_HUMAN_FINAL_INFERENCE"
PN = "PSM_REQUIRED_PRODUCTION_NONCLAIM"
EXTERNAL = sup.EXTERNAL_PREDICATES
# Never created: read-only lookups of a missing ledger see an empty ledger.
ABSENT_LEDGER = Path(tempfile.gettempdir()) / "inr001_r3_absent" / "ledger.jsonl"


def rmtree(path):
    def onexc(func, target, _exc):
        os.chmod(target, stat.S_IWRITE)
        func(target)
    if sys.version_info >= (3, 12):
        shutil.rmtree(path, onexc=onexc)
    else:  # pragma: no cover
        shutil.rmtree(path, onerror=lambda f, p, e: onexc(f, p, e))


def tempdir():
    return Path(tempfile.mkdtemp(prefix=TMP_PREFIX))


def _live_available():
    try:
        sup.probe_git(REPO)
        return True
    except (OSError, ValueError, subprocess.SubprocessError):
        return False


LIVE = _live_available()


def profile():
    return sup.configuration()[0]


def spec(case_id):
    return next(c for c in profile()["required_cases"] if c["case_id"] == case_id)


def not_pass(test, result):
    test.assertIsInstance(result, dict)
    test.assertFalse(result.get("pass_allowed"), result)
    test.assertNotEqual(result.get("derived_result"), "PASS", result)


def record(export, case_id):
    return next(r for r in export["capture_records"] if r["case_id"] == case_id)


def child_report(rec):
    return json.loads(base64.b64decode(rec["stdout_base64"]))


def run_supervisor_process(event_id, tmp, *, repository=REPO, ledger=None, env=None):
    """Launch the real supervisor process through the launcher; (report, rc, export|None)."""
    out = tmp / (event_id + ".export.json")
    ledger = tmp / "ledger.jsonl" if ledger is None else ledger
    with mock.patch.dict(os.environ, env or {}):
        report, rc = capture.launch_supervisor(event_id, repository, out, ledger=ledger, work_dir=tmp)
    export = json.loads(out.read_bytes()) if out.exists() else None
    return report, rc, export


def pinned_bytes(path):
    return sup._git(sup.DEFAULT_GIT.resolve(), REPO, "show", sup.TARGET_SHA + ":" + path)


def run_pinned_probe(input_bytes):
    """Run the pinned PSM validator through the runtime probe on caller bytes; (rc, errors)."""
    executable = sup.DEFAULT_GIT.resolve()
    tmp = tempdir()
    try:
        (tmp / "validate_psm_v0.py").write_bytes(pinned_bytes("docs/portfolio_state/validate_psm_v0.py"))
        (tmp / "input.json").write_bytes(input_bytes)
        cp = subprocess.run([sys.executable, "-I", "-S", "-B", str(sup.PROBE), str(tmp / "validate_psm_v0.py"),
                             str(tmp / "input.json"), str(REPO)], cwd=tmp, env=sup.child_environment(executable),
                            capture_output=True, check=False, timeout=300)
        return cp.returncode, json.loads(cp.stdout)["errors"]
    finally:
        rmtree(tmp)


def synthetic_export(event_id, challenge, reservation_sha, *, pid=4242):
    """A schema-valid, fully self-authored export that claims PASS everywhere."""
    stdout = json.dumps({"event_id": event_id, "challenge": challenge, "case_id": "PSM_POSITIVE_ACCEPTED_RECORD",
                         "case_nonce": "a" * 32, "identity": {}, "errors": []}).encode()
    rec = {"case_id": "PSM_POSITIVE_ACCEPTED_RECORD", "command_id": "CMD_PSM_POSITIVE_ACCEPTED_RECORD",
           "sequence": 1, "event_id": event_id, "challenge": challenge, "case_nonce": "a" * 32,
           "argv": ["python", "-I", "-S", "-B"], "popen_args": ["python", "-I", "-S", "-B"], "cwd": "C:/x",
           "env_path": "C:/git", "env_git": [["GIT_NO_REPLACE_OBJECTS", "1"]], "child_pid": pid,
           "return_code": 0, "start_ns": 1, "end_ns": 2,
           "stdout_base64": base64.b64encode(stdout).decode(), "stderr_base64": "",
           "stdout_sha256": sup.digest(stdout), "stderr_sha256": sup.digest(b"")}
    verification = {"schema_version": sup.RESULT_SCHEMA_VERSION, "result_kind": "FRESH_SUPERVISOR_RUN",
                    "event_id": event_id, "supervisor_pid": pid, "derived_result": "PASS", "pass_allowed": True,
                    "local_controls_result": "PASS",
                    "predicates": {name: "PASS" for name in sup.REQUIRED_PREDICATES},
                    "not_established": [], "blocked": [], "fail": [], "unconfirmed": [], "contradictions": [],
                    "nonclaims": list(sup.NONCLAIMS)}
    return {"schema_version": sup.EVENT_SCHEMA_VERSION, "inr_event_id": event_id, "target_sha": sup.TARGET_SHA,
            "accepted_target_profile_binding": {"target_profile_id": "INR_TARGET_PROFILE_PSM_001_V0",
                                                "target_profile_digest": sup.PROFILE_DIGEST},
            "accepted_origin_reference_binding": {"origin_reference_set_id": "x",
                                                  "origin_reference_set_digest": sup.ORIGIN_DIGEST},
            "challenge": challenge, "ledger_reservation_entry_sha256": reservation_sha,
            "supervisor": {"pid": pid, "executable": "python", "python_version": [3, 11, 9], "isolated": 1,
                           "no_site": 1, "dont_write_bytecode": True, "is_supervisor_process": True},
            "lifecycle": {name: index for index, name in enumerate(sup.LIFECYCLE, 1)},
            "git_probe": {}, "measurements": {}, "capture_records": [rec], "verification": verification,
            "nonclaims": list(sup.NONCLAIMS)}
