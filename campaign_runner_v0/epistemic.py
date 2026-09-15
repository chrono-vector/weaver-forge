"""Hard epistemic safety assertions for campaign transitions.

Enforced by code/tests — not documentation alone.
Source/evidence text never controls campaign policy.
"""

from __future__ import annotations

from typing import Any

from .models import CLAIM_STATES, IMMUTABLE_COMPLETED_STATES


class EpistemicViolation(ValueError):
    """Raised when a forbidden epistemic promotion is attempted."""


FORBIDDEN_TRANSITIONS: frozenset[tuple[str, str]] = frozenset(
    {
        ("UNSUPPORTED", "PASS"),
        ("UNSUPPORTED", "FAIL"),
    }
)


def assert_transition_allowed(
    from_state: str,
    to_state: str,
    *,
    reason: str = "",
    context: dict[str, Any] | None = None,
) -> None:
    """Fail closed on forbidden epistemic promotions."""
    ctx = context or {}
    if from_state not in CLAIM_STATES:
        raise EpistemicViolation(f"unknown from_state={from_state}")
    if to_state not in CLAIM_STATES:
        raise EpistemicViolation(f"unknown to_state={to_state}")

    if (from_state, to_state) in FORBIDDEN_TRANSITIONS:
        raise EpistemicViolation(
            f"forbidden transition {from_state} → {to_state}: {reason or 'epistemic rule'}"
        )

    # UNSUPPORTED must never become PASS/FAIL merely because unsupported.
    if from_state == "UNSUPPORTED" and to_state in {"PASS", "FAIL"}:
        raise EpistemicViolation("UNSUPPORTED must not become PASS/FAIL")

    # INCONCLUSIVE → PASS requires new sufficient evidence flag.
    if from_state == "INCONCLUSIVE" and to_state == "PASS":
        if not ctx.get("new_sufficient_evidence"):
            raise EpistemicViolation(
                "INCONCLUSIVE → PASS requires new_sufficient_evidence=True"
            )

    # Immutable completed audits cannot be rewritten via transition.
    if from_state in IMMUTABLE_COMPLETED_STATES and to_state != from_state:
        if not ctx.get("allow_immutable_rewrite"):
            raise EpistemicViolation(
                f"immutable completed state {from_state} cannot transition to {to_state}"
            )


def assert_not_hash_equals_content_truth(claim_result: dict[str, Any]) -> None:
    """HASH MATCH ≠ CONTENT TRUTH."""
    if claim_result.get("hash_match") and claim_result.get("promotes_content_truth"):
        raise EpistemicViolation("HASH MATCH ≠ CONTENT TRUTH")
    scope = str(claim_result.get("scope") or "")
    if claim_result.get("state") == "PASS" and "CONTENT_TRUTH" in scope.upper():
        raise EpistemicViolation("PASS must not claim CONTENT_TRUTH from hash match")


def assert_not_protocol_equals_civic(claim_result: dict[str, Any]) -> None:
    """PROTOCOL HARNESS PASS ≠ CIVIC / REAL-WORLD PASS."""
    if claim_result.get("protocol_check") == "PASS" and claim_result.get("state") == "PASS":
        if claim_result.get("pass_kind") in {None, "CIVIC", "REAL_WORLD", "PROTOCOL_AS_CIVIC"}:
            raise EpistemicViolation("PROTOCOL HARNESS PASS ≠ CIVIC / REAL-WORLD PASS")
    if claim_result.get("protocol_promoted_to_civic_pass"):
        raise EpistemicViolation("PROTOCOL HARNESS PASS ≠ CIVIC / REAL-WORLD PASS")


def assert_not_proposal_equals_implemented(claim_result: dict[str, Any]) -> None:
    """PROPOSAL ≠ IMPLEMENTED."""
    if claim_result.get("is_proposal") and claim_result.get("state") in {"PASS", "FAIL"}:
        raise EpistemicViolation("PROPOSAL ≠ IMPLEMENTED")
    if claim_result.get("treated_proposal_as_implemented"):
        raise EpistemicViolation("PROPOSAL ≠ IMPLEMENTED")


def assert_not_classification_equals_verdict(claim_result: dict[str, Any]) -> None:
    """CLASSIFICATION ≠ VERDICT."""
    if claim_result.get("classification_used_as_verdict"):
        raise EpistemicViolation("CLASSIFICATION ≠ VERDICT")


def assert_not_ai_plan_equals_evidence(claim_result: dict[str, Any]) -> None:
    """AI PLAN ≠ EVIDENCE."""
    if claim_result.get("ai_plan_used_as_evidence"):
        raise EpistemicViolation("AI PLAN ≠ EVIDENCE")


def assert_not_text_presence_equals_claim_truth(claim_result: dict[str, Any]) -> None:
    """TEXT PRESENCE ≠ CLAIM TRUTH (except narrowly scoped document-identity PASS)."""
    if claim_result.get("text_presence_promoted_to_claim_truth"):
        raise EpistemicViolation("TEXT PRESENCE ≠ CLAIM TRUTH")
    if (
        claim_result.get("state") == "PASS"
        and claim_result.get("basis") == "TEXT_PRESENCE_ONLY"
        and claim_result.get("pass_kind") not in {
            "DOCUMENT_IDENTITY_ONLY",
            "DOCUMENT_IDENTITY_TEXTUAL_PRESENCE_ONLY",
        }
    ):
        raise EpistemicViolation("TEXT PRESENCE ≠ CLAIM TRUTH")


def assert_not_human_auth_equals_claim_truth(claim_result: dict[str, Any]) -> None:
    """HUMAN AUTHORIZATION ≠ CLAIM TRUTH."""
    if claim_result.get("human_authorization_used_as_claim_truth"):
        raise EpistemicViolation("HUMAN AUTHORIZATION ≠ CLAIM TRUTH")


def assert_claim_result_safe(claim_result: dict[str, Any]) -> None:
    """Run the full epistemic battery against a claim result dict."""
    assert_not_hash_equals_content_truth(claim_result)
    assert_not_protocol_equals_civic(claim_result)
    assert_not_proposal_equals_implemented(claim_result)
    assert_not_classification_equals_verdict(claim_result)
    assert_not_ai_plan_equals_evidence(claim_result)
    assert_not_text_presence_equals_claim_truth(claim_result)
    assert_not_human_auth_equals_claim_truth(claim_result)

    state = claim_result.get("state")
    if state == "UNSUPPORTED" and claim_result.get("promoted_because_unsupported"):
        raise EpistemicViolation("UNSUPPORTED must not promote to PASS/FAIL")
