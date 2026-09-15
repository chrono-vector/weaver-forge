"""Campaign runner data models and claim-state vocabulary."""

from __future__ import annotations

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

# Evidence-backed terminal states that MUST be revalidated from authoritative inputs.
# A stored CAMPAIGN_STATE row alone never justifies these (STATE != EVIDENCE).
EVIDENCE_BACKED_TERMINAL_STATES = frozenset({"PASS", "FAIL"})

# Alias used by transition guards; invalidation clears cache before recompute.
IMMUTABLE_COMPLETED_STATES = EVIDENCE_BACKED_TERMINAL_STATES

# Deterministic route → furthest legitimate campaign state mapping (generic).
ROUTE_TO_STATE: dict[str, str] = {
    "VERIFIABLE_NOW": "ROUTED",  # resolved via evidence reuse / capability
    "VERIFIABLE_WITH_ADDITIONAL_EVIDENCE": "BLOCKED_EVIDENCE",
    "INSUFFICIENT_EVIDENCE": "BLOCKED_EVIDENCE",
    "SANDBOX_TESTABLE": "INCONCLUSIVE",  # may become BLOCKED_HUMAN via bindings
    "PROPOSAL_NOT_YET_IMPLEMENTED": "IMPLEMENTATION_REQUIRED",
    "NORMATIVE_NOT_FACTUAL": "NORMATIVE_NOT_FACTUAL",
    "SYMBOLIC_NOT_EMPIRICALLY_TESTABLE": "SYMBOLIC_NOT_EMPIRICAL",
    "UNSUPPORTED_HISTORICAL_CLAIM": "HISTORICAL_CORROBORATION_REQUIRED",
}


def empty_state_counts() -> dict[str, int]:
    return {s: 0 for s in sorted(CLAIM_STATES)}


def validate_claim_state(state: str) -> str:
    if state not in CLAIM_STATES:
        raise ValueError(f"unknown claim state: {state}")
    return state
