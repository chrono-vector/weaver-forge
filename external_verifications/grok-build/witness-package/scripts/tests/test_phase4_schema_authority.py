#!/usr/bin/env python3
"""Phase 4-S1 focused tests: canonical schema authority and validator mode framework.

Uses only the Python standard library and local controlled temporary directories.
Does not invoke Docker, Cargo, compilers, product binaries, network, or Witness
workflows.
"""

from __future__ import annotations

import json
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

REGISTER_PATH = (
    PACKAGE_DIR / "schemas" / "canonical_schema_register_rc5_phase4_s1.json"
)
FIXTURES = TESTS_DIR / "fixtures"
MANUAL_FILES = frozenset(
    {"WITNESS_STATEMENT.md", "WITNESS_VERDICT.md", "REDACTIONS.md"}
)

_TEMPS: list[Path] = []


def _mktmp(prefix: str = "phase4_test_") -> Path:
    path = Path(tempfile.mkdtemp(prefix=prefix, dir=str(TESTS_DIR)))
    _TEMPS.append(path)
    return path


def _cleanup() -> None:
    for path in _TEMPS:
        if path.exists():
            shutil.rmtree(path, ignore_errors=True)
    _TEMPS.clear()
    # Also clear any leftover phase4_test_* under tests/
    for path in TESTS_DIR.glob("phase4_test_*"):
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)


def _write_register(data: dict, path: Path) -> Path:
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return path


def _base_register() -> dict:
    return json.loads(REGISTER_PATH.read_text(encoding="utf-8"))


def _copy_success_without_manuals(dest: Path) -> Path:
    """Minimum current-compatible host-preliminary package without manual files."""
    src = FIXTURES / "success-artifact-present"
    dest.mkdir(parents=True, exist_ok=True)
    for item in src.iterdir():
        if item.name in MANUAL_FILES:
            continue
        if item.is_file():
            shutil.copy2(item, dest / item.name)
    # Rebuild preliminary-shaped manifest without manual entries.
    files = {
        p.name: p.read_text(encoding="utf-8")
        for p in dest.iterdir()
        if p.is_file() and p.name != v.MANIFEST_NAME
    }
    fx.write_tree(dest, files)
    return dest


