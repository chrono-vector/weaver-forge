"""Fixed WVMA-V1 B2 source mutations.

Replacements are sealed byte constants. They are applied only to Git-export
bytes inside a disposable tree. Zero or multiple matches, a preimage mismatch,
or a postimage mismatch is an apply error. The historical C11-S2 deletion is
recorded here so tests can show it is equivalent; it is not a required kill.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from audit_lifecycle.request import read_json, write_json
from wvma_v1.baselines import (
    build_audit_r4b_zero_review,
    rebind_freeze_package_hashes,
    rebind_root_sha256sums,
)
from wvma_v1.mutations import MutationApplication
from wvma_v1.oracle import CaseEvaluationInput, evaluate_case
from wvma_v1.runner import ProcessReceipt, runner_module_origin
from wvma_v1.target_launcher import module_origin as trusted_launcher_origin
from wvma_v1.workspace import (
    WorkspaceError,
    create_disposable_root,
    export_tracked_tree,
    resolve_under_root,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
PROBE_PATH = Path(__file__).resolve().parent / "source_probe.py"
EQUIVALENT_MUTANT = "EQUIVALENT_MUTANT"
_C06_SHA = "cd" * 32

_C06_S1_FIND = (
    b"        raise R4BExpectationError(\n"
    b'            f"{field_name} must be a list/tuple of digests, not a string"\n'
    b"        )\n"
)
_C06_S1_REPLACE = b"        value = [value]\n"

_C06_S2_FIND = (
    b'            f"{field_name} must be a list/tuple of refs, not a string"\n'
    b"        )\n"
    b"    if not isinstance(value, (list, tuple)):\n"
)
_C06_S2_REPLACE = (
    b'            f"{field_name} must be a list/tuple of refs, not a string"\n'
    b"        )\n"
    b"    if not value:\n"
    b"        return ()\n"
    b"    if not isinstance(value, (list, tuple)):\n"
)

_C11_LINE = b'verify_ok = hash_ok and bool(semantic.get("ok")) and txn_ok'
_C11_S1_REPLACE = b"verify_ok = hash_ok and txn_ok"
_C11_S2_REPLACE = b'verify_ok = hash_ok and bool(semantic.get("ok"))'


class SourceApplyError(ValueError):
    """Closed apply failure. Callers classify this as APPLY_ERROR."""


@dataclass(frozen=True)
class SourceMutation:
    case_id: str
    target_relative_path: str
    preimage_sha256: str
    postimage_sha256: str
    find: bytes
    replace: bytes
    entry_point: str
    probe_case: str
    critical: bool


@dataclass(frozen=True)
class SourceCaseOutcome:
    case_id: str
    result_class: str
    property_violated: bool
    module_inside_export: bool
    module_sha256: str
    probe_inside_export: bool
    wvma_loaded_from_export: bool
    equivalent_label: str | None
    detail: str


SOURCE_MUTATIONS: tuple[SourceMutation, ...] = (
    SourceMutation(
        case_id="C06-S1",
        target_relative_path="audit_lifecycle/epistemic/expectation.py",
        preimage_sha256="46c636180ad95b43e9070731702072ad5e06cb95d17702195749a45084cba96f",
        postimage_sha256="a3a9b0ddf886186b13b3f20273c9ba0e9d87a8a1f14086792026d868465afe74",
        find=_C06_S1_FIND,
        replace=_C06_S1_REPLACE,
        entry_point="strict_parse_r4b_expectation",
        probe_case="C06-S1",
        critical=True,
    ),
    SourceMutation(
        case_id="C06-S2",
        target_relative_path="audit_lifecycle/epistemic/provenance.py",
        preimage_sha256="541b9fba66e26dd697cafdf4edfc9ca23d620ab7f6f16f4545d769dc2dda1d83",
        postimage_sha256="40a18d8fc90b3d6ae867cbf3c14751a3f59eb4ac16d9b645e8215bde1d5d8453",
        find=_C06_S2_FIND,
        replace=_C06_S2_REPLACE,
        entry_point="ProvenanceRecord.from_dict",
        probe_case="C06-S2",
        critical=True,
    ),
    SourceMutation(
        case_id="C11-S1",
        target_relative_path="audit_lifecycle/orchestrator.py",
        preimage_sha256="ec771bab7090c14d94832298fc5588681c0696588d6a7bc1b0bf090c2524e17c",
        postimage_sha256="55dc89bba2ccb264acde95f25952d7dd46e82b5932699afc300aa9fac3f313ca",
        find=_C11_LINE,
        replace=_C11_S1_REPLACE,
        entry_point="AuditOrchestrator.verify_run",
        probe_case="VERIFY_RUN",
        critical=True,
    ),
)

HISTORICAL_C11_S2 = SourceMutation(
    case_id="C11-S2",
    target_relative_path="audit_lifecycle/orchestrator.py",
    preimage_sha256="ec771bab7090c14d94832298fc5588681c0696588d6a7bc1b0bf090c2524e17c",
    postimage_sha256="d11a96041b52ce391ffc134f0e723e5043e44c0d86380d45f344f27deb63c5ba",
    find=_C11_LINE,
    replace=_C11_S2_REPLACE,
    entry_point="AuditOrchestrator.verify_run",
    probe_case="VERIFY_RUN",
    critical=False,
)

REQUIRED_SOURCE_CASE_IDS: tuple[str, ...] = tuple(
    spec.case_id for spec in SOURCE_MUTATIONS if spec.critical
)


def source_mutation(case_id: str) -> SourceMutation:
    if case_id == HISTORICAL_C11_S2.case_id:
        return HISTORICAL_C11_S2
    for spec in SOURCE_MUTATIONS:
        if spec.case_id == case_id:
            return spec
    raise KeyError(case_id)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_blob_bytes(repo: Path, relative_path: str, revision: str = "HEAD") -> bytes:
    """Return Git blob bytes. This is not a worktree read."""
    return subprocess.check_output(
        [
            "git",
            "-C",
            str(repo),
            "-c",
            "core.autocrlf=false",
            "show",
            f"{revision}:{relative_path}",
        ]
    )


def exact_replace(data: bytes, find: bytes, replace: bytes) -> bytes:
    """Replace ``find`` only when it occurs exactly once. No fuzzy match."""
    if find == b"":
        raise SourceApplyError("APPLY_ERROR empty find")
    count = data.count(find)
    if count != 1:
        raise SourceApplyError(f"APPLY_ERROR match count {count}")
    return data.replace(find, replace, 1)


def apply_source_mutation(export_root: Path, spec: SourceMutation) -> MutationApplication:
    """Apply one sealed replacement to a Git export. Does not touch the active tree."""
    try:
        target = resolve_under_root(export_root, spec.target_relative_path)
    except WorkspaceError as exc:
        raise SourceApplyError(f"APPLY_ERROR {exc}") from exc
    data = target.read_bytes()
    blob = git_blob_bytes(REPO_ROOT, spec.target_relative_path)
    if data != blob:
        raise SourceApplyError("APPLY_ERROR export bytes are not git-export bytes")
    preimage = sha256_bytes(data)
    if preimage != spec.preimage_sha256:
        raise SourceApplyError(
            f"APPLY_ERROR preimage mismatch actual={preimage} sealed={spec.preimage_sha256}"
        )
    try:
        updated = exact_replace(data, spec.find, spec.replace)
    except SourceApplyError:
        raise
    postimage = sha256_bytes(updated)
    if postimage != spec.postimage_sha256:
        raise SourceApplyError(
            f"APPLY_ERROR postimage mismatch actual={postimage} sealed={spec.postimage_sha256}"
        )
    target.write_bytes(updated)
    if target.read_bytes() != updated:
        raise SourceApplyError("APPLY_ERROR write did not stick")
    return MutationApplication(
        case_id=spec.case_id,
        operation_enum="REPLACE_EXACT_BYTES",
        target_relative_path=spec.target_relative_path,
        preimage_sha256=preimage,
        postimage_sha256=postimage,
        applied=True,
    )


# B2 probes import only this package. The accepted full-tree exporter rejects
# unrelated tracked names, so the disposable export is this Git pathspec.
_PRODUCT_EXPORT_PATHSPECS = ("audit_lifecycle",)


def export_head(destination: Path, *, repo: Path = REPO_ROOT) -> None:
    export_tracked_tree(
        repo_root=repo,
        revision="HEAD",
        destination=destination,
        pathspecs=_PRODUCT_EXPORT_PATHSPECS,
    )


def _probe_env(export_root: Path) -> dict[str, str]:
    env = {
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONNOUSERSITE": "1",
        "PYTHONHASHSEED": "0",
        "PYTHONPATH": str(export_root.resolve()),
        "LANG": "C",
        "LC_ALL": "C",
    }
    for key in ("SYSTEMROOT", "WINDIR", "SystemRoot", "COMSPEC", "PATH", "PATHEXT"):
        if key in os.environ:
            env[key] = os.environ[key]
    return env


def run_probe(
    export_root: Path,
    probe_case: str,
    *,
    audit_root: Path | None = None,
) -> dict[str, Any]:
    """Run the trusted active probe. Product imports resolve only inside ``export_root``."""
    if not PROBE_PATH.is_file():
        raise RuntimeError(f"trusted probe missing: {PROBE_PATH}")
    export_resolved = export_root.resolve()
    if PROBE_PATH.resolve().is_relative_to(export_resolved):
        raise RuntimeError("probe origin is inside the disposable export")
    argv = [
        sys.executable,
        "-B",
        str(PROBE_PATH),
        "--export",
        str(export_resolved),
        "--case",
        probe_case,
    ]
    if audit_root is not None:
        argv.extend(["--audit-root", str(audit_root)])
    proc = subprocess.run(
        argv,
        cwd=str(export_resolved),
        env=_probe_env(export_resolved),
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )
    line = ""
    for candidate in reversed(proc.stdout.splitlines()):
        if candidate.strip().startswith("{"):
            line = candidate.strip()
            break
    if not line:
        raise RuntimeError(
            f"probe produced no JSON exit={proc.returncode} stderr={proc.stderr[:500]}"
        )
    payload = json.loads(line)
    payload["probe_exit_code"] = proc.returncode
    return payload


def _component_flags(observation: dict[str, Any]) -> tuple[bool, bool, bool, bool, bool]:
    hash_ok = bool(observation.get("sha256sums_ok")) and (
        observation.get("freeze_sums_ok") is not False
    )
    txn_ok = observation.get("txn_verify_ok") is True
    semantic_ok = observation.get("semantic_ok") is True
    original = hash_ok and semantic_ok and txn_ok
    historical = hash_ok and semantic_ok
    return hash_ok, txn_ok, semantic_ok, original, historical


def _c06_s1_violated(payload: dict[str, Any]) -> bool:
    obs = payload.get("observation") or {}
    return (
        obs.get("entry_point") == "strict_parse_r4b_expectation"
        and obs.get("accepted") is True
        and obs.get("digests") == [_C06_SHA]
    )


def _c06_s1_baseline_held(payload: dict[str, Any]) -> bool:
    obs = payload.get("observation") or {}
    return obs.get("accepted") is False and obs.get("error_type") == "R4BExpectationError"


def _c06_s2_violated(payload: dict[str, Any]) -> bool:
    obs = payload.get("observation") or {}
    rows = obs.get("present_invalid") or {}
    if obs.get("entry_point") != "ProvenanceRecord.from_dict":
        return False
    return all(
        isinstance(rows.get(name), dict)
        and rows[name].get("accepted") is True
        and rows[name].get("parent_sources") == []
        for name in ("none", "false", "zero")
    )


def _c06_s2_baseline_held(payload: dict[str, Any]) -> bool:
    rows = (payload.get("observation") or {}).get("present_invalid") or {}
    return all(
        isinstance(rows.get(name), dict) and rows[name].get("accepted") is False
        for name in ("none", "false", "zero")
    )


def _c11_s1_violated(payload: dict[str, Any]) -> bool:
    obs = payload.get("observation") or {}
    hash_ok, txn_ok, semantic_ok, _original, historical = _component_flags(obs)
    return (
        obs.get("entry_point") == "AuditOrchestrator.verify_run"
        and hash_ok
        and txn_ok
        and not semantic_ok
        and obs.get("verify_ok") is True
        and historical is False
    )


def _c11_s1_baseline_held(payload: dict[str, Any]) -> bool:
    obs = payload.get("observation") or {}
    hash_ok, txn_ok, semantic_ok, original, _historical = _component_flags(obs)
    return hash_ok and txn_ok and not semantic_ok and original is False and obs.get("verify_ok") is False


def property_violated(spec: SourceMutation, mutant: dict[str, Any]) -> bool:
    if mutant.get("unrelated_failure") is True:
        return False
    if spec.case_id == "C06-S1":
        return _c06_s1_violated(mutant)
    if spec.case_id == "C06-S2":
        return _c06_s2_violated(mutant)
    if spec.case_id == "C11-S1":
        return _c11_s1_violated(mutant)
    return False


def baseline_held(spec: SourceMutation, baseline: dict[str, Any]) -> bool:
    if spec.case_id == "C06-S1":
        return _c06_s1_baseline_held(baseline)
    if spec.case_id == "C06-S2":
        return _c06_s2_baseline_held(baseline)
    if spec.case_id == "C11-S1":
        return _c11_s1_baseline_held(baseline)
    return False


def origin_confirmed(payload: dict[str, Any], export_root: Path, expected_sha: str) -> bool:
    try:
        module = Path(str(payload["module_file"])).resolve()
        probe = Path(str(payload["probe_file"])).resolve()
        export_resolved = export_root.resolve()
    except (KeyError, TypeError, OSError):
        return False
    return (
        module.is_relative_to(export_resolved)
        and not probe.is_relative_to(export_resolved)
        and payload.get("module_sha256") == expected_sha
        and payload.get("wvma_loaded_from_export") is False
    )


def _receipt(export_root: Path, payload: dict[str, Any]) -> ProcessReceipt:
    raw = json.dumps(payload, sort_keys=True).encode("utf-8")
    observation = payload.get("observation") or {}
    verify_ok = observation.get("verify_ok")
    if not isinstance(verify_ok, bool):
        verify_ok = None
    claimed = "DETECTED" if payload.get("unrelated_failure") else None
    return ProcessReceipt(
        invocation_id="audit.verify_run",
        argv=(sys.executable, "-B", str(PROBE_PATH), "--case", str(payload.get("case_id"))),
        cwd=str(export_root),
        exit_code=int(payload.get("probe_exit_code") or 0),
        timed_out=False,
        stdout_sha256=sha256_bytes(raw),
        stderr_sha256=sha256_bytes(b""),
        stdout_truncated=False,
        stderr_truncated=False,
        stdout_byte_length=len(raw),
        stderr_byte_length=0,
        python_executable=sys.executable,
        launcher_module_origin=trusted_launcher_origin(),
        runner_module_origin=runner_module_origin(),
        env_digest=sha256_bytes(b"wvma-b2-probe"),
        started_at="20261002T000000Z",
        completed_at="20261002T000000Z",
        workspace_root=str(export_root.resolve()),
        verify_ok_claimed=verify_ok,
        self_claimed_result=claimed,
        stdout_text_preview="",
    )


def classify_source_observation(
    spec: SourceMutation,
    *,
    export_root: Path,
    application: MutationApplication | None,
    baseline: dict[str, Any] | None,
    mutant: dict[str, Any] | None,
    apply_error: bool = False,
) -> str:
    """Classify from the specific observation. Exit status alone cannot detect."""
    if apply_error or application is None or not application.applied:
        return evaluate_case(
            CaseEvaluationInput(
                case_id=spec.case_id,
                mutation=application,
                expected_preimage_sha256=spec.preimage_sha256,
                expected_postimage_sha256=spec.postimage_sha256,
                baseline_receipt=None,
                mutation_receipt=None,
                property_violated=False,
                verifier_exercised=False,
                expected_rejection_observed=False,
                apply_error=True,
            )
        ).result_class.value

    assert mutant is not None and baseline is not None
    violated = property_violated(spec, mutant)
    held = baseline_held(spec, baseline)
    exercised = origin_confirmed(mutant, export_root, spec.postimage_sha256)
    # The property test held on the unmutated export and fails on this mutant.
    rejection = bool(violated and held and exercised)
    if mutant.get("unrelated_failure") is True or mutant.get("error"):
        violated = False
        rejection = False
        if mutant.get("unrelated_failure") is not True and not mutant.get("observation"):
            return evaluate_case(
                CaseEvaluationInput(
                    case_id=spec.case_id,
                    mutation=application,
                    expected_preimage_sha256=spec.preimage_sha256,
                    expected_postimage_sha256=spec.postimage_sha256,
                    baseline_receipt=None,
                    mutation_receipt=_receipt(export_root, mutant),
                    property_violated=False,
                    verifier_exercised=exercised,
                    expected_rejection_observed=False,
                    execution_error=True,
                )
            ).result_class.value
    return evaluate_case(
        CaseEvaluationInput(
            case_id=spec.case_id,
            mutation=application,
            expected_preimage_sha256=spec.preimage_sha256,
            expected_postimage_sha256=spec.postimage_sha256,
            baseline_receipt=None,
            mutation_receipt=_receipt(export_root, mutant),
            property_violated=violated,
            verifier_exercised=exercised,
            expected_rejection_observed=rejection,
        )
    ).result_class.value


def _new_disposable(parent: Path) -> Path:
    return create_disposable_root(
        parent=parent,
        prefix="b2-",
        active_repository=REPO_ROOT,
    )


def prepare_c11_s1_canary(workspace: Path) -> Path:
    """Integrity and freeze transaction pass; stored decision no longer matches."""
    root = build_audit_r4b_zero_review(
        workspace, audit_id="WVMA-B2-S1", force_fail=False, freeze=True
    )
    dec_path = root / "DECISION.json"
    decision = dict(read_json(dec_path))
    decision["decision"] = "FAIL" if decision.get("decision") == "PASS" else "PASS"
    decision["reason"] = "WVMA_C11_S1_CANARY"
    write_json(dec_path, decision)
    rebind_root_sha256sums(root)
    rebind_freeze_package_hashes(root)
    return root


def prepare_transaction_failure(workspace: Path, *, mode: str) -> Path:
    """Reachable freeze-transaction failures. Does not edit product source."""
    root = build_audit_r4b_zero_review(
        workspace, audit_id=f"WVMA-B2-{mode}", force_fail=False, freeze=True
    )
    if mode == "TEMP":
        (root / "freeze" / ".wf_freeze_tmp_WVMA-B2-TEMP_deadbeef").mkdir()
        return root
    if mode == "DIGEST":
        status_path = root / "FREEZE_STATUS.json"
        status = dict(read_json(status_path))
        status["sha256sums_digest"] = "ab" * 32
        write_json(status_path, status)
        rebind_root_sha256sums(root)
        return root
    raise ValueError(mode)


def run_required_case(case_id: str) -> SourceCaseOutcome:
    spec = source_mutation(case_id)
    if not spec.critical:
        raise ValueError(f"{case_id} is not a required critical source mutant")
    with tempfile.TemporaryDirectory(prefix="wvma-b2-case-") as td:
        parent = Path(td)
        disposable = _new_disposable(parent)
        export = disposable / "export"
        export.mkdir()
        export_head(export)
        audit: Path | None = None
        if spec.case_id == "C11-S1":
            audit = prepare_c11_s1_canary(disposable / "canary")
        baseline = run_probe(export, spec.probe_case, audit_root=audit)
        application = apply_source_mutation(export, spec)
        mutant = run_probe(export, spec.probe_case, audit_root=audit)
        result = classify_source_observation(
            spec,
            export_root=export,
            application=application,
            baseline=baseline,
            mutant=mutant,
        )
        return SourceCaseOutcome(
            case_id=spec.case_id,
            result_class=result,
            property_violated=property_violated(spec, mutant),
            module_inside_export=origin_confirmed(mutant, export, spec.postimage_sha256),
            module_sha256=str(mutant.get("module_sha256")),
            probe_inside_export=Path(str(mutant.get("probe_file"))).resolve().is_relative_to(
                export.resolve()
            ),
            wvma_loaded_from_export=mutant.get("wvma_loaded_from_export") is True,
            equivalent_label=None,
            detail=json.dumps(
                {"baseline": baseline.get("observation"), "mutant": mutant.get("observation")},
                sort_keys=True,
            )[:1200],
        )


def run_unrelated_failure() -> SourceCaseOutcome:
    """A mutated export that reports an unrelated failure must not be DETECTED."""
    spec = source_mutation("C06-S1")
    with tempfile.TemporaryDirectory(prefix="wvma-b2-unrelated-") as td:
        disposable = _new_disposable(Path(td))
        export = disposable / "export"
        export.mkdir()
        export_head(export)
        application = apply_source_mutation(export, spec)
        mutant = run_probe(export, "UNRELATED")
        baseline = {
            "observation": {
                "accepted": False,
                "error_type": "R4BExpectationError",
            }
        }
        result = classify_source_observation(
            spec,
            export_root=export,
            application=application,
            baseline=baseline,
            mutant=mutant,
        )
        return SourceCaseOutcome(
            case_id="UNRELATED",
            result_class=result,
            property_violated=property_violated(spec, mutant),
            module_inside_export=origin_confirmed(mutant, export, spec.postimage_sha256),
            module_sha256=str(mutant.get("module_sha256")),
            probe_inside_export=False,
            wvma_loaded_from_export=mutant.get("wvma_loaded_from_export") is True,
            equivalent_label=None,
            detail=json.dumps(mutant, sort_keys=True)[:800],
        )


def _transaction_failure_is_equivalent(observation: dict[str, Any]) -> bool:
    hash_ok, txn_ok, semantic_ok, original, historical = _component_flags(observation)
    if txn_ok:
        return False
    # Accepted coupling: transaction failure keeps both formulas false.
    return (
        hash_ok is False
        and semantic_ok is False
        and original is False
        and historical is False
        and original == historical
        and observation.get("verify_ok") is False
    )


def record_c11_s2_equivalence() -> SourceCaseOutcome:
    """Apply the historical deletion only to prove it does not change verify_ok."""
    spec = HISTORICAL_C11_S2
    with tempfile.TemporaryDirectory(prefix="wvma-b2-c11s2-") as td:
        parent = Path(td)
        disposable = _new_disposable(parent)
        export = disposable / "export"
        export.mkdir()
        export_head(export)
        modes: dict[str, dict[str, Any]] = {}
        audits: dict[str, Path] = {}
        for mode in ("TEMP", "DIGEST"):
            audit = prepare_transaction_failure(disposable / mode, mode=mode)
            audits[mode] = audit
            observed = run_probe(export, "VERIFY_RUN", audit_root=audit)
            modes[mode] = observed
            if not _transaction_failure_is_equivalent(observed.get("observation") or {}):
                raise AssertionError(
                    f"C11-S2 baseline not an equivalent failure state {mode}: {observed}"
                )
        application = apply_source_mutation(export, spec)
        mutant_ok = False
        mutant_payload: dict[str, Any] | None = None
        for mode, audit in audits.items():
            mutant = run_probe(export, "VERIFY_RUN", audit_root=audit)
            mutant_payload = mutant
            observation = mutant.get("observation") or {}
            _hash_ok, _txn_ok, _semantic_ok, original, historical = _component_flags(
                observation
            )
            if observation.get("verify_ok") is not False or original is not False or historical is not False:
                mutant_ok = True
            if not _transaction_failure_is_equivalent(observation):
                raise AssertionError(
                    f"C11-S2 mutant escaped equivalence {mode}: {mutant}"
                )
            if modes[mode]["observation"]["verify_ok"] != observation["verify_ok"]:
                mutant_ok = True
        assert mutant_payload is not None
        result = classify_source_observation(
            spec,
            export_root=export,
            application=application,
            baseline={"observation": {}},
            mutant=mutant_payload,
        )
        # property_violated is false for C11-S2, so the class is INVALID_MUTANT.
        if mutant_ok:
            raise AssertionError("historical C11-S2 changed verify_ok")
        return SourceCaseOutcome(
            case_id=spec.case_id,
            result_class=result,
            property_violated=False,
            module_inside_export=origin_confirmed(
                mutant_payload, export, spec.postimage_sha256
            ),
            module_sha256=str(mutant_payload.get("module_sha256")),
            probe_inside_export=False,
            wvma_loaded_from_export=mutant_payload.get("wvma_loaded_from_export") is True,
            equivalent_label=EQUIVALENT_MUTANT,
            detail="historical txn_ok deletion stayed verify_ok false",
        )


__all__ = [
    "EQUIVALENT_MUTANT",
    "HISTORICAL_C11_S2",
    "REQUIRED_SOURCE_CASE_IDS",
    "REPO_ROOT",
    "SOURCE_MUTATIONS",
    "SourceApplyError",
    "SourceCaseOutcome",
    "SourceMutation",
    "apply_source_mutation",
    "exact_replace",
    "export_head",
    "git_blob_bytes",
    "record_c11_s2_equivalence",
    "run_required_case",
    "run_unrelated_failure",
    "sha256_bytes",
    "source_mutation",
]
