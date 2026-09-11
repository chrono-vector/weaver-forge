"""CAW reconsumption for static-completion axis split (SCI).

Re-runs runtime-path-synthesizer-v0 against frozen CAW evidence with S7
path-specific SoT ingested. No network, RPC, runtime execution, or CAW mutation.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

RUN_ID = "SCI-20260912-013404-466F4ABE"
ROOT = Path(r"C:\dev\Weaver\weaver-forge\external_verifications")
RAW = Path(r"C:\dev\external-verification-work\caw-actual-system-audit-v0.1\raw")
S7 = Path(r"C:\dev\external-verification-work\caw-c3-s7-path-binding-e2074718\S7-20260911-151542-52348FBA")
CC = Path(r"C:\dev\external-verification-work\caw-caller-chain-precision-e2074718\CC-20260911-160624-5D7BCBD0")
SP = Path(r"C:\dev\external-verification-work\caw-signer-provenance-e2074718\SP-20260911-155353-F30CE75D")
OUT = Path(r"C:\dev\external-verification-work\weaver-static-completion-implementation") / RUN_ID
COMMIT = "e2074718bcea293726ddfcf8764e1499e7b9217c"
FREEZE = Path(r"C:\dev\external-verification-work\caw-freeze-e2074718")

FP = {
    "wrps-v0-p0004",
    "wrps-v0-p0026",
    "wrps-v0-p0028",
    "wrps-v0-p0041",
    "wrps-v0-p0043",
}
EXPECTED_COMPLETE = {
    "wrps-v0-p0039",
    "wrps-v0-p0040",
    "wrps-v0-p0042",
    "wrps-v0-p0044",
    "wrps-v0-p0045",
    "wrps-v0-p0046",
    "wrps-v0-p0047",
    "wrps-v0-p0048",
    "wrps-v0-p0049",
    "wrps-v0-p0050",
}
UNLABELED = {
    "wrps-v0-p0013",
    "wrps-v0-p0014",
    "wrps-v0-p0015",
    "wrps-v0-p0016",
    "wrps-v0-p0019",
    "wrps-v0-p0020",
}

sys.path.insert(0, str(ROOT / "runtime-path-synthesizer-v0"))
from path_specific_sot_v0 import ingest_cc_sp_clearance, ingest_s7_path_bindings  # noqa: E402
from runtime_path_synthesizer_v0 import (  # noqa: E402
    SCHEMA_VERSION,
    synthesize_runtime_paths_v0,
    validate_runtime_path_synthesizer_result_v0,
)


def load(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def dump(p: Path, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def primary_static_blocker(gaps: list[dict], path: dict) -> str:
    types = {g["gap_type"] for g in gaps}
    order = [
        "STATIC_TARGET_UNRESOLVED",
        "PROVENANCE_CONFLICT",
        "ADDRESS_SOURCE_PARTIAL",
        "GENERATED_CONFIG_DEPENDENCY",
        "GENERATED_CONFIG_PARTIAL",
        "NOT_FOUND_DEPENDENCY",
        "SIGNER_SOURCE_PARTIAL",
        "CALLER_CHAIN_HEURISTIC",
        "CALLER_CHAIN_UNRESOLVED",
    ]
    for t in order:
        if t in types:
            return t
    if path.get("STATIC_PATH_STATUS") == "COMPLETE":
        return "NONE"
    aa = path.get("address_axes") or {}
    if aa.get("PATH_USABLE_ADDRESS_STATUS") != "ESTABLISHED":
        return "ADDRESS_SOURCE_PATH_USABLE_MISSING"
    return "OTHER_STATIC_PARTIAL"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    graph = load(RAW / "caw-c1-manual-vs-weaver-comparison-v7" / "caw_static_evidence_integration_result_v7.json")
    path_input_path = RAW / "weaver-runtime-path-synthesizer-v0" / "caw_c1_runtime_path_input.json"
    if path_input_path.exists():
        path_input = load(path_input_path)
    else:
        sv = load(RAW / "weaver-external-repo-source-verifier-v0" / "caw_c1_acceptance_result.json")
        ri = load(RAW / "weaver-runtime-surface-inventory-v0" / "caw_c1_runtime_inventory_result.json")
        mc = load(RAW / "weaver-mutating-callsite-analyzer-v0" / "caw_c1_mutating_callsite_result.json")
        qs = load(RAW / "weaver-queue-state-transition-analyzer-v0" / "caw_c1_txqueue_result.json")
        path_input = {
            "schema_version": SCHEMA_VERSION,
            "source_verifier_result": sv,
            "runtime_inventory_result": ri,
            "mutating_callsite_result": mc,
            "queue_state_transition_result": qs,
            "repo_path": str(FREEZE),
            "target_commit": COMMIT,
            "notes": "SCI reconsumption",
        }

    bindings = load(S7 / "path-specific-binding.json")
    sot_bundle = ingest_s7_path_bindings(bindings, global_canonical="UNRESOLVED")
    dump(OUT / "path-sot-contract.json", sot_bundle)

    cc = load(CC / "full-50-path-reassessment.json")
    sp_path = SP / "signer-blocker-recalculation.json"
    signer_rec = load(sp_path) if sp_path.exists() else None
    clearance = ingest_cc_sp_clearance(cc, signer_rec)
    dump(OUT / "path-static-clearance-overlay.json", clearance)

    path_input["static_evidence_graph"] = graph
    path_input["path_specific_sot_evidence"] = sot_bundle
    path_input["path_static_clearance_overlay"] = clearance
    path_input["target_commit"] = COMMIT
    path_input["schema_version"] = SCHEMA_VERSION
    path_input["notes"] = (
        "SCI static-completion axis split reconsumption; S7 path-SoT + CC/SP clearance ingested; "
        "no runtime execution; execution_authorized=false"
    )

    result = synthesize_runtime_paths_v0(path_input)
    dump(OUT / "caw_runtime_path_result_sci.json", result)
    errs = validate_runtime_path_synthesizer_result_v0(result)

    # Overlay FP classification from caller-chain reassessment when available
    cc_by = {p["PATH_ID"]: p for p in cc.get("paths") or []}

    final_rows = []
    for p in result.get("paths") or []:
        pid = p.get("path_id") or ""
        gaps = [g for g in (result.get("path_gaps") or []) if g.get("path_id") == pid]
        cc_row = cc_by.get(pid) or {}
        fp = pid in FP or cc_row.get("static_path_class") == "FALSE_POSITIVE_REMOVED"
        if fp:
            static_status = "FALSE_POSITIVE_REMOVED"
            active = False
        else:
            static_status = p.get("STATIC_PATH_STATUS") or (
                "COMPLETE" if p.get("path_status") == "COMPLETE" else "PARTIAL"
            )
            active = True
        final_rows.append({
            "PATH_ID": pid,
            "path_name": p.get("path_name"),
            "ACTIVE": active,
            "STATIC_PATH_STATUS": static_status,
            "path_status_legacy": p.get("path_status"),
            "RUNTIME_EXECUTION_STATUS": p.get("RUNTIME_EXECUTION_STATUS"),
            "SIGNER_IDENTITY_STATUS": p.get("SIGNER_IDENTITY_STATUS"),
            "AUTHORITY_STATUS": p.get("AUTHORITY_STATUS"),
            "INDEPENDENT_WITNESS_STATUS": p.get("INDEPENDENT_WITNESS_STATUS"),
            "SOT_STATUS": p.get("SOT_STATUS"),
            "address_axes": p.get("address_axes"),
            "PRIMARY_STATIC_BLOCKER": "FALSE_POSITIVE" if fp else primary_static_blocker(gaps, p),
            "gap_types": sorted({g.get("gap_type") for g in gaps if g.get("gap_type")}),
            "path_sot_cleared_gaps": p.get("path_sot_cleared_gaps") or [],
            "EXPECTED_COMPLETE": pid in EXPECTED_COMPLETE,
            "EXPECTED_UNLABELED_CLUSTER": pid in UNLABELED,
        })

    active = [r for r in final_rows if r["ACTIVE"]]
    complete = [r for r in active if r["STATIC_PATH_STATUS"] == "COMPLETE"]
    partial = [r for r in active if r["STATIC_PATH_STATUS"] == "PARTIAL"]
    unresolved = [r for r in active if r["STATIC_PATH_STATUS"] == "UNRESOLVED"]

    counts = {
        "ACTIVE_PATHS": len(active),
        "STATIC_COMPLETE": len(complete),
        "STATIC_PARTIAL": len(partial),
        "STATIC_UNRESOLVED": len(unresolved),
        "FALSE_POSITIVE_REMOVED": sum(1 for r in final_rows if r["STATIC_PATH_STATUS"] == "FALSE_POSITIVE_REMOVED"),
        "RUNTIME_EXECUTION_VERIFIED": sum(1 for r in active if r["RUNTIME_EXECUTION_STATUS"] == "VERIFIED"),
        "AUTHORITY_VERIFIED": sum(1 for r in active if r["AUTHORITY_STATUS"] == "VERIFIED"),
        "RUNTIME_SIGNER_IDENTITY_VERIFIED": sum(1 for r in active if r["SIGNER_IDENTITY_STATUS"] == "VERIFIED"),
        "INDEPENDENT_WITNESS_VERIFIED": sum(1 for r in active if r["INDEPENDENT_WITNESS_STATUS"] == "SATISFIED"),
        "EXPECTED_COMPLETE_10_ACTUAL": len([r for r in complete if r["PATH_ID"] in EXPECTED_COMPLETE]),
        "EXPECTED_PARTIAL_35_ACTUAL": len(partial),
        "complete_path_ids": sorted(r["PATH_ID"] for r in complete),
        "unexpected_complete": sorted(r["PATH_ID"] for r in complete if r["PATH_ID"] not in EXPECTED_COMPLETE),
        "expected_complete_still_partial": sorted(
            r["PATH_ID"] for r in partial if r["PATH_ID"] in EXPECTED_COMPLETE
        ),
        "validation_errors": errs,
        "synthesizer_summary": result.get("summary"),
    }

    remaining = []
    for r in partial:
        remaining.append({
            "PATH_ID": r["PATH_ID"],
            "PRIMARY_STATIC_BLOCKER": r["PRIMARY_STATIC_BLOCKER"],
            "gap_types": r["gap_types"],
            "SOT_STATUS": r["SOT_STATUS"],
            "EXPECTED_UNLABELED_CLUSTER": r["EXPECTED_UNLABELED_CLUSTER"],
        })

    blocker_counts = Counter(r["PRIMARY_STATIC_BLOCKER"] for r in remaining)

    dump(OUT / "45-path-final-status.json", {
        "run_id": RUN_ID,
        "target_commit": COMMIT,
        "counts": counts,
        "paths": final_rows,
    })
    dump(OUT / "remaining-static-blockers.json", {
        "run_id": RUN_ID,
        "partial_count": len(remaining),
        "blocker_counts": dict(blocker_counts),
        "paths": remaining,
    })
    dump(OUT / "caw-reconsumption-results.json", {
        "run_id": RUN_ID,
        "method": "synthesize_runtime_paths_v0 + S7 path-SoT ingest + FP overlay",
        "network_used": False,
        "rpc_used": False,
        "runtime_execution": False,
        "caw_verdict_changed": False,
        "counts": counts,
        "nonclaims": [
            "STATIC COMPLETE ≠ RUNTIME VERIFIED",
            "STATIC COMPLETE ≠ AUTHORITY VERIFIED",
            "STATIC COMPLETE ≠ RUNTIME SIGNER IDENTITY VERIFIED",
            "STATIC COMPLETE ≠ TRUSTLESS VERIFIED",
            "STATIC COMPLETE ≠ DECENTRALIZED VERIFIED",
            "STATIC COMPLETE ≠ IW COMPLETE",
        ],
    })

    print(json.dumps(counts, indent=2))
    return 0 if not errs else 3


if __name__ == "__main__":
    raise SystemExit(main())
