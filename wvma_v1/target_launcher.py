"""Code-owned target invocation launcher for WVMA-V1 Batch A2/B1.

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

# Closed invocation identifiers owned by this module.
ALLOWED_INVOCATION_IDS = frozenset(
    {
        "synthetic.verify",
        "synthetic.canary_pass",
        "synthetic.canary_fail",
        "audit.verify_semantics",
        "audit.verify_run",
        "audit.verify_r4b",
        "audit.verify_reconstructability",
        "audit.validate_freeze_transaction",
        "audit.freeze_run",
        "campaign.revalidate",
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


def _resolve_audit_root(workspace: Path) -> Path:
    marker = workspace / ".wvma_audit_root"
    if marker.is_file():
        rel = marker.read_text(encoding="utf-8").strip()
        root = (workspace / rel).resolve()
        if root.is_dir():
            return root
    if (workspace / "DECISION.json").is_file() or (workspace / "CLAIM.json").is_file():
        return workspace.resolve()
    runs = workspace / "runs"
    if runs.is_dir():
        candidates = sorted(p for p in runs.iterdir() if p.is_dir())
        if len(candidates) == 1:
            return candidates[0].resolve()
    raise LauncherError(f"cannot resolve audit root under {workspace}")


def _audit_verify_semantics(workspace: Path) -> int:
    from audit_lifecycle.semantic_verification import verify_semantics

    root = _resolve_audit_root(workspace)
    result = verify_semantics(root)
    ok = bool(result.get("ok"))
    return _emit(
        {
            "invocation_id": "audit.verify_semantics",
            "verify_ok": ok,
            "semantic_ok": ok,
            "match": result.get("match"),
            "decision_match": result.get("decision_match"),
            "final_decision_match": result.get("final_decision_match"),
            "launcher_origin": module_origin(),
            "self_claimed_result": "DETECTED" if not ok else "SURVIVED",
        },
        exit_code=0 if ok else 1,
    )


def _audit_verify_run(workspace: Path) -> int:
    from audit_lifecycle.orchestrator import AuditOrchestrator

    root = _resolve_audit_root(workspace)
    orch = AuditOrchestrator(root.parent)
    result = orch.verify_run(root)
    ok = bool(result.get("verify_ok"))
    return _emit(
        {
            "invocation_id": "audit.verify_run",
            "verify_ok": ok,
            "semantic_ok": result.get("semantic_ok"),
            "sha256sums_ok": result.get("sha256sums_ok"),
            "launcher_origin": module_origin(),
            "self_claimed_result": "DETECTED" if not ok else "SURVIVED",
        },
        exit_code=0 if ok else 1,
    )


def _audit_verify_r4b(workspace: Path) -> int:
    from audit_lifecycle.epistemic.r4b_verify import verify_r4b_at_root

    root = _resolve_audit_root(workspace)
    result = verify_r4b_at_root(root)
    ok = bool(result.get("ok"))
    return _emit(
        {
            "invocation_id": "audit.verify_r4b",
            "verify_ok": ok,
            "state": result.get("state"),
            "status": result.get("status"),
            "launcher_origin": module_origin(),
            "self_claimed_result": "DETECTED" if not ok else "SURVIVED",
        },
        exit_code=0 if ok else 1,
    )


def _audit_verify_reconstructability(workspace: Path) -> int:
    from audit_lifecycle.epistemic.reconstructability import (
        verify_reconstructability_at_root,
    )

    root = _resolve_audit_root(workspace)
    result = verify_reconstructability_at_root(root, required=True)
    ok = bool(result.get("ok"))
    return _emit(
        {
            "invocation_id": "audit.verify_reconstructability",
            "verify_ok": ok,
            "status": result.get("status"),
            "launcher_origin": module_origin(),
            "self_claimed_result": "DETECTED" if not ok else "SURVIVED",
        },
        exit_code=0 if ok else 1,
    )


def _audit_validate_freeze_transaction(workspace: Path) -> int:
    from audit_lifecycle.epistemic.expectation import (
        FREEZE_STATE_FROZEN,
        FREEZE_STATE_PRE,
        validate_freeze_transaction,
    )

    root = _resolve_audit_root(workspace)
    result = validate_freeze_transaction(root)
    state = result.get("state")
    # Baseline may be PRE (no freeze markers) or FROZEN. Incomplete never ok.
    ok = bool(result.get("verify_ok")) and state in {
        FREEZE_STATE_FROZEN,
        FREEZE_STATE_PRE,
    }
    return _emit(
        {
            "invocation_id": "audit.validate_freeze_transaction",
            "verify_ok": ok,
            "txn_ok": result.get("ok"),
            "state": state,
            "error": result.get("error"),
            "launcher_origin": module_origin(),
            "self_claimed_result": "DETECTED" if not ok else "SURVIVED",
        },
        exit_code=0 if ok else 1,
    )


def _audit_freeze_run(workspace: Path) -> int:
    from wvma_v1.baselines import attempt_freeze

    root = _resolve_audit_root(workspace)
    policy = {}
    req = root / "AUDIT_REQUEST.json"
    if req.is_file():
        try:
            policy = _read_json(req).get("policy") or {}
        except (OSError, json.JSONDecodeError, AttributeError):
            policy = {}
    outcome = attempt_freeze(root, policy)
    ok = bool(outcome.get("ok"))
    return _emit(
        {
            "invocation_id": "audit.freeze_run",
            "verify_ok": ok,
            "error": outcome.get("error"),
            "launcher_origin": module_origin(),
            "self_claimed_result": "DETECTED" if not ok else "SURVIVED",
        },
        exit_code=0 if ok else 1,
    )


def _resolve_campaign_workspace(workspace: Path) -> tuple[Path, str]:
    marker = workspace / ".wvma_campaign"
    if marker.is_file():
        data = json.loads(marker.read_text(encoding="utf-8"))
        ws = (workspace / data["workspace"]).resolve()
        return ws, str(data["campaign_id"])
    # Heuristic: workspace itself is aurora-like.
    campaigns = workspace / "campaigns"
    if campaigns.is_dir():
        ids = sorted(p.name for p in campaigns.iterdir() if p.is_dir())
        if len(ids) == 1:
            return workspace.resolve(), ids[0]
    aurora = workspace / "aurora_audit"
    if aurora.is_dir():
        campaigns = aurora / "campaigns"
        ids = sorted(p.name for p in campaigns.iterdir() if p.is_dir()) if campaigns.is_dir() else []
        if len(ids) == 1:
            return aurora.resolve(), ids[0]
    raise LauncherError(f"cannot resolve campaign under {workspace}")


def _campaign_revalidate(workspace: Path) -> int:
    from campaign_runner_v0.runner import run_campaign

    camp_ws, campaign_id = _resolve_campaign_workspace(workspace)
    policy = (
        Path(__file__).resolve().parent.parent
        / "campaign_runner_v0"
        / "policies"
        / "aurora_default.json"
    )
    result = run_campaign(
        workspace=camp_ws, campaign_id=campaign_id, policy_path=policy
    )
    claims = (result.get("campaign_state") or {}).get("claims") or {}
    rejected = result.get("revalidation", {}).get("rejected_terminals") or []
    marker = workspace / ".wvma_c10_expect"
    if marker.is_file():
        expect = json.loads(marker.read_text(encoding="utf-8"))
        mode = expect.get("mode")
        cid = expect.get("claim_id")
        if mode == "false_pass":
            retained = bool(cid) and claims.get(cid, {}).get("state") == "PASS"
            ok = retained  # True only if mutant survived
        elif mode == "reuse_fail":
            # Detection: revalidation rejected the tampered evidence binding.
            ok = not any(r.get("claim_id") == cid for r in rejected)
        elif mode == "foreign":
            foreign = expect.get("claim_id", "FOREIGN-CLAIM-NO-BINDING")
            ok = claims.get(foreign, {}).get("state") == "PASS"
        else:
            ok = True
    else:
        # Baseline: campaign completed; treat as accepted.
        ok = True
    return _emit(
        {
            "invocation_id": "campaign.revalidate",
            "verify_ok": ok,
            "rejected_terminals": rejected,
            "pass_count": sum(1 for r in claims.values() if r.get("state") == "PASS"),
            "launcher_origin": module_origin(),
            "self_claimed_result": "DETECTED" if not ok else "SURVIVED",
        },
        exit_code=0 if ok else 1,
    )


_HANDLERS: dict[str, Callable[[Path], int]] = {
    "synthetic.verify": _synthetic_verify,
    "synthetic.canary_pass": _synthetic_canary_pass,
    "synthetic.canary_fail": _synthetic_canary_fail,
    "audit.verify_semantics": _audit_verify_semantics,
    "audit.verify_run": _audit_verify_run,
    "audit.verify_r4b": _audit_verify_r4b,
    "audit.verify_reconstructability": _audit_verify_reconstructability,
    "audit.validate_freeze_transaction": _audit_validate_freeze_transaction,
    "audit.freeze_run": _audit_freeze_run,
    "campaign.revalidate": _campaign_revalidate,
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
    except Exception as exc:  # conservative process failure
        sys.stderr.write(f"launcher_error:{type(exc).__name__}:{exc}\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
