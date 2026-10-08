"""Closed deterministic PSM control inputs; caller input is not used.

Every JSON control keeps the accepted record's closed top-level key set, so a
negative control can only be refused by the intended rule inside the pinned
validator and never by the generic top-level-schema early return.
"""
from __future__ import annotations

import copy
import json

HUMAN_FINAL_PRODUCTION_NONCLAIMS = ("does_not_create_human_final",
                                    "does_not_grant_production_permission")


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
    elif case_id == "PSM_NEG_HUMAN_FINAL_PRODUCTION_INFERENCE":
        # Infer Human Final from a non-Human-Final (verification) source record and
        # drop the Human Final / production-permission nonclaims. Both are refused by
        # dedicated rules in the pinned validator; no top-level key is added.
        value["source_records"][1]["record_kind"] = "human_final"
        value["nonclaims"] = [item for item in value["nonclaims"]
                              if item not in HUMAN_FINAL_PRODUCTION_NONCLAIMS]
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
