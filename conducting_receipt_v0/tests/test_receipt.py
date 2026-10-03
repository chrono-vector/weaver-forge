"""Focused tests for Conducting Receipt v0."""

from __future__ import annotations

import copy
import json
import subprocess
import unittest
from collections.abc import Mapping
from pathlib import Path

from audit_lifecycle.epistemic.serialize import canonical_digest
from conducting_receipt_v0 import ConductingError, build_conducting_receipt

REPO = Path(__file__).resolve().parents[2]

_STATEMENT = "bytes are well formed"
_OTHER = "cd" * 32
_UNPINNED = (
    "HEAD",
    "latest",
    "main",
    "master",
    "origin/main",
    "origin/master",
    "current",
    "same as above",
    " Head ",
)
_PROOF_TOKENS = (
    "PROVEN_TRUE",
    "HUMAN_REVIEW_ACCEPTED",
    "verified",
    "independent_evidence_count",
    "structural_candidate",
    "admission_status",
    "verification_kind",
)


class _SplitView(Mapping):
    """Bound iteration is the record. Live lookup is the attack."""

    def __init__(self, bound: dict, live: dict) -> None:
        self._bound = bound
        self._live = live

    def __getitem__(self, key: str):
        return self._live[key]

    def __iter__(self):
        return iter(self._bound)

    def __len__(self) -> int:
        return len(self._bound)

    def items(self):
        return self._bound.items()

    def get(self, key: str, default=None):
        return self._live.get(key, default)


class _SplitDict(dict):
    def __init__(self, bound: dict, live: dict) -> None:
        super().__init__(bound)
        self._live = live

    def __getitem__(self, key: str):
        return self._live[key]

    def get(self, key: str, default=None):
        return self._live.get(key, default)


class _HostileStr(str):
    def __eq__(self, other: object) -> bool:
        return True

    def __hash__(self) -> int:
        return hash("PASS")


class _HostileInt(int):
    def __eq__(self, other: object) -> bool:
        return other is True or int.__eq__(self, other)

    def __hash__(self) -> int:
        return hash(True)


class _Rows(list):
    """Caller-owned list subclass."""


class _Reuse(tuple):
    """Caller-owned tuple subclass."""


class _DupKeys(Mapping):
    def __getitem__(self, key: str):
        return "x"

    def __iter__(self):
        return iter(("session_id",))

    def __len__(self) -> int:
        return 2

    def items(self):
        return [("session_id", "session-1"), ("session_id", "other")]


def _stmt_digest(statement: str = _STATEMENT) -> str:
    return canonical_digest(statement)


def _content(payload: str) -> dict:
    return {"payload": payload}


def _open_assumption(statement: str = _STATEMENT, introduced: str = "r0", **over: object) -> dict:
    record = {
        "statement": statement,
        "introduced_in_revision": introduced,
        "status": "OPEN",
    }
    record.update(over)
    return record


def _resolved_assumption(
    statement: str = _STATEMENT,
    introduced: str = "r0",
    resolver: str = "r1",
    **over: object,
) -> dict:
    record = _open_assumption(statement, introduced, status="RESOLVED", resolved_by_revision=resolver)
    record.update(over)
    return record


def _r0(*, payload: str = "proposal", **over: object) -> dict:
    record = {
        "revision_id": "r0",
        "content": _content(payload),
        "created_order": 0,
        "event_order": 0,
        "agent_id": "agent-a",
        "agent_role": "PROPOSER",
        "assumptions": [_open_assumption()],
    }
    record.update(over)
    return record


def _rationale() -> dict:
    return {
        "claim": "proposal fails on empty input",
        "assumptions": [_STATEMENT],
        "attack": "empty input yields a different digest",
    }


def _c1(target_digest: str, *, kind: str = "COUNTEREXAMPLE", present: bool = True, **over: object) -> dict:
    record = {
        "challenge_id": "c1",
        "target_revision_id": "r0",
        "target_content_digest": target_digest,
        "challenger_id": "agent-b",
        "agent_role": "CHALLENGER",
        "challenge_kind": kind,
        "rationale": _rationale(),
        "counterexample_present": present,
        "assumptions_attacked": [_stmt_digest()],
        "created_order": 0,
        "event_order": 1,
    }
    if present:
        record["counterexample"] = {"body": {"payload": "empty"}}
    record.update(over)
    return record


def _r1(parent_digest: str, *, payload: str = "revised", **over: object) -> dict:
    record = {
        "revision_id": "r1",
        "content": _content(payload),
        "created_order": 1,
        "event_order": 2,
        "agent_id": "agent-a",
        "agent_role": "REVISER",
        "parent_revision_id": "r0",
        "parent_content_digest": parent_digest,
        "responds_to": ["c1"],
        "assumptions": [_open_assumption()],
    }
    record.update(over)
    return record


def _challenge_material(challenge: Mapping[str, object]) -> dict:
    material = {
        "target_revision_id": challenge["target_revision_id"],
        "target_content_digest": challenge["target_content_digest"],
        "challenge_kind": challenge["challenge_kind"],
        "rationale": challenge["rationale"],
        "assumptions_attacked": challenge["assumptions_attacked"],
        "counterexample_present": challenge["counterexample_present"],
    }
    if challenge["counterexample_present"]:
        material["counterexample_body"] = challenge["counterexample"]["body"]
    return material


