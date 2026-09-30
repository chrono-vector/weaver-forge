"""Strict schema and ABSENT vs PRESENT-invalid tests."""

from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from wvma_v1.canonical import digest_excluding_field
from wvma_v1.models import (
    AttemptState,
    AttemptVerdict,
    ResultClass,
    SchemaError,
    build_case_result,
    build_oracle_result,
    build_status,
    critical_acceptance_blocks,
    loads_strict_json,
    strict_parse_case_result,
    strict_parse_catalog,
    strict_parse_finalize_intent,
    strict_parse_status,
)

FIXTURE = (
    Path(__file__).resolve().parent / "fixtures" / "SYNTHETIC_CATALOG.json"
)


def _load_catalog_dict() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


class ModelStrictnessTests(unittest.TestCase):
    def test_fixture_parses(self):
        catalog = strict_parse_catalog(_load_catalog_dict())
        self.assertEqual(catalog.catalog_id, "WVMA-SYNTHETIC-A1")
        self.assertFalse(catalog.authority)

    def test_unknown_fields_reject(self):
        data = _load_catalog_dict()
        data["extra"] = 1
        data["catalog_digest"] = digest_excluding_field(data, "catalog_digest")
        with self.assertRaises(SchemaError):
            strict_parse_catalog(data)

    def test_absent_required_field_rejects(self):
        data = _load_catalog_dict()
        del data["catalog_version"]
        with self.assertRaises(SchemaError):
            strict_parse_catalog(data)

    def test_absent_vs_none(self):
        data = _load_catalog_dict()
        data["catalog_version"] = None
        with self.assertRaises(SchemaError):
            strict_parse_catalog(data)

    def test_absent_vs_false_for_required_string(self):
        data = _load_catalog_dict()
        data["catalog_version"] = False
        with self.assertRaises(SchemaError):
            strict_parse_catalog(data)

    def test_absent_vs_scalar_for_list(self):
        data = _load_catalog_dict()
        data["properties"] = 1
        with self.assertRaises(SchemaError):
            strict_parse_catalog(data)

    def test_mapping_as_list_rejects(self):
        data = _load_catalog_dict()
        data["properties"] = {"0": data["properties"][0]}
        with self.assertRaises(SchemaError):
            strict_parse_catalog(data)

    def test_string_as_list_rejects(self):
        data = _load_catalog_dict()
        data["critical_case_ids"] = "WVMA-S01-M01"
        with self.assertRaises(SchemaError):
            strict_parse_catalog(data)

    def test_authority_must_be_exactly_false(self):
        data = _load_catalog_dict()
        for bad in (True, 0, "false", None):
            mutated = copy.deepcopy(data)
            mutated["authority"] = bad
            with self.assertRaises(SchemaError):
                strict_parse_catalog(mutated)

    def test_duplicate_property_ids(self):
        data = _load_catalog_dict()
        data["properties"].append(copy.deepcopy(data["properties"][0]))
        data["catalog_digest"] = digest_excluding_field(data, "catalog_digest")
        with self.assertRaises(SchemaError):
            strict_parse_catalog(data)

    def test_duplicate_case_ids(self):
        data = _load_catalog_dict()
        data["mutations"].append(copy.deepcopy(data["mutations"][0]))
        data["catalog_digest"] = digest_excluding_field(data, "catalog_digest")
        with self.assertRaises(SchemaError):
            strict_parse_catalog(data)

    def test_catalog_self_digest_mismatch(self):
        data = _load_catalog_dict()
        data["catalog_digest"] = "a" * 64
        with self.assertRaises(SchemaError):
            strict_parse_catalog(data)

    def test_partial_result_rejects(self):
        oracle = build_oracle_result(
            case_id="WVMA-S01-M01",
            mutation_valid=True,
            property_violated=True,
            verifier_exercised=True,
            expected_rejection_observed=True,
            result_class=ResultClass.DETECTED,
        )
        result = build_case_result(
            attempt_id="WVMA-20260101T000000Z-deadbeef",
            catalog_digest="0" * 64,
            case_id="WVMA-S01-M01",
            property_id="WVMA-S01",
            result_class=ResultClass.DETECTED,
            oracle_result=oracle,
            started_at="2026-01-01T00:00:00Z",
            completed_at="2026-01-01T00:00:01Z",
        )
        body = result.to_dict()
        del body["process_observation"]
        with self.assertRaises(SchemaError):
            strict_parse_case_result(body)

    def test_partial_status_rejects(self):
        status = build_status(
            attempt_id="WVMA-20260101T000000Z-deadbeef",
            catalog_digest="0" * 64,
            source_revision="0" * 64,
            runner_digest="1" * 64,
            oracle_digest="2" * 64,
            state=AttemptState.RUN_COMPLETE,
            verdict=AttemptVerdict.ALL_CRITICAL_DETECTED,
            baseline_receipt_digest="3" * 64,
            case_result_digests=[],
            result_counts={},
            blocking_case_ids=[],
            attempt_root_digest="4" * 64,
            completed_at="2026-01-01T00:00:00Z",
        )
        body = status.to_dict()
        del body["attempt_root_digest"]
        with self.assertRaises(SchemaError):
            strict_parse_status(body)

    def test_verdict_forbidden_outside_complete(self):
        with self.assertRaises(SchemaError):
            build_status(
                attempt_id="WVMA-20260101T000000Z-deadbeef",
                catalog_digest="0" * 64,
                source_revision="0" * 64,
                runner_digest="1" * 64,
                oracle_digest="2" * 64,
                state=AttemptState.RUN_INVALID,
                verdict=AttemptVerdict.ALL_CRITICAL_DETECTED,
                baseline_receipt_digest="3" * 64,
                case_result_digests=[],
                result_counts={},
                blocking_case_ids=[],
                attempt_root_digest="4" * 64,
                completed_at="2026-01-01T00:00:00Z",
            )

    def test_critical_non_detected_blocks_acceptance(self):
        for cls in ResultClass:
            if cls == ResultClass.DETECTED:
                self.assertFalse(critical_acceptance_blocks(cls))
            else:
                self.assertTrue(critical_acceptance_blocks(cls))


