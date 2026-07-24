#!/usr/bin/env python3
"""Phase 3F-A validator prerequisite tests (Pi-adjudicated plan).

Safety contract:
- Python standard library only
- Temporary workspaces are children of scripts/tests/ (phase3f_test_*)
- Validator exercised only against isolated fixture directories
- No real Docker, Cargo, rustc, compiler, host Witness workflow, product,
  bootstrap, ldd, package manager, network, or Independent Witness execution
- Phase 3F-B host gating is asserted only as current-source supersession in
  test_22; validator still writes no evidence
- Validator must not write into evidence
- Cleanup of repository-local temps on success and failure
"""

from __future__ import annotations

import os
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = TESTS_DIR.parent
sys.path.insert(0, str(SCRIPTS_DIR))
sys.path.insert(0, str(TESTS_DIR))

import fixtures_lib as fx  # noqa: E402
import validate_witness_evidence as v  # noqa: E402

HOST = v.HOST_OUTCOME_INGESTION_NAME
HOST_SCRIPT = SCRIPTS_DIR / "run_witness_narrow_build.sh"
VALIDATOR = SCRIPTS_DIR / "validate_witness_evidence.py"


def _cleanup_phase3f_temps() -> None:
    for path in TESTS_DIR.glob("phase3f_test_*"):
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)


