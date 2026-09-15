"""Minimal declarative capability registry for Operational V1."""

from __future__ import annotations

from typing import Any

# Capabilities are declarative labels only — no broad worker fleet.
CAPABILITIES: dict[str, dict[str, Any]] = {
    "reuse_frozen_document_identity_audit": {
        "description": "Verify and bind existing frozen Weaver hash/document-identity audits.",
        "network": False,
        "target_code_execution": False,
        "external_services": False,
        "applies_to_routes": ["VERIFIABLE_NOW"],
        "applies_to_claims": ["AUR-A-001", "AUR-A-002"],
    },
    "bind_protocol_harness_evidence": {
        "description": (
            "Bind existing protocol/sandbox harness results without promoting to civic PASS."
        ),
        "network": False,
        "target_code_execution": False,
        "external_services": False,
        "applies_to_routes": ["SANDBOX_TESTABLE"],
        "applies_to_claims": ["AUR-A-005", "AUR-A-009", "AUR-A-012", "AUR-A-018"],
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
        "description": "Verify frozen Source A/B identity against expected SHA-256 digests.",
        "network": False,
        "target_code_execution": False,
        "external_services": False,
        "applies_to_routes": ["*"],
        "applies_to_claims": ["*"],
    },
}


def select_capability(claim_id: str, route: str) -> str | None:
    if claim_id in {"AUR-A-001", "AUR-A-002"}:
        return "reuse_frozen_document_identity_audit"
    if claim_id in {"AUR-A-005", "AUR-A-009", "AUR-A-012", "AUR-A-018"}:
        return "bind_protocol_harness_evidence"
    if route in CAPABILITIES["classify_bounded_states"]["applies_to_routes"]:
        return "classify_bounded_states"
    if route == "VERIFIABLE_NOW":
        return "reuse_frozen_document_identity_audit"
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
