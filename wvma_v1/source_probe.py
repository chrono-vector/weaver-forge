"""Trusted B2 probe. Executed from the active tree, never imported from an export.

Product modules are imported after PYTHONPATH has been set to the disposable
Git export by the parent. This file must not import wvma_v1.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _inside(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def _wvma_loaded_from_export(export_root: Path) -> bool:
    for name, module in sys.modules.items():
        if name != "wvma_v1" and not name.startswith("wvma_v1."):
            continue
        file_name = getattr(module, "__file__", None)
        if file_name and _inside(Path(file_name), export_root):
            return True
    return False


def _module_record(module: Any, export_root: Path) -> dict[str, Any]:
    file_name = Path(module.__file__).resolve()
    return {
        "module_file": str(file_name),
        "module_inside_export": _inside(file_name, export_root),
        "module_sha256": _sha256_file(file_name),
    }


def _observe_c06_s1(export_root: Path) -> dict[str, Any]:
    from audit_lifecycle.epistemic.expectation import (
        REPORT_FILENAME,
        R4BExpectationError,
        strict_parse_r4b_expectation,
    )
    import audit_lifecycle.epistemic.expectation as expectation

    sha = "cd" * 32
    payload = {
        "schema_version": "r4.epistemic.expectation.v1",
        "enabled": True,
        "contract_marker": "weaver_forge_audit_lifecycle_r4b_v1",
        "reconstructability_report": {
            "required": True,
            "path": REPORT_FILENAME,
            "digest": "ab" * 32,
        },
        "expected_disagreement_record_digests": sha,
        "expected_disagreement_chain_heads": [],
        "finalized_for_freeze": True,
    }
    try:
        parsed = strict_parse_r4b_expectation(payload)
        observation: dict[str, Any] = {
            "entry_point": "strict_parse_r4b_expectation",
            "accepted": True,
            "digests": list(parsed.expected_disagreement_record_digests),
            "error_type": None,
        }
    except R4BExpectationError:
        observation = {
            "entry_point": "strict_parse_r4b_expectation",
            "accepted": False,
            "digests": None,
            "error_type": "R4BExpectationError",
        }
    return {**_module_record(expectation, export_root), "observation": observation}


def _observe_c06_s2(export_root: Path) -> dict[str, Any]:
    from audit_lifecycle.epistemic.provenance import ProvenanceRecord
    import audit_lifecycle.epistemic.provenance as provenance

    base = {
        "schema_version": "r4.epistemic.provenance.v1",
        "artifact_id": "a1",
        "digest": "d1",
        "source_id": "s1",
        "lineage_id": "L1",
        "authority": False,
    }
    present: dict[str, Any] = {}
    for name, value in (("none", None), ("false", False), ("zero", 0)):
        candidate = dict(base)
        candidate["parent_sources"] = value
        try:
            record = ProvenanceRecord.from_dict(candidate)
            present[name] = {
                "accepted": True,
                "parent_sources": list(record.parent_sources),
                "error_type": None,
            }
        except ValueError as exc:
            present[name] = {
                "accepted": False,
                "parent_sources": None,
                "error_type": type(exc).__name__,
            }
    return {
        **_module_record(provenance, export_root),
        "observation": {
            "entry_point": "ProvenanceRecord.from_dict",
            "present_invalid": present,
        },
    }


def _observe_verify_run(export_root: Path, audit_root: Path) -> dict[str, Any]:
    from audit_lifecycle.orchestrator import AuditOrchestrator
    import audit_lifecycle.orchestrator as orchestrator

    result = AuditOrchestrator(audit_root.parent).verify_run(audit_root)
    transaction = result.get("freeze_transaction") or {}
    observation = {
        "entry_point": "AuditOrchestrator.verify_run",
        "verify_ok": bool(result.get("verify_ok")),
        "semantic_ok": bool(result.get("semantic_ok")),
        "sha256sums_ok": bool(result.get("sha256sums_ok")),
        "freeze_sums_ok": result.get("freeze_sums_ok"),
        "txn_verify_ok": bool(transaction.get("verify_ok")),
        "txn_state": transaction.get("state"),
        "txn_error": transaction.get("error"),
    }
    return {**_module_record(orchestrator, export_root), "observation": observation}


def _observe_unrelated(export_root: Path) -> dict[str, Any]:
    import audit_lifecycle.epistemic.expectation as expectation

    return {
        **_module_record(expectation, export_root),
        "observation": None,
        "unrelated_failure": True,
        "error": "unrelated_runtime_failure",
        "self_claimed_result": "DETECTED",
    }


def run(argv: list[str] | None = None) -> dict[str, Any]:
    parser = argparse.ArgumentParser(prog="wvma_v1.source_probe")
    parser.add_argument("--export", required=True, type=Path)
    parser.add_argument("--case", required=True)
    parser.add_argument("--audit-root", type=Path)
    args = parser.parse_args(argv)
    export_root = args.export.resolve()
    if args.case == "C06-S1":
        body = _observe_c06_s1(export_root)
    elif args.case == "C06-S2":
        body = _observe_c06_s2(export_root)
    elif args.case == "VERIFY_RUN":
        if args.audit_root is None:
            raise RuntimeError("VERIFY_RUN requires --audit-root")
        body = _observe_verify_run(export_root, args.audit_root)
    elif args.case == "UNRELATED":
        body = _observe_unrelated(export_root)
    else:
        raise RuntimeError(f"unsupported probe case: {args.case}")
    probe_file = Path(__file__).resolve()
    body.update(
        {
            "case_id": args.case,
            "probe_file": str(probe_file),
            "probe_inside_export": _inside(probe_file, export_root),
            "wvma_loaded_from_export": _wvma_loaded_from_export(export_root),
            "error": body.get("error"),
        }
    )
    return body


def main(argv: list[str] | None = None) -> int:
    try:
        payload = run(argv)
        code = 0
    except Exception as exc:
        payload = {
            "ok": False,
            "error": f"{type(exc).__name__}: {exc}",
            "unrelated_failure": False,
            "observation": None,
            "probe_file": str(Path(__file__).resolve()),
            "wvma_loaded_from_export": False,
        }
        code = 1
    sys.stdout.write(json.dumps(payload, sort_keys=True))
    sys.stdout.write("\n")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