class SchemaRegisterLoaderTests(unittest.TestCase):
    def test_01_register_parses_successfully(self) -> None:
        # Historical S1 register remains loadable and truthful.
        reg = srl.load_canonical_register(REGISTER_PATH)
        self.assertEqual(reg.schema_register_version, "rc5-phase4-s1.1")
        self.assertEqual(reg.evidence_schema_version, "1")
        self.assertTrue(reg.is_historical_s1)

    def test_02_supported_version_accepted_unsupported_rejected(self) -> None:
        ok = _base_register()
        srl.validate_register_document(ok)
        bad = _base_register()
        bad["schema_register_version"] = "rc5-phase4-s1.999"
        with self.assertRaises(srl.SchemaRegisterError):
            srl.validate_register_document(bad)

    def test_03_unknown_top_level_and_artifact_keys_rejected(self) -> None:
        top = _base_register()
        top["unexpected_top"] = True
        with self.assertRaises(srl.SchemaRegisterError) as ctx:
            srl.validate_register_document(top)
        self.assertIn("unknown key", str(ctx.exception))

        art = _base_register()
        art["artifacts"][0]["unexpected_artifact_key"] = 1
        with self.assertRaises(srl.SchemaRegisterError) as ctx2:
            srl.validate_register_document(art)
        self.assertIn("unknown key", str(ctx2.exception))

    def test_04_duplicate_artifact_mode_unknown_mode_malformed_fields(self) -> None:
        data = _base_register()
        # Duplicate mode-specific DEVIATIONS entry.
        clone = json.loads(json.dumps(data["artifacts"][-5]))
        # Find final-submission DEVIATIONS and duplicate it.
        for art in data["artifacts"]:
            if art.get("artifact_id") == "DEVIATIONS.txt@final-submission":
                clone = json.loads(json.dumps(art))
                clone["artifact_id"] = "DEVIATIONS.txt@final-submission-dup"
                data["artifacts"].append(clone)
                break
        with self.assertRaises(srl.SchemaRegisterError):
            srl.validate_register_document(data)

        mode_bad = _base_register()
        mode_bad["artifacts"][0]["lifecycle_modes"] = ["not-a-mode"]
        with self.assertRaises(srl.SchemaRegisterError):
            srl.validate_register_document(mode_bad)

        mal = _base_register()
        mal["artifacts"][0]["fields"] = [{"name": "", "requirement": "required"}]
        with self.assertRaises(srl.SchemaRegisterError):
            srl.validate_register_document(mal)

    def test_05_required_optional_contradiction_rejected(self) -> None:
        data = _base_register()
        target = None
        for art in data["artifacts"]:
            if art["filename"] == "POST_BUILD_INTEGRITY.txt":
                target = art
                break
        assert target is not None
        target["optional_fields"] = [
            {"name": "status", "requirement": "optional"}
        ]
        with self.assertRaises(srl.SchemaRegisterError) as ctx:
            srl.validate_register_document(data)
        self.assertIn("contradictory required/optional", str(ctx.exception))

    def test_06_deterministic_lookup_ordered_exact_legal(self) -> None:
        reg = srl.load_canonical_register(REGISTER_PATH)
        art = reg.lookup("POST_BUILD_INTEGRITY.txt", "host-preliminary")
        self.assertEqual(art["filename"], "POST_BUILD_INTEGRITY.txt")
        ordered = reg.ordered_fields("POST_BUILD_INTEGRITY.txt", "final-submission")
        self.assertEqual(ordered[0], "evidence_schema_version")
        self.assertEqual(ordered[-1], "post_build_integrity_ok")
        self.assertEqual(
            reg.exact_field_set_policy("POST_BUILD_INTEGRITY.txt", "host-preliminary"),
            "exact",
        )
        self.assertEqual(
            reg.exact_field_set_policy("HOST_OUTCOME_INGESTION.txt", "host-preliminary"),
            "exact",
        )
        self.assertTrue(reg.field_order_normative("POST_BUILD_INTEGRITY.txt", "final-submission"))
        legal = reg.legal_values("DEVIATIONS.txt", "final-submission")
        self.assertIn("NONE", legal.get("deviation_state", ()))
        # Frozen S1 historical truth: HOST_RUN_METADATA was future S2 at S1 time.
        self.assertEqual(
            reg.activation("HOST_RUN_METADATA.txt", "host-preliminary"),
            "defined_future_s2_writer_alignment",
        )


