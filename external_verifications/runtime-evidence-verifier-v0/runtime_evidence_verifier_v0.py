"""Weaver Runtime Evidence Verifier v0.

Validates and normalizes already-produced runtime evidence packs.
Does not execute forks, call RPC, discover runtime paths, or mutate CAW.

Architecture D (WREID-20260912-113817-2D2509C8):
  additive schemas + this verifier + thin optional synthesizer consumer.

Axis refinement (WRAR):
  RUN_STAGE (record.level / campaign chronology) is independent from
  EVIDENCE_STATUS (axes derived from proven facts). Success at V-R1 may
  establish LOCAL_EXECUTION_ALIGNED without requiring V-R2/V-R3 records.
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "weaver-runtime-evidence-verifier-v0"
PACK_SCHEMA = "weaver-runtime-evidence-pack-v0"
INPUT_ARTIFACT_SCHEMA = "weaver-runtime-input-artifact-v0"
DISPATCH_ARTIFACT_SCHEMA = "weaver-runtime-dispatch-artifact-v0"
PRECONDITION_CHAIN_SCHEMA = "weaver-runtime-precondition-chain-v0"
LOCAL_FORK_MUTATION_SCHEMA = "weaver-local-fork-mutation-v0"
RESULT_EVENT_SCHEMA = "weaver-runtime-result-event-v0"
STATIC_RUNTIME_LINK_SCHEMA = "weaver-static-runtime-link-v0"
CONSUMER_CONTRACT_SCHEMA = "weaver-runtime-path-synthesizer-runtime-evidence-contract-v0"
RID_PREFIX = "wrev-v0-"

# Capability labels (evidence strength). Names retain R0..R3 for backward
# compatibility but do NOT require matching campaign run ordinals.
LEVEL_ORDER = [
    "R0_INPUT_ALIGNED",
    "R1_DISPATCH_ALIGNED",
    "R2_PRECONDITION_PATH_ALIGNED",
    "R3_LOCAL_EXECUTION_ALIGNED",
    "LIVE_TRANSACTION_VERIFIED",
]

# Campaign chronology / RUN_STAGE labels on pack records.
RECORD_LEVEL_ORDER = ["R0", "R1", "R2", "R3", "LIVE"]
RUN_STAGE_LABELS = {
    "R0": "VR0",
    "R1": "VR1",
    "R2": "VR2",
    "R3": "VR3",
    "LIVE": "LIVE",
}

LOCAL_MUTATION_TYPES = {
    "ACCOUNT_IMPERSONATION",
    "LOCAL_BALANCE_SET",
    "LOCAL_APPROVAL_TX",
    "LOCAL_STATE_MUTATION",
    "SNAPSHOT",
    "REVERT",
    "FORK_DISPOSED",
}

NONCLAIM_AXES = (
    "AUTHORITY_STATUS",
    "SIGNER_IDENTITY_STATUS",
    "INDEPENDENT_WITNESS_STATUS",
)

INPUT_ALIGNED_STATUSES = {
    "RUNTIME_INPUT_ALIGNMENT_VERIFIED",
    "ALIGNED",
    "VERIFIED",
}
DISPATCH_ALIGNED_STATUSES = {
    "RUNTIME_DISPATCH_ALIGNMENT_VERIFIED",
    "RUNTIME_DEEPER_PATH_ALIGNMENT_VERIFIED",
    "ALIGNED",
    "VERIFIED",
    "PROGRESSING",
}
# Execution success statuses may appear on any RUN_STAGE (e.g. permissionless mint at VR1).
# Intentionally excludes generic ALIGNED/VERIFIED — those alone are not execution proof.
EXECUTION_ALIGNED_STATUSES = {
    "RUNTIME_EXECUTION_ALIGNMENT_VERIFIED",
    "LOCAL_EXECUTION_ALIGNED",
    "SUCCESS",
}
CALL_SUCCESS_OUTCOMES = {"CALL_RETURNED_SUCCESS", "SUCCESS"}
CALL_REVERT_OUTCOMES = {"CALL_REVERTED", "REVERTED", "REVERT"}
BLOCKING_PRECONDITION_CLASSES = {
    "OWNERSHIP_PRECONDITION",
    "APPROVAL_PRECONDITION",
    "AUTH_PRECONDITION",
    "ACCESS_CONTROL_PRECONDITION",
    "ROLE_PRECONDITION",
    "PAUSE_PRECONDITION",
    "BALANCE_PRECONDITION",
}
NO_BLOCKER_PRECONDITION_CLASSES = {
    "OTHER",
    "NONE",
    "NO_BLOCKING_PRECONDITION",
    "NO_BLOCKING_PRECONDITION_OBSERVED",
    "PERMISSIONLESS",
}


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def canon(x: Any) -> str:
    return json.dumps(x, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def digest(payload: Any) -> str:
    return hashlib.sha256(canon(payload).encode()).hexdigest()


def rid(result: dict[str, Any]) -> str:
    return RID_PREFIX + digest({k: v for k, v in result.items() if k != "result_id"})[:32]


def norm_addr(a: Any) -> str:
    s = str(a or "").strip()
    if s.startswith("0x") or s.startswith("0X"):
        return "0x" + s[2:].lower()
    return s.lower()


def norm_sel(s: Any) -> str:
    t = str(s or "").strip().lower()
    if t and not t.startswith("0x"):
        t = "0x" + t
    return t


def _err(code: str, detail: str = "") -> dict[str, str]:
    return {"code": code, "detail": detail}


def extract_link(pack: dict[str, Any]) -> dict[str, Any]:
    link = dict(pack.get("static_runtime_link") or pack.get("static_link") or {})
    # Allow top-level convenience fields to fill gaps.
    for k, src in (
        ("PATH_ID", "path_id"),
        ("TARGET_ADDRESS", "target_address"),
        ("METHOD_SIGNATURE", "method_signature"),
        ("SELECTOR", "selector"),
        ("CALLDATA_SHA256", "calldata_sha256"),
        ("CHAIN_ID", "chain_id"),
        ("FORK_BLOCK", "fork_block"),
    ):
        if not link.get(k) and pack.get(src) is not None:
            link[k] = pack[src]
    if "RUNTIME_RUN_IDS" not in link:
        runs = {}
        for rec in pack.get("records") or []:
            lvl = str(rec.get("level") or "").upper()
            rid_v = rec.get("run_id")
            if lvl and rid_v:
                runs[f"V_{lvl}"] = rid_v
        if runs:
            link["RUNTIME_RUN_IDS"] = runs
    return link


def validate_pack_schema(pack: dict[str, Any]) -> list[dict[str, str]]:
    errs: list[dict[str, str]] = []
    if not isinstance(pack, dict):
        return [_err("invalid_pack", "pack must be object")]
    if pack.get("schema_version") != PACK_SCHEMA:
        errs.append(_err("bad_pack_schema", f"expected {PACK_SCHEMA}"))
    link = extract_link(pack)
    for req in (
        "PATH_ID",
        "TARGET_ADDRESS",
        "METHOD_SIGNATURE",
        "SELECTOR",
        "CALLDATA_SHA256",
    ):
        if not link.get(req):
            errs.append(_err("missing_link_field", req))
    records = pack.get("records")
    if not isinstance(records, list) or not records:
        errs.append(_err("missing_records", "at least one runtime record required"))
    return errs


def validate_record_bindings(pack: dict[str, Any], link: dict[str, Any]) -> list[dict[str, str]]:
    """Fail-closed static→runtime link: all records must bind to the same path artifact."""
    errs: list[dict[str, str]] = []
    path_id = link.get("PATH_ID")
    target = norm_addr(link.get("TARGET_ADDRESS"))
    selector = norm_sel(link.get("SELECTOR"))
    calldata = str(link.get("CALLDATA_SHA256") or "").lower()
    method = link.get("METHOD_SIGNATURE")
    chain_id = link.get("CHAIN_ID")
    fork_block = link.get("FORK_BLOCK")

    seen_levels: list[str] = []
    for i, rec in enumerate(pack.get("records") or []):
        if not isinstance(rec, dict):
            errs.append(_err("bad_record", f"index={i}"))
            continue
        lvl = str(rec.get("level") or "").upper()
        if lvl not in RECORD_LEVEL_ORDER:
            errs.append(_err("unknown_record_level", f"{lvl}@index={i}"))
        else:
            seen_levels.append(lvl)

        r_path = rec.get("PATH_ID") or rec.get("path_id")
        if r_path is not None and r_path != path_id:
            errs.append(_err("mismatched_PATH_ID", f"{r_path} != {path_id}"))

        r_target = rec.get("TARGET_ADDRESS") or rec.get("target_address")
        if r_target is not None and norm_addr(r_target) != target:
            errs.append(_err("mismatched_target", f"{r_target} != {link.get('TARGET_ADDRESS')}"))

        r_sel = rec.get("SELECTOR") or rec.get("selector")
        if r_sel is not None and norm_sel(r_sel) != selector:
            errs.append(_err("mismatched_selector", f"{r_sel} != {link.get('SELECTOR')}"))

        r_cd = rec.get("CALLDATA_SHA256") or rec.get("calldata_sha256")
        if r_cd is not None and str(r_cd).lower() != calldata:
            errs.append(_err("mismatched_calldata_hash", f"{r_cd} != {calldata}"))

        r_method = rec.get("METHOD_SIGNATURE") or rec.get("method_signature")
        if r_method is not None and r_method != method:
            errs.append(_err("mismatched_method", f"{r_method} != {method}"))

        # R1+ must share chain/fork unless explicitly re-bound.
        if lvl in {"R1", "R2", "R3", "LIVE"}:
            r_chain = rec.get("CHAIN_ID") if "CHAIN_ID" in rec else rec.get("chain_id")
            r_fork = rec.get("FORK_BLOCK") if "FORK_BLOCK" in rec else rec.get("fork_block")
            rebind = bool(rec.get("new_fork_context"))
            if not rebind:
                if chain_id is not None and r_chain is not None and int(r_chain) != int(chain_id):
                    errs.append(_err("mismatched_chain_id", f"{r_chain} != {chain_id}"))
                if fork_block is not None and r_fork is not None and int(r_fork) != int(fork_block):
                    errs.append(_err("mismatched_fork_block", f"{r_fork} != {fork_block}"))

    # Ordering: levels must appear in non-decreasing depth order.
    idxs = [RECORD_LEVEL_ORDER.index(x) for x in seen_levels if x in RECORD_LEVEL_ORDER]
    if idxs != sorted(idxs):
        errs.append(_err("out_of_order_runtime_chain", ",".join(seen_levels)))
    # No duplicate levels.
    if len(seen_levels) != len(set(seen_levels)):
        errs.append(_err("duplicate_runtime_level", ",".join(seen_levels)))
    return errs


def validate_local_live_separation(pack: dict[str, Any]) -> list[dict[str, str]]:
    errs: list[dict[str, str]] = []
    mutations = pack.get("local_fork_mutations") or []
    live = pack.get("live_transaction") or {}
    for m in mutations:
        if not isinstance(m, dict):
            errs.append(_err("bad_mutation_record", "non-object"))
            continue
        mtype = m.get("type")
        if mtype not in LOCAL_MUTATION_TYPES:
            errs.append(_err("unknown_mutation_type", str(mtype)))
        scope = m.get("mutation_scope") or m.get("scope") or "LOCAL_FORK_ONLY"
        if scope == "LIVE_CHAIN":
            errs.append(_err("contradictory_live_local_mutation", f"{mtype} marked LIVE_CHAIN"))
        if scope != "LOCAL_FORK_ONLY" and mtype in LOCAL_MUTATION_TYPES:
            # LOCAL_* types must remain LOCAL_FORK_ONLY
            if str(mtype).startswith("LOCAL_") or mtype in {
                "ACCOUNT_IMPERSONATION",
                "SNAPSHOT",
                "REVERT",
                "FORK_DISPOSED",
            }:
                errs.append(_err("local_mutation_not_local_scope", str(mtype)))
        if m.get("LIVE_CHAIN_MUTATION") is True:
            errs.append(_err("contradictory_live_local_mutation", "LIVE_CHAIN_MUTATION true on local record"))

    if live.get("verified") is True or live.get("LIVE_TRANSACTION_STATUS") == "VERIFIED":
        # Require explicit live evidence fields; local-only packs must not claim live.
        if not live.get("live_tx_hash") and not live.get("public_transaction"):
            errs.append(_err("live_claim_without_evidence", "verified without live_tx_hash/public_transaction"))
        # Contradict if mutations claim local-only success as live.
        if any((m.get("mutation_scope") or "LOCAL_FORK_ONLY") == "LOCAL_FORK_ONLY" for m in mutations) and live.get(
            "derived_from_local_fork"
        ):
            errs.append(_err("contradictory_live_local_mutation", "live claim derived_from_local_fork"))

    # Explicit contradiction flag support for negative tests.
    if pack.get("claim_live_from_local_fork") is True:
        errs.append(_err("contradictory_live_local_mutation", "claim_live_from_local_fork"))
    return errs


def validate_precondition_chain(chain: list[Any] | None) -> list[dict[str, str]]:
    if chain is None:
        return []
    errs: list[dict[str, str]] = []
    if not isinstance(chain, list):
        return [_err("bad_precondition_chain", "must be list")]
    required = {
        "PRECONDITION_ID",
        "SOURCE_LOCATION",
        "CONDITION",
        "INPUT_STATE",
        "SETUP_ACTION",
        "RESULT",
        "NEXT_CONDITION",
        "EVIDENCE_REFERENCES",
    }
    for i, gate in enumerate(chain):
        if not isinstance(gate, dict):
            errs.append(_err("bad_precondition_gate", f"index={i}"))
            continue
        missing = required - set(gate.keys())
        if missing:
            errs.append(_err("precondition_missing_fields", f"{gate.get('PRECONDITION_ID')}:{sorted(missing)}"))
        setup = gate.get("SETUP_ACTION") or {}
        if isinstance(setup, dict) and setup.get("authority_claim") is True:
            errs.append(_err("setup_authority_claim_forbidden", str(gate.get("PRECONDITION_ID"))))
    return errs


def _rec_status(rec: dict[str, Any]) -> str:
    return str(rec.get("status") or rec.get("alignment_status") or "")


def _rec_outcome(rec: dict[str, Any]) -> str:
    art = rec.get("artifact") if isinstance(rec.get("artifact"), dict) else {}
    return str(
        rec.get("call_outcome")
        or rec.get("CALL_OUTCOME")
        or art.get("call_outcome")
        or art.get("CALL_OUTCOME")
        or ""
    )


def _rec_precondition_class(rec: dict[str, Any]) -> str:
    art = rec.get("artifact") if isinstance(rec.get("artifact"), dict) else {}
    return str(
        rec.get("precondition_class")
        or rec.get("PRECONDITION_CLASS")
        or art.get("precondition_class")
        or art.get("PRECONDITION_CLASS")
        or ""
    ).upper()


def _observed_local_state_transition(pack: dict[str, Any], rec: dict[str, Any] | None = None) -> bool:
    result_event = pack.get("result_event") or {}
    candidates = []
    if rec is not None:
        candidates.append(rec.get("state_transition"))
    candidates.append(result_event.get("state_transition"))
    candidates.append(result_event.get("RUNTIME_STATE_TRANSITION_STATUS"))
    candidates.append(pack.get("state_transition_observation_mode"))
    for st_trans in candidates:
        if isinstance(st_trans, dict):
            if st_trans.get("observed"):
                return True
            continue
        if st_trans in {"REACHED", "OBSERVED_LOCAL", "BOUNDED_LOCAL_FORK_SAMPLE", True}:
            return True
    if any(
        isinstance(m, dict) and m.get("type") == "LOCAL_STATE_MUTATION"
        for m in (pack.get("local_fork_mutations") or [])
    ):
        return True
    if pack.get("persistent_state_commit_observed") is True:
        return True
    return False


def collect_run_stage_meta(pack: dict[str, Any]) -> dict[str, Any]:
    """Campaign chronology metadata — independent of evidence capability."""
    stages: list[str] = []
    for rec in pack.get("records") or []:
        lvl = str(rec.get("level") or "").upper()
        if lvl in RUN_STAGE_LABELS:
            stages.append(RUN_STAGE_LABELS[lvl])
        elif lvl:
            stages.append("OTHER")
    # Preserve first-seen order, unique.
    seen: list[str] = []
    for s in stages:
        if s not in seen:
            seen.append(s)
    return {
        "run_stages_present": seen,
        "max_run_stage": seen[-1] if seen else None,
    }


def classify_axes(pack: dict[str, Any], link: dict[str, Any]) -> dict[str, Any]:
    """Derive EVIDENCE_STATUS axes from proven facts across any RUN_STAGE.

    Run ordinal (R0/R1/R2/R3) records campaign chronology only. Semantic
    strength (input/dispatch/execution/state/live) comes from evidence content.
    """
    _ = link  # link used for binding validation; axes come from pack facts
    prior = pack.get("prior_axes") or {}
    records = [r for r in (pack.get("records") or []) if isinstance(r, dict)]

    axes = {
        "STATIC_PATH_STATUS": prior.get("STATIC_PATH_STATUS") or pack.get("STATIC_PATH_STATUS") or "UNKNOWN",
        "RUNTIME_INPUT_STATUS": "UNVERIFIED",
        "RUNTIME_DISPATCH_STATUS": "UNVERIFIED",
        "RUNTIME_PRECONDITION_STATUS": "UNVERIFIED",
        "RUNTIME_EXECUTION_STATUS": "UNVERIFIED",
        "RUNTIME_STATE_TRANSITION_STATUS": "UNVERIFIED",
        "LIVE_TRANSACTION_STATUS": "NOT_VERIFIED",
        "AUTHORITY_STATUS": prior.get("AUTHORITY_STATUS") or "NOT_VERIFIED",
        "SIGNER_IDENTITY_STATUS": prior.get("SIGNER_IDENTITY_STATUS") or "NOT_VERIFIED",
        "INDEPENDENT_WITNESS_STATUS": prior.get("INDEPENDENT_WITNESS_STATUS") or "NOT_SATISFIED",
    }

    execution_source_stage: str | None = None
    saw_dispatch = False
    saw_execution_success = False
    saw_deterministic_revert = False
    saw_deeper_path = False
    saw_blocking_precondition = False
    saw_no_blocker_class = False

    for rec in records:
        lvl = str(rec.get("level") or "").upper()
        stage = RUN_STAGE_LABELS.get(lvl, "OTHER")
        st = _rec_status(rec)
        outcome = _rec_outcome(rec)
        pc = _rec_precondition_class(rec)

        # INPUT — typically R0, but accept content anywhere.
        if st in INPUT_ALIGNED_STATUSES and (
            lvl == "R0" or axes["RUNTIME_INPUT_STATUS"] == "UNVERIFIED"
        ):
            if lvl == "R0" or st == "RUNTIME_INPUT_ALIGNMENT_VERIFIED":
                axes["RUNTIME_INPUT_STATUS"] = "ALIGNED"
        if lvl == "R0" and st in {"MISALIGNED", "FAILED"}:
            axes["RUNTIME_INPUT_STATUS"] = "MISALIGNED"

        # DISPATCH — any stage that proves selector/path dispatch.
        dispatch_hit = False
        if st in DISPATCH_ALIGNED_STATUSES:
            dispatch_hit = True
        if st in EXECUTION_ALIGNED_STATUSES:
            # Execution alignment implies dispatch was reached.
            dispatch_hit = True
        if outcome in CALL_SUCCESS_OUTCOMES or outcome in CALL_REVERT_OUTCOMES:
            dispatch_hit = True
        if dispatch_hit:
            saw_dispatch = True
            axes["RUNTIME_DISPATCH_STATUS"] = "ALIGNED"
        if st in {"MISALIGNED", "FAILED"} and lvl in {"R1", "R2"} and not dispatch_hit:
            axes["RUNTIME_DISPATCH_STATUS"] = "MISALIGNED"

        # Deeper precondition path (historically R2).
        if st == "RUNTIME_DEEPER_PATH_ALIGNMENT_VERIFIED" or lvl == "R2":
            saw_deeper_path = True
            own = rec.get("ownership_gate") or rec.get("OWNERSHIP_GATE")
            appr = rec.get("approval_gate") or rec.get("APPROVAL_GATE") or rec.get("next_precondition_class")
            if st in {
                "RUNTIME_DEEPER_PATH_ALIGNMENT_VERIFIED",
                "ALIGNED",
                "VERIFIED",
                "PROGRESSING",
            } or (
                own in {"CLEARED", "OWNERSHIP_GATE_CLEARED", "YES"}
                and appr
                in {
                    "BLOCKED",
                    "APPROVAL_PRECONDITION",
                    "CALL_REVERTED_ON_NEXT_PRECONDITION",
                }
            ):
                axes["RUNTIME_PRECONDITION_STATUS"] = "PROGRESSING"

        # Precondition class semantics (do not treat OTHER as BLOCKED).
        if pc in BLOCKING_PRECONDITION_CLASSES:
            saw_blocking_precondition = True
        if pc in NO_BLOCKER_PRECONDITION_CLASSES:
            saw_no_blocker_class = True

        # EXECUTION — derived from evidence content at any RUN_STAGE.
        exec_success = st in EXECUTION_ALIGNED_STATUSES or outcome in CALL_SUCCESS_OUTCOMES
        if exec_success:
            saw_execution_success = True
            axes["RUNTIME_EXECUTION_STATUS"] = "LOCAL_EXECUTION_ALIGNED"
            if execution_source_stage is None:
                execution_source_stage = stage
        elif outcome in CALL_REVERT_OUTCOMES:
            saw_deterministic_revert = True
        elif st == "RUNTIME_DISPATCH_ALIGNMENT_VERIFIED":
            # Dispatch-aligned revert samples: outcome on record or artifact, or decoded error.
            art = rec.get("artifact") if isinstance(rec.get("artifact"), dict) else {}
            art_outcome = str(art.get("call_outcome") or "")
            if art_outcome in CALL_REVERT_OUTCOMES or rec.get("decoded_result_or_error"):
                saw_deterministic_revert = True

        # Per-record state observation (does not auto-claim from execution alone).
        if _observed_local_state_transition(pack, rec):
            axes["RUNTIME_STATE_TRANSITION_STATUS"] = "OBSERVED_LOCAL"

    # Deterministic revert → EXECUTION_PARTIAL when dispatch aligned but no success.
    if saw_dispatch and saw_deterministic_revert and not saw_execution_success:
        axes["RUNTIME_EXECUTION_STATUS"] = "EXECUTION_PARTIAL"
        if saw_deeper_path:
            axes["RUNTIME_PRECONDITION_STATUS"] = "PROGRESSING"
        elif saw_blocking_precondition:
            axes["RUNTIME_PRECONDITION_STATUS"] = "BLOCKED"

    # Blocking precondition without success.
    if saw_blocking_precondition and not saw_execution_success:
        if axes["RUNTIME_PRECONDITION_STATUS"] == "UNVERIFIED":
            axes["RUNTIME_PRECONDITION_STATUS"] = "BLOCKED"
        if saw_dispatch and axes["RUNTIME_EXECUTION_STATUS"] == "UNVERIFIED":
            axes["RUNTIME_EXECUTION_STATUS"] = "EXECUTION_PARTIAL"

    # Empty / zero-blocker precondition chain when source/runtime supports it.
    chain = pack.get("precondition_chain")
    if chain is None:
        chain = []
    if not isinstance(chain, list):
        chain = []

    if saw_execution_success:
        if chain and all(isinstance(g, dict) and g.get("RESULT") == "CLEARED" for g in chain):
            axes["RUNTIME_PRECONDITION_STATUS"] = "CLEARED"
        elif not chain and (saw_no_blocker_class or not saw_blocking_precondition):
            axes["RUNTIME_PRECONDITION_STATUS"] = "NO_BLOCKING_PRECONDITION_OBSERVED"
        elif not chain:
            axes["RUNTIME_PRECONDITION_STATUS"] = "NO_BLOCKING_PRECONDITION_OBSERVED"
        elif all(isinstance(g, dict) and g.get("RESULT") == "CLEARED" for g in chain):
            axes["RUNTIME_PRECONDITION_STATUS"] = "CLEARED"

    # Explicit CLEARED chain without requiring an R3 run stage.
    if chain and all(isinstance(g, dict) and g.get("RESULT") == "CLEARED" for g in chain):
        if saw_execution_success or any(str(r.get("level") or "").upper() == "R3" for r in records):
            axes["RUNTIME_PRECONDITION_STATUS"] = "CLEARED"

    # Pack-level simulation / persistence flags (additive).
    if pack.get("simulation_success") is True and not saw_execution_success:
        # Explicit pack assertion still requires call/status evidence elsewhere;
        # do not promote from flag alone.
        pass

    # State transition: separate from execution success.
    if axes["RUNTIME_STATE_TRANSITION_STATUS"] != "OBSERVED_LOCAL":
        mode = (
            pack.get("state_transition_observation_mode")
            or (pack.get("result_event") or {}).get("RUNTIME_STATE_TRANSITION_STATUS")
            or (pack.get("result_event") or {}).get("state_transition_observation_mode")
        )
        if mode in {
            "SIMULATED_ONLY",
            "NOT_OBSERVED_PERSISTENTLY",
            "NOT_OBSERVED",
            "UNVERIFIED",
        }:
            axes["RUNTIME_STATE_TRANSITION_STATUS"] = str(mode)
        elif pack.get("persistent_state_commit_observed") is False and saw_execution_success:
            axes["RUNTIME_STATE_TRANSITION_STATUS"] = "SIMULATED_ONLY"
        elif saw_execution_success and not _observed_local_state_transition(pack):
            # Successful eth_call / local execution without observed commit.
            axes["RUNTIME_STATE_TRANSITION_STATUS"] = "SIMULATED_ONLY"
        elif _observed_local_state_transition(pack):
            axes["RUNTIME_STATE_TRANSITION_STATUS"] = "OBSERVED_LOCAL"

    # LIVE — never derived from local fork / eth_call success.
    live = pack.get("live_transaction") or {}
    if live.get("verified") is True and live.get("live_tx_hash") and not live.get("derived_from_local_fork"):
        axes["LIVE_TRANSACTION_STATUS"] = "VERIFIED"
    else:
        axes["LIVE_TRANSACTION_STATUS"] = "NOT_VERIFIED"

    # Nonclaim freeze: runtime ingestion never promotes these.
    if axes["AUTHORITY_STATUS"] == "VERIFIED" and not prior.get("AUTHORITY_STATUS") == "VERIFIED":
        axes["AUTHORITY_STATUS"] = prior.get("AUTHORITY_STATUS") or "NOT_VERIFIED"
    axes["SIGNER_IDENTITY_STATUS"] = prior.get("SIGNER_IDENTITY_STATUS") or "NOT_VERIFIED"
    if axes["SIGNER_IDENTITY_STATUS"] == "VERIFIED" and any(
        (m.get("type") == "ACCOUNT_IMPERSONATION") for m in (pack.get("local_fork_mutations") or [])
    ):
        if not prior.get("SIGNER_IDENTITY_STATUS") == "VERIFIED":
            axes["SIGNER_IDENTITY_STATUS"] = "NOT_VERIFIED"
    axes["INDEPENDENT_WITNESS_STATUS"] = prior.get("INDEPENDENT_WITNESS_STATUS") or "NOT_SATISFIED"
    if axes["INDEPENDENT_WITNESS_STATUS"] == "SATISFIED" and not prior.get("INDEPENDENT_WITNESS_STATUS") == "SATISFIED":
        axes["INDEPENDENT_WITNESS_STATUS"] = "NOT_SATISFIED"

    if pack.get("force_iw_satisfied"):
        axes["INDEPENDENT_WITNESS_STATUS"] = "NOT_SATISFIED"

    axes["_meta"] = {
        "execution_evidence_source_stage": execution_source_stage,
        "simulation_success": bool(saw_execution_success),
        "persistent_state_commit_observed": axes["RUNTIME_STATE_TRANSITION_STATUS"] == "OBSERVED_LOCAL",
        "state_transition_observation_mode": axes["RUNTIME_STATE_TRANSITION_STATUS"],
        **collect_run_stage_meta(pack),
    }
    return axes


def classify_highest_level(axes: dict[str, Any]) -> str | None:
    """Map evidence axes to capability label (not campaign run ordinal)."""
    if axes.get("LIVE_TRANSACTION_STATUS") == "VERIFIED":
        return "LIVE_TRANSACTION_VERIFIED"
    if axes.get("RUNTIME_EXECUTION_STATUS") == "LOCAL_EXECUTION_ALIGNED":
        return "R3_LOCAL_EXECUTION_ALIGNED"
    if axes.get("RUNTIME_PRECONDITION_STATUS") in {
        "PROGRESSING",
        "CLEARED",
        "NO_BLOCKING_PRECONDITION_OBSERVED",
    } and axes.get("RUNTIME_DISPATCH_STATUS") == "ALIGNED":
        if axes.get("RUNTIME_EXECUTION_STATUS") == "LOCAL_EXECUTION_ALIGNED":
            return "R3_LOCAL_EXECUTION_ALIGNED"
        if axes.get("RUNTIME_PRECONDITION_STATUS") == "PROGRESSING":
            return "R2_PRECONDITION_PATH_ALIGNED"
        if axes.get("RUNTIME_PRECONDITION_STATUS") == "CLEARED":
            return "R2_PRECONDITION_PATH_ALIGNED"
        # NO_BLOCKING without execution still only dispatch-aligned.
        return "R1_DISPATCH_ALIGNED"
    if axes.get("RUNTIME_DISPATCH_STATUS") == "ALIGNED":
        return "R1_DISPATCH_ALIGNED"
    if axes.get("RUNTIME_INPUT_STATUS") == "ALIGNED":
        return "R0_INPUT_ALIGNED"
    return None


def extract_axis_meta(axes: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    meta = dict(axes.pop("_meta", {}) or {})
    return axes, meta


def apply_nonclaim_gates(
    axes: dict[str, Any],
    pack: dict[str, Any],
    *,
    prior_caw_verdict_changed: bool | None = None,
) -> dict[str, Any]:
    gates = {
        "NG-1_local_fork_blocks_live": True,
        "NG-2_setup_authority_claim_false": True,
        "NG-3_impersonation_not_signer_verified": True,
        "NG-4_iw_not_writable_by_runtime_verifier": True,
        "NG-5_legacy_runtime_execution_verified_stays_false": True,
        "AUTHORITY_VERIFIED": False,
        "TRUSTLESS_VERIFIED": False,
        "DECENTRALIZED_VERIFIED": False,
        "RUNTIME_SIGNER_IDENTITY_VERIFIED": False,
        "INDEPENDENT_WITNESS_VERIFIED": False,
        "CAW_VERDICT_CHANGED": False if prior_caw_verdict_changed is None else prior_caw_verdict_changed,
        "LIVE_TRANSACTION_VERIFIED": axes.get("LIVE_TRANSACTION_STATUS") == "VERIFIED",
    }

    # NG-1
    has_local = bool(pack.get("local_fork_mutations"))
    if has_local or axes.get("RUNTIME_EXECUTION_STATUS") == "LOCAL_EXECUTION_ALIGNED":
        if axes.get("LIVE_TRANSACTION_STATUS") == "VERIFIED" and (pack.get("live_transaction") or {}).get(
            "derived_from_local_fork"
        ):
            axes["LIVE_TRANSACTION_STATUS"] = "NOT_VERIFIED"
            gates["LIVE_TRANSACTION_VERIFIED"] = False
        if not (pack.get("live_transaction") or {}).get("live_tx_hash"):
            axes["LIVE_TRANSACTION_STATUS"] = "NOT_VERIFIED"
            gates["LIVE_TRANSACTION_VERIFIED"] = False

    # Never promote authority/signer/IW from runtime pack fields.
    if axes.get("AUTHORITY_STATUS") == "VERIFIED":
        prior = (pack.get("prior_axes") or {}).get("AUTHORITY_STATUS")
        if prior != "VERIFIED":
            axes["AUTHORITY_STATUS"] = prior or "NOT_VERIFIED"
    gates["AUTHORITY_VERIFIED"] = axes.get("AUTHORITY_STATUS") == "VERIFIED"

    if axes.get("SIGNER_IDENTITY_STATUS") == "VERIFIED":
        prior = (pack.get("prior_axes") or {}).get("SIGNER_IDENTITY_STATUS")
        if prior != "VERIFIED":
            axes["SIGNER_IDENTITY_STATUS"] = "NOT_VERIFIED"
    gates["RUNTIME_SIGNER_IDENTITY_VERIFIED"] = axes.get("SIGNER_IDENTITY_STATUS") == "VERIFIED"

    axes["INDEPENDENT_WITNESS_STATUS"] = (pack.get("prior_axes") or {}).get(
        "INDEPENDENT_WITNESS_STATUS", "NOT_SATISFIED"
    )
    if axes["INDEPENDENT_WITNESS_STATUS"] not in {"NOT_SATISFIED", "SATISFIED", "UNVERIFIED"}:
        axes["INDEPENDENT_WITNESS_STATUS"] = "NOT_SATISFIED"
    # Runtime verifier cannot write SATISFIED.
    if axes["INDEPENDENT_WITNESS_STATUS"] == "SATISFIED" and (pack.get("prior_axes") or {}).get(
        "INDEPENDENT_WITNESS_STATUS"
    ) != "SATISFIED":
        axes["INDEPENDENT_WITNESS_STATUS"] = "NOT_SATISFIED"
    gates["INDEPENDENT_WITNESS_VERIFIED"] = axes.get("INDEPENDENT_WITNESS_STATUS") == "SATISFIED"

    caw = pack.get("caw_verdict_snapshot") or {}
    gates["CAW_VERDICT_CHANGED"] = bool(caw.get("CAW_VERDICT_CHANGED", False))

    return {"axes": axes, "nonclaim_gates": gates}


def evidence_digests(pack: dict[str, Any]) -> dict[str, str]:
    out = {}
    for rec in pack.get("records") or []:
        lvl = str(rec.get("level") or "").upper()
        art = rec.get("artifact") or rec
        key = {
            "R0": "vr0_calldata_artifact",
            "R1": "vr1_dispatch_artifact",
            "R2": "vr2_precondition_artifact",
            "R3": "vr3_execution_artifact",
            "LIVE": "live_transaction_artifact",
        }.get(lvl, f"record_{lvl.lower()}")
        out[key] = digest(art)
    out["link_bundle"] = digest(extract_link(pack))
    if pack.get("precondition_chain") is not None:
        out["precondition_chain"] = digest(pack.get("precondition_chain"))
    if pack.get("local_fork_mutations") is not None:
        out["local_fork_mutations"] = digest(pack.get("local_fork_mutations"))
    if pack.get("result_event") is not None:
        out["result_event"] = digest(pack.get("result_event"))
    return out


def verify_runtime_evidence_v0(req: dict[str, Any]) -> dict[str, Any]:
    """Validate schema, link, ordering, classify level, preserve nonclaims."""
    created = now()
    if not isinstance(req, dict) or req.get("schema_version") != SCHEMA_VERSION:
        r = {
            "schema_version": SCHEMA_VERSION,
            "result_id": "",
            "verification_status": "REJECTED",
            "reason_codes": ["invalid_input_or_schema"],
            "errors": [_err("invalid_input_or_schema")],
            "runtime_execution_verified": False,
            "execution_authorized": False,
            "created_at": created,
        }
        r["result_id"] = rid(r)
        return r

    pack = req.get("runtime_evidence_pack") or req.get("pack") or {}
    errors: list[dict[str, str]] = []
    errors.extend(validate_pack_schema(pack))
    link = extract_link(pack) if isinstance(pack, dict) else {}
    if not errors:
        errors.extend(validate_record_bindings(pack, link))
        errors.extend(validate_local_live_separation(pack))
        errors.extend(validate_precondition_chain(pack.get("precondition_chain")))

    if errors:
        r = {
            "schema_version": SCHEMA_VERSION,
            "result_id": "",
            "verification_status": "REJECTED",
            "path_id": link.get("PATH_ID"),
            "static_runtime_link": link,
            "errors": errors,
            "reason_codes": sorted({e["code"] for e in errors}),
            "axes": {},
            "highest_runtime_level": None,
            "runtime_execution_verified": False,
            "execution_authorized": False,
            "limitations": [
                "verification only; no network/rpc/fork execution",
                "rejected pack is fail-closed",
            ],
            "created_at": created,
        }
        r["result_id"] = rid(r)
        return r

    axes_raw = classify_axes(pack, link)
    axes, axis_meta = extract_axis_meta(axes_raw)
    gated = apply_nonclaim_gates(axes, pack)
    axes = gated["axes"]
    highest = classify_highest_level(axes)
    digests = evidence_digests(pack)
    run_stage_meta = {
        "run_stages_present": axis_meta.get("run_stages_present") or [],
        "max_run_stage": axis_meta.get("max_run_stage"),
        "execution_evidence_source_stage": axis_meta.get("execution_evidence_source_stage"),
        "simulation_success": axis_meta.get("simulation_success"),
        "persistent_state_commit_observed": axis_meta.get("persistent_state_commit_observed"),
        "state_transition_observation_mode": axis_meta.get("state_transition_observation_mode"),
        "note": "RUN_STAGE is campaign chronology; highest_runtime_level is evidence capability",
    }

    # Sample-bound result event
    result_event = pack.get("result_event") or {}
    if result_event and not result_event.get("scope"):
        result_event = {**result_event, "scope": "BOUNDED_LOCAL_FORK_SAMPLE"}

    consumer_contract = {
        "schema_version": CONSUMER_CONTRACT_SCHEMA,
        "path_id": link.get("PATH_ID"),
        "join_key": "PATH_ID",
        "axes": axes,
        "highest_runtime_level": highest,
        "run_stage_meta": run_stage_meta,
        "execution_evidence_source_stage": run_stage_meta.get("execution_evidence_source_stage"),
        "static_runtime_link": {
            **link,
            "schema_version": STATIC_RUNTIME_LINK_SCHEMA,
            "EVIDENCE_DIGESTS": digests,
        },
        "precondition_chain": pack.get("precondition_chain") or [],
        "local_fork_mutations": pack.get("local_fork_mutations") or [],
        "result_event": result_event,
        "nonclaim_gates": gated["nonclaim_gates"],
        "do_not_merge_into_static_path_status": True,
    }

    # Optional authority-link reference (link-only). Never promotes authority axes
    # from runtime evidence; never completes runtime from authority presence.
    authority_link_ref = (
        req.get("authority_link")
        or req.get("authority_pack_digest")
        or pack.get("authority_link")
        or pack.get("authority_pack_digest")
    )
    authority_link_attach: dict[str, Any] | None = None
    if authority_link_ref is not None:
        # Accept opaque digest string or link object; do not merge into axes.
        if isinstance(authority_link_ref, str):
            authority_link_attach = {
                "status": "REFERENCE_RECORDED",
                "authority_pack_digest": authority_link_ref,
                "authority_promotion_refused": True,
                "runtime_completion_promotion_refused": True,
            }
        elif isinstance(authority_link_ref, dict):
            # Refuse upward authority promotion from link payload alone.
            promoted = authority_link_ref.get("AUTHORITY_STATUS") == "VERIFIED" or authority_link_ref.get(
                "promote_authority_verified"
            )
            aclass = authority_link_ref.get("AUTHORITY_CLASS")
            authority_link_attach = {
                "status": "REFERENCE_RECORDED",
                "link": {
                    "PATH_ID": authority_link_ref.get("PATH_ID") or link.get("PATH_ID"),
                    "CONTRACT_ADDRESS": authority_link_ref.get("CONTRACT_ADDRESS"),
                    "METHOD": authority_link_ref.get("METHOD"),
                    "AUTHORITY_ID": authority_link_ref.get("AUTHORITY_ID"),
                    "CALLER_GATE_CLASS": authority_link_ref.get("CALLER_GATE_CLASS"),
                    "AUTHORITY_CLASS": aclass,
                    "RUNTIME_RUN_ID": authority_link_ref.get("RUNTIME_RUN_ID"),
                    "AUTHORITY_READ_RUN_ID": authority_link_ref.get("AUTHORITY_READ_RUN_ID"),
                    "EVIDENCE_DIGEST": authority_link_ref.get("EVIDENCE_DIGEST")
                    or authority_link_ref.get("authority_pack_digest"),
                },
                "authority_promotion_refused": True,
                "runtime_completion_promotion_refused": True,
                "refused_authority_verified_promotion": bool(promoted),
            }
            # Explicitly do not write AUTHORITY_STATUS=VERIFIED from link.
            if promoted:
                axes["AUTHORITY_STATUS"] = (pack.get("prior_axes") or {}).get("AUTHORITY_STATUS") or "NOT_VERIFIED"
        else:
            authority_link_attach = {
                "status": "REFERENCE_IGNORED_BAD_TYPE",
                "authority_promotion_refused": True,
                "runtime_completion_promotion_refused": True,
            }

    r = {
        "schema_version": SCHEMA_VERSION,
        "result_id": "",
        "verification_status": "ACCEPTED",
        "path_id": link.get("PATH_ID"),
        "static_runtime_link": consumer_contract["static_runtime_link"],
        "records_verified": [
            {
                "level": rec.get("level"),
                "run_id": rec.get("run_id"),
                "status": rec.get("status") or rec.get("alignment_status"),
                "run_stage": RUN_STAGE_LABELS.get(str(rec.get("level") or "").upper(), "OTHER"),
            }
            for rec in pack.get("records") or []
        ],
        "precondition_chain": pack.get("precondition_chain") or [],
        "local_fork_mutations": pack.get("local_fork_mutations") or [],
        "result_event": result_event,
        "axes": axes,
        "STATIC_PATH_STATUS": axes["STATIC_PATH_STATUS"],
        "RUNTIME_INPUT_STATUS": axes["RUNTIME_INPUT_STATUS"],
        "RUNTIME_DISPATCH_STATUS": axes["RUNTIME_DISPATCH_STATUS"],
        "RUNTIME_PRECONDITION_STATUS": axes["RUNTIME_PRECONDITION_STATUS"],
        "RUNTIME_EXECUTION_STATUS": axes["RUNTIME_EXECUTION_STATUS"],
        "RUNTIME_STATE_TRANSITION_STATUS": axes["RUNTIME_STATE_TRANSITION_STATUS"],
        "LIVE_TRANSACTION_STATUS": axes["LIVE_TRANSACTION_STATUS"],
        "AUTHORITY_STATUS": axes["AUTHORITY_STATUS"],
        "SIGNER_IDENTITY_STATUS": axes["SIGNER_IDENTITY_STATUS"],
        "INDEPENDENT_WITNESS_STATUS": axes["INDEPENDENT_WITNESS_STATUS"],
        "highest_runtime_level": highest,
        "run_stage_meta": run_stage_meta,
        "execution_evidence_source_stage": run_stage_meta.get("execution_evidence_source_stage"),
        "evidence_digests": digests,
        "nonclaim_gates": gated["nonclaim_gates"],
        "consumer_contract": consumer_contract,
        "authority_link_attach": authority_link_attach,
        "errors": [],
        "reason_codes": [],
        "runtime_execution_verified": False,  # NG-5: never flip true for local execution
        "execution_authorized": False,
        "live_match_verified": False,
        "limitations": [
            "verifies existing evidence only; does not execute runtime",
            "LOCAL_EXECUTION_ALIGNED does not imply LIVE_TRANSACTION_VERIFIED",
            "LOCAL_EXECUTION_ALIGNED does not imply persistent state commit",
            "RUN_STAGE (VR0..VR3) is chronology; highest_runtime_level is capability",
            "does not prove authority, signer identity, IW, trustlessness, or CAW verdict",
            "optional authority_link is reference-only; refuses authority/runtime promotion",
            "result_event scope is BOUNDED_LOCAL_FORK_SAMPLE when present",
        ],
        "created_at": created,
        "design_run_id": req.get("design_run_id") or "WREID-20260912-113817-2D2509C8",
    }
    r["result_id"] = rid(r)
    return r


def attach_runtime_evidence_to_synthesizer_paths_v0(
    synthesizer_result: dict[str, Any],
    verifier_result: dict[str, Any],
) -> dict[str, Any]:
    """Thin optional consumer: attach runtime axes by PATH_ID.

    Does not merge runtime status into STATIC_PATH_STATUS / legacy path_status.
    Does not flip runtime_execution_verified.
    """
    out = json.loads(json.dumps(synthesizer_result))  # deep copy via JSON
    if not isinstance(out, dict):
        return {"error": "invalid_synthesizer_result"}
    if verifier_result.get("verification_status") != "ACCEPTED":
        out.setdefault("runtime_evidence_attach", {})
        out["runtime_evidence_attach"] = {
            "status": "SKIPPED_REJECTED_VERIFIER",
            "verifier_result_id": verifier_result.get("result_id"),
        }
        return out

    path_id = verifier_result.get("path_id")
    axes = verifier_result.get("axes") or {}
    attached = 0
    for p in out.get("paths") or []:
        if p.get("path_id") != path_id:
            continue
        # Preserve static axis.
        static_before = p.get("STATIC_PATH_STATUS")
        p["RUNTIME_INPUT_STATUS"] = axes.get("RUNTIME_INPUT_STATUS", "UNVERIFIED")
        p["RUNTIME_DISPATCH_STATUS"] = axes.get("RUNTIME_DISPATCH_STATUS", "UNVERIFIED")
        p["RUNTIME_PRECONDITION_STATUS"] = axes.get("RUNTIME_PRECONDITION_STATUS", "UNVERIFIED")
        # Refined execution axis — do not write legacy VERIFIED from local fork.
        p["RUNTIME_EXECUTION_STATUS"] = axes.get("RUNTIME_EXECUTION_STATUS", "UNVERIFIED")
        p["RUNTIME_STATE_TRANSITION_STATUS"] = axes.get("RUNTIME_STATE_TRANSITION_STATUS", "UNVERIFIED")
        p["LIVE_TRANSACTION_STATUS"] = axes.get("LIVE_TRANSACTION_STATUS", "NOT_VERIFIED")
        # Nonclaims: never promote from verifier beyond prior path values if already set.
        if p.get("AUTHORITY_STATUS") == "VERIFIED":
            pass  # keep prior static classification
        else:
            # Do not upgrade to VERIFIED via runtime.
            auth = axes.get("AUTHORITY_STATUS") or p.get("AUTHORITY_STATUS") or "NOT_VERIFIED"
            p["AUTHORITY_STATUS"] = "NOT_VERIFIED" if auth == "VERIFIED" else auth
        if p.get("SIGNER_IDENTITY_STATUS") != "VERIFIED":
            sig = axes.get("SIGNER_IDENTITY_STATUS") or p.get("SIGNER_IDENTITY_STATUS") or "NOT_VERIFIED"
            p["SIGNER_IDENTITY_STATUS"] = "NOT_VERIFIED" if sig == "VERIFIED" else sig
        p["INDEPENDENT_WITNESS_STATUS"] = p.get("INDEPENDENT_WITNESS_STATUS") or "NOT_SATISFIED"
        if p["INDEPENDENT_WITNESS_STATUS"] == "SATISFIED" and axes.get("INDEPENDENT_WITNESS_STATUS") != "SATISFIED":
            # Keep prior only if already satisfied from IW module; runtime cannot set it.
            pass
        elif axes.get("INDEPENDENT_WITNESS_STATUS") == "SATISFIED":
            p["INDEPENDENT_WITNESS_STATUS"] = "NOT_SATISFIED"
        else:
            p["INDEPENDENT_WITNESS_STATUS"] = axes.get("INDEPENDENT_WITNESS_STATUS") or "NOT_SATISFIED"

        p["runtime_evidence_level"] = verifier_result.get("highest_runtime_level")
        p["runtime_evidence_link"] = verifier_result.get("static_runtime_link")
        p["runtime_evidence_result_id"] = verifier_result.get("result_id")
        p["execution_evidence_source_stage"] = verifier_result.get("execution_evidence_source_stage")
        p["run_stage_meta"] = verifier_result.get("run_stage_meta")
        if static_before is not None:
            p["STATIC_PATH_STATUS"] = static_before
        attached += 1

    summary = out.setdefault("summary", {})
    summary["paths_with_runtime_input_aligned"] = sum(
        1 for p in out.get("paths") or [] if p.get("RUNTIME_INPUT_STATUS") == "ALIGNED"
    )
    summary["paths_with_runtime_dispatch_aligned"] = sum(
        1 for p in out.get("paths") or [] if p.get("RUNTIME_DISPATCH_STATUS") == "ALIGNED"
    )
    summary["paths_with_local_execution_aligned"] = sum(
        1 for p in out.get("paths") or [] if p.get("RUNTIME_EXECUTION_STATUS") == "LOCAL_EXECUTION_ALIGNED"
    )
    summary["paths_with_live_transaction_verified"] = sum(
        1 for p in out.get("paths") or [] if p.get("LIVE_TRANSACTION_STATUS") == "VERIFIED"
    )
    # Forbidden collapsed counters intentionally omitted.

    out["runtime_execution_verified"] = False
    out["runtime_evidence_attach"] = {
        "status": "ATTACHED" if attached else "NO_MATCHING_PATH",
        "path_id": path_id,
        "paths_attached": attached,
        "verifier_result_id": verifier_result.get("result_id"),
        "highest_runtime_level": verifier_result.get("highest_runtime_level"),
        "execution_evidence_source_stage": verifier_result.get("execution_evidence_source_stage"),
    }
    # Recompute result_id if synthesizer convention present.
    if str(out.get("result_id", "")).startswith("wrps-v0-"):
        payload = {k: v for k, v in out.items() if k != "result_id"}
        out["result_id"] = "wrps-v0-" + digest(payload)[:32]
    return out


def validate_runtime_evidence_verifier_result_v0(r: dict[str, Any]) -> list[str]:
    errs: list[str] = []
    if r.get("schema_version") != SCHEMA_VERSION:
        errs.append("bad schema_version")
    if not str(r.get("result_id", "")).startswith(RID_PREFIX):
        errs.append("bad result_id")
    if r.get("runtime_execution_verified") is not False:
        errs.append("runtime_execution_verified must be false")
    if r.get("execution_authorized") is not False:
        errs.append("execution_authorized must be false")
    if r.get("verification_status") == "ACCEPTED":
        if r.get("RUNTIME_EXECUTION_STATUS") == "LOCAL_EXECUTION_ALIGNED":
            if r.get("LIVE_TRANSACTION_STATUS") == "VERIFIED" and not (
                (r.get("nonclaim_gates") or {}).get("LIVE_TRANSACTION_VERIFIED")
                and (r.get("static_runtime_link") or {}).get("live_tx_hash")
            ):
                # Local R3 must not imply live unless separate live evidence.
                live = r.get("LIVE_TRANSACTION_STATUS")
                if live == "VERIFIED" and not (r.get("records_verified") or []):
                    errs.append("local execution must not imply live tx")
        if r.get("highest_runtime_level") == "R3_LOCAL_EXECUTION_ALIGNED":
            if r.get("LIVE_TRANSACTION_STATUS") == "VERIFIED":
                errs.append("R3 must not auto-set LIVE_TRANSACTION_VERIFIED")
        if r.get("AUTHORITY_STATUS") == "VERIFIED" and not (r.get("nonclaim_gates") or {}).get(
            "AUTHORITY_VERIFIED"
        ):
            errs.append("authority verified without gate")
        if r.get("INDEPENDENT_WITNESS_STATUS") == "SATISFIED":
            # Only allowed if prior; verifier default should be NOT_SATISFIED for runtime-only.
            pass
    if r.get("result_id") != rid({k: v for k, v in r.items() if k != "result_id"}):
        errs.append("result_id mismatch")
    return errs


def build_p0014_runtime_evidence_pack() -> dict[str, Any]:
    """Normalized pack for existing VR0→VR3 evidence (no re-execution)."""
    path_id = "wrps-v0-p0014"
    target = "0x6404d1D3D878407a0977d99C832453f235DA67C3"
    method = "createListing(uint32,uint8,address,uint256,uint256,uint64)"
    selector = "0x56926d15"
    calldata = "b267246aafdc5c0672fb008cb9611e1e36bf0465b8d0116a5d66ba925bd856ea"
    chain_id = 11155111
    fork_block = 11685854
    owner = "0x7e2aeea84a4b351e915d1c8ffa2b60dae7ef6a86"

    link = {
        "schema_version": STATIC_RUNTIME_LINK_SCHEMA,
        "PATH_ID": path_id,
        "TARGET_ADDRESS": target,
        "METHOD_SIGNATURE": method,
        "SELECTOR": selector,
        "CALLDATA_SHA256": calldata,
        "CHAIN_ID": chain_id,
        "FORK_BLOCK": fork_block,
        "RUNTIME_RUN_IDS": {
            "V_R0": "VR0P14-20260912-101043-DAE3021C",
            "V_R1": "VR1P14-20260912-105756-3BDE465A",
            "V_R2": "VR2P14-20260912-111514-D9C9AA04",
            "V_R3": "VR3P14-20260912-112620-F16EA9AD",
        },
    }

    records = [
        {
            "level": "R0",
            "run_id": "VR0P14-20260912-101043-DAE3021C",
            "status": "RUNTIME_INPUT_ALIGNMENT_VERIFIED",
            "PATH_ID": path_id,
            "TARGET_ADDRESS": target,
            "METHOD_SIGNATURE": method,
            "SELECTOR": selector,
            "CALLDATA_SHA256": calldata,
            "artifact": {
                "schema_version": INPUT_ARTIFACT_SCHEMA,
                "calldata_sha256": calldata,
                "selector": selector,
                "target_address": target,
                "method_signature": method,
            },
        },
        {
            "level": "R1",
            "run_id": "VR1P14-20260912-105756-3BDE465A",
            "status": "RUNTIME_DISPATCH_ALIGNMENT_VERIFIED",
            "PATH_ID": path_id,
            "TARGET_ADDRESS": target,
            "METHOD_SIGNATURE": method,
            "SELECTOR": selector,
            "CALLDATA_SHA256": calldata,
            "CHAIN_ID": chain_id,
            "FORK_BLOCK": fork_block,
            "precondition_class": "OWNERSHIP_PRECONDITION",
            "decoded_result_or_error": "Not token owner",
            "artifact": {
                "schema_version": DISPATCH_ARTIFACT_SCHEMA,
                "call_outcome": "CALL_REVERTED",
                "precondition_class": "OWNERSHIP_PRECONDITION",
                "decoded_error": "Not token owner",
            },
        },
        {
            "level": "R2",
            "run_id": "VR2P14-20260912-111514-D9C9AA04",
            "status": "RUNTIME_DEEPER_PATH_ALIGNMENT_VERIFIED",
            "PATH_ID": path_id,
            "TARGET_ADDRESS": target,
            "METHOD_SIGNATURE": method,
            "SELECTOR": selector,
            "CALLDATA_SHA256": calldata,
            "CHAIN_ID": chain_id,
            "FORK_BLOCK": fork_block,
            "ownership_gate": "CLEARED",
            "approval_gate": "BLOCKED",
            "next_precondition_class": "APPROVAL_PRECONDITION",
            "decoded_result_or_error": "Marketplace not approved",
            "artifact": {
                "schema_version": PRECONDITION_CHAIN_SCHEMA,
                "ownership_gate": "CLEARED",
                "next_error": "Marketplace not approved",
            },
        },
        {
            "level": "R3",
            "run_id": "VR3P14-20260912-112620-F16EA9AD",
            "status": "RUNTIME_EXECUTION_ALIGNMENT_VERIFIED",
            "PATH_ID": path_id,
            "TARGET_ADDRESS": target,
            "METHOD_SIGNATURE": method,
            "SELECTOR": selector,
            "CALLDATA_SHA256": calldata,
            "CHAIN_ID": chain_id,
            "FORK_BLOCK": fork_block,
            "call_outcome": "CALL_RETURNED_SUCCESS",
            "state_transition": "REACHED",
            "artifact": {
                "schema_version": RESULT_EVENT_SCHEMA,
                "listingId": 74,
                "event": "Listed",
                "call_outcome": "CALL_RETURNED_SUCCESS",
            },
        },
    ]

    precondition_chain = [
        {
            "PRECONDITION_ID": "p0014.ownership.gate",
            "SOURCE_LOCATION": "CawProfileMarketplace.createListing ownership check",
            "CONDITION": "msg.sender is token owner",
            "INPUT_STATE": {"token_owner": owner, "vr1_caller": "non-owner (dispatch sample)"},
            "SETUP_ACTION": {
                "type": "LOCAL_IMPERSONATION",
                "account": owner,
                "authority_claim": False,
                "introduced_at": "VR2P14-20260912-111514-D9C9AA04",
            },
            "RESULT": "CLEARED",
            "NEXT_CONDITION": "p0014.approval.gate",
            "EVIDENCE_REFERENCES": [
                "VR1P14-20260912-105756-3BDE465A",
                "VR2P14-20260912-111514-D9C9AA04",
            ],
        },
        {
            "PRECONDITION_ID": "p0014.approval.gate",
            "SOURCE_LOCATION": "CawProfileMarketplace.createListing approval check",
            "CONDITION": "isApprovedForAll(owner, Marketplace) OR getApproved(tokenId)==Marketplace",
            "INPUT_STATE": {"pre_approval": "FAIL", "token_id": 42},
            "SETUP_ACTION": {
                "type": "LOCAL_APPROVAL_TX",
                "method": "approve(address,uint256)",
                "approval_target": target,
                "authority_claim": False,
                "introduced_at": "VR3P14-20260912-112620-F16EA9AD",
            },
            "RESULT": "CLEARED",
            "NEXT_CONDITION": "SUCCESS",
            "EVIDENCE_REFERENCES": ["VR3P14-20260912-112620-F16EA9AD"],
        },
        {
            "PRECONDITION_ID": "p0014.createListing.success",
            "SOURCE_LOCATION": "CawProfileMarketplace.createListing return/event path",
            "CONDITION": "createListing completes with listing state transition",
            "INPUT_STATE": {
                "ownership_gate": "CLEARED",
                "approval_gate": "CLEARED",
                "calldata_sha256": calldata,
            },
            "SETUP_ACTION": {"type": "NONE", "authority_claim": False},
            "RESULT": "CLEARED",
            "NEXT_CONDITION": "NONE",
            "EVIDENCE_REFERENCES": ["VR3P14-20260912-112620-F16EA9AD"],
        },
    ]

    local_fork_mutations = [
        {
            "type": "ACCOUNT_IMPERSONATION",
            "mutation_scope": "LOCAL_FORK_ONLY",
            "account": owner,
            "purpose": "clear ownership gate for createListing sample",
            "authority_claim": False,
            "run_id": "VR2P14-20260912-111514-D9C9AA04",
        },
        {
            "type": "LOCAL_BALANCE_SET",
            "mutation_scope": "LOCAL_FORK_ONLY",
            "present": True,
            "run_id": "VR3P14-20260912-112620-F16EA9AD",
        },
        {
            "type": "LOCAL_APPROVAL_TX",
            "mutation_scope": "LOCAL_FORK_ONLY",
            "method": "approve(address,uint256)",
            "spender_or_operator": target,
            "token_id": 42,
            "result": "SUCCESS",
            "run_id": "VR3P14-20260912-112620-F16EA9AD",
        },
        {
            "type": "LOCAL_STATE_MUTATION",
            "mutation_scope": "LOCAL_FORK_ONLY",
            "description": "createListing listingId=74 + Listed event",
            "scope": "LOCAL_FORK_ONLY",
            "run_id": "VR3P14-20260912-112620-F16EA9AD",
        },
        {
            "type": "SNAPSHOT",
            "mutation_scope": "LOCAL_FORK_ONLY",
            "snapshot_id_or_marker": "0x1",
            "taken_before": "state_setup",
            "run_id": "VR2P14-20260912-111514-D9C9AA04",
        },
        {
            "type": "REVERT",
            "mutation_scope": "LOCAL_FORK_ONLY",
            "reverted": True,
            "run_id": "VR3P14-20260912-112620-F16EA9AD",
        },
        {
            "type": "FORK_DISPOSED",
            "mutation_scope": "LOCAL_FORK_ONLY",
            "disposed": True,
            "public_rpc_mutation": False,
            "live_tx_hash": None,
            "run_id": "VR3P14-20260912-112620-F16EA9AD",
        },
    ]

    result_event = {
        "schema_version": RESULT_EVENT_SCHEMA,
        "scope": "BOUNDED_LOCAL_FORK_SAMPLE",
        "run_id": "VR3P14-20260912-112620-F16EA9AD",
        "return_value": {"decoded": {"listingId": 74}},
        "events": [{"name": "Listed", "relevance": "listing creation path entered"}],
        "state_transition": {"kind": "listing_created", "observed": True},
        "RUNTIME_STATE_TRANSITION_STATUS": "OBSERVED_LOCAL",
        "transaction_receipt": {
            "context": "LOCAL_FORK_ONLY",
            "live_tx_hash": None,
            "public_transaction": False,
            "local_tx_hash": "0xb82d4aa7c32a1a035def268d166b2be4766017e7b39679b35772138261f1804e",
        },
    }

    return {
        "schema_version": PACK_SCHEMA,
        "path_id": path_id,
        "static_runtime_link": link,
        "records": records,
        "precondition_chain": precondition_chain,
        "local_fork_mutations": local_fork_mutations,
        "result_event": result_event,
        "live_transaction": {
            "verified": False,
            "public_transaction": False,
            "live_tx_hash": None,
            "derived_from_local_fork": False,
        },
        "prior_axes": {
            "STATIC_PATH_STATUS": "COMPLETE",
            "AUTHORITY_STATUS": "NOT_VERIFIED",
            "SIGNER_IDENTITY_STATUS": "NOT_VERIFIED",
            "INDEPENDENT_WITNESS_STATUS": "NOT_SATISFIED",
        },
        "caw_verdict_snapshot": {"CAW_VERDICT_CHANGED": False},
        "source_evidence_roots": {
            "V_R0": "C:/dev/external-verification-work/caw-runtime-vr0-p0014/VR0P14-20260912-101043-DAE3021C",
            "V_R1": "C:/dev/external-verification-work/caw-runtime-vr1-p0014/VR1P14-20260912-105756-3BDE465A",
            "V_R2": "C:/dev/external-verification-work/caw-runtime-vr2-p0014/VR2P14-20260912-111514-D9C9AA04",
            "V_R3": "C:/dev/external-verification-work/caw-runtime-vr3-p0014/VR3P14-20260912-112620-F16EA9AD",
        },
    }


def build_p0030_runtime_evidence_pack() -> dict[str, Any]:
    """Normalized pack for existing VR0→VR1 MintableCaw.mint evidence (no re-execution)."""
    path_id = "wrps-v0-p0030"
    target = "0x56817dc696448135203C0556f702c6a953260411"
    method = "mint(address,uint256)"
    selector = "0x40c10f19"
    calldata = "76dffbb3bba4336e7bbe803df8fb7c0ce58e45a7d02e9a92c8a45b52a5a0f117"
    chain_id = 11155111
    fork_block = 11686270

    link = {
        "schema_version": STATIC_RUNTIME_LINK_SCHEMA,
        "PATH_ID": path_id,
        "TARGET_ADDRESS": target,
        "METHOD_SIGNATURE": method,
        "SELECTOR": selector,
        "CALLDATA_SHA256": calldata,
        "CHAIN_ID": chain_id,
        "FORK_BLOCK": fork_block,
        "RUNTIME_RUN_IDS": {
            "V_R0": "VR0P30-20260912-121749-A0C772C8",
            "V_R1": "VR1P30-20260912-122352-6904D21C",
        },
    }

    records = [
        {
            "level": "R0",
            "run_id": "VR0P30-20260912-121749-A0C772C8",
            "status": "RUNTIME_INPUT_ALIGNMENT_VERIFIED",
            "PATH_ID": path_id,
            "TARGET_ADDRESS": target,
            "METHOD_SIGNATURE": method,
            "SELECTOR": selector,
            "CALLDATA_SHA256": calldata,
            "artifact": {
                "schema_version": INPUT_ARTIFACT_SCHEMA,
                "calldata_sha256": calldata,
                "selector": selector,
                "target_address": target,
                "method_signature": method,
            },
        },
        {
            "level": "R1",
            "run_id": "VR1P30-20260912-122352-6904D21C",
            "status": "RUNTIME_EXECUTION_ALIGNMENT_VERIFIED",
            "PATH_ID": path_id,
            "TARGET_ADDRESS": target,
            "METHOD_SIGNATURE": method,
            "SELECTOR": selector,
            "CALLDATA_SHA256": calldata,
            "CHAIN_ID": chain_id,
            "FORK_BLOCK": fork_block,
            "precondition_class": "OTHER",
            "call_outcome": "CALL_RETURNED_SUCCESS",
            "decoded_result_or_error": "SUCCESS_VOID_RETURN",
            "artifact": {
                "schema_version": DISPATCH_ARTIFACT_SCHEMA,
                "call_outcome": "CALL_RETURNED_SUCCESS",
                "precondition_class": "OTHER",
                "decoded_error": None,
                "return_data": "0x",
            },
        },
    ]

    return {
        "schema_version": PACK_SCHEMA,
        "path_id": path_id,
        "static_runtime_link": link,
        "records": records,
        "precondition_chain": [],
        "local_fork_mutations": [],
        "result_event": {},
        "simulation_success": True,
        "persistent_state_commit_observed": False,
        "state_transition_observation_mode": "SIMULATED_ONLY",
        "live_transaction": {
            "verified": False,
            "public_transaction": False,
            "live_tx_hash": None,
            "derived_from_local_fork": False,
        },
        "prior_axes": {
            "STATIC_PATH_STATUS": "COMPLETE",
            "AUTHORITY_STATUS": "NOT_VERIFIED",
            "SIGNER_IDENTITY_STATUS": "NOT_VERIFIED",
            "INDEPENDENT_WITNESS_STATUS": "NOT_SATISFIED",
        },
        "caw_verdict_snapshot": {"CAW_VERDICT_CHANGED": False},
        "source_evidence_roots": {
            "V_R0": "C:/dev/external-verification-work/caw-runtime-vr0-p0030/VR0P30-20260912-121749-A0C772C8",
            "V_R1": "C:/dev/external-verification-work/caw-runtime-vr1-p0030/VR1P30-20260912-122352-6904D21C",
        },
    }


def pack_subset(full: dict[str, Any], levels: list[str]) -> dict[str, Any]:
    """Build a pack containing only the requested record levels (for AT-01..AT-03)."""
    want = {x.upper() for x in levels}
    pack = json.loads(json.dumps(full))
    pack["records"] = [r for r in pack["records"] if str(r.get("level")).upper() in want]
    if "R3" not in want:
        pack["result_event"] = {}
        pack["precondition_chain"] = [
            g
            for g in pack.get("precondition_chain") or []
            if ("R2" in want and g["PRECONDITION_ID"] == "p0014.ownership.gate")
            or ("R1" in want and g["PRECONDITION_ID"] == "p0014.ownership.gate" and "R2" not in want)
        ]
        if "R1" in want and "R2" not in want:
            # Ownership still blocked at R1.
            for g in pack["precondition_chain"]:
                if g["PRECONDITION_ID"] == "p0014.ownership.gate":
                    g["RESULT"] = "BLOCKED"
                    g["SETUP_ACTION"] = {"type": "NONE", "authority_claim": False}
                    g["NEXT_CONDITION"] = "NONE"
                    g["EVIDENCE_REFERENCES"] = ["VR1P14-20260912-105756-3BDE465A"]
        if "R2" in want and "R3" not in want:
            # Approval still blocked.
            pack["precondition_chain"] = [
                {
                    "PRECONDITION_ID": "p0014.ownership.gate",
                    "SOURCE_LOCATION": "CawProfileMarketplace.createListing ownership check",
                    "CONDITION": "msg.sender is token owner",
                    "INPUT_STATE": {"token_owner": "0x7e2aeea84a4b351e915d1c8ffa2b60dae7ef6a86"},
                    "SETUP_ACTION": {
                        "type": "LOCAL_IMPERSONATION",
                        "authority_claim": False,
                        "account": "0x7e2aeea84a4b351e915d1c8ffa2b60dae7ef6a86",
                    },
                    "RESULT": "CLEARED",
                    "NEXT_CONDITION": "p0014.approval.gate",
                    "EVIDENCE_REFERENCES": [
                        "VR1P14-20260912-105756-3BDE465A",
                        "VR2P14-20260912-111514-D9C9AA04",
                    ],
                },
                {
                    "PRECONDITION_ID": "p0014.approval.gate",
                    "SOURCE_LOCATION": "CawProfileMarketplace.createListing approval check",
                    "CONDITION": "marketplace approved",
                    "INPUT_STATE": {"pre_approval": "FAIL"},
                    "SETUP_ACTION": {"type": "NONE", "authority_claim": False},
                    "RESULT": "BLOCKED",
                    "NEXT_CONDITION": "NONE",
                    "EVIDENCE_REFERENCES": ["VR2P14-20260912-111514-D9C9AA04"],
                },
            ]
            pack["local_fork_mutations"] = [
                m
                for m in pack.get("local_fork_mutations") or []
                if m.get("type") in {"ACCOUNT_IMPERSONATION", "SNAPSHOT", "REVERT", "FORK_DISPOSED"}
            ]
        if "R1" in want and "R2" not in want and "R3" not in want:
            pack["local_fork_mutations"] = []
        if want == {"R0"}:
            pack["precondition_chain"] = []
            pack["local_fork_mutations"] = []
            pack["result_event"] = {}
    return pack


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) == 1 and args[0] == "--emit-p0014-pack":
        print(json.dumps(build_p0014_runtime_evidence_pack(), indent=2, ensure_ascii=True))
        return 0
    if len(args) == 1 and args[0] == "--emit-p0030-pack":
        print(json.dumps(build_p0030_runtime_evidence_pack(), indent=2, ensure_ascii=True))
        return 0
    if len(args) != 1:
        sys.stderr.write(
            "usage: runtime_evidence_verifier_v0.py <input.json>\n"
            "       runtime_evidence_verifier_v0.py --emit-p0014-pack\n"
            "       runtime_evidence_verifier_v0.py --emit-p0030-pack\n"
        )
        return 1
    req = json.loads(Path(args[0]).read_text(encoding="utf-8"))
    res = verify_runtime_evidence_v0(req)
    print(json.dumps(res, indent=2, ensure_ascii=True))
    return 0 if res.get("verification_status") == "ACCEPTED" else 3


if __name__ == "__main__":
    raise SystemExit(main())
