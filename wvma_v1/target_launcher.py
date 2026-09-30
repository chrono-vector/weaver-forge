"""Code-owned target invocation launcher for WVMA-V1 Batch A2.

This module is trusted WVMA code. It must be loaded from the active package
installation (never from a disposable mutated export). Invocation identifiers
are closed; arbitrary command strings are rejected.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Callable, Mapping

# Closed invocation identifiers owned by this module (A2 synthetic + reserved).
ALLOWED_INVOCATION_IDS = frozenset(
    {
        "synthetic.verify",
        "synthetic.canary_pass",
        "synthetic.canary_fail",
    }
)


class LauncherError(ValueError):
    """Bounded launcher rejection."""


def module_origin() -> str:
    """Absolute path of this trusted launcher module."""
    return str(Path(__file__).resolve())


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            chunk = fh.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _read_json(path: Path) -> Any:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _emit(payload: Mapping[str, Any], *, exit_code: int) -> int:
    sys.stdout.write(json.dumps(dict(payload), sort_keys=True, separators=(",", ":")))
    sys.stdout.write("\n")
    sys.stdout.flush()
    return exit_code


def _synthetic_verify(workspace: Path) -> int:
    """Synthetic verifier: reject unless artifact status is exactly 'accepted'."""
    artifact = workspace / "synthetic" / "artifact.json"
    if not artifact.is_file():
        return _emit(
            {
                "invocation_id": "synthetic.verify",
                "verify_ok": False,
                "reason": "artifact_missing",
                "launcher_origin": module_origin(),
            },
            exit_code=2,
        )
    try:
        data = _read_json(artifact)
    except (OSError, json.JSONDecodeError) as exc:
        return _emit(
            {
                "invocation_id": "synthetic.verify",
                "verify_ok": False,
                "reason": f"artifact_unreadable:{exc}",
                "launcher_origin": module_origin(),
            },
            exit_code=2,
        )
    status = data.get("status") if isinstance(data, dict) else None
    ok = status == "accepted"
    return _emit(
        {
            "invocation_id": "synthetic.verify",
            "verify_ok": ok,
            "status": status,
            "artifact_sha256": _sha256_file(artifact),
            "launcher_origin": module_origin(),
            # Self-asserted kill label — oracle must NOT trust this alone.
            "self_claimed_result": "DETECTED" if not ok else "SURVIVED",
        },
        exit_code=0 if ok else 1,
    )


def _synthetic_canary_pass(workspace: Path) -> int:
    del workspace
    return _emit(
        {
            "invocation_id": "synthetic.canary_pass",
            "verify_ok": True,
            "self_claimed_result": "DETECTED",
            "launcher_origin": module_origin(),
        },
        exit_code=0,
    )


def _synthetic_canary_fail(workspace: Path) -> int:
    del workspace
    return _emit(
        {
            "invocation_id": "synthetic.canary_fail",
            "verify_ok": False,
            "self_claimed_result": "DETECTED",
            "launcher_origin": module_origin(),
        },
        exit_code=1,
    )


_HANDLERS: dict[str, Callable[[Path], int]] = {
    "synthetic.verify": _synthetic_verify,
    "synthetic.canary_pass": _synthetic_canary_pass,
    "synthetic.canary_fail": _synthetic_canary_fail,
}


def resolve_handler(invocation_id: str) -> Callable[[Path], int]:
    if not isinstance(invocation_id, str) or not invocation_id:
        raise LauncherError("invocation_id must be non-empty str")
    if invocation_id not in ALLOWED_INVOCATION_IDS:
        raise LauncherError(f"unsupported invocation_id: {invocation_id}")
    return _HANDLERS[invocation_id]


def run_invocation(invocation_id: str, workspace: Path | str) -> int:
    handler = resolve_handler(invocation_id)
    root = Path(workspace)
    if not root.is_dir():
        raise LauncherError(f"workspace is not a directory: {root}")
    return handler(root.resolve())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="wvma_v1.target_launcher")
    parser.add_argument("--invocation-id", required=True)
    parser.add_argument("--workspace", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        return run_invocation(args.invocation_id, args.workspace)
    except LauncherError as exc:
        sys.stderr.write(f"launcher_error:{exc}\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
