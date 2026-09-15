"""One-invocation campaign orchestration."""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .bindings import load_campaign_bindings
from .capabilities import capability_registry_snapshot, require_capability
from .epistemic import EpistemicViolation, assert_claim_result_safe, assert_transition_allowed
from .evidence import (
    bind_protocol_harness,
    empty_evidence_register,
    load_synthetic_test_evidence,
    verify_frozen_audit_reuse,
)
from .loaders import (
    load_workspace_artifacts,
    validate_claim_register,
    validate_compatibility,
    validate_routing,
    verify_source_integrity,
)
from .models import (
    EVIDENCE_BACKED_TERMINAL_STATES,
    FURTHEST_LEGITIMATE_STATES,
    empty_state_counts,
    validate_claim_state,
)
from .planner import build_verification_plan
from .report import (
    build_blocker_queue,
    build_campaign_report,
    build_human_action_requests,
    render_campaign_index_md,
    render_campaign_matrix_md,
)
from .safety import (
    CampaignLock,
    SafetyError,
    append_jsonl,
    assert_not_frozen_write,
    load_json,
    resolve_confined,
    write_json,
)
from .state_revalidation import compute_state_integrity_digest, revalidate_prior_claim_states


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _default_policy() -> dict[str, Any]:
    return {
        "network": "denied",
        "external_services": "denied",
        "target_code_execution": "denied",
        "allow_frozen_rewrite": False,
        "allow_audit_lifecycle_write": False,
        "dry_run": False,
        "lock_stale_seconds": 3600,
        "idempotent": True,
        "update_derived_views": True,
    }


def load_policy(path: Path | None) -> dict[str, Any]:
    policy = _default_policy()
    if path is not None:
        loaded = load_json(path)
        if not isinstance(loaded, dict):
            raise SafetyError("policy must be a JSON object")
        for k, v in loaded.items():
            if k.startswith("_"):
                continue
            policy[k] = v
    return policy


def campaign_dir(workspace: Path, campaign_id: str) -> Path:
    return resolve_confined(workspace, f"campaigns/{campaign_id}")


def _receipt(
    *,
    claim_id: str,
    capability: str | None,
    action: str,
    result: str,
    detail: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "schema": "weaver.campaign_runner_v0.worker_receipt.v0",
        "receipt_id": str(uuid.uuid4()),
        "at_utc": _utc_now(),
        "claim_id": claim_id,
        "capability": capability,
        "action": action,
        "result": result,
        "detail": detail or {},
    }


def _set_state(
    claim_states: dict[str, dict[str, Any]],
    claim_id: str,
    new_state: str,
    *,
    reason: str,
    extra: dict[str, Any] | None = None,
) -> None:
    validate_claim_state(new_state)
    prev = claim_states.get(claim_id, {"state": "NEW"})
    prev_state = prev.get("state", "NEW")
    assert_transition_allowed(prev_state, new_state, reason=reason, context=extra or {})
    row = {
        **prev,
        "claim_id": claim_id,
        "state": new_state,
        "reason": reason,
        "updated_at_utc": _utc_now(),
        "state_authoritative": False,
    }
    if extra:
        row.update(extra)
    assert_claim_result_safe(row)
    claim_states[claim_id] = row


