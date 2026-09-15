from __future__ import annotations

import traceback
from pathlib import Path
from typing import Any

from .adapters.hash_claim import get_adapter
from .baseline import snapshot_baseline
from .boundary import BoundaryManager, BoundaryViolation
from .claim_scope import compile_claim_and_scope
from .decision import decide
from .evidence import EvidenceCollector
from .freeze import assert_one_shot_freeze_allowed, create_freeze_package
from .independent_verification import run_independent_verification_hook
from .pin import pin_target
from .request import AuditRequest, read_json, sha256_file, stable_run_id, utc_now, write_json
from .review_gate import HumanReviewRequired, enforce_human_review_gate
from .semantic_verification import verify_semantics
from .adapters import VectorResult


class AuditOrchestrator:
    """
    Predefined lifecycle:
    REQUEST → SCOPE/CLAIM → BOUNDARY → BASELINE → PIN → EXECUTION → EVIDENCE →
    CONTROLS → DECISION → HUMAN REVIEW (if policy) → MANIFEST/SHA → FREEZE → FINAL PACKAGE
    """

    def __init__(self, runs_parent: Path):
        self.runs_parent = runs_parent.resolve()
        self.runs_parent.mkdir(parents=True, exist_ok=True)

    def create_run(self, request: AuditRequest) -> Path:
        audit_id = stable_run_id("WFA")
        audit_root = self.runs_parent / audit_id
        if audit_root.exists():
            raise RuntimeError(f"run directory already exists: {audit_root}")
        audit_root.mkdir(parents=True, exist_ok=False)
        write_json(
            audit_root / "AUDIT_REQUEST.json",
            {
                "audit_id": audit_id,
                "received_at_utc": utc_now(),
                "target_path": request.target_path,
                "claim": request.claim,
                "policy": request.policy,
                "protected_paths": request.protected_paths,
                "prior_freeze_sums": request.prior_freeze_sums,
            },
        )
        return audit_root

    def run_through_decision(self, request: AuditRequest, audit_root: Path | None = None) -> dict[str, Any]:
        """Execute lifecycle through DECISION (and optional auto-freeze if policy allows)."""
        if audit_root is None:
            audit_root = self.create_run(request)
        audit_id = audit_root.name
        failure_log: list[str] = []

        try:
            compiled = compile_claim_and_scope(request, audit_root, audit_id)
            claim = compiled["claim"]
            scope = compiled["scope"]

            boundary = BoundaryManager(
                allowed_root=audit_root,
                protected_paths=request.protected_paths,
            )

            baseline = snapshot_baseline(
                audit_root,
                audit_id,
                request.protected_paths,
                request.prior_freeze_sums,
            )

            expected = (claim.get("adapter_params") or {}).get("expected_sha256")
            provenance = pin_target(
                boundary,
                audit_root,
                Path(request.target_path),
                expected_sha256=expected if Path(request.target_path).is_file() else None,
            )

            evidence = EvidenceCollector(boundary, audit_root)

            # Boundary violation control (real enforcer, not simulation-only)
            probe_target = None
            if request.protected_paths:
                prot = Path(request.protected_paths[0]).resolve()
                probe_target = prot / "__weaver_forge_should_not_write__.txt" if prot.is_dir() else prot.parent / (prot.name + ".__wf_deny__")
            else:
                # Use sibling outside allowed root
                probe_target = audit_root.parent / f"{audit_id}_OUTSIDE_WRITE_PROBE.txt"
            bv = boundary.probe_protected_write(probe_target)
            # Extra: try actual write via open_write and ensure it raises
            write_denied = False
            try:
                boundary.open_write(probe_target, "DENIED\n")
            except BoundaryViolation:
                write_denied = True
            bv_vector = VectorResult(
                id="BV1_PROTECTED_BOUNDARY_WRITE_DENIED",
                result="PASS" if (bv["result"] == "PASS" and write_denied and not probe_target.exists()) else "FAIL",
                detail={**bv, "open_write_denied": write_denied},
            )
            evidence.write_raw_json("boundary_probe.json", bv_vector.detail)

            adapter = get_adapter(claim.get("adapter", "hash_claim"))
            adapter_result = adapter.execute(
                audit_root / "pinned_target",
                claim,
                evidence.raw,
            )
            evidence.write_log("adapter.log", "\n".join(adapter_result.logs))
            evidence.write_raw_json(
                "vectors.json",
                [v.__dict__ for v in adapter_result.vectors] + [bv_vector.__dict__],
            )

            iv = run_independent_verification_hook(audit_root, request.policy)
            if iv.get("result") == "BLOCKED":
                write_json(
                    audit_root / "DECISION.json",
                    {
                        "decision": "BLOCKED",
                        "claim_result": "BLOCKED",
                        "reason": "INDEPENDENT_VERIFICATION_BLOCKED",
                        "independent_verification": iv,
                        "promoted": False,
                    },
                )
                evidence.bind_sha256sums()
                return {
                    "audit_id": audit_id,
                    "audit_root": str(audit_root),
                    "decision": read_json(audit_root / "DECISION.json"),
                    "independent_verification": iv,
                    "frozen": False,
                }

            # Incomplete evidence detection
            mode = (claim.get("adapter_params") or {}).get("mode")
            evidence_complete = mode != "incomplete" and adapter_result.claim_result != "INCONCLUSIVE"
            # Also require vectors.json and provenance
            if not (evidence.raw / "vectors.json").is_file():
                evidence_complete = False

            decision = decide(
                claim=claim,
                adapter_result=adapter_result,
                boundary_vector=bv_vector,
                policy=request.policy,
                evidence_complete=evidence_complete,
            )
            decision["independent_verification"] = {
                "status": iv.get("status"),
                "result": iv.get("result"),
                "claims_iw_acceptance": False,
            }
            write_json(audit_root / "DECISION.json", decision)

            manifest = {
                "audit_id": audit_id,
                "lifecycle": "weaver_forge_audit_lifecycle_v0",
                "stages_completed_through": "DECISION",
                "started_request": True,
                "claim_id": claim["claim_id"],
                "adapter": claim.get("adapter"),
                "decision": decision.get("decision"),
                "claim_result": decision.get("claim_result"),
                "promoted_to_full": False,
                "baseline_prior_freeze_ok": baseline["prior_freeze_integrity"]["all_ok"],
                "provenance_files": len(provenance.get("files") or []),
                "timestamp_utc": utc_now(),
            }
            write_json(audit_root / "EXECUTION_MANIFEST.json", manifest)
            evidence.bind_sha256sums()

            result = {
                "audit_id": audit_id,
                "audit_root": str(audit_root),
                "decision": decision,
                "manifest": manifest,
                "awaiting_human_review": bool(request.policy.get("human_review_required", True)),
                "frozen": False,
            }

            # Auto-freeze only when policy explicitly disables human review OR review already present
            if not request.policy.get("human_review_required", True):
                freeze_status = self.freeze_run(audit_root, request.policy, decision)
                result["frozen"] = True
                result["freeze"] = freeze_status
            elif (audit_root / "HUMAN_REVIEW.json").is_file():
                freeze_status = self.freeze_run(audit_root, request.policy, decision)
                result["frozen"] = True
                result["freeze"] = freeze_status

            return result

        except Exception as e:
            failure_log.append(traceback.format_exc())
            # Failure-path preservation: never delete the run; record FAILURE.json
            try:
                write_json(
                    audit_root / "FAILURE.json",
                    {
                        "audit_id": audit_root.name,
                        "failed_at_utc": utc_now(),
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "traceback": failure_log[-1],
                        "preserved": True,
                        "false_pass_forbidden": True,
                    },
                )
            except Exception:
                pass
            raise

    def freeze_run(
        self,
        audit_root: Path,
        policy: dict[str, Any],
        decision: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        audit_root = audit_root.resolve()
        # One-shot from FREEZE_STATUS (independent of freeze dir presence) —
        # must run before any SHA rebind or package mutation.
        assert_one_shot_freeze_allowed(audit_root)
        if decision is None:
            from .request import read_json

            decision = read_json(audit_root / "DECISION.json")

        # Re-load protected paths from SCOPE if present
        from .request import read_json

        scope = read_json(audit_root / "SCOPE.json")
        boundary = BoundaryManager(
            allowed_root=audit_root,
            protected_paths=scope.get("protected_paths") or [],
        )
        review = enforce_human_review_gate(audit_root, policy, decision)

        # Re-verify sums before freeze
        evidence = EvidenceCollector(boundary, audit_root)
        # Refresh sums to include DECISION etc., then verify
        evidence.bind_sha256sums()
        verify = evidence.verify_sha256sums()
        if not verify["ok"]:
            write_json(audit_root / "FAILURE.json", {
                "error": "SHA256SUMS_MISMATCH_BEFORE_FREEZE",
                "verify": verify,
                "preserved": True,
            })
            raise RuntimeError("SHA256SUMS_MISMATCH_BEFORE_FREEZE")

        # Evidence tamper detection support: if policy asks verify_only integrity
        status = create_freeze_package(
            boundary,
            audit_root,
            audit_root.name,
            decision,
            review,
        )
        # Update execution manifest BEFORE final SHA binding so verify matches disk.
        write_json(audit_root / "EXECUTION_MANIFEST.json", {
            **(read_json(audit_root / "EXECUTION_MANIFEST.json")),
            "stages_completed_through": "FREEZE",
            "freeze_performed": True,
            "freeze": status,
        })
        evidence.bind_sha256sums()
        return status

    def verify_run(self, audit_root: Path) -> dict[str, Any]:
        from .request import read_json

        audit_root = audit_root.resolve()
        evidence = EvidenceCollector(BoundaryManager(audit_root, []), audit_root)
        sums_verify = evidence.verify_sha256sums()
        freeze_status = None
        freeze_sums_ok = None
        fs = audit_root / "FREEZE_STATUS.json"
        if fs.is_file():
            freeze_status = read_json(fs)
            freeze_dir = Path(freeze_status["freeze_directory"])
            sums = freeze_dir / "SHA256SUMS.txt"
            ok = 0
            fail = 0
            for line in sums.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                digest, name = line.split(None, 1)
                p = freeze_dir / name
                if not p.is_file() or sha256_file(p) != digest.lower():
                    fail += 1
                else:
                    ok += 1
            freeze_sums_ok = fail == 0
        decision = read_json(audit_root / "DECISION.json") if (audit_root / "DECISION.json").is_file() else None
        semantic = verify_semantics(audit_root)
        hash_ok = bool(sums_verify["ok"]) and (freeze_sums_ok is not False)
        verify_ok = hash_ok and bool(semantic.get("ok"))
        return {
            "audit_root": str(audit_root),
            "sha256sums_ok": sums_verify["ok"],
            "sha256sums": sums_verify,
            "freeze_status": freeze_status,
            "freeze_sums_ok": freeze_sums_ok,
            "decision": decision,
            "semantic_verification": semantic,
            "semantic_ok": bool(semantic.get("ok")),
            "verify_ok": verify_ok,
            "has_failure_artifact": (audit_root / "FAILURE.json").is_file(),
        }
