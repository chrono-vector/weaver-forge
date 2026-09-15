"""CLI for campaign_runner_v0."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .runner import run_campaign
from .safety import SafetyError


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="campaign_runner_v0",
        description="Weaver Forge Operational V1 — external campaign runner",
    )
    sub = p.add_subparsers(dest="command", required=True)

    run_p = sub.add_parser("run", help="One-invocation campaign run")
    run_p.add_argument(
        "--workspace",
        required=True,
        help="Aurora workspace directory (e.g. aurora_audit)",
    )
    run_p.add_argument(
        "--policy",
        default=None,
        help="Path to campaign policy JSON",
    )
    run_p.add_argument(
        "--campaign-id",
        default="aurora_operational_v1",
        help="Campaign identifier (state under workspace/campaigns/<id>)",
    )
    run_p.add_argument(
        "--dry-run",
        action="store_true",
        help="Plan and validate without writing campaign artifacts",
    )
    run_p.add_argument(
        "--synthetic-evidence",
        action="append",
        default=[],
        help="TEST_ONLY synthetic evidence JSON (repeatable); never canonical",
    )
    run_p.add_argument(
        "--force-unlock-stale",
        action="store_true",
        help="Remove stale lock if older than policy lock_stale_seconds",
    )
    run_p.add_argument(
        "--json-out",
        default=None,
        help="Optional path to write invocation summary JSON",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command != "run":
        parser.error(f"unknown command {args.command}")

    workspace = Path(args.workspace)
    policy = Path(args.policy) if args.policy else None
    # Default policy next to package if not provided.
    if policy is None:
        default_policy = Path(__file__).resolve().parent / "policies" / "aurora_default.json"
        if default_policy.is_file():
            policy = default_policy

    try:
        result = run_campaign(
            workspace=workspace,
            campaign_id=args.campaign_id,
            policy_path=policy,
            synthetic_evidence_paths=[Path(p) for p in args.synthetic_evidence],
            dry_run=args.dry_run,
            force_unlock_stale=args.force_unlock_stale,
        )
    except (SafetyError, OSError, ValueError) as exc:
        print(f"FAIL_CLOSED: {exc}", file=sys.stderr)
        return 3

    summary = {
        "ok": result["ok"],
        "campaign_id": result["campaign_id"],
        "invocation_id": result["invocation_id"],
        "dry_run": result["dry_run"],
        "claim_count": result["claim_count"],
        "state_counts": result["state_counts"],
        "blocker_count": result["blocker_count"],
        "campaign_dir": result["campaign_dir"],
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    if args.json_out:
        Path(args.json_out).write_text(
            json.dumps(summary, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
