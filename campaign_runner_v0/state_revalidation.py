"""Authoritative revalidation of stored campaign state (STATE != EVIDENCE)."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .bindings import CampaignBindings
from .evidence import verify_frozen_audit_reuse
from .models import EVIDENCE_BACKED_TERMINAL_STATES
from .safety import SafetyError


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def compute_state_integrity_digest(
    claims: dict[str, dict[str, Any]],
    evidence_register: dict[str, Any],
) -> str:
    """Integrity-bind claim rows + evidence register. Not authoritative truth alone."""
    payload = {
        "claims": claims,
        "evidence_register": {
            "entries": evidence_register.get("entries", []),
        },
    }
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _evidence_by_claim(evidence_register: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = {}
    for entry in evidence_register.get("entries") or []:
        cid = entry.get("claim_id")
        if not cid:
            continue
        out.setdefault(cid, []).append(entry)
    return out


def validate_pass_fail_against_evidence(
    *,
    workspace: Path,
    claim_id: str,
    row: dict[str, Any],
    plan_row: dict[str, Any],
    evidence_entries: list[dict[str, Any]],
    bindings: CampaignBindings,
) -> tuple[bool, dict[str, Any] | None, str]:
    """Return (ok, refreshed_row_or_none, reason).

    PASS/FAIL require validated evidence provenance. Stored state alone is insufficient.
    """
    state = row.get("state")
    if state not in EVIDENCE_BACKED_TERMINAL_STATES:
        return True, None, "not_evidence_backed_terminal"

    # Protocol / civic / implementation / human cannot mint PASS via state edit.
    if plan_row.get("bind_protocol_evidence") and state == "PASS":
        return False, None, "protocol_evidence_cannot_justify_civic_PASS"
    if plan_row.get("requires_human_auth") and state == "PASS":
        return False, None, "human_auth_block_cannot_justify_PASS"
    if plan_row.get("planned_state") == "IMPLEMENTATION_REQUIRED" and state == "PASS":
        return False, None, "implementation_required_cannot_justify_PASS"
    if (
        plan_row.get("planned_state")
        in {
            "BLOCKED_EVIDENCE",
            "INCONCLUSIVE",
            "NORMATIVE_NOT_FACTUAL",
            "SYMBOLIC_NOT_EMPIRICAL",
            "HISTORICAL_CORROBORATION_REQUIRED",
            "UNSUPPORTED",
            "BLOCKED_HUMAN",
            "BLOCKED_AUTHORITY",
        }
        and state == "PASS"
        and not plan_row.get("reuse_existing_audit")
    ):
        return False, None, "planned_non_pass_cannot_be_state_promoted_to_PASS"

    if not plan_row.get("reuse_existing_audit"):
        # Only reuse-bound claims may hold PASS in Operational V1 without new evidence.
        if state == "PASS":
            return False, None, "PASS_without_reuse_binding_or_validated_evidence"
        return False, None, "FAIL_without_validated_evidence_path"

    # Recompute authoritative reuse evidence (digest check; no refreeze).
    try:
        ev = verify_frozen_audit_reuse(workspace, claim_id, bindings)
    except SafetyError as exc:
        return False, None, f"reuse_validation_failed:{exc}"

    if state != "PASS":
        return False, None, "reuse_binding_expects_PASS_when_package_valid"

    expected_eid = ev["evidence_id"]
    row_eid = row.get("evidence_id")
    if row_eid and row_eid != expected_eid:
        return False, None, "stored_evidence_id_mismatch"

    # Evidence register must contain matching provenance (or we refresh from package).
    matching = [
        e
        for e in evidence_entries
        if e.get("evidence_id") == expected_eid and e.get("kind") == "FROZEN_WEAVER_AUDIT_REUSE"
    ]
    if matching:
        reg_digest = matching[0].get("sha256sums_digest") or (
            matching[0].get("evidence_digests") or {}
        ).get("sha256sums")
        if reg_digest and reg_digest != ev["sha256sums_digest"]:
            return False, None, "evidence_register_digest_mismatch"

    refreshed = {
        **row,
        "claim_id": claim_id,
        "state": "PASS",
        "evidence_id": expected_eid,
        "evidence_digests": ev.get("evidence_digests"),
        "evidence_references": [expected_eid],
        "verification_scope": ev.get("verification_scope") or ev.get("scope"),
        "verification_mechanism": ev.get("verification_mechanism"),
        "source_binding": ev.get("source_binding"),
        "package_reference": ev.get("package_reference") or ev.get("frozen_path"),
        "run_reference": ev.get("run_path"),
        "capability": plan_row.get("capability"),
        "pass_kind": ev.get("scope"),
        "hash_match": True,
        "promotes_content_truth": False,
        "basis": "FROZEN_AUDIT_REUSE",
        "state_authoritative": False,
        "evidence_validated": True,
        "validated_at_utc": _utc_now(),
        "reason": row.get("reason")
        or f"Reused immutable audit {ev.get('audit_id')}; scope={ev.get('scope')}",
    }
    return True, refreshed, "reuse_validated"


def revalidate_prior_claim_states(
    *,
    workspace: Path,
    claim_states: dict[str, dict[str, Any]],
    evidence_register: dict[str, Any],
    plan: dict[str, Any],
    bindings: CampaignBindings,
    prior_integrity_digest: str | None,
) -> dict[str, Any]:
    """Strip or refresh untrusted PASS/FAIL rows. Digest mismatch never restores truth."""
    plan_by_id = {r["claim_id"]: r for r in plan["claims"]}
    by_claim = _evidence_by_claim(evidence_register)
    rejected: list[dict[str, Any]] = []
    validated_reuse: list[str] = []

    # Integrity digest is advisory only — semantic revalidation always runs.
    integrity_ok = True
    if prior_integrity_digest:
        recomputed = compute_state_integrity_digest(claim_states, evidence_register)
        integrity_ok = recomputed == prior_integrity_digest

    for cid, row in list(claim_states.items()):
        state = row.get("state")
        if state not in EVIDENCE_BACKED_TERMINAL_STATES:
            continue
        plan_row = plan_by_id.get(cid)
        if not plan_row:
            claim_states[cid] = {
                "claim_id": cid,
                "state": "NEW",
                "reason": "untrusted terminal state cleared — claim missing from plan",
                "updated_at_utc": _utc_now(),
                "prior_untrusted_state": state,
                "state_authoritative": False,
            }
            rejected.append({"claim_id": cid, "prior_state": state, "reason": "missing_plan"})
            continue

        ok, refreshed, reason = validate_pass_fail_against_evidence(
            workspace=workspace,
            claim_id=cid,
            row=row,
            plan_row=plan_row,
            evidence_entries=by_claim.get(cid, []),
            bindings=bindings,
        )
        if ok and refreshed is not None:
            claim_states[cid] = refreshed
            validated_reuse.append(cid)
        elif ok:
            continue
        else:
            claim_states[cid] = {
                "claim_id": cid,
                "state": "NEW",
                "reason": f"untrusted terminal state rejected ({reason}); STATE≠EVIDENCE",
                "updated_at_utc": _utc_now(),
                "prior_untrusted_state": state,
                "prior_untrusted_reason": row.get("reason"),
                "rejection_reason": reason,
                "state_authoritative": False,
                "tamper_or_invalid_terminal_cleared": True,
            }
            rejected.append({"claim_id": cid, "prior_state": state, "reason": reason})

    return {
        "integrity_digest_matched": integrity_ok if prior_integrity_digest else None,
        "rejected_terminals": rejected,
        "validated_reuse_claims": validated_reuse,
        "note": "STATE≠EVIDENCE; digest alone never restores PASS/FAIL",
    }
