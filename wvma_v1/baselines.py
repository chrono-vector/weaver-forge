"""Code-owned baseline profiles for WVMA-V1 Batch B1.

Profiles are identifiers only. Catalog text never supplies commands.
All builds occur under a caller-provided disposable workspace root.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from typing import Any, Callable

from audit_lifecycle.boundary import BoundaryManager
from audit_lifecycle.epistemic.expectation import (
    LEGACY_LIFECYCLE,
    R4B_CONTRACT_MARKER,
    build_r4b_expectation,
    expectation_digest,
)
from audit_lifecycle.epistemic.reconstructability import (
    REPORT_FILENAME,
    emit_reconstructability_report,
)
from audit_lifecycle.epistemic.review_disagreement import (
    create_disagreement_record,
    create_successor_record,
    write_disagreement_record,
)
from audit_lifecycle.evidence import EvidenceCollector
from audit_lifecycle.orchestrator import AuditOrchestrator
from audit_lifecycle.request import AuditRequest, read_json, sha256_file, write_json
from audit_lifecycle.review_gate import HumanReviewRequired

FIXED_UTC = "2026-01-01T00:00:00.000000Z"
# Root-independent path prefix for disposable absolute paths in baselines.
STABLE_ROOT = "WVMA_STABLE_ROOT"
FIXED_CAMPAIGN_INVOCATION_ID = "INV-WVMA-B1-FIXED-00000000"
FRESH_TARGET = (
    Path(__file__).resolve().parent.parent
    / "audit_lifecycle"
    / "fixtures"
    / "fresh_target"
    / "README.txt"
)

PROFILE_AUDIT_R4B_ZERO_REVIEW = "AUDIT_R4B_ZERO_REVIEW"
PROFILE_AUDIT_R4B_REVIEW_CHAIN = "AUDIT_R4B_REVIEW_CHAIN"
PROFILE_AUDIT_HUMAN_REVIEW_PREFREEZE = "AUDIT_HUMAN_REVIEW_PREFREEZE"
PROFILE_CAMPAIGN_TEST_ONLY = "CAMPAIGN_TEST_ONLY"

ALLOWED_BASELINE_PROFILES = frozenset(
    {
        PROFILE_AUDIT_R4B_ZERO_REVIEW,
        PROFILE_AUDIT_R4B_REVIEW_CHAIN,
        PROFILE_AUDIT_HUMAN_REVIEW_PREFREEZE,
        PROFILE_CAMPAIGN_TEST_ONLY,
    }
)


class BaselineError(ValueError):
    """Baseline profile construction rejection."""


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _positions(a: str = "PASS", b: str = "FAIL") -> list[dict[str, str]]:
    return [
        {"reviewer_id": "rev-A", "position": a, "label": "A"},
        {"reviewer_id": "rev-B", "position": b, "label": "B"},
    ]


def _copy_fresh_target(workspace: Path) -> tuple[Path, str]:
    target_dir = workspace / "target"
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / "README.txt"
    shutil.copy2(FRESH_TARGET, target)
    return target, sha256_file(target)


def _scrub_timestamps(obj: Any) -> Any:
    if isinstance(obj, dict):
        out: dict[str, Any] = {}
        for key, value in obj.items():
            if key.endswith("_utc") or key in {
                "received_at_utc",
                "frozen_at_utc",
                "started_at_utc",
                "completed_at_utc",
                "timestamp_utc",
                "created_at_utc",
                "updated_at_utc",
                "validated_at_utc",
                "generated_at_utc",
                "intent_utc",
            }:
                out[key] = FIXED_UTC
            else:
                out[key] = _scrub_timestamps(value)
        return out
    if isinstance(obj, list):
        return [_scrub_timestamps(x) for x in obj]
    return obj


def _workspace_for_audit(audit_root: Path) -> Path:
    """runs/<audit_id> → disposable workspace root."""
    return audit_root.resolve().parent.parent


def _path_rewrite_mapping(audit_root: Path) -> list[tuple[str, str]]:
    workspace = _workspace_for_audit(audit_root)
    audit = audit_root.resolve()
    pairs: dict[str, str] = {}
    for src, dst in (
        (audit, f"{STABLE_ROOT}/runs/{audit_root.name}"),
        (workspace.resolve(), STABLE_ROOT),
    ):
        text = str(src)
        pairs[text] = dst
        pairs[text.replace("\\", "/")] = dst
    return sorted(pairs.items(), key=lambda item: len(item[0]), reverse=True)


def _rewrite_disposable_paths(obj: Any, mapping: list[tuple[str, str]]) -> Any:
    if isinstance(obj, dict):
        return {k: _rewrite_disposable_paths(v, mapping) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_rewrite_disposable_paths(x, mapping) for x in obj]
    if isinstance(obj, str):
        out = obj
        for old, new in mapping:
            if old:
                out = out.replace(old, new)
        return out
    return obj


def _rewrite_json_scrubbed(path: Path, mapping: list[tuple[str, str]] | None = None) -> None:
    if not path.is_file():
        return
    data = _scrub_timestamps(read_json(path))
    if mapping is not None:
        data = _rewrite_disposable_paths(data, mapping)
    write_json(path, data)


def _stable_freeze_directory(audit_root: Path, package: Path) -> str:
    return f"{STABLE_ROOT}/runs/{audit_root.name}/freeze/{package.name}"


def _stable_sha256sums_path(audit_root: Path, package: Path) -> str:
    return _stable_freeze_directory(audit_root, package) + "/SHA256SUMS.txt"


def _iter_freeze_packages(audit_root: Path) -> list[Path]:
    freeze_root = audit_root / "freeze"
    if not freeze_root.is_dir():
        return []
    return sorted(
        p
        for p in freeze_root.iterdir()
        if p.is_dir() and p.name.endswith("_FROZEN") and not p.name.startswith(".")
    )


def _step4_sha256sums_digest(audit_root: Path) -> str:
    """Digest of root sums as bound before freeze package publication."""
    skip_names = {"SHA256SUMS.txt", "SHA256SUMS_EXECUTION.txt"}
    lines: list[str] = []
    for path in sorted(audit_root.rglob("*")):
        if not path.is_file():
            continue
        if path.name in skip_names:
            continue
        if path.suffix == ".pyc" or "__pycache__" in path.parts:
            continue
        if "freeze" in path.parts:
            continue
        if path.name == "FREEZE_STATUS.json":
            continue
        rel = path.relative_to(audit_root).as_posix()
        lines.append(f"{sha256_file(path)}  {rel}")
    blob = ("\n".join(lines) + "\n").encode("utf-8")
    return _sha256_bytes(blob)


def _refresh_freeze_evidence_index(audit_root: Path, package: Path) -> None:
    index_path = package / "FINAL_EVIDENCE_INDEX.json"
    if not index_path.is_file():
        return
    index = read_json(index_path)
    step4_sums = _step4_sha256sums_digest(audit_root)
    entries = index.get("entries") or []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        rel = entry.get("path")
        if not isinstance(rel, str):
            continue
        if rel == "SHA256SUMS.txt":
            entry["sha256"] = step4_sums
            continue
        candidate = audit_root / rel
        if candidate.is_file():
            entry["sha256"] = sha256_file(candidate)
    write_json(index_path, _scrub_timestamps(index))


def rebind_root_sha256sums(audit_root: Path) -> None:
    """Trusted integrity sync for disposable copies (not a catalog mutation)."""
    EvidenceCollector(BoundaryManager(audit_root, []), audit_root).bind_sha256sums()


def rebind_freeze_package_hashes(audit_root: Path) -> None:
    """Rebind freeze package SHA256SUMS + FREEZE_STATUS digests after mutation.

    Preserves root-independent freeze_directory / sha256sums strings so later
    rebinds never restore disposable absolute paths.
    """
    packages = _iter_freeze_packages(audit_root)
    if not packages:
        return
    package = packages[0]
    lines: list[str] = []
    for path in sorted(package.iterdir()):
        if path.is_file() and path.name != "SHA256SUMS.txt":
            lines.append(f"{sha256_file(path)}  {path.name}")
    (package / "SHA256SUMS.txt").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    status_path = audit_root / "FREEZE_STATUS.json"
    if status_path.is_file():
        status = _scrub_timestamps(read_json(status_path))
        status["sha256sums_digest"] = sha256_file(package / "SHA256SUMS.txt")
        status["frozen_manifest_digest"] = sha256_file(package / "MANIFEST.json")
        status["freeze_directory"] = _stable_freeze_directory(audit_root, package)
        status["sha256sums"] = _stable_sha256sums_path(audit_root, package)
        write_json(status_path, status)
    rebind_root_sha256sums(audit_root)


def _refresh_recon_and_manifest(audit_root: Path) -> None:
    if not (audit_root / REPORT_FILENAME).is_file():
        return
    report = emit_reconstructability_report(audit_root)
    em_path = audit_root / "EXECUTION_MANIFEST.json"
    if not em_path.is_file():
        return
    em = _scrub_timestamps(read_json(em_path))
    r4b = em.get("r4_b")
    if isinstance(r4b, dict):
        exp = build_r4b_expectation(
            reconstructability_report_digest=report.report_digest,
            expected_disagreement_record_digests=list(
                r4b.get("expected_disagreement_record_digests") or []
            ),
            expected_disagreement_chain_heads=list(
                r4b.get("expected_disagreement_chain_heads") or []
            ),
            finalized_for_freeze=bool(r4b.get("finalized_for_freeze", True)),
        )
        em["r4_b"] = exp.to_dict() if hasattr(exp, "to_dict") else dict(exp)
    write_json(em_path, em)


def _rewrite_non_json_disposable_paths(audit_root: Path) -> None:
    mapping = _path_rewrite_mapping(audit_root)
    for path in sorted(audit_root.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() not in {".log", ".md", ".txt"}:
            continue
        if path.name in {"SHA256SUMS.txt", "SHA256SUMS_EXECUTION.txt"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        new = text
        for old, repl in mapping:
            new = new.replace(old, repl)
        if new != text:
            path.write_text(new, encoding="utf-8", newline="\n")


def _sync_frozen_expectation(audit_root: Path) -> None:
    """Point freeze artifacts at the post-normalization expectation digest."""
    em_path = audit_root / "EXECUTION_MANIFEST.json"
    if not em_path.is_file():
        return
    em = read_json(em_path)
    r4b = em.get("r4_b")
    if not isinstance(r4b, dict):
        return
    exp = expectation_digest(r4b)
    em_digest = sha256_file(em_path)
    for rel in ("FREEZE_INTENT.json", "FREEZE_STATUS.json"):
        path = audit_root / rel
        if not path.is_file():
            continue
        doc = _scrub_timestamps(read_json(path))
        if "r4_b_expectation_digest" in doc:
            doc["r4_b_expectation_digest"] = exp
        if "execution_manifest_digest" in doc:
            doc["execution_manifest_digest"] = em_digest
        write_json(path, doc)
    for package in _iter_freeze_packages(audit_root):
        _refresh_freeze_evidence_index(audit_root, package)
        man_path = package / "MANIFEST.json"
        if not man_path.is_file():
            continue
        man = _scrub_timestamps(read_json(man_path))
        man = _rewrite_disposable_paths(man, _path_rewrite_mapping(audit_root))
        man["freeze_directory"] = _stable_freeze_directory(audit_root, package)
        if "r4_b_expectation_digest" in man:
            man["r4_b_expectation_digest"] = exp
        if "execution_manifest_digest" in man:
            man["execution_manifest_digest"] = em_digest
        if (package / "FINAL_DECISION.json").is_file() and "final_decision_sha256" in man:
            man["final_decision_sha256"] = sha256_file(package / "FINAL_DECISION.json")
        if (package / "FINAL_EVIDENCE_INDEX.json").is_file() and (
            "final_evidence_index_sha256" in man
        ):
            man["final_evidence_index_sha256"] = sha256_file(
                package / "FINAL_EVIDENCE_INDEX.json"
            )
        refs = man.get("referenced_audit_files")
        if isinstance(refs, list):
            for ref in refs:
                if not isinstance(ref, dict) or "sha256" not in ref:
                    continue
                rel = ref.get("relative_path") or ref.get("path")
                if not isinstance(rel, str):
                    continue
                # Root sums are rewritten after FREEZE_STATUS. Bind the
                # pre-status snapshot so the manifest digest is not circular.
                if rel == "SHA256SUMS.txt":
                    ref["sha256"] = _step4_sha256sums_digest(audit_root)
                    continue
                candidate = audit_root / rel
                if candidate.is_file():
                    ref["sha256"] = sha256_file(candidate)
        write_json(man_path, man)


def _normalize_audit_tree(audit_root: Path) -> None:
    """Timestamp normalization. Frozen trees also drop disposable absolute paths."""
    frozen = (audit_root / "FREEZE_STATUS.json").is_file()
    if frozen:
        mapping = _path_rewrite_mapping(audit_root)
        for path in sorted(audit_root.rglob("*.json")):
            if path.is_file():
                _rewrite_json_scrubbed(path, mapping)
        _rewrite_non_json_disposable_paths(audit_root)
        _refresh_recon_and_manifest(audit_root)
        _sync_frozen_expectation(audit_root)
        rebind_freeze_package_hashes(audit_root)
        return
    for path in sorted(audit_root.rglob("*.json")):
        if path.is_file():
            _rewrite_json_scrubbed(path)
    if (audit_root / "SHA256SUMS.txt").is_file():
        rebind_root_sha256sums(audit_root)


def _make_request(
    target: Path,
    digest: str,
    *,
    human_review_required: bool,
    force_fail: bool = False,
    audit_claim_id: str = "WVMA-B1-CLAIM",
) -> AuditRequest:
    params: dict[str, Any] = {
        "primary_file": "README.txt",
        "expected_sha256": digest,
        "mode": "force_fail" if force_fail else "verify_digest",
    }
    return AuditRequest(
        target_path=str(target.parent if target.is_file() else target),
        claim={
            "id": audit_claim_id,
            "statement": "WVMA B1 deterministic hash claim",
            "adapter": "hash_claim",
            "adapter_params": params,
        },
        policy={
            "human_review_required": human_review_required,
            "required_vectors": [
                "POSITIVE_DIGEST_MATCH",
                "NC1_WRONG_DIGEST_REJECTED",
                "T1_TAMPER_CHANGES_DIGEST",
                "R1_REHASH_REPRODUCTION",
                "BV1_PROTECTED_BOUNDARY_WRITE_DENIED",
            ],
        },
    )


def build_audit_r4b_zero_review(
    workspace: Path,
    *,
    audit_id: str = "WFA-WVMA-B1-ZERO",
    force_fail: bool = False,
    freeze: bool = True,
) -> Path:
    """Frozen (or decision-stage) R4-B audit.

    When ``freeze`` is False, human review is required so the orchestrator does
    not auto-freeze; no HUMAN_REVIEW.json is written (decision-stage only).
    """
    target, digest = _copy_fresh_target(workspace)
    runs = workspace / "runs"
    orch = AuditOrchestrator(runs)
    audit_root = runs / audit_id
    if audit_root.exists():
        raise BaselineError(f"audit root already exists: {audit_root}")
    audit_root.mkdir(parents=True, exist_ok=False)
    # freeze=False => require HR so orchestrator will not auto-freeze.
    req = _make_request(
        target,
        digest,
        human_review_required=(not freeze),
        force_fail=force_fail,
    )
    write_json(
        audit_root / "AUDIT_REQUEST.json",
        {
            "audit_id": audit_id,
            "received_at_utc": FIXED_UTC,
            "target_path": req.target_path,
            "claim": req.claim,
            "policy": req.policy,
            "protected_paths": [],
            "prior_freeze_sums": [],
        },
    )
    result = orch.run_through_decision(req, audit_root=audit_root)
    run = Path(result["audit_root"])
    if freeze and not result.get("frozen"):
        orch.freeze_run(run, req.policy)
    _normalize_audit_tree(run)
    return run


def build_audit_r4b_review_chain(
    workspace: Path,
    *,
    audit_id: str = "WFA-WVMA-B1-CHAIN",
) -> Path:
    """R4-B root with reconstructability + disagreement chain (pre-freeze)."""
    root = workspace / "runs" / audit_id
    root.mkdir(parents=True, exist_ok=False)
    write_json(
        root / "AUDIT_REQUEST.json",
        {
            "audit_id": audit_id,
            "received_at_utc": FIXED_UTC,
            "target_path": "/t",
            "claim": {"id": "C-1", "statement": "s"},
            "policy": {},
        },
    )
    write_json(
        root / "CLAIM.json",
        {"claim_id": "C-1", "statement": "s", "adapter": "hash_claim"},
    )
    write_json(root / "SCOPE.json", {"audit_id": audit_id, "policy": {}})
    write_json(
        root / "PROVENANCE.json",
        {
            "files": [{"relative_path": "f", "sha256": "aa"}],
            "classification": "PINNED_INPUT",
        },
    )
    write_json(
        root / "DECISION.json",
        {"decision": "PASS", "claim_result": "PASS", "promoted_to_full": False},
    )
    report = emit_reconstructability_report(root)
    first = create_disagreement_record(
        disagreement_id="D-1",
        subject_id=audit_id,
        reviewer_positions=_positions(),
        scope="unit",
        category="SPEC_AMBIGUITY",
    )
    write_disagreement_record(root, first)
    second = create_successor_record(
        first,
        disagreement_id="D-2",
        status="OPEN",
        reason="successor",
        reviewer_positions=_positions("FAIL", "PASS"),
    )
    write_disagreement_record(root, second)
    r4_b = build_r4b_expectation(
        reconstructability_report_digest=report.report_digest,
        expected_disagreement_record_digests=[
            first.record_digest,
            second.record_digest,
        ],
        # Chain heads are roots (no predecessor), not tips.
        expected_disagreement_chain_heads=[first.record_digest],
        finalized_for_freeze=True,
    )
    write_json(
        root / "EXECUTION_MANIFEST.json",
        {
            "audit_id": audit_id,
            "lifecycle": LEGACY_LIFECYCLE,
            "stages_completed_through": "DECISION",
            "started_request": True,
            "claim_id": "C-1",
            "adapter": "hash_claim",
            "decision": "PASS",
            "claim_result": "PASS",
            "promoted_to_full": False,
            "baseline_prior_freeze_ok": True,
            "provenance_files": 1,
            "timestamp_utc": FIXED_UTC,
            "r4_b": r4_b,
        },
    )
    return root


def build_audit_human_review_prefreeze(
    workspace: Path,
    *,
    audit_id: str = "WFA-WVMA-B1-HR",
    with_accepted_review: bool = True,
) -> tuple[Path, AuditRequest]:
    """Decision-stage audit requiring human review before freeze."""
    target, digest = _copy_fresh_target(workspace)
    runs = workspace / "runs"
    orch = AuditOrchestrator(runs)
    audit_root = runs / audit_id
    audit_root.mkdir(parents=True, exist_ok=False)
    req = _make_request(target, digest, human_review_required=True)
    write_json(
        audit_root / "AUDIT_REQUEST.json",
        {
            "audit_id": audit_id,
            "received_at_utc": FIXED_UTC,
            "target_path": req.target_path,
            "claim": req.claim,
            "policy": req.policy,
            "protected_paths": [],
            "prior_freeze_sums": [],
        },
    )
    orch.run_through_decision(req, audit_root=audit_root)
    if with_accepted_review:
        write_json(
            audit_root / "HUMAN_REVIEW.json",
            {
                "status": "ACCEPTED",
                "reviewer": "wvma-b1",
                "notes": "accepted for baseline",
                "audit_id": audit_id,
                "decision_digest": "00" * 32,
            },
        )
    _normalize_audit_tree(audit_root)
    return audit_root, req


def build_audit_human_review_frozen(
    workspace: Path,
    *,
    audit_id: str = "WFA-WVMA-B1-HRF",
) -> Path:
    """Frozen audit with accepted HUMAN_REVIEW.json present."""
    run, req = build_audit_human_review_prefreeze(
        workspace, audit_id=audit_id, with_accepted_review=True
    )
    orch = AuditOrchestrator(run.parent)
    orch.freeze_run(run, req.policy)
    _normalize_audit_tree(run)
    return run


def _pin_campaign_state(campaign_dir: Path) -> None:
    """Pin runtime-dependent campaign fields to code-owned constants."""
    from campaign_runner_v0.state_revalidation import compute_state_integrity_digest

    state_path = campaign_dir / "CAMPAIGN_STATE.json"
    if not state_path.is_file():
        raise BaselineError("CAMPAIGN_STATE.json missing after campaign baseline")
    state = _scrub_timestamps(read_json(state_path))
    state["workspace"] = "aurora_audit"
    state["invocation_id"] = FIXED_CAMPAIGN_INVOCATION_ID
    state["updated_at_utc"] = FIXED_UTC
    register = state.get("evidence_register")
    if isinstance(register, dict):
        register["updated_at_utc"] = FIXED_UTC
    claims = state.get("claims") or {}
    if isinstance(claims, dict):
        for row in claims.values():
            if isinstance(row, dict):
                row["updated_at_utc"] = FIXED_UTC
                if "validated_at_utc" in row:
                    row["validated_at_utc"] = FIXED_UTC
    digest = compute_state_integrity_digest(
        claims if isinstance(claims, dict) else {},
        register if isinstance(register, dict) else {},
    )
    prior = state.get("state_integrity") if isinstance(state.get("state_integrity"), dict) else {}
    state["state_integrity"] = {
        "digest": digest,
        "algorithm": "sha256",
        "covers": list(prior.get("covers") or ["claims", "evidence_register.entries"]),
        "note": prior.get("note") or "wvma-deterministic-campaign",
    }
    write_json(state_path, state)
    register_path = campaign_dir / "EVIDENCE_REGISTER.json"
    if register_path.is_file():
        reg = _scrub_timestamps(read_json(register_path))
        if isinstance(reg, dict):
            reg["updated_at_utc"] = FIXED_UTC
            write_json(register_path, reg)


def build_campaign_test_only(
    workspace: Path,
    *,
    campaign_id: str = "wvma_b1_campaign",
) -> Path:
    """Minimal campaign workspace for C10 state/evidence mutations."""
    from campaign_runner_v0.runner import run_campaign

    aurora = (
        Path(__file__).resolve().parent.parent / "aurora_audit"
    )
    if not aurora.is_dir():
        raise BaselineError("aurora_audit workspace missing")
    # Copy only what campaign runner needs into disposable workspace.
    dest = workspace / "aurora_audit"
    if dest.exists():
        raise BaselineError(f"campaign dest exists: {dest}")
    shutil.copytree(
        aurora,
        dest,
        ignore=shutil.ignore_patterns(
            "__pycache__", "*.pyc", ".git", "campaigns"
        ),
    )
    (dest / "campaigns").mkdir(parents=True, exist_ok=True)
    policy = (
        Path(__file__).resolve().parent.parent
        / "campaign_runner_v0"
        / "policies"
        / "aurora_default.json"
    )
    run_campaign(workspace=dest, campaign_id=campaign_id, policy_path=policy)
    cdir = dest / "campaigns" / campaign_id
    if not cdir.is_dir():
        raise BaselineError("campaign directory missing after baseline run")
    _pin_campaign_state(cdir)
    # The baseline verifier invokes run_campaign again. Pin that revalidation
    # so the sealed preimage is the post-verifier state, without per-run ids.
    run_campaign(workspace=dest, campaign_id=campaign_id, policy_path=policy)
    _pin_campaign_state(cdir)
    return cdir


def build_profile(profile_id: str, workspace: Path, **kwargs: Any) -> Path:
    if profile_id not in ALLOWED_BASELINE_PROFILES:
        raise BaselineError(f"unsupported baseline profile: {profile_id}")
    if profile_id == PROFILE_AUDIT_R4B_ZERO_REVIEW:
        return build_audit_r4b_zero_review(workspace, **kwargs)
    if profile_id == PROFILE_AUDIT_R4B_REVIEW_CHAIN:
        return build_audit_r4b_review_chain(workspace, **kwargs)
    if profile_id == PROFILE_AUDIT_HUMAN_REVIEW_PREFREEZE:
        root, _req = build_audit_human_review_prefreeze(workspace, **kwargs)
        return root
    if profile_id == PROFILE_CAMPAIGN_TEST_ONLY:
        return build_campaign_test_only(workspace, **kwargs)
    raise BaselineError(f"unhandled profile: {profile_id}")


def attempt_freeze(audit_root: Path, policy: dict[str, Any] | None = None) -> dict[str, Any]:
    """Exercise freeze_run; returns structured outcome without raising."""
    orch = AuditOrchestrator(audit_root.parent)
    pol = policy
    if pol is None:
        req_path = audit_root / "AUDIT_REQUEST.json"
        pol = read_json(req_path).get("policy") if req_path.is_file() else {}
    try:
        result = orch.freeze_run(audit_root, pol or {})
        if (audit_root / "FREEZE_STATUS.json").is_file():
            _normalize_audit_tree(audit_root)
        return {"ok": True, "result": result, "error": None}
    except HumanReviewRequired as exc:
        return {"ok": False, "result": None, "error": f"HumanReviewRequired:{exc}"}
    except Exception as exc:  # conservative failure observation
        return {"ok": False, "result": None, "error": f"{type(exc).__name__}:{exc}"}


__all__ = [
    "ALLOWED_BASELINE_PROFILES",
    "BaselineError",
    "FIXED_CAMPAIGN_INVOCATION_ID",
    "FIXED_UTC",
    "PROFILE_AUDIT_HUMAN_REVIEW_PREFREEZE",
    "PROFILE_AUDIT_R4B_REVIEW_CHAIN",
    "PROFILE_AUDIT_R4B_ZERO_REVIEW",
    "PROFILE_CAMPAIGN_TEST_ONLY",
    "STABLE_ROOT",
    "attempt_freeze",
    "build_audit_human_review_frozen",
    "build_audit_human_review_prefreeze",
    "build_audit_r4b_review_chain",
    "build_audit_r4b_zero_review",
    "build_campaign_test_only",
    "build_profile",
    "rebind_freeze_package_hashes",
    "rebind_root_sha256sums",
]