def _detected_result_dict(
    *,
    applied: bool = True,
    observed: bool = True,
    invoked: bool = True,
    mutation_proof: dict | None = None,
    violation_proof: dict | None = None,
    verifier_exercise_proof: dict | None = None,
    mutation_valid: bool = True,
    property_violated: bool = True,
    verifier_exercised: bool = True,
    expected_rejection_observed: bool = True,
) -> dict:
    oracle = build_oracle_result(
        case_id="WVMA-S01-M01",
        mutation_valid=mutation_valid,
        property_violated=property_violated,
        verifier_exercised=verifier_exercised,
        expected_rejection_observed=expected_rejection_observed,
        result_class=ResultClass.DETECTED,
    )
    body = {
        "schema_version": "wvma_v1.result.v1",
        "authority": False,
        "attempt_id": "WVMA-20260101T000000Z-deadbeef",
        "catalog_digest": "0" * 64,
        "case_id": "WVMA-S01-M01",
        "property_id": "WVMA-S01",
        "result_class": "DETECTED",
        "mutation_proof": (
            dict(mutation_proof)
            if mutation_proof is not None
            else {"applied": applied}
        ),
        "violation_proof": (
            dict(violation_proof)
            if violation_proof is not None
            else {"observed": observed}
        ),
        "verifier_exercise_proof": (
            dict(verifier_exercise_proof)
            if verifier_exercise_proof is not None
            else {"invoked": invoked}
        ),
        "process_observation": {"exit_code": 0},
        "filesystem_observations": [],
        "digest_observations": [],
        "oracle_result": oracle.to_dict(),
        "started_at": "2026-01-01T00:00:00Z",
        "completed_at": "2026-01-01T00:00:01Z",
    }
    body["result_digest"] = digest_excluding_field(body, "result_digest")
    return body


class DetectedProofInvariantTests(unittest.TestCase):
    def test_detected_all_proof_booleans_false_rejects(self):
        body = _detected_result_dict(applied=False, observed=False, invoked=False)
        with self.assertRaises(SchemaError):
            strict_parse_case_result(body)

    def test_detected_each_required_proof_false_rejects(self):
        cases = [
            {"applied": False, "observed": True, "invoked": True},
            {"applied": True, "observed": False, "invoked": True},
            {"applied": True, "observed": True, "invoked": False},
        ]
        for kwargs in cases:
            with self.subTest(**kwargs):
                body = _detected_result_dict(**kwargs)
                with self.assertRaises(SchemaError):
                    strict_parse_case_result(body)

    def test_detected_empty_proof_mappings_reject(self):
        for field in (
            "mutation_proof",
            "violation_proof",
            "verifier_exercise_proof",
        ):
            with self.subTest(field=field):
                kwargs = {
                    "mutation_proof": {"applied": True},
                    "violation_proof": {"observed": True},
                    "verifier_exercise_proof": {"invoked": True},
                }
                kwargs[field] = {}
                body = _detected_result_dict(**kwargs)
                with self.assertRaises(SchemaError):
                    strict_parse_case_result(body)

    def test_detected_malformed_nested_proof_rejects(self):
        body = _detected_result_dict(mutation_proof={"applied": "yes"})
        with self.assertRaises(SchemaError):
            strict_parse_case_result(body)

    def test_detected_unknown_nested_proof_field_rejects(self):
        body = _detected_result_dict(
            mutation_proof={"applied": True, "extra": True}
        )
        with self.assertRaises(SchemaError):
            strict_parse_case_result(body)

    def test_valid_detected_with_all_predicates_true(self):
        body = _detected_result_dict()
        parsed = strict_parse_case_result(body)
        self.assertEqual(parsed.result_class, ResultClass.DETECTED)
        self.assertEqual(parsed.mutation_proof, {"applied": True})
        self.assertEqual(parsed.violation_proof, {"observed": True})
        self.assertEqual(parsed.verifier_exercise_proof, {"invoked": True})


