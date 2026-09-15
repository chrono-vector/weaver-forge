"""Campaign runner data models and claim-state vocabulary."""

from __future__ import annotations

from typing import Any

CLAIM_STATES = frozenset(
    {
        "NEW",
        "PLANNED",
        "ROUTED",
        "RUNNING",
        "PASS",
        "FAIL",
        "INCONCLUSIVE",
        "UNSUPPORTED",
        "BLOCKED_HUMAN",
        "BLOCKED_EVIDENCE",
        "BLOCKED_AUTHORITY",
        "IMPLEMENTATION_REQUIRED",
        "NORMATIVE_NOT_FACTUAL",
        "SYMBOLIC_NOT_EMPIRICAL",
        "HISTORICAL_CORROBORATION_REQUIRED",
    }
)

# Terminal-ish states that one invocation may leave a claim in.
FURTHEST_LEGITIMATE_STATES = frozenset(
    {
        "PASS",
        "FAIL",
        "INCONCLUSIVE",
        "UNSUPPORTED",
        "BLOCKED_HUMAN",
        "BLOCKED_EVIDENCE",
        "BLOCKED_AUTHORITY",
        "IMPLEMENTATION_REQUIRED",
        "NORMATIVE_NOT_FACTUAL",
        "SYMBOLIC_NOT_EMPIRICAL",
        "HISTORICAL_CORROBORATION_REQUIRED",
    }
)

IMMUTABLE_COMPLETED_STATES = frozenset({"PASS", "FAIL"})

# Deterministic route → furthest legitimate campaign state mapping.
ROUTE_TO_STATE: dict[str, str] = {
    "VERIFIABLE_NOW": "ROUTED",  # resolved via evidence reuse / capability
    "VERIFIABLE_WITH_ADDITIONAL_EVIDENCE": "BLOCKED_EVIDENCE",
    "INSUFFICIENT_EVIDENCE": "BLOCKED_EVIDENCE",
    "SANDBOX_TESTABLE": "INCONCLUSIVE",  # may become BLOCKED_HUMAN if no protocol bind
    "PROPOSAL_NOT_YET_IMPLEMENTED": "IMPLEMENTATION_REQUIRED",
    "NORMATIVE_NOT_FACTUAL": "NORMATIVE_NOT_FACTUAL",
    "SYMBOLIC_NOT_EMPIRICALLY_TESTABLE": "SYMBOLIC_NOT_EMPIRICAL",
    "UNSUPPORTED_HISTORICAL_CLAIM": "HISTORICAL_CORROBORATION_REQUIRED",
}

KNOWN_REUSE_AUDITS: dict[str, dict[str, Any]] = {
    "AUR-A-001": {
        "audit_id": "WFA-20260915T042439Z-8BE7790F",
        "run_relpath": "runs/WFA-20260915T042439Z-8BE7790F",
        "frozen_relpath": (
            "runs/WFA-20260915T042439Z-8BE7790F/freeze/"
            "WFA-20260915T042439Z-8BE7790F_FROZEN"
        ),
        "audit_record_relpath": "audits/AUR-A-001/AUDIT_RECORD.md",
        "expected_sha256sums_digest": (
            "5b5b695a50bf03b98bffad8027ad753f719b5ef9ddff82d4f4850fa98bc6c8ae"
        ),
        "scope": "DOCUMENT_IDENTITY_ONLY",
        "verdict": "PASS",
    },
    "AUR-A-002": {
        "audit_id": "WFA-20260915T043650Z-C49CA863",
        "run_relpath": "runs/WFA-20260915T043650Z-C49CA863",
        "frozen_relpath": (
            "runs/WFA-20260915T043650Z-C49CA863/freeze/"
            "WFA-20260915T043650Z-C49CA863_FROZEN"
        ),
        "audit_record_relpath": "audits/AUR-A-002/AUDIT_RECORD.md",
        "expected_sha256sums_digest": (
            "2c0abec238b749811c0bd19793df751721d9f81a9cfbea3e73d0f5d94bf63643"
        ),
        "scope": "DOCUMENT_IDENTITY_TEXTUAL_PRESENCE_ONLY",
        "verdict": "PASS",
    },
}

PROTOCOL_BOUND_CLAIMS = frozenset(
    {"AUR-A-005", "AUR-A-009", "AUR-A-012", "AUR-A-018"}
)

HUMAN_AUTH_REQUIRED_CLAIMS = frozenset({"AUR-A-021"})

EXPECTED_SOURCE_HASHES = {
    "SOURCE_A": "a38e9f918bed135b5e5a90580830611923c81866aeecb5b8b7b35edd3552d3de",
    "SOURCE_B": "9653ff6b4c59da68bd8ecaae4186172aa7fb367b6fb2711d97129a92aa9c39c2",
}


def empty_state_counts() -> dict[str, int]:
    return {s: 0 for s in sorted(CLAIM_STATES)}


def validate_claim_state(state: str) -> str:
    if state not in CLAIM_STATES:
        raise ValueError(f"unknown claim state: {state}")
    return state
