from __future__ import annotations

from typing import Any

from .adapters import AdapterResult, VectorResult


def decide(
    claim: dict[str, Any],
    adapter_result: AdapterResult,
    boundary_vector: VectorResult,
    policy: dict[str, Any],
    evidence_complete: bool,
) -> dict[str, Any]:
    """
    Conservative decision engine.
    Never invents FULL/stronger promotions. No false PASS on incomplete/tampered/boundary failures.
    """
    vectors = list(adapter_result.vectors) + [boundary_vector]
    by_id = {v.id: v for v in vectors}

    if not evidence_complete:
        return {
            "decision": "INCONCLUSIVE",
            "claim_result": "INCONCLUSIVE",
            "reason": "INCOMPLETE_EVIDENCE",
            "promoted": False,
            "vectors": {v.id: v.result for v in vectors},
        }

    if boundary_vector.result != "PASS":
        return {
            "decision": "BLOCKED",
            "claim_result": "BLOCKED",
            "reason": "BOUNDARY_VIOLATION_OR_GATE_FAIL",
            "promoted": False,
            "vectors": {v.id: v.result for v in vectors},
        }

    if adapter_result.claim_result == "BLOCKED":
        return {
            "decision": "BLOCKED",
            "claim_result": "BLOCKED",
            "reason": "ADAPTER_BLOCKED",
            "promoted": False,
            "vectors": {v.id: v.result for v in vectors},
        }

    if adapter_result.claim_result != "PASS":
        return {
            "decision": "FAIL",
            "claim_result": adapter_result.claim_result,
            "reason": "ADAPTER_CLAIM_NOT_PASS",
            "promoted": False,
            "vectors": {v.id: v.result for v in vectors},
        }

    # All required adapter vectors must PASS
    required = policy.get("required_vectors") or [
        "POSITIVE_DIGEST_MATCH",
        "NC1_WRONG_DIGEST_REJECTED",
        "T1_TAMPER_CHANGES_DIGEST",
        "R1_REHASH_REPRODUCTION",
        "BV1_PROTECTED_BOUNDARY_WRITE_DENIED",
    ]
    missing = [r for r in required if r not in by_id]
    if missing:
        return {
            "decision": "INCONCLUSIVE",
            "claim_result": "INCONCLUSIVE",
            "reason": "MISSING_REQUIRED_VECTORS",
            "missing": missing,
            "promoted": False,
            "vectors": {v.id: v.result for v in vectors},
        }
    if any(by_id[r].result != "PASS" for r in required):
        return {
            "decision": "FAIL",
            "claim_result": "FAIL",
            "reason": "REQUIRED_VECTOR_FAIL",
            "promoted": False,
            "vectors": {v.id: v.result for v in vectors},
        }

    # Conservative: PASS claim only; never auto-promote broader classifications
    broader = policy.get("broader_classification_on_pass", "CLAIM_SUPPORTED_PARTIAL")
    force_full = bool(policy.get("force_full_on_pass", False))
    if force_full:
        # Explicitly refuse silent FULL even if policy asks — conservative engine
        broader = "CLAIM_SUPPORTED_PARTIAL"
        promotion_note = "force_full_on_pass ignored by conservative Decision Engine"
    else:
        promotion_note = "no broader FULL promotion"

    return {
        "decision": "PASS",
        "claim_result": "PASS",
        "broader_classification": broader,
        "promoted_to_full": False,
        "promotion_note": promotion_note,
        "reason": "ALL_REQUIRED_VECTORS_PASS",
        "promoted": False,
        "vectors": {v.id: v.result for v in vectors},
        "claim_id": claim.get("id") or claim.get("claim_id"),
    }