class FinalizeIntentStrictTests(unittest.TestCase):
    def _valid_intent(self) -> dict:
        return {
            "schema_version": "wvma_v1.finalize_intent.v1",
            "authority": False,
            "attempt_id": "WVMA-20260101T000000Z-aaaaaaaa",
            "attempt_root_digest": "a" * 64,
            "intended_status_digest": "b" * 64,
            "result_references": [
                {"case_id": "WVMA-S01-M01", "result_digest": "c" * 64},
                {"case_id": "WVMA-S01-M02", "result_digest": "d" * 64},
            ],
        }

    def test_authority_true_rejects(self):
        data = self._valid_intent()
        data["authority"] = True
        with self.assertRaises(SchemaError):
            strict_parse_finalize_intent(
                data, expected_attempt_id=data["attempt_id"]
            )

    def test_foreign_attempt_id_rejects(self):
        data = self._valid_intent()
        with self.assertRaises(SchemaError):
            strict_parse_finalize_intent(
                data, expected_attempt_id="WVMA-20260101T000000Z-bbbbbbbb"
            )

    def test_unknown_field_rejects(self):
        data = self._valid_intent()
        data["extra"] = 1
        with self.assertRaises(SchemaError):
            strict_parse_finalize_intent(
                data, expected_attempt_id=data["attempt_id"]
            )

    def test_missing_field_rejects(self):
        data = self._valid_intent()
        del data["intended_status_digest"]
        with self.assertRaises(SchemaError):
            strict_parse_finalize_intent(
                data, expected_attempt_id=data["attempt_id"]
            )

    def test_duplicate_json_field_rejects(self):
        text = (
            '{"schema_version":"wvma_v1.finalize_intent.v1",'
            '"authority":false,'
            '"attempt_id":"WVMA-20260101T000000Z-aaaaaaaa",'
            '"attempt_root_digest":"' + ("a" * 64) + '",'
            '"intended_status_digest":"' + ("b" * 64) + '",'
            '"intended_status_digest":"' + ("c" * 64) + '",'
            '"result_references":[]}'
        )
        with self.assertRaises(SchemaError):
            loads_strict_json(text)

    def test_malformed_digest_rejects(self):
        data = self._valid_intent()
        data["attempt_root_digest"] = "ZZ" + ("a" * 62)
        with self.assertRaises(SchemaError):
            strict_parse_finalize_intent(
                data, expected_attempt_id=data["attempt_id"]
            )

    def test_result_references_not_list_rejects(self):
        data = self._valid_intent()
        data["result_references"] = {"case_id": "x"}
        with self.assertRaises(SchemaError):
            strict_parse_finalize_intent(
                data, expected_attempt_id=data["attempt_id"]
            )

    def test_duplicate_case_reference_rejects(self):
        data = self._valid_intent()
        data["result_references"] = [
            {"case_id": "WVMA-S01-M01", "result_digest": "c" * 64},
            {"case_id": "WVMA-S01-M01", "result_digest": "d" * 64},
        ]
        with self.assertRaises(SchemaError):
            strict_parse_finalize_intent(
                data, expected_attempt_id=data["attempt_id"]
            )

    def test_unsorted_result_references_reject(self):
        data = self._valid_intent()
        data["result_references"] = [
            {"case_id": "WVMA-S01-M02", "result_digest": "d" * 64},
            {"case_id": "WVMA-S01-M01", "result_digest": "c" * 64},
        ]
        with self.assertRaises(SchemaError):
            strict_parse_finalize_intent(
                data, expected_attempt_id=data["attempt_id"]
            )

    def test_valid_finalize_intent(self):
        data = self._valid_intent()
        parsed = strict_parse_finalize_intent(
            data, expected_attempt_id=data["attempt_id"]
        )
        self.assertEqual(parsed.attempt_id, data["attempt_id"])
        self.assertFalse(parsed.authority)


if __name__ == "__main__":
    unittest.main()