class Phase3FValidatorPrerequisites(unittest.TestCase):
    def setUp(self) -> None:
        self._temps: list[Path] = []

    def tearDown(self) -> None:
        for path in self._temps:
            if path.exists():
                shutil.rmtree(path, ignore_errors=True)
        self._temps.clear()
        _cleanup_phase3f_temps()

    def _tmpdir(self) -> Path:
        path = Path(tempfile.mkdtemp(prefix="phase3f_test_", dir=str(TESTS_DIR)))
        self._temps.append(path)
        return path

    def _write_success(self) -> Path:
        tmp = self._tmpdir()
        fx.build_and_write(tmp, "success-artifact-present")
        return tmp

    def _host_lines(self, tree: Path) -> list[str]:
        return (tree / HOST).read_text(encoding="utf-8").splitlines()

    def _rewrite_host(self, tree: Path, lines: list[str]) -> None:
        text = "\n".join(lines) + "\n"
        (tree / HOST).write_text(text, encoding="utf-8", newline="\n")
        # Refresh manifest hash for HOST_OUTCOME when listed.
        files = {
            p.name: p.read_text(encoding="utf-8")
            for p in tree.iterdir()
            if p.is_file() and p.name != v.MANIFEST_NAME
        }
        fx.write_tree(tree, files)

    # ------------------------------------------------------------------
    # Explicit outcome / no inference
    # ------------------------------------------------------------------
    def test_01_explicit_outcome_accepted(self) -> None:
        tree = self._write_success()
        errors = v.validate_dir(tree)
        self.assertEqual(errors, [], errors)

    def test_02_missing_outcome_rejected(self) -> None:
        tree = self._write_success()
        bec = tree / "BUILD_EXIT_CODE.txt"
        bec.write_text(
            "\n".join(l for l in bec.read_text(encoding="utf-8").splitlines() if not l.startswith("outcome="))
            + "\n",
            encoding="utf-8",
            newline="\n",
        )
        files = {
            p.name: p.read_text(encoding="utf-8")
            for p in tree.iterdir()
            if p.is_file() and p.name != v.MANIFEST_NAME
        }
        fx.write_tree(tree, files)
        errors = v.validate_dir(tree)
        self.assertTrue(any("explicit 'outcome'" in e for e in errors), errors)

    def test_03_empty_outcome_rejected(self) -> None:
        tree = self._write_success()
        bec = tree / "BUILD_EXIT_CODE.txt"
        text = bec.read_text(encoding="utf-8").replace(
            "outcome=CARGO_SUCCEEDED_ARTIFACT_PRESENT", "outcome="
        )
        bec.write_text(text, encoding="utf-8", newline="\n")
        files = {
            p.name: p.read_text(encoding="utf-8")
            for p in tree.iterdir()
            if p.is_file() and p.name != v.MANIFEST_NAME
        }
        fx.write_tree(tree, files)
        errors = v.validate_dir(tree)
        self.assertTrue(any("empty" in e.lower() and "outcome" in e.lower() for e in errors), errors)

    def test_04_malformed_outcome_rejected(self) -> None:
        tree = self._write_success()
        bec = tree / "BUILD_EXIT_CODE.txt"
        text = bec.read_text(encoding="utf-8").replace(
            "outcome=CARGO_SUCCEEDED_ARTIFACT_PRESENT", "outcome=NOT A VALID TOKEN"
        )
        bec.write_text(text, encoding="utf-8", newline="\n")
        files = {
            p.name: p.read_text(encoding="utf-8")
            for p in tree.iterdir()
            if p.is_file() and p.name != v.MANIFEST_NAME
        }
        fx.write_tree(tree, files)
        errors = v.validate_dir(tree)
        self.assertTrue(any("not an allowed" in e or "unsupported" in e.lower() for e in errors), errors)

    def test_05_unsupported_outcome_rejected(self) -> None:
        tree = self._write_success()
        bec = tree / "BUILD_EXIT_CODE.txt"
        text = bec.read_text(encoding="utf-8").replace(
            "outcome=CARGO_SUCCEEDED_ARTIFACT_PRESENT", "outcome=SUCCESS"
        )
        bec.write_text(text, encoding="utf-8", newline="\n")
        files = {
            p.name: p.read_text(encoding="utf-8")
            for p in tree.iterdir()
            if p.is_file() and p.name != v.MANIFEST_NAME
        }
        fx.write_tree(tree, files)
        errors = v.validate_dir(tree)
        self.assertTrue(any("SUCCESS" in e for e in errors), errors)

    def test_06_prior_inference_combinations_no_longer_produce_outcome(self) -> None:
        """Former cargo_started/build_status inference pairs must not yield outcome."""
        cases = [
            ("NO", "BUILD_NOT_STARTED"),
            ("NO", "INFRASTRUCTURE_FAILURE"),
            ("YES", "FAILED"),
        ]
        for cargo_started, build_status in cases:
            with self.subTest(cargo_started=cargo_started, build_status=build_status):
                tree = self._tmpdir()
                files = fx.build_scenario("success-artifact-present")
                # Strip explicit outcome; leave secondary fields that previously inferred.
                lines = [
                    l
                    for l in files["BUILD_EXIT_CODE.txt"].splitlines()
                    if not l.startswith("outcome=")
                ]
                rebuilt = []
                for l in lines:
                    if l.startswith("cargo_started="):
                        rebuilt.append(f"cargo_started={cargo_started}")
                    elif l.startswith("build_status="):
                        rebuilt.append(f"build_status={build_status}")
                    else:
                        rebuilt.append(l)
                files["BUILD_EXIT_CODE.txt"] = "\n".join(rebuilt) + "\n"
                fx.write_tree(tree, files)
                errors = v.validate_dir(tree)
                self.assertTrue(errors, "expected fail-closed without explicit outcome")
                self.assertTrue(
                    any("explicit 'outcome'" in e or "inference" in e.lower() for e in errors),
                    errors,
                )
                # Must not silently accept as structural PASS via inference.
                self.assertNotEqual(errors, [])

    def test_07_contradictory_explicit_outcome_and_secondary_fields_rejected(self) -> None:
        tree = self._write_success()
        bec = tree / "BUILD_EXIT_CODE.txt"
        text = bec.read_text(encoding="utf-8").replace("cargo_started=YES", "cargo_started=NO")
        bec.write_text(text, encoding="utf-8", newline="\n")
        files = {
            p.name: p.read_text(encoding="utf-8")
            for p in tree.iterdir()
            if p.is_file() and p.name != v.MANIFEST_NAME
        }
        fx.write_tree(tree, files)
        errors = v.validate_dir(tree)
        self.assertTrue(any("cargo_started" in e for e in errors), errors)
        # Outcome must remain the explicit value — contradiction fails, not repair.
        self.assertFalse(any("inferred" in e.lower() for e in errors), errors)

    # ------------------------------------------------------------------
    # HOST_OUTCOME closed aux + structure
    # ------------------------------------------------------------------
    def test_08_host_outcome_accepted_as_declared_closed_auxiliary(self) -> None:
        tree = self._write_success()
        self.assertTrue((tree / HOST).is_file())
        self.assertIn(HOST, v.CLOSED_AUX_EVIDENCE_FILES)
        errors = v.validate_dir(tree)
        self.assertEqual(errors, [], errors)
        # Listed in manifest must not be rejected as undeclared aux.
        manifest = (tree / v.MANIFEST_NAME).read_text(encoding="utf-8")
        self.assertIn(f"./{HOST}", manifest)

    def test_09_host_outcome_missing_fields_rejected(self) -> None:
        tree = self._write_success()
        lines = [l for l in self._host_lines(tree) if not l.startswith("failure_stage=")]
        self._rewrite_host(tree, lines)
        errors = v.validate_dir(tree)
        self.assertTrue(any("missing required field 'failure_stage'" in e for e in errors), errors)

    def test_10_host_outcome_extra_fields_rejected(self) -> None:
        tree = self._write_success()
        lines = self._host_lines(tree) + ["extra_field=nope"]
        self._rewrite_host(tree, lines)
        errors = v.validate_dir(tree)
        self.assertTrue(any("unknown/extra field 'extra_field'" in e for e in errors), errors)

    def test_11_host_outcome_duplicate_fields_rejected(self) -> None:
        tree = self._write_success()
        lines = self._host_lines(tree) + ["status=OK"]
        self._rewrite_host(tree, lines)
        errors = v.validate_dir(tree)
        self.assertTrue(any("duplicate key 'status'" in e for e in errors), errors)

    def test_12_illegal_host_status_rejected(self) -> None:
        tree = self._write_success()
        lines = [
            "host_infrastructure_status=BANANA" if l.startswith("host_infrastructure_status=") else l
            for l in self._host_lines(tree)
        ]
        self._rewrite_host(tree, lines)
        errors = v.validate_dir(tree)
        self.assertTrue(any("host_infrastructure_status" in e for e in errors), errors)

    def test_13_illegal_container_result_status_rejected(self) -> None:
        tree = self._write_success()
        lines = [
            "container_result_presence=MAYBE" if l.startswith("container_result_presence=") else l
            for l in self._host_lines(tree)
        ]
        self._rewrite_host(tree, lines)
        errors = v.validate_dir(tree)
        self.assertTrue(any("container_result_presence" in e for e in errors), errors)

    def test_14_outcome_disagreement_rejected(self) -> None:
        tree = self._write_success()
        lines = [
            "container_outcome=CARGO_FAILED" if l.startswith("container_outcome=") else l
            for l in self._host_lines(tree)
        ]
        self._rewrite_host(tree, lines)
        errors = v.validate_dir(tree)
        self.assertTrue(any("disagrees with authoritative" in e for e in errors), errors)

    # ------------------------------------------------------------------
    # Host-preliminary / automatable RC4B-017 subset
    # ------------------------------------------------------------------
    def test_15_host_preliminary_pass_requires_post_build_status_ok(self) -> None:
        tree = self._write_success()
        post = tree / "POST_BUILD_INTEGRITY.txt"
        text = post.read_text(encoding="utf-8")
        text = text.replace("status=OK", "status=FAILED").replace(
            "post_build_integrity_ok=yes", "post_build_integrity_ok=no"
        )
        post.write_text(text, encoding="utf-8", newline="\n")
        files = {
            p.name: p.read_text(encoding="utf-8")
            for p in tree.iterdir()
            if p.is_file() and p.name != v.MANIFEST_NAME
        }
        fx.write_tree(tree, files)
        errors = v.validate_dir(tree, host_preliminary=True)
        self.assertTrue(
            any("host-preliminary structural PASS requires status=OK" in e for e in errors),
            errors,
        )

    def test_16_host_preliminary_pass_requires_post_build_integrity_ok_yes(self) -> None:
        tree = self._write_success()
        # Contradictory OK/no is already a schema error; also covered by subset.
        post = tree / "POST_BUILD_INTEGRITY.txt"
        text = post.read_text(encoding="utf-8").replace(
            "post_build_integrity_ok=yes", "post_build_integrity_ok=no"
        )
        post.write_text(text, encoding="utf-8", newline="\n")
        files = {
            p.name: p.read_text(encoding="utf-8")
            for p in tree.iterdir()
            if p.is_file() and p.name != v.MANIFEST_NAME
        }
        fx.write_tree(tree, files)
        errors = v.validate_dir(tree, host_preliminary=True)
        self.assertTrue(
            any("post_build_integrity_ok" in e for e in errors),
            errors,
        )

    def test_17_host_preliminary_enforces_source_lock_subset(self) -> None:
        tree = self._write_success()
        post = tree / "POST_BUILD_INTEGRITY.txt"
        text = post.read_text(encoding="utf-8").replace(
            "source_head_unchanged=yes", "source_head_unchanged=no"
        )
        post.write_text(text, encoding="utf-8", newline="\n")
        files = {
            p.name: p.read_text(encoding="utf-8")
            for p in tree.iterdir()
            if p.is_file() and p.name != v.MANIFEST_NAME
        }
        fx.write_tree(tree, files)
        errors = v.validate_dir(tree, host_preliminary=True)
        self.assertTrue(any("source_head_unchanged=yes" in e for e in errors), errors)

    def test_18_host_outcome_statuses_must_match_post_build_ok_conditions(self) -> None:
        tree = self._write_success()
        lines = [
            "post_build_integrity_status=FAILED" if l.startswith("post_build_integrity_status=") else l
            for l in self._host_lines(tree)
        ]
        self._rewrite_host(tree, lines)
        errors = v.validate_dir(tree, host_preliminary=True)
        self.assertTrue(
            any("post_build_integrity_status=OK" in e for e in errors),
            errors,
        )

    def test_19_evidence_inventory_complete_not_required_for_host_preliminary_pass(self) -> None:
        tree = self._write_success()
        post = (tree / "POST_BUILD_INTEGRITY.txt").read_text(encoding="utf-8")
        self.assertIn("evidence_inventory_complete=no", post)
        errors = v.validate_dir(tree, host_preliminary=True)
        self.assertEqual(errors, [], errors)
        self.assertFalse(any("evidence_inventory_complete=yes" in e for e in errors))

    def test_20_preliminary_success_eligible_remains_no_not_final_eligibility(self) -> None:
        tree = self._write_success()
        host = (tree / HOST).read_text(encoding="utf-8")
        self.assertIn("preliminary_success_eligible=NO", host)
        errors = v.validate_dir(tree, host_preliminary=True)
        self.assertEqual(errors, [], errors)
        # Flipping to YES fails host-preliminary (never final eligibility).
        lines = [
            "preliminary_success_eligible=YES" if l.startswith("preliminary_success_eligible=") else l
            for l in self._host_lines(tree)
        ]
        self._rewrite_host(tree, lines)
        errors_yes = v.validate_dir(tree, host_preliminary=True)
        self.assertTrue(
            any("preliminary_success_eligible must remain NO" in e for e in errors_yes),
            errors_yes,
        )

    # ------------------------------------------------------------------
    # Boundaries: no-write, no host gating, closed aux still closed
    # ------------------------------------------------------------------
    def test_21_validator_writes_no_evidence(self) -> None:
        tree = self._write_success()
        before = {
            p.name: (p.stat().st_mtime_ns, p.read_bytes())
            for p in tree.iterdir()
            if p.is_file()
        }
        errors = v.validate_dir(tree, host_preliminary=True)
        self.assertEqual(errors, [], errors)
        after_names = {p.name for p in tree.iterdir() if p.is_file()}
        self.assertEqual(after_names, set(before))
        for name, (mtime, data) in before.items():
            p = tree / name
            self.assertEqual(p.read_bytes(), data)
            self.assertEqual(p.stat().st_mtime_ns, mtime)
        self.assertNotIn("VALIDATOR_RESULT.txt", after_names)
        src = VALIDATOR.read_text(encoding="utf-8")
        self.assertIn("writes only to its own stdout/stderr", src)
        self.assertIn("never writes into the", src)
        self.assertIn("evidence directory it is validating", src)
        self.assertNotIn("VALIDATOR_RESULT", src)
        self.assertIsNone(re.search(r"evidence_dir[^\n]*\.write_", src))

    def test_22_host_gating_deferred_from_3f_a_implemented_in_3f_b(self) -> None:
        # Phase 3F-A historical boundary: validator itself still writes no VALIDATOR_RESULT.
        src = VALIDATOR.read_text(encoding="utf-8")
        self.assertNotIn("VALIDATOR_RESULT", src)
        self.assertIn("writes only to its own stdout/stderr", src)
        # Current host source after Phase 3F-B: repository validator is invoked in
        # host-preliminary mode and host exit is validator-gated.
        host = HOST_SCRIPT.read_text(encoding="utf-8")
        self.assertIsNotNone(
            re.search(
                r"(?:^|\n)\s*(?:\"\$\{?py\}?\"|\$\{?py\}?|python3?)[^\n]*--host-preliminary",
                host,
            )
            or ("--host-preliminary" in host and "invoke_host_preliminary_validator" in host)
        )
        self.assertIn("--host-preliminary", host)
        self.assertIn("VALIDATOR_RESULT", host)
        self.assertIn("invoke_host_preliminary_validator", host)
        self.assertIn("evaluate_host_automated_structural_gate", host)
        self.assertIn("STRUCTURAL VALIDATION: PASS", host)
        self.assertIn('if [[ "${POST_BUILD_INTEGRITY_OK}" != "yes" ]]; then', host)
        self.assertIn('HOST_VALIDATOR_GATE_OK', host)

    def test_23_closed_auxiliary_inventory_still_rejects_unrelated_extra_files(self) -> None:
        tree = self._write_success()
        extra = tree / "SOMETHING_ELSE.txt"
        extra.write_text("hello\n", encoding="utf-8", newline="\n")
        digest = v.sha256_file(extra)
        mpath = tree / v.MANIFEST_NAME
        mpath.write_text(
            mpath.read_text(encoding="utf-8") + f"{digest}  ./SOMETHING_ELSE.txt\n",
            encoding="utf-8",
            newline="\n",
        )
        errors = v.validate_dir(tree)
        self.assertTrue(any("outside the closed" in e for e in errors), errors)

    def test_24_host_preliminary_pass_on_success_fixture(self) -> None:
        tree = self._write_success()
        errors = v.validate_dir(tree, host_preliminary=True)
        self.assertEqual(errors, [], errors)
        rc = v.main([str(tree), "--host-preliminary"])
        self.assertEqual(rc, 0)

    def test_25_source_or_lock_changed_must_be_no_for_host_preliminary(self) -> None:
        tree = self._write_success()
        post = tree / "POST_BUILD_INTEGRITY.txt"
        text = post.read_text(encoding="utf-8").replace(
            "source_or_lock_changed=no", "source_or_lock_changed=yes"
        )
        post.write_text(text, encoding="utf-8", newline="\n")
        files = {
            p.name: p.read_text(encoding="utf-8")
            for p in tree.iterdir()
            if p.is_file() and p.name != v.MANIFEST_NAME
        }
        fx.write_tree(tree, files)
        errors = v.validate_dir(tree, host_preliminary=True)
        self.assertTrue(any("source_or_lock_changed=no" in e for e in errors), errors)


if __name__ == "__main__":
    try:
        unittest.main(verbosity=2, exit=False)
    finally:
        _cleanup_phase3f_temps()
