from __future__ import annotations

import os
import secrets
import shutil
from pathlib import Path
from typing import Any, Mapping

from .boundary import BoundaryManager
from .epistemic.expectation import (
    FREEZE_STATE_FROZEN,
    FREEZE_STATE_IN_PROGRESS,
    R4B_CONTRACT_MARKER,
    R4BExpectationError,
    expectation_digest,
    frozen_package_dir,
    strict_parse_r4b_expectation,
    validate_freeze_transaction,
)
from .request import read_json, sha256_file, utc_now, write_json


class FreezeAlreadyExists(RuntimeError):
    """Fail-closed: freeze is a one-shot finalization; refuse overwrite/regeneration."""

    code = "FREEZE_ALREADY_EXISTS"


class FreezeIntegrityError(RuntimeError):
    """Fail-closed: completed freeze state is inconsistent (e.g. package missing)."""

    code = "FREEZE_INTEGRITY_FAILURE"


class FreezeIncompleteError(RuntimeError):
    """Fail-closed: freeze transaction interrupted or partially published."""

    code = "FREEZE_INCOMPLETE"


def _write_failure(audit_root: Path, failure: dict[str, Any]) -> None:
    write_json(audit_root / "FAILURE.json", failure)


def _owned_temp_prefix(audit_id: str) -> str:
    return f".wf_freeze_tmp_{audit_id}_"


def _cleanup_owned_temps(audit_root: Path, audit_id: str) -> list[str]:
    """Remove only uniquely owned temporary freeze directories before publication."""
    freeze_root = audit_root / "freeze"
    removed: list[str] = []
    if not freeze_root.is_dir():
        return removed
    prefix = _owned_temp_prefix(audit_id)
    for p in list(freeze_root.iterdir()):
        if p.is_dir() and p.name.startswith(prefix):
            shutil.rmtree(p, ignore_errors=True)
            removed.append(p.name)
    return removed


def assert_one_shot_freeze_allowed(audit_root: Path) -> None:
    """
    Enforce freeze one-shot from completed FREEZE_STATUS independently of
    whether the frozen package directory still exists on disk.

    Must run before any SHA rebind or package mutation.
    """
    audit_root = audit_root.resolve()
    audit_id = audit_root.name
    expected_dir = frozen_package_dir(audit_root)
    status_path = audit_root / "FREEZE_STATUS.json"
    intent_path = audit_root / "FREEZE_INTENT.json"

    prior: dict[str, Any] | None = None
    if status_path.is_file():
        prior = read_json(status_path)

    completed = bool(
        prior
        and prior.get("freeze_performed") is True
        and prior.get("state") == FREEZE_STATE_FROZEN
    )
    recorded_dir: Path | None = None
    if prior and prior.get("freeze_directory"):
        recorded_dir = Path(str(prior["freeze_directory"]))

    package_present = expected_dir.is_dir() or (
        recorded_dir is not None and recorded_dir.is_dir()
    )

    if completed:
        if not package_present:
            failure = {
                "audit_id": audit_id,
                "error": "FREEZE_INTEGRITY_FAILURE",
                "code": "FREEZE_PACKAGE_MISSING",
                "detail": (
                    "FREEZE_STATUS.json records a completed freeze but the frozen "
                    "package directory is missing; refuse regenerate/replacement"
                ),
                "freeze_status": prior,
                "expected_freeze_directory": str(expected_dir),
                "recorded_freeze_directory": str(recorded_dir) if recorded_dir else None,
                "preserved": True,
                "refuse_regenerate": True,
            }
            _write_failure(audit_root, failure)
            raise FreezeIntegrityError(
                "FREEZE_INTEGRITY_FAILURE: FREEZE_PACKAGE_MISSING — prior successful "
                f"freeze recorded for {audit_id}; refuse regenerate because frozen "
                "package directory is absent"
            )
        raise FreezeAlreadyExists(
            f"FREEZE_ALREADY_EXISTS: FREEZE_STATUS.json already records a completed "
            f"freeze for {audit_id}; refuse regenerate/overwrite"
        )

    if package_present:
        raise FreezeAlreadyExists(
            f"FREEZE_ALREADY_EXISTS: refuse regenerate/overwrite of existing freeze at "
            f"{expected_dir if expected_dir.is_dir() else recorded_dir}"
        )

    if status_path.is_file():
        failure = {
            "audit_id": audit_id,
            "error": "FREEZE_INTEGRITY_FAILURE",
            "code": "FREEZE_STATUS_INCONSISTENT",
            "detail": (
                "FREEZE_STATUS.json exists without state=FROZEN/"
                "freeze_performed=true; refuse freeze to avoid ambiguous one-shot state"
            ),
            "freeze_status": prior,
            "preserved": True,
            "refuse_regenerate": True,
        }
        _write_failure(audit_root, failure)
        raise FreezeIntegrityError(
            "FREEZE_INTEGRITY_FAILURE: FREEZE_STATUS_INCONSISTENT — refuse freeze"
        )

    if intent_path.is_file():
        # Incomplete prior attempt — preserve intent, clean owned temps, fail closed.
        _cleanup_owned_temps(audit_root, audit_id)
        intent = read_json(intent_path)
        failure = {
            "audit_id": audit_id,
            "error": "FREEZE_INCOMPLETE",
            "code": "FREEZE_INTENT_PRESENT_WITHOUT_STATUS",
            "detail": (
                "FREEZE_INTENT.json exists without a completed FREEZE_STATUS; "
                "refuse automatic regenerate. Recovery must validate the complete "
                "package before creating status."
            ),
            "freeze_intent": intent,
            "preserved": True,
            "refuse_regenerate": True,
        }
        _write_failure(audit_root, failure)
        raise FreezeIncompleteError(
            "FREEZE_INCOMPLETE: FREEZE_INTENT present without completed status — "
            "refuse freeze"
        )


