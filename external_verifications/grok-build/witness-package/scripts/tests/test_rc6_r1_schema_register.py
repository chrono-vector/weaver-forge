#!/usr/bin/env python3
"""RC6-R1 focused tests: schema register foundation retained under RC6-R3.

Active authority is now rc6.4; this file keeps the R1 exact-key / historical
compatibility regressions and updates version expectations accordingly.
Uses only the Python standard library and local controlled temporary directories.
Does not invoke Docker, Cargo, compilers, product binaries, network, or Witness
workflows. Synthetic only — not Independent Witness evidence.
"""

from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = TESTS_DIR.parent
PACKAGE_DIR = SCRIPTS_DIR.parent
sys.path.insert(0, str(SCRIPTS_DIR))
sys.path.insert(0, str(TESTS_DIR))

import fixtures_lib as fx  # noqa: E402
import schema_register_loader as srl  # noqa: E402
import validate_witness_evidence as v  # noqa: E402

RC6_REGISTER = PACKAGE_DIR / "schemas" / "canonical_schema_register_rc6.json"
RC61_REGISTER = PACKAGE_DIR / "schemas" / "canonical_schema_register_rc6.1.json"
S2_REGISTER = PACKAGE_DIR / "schemas" / "canonical_schema_register_rc5_phase4_s2.json"
S1_REGISTER = PACKAGE_DIR / "schemas" / "canonical_schema_register_rc5_phase4_s1.json"
FIXTURES = TESTS_DIR / "fixtures"

_TEMPS: list[Path] = []


def _mktmp(prefix: str = "rc6r1_test_") -> Path:
    path = Path(tempfile.mkdtemp(prefix=prefix, dir=str(TESTS_DIR)))
    _TEMPS.append(path)
    return path


def _cleanup() -> None:
    for path in _TEMPS:
        if path.exists():
            shutil.rmtree(path, ignore_errors=True)
    _TEMPS.clear()
    for path in TESTS_DIR.glob("rc6r1_test_*"):
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)