def _complete(**over: object) -> dict:
    r0 = _r0()
    digest = canonical_digest(r0["content"])
    exchange = {
        "session_id": "session-1",
        "target_claim_id": "CLAIM-1",
        "revisions": [r0, _r1(digest)],
        "challenges": [_c1(digest)],
    }
    exchange.update(over)
    return exchange


def _proposal_only(**over: object) -> dict:
    exchange = {
        "session_id": "session-1",
        "revisions": [_r0()],
        "challenges": [],
    }
    exchange.update(over)
    return exchange


def _build(exchange: Mapping[str, object] | None = None, **kwargs: object) -> dict:
    if exchange is None:
        exchange = _complete()
    return build_conducting_receipt(exchange, **kwargs)


def _expect(test: unittest.TestCase, code: str, fn) -> None:
    with test.assertRaises(ConductingError) as caught:
        fn()
    test.assertEqual(caught.exception.code, code)


def _assert_closed(test: unittest.TestCase, receipt: Mapping[str, object]) -> None:
    test.assertIs(receipt["authority"], False)
    test.assertEqual(receipt["schema_version"], "conducting_receipt.v0")
    blob = json.dumps(receipt)
    for token in _PROOF_TOKENS:
        test.assertNotIn(token, blob)
    test.assertNotIn("HUMAN_REVIEW_ACCEPTED", receipt["selection_status"])
    test.assertNotEqual(receipt["selection_status"], "HUMAN_REVIEW_ACCEPTED")
    test.assertNotIn("diversity_score", receipt)
    test.assertNotIn("independence_score", receipt)
    test.assertNotIn("consensus", receipt)


class TestTrustBoundary(unittest.TestCase):
    def test_01_mapping_split_view_neutralized(self) -> None:
        bound = _complete()
        live = _complete()
        live["session_id"] = "attack-session"
        live["independent_evidence_count"] = 3
        live["human_final"] = True
        receipt = _build(_SplitView(bound, live))
        self.assertEqual(receipt["session_id"], "session-1")
        self.assertNotIn("independent_evidence_count", receipt)
        self.assertIs(receipt["authority"], False)
        _assert_closed(self, receipt)

    def test_02_nested_content_split_view_neutralized(self) -> None:
        bound_content = _content("proposal")
        live_content = _content("attack")
        r0 = _r0()
        r0["content"] = _SplitView(bound_content, live_content)
        digest = canonical_digest(bound_content)
        exchange = {
            "session_id": "session-1",
            "revisions": [r0, _r1(digest)],
            "challenges": [_c1(digest)],
        }
        receipt = _build(exchange)
        self.assertEqual(receipt["proposal"]["content"], bound_content)
        self.assertEqual(receipt["proposal"]["content_digest"], digest)
        self.assertNotEqual(receipt["proposal"]["content"], live_content)

    def test_03_scalar_subclass_rejected(self) -> None:
        exchange = _complete()
        exchange["session_id"] = _HostileStr("session-1")
        _expect(self, "CONDUCTING_SOURCE_INVALID", lambda: _build(exchange))
        r0 = _r0(agent_id=_HostileStr("agent-a"))
        digest = canonical_digest(r0["content"])
        hostile = {
            "session_id": "session-1",
            "revisions": [r0, _r1(digest)],
            "challenges": [_c1(digest)],
        }
        _expect(self, "CONDUCTING_SOURCE_INVALID", lambda: _build(hostile))
        counted = _proposal_only()
        counted["revisions"][0]["created_order"] = _HostileInt(0)
        _expect(self, "CONDUCTING_SOURCE_INVALID", lambda: _build(counted))

    def test_04_container_subclass_rejected(self) -> None:
        exchange = _complete()
        exchange["revisions"] = _Rows(exchange["revisions"])
        _expect(self, "CONDUCTING_SOURCE_INVALID", lambda: _build(exchange))
        exchange = _complete()
        exchange["challenges"] = _Rows(exchange["challenges"])
        _expect(self, "CONDUCTING_SOURCE_INVALID", lambda: _build(exchange))
        exchange = _proposal_only()
        exchange["revisions"][0]["assumptions"] = _Reuse(
            (exchange["revisions"][0]["assumptions"][0],)
        )
        _expect(self, "CONDUCTING_SOURCE_INVALID", lambda: _build(exchange))

    def test_05_unknown_kwargs_rejected(self) -> None:
        _expect(self, "CONDUCTING_SOURCE_INVALID", lambda: _build(extra=True))

    def test_06_forbidden_assertions_rejected(self) -> None:
        for key in (
            "independent_evidence_count",
            "admission_status",
            "structural_candidate",
            "verification_kind",
            "claims_iw_acceptance",
            "Human Final",
            "human_final_status",
            "independence_score",
            "diversity_score",
            "consensus",
            "majority",
            "verified",
            "recovered",
            "VECTOR",
            "EIG",
            "canonical",
            "published",
            "deployed",
        ):
            _expect(
                self,
                "CONDUCTING_SCOPE_VIOLATION",
                lambda key=key: _build(**{key: True}),
            )
            exchange = _proposal_only()
            exchange[key] = True
            _expect(self, "CONDUCTING_SCOPE_VIOLATION", lambda exchange=exchange: _build(exchange))

    def test_07_hidden_chain_of_thought_rejected(self) -> None:
        for key in (
            "chain_of_thought",
            "private_reasoning",
            "hidden_reasoning",
            "scratchpad",
        ):
            exchange = _proposal_only()
            exchange[key] = "secret"
            _expect(self, "CONDUCTING_COT_FORBIDDEN", lambda exchange=exchange: _build(exchange))
        nested = _proposal_only()
        nested["revisions"][0]["content"] = {"payload": "proposal", "scratchpad": "secret"}
        _expect(self, "CONDUCTING_COT_FORBIDDEN", lambda: _build(nested))


