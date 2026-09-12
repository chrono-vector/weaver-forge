"""Weaver Runtime Path Synthesizer v0.

Static-only synthesis of previously extracted Weaver evidence into bounded runtime
path graphs. It does not execute target repository code.

Optionally consumes weaver-static-evidence-graph-v0 when supplied. Absent graph
input preserves legacy behavior.

Static path completion (STATIC_PATH_STATUS) is evaluated independently from
runtime execution, authority, runtime signer identity, and independent witness.
Path-specific SoT may satisfy the address/deployment dimension without a global
canonical family. Legacy path_status tracks STATIC_PATH_STATUS (COMPLETE/PARTIAL/
BROKEN) and must not overwrite the multi-axis fields.
"""
from __future__ import annotations
import hashlib, json, re, sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from path_specific_sot_v0 import (
    PATH_SOT_SCHEMA,
    address_axes_from_path_sot,
    dynamic_target_axes,
    index_path_clearance,
    index_path_sot,
    path_sot_conflict_cleared,
    path_sot_static_target_resolved,
    path_sot_usable,
    sot_status_axis,
)

SCHEMA_VERSION = "weaver-runtime-path-synthesizer-v0"
SV_SCHEMA = "weaver-external-repo-source-verifier-v0"
RI_SCHEMA = "weaver-runtime-surface-inventory-v0"
MC_SCHEMA = "weaver-mutating-callsite-analyzer-v0"
QS_SCHEMA = "weaver-queue-state-transition-analyzer-v0"
GRAPH_SCHEMA = "weaver-static-evidence-graph-v0"
CONTRACT_SCHEMA = "weaver-runtime-path-synthesizer-evidence-contract-v0"
RID_PREFIX = "wrps-v0-"

# Gaps that block STATIC_PATH_COMPLETE after path-SoT / evidence clearance.
STATIC_COMPLETION_BLOCKING = {
    "SIGNER_SOURCE_PARTIAL",
    "ADDRESS_SOURCE_PARTIAL",
    "GENERATED_CONFIG_DEPENDENCY",
    "GENERATED_CONFIG_PARTIAL",
    "CALLER_CHAIN_HEURISTIC",
    "CALLER_CHAIN_UNRESOLVED",
    "PROVENANCE_CONFLICT",
    "NOT_FOUND_DEPENDENCY",
    "STATIC_TARGET_UNRESOLVED",
}

# Explicitly axis-separated / informational — do not veto STATIC_PATH_COMPLETE.
STATIC_COMPLETION_NON_BLOCKING = {
    "AUTHORITY_CONDITION_PARTIAL",
    "RETRY_PATH_PARTIAL",
    "CONCURRENCY_UNRESOLVED",
    "ABI_LINK_PARTIAL",
    "QUEUE_RETRY_PARTIAL",
    "CONCURRENCY_PARTIAL",
}

# Edge types whose HEURISTIC mode blocks static completion.
STATIC_CRITICAL_EDGE_TYPES = {
    "CALLS",
    "INVOKES",
    "DELEGATES_TO",
    "DISPATCHES_TO",
    "PROCESSES",
    "HANDLES",
    "SUBMITS_VIA",
    "RESOLVES_ADDRESS",
    "RESOLVES_SIGNER",
    "USES_SIGNER",
    "SIGNS_FOR",
}

# Addresses generated-config paths that must not be inferred as present.
GENERATED_ADDRESS_PATHS = {
    "client/src/abi/addresses.ts",
    "client\\src\\abi\\addresses.ts",
}
GENERATED_ADDRESS_EXAMPLE_PATHS = {
    "client/src/abi/addresses.ts.example",
    "client\\src\\abi\\addresses.ts.example",
}


