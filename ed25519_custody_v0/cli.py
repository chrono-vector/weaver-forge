"""Command-line entry for the Ed25519 custody helper v0.

Exactly one no-argument subcommand runs per process. There are no options,
paths, key, snapshot, algorithm, passphrase, or message arguments. Errors
are fixed public codes; no traceback or exception text is printed.
"""

from __future__ import annotations

import sys

from . import custody, manifest
from .errors import CustodyError

COMMANDS = {
    "preflight": custody.phase_preflight,
    "init": custody.phase_init,
    "generate": custody.phase_generate,
    "derive-candidate": custody.phase_derive_candidate,
    "verify-candidate": custody.phase_verify_candidate,
    "restore-init": custody.phase_restore_init,
    "restore-check": custody.phase_restore_check,
    "restore-clear": custody.phase_restore_clear,
    "mark-backups-verified": custody.phase_mark_backups_verified,
    "mark-ready": custody.phase_mark_ready,
    "pre-prepare-display": custody.phase_pre_prepare_display,
    "abandon": custody.phase_abandon,
    "status": custody.phase_status,
}


def _emit(stream, lines) -> None:
    for line in lines:
        stream.write(line + "\n")
    stream.flush()


def main(argv=None) -> int:
    sys.tracebacklimit = 0
    if argv is None:
        argv = sys.argv[1:]
    if type(argv) is not list or len(argv) != 1 or type(argv[0]) is not str or argv[0] not in COMMANDS:
        _emit(sys.stderr, ["ERROR USAGE_REJECTED"])
        return 2
    command = COMMANDS[argv[0]]
    try:
        manifest.run_preflight()
        session = custody.open_session()
        lines = command(session)
    except CustodyError as exc:
        out = ["ERROR " + exc.code]
        if exc.abandoned:
            out.append("STATE " + "ABANDONED")
        _emit(sys.stderr, out)
        return 1
    except Exception:
        _emit(sys.stderr, ["ERROR INTERNAL_FAILURE"])
        return 1
    _emit(sys.stdout, lines)
    return 0