class TestProposalRevision(unittest.TestCase):
    def test_08_valid_r0_proposal(self) -> None:
        receipt = _build(_proposal_only())
        self.assertEqual(receipt["proposal"]["revision_id"], "r0")
        self.assertEqual(receipt["proposal"]["agent_role"], "PROPOSER")
        self.assertEqual(receipt["proposal"]["created_order"], 0)
        self.assertNotIn("parent_revision_id", receipt["proposal"])
        self.assertEqual(receipt["sequence_status"], "INCOMPLETE_SEQUENCE")
        self.assertEqual(receipt["counterexample_status"], "NO_COUNTEREXAMPLE")
        _assert_closed(self, receipt)

    def test_09_r0_parent_forbidden(self) -> None:
        r0 = _r0(parent_revision_id="rX", parent_content_digest=_OTHER)
        _expect(
            self,
            "CONDUCTING_LINEAGE_INVALID",
            lambda: _build({"session_id": "session-1", "revisions": [r0], "challenges": []}),
        )

    def test_10_later_revision_requires_parent_id_and_digest(self) -> None:
        r0 = _r0()
        digest = canonical_digest(r0["content"])
        missing_parent = _r1(digest)
        del missing_parent["parent_revision_id"]
        _expect(
            self,
            "CONDUCTING_REVISION_UNBOUND",
            lambda: _build(
                {
                    "session_id": "session-1",
                    "revisions": [r0, missing_parent],
                    "challenges": [_c1(digest)],
                }
            ),
        )
        missing_digest = _r1(digest)
        del missing_digest["parent_content_digest"]
        _expect(
            self,
            "CONDUCTING_REVISION_UNBOUND",
            lambda: _build(
                {
                    "session_id": "session-1",
                    "revisions": [r0, missing_digest],
                    "challenges": [_c1(digest)],
                }
            ),
        )

    def test_11_wrong_parent_digest_rejected(self) -> None:
        r0 = _r0()
        digest = canonical_digest(r0["content"])
        _expect(
            self,
            "CONDUCTING_REVISION_UNBOUND",
            lambda: _build(
                {
                    "session_id": "session-1",
                    "revisions": [r0, _r1(_OTHER)],
                    "challenges": [_c1(digest)],
                }
            ),
        )

    def test_12_duplicate_revision_content_rejected(self) -> None:
        r0 = _r0()
        digest = canonical_digest(r0["content"])
        r1 = _r1(digest, payload="proposal")
        _expect(
            self,
            "CONDUCTING_REPLAY",
            lambda: _build(
                {
                    "session_id": "session-1",
                    "revisions": [r0, r1],
                    "challenges": [_c1(digest)],
                }
            ),
        )

    def test_13_noncontiguous_created_order_rejected(self) -> None:
        r0 = _r0()
        digest = canonical_digest(r0["content"])
        r1 = _r1(digest, created_order=2)
        _expect(
            self,
            "CONDUCTING_LINEAGE_INVALID",
            lambda: _build(
                {
                    "session_id": "session-1",
                    "revisions": [r0, r1],
                    "challenges": [_c1(digest)],
                }
            ),
        )

    def test_14_self_parent_rejected(self) -> None:
        r0 = _r0()
        digest = canonical_digest(r0["content"])
        r1 = _r1(digest, parent_revision_id="r1")
        _expect(
            self,
            "CONDUCTING_LINEAGE_INVALID",
            lambda: _build(
                {
                    "session_id": "session-1",
                    "revisions": [r0, r1],
                    "challenges": [_c1(digest)],
                }
            ),
        )

    def test_15_unpinned_aliases_rejected(self) -> None:
        for alias in _UNPINNED:
            r0 = _r0(revision_id=alias)
            _expect(
                self,
                "CONDUCTING_REVISION_UNBOUND",
                lambda r0=r0: _build(
                    {"session_id": "session-1", "revisions": [r0], "challenges": []}
                ),
            )
        r0 = _r0()
        digest = canonical_digest(r0["content"])
        r1 = _r1(digest, parent_revision_id="latest")
        _expect(
            self,
            "CONDUCTING_REVISION_UNBOUND",
            lambda: _build(
                {
                    "session_id": "session-1",
                    "revisions": [r0, r1],
                    "challenges": [_c1(digest)],
                }
            ),
        )
        exchange = _complete()
        exchange["target_artifact_digest"] = "current"
        _expect(self, "CONDUCTING_REVISION_UNBOUND", lambda: _build(exchange))


