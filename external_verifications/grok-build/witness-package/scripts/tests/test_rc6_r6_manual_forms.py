#!/usr/bin/env python3
"""RC6-R6 tests: statement M2+timing, intake/correction sidecars, redaction RD2.

Uses only the Python standard library and local controlled temporary directories.
Does not invoke Docker, Cargo, compilers, product binaries, network, or Witness
workflows. Synthetic only — not Independent Witness evidence.
"""

from __future__ import annotations

import hashlib
import shutil
import tempfile
import unittest
from pathlib import Path
import sys

TESTS_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = TESTS_DIR.parent
PACKAGE_DIR = SCRIPTS_DIR.parent
sys.path.insert(0, str(SCRIPTS_DIR))
sys.path.insert(0, str(TESTS_DIR))

import redaction_index as ridx  # noqa: E402
import schema_register_loader as srl  # noqa: E402
import statement_binding as sb  # noqa: E402
import submission_sidecars as sidecars  # noqa: E402
import validate_witness_evidence as v  # noqa: E402

FIXTURES = TESTS_DIR / "fixtures"
_TEMPS: list[Path] = []


def _mktmp(prefix: str = "rc6r6_test_") -> Path:
    path = Path(tempfile.mkdtemp(prefix=prefix, dir=str(TESTS_DIR)))
    _TEMPS.append(path)
    return path


def _cleanup() -> None:
    for path in _TEMPS:
        if path.exists():
            shutil.rmtree(path, ignore_errors=True)
    _TEMPS.clear()
    for path in TESTS_DIR.glob("rc6r6_test_*"):
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)


def _copy_fixture(name: str) -> Path:
    dst = _mktmp()
    # mkdtemp creates the directory; replace with fixture tree.
    shutil.rmtree(dst)
    shutil.copytree(FIXTURES / name, dst)
    return dst


def _sha_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class Rc6R6SchemaAuthorityTests(unittest.TestCase):
    def tearDown(self) -> None:
        _cleanup()

    def test_01_active_rc65_historical_rc64(self) -> None:
        active = srl.load_active_register()
        self.assertEqual(active.schema_register_version, "rc6.5")
        self.assertEqual(active.supersession().get("supersedes"), "rc6.4")
        self.assertIn("REDACTIONS_INDEX.txt", active.required_files("final-submission"))
        hist = srl.load_historical_register("rc6.4")
        self.assertTrue(hist.is_historical_rc64)
        with self.assertRaises(srl.SchemaRegisterError):
            srl.load_historical_register("rc6.5")
        self.assertEqual(v.validate_dir(FIXTURES / "rc6-r6-synthetic-final"), [])
        self.assertEqual(
            v.validate_dir(FIXTURES / "rc6-r5-synthetic-final", schema_register_version="rc6.4"),
            [],
        )


class Rc6R6StatementTimingTests(unittest.TestCase):
    def tearDown(self) -> None:
        _cleanup()

    def test_02_statement_identity_and_timing_bind(self) -> None:
        tree = _copy_fixture("rc6-r6-synthetic-final")
        self.assertEqual(v.validate_dir(tree), [])
        stmt = v.parse_kv((tree / "WITNESS_STATEMENT.md").read_text(encoding="utf-8"))[0]
        expected = sb.compute_statement_identity_sha256(stmt)
        self.assertEqual(stmt["statement_identity_sha256"], expected)
        self.assertEqual(stmt["execution_timing_source_file"], "BUILD_TIMING.txt")
        self.assertEqual(stmt["execution_timing_source_start_field"], "docker_started_utc")
        self.assertEqual(stmt["execution_timing_source_end_field"], "docker_finished_utc")

    def test_03_timing_mismatch_and_reversed_reject(self) -> None:
        tree = _copy_fixture("rc6-r6-synthetic-final")
        text = (tree / "WITNESS_STATEMENT.md").read_text(encoding="utf-8")
        text = text.replace(
            "execution_started_utc=2026-07-22T00:00:00Z",
            "execution_started_utc=2026-07-22T02:00:00Z",
        )
        # Keep finished earlier → reversed + mismatch vs BUILD_TIMING
        (tree / "WITNESS_STATEMENT.md").write_text(text, encoding="utf-8", newline="\n")
        errs = v.validate_dir(tree)
        self.assertTrue(any("execution_started_utc" in e for e in errs))

    def test_04_wrong_timing_source_file_rejects(self) -> None:
        tree = _copy_fixture("rc6-r6-synthetic-final")
        text = (tree / "WITNESS_STATEMENT.md").read_text(encoding="utf-8")
        text = text.replace(
            "execution_timing_source_file=BUILD_TIMING.txt",
            "execution_timing_source_file=BUILD_EXIT_CODE.txt",
        )
        (tree / "WITNESS_STATEMENT.md").write_text(text, encoding="utf-8", newline="\n")
        errs = v.validate_dir(tree)
        self.assertTrue(any("execution_timing_source_file" in e for e in errs))


