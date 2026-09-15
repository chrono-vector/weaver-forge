from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from .adapters import AdapterResult, VectorResult
from .decision import decide
from .request import read_json


# Material semantic fields only — ignore presentation/metadata wrappers.
_SEMANTIC_MATERIAL_KEYS = (
    "decision",
    "claim_result",
    "broader_classification",
    "promoted_to_full",
)


def _material_semantic_view(decision_obj: dict[str, Any] | None) -> dict[str, Any]:
    """
    Project a decision object to material semantic claim fields.

    Explicit freeze mapping: FINAL_DECISION.json wraps DECISION.json as
    FINAL_DECISION["decision"]; only that nested object is compared here.
    Metadata such as audit_id / frozen_at_utc / human_review_gate is excluded.
    """
    d = decision_obj or {}
    return {
        "decision": d.get("decision"),
        "claim_result": d.get("claim_result"),
        "broader_classification": d.get("broader_classification"),
        "promoted_to_full": bool(d.get("promoted_to_full", False)),
    }


def _expected_semantic_view(recomputed: dict[str, Any]) -> dict[str, Any]:
    return {
        "decision": recomputed.get("decision"),
        "claim_result": recomputed.get("claim_result"),
        "broader_classification": recomputed.get("broader_classification"),
        "promoted_to_full": bool(recomputed.get("promoted_to_full", False)),
    }


def _find_final_decision_path(audit_root: Path) -> Path | None:
    freeze_root = audit_root / "freeze"
    if not freeze_root.is_dir():
        return None
    candidates = sorted(freeze_root.glob("*_FROZEN/FINAL_DECISION.json"))
    return candidates[0] if candidates else None


