from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .boundary import BoundaryManager
from .request import sha256_file, utc_now, write_json


class FreezeAlreadyExists(RuntimeError):
    """Fail-closed: freeze is a one-shot finalization; refuse overwrite/regeneration."""

    code = "FREEZE_ALREADY_EXISTS"


def create_freeze_package(
    boundary: BoundaryManager,
    audit_root: Path,
    audit_id: str,
    decision: dict[str, Any],
    review_gate: dict[str, Any],
) -> dict[str, Any]:
    """Seal FINAL AUDIT PACKAGE under freeze/ without mutating prior foreign freezes."""
    freeze_dir = audit_root / "freeze" / f"{audit_id}_FROZEN"
    if freeze_dir.exists():
        raise FreezeAlreadyExists(
            f"FREEZE_ALREADY_EXISTS: refuse regenerate/overwrite of existing freeze at {freeze_dir}"
        )
    boundary.assert_writable(freeze_dir / ".keep")
    freeze_dir.mkdir(parents=True, exist_ok=False)

    # Final evidence index over audit_root files (excluding freeze dir contents being written)
    index_rows = []
    for p in sorted(audit_root.rglob("*")):
        if not p.is_file():
            continue
        if "freeze" in p.parts and freeze_dir.name in p.parts:
            continue
        if p.suffix == ".pyc" or "__pycache__" in p.parts:
            continue
        rel = p.relative_to(audit_root).as_posix()
        index_rows.append(
            {
                "path": rel,
                "sha256": sha256_file(p),
                "role": _role_for(rel),
            }
        )

    decision_path = freeze_dir / "FINAL_DECISION.json"
    write_json(
        decision_path,
        {
            "audit_id": audit_id,
            "frozen_at_utc": utc_now(),
            "decision": decision,
            "human_review_gate": review_gate,
        },
    )

    index_path = freeze_dir / "FINAL_EVIDENCE_INDEX.json"
    write_json(
        index_path,
        {
            "audit_id": audit_id,
            "audit_root": str(audit_root.resolve()),
            "freeze_directory": str(freeze_dir.resolve()),
            "entries": index_rows,
        },
    )

    repro_path = freeze_dir / "REPRODUCTION_INSTRUCTIONS.md"
    repro = f"""# Reproduction instructions — {audit_id}

## Operator inputs (only)
Provide an audit request JSON with:
- `target_path`
- `claim` (id, statement, adapter, adapter_params)
- `policy` (optional)
- `protected_paths` / `prior_freeze_sums` (optional)

Do **not** manually construct manifests, hash inventories, decision documents, or freeze structure unless policy assigns a Human Review action.

## Command
```
python -m audit_lifecycle.cli run --request <request.json> --out <runs_parent_dir>
```
If `policy.human_review_required` is true, after decision and before freeze the workflow requires:
```
# write HUMAN_REVIEW.json into the run directory, then:
python -m audit_lifecycle.cli freeze --run <run_dir>
```

## Verify sealed package
```
python -m audit_lifecycle.cli verify --run <run_dir>
```
"""
    boundary.open_write(repro_path, repro)

    manifest = {
        "audit_id": audit_id,
        "freeze_label": f"{audit_id}_FROZEN",
        "freeze_directory": str(freeze_dir.resolve()),
        "decision": decision.get("decision"),
        "claim_result": decision.get("claim_result"),
        "promoted_to_full": decision.get("promoted_to_full", False),
        "human_review": review_gate,
        "final_decision_sha256": sha256_file(decision_path),
        "final_evidence_index_sha256": sha256_file(index_path),
        "reproduction_instructions": "REPRODUCTION_INSTRUCTIONS.md",
        "referenced_audit_files": index_rows,
    }
    manifest_path = freeze_dir / "MANIFEST.json"
    write_json(manifest_path, manifest)

    # Freeze-directory SHA256SUMS
    freeze_sums_lines = []
    for p in sorted(freeze_dir.iterdir()):
        if p.is_file() and p.name != "SHA256SUMS.txt":
            freeze_sums_lines.append(f"{sha256_file(p)}  {p.name}")
    sums_path = freeze_dir / "SHA256SUMS.txt"
    boundary.open_write(sums_path, "\n".join(freeze_sums_lines) + "\n")

    # Re-bind freeze sums into manifest note
    status = {
        "audit_id": audit_id,
        "freeze_performed": True,
        "freeze_directory": str(freeze_dir.resolve()),
        "sha256sums": str(sums_path.resolve()),
        "sha256sums_digest": sha256_file(sums_path),
        "frozen_at_utc": utc_now(),
    }
    write_json(audit_root / "FREEZE_STATUS.json", status)
    return status


def _role_for(rel: str) -> str:
    if rel in {"CLAIM.json", "SCOPE.json", "BASELINE.json"}:
        return "lifecycle"
    if rel.startswith("evidence/"):
        return "evidence"
    if rel in {"DECISION.json", "EXECUTION_MANIFEST.json"}:
        return "decision"
    if rel == "PROVENANCE.json":
        return "provenance"
    if rel.startswith("pinned_target/"):
        return "pinned_input"
    return "artifact"
