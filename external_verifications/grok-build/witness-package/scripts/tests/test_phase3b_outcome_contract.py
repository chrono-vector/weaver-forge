#!/usr/bin/env python3
"""Phase 3B authoritative outcome ownership contract tests.

Safety contract:
- Python standard library only
- Reads repository files only (JSON contract, implementation note, source text)
- Does not execute host/container scripts
- Does not invoke or import the validator as a module
- No Docker, Cargo, compiler, product, Git clone, or network access
- No subprocess execution of Witness scripts
"""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = TESTS_DIR.parent
PACKAGE_DIR = SCRIPTS_DIR.parent
GROK_BUILD_DIR = PACKAGE_DIR.parent
CONTRACT_PATH = PACKAGE_DIR / "AUTHORITATIVE_OUTCOME_CONTRACT.json"
NOTE_PATH = (
    GROK_BUILD_DIR
    / "evidence"
    / "rc5-remediation"
    / "PHASE_3B_OUTCOME_OWNERSHIP_CONTRACT.md"
)
HOST_SCRIPT = SCRIPTS_DIR / "run_witness_narrow_build.sh"
CONTAINER_SCRIPT = SCRIPTS_DIR / "container_narrow_build.sh"
VALIDATOR_SCRIPT = SCRIPTS_DIR / "validate_witness_evidence.py"

EXPECTED_TERMINAL = frozenset(
    {
        "BUILD_NOT_STARTED",
        "CARGO_FAILED",
        "CARGO_SUCCEEDED_ARTIFACT_MISSING",
        "CARGO_SUCCEEDED_ARTIFACT_PRESENT",
        "INFRASTRUCTURE_FAILURE",
    }
)

REQUIRED_TERMINAL_FIELDS = frozenset(
    {
        "value",
        "meaning",
        "terminal",
        "success_capable",
        "cargo_started",
        "cargo_exit_class",
        "artifact_requirement",
        "permitted_primary_producer",
        "host_may_replace",
        "validator_may_infer",
    }
)

REQUIRED_TUPLE_FIELDS = (
    "schema_version",
    "run_id",
    "container_outcome",
    "container_exit_code",
    "cargo_started",
    "cargo_exit_code",
    "artifact_present",
    "artifact_identity_complete",
    "static_inspection_complete",
    "host_infrastructure_status",
    "host_source_integrity_status",
    "post_build_integrity_status",
    "evidence_completeness_status",
    "validator_status",
    "machine_verdict_ceiling",
)

VIOLATION_VALIDATOR_INFERENCE = "VALIDATOR_DETERMINE_OUTCOME_INFERENCE"
VIOLATION_HOST_OVERWRITE = "HOST_OVERWRITES_CONTAINER_BUILD_EXIT_CODE"
UNRESOLVED = "UNRESOLVED_IMPLEMENTATION_VIOLATION"


def _load_contract() -> dict:
    text = CONTRACT_PATH.read_text(encoding="utf-8")
    return json.loads(text)


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _terminal_by_value(contract: dict) -> dict[str, dict]:
    return {row["value"]: row for row in contract["terminal_outcomes"]}


def _tuple_by_name(contract: dict) -> dict[str, dict]:
    return {row["name"]: row for row in contract["authoritative_result_tuple"]["fields"]}


def _violation_by_id(contract: dict, vid: str) -> dict:
    for row in contract["known_implementation_violations"]:
        if row["id"] == vid:
            return row
    raise AssertionError(f"missing known violation id={vid}")