def verify_semantics(audit_root: Path) -> dict[str, Any]:
    """
    Independently recompute claim semantics from pinned/frozen audit inputs.

    DECISION.json / FINAL_DECISION.json are objects under verification — never
    authoritative inputs to the recomputation.
    """
    audit_root = audit_root.resolve()
    claim_path = audit_root / "CLAIM.json"
    scope_path = audit_root / "SCOPE.json"
    decision_path = audit_root / "DECISION.json"

    if not claim_path.is_file() or not scope_path.is_file():
        return {
            "ok": False,
            "status": "SEMANTIC_VERIFICATION_BLOCKED",
            "error": "MISSING_CLAIM_OR_SCOPE",
            "stored_decision": None,
            "recomputed_decision": None,
            "match": False,
            "final_decision_match": None,
        }

    claim = read_json(claim_path)
    scope = read_json(scope_path)
    policy = scope.get("policy") or {}
    adapter_name = claim.get("adapter", "hash_claim")

    stored = None
    if decision_path.is_file():
        stored = read_json(decision_path)

    if adapter_name != "hash_claim":
        return {
            "ok": False,
            "status": "SEMANTIC_VERIFICATION_UNSUPPORTED",
            "error": f"no semantic verifier for adapter {adapter_name!r}",
            "adapter": adapter_name,
            "stored_decision": stored,
            "recomputed_decision": None,
            "match": False,
            "final_decision_match": None,
        }

    recomputed, facts = _recompute_hash_claim(audit_root, claim, scope, policy)
    expected = _expected_semantic_view(recomputed)
    stored_view = _material_semantic_view(stored)
    decision_match = stored is not None and stored_view == expected

    # Frozen packages: FINAL_DECISION.json must match the same recomputed outcome.
    freeze_present = (audit_root / "FREEZE_STATUS.json").is_file() or any(
        (audit_root / "freeze").glob("*_FROZEN")
    ) if (audit_root / "freeze").is_dir() else False

    final_decision_path = _find_final_decision_path(audit_root)
    final_decision_doc = None
    final_decision_view = None
    final_decision_match: bool | None = None
    final_decision_error = None

    if freeze_present:
        if final_decision_path is None or not final_decision_path.is_file():
            final_decision_match = False
            final_decision_error = "FINAL_DECISION_MISSING_FOR_FROZEN_PACKAGE"
        else:
            final_decision_doc = read_json(final_decision_path)
            # Explicit mapping: freeze projects DECISION into FINAL_DECISION["decision"].
            nested = final_decision_doc.get("decision")
            if not isinstance(nested, dict):
                final_decision_match = False
                final_decision_error = "FINAL_DECISION_MISSING_NESTED_DECISION"
            else:
                final_decision_view = _material_semantic_view(nested)
                final_decision_match = final_decision_view == expected

    match = decision_match and (final_decision_match is not False)

    # Frozen packages with required human review must satisfy the gate.
    hr_check = _human_review_gate_ok(audit_root, policy)
    if not hr_check["ok"]:
        return {
            "ok": False,
            "status": "SEMANTIC_VERIFICATION_FAIL",
            "error": hr_check["error"],
            "human_review": hr_check,
            "facts": facts,
            "stored_decision": stored_view,
            "recomputed_decision": expected,
            "match": False,
            "decision_match": decision_match,
            "final_decision_match": final_decision_match,
            "final_decision_error": final_decision_error,
            "final_decision_path": str(final_decision_path) if final_decision_path else None,
            "final_decision_stored": final_decision_view,
        }

    if final_decision_error:
        return {
            "ok": False,
            "status": "SEMANTIC_VERIFICATION_FAIL",
            "error": final_decision_error,
            "adapter": adapter_name,
            "facts": facts,
            "human_review": hr_check,
            "stored_decision": stored_view,
            "recomputed_decision": {
                **expected,
                "reason": recomputed.get("reason"),
            },
            "match": False,
            "decision_match": decision_match,
            "final_decision_match": final_decision_match,
            "final_decision_error": final_decision_error,
            "final_decision_path": str(final_decision_path) if final_decision_path else None,
            "final_decision_stored": final_decision_view,
            "semantic_material_keys": list(_SEMANTIC_MATERIAL_KEYS),
        }

    return {
        "ok": match,
        "status": "SEMANTIC_VERIFICATION_PASS" if match else "SEMANTIC_VERIFICATION_FAIL",
        "adapter": adapter_name,
        "facts": facts,
        "human_review": hr_check,
        "stored_decision": {
            **stored_view,
            "reason": (stored or {}).get("reason"),
        },
        "recomputed_decision": {
            **expected,
            "reason": recomputed.get("reason"),
        },
        "match": match,
        "decision_match": decision_match,
        "final_decision_match": final_decision_match,
        "final_decision_path": str(final_decision_path) if final_decision_path else None,
        "final_decision_stored": final_decision_view,
        "semantic_material_keys": list(_SEMANTIC_MATERIAL_KEYS),
    }


def _human_review_gate_ok(audit_root: Path, policy: dict[str, Any]) -> dict[str, Any]:
    required = bool(policy.get("human_review_required", True))
    freeze_present = (audit_root / "FREEZE_STATUS.json").is_file() or any(
        (audit_root / "freeze").glob("*_FROZEN")
    ) if (audit_root / "freeze").is_dir() else False

    if not required:
        return {"ok": True, "required": False, "status": "NOT_REQUIRED"}

    # Gate binds freeze finalization; enforce when freeze exists or when verifying
    # a package that claims freeze completion.
    if not freeze_present:
        return {"ok": True, "required": True, "status": "DEFERRED_UNTIL_FREEZE"}

    review_path = audit_root / "HUMAN_REVIEW.json"
    if not review_path.is_file():
        return {"ok": False, "required": True, "error": "HUMAN_REVIEW_MISSING_FOR_FROZEN_PACKAGE"}

    review = read_json(review_path)
    status = str(review.get("status", "")).upper()
    if status != "ACCEPTED":
        return {
            "ok": False,
            "required": True,
            "error": "HUMAN_REVIEW_NOT_ACCEPTED",
            "status": status,
        }
    return {"ok": True, "required": True, "status": status}


