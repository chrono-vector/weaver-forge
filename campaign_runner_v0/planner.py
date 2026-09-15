"""Deterministic verification plan builder."""

from __future__ import annotations

from typing import Any

from .bindings import CampaignBindings
from .capabilities import select_capability
from .models import ROUTE_TO_STATE, validate_claim_state


def build_verification_plan(
    claims: list[dict[str, Any]],
    routes_by_id: dict[str, dict[str, Any]],
    compat_by_id: dict[str, dict[str, Any]],
    *,
    campaign_id: str,
    bindings: CampaignBindings,
) -> dict[str, Any]:
    """Build a deterministic plan covering every claim exactly once."""
    planned: list[dict[str, Any]] = []
    for claim in claims:
        cid = claim["claim_id"]
        route_row = routes_by_id[cid]
        route = route_row["route"]
        compat = compat_by_id[cid]
        capability = select_capability(cid, route, bindings)
        reuse = cid in bindings.reuse_audits
        protocol = bindings.is_protocol_bound(cid)
        human = bindings.requires_human_auth(cid)

        target_state = ROUTE_TO_STATE.get(route, "UNSUPPORTED")
        if human:
            target_state = "BLOCKED_HUMAN"
        elif reuse:
            target_state = "PASS"
        elif protocol:
            target_state = "INCONCLUSIVE"
        elif target_state == "ROUTED":
            # VERIFIABLE_NOW without reuse binding cannot invent PASS.
            target_state = "BLOCKED_EVIDENCE"

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
                "reuse_existing_audit": reuse,
                "bind_protocol_evidence": protocol,
                "requires_human_auth": human,
            }
        )
    planned.sort(key=lambda x: x["claim_id"])
    return {
        "schema": "weaver.campaign_runner_v0.verification_plan.v0",
        "campaign_id": campaign_id,
        "claim_count": len(planned),
        "claims": planned,
        "deterministic": True,
        "notes": [
            "Plan is derived from intake routing/compatibility + campaign bindings.",
            "No AI classification/extraction.",
            "No claim-ID product hardcoding.",
            "UNSUPPORTED must never become PASS/FAIL.",
            "PROTOCOL harness PASS ≠ civic PASS.",
            "STATE ≠ EVIDENCE.",
        ],
    }