class Phase3BOutcomeContractTests(unittest.TestCase):
    """25 contract-lock tests for Phase 3B."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = _load_contract()
        cls.note = _read_text(NOTE_PATH)
        cls.host = _read_text(HOST_SCRIPT)
        cls.container = _read_text(CONTAINER_SCRIPT)
        cls.validator = _read_text(VALIDATOR_SCRIPT)

    # 1
    def test_01_contract_json_parses(self) -> None:
        self.assertIsInstance(self.contract, dict)
        self.assertTrue(CONTRACT_PATH.is_file())

    # 2
    def test_02_exactly_five_terminal_outcomes(self) -> None:
        self.assertEqual(len(self.contract["terminal_outcomes"]), 5)

    # 3
    def test_03_exact_terminal_outcome_set(self) -> None:
        values = {row["value"] for row in self.contract["terminal_outcomes"]}
        self.assertEqual(values, EXPECTED_TERMINAL)

    # 4
    def test_04_sentinels_do_not_overlap_terminal_outcomes(self) -> None:
        terminals = {row["value"] for row in self.contract["terminal_outcomes"]}
        sentinels = {row["value"] for row in self.contract["nonterminal_sentinels"]}
        self.assertTrue(terminals.isdisjoint(sentinels))
        for row in self.contract["nonterminal_sentinels"]:
            self.assertFalse(row["may_be_terminal_outcome"])

    # 5
    def test_05_every_terminal_outcome_has_required_fields(self) -> None:
        for row in self.contract["terminal_outcomes"]:
            missing = REQUIRED_TERMINAL_FIELDS - set(row)
            self.assertFalse(missing, f"{row.get('value')}: missing {missing}")
            self.assertIs(row["terminal"], True)

    # 6
    def test_06_only_artifact_present_is_success_capable(self) -> None:
        capable = [
            row["value"]
            for row in self.contract["terminal_outcomes"]
            if row["success_capable"] is True
        ]
        self.assertEqual(capable, ["CARGO_SUCCEEDED_ARTIFACT_PRESENT"])

    # 7
    def test_07_failure_only_outcomes_cannot_permit_pass(self) -> None:
        failure = set(self.contract["failure_rules"]["failure_only_outcomes"])
        self.assertEqual(
            failure,
            EXPECTED_TERMINAL - {"CARGO_SUCCEEDED_ARTIFACT_PRESENT"},
        )
        self.assertTrue(
            self.contract["failure_rules"]["failure_only_outcomes_permanently_ineligible_for_PASS"]
        )
        for row in self.contract["terminal_outcomes"]:
            if row["value"] in failure:
                self.assertIs(row["success_capable"], False)

    # 8
    def test_08_container_owns_container_outcome(self) -> None:
        self.assertEqual(
            self.contract["producer_ownership"]["container_outcome_owner"], "container"
        )
        self.assertIn(
            "container_outcome", self.contract["producer_ownership"]["container_owns"]
        )
        field = _tuple_by_name(self.contract)["container_outcome"]
        self.assertEqual(field["owner"], "container")
        self.assertEqual(field["required_producer"], "container")

    # 9
    def test_09_host_cannot_replace_container_outcome(self) -> None:
        self.assertIs(
            self.contract["producer_ownership"]["host_may_replace_container_outcome"],
            False,
        )
        self.assertIs(
            self.contract["overwrite_rules"]["host_may_replace_valid_container_outcome"],
            False,
        )
        for row in self.contract["terminal_outcomes"]:
            self.assertIs(row["host_may_replace"], False)

    # 10
    def test_10_validator_may_not_infer_container_outcome(self) -> None:
        self.assertIs(
            self.contract["producer_ownership"]["validator_may_infer_container_outcome"],
            False,
        )
        self.assertIs(
            self.contract["inference_rules"]["validator_may_infer_container_outcome"],
            False,
        )
        for row in self.contract["terminal_outcomes"]:
            self.assertIs(row["validator_may_infer"], False)
        field = _tuple_by_name(self.contract)["container_outcome"]
        self.assertIs(field["validator_may_infer"], False)

    # 11
    def test_11_missing_invalid_outcome_is_fail_closed(self) -> None:
        self.assertEqual(
            self.contract["consumer_rules"]["missing_empty_duplicate_malformed_unsupported_outcome"],
            "fail_closed",
        )
        self.assertTrue(self.contract["inference_rules"]["fail_closed"])
        self.assertEqual(
            self.contract["failure_rules"]["missing_invalid_outcome"],
            "fail_closed_with_separate_host_infrastructure_failure_record",
        )

    # 12
    def test_12_complete_result_tuple_contains_every_required_field(self) -> None:
        names = [row["name"] for row in self.contract["authoritative_result_tuple"]["fields"]]
        self.assertEqual(names, list(REQUIRED_TUPLE_FIELDS))

    # 13
    def test_13_every_tuple_field_has_one_declared_owner(self) -> None:
        allowed_owners = {"container", "host", "validator", "shared"}
        for row in self.contract["authoritative_result_tuple"]["fields"]:
            self.assertIn(row["owner"], allowed_owners)
            self.assertIsInstance(row["owner"], str)
            self.assertTrue(row["owner"])

    # 14
    def test_14_success_eligibility_requires_all_declared_gates(self) -> None:
        gates = self.contract["success_eligibility"]["preliminary_success_possible_only_when_all_true"]
        self.assertGreaterEqual(len(gates), 13)
        self.assertTrue(
            self.contract["success_eligibility"][
                "single_false_missing_duplicate_malformed_or_sentinel_in_required_success_field_prevents_success"
            ]
        )
        self.assertTrue(
            self.contract["success_eligibility"]["CARGO_SUCCEEDED_ARTIFACT_PRESENT_alone_insufficient"]
        )
        required_substrings = (
            "CARGO_SUCCEEDED_ARTIFACT_PRESENT",
            "docker_container_exit_code_is_zero",
            "cargo_started_YES",
            "cargo_exit_code_0",
            "artifact_present_YES",
            "artifact_identity_complete",
            "static_inspection_complete",
            "host_infrastructure_status_OK",
            "host_source_integrity_status_OK",
            "post_build_integrity_status_OK",
            "evidence_completeness_status_COMPLETE",
            "validator_status_PASS",
            "machine_verdict_ceiling_permits_PASS",
        )
        joined = "\n".join(gates)
        for needle in required_substrings:
            self.assertIn(needle, joined)

    # 15
    def test_15_infrastructure_failure_permits_cargo_started_yes_or_no(self) -> None:
        row = _terminal_by_value(self.contract)["INFRASTRUCTURE_FAILURE"]
        self.assertEqual(row["cargo_started"], "YES_OR_NO")
        self.assertTrue(row["tuple_consistency"]["must_not_impose_universal_cargo_started_NO"])
        self.assertEqual(row["tuple_consistency"]["cargo_started"], "YES_OR_NO")

    # 16
    def test_16_build_not_started_requires_cargo_started_no(self) -> None:
        row = _terminal_by_value(self.contract)["BUILD_NOT_STARTED"]
        self.assertEqual(row["cargo_started"], "NO")
        self.assertEqual(row["tuple_consistency"]["cargo_started"], "NO")
        self.assertEqual(row["tuple_consistency"]["artifact_present"], "NO")

    # 17
    def test_17_cargo_failed_requires_nonzero_cargo_exit(self) -> None:
        row = _terminal_by_value(self.contract)["CARGO_FAILED"]
        self.assertEqual(row["cargo_started"], "YES")
        self.assertEqual(row["cargo_exit_class"], "NONZERO")
        self.assertEqual(row["tuple_consistency"]["cargo_exit_code"], "nonzero")

    # 18
    def test_18_artifact_missing_requires_cargo_exit_zero_and_artifact_absent(self) -> None:
        row = _terminal_by_value(self.contract)["CARGO_SUCCEEDED_ARTIFACT_MISSING"]
        self.assertEqual(row["cargo_exit_class"], "ZERO")
        self.assertEqual(row["tuple_consistency"]["cargo_exit_code"], "0")
        self.assertEqual(row["tuple_consistency"]["artifact_present"], "NO")

    # 19
    def test_19_artifact_present_requires_cargo_exit_zero_and_artifact_present(self) -> None:
        row = _terminal_by_value(self.contract)["CARGO_SUCCEEDED_ARTIFACT_PRESENT"]
        self.assertEqual(row["cargo_exit_class"], "ZERO")
        self.assertEqual(row["tuple_consistency"]["cargo_exit_code"], "0")
        self.assertEqual(row["tuple_consistency"]["artifact_present"], "YES")
        self.assertIs(row["success_capable"], True)

    # 20
    def test_20_current_host_script_contains_five_terminal_values(self) -> None:
        for value in sorted(EXPECTED_TERMINAL):
            self.assertIn(value, self.host)

    # 21
    def test_21_current_container_script_contains_five_terminal_values(self) -> None:
        for value in sorted(EXPECTED_TERMINAL):
            self.assertIn(value, self.container)

    # 22
    def test_22_current_validator_contains_or_recognizes_five_terminal_values(self) -> None:
        for value in sorted(EXPECTED_TERMINAL):
            self.assertIn(value, self.validator)
        self.assertIn("OUTCOME_VALUES", self.validator)

    # 23 — Phase 3B discovered validator inference; Phase 3F-A removes it from
    # current source. Historical contract/note baseline remains UNRESOLVED /
    # not ACCEPTABLE (AUTHORITATIVE_OUTCOME_CONTRACT.json and Phase 3B note
    # are unchanged historical records). Supersede only the stale expectation
    # that inference must still exist in current validator source.
    def test_23_validator_inference_detected_and_recorded_as_unresolved_violation(self) -> None:
        self.assertIn("def determine_outcome", self.validator)
        # Phase 3F-A: current source must contain no inference fallback.
        self.assertNotRegex(
            self.validator,
            re.compile(
                r"Conservative inference fallback|"
                r"conservatively inferred from cargo_started",
                re.MULTILINE,
            ),
        )
        self.assertNotIn("conservatively inferred", self.validator)
        # Explicit-outcome-only rule must be present.
        self.assertIn("outcome inference", self.validator.lower())
        self.assertIn("explicit", self.validator.lower())
        # Historical Phase 3B contract/note still record the discovered violation.
        violation = _violation_by_id(self.contract, VIOLATION_VALIDATOR_INFERENCE)
        self.assertEqual(violation["status"], UNRESOLVED)
        self.assertIs(violation["acceptable"], False)
        self.assertIn(VIOLATION_VALIDATOR_INFERENCE, self.note)
        self.assertIn(UNRESOLVED, self.note)
        self.assertIn("determine_outcome", self.note)
        # Must not claim the violation is acceptable / remediated / CLOSED in the
        # historical Phase 3B note (implementation advancement is ledger/Phase 3F).
        self.assertNotRegex(
            self.note,
            re.compile(
                rf"{VIOLATION_VALIDATOR_INFERENCE}[^\n]*ACCEPTABLE|"
                rf"{VIOLATION_VALIDATOR_INFERENCE}[^\n]*REMEDIATED|"
                rf"{VIOLATION_VALIDATOR_INFERENCE}[^\n]*CLOSED",
                re.IGNORECASE,
            ),
        )

    # 24 — host overwrite must be absent from post-Docker source-integrity path;
    # contract/note may still list the historical id as unresolved (not CLOSED).
    def test_24_host_overwrite_detected_and_recorded_as_unresolved_violation(self) -> None:
        self.assertIn("enforce_post_docker_source_integrity_boundary", self.host)
        # Phase 3D no-fabrication correction: fixing the overwrite is required.
        # The source-integrity boundary must not create/replace BUILD_EXIT_CODE.txt.
        boundary = re.search(
            r"enforce_post_docker_source_integrity_boundary\(\)\s*\{([\s\S]*?)\n"
            r"(?=[a-zA-Z_][a-zA-Z0-9_]*\(\)|# -----)",
            self.host,
        )
        self.assertIsNotNone(boundary)
        boundary_body = boundary.group(1)
        self.assertNotIn("producer=host_no_container_result", boundary_body)
        self.assertNotIn("outcome=INFRASTRUCTURE_FAILURE", boundary_body)
        self.assertNotRegex(
            boundary_body,
            r'>\s*"\$\{(?:EVIDENCE_DIR)/BUILD_EXIT_CODE\.txt|build_exit_file\}"',
        )
        self.assertIn("finalize_post_docker_host_failure", boundary_body)
        # Historical contract visibility: id remains listed, not ACCEPTABLE/CLOSED.
        # Implementation fix is not treated as a failure.
        violation = _violation_by_id(self.contract, VIOLATION_HOST_OVERWRITE)
        self.assertEqual(violation["status"], UNRESOLVED)
        self.assertIs(violation["acceptable"], False)
        self.assertIn(VIOLATION_HOST_OVERWRITE, self.note)
        self.assertIn(UNRESOLVED, self.note)
        self.assertIn("enforce_post_docker_source_integrity_boundary", self.note)
        self.assertNotRegex(
            self.note,
            re.compile(
                rf"{VIOLATION_HOST_OVERWRITE}[^\n]*ACCEPTABLE|"
                rf"{VIOLATION_HOST_OVERWRITE}[^\n]*REMEDIATED|"
                rf"{VIOLATION_HOST_OVERWRITE}[^\n]*CLOSED",
                re.IGNORECASE,
            ),
        )

    # 25
    def test_25_contract_version_and_status_fields_present(self) -> None:
        self.assertEqual(self.contract["contract_version"], "1.0.0-phase3b")
        self.assertEqual(
            self.contract["contract_status"],
            "CONTRACT_DEFINED_ON_MAIN_IMPLEMENTATION_PENDING",
        )
        self.assertIn("contract_version", self.contract)
        self.assertIn("contract_status", self.contract)


if __name__ == "__main__":
    unittest.main()
