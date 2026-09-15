from __future__ import annotations

from pathlib import Path
from typing import Any

from .request import read_json, write_json


class HumanReviewRequired(RuntimeError):
    pass


def enforce_human_review_gate(
    audit_root: Path,
    policy: dict[str, Any],
    decision: dict[str, Any],
) -> dict[str, Any]:
    """
    Human approval gate — only when explicitly required by policy.
    Operator provides HUMAN_REVIEW.json under the audit root (defined workflow action).
    """
    required = bool(policy.get("human_review_required", True))
    gate_path = audit_root / "HUMAN_REVIEW.json"

    if not required:
        record = {
            "required": False,
            "status": "NOT_REQUIRED",
            "decision_snapshot": decision.get("decision"),
        }
        write_json(audit_root / "HUMAN_REVIEW_GATE.json", record)
        return record

    if not gate_path.is_file():
        raise HumanReviewRequired(
            "HUMAN_REVIEW_REQUIRED: place HUMAN_REVIEW.json with status=ACCEPTED|REJECTED before freeze"
        )

    review = read_json(gate_path)
    status = str(review.get("status", "")).upper()
    if status not in {"ACCEPTED", "REJECTED"}:
        raise HumanReviewRequired("HUMAN_REVIEW.json must set status to ACCEPTED or REJECTED")

    record = {
        "required": True,
        "status": status,
        "reviewer": review.get("reviewer", "unspecified"),
        "notes": review.get("notes", ""),
        "decision_snapshot": decision.get("decision"),
    }
    write_json(audit_root / "HUMAN_REVIEW_GATE.json", record)

    if status != "ACCEPTED":
        raise HumanReviewRequired("HUMAN_REVIEW status is not ACCEPTED; freeze blocked")
    return record