class TestChallenge(unittest.TestCase):
    def test_16_valid_challenge_bound_to_exact_revision(self) -> None:
        receipt = _build()
        challenge = receipt["challenges"][0]
        self.assertEqual(challenge["target_revision_id"], "r0")
        self.assertEqual(
            challenge["target_content_digest"],
            receipt["proposal"]["content_digest"],
        )
        self.assertEqual(challenge["result"], "COUNTEREXAMPLE_FOUND")
        self.assertEqual(receipt["sequence_status"], "COMPLETE_SEQUENCE")
        _assert_closed(self, receipt)

    def test_17_wrong_target_digest_rejected(self) -> None:
        r0 = _r0()
        digest = canonical_digest(r0["content"])
        _expect(
            self,
            "CONDUCTING_CHALLENGE_UNBOUND",
            lambda: _build(
                {
                    "session_id": "session-1",
                    "revisions": [r0, _r1(digest)],
                    "challenges": [_c1(_OTHER)],
                }
            ),
        )

    def test_18_unknown_target_revision_rejected(self) -> None:
        r0 = _r0()
        digest = canonical_digest(r0["content"])
        _expect(
            self,
            "CONDUCTING_CHALLENGE_UNBOUND",
            lambda: _build(
                {
                    "session_id": "session-1",
                    "revisions": [r0],
                    "challenges": [_c1(digest, target_revision_id="r9")],
                }
            ),
        )

    def test_19_challenge_replay_under_new_id_rejected(self) -> None:
        r0 = _r0()
        digest = canonical_digest(r0["content"])
        first = _c1(digest)
        second = _c1(digest, challenge_id="c2", created_order=1, event_order=2)
        r1 = _r1(digest, event_order=3)
        _expect(
            self,
            "CONDUCTING_REPLAY",
            lambda: _build(
                {
                    "session_id": "session-1",
                    "revisions": [r0, r1],
                    "challenges": [first, second],
                }
            ),
        )

    def test_20_unsupported_challenge_kind_rejected(self) -> None:
        r0 = _r0()
        digest = canonical_digest(r0["content"])
        _expect(
            self,
            "CONDUCTING_SOURCE_INVALID",
            lambda: _build(
                {
                    "session_id": "session-1",
                    "revisions": [r0],
                    "challenges": [_c1(digest, kind="PROOF")],
                }
            ),
        )

    def test_21_no_counterexample_never_emits_proof_token(self) -> None:
        r0 = _r0()
        digest = canonical_digest(r0["content"])
        challenge = _c1(digest, kind="WEAKENING", present=False)
        r1 = _r1(digest)
        receipt = _build(
            {
                "session_id": "session-1",
                "revisions": [r0, r1],
                "challenges": [challenge],
            }
        )
        self.assertEqual(receipt["challenges"][0]["result"], "NO_COUNTEREXAMPLE_FOUND")
        self.assertEqual(receipt["counterexample_status"], "NO_COUNTEREXAMPLE")
        self.assertNotIn("PROVEN_TRUE", json.dumps(receipt))
        _assert_closed(self, receipt)

    def test_22_counterexample_true_without_object_rejected(self) -> None:
        r0 = _r0()
        digest = canonical_digest(r0["content"])
        challenge = _c1(digest)
        del challenge["counterexample"]
        _expect(
            self,
            "CONDUCTING_SOURCE_INVALID",
            lambda: _build(
                {
                    "session_id": "session-1",
                    "revisions": [r0],
                    "challenges": [challenge],
                }
            ),
        )

    def test_23_counterexample_false_with_object_rejected(self) -> None:
        r0 = _r0()
        digest = canonical_digest(r0["content"])
        challenge = _c1(digest, kind="WEAKENING", present=False)
        challenge["counterexample"] = {"body": {"payload": "empty"}}
        _expect(
            self,
            "CONDUCTING_SOURCE_INVALID",
            lambda: _build(
                {
                    "session_id": "session-1",
                    "revisions": [r0],
                    "challenges": [challenge],
                }
            ),
        )

    def test_24_preserved_counterexample_survives_later_revision(self) -> None:
        receipt = _build()
        body = receipt["challenges"][0]["counterexample"]["body"]
        digest = receipt["challenges"][0]["counterexample_digest"]
        self.assertEqual(body, {"payload": "empty"})
        self.assertEqual(digest, canonical_digest(body))
        self.assertEqual(len(receipt["revisions"]), 2)
        self.assertEqual(receipt["counterexample_status"], "COUNTEREXAMPLE_ADDRESSED")
        self.assertNotEqual(receipt["counterexample_status"], "fixed")