def _process_claim(
    *,
    workspace: Path,
    plan_row: dict[str, Any],
    claim_states: dict[str, dict[str, Any]],
    evidence_register: dict[str, Any],
    receipts: list[dict[str, Any]],
    synthetic_by_claim: dict[str, dict[str, Any]],
    bindings: Any,
    dry_run: bool,
) -> None:
    cid = plan_row["claim_id"]
    existing = claim_states.get(cid)

    # Efficient reuse: only after evidence-backed terminal was revalidated this invocation.
    if (
        existing
        and existing.get("state") in EVIDENCE_BACKED_TERMINAL_STATES
        and existing.get("evidence_validated") is True
        and existing.get("basis") == "FROZEN_AUDIT_REUSE"
        and cid not in synthetic_by_claim
    ):
        receipts.append(
            _receipt(
                claim_id=cid,
                capability=plan_row.get("capability"),
                action="SKIP_VALIDATED_REUSE",
                result="UNCHANGED",
                detail={
                    "state": existing["state"],
                    "evidence_id": existing.get("evidence_id"),
                    "evidence_digests": existing.get("evidence_digests"),
                    "note": "STATE≠EVIDENCE; skip only after revalidation",
                },
            )
        )
        return

    # Resume: skip furthest non-PASS/FAIL when aligned with plan, or when a prior
    # TEST_ONLY advance must be preserved without re-supplying synthetic evidence.
    if (
        existing
        and existing.get("state") in FURTHEST_LEGITIMATE_STATES
        and existing.get("state") not in EVIDENCE_BACKED_TERMINAL_STATES
        and cid not in synthetic_by_claim
        and (
            existing.get("state") == plan_row.get("planned_state")
            or existing.get("TEST_ONLY") is True
        )
        and not existing.get("tamper_or_invalid_terminal_cleared")
    ):
        receipts.append(
            _receipt(
                claim_id=cid,
                capability=plan_row.get("capability"),
                action="SKIP_ALREADY_FURTHEST",
                result="UNCHANGED",
                detail={"state": existing["state"]},
            )
        )
        return

    # Cleared untrusted terminals start from NEW for transitions.
    if existing and existing.get("tamper_or_invalid_terminal_cleared"):
        claim_states[cid] = {
            "claim_id": cid,
            "state": "NEW",
            "reason": existing.get("reason") or "cleared untrusted terminal",
            "updated_at_utc": _utc_now(),
            "state_authoritative": False,
        }

    _set_state(claim_states, cid, "RUNNING", reason="campaign processing")
    capability = plan_row.get("capability")
    route = plan_row["route"]
    planned = plan_row["planned_state"]

    try:
        if capability:
            require_capability(capability)

        if plan_row.get("reuse_existing_audit"):
            if dry_run:
                ev = {
                    "evidence_id": f"dry-run-reuse:{cid}",
                    "claim_id": cid,
                    "kind": "FROZEN_WEAVER_AUDIT_REUSE",
                    "immutable": True,
                    "scope": "DOCUMENT_IDENTITY_ONLY",
                    "sha256sums_digest": "dry-run",
                    "evidence_digests": {"sha256sums": "dry-run"},
                    "verification_scope": "DOCUMENT_IDENTITY_ONLY",
                    "verification_mechanism": "reuse_frozen_document_identity_audit",
                }
            else:
                ev = verify_frozen_audit_reuse(workspace, cid, bindings)
            evidence_register["entries"].append(ev)
            _set_state(
                claim_states,
                cid,
                "PASS",
                reason=f"Reused immutable audit {ev.get('audit_id')}; scope={ev.get('scope')}",
                extra={
                    "route": route,
                    "capability": capability,
                    "evidence_id": ev["evidence_id"],
                    "evidence_references": [ev["evidence_id"]],
                    "evidence_digests": ev.get("evidence_digests")
                    or {"sha256sums": ev.get("sha256sums_digest")},
                    "verification_scope": ev.get("verification_scope") or ev.get("scope"),
                    "verification_mechanism": ev.get("verification_mechanism"),
                    "source_binding": ev.get("source_binding"),
                    "package_reference": ev.get("package_reference") or ev.get("frozen_path"),
                    "run_reference": ev.get("run_path"),
                    "pass_kind": ev.get("scope") or "DOCUMENT_IDENTITY_ONLY",
                    "hash_match": True,
                    "promotes_content_truth": False,
                    "basis": "FROZEN_AUDIT_REUSE",
                    "evidence_validated": True,
                    "state_authoritative": False,
                },
            )
            receipts.append(
                _receipt(
                    claim_id=cid,
                    capability=capability,
                    action="REUSE_FROZEN_AUDIT",
                    result="PASS",
                    detail={"evidence_id": ev["evidence_id"], "modified": False},
                )
            )
            return

        if plan_row.get("bind_protocol_evidence"):
            if dry_run:
                ev = {
                    "evidence_id": f"dry-run-protocol:{cid}",
                    "claim_id": cid,
                    "kind": "PROTOCOL_HARNESS_BIND",
                    "protocol_check": "PASS",
                    "civic_claim_state": "INCONCLUSIVE",
                }
            else:
                ev = bind_protocol_harness(workspace, cid, bindings)
            evidence_register["entries"].append(ev)
            _set_state(
                claim_states,
                cid,
                "INCONCLUSIVE",
                reason=(
                    "Protocol harness bound; civic/real-world claim remains INCONCLUSIVE "
                    "(PROTOCOL ≠ CIVIC PASS)"
                ),
                extra={
                    "route": route,
                    "capability": capability,
                    "evidence_id": ev["evidence_id"],
                    "evidence_references": [ev["evidence_id"]],
                    "evidence_digests": ev.get("evidence_digests"),
                    "verification_scope": ev.get("verification_scope"),
                    "verification_mechanism": ev.get("verification_mechanism"),
                    "protocol_check": ev.get("protocol_check"),
                    "protocol_promoted_to_civic_pass": False,
                    "pass_kind": "NONE",
                    "state_authoritative": False,
                },
            )
            receipts.append(
                _receipt(
                    claim_id=cid,
                    capability=capability,
                    action="BIND_PROTOCOL_EVIDENCE",
                    result="INCONCLUSIVE",
                    detail={"evidence_id": ev["evidence_id"]},
                )
            )
            return

        if plan_row.get("requires_human_auth"):
            _set_state(
                claim_states,
                cid,
                "BLOCKED_HUMAN",
                reason=(
                    "Human sandbox authorization / consenting participants required; "
                    "HUMAN AUTHORIZATION ≠ CLAIM TRUTH"
                ),
                extra={
                    "route": route,
                    "capability": capability,
                    "human_authorization_used_as_claim_truth": False,
                    "state_authoritative": False,
                },
            )
            receipts.append(
                _receipt(
                    claim_id=cid,
                    capability=capability,
                    action="BLOCK_HUMAN_AUTH",
                    result="BLOCKED_HUMAN",
                )
            )
            return

        if cid in synthetic_by_claim:
            syn = synthetic_by_claim[cid]
            evidence_register["entries"].append(syn)
            new_state = syn.get("payload", {}).get("test_advance_state") or "INCONCLUSIVE"
            if new_state == "PASS":
                new_state = "INCONCLUSIVE"
            _set_state(
                claim_states,
                cid,
                new_state,
                reason=(
                    "TEST_ONLY synthetic evidence applied for resume; "
                    "NOT_REAL_AURORA_EVIDENCE; canonical evidence untouched"
                ),
                extra={
                    "route": route,
                    "capability": capability,
                    "evidence_id": syn["evidence_id"],
                    "evidence_references": [syn["evidence_id"]],
                    "TEST_ONLY": True,
                    "SYNTHETIC": True,
                    "NOT_REAL_AURORA_EVIDENCE": True,
                    "new_sufficient_evidence": new_state == "PASS",
                    "state_authoritative": False,
                },
            )
            receipts.append(
                _receipt(
                    claim_id=cid,
                    capability=capability,
                    action="APPLY_TEST_ONLY_SYNTHETIC",
                    result=new_state,
                    detail={"evidence_id": syn["evidence_id"]},
                )
            )
            return

        reason_map = {
            "BLOCKED_EVIDENCE": "Additional / insufficient evidence; not converted to FAIL",
            "IMPLEMENTATION_REQUIRED": (
                "Proposal/described mechanism not implemented (PROPOSAL ≠ IMPLEMENTED)"
            ),
            "NORMATIVE_NOT_FACTUAL": "Normative/ethical claim — not empirical PASS/FAIL",
            "SYMBOLIC_NOT_EMPIRICAL": "Symbolic/metaphorical — not empirically testable",
            "HISTORICAL_CORROBORATION_REQUIRED": (
                "Historical claim lacks independent corroboration; not PASS/FAIL"
            ),
            "UNSUPPORTED": "Unsupported by current capability; not PASS/FAIL",
            "INCONCLUSIVE": "Insufficient to conclude; not promoted to PASS",
        }
        reason = reason_map.get(planned, f"Routed to bounded state {planned}")
        extra: dict[str, Any] = {
            "route": route,
            "capability": capability,
            "is_proposal": planned == "IMPLEMENTATION_REQUIRED",
            "treated_proposal_as_implemented": False,
            "classification_used_as_verdict": False,
            "ai_plan_used_as_evidence": False,
            "text_presence_promoted_to_claim_truth": False,
            "state_authoritative": False,
        }
        _set_state(claim_states, cid, planned, reason=reason, extra=extra)
        receipts.append(
            _receipt(
                claim_id=cid,
                capability=capability,
                action="CLASSIFY_BOUNDED_STATE",
                result=planned,
            )
        )
    except (SafetyError, EpistemicViolation, KeyError) as exc:
        _set_state(
            claim_states,
            cid,
            "BLOCKED_AUTHORITY" if isinstance(exc, EpistemicViolation) else "BLOCKED_EVIDENCE",
            reason=f"fail-closed: {exc}",
            extra={"route": route, "capability": capability, "error": str(exc)},
        )
        receipts.append(
            _receipt(
                claim_id=cid,
                capability=capability,
                action="FAIL_CLOSED",
                result="ERROR",
                detail={"error": str(exc)},
            )
        )