class Rc6R1RegisterAuthorityTests(unittest.TestCase):
    @classmethod
    def tearDownClass(cls) -> None:
        _cleanup()

    def tearDown(self) -> None:
        _cleanup()

    def test_01_active_default_is_rc6_2(self) -> None:
        default = srl.load_canonical_register()
        active = srl.load_active_register()
        self.assertEqual(default.schema_register_version, "rc6.4")
        self.assertEqual(active.schema_register_version, "rc6.4")
        self.assertEqual(active.raw["family"], "rc6_remediation_canonical_schema")
        self.assertEqual(active.source_path.resolve(), RC6_REGISTER.resolve())
        self.assertEqual(v.SCHEMA_REGISTER_VERSION, "rc6.4")
        self.assertTrue(RC6_REGISTER.is_file())

    def test_02_historical_rc61_s2_s1_explicit_only(self) -> None:
        rc61 = srl.load_historical_register("rc6.1")
        s2 = srl.load_historical_register("rc5-phase4-s2.1")
        s1 = srl.load_historical_register("rc5-phase4-s1.1")
        self.assertTrue(rc61.is_historical_rc61)
        self.assertTrue(s2.is_historical_s2)
        self.assertTrue(s1.is_historical_s1)
        self.assertFalse(rc61.is_active_authority)
        self.assertFalse(s2.is_active_authority)
        self.assertFalse(s1.is_active_authority)
        self.assertEqual(rc61.source_path.resolve(), RC61_REGISTER.resolve())
        self.assertEqual(s2.source_path.resolve(), S2_REGISTER.resolve())
        self.assertEqual(s1.source_path.resolve(), S1_REGISTER.resolve())
        with self.assertRaises(srl.SchemaRegisterError):
            srl.load_historical_register("rc6.4")
        with self.assertRaises(srl.SchemaRegisterError):
            srl.load_canonical_register(version="rc6.99")

    def test_03_supersession_and_non_competing_historical(self) -> None:
        active = srl.load_active_register()
        hist = active.historical_compatibility()
        self.assertEqual(active.supersession().get("supersedes"), "rc6.3")
        self.assertEqual(hist.get("active_authority"), "rc6.4")
        self.assertEqual(hist.get("immediate_predecessor_version"), "rc6.3")
        self.assertEqual(hist.get("earlier_historical_compatibility_version"), "rc6.2")
        self.assertEqual(hist.get("prior_historical_compatibility_version"), "rc5-phase4-s2.1")
        self.assertEqual(hist.get("earliest_historical_compatibility_version"), "rc5-phase4-s1.1")
        self.assertTrue(hist.get("not_a_second_schema_authority"))

    def test_04_no_required_subset_on_active_structured_files(self) -> None:
        active = srl.load_active_register()
        for art in active.raw["artifacts"]:
            policy = art["exact_field_set_policy"]
            self.assertNotEqual(
                policy,
                "required_subset_allowed",
                msg=f"{art['artifact_id']} must not remain required-subset-only",
            )

    def test_05_unknown_key_rejected_per_structured_family(self) -> None:
        tree = _mktmp()
        files = fx.build_scenario("success-artifact-present")
        files["SOURCE_ACQUISITION.txt"] += "unexpected_rc6_probe_key=1\n"
        fx.write_tree(tree, files)
        errors = v.validate_dir(tree, schema_register_version="rc6.1")
        self.assertTrue(any("unknown/extra field 'unexpected_rc6_probe_key'" in e for e in errors), errors)

    def test_06_named_optional_passes_unknown_fails(self) -> None:
        tree = _mktmp()
        files = fx.build_scenario("success-artifact-present")
        # status is a named optional on SOURCE_IDENTITY under rc6.1
        src = files["SOURCE_IDENTITY.txt"]
        if "status=" not in src:
            files["SOURCE_IDENTITY.txt"] = "status=OK\n" + src
        fx.write_tree(tree, files)
        self.assertEqual(v.validate_dir(tree, schema_register_version="rc6.1"), [])

        tree2 = _mktmp()
        files2 = fx.build_scenario("success-artifact-present")
        files2["SOURCE_IDENTITY.txt"] += "not_a_registered_optional=x\n"
        fx.write_tree(tree2, files2)
        errors = v.validate_dir(tree2, schema_register_version="rc6.1")
        self.assertTrue(any("not_a_registered_optional" in e for e in errors), errors)

    def test_07_missing_and_duplicate_keys_fail(self) -> None:
        tree = _mktmp()
        files = fx.build_scenario("success-artifact-present")
        lines = [
            ln
            for ln in files["BUILD_EXIT_CODE.txt"].splitlines()
            if not ln.startswith("failure_stage=")
        ]
        files["BUILD_EXIT_CODE.txt"] = "\n".join(lines) + "\n"
        fx.write_tree(tree, files)
        errors = v.validate_dir(tree, schema_register_version="rc6.1")
        self.assertTrue(any("missing required field 'failure_stage'" in e for e in errors), errors)

        tree2 = _mktmp()
        files2 = fx.build_scenario("success-artifact-present")
        files2["BUILD_EXIT_CODE.txt"] += "outcome=CARGO_SUCCEEDED_ARTIFACT_PRESENT\n"
        fx.write_tree(tree2, files2)
        errors2 = v.validate_dir(tree2, schema_register_version="rc6.1")
        self.assertTrue(any("duplicate" in e.lower() or "repeated" in e.lower() for e in errors2), errors2)

    def test_08_raw_captures_outside_exact_closure(self) -> None:
        active = srl.load_active_register()
        for raw in (
            "BUILD_STDOUT.txt",
            "BUILD_STDERR.txt",
            "CONTAINER_STDOUT.txt",
            "CONTAINER_STDERR.txt",
        ):
            self.assertEqual(
                active.exact_field_set_policy(raw, "final-submission"),
                "raw_stream",
            )
        tree = _mktmp()
        files = fx.build_scenario("success-artifact-present")
        files["BUILD_STDOUT.txt"] = "not_key_value_raw_output\nline2\n"
        fx.write_tree(tree, files)
        self.assertEqual(v.validate_dir(tree, schema_register_version="rc6.1"), [])

    def test_09_evidence_cannot_select_schema_authority(self) -> None:
        tree = _mktmp()
        files = fx.build_scenario("success-artifact-present")
        # Inject a fake register-selector key; must not switch authority and must fail as unknown.
        files["ENVIRONMENT.txt"] += "schema_register_version=rc5-phase4-s1.1\n"
        fx.write_tree(tree, files)
        errors = v.validate_dir(tree, schema_register_version="rc6.1")
        self.assertEqual(v.SCHEMA_REGISTER_VERSION, "rc6.4")
        self.assertTrue(any("schema_register_version" in e for e in errors), errors)

    def test_10_historical_rc4_and_rc5_fixtures_still_pass(self) -> None:
        rc4 = FIXTURES / "success-artifact-present"
        errors = v.validate_dir(rc4, schema_register_version="rc6.1")
        self.assertEqual(errors, [], errors)
        pkg = (rc4 / "WEAVER_FORGE_PACKAGE_IDENTITY.txt").read_text(encoding="utf-8")
        self.assertIn("package_version=1.0.0-rc4", pkg)

        rc5p = FIXTURES / "rc5-preliminary-success"
        self.assertEqual(v.validate_dir(rc5p, host_preliminary=True, schema_register_version="rc6.1"), [])
        rc5f = FIXTURES / "rc5-synthetic-final-success"
        self.assertEqual(v.validate_dir(rc5f, schema_register_version="rc6.1"), [])
        # Must not be relabeled as rc6 production evidence.
        self.assertIn("1.0.0-rc5-phase4-s3-fixture", (rc5f / "WEAVER_FORGE_PACKAGE_IDENTITY.txt").read_text(encoding="utf-8"))

    def test_11_rc6_historical_and_active_synthetic_fixtures_conform(self) -> None:
        prelim = FIXTURES / "rc6-r1-synthetic-preliminary"
        final = FIXTURES / "rc6-r1-synthetic-final"
        self.assertTrue(prelim.is_dir(), "rc6-r1-synthetic-preliminary fixture required")
        self.assertTrue(final.is_dir(), "rc6-r1-synthetic-final fixture required")
        self.assertEqual(v.validate_dir(prelim, host_preliminary=True, schema_register_version="rc6.1"), [])
        self.assertEqual(v.validate_dir(final, schema_register_version="rc6.1"), [])
        for tree in (prelim, final):
            pkg = (tree / "WEAVER_FORGE_PACKAGE_IDENTITY.txt").read_text(encoding="utf-8")
            self.assertIn("run-rc6-r1-schema-synthetic", pkg)
            self.assertNotIn("Independent Witness PASS", pkg)
            self.assertNotIn("weaver_forge_tag_object_id", pkg)
        r3p = FIXTURES / "rc6-r3-synthetic-preliminary"
        r3f = FIXTURES / "rc6-r3-synthetic-final"
        # Pre-R5 fixtures validate under explicit historical rc6.3.
        self.assertEqual(
            v.validate_dir(r3p, host_preliminary=True, schema_register_version="rc6.3"),
            [],
        )
        self.assertEqual(v.validate_dir(r3f, schema_register_version="rc6.3"), [])
        r5p = FIXTURES / "rc6-r5-synthetic-preliminary"
        r5f = FIXTURES / "rc6-r5-synthetic-final"
        self.assertEqual(v.validate_dir(r5p, host_preliminary=True), [])
        self.assertEqual(v.validate_dir(r5f), [])
        self.assertIn(
            "weaver_forge_tag_object_id=",
            (r5f / "WEAVER_FORGE_PACKAGE_IDENTITY.txt").read_text(encoding="utf-8"),
        )

    def test_12_witness_statement_ai_assistance_detail_authorized(self) -> None:
        """Pi conformance: ai_assistance_detail is a named optional; yes requires nonempty."""
        active = srl.load_active_register()
        opts = active.optional_field_names("WITNESS_STATEMENT.md", "final-submission")
        self.assertIn("ai_assistance_detail", opts)

        def _set_statement(files: dict[str, str], *, used: str, detail: str | None) -> None:
            lines = []
            for line in files["WITNESS_STATEMENT.md"].splitlines():
                if line.startswith("ai_assistance_used="):
                    lines.append(f"ai_assistance_used={used}")
                elif line.startswith("ai_assistance_detail="):
                    continue
                else:
                    lines.append(line)
            if detail is not None:
                # Keep template-adjacent order: immediately after ai_assistance_used.
                out: list[str] = []
                for line in lines:
                    out.append(line)
                    if line.startswith("ai_assistance_used="):
                        out.append(f"ai_assistance_detail={detail}")
                lines = out
            files["WITNESS_STATEMENT.md"] = "\n".join(lines) + "\n"

        # yes + nonempty detail must pass under exact + named optional.
        tree_ok = _mktmp()
        files_ok = fx.build_scenario("success-artifact-present")
        _set_statement(files_ok, used="yes", detail="local_editor_autocomplete_only")
        fx.write_tree(tree_ok, files_ok)
        self.assertEqual(v.validate_dir(tree_ok, schema_register_version="rc6.1"), [])

        # yes without ai_assistance_detail must fail (existing semantic rule).
        tree_missing = _mktmp()
        files_missing = fx.build_scenario("success-artifact-present")
        _set_statement(files_missing, used="yes", detail=None)
        fx.write_tree(tree_missing, files_missing)
        errors_missing = v.validate_dir(tree_missing, schema_register_version="rc6.1")
        self.assertTrue(
            any("ai_assistance_detail is required when ai_assistance_used=yes" in e for e in errors_missing),
            errors_missing,
        )

        # unknown unrelated field on WITNESS_STATEMENT still rejected.
        tree_unknown = _mktmp()
        files_unknown = fx.build_scenario("success-artifact-present")
        _set_statement(files_unknown, used="yes", detail="local_editor_autocomplete_only")
        files_unknown["WITNESS_STATEMENT.md"] += "not_a_statement_field=1\n"
        fx.write_tree(tree_unknown, files_unknown)
        errors_unknown = v.validate_dir(tree_unknown, schema_register_version="rc6.1")
        self.assertTrue(
            any("unknown/extra field 'not_a_statement_field'" in e for e in errors_unknown),
            errors_unknown,
        )


if __name__ == "__main__":
    unittest.main()