class TestRevisionResponse(unittest.TestCase):
    def test_25_revision_responds_to_known_parent_challenge(self) -> None:
        receipt = _build()
        self.assertEqual(receipt["revisions"][1]["responds_to"], ["c1"])
        self.assertEqual(receipt["challenges"][0]["target_revision_id"], "r0")
        self.assertEqual(receipt["sequence_status"], "COMPLETE_SEQUENCE")

    def test_26_challenge_against_another_revision_rejected(self) -> None:
        r0 = _r0()
        digest = canonical_digest(r0["content"])
        c1 = _c1(digest, target_revision_id="r0")
        r1 = _r1(digest, responds_to=["c1"])
        r1_digest = canonical_digest(r1["content"])
        c2 = _c1(
            r1_digest,
            challenge_id="c2",
            target_revision_id="r1",
            created_order=1,
            event_order=3,
            present=False,
            kind="WEAKENING",
            rationale={
                "claim": "revision still fails",
                "assumptions": [_STATEMENT],
                "attack": "the same empty input still differs",
            },
        )
        r2 = {
            "revision_id": "r2",
            "content": _content("second"),
            "created_order": 2,
            "event_order": 4,
            "agent_id": "agent-a",
            "agent_role": "REVISER",
            "parent_revision_id": "r1",
            "parent_content_digest": r1_digest,
            "responds_to": ["c1"],
            "assumptions": [_open_assumption()],
        }
        _expect(
            self,
            "CONDUCTING_CHALLENGE_UNBOUND",
            lambda: _build(
                {
                    "session_id": "session-1",
                    "revisions": [r0, r1, r2],
                    "challenges": [c1, c2],
                }
            ),
        )

    def test_27_future_challenge_cannot_be_answered(self) -> None:
        r0 = _r0()
        digest = canonical_digest(r0["content"])
        r1 = _r1(digest, event_order=1, responds_to=["c1"])
        c1 = _c1(digest, event_order=2)
        _expect(
            self,
            "CONDUCTING_CHALLENGE_UNBOUND",
            lambda: _build(
                {
                    "session_id": "session-1",
                    "revisions": [r0, r1],
                    "challenges": [c1],
                }
            ),
        )

    def test_28_duplicate_responds_to_rejected(self) -> None:
        r0 = _r0()
        digest = canonical_digest(r0["content"])
        _expect(
            self,
            "CONDUCTING_CHALLENGE_UNBOUND",
            lambda: _build(
                {
                    "session_id": "session-1",
                    "revisions": [r0, _r1(digest, responds_to=["c1", "c1"])],
                    "challenges": [_c1(digest)],
                }
            ),
        )


class TestAssumptions(unittest.TestCase):
    def test_29_assumption_digest_recomputed(self) -> None:
        receipt = _build(_proposal_only())
        digest = _stmt_digest()
        self.assertEqual(receipt["assumption_records"][0]["assumption_digest"], digest)
        r0 = _r0()
        r0["assumptions"][0]["assumption_digest"] = _OTHER
        _expect(
            self,
            "CONDUCTING_SOURCE_INVALID",
            lambda: _build({"session_id": "session-1", "revisions": [r0], "challenges": []}),
        )

    def test_30_open_assumption_carried_forward(self) -> None:
        receipt = _build()
        self.assertEqual(receipt["unresolved_assumptions"], [_stmt_digest()])
        self.assertEqual(
            receipt["revisions"][1]["assumptions"][0]["introduced_in_revision"],
            "r0",
        )

    def test_31_silent_drop_rejected(self) -> None:
        r0 = _r0()
        digest = canonical_digest(r0["content"])
        r1 = _r1(digest, assumptions=[])
        _expect(
            self,
            "CONDUCTING_ASSUMPTION_DROPPED",
            lambda: _build(
                {
                    "session_id": "session-1",
                    "revisions": [r0, r1],
                    "challenges": [_c1(digest)],
                }
            ),
        )

    def test_32_resolved_assumption_requires_later_revision(self) -> None:
        r0 = _r0(assumptions=[_resolved_assumption(resolver="r0")])
        _expect(
            self,
            "CONDUCTING_REVISION_UNBOUND",
            lambda: _build({"session_id": "session-1", "revisions": [r0], "challenges": []}),
        )

    def test_33_invalid_resolution_ref_rejected(self) -> None:
        r0 = _r0()
        digest = canonical_digest(r0["content"])
        r1 = _r1(
            digest,
            assumptions=[_resolved_assumption(resolution_ref=_OTHER)],
        )
        _expect(
            self,
            "CONDUCTING_SOURCE_INVALID",
            lambda: _build(
                {
                    "session_id": "session-1",
                    "revisions": [r0, r1],
                    "challenges": [_c1(digest)],
                }
            ),
        )

    def test_34_unresolved_list_derived_not_caller_controlled(self) -> None:
        exchange = _complete()
        exchange["unresolved_assumptions"] = []
        _expect(self, "CONDUCTING_SCOPE_VIOLATION", lambda: _build(exchange))
        r0 = _r0()
        digest = canonical_digest(r0["content"])
        material = _challenge_material(_c1(digest))
        r1 = _r1(
            digest,
            assumptions=[
                _resolved_assumption(resolution_ref=canonical_digest(material))
            ],
        )
        receipt = _build(
            {
                "session_id": "session-1",
                "revisions": [r0, r1],
                "challenges": [_c1(digest)],
            }
        )
        self.assertEqual(receipt["unresolved_assumptions"], [])
        self.assertEqual(receipt["assumption_records"][0]["status"], "RESOLVED")