class Rc6R6IntakeCorrectionTests(unittest.TestCase):
    def tearDown(self) -> None:
        _cleanup()

    def test_05_final_intake_must_be_pending(self) -> None:
        tree = _copy_fixture("rc6-r6-synthetic-final")
        text = (tree / "WITNESS_VERDICT.md").read_text(encoding="utf-8")
        text = text.replace(
            "maintainer_intake_verdict=pending",
            "maintainer_intake_verdict=accepted",
        )
        (tree / "WITNESS_VERDICT.md").write_text(text, encoding="utf-8", newline="\n")
        errs = v.validate_dir(tree)
        self.assertTrue(any("maintainer_intake_verdict must be pending" in e for e in errs))

    def test_06_intake_sidecar_append_only_outside_package(self) -> None:
        run_id = "run-rc6-r6-intake-001"
        root = _mktmp()
        side = sidecars.sidecar_dir_for_run(root, run_id)
        side.mkdir(parents=True)
        body = (
            sidecars.emit_empty_intake_ledger_header(run_id)
            + "BEGIN_ENTRY\n"
            f"run_id={run_id}\n"
            "recorded_utc=2026-07-26T12:00:00Z\n"
            "maintainer_identity=example-maintainer\n"
            "maintainer_intake_verdict=accepted\n"
            "original_evidence_manifest_sha256="
            + ("a" * 64)
            + "\n"
            "mutates_original_package=no\n"
            "END_ENTRY\n"
        )
        (side / sidecars.MAINTAINER_INTAKE_LEDGER_NAME).write_text(body, encoding="utf-8")
        errs = sidecars.validate_maintainer_intake_ledger(
            body, expected_run_id=run_id, original_manifest_sha256="a" * 64
        )
        self.assertEqual(errs, [])
        # Evidence package must not contain the sidecar.
        self.assertFalse((FIXTURES / "rc6-r6-synthetic-final" / sidecars.MAINTAINER_INTAKE_LEDGER_NAME).exists())

    def test_07_correction_requires_superseding_for_critical(self) -> None:
        run_id = "run-rc6-r6-corr-001"
        body = (
            "BEGIN_ENTRY\n"
            "entry_id=CL-0001\n"
            "recorded_utc=2026-07-26T12:00:00Z\n"
            f"original_run_id={run_id}\n"
            "original_evidence_manifest_sha256="
            + ("b" * 64)
            + "\n"
            "supersession_relationship=ADDENDUM\n"
            "affected_integrity_critical_properties=machine_ceiling,verdict\n"
            "original_negative_evidence_preserved=yes\n"
            "mutates_original_package=no\n"
            "reason=attempted silent ceiling repair\n"
            "END_ENTRY\n"
        )
        errs = sidecars.validate_correction_ledger_entries(body, expected_run_id=run_id)
        self.assertTrue(any("REQUIRES_SUPERSEDING_PACKAGE" in e for e in errs))


