"""Hard epistemic safety tests."""

from __future__ import annotations

import pytest

from campaign_runner_v0.epistemic import (
    EpistemicViolation,
    assert_claim_result_safe,
    assert_not_ai_plan_equals_evidence,
    assert_not_classification_equals_verdict,
    assert_not_hash_equals_content_truth,
    assert_not_human_auth_equals_claim_truth,
    assert_not_proposal_equals_implemented,
    assert_not_protocol_equals_civic,
    assert_not_text_presence_equals_claim_truth,
    assert_transition_allowed,
)


def test_unsupported_cannot_become_pass():
    with pytest.raises(EpistemicViolation):
        assert_transition_allowed("UNSUPPORTED", "PASS")


def test_unsupported_cannot_become_fail():
    with pytest.raises(EpistemicViolation):
        assert_transition_allowed("UNSUPPORTED", "FAIL")


def test_inconclusive_cannot_become_pass_without_evidence():
    with pytest.raises(EpistemicViolation):
        assert_transition_allowed("INCONCLUSIVE", "PASS")
    assert_transition_allowed(
        "INCONCLUSIVE", "PASS", context={"new_sufficient_evidence": True}
    )


def test_hash_match_not_content_truth():
    with pytest.raises(EpistemicViolation):
        assert_not_hash_equals_content_truth(
            {"hash_match": True, "promotes_content_truth": True}
        )
    assert_not_hash_equals_content_truth(
        {"hash_match": True, "promotes_content_truth": False, "state": "PASS", "scope": "DOCUMENT_IDENTITY_ONLY"}
    )


def test_protocol_not_civic_pass():
    with pytest.raises(EpistemicViolation):
        assert_not_protocol_equals_civic(
            {"protocol_check": "PASS", "state": "PASS", "pass_kind": "CIVIC"}
        )
    with pytest.raises(EpistemicViolation):
        assert_not_protocol_equals_civic({"protocol_promoted_to_civic_pass": True})
    # Protocol PASS with civic INCONCLUSIVE is fine.
    assert_not_protocol_equals_civic(
        {
            "protocol_check": "PASS",
            "state": "INCONCLUSIVE",
            "protocol_promoted_to_civic_pass": False,
        }
    )


def test_proposal_not_implemented():
    with pytest.raises(EpistemicViolation):
        assert_not_proposal_equals_implemented(
            {"is_proposal": True, "state": "PASS"}
        )


def test_classification_not_verdict():
    with pytest.raises(EpistemicViolation):
        assert_not_classification_equals_verdict(
            {"classification_used_as_verdict": True}
        )


def test_ai_plan_not_evidence():
    with pytest.raises(EpistemicViolation):
        assert_not_ai_plan_equals_evidence({"ai_plan_used_as_evidence": True})


def test_text_presence_not_claim_truth():
    with pytest.raises(EpistemicViolation):
        assert_not_text_presence_equals_claim_truth(
            {
                "state": "PASS",
                "basis": "TEXT_PRESENCE_ONLY",
                "pass_kind": "CIVIC",
            }
        )


def test_human_auth_not_claim_truth():
    with pytest.raises(EpistemicViolation):
        assert_not_human_auth_equals_claim_truth(
            {"human_authorization_used_as_claim_truth": True}
        )


def test_assert_claim_result_safe_bundle():
    assert_claim_result_safe(
        {
            "state": "PASS",
            "pass_kind": "DOCUMENT_IDENTITY_ONLY",
            "hash_match": True,
            "promotes_content_truth": False,
            "protocol_promoted_to_civic_pass": False,
            "treated_proposal_as_implemented": False,
            "classification_used_as_verdict": False,
            "ai_plan_used_as_evidence": False,
            "text_presence_promoted_to_claim_truth": False,
            "human_authorization_used_as_claim_truth": False,
        }
    )