def run_campaign(
    *,
    workspace: Path,
    campaign_id: str = "aurora_operational_v1",
    policy_path: Path | None = None,
    synthetic_evidence_paths: list[Path] | None = None,
    dry_run: bool = False,
    force_unlock_stale: bool = False,
) -> dict[str, Any]:
    """Execute one campaign invocation over all claims."""
    workspace = workspace.resolve()
    if not workspace.is_dir():
        raise SafetyError(f"workspace not found: {workspace}")

    policy = load_policy(policy_path)
    if dry_run:
        policy["dry_run"] = True
    policy["dry_run"] = bool(policy.get("dry_run"))

    if policy.get("allow_audit_lifecycle_write"):
        raise SafetyError("policy must not allow audit_lifecycle writes")
    if policy.get("allow_frozen_rewrite"):
        raise SafetyError("policy must not allow frozen package rewrites")

    cdir = campaign_dir(workspace, campaign_id)
    lock_path = cdir / "campaign.lock"
    state_path = cdir / "CAMPAIGN_STATE.json"
    owner = f"campaign_runner_v0:{campaign_id}:{uuid.uuid4().hex[:8]}"

    if force_unlock_stale and lock_path.exists() and not policy["dry_run"]:
        try:
            meta = load_json(lock_path)
            age = datetime.now(timezone.utc).timestamp() - float(meta.get("acquired_at_epoch", 0))
            if age >= float(policy.get("lock_stale_seconds", 3600)):
                lock_path.unlink()
        except SafetyError:
            raise SafetyError("stale lock unreadable — fail closed")

    artifacts = load_workspace_artifacts(workspace)
    bindings = load_campaign_bindings(workspace)
    claims = validate_claim_register(artifacts["claim_register"], bindings=bindings)
    claim_ids = {c["claim_id"] for c in claims}
    routes_by_id = validate_routing(artifacts["verification_routing"], claim_ids)
    compat_by_id = validate_compatibility(artifacts["weaver_compatibility"], claim_ids)
    source_integrity = verify_source_integrity(workspace, artifacts["source_manifest"])

    plan = build_verification_plan(
        claims,
        routes_by_id,
        compat_by_id,
        campaign_id=campaign_id,
        bindings=bindings,
    )

    prior_state: dict[str, Any] | None = None
    if state_path.exists() and not policy["dry_run"]:
        try:
            prior_state = load_json(state_path)
        except SafetyError as exc:
            raise SafetyError(f"corrupted campaign state — fail closed: {exc}") from exc

    claim_states: dict[str, dict[str, Any]] = {}
    if prior_state and isinstance(prior_state.get("claims"), dict):
        claim_states = dict(prior_state["claims"])

    evidence_register = empty_evidence_register(campaign_id)
    if prior_state and isinstance(prior_state.get("evidence_register"), dict):
        evidence_register = prior_state["evidence_register"]

    revalidation_report: dict[str, Any] | None = None
    if prior_state and not policy["dry_run"]:
        revalidation_report = revalidate_prior_claim_states(
            workspace=workspace,
            claim_states=claim_states,
            evidence_register=evidence_register,
            plan=plan,
            bindings=bindings,
            prior_integrity_digest=(prior_state.get("state_integrity") or {}).get(
                "digest"
            ),
        )

    synthetic_by_claim: dict[str, dict[str, Any]] = {}
    for p in synthetic_evidence_paths or []:
        syn = load_synthetic_test_evidence(Path(p), workspace)
        synthetic_by_claim[syn["claim_id"]] = syn

    receipts: list[dict[str, Any]] = []
    invocation_id = f"INV-{_utc_now().replace(':', '').replace('-', '')}-{uuid.uuid4().hex[:8]}"

    with CampaignLock(
        lock_path,
        owner=owner,
        stale_seconds=int(policy.get("lock_stale_seconds", 3600)),
        dry_run=policy["dry_run"],
    ):
        for c in claims:
            cid = c["claim_id"]
            if cid not in claim_states:
                claim_states[cid] = {
                    "claim_id": cid,
                    "state": "NEW",
                    "reason": "loaded from claim register",
                    "updated_at_utc": _utc_now(),
                    "state_authoritative": False,
                }

        for row in plan["claims"]:
            cid = row["claim_id"]
            cur = claim_states[cid]["state"]
            if (
                cur in EVIDENCE_BACKED_TERMINAL_STATES
                and claim_states[cid].get("evidence_validated") is True
            ):
                continue
            if cur == "NEW" or claim_states[cid].get("tamper_or_invalid_terminal_cleared"):
                if claim_states[cid].get("tamper_or_invalid_terminal_cleared"):
                    claim_states[cid] = {
                        "claim_id": cid,
                        "state": "NEW",
                        "reason": claim_states[cid].get("reason") or "cleared",
                        "updated_at_utc": _utc_now(),
                        "state_authoritative": False,
                    }
                _set_state(claim_states, cid, "PLANNED", reason="verification plan built")
                _set_state(
                    claim_states,
                    cid,
                    "ROUTED",
                    reason=f"route={row['route']}",
                    extra={"route": row["route"], "capability": row.get("capability")},
                )
            elif cur in {"PLANNED"}:
                _set_state(
                    claim_states,
                    cid,
                    "ROUTED",
                    reason=f"route={row['route']}",
                    extra={"route": row["route"], "capability": row.get("capability")},
                )

        existing_evidence_ids = {
            e.get("evidence_id") for e in evidence_register.get("entries", [])
        }
        for row in plan["claims"]:
            before_ids = set(existing_evidence_ids)
            _process_claim(
                workspace=workspace,
                plan_row=row,
                claim_states=claim_states,
                evidence_register=evidence_register,
                receipts=receipts,
                synthetic_by_claim=synthetic_by_claim,
                bindings=bindings,
                dry_run=policy["dry_run"],
            )
            for e in evidence_register.get("entries", []):
                eid = e.get("evidence_id")
                if eid in before_ids:
                    continue
                existing_evidence_ids.add(eid)

        seen: set[str] = set()
        deduped = []
        for e in evidence_register.get("entries", []):
            eid = e.get("evidence_id")
            if eid in seen:
                continue
            seen.add(eid)
            deduped.append(e)
        evidence_register["entries"] = deduped
        evidence_register["updated_at_utc"] = _utc_now()

        blocker_queue = build_blocker_queue(claim_states)
        human_actions = build_human_action_requests(blocker_queue)
        counts = empty_state_counts()
        for row in claim_states.values():
            counts[row["state"]] = counts.get(row["state"], 0) + 1

        unfinished = [
            cid
            for cid, row in claim_states.items()
            if row["state"] not in FURTHEST_LEGITIMATE_STATES
        ]
        if unfinished:
            raise SafetyError(
                f"campaign did not advance all claims to furthest state: {unfinished}"
            )

        integrity_digest = compute_state_integrity_digest(claim_states, evidence_register)
        campaign_state = {
            "schema": "weaver.campaign_runner_v0.campaign_state.v0",
            "campaign_id": campaign_id,
            "invocation_id": invocation_id,
            "workspace": workspace.name,
            "updated_at_utc": _utc_now(),
            "status": "COMPLETED_INVOCATION",
            "claim_count": len(claim_states),
            "state_counts": counts,
            "claims": claim_states,
            "evidence_register": evidence_register,
            "blocker_queue": blocker_queue,
            "human_action_requests": human_actions,
            "capability_registry": capability_registry_snapshot(),
            "source_integrity": source_integrity,
            "state_integrity": {
                "digest": integrity_digest,
                "algorithm": "sha256",
                "covers": ["claims", "evidence_register.entries"],
                "note": (
                    "Integrity digest binds cache bytes only. "
                    "STATE≠EVIDENCE; PASS/FAIL require validated evidence provenance."
                ),
            },
            "revalidation": revalidation_report,
            "plan_fingerprint": hashlib.sha256(
                json.dumps(plan, sort_keys=True, separators=(",", ":")).encode()
            ).hexdigest(),
        }

        report = build_campaign_report(
            campaign_id=campaign_id,
            workspace=workspace.name,
            source_integrity=source_integrity,
            plan=plan,
            claim_states=claim_states,
            evidence_register=evidence_register,
            blocker_queue=blocker_queue,
            receipts=receipts,
            policy=policy,
        )

        matrix_md = render_campaign_matrix_md(claim_states, campaign_id=campaign_id)
        index_md = render_campaign_index_md(
            claim_states, evidence_register, campaign_id=campaign_id
        )

        if not policy["dry_run"]:
            for name, data in (
                ("VERIFICATION_PLAN.json", plan),
                ("CAMPAIGN_STATE.json", campaign_state),
                ("EVIDENCE_REGISTER.json", evidence_register),
                ("BLOCKER_QUEUE.json", blocker_queue),
                ("CAMPAIGN_REPORT.json", report),
                ("HUMAN_ACTION_REQUESTS.json", {"requests": human_actions}),
            ):
                out = cdir / name
                assert_not_frozen_write(workspace, out)
                write_json(out, data)

            receipts_path = cdir / "worker_receipts.jsonl"
            assert_not_frozen_write(workspace, receipts_path)
            for r in receipts:
                append_jsonl(receipts_path, r)

            if policy.get("update_derived_views", True):
                matrix_path = cdir / "CAMPAIGN_MATRIX.md"
                index_path = cdir / "CAMPAIGN_INDEX.md"
                assert_not_frozen_write(workspace, matrix_path)
                assert_not_frozen_write(workspace, index_path)
                matrix_path.write_text(matrix_md, encoding="utf-8", newline="\n")
                index_path.write_text(index_md, encoding="utf-8", newline="\n")

        return {
            "ok": True,
            "campaign_id": campaign_id,
            "invocation_id": invocation_id,
            "dry_run": policy["dry_run"],
            "campaign_dir": str(cdir) if not policy["dry_run"] else None,
            "claim_count": len(claim_states),
            "state_counts": counts,
            "blocker_count": blocker_queue["count"],
            "plan": plan,
            "campaign_state": campaign_state,
            "evidence_register": evidence_register,
            "blocker_queue": blocker_queue,
            "report": report,
            "receipts": receipts,
            "matrix_md": matrix_md,
            "index_md": index_md,
            "source_integrity": source_integrity,
            "revalidation": revalidation_report,
        }
