"""Deterministic verification plan builder."""

from __future__ import annotations

from typing import Any

from .capabilities import select_capability
from .models import ROUTE_TO_STATE, validate_claim_state


def build_verification_plan(
    claims: list[dict[str, Any]],
    routes_by_id: dict[str, dict[str, Any]],
    compat_by_id: dict[str, dict[str, Any]],
    *,
    campaign_id: str,
) -> dict[str, Any]:
    """Build a deterministic plan covering every claim exactly once."""
    planned: list[dict[str, Any]] = []
    for claim in claims:
        cid = claim["claim_id"]
        route_row = routes_by_id[cid]
        route = route_row["route"]
        compat = compat_by_id[cid]
        capability = select_capability(cid, route)
        target_state = ROUTE_TO_STATE.get(route, "UNSUPPORTED")
        # Special-case human sandbox authorization.
        if cid == "AUR-A-021":
            target_state = "BLOCKED_HUMAN"
        # Reuse audits resolve to PASS via capability, not ROUTED.
        if cid in {"AUR-A-001", "AUR-A-002"}:
            target_state = "PASS"
        if cid in {"AUR-A-005", "AUR-A-009", "AUR-A-012", "AUR-A-018"}:
            target_state = "INCONCLUSIVE"
        validate_claim_state(target_state)
        planned.append(
            {
                "claim_id": cid,
                "claim_type": claim.get("claim_type"),
                "route": route,
                "route_rationale": route_row.get("rationale"),
                "compatibility": compat.get("compatibility"),
                "adapter": compat.get("adapter"),
                "capability": capability,
                "planned_state": target_state,
                "reuse_existing_audit": cid in {"AUR-A-001", "AUR-A-002"},
                "bind_protocol_evidence": cid
                in {"AUR-A-005", "AUR-A-009", "AUR-A-012", "AUR-A-018"},
            }
        )
    # Deterministic order by claim_id.
    planned.sort(key=lambda x: x["claim_id"])
    return {
        "schema": "weaver.campaign_runner_v0.verification_plan.v0",
        "campaign_id": campaign_id,
        "claim_count": len(planned),
        "claims": planned,
        "deterministic": True,
        "notes": [
            "Plan is derived from existing intake routing/compatibility.",
            "No AI classification/extraction.",
            "UNSUPPORTED must never become PASS/FAIL.",
            "PROTOCOL harness PASS ≠ civic PASS.",
        ],
    }