def write_freeze_intent(
    audit_root: Path,
    *,
    contract_marker: str,
    execution_manifest_digest: str,
    r4_b_expectation_digest: str,
) -> dict[str, Any]:
    """Write durable FREEZE_INTENT.json (freeze completion must NOT be claimed)."""
    audit_root = audit_root.resolve()
    intent = {
        "audit_id": audit_root.name,
        "state": FREEZE_STATE_IN_PROGRESS,
        "contract_marker": contract_marker,
        "execution_manifest_digest": execution_manifest_digest,
        "r4_b_expectation_digest": r4_b_expectation_digest,
        "intent_utc": utc_now(),
        # Completion fields forbidden on intent.
    }
    if intent.get("freeze_performed") is True:
        raise FreezeIntegrityError("FREEZE_INTENT must not claim freeze_performed")
    if intent.get("stages_completed_through") == "FREEZE":
        raise FreezeIntegrityError(
            "FREEZE_INTENT must not claim stages_completed_through=FREEZE"
        )
    write_json(audit_root / "FREEZE_INTENT.json", intent)
    return intent


def _validate_temp_package(
    audit_root: Path,
    temp_dir: Path,
    *,
    r4_b: Mapping[str, Any],
    execution_manifest_digest: str,
) -> dict[str, Any]:
    """Validate every package digest and R4-B expectation binding before publish."""
    required = (
        "FINAL_DECISION.json",
        "FINAL_EVIDENCE_INDEX.json",
        "MANIFEST.json",
        "SHA256SUMS.txt",
        "REPRODUCTION_INSTRUCTIONS.md",
    )
    missing = [n for n in required if not (temp_dir / n).is_file()]
    if missing:
        raise FreezeIntegrityError(
            f"temporary freeze package incomplete: missing {missing}"
        )

    expectation = strict_parse_r4b_expectation(r4_b)
    exp_digest = expectation_digest(expectation)
    frozen_manifest = read_json(temp_dir / "MANIFEST.json")
    if not isinstance(frozen_manifest, Mapping):
        raise FreezeIntegrityError("temporary MANIFEST.json must be a mapping")
    if frozen_manifest.get("contract_marker") != R4B_CONTRACT_MARKER:
        raise FreezeIntegrityError(
            "temporary MANIFEST.contract_marker must be R4-B marker"
        )
    committed = frozen_manifest.get("r4_b_expectation_digest")
    if committed != exp_digest:
        raise FreezeIntegrityError(
            "temporary MANIFEST.r4_b_expectation_digest mismatch"
        )
    if frozen_manifest.get("execution_manifest_digest") != execution_manifest_digest:
        raise FreezeIntegrityError(
            "temporary MANIFEST.execution_manifest_digest mismatch"
        )

    # Verify SHA256SUMS over package files.
    sums_path = temp_dir / "SHA256SUMS.txt"
    fail = 0
    for line in sums_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        parts = line.split(None, 1)
        if len(parts) != 2:
            fail += 1
            continue
        digest, name = parts
        p = temp_dir / name.strip()
        if not p.is_file() or sha256_file(p) != digest.lower():
            fail += 1
    if fail:
        raise FreezeIntegrityError(
            f"temporary freeze SHA256SUMS verification failed ({fail} entries)"
        )

    # Evidence index must include finalized EXECUTION_MANIFEST at recorded digest.
    index = read_json(temp_dir / "FINAL_EVIDENCE_INDEX.json")
    entries = {
        e["path"]: e["sha256"]
        for e in (index.get("entries") or [])
        if isinstance(e, Mapping) and "path" in e and "sha256" in e
    }
    if entries.get("EXECUTION_MANIFEST.json") != execution_manifest_digest:
        raise FreezeIntegrityError(
            "FINAL_EVIDENCE_INDEX EXECUTION_MANIFEST digest mismatch"
        )
    root_manifest = read_json(audit_root / "EXECUTION_MANIFEST.json")
    if not isinstance(root_manifest, Mapping) or "r4_b" not in root_manifest:
        raise FreezeIntegrityError(
            "root EXECUTION_MANIFEST.r4_b missing at package validation"
        )
    if expectation_digest(root_manifest["r4_b"]) != exp_digest:
        raise FreezeIntegrityError(
            "root r4_b changed after intent; refuse package publication"
        )

    return {
        "frozen_manifest": dict(frozen_manifest),
        "r4_b_expectation_digest": exp_digest,
        "frozen_manifest_digest": sha256_file(temp_dir / "MANIFEST.json"),
        "sha256sums_digest": sha256_file(sums_path),
    }