class TestHumanSelection(unittest.TestCase):
    def test_35_absent_selection_is_no_human_selection(self) -> None:
        receipt = _build()
        self.assertEqual(receipt["selection_status"], "NO_HUMAN_SELECTION")
        self.assertIs(receipt["human_selection"]["selection_present"], False)
        _assert_closed(self, receipt)

    def test_36_valid_human_selection_bound_to_id_and_digest(self) -> None:
        r0 = _r0()
        digest = canonical_digest(r0["content"])
        r1 = _r1(digest)
        selected = canonical_digest(r1["content"])
        receipt = _build(
            {
                "session_id": "session-1",
                "revisions": [r0, r1],
                "challenges": [_c1(digest)],
                "human_selection": {
                    "selected_revision_id": "r1",
                    "selected_content_digest": selected,
                    "selector_is_human": True,
                    "selection_note": "continue with r1",
                    "authority": False,
                },
            }
        )
        self.assertEqual(receipt["selection_status"], "REVISION_SELECTED")
        self.assertIs(receipt["human_selection"]["selector_is_human"], True)
        self.assertEqual(receipt["human_selection"]["selected_content_digest"], selected)
        self.assertIs(receipt["human_selection"]["authority"], False)
        _assert_closed(self, receipt)

    def test_37_selected_wrong_digest_rejected(self) -> None:
        r0 = _r0()
        digest = canonical_digest(r0["content"])
        _expect(
            self,
            "CONDUCTING_SELECTION_UNBOUND",
            lambda: _build(
                {
                    "session_id": "session-1",
                    "revisions": [r0, _r1(digest)],
                    "challenges": [_c1(digest)],
                    "human_selection": {
                        "selected_revision_id": "r1",
                        "selected_content_digest": digest,
                        "selector_is_human": True,
                    },
                }
            ),
        )

    def test_38_selector_is_human_false_rejected(self) -> None:
        r0 = _r0()
        digest = canonical_digest(r0["content"])
        r1 = _r1(digest)
        _expect(
            self,
            "CONDUCTING_SELECTION_UNBOUND",
            lambda: _build(
                {
                    "session_id": "session-1",
                    "revisions": [r0, r1],
                    "challenges": [_c1(digest)],
                    "human_selection": {
                        "selected_revision_id": "r1",
                        "selected_content_digest": canonical_digest(r1["content"]),
                        "selector_is_human": False,
                    },
                }
            ),
        )

    def test_39_agent_label_cannot_create_human_selection(self) -> None:
        r0 = _r0()
        digest = canonical_digest(r0["content"])
        r1 = _r1(digest)
        _expect(
            self,
            "CONDUCTING_SOURCE_INVALID",
            lambda: _build(
                {
                    "session_id": "session-1",
                    "revisions": [r0, r1],
                    "challenges": [_c1(digest)],
                    "human_selection": {
                        "selected_revision_id": "r1",
                        "selected_content_digest": canonical_digest(r1["content"]),
                        "selector_is_human": True,
                        "agent_id": "agent-a",
                    },
                }
            ),
        )

    def test_40_selection_never_emits_human_final_or_verified(self) -> None:
        r0 = _r0()
        digest = canonical_digest(r0["content"])
        r1 = _r1(digest)
        receipt = _build(
            {
                "session_id": "session-1",
                "revisions": [r0, r1],
                "challenges": [_c1(digest)],
                "human_selection": {
                    "selected_revision_id": "r1",
                    "selected_content_digest": canonical_digest(r1["content"]),
                    "selector_is_human": True,
                },
            }
        )
        self.assertEqual(receipt["selection_status"], "REVISION_SELECTED")
        self.assertNotEqual(receipt["selection_status"], "HUMAN_REVIEW_ACCEPTED")
        self.assertIs(receipt["authority"], False)
        _assert_closed(self, receipt)
        exchange = _complete()
        exchange["human_selection"] = {
            "selected_revision_id": "r1",
            "selected_content_digest": canonical_digest(_content("revised")),
            "selector_is_human": True,
            "human_final": True,
        }
        _expect(self, "CONDUCTING_SCOPE_VIOLATION", lambda: _build(exchange))


