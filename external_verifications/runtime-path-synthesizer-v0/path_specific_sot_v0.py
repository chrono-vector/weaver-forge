"""Path-specific SoT evidence contract for Weaver runtime-path-synthesizer-v0.

Additive overlay contract. Does not force a global canonical family.
Does not discover deployments autonomously — consumes operator/S7 fixtures.
"""
from __future__ import annotations

from typing import Any

PATH_SOT_SCHEMA = "weaver-path-specific-sot-evidence-v0"

PATH_SOT_USABLE = {
    "PATH_SOT_DUAL_VALID",
    "PATH_SPECIFIC_USABLE",
    "PATH_SOT_USABLE",
    "ESTABLISHED",
}

PATH_SOT_CONFLICT_CLEARED = {"CLEARED", "NONE", "NO_CONFLICT", ""}

UNLABELED_TARGETS = {
    "MULTI_LITERAL_UNLABELED_CLUSTER",
    "UNLABELED_CLUSTER",
    "STATIC_TARGET_UNRESOLVED",
}


def empty_path_sot_bundle() -> dict[str, Any]:
    return {
        "schema_version": PATH_SOT_SCHEMA,
        "global_canonical_status": "UNRESOLVED",
        "multi_generation_status": "OVERLAY_ONLY",
        "records": [],
        "limitations": [
            "path-specific SoT overlay; does not select a global canonical family",
            "does not prove runtime execution, authority, or independent witness",
        ],
    }


def normalize_path_sot_record(raw: dict[str, Any]) -> dict[str, Any]:
    """Normalize one path-SoT record into the machine-readable contract."""
    pid = raw.get("PATH_ID") or raw.get("path_id") or ""
    classification = (
        raw.get("path_specific_sot_classification")
        or raw.get("PATH_SPECIFIC_SOT_STATUS")
        or raw.get("sot_classification")
        or "NOT_ESTABLISHED"
    )
    conflict = raw.get("conflict_status") or raw.get("CONFLICT_STATUS") or "UNRESOLVED"
    static_target = raw.get("target_contract_role") or raw.get("STATIC_TARGET") or ""
    addresses = raw.get("supported_addresses") or raw.get("LIVE_ADDRESS") or {}
    if not isinstance(addresses, dict):
        addresses = {"_raw": addresses}
    generation = (
        raw.get("generation_family")
        or raw.get("DEPLOYMENT_FAMILY")
        or raw.get("generation")
        or "UNSPECIFIED"
    )
    source_commits = (
        raw.get("source_artifact_commit")
        or raw.get("SOURCE_ARTIFACT_COMMIT")
        or {}
    )
    bytecode = (
        raw.get("live_bytecode_binding_classification")
        or raw.get("BYTECODE_BINDING_RESULT")
        or {}
    )
    dual_valid = classification in {"PATH_SOT_DUAL_VALID"} or bool(raw.get("dual_valid"))
    evidence_refs = list(raw.get("evidence_references") or raw.get("CONFLICT_SOURCES_ATTACHED") or [])
    return {
        "path_id": pid,
        "target_contract_role": static_target,
        "supported_addresses": addresses,
        "generation_family": generation,
        "source_artifact_commit": source_commits if isinstance(source_commits, dict) else {"value": source_commits},
        "live_bytecode_binding_classification": bytecode if isinstance(bytecode, dict) else {"value": bytecode},
        "dual_valid": dual_valid,
        "conflict_status": conflict,
        "path_specific_sot_classification": classification,
        "evidence_references": evidence_refs,
        "layer_note": raw.get("LAYER_NOTE") or raw.get("layer_note") or "",
        "global_canonical_required": False,
    }


def ingest_s7_path_bindings(bindings: dict[str, Any], *, global_canonical: str = "UNRESOLVED") -> dict[str, Any]:
    """Bridge S7 path-specific-binding.json into the native path-SoT contract."""
    bundle = empty_path_sot_bundle()
    bundle["global_canonical_status"] = global_canonical
    bundle["multi_generation_status"] = "OVERLAY_INGESTED_FIXTURE"
    bundle["source"] = "S7_path-specific-binding"
    records = []
    for p in bindings.get("paths") or []:
        if not isinstance(p, dict):
            continue
        rec = normalize_path_sot_record(p)
        if rec["path_id"]:
            records.append(rec)
    bundle["records"] = records
    bundle["record_count"] = len(records)
    return bundle


