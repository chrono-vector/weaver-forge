"""Local INR capture CLI: the only operator entry into the fused capture/verify path.

The written export is a record, not evidence: re-checking it from disk
(validate_inr_v0) can never yield PASS.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .trusted_capture import _run_and_verify


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--event-id", required=True)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--ledger", type=Path, default=None,
                        help="ledger JSONL path (default: per-user location outside the worktree)")
    parser.add_argument("--work-dir", type=Path, default=None,
                        help="parent directory for the temporary staging directory")
    args = parser.parse_args(argv)
    if args.out.exists():
        parser.error("refusing to overwrite an existing event export")
    result, export = _run_and_verify(args.repository, args.event_id,
                                     ledger_path=args.ledger, work_dir=args.work_dir)
    if export is not None:
        with args.out.open("x", encoding="utf-8", newline="\n") as handle:
            json.dump(export, handle, indent=2, sort_keys=True)
            handle.write("\n")
    print(json.dumps(result, sort_keys=True))
    return 0 if result["pass_allowed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