class Rc6R6RedactionTests(unittest.TestCase):
    def tearDown(self) -> None:
        _cleanup()

    def test_08_categories_remain_distinct(self) -> None:
        self.assertIn("COMMAND_TEXT", ridx.REDACTION_CATEGORIES)
        self.assertIn("CAPTURED_COMMAND_OUTPUT", ridx.REDACTION_CATEGORIES)
        self.assertNotEqual(
            "COMMAND_TEXT",
            "CAPTURED_COMMAND_OUTPUT",
        )

    def test_09_command_text_integrity_critical_feeds_fail(self) -> None:
        tree = _copy_fixture("rc6-r6-synthetic-final")
        env = tree / "ENVIRONMENT.txt"
        env.write_text(
            env.read_text(encoding="utf-8")
            + "note=[REDACTED:COMMAND_TEXT:cmd]\n",
            encoding="utf-8",
            newline="\n",
        )
        index = (
            "evidence_schema_version=1\n"
            "run_id=run-rc6-r3-schema-synthetic-001\n"
            "redaction_state=PRESENT\n"
            "redaction_count=1\n"
            "redaction_1_file=ENVIRONMENT.txt\n"
            "redaction_1_field=build_command\n"
            "redaction_1_category=COMMAND_TEXT\n"
            "redaction_1_original_value_sha256="
            + ("c" * 64)
            + "\n"
            "redaction_1_replacement_marker=[REDACTED:COMMAND_TEXT:cmd]\n"
        )
        (tree / "REDACTIONS_INDEX.txt").write_text(index, encoding="utf-8", newline="\n")
        red = (tree / "REDACTIONS.md").read_text(encoding="utf-8")
        red = red.replace("redaction_state=NONE", "redaction_state=PRESENT")
        (tree / "REDACTIONS.md").write_text(red, encoding="utf-8", newline="\n")
        errs = v.validate_dir(tree)
        self.assertTrue(any("integrity-critical" in e or "COMMAND_TEXT" in e for e in errs))

    def test_10_marker_count_mismatch_rejects(self) -> None:
        tree = _copy_fixture("rc6-r6-synthetic-final")
        env = tree / "ENVIRONMENT.txt"
        env.write_text(
            env.read_text(encoding="utf-8")
            + "path=[REDACTED:HOME_PATH_IDENTIFIER:home]\n",
            encoding="utf-8",
            newline="\n",
        )
        errs = v.validate_dir(tree)
        self.assertTrue(any("REDACTED" in e or "redaction_state=NONE" in e for e in errs))

    def test_11_unknown_category_rejects(self) -> None:
        fields = {
            "evidence_schema_version": "1",
            "run_id": "run-x",
            "redaction_state": "PRESENT",
            "redaction_count": "1",
            "redaction_1_file": "ENVIRONMENT.txt",
            "redaction_1_field": "home",
            "redaction_1_category": "USERNAME",
            "redaction_1_original_value_sha256": "d" * 64,
            "redaction_1_replacement_marker": "[REDACTED:HOME_PATH_IDENTIFIER:home]",
        }
        errors, _ = ridx.validate_redaction_index_fields(fields)
        self.assertTrue(any("unknown" in e for e in errors))

    def test_12_unknown_extra_statement_field_rejects(self) -> None:
        tree = _copy_fixture("rc6-r6-synthetic-final")
        path = tree / "WITNESS_STATEMENT.md"
        path.write_text(
            path.read_text(encoding="utf-8") + "unexpected_extra_field=nope\n",
            encoding="utf-8",
            newline="\n",
        )
        errs = v.validate_dir(tree)
        self.assertTrue(
            any(
                "WITNESS_STATEMENT.md" in e and "unknown/extra field" in e
                for e in errs
            ),
            errs,
        )

    def test_13_unknown_extra_verdict_field_rejects(self) -> None:
        tree = _copy_fixture("rc6-r6-synthetic-final")
        path = tree / "WITNESS_VERDICT.md"
        text = path.read_text(encoding="utf-8")
        text = text.replace(
            "final_machine_ceiling=PASS\n",
            "final_machine_ceiling=PASS\norphan_verdict_key=bad\n",
        )
        path.write_text(text, encoding="utf-8", newline="\n")
        errs = v.validate_dir(tree)
        self.assertTrue(
            any(
                "WITNESS_VERDICT.md" in e and "unknown/extra field" in e
                for e in errs
            ),
            errs,
        )

    def test_14_field_relocation_rejects(self) -> None:
        marker = "[REDACTED:FILESYSTEM_PATH:path]"
        errors = ridx.reconcile_markers(
            index_fields={
                "redaction_state": "PRESENT",
                "redaction_count": "1",
                "redaction_1_file": "ENVIRONMENT.txt",
                "redaction_1_field": "host_cpu",
                "redaction_1_category": "FILESYSTEM_PATH",
                "redaction_1_original_value_sha256": "a" * 64,
                "redaction_1_replacement_marker": marker,
            },
            all_texts={
                "ENVIRONMENT.txt": f"host_cpu=arm64\nhost_path={marker}\n",
            },
        )
        self.assertTrue(any("field/section" in e or "not present" in e for e in errors), errors)

    def test_15_category_substitution_same_location_rejects(self) -> None:
        marker = "[REDACTED:FILESYSTEM_PATH:path]"
        errors = ridx.reconcile_markers(
            index_fields={
                "redaction_state": "PRESENT",
                "redaction_count": "2",
                "redaction_1_file": "ENVIRONMENT.txt",
                "redaction_1_field": "host_path",
                "redaction_1_category": "FILESYSTEM_PATH",
                "redaction_1_original_value_sha256": "a" * 64,
                "redaction_1_replacement_marker": marker,
                "redaction_2_file": "ENVIRONMENT.txt",
                "redaction_2_field": "host_path",
                "redaction_2_category": "HOME_PATH_IDENTIFIER",
                "redaction_2_original_value_sha256": "b" * 64,
                "redaction_2_replacement_marker": marker,
            },
            all_texts={
                "ENVIRONMENT.txt": f"host_path={marker}\n",
            },
        )
        self.assertTrue(
            any("category substitution" in e or "multiple index entries" in e for e in errors),
            errors,
        )

    def test_16_duplicate_marker_one_to_many_rejects(self) -> None:
        marker = "[REDACTED:FILESYSTEM_PATH:shared]"
        errors = ridx.reconcile_markers(
            index_fields={
                "redaction_state": "PRESENT",
                "redaction_count": "2",
                "redaction_1_file": "ENVIRONMENT.txt",
                "redaction_1_field": "host_path",
                "redaction_1_category": "FILESYSTEM_PATH",
                "redaction_1_original_value_sha256": "a" * 64,
                "redaction_1_replacement_marker": marker,
                "redaction_2_file": "ENVIRONMENT.txt",
                "redaction_2_field": "alt_path",
                "redaction_2_category": "FILESYSTEM_PATH",
                "redaction_2_original_value_sha256": "b" * 64,
                "redaction_2_replacement_marker": marker,
            },
            all_texts={
                "ENVIRONMENT.txt": (
                    f"host_path={marker}\nalt_path=/tmp/other\n"
                ),
            },
        )
        self.assertTrue(
            any(
                "not present" in e
                or "multiple index entries" in e
                or "orphan" in e
                for e in errors
            ),
            errors,
        )

    def test_17_entry_swap_within_file_rejects(self) -> None:
        path_marker = "[REDACTED:FILESYSTEM_PATH:path]"
        home_marker = "[REDACTED:HOME_PATH_IDENTIFIER:home]"
        errors = ridx.reconcile_markers(
            index_fields={
                "redaction_state": "PRESENT",
                "redaction_count": "2",
                "redaction_1_file": "ENVIRONMENT.txt",
                "redaction_1_field": "host_path",
                "redaction_1_category": "FILESYSTEM_PATH",
                "redaction_1_original_value_sha256": "a" * 64,
                "redaction_1_replacement_marker": path_marker,
                "redaction_2_file": "ENVIRONMENT.txt",
                "redaction_2_field": "home_path",
                "redaction_2_category": "HOME_PATH_IDENTIFIER",
                "redaction_2_original_value_sha256": "b" * 64,
                "redaction_2_replacement_marker": home_marker,
            },
            all_texts={
                "ENVIRONMENT.txt": (
                    f"host_path={home_marker}\nhome_path={path_marker}\n"
                ),
            },
        )
        self.assertTrue(any("not present" in e for e in errors), errors)

    def test_18_single_entry_category_substitution_rejects(self) -> None:
        marker = "[REDACTED:FILESYSTEM_PATH:path]"
        errors = ridx.reconcile_markers(
            index_fields={
                "redaction_state": "PRESENT",
                "redaction_count": "1",
                "redaction_1_file": "ENVIRONMENT.txt",
                "redaction_1_field": "host_path",
                "redaction_1_category": "HOME_PATH_IDENTIFIER",
                "redaction_1_original_value_sha256": "a" * 64,
                "redaction_1_replacement_marker": marker,
            },
            all_texts={
                "ENVIRONMENT.txt": f"host_path={marker}\n",
            },
        )
        self.assertTrue(any("category substitution" in e for e in errors), errors)

        field_errors, _ = ridx.validate_redaction_index_fields(
            {
                "evidence_schema_version": "1",
                "run_id": "run-x",
                "redaction_state": "PRESENT",
                "redaction_count": "1",
                "redaction_1_file": "ENVIRONMENT.txt",
                "redaction_1_field": "host_path",
                "redaction_1_category": "HOME_PATH_IDENTIFIER",
                "redaction_1_original_value_sha256": "a" * 64,
                "redaction_1_replacement_marker": marker,
            }
        )
        self.assertTrue(
            any("must exactly equal" in e or "category" in e for e in field_errors),
            field_errors,
        )

    def test_19_malformed_marker_grammar_rejects(self) -> None:
        errors, _ = ridx.validate_redaction_index_fields(
            {
                "evidence_schema_version": "1",
                "run_id": "run-x",
                "redaction_state": "PRESENT",
                "redaction_count": "1",
                "redaction_1_file": "ENVIRONMENT.txt",
                "redaction_1_field": "host_path",
                "redaction_1_category": "FILESYSTEM_PATH",
                "redaction_1_original_value_sha256": "a" * 64,
                "redaction_1_replacement_marker": "[REDACTED: path]",
            }
        )
        self.assertTrue(any("must exactly match" in e for e in errors), errors)


if __name__ == "__main__":
    unittest.main()
