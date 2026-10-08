"""Closed deterministic PSM control inputs; caller input is not used.

Every JSON control keeps the accepted record's closed top-level key set, so a
negative control can only be refused by the intended rule inside the pinned
validator and never by the generic top-level-schema early return.
"""
from __future__ import annotations

import copy
import json

# The only production-related rule in the pinned validator is the required-nonclaims
# rule (_REQUIRED_NONCLAIMS); it has no rule rejecting a positive production grant.
PRODUCTION_NONCLAIM = "does_not_grant_production_permission"


def case_value(case_id, accepted_bytes):
    value = copy.deepcopy(json.loads(accepted_bytes))
    if case_id == "PSM_POSITIVE_ACCEPTED_RECORD":
        pass
    elif case_id == "PSM_NEG_UNSUPPORTED_STRONGER_EARNED":
        value["earned"][0]["description"] = "Unsupported stronger claim"
    elif case_id == "PSM_NEG_SOURCE_BINDING_MISMATCH":
        value["source_records"][0]["path"] = "docs/inr_missing_source.md"
    elif case_id == "PSM_NEG_BLOCKER_DEBT_REMOVAL":
        value["validation_debt"].pop(0)
    elif case_id == "PSM_NEG_COUNTEREXAMPLE_DELETION":
        value["counterexamples"] = []
    elif case_id == "PSM_NEG_HISTORY_COLLAPSE":
        value["counterexamples"][0]["outcome_history"] = ["PASS"]
    elif case_id == "PSM_NEG_UNKNOWN_CLAIM_CLASS":
        value["assumptions"][0]["status"] = "PASS"
    elif case_id == "PSM_NEG_INDEPENDENT_REPRODUCTION_INFERENCE":
        value["replayability"]["independent_reproduction"] = "ESTABLISHED"
    elif case_id == "PSM_NEG_HUMAN_FINAL_INFERENCE":
        # Declare the SEIC verification source record as Human Final. Its content at
        # the declared commit has no HUMAN_REVIEW_ACCEPTED decision, so the pinned
        # _HUMAN_ACCEPTANCE source rule refuses it. Nonclaims are left intact so this
        # case tests that single rule only.
        value["source_records"][1]["record_kind"] = "human_final"
    elif case_id == "PSM_REQUIRED_PRODUCTION_NONCLAIM":
        # Omit exactly the required production-permission nonclaim; refused by the
        # pinned required-nonclaims rule. This is NOT a positive production grant.
        value["nonclaims"] = [item for item in value["nonclaims"] if item != PRODUCTION_NONCLAIM]
    else:
        raise ValueError("unknown closed case")
    if set(value) != set(json.loads(accepted_bytes)):
        raise ValueError("closed control changed the top-level key set")
    return value


def case_bytes(case_id, accepted_bytes):
    if case_id == "PSM_NEG_MUTATED_ARCHIVE_OR_INPUT":
        return b"invalid UTF-8 input: \xff"
    value = case_value(case_id, accepted_bytes)
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
            + "\n").encode("utf-8")
