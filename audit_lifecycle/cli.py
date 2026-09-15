from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .freeze import FreezeAlreadyExists
from .orchestrator import AuditOrchestrator
from .request import AuditRequest, read_json, write_json


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="audit_lifecycle",
        description="Weaver Forge Audit Lifecycle — third-party entrypoint",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    run_p = sub.add_parser("run", help="Intake request and execute through decision/freeze")
    run_p.add_argument("--request", required=True, help="Path to audit request JSON")
    run_p.add_argument("--out", required=True, help="Parent directory for run outputs")

    freeze_p = sub.add_parser("freeze", help="Apply human-review gate and freeze an existing run")
    freeze_p.add_argument("--run", required=True, help="Run directory")
    freeze_p.add_argument(
        "--policy-from-request",
        action="store_true",
        default=True,
        help="Load policy from AUDIT_REQUEST.json (default)",
    )

    verify_p = sub.add_parser("verify", help="Verify SHA256 bindings and freeze integrity")
    verify_p.add_argument("--run", required=True, help="Run directory")

    args = parser.parse_args(argv)

    if args.cmd == "run":
        request = AuditRequest.from_file(Path(args.request))
        orch = AuditOrchestrator(Path(args.out))
        result = orch.run_through_decision(request)
        print(json.dumps(result, indent=2))
        decision = result["decision"]["decision"]
        if decision == "PASS" and result.get("frozen"):
            return 0
        if decision == "PASS" and not result.get("frozen"):
            print(
                "AWAITING_HUMAN_REVIEW: write HUMAN_REVIEW.json then run: "
                "python -m audit_lifecycle.cli freeze --run <run_dir>",
                file=sys.stderr,
            )
            return 0
        # FAIL/BLOCKED/INCONCLUSIVE preserved under run dir
        return 1

    if args.cmd == "freeze":
        run_dir = Path(args.run)
        req = read_json(run_dir / "AUDIT_REQUEST.json")
        policy = req.get("policy") or {}
        orch = AuditOrchestrator(run_dir.parent)
        try:
            status = orch.freeze_run(run_dir, policy)
        except FreezeAlreadyExists as e:
            print(
                json.dumps(
                    {
                        "error": "FREEZE_ALREADY_EXISTS",
                        "code": "FREEZE_ALREADY_EXISTS",
                        "detail": str(e),
                        "run": str(run_dir),
                    },
                    indent=2,
                )
            )
            return 3
        print(json.dumps(status, indent=2))
        return 0

    if args.cmd == "verify":
        orch = AuditOrchestrator(Path(args.run).parent)
        result = orch.verify_run(Path(args.run))
        print(json.dumps(result, indent=2))
        if result.get("verify_ok"):
            return 0
        return 2

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
