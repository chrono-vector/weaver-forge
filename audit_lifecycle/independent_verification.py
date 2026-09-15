from __future__ import annotations

from pathlib import Path
from typing import Any

from .request import utc_now, write_json


def run_independent_verification_hook(
    audit_root: Path,
    policy: dict[str, Any],
) -> dict[str, Any]:
    """
    Lifecycle stage: Independent verification hook.

    Default: record NOT_RUN / NOT_CLAIMED unless policy explicitly enables a local tool.
    Never silently claims Independent Witness acceptance.
    """
    mode = str(policy.get("independent_verification", "record_only")).lower()
    record: dict[str, Any] = {
        "stage": "independent_verification",
        "at_utc": utc_now(),
        "mode": mode,
        "claims_iw_acceptance": False,
        "claims_independent_witness": False,
        "note": (
            "Weaver Forge lifecycle records this stage explicitly. "
            "Existing tools under external_verifications/ may be invoked only when policy enables them; "
            "PASS here is not IW acceptance."
        ),
    }

    if mode in {"skip", "record_only", "not_required"}:
        record["status"] = "RECORDED_NOT_RUN"
        record["result"] = "NOT_CLAIMED"
    elif mode == "require_external_tool":
        tool = policy.get("independent_verification_tool")
        if not tool:
            record["status"] = "BLOCKED"
            record["result"] = "BLOCKED"
            record["error"] = "independent_verification_tool not configured"
        else:
            # Do not auto-execute arbitrary tools; require operator-provided receipt path.
            receipt = policy.get("independent_verification_receipt")
            if not receipt or not Path(receipt).is_file():
                record["status"] = "BLOCKED"
                record["result"] = "BLOCKED"
                record["error"] = "independent_verification_receipt missing"
            else:
                record["status"] = "RECEIPT_BOUND"
                record["result"] = "RECEIPT_PRESENT"
                record["receipt_path"] = str(Path(receipt).resolve())
    else:
        record["status"] = "RECORDED_NOT_RUN"
        record["result"] = "NOT_CLAIMED"
        record["warning"] = f"unknown mode {mode!r}; defaulted to NOT_CLAIMED"

    write_json(audit_root / "INDEPENDENT_VERIFICATION.json", record)
    return record
