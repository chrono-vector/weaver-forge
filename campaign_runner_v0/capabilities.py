"""Minimal declarative capability registry for Operational V1."""

from __future__ import annotations

from typing import Any

from .bindings import CampaignBindings

# Capabilities are declarative labels only — no claim-ID product constants.
CAPABILITIES: dict[str, dict[str, Any]] = {
    "reuse_frozen_document_identity_audit": {
        "description": "Verify and bind existing frozen Weaver hash/document-identity audits.",
        "network": False,
        "target_code_execution": False,
        "external_services": False,
        "applies_to_routes": ["VERIFIABLE_NOW"],
        "applies_to_claims": ["from_campaign_bindings.reuse_audits"],
    },
    "bind_protocol_harness_evidence": {
        "description": (
            "Bind existing protocol/sandbox harness results without promoting to civic PASS."
        ),
        "network": False,
        "target_code_execution": False,
        "external_services": False,
        "applies_to_routes": ["SANDBOX_TESTABLE"],
        "applies_to_claims": ["from_campaign_bindings.protocol_bound_claims"],
    },
    "classify_bounded_states": {
        "description": (
            "Map intake routes to bounded campaign states "
            "(evidence/human/implementation/normative/symbolic/historical)."
        ),
        "network": False,
        "target_code_execution": False,
        "external_services": False,
        "applies_to_routes": [
            "VERIFIABLE_WITH_ADDITIONAL_EVIDENCE",
            "INSUFFICIENT_EVIDENCE",
            "PROPOSAL_NOT_YET_IMPLEMENTED",
            "NORMATIVE_NOT_FACTUAL",
            "SYMBOLIC_NOT_EMPIRICALLY_TESTABLE",
            "UNSUPPORTED_HISTORICAL_CLAIM",
            "SANDBOX_TESTABLE",
        ],
        "applies_to_claims": ["*"],
    },
    "source_manifest_integrity": {
        "description": "Verify frozen source identity against SOURCE_MANIFEST expected digests.",
        "network": False,
        "target_code_execution": False,
        "external_services": False,
        "applies_to_routes": ["*"],
        "applies_to_claims": ["*"],
    },
}


def select_capability(
    claim_id: str, route: str, bindings: CampaignBindings
) -> str | None:
    if claim_id in bindings.reuse_audits:
        return "reuse_frozen_document_identity_audit"
    if bindings.is_protocol_bound(claim_id):
        return "bind_protocol_harness_evidence"
    if bindings.requires_human_auth(claim_id):
        return "classify_bounded_states"
    if route in CAPABILITIES["classify_bounded_states"]["applies_to_routes"]:
        return "classify_bounded_states"
    if route == "VERIFIABLE_NOW":
        # Verifiable-now without a reuse binding cannot invent PASS.
        return "classify_bounded_states"
    return None


def require_capability(name: str) -> dict[str, Any]:
    if name not in CAPABILITIES:
        raise KeyError(f"unsupported capability: {name}")
    return CAPABILITIES[name]


def capability_registry_snapshot() -> dict[str, Any]:
    return {
        "schema": "weaver.campaign_runner_v0.capability_registry.v0",
        "capabilities": CAPABILITIES,
        "policy_defaults": {
            "network": "denied",
            "external_services": "denied",
            "target_code_execution": "denied",
        },
    }
