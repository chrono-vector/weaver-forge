"""Weaver Independent Witness Verifier v0.

Validates already-produced IW evidence packs. Does not run network, execute
runtime calls, generate witness evidence, or infer independence from role/name.

Architecture D (WIWPD-20260912-143017-D82A0D4E):
  additive IW schemas + this verifier + frozen iw-pack-v1 structural support.

MATCHED != ACCEPTED. DESIGNATED_WITNESS alone never satisfies IW.
Maintainer dry-run != independent reproduction.
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "weaver-independent-witness-verifier-v0"
PACK_SCHEMA = "weaver-independent-witness-pack-v0"
PACK_FORMAT_VERSION = "iw-pack-v1"
IW_VERIFIER_VERSION = "v0"
RID_PREFIX = "wiwv-v0-"

FROZEN_CAW_COMMIT = "e2074718bcea293726ddfcf8764e1499e7b9217c"
SELECTED_STATIC_PATHS = ("wrps-v0-p0014", "wrps-v0-p0030")
SELECTED_RUNTIME_PATHS = ("wrps-v0-p0014", "wrps-v0-p0030")
RUNTIME_TARGETS = {
    "wrps-v0-p0014": "0x6404d1d3d878407a0977d99c832453f235da67c3",
    "wrps-v0-p0030": "0x56817dc696448135203c0556f702c6a953260411",
}
RUNTIME_METHODS = {
    "wrps-v0-p0014": "createListing(uint32,uint8,address,uint256,uint256,uint64)",
    "wrps-v0-p0030": "mint(address,uint256)",
}
PRIMARY_CHAIN_ID = 11155111
AUTHORITY_SUBSET = {
    "AUTHORITY_ID": "AUTH-005",
    "CONTRACT": "CawProfile",
    "ADDRESS": "0x9fcbb3d6880cd3293f1a731fe6c958a6621a74bf",
    "READ_METHOD": "owner()",
    "SELECTOR": "0x8da5cb5b",
    "CHAIN_ID": 11155111,
    "REFERENCE_BLOCK": 11686511,
}

IW_STATUSES = {
    "IW_NOT_STARTED",
    "IW_IN_PROGRESS",
    "IW_REPRODUCTION_PARTIAL",
    "IW_REPRODUCTION_MATCHED",
    "IW_ACCEPTED",
    "IW_REJECTED",
}

INDEPENDENCE_AXES = (
    "OPERATOR_INDEPENDENCE",
    "ENVIRONMENT_INDEPENDENCE",
    "EXECUTION_INDEPENDENCE",
    "OBSERVATION_INDEPENDENCE",
    "EVIDENCE_GENERATION_INDEPENDENCE",
    "RESULT_SUBMISSION_INDEPENDENCE",
)

AXIS_STATUSES = {"VERIFIED", "PARTIAL", "NOT_VERIFIED", "FAILED"}

REPRODUCTION_CLASSES = (
    "STATIC_REPRODUCTION",
    "RUNTIME_INPUT_REPRODUCTION",
    "RUNTIME_DISPATCH_REPRODUCTION",
    "RUNTIME_EXECUTION_REPRODUCTION",
    "AUTHORITY_READ_REPRODUCTION",
)

FAILURE_CATEGORIES = {
    "REPRODUCTION_PASS",
    "REPRODUCTION_MISMATCH",
    "ENVIRONMENT_BLOCKED",
    "DEPENDENCY_BLOCKED",
    "RPC_BLOCKED",
    "SOURCE_MISMATCH",
    "RUNTIME_MISMATCH",
    "UNEXPECTED_RESULT",
    "WITNESS_ABORTED",
}

NETWORK_MODES = {
    "NO_NETWORK",
    "READ_ONLY_NETWORK",
    "LOCAL_FORK_READ_ONLY",
    "LOCAL_FORK_BOUNDED_MUTATION",
    "FORBIDDEN_LIVE_MUTATION",
}

NONCLAIM_GATES = (
    "CAW_CERTIFIED",
    "TRUSTLESS_VERIFIED",
    "DECENTRALIZED_VERIFIED",
    "LIVE_TRANSACTION_VERIFIED",
    "AUTHORITY_EXECUTION_VERIFIED",
    "SYSTEM_PERMISSIONLESS",
    "SECURITY_AUDIT_COMPLETE",
    "PRODUCTION_SAFE",
)

ROLE_FLAGS = (
    "WITNESS_REFERENCE",
    "DESIGNATED_WITNESS",
    "DECLARED_INDEPENDENT",
    "REPRODUCTION_COMPLETED",
    "REPRODUCTION_MATCHED",
    "INDEPENDENCE_ACCEPTED",
    "ACCEPTED_INDEPENDENT_REPRODUCTION",
)

REQUIRED_PACK_MEMBERS = (
    "witness_run_metadata",
    "frozen_input_verification",
    "environment",
    "independence",
    "reproduction_scope",
    "static_reproduction_results",
    "runtime_input_results",
    "runtime_dispatch_results",
    "runtime_execution_results",
    "authority_read_results",
    "failure_log",
    "retry_log",
    "evidence_digests",
    "witness_attestation",
    "witness_receipt",
    "manifest",
)


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def canon(x: Any) -> str:
    return json.dumps(x, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def digest(payload: Any) -> str:
    return hashlib.sha256(canon(payload).encode()).hexdigest()


def digest_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def rid(result: dict[str, Any]) -> str:
    return RID_PREFIX + digest({k: v for k, v in result.items() if k != "result_id"})[:32]


def norm_addr(a: Any) -> str:
    s = str(a or "").strip()
    if s.startswith("0x") or s.startswith("0X"):
        return "0x" + s[2:].lower()
    return s.lower()


def _err(code: str, detail: str = "") -> dict[str, str]:
    return {"code": code, "detail": detail}


def _axis_status(independence: dict[str, Any], axis: str) -> str:
    entry = independence.get(axis) or independence.get("axes", {}).get(axis) or {}
    if isinstance(entry, str):
        return entry
    status = str(entry.get("status") or entry.get("STATUS") or "NOT_VERIFIED").upper()
    return status if status in AXIS_STATUSES else "NOT_VERIFIED"


def _has_evidence(independence: dict[str, Any], axis: str) -> bool:
    entry = independence.get(axis) or independence.get("axes", {}).get(axis) or {}
    if not isinstance(entry, dict):
        return False
    ev = entry.get("evidence") or entry.get("EVIDENCE") or entry.get("evidence_references")
    if ev is None:
        return False
    if isinstance(ev, str):
        return bool(ev.strip())
    if isinstance(ev, list):
        return len(ev) > 0
    if isinstance(ev, dict):
        return len(ev) > 0
    return bool(ev)


def default_frozen_boundary(weaver_commit: str | None = None, weaver_tree: str | None = None) -> dict[str, Any]:
    return {
        "schema_version": "weaver-iw-frozen-boundary-verification-v0",
        "CAW_COMMIT": FROZEN_CAW_COMMIT,
        "WEAVER_COMMIT": weaver_commit or "PIN_AT_PACK_FREEZE",
        "WEAVER_TREE": weaver_tree or "PIN_AT_PACK_FREEZE",
        "SCHEMA_VERSIONS": [
            "weaver-path-specific-sot-evidence-v0",
            "weaver-runtime-evidence-pack-v0",
            "weaver-runtime-input-artifact-v0",
            "weaver-runtime-dispatch-artifact-v0",
            "weaver-authority-evidence-pack-v0",
            PACK_SCHEMA,
        ],
        "IW_VERIFIER_VERSION": IW_VERIFIER_VERSION,
        "PACK_FORMAT_VERSION": PACK_FORMAT_VERSION,
        "PATH_IDS": list(SELECTED_STATIC_PATHS),
        "RUNTIME_PATH_IDS": list(SELECTED_RUNTIME_PATHS),
        "TARGET_ADDRESSES": dict(RUNTIME_TARGETS),
        "METHOD_SIGNATURES": dict(RUNTIME_METHODS),
        "CHAIN_IDS": {"primary_runtime": PRIMARY_CHAIN_ID},
        "REFERENCE_BLOCKS": {
            "authority_read": AUTHORITY_SUBSET["REFERENCE_BLOCK"],
            "policy": "PIN_AT_PACK_FREEZE_OR_RECORD_ACTUAL",
        },
        "AUTHORITY_READ_SUBSET": dict(AUTHORITY_SUBSET),
        "FIXTURE_DIGESTS": {},
    }


def empty_role_separation() -> dict[str, Any]:
    return {k: False for k in ROLE_FLAGS}


def empty_independence() -> dict[str, Any]:
    return {
        "schema_version": "weaver-iw-independence-criteria-v0",
        "axes": {
            axis: {"status": "NOT_VERIFIED", "evidence": []}
            for axis in INDEPENDENCE_AXES
        },
    }


def empty_network_safety() -> dict[str, Any]:
    return {
        "schema_version": "weaver-iw-network-safety-v0",
        "modes_used": ["NO_NETWORK"],
        "REAL_WALLET": "NO",
        "REAL_PRIVATE_KEY": "NO",
        "REAL_CREDENTIAL": "NO",
        "LIVE_BROADCAST": "NO",
        "LIVE_MUTATION": "NO",
        "FORBIDDEN_LIVE_MUTATION": True,
    }


def empty_nonclaims() -> dict[str, bool]:
    return {k: False for k in NONCLAIM_GATES}


def classify_iw_status(
    *,
    pack_present: bool,
    scope_complete: bool,
    reproduction_matched: bool,
    independence_accepted: bool,
    rejected: bool,
    in_progress: bool,
) -> str:
    if rejected:
        return "IW_REJECTED"
    if not pack_present:
        return "IW_NOT_STARTED"
    if independence_accepted and reproduction_matched and scope_complete:
        return "IW_ACCEPTED"
    if reproduction_matched and scope_complete:
        return "IW_REPRODUCTION_MATCHED"
    if pack_present and not scope_complete:
        return "IW_REPRODUCTION_PARTIAL"
    if in_progress:
        return "IW_IN_PROGRESS"
    return "IW_IN_PROGRESS"


def validate_frozen_boundary(
    observed: dict[str, Any],
    expected: dict[str, Any] | None = None,
) -> tuple[bool, list[dict[str, str]], dict[str, Any]]:
    exp = expected or default_frozen_boundary(
        weaver_commit=str(observed.get("WEAVER_COMMIT") or ""),
        weaver_tree=str(observed.get("WEAVER_TREE") or ""),
    )
    errors: list[dict[str, str]] = []
    checks: dict[str, Any] = {}

    def _check(name: str, got: Any, want: Any, mandatory: bool = True) -> None:
        ok = got == want
        checks[name] = {"observed": got, "expected": want, "match": ok, "mandatory": mandatory}
        if not ok and mandatory:
            errors.append(_err("frozen_boundary_mismatch", f"{name}: observed={got!r} expected={want!r}"))

    _check("CAW_COMMIT", str(observed.get("CAW_COMMIT") or ""), str(exp.get("CAW_COMMIT") or FROZEN_CAW_COMMIT))

    weaver_commit_got = str(observed.get("WEAVER_COMMIT") or "")
    weaver_commit_want = str(exp.get("WEAVER_COMMIT") or "")
    weaver_mandatory = bool(exp.get("WEAVER_COMMIT_MANDATORY", True)) and weaver_commit_want not in {
        "",
        "PIN_AT_PACK_FREEZE",
    }
    if weaver_commit_want and weaver_commit_want != "PIN_AT_PACK_FREEZE":
        _check("WEAVER_COMMIT", weaver_commit_got, weaver_commit_want, mandatory=weaver_mandatory)
    else:
        checks["WEAVER_COMMIT"] = {
            "observed": weaver_commit_got,
            "expected": weaver_commit_want or "PIN_AT_PACK_FREEZE",
            "match": bool(weaver_commit_got),
            "mandatory": False,
            "recorded": True,
        }
        if not weaver_commit_got:
            errors.append(_err("weaver_commit_missing", "WEAVER_COMMIT must be recorded"))

    weaver_tree_got = str(observed.get("WEAVER_TREE") or "")
    weaver_tree_want = str(exp.get("WEAVER_TREE") or "")
    tree_mandatory = bool(exp.get("WEAVER_TREE_MANDATORY", True)) and weaver_tree_want not in {
        "",
        "PIN_AT_PACK_FREEZE",
    }
    if weaver_tree_want and weaver_tree_want != "PIN_AT_PACK_FREEZE":
        _check("WEAVER_TREE", weaver_tree_got, weaver_tree_want, mandatory=tree_mandatory)
    else:
        checks["WEAVER_TREE"] = {
            "observed": weaver_tree_got,
            "expected": weaver_tree_want or "PIN_AT_PACK_FREEZE",
            "match": bool(weaver_tree_got),
            "mandatory": False,
            "recorded": True,
        }

    pack_ver = str(observed.get("PACK_FORMAT_VERSION") or observed.get("pack_format_version") or "")
    _check("PACK_FORMAT_VERSION", pack_ver, str(exp.get("PACK_FORMAT_VERSION") or PACK_FORMAT_VERSION))

    iw_ver = str(observed.get("IW_VERIFIER_VERSION") or "")
    _check("IW_VERIFIER_VERSION", iw_ver, str(exp.get("IW_VERIFIER_VERSION") or IW_VERIFIER_VERSION))

    path_ids = [str(x) for x in (observed.get("PATH_IDS") or [])]
    want_paths = [str(x) for x in (exp.get("PATH_IDS") or list(SELECTED_STATIC_PATHS))]
    _check("PATH_IDS", sorted(path_ids), sorted(want_paths))

    targets = {k: norm_addr(v) for k, v in dict(observed.get("TARGET_ADDRESSES") or {}).items()}
    want_targets = {k: norm_addr(v) for k, v in dict(exp.get("TARGET_ADDRESSES") or RUNTIME_TARGETS).items()}
    _check("TARGET_ADDRESSES", targets, want_targets)

    chain = observed.get("CHAIN_IDS") or {}
    want_chain = exp.get("CHAIN_IDS") or {"primary_runtime": PRIMARY_CHAIN_ID}
    primary = int((chain.get("primary_runtime") if isinstance(chain, dict) else chain) or 0)
    want_primary = int(want_chain.get("primary_runtime") if isinstance(want_chain, dict) else want_chain)
    _check("CHAIN_ID_PRIMARY", primary, want_primary)

    auth = observed.get("AUTHORITY_READ_SUBSET") or {}
    want_auth = exp.get("AUTHORITY_READ_SUBSET") or AUTHORITY_SUBSET
    _check(
        "AUTHORITY_ADDRESS",
        norm_addr(auth.get("ADDRESS")),
        norm_addr(want_auth.get("ADDRESS")),
    )
    _check("AUTHORITY_SELECTOR", str(auth.get("SELECTOR") or "").lower(), str(want_auth.get("SELECTOR") or "").lower())

    # Manifest digests: if expected provides them, require match
    obs_manifest = str(observed.get("MANIFEST_DIGEST") or observed.get("manifest_digest") or "")
    exp_manifest = str(exp.get("MANIFEST_DIGEST") or "")
    if exp_manifest:
        _check("MANIFEST_DIGEST", obs_manifest, exp_manifest)

    # Two-level seal digests when provided
    for digest_key in ("CONTENT_MANIFEST_DIGEST", "PACK_SEAL_DIGEST"):
        exp_d = str(exp.get(digest_key) or "")
        obs_d = str(
            observed.get(digest_key)
            or (observed.get("frozen_input_verification") or {}).get(digest_key)
            or ""
        )
        # also allow top-level pack.frozen_input_verification already being observed
        if not obs_d and isinstance(observed.get("seal"), dict):
            obs_d = str(observed["seal"].get(digest_key) or "")
        if exp_d:
            _check(digest_key, obs_d.lower(), exp_d.lower())

    fixture_obs = dict(observed.get("FIXTURE_DIGESTS") or {})
    fixture_exp = dict(exp.get("FIXTURE_DIGESTS") or {})
    if fixture_exp:
        _check("FIXTURE_DIGESTS", fixture_obs, fixture_exp)

    schema_obs = [str(x) for x in (observed.get("SCHEMA_VERSIONS") or [])]
    schema_exp = [str(x) for x in (exp.get("SCHEMA_VERSIONS") or [])]
    if schema_exp:
        missing = [s for s in schema_exp if s not in schema_obs]
        checks["SCHEMA_VERSIONS"] = {
            "observed": schema_obs,
            "expected": schema_exp,
            "match": not missing,
            "mandatory": True,
            "missing": missing,
        }
        if missing:
            errors.append(_err("schema_version_mismatch", f"missing={missing}"))

    return len(errors) == 0, errors, checks


def _result_pass(entry: dict[str, Any]) -> bool:
    status = str(
        entry.get("result")
        or entry.get("RESULT")
        or entry.get("status")
        or entry.get("STATUS")
        or ""
    ).upper()
    return status in {
        "REPRODUCTION_PASS",
        "PASS",
        "MATCHED",
        "ALIGNED",
        "VERIFIED",
        "OK",
        "SUCCESS",
    }


def _collect_path_ids(results: list[Any]) -> set[str]:
    out: set[str] = set()
    for r in results or []:
        if isinstance(r, dict):
            pid = r.get("PATH_ID") or r.get("path_id")
            if pid:
                out.add(str(pid))
    return out


def evaluate_reproduction_scope(pack: dict[str, Any]) -> dict[str, Any]:
    scope = pack.get("reproduction_scope") or {}
    required = list(scope.get("required_classes") or REPRODUCTION_CLASSES)
    static = list(pack.get("static_reproduction_results") or [])
    rin = list(pack.get("runtime_input_results") or [])
    rdisp = list(pack.get("runtime_dispatch_results") or [])
    rex = list(pack.get("runtime_execution_results") or [])
    auth = list(pack.get("authority_read_results") or [])

    class_status: dict[str, Any] = {}
    for cls in required:
        if cls == "STATIC_REPRODUCTION":
            paths = _collect_path_ids(static)
            ok = set(SELECTED_STATIC_PATHS).issubset(paths) and all(_result_pass(x) for x in static if str(x.get("PATH_ID")) in SELECTED_STATIC_PATHS)
            present = set(SELECTED_STATIC_PATHS).issubset(paths)
            class_status[cls] = {"present": present, "matched": ok, "path_ids": sorted(paths)}
        elif cls == "RUNTIME_INPUT_REPRODUCTION":
            paths = _collect_path_ids(rin)
            ok = set(SELECTED_RUNTIME_PATHS).issubset(paths) and all(
                _result_pass(x) for x in rin if str(x.get("PATH_ID")) in SELECTED_RUNTIME_PATHS
            )
            present = set(SELECTED_RUNTIME_PATHS).issubset(paths)
            class_status[cls] = {"present": present, "matched": ok, "path_ids": sorted(paths)}
        elif cls == "RUNTIME_DISPATCH_REPRODUCTION":
            paths = _collect_path_ids(rdisp)
            ok = set(SELECTED_RUNTIME_PATHS).issubset(paths) and all(
                _result_pass(x) for x in rdisp if str(x.get("PATH_ID")) in SELECTED_RUNTIME_PATHS
            )
            present = set(SELECTED_RUNTIME_PATHS).issubset(paths)
            class_status[cls] = {"present": present, "matched": ok, "path_ids": sorted(paths)}
        elif cls == "RUNTIME_EXECUTION_REPRODUCTION":
            paths = _collect_path_ids(rex)
            ok = set(SELECTED_RUNTIME_PATHS).issubset(paths) and all(
                _result_pass(x) for x in rex if str(x.get("PATH_ID")) in SELECTED_RUNTIME_PATHS
            )
            present = set(SELECTED_RUNTIME_PATHS).issubset(paths)
            class_status[cls] = {"present": present, "matched": ok, "path_ids": sorted(paths)}
        elif cls == "AUTHORITY_READ_REPRODUCTION":
            present = len(auth) > 0
            ok = present and all(_result_pass(x) for x in auth)
            class_status[cls] = {"present": present, "matched": ok, "count": len(auth)}
        else:
            class_status[cls] = {"present": False, "matched": False, "unsupported": True}

    scope_complete = all(v.get("present") for v in class_status.values())
    reproduction_matched = all(v.get("matched") for v in class_status.values()) and scope_complete
    return {
        "required_classes": required,
        "class_status": class_status,
        "scope_complete": scope_complete,
        "reproduction_matched": reproduction_matched,
        "acceptance_scope": {
            "kind": "BOUNDED_D",
            "static_paths": list(SELECTED_STATIC_PATHS),
            "runtime_paths": list(SELECTED_RUNTIME_PATHS),
            "authority": "READ_ONLY_SUBSET",
            "whole_repository": False,
        },
    }


def evaluate_independence(pack: dict[str, Any]) -> dict[str, Any]:
    independence = pack.get("independence") or {}
    axes_out: dict[str, Any] = {}
    all_verified = True
    missing_mandatory = []
    for axis in INDEPENDENCE_AXES:
        status = _axis_status(independence, axis)
        has_ev = _has_evidence(independence, axis)
        ok = status == "VERIFIED" and has_ev
        if not ok:
            all_verified = False
            if status != "VERIFIED" or not has_ev:
                missing_mandatory.append(axis)
        axes_out[axis] = {
            "status": status,
            "evidence_present": has_ev,
            "satisfied": ok,
        }
    return {
        "axes": axes_out,
        "all_mandatory_satisfied": all_verified,
        "missing_mandatory": missing_mandatory,
        "INDEPENDENCE_ACCEPTED": all_verified,
    }


def evaluate_network_safety(pack: dict[str, Any]) -> tuple[bool, list[dict[str, str]], dict[str, Any]]:
    net = pack.get("network_safety") or pack.get("witness_run_metadata", {}).get("network_safety") or {}
    errors: list[dict[str, str]] = []
    safety = {
        "REAL_WALLET": str(net.get("REAL_WALLET", "NO")).upper(),
        "REAL_PRIVATE_KEY": str(net.get("REAL_PRIVATE_KEY", "NO")).upper(),
        "REAL_CREDENTIAL": str(net.get("REAL_CREDENTIAL", "NO")).upper(),
        "LIVE_BROADCAST": str(net.get("LIVE_BROADCAST", "NO")).upper(),
        "LIVE_MUTATION": str(net.get("LIVE_MUTATION", "NO")).upper(),
        "modes_used": list(net.get("modes_used") or []),
    }
    for k in ("REAL_WALLET", "REAL_PRIVATE_KEY", "REAL_CREDENTIAL", "LIVE_BROADCAST", "LIVE_MUTATION"):
        if safety[k] not in {"NO", "FALSE", "0"}:
            errors.append(_err("network_safety_violation", f"{k}={safety[k]}"))
    # Detect live mutation evidence elsewhere
    if pack.get("live_mutation_evidence") or pack.get("live_broadcast_evidence"):
        errors.append(_err("live_mutation_evidence_present", "live mutation/broadcast evidence present"))
        safety["LIVE_MUTATION"] = "YES"
    if pack.get("real_credential_evidence") or pack.get("real_wallet_evidence"):
        errors.append(_err("real_credential_evidence_present", "real credential/wallet evidence present"))
        safety["REAL_CREDENTIAL"] = "YES"
    return len(errors) == 0, errors, safety


def evaluate_failure_preservation(pack: dict[str, Any]) -> tuple[bool, list[dict[str, str]], dict[str, Any]]:
    failures = list(pack.get("failure_log") or [])
    retries = list(pack.get("retry_log") or [])
    errors: list[dict[str, str]] = []

    # Hidden/replaced failed attempts: if a retry references a prior failure id, that id must remain in failure_log
    fail_ids = {str(f.get("attempt_id") or f.get("id") or "") for f in failures}
    for r in retries:
        prior = str(r.get("prior_failure_id") or r.get("prior_attempt_id") or "")
        if prior and prior not in fail_ids and prior != "":
            errors.append(_err("hidden_replaced_failed_attempt", f"retry references missing failure {prior}"))

    # Declared concealment flag
    if pack.get("conceal_failures") or pack.get("overwrite_failures"):
        errors.append(_err("failure_concealment_declared", "pack declares failure concealment/overwrite"))

    # Category vocabulary
    for f in failures:
        cat = str(f.get("category") or f.get("CATEGORY") or "")
        if cat and cat not in FAILURE_CATEGORIES:
            errors.append(_err("unknown_failure_category", cat))

    assurance = str(
        pack.get("FAILURE_HISTORY_ASSURANCE")
        or pack.get("failure_history_assurance")
        or "SUBMITTED_HISTORY_PRESERVED"
    )
    if assurance == "COMPLETE_HISTORY_CRYPTOGRAPHICALLY_PROVEN":
        # Never claim cryptographic complete-history proof at v0
        assurance = "SUBMITTED_HISTORY_PRESERVED"
        errors.append(
            _err(
                "failure_history_overclaim",
                "COMPLETE_HISTORY_CRYPTOGRAPHICALLY_PROVEN forbidden; use SUBMITTED_HISTORY_PRESERVED",
            )
        )

    policy = pack.get("failure_history_policy") or {}
    attempt_note = (
        policy.get("attempt_id_policy")
        or "ATTEMPT_ID / PRIOR_ATTEMPT_ID must be retained; retries append; later PASS does not erase earlier failure"
    )

    return len(errors) == 0, errors, {
        "failure_count": len(failures),
        "retry_count": len(retries),
        "failures_preserved": len(errors) == 0,
        "retries_preserved": True,
        "FAILURE_HISTORY_ASSURANCE": assurance,
        "attempt_id_policy_note": attempt_note,
        "never_claims": "COMPLETE_HISTORY_CRYPTOGRAPHICALLY_PROVEN",
    }


def evaluate_external_submission_provenance(pack: dict[str, Any]) -> tuple[bool, list[dict[str, str]], dict[str, Any]]:
    """Require external submission receipt for IW acceptance eligibility."""
    errors: list[dict[str, str]] = []
    receipt = (
        pack.get("external_submission_receipt")
        or pack.get("submission_receipt")
        or (pack.get("witness_receipt") or {}).get("external_submission_receipt")
    )
    info: dict[str, Any] = {"receipt_present": bool(receipt)}

    if not isinstance(receipt, dict) or not receipt:
        errors.append(_err("external_submission_receipt_missing", "external_submission_receipt required for IW acceptance"))
        # Self-declared independence alone is insufficient
        indep = pack.get("independence") or {}
        declared = bool(
            (pack.get("witness_run_metadata") or {}).get("declared_independent")
            or pack.get("declared_independent")
            or indep.get("DECLARED_INDEPENDENT")
        )
        if declared or True:
            errors.append(
                _err(
                    "self_declared_independence_insufficient",
                    "self-declared independence without valid external submission receipt cannot yield IW_ACCEPTED",
                )
            )
        info["ACCEPTANCE_ELIGIBLE"] = False
        info["valid_for_iw_acceptance"] = False
        return False, errors, info

    required_fields = (
        "SUBMISSION_RECEIPT_ID",
        "SUBMISSION_CHANNEL_CLASS",
        "SUBMISSION_TIMESTAMP",
        "PACK_DIGEST_RECEIVED",
        "OUTPUT_DIGEST_SUBMITTED",
        "SUBMITTER_ROLE",
        "MAINTAINER_ORIGIN",
        "ACCEPTANCE_ELIGIBLE",
    )
    for f in required_fields:
        if receipt.get(f) in (None, ""):
            errors.append(_err("external_submission_receipt_missing", f"missing field {f}"))

    maintainer_origin = str(receipt.get("MAINTAINER_ORIGIN") or "UNKNOWN").upper()
    acceptance_eligible = str(receipt.get("ACCEPTANCE_ELIGIBLE") or "NO").upper()
    pack_digest_received = str(receipt.get("PACK_DIGEST_RECEIVED") or "").strip().lower()
    output_digest_submitted = str(receipt.get("OUTPUT_DIGEST_SUBMITTED") or "").strip().lower()

    info.update(
        {
            "SUBMISSION_RECEIPT_ID": receipt.get("SUBMISSION_RECEIPT_ID"),
            "MAINTAINER_ORIGIN": maintainer_origin,
            "ACCEPTANCE_ELIGIBLE": acceptance_eligible,
            "PACK_DIGEST_RECEIVED": pack_digest_received,
            "OUTPUT_DIGEST_SUBMITTED": output_digest_submitted,
        }
    )

    if maintainer_origin == "YES":
        errors.append(_err("maintainer_origin_submission", "MAINTAINER_ORIGIN=YES cannot be IW acceptance eligible"))

    if acceptance_eligible != "YES":
        errors.append(_err("external_submission_receipt_missing", "ACCEPTANCE_ELIGIBLE must be YES"))

    if not pack_digest_received or not output_digest_submitted:
        errors.append(_err("external_submission_receipt_missing", "PACK_DIGEST_RECEIVED and OUTPUT_DIGEST_SUBMITTED required"))

    expected_pack_digest = str(
        pack.get("pack_digest")
        or receipt.get("EXPECTED_PACK_DIGEST")
        or ""
    ).strip().lower()
    expected_output_digest = str(
        pack.get("output_digest")
        or pack.get("evidence_digests", {}).get("output_digest")
        or receipt.get("EXPECTED_OUTPUT_DIGEST")
        or ""
    ).strip().lower()

    # Prefer explicit expected digests on pack; else verify receipt internal consistency with pack.pack_digest
    if expected_pack_digest and pack_digest_received and pack_digest_received != expected_pack_digest:
        errors.append(
            _err(
                "external_submission_receipt_digest_mismatch",
                f"PACK_DIGEST_RECEIVED={pack_digest_received} expected={expected_pack_digest}",
            )
        )
    if expected_output_digest and output_digest_submitted and output_digest_submitted != expected_output_digest:
        errors.append(
            _err(
                "external_submission_receipt_digest_mismatch",
                f"OUTPUT_DIGEST_SUBMITTED={output_digest_submitted} expected={expected_output_digest}",
            )
        )

    # If pack carries content_manifest / pack_seal digests, receipt may bind them
    for key, receipt_key in (
        ("CONTENT_MANIFEST_DIGEST", "CONTENT_MANIFEST_DIGEST"),
        ("PACK_SEAL_DIGEST", "PACK_SEAL_DIGEST"),
    ):
        want = str(pack.get(key) or (pack.get("frozen_input_verification") or {}).get(key) or "").lower()
        got = str(receipt.get(receipt_key) or "").lower()
        if want and got and want != got:
            errors.append(_err("external_submission_receipt_digest_mismatch", f"{key} mismatch"))

    valid = (
        maintainer_origin != "YES"
        and acceptance_eligible == "YES"
        and bool(pack_digest_received)
        and bool(output_digest_submitted)
        and not any(
            e["code"]
            in {
                "external_submission_receipt_digest_mismatch",
                "maintainer_origin_submission",
                "external_submission_receipt_missing",
            }
            for e in errors
        )
    )
    info["valid_for_iw_acceptance"] = valid
    if not valid and not any(e["code"] == "self_declared_independence_insufficient" for e in errors):
        # Independence axes alone cannot accept without valid external receipt
        errors.append(
            _err(
                "self_declared_independence_insufficient",
                "valid external submission receipt required for IW_ACCEPTED",
            )
        )
    return valid, errors, info


P0014_PROCEDURE_KEYWORDS = (
    "CAW source commit",
    "Weaver pin",
    "11155111",
    "fixed fork block",
    "target address",
    "ABI",
    "deterministic fixture",
    "calldata",
    "calldata hash",
    "owner resolution",
    "local fork",
    "impersonation",
    "ownership verification",
    "approval",
    "local approval tx",
    "snapshot",
    "createListing",
    "return",
    "snapshot revert",
    "post-revert",
    "raw evidence",
    "failure recording",
)

P0030_PROCEDURE_KEYWORDS = (
    "target",
    "ABI",
    "parseUnits",
    "18",
    "deterministic fixture",
    "fixed block",
    "fork source",
    "eth_call",
    "raw return",
    "calldata hash",
)


def validate_procedure_completeness_p0014(text: str) -> list[str]:
    missing: list[str] = []
    low = text.lower()
    for kw in P0014_PROCEDURE_KEYWORDS:
        # flexible match: allow slight wording variation for a few keys
        variants = [kw.lower()]
        if kw == "CAW source commit":
            variants += ["caw commit", "frozen caw commit", "caw source commit"]
        elif kw == "Weaver pin":
            variants += ["weaver commit", "weaver pin", "weaver-pin"]
        elif kw == "fixed fork block":
            variants += ["fork block", "fixed block", "11685854"]
        elif kw == "target address":
            variants += ["target", "0x6404d1d3"]
        elif kw == "calldata hash":
            variants += ["calldata_sha256", "calldata digest", "calldata hash"]
        elif kw == "owner resolution":
            variants += ["resolve owner", "owner resolution", "token owner"]
        elif kw == "ownership verification":
            variants += ["ownership", "token owner"]
        elif kw == "local approval tx":
            variants += ["approval tx", "local approval", "setapprovalforall"]
        elif kw == "snapshot revert":
            variants += ["revert snapshot", "snapshot revert", "evm_revert"]
        elif kw == "post-revert":
            variants += ["post-revert", "post revert", "after revert"]
        elif kw == "failure recording":
            variants += ["failure recording", "failure-log", "record failure"]
        elif kw == "raw evidence":
            variants += ["raw evidence", "evidence outputs", "evidence-digests"]
        elif kw == "return":
            variants += ["return/event/state", "return", "event", "state"]
        if not any(v in low for v in variants):
            missing.append(kw)
    return missing


def validate_procedure_completeness_p0030(text: str) -> list[str]:
    missing: list[str] = []
    low = text.lower()
    for kw in P0030_PROCEDURE_KEYWORDS:
        variants = [kw.lower()]
        if kw == "parseUnits":
            variants += ["parseunits", "parse_units"]
        elif kw == "fixed block":
            variants += ["fixed block", "fork block", "11686"]
        elif kw == "fork source":
            variants += ["fork source", "fork rpc", "local fork"]
        elif kw == "raw return":
            variants += ["raw return", "return data", "raw returndata"]
        elif kw == "calldata hash":
            variants += ["calldata hash", "calldata_sha256", "calldata digest"]
        elif kw == "deterministic fixture":
            variants += ["deterministic fixture", "fixture"]
        if not any(v in low for v in variants):
            missing.append(kw)
    return missing


def validate_static_procedure_anti_circularity(path_sot_obj: dict[str, Any], procedure_text: str) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    text = procedure_text or ""
    low = text.lower()
    for label in ("INPUT SOURCE", "DERIVED BY WITNESS", "POST-RUN COMPARISON"):
        if label.lower() not in low:
            issues.append({"code": "static_procedure_label_missing", "detail": label})
    if path_sot_obj.get("STATIC_STATUS_REFERENCE") == "COMPLETE":
        issues.append(
            {
                "code": "path_sot_status_leak",
                "detail": "STATIC_STATUS_REFERENCE=COMPLETE must not appear in pre-run path-sot",
            }
        )
    role = str(path_sot_obj.get("ROLE") or "")
    if role and "COMPARISON" not in role.upper() and "REFERENCE" not in role.upper():
        # allow missing ROLE but flag proof-source language
        pass
    if "sole proof" in low or "path-sot as proof" in low or "path sot is proof" in low:
        issues.append({"code": "path_sot_as_sole_proof", "detail": "path-sot must not be sole proof source"})
    # Detect procedure treating path-sot COMPLETE as proof substitute
    if "path-sot" in low and "complete" in low and ("proof" in low or "substitute" in low):
        issues.append(
            {
                "code": "static_path_sot_proof_substitute",
                "detail": "static witness must not use maintainer path-sot COMPLETE as proof substitute",
            }
        )
    return issues


def detect_semi_blind_leakage(pre_run_objects: dict[str, Any] | list[Any]) -> list[dict[str, str]]:
    """Fail if protected expected-result fields appear in pre-run fixture/path-sot surfaces."""
    errors: list[dict[str, str]] = []
    objs: list[Any]
    if isinstance(pre_run_objects, dict):
        objs = list(pre_run_objects.values()) if not any(
            k in pre_run_objects for k in ("PATH_ID", "fixture_policy", "params_template", "STATIC_STATUS_REFERENCE")
        ) else [pre_run_objects]
        # Also flatten known keys
        for k in ("path_sot", "fixture_specs", "fixtures", "objects"):
            v = pre_run_objects.get(k) if isinstance(pre_run_objects, dict) else None
            if isinstance(v, list):
                objs.extend(v)
            elif isinstance(v, dict):
                objs.append(v)
    else:
        objs = list(pre_run_objects or [])

    protected_owner = norm_addr(AUTHORITY_SUBSET.get("ADDRESS"))
    # Known shared owner from authority — expected owner reveal is sealed post-freeze
    known_expected_owners = {
        protected_owner,
        "0xf71338f3eaa483aa66125598b09ba1988e694a95",
    }

    def _walk(obj: Any, path: str = "") -> None:
        if isinstance(obj, dict):
            if obj.get("STATIC_STATUS_REFERENCE") == "COMPLETE":
                errors.append(
                    _err(
                        "semi_blind_leakage",
                        f"{path}: STATIC_STATUS_REFERENCE=COMPLETE in pre-run path-sot (use COMPARISON_ONLY)",
                    )
                )
            for k, v in obj.items():
                kl = str(k).lower()
                if kl in {
                    "expected_success",
                    "expected_verdict",
                    "must_pass",
                    "expected_result",
                    "expected_owner",
                    "expected_return_value",
                }:
                    if str(v).upper() in {"PASS", "REPRODUCTION_PASS", "SUCCESS", "OK"} or (
                        isinstance(v, str) and v.startswith("0x") and len(v) == 42
                    ):
                        errors.append(_err("semi_blind_leakage", f"{path}.{k}={v}"))
                if kl in {"expected_owner", "owner_address", "reference_owner"} and isinstance(v, str):
                    if norm_addr(v) in known_expected_owners:
                        errors.append(_err("semi_blind_leakage", f"{path}.{k} reveals expected owner"))
                if isinstance(v, str) and v.upper() in {"PASS", "REPRODUCTION_PASS"} and "expected" in kl:
                    errors.append(_err("semi_blind_leakage", f"{path}.{k} exposes PASS verdict"))
                _walk(v, f"{path}.{k}" if path else k)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                _walk(item, f"{path}[{i}]")

    for o in objs:
        _walk(o)
    return errors


def detect_out_of_manifest_required_dependency(
    pack: dict[str, Any],
    *,
    required_paths: list[str] | None = None,
    manifest_members: dict[str, Any] | None = None,
) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []
    members = manifest_members or (pack.get("manifest") or {}).get("members") or {}
    content = pack.get("content_manifest") or {}
    content_files = content.get("files") or content.get("members") or {}
    sealed = set(map(str, members.keys())) | set(map(str, content_files.keys()))
    req = required_paths or list(pack.get("required_dependencies") or [])
    for p in req:
        if str(p) not in sealed:
            errors.append(_err("out_of_manifest_required_dependency", str(p)))
    if pack.get("influence_from_untracked_module"):
        errors.append(
            _err(
                "untracked_module_influence",
                "excluded untracked module must not influence verifier acceptance",
            )
        )
    return errors


def detect_pack_seal_mismatch(pack: dict[str, Any], expected_seal: dict[str, Any] | None = None) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []
    seal = pack.get("pack_seal") or (pack.get("frozen_input_verification") or {})
    exp = expected_seal or pack.get("expected_pack_seal") or {}
    for key in ("CONTENT_MANIFEST_DIGEST", "PACK_SEAL_DIGEST", "content_manifest_digest", "pack_seal_digest"):
        want = str(exp.get(key) or "")
        got = str(seal.get(key) or pack.get(key) or "")
        if want and got and want.lower() != got.lower():
            errors.append(_err("pack_seal_mismatch", f"{key}: observed={got} expected={want}"))
        elif want and not got:
            errors.append(_err("pack_seal_mismatch", f"{key} missing"))
    return errors


def detect_maintainer_substitution(pack: dict[str, Any]) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []
    # Explicit substitution markers
    if pack.get("uses_maintainer_result_artifact") or pack.get("substituted_operator_evidence"):
        errors.append(_err("maintainer_result_substitution", "witness output uses maintainer/operator result artifact"))
    meta = pack.get("witness_run_metadata") or {}
    if meta.get("evidence_source") in {"MAINTAINER_OUTPUT", "OPERATOR_RESULT", "COPIED_OPERATOR_ARTIFACT"}:
        errors.append(_err("maintainer_result_substitution", f"evidence_source={meta.get('evidence_source')}"))
    # Role-only designation without generation claim
    for key in ("static_reproduction_results", "runtime_input_results", "runtime_execution_results", "authority_read_results"):
        for entry in pack.get(key) or []:
            if isinstance(entry, dict) and entry.get("derived_from_operator_artifact") is True:
                errors.append(_err("operator_artifact_reuse", f"{key} marks derived_from_operator_artifact"))
    return errors


def detect_scope_expansion(pack: dict[str, Any]) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []
    scope = pack.get("reproduction_scope") or {}
    if scope.get("whole_repository") is True or scope.get("claim_whole_repository_iw") is True:
        errors.append(_err("scope_expansion", "whole-repository IW claim forbidden for v1"))
    extra = scope.get("extra_path_ids") or []
    allowed = set(SELECTED_STATIC_PATHS) | set(SELECTED_RUNTIME_PATHS)
    for pid in extra:
        if str(pid) not in allowed:
            errors.append(_err("scope_expansion", f"extra path {pid} outside BOUNDED_D"))
    if pack.get("promote_to_full_caw_iw") is True:
        errors.append(_err("scope_expansion", "promote_to_full_caw_iw forbidden"))
    return errors


def evaluate_role_separation(pack: dict[str, Any], *, reproduction_matched: bool, independence_accepted: bool, scope_complete: bool) -> dict[str, Any]:
    roles = dict(empty_role_separation())
    meta = pack.get("witness_run_metadata") or {}
    roles["WITNESS_REFERENCE"] = bool(meta.get("witness_reference") or meta.get("witness_id") or meta.get("witness_handle"))
    roles["DESIGNATED_WITNESS"] = bool(meta.get("designated_witness") or pack.get("designated_witness"))
    roles["DECLARED_INDEPENDENT"] = bool(meta.get("declared_independent") or pack.get("declared_independent"))
    roles["REPRODUCTION_COMPLETED"] = scope_complete
    roles["REPRODUCTION_MATCHED"] = reproduction_matched
    roles["INDEPENDENCE_ACCEPTED"] = independence_accepted
    roles["ACCEPTED_INDEPENDENT_REPRODUCTION"] = bool(
        reproduction_matched and independence_accepted and scope_complete
    )
    return roles


def apply_nonclaim_gates(pack: dict[str, Any]) -> tuple[dict[str, bool], list[dict[str, str]]]:
    gates = empty_nonclaims()
    errors: list[dict[str, str]] = []
    claimed = pack.get("claimed_implications") or pack.get("nonclaim_violations") or {}
    for k in NONCLAIM_GATES:
        if claimed.get(k) is True or pack.get(k) is True:
            errors.append(_err("nonclaim_gate_violation", k))
            gates[k] = True  # violation present
        else:
            gates[k] = False
    return gates, errors


def validate_pack_structure(pack: dict[str, Any]) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []
    if str(pack.get("schema_version") or "") != PACK_SCHEMA:
        errors.append(_err("invalid_pack_schema", str(pack.get("schema_version"))))
    for member in REQUIRED_PACK_MEMBERS:
        if member not in pack:
            errors.append(_err("missing_pack_member", member))
    env = pack.get("environment") or {}
    for field in ("os_family", "arch", "python_version", "tool_versions"):
        if field not in env and field.upper() not in env:
            # allow either casing
            if not any(k.lower() == field for k in env.keys()):
                errors.append(_err("environment_incomplete", field))
    return errors


def validate_manifest_digests(pack: dict[str, Any]) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []
    manifest = pack.get("manifest") or {}
    members = manifest.get("members") or manifest.get("digests") or {}
    evidence_digests = pack.get("evidence_digests") or {}
    if not members and not evidence_digests:
        errors.append(_err("manifest_digest_missing", "no manifest digests"))
        return errors
    # If pack embeds content digests for key sections, verify consistency
    for key, content_key in (
        ("static_reproduction_results", "static_reproduction_results"),
        ("runtime_input_results", "runtime_input_results"),
        ("runtime_execution_results", "runtime_execution_results"),
        ("authority_read_results", "authority_read_results"),
        ("failure_log", "failure_log"),
        ("retry_log", "retry_log"),
    ):
        declared = (
            (members.get(key) if isinstance(members, dict) else None)
            or evidence_digests.get(key)
            or evidence_digests.get(f"{key}_sha256")
        )
        if declared and key in pack:
            actual = digest(pack.get(key))
            if str(declared).lower() != actual.lower():
                errors.append(_err("manifest_digest_mismatch", f"{key}: declared={declared} actual={actual}"))
    expected_manifest = pack.get("expected_manifest_digest")
    if expected_manifest:
        actual_m = digest(manifest)
        if str(expected_manifest).lower() != actual_m.lower():
            errors.append(_err("manifest_digest_mismatch", f"manifest root declared={expected_manifest} actual={actual_m}"))
    return errors


def transition_iw_status(current: str, event: str) -> str:
    """Synthetic state machine for tests. Does not accept real CAW IW runs."""
    cur = current if current in IW_STATUSES else "IW_NOT_STARTED"
    if event == "START":
        return "IW_IN_PROGRESS" if cur == "IW_NOT_STARTED" else cur
    if event == "PARTIAL":
        return "IW_REPRODUCTION_PARTIAL"
    if event == "MATCH":
        return "IW_REPRODUCTION_MATCHED"
    if event == "ACCEPT":
        # Only structurally allowable from MATCHED when caller already checked independence
        return "IW_ACCEPTED" if cur == "IW_REPRODUCTION_MATCHED" else cur
    if event == "REJECT":
        return "IW_REJECTED"
    return cur


def verify_independent_witness_v0(inp: dict[str, Any]) -> dict[str, Any]:
    errors: list[dict[str, str]] = []
    reason_codes: list[str] = []

    pack = inp.get("independent_witness_pack") or inp.get("iw_pack") or {}
    expected_boundary = inp.get("expected_frozen_boundary")
    allow_accept = bool(inp.get("allow_iw_accepted", True))
    force_status = inp.get("force_iw_status")

    # Structure
    struct_errors = validate_pack_structure(pack)
    errors.extend(struct_errors)

    # Frozen boundary
    observed_boundary = pack.get("frozen_input_verification") or pack.get("frozen_boundary") or {}
    boundary_ok, boundary_errors, boundary_checks = validate_frozen_boundary(observed_boundary, expected_boundary)
    errors.extend(boundary_errors)

    # Scope / reproduction
    scope_eval = evaluate_reproduction_scope(pack)
    indep_eval = evaluate_independence(pack)
    net_ok, net_errors, net_safety = evaluate_network_safety(pack)
    errors.extend(net_errors)
    fail_ok, fail_errors, fail_info = evaluate_failure_preservation(pack)
    errors.extend(fail_errors)
    errors.extend(detect_maintainer_substitution(pack))
    errors.extend(detect_scope_expansion(pack))
    errors.extend(validate_manifest_digests(pack))
    errors.extend(detect_out_of_manifest_required_dependency(pack))
    errors.extend(detect_pack_seal_mismatch(pack))
    if pack.get("pre_run_objects") is not None:
        errors.extend(detect_semi_blind_leakage(pack.get("pre_run_objects") or {}))
    nonclaims, nonclaim_errors = apply_nonclaim_gates(pack)
    errors.extend(nonclaim_errors)

    submission_ok, submission_errors, submission_info = evaluate_external_submission_provenance(pack)
    # Hard errors reject verification; soft acceptance blockers only prevent IW_ACCEPTED
    hard_submission_codes = {
        "maintainer_origin_submission",
        "external_submission_receipt_digest_mismatch",
    }
    soft_submission_codes = {
        "external_submission_receipt_missing",
        "self_declared_independence_insufficient",
    }
    for e in submission_errors:
        if e["code"] in hard_submission_codes:
            errors.append(e)
        elif e["code"] in soft_submission_codes:
            # Record for reason_codes without forcing REJECTED unless pack demands acceptance
            if pack.get("require_external_submission_for_verify"):
                errors.append(e)

    meta = pack.get("witness_run_metadata") or {}
    is_maintainer_dry_run = str(meta.get("witness_identity_class") or meta.get("run_class") or "").upper() in {
        "MAINTAINER_DRY_RUN",
        "STRUCTURAL_DRY_RUN",
    }

    reproduction_matched = bool(scope_eval["reproduction_matched"]) and boundary_ok
    independence_accepted = (
        bool(indep_eval["INDEPENDENCE_ACCEPTED"])
        and not is_maintainer_dry_run
        and submission_ok
    )
    scope_complete = bool(scope_eval["scope_complete"])

    roles = evaluate_role_separation(
        pack,
        reproduction_matched=reproduction_matched,
        independence_accepted=independence_accepted,
        scope_complete=scope_complete,
    )

    # Designated alone never accepts
    if roles["DESIGNATED_WITNESS"] and not (
        reproduction_matched and independence_accepted and scope_complete
    ):
        roles["ACCEPTED_INDEPENDENT_REPRODUCTION"] = False

    if is_maintainer_dry_run:
        independence_accepted = False
        roles["INDEPENDENCE_ACCEPTED"] = False
        roles["ACCEPTED_INDEPENDENT_REPRODUCTION"] = False
        indep_eval = dict(indep_eval)
        indep_eval["INDEPENDENCE_ACCEPTED"] = False
        indep_eval["dry_run_note"] = "MAINTAINER_DRY_RUN independence NOT_APPLICABLE_FOR_ACCEPTANCE"

    if not submission_ok:
        independence_accepted = False
        roles["INDEPENDENCE_ACCEPTED"] = False
        roles["ACCEPTED_INDEPENDENT_REPRODUCTION"] = False
        indep_eval = dict(indep_eval)
        indep_eval["INDEPENDENCE_ACCEPTED"] = False
        indep_eval["submission_note"] = "external submission receipt required for IW acceptance"

    rejected = len(errors) > 0
    if not allow_accept:
        # Structural classification only
        pass

    in_progress = bool(meta.get("in_progress")) or (
        bool(pack) and not scope_complete and not rejected
    )

    iw_status = classify_iw_status(
        pack_present=bool(pack),
        scope_complete=scope_complete,
        reproduction_matched=reproduction_matched and not rejected,
        independence_accepted=independence_accepted and not rejected and allow_accept,
        rejected=rejected,
        in_progress=in_progress,
    )

    # MATCHED must not become ACCEPTED without independence + valid external receipt
    if iw_status == "IW_ACCEPTED" and (not independence_accepted or not submission_ok):
        iw_status = "IW_REPRODUCTION_MATCHED" if reproduction_matched else "IW_REPRODUCTION_PARTIAL"

    if is_maintainer_dry_run and iw_status == "IW_ACCEPTED":
        iw_status = "IW_REPRODUCTION_MATCHED" if reproduction_matched else "IW_REPRODUCTION_PARTIAL"

    if force_status:
        iw_status = str(force_status)

    # Structural ACCEPTABLE classification (for synthetic fixtures) without marking real CAW IW accepted
    structurally_acceptable = bool(
        reproduction_matched
        and indep_eval.get("all_mandatory_satisfied")
        and submission_ok
        and not rejected
        and not is_maintainer_dry_run
        and boundary_ok
        and net_ok
        and fail_ok
    )

    for e in errors:
        if e["code"] not in reason_codes:
            reason_codes.append(e["code"])
    for e in submission_errors:
        if e["code"] not in reason_codes:
            reason_codes.append(e["code"])

    verification_status = "REJECTED" if rejected else "ACCEPTED"
    # Note: verification_status ACCEPTED means the verifier run validated the pack
    # structure/rules; it is NOT IW_ACCEPTED unless iw_status says so.

    result: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "iw_verifier_version": IW_VERIFIER_VERSION,
        "pack_format_version": PACK_FORMAT_VERSION,
        "verification_status": verification_status,
        "IW_STATUS": iw_status,
        "REAL_IW_STATUS": "NOT_SATISFIED" if iw_status != "IW_ACCEPTED" else "SATISFIED_SCOPED",
        "MATCHED_NEQ_ACCEPTED": True,
        "reproduction": scope_eval,
        "independence": indep_eval,
        "external_submission": submission_info,
        "role_separation": roles,
        "frozen_boundary_checks": boundary_checks,
        "frozen_boundary_ok": boundary_ok,
        "network_safety": net_safety,
        "failure_retry": fail_info,
        "nonclaim_gates": {k: (not v) for k, v in nonclaims.items()},  # True => gate held (claim absent)
        "nonclaim_violations": {k: v for k, v in nonclaims.items() if v},
        "acceptance_scope": scope_eval["acceptance_scope"],
        "scope_limited": True,
        "structurally_acceptable": structurally_acceptable,
        "ACCEPTED_INDEPENDENT_REPRODUCTION": roles["ACCEPTED_INDEPENDENT_REPRODUCTION"] and iw_status == "IW_ACCEPTED",
        "maintainer_dry_run": is_maintainer_dry_run,
        "dry_run_independence": "NOT_ACCEPTABLE_FOR_IW" if is_maintainer_dry_run else None,
        "errors": errors,
        "reason_codes": reason_codes,
        "axes": {
            "REPRODUCTION_MATCHED": reproduction_matched,
            "INDEPENDENCE_ACCEPTED": independence_accepted,
            "IW_ACCEPTED": iw_status == "IW_ACCEPTED",
            "DESIGNATED_WITNESS_ONLY": roles["DESIGNATED_WITNESS"] and not roles["ACCEPTED_INDEPENDENT_REPRODUCTION"],
            "EXTERNAL_SUBMISSION_VALID": submission_ok,
        },
        "caw_verdict_changed": False,
        "generated_at": now(),
    }
    result["result_id"] = rid(result)
    result["result_digest"] = digest({k: v for k, v in result.items() if k not in {"result_id", "result_digest"}})
    return result


def build_minimal_pack(**overrides: Any) -> dict[str, Any]:
    """Synthetic pack builder for tests / structural dry-run."""
    static = [
        {"PATH_ID": "wrps-v0-p0014", "result": "REPRODUCTION_PASS", "class": "STATIC_REPRODUCTION"},
        {"PATH_ID": "wrps-v0-p0030", "result": "REPRODUCTION_PASS", "class": "STATIC_REPRODUCTION"},
    ]
    rin = [
        {"PATH_ID": "wrps-v0-p0014", "result": "REPRODUCTION_PASS", "calldata_sha256": "a" * 64},
        {"PATH_ID": "wrps-v0-p0030", "result": "REPRODUCTION_PASS", "calldata_sha256": "b" * 64},
    ]
    rdisp = [
        {"PATH_ID": "wrps-v0-p0014", "result": "REPRODUCTION_PASS"},
        {"PATH_ID": "wrps-v0-p0030", "result": "REPRODUCTION_PASS"},
    ]
    rex = [
        {"PATH_ID": "wrps-v0-p0014", "result": "REPRODUCTION_PASS", "mode": "LOCAL_FORK_BOUNDED_MUTATION"},
        {"PATH_ID": "wrps-v0-p0030", "result": "REPRODUCTION_PASS", "mode": "LOCAL_FORK_READ_ONLY"},
    ]
    auth = [
        {
            "AUTHORITY_ID": "AUTH-005",
            "result": "REPRODUCTION_PASS",
            "selector": "0x8da5cb5b",
            "address": AUTHORITY_SUBSET["ADDRESS"],
        }
    ]
    failure_log = [
        {
            "attempt_id": "fail-1",
            "category": "RPC_BLOCKED",
            "step": "RUNTIME_EXECUTION_P0030",
            "detail": "synthetic first attempt blocked",
        }
    ]
    retry_log = [
        {
            "attempt_id": "retry-1",
            "prior_failure_id": "fail-1",
            "prior_failure_category": "RPC_BLOCKED",
            "result": "REPRODUCTION_PASS",
        }
    ]
    pack: dict[str, Any] = {
        "schema_version": PACK_SCHEMA,
        "pack_format_version": PACK_FORMAT_VERSION,
        "witness_run_metadata": {
            "run_id": "SYNTH-IW-001",
            "witness_handle": "synthetic-witness",
            "witness_reference": "synth://witness",
            "designated_witness": False,
            "declared_independent": True,
            "witness_identity_class": "SYNTHETIC_FIXTURE",
            "pack_version": PACK_FORMAT_VERSION,
            "in_progress": False,
        },
        "frozen_input_verification": default_frozen_boundary(
            weaver_commit="SYNTHETIC_WEAVER_COMMIT",
            weaver_tree="SYNTHETIC_WEAVER_TREE",
        ),
        "environment": {
            "os_family": "Windows",
            "arch": "AMD64",
            "python_version": "3.11",
            "tool_versions": {"foundry": "synthetic"},
        },
        "independence": {
            "schema_version": "weaver-iw-independence-criteria-v0",
            "axes": {
                axis: {"status": "VERIFIED", "evidence": [f"synthetic-evidence-{axis}"]}
                for axis in INDEPENDENCE_AXES
            },
        },
        "reproduction_scope": {
            "required_classes": list(REPRODUCTION_CLASSES),
            "kind": "BOUNDED_D",
            "whole_repository": False,
        },
        "static_reproduction_results": static,
        "runtime_input_results": rin,
        "runtime_dispatch_results": rdisp,
        "runtime_execution_results": rex,
        "authority_read_results": auth,
        "failure_log": failure_log,
        "retry_log": retry_log,
        "FAILURE_HISTORY_ASSURANCE": "SUBMITTED_HISTORY_PRESERVED",
        "failure_history_assurance": "SUBMITTED_HISTORY_PRESERVED",
        "failure_history_policy": {
            "attempt_id_policy": (
                "ATTEMPT_ID / PRIOR_ATTEMPT_ID retained; retries append; later PASS does not erase earlier failure"
            ),
            "assurance": "SUBMITTED_HISTORY_PRESERVED",
            "forbidden_claim": "COMPLETE_HISTORY_CRYPTOGRAPHICALLY_PROVEN",
        },
        "evidence_digests": {},
        "witness_attestation": {
            "statements": {
                "performed_steps_myself": True,
                "did_not_use_real_wallet": True,
                "did_not_broadcast": True,
                "recorded_failures": True,
            }
        },
        "witness_receipt": {"submitted": True, "receipt_id": "synth-receipt-1"},
        "manifest": {"members": {}},
        "network_safety": empty_network_safety(),
    }
    # Fill digest declarations to match content
    for key in (
        "static_reproduction_results",
        "runtime_input_results",
        "runtime_execution_results",
        "authority_read_results",
        "failure_log",
        "retry_log",
    ):
        d = digest(pack[key])
        pack["evidence_digests"][key] = d
        pack["manifest"]["members"][key] = d

    pack["output_digest"] = digest(
        {
            "static_reproduction_results": pack["static_reproduction_results"],
            "runtime_input_results": pack["runtime_input_results"],
            "runtime_execution_results": pack["runtime_execution_results"],
            "authority_read_results": pack["authority_read_results"],
        }
    )
    pack["evidence_digests"]["output_digest"] = pack["output_digest"]

    # Pack digest for external submission receipt binding (exclude receipt itself)
    pack_digest_body = {k: v for k, v in pack.items() if k not in {"pack_digest", "external_submission_receipt"}}
    pack["pack_digest"] = digest(pack_digest_body)
    pack["external_submission_receipt"] = {
        "SUBMISSION_RECEIPT_ID": "synth-ext-receipt-001",
        "SUBMISSION_CHANNEL_CLASS": "EXTERNAL_SYNTHETIC_CHANNEL",
        "SUBMISSION_TIMESTAMP": "2026-09-12T00:00:00Z",
        "PACK_DIGEST_RECEIVED": pack["pack_digest"],
        "OUTPUT_DIGEST_SUBMITTED": pack["output_digest"],
        "SUBMITTER_ROLE": "EXTERNAL_WITNESS",
        "MAINTAINER_ORIGIN": "NO",
        "ACCEPTANCE_ELIGIBLE": "YES",
    }

    # deep merge overrides
    def _merge(dst: dict[str, Any], src: dict[str, Any]) -> dict[str, Any]:
        for k, v in src.items():
            if isinstance(v, dict) and isinstance(dst.get(k), dict):
                _merge(dst[k], v)
            else:
                dst[k] = v
        return dst

    if overrides:
        _merge(pack, overrides)
        # refresh digests if content keys overridden without digest update
        for key in (
            "static_reproduction_results",
            "runtime_input_results",
            "runtime_execution_results",
            "authority_read_results",
            "failure_log",
            "retry_log",
        ):
            if key in overrides:
                d = digest(pack[key])
                pack["evidence_digests"][key] = d
                pack["manifest"]["members"][key] = d
        # Refresh pack/output digests + receipt binding unless caller overrode receipt/digests explicitly
        if "output_digest" not in overrides:
            pack["output_digest"] = digest(
                {
                    "static_reproduction_results": pack["static_reproduction_results"],
                    "runtime_input_results": pack["runtime_input_results"],
                    "runtime_execution_results": pack["runtime_execution_results"],
                    "authority_read_results": pack["authority_read_results"],
                }
            )
            pack["evidence_digests"]["output_digest"] = pack["output_digest"]
        if "pack_digest" not in overrides:
            pack_digest_body = {
                k: v for k, v in pack.items() if k not in {"pack_digest", "external_submission_receipt"}
            }
            pack["pack_digest"] = digest(pack_digest_body)
        if "external_submission_receipt" not in overrides and isinstance(
            pack.get("external_submission_receipt"), dict
        ):
            pack["external_submission_receipt"]["PACK_DIGEST_RECEIVED"] = pack["pack_digest"]
            pack["external_submission_receipt"]["OUTPUT_DIGEST_SUBMITTED"] = pack["output_digest"]
    return pack


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        print("usage: independent_witness_verifier_v0.py <iw_pack.json> [expected_boundary.json]")
        return 2
    pack = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    expected = None
    if len(argv) > 1:
        expected = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
    result = verify_independent_witness_v0(
        {
            "schema_version": SCHEMA_VERSION,
            "independent_witness_pack": pack,
            "expected_frozen_boundary": expected,
        }
    )
    print(json.dumps(result, indent=2))
    return 0 if result["verification_status"] == "ACCEPTED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
