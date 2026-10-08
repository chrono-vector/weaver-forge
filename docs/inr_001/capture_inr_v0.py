"""Local INR capture CLI: an UNTRUSTED launcher for the trusted supervisor process.

    python -m docs.inr_001.capture_inr_v0 --event-id ID --repository REPO --out EXPORT.json
        [--ledger PATH] [--work-dir DIR]

This process computes no INR fact and accepts no evidence. It starts
``python -I -S -B <worktree>/docs/inr_001/supervisor_inr_v0.py`` by absolute path
with only non-trust parameters (event ID, repository, output path, ledger path,
work dir), stdin closed, and relays the report the supervisor prints on stdout. The
supervisor writes the export itself. The relayed report is only accepted when it
is bound to the launched process (its ``supervisor_pid`` equals the pid of the
child this launcher created and its ``event_id`` equals the requested one);
otherwise the launcher reports a non-PASS binding failure.

A written export or report on disk is a record, not evidence: re-checking it
(``validate_inr_v0``) is INFORMATIONAL_RECHECK only and never yields PASS.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

SUPERVISOR = Path(__file__).resolve().with_name("supervisor_inr_v0.py")
SUPERVISOR_TIMEOUT_SECONDS = 3600
INTERPRETER_FLAGS = ("-I", "-S", "-B")


def supervisor_command(event_id, repository, out, *, ledger=None, work_dir=None):
    """The exact supervisor argv: interpreter, isolation flags, absolute script, non-trust parameters."""
    command = [str(Path(sys.executable).resolve()), *INTERPRETER_FLAGS, str(SUPERVISOR),
               "--event-id", str(event_id), "--repository", str(Path(repository).resolve()),
               "--out", str(Path(out).resolve())]
    if ledger is not None:
        command += ["--ledger", str(Path(ledger).resolve())]
    if work_dir is not None:
        command += ["--work-dir", str(Path(work_dir).resolve())]
    return command


def _binding_failure(event_id, reason, returncode=None, stderr=b""):
    return {"schema_version": "inr.launcher.result.v0.r3", "result_kind": "LAUNCHER_BINDING_FAILURE",
            "derived_result": "UNCONFIRMED", "pass_allowed": False, "local_controls_result": "UNCONFIRMED",
            "event_id": event_id, "unconfirmed": ["launcher: " + reason],
            "supervisor_returncode": returncode,
            "supervisor_stderr_tail": stderr[-2000:].decode("utf-8", "replace")}


def launch_supervisor(event_id, repository, out, *, ledger=None, work_dir=None):
    """Launch the supervisor process and return (report, supervisor_returncode)."""
    command = supervisor_command(event_id, repository, out, ledger=ledger, work_dir=work_dir)
    child = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, env=dict(os.environ), shell=False)
    try:
        stdout, stderr = child.communicate(timeout=SUPERVISOR_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired:
        child.kill()
        child.communicate()
        return _binding_failure(event_id, "supervisor timeout"), None
    try:
        report = json.loads(stdout.decode("utf-8").strip().splitlines()[-1])
        if type(report) is not dict:
            raise ValueError
    except (IndexError, UnicodeError, ValueError):
        return _binding_failure(event_id, "supervisor produced no report", child.returncode, stderr), child.returncode
    if report.get("supervisor_pid") != child.pid or report.get("event_id") != event_id:
        return _binding_failure(event_id, "report is not bound to the launched supervisor process",
                                child.returncode, stderr), child.returncode
    if bool(report.get("pass_allowed")) != (child.returncode == 0):
        return _binding_failure(event_id, "supervisor exit status contradicts its report",
                                child.returncode, stderr), child.returncode
    return report, child.returncode


def main(argv=None):
    parser = argparse.ArgumentParser(prog="capture_inr_v0", allow_abbrev=False)
    parser.add_argument("--event-id", required=True)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--ledger", type=Path, default=None,
                        help="ledger JSONL path (default: per-user location outside the worktree)")
    parser.add_argument("--work-dir", type=Path, default=None,
                        help="parent directory for the supervisor's temporary staging directory")
    args = parser.parse_args(argv)
    if args.out.exists():
        parser.error("refusing to overwrite an existing event export")
    report, _ = launch_supervisor(args.event_id, args.repository, args.out,
                                  ledger=args.ledger, work_dir=args.work_dir)
    print(json.dumps(report, sort_keys=True))
    return 0 if report.get("pass_allowed") is True else 1


if __name__ == "__main__":
    raise SystemExit(main())
