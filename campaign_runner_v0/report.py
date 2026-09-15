"""Campaign report, blocker queue, and derived matrix/index views."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .models import empty_state_counts
from .safety import redact_secrets


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def build_blocker_queue(claim_states: dict[str, dict[str, Any]]) -> dict[str, Any]:
    blockers: list[dict[str, Any]] = []
    for cid in sorted(claim_states):
        row = claim_states[cid]
        state = row["state"]
        if state in {
            "BLOCKED_HUMAN",
            "BLOCKED_EVIDENCE",
            "BLOCKED_AUTHORITY",
            "IMPLEMENTATION_REQUIRED",
            "HISTORICAL_CORROBORATION_REQUIRED",
        }:
            blockers.append(
                {
                    "claim_id": cid,
                    "blocker_type": state,
                    "reason": row.get("reason"),
                    "human_action_required": state == "BLOCKED_HUMAN",
                    "evidence_required": state
                    in {"BLOCKED_EVIDENCE", "HISTORICAL_CORROBORATION_REQUIRED"},
                    "resumable": True,
                }
            )
    return {
        "schema": "weaver.campaign_runner_v0.blocker_queue.v0",
        "generated_at_utc": _utc_now(),
        "count": len(blockers),
        "blockers": blockers,
        "finite": True,
    }


def build_human_action_requests(blocker_queue: dict[str, Any]) -> list[dict[str, Any]]:
    out = []
    for b in blocker_queue.get("blockers", []):
        if b.get("human_action_required"):
            out.append(
                {
                    "schema": "weaver.campaign_runner_v0.human_action_request.v0",
                    "claim_id": b["claim_id"],
                    "action": "AUTHORIZE_AND_EXECUTE_SANDBOX_OR_SUPPLY_CONSENT_RECORDS",
                    "blocker_type": b["blocker_type"],
                    "reason": b.get("reason"),
                }
            )
    return out


def build_campaign_report(
    *,
    campaign_id: str,
    workspace: str,
    source_integrity: dict[str, Any],
    plan: dict[str, Any],
    claim_states: dict[str, dict[str, Any]],
    evidence_register: dict[str, Any],
    blocker_queue: dict[str, Any],
    receipts: list[dict[str, Any]],
    policy: dict[str, Any],
) -> dict[str, Any]:
    counts = empty_state_counts()
    for row in claim_states.values():
        counts[row["state"]] = counts.get(row["state"], 0) + 1
    report = {
        "schema": "weaver.campaign_runner_v0.campaign_report.v0",
        "campaign_id": campaign_id,
        "workspace": workspace,
        "generated_at_utc": _utc_now(),
        "source_integrity": source_integrity,
        "claim_count": len(claim_states),
        "state_counts": counts,
        "claims": {cid: claim_states[cid] for cid in sorted(claim_states)},
        "blocker_queue_count": blocker_queue.get("count", 0),
        "evidence_entry_count": len(evidence_register.get("entries", [])),
        "worker_receipt_count": len(receipts),
        "plan_claim_count": plan.get("claim_count"),
        "policy_summary": {
            "network": policy.get("network", "denied"),
            "external_services": policy.get("external_services", "denied"),
            "target_code_execution": policy.get("target_code_execution", "denied"),
            "dry_run": policy.get("dry_run", False),
        },
        "epistemic_rules_enforced": [
            "UNSUPPORTED ≠ PASS/FAIL",
            "INCONCLUSIVE ≠ PASS without new sufficient evidence",
            "HASH MATCH ≠ CONTENT TRUTH",
            "PROTOCOL HARNESS PASS ≠ CIVIC / REAL-WORLD PASS",
            "PROPOSAL ≠ IMPLEMENTED",
            "CLASSIFICATION ≠ VERDICT",
            "AI PLAN ≠ EVIDENCE",
            "TEXT PRESENCE ≠ CLAIM TRUTH",
            "HUMAN AUTHORIZATION ≠ CLAIM TRUTH",
        ],
        "notes": [
            "Campaign report is an aggregate view and never substitutes for underlying evidence.",
            "Canonical frozen packages remain authoritative.",
            "No Job Agent / VECTOR integration.",
        ],
    }
    return redact_secrets(report)


def render_campaign_matrix_md(
    claim_states: dict[str, dict[str, Any]],
    *,
    campaign_id: str,
) -> str:
    """Derived campaign matrix view — does not rewrite canonical matrix authority."""
    lines = [
        f"# Campaign Matrix View — `{campaign_id}`",
        "",
        "**Derived aggregate view only.** Canonical intake/matrix/evidence remain authoritative.",
        f"**Generated (UTC):** `{_utc_now()}`",
        "",
        "| Claim ID | Campaign state | Route | Capability | Evidence | Notes |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for cid in sorted(claim_states):
        row = claim_states[cid]
        lines.append(
            "| {cid} | {state} | {route} | {cap} | {ev} | {notes} |".format(
                cid=cid,
                state=row.get("state"),
                route=row.get("route", ""),
                cap=row.get("capability") or "",
                ev=row.get("evidence_id") or "",
                notes=(row.get("reason") or "").replace("|", "/"),
            )
        )
    lines.append("")
    lines.append("## Rule reminders")
    lines.append("")
    lines.append("- HASH MATCH ≠ CONTENT TRUTH")
    lines.append("- PROTOCOL ≠ CIVIC PASS")
    lines.append("- PROPOSAL ≠ IMPLEMENTED")
    lines.append("- Reports ≠ underlying evidence")
    lines.append("")
    return "\n".join(lines)


def render_campaign_index_md(
    claim_states: dict[str, dict[str, Any]],
    evidence_register: dict[str, Any],
    *,
    campaign_id: str,
) -> str:
    lines = [
        f"# Campaign Audit Index View — `{campaign_id}`",
        "",
        "**Derived index view only.** Does not replace `AUDIT_INDEX.md` canonical entries.",
        f"**Generated (UTC):** `{_utc_now()}`",
        "",
        "## Claim outcomes",
        "",
    ]
    for cid in sorted(claim_states):
        row = claim_states[cid]
        lines.append(
            f"- `{cid}`: **{row.get('state')}** — {row.get('reason') or 'n/a'}"
        )
    lines.append("")
    lines.append("## Evidence register entries")
    lines.append("")
    for e in evidence_register.get("entries", []):
        lines.append(
            f"- `{e.get('evidence_id')}` → `{e.get('claim_id')}` ({e.get('kind')})"
        )
    lines.append("")
    return "\n".join(lines)