def index_path_sot(bundle: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    if not bundle or not isinstance(bundle, dict):
        return {}
    out: dict[str, dict[str, Any]] = {}
    for r in bundle.get("records") or []:
        if not isinstance(r, dict):
            continue
        pid = r.get("path_id") or ""
        if pid:
            out[pid] = r
    return out


def path_sot_usable(rec: dict[str, Any] | None) -> bool:
    if not rec:
        return False
    cls = rec.get("path_specific_sot_classification") or ""
    return cls in PATH_SOT_USABLE


def path_sot_conflict_cleared(rec: dict[str, Any] | None) -> bool:
    if not rec:
        return False
    return str(rec.get("conflict_status") or "").upper() in PATH_SOT_CONFLICT_CLEARED


def path_sot_static_target_resolved(rec: dict[str, Any] | None) -> bool:
    if not rec:
        return False
    target = str(rec.get("target_contract_role") or "")
    if not target or target in UNLABELED_TARGETS or target == "NOT_BOUND":
        return False
    return True


def address_axes_from_path_sot(
    rec: dict[str, Any] | None,
    *,
    global_canonical_status: str = "UNRESOLVED",
) -> dict[str, str]:
    """Split overloaded ADDRESS_SOURCE into explicit axes."""
    if not rec:
        return {
            "GLOBAL_CANONICAL_STATUS": global_canonical_status,
            "PATH_USABLE_ADDRESS_STATUS": "UNRESOLVED",
            "ADDRESS_CONFLICT_STATUS": "UNRESOLVED",
            "MULTI_GENERATION_STATUS": "UNSUPPORTED",
        }
    usable = path_sot_usable(rec)
    conflict_cleared = path_sot_conflict_cleared(rec)
    dual = bool(rec.get("dual_valid")) or rec.get("path_specific_sot_classification") == "PATH_SOT_DUAL_VALID"
    return {
        "GLOBAL_CANONICAL_STATUS": global_canonical_status,
        "PATH_USABLE_ADDRESS_STATUS": "ESTABLISHED" if usable else "UNRESOLVED",
        "ADDRESS_CONFLICT_STATUS": "CLEARED" if conflict_cleared else "UNRESOLVED",
        "MULTI_GENERATION_STATUS": "DUAL_VALID_OVERLAY" if dual else "SINGLE_OR_UNSPECIFIED",
    }


def sot_status_axis(rec: dict[str, Any] | None, *, global_canonical_status: str = "UNRESOLVED") -> str:
    if global_canonical_status == "BOUND":
        return "GLOBAL_CANONICAL_BOUND"
    if not rec or not path_sot_usable(rec):
        return "NOT_ESTABLISHED"
    if not path_sot_conflict_cleared(rec):
        return "CONFLICT"
    if rec.get("path_specific_sot_classification") == "PATH_SOT_DUAL_VALID" or rec.get("dual_valid"):
        return "PATH_SPECIFIC_DUAL_VALID"
    return "PATH_SPECIFIC_USABLE"


CLEARANCE_SCHEMA = "weaver-path-static-clearance-overlay-v0"


def index_path_clearance(bundle: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    """Optional per-path static clearance from CC/SP operator overlays."""
    if not bundle or not isinstance(bundle, dict):
        return {}
    out: dict[str, dict[str, Any]] = {}
    for r in bundle.get("records") or []:
        if not isinstance(r, dict):
            continue
        pid = r.get("path_id") or r.get("PATH_ID") or ""
        if pid:
            out[pid] = r
    return out


def ingest_cc_sp_clearance(cc: dict[str, Any], signer_rec: dict[str, Any] | None = None) -> dict[str, Any]:
    """Bridge CC/SP recalculation artifacts into clearance overlay records."""
    records = []
    signer_by = {}
    if signer_rec:
        rows = signer_rec.get("path_reclassifications") or signer_rec.get("cleared_paths") or []
        for row in rows:
            if isinstance(row, dict) and row.get("PATH_ID"):
                signer_by[row["PATH_ID"]] = row
    for row in cc.get("paths") or []:
        if not isinstance(row, dict):
            continue
        pid = row.get("PATH_ID") or ""
        if not pid:
            continue
        srow = signer_by.get(pid) or {}
        records.append({
            "path_id": pid,
            "caller_chain_complete": bool(row.get("STATIC_CALLER_CHAIN_COMPLETE")) and not bool(row.get("caller_chain_blocked")),
            "signer_mechanism_cleared": (not bool(row.get("SIGNER_BLOCKED"))) or bool(srow.get("cleared")),
            "conflict_cleared": not bool(row.get("CONFLICT_BLOCKED")),
            "false_positive_removed": row.get("static_path_class") == "FALSE_POSITIVE_REMOVED",
            "evidence_references": ["CC_overlay", "SP_overlay"],
        })
    return {
        "schema_version": CLEARANCE_SCHEMA,
        "records": records,
        "limitations": [
            "operator overlay clearance for static axes only",
            "does not prove runtime execution, authority, or independent witness",
        ],
    }