class TestReplayLineage(unittest.TestCase):
    def test_41_same_proposal_content_new_agent_label_replay(self) -> None:
        r0 = _r0()
        digest = canonical_digest(r0["content"])
        r1 = _r1(digest, payload="proposal", agent_id="agent-c")
        _expect(
            self,
            "CONDUCTING_REPLAY",
            lambda: _build(
                {
                    "session_id": "session-1",
                    "revisions": [r0, r1],
                    "challenges": [_c1(digest)],
                }
            ),
        )

    def test_42_same_challenge_content_new_challenger_label_replay(self) -> None:
        r0 = _r0()
        digest = canonical_digest(r0["content"])
        first = _c1(digest)
        second = _c1(
            digest,
            challenge_id="c2",
            challenger_id="agent-z",
            created_order=1,
            event_order=2,
        )
        r1 = _r1(digest, event_order=3)
        _expect(
            self,
            "CONDUCTING_REPLAY",
            lambda: _build(
                {
                    "session_id": "session-1",
                    "revisions": [r0, r1],
                    "challenges": [first, second],
                }
            ),
        )

    def test_43_parent_loop_rejected(self) -> None:
        r0 = _r0()
        digest = canonical_digest(r0["content"])
        r1 = _r1(digest, parent_revision_id="r1")
        _expect(
            self,
            "CONDUCTING_LINEAGE_INVALID",
            lambda: _build(
                {
                    "session_id": "session-1",
                    "revisions": [r0, r1],
                    "challenges": [_c1(digest)],
                }
            ),
        )

    def test_44_mutable_current_aliases_rejected(self) -> None:
        r0 = _r0()
        digest = canonical_digest(r0["content"])
        r1 = _r1(digest, revision_id="current")
        _expect(
            self,
            "CONDUCTING_REVISION_UNBOUND",
            lambda: _build(
                {
                    "session_id": "session-1",
                    "revisions": [r0, r1],
                    "challenges": [_c1(digest)],
                }
            ),
        )
        challenge = _c1(digest, target_revision_id="HEAD")
        _expect(
            self,
            "CONDUCTING_CHALLENGE_UNBOUND",
            lambda: _build(
                {
                    "session_id": "session-1",
                    "revisions": [r0],
                    "challenges": [challenge],
                }
            ),
        )

    def test_45_append_only_lineage_preserved(self) -> None:
        receipt = _build()
        self.assertEqual(
            [item["revision_id"] for item in receipt["revisions"]],
            ["r0", "r1"],
        )
        self.assertEqual(receipt["revisions"][0]["content"], _content("proposal"))
        self.assertEqual(receipt["challenges"][0]["counterexample"]["body"], {"payload": "empty"})
        self.assertEqual(receipt["revisions"][1]["parent_revision_id"], "r0")
        self.assertEqual(receipt["revisions"][1]["responds_to"], ["c1"])
        self.assertEqual(
            [item["event_order"] for item in receipt["revisions"]]
            + [item["event_order"] for item in receipt["challenges"]],
            [0, 2, 1],
        )


