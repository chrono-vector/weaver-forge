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
    strict_parse_case_result,
    strict_parse_catalog,
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


if __name__ == "__main__":
    unittest.main()