def create_freeze_package(
    boundary: BoundaryManager,
    audit_root: Path,
    audit_id: str,
    decision: dict[str, Any],
    review_gate: dict[str, Any],
    *,
    r4_b: Mapping[str, Any],
    execution_manifest_digest: str,
) -> dict[str, Any]:
    """
    Seal FINAL AUDIT PACKAGE under freeze/ via:

      temp build → validate → atomic rename → FREEZE_STATUS last

    Never publishes directly into the final directory. Never claims freeze
    completion before FREEZE_STATUS.json is written.

    Caller must already have passed assert_one_shot_freeze_allowed and written
    FREEZE_INTENT.json (intent may therefore be present here).
    """
    audit_root = audit_root.resolve()
    status_path = audit_root / "FREEZE_STATUS.json"
    if status_path.is_file():
        raise FreezeAlreadyExists(
            f"FREEZE_ALREADY_EXISTS: FREEZE_STATUS.json already present for {audit_id}"
        )

    freeze_root = audit_root / "freeze"
    boundary.assert_writable(freeze_root / ".keep")
    freeze_root.mkdir(parents=True, exist_ok=True)

    final_dir = frozen_package_dir(audit_root)
    if final_dir.exists():
        raise FreezeAlreadyExists(
            f"FREEZE_ALREADY_EXISTS: final package path already present at {final_dir}"
        )

    _cleanup_owned_temps(audit_root, audit_id)
    nonce = secrets.token_hex(8)
    temp_dir = freeze_root / f"{_owned_temp_prefix(audit_id)}{nonce}"
    boundary.assert_writable(temp_dir / ".keep")
    temp_dir.mkdir(parents=True, exist_ok=False)

    expectation = strict_parse_r4b_expectation(r4_b)
    exp_digest = expectation_digest(expectation)

    try:
        # Final evidence index over audit_root files (exclude freeze package trees).
        index_rows = []
        for p in sorted(audit_root.rglob("*")):
            if not p.is_file():
                continue
            if "freeze" in p.parts:
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

        decision_path = temp_dir / "FINAL_DECISION.json"
        write_json(
            decision_path,
            {
                "audit_id": audit_id,
                "frozen_at_utc": utc_now(),
                "decision": decision,
                "human_review_gate": review_gate,
            },
        )

        index_path = temp_dir / "FINAL_EVIDENCE_INDEX.json"
        write_json(
            index_path,
            {
                "audit_id": audit_id,
                "audit_root": str(audit_root.resolve()),
                "freeze_directory": str(final_dir.resolve()),
                "entries": index_rows,
            },
        )

        repro_path = temp_dir / "REPRODUCTION_INSTRUCTIONS.md"
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
            "freeze_directory": str(final_dir.resolve()),
            "contract_marker": R4B_CONTRACT_MARKER,
            "r4_b_expectation_digest": exp_digest,
            "execution_manifest_digest": execution_manifest_digest,
            "decision": decision.get("decision"),
            "claim_result": decision.get("claim_result"),
            "promoted_to_full": decision.get("promoted_to_full", False),
            "human_review": review_gate,
            "final_decision_sha256": sha256_file(decision_path),
            "final_evidence_index_sha256": sha256_file(index_path),
            "reproduction_instructions": "REPRODUCTION_INSTRUCTIONS.md",
            "referenced_audit_files": index_rows,
        }
        manifest_path = temp_dir / "MANIFEST.json"
        write_json(manifest_path, manifest)

        # Freeze-directory SHA256SUMS (excluding the sums file itself).
        freeze_sums_lines = []
        for p in sorted(temp_dir.iterdir()):
            if p.is_file() and p.name != "SHA256SUMS.txt":
                freeze_sums_lines.append(f"{sha256_file(p)}  {p.name}")
        sums_path = temp_dir / "SHA256SUMS.txt"
        boundary.open_write(sums_path, "\n".join(freeze_sums_lines) + "\n")

        validated = _validate_temp_package(
            audit_root,
            temp_dir,
            r4_b=r4_b,
            execution_manifest_digest=execution_manifest_digest,
        )

        # Atomic publication: rename owned temp → final path (must not exist).
        os.rename(str(temp_dir), str(final_dir))
        temp_dir = final_dir  # published; do not delete on success cleanup

        status = {
            "audit_id": audit_id,
            "state": FREEZE_STATE_FROZEN,
            "freeze_performed": True,
            "stages_completed_through": "FREEZE",
            "contract_marker": R4B_CONTRACT_MARKER,
            "freeze_directory": str(final_dir.resolve()),
            "sha256sums": str((final_dir / "SHA256SUMS.txt").resolve()),
            "sha256sums_digest": validated["sha256sums_digest"],
            "frozen_manifest_digest": validated["frozen_manifest_digest"],
            "r4_b_expectation_digest": validated["r4_b_expectation_digest"],
            "execution_manifest_digest": execution_manifest_digest,
            "frozen_at_utc": utc_now(),
        }
        # FREEZE_STATUS written LAST — only here may completion fields appear.
        write_json(audit_root / "FREEZE_STATUS.json", status)

        # Post-publication consistency check.
        txn = validate_freeze_transaction(audit_root)
        if not txn.get("ok") or txn.get("state") != FREEZE_STATE_FROZEN:
            raise FreezeIntegrityError(
                f"post-publication freeze transaction invalid: {txn.get('error')}"
            )
        return status
    except Exception as e:
        # Preserve FREEZE_INTENT / FAILURE; remove only owned temporary directory.
        if temp_dir.exists() and temp_dir.name.startswith(_owned_temp_prefix(audit_id)):
            shutil.rmtree(temp_dir, ignore_errors=True)
        if not isinstance(
            e, (FreezeAlreadyExists, FreezeIntegrityError, FreezeIncompleteError)
        ):
            _write_failure(
                audit_root,
                {
                    "audit_id": audit_id,
                    "error": "FREEZE_INCOMPLETE",
                    "code": "FREEZE_PACKAGE_BUILD_FAILED",
                    "detail": str(e),
                    "error_type": type(e).__name__,
                    "preserved": True,
                },
            )
        raise


def _role_for(rel: str) -> str:
    if rel in {"CLAIM.json", "SCOPE.json", "BASELINE.json"}:
        return "lifecycle"
    if rel.startswith("evidence/"):
        return "evidence"
    if rel in {"DECISION.json", "EXECUTION_MANIFEST.json"}:
        return "decision"
    if rel == "PROVENANCE.json":
        return "provenance"
    if rel == "RECONSTRUCTABILITY_REPORT.json":
        return "epistemic_derived"
    if rel.startswith("reviews/"):
        return "epistemic_review_disagreement"
    if rel.startswith("pinned_target/"):
        return "pinned_input"
    if rel in {"FREEZE_INTENT.json", "FREEZE_STATUS.json"}:
        return "freeze_transaction"
    return "artifact"