def now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def canon(x):
    return json.dumps(x, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def rid(r):
    return RID_PREFIX + hashlib.sha256(canon({k: v for k, v in r.items() if k != "result_id"}).encode()).hexdigest()[:32]


def _node(nodes, ntype, file, line_start, line_end, symbol, source_module, mode="DETERMINISTIC", status="CONFIRMED", origin="WORKTREE", limitations=None):
    key = (ntype, file, line_start, symbol, source_module)
    if key in nodes["_idx"]:
        return nodes["_idx"][key]
    nid = f"wrps-v0-n{len(nodes['items'])+1:04d}"
    rec = {
        "node_id": nid,
        "node_type": ntype,
        "file": file or "",
        "line_start": line_start,
        "line_end": line_end,
        "symbol": symbol or "",
        "source_module": source_module,
        "analysis_mode": mode,
        "evidence_status": status,
        "source_origin": origin or "UNKNOWN",
        "limitations": limitations or ["static evidence node; runtime not executed"],
    }
    nodes["items"].append(rec)
    nodes["_idx"][key] = nid
    return nid


def _edge(edges, from_node, to_node, etype, file, line_start, line_end, mode="DETERMINISTIC", status="CONFIRMED", confidence="HIGH"):
    eid = f"wrps-v0-e{len(edges)+1:04d}"
    edges.append({
        "edge_id": eid,
        "from_node": from_node,
        "to_node": to_node,
        "edge_type": etype,
        "evidence_file": file or "",
        "line_start": line_start,
        "line_end": line_end,
        "analysis_mode": mode,
        "evidence_status": status,
        "confidence": confidence,
    })
    return eid


def base(req):
    sv = (req or {}).get("source_verifier_result") or {}
    ri = (req or {}).get("runtime_inventory_result") or {}
    mc = (req or {}).get("mutating_callsite_result") or {}
    qs = (req or {}).get("queue_state_transition_result") or {}
    graph = (req or {}).get("static_evidence_graph") or {}
    return {
        "schema_version": SCHEMA_VERSION,
        "result_id": "",
        "target_commit": (req or {}).get("target_commit", ""),
        "source_verifier_result_id": sv.get("result_id", ""),
        "runtime_inventory_result_id": ri.get("result_id", ""),
        "mutating_callsite_result_id": mc.get("result_id", ""),
        "queue_state_transition_result_id": qs.get("result_id", ""),
        "static_evidence_graph_result_id": graph.get("result_id", "") if isinstance(graph, dict) else "",
        "repo_path": (req or {}).get("repo_path", sv.get("repo_path", "")),
        "nodes": [],
        "edges": [],
        "paths": [],
        "path_gaps": [],
        "summary": {
            "paths_total": 0,
            "paths_complete": 0,
            "paths_partial": 0,
            "paths_broken": 0,
            "paths_unknown": 0,
            "validator_paths": 0,
            "archive_paths": 0,
            "user_paths": 0,
            "admin_paths": 0,
            "frontend_paths": 0,
            "cli_paths": 0,
            "deterministic_edges": 0,
            "heuristic_edges": 0,
            "human_review_required_paths": 0,
            "evidence_graph_consumed": "NO",
            "conflict_blocked_paths": 0,
            "not_found_blocked_paths": 0,
            "address_source_blocker_paths": 0,
            "generated_config_blocker_paths": 0,
            "signer_source_blocker_paths": 0,
            "caller_chain_heuristic_blocker_paths": 0,
        },
        "runtime_execution_verified": False,
        "limitations": [
            "static synthesis only",
            "does not prove runtime execution, transaction success, live authority, deployed bytecode identity, security, decentralization, trustlessness, Independent Witness, or Evidence admission",
        ],
        "reason_codes": [],
        "created_at": now(),
    }


def _check(req, r):
    if not isinstance(req, dict) or req.get("schema_version") != SCHEMA_VERSION:
        return "invalid_input_or_schema"
    sv = req.get("source_verifier_result") or {}
    ri = req.get("runtime_inventory_result") or {}
    mc = req.get("mutating_callsite_result") or {}
    qs = req.get("queue_state_transition_result") or {}
    if sv.get("schema_version") != SV_SCHEMA or sv.get("audit_source_valid") is not True:
        return "source_verifier_precondition_failed"
    if ri.get("schema_version") != RI_SCHEMA or ri.get("runtime_execution_verified") is not False:
        return "runtime_inventory_precondition_failed"
    if mc.get("schema_version") != MC_SCHEMA or mc.get("runtime_execution_verified") is not False:
        return "mutating_callsite_precondition_failed"
    if qs.get("schema_version") != QS_SCHEMA or qs.get("dynamic_execution_verified") is not False:
        return "queue_state_transition_precondition_failed"
    t = req.get("target_commit")
    if any(x.get("target_commit") != t for x in [sv, ri, mc, qs]):
        return "target_commit_mismatch"
    graph = req.get("static_evidence_graph")
    if graph is not None:
        if not isinstance(graph, dict) or graph.get("schema_version") != GRAPH_SCHEMA:
            return "static_evidence_graph_precondition_failed"
        if graph.get("target_commit") != t:
            return "static_evidence_graph_commit_mismatch"
        if graph.get("runtime_execution_verified") is not False:
            return "static_evidence_graph_precondition_failed"
    return ""


def _norm_path(p: str) -> str:
    return str(p or "").replace("\\", "/").strip()


def _is_addresses_ts(path: str) -> bool:
    return _norm_path(path).endswith("client/src/abi/addresses.ts")


def _is_addresses_example(path: str) -> bool:
    return _norm_path(path).endswith("client/src/abi/addresses.ts.example")


def _gaps_for_call(c, sv, mc, qs):
    gaps = []
    if c.get("signer_source", "unknown signer source") == "unknown signer source" or mc.get("signer_sources_mapped") != "YES":
        gaps.append(("SIGNER_SOURCE_PARTIAL", "NON_BLOCKING"))
    if c.get("contract_address_source", "unknown") == "unknown" or mc.get("contract_address_sources_mapped") != "YES":
        gaps.append(("ADDRESS_SOURCE_PARTIAL", "NON_BLOCKING"))
    if c.get("authority_status") != "CONFIRMED":
        gaps.append(("AUTHORITY_CONDITION_PARTIAL", "NON_BLOCKING"))
    if qs.get("summary", {}).get("partial_findings", 0):
        gaps.append(("RETRY_PATH_PARTIAL", "INFORMATIONAL"))
    if qs.get("summary", {}).get("unresolved_count", 0):
        gaps.append(("CONCURRENCY_UNRESOLVED", "INFORMATIONAL"))
    for gd in (sv.get("evidence_critical_results", []) + mc.get("generated_dependency_findings", [])):
        if "addresses.ts" in str(gd.get("path", "")) and (
            gd.get("status") in {"EXPECTED_MISSING", "MISSING_IN_TARGET"}
            or gd.get("classification") == "GENERATED_DEPENDENCY"
            or gd.get("exists_in_target") in {False, "NO", "FALSE"}
            or gd.get("evidence_status") == "NOT_FOUND"
        ):
            gaps.append(("GENERATED_CONFIG_DEPENDENCY", "NON_BLOCKING"))
            break
    return gaps


def _actor_bucket(role):
    s = (role or "unknown").lower()
    if "validator" in s:
        return "validator_paths"
    if "archive" in s:
        return "archive_paths"
    if "frontend" in s or "wallet" in s:
        return "frontend_paths"
    if "cli" in s or "operator" in s:
        return "cli_paths"
    if "owner" in s or "admin" in s or "deployer" in s:
        return "admin_paths"
    if "user" in s:
        return "user_paths"
    return "user_paths"


def _index_evidence_graph(graph: dict[str, Any] | None) -> dict[str, Any] | None:
    if not graph or not isinstance(graph, dict):
        return None
    records = list(graph.get("normalized_records") or [])
    conflicts = list(graph.get("conflicts") or [])
    not_found = list(graph.get("not_found_records") or [])
    contract = graph.get("path_synthesizer_contract") or {}
    updates = list(contract.get("path_blocker_updates") or []) if isinstance(contract, dict) else []

    by_callsite: dict[str, list[dict[str, Any]]] = {}
    by_file_line: dict[tuple[str, Any], list[dict[str, Any]]] = {}
    by_orphan: dict[str, list[dict[str, Any]]] = {}
    for r in records:
        cid = r.get("callsite_id") or ""
        if cid:
            by_callsite.setdefault(cid, []).append(r)
        fl = (_norm_path(r.get("source_file") or (r.get("from_entity") or {}).get("file") or ""), r.get("line_start"))
        if fl[0]:
            by_file_line.setdefault(fl, []).append(r)
        ot = r.get("orphan_type") or ""
        if ot:
            by_orphan.setdefault(ot, []).append(r)

    updates_by_callsite: dict[str, list[dict[str, Any]]] = {}
    global_updates: list[dict[str, Any]] = []
    for u in updates:
        cid = u.get("callsite_id") or ""
        if cid:
            updates_by_callsite.setdefault(cid, []).append(u)
        else:
            global_updates.append(u)

    idx = {
        "graph": graph,
        "records": records,
        "conflicts": conflicts,
        "not_found": not_found,
        "contract": contract if isinstance(contract, dict) else {},
        "updates": updates,
        "by_callsite": by_callsite,
        "by_file_line": by_file_line,
        "by_orphan": by_orphan,
        "updates_by_callsite": updates_by_callsite,
        "global_updates": global_updates,
    }
    idx["conflict_scopes"] = _build_conflict_scopes(idx)
    idx["not_found_scopes"] = _build_not_found_scopes(idx)
    return idx


def _not_found_category(r: dict[str, Any]) -> str:
    """Classify a NOT_FOUND record for root/derived reporting."""
    sid = str(r.get("subject_id") or "")
    sf = _norm_path(r.get("source_file") or "")
    ot = str(r.get("orphan_type") or "")
    rel = str(r.get("relation_type") or "")
    blob = f"{sid} {sf}".lower()
    if "addresses.ts" in blob or (
        ot == "GENERATED_ARTIFACTS"
        and ("addresses" in blob or sid.startswith("wcap-v0-g0001") or "generated" in blob)
    ):
        if rel == "NOT_FOUND_FOR" and (
            _is_addresses_ts(sid)
            or _is_addresses_ts(sf)
            or sid.startswith("wcap-v0-g0001")
        ):
            return "ROOT_GENERATED_ARTIFACT"
        return "DERIVED_GENERATED_CONFIG"
    if ot in {
        "SIGNER_SOURCE_STATUS",
        "SIGNER_SOURCES",
        "MUTATING_CALLSITE_SIGNER_REFINEMENTS",
        "CREDENTIAL_REFERENCES",
        "SIGNER_PROVENANCE_CHAINS",
    } or "signer" in sid.lower():
        return "SIGNER"
    if ot in {"CONCURRENCY_CONTROLS", "QUEUE_CONTROLS"} or sid.startswith("wqsta"):
        return "CONCURRENCY_QUEUE"
    if ot in {"ABI_ADDRESS_LINKS", "ABI_LINKS"} or "abi" in sid.lower():
        return "ABI_ADDRESS_BINDING"
    if ot in {"CALLGRAPH_EDGES", "CALLGRAPH_NODES", "CALLSITE_ANCESTRY_REFINEMENTS"}:
        return "CALLGRAPH"
    return "OTHER"


def _is_addresses_module_ref(s: str) -> bool:
    n = _norm_path(s).lower()
    if not n:
        return False
    if "addresses.ts.example" in n:
        return False
    return (
        n.endswith("/addresses")
        or n.endswith("/addresses.js")
        or n.endswith("/addresses.ts")
        or "abi/addresses" in n
        or n == "client/src/abi/addresses.ts"
    )


def _entity_is_generated_address_module(entity_id: str) -> bool:
    s = str(entity_id or "").lower()
    if not s:
        return False
    if "deployments" in s:
        return False
    return (
        "imported address module" in s
        or "generated constant" in s
        or "generated_dependency" in s
        or _is_addresses_module_ref(s)
    )


def _entity_is_alternate_static_source(entity_id: str, source_file: str = "") -> bool:
    s = str(entity_id or "").lower()
    sf = _norm_path(source_file).lower()
    if "deployments" in s or sf.endswith("deployments.ts"):
        return True
    if "hardcoded" in s or s.startswith("0x"):
        return True
    if ".deploy-state" in sf or "deploy-state" in s:
        return True
    return False


def _build_not_found_scopes(idx: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Subject scope for each NOT_FOUND record (mirrors conflict scopes)."""
    scopes: dict[str, dict[str, Any]] = {}
    for r in idx.get("not_found") or []:
        eid = r.get("evidence_id") or ""
        if not eid:
            continue
        cat = _not_found_category(r)
        files: set[str] = set()
        symbols: set[str] = set()
        chains: set[str] = set()
        callsite_ids: set[str] = set()
        subject_ids: set[str] = set()
        contracts: set[str] = set()
        gen_artifacts: set[str] = set()

        sf = _norm_path(r.get("source_file") or (r.get("from_entity") or {}).get("file") or "")
        if sf:
            files.add(sf)
        sid = str(r.get("subject_id") or "")
        if sid:
            subject_ids.add(sid)
            if _is_addresses_ts(sid) or _is_addresses_module_ref(sid):
                gen_artifacts.add(_norm_path(sid) if "/" in sid else "client/src/abi/addresses.ts")
        if _is_addresses_ts(sf) or _is_addresses_module_ref(sf):
            gen_artifacts.add(sf if _is_addresses_ts(sf) else "client/src/abi/addresses.ts")
        if r.get("callsite_id"):
            callsite_ids.add(str(r["callsite_id"]))
        if r.get("source_symbol"):
            symbols.add(str(r["source_symbol"]))
        if r.get("contract_name") and not _is_generic_contract_token(str(r["contract_name"])):
            contracts.add(str(r["contract_name"]))
        if r.get("config_key") and not _is_generic_contract_token(str(r["config_key"])):
            contracts.add(str(r["config_key"]))
        cc = r.get("chain_context") or ""
        if cc and cc not in {"UNKNOWN", "unknown", ""}:
            chains.add(str(cc))

        # Root subject for derived generated-config rows.
        root_subject = ""
        if cat in {"ROOT_GENERATED_ARTIFACT", "DERIVED_GENERATED_CONFIG"}:
            root_subject = "client/src/abi/addresses.ts"
            gen_artifacts.add("client/src/abi/addresses.ts")

        scopes[eid] = {
            "record": r,
            "category": cat,
            "root_subject": root_subject,
            "is_root": cat == "ROOT_GENERATED_ARTIFACT",
            "is_derived": cat == "DERIVED_GENERATED_CONFIG",
            "files": files,
            "symbols": symbols,
            "chains": chains,
            "callsite_ids": callsite_ids,
            "subject_ids": subject_ids,
            "contracts": contracts,
            "gen_artifacts": gen_artifacts,
        }
    return scopes


def _path_directory(path_file: str) -> str:
    p = _norm_path(path_file)
    if "/" not in p:
        return ""
    return p.rsplit("/", 1)[0]


def _path_depends_on_addresses_ts(
    idx: dict[str, Any],
    c: dict[str, Any],
    matched: list[dict[str, Any]],
) -> tuple[bool, str]:
    """True when path has a supported dependency on the generated addresses.ts module."""
    path_file = _norm_path(c.get("file") or "")
    path_dir = _path_directory(path_file)
    cid = str(c.get("callsite_id") or "")

    # Direct path file is the artifact.
    if _is_addresses_ts(path_file):
        return True, "path_is_generated_artifact"

    # Matched evidence: generated dependency / imported address module.
    for r in matched:
        if str(r.get("generated_dependency") or "").upper() in {"YES", "TRUE", "PARTIAL"}:
            te = str((r.get("to_entity") or {}).get("entity_id") or "")
            if _entity_is_generated_address_module(te) or not te:
                return True, "generated_dependency_flag"
        if r.get("relation_type") in {"DEPENDS_ON_GENERATED_ARTIFACT", "NOT_FOUND_FOR"}:
            sid = str(r.get("subject_id") or "")
            sf = _norm_path(r.get("source_file") or "")
            if _is_addresses_ts(sid) or _is_addresses_ts(sf) or _is_addresses_module_ref(sid):
                return True, "generated_artifact_relation"
        if r.get("relation_type") in {"RESOLVES_ADDRESS", "USES_ADDRESS"}:
            te = str((r.get("to_entity") or {}).get("entity_id") or "")
            if _entity_is_generated_address_module(te):
                return True, "address_resolution_relation"

    # ADDRESS_CONSUMERS: same file, or sibling under a package entrypoint (index.*).
    # Shared directories like FrontEnd/src/hooks must NOT inherit for every hook file.
    for r in idx["by_orphan"].get("ADDRESS_CONSUMERS", []):
        rf = _norm_path(r.get("source_file") or "")
        te = str((r.get("to_entity") or {}).get("entity_id") or "")
        if not _is_addresses_module_ref(te):
            continue
        if path_file and rf == path_file:
            return True, "config_consumer_same_file"
        base = path_file.rsplit("/", 1)[-1] if path_file else ""
        if (
            base in {"index.ts", "index.js", "index.tsx", "index.mjs", "index.cjs"}
            and path_dir
            and rf.startswith(path_dir + "/")
            and _path_directory(rf) == path_dir
        ):
            return True, "config_consumer_same_package"

    # Explicit GENERATED_ARTIFACTS dependency rows tied to path file / package.
    for r in idx["by_orphan"].get("GENERATED_ARTIFACTS", []):
        sid = str(r.get("subject_id") or "")
        sf = _norm_path(r.get("source_file") or "")
        if not (_is_addresses_ts(sid) or _is_addresses_ts(sf) or sid.startswith("wcap-v0-g0001")):
            continue
        if path_file and (sf == path_file or (path_dir and sf.startswith(path_dir + "/"))):
            return True, "generated_artifact_package"
        if r.get("callsite_id") and str(r.get("callsite_id")) == cid:
            return True, "generated_artifact_callsite"

    # Callsite-declared generated address source (mutating analyzer).
    cas = str(c.get("contract_address_source") or "").lower()
    if "addresses" in cas or cas in {"generated address", "generated constant", "environment/generated constant"}:
        return True, "callsite_address_source"

    return False, "no_addresses_dependency"


def _path_has_alternate_static_address_source(
    idx: dict[str, Any],
    c: dict[str, Any],
    matched: list[dict[str, Any]],
) -> bool:
    """True when path already binds via deployments/hardcoded/static SoT (not addresses.ts)."""
    for r in matched:
        te = str((r.get("to_entity") or {}).get("entity_id") or "")
        sf = _norm_path(r.get("source_file") or (r.get("to_entity") or {}).get("file") or "")
        if r.get("relation_type") in {"RESOLVES_ADDRESS", "USES_ADDRESS", "CONSUMES"}:
            if _entity_is_alternate_static_source(te, sf):
                return True
        if r.get("orphan_type") == "ADDRESS_SOURCES" and _entity_is_alternate_static_source(te, sf):
            return True
    path_file = _norm_path(c.get("file") or "")
    for r in idx["by_orphan"].get("ADDRESS_CONSUMERS", []):
        rf = _norm_path(r.get("source_file") or "")
        if path_file and rf == path_file:
            te = str((r.get("to_entity") or {}).get("entity_id") or "")
            if _entity_is_alternate_static_source(te, rf):
                return True
    return False


def _not_found_attaches_to_path(
    scope: dict[str, Any],
    path_scope: dict[str, Any],
    matched: list[dict[str, Any]],
    c: dict[str, Any],
    idx: dict[str, Any],
    addresses_dep: bool,
) -> tuple[bool, str]:
    """Subject-scoped NOT_FOUND attach. Never attach solely on repo/commit presence."""
    cat = scope.get("category") or "OTHER"
    # Fail closed on explicit chain-context mismatch when both sides are specific.
    if scope["chains"] and path_scope["chains"] and not (scope["chains"] & path_scope["chains"]):
        return False, "chain_context_mismatch"

    if cat in {"ROOT_GENERATED_ARTIFACT", "DERIVED_GENERATED_CONFIG"}:
        if not addresses_dep:
            # Alternate static source alone must not inherit addresses.ts absence.
            return False, "no_generated_artifact_dependency"
        return True, "generated_artifact_dependency"

    if cat == "SIGNER":
        cid = str(c.get("callsite_id") or "")
        if scope["callsite_ids"] and cid and cid in scope["callsite_ids"]:
            return True, "callsite_id"
        if scope["subject_ids"] and cid and cid in scope["subject_ids"]:
            return True, "subject_id"
        path_file = path_scope.get("path_file") or ""
        if path_file and scope["files"] and path_file in scope["files"]:
            # Only when path is signer-dependent (has signer gap potential / signer node).
            if str(c.get("signer_source") or "") or any(
                r.get("orphan_type") in {
                    "MUTATING_CALLSITE_SIGNER_REFINEMENTS",
                    "SIGNER_SOURCES",
                    "SIGNER_SOURCE_STATUS",
                    "CREDENTIAL_REFERENCES",
                }
                or r.get("relation_type") in {"USES_SIGNER", "SIGNS_FOR", "NOT_FOUND_FOR"}
                for r in matched
            ):
                return True, "file"
        return False, "signer_no_relation"

    if cat == "CONCURRENCY_QUEUE":
        # Queue/concurrency NOT_FOUND attaches only via explicit callsite / subject join.
        cid = str(c.get("callsite_id") or "")
        if scope["callsite_ids"] and cid and cid in scope["callsite_ids"]:
            return True, "callsite_id"
        if scope["subject_ids"] & path_scope["subject_ids"]:
            return True, "subject_id"
        matched_ids = {r.get("evidence_id") for r in matched if r.get("evidence_id")}
        reid = (scope.get("record") or {}).get("evidence_id")
        if reid and reid in matched_ids:
            return True, "evidence_graph_edge"
        return False, "concurrency_unrelated"

    # Generic / ABI / callgraph / other: require concrete relation.
    if scope["callsite_ids"] and (scope["callsite_ids"] & path_scope["callsite_ids"]):
        return True, "callsite_id"
    if scope["subject_ids"] and (scope["subject_ids"] & path_scope["subject_ids"]):
        return True, "subject_id"
    if scope["files"] and (scope["files"] & path_scope["files"]):
        return True, "file"
    matched_ids = {r.get("evidence_id") for r in matched if r.get("evidence_id")}
    reid = (scope.get("record") or {}).get("evidence_id")
    if reid and reid in matched_ids:
        return True, "evidence_graph_edge"
    return False, "no_relation"


def _path_relevant_not_found(
    idx: dict[str, Any],
    matched: list[dict[str, Any]],
    c: dict[str, Any],
) -> tuple[list[dict[str, Any]], bool, list[str], list[str]]:
    """Attach only NOT_FOUND records with a supported subject/dependency relation.

    Returns (attached_records, addresses_blocks, root_evidence_ids, derived_evidence_ids).
    """
    if not idx.get("not_found"):
        # Still allow sv/mc addresses absence when path depends on generated module.
        addresses_dep, _ = _path_depends_on_addresses_ts(idx, c, matched)
        return [], addresses_dep, [], []

    path_scope = _path_conflict_scope(idx, c, matched)
    addresses_dep, _dep_reason = _path_depends_on_addresses_ts(idx, c, matched)
    alternate = _path_has_alternate_static_address_source(idx, c, matched)
    # Alternate static SoT without addresses dependency → do not inherit addresses.ts blocker.
    if alternate and not addresses_dep:
        addresses_dep = False

    scopes = idx.get("not_found_scopes") or _build_not_found_scopes(idx)
    attached: list[dict[str, Any]] = []
    root_ids: list[str] = []
    derived_ids: list[str] = []
    for r in idx["not_found"]:
        eid = r.get("evidence_id") or ""
        scope = scopes.get(eid) or {
            "record": r,
            "category": _not_found_category(r),
            "root_subject": "",
            "is_root": False,
            "is_derived": False,
            "files": set(),
            "symbols": set(),
            "chains": set(),
            "callsite_ids": set(),
            "subject_ids": set(),
            "contracts": set(),
            "gen_artifacts": set(),
        }
        ok, _reason = _not_found_attaches_to_path(scope, path_scope, matched, c, idx, addresses_dep)
        if not ok:
            continue
        attached.append(r)
        cat = scope.get("category")
        if cat == "ROOT_GENERATED_ARTIFACT":
            root_ids.append(eid)
        elif cat == "DERIVED_GENERATED_CONFIG":
            derived_ids.append(eid)
        elif cat == "SIGNER":
            # Signer NOT_FOUND is path-local; treat as root for this path's NF summary.
            root_ids.append(eid)
        else:
            derived_ids.append(eid)

    addresses_blocks = addresses_dep and (
        any(_not_found_category(r) in {"ROOT_GENERATED_ARTIFACT", "DERIVED_GENERATED_CONFIG"} for r in attached)
        or _addresses_ts_absent_in_graph(idx)
    )
    return attached, addresses_blocks, [x for x in root_ids if x], [x for x in derived_ids if x]


def _addresses_ts_absent_in_graph(idx: dict[str, Any] | None) -> bool:
    if not idx:
        return False
    for r in (idx.get("not_found") or []) + idx["by_orphan"].get("GENERATED_ARTIFACTS", []):
        sid = r.get("subject_id") or r.get("source_file") or ""
        if _is_addresses_ts(sid) or _is_addresses_ts(r.get("source_file") or ""):
            if r.get("evidence_status") == "NOT_FOUND" or r.get("relation_type") == "NOT_FOUND_FOR":
                return True
    return False


def _norm_name(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(s or "").lower())


def _is_generic_contract_token(s: str) -> bool:
    n = _norm_name(s)
    return (not n) or n in {
        "unknown",
        "other",
        "conflict",
        "conflictsources",
        "address",
        "config",
        "configaddress",
    }


def _names_overlap(a: str, b: str) -> bool:
    """Token overlap for contract/config names (Archive ↔ CAW_ACTIONS_ARCHIVE_ADDRESS)."""
    if _is_generic_contract_token(a) or _is_generic_contract_token(b):
        return False
    na, nb = _norm_name(a), _norm_name(b)
    if not na or not nb:
        return False
    if na == nb:
        return True
    # Require substantial containment to avoid tiny false positives.
    if len(na) >= 6 and len(nb) >= 6 and (na in nb or nb in na):
        return True
    return False


def _conflict_source_ids(conflict: dict[str, Any]) -> list[str]:
    explicit = conflict.get("sources")
    if isinstance(explicit, list) and explicit:
        return [str(x).strip() for x in explicit if str(x).strip()]
    te = conflict.get("to_entity") or {}
    eid = str(te.get("entity_id") or "").strip()
    if not eid or eid == "conflict-sources":
        return []
    return [x.strip() for x in eid.split(",") if x.strip() and x.strip() != "conflict-sources"]


def _is_conflict_id_subject(sid: str) -> bool:
    return bool(re.match(r"^wcap-v0-x\d+", str(sid or "")))


def _build_conflict_scopes(idx: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Resolve attachable subject scope for each provenance conflict from linked evidence."""
    addr_by_id: dict[str, dict[str, Any]] = {}
    for r in idx["by_orphan"].get("ADDRESS_SOURCES", []):
        sid = str(r.get("subject_id") or r.get("source_record_id") or "")
        if sid:
            addr_by_id[sid] = r

    scopes: dict[str, dict[str, Any]] = {}
    for c in idx["conflicts"]:
        eid = c.get("evidence_id") or ""
        source_ids = _conflict_source_ids(c)
        contracts: set[str] = set()
        files: set[str] = set()
        symbols: set[str] = set()
        chains: set[str] = set()
        callsite_ids: set[str] = set()
        subject_ids: set[str] = set()

        if c.get("contract_name") and not _is_generic_contract_token(str(c["contract_name"])):
            contracts.add(str(c["contract_name"]))
        if c.get("config_key") and not _is_generic_contract_token(str(c["config_key"])):
            contracts.add(str(c["config_key"]))
        if c.get("callsite_id"):
            callsite_ids.add(str(c["callsite_id"]))
        sid = str(c.get("subject_id") or "")
        if sid and not _is_conflict_id_subject(sid):
            subject_ids.add(sid)
        sf = _norm_path(c.get("source_file") or "")
        if sf:
            files.add(sf)
        if c.get("source_symbol"):
            symbols.add(str(c["source_symbol"]))
        cc = c.get("chain_context") or ""
        if cc and cc not in {"UNKNOWN", "unknown", ""}:
            chains.add(str(cc))

        for sid in source_ids:
            a = addr_by_id.get(sid)
            if not a:
                continue
            if a.get("contract_name") and not _is_generic_contract_token(str(a["contract_name"])):
                contracts.add(str(a["contract_name"]))
            if a.get("config_key") and not _is_generic_contract_token(str(a["config_key"])):
                contracts.add(str(a["config_key"]))
            te = a.get("to_entity") or {}
            if te.get("entity_id") and not _is_generic_contract_token(str(te["entity_id"])):
                contracts.add(str(te["entity_id"]))
            af = _norm_path(a.get("source_file") or (a.get("from_entity") or {}).get("file") or "")
            if af:
                files.add(af)
            if a.get("source_symbol"):
                symbols.add(str(a["source_symbol"]))
            ac = a.get("chain_context") or ""
            if ac and ac not in {"UNKNOWN", "unknown", ""}:
                chains.add(str(ac))
            if a.get("callsite_id"):
                callsite_ids.add(str(a["callsite_id"]))

        # Zero-source / degenerate conflicts are preserved in the graph but must not
        # globally block unrelated paths (e.g. empty analyzer grouping artifacts).
        zero_source = (
            len(source_ids) == 0
            and not contracts
            and not callsite_ids
            and not files
            and not symbols
            and not subject_ids
        )

        scopes[eid] = {
            "conflict": c,
            "source_ids": source_ids,
            "contracts": contracts,
            "files": files,
            "symbols": symbols,
            "chains": chains,
            "callsite_ids": callsite_ids,
            "subject_ids": subject_ids,
            "zero_source": zero_source,
        }
    return scopes


def _path_conflict_scope(idx: dict[str, Any], c: dict[str, Any], matched: list[dict[str, Any]]) -> dict[str, Any]:
    """Collect path-side tokens used for subject-scoped conflict attach."""
    path_file = _norm_path(c.get("file") or "")
    contracts: set[str] = set()
    files: set[str] = {path_file} if path_file else set()
    symbols: set[str] = set()
    chains: set[str] = set()
    callsite_ids: set[str] = set()
    subject_ids: set[str] = set()
    source_ids: set[str] = set()
    gen_artifacts: set[str] = set()

    tc = c.get("target_contract") or ""
    if tc and str(tc).lower() not in {"unknown", ""} and not _is_generic_contract_token(str(tc)):
        contracts.add(str(tc))
    for sym in (c.get("symbol"), c.get("caller_symbol"), c.get("target_method")):
        if sym and str(sym).lower() not in {"unknown", ""}:
            symbols.add(str(sym))
    if c.get("callsite_id"):
        callsite_ids.add(str(c["callsite_id"]))
        subject_ids.add(str(c["callsite_id"]))
    cs = c.get("chain_source") or ""
    if cs and str(cs).lower() not in {"unknown", ""}:
        chains.add(str(cs))

    for r in matched:
        if r.get("contract_name") and not _is_generic_contract_token(str(r["contract_name"])):
            contracts.add(str(r["contract_name"]))
        if r.get("config_key") and not _is_generic_contract_token(str(r["config_key"])):
            contracts.add(str(r["config_key"]))
        rf = _norm_path(r.get("source_file") or (r.get("from_entity") or {}).get("file") or "")
        if rf:
            files.add(rf)
        if r.get("source_symbol"):
            symbols.add(str(r["source_symbol"]))
        if r.get("callsite_id"):
            callsite_ids.add(str(r["callsite_id"]))
        if r.get("subject_id"):
            subject_ids.add(str(r["subject_id"]))
        rc = r.get("chain_context") or ""
        if rc and rc not in {"UNKNOWN", "unknown", ""}:
            chains.add(str(rc))
        if r.get("orphan_type") == "ADDRESS_SOURCES":
            sid = str(r.get("subject_id") or r.get("source_record_id") or "")
            if sid:
                source_ids.add(sid)
        if r.get("orphan_type") in {"GENERATED_ARTIFACTS"} or r.get("relation_type") in {
            "DEPENDS_ON_GENERATED_ARTIFACT",
            "NOT_FOUND_FOR",
        }:
            gp = _norm_path(r.get("source_file") or r.get("subject_id") or "")
            if gp:
                gen_artifacts.add(gp)

    # Path dependency ancestry via ADDRESS_CONSUMERS on the same file.
    for r in idx["by_orphan"].get("ADDRESS_CONSUMERS", []):
        rf = _norm_path(r.get("source_file") or "")
        if path_file and rf == path_file:
            blob = " ".join(
                [
                    str(r.get("contract_name") or ""),
                    str(r.get("config_key") or ""),
                    str((r.get("to_entity") or {}).get("entity_id") or ""),
                ]
            )
            for tok in re.split(r"[,;\s]+", blob):
                tok = tok.strip()
                if tok and not _is_generic_contract_token(tok):
                    contracts.add(tok)
            files.add(path_file)

    return {
        "contracts": contracts,
        "files": files,
        "symbols": symbols,
        "chains": chains,
        "callsite_ids": callsite_ids,
        "subject_ids": subject_ids,
        "source_ids": source_ids,
        "gen_artifacts": gen_artifacts,
        "path_file": path_file,
    }


def _conflict_attaches_to_path(
    scope: dict[str, Any],
    path_scope: dict[str, Any],
    matched: list[dict[str, Any]],
) -> tuple[bool, str]:
    """Subject-scoped attach rule. Never attach solely on target_commit / repo presence."""
    if scope.get("zero_source"):
        return False, "zero_source_preserved_not_blocking"

    # Fail closed on explicit chain-context mismatch when both sides are specific.
    if scope["chains"] and path_scope["chains"] and not (scope["chains"] & path_scope["chains"]):
        return False, "chain_context_mismatch"

    if scope["callsite_ids"] and (scope["callsite_ids"] & path_scope["callsite_ids"]):
        return True, "callsite_id"

    if scope["subject_ids"] and (scope["subject_ids"] & path_scope["subject_ids"]):
        return True, "subject_id"

    for cc in scope["contracts"]:
        for pc in path_scope["contracts"]:
            if _names_overlap(cc, pc):
                return True, "contract_name"

    if scope["source_ids"] and (set(scope["source_ids"]) & path_scope["source_ids"]):
        return True, "address_source"

    if scope["files"] and (scope["files"] & path_scope["files"]):
        return True, "file"

    if scope["symbols"] and path_scope["symbols"]:
        # Ignore ultra-generic shared symbols that appear on unrelated records.
        generic = {"deployments", "process", "unknown", "sendtransaction"}
        scoped = {s for s in scope["symbols"] if _norm_name(s) not in generic and s}
        path_syms = {s for s in path_scope["symbols"] if _norm_name(s) not in generic and s}
        if scoped & path_syms:
            return True, "symbol"

    # Generated-artifact relation: only when conflict sources live in a generated
    # address artifact AND the path itself is that artifact (or explicit gen dep).
    conflict_gen = {f for f in scope["files"] if _is_addresses_ts(f) or _is_addresses_example(f)}
    if conflict_gen and (
        (path_scope["path_file"] and path_scope["path_file"] in conflict_gen)
        or (path_scope["gen_artifacts"] & conflict_gen)
    ):
        return True, "generated_artifact"

    matched_ids = {r.get("evidence_id") for r in matched if r.get("evidence_id")}
    ceid = (scope.get("conflict") or {}).get("evidence_id")
    if ceid and ceid in matched_ids:
        return True, "evidence_graph_edge"

    return False, "no_relation"


def _join_records_for_call(idx: dict[str, Any], c: dict[str, Any]) -> tuple[list[dict[str, Any]], str]:
    """Return matching records and join mode DETERMINISTIC|HEURISTIC|NONE."""
    cid = c.get("callsite_id") or ""
    matched: list[dict[str, Any]] = []
    mode = "NONE"
    if cid and cid in idx["by_callsite"]:
        matched.extend(idx["by_callsite"][cid])
        mode = "DETERMINISTIC"
    file = _norm_path(c.get("file") or "")
    line = c.get("line_start")
    if file and (file, line) in idx["by_file_line"]:
        for r in idx["by_file_line"][(file, line)]:
            if r not in matched:
                matched.append(r)
        if mode == "NONE":
            mode = "DETERMINISTIC"
    # Heuristic fallback: contract_name / symbol / file-only
    if mode == "NONE":
        sym = c.get("symbol") or c.get("caller_symbol") or ""
        contract = c.get("target_contract") or ""
        for r in idx["records"]:
            if contract and contract != "unknown" and r.get("contract_name") == contract:
                matched.append(r)
            elif sym and (r.get("source_symbol") == sym or (r.get("from_entity") or {}).get("symbol") == sym):
                matched.append(r)
            elif file and _norm_path(r.get("source_file") or "") == file and not r.get("callsite_id"):
                matched.append(r)
        if matched:
            mode = "HEURISTIC"
    return matched, mode


def _addresses_ts_not_found(idx: dict[str, Any] | None, sv: dict[str, Any], mc: dict[str, Any]) -> tuple[bool, list[str]]:
    eids: list[str] = []
    if idx:
        for r in idx["not_found"] + idx["by_orphan"].get("GENERATED_ARTIFACTS", []):
            sid = r.get("subject_id") or r.get("source_file") or ""
            if _is_addresses_ts(sid) or _is_addresses_ts(r.get("source_file") or ""):
                if r.get("evidence_status") == "NOT_FOUND" or r.get("relation_type") == "NOT_FOUND_FOR":
                    eids.append(r.get("evidence_id", ""))
        # example present must not imply generated output exists
        for r in idx["records"]:
            sid = r.get("subject_id") or r.get("source_file") or ""
            if _is_addresses_example(sid) and r.get("evidence_status") in {"CONFIRMED", "PARTIAL"}:
                # presence of example alone does not clear absence of addresses.ts
                pass
    for gd in (sv.get("evidence_critical_results", []) + mc.get("generated_dependency_findings", [])):
        p = gd.get("path") or ""
        if _is_addresses_ts(p) and (
            gd.get("status") in {"EXPECTED_MISSING", "MISSING_IN_TARGET"}
            or gd.get("exists_in_target") in {False, "NO", "FALSE"}
            or gd.get("evidence_status") == "NOT_FOUND"
            or gd.get("classification") == "GENERATED_DEPENDENCY"
        ):
            eids.append(str(gd.get("finding_id") or gd.get("path") or "addresses.ts"))
    return (len(eids) > 0), [e for e in eids if e]


def _address_join_justifies_removal(matched: list[dict[str, Any]], join_mode: str, has_conflict: bool, addresses_missing: bool) -> tuple[bool, list[str]]:
    """Remove ADDRESS_SOURCE_PARTIAL only when deterministic CONFIRMED join exists and no conflict/NOT_FOUND.

    Path-usable / dual-valid SoT clearance is applied separately via
    `_apply_path_sot_clearance` so global canonical collapse is not required.
    """
    if has_conflict or addresses_missing or join_mode != "DETERMINISTIC":
        return False, []
    eids = []
    for r in matched:
        if r.get("orphan_type") not in {"MUTATING_CALLSITE_ADDRESS_SOURCE_REFINEMENTS", "ADDRESS_SOURCES", "ADDRESS_CONSUMERS", "ABI_ADDRESS_LINKS", "PROVENANCE_CHAINS"}:
            if r.get("relation_type") not in {"RESOLVES_ADDRESS", "USES_ADDRESS", "REFERENCES_ABI"}:
                continue
        if r.get("evidence_status") == "CONFIRMED" and r.get("analysis_mode") == "DETERMINISTIC":
            eids.append(r.get("evidence_id", ""))
    # also accept explicit contract update that removes blocker
    return (len(eids) > 0), [e for e in eids if e]


def _critical_edges_deterministic(path_edge_records: list[dict[str, Any]] | None) -> bool:
    """True when caller/address/signer-critical edges are DETERMINISTIC (or absent)."""
    if not path_edge_records:
        return True
    critical = [e for e in path_edge_records if e.get("edge_type") in STATIC_CRITICAL_EDGE_TYPES]
    if not critical:
        return True
    return all(e.get("analysis_mode") == "DETERMINISTIC" for e in critical)


def _apply_path_sot_clearance(
    gaps: list[dict[str, Any]],
    meta: dict[str, Any],
    sot_rec: dict[str, Any] | None,
    *,
    global_canonical_status: str = "UNRESOLVED",
    clearance_rec: dict[str, Any] | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Apply path-specific SoT + optional CC/SP clearance without requiring global canonical."""
    meta = dict(meta)
    meta["path_sot_record"] = sot_rec
    meta["path_clearance_record"] = clearance_rec
    meta["address_axes"] = address_axes_from_path_sot(sot_rec, global_canonical_status=global_canonical_status)
    meta["sot_status"] = sot_status_axis(sot_rec, global_canonical_status=global_canonical_status)
    meta["global_canonical_status"] = global_canonical_status

    gap_map = {g["gap_type"]: dict(g) for g in gaps}

    if path_sot_usable(sot_rec) and path_sot_conflict_cleared(sot_rec):
        # Path-usable dual-valid SoT satisfies address/deployment for THIS path.
        for gt in ("ADDRESS_SOURCE_PARTIAL", "GENERATED_CONFIG_DEPENDENCY", "GENERATED_CONFIG_PARTIAL"):
            if gt in gap_map:
                gap_map.pop(gt)
                meta["path_sot_cleared"] = list(dict.fromkeys((meta.get("path_sot_cleared") or []) + [gt]))
        # addresses.ts NOT_FOUND is informational when path SoT supplies usable bindings.
        # Do NOT clear signer/path-local NOT_FOUND (refinement NOT_FOUND_PRESERVED).
        if "NOT_FOUND_DEPENDENCY" in gap_map:
            nf = gap_map["NOT_FOUND_DEPENDENCY"]
            refinement = str(nf.get("refinement") or "")
            if refinement == "GENERATED_ARTIFACT_ABSENT" or (
                nf.get("root_cause") == "NOT_FOUND_DEPENDENCY"
                and "generated" in " ".join(nf.get("limitations") or []).lower()
            ):
                gap_map.pop("NOT_FOUND_DEPENDENCY")
                meta["path_sot_cleared"] = list(dict.fromkeys((meta.get("path_sot_cleared") or []) + ["NOT_FOUND_DEPENDENCY"]))
                meta["not_found_blocks"] = False
            elif refinement == "" and meta.get("not_found_root_evidence_ids"):
                # Prefer leaving unknown NOT_FOUND in place unless generated-config was also cleared
                if "GENERATED_CONFIG_DEPENDENCY" in (meta.get("path_sot_cleared") or []):
                    gap_map.pop("NOT_FOUND_DEPENDENCY")
                    meta["path_sot_cleared"] = list(dict.fromkeys((meta.get("path_sot_cleared") or []) + ["NOT_FOUND_DEPENDENCY"]))
                    meta["not_found_blocks"] = False
        meta["address_resolved"] = True
        meta["path_usable_address"] = True

    if path_sot_usable(sot_rec) and path_sot_conflict_cleared(sot_rec):
        if "PROVENANCE_CONFLICT" in gap_map:
            gap_map.pop("PROVENANCE_CONFLICT")
            meta["path_sot_cleared"] = list(dict.fromkeys((meta.get("path_sot_cleared") or []) + ["PROVENANCE_CONFLICT"]))
            meta["conflict_blocks"] = False
    elif clearance_rec and clearance_rec.get("conflict_cleared") and "PROVENANCE_CONFLICT" in gap_map:
        gap_map.pop("PROVENANCE_CONFLICT")
        meta["path_sot_cleared"] = list(dict.fromkeys((meta.get("path_sot_cleared") or []) + ["PROVENANCE_CONFLICT"]))
        meta["conflict_blocks"] = False

    if clearance_rec and clearance_rec.get("caller_chain_complete") and "CALLER_CHAIN_HEURISTIC" in gap_map:
        gap_map.pop("CALLER_CHAIN_HEURISTIC")
        meta["path_sot_cleared"] = list(dict.fromkeys((meta.get("path_sot_cleared") or []) + ["CALLER_CHAIN_HEURISTIC"]))
        meta["callgraph_resolved"] = True

    if clearance_rec and clearance_rec.get("signer_mechanism_cleared") and "SIGNER_SOURCE_PARTIAL" in gap_map:
        gap_map.pop("SIGNER_SOURCE_PARTIAL")
        meta["path_sot_cleared"] = list(dict.fromkeys((meta.get("path_sot_cleared") or []) + ["SIGNER_SOURCE_PARTIAL"]))

    if path_sot_usable(sot_rec) and not path_sot_static_target_resolved(sot_rec):
        gap_map["STATIC_TARGET_UNRESOLVED"] = {
            "gap_type": "STATIC_TARGET_UNRESOLVED",
            "severity_for_path": "BLOCKING",
            "limitations": [
                "path-specific SoT present but static target is an unlabeled multi-literal cluster",
            ],
            "evidence_ids": list((sot_rec or {}).get("evidence_references") or []),
            "refinement": "PATH_SOT_UNLABELED_CLUSTER",
            "analysis_mode": "DETERMINISTIC",
            "root_cause": "STATIC_TARGET_UNRESOLVED",
        }

    if sot_rec and not path_sot_conflict_cleared(sot_rec) and path_sot_usable(sot_rec):
        meta["conflict_blocks"] = True
        gap_map.setdefault("PROVENANCE_CONFLICT", {
            "gap_type": "PROVENANCE_CONFLICT",
            "severity_for_path": "BLOCKING",
            "limitations": ["path-specific SoT reports unresolved address/deployment conflict"],
            "evidence_ids": list(sot_rec.get("evidence_references") or []),
            "refinement": "PATH_SOT_CONFLICT",
            "analysis_mode": "DETERMINISTIC",
            "root_cause": "PROVENANCE_CONFLICT",
        })

    return list(gap_map.values()), meta


def _axis_statuses_for_path(
    *,
    static_status: str,
    c: dict[str, Any],
    gap_types: set[str],
    meta: dict[str, Any],
    runtime_execution_verified: bool = False,
) -> dict[str, str]:
    """Explicit multi-axis statuses. Independent of legacy aggregate consumers."""
    # STATIC_PATH_STATUS maps COMPLETE/PARTIAL/BROKEN; UNRESOLVED reserved for non-classified
    if static_status == "COMPLETE":
        static_axis = "COMPLETE"
    elif static_status == "BROKEN":
        static_axis = "UNRESOLVED"
    else:
        static_axis = "PARTIAL"

    if runtime_execution_verified:
        runtime_axis = "VERIFIED"
    else:
        runtime_axis = "UNVERIFIED"

    if "SIGNER_SOURCE_PARTIAL" in gap_types:
        signer_axis = "UNVERIFIED"
    else:
        # Mechanism may be known while exact EOA remains unresolved (separate axis).
        signer_axis = "DYNAMIC_BY_DESIGN_UNRESOLVED" if str(c.get("signer_source") or "").lower() in {
            "unknown signer source",
            "wallet",
            "user wallet",
            "frontend wallet",
        } or "wallet" in str(c.get("signer_source") or "").lower() else "PARTIAL"

    auth = c.get("authority_status")
    if auth == "CONFIRMED" and "AUTHORITY_CONDITION_PARTIAL" not in gap_types:
        authority_axis = "VERIFIED"
    elif auth == "PARTIAL" or "AUTHORITY_CONDITION_PARTIAL" in gap_types:
        authority_axis = "PARTIAL"
    else:
        authority_axis = "UNVERIFIED"

    return {
        "STATIC_PATH_STATUS": static_axis,
        "RUNTIME_EXECUTION_STATUS": runtime_axis,
        "SIGNER_IDENTITY_STATUS": signer_axis,
        "AUTHORITY_STATUS": authority_axis,
        "INDEPENDENT_WITNESS_STATUS": "NOT_SATISFIED",
        "SOT_STATUS": meta.get("sot_status") or "NOT_ESTABLISHED",
    }


def _signer_join_justifies_removal(matched: list[dict[str, Any]], updates: list[dict[str, Any]], join_mode: str) -> tuple[bool, list[str]]:
    """Remove SIGNER_SOURCE_PARTIAL only when deterministic CONFIRMED signer provenance justifies it."""
    if join_mode == "HEURISTIC":
        return False, []
    eids: list[str] = []
    for u in updates:
        if u.get("gap_type") != "SIGNER_SOURCE_PARTIAL":
            continue
        if u.get("removes_blocker") is True and u.get("evidence_status") == "CONFIRMED" and u.get("analysis_mode") == "DETERMINISTIC":
            eids.extend(u.get("evidence_ids") or [])
    for r in matched:
        if r.get("orphan_type") != "MUTATING_CALLSITE_SIGNER_REFINEMENTS":
            continue
        if r.get("relation_type") not in {"USES_SIGNER", "SIGNS_FOR"}:
            continue
        lim = " ".join(r.get("limitations") or [])
        if (
            r.get("evidence_status") == "CONFIRMED"
            and r.get("analysis_mode") == "DETERMINISTIC"
            and "removes_signer_blocker=YES" in lim
        ):
            eids.append(r.get("evidence_id", ""))
    eids = [e for e in eids if e]
    return (len(eids) > 0), eids


def _path_relevant_conflicts(
    idx: dict[str, Any],
    matched: list[dict[str, Any]],
    c: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Attach only conflicts with a supported subject/dependency relation to this path.

    Supported relations: subject_id, contract_name, contract instance / address source,
    generated artifact, file/symbol, callsite_id, chain_context (fail-closed on mismatch),
    path dependency ancestry (ADDRESS_CONSUMERS), explicit evidence-graph edge.

    Does NOT attach solely because target_commit matches or a conflict exists in-repo.
    Zero-source conflicts are preserved in the graph but excluded from path blocking.
    """
    if not idx.get("conflicts"):
        return []
    if c is None:
        # Legacy callers without path context: fail closed (no universal attach).
        return []
    path_scope = _path_conflict_scope(idx, c, matched)
    scopes = idx.get("conflict_scopes") or _build_conflict_scopes(idx)
    out: list[dict[str, Any]] = []
    for conf in idx["conflicts"]:
        eid = conf.get("evidence_id") or ""
        scope = scopes.get(eid) or {
            "conflict": conf,
            "source_ids": _conflict_source_ids(conf),
            "contracts": set(),
            "files": set(),
            "symbols": set(),
            "chains": set(),
            "callsite_ids": set(),
            "subject_ids": set(),
            "zero_source": len(_conflict_source_ids(conf)) == 0,
        }
        ok, _reason = _conflict_attaches_to_path(scope, path_scope, matched)
        if ok:
            out.append(conf)
    return out


def _queue_evidence_for_path(idx: dict[str, Any], c: dict[str, Any], matched: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for r in matched:
        if r.get("orphan_type") in {"QUEUE_STATES", "QUEUE_TRANSITIONS", "FAILURE_MODES", "CONCURRENCY_CONTROLS"} or r.get("subject_type") in {"QUEUE", "QUEUE_STATE"}:
            out.append(r)
    # attach global queue records that share file
    file = _norm_path(c.get("file") or "")
    for ot in ("QUEUE_STATES", "QUEUE_TRANSITIONS", "FAILURE_MODES", "CONCURRENCY_CONTROLS"):
        for r in idx["by_orphan"].get(ot, []):
            if file and _norm_path(r.get("source_file") or "") == file and r not in out:
                out.append(r)
    return out


def _mutating_evidence_for_path(matched: list[dict[str, Any]], c: dict[str, Any]) -> list[dict[str, Any]]:
    out = []
    cid = c.get("callsite_id") or ""
    for r in matched:
        if r.get("subject_type") == "CALLSITE" or r.get("callsite_id") == cid or r.get("orphan_type") in {
            "MUTATING_CALLSITES",
            "MUTATING_CALLSITE_ADDRESS_SOURCE_REFINEMENTS",
            "MUTATING_CALLSITE_SIGNER_REFINEMENTS",
            "ACTOR_GROUPS",
            "SIGNER_SOURCE_STATUS",
            "SIGNER_SOURCES",
            "CREDENTIAL_REFERENCES",
            "SIGNER_PROVENANCE_CHAINS",
            "SIGNER_AUTHORITY_SEPARATIONS",
            "CALLSITE_ANCESTRY_REFINEMENTS",
            "CALLGRAPH_EDGES",
            "CALLGRAPH_SIGNER_CONSUMER_LINKS",
        }:
            out.append(r)
    return out


def _callgraph_join_justifies_removal(matched: list[dict[str, Any]], updates: list[dict[str, Any]], join_mode: str) -> tuple[bool, list[str]]:
    """Clear CALLER_CHAIN_HEURISTIC only when deterministic CONFIRMED ancestry justifies it."""
    if join_mode == "HEURISTIC":
        return False, []
    eids: list[str] = []
    for u in updates:
        if u.get("gap_type") != "CALLER_CHAIN_HEURISTIC":
            continue
        if u.get("removes_blocker") is True and u.get("evidence_status") == "CONFIRMED" and u.get("analysis_mode") == "DETERMINISTIC":
            eids.extend(u.get("evidence_ids") or [])
    for r in matched:
        if r.get("orphan_type") != "CALLSITE_ANCESTRY_REFINEMENTS":
            continue
        lim = " ".join(r.get("limitations") or [])
        if (
            r.get("evidence_status") == "CONFIRMED"
            and r.get("analysis_mode") == "DETERMINISTIC"
            and "removes_caller_chain_blocker=YES" in lim
            and r.get("relation_type") != "REFINES_BLOCKER"
        ):
            eids.append(r.get("evidence_id", ""))
    eids = [e for e in eids if e]
    return (len(eids) > 0), eids


def _caller_chain_edge_modes(path_edge_records: list[dict[str, Any]]) -> list[str]:
    """Modes of edges that represent caller-chain continuity (not address/signer/tx/queue-state)."""
    # READS/UPDATES_QUEUE inherit queue-transition certainty; they are not pure caller-chain roots.
    caller_types = {"CALLS", "INVOKES", "DELEGATES_TO", "DISPATCHES_TO", "PROCESSES", "HANDLES", "SUBMITS_VIA"}
    return [e.get("analysis_mode", "HEURISTIC") for e in path_edge_records if e.get("edge_type") in caller_types]


def _has_callgraph_evidence(idx: dict[str, Any] | None) -> bool:
    if not idx:
        return False
    return bool(
        idx["by_orphan"].get("CALLSITE_ANCESTRY_REFINEMENTS")
        or idx["by_orphan"].get("CALLGRAPH_EDGES")
        or idx["by_orphan"].get("CALLGRAPH_NODES")
    )

def _refine_gaps_with_evidence(
    base_gaps: list[tuple[str, str]],
    c: dict[str, Any],
    idx: dict[str, Any] | None,
    sv: dict[str, Any],
    mc: dict[str, Any],
    path_edges_modes: list[str],
    path_edge_records: list[dict[str, Any]] | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Return refined gap dicts (without gap_id/path_id) and join metadata."""
    meta: dict[str, Any] = {
        "join_mode": "NONE",
        "evidence_refs": [],
        "queue_evidence_ids": [],
        "mutating_evidence_ids": [],
        "conflict_evidence_ids": [],
        "not_found_evidence_ids": [],
        "not_found_root_evidence_ids": [],
        "not_found_derived_evidence_ids": [],
        "address_resolved": False,
        "human_join_review": False,
        "conflict_blocks": False,
        "not_found_blocks": False,
        "callgraph_resolved": False,
    }
    gap_map: dict[str, dict[str, Any]] = {}
    for gt, sev in base_gaps:
        gap_map[gt] = {
            "gap_type": gt,
            "severity_for_path": sev,
            "limitations": ["static path gap; not a security severity"],
            "evidence_ids": [],
            "refinement": "",
            "analysis_mode": "HEURISTIC" if gt.endswith("PARTIAL") or gt.endswith("UNRESOLVED") else "DETERMINISTIC",
            "root_cause": gt,
        }

    if not idx:
        return list(gap_map.values()), meta

    matched, join_mode = _join_records_for_call(idx, c)
    meta["join_mode"] = join_mode
    meta["evidence_refs"] = [r.get("evidence_id") for r in matched if r.get("evidence_id")]
    if join_mode == "HEURISTIC":
        meta["human_join_review"] = True

    # Global artifact absence (preserved in graph); path attach is subject-scoped.
    addresses_absent_global, addr_nf_ids_global = _addresses_ts_not_found(idx, sv, mc)
    nf_attached, addresses_missing, nf_root_ids, nf_derived_ids = _path_relevant_not_found(idx, matched, c)
    # Legacy / no-scope fallback: if graph has no not_found list but sv/mc flags absence
    # and path depends on generated addresses, still block.
    if addresses_absent_global and not (idx.get("not_found") or []):
        dep, _ = _path_depends_on_addresses_ts(idx, c, matched)
        addresses_missing = dep
        if dep:
            nf_root_ids = list(addr_nf_ids_global)
    conflicts = _path_relevant_conflicts(idx, matched, c)
    relevant_conflict_eids = {x.get("evidence_id") for x in conflicts if x.get("evidence_id")}
    meta["conflict_evidence_ids"] = [x.get("evidence_id") for x in conflicts if x.get("evidence_id")]
    # Path-facing NOT_FOUND evidence: root ids for blocker summary; derived kept separately.
    meta["not_found_evidence_ids"] = list(dict.fromkeys(nf_root_ids))
    meta["not_found_derived_evidence_ids"] = list(dict.fromkeys(nf_derived_ids))
    meta["not_found_root_evidence_ids"] = list(dict.fromkeys(nf_root_ids))

    # Apply contract updates for this callsite + globals that refine known gaps
    updates = list(idx["updates_by_callsite"].get(c.get("callsite_id") or "", []))
    # Global generated/conflict/queue updates
    for u in idx["global_updates"]:
        if u.get("gap_type") in {
            "GENERATED_CONFIG_DEPENDENCY",
            "ADDRESS_SOURCE_CONFLICT",
            "QUEUE_STATE_DETAIL",
            "QUEUE_TRANSITION_DETAIL",
            "RETRY_PATH_PARTIAL",
            "CONCURRENCY_UNRESOLVED",
            "SIGNER_SOURCE_PARTIAL",
            "CALLER_CHAIN_HEURISTIC",
        }:
            updates.append(u)

    for u in updates:
        gt = u.get("gap_type") or ""
        # Map conflict type to PROVENANCE_CONFLICT only when subject-scoped attach applies.
        if gt == "ADDRESS_SOURCE_CONFLICT":
            eids = set(u.get("evidence_ids") or [])
            if not (eids & relevant_conflict_eids):
                continue
            gt = "PROVENANCE_CONFLICT"
        if gt in {"QUEUE_STATE_DETAIL", "QUEUE_TRANSITION_DETAIL"}:
            # attach as evidence refinement, not a new blocker unless already present
            meta["queue_evidence_ids"].extend(u.get("evidence_ids") or [])
            continue
        if gt == "GENERATED_CONFIG_DEPENDENCY":
            # Only inherit global generated-config NOT_FOUND when path depends on addresses.ts.
            if addresses_missing and ((u.get("evidence_status") == "NOT_FOUND") or addresses_absent_global):
                meta["not_found_derived_evidence_ids"].extend(u.get("evidence_ids") or [])
            else:
                # Do not globally force addresses_missing / GENERATED_CONFIG onto unrelated paths.
                continue
        if gt not in gap_map and gt not in {"ADDRESS_SOURCE_PARTIAL", "SIGNER_SOURCE_PARTIAL", "RETRY_PATH_PARTIAL", "CONCURRENCY_UNRESOLVED", "GENERATED_CONFIG_DEPENDENCY", "PROVENANCE_CONFLICT", "NOT_FOUND_DEPENDENCY", "ABI_LINK_PARTIAL", "CALLER_CHAIN_HEURISTIC", "GENERATED_CONFIG_PARTIAL", "QUEUE_RETRY_PARTIAL", "CONCURRENCY_PARTIAL"}:
            continue
        if gt in gap_map:
            gap_map[gt]["evidence_ids"] = list(dict.fromkeys((gap_map[gt].get("evidence_ids") or []) + (u.get("evidence_ids") or [])))
            gap_map[gt]["refinement"] = u.get("refinement") or gap_map[gt].get("refinement") or ""
            if u.get("analysis_mode"):
                gap_map[gt]["analysis_mode"] = u["analysis_mode"]
        elif gt in {"PROVENANCE_CONFLICT", "NOT_FOUND_DEPENDENCY", "ABI_LINK_PARTIAL", "CALLER_CHAIN_HEURISTIC", "GENERATED_CONFIG_PARTIAL", "QUEUE_RETRY_PARTIAL", "CONCURRENCY_PARTIAL"}:
            gap_map[gt] = {
                "gap_type": gt,
                "severity_for_path": "NON_BLOCKING",
                "limitations": ["static path gap; not a security severity"],
                "evidence_ids": list(u.get("evidence_ids") or []),
                "refinement": u.get("refinement") or "",
                "analysis_mode": u.get("analysis_mode") or "DETERMINISTIC",
                "root_cause": gt,
            }

    # Drop base-gap GENERATED_CONFIG when path does not depend on addresses.ts.
    if not addresses_missing:
        gap_map.pop("GENERATED_CONFIG_DEPENDENCY", None)
        gap_map.pop("GENERATED_CONFIG_PARTIAL", None)

    # Address evidence consumption
    addr_recs = [
        r for r in matched
        if r.get("orphan_type") in {"MUTATING_CALLSITE_ADDRESS_SOURCE_REFINEMENTS", "ADDRESS_SOURCES", "ADDRESS_CONSUMERS", "PROVENANCE_CHAINS"}
        or r.get("relation_type") in {"RESOLVES_ADDRESS", "USES_ADDRESS"}
    ]
    remove_addr, addr_eids = _address_join_justifies_removal(matched, join_mode, bool(conflicts), addresses_missing)
    # Explicit removes_blocker=true from contract also honored when status CONFIRMED+DETERMINISTIC
    for u in updates:
        if u.get("gap_type") == "ADDRESS_SOURCE_PARTIAL" and u.get("removes_blocker") is True:
            if u.get("evidence_status") == "CONFIRMED" and u.get("analysis_mode") == "DETERMINISTIC" and not conflicts and not addresses_missing:
                remove_addr = True
                addr_eids = list(dict.fromkeys(addr_eids + (u.get("evidence_ids") or [])))
    if remove_addr and "ADDRESS_SOURCE_PARTIAL" in gap_map:
        del gap_map["ADDRESS_SOURCE_PARTIAL"]
        meta["address_resolved"] = True
        meta["evidence_refs"] = list(dict.fromkeys(meta["evidence_refs"] + addr_eids))
    elif addr_recs and "ADDRESS_SOURCE_PARTIAL" in gap_map:
        gap_map["ADDRESS_SOURCE_PARTIAL"]["evidence_ids"] = list(dict.fromkeys(
            (gap_map["ADDRESS_SOURCE_PARTIAL"].get("evidence_ids") or []) + [r.get("evidence_id") for r in addr_recs if r.get("evidence_id")]
        ))
        gap_map["ADDRESS_SOURCE_PARTIAL"]["refinement"] = "STATIC_ADDRESS_PROVENANCE_LINKED"
        # PARTIAL evidence must not clear blocker
        modes = {r.get("analysis_mode") for r in addr_recs}
        statuses = {r.get("evidence_status") for r in addr_recs}
        if "HEURISTIC" in modes or statuses & {"PARTIAL", "UNKNOWN", "NOT_FOUND", "CONFLICT"}:
            gap_map["ADDRESS_SOURCE_PARTIAL"]["analysis_mode"] = "HEURISTIC" if "HEURISTIC" in modes else "DETERMINISTIC"

    # Signer evidence consumption — clear only when justified
    signer_recs = [
        r for r in matched
        if r.get("orphan_type") in {
            "MUTATING_CALLSITE_SIGNER_REFINEMENTS",
            "SIGNER_SOURCES",
            "CREDENTIAL_REFERENCES",
            "SIGNER_PROVENANCE_CHAINS",
            "SIGNER_SOURCE_STATUS",
        }
        or r.get("relation_type") in {"USES_SIGNER", "SIGNS_FOR", "READS", "PROVIDES"}
    ]
    remove_signer, signer_eids = _signer_join_justifies_removal(matched, updates, join_mode)
    for u in updates:
        if u.get("gap_type") == "SIGNER_SOURCE_PARTIAL" and u.get("removes_blocker") is True:
            if u.get("evidence_status") == "CONFIRMED" and u.get("analysis_mode") == "DETERMINISTIC":
                remove_signer = True
                signer_eids = list(dict.fromkeys(signer_eids + (u.get("evidence_ids") or [])))
    # Do not clear if dedicated signer provenance is NOT_FOUND for this callsite.
    # Shallow mutating SIGNER_SOURCE_STATUS NOT_FOUND is superseded by dedicated
    # MUTATING_CALLSITE_SIGNER_REFINEMENTS when that refinement is CONFIRMED+DETERMINISTIC.
    signer_not_found = any(
        r.get("evidence_status") == "NOT_FOUND"
        and r.get("orphan_type") == "MUTATING_CALLSITE_SIGNER_REFINEMENTS"
        and r.get("relation_type") in {"NOT_FOUND_FOR", "USES_SIGNER"}
        for r in matched
    )
    if signer_not_found:
        remove_signer = False
    if remove_signer and "SIGNER_SOURCE_PARTIAL" in gap_map:
        del gap_map["SIGNER_SOURCE_PARTIAL"]
        meta["evidence_refs"] = list(dict.fromkeys(meta["evidence_refs"] + signer_eids))
    elif signer_recs and "SIGNER_SOURCE_PARTIAL" in gap_map:
        gap_map["SIGNER_SOURCE_PARTIAL"]["evidence_ids"] = list(dict.fromkeys(
            (gap_map["SIGNER_SOURCE_PARTIAL"].get("evidence_ids") or [])
            + [r.get("evidence_id") for r in signer_recs if r.get("evidence_id")]
        ))
        gap_map["SIGNER_SOURCE_PARTIAL"]["refinement"] = "STATIC_SIGNER_PROVENANCE_LINKED"
        modes = {r.get("analysis_mode") for r in signer_recs}
        statuses = {r.get("evidence_status") for r in signer_recs}
        if "HEURISTIC" in modes or statuses & {"PARTIAL", "UNKNOWN", "NOT_FOUND", "CONFLICT"}:
            gap_map["SIGNER_SOURCE_PARTIAL"]["analysis_mode"] = "HEURISTIC" if "HEURISTIC" in modes else "DETERMINISTIC"

    # Generated config / addresses.ts — subject-scoped; root vs derived separated.
    if addresses_missing:
        meta["not_found_blocks"] = True
        root_eids = list(dict.fromkeys(meta["not_found_root_evidence_ids"] or meta["not_found_evidence_ids"]))
        if not root_eids and addr_nf_ids_global:
            # Preserve root absence evidence even when only derived rows matched.
            root_eids = [
                e for e in addr_nf_ids_global
                if any(
                    (_not_found_category(r) == "ROOT_GENERATED_ARTIFACT" and r.get("evidence_id") == e)
                    for r in (idx.get("not_found") or [])
                )
            ] or list(dict.fromkeys(addr_nf_ids_global[:1]))
        derived_eids = list(dict.fromkeys(meta.get("not_found_derived_evidence_ids") or []))
        meta["not_found_evidence_ids"] = list(dict.fromkeys(root_eids))
        nf_gap = {
            "gap_type": "NOT_FOUND_DEPENDENCY",
            "severity_for_path": "NON_BLOCKING",
            "limitations": [
                "addresses.ts absent or NOT_FOUND; example file does not imply generated output exists",
                "root_not_found_subject=client/src/abi/addresses.ts",
            ],
            "evidence_ids": root_eids,
            "refinement": "GENERATED_ARTIFACT_ABSENT",
            "analysis_mode": "DETERMINISTIC",
            "root_cause": "NOT_FOUND_DEPENDENCY",
            "derived_evidence_ids": derived_eids,
        }
        gap_map["NOT_FOUND_DEPENDENCY"] = nf_gap
        if "GENERATED_CONFIG_DEPENDENCY" not in gap_map:
            gap_map["GENERATED_CONFIG_DEPENDENCY"] = {
                "gap_type": "GENERATED_CONFIG_DEPENDENCY",
                "severity_for_path": "NON_BLOCKING",
                "limitations": [
                    "static path gap; not a security severity",
                    "derived_from_root=NOT_FOUND_DEPENDENCY",
                ],
                "evidence_ids": derived_eids or root_eids,
                "refinement": "GENERATED_CONFIG_PARTIAL",
                "analysis_mode": "DETERMINISTIC",
                "root_cause": "NOT_FOUND_DEPENDENCY",
            }
        else:
            gap_map["GENERATED_CONFIG_DEPENDENCY"]["evidence_ids"] = list(dict.fromkeys(
                (gap_map["GENERATED_CONFIG_DEPENDENCY"].get("evidence_ids") or []) + (derived_eids or root_eids)
            ))
            gap_map["GENERATED_CONFIG_DEPENDENCY"]["refinement"] = "GENERATED_CONFIG_PARTIAL"
            gap_map["GENERATED_CONFIG_DEPENDENCY"]["root_cause"] = "NOT_FOUND_DEPENDENCY"
            gap_map["GENERATED_CONFIG_DEPENDENCY"]["limitations"] = list(dict.fromkeys(
                (gap_map["GENERATED_CONFIG_DEPENDENCY"].get("limitations") or [])
                + ["derived_from_root=NOT_FOUND_DEPENDENCY"]
            ))
        # Deduplicate: drop GENERATED_CONFIG_PARTIAL alias if we use DEPENDENCY + NOT_FOUND
        gap_map.pop("GENERATED_CONFIG_PARTIAL", None)

    # Conflicts — subject-scoped only; never leave a global PROVENANCE_CONFLICT residue
    if conflicts:
        meta["conflict_blocks"] = True
        gap_map["PROVENANCE_CONFLICT"] = {
            "gap_type": "PROVENANCE_CONFLICT",
            "severity_for_path": "NON_BLOCKING",
            "limitations": ["static provenance conflict preserved; not collapsed"],
            "evidence_ids": meta["conflict_evidence_ids"],
            "refinement": "STATIC_CONFLICT_PRESERVED",
            "analysis_mode": "DETERMINISTIC",
            "root_cause": "PROVENANCE_CONFLICT",
        }
    else:
        meta["conflict_blocks"] = False
        gap_map.pop("PROVENANCE_CONFLICT", None)

    # ABI link partial
    abi_recs = [r for r in matched if r.get("orphan_type") == "ABI_ADDRESS_LINKS" or r.get("relation_type") == "REFERENCES_ABI"]
    if not abi_recs:
        abi_recs = [r for r in idx["by_orphan"].get("ABI_ADDRESS_LINKS", []) if r.get("evidence_status") in {"PARTIAL", "NOT_FOUND", "UNKNOWN"}][:1]
    if abi_recs and any(r.get("evidence_status") != "CONFIRMED" for r in abi_recs):
        # Only add if address path still relevant
        gap_map["ABI_LINK_PARTIAL"] = {
            "gap_type": "ABI_LINK_PARTIAL",
            "severity_for_path": "INFORMATIONAL",
            "limitations": ["ABI/address linkage incomplete; static only"],
            "evidence_ids": [r.get("evidence_id") for r in abi_recs if r.get("evidence_id")][:5],
            "refinement": "ABI_ADDRESS_LINK_ATTACHED",
            "analysis_mode": "HEURISTIC" if any(r.get("analysis_mode") == "HEURISTIC" for r in abi_recs) else "DETERMINISTIC",
            "root_cause": "ABI_LINK_PARTIAL",
        }

    # Queue evidence attachment (refine naming without inventing dynamic verification)
    q_recs = _queue_evidence_for_path(idx, c, matched)
    meta["queue_evidence_ids"] = list(dict.fromkeys(meta["queue_evidence_ids"] + [r.get("evidence_id") for r in q_recs if r.get("evidence_id")]))
    if "RETRY_PATH_PARTIAL" in gap_map and meta["queue_evidence_ids"]:
        gap_map["RETRY_PATH_PARTIAL"]["refinement"] = "QUEUE_EVIDENCE_NORMALIZED"
        gap_map["RETRY_PATH_PARTIAL"]["evidence_ids"] = list(dict.fromkeys(
            (gap_map["RETRY_PATH_PARTIAL"].get("evidence_ids") or []) + meta["queue_evidence_ids"][:8]
        ))
    if "CONCURRENCY_UNRESOLVED" in gap_map and meta["queue_evidence_ids"]:
        gap_map["CONCURRENCY_UNRESOLVED"]["refinement"] = "QUEUE_EVIDENCE_NORMALIZED"
        gap_map["CONCURRENCY_UNRESOLVED"]["evidence_ids"] = list(dict.fromkeys(
            (gap_map["CONCURRENCY_UNRESOLVED"].get("evidence_ids") or []) + meta["queue_evidence_ids"][:8]
        ))

    # Mutating callsite evidence
    m_recs = _mutating_evidence_for_path(matched, c)
    meta["mutating_evidence_ids"] = [r.get("evidence_id") for r in m_recs if r.get("evidence_id")]

    # Caller-chain heuristic — when callgraph evidence exists, attribute only to true
    # caller-chain uncertainty (not address / submits_transaction / signer heuristics).
    cg_recs = [
        r for r in matched
        if r.get("orphan_type") in {
            "CALLSITE_ANCESTRY_REFINEMENTS",
            "CALLGRAPH_EDGES",
            "CALLGRAPH_NODES",
            "CALLGRAPH_SIGNER_CONSUMER_LINKS",
        }
    ]
    remove_cch, cch_eids = _callgraph_join_justifies_removal(matched, updates, join_mode)
    for u in updates:
        if u.get("gap_type") == "CALLER_CHAIN_HEURISTIC" and u.get("removes_blocker") is True:
            if u.get("evidence_status") == "CONFIRMED" and u.get("analysis_mode") == "DETERMINISTIC":
                remove_cch = True
                cch_eids = list(dict.fromkeys(cch_eids + (u.get("evidence_ids") or [])))

    has_cg = _has_callgraph_evidence(idx) or bool(cg_recs)
    if has_cg:
        caller_modes = _caller_chain_edge_modes(path_edge_records or [])
        ancestry_heu = any(
            r.get("orphan_type") == "CALLSITE_ANCESTRY_REFINEMENTS"
            and r.get("analysis_mode") == "HEURISTIC"
            and r.get("relation_type") != "REFINES_BLOCKER"
            for r in (cg_recs + matched)
        )
        need_cch = (
            join_mode == "HEURISTIC"
            or ancestry_heu
            or any(m == "HEURISTIC" for m in caller_modes)
            or (
                not remove_cch
                and not any(
                    r.get("orphan_type") == "CALLSITE_ANCESTRY_REFINEMENTS"
                    and r.get("analysis_mode") == "DETERMINISTIC"
                    and "removes_caller_chain_blocker=YES" in " ".join(r.get("limitations") or [])
                    for r in matched
                )
                and not caller_modes
            )
        )
        if need_cch and not remove_cch:
            gap_map["CALLER_CHAIN_HEURISTIC"] = {
                "gap_type": "CALLER_CHAIN_HEURISTIC",
                "severity_for_path": "NON_BLOCKING",
                "limitations": ["caller chain ancestry is heuristic or unresolved; not dynamically verified"],
                "evidence_ids": list(dict.fromkeys(
                    [r.get("evidence_id") for r in cg_recs if r.get("evidence_id")][:5]
                    + (meta["mutating_evidence_ids"][:3])
                )),
                "refinement": "CALLGRAPH_HEURISTIC_OR_MISSING",
                "analysis_mode": "HEURISTIC",
                "root_cause": "CALLER_CHAIN_HEURISTIC",
            }
            meta["human_join_review"] = True
        elif remove_cch:
            if "CALLER_CHAIN_HEURISTIC" in gap_map:
                del gap_map["CALLER_CHAIN_HEURISTIC"]
            meta["evidence_refs"] = list(dict.fromkeys(meta["evidence_refs"] + cch_eids))
            meta["callgraph_resolved"] = True
        else:
            if "CALLER_CHAIN_HEURISTIC" in gap_map:
                del gap_map["CALLER_CHAIN_HEURISTIC"]
            meta["callgraph_resolved"] = True
    else:
        # Legacy (no callgraph producer): any heuristic path edge or heuristic join → CCH
        if any(m == "HEURISTIC" for m in path_edges_modes) or join_mode == "HEURISTIC":
            gap_map["CALLER_CHAIN_HEURISTIC"] = {
                "gap_type": "CALLER_CHAIN_HEURISTIC",
                "severity_for_path": "NON_BLOCKING",
                "limitations": ["caller chain or evidence join is heuristic; not dynamically verified"],
                "evidence_ids": meta["mutating_evidence_ids"][:5],
                "refinement": "HEURISTIC_JOIN_OR_EDGE",
                "analysis_mode": "HEURISTIC",
                "root_cause": "CALLER_CHAIN_HEURISTIC",
            }
            meta["human_join_review"] = True

    # Other subject-scoped NOT_FOUND (signer / path-local) — do not convert to UNKNOWN
    for r in nf_attached:
        cat = _not_found_category(r)
        eid = r.get("evidence_id")
        if not eid:
            continue
        if cat in {"ROOT_GENERATED_ARTIFACT", "DERIVED_GENERATED_CONFIG"}:
            continue  # already handled via addresses_missing
        if eid in meta["not_found_evidence_ids"]:
            continue
        if cat == "SIGNER":
            meta["not_found_evidence_ids"].append(eid)
            meta["not_found_blocks"] = True
            if "SIGNER_SOURCE_PARTIAL" in gap_map:
                gap_map["SIGNER_SOURCE_PARTIAL"]["evidence_ids"] = list(dict.fromkeys(
                    (gap_map["SIGNER_SOURCE_PARTIAL"].get("evidence_ids") or []) + [eid]
                ))
                gap_map["SIGNER_SOURCE_PARTIAL"]["refinement"] = "NOT_FOUND_PRESERVED"
        else:
            meta["not_found_evidence_ids"].append(eid)
            meta["not_found_blocks"] = True

    if meta["not_found_blocks"] and "NOT_FOUND_DEPENDENCY" not in gap_map:
        gap_map["NOT_FOUND_DEPENDENCY"] = {
            "gap_type": "NOT_FOUND_DEPENDENCY",
            "severity_for_path": "NON_BLOCKING",
            "limitations": ["NOT_FOUND evidence preserved; not converted to UNKNOWN"],
            "evidence_ids": list(dict.fromkeys(meta["not_found_evidence_ids"])),
            "refinement": "NOT_FOUND_PRESERVED",
            "analysis_mode": "DETERMINISTIC",
            "root_cause": "NOT_FOUND_DEPENDENCY",
        }

    # Deduplicate derived gaps sharing the same root_cause when NOT_FOUND explains generated config:
    # keep both for metric continuity but mark root_cause; do not add GENERATED_CONFIG_PARTIAL duplicate.
    return list(gap_map.values()), meta


def _completion_blocked(
    gap_types: set[str],
    all_det: bool,
    receipt: str,
    local: str,
    meta: dict[str, Any],
    path_edge_records: list[dict[str, Any]] | None = None,
) -> bool:
    """Decide whether STATIC_PATH_COMPLETE is blocked.

    Legacy signature retained (all_det/receipt/local) for call-site compatibility.
    Semantics (STATIC_PATH_COMPLETE_v1):
      - Blocks on unresolved static evidence gaps in STATIC_COMPLETION_BLOCKING
      - Does NOT block on AUTHORITY / INFORMATIONAL retry-concurrency-ABI alone
      - Does NOT require runtime execution, exact signer identity, IW, or global canonical
      - Does NOT require universal local==YES
      - receipt retained only as informational; does not veto static completion
      - critical caller/address/signer edges must be DETERMINISTIC (not all incidental edges)
    """
    _ = (all_det, receipt, local)  # retained; no longer universal COMPLETE gates
    blocking_hits = gap_types & STATIC_COMPLETION_BLOCKING
    if blocking_hits:
        return True
    if meta.get("conflict_blocks") or meta.get("not_found_blocks"):
        # Path-SoT may have cleared these flags; if still set, block.
        return True
    if meta.get("join_mode") == "HEURISTIC" and not meta.get("path_usable_address"):
        return True
    if path_edge_records is not None:
        if not _critical_edges_deterministic(path_edge_records):
            return True
    elif not all_det:
        # Legacy callers without edge records: keep all_det as stand-in for critical certainty
        # only when no path-SoT established (conservative).
        if not meta.get("path_usable_address"):
            return True
    return False


def _legacy_static_gaps_block(path_gap_types: list[tuple[str, str]]) -> bool:
    """Legacy (no graph) static-completion gap filter."""
    types = {gt for gt, _sev in path_gap_types}
    return bool(types & STATIC_COMPLETION_BLOCKING)


def synthesize_runtime_paths_v0(req: dict[str, Any]) -> dict[str, Any]:
    r = base(req if isinstance(req, dict) else {})
    err = _check(req, r)
    if err:
        r["reason_codes"].append(err)
        r["result_id"] = rid(r)
        return r
    sv = req["source_verifier_result"]
    ri = req["runtime_inventory_result"]
    mc = req["mutating_callsite_result"]
    qs = req["queue_state_transition_result"]
    graph = req.get("static_evidence_graph")
    idx = _index_evidence_graph(graph if isinstance(graph, dict) else None)
    path_sot_bundle = req.get("path_specific_sot_evidence")
    path_sot_index = index_path_sot(path_sot_bundle if isinstance(path_sot_bundle, dict) else None)
    clearance_bundle = req.get("path_static_clearance_overlay")
    clearance_index = index_path_clearance(clearance_bundle if isinstance(clearance_bundle, dict) else None)
    global_canonical_status = "UNRESOLVED"
    if isinstance(path_sot_bundle, dict):
        global_canonical_status = str(path_sot_bundle.get("global_canonical_status") or "UNRESOLVED")
        r["summary"]["path_specific_sot_consumed"] = "YES"
        r["summary"]["path_specific_sot_records"] = len(path_sot_index)
        r["summary"]["global_canonical_status"] = global_canonical_status
        r["limitations"].append(
            "path-specific SoT overlay consumed; global canonical family not required for STATIC_PATH_COMPLETE"
        )
    else:
        r["summary"]["path_specific_sot_consumed"] = "NO"
        r["summary"]["global_canonical_status"] = global_canonical_status
    if clearance_index:
        r["summary"]["path_static_clearance_consumed"] = "YES"
        r["summary"]["path_static_clearance_records"] = len(clearance_index)
        r["limitations"].append("path static clearance overlay consumed for caller/signer/conflict axes")
    else:
        r["summary"]["path_static_clearance_consumed"] = "NO"
    if idx:
        r["summary"]["evidence_graph_consumed"] = "YES"
        r["limitations"].append("static evidence graph consumed; refinements do not prove runtime execution")
    nodes = {"items": [], "_idx": {}}
    edges: list[dict[str, Any]] = []
    paths: list[dict[str, Any]] = []
    gaps: list[dict[str, Any]] = []
    qmodels = qs.get("queue_models", [])
    trans = qs.get("transitions", [])
    calls = mc.get("callsite_results", [])
    signer_surfaces = [s for s in ri.get("surface_results", []) if s.get("category") == "signer_private_key_loading" and s.get("evidence_status") in {"CONFIRMED", "PARTIAL"}]
    provider_surfaces = [s for s in ri.get("surface_results", []) if s.get("category") == "rpc_provider_initialization" and s.get("evidence_status") in {"CONFIRMED", "PARTIAL"}]
    receipt_surfaces = [s for s in ri.get("surface_results", []) if s.get("category") == "receipt_confirmation" and s.get("evidence_status") in {"CONFIRMED", "PARTIAL"}]
    failure_surfaces = [s for s in ri.get("surface_results", []) if s.get("category") in {"failure_error_handling", "retry_logic"} and s.get("evidence_status") in {"CONFIRMED", "PARTIAL"}]

    for exp in req.get("expected_paths", []) or []:
        if not calls:
            pid = f"wrps-v0-p{len(paths)+1:04d}"
            paths.append({
                "path_id": pid,
                "path_name": exp.get("path_name", "expected path"),
                "actor_role": exp.get("actor_role", "unknown"),
                "entry_node": "",
                "terminal_node": "",
                "nodes": [],
                "edges": [],
                "path_status": "BROKEN",
                "static_continuity": "NO",
                "transaction_submission_present": "NO",
                "receipt_handling_present": "UNKNOWN",
                "local_state_update_present": "UNKNOWN",
                "failure_path_present": "UNKNOWN",
                "authority_condition_known": "NO",
                "runtime_execution_verified": False,
                "human_review_required": "YES",
                "evidence_refs": [],
                "static_evidence_join_mode": "NONE",
                "limitations": ["expected path could not be connected from supplied static evidence"],
                "STATIC_PATH_STATUS": "UNRESOLVED",
                "RUNTIME_EXECUTION_STATUS": "UNVERIFIED",
                "SIGNER_IDENTITY_STATUS": "UNVERIFIED",
                "AUTHORITY_STATUS": "UNVERIFIED",
                "INDEPENDENT_WITNESS_STATUS": "NOT_SATISFIED",
                "SOT_STATUS": "NOT_ESTABLISHED",
                "address_axes": address_axes_from_path_sot(None, global_canonical_status=global_canonical_status),
            })
            gaps.append({
                "gap_id": f"wrps-v0-g{len(gaps)+1:04d}",
                "path_id": pid,
                "gap_type": "CALLER_CHAIN_UNRESOLVED",
                "severity_for_path": "BLOCKING",
                "limitations": ["no source-connected callsite evidence"],
                "evidence_ids": [],
                "refinement": "",
                "analysis_mode": "DETERMINISTIC",
                "root_cause": "CALLER_CHAIN_UNRESOLVED",
            })

    selected = calls
    max_paths = req.get("max_paths")
    if isinstance(max_paths, int) and max_paths > 0:
        selected = selected[:max_paths]

    for c in selected:
        file = c.get("file", "")
        line = c.get("line_start")
        role = c.get("actor_role", "unknown")
        method = c.get("target_method") or c.get("symbol") or "transaction"
        pid = f"wrps-v0-p{len(paths)+1:04d}"
        path_nodes: list[str] = []
        path_edges: list[str] = []
        matching_trans = [t for t in trans if t.get("file") == file or ("ValidatorService" in file and "ValidatorService" in t.get("file", ""))]
        if qmodels and ("validator" in role.lower() or "archive" in role.lower() or "ValidatorService" in file):
            qm = qmodels[0]
            qn = _node(nodes, "queue/model", qm.get("file"), qm.get("line_start"), qm.get("line_end"), qm.get("symbol") or qm.get("model_name"), "queue-state-transition-analyzer", qm.get("analysis_mode", "DETERMINISTIC"), qm.get("evidence_status", "CONFIRMED"), qm.get("source_origin", "WORKTREE"))
            path_nodes.append(qn)
        else:
            qn = ""
        sn = _node(nodes, "service method" if "frontend" not in role.lower() else "controller/API entrypoint", file, line, c.get("line_end"), c.get("caller_symbol") or c.get("symbol"), "mutating-callsite-analyzer", c.get("analysis_mode", "HEURISTIC"), c.get("evidence_status", "PARTIAL"), c.get("source_origin", "WORKTREE"))
        path_nodes.append(sn)
        if qn:
            if matching_trans:
                ev = matching_trans[0]
                path_edges.append(_edge(edges, qn, sn, "READS", ev.get("file"), ev.get("line_start"), ev.get("line_end"), ev.get("analysis_mode", "DETERMINISTIC"), ev.get("evidence_status", "CONFIRMED"), "HIGH"))
            else:
                # Prefer deterministic callgraph PROCESSES/HANDLES linkage when available
                cg_mode, cg_status, cg_file, cg_ls, cg_le = "HEURISTIC", "PARTIAL", file, line, c.get("line_end")
                if idx:
                    matched_pre, _join_pre = _join_records_for_call(idx, c)
                    proc = [
                        x for x in matched_pre
                        if x.get("orphan_type") in {"CALLSITE_ANCESTRY_REFINEMENTS", "CALLGRAPH_EDGES"}
                        and x.get("relation_type") in {"PROCESSES", "HANDLES", "CALLS", "INVOKES"}
                        and x.get("analysis_mode") == "DETERMINISTIC"
                        and x.get("evidence_status") == "CONFIRMED"
                    ]
                    if proc:
                        cg_mode, cg_status = "DETERMINISTIC", "CONFIRMED"
                        cg_file = proc[0].get("source_file") or file
                        cg_ls = proc[0].get("line_start") or line
                        cg_le = proc[0].get("line_end") or c.get("line_end")
                path_edges.append(_edge(edges, qn, sn, "CALLS" if cg_mode == "HEURISTIC" else "PROCESSES", cg_file, cg_ls, cg_le, cg_mode, cg_status, "HIGH" if cg_mode == "DETERMINISTIC" else "MEDIUM"))
        if signer_surfaces or c.get("signer_source") != "unknown signer source":
            ss = signer_surfaces[0] if signer_surfaces else c
            signer = _node(nodes, "signer/key acquisition", ss.get("file", file), ss.get("line_start", line), ss.get("line_end", line), c.get("signer_source") or ss.get("symbol"), "runtime-surface-inventory" if signer_surfaces else "mutating-callsite-analyzer", ss.get("analysis_mode", "DETERMINISTIC"), ss.get("evidence_status", "PARTIAL"), ss.get("source_origin", "WORKTREE"))
            path_nodes.append(signer)
            path_edges.append(_edge(edges, sn, signer, "RESOLVES_SIGNER", ss.get("file", file), ss.get("line_start", line), ss.get("line_end", line), ss.get("analysis_mode", "DETERMINISTIC"), ss.get("evidence_status", "PARTIAL"), "HIGH" if ss.get("analysis_mode") == "DETERMINISTIC" else "MEDIUM"))
        else:
            signer = ""
        if provider_surfaces:
            ps = provider_surfaces[0]
            pn = _node(nodes, "provider/RPC acquisition", ps.get("file"), ps.get("line_start"), ps.get("line_end"), ps.get("symbol"), "runtime-surface-inventory", ps.get("analysis_mode"), ps.get("evidence_status"), ps.get("source_origin"))
            path_nodes.append(pn)
            path_edges.append(_edge(edges, sn, pn, "DEPENDS_ON", ps.get("file"), ps.get("line_start"), ps.get("line_end"), ps.get("analysis_mode"), ps.get("evidence_status"), "HIGH"))

        # Address resolution — prefer graph-backed status when available
        address_status = "PARTIAL" if c.get("contract_address_source") in {"unknown", ""} or mc.get("contract_address_sources_mapped") != "YES" else "CONFIRMED"
        address_mode = "HEURISTIC" if address_status == "PARTIAL" else "DETERMINISTIC"
        address_symbol = c.get("contract_address_source", "unknown")
        if idx:
            matched_pre, join_pre = _join_records_for_call(idx, c)
            addr_recs = [
                x for x in matched_pre
                if x.get("orphan_type") in {"MUTATING_CALLSITE_ADDRESS_SOURCE_REFINEMENTS", "ADDRESS_SOURCES"}
                or x.get("relation_type") == "RESOLVES_ADDRESS"
            ]
            if addr_recs:
                # Never promote PARTIAL → CONFIRMED
                if all(x.get("evidence_status") == "CONFIRMED" and x.get("analysis_mode") == "DETERMINISTIC" for x in addr_recs):
                    addresses_absent_global, _ = _addresses_ts_not_found(idx, sv, mc)
                    addresses_dep, _ = _path_depends_on_addresses_ts(idx, c, matched_pre)
                    addresses_missing = bool(addresses_absent_global and addresses_dep)
                    if not addresses_missing and not idx["conflicts"]:
                        address_status = "CONFIRMED"
                        address_mode = "DETERMINISTIC"
                    else:
                        address_status = "PARTIAL"
                        address_mode = "DETERMINISTIC" if join_pre == "DETERMINISTIC" else "HEURISTIC"
                else:
                    address_status = "PARTIAL"
                    address_mode = "HEURISTIC" if any(x.get("analysis_mode") == "HEURISTIC" for x in addr_recs) else "DETERMINISTIC"
                to_ent = (addr_recs[0].get("to_entity") or {})
                if to_ent.get("entity_id"):
                    address_symbol = to_ent.get("entity_id")
        sot_rec_pre = path_sot_index.get(pid)
        if path_sot_usable(sot_rec_pre) and path_sot_conflict_cleared(sot_rec_pre):
            address_status = "CONFIRMED" if path_sot_static_target_resolved(sot_rec_pre) else "PARTIAL"
            address_mode = "DETERMINISTIC"
            address_symbol = (sot_rec_pre or {}).get("target_contract_role") or address_symbol
        an = _node(nodes, "contract/address resolution", file, line, c.get("line_end"), address_symbol, "static-evidence-graph" if idx else "mutating-callsite-analyzer", address_mode, address_status, c.get("source_origin", "WORKTREE"))
        path_nodes.append(an)
        path_edges.append(_edge(edges, sn, an, "RESOLVES_ADDRESS", file, line, c.get("line_end"), address_mode, address_status, "MEDIUM"))

        tn = _node(nodes, "transaction submission", file, line, c.get("line_end"), method, "mutating-callsite-analyzer", c.get("analysis_mode", "HEURISTIC"), c.get("evidence_status", "PARTIAL"), c.get("source_origin", "WORKTREE"))
        path_nodes.append(tn)
        path_edges.append(_edge(edges, sn, tn, "SUBMITS_TRANSACTION", file, line, c.get("line_end"), c.get("analysis_mode", "HEURISTIC"), c.get("evidence_status", "PARTIAL"), "HIGH" if c.get("capability_status") == "CONFIRMED" else "MEDIUM"))

        receipt = "UNKNOWN"
        if receipt_surfaces:
            rs = receipt_surfaces[0]
            rn = _node(nodes, "receipt/confirmation", rs.get("file"), rs.get("line_start"), rs.get("line_end"), rs.get("symbol"), "runtime-surface-inventory", rs.get("analysis_mode"), rs.get("evidence_status"), rs.get("source_origin"))
            path_nodes.append(rn)
            path_edges.append(_edge(edges, tn, rn, "WAITS_FOR_RECEIPT", rs.get("file"), rs.get("line_start"), rs.get("line_end"), rs.get("analysis_mode"), rs.get("evidence_status"), "HIGH"))
            receipt = "YES"
        elif "wait" in str(c).lower() or "receipt" in str(c).lower():
            receipt = "YES"
        else:
            receipt = "NO"

        local = "UNKNOWN"
        if matching_trans:
            tr = matching_trans[0]
            ln = _node(nodes, "local status update", tr.get("file"), tr.get("line_start"), tr.get("line_end"), tr.get("to_state"), "queue-state-transition-analyzer", tr.get("analysis_mode"), tr.get("evidence_status"), "WORKTREE")
            path_nodes.append(ln)
            path_edges.append(_edge(edges, tn, ln, "UPDATES_QUEUE", tr.get("file"), tr.get("line_start"), tr.get("line_end"), tr.get("analysis_mode"), tr.get("evidence_status"), "HIGH" if tr.get("analysis_mode") == "DETERMINISTIC" else "MEDIUM"))
            local = "YES"
        elif qn:
            local = "NO"

        failure = "NO"
        if failure_surfaces:
            fs = failure_surfaces[0]
            fn = _node(nodes, "retry/failure handler", fs.get("file"), fs.get("line_start"), fs.get("line_end"), fs.get("symbol"), "runtime-surface-inventory", fs.get("analysis_mode"), fs.get("evidence_status"), fs.get("source_origin"))
            path_nodes.append(fn)
            path_edges.append(_edge(edges, tn, fn, "RETRIES", fs.get("file"), fs.get("line_start"), fs.get("line_end"), fs.get("analysis_mode"), fs.get("evidence_status"), "MEDIUM"))
            failure = "YES"

        edge_modes = [e["analysis_mode"] for eid in path_edges for e in edges if e["edge_id"] == eid]
        path_edge_recs = [e for eid in path_edges for e in edges if e["edge_id"] == eid]
        base_gap_types = _gaps_for_call(c, sv, mc, qs)
        refined, meta = _refine_gaps_with_evidence(base_gap_types, c, idx, sv, mc, edge_modes, path_edge_recs)
        sot_rec = path_sot_index.get(pid)
        clearance_rec = clearance_index.get(pid)
        refined, meta = _apply_path_sot_clearance(
            refined,
            meta,
            sot_rec,
            global_canonical_status=global_canonical_status,
            clearance_rec=clearance_rec,
        )

        # Legacy path (no graph): emit gaps; apply static-axis completion (not authority/local/receipt gates)
        if not idx:
            gap_dicts = [
                {
                    "gap_type": gt,
                    "severity_for_path": sev,
                    "limitations": ["static path gap; not a security severity"],
                    "evidence_ids": [],
                    "refinement": "",
                    "analysis_mode": "HEURISTIC",
                    "root_cause": gt,
                }
                for gt, sev in base_gap_types
            ]
            gap_dicts, meta = _apply_path_sot_clearance(
                gap_dicts,
                meta,
                sot_rec,
                global_canonical_status=global_canonical_status,
                clearance_rec=clearance_rec,
            )
            for g in gap_dicts:
                gaps.append({
                    "gap_id": f"wrps-v0-g{len(gaps)+1:04d}",
                    "path_id": pid,
                    "gap_type": g["gap_type"],
                    "severity_for_path": g.get("severity_for_path") or "NON_BLOCKING",
                    "limitations": g.get("limitations") or ["static path gap; not a security severity"],
                    "evidence_ids": g.get("evidence_ids") or [],
                    "refinement": g.get("refinement") or "",
                    "analysis_mode": g.get("analysis_mode") or "HEURISTIC",
                    "root_cause": g.get("root_cause") or g["gap_type"],
                })
            det_edges = sum(1 for eid in path_edges for e in edges if e["edge_id"] == eid and e["analysis_mode"] == "DETERMINISTIC")
            all_det = det_edges == len(path_edges) and bool(path_edges)
            gap_types = {g["gap_type"] for g in gap_dicts}
            blocked = _completion_blocked(gap_types, all_det, receipt, local, meta, path_edge_recs)
            status = "PARTIAL" if blocked else "COMPLETE"
            if "CALLER_CHAIN_UNRESOLVED" in gap_types:
                status = "BROKEN"
            axes = _axis_statuses_for_path(
                static_status=status, c=c, gap_types=gap_types, meta=meta, runtime_execution_verified=False
            )
            human = "NO" if status == "COMPLETE" and all_det and not gap_types else "YES"
            paths.append({
                "path_id": pid,
                "path_name": f"{role} {method} static path",
                "actor_role": role,
                "entry_node": path_nodes[0] if path_nodes else "",
                "terminal_node": path_nodes[-1] if path_nodes else "",
                "nodes": path_nodes,
                "edges": path_edges,
                "path_status": status,
                "static_continuity": "YES" if status == "COMPLETE" else "PARTIAL" if status == "PARTIAL" else "NO",
                "transaction_submission_present": "YES",
                "receipt_handling_present": receipt,
                "local_state_update_present": local,
                "failure_path_present": failure,
                "authority_condition_known": "YES" if c.get("authority_status") == "CONFIRMED" else "PARTIAL" if c.get("authority_status") == "PARTIAL" else "NO",
                "runtime_execution_verified": False,
                "human_review_required": human,
                "limitations": [
                    "static source-path synthesis; runtime not executed",
                    "STATIC_PATH_COMPLETE ≠ RUNTIME/AUTHORITY/IW verified",
                ],
                **axes,
                "address_axes": meta.get("address_axes") or address_axes_from_path_sot(sot_rec, global_canonical_status=global_canonical_status),
            })
            continue

        for g in refined:
            gaps.append({
                "gap_id": f"wrps-v0-g{len(gaps)+1:04d}",
                "path_id": pid,
                "gap_type": g["gap_type"],
                "severity_for_path": g["severity_for_path"],
                "limitations": g.get("limitations") or ["static path gap; not a security severity"],
                "evidence_ids": g.get("evidence_ids") or [],
                "refinement": g.get("refinement") or "",
                "analysis_mode": g.get("analysis_mode") or "HEURISTIC",
                "root_cause": g.get("root_cause") or g["gap_type"],
            })

        det_edges = sum(1 for eid in path_edges for e in edges if e["edge_id"] == eid and e["analysis_mode"] == "DETERMINISTIC")
        all_det = det_edges == len(path_edges) and bool(path_edges)
        gap_types = {g["gap_type"] for g in refined}
        blocked = _completion_blocked(gap_types, all_det, receipt, local, meta, path_edge_recs)
        status = "PARTIAL" if blocked else "COMPLETE"
        if "CALLER_CHAIN_UNRESOLVED" in gap_types:
            status = "BROKEN"

        axes = _axis_statuses_for_path(
            static_status=status, c=c, gap_types=gap_types, meta=meta, runtime_execution_verified=False
        )

        # human_review_required may become NO only when all joins deterministic, no conflict, no NOT_FOUND, no blockers
        human = "YES"
        if (
            status == "COMPLETE"
            and all_det
            and meta.get("join_mode") in {"DETERMINISTIC", "NONE"}
            and not meta.get("conflict_blocks")
            and not meta.get("not_found_blocks")
            and not gap_types
            and not meta.get("human_join_review")
        ):
            human = "NO"

        path_lim = [
            "static source-path synthesis; runtime not executed",
            "static evidence graph joins attached",
            "STATIC_PATH_COMPLETE ≠ RUNTIME/AUTHORITY/SIGNER_IDENTITY/IW verified",
        ]
        if meta.get("join_mode") == "HEURISTIC":
            path_lim.append("evidence join was heuristic; human review required")
        if meta.get("path_usable_address"):
            path_lim.append("path-specific SoT satisfied address axis without global canonical family")
        paths.append({
            "path_id": pid,
            "path_name": f"{role} {method} static path",
            "actor_role": role,
            "entry_node": path_nodes[0] if path_nodes else "",
            "terminal_node": path_nodes[-1] if path_nodes else "",
            "nodes": path_nodes,
            "edges": path_edges,
            "path_status": status,
            "static_continuity": "YES" if status == "COMPLETE" else "PARTIAL" if status == "PARTIAL" else "NO",
            "transaction_submission_present": "YES",
            "receipt_handling_present": receipt,
            "local_state_update_present": local,
            "failure_path_present": failure,
            "authority_condition_known": "YES" if c.get("authority_status") == "CONFIRMED" else "PARTIAL" if c.get("authority_status") == "PARTIAL" else "NO",
            "runtime_execution_verified": False,
            "human_review_required": human,
            "callsite_id": c.get("callsite_id") or "",
            "evidence_refs": meta.get("evidence_refs") or [],
            "queue_evidence_ids": meta.get("queue_evidence_ids") or [],
            "mutating_evidence_ids": meta.get("mutating_evidence_ids") or [],
            "conflict_evidence_ids": meta.get("conflict_evidence_ids") or [],
            "not_found_evidence_ids": meta.get("not_found_evidence_ids") or [],
            "static_evidence_join_mode": meta.get("join_mode") or "NONE",
            "limitations": path_lim,
            **axes,
            "address_axes": meta.get("address_axes") or address_axes_from_path_sot(sot_rec, global_canonical_status=global_canonical_status),
            "path_sot_cleared_gaps": meta.get("path_sot_cleared") or [],
            **({k: v for k, v in dynamic_target_axes(sot_rec).items() if v not in ("", None, False) or k in {
                "DYNAMIC_TARGET_CLASS",
                "STATIC_DOMAIN_STATUS",
                "RUNTIME_TARGET_IDENTITY_STATUS",
                "STATIC_DOMAIN_COMPLETE",
                "RUNTIME_TARGET_IDENTITY_COMPLETE",
            }} if sot_rec and (sot_rec.get("dynamic_target_class") or sot_rec.get("path_specific_sot_classification", "").startswith("PATH_SOT_FINITE") or sot_rec.get("path_specific_sot_classification", "") in {
                "PATH_SOT_FINITE_DYNAMIC_SET",
                "PATH_SOT_DATA_PROPAGATED_TARGET",
                "PATH_SOT_CALLER_PROPAGATED_TARGET",
                "PATH_SOT_UNBOUNDED_DYNAMIC",
            }) else {}),
        })

    r["nodes"] = nodes["items"]
    r["edges"] = edges
    r["paths"] = paths
    r["path_gaps"] = gaps
    summary = r["summary"]
    summary["paths_total"] = len(paths)
    summary["paths_complete"] = sum(1 for p in paths if p["path_status"] == "COMPLETE")
    summary["paths_partial"] = sum(1 for p in paths if p["path_status"] == "PARTIAL")
    summary["paths_broken"] = sum(1 for p in paths if p["path_status"] == "BROKEN")
    summary["paths_unknown"] = sum(1 for p in paths if p["path_status"] == "UNKNOWN")
    summary["static_paths_complete"] = sum(1 for p in paths if p.get("STATIC_PATH_STATUS") == "COMPLETE")
    summary["static_paths_partial"] = sum(1 for p in paths if p.get("STATIC_PATH_STATUS") == "PARTIAL")
    summary["static_paths_unresolved"] = sum(1 for p in paths if p.get("STATIC_PATH_STATUS") == "UNRESOLVED")
    summary["runtime_execution_verified_paths"] = sum(1 for p in paths if p.get("RUNTIME_EXECUTION_STATUS") == "VERIFIED")
    summary["authority_verified_paths"] = sum(1 for p in paths if p.get("AUTHORITY_STATUS") == "VERIFIED")
    summary["signer_identity_verified_paths"] = sum(1 for p in paths if p.get("SIGNER_IDENTITY_STATUS") == "VERIFIED")
    summary["independent_witness_satisfied_paths"] = sum(1 for p in paths if p.get("INDEPENDENT_WITNESS_STATUS") == "SATISFIED")
    for p in paths:
        summary[_actor_bucket(p.get("actor_role"))] += 1
    validator_methods = {"sendTransaction", "deposit", "withdraw", "submitReplication", "finalizeSubmission", "resolveChallenge", "relayChallengeBatch", "slashIncoherentRoot"}
    vm_count = sum(1 for p in paths if p.get("actor_role") in {"validator", "archive operator"} and any(f" {m} static path" in p.get("path_name", "") for m in validator_methods))
    if vm_count:
        summary["validator_paths"] = vm_count
    summary["deterministic_edges"] = sum(1 for e in edges if e["analysis_mode"] == "DETERMINISTIC")
    summary["heuristic_edges"] = sum(1 for e in edges if e["analysis_mode"] == "HEURISTIC")
    summary["human_review_required_paths"] = sum(1 for p in paths if p["human_review_required"] == "YES")

    def _paths_with_gap(*types: str) -> int:
        pids = {g["path_id"] for g in gaps if g.get("gap_type") in types}
        return len(pids)

    summary["address_source_blocker_paths"] = _paths_with_gap("ADDRESS_SOURCE_PARTIAL")
    summary["generated_config_blocker_paths"] = _paths_with_gap("GENERATED_CONFIG_DEPENDENCY", "GENERATED_CONFIG_PARTIAL")
    summary["signer_source_blocker_paths"] = _paths_with_gap("SIGNER_SOURCE_PARTIAL")
    summary["caller_chain_heuristic_blocker_paths"] = _paths_with_gap("CALLER_CHAIN_HEURISTIC", "CALLER_CHAIN_UNRESOLVED")
    summary["conflict_blocked_paths"] = _paths_with_gap("PROVENANCE_CONFLICT")
    summary["not_found_blocked_paths"] = _paths_with_gap("NOT_FOUND_DEPENDENCY")
    summary["static_target_unresolved_paths"] = _paths_with_gap("STATIC_TARGET_UNRESOLVED")
    if idx and summary["evidence_graph_consumed"] == "YES":
        # PARTIAL consumption if graph present but no path got evidence refs
        if paths and not any(p.get("evidence_refs") for p in paths):
            summary["evidence_graph_consumed"] = "PARTIAL"
    r["result_id"] = rid(r)
    return r


def validate_runtime_path_synthesizer_result_v0(r):
    errs = []
    if r.get("schema_version") != SCHEMA_VERSION:
        errs.append("bad schema_version")
    if not str(r.get("result_id", "")).startswith(RID_PREFIX):
        errs.append("bad result_id")
    if r.get("runtime_execution_verified") is not False:
        errs.append("runtime_execution_verified must be false")
    node_ids = {n.get("node_id") for n in r.get("nodes", [])}
    for e in r.get("edges", []):
        if e.get("from_node") not in node_ids or e.get("to_node") not in node_ids:
            errs.append("edge references missing node")
        if not e.get("evidence_file") or e.get("line_start") is None:
            errs.append("edge lacks source evidence")
        if e.get("analysis_mode") not in {"DETERMINISTIC", "HEURISTIC", "AI_ASSISTED", "HUMAN_REVIEW_REQUIRED"}:
            errs.append("bad edge mode")
    if r.get("result_id") != rid({k: v for k, v in r.items() if k != "result_id"}):
        errs.append("result_id mismatch")
    return errs


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 1:
        sys.stderr.write("usage: runtime_path_synthesizer_v0.py <input.json>\n")
        return 1
    res = synthesize_runtime_paths_v0(json.loads(Path(args[0]).read_text(encoding="utf-8")))
    print(json.dumps(res, indent=2, ensure_ascii=True))
    return 0 if not res.get("reason_codes") else 3


if __name__ == "__main__":
    raise SystemExit(main())
