"""Independent evaluation of WVMA-V1 A2 execution receipts.

Oracle code is trusted and must not be loaded from a disposable mutated tree.
It never promotes a mutated target's self-claimed PASS/DETECTED into DETECTED.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from wvma_v1.models import (
    OracleResult,
    ResultClass,
    build_oracle_result,
)
from wvma_v1.mutations import MutationApplication
from wvma_v1.runner import ProcessReceipt, runner_module_origin
from wvma_v1.target_launcher import module_origin as launcher_module_origin
from wvma_v1.workspace import WorkspaceError, assert_no_reparse_chain

ORACLE_CONTRACT_VERSION = "wvma_v1.oracle.a2"


class OracleError(ValueError):
    """Oracle evaluation rejection."""


@dataclass(frozen=True)
class CaseEvaluationInput:
    """Structured evidence bundle for one A2 case evaluation."""

    case_id: str
    mutation: MutationApplication | None
    expected_preimage_sha256: str
    expected_postimage_sha256: str
    baseline_receipt: ProcessReceipt | None
    mutation_receipt: ProcessReceipt | None
    # Independent oracle observations (computed outside mutated code).
    property_violated: bool | None = None
    verifier_exercised: bool | None = None
    expected_rejection_observed: bool | None = None
    baseline_ok: bool | None = None
    execution_error: bool = False
    apply_error: bool = False
    oracle_internal_error: str | None = None


def oracle_module_origin() -> str:
    return str(Path(__file__).resolve())


def assert_trusted_origins(
    *,
    disposable_workspace: Path | str | None = None,
) -> dict[str, str]:
    """Prove runner/oracle/launcher origins are outside the disposable workspace."""
    origins = {
        "runner": runner_module_origin(),
        "oracle": oracle_module_origin(),
        "launcher": launcher_module_origin(),
    }
    if disposable_workspace is None:
        return origins
    raw = Path(disposable_workspace)
    try:
        assert_no_reparse_chain(raw, field="disposable_workspace")
    except WorkspaceError as exc:
        raise OracleError(str(exc)) from exc
    root = raw.resolve()
    for name, origin in origins.items():
        try:
            Path(origin).resolve().relative_to(root)
        except ValueError:
            continue
        raise OracleError(f"{name} origin is inside disposable workspace: {origin}")
    return origins


def derive_result_class(
    *,
    mutation_valid: bool,
    property_violated: bool,
    verifier_exercised: bool,
    expected_rejection_observed: bool,
    apply_error: bool = False,
    execution_error: bool = False,
    oracle_error: bool = False,
    missing_result: bool = False,
) -> ResultClass:
    """Classify A2 outcomes from structured evidence (fail-closed)."""
    if oracle_error:
        return ResultClass.ORACLE_ERROR
    if missing_result:
        return ResultClass.MISSING_RESULT
    if execution_error:
        return ResultClass.EXECUTION_ERROR
    if apply_error or not mutation_valid:
        return ResultClass.APPLY_ERROR
    # Valid mutation applied, but no independent property violation → equivalent.
    if not property_violated:
        return ResultClass.INVALID_MUTANT
    if not verifier_exercised:
        return ResultClass.EXECUTION_ERROR
    if expected_rejection_observed:
        return ResultClass.DETECTED
    # Violation present but catalogued verifier did not reject.
    return ResultClass.SURVIVED


def _infer_from_receipts(
    data: CaseEvaluationInput,
) -> tuple[bool, bool, bool, bool, list[str], list[str]]:
    """Derive flags independently; never trust self_claimed_result for DETECTED."""
    observations: list[str] = []
    errors: list[str] = []

    mutation = data.mutation
    mutation_valid = False
    if mutation is None:
        errors.append("mutation_application_absent")
    elif not mutation.applied:
        errors.append("mutation_not_applied")
    elif mutation.preimage_sha256 != data.expected_preimage_sha256:
        errors.append("preimage_mismatch")
    elif mutation.postimage_sha256 != data.expected_postimage_sha256:
        errors.append("postimage_mismatch")
    else:
        mutation_valid = True
        observations.append("mutation_digests_match")

    # Baseline must have succeeded when provided.
    if data.baseline_receipt is not None:
        br = data.baseline_receipt
        baseline_ok = (
            (not br.timed_out)
            and br.exit_code == 0
            and br.verify_ok_claimed is True
        )
        if data.baseline_ok is not None:
            baseline_ok = bool(data.baseline_ok)
        if not baseline_ok:
            errors.append("baseline_not_ok")
            observations.append("baseline_failed")
        else:
            observations.append("baseline_ok")

    property_violated = data.property_violated
    verifier_exercised = data.verifier_exercised
    rejection = data.expected_rejection_observed

    mr = data.mutation_receipt
    if mr is None:
        if verifier_exercised is None:
            verifier_exercised = False
        if rejection is None:
            rejection = False
        if property_violated is None:
            property_violated = False
        errors.append("mutation_receipt_absent")
    else:
        # Exercise means the catalogued invocation actually ran under trusted launcher.
        exercised = (
            (not mr.timed_out)
            and mr.exit_code is not None
            and mr.invocation_id
            and Path(mr.launcher_module_origin).resolve()
            == Path(launcher_module_origin()).resolve()
            and Path(mr.runner_module_origin).resolve()
            == Path(runner_module_origin()).resolve()
        )
        if verifier_exercised is None:
            verifier_exercised = exercised
        if exercised:
            observations.append("verifier_exercised_trusted_launcher")
        else:
            errors.append("verifier_not_exercised_or_untrusted")

        # Independent rejection observation: non-zero exit OR verify_ok_claimed False.
        # Do NOT accept self_claimed_result == "DETECTED" as sufficient.
        observed_rejection = (mr.exit_code not in (None, 0)) or (
            mr.verify_ok_claimed is False
        )
        if rejection is None:
            rejection = bool(observed_rejection and exercised)
        if mr.self_claimed_result == "DETECTED" and not observed_rejection:
            observations.append("ignored_false_self_claimed_detected")
        if observed_rejection:
            observations.append("rejection_signal_present")

        # Property violation: baseline accepted semantics, mutation does not.
        if property_violated is None:
            if data.baseline_receipt is not None:
                property_violated = (
                    data.baseline_receipt.verify_ok_claimed is True
                    and mr.verify_ok_claimed is False
                )
            else:
                property_violated = mr.verify_ok_claimed is False
        if property_violated:
            observations.append("property_violated")
        else:
            observations.append("property_not_violated")

    assert property_violated is not None
    assert verifier_exercised is not None
    assert rejection is not None
    return (
        mutation_valid,
        bool(property_violated),
        bool(verifier_exercised),
        bool(rejection),
        observations,
        errors,
    )


def evaluate_case(data: CaseEvaluationInput) -> OracleResult:
    """Independently evaluate one case and return an A1-compatible OracleResult."""
    if not isinstance(data.case_id, str) or not data.case_id:
        raise OracleError("case_id must be non-empty str")

    if data.oracle_internal_error:
        return build_oracle_result(
            case_id=data.case_id,
            mutation_valid=False,
            property_violated=False,
            verifier_exercised=False,
            expected_rejection_observed=False,
            result_class=ResultClass.ORACLE_ERROR,
            observations=[],
            errors=[data.oracle_internal_error],
        )

    try:
        assert_trusted_origins(
            disposable_workspace=(
                data.mutation_receipt.workspace_root
                if data.mutation_receipt is not None
                else None
            )
        )
        (
            mutation_valid,
            property_violated,
            verifier_exercised,
            rejection,
            observations,
            errors,
        ) = _infer_from_receipts(data)
    except OracleError as exc:
        return build_oracle_result(
            case_id=data.case_id,
            mutation_valid=False,
            property_violated=False,
            verifier_exercised=False,
            expected_rejection_observed=False,
            result_class=ResultClass.ORACLE_ERROR,
            observations=[],
            errors=[str(exc)],
        )

    apply_error = bool(data.apply_error) or (not mutation_valid)
    execution_error = bool(data.execution_error)
    missing = data.mutation_receipt is None and not apply_error

    if data.mutation_receipt is not None and data.mutation_receipt.timed_out:
        execution_error = True
        errors.append("timed_out")

    result_class = derive_result_class(
        mutation_valid=mutation_valid and not apply_error,
        property_violated=property_violated,
        verifier_exercised=verifier_exercised,
        expected_rejection_observed=rejection,
        apply_error=apply_error,
        execution_error=execution_error,
        oracle_error=False,
        missing_result=missing,
    )

    # DETECTED requires all four independent proofs; clear rejection if not valid.
    if result_class == ResultClass.DETECTED:
        if not (
            mutation_valid
            and property_violated
            and verifier_exercised
            and rejection
        ):
            raise OracleError("internal DETECTED invariant broken")

    return build_oracle_result(
        case_id=data.case_id,
        mutation_valid=mutation_valid and not apply_error,
        property_violated=property_violated,
        verifier_exercised=verifier_exercised,
        expected_rejection_observed=rejection,
        result_class=result_class,
        observations=observations,
        errors=errors,
    )


__all__ = [
    "OracleError",
    "CaseEvaluationInput",
    "evaluate_case",
    "derive_result_class",
    "oracle_module_origin",
    "assert_trusted_origins",
    "ORACLE_CONTRACT_VERSION",
]