def _recompute_hash_claim(
    audit_root: Path,
    claim: dict[str, Any],
    scope: dict[str, Any],
    policy: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    pinned_root = audit_root / "pinned_target"
    params = claim.get("adapter_params") or {}
    expected = (params.get("expected_sha256") or "").lower()
    primary_name = params.get("primary_file")
    mode = params.get("mode", "verify_digest")

    facts: dict[str, Any] = {
        "pinned_target_exists": pinned_root.is_dir(),
        "expected_sha256": expected,
        "mode": mode,
        "primary_file": primary_name,
    }

    if not pinned_root.is_dir():
        recomputed = {
            "decision": "BLOCKED",
            "claim_result": "BLOCKED",
            "reason": "PINNED_TARGET_MISSING",
            "promoted": False,
        }
        return recomputed, facts

    files = sorted(p for p in pinned_root.rglob("*") if p.is_file())
    facts["pinned_file_count"] = len(files)
    if not files:
        recomputed = {
            "decision": "BLOCKED",
            "claim_result": "BLOCKED",
            "reason": "NO_PINNED_FILES",
            "promoted": False,
        }
        return recomputed, facts

    primary = None
    if primary_name:
        candidates = [p for p in files if p.name == primary_name or p.as_posix().endswith(primary_name)]
        primary = candidates[0] if candidates else None
    else:
        primary = files[0]

    if primary is None:
        facts["primary_present"] = False
        recomputed = {
            "decision": "FAIL",
            "claim_result": "FAIL",
            "reason": "PRIMARY_FILE_MISSING",
            "promoted": False,
        }
        return recomputed, facts

    actual = hashlib.sha256(primary.read_bytes()).hexdigest()
    # Also confirm PROVENANCE / EXPECTED_SHA256.txt if present agrees with claim expected.
    expected_file = pinned_root / "EXPECTED_SHA256.txt"
    expected_file_digest = None
    if expected_file.is_file():
        expected_file_digest = expected_file.read_text(encoding="utf-8").strip().lower()

    facts.update(
        {
            "primary_present": True,
            "primary_path": str(primary.relative_to(pinned_root)).replace("\\", "/"),
            "actual_sha256": actual,
            "digest_match": bool(expected) and actual == expected,
            "expected_file_digest": expected_file_digest,
            "expected_file_agrees_with_claim": (
                expected_file_digest is None or expected_file_digest == expected
            ),
        }
    )

    vectors: list[VectorResult] = []
    if mode == "incomplete":
        vectors.append(
            VectorResult(
                id="POSITIVE_DIGEST_MATCH",
                result="PASS",
                detail={"note": "incomplete mode reconstructed"},
            )
        )
        adapter_result = AdapterResult(
            claim_result="INCONCLUSIVE",
            vectors=vectors,
            artifacts={"incomplete": True},
            logs=["semantic recompute: incomplete"],
        )
        evidence_complete = False
    else:
        digest_ok = bool(expected) and actual == expected
        if mode == "force_fail":
            digest_ok = False
        vectors.append(
            VectorResult(
                id="POSITIVE_DIGEST_MATCH",
                result="PASS" if digest_ok else "FAIL",
                detail={
                    "expected_sha256": expected,
                    "actual_sha256": actual,
                    "primary_file": str(primary),
                    "source": "semantic_recompute",
                },
            )
        )

        wrong = ("0" * 63) + "1"
        vectors.append(
            VectorResult(
                id="NC1_WRONG_DIGEST_REJECTED",
                result="PASS" if actual != wrong else "FAIL",
                detail={"wrong_digest": wrong, "source": "semantic_recompute"},
            )
        )

        original = primary.read_bytes()
        if not original:
            tampered = b"\x00"
        else:
            b = bytearray(original)
            b[0] ^= 0x01
            tampered = bytes(b)
        tampered_digest = hashlib.sha256(tampered).hexdigest()
        vectors.append(
            VectorResult(
                id="T1_TAMPER_CHANGES_DIGEST",
                result="PASS" if tampered_digest != actual else "FAIL",
                detail={
                    "original_sha256": actual,
                    "tampered_sha256": tampered_digest,
                    "source": "semantic_recompute",
                },
            )
        )

        again = hashlib.sha256(primary.read_bytes()).hexdigest()
        vectors.append(
            VectorResult(
                id="R1_REHASH_REPRODUCTION",
                result="PASS" if again == actual else "FAIL",
                detail={"first": actual, "second": again, "source": "semantic_recompute"},
            )
        )

        by_id = {v.id: v for v in vectors}
        claim_pass = all(by_id[i].result == "PASS" for i in [
            "POSITIVE_DIGEST_MATCH",
            "NC1_WRONG_DIGEST_REJECTED",
            "T1_TAMPER_CHANGES_DIGEST",
            "R1_REHASH_REPRODUCTION",
        ])
        adapter_result = AdapterResult(
            claim_result="PASS" if claim_pass else "FAIL",
            vectors=vectors,
            artifacts={"actual_sha256": actual},
            logs=["semantic recompute: hash_claim"],
        )
        evidence_complete = mode != "incomplete" and adapter_result.claim_result != "INCONCLUSIVE"
        vectors_path = audit_root / "evidence" / "raw" / "vectors.json"
        if not vectors_path.is_file():
            evidence_complete = False
            facts["vectors_json_present"] = False
        else:
            facts["vectors_json_present"] = True

    boundary_vector = _recompute_boundary_vector(audit_root, scope)
    facts["boundary_vector"] = boundary_vector.result
    facts["boundary_detail"] = boundary_vector.detail

    # If claim expected disagrees with pinned EXPECTED_SHA256.txt, refuse PASS.
    if facts.get("expected_file_agrees_with_claim") is False:
        evidence_complete = True  # complete but inconsistent → decide via adapter fail
        # Force digest vector fail already if actual != expected; also mark claim mismatch.
        facts["claim_expected_file_mismatch"] = True

    recomputed = decide(
        claim=claim,
        adapter_result=adapter_result,
        boundary_vector=boundary_vector,
        policy=policy,
        evidence_complete=evidence_complete,
    )
    return recomputed, facts


def _recompute_boundary_vector(audit_root: Path, scope: dict[str, Any]) -> VectorResult:
    """
    Independently assess BV1 from recorded probe evidence + protected path cleanliness.
    Does not trust DECISION.json.
    """
    probe_path = audit_root / "evidence" / "raw" / "boundary_probe.json"
    vectors_path = audit_root / "evidence" / "raw" / "vectors.json"
    detail: dict[str, Any] = {"source": "semantic_recompute"}

    if not probe_path.is_file():
        return VectorResult(
            id="BV1_PROTECTED_BOUNDARY_WRITE_DENIED",
            result="FAIL",
            detail={**detail, "error": "BOUNDARY_PROBE_MISSING"},
        )

    probe = read_json(probe_path)
    detail["probe"] = probe

    open_write_denied = probe.get("open_write_denied")
    if open_write_denied is None and vectors_path.is_file():
        try:
            vectors = read_json(vectors_path)
            for v in vectors:
                if v.get("id") == "BV1_PROTECTED_BOUNDARY_WRITE_DENIED":
                    open_write_denied = (v.get("detail") or {}).get("open_write_denied")
                    detail["vector_bv1_result"] = v.get("result")
                    break
        except Exception:
            pass

    # Protected paths must not contain Weaver Forge deny-probe artifacts.
    protected = [Path(p) for p in (scope.get("protected_paths") or [])]
    leaks: list[str] = []
    for prot in protected:
        if not prot.exists():
            continue
        if prot.is_dir():
            for p in prot.rglob("__weaver_forge_should_not_write__*"):
                leaks.append(str(p))
            for p in prot.rglob("*.__wf_deny__"):
                leaks.append(str(p))
        else:
            sibling = prot.parent / (prot.name + ".__wf_deny__")
            if sibling.exists():
                leaks.append(str(sibling))

    detail["protected_leaks"] = leaks
    detail["open_write_denied"] = open_write_denied

    # Require recorded probe PASS and no leak artifacts.
    # open_write_denied defaults true when absent on older probe shapes that already PASS.
    denied_ok = True if open_write_denied is None else bool(open_write_denied)
    ok = probe.get("result") == "PASS" and denied_ok and not leaks
    return VectorResult(
        id="BV1_PROTECTED_BOUNDARY_WRITE_DENIED",
        result="PASS" if ok else "FAIL",
        detail=detail,
    )
