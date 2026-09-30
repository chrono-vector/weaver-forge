"""Independent oracle evaluation tests for WVMA-V1 Batch A2."""

from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from wvma_v1.canonical import canonical_bytes
from wvma_v1.models import ResultClass
from wvma_v1.mutations import MutationApplication, apply_mutation
from wvma_v1.models import MutationSpec
from wvma_v1.oracle import (
    CaseEvaluationInput,
    assert_trusted_origins,
    derive_result_class,
    evaluate_case,
    oracle_module_origin,
)
from wvma_v1.runner import InvocationContract, run_baseline, run_mutation_case
from wvma_v1.workspace import create_disposable_root


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _spec(pre: str, post: str, value: str = "BAD") -> MutationSpec:
    return MutationSpec(
        case_id="WVMA-S01-M01",
        property_id="WVMA-S01",
        critical=True,
        mutation_kind="SYNTHETIC_ARTIFACT",
        target_relative_path="synthetic/artifact.json",
        expected_preimage_sha256=pre,
        operation_enum="SET_JSON_POINTER",
        operation_arguments={"pointer": "/status", "value": value},
        expected_postimage_sha256=post,
        mutation_timing="PRE_VERIFY",
        verifier_invocation_id="synthetic.verify",
        violation_predicate="status_not_accepted",
        expected_rejection_predicate="verify_rejects",
        oracle_observations=("status_field",),
        materiality="MATERIAL",
    )


class TestDeriveResultClass(unittest.TestCase):
    def test_detected_requires_all_four(self):
        self.assertEqual(
            derive_result_class(
                mutation_valid=True,
                property_violated=True,
                verifier_exercised=True,
                expected_rejection_observed=True,
            ),
            ResultClass.DETECTED,
        )

    def test_survived_when_rejection_missing(self):
        self.assertEqual(
            derive_result_class(
                mutation_valid=True,
                property_violated=True,
                verifier_exercised=True,
                expected_rejection_observed=False,
            ),
            ResultClass.SURVIVED,
        )

    def test_invalid_mutant_when_no_violation(self):
        self.assertEqual(
            derive_result_class(
                mutation_valid=True,
                property_violated=False,
                verifier_exercised=True,
                expected_rejection_observed=False,
            ),
            ResultClass.INVALID_MUTANT,
        )

    def test_apply_and_execution_errors(self):
        self.assertEqual(
            derive_result_class(
                mutation_valid=False,
                property_violated=False,
                verifier_exercised=False,
                expected_rejection_observed=False,
            ),
            ResultClass.APPLY_ERROR,
        )
        self.assertEqual(
            derive_result_class(
                mutation_valid=True,
                property_violated=True,
                verifier_exercised=True,
                expected_rejection_observed=True,
                execution_error=True,
            ),
            ResultClass.EXECUTION_ERROR,
        )


class TestEvaluateCase(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory(prefix="wvma-orc-")
        self.active = Path(__file__).resolve().parents[2]
        self.disp = create_disposable_root(
            parent=Path(self._tmpdir.name),
            prefix="ws-",
            active_repository=self.active,
        )
        syn = self.disp / "synthetic"
        syn.mkdir()
        self.original = canonical_bytes({"n": 1, "status": "accepted"})
        (syn / "artifact.json").write_bytes(self.original)

    def tearDown(self):
        self._tmpdir.cleanup()

    def test_end_to_end_detected(self):
        baseline = run_baseline(
            workspace_root=self.disp,
            contract=InvocationContract(invocation_id="synthetic.verify"),
        )
        self.assertEqual(baseline.exit_code, 0)
        mutated = canonical_bytes({"n": 1, "status": "BAD"})
        app = apply_mutation(
            self.disp,
            _spec(pre=_sha(self.original), post=_sha(mutated)),
        )
        mut_receipt = run_mutation_case(
            workspace_root=self.disp,
            contract=InvocationContract(invocation_id="synthetic.verify"),
        )
        result = evaluate_case(
            CaseEvaluationInput(
                case_id="WVMA-S01-M01",
                mutation=app,
                expected_preimage_sha256=_sha(self.original),
                expected_postimage_sha256=_sha(mutated),
                baseline_receipt=baseline,
                mutation_receipt=mut_receipt,
            )
        )
        self.assertEqual(result.result_class, ResultClass.DETECTED)
        self.assertTrue(result.mutation_valid)
        self.assertTrue(result.property_violated)
        self.assertTrue(result.verifier_exercised)
        self.assertTrue(result.expected_rejection_observed)

    def test_false_self_claim_cannot_create_detected(self):
        # canary_pass exits 0 but self_claimed_result=DETECTED
        receipt = run_baseline(
            workspace_root=self.disp,
            contract=InvocationContract(invocation_id="synthetic.canary_pass"),
        )
        self.assertEqual(receipt.self_claimed_result, "DETECTED")
        fake_mut = MutationApplication(
            case_id="WVMA-S01-M01",
            operation_enum="SET_JSON_POINTER",
            target_relative_path="synthetic/artifact.json",
            preimage_sha256="1" * 64,
            postimage_sha256="2" * 64,
            applied=True,
        )
        result = evaluate_case(
            CaseEvaluationInput(
                case_id="WVMA-S01-M01",
                mutation=fake_mut,
                expected_preimage_sha256="1" * 64,
                expected_postimage_sha256="2" * 64,
                baseline_receipt=None,
                mutation_receipt=receipt,
                property_violated=True,
                verifier_exercised=True,
                expected_rejection_observed=None,
            )
        )
        self.assertNotEqual(result.result_class, ResultClass.DETECTED)
        self.assertEqual(result.result_class, ResultClass.SURVIVED)

    def test_trusted_origins_outside_disposable(self):
        origins = assert_trusted_origins(disposable_workspace=self.disp)
        self.assertEqual(
            Path(origins["oracle"]).resolve(),
            Path(oracle_module_origin()).resolve(),
        )
        for origin in origins.values():
            with self.assertRaises(ValueError):
                Path(origin).resolve().relative_to(self.disp.resolve())

    def test_apply_error_when_mutation_missing(self):
        result = evaluate_case(
            CaseEvaluationInput(
                case_id="WVMA-S01-M01",
                mutation=None,
                expected_preimage_sha256="1" * 64,
                expected_postimage_sha256="2" * 64,
                baseline_receipt=None,
                mutation_receipt=None,
                apply_error=True,
            )
        )
        self.assertEqual(result.result_class, ResultClass.APPLY_ERROR)


if __name__ == "__main__":
    unittest.main()
