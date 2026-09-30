"""Minimal WVMA-V1 CLI for Batch A1 seal/verify/state operations."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from wvma_v1.state import (
    derive_attempt_state,
    seal_catalog,
    verify_attempt,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="wvma_v1",
        description="WVMA-V1 non-authoritative mutation assurance (Batch A1)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    seal_p = sub.add_parser("seal", help="Seal a catalog into <out>/catalogs/")
    seal_p.add_argument("--out", required=True, type=Path)
    seal_p.add_argument("--catalog", required=True, type=Path)

    state_p = sub.add_parser("state", help="Derive attempt/out-root state")
    state_p.add_argument("--out", required=True, type=Path)
    state_p.add_argument("--attempt-id", default=None)

    verify_p = sub.add_parser("verify", help="Verify a completed attempt")
    verify_p.add_argument("--out", required=True, type=Path)
    verify_p.add_argument("--attempt-id", required=True)

    args = parser.parse_args(argv)

    if args.command == "seal":
        catalog = seal_catalog(args.out, args.catalog)
        print(json.dumps({"catalog_digest": catalog.catalog_digest}, sort_keys=True))
        return 0
    if args.command == "state":
        state = derive_attempt_state(args.out, args.attempt_id)
        print(json.dumps({"state": state.value}, sort_keys=True))
        return 0
    if args.command == "verify":
        state = verify_attempt(args.out, args.attempt_id)
        print(json.dumps({"state": state.value}, sort_keys=True))
        return 0
    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