class ValidatorModeFrameworkTests(unittest.TestCase):
    def test_07_host_preliminary_required_excludes_manual_final_includes(self) -> None:
        prelim = set(v.required_files_for_mode(v.MODE_HOST_PRELIMINARY))
        final = set(v.required_files_for_mode(v.MODE_FINAL_SUBMISSION))
        for name in MANUAL_FILES:
            self.assertNotIn(name, prelim)
            self.assertIn(name, final)
        self.assertIn("DEVIATIONS.txt", prelim)
        self.assertIn(v.HOST_OUTCOME_INGESTION_NAME, prelim)

    def test_08_default_aliases_final_and_modes_mutual_exclusion(self) -> None:
        self.assertEqual(v.DEFAULT_MODE_COMPATIBILITY_ALIAS, v.MODE_FINAL_SUBMISSION)
        self.assertEqual(
            v.resolve_validation_mode(),
            v.MODE_FINAL_SUBMISSION,
        )
        self.assertEqual(
            v.resolve_validation_mode(host_preliminary=True),
            v.MODE_HOST_PRELIMINARY,
        )
        # Mutually exclusive flags.
        with self.assertRaises(SystemExit):
            v.main(
                [
                    str(FIXTURES / "success-artifact-present"),
                    "--host-preliminary",
                    "--final-submission",
                ]
            )

    def test_09_help_text_identifies_modes_and_non_claim_ceilings(self) -> None:
        import io
        from contextlib import redirect_stdout

        buf = io.StringIO()
        with self.assertRaises(SystemExit), redirect_stdout(buf):
            v.main(["--help"])
        help_text = buf.getvalue()
        self.assertIn("--host-preliminary", help_text)
        self.assertIn("--final-submission", help_text)
        self.assertIn("compatibility alias", help_text)
        self.assertIn("Independent Witness PASS", help_text)
        self.assertIn("READY", help_text)
        self.assertIn("rc5", help_text.lower())

    def test_10_validator_no_write_no_inference(self) -> None:
        tree = _copy_success_without_manuals(_mktmp())
        before = {
            p.name: (p.stat().st_mtime_ns, p.read_bytes())
            for p in tree.iterdir()
            if p.is_file()
        }
        errors = v.validate_dir(tree, host_preliminary=True, schema_register_version="rc6.1")
        self.assertEqual(errors, [], errors)
        after = {p.name for p in tree.iterdir() if p.is_file()}
        self.assertEqual(after, set(before))
        for name, (mtime, data) in before.items():
            p = tree / name
            self.assertEqual(p.read_bytes(), data)
            self.assertEqual(p.stat().st_mtime_ns, mtime)
        src = (SCRIPTS_DIR / "validate_witness_evidence.py").read_text(encoding="utf-8")
        self.assertIn("no inference", src.lower())
        self.assertIn("Explicit authoritative outcome only", src)
        self.assertIn("writes only to its own stdout/stderr", src)

    def test_11_host_preliminary_pass_without_manual_files(self) -> None:
        tree = _copy_success_without_manuals(_mktmp())
        for name in MANUAL_FILES:
            self.assertFalse((tree / name).exists())
        errors = v.validate_dir(tree, mode=v.MODE_HOST_PRELIMINARY, schema_register_version="rc6.1")
        self.assertEqual(errors, [], errors)
        rc = v.main([str(tree), "--host-preliminary", "--schema-register-version", "rc6.1"])
        self.assertEqual(rc, 0)

    def test_12_manual_looking_fixture_content_not_required(self) -> None:
        # Full fixture retains manuals; host-preliminary still PASSes and does
        # not treat their presence as eligibility elevation.
        tree = _mktmp()
        files = fx.build_scenario("success-artifact-present")
        fx.write_tree(tree, files)
        # Ensure HOST_OUTCOME present for preliminary.
        self.assertTrue((tree / v.HOST_OUTCOME_INGESTION_NAME).is_file())
        errors = v.validate_dir(tree, host_preliminary=True, schema_register_version="rc6.1")
        self.assertEqual(errors, [], errors)
        host = (tree / v.HOST_OUTCOME_INGESTION_NAME).read_text(encoding="utf-8")
        self.assertIn("preliminary_success_eligible=NO", host)

    def test_13_final_submission_hardened_and_mode_pass_wording(self) -> None:
        tree = FIXTURES / "success-artifact-present"
        import io
        from contextlib import redirect_stdout

        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = v.main([str(tree), "--final-submission", "--schema-register-version", "rc6.1"])
        self.assertEqual(rc, 0)
        out = buf.getvalue()
        self.assertIn("final-submission structural PASS", out)
        self.assertNotIn("not fully hardened until Phase 4-S3", out)
        self.assertNotIn("Independent Witness PASS claimed", out)
        self.assertIn("not Independent Witness PASS", out)
        self.assertIn("not READY", out)
        self.assertIn("not rc5 readiness", out)
        # Register marks final cryptographic closure as enforced S3.
        reg = srl.load_canonical_register(REGISTER_PATH)
        # Active authority is S2; load active for activation detail.
        active = srl.load_active_register()
        man = active.lookup("EVIDENCE_MANIFEST.sha256", "final-submission")
        self.assertEqual(
            man["activation_detail"]["final_cryptographic_closure"],
            "enforced_s3_manifest_completeness",
        )
        self.assertEqual(reg.schema_register_version, "rc5-phase4-s1.1")

    def test_14_exact_protections_remain_and_future_targets_not_falsely_enforced(self) -> None:
        self.assertEqual(
            v._SCHEMA_REGISTER.exact_field_set_policy(
                "POST_BUILD_INTEGRITY.txt", "host-preliminary"
            ),
            "exact",
        )
        self.assertEqual(
            v._SCHEMA_REGISTER.exact_field_set_policy(
                "HOST_OUTCOME_INGESTION.txt", "final-submission"
            ),
            "exact",
        )
        # Historical S1 register: annotated-tag / NOT_APPLICABLE targets were
        # future-only at S1 (frozen truth preserved).
        s1 = srl.load_historical_s1_register()
        pkg = [
            a
            for a in s1.raw["artifacts"]
            if a["filename"] == "WEAVER_FORGE_PACKAGE_IDENTITY.txt"
        ][0]
        future = pkg["future_alignment_fields"]
        self.assertEqual(future["activation"], "defined_future_s2_writer_alignment")
        future_names = {f["name"] for f in future["fields"]}
        self.assertIn("weaver_forge_tag_raw_object_type_observed", future_names)
        self.assertIn("weaver_forge_tag_peeled_commit", future_names)
        # Historical compatibility projection still does not force S2 tag fields
        # onto historical fixtures.
        self.assertNotIn(
            "weaver_forge_tag_peeled_commit",
            v.FILE_REQUIRED_FIELDS["WEAVER_FORGE_PACKAGE_IDENTITY.txt"],
        )
        boot_s1 = s1.lookup("BOOTSTRAP.txt", "host-preliminary")
        variants_s1 = {x["variant_id"]: x for x in boot_s1["conditional_variants"]}
        self.assertEqual(
            variants_s1["early_failure_not_applicable_target"]["activation"],
            "defined_future_s2_writer_alignment",
        )
        # Active rc6 register supersedes rc6.3 and retains S2 writer-aligned activations.
        self.assertEqual(v.SCHEMA_REGISTER_VERSION, srl.ACTIVE_REGISTER_VERSION)
        self.assertEqual(v.SCHEMA_REGISTER_VERSION, "rc6.4")
        self.assertEqual(
            v._SCHEMA_REGISTER.supersession().get("supersedes"),
            srl.HISTORICAL_RC63_REGISTER_VERSION,
        )
        boot_active = v._SCHEMA_REGISTER.lookup("BOOTSTRAP.txt", "host-preliminary")
        variants_active = {x["variant_id"]: x for x in boot_active["conditional_variants"]}
        self.assertEqual(
            variants_active["early_failure_not_applicable_target"]["activation"],
            "enforced_s2_writer_aligned",
        )
        self.assertEqual(
            v._SCHEMA_REGISTER.activation("HOST_RUN_METADATA.txt", "host-preliminary"),
            "enforced_s2_writer_aligned",
        )
        # Frozen S2 remains explicitly loadable as historical predecessor.
        s2 = srl.load_historical_s2_register()
        self.assertEqual(s2.supersession().get("supersedes"), srl.HISTORICAL_S1_REGISTER_VERSION)
        # Historical contract path unchanged / present.
        contract = PACKAGE_DIR / "AUTHORITATIVE_OUTCOME_CONTRACT.json"
        self.assertTrue(contract.is_file())


class HistoricalNonModificationSmoke(unittest.TestCase):
    def test_15_default_mode_still_validates_existing_fixture(self) -> None:
        errors = v.validate_dir(FIXTURES / "success-artifact-present", schema_register_version="rc6.1")
        self.assertEqual(errors, [], errors)


def tearDownModule() -> None:
    _cleanup()


if __name__ == "__main__":
    try:
        suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        if not result.wasSuccessful():
            sys.exit(1)
    finally:
        _cleanup()