class TestSameClassReview(unittest.TestCase):
    def test_split_dict_lookup_cannot_replace_session(self) -> None:
        bound = _complete()
        live = copy.deepcopy(bound)
        live["session_id"] = "live-session"
        receipt = _build(_SplitDict(bound, live))
        self.assertEqual(receipt["session_id"], "session-1")

    def test_duplicate_mapping_keys_rejected(self) -> None:
        _expect(self, "CONDUCTING_SOURCE_INVALID", lambda: _build(_DupKeys()))

    def test_exact_tuple_copied_into_plain_list(self) -> None:
        r0 = _r0()
        digest = canonical_digest(r0["content"])
        exchange = {
            "session_id": "session-1",
            "revisions": (r0, _r1(digest)),
            "challenges": (_c1(digest),),
        }
        receipt = _build(exchange)
        self.assertIs(type(receipt["revisions"]), list)
        self.assertIs(type(receipt["challenges"]), list)
        self.assertEqual(receipt["sequence_status"], "COMPLETE_SEQUENCE")

    def test_digest_without_body_rejected(self) -> None:
        r0 = _r0()
        del r0["content"]
        r0["content_digest"] = _OTHER
        _expect(
            self,
            "CONDUCTING_SOURCE_INVALID",
            lambda: _build({"session_id": "session-1", "revisions": [r0], "challenges": []}),
        )

    def test_selection_id_without_digest_rejected(self) -> None:
        r0 = _r0()
        digest = canonical_digest(r0["content"])
        r1 = _r1(digest)
        _expect(
            self,
            "CONDUCTING_SOURCE_INVALID",
            lambda: _build(
                {
                    "session_id": "session-1",
                    "revisions": [r0, r1],
                    "challenges": [_c1(digest)],
                    "human_selection": {
                        "selected_revision_id": "r1",
                        "selector_is_human": True,
                    },
                }
            ),
        )

    def test_caller_result_rejected(self) -> None:
        r0 = _r0()
        digest = canonical_digest(r0["content"])
        challenge = _c1(digest, result="PROVEN_TRUE")
        _expect(
            self,
            "CONDUCTING_SOURCE_INVALID",
            lambda: _build(
                {
                    "session_id": "session-1",
                    "revisions": [r0],
                    "challenges": [challenge],
                }
            ),
        )

    def test_caller_sequence_status_rejected(self) -> None:
        exchange = _complete()
        exchange["sequence_status"] = "COMPLETE_SEQUENCE"
        _expect(self, "CONDUCTING_SCOPE_VIOLATION", lambda: _build(exchange))

    def test_byte_identical_challenge_is_invalid_not_proof(self) -> None:
        rationale = _rationale()
        r0 = _r0(content=rationale, assumptions=[_open_assumption()])
        digest = canonical_digest(rationale)
        challenge = _c1(digest, kind="WEAKENING", present=False, rationale=rationale)
        receipt = _build(
            {
                "session_id": "session-1",
                "revisions": [r0],
                "challenges": [challenge],
            }
        )
        self.assertEqual(receipt["challenges"][0]["result"], "INVALID_CHALLENGE")
        self.assertEqual(receipt["sequence_status"], "INCOMPLETE_SEQUENCE")
        self.assertNotIn("PROVEN_TRUE", json.dumps(receipt))

    def test_open_counterexample_without_revision(self) -> None:
        r0 = _r0()
        digest = canonical_digest(r0["content"])
        receipt = _build(
            {
                "session_id": "session-1",
                "revisions": [r0],
                "challenges": [_c1(digest)],
            }
        )
        self.assertEqual(receipt["counterexample_status"], "COUNTEREXAMPLE_OPEN")
        self.assertEqual(receipt["sequence_status"], "INCOMPLETE_SEQUENCE")

    def test_duplicate_counterexample_digest_replayed(self) -> None:
        r0 = _r0()
        digest = canonical_digest(r0["content"])
        first = _c1(digest)
        second = _c1(
            digest,
            challenge_id="c2",
            created_order=1,
            event_order=2,
            rationale={
                "claim": "another attack",
                "assumptions": [_STATEMENT],
                "attack": "a different write-up of the same empty input",
            },
        )
        _expect(
            self,
            "CONDUCTING_REPLAY",
            lambda: _build(
                {
                    "session_id": "session-1",
                    "revisions": [r0],
                    "challenges": [first, second],
                }
            ),
        )

    def test_same_provider_is_descriptive_not_replay(self) -> None:
        r0 = _r0(provider="same-lab", model="same-model")
        digest = canonical_digest(r0["content"])
        challenge = _c1(digest, provider="same-lab", model="same-model")
        r1 = _r1(digest, provider="same-lab", model="same-model")
        receipt = _build(
            {
                "session_id": "session-1",
                "revisions": [r0, r1],
                "challenges": [challenge],
            }
        )
        self.assertEqual(receipt["proposal"]["descriptive"]["provider"], "same-lab")
        self.assertIs(receipt["proposal"]["descriptive"]["authority"], False)
        self.assertEqual(receipt["sequence_status"], "COMPLETE_SEQUENCE")
        _assert_closed(self, receipt)

    def test_supplied_content_digest_must_match(self) -> None:
        r0 = _r0()
        r0["content_digest"] = _OTHER
        _expect(
            self,
            "CONDUCTING_REVISION_UNBOUND",
            lambda: _build({"session_id": "session-1", "revisions": [r0], "challenges": []}),
        )

    def test_resolved_assumption_cannot_reopen(self) -> None:
        r0 = _r0()
        digest = canonical_digest(r0["content"])
        r1 = _r1(digest, assumptions=[_resolved_assumption()])
        r1_digest = canonical_digest(r1["content"])
        c2 = _c1(
            r1_digest,
            challenge_id="c2",
            target_revision_id="r1",
            created_order=1,
            event_order=3,
            present=False,
            kind="WEAKENING",
            rationale={
                "claim": "reopen attempt",
                "assumptions": [_STATEMENT],
                "attack": "treat the resolved assumption as open again",
            },
            assumptions_attacked=[],
        )
        r2 = {
            "revision_id": "r2",
            "content": _content("reopened"),
            "created_order": 2,
            "event_order": 4,
            "agent_id": "agent-a",
            "agent_role": "REVISER",
            "parent_revision_id": "r1",
            "parent_content_digest": r1_digest,
            "responds_to": ["c2"],
            "assumptions": [_open_assumption()],
        }
        _expect(
            self,
            "CONDUCTING_LINEAGE_INVALID",
            lambda: _build(
                {
                    "session_id": "session-1",
                    "revisions": [r0, r1, r2],
                    "challenges": [_c1(digest), c2],
                }
            ),
        )

    def test_event_order_gap_rejected(self) -> None:
        r0 = _r0()
        digest = canonical_digest(r0["content"])
        c1 = _c1(digest, event_order=2)
        r1 = _r1(digest, event_order=3)
        _expect(
            self,
            "CONDUCTING_LINEAGE_INVALID",
            lambda: _build(
                {
                    "session_id": "session-1",
                    "revisions": [r0, r1],
                    "challenges": [c1],
                }
            ),
        )


class TestNoAcceptedWrites(unittest.TestCase):
    def test_generation_does_not_write_accepted_trees(self) -> None:
        before = subprocess.check_output(
            ["git", "-C", str(REPO), "status", "--porcelain"],
            text=True,
        )
        _build()
        after = subprocess.check_output(
            ["git", "-C", str(REPO), "status", "--porcelain"],
            text=True,
        )
        self.assertEqual(before, after)
        for line in after.splitlines():
            path = line[3:].strip().strip('"')
            self.assertTrue(path.startswith("conducting_receipt_v0"), path)


if __name__ == "__main__":
    unittest.main()
