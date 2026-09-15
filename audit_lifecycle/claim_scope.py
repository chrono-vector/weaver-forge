from __future__ import annotations

from pathlib import Path
from typing import Any

from .request import AuditRequest, validate_claim_id, write_json


def compile_claim_and_scope(
    request: AuditRequest,
    audit_root: Path,
    audit_id: str,
) -> dict[str, Any]:
    """Compile claim + scope manifests from operator request (no ad-hoc redesign)."""
    validate_claim_id(str(request.claim["id"]))
    target = Path(request.target_path).resolve()
    if not target.exists():
        raise FileNotFoundError(f"audit target not found: {target}")

    claim_doc = {
        "audit_id": audit_id,
        "claim_id": request.claim["id"],
        "statement": request.claim["statement"],
        "pass_criteria": request.claim.get("pass_criteria", []),
        "fail_criteria": request.claim.get("fail_criteria", []),
        "adapter": request.claim.get("adapter", "hash_claim"),
        "adapter_params": request.claim.get("adapter_params", {}),
        "target_path": str(target),
    }
    scope_doc = {
        "audit_id": audit_id,
        "target_path": str(target),
        "allowed_write_boundary": [str(audit_root.resolve()), str(audit_root.resolve()) + "/**"],
        "protected_paths": [str(Path(p).resolve()) for p in request.protected_paths],
        "policy": request.policy,
        "notes": "Compiled by audit_lifecycle.claim_scope; operator must not hand-edit during run.",
    }
    write_json(audit_root / "CLAIM.json", claim_doc)
    write_json(audit_root / "SCOPE.json", scope_doc)
    return {"claim": claim_doc, "scope": scope_doc}
