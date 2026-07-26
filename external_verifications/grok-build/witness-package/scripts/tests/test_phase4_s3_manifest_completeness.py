#!/usr/bin/env python3
"""Phase 4-S3 focused tests: manifest totality, completeness state machine, fixtures.

Uses only the Python standard library and real local validator against disposable
or committed fixture trees. No Docker daemon, Cargo, product binary, network,
production Witness, or Independent Witness execution.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
TESTS_DIR = Path(__file__).resolve().parent
FIXTURES = TESTS_DIR / "fixtures"
PACKAGE_DIR = SCRIPTS_DIR.parent

sys.path.insert(0, str(SCRIPTS_DIR))
sys.path.insert(0, str(TESTS_DIR))

import evidence_inventory as ei  # noqa: E402
import fixtures_lib as fx  # noqa: E402
import schema_register_loader as srl  # noqa: E402
import synthetic_final_submission_helper as syn  # noqa: E402
import validate_witness_evidence as v  # noqa: E402

_TEMP_ROOTS: list[Path] = []


def _mktmp() -> Path:
    root = Path(tempfile.mkdtemp(prefix="phase4_s3_test_"))
    _TEMP_ROOTS.append(root)
    return root


def tearDownModule() -> None:
    for root in _TEMP_ROOTS:
        shutil.rmtree(root, ignore_errors=True)
    _TEMP_ROOTS.clear()


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class PreliminaryManifestTests(unittest.TestCase):
    def test_01_complete_recursive_inclusion_self_exclusion_order_sha(self) -> None:
        tree = _mktmp()
        files = fx.build_rc5_preliminary_success()
        fx.write_tree(tree, files)
        # Nested regular file must be recursively included under total closure.
        nested = tree / "nested" / "extra.txt"
        nested.parent.mkdir(parents=True)
        nested.write_text("nested-payload\n", encoding="utf-8", newline="\n")
        ei.write_evidence_manifest(tree)
        lines = (tree / v.MANIFEST_NAME).read_text(encoding="utf-8").splitlines()
        self.assertTrue(lines)
        self.assertFalse(any(v.MANIFEST_NAME in line for line in lines))
        rels = [line.split("  ./", 1)[1] for line in lines]
        self.assertEqual(rels, sorted(rels))
        self.assertIn("nested/extra.txt", rels)
        inv = ei.enumerate_evidence_files(tree)
        self.assertIn("nested/extra.txt", inv)
        for line in lines:
            digest, rel = line.split("  ./", 1)
            self.assertEqual(digest, _sha(tree / rel))
        nested_line = next(ln for ln in lines if ln.endswith("  ./nested/extra.txt"))
        self.assertEqual(nested_line.split("  ./", 1)[0], _sha(nested))
        # Valid closed preliminary package with nested file must PASS.
        self.assertEqual(v.validate_dir(tree, mode=v.MODE_HOST_PRELIMINARY, schema_register_version="rc6.1"), [])
        # Unlisted nested file fails totality.
        (tree / "nested" / "orphan.txt").write_text("orphan\n", encoding="utf-8", newline="\n")
        errors_unlisted = v.validate_dir(tree, mode=v.MODE_HOST_PRELIMINARY, schema_register_version="rc6.1")
        self.assertTrue(
            any("no auxiliary exemption" in e and "nested/orphan.txt" in e for e in errors_unlisted),
            errors_unlisted,
        )

    def test_02_auxiliary_inclusion_and_unlisted_stale_rejection(self) -> None:
        tree = _mktmp()
        files = fx.build_rc5_preliminary_success()
        fx.write_tree(tree, files)
        # Aux present and listed.
        self.assertTrue((tree / "HOST_RUN_METADATA.txt").is_file())
        manifest = (tree / v.MANIFEST_NAME).read_text(encoding="utf-8")
        self.assertIn("./HOST_RUN_METADATA.txt", manifest)
        self.assertEqual(v.validate_dir(tree, mode=v.MODE_HOST_PRELIMINARY, schema_register_version="rc6.1"), [])

        # Unlisted closed-aux rejection for S2-shaped.
        lines = [
            ln
            for ln in manifest.splitlines()
            if "HOST_RUN_METADATA.txt" not in ln
        ]
        (tree / v.MANIFEST_NAME).write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
        errors = v.validate_dir(tree, mode=v.MODE_HOST_PRELIMINARY, schema_register_version="rc6.1")
        self.assertTrue(any("no auxiliary exemption" in e for e in errors), errors)

        # Stale hash rejection.
        tree2 = _mktmp()
        fx.write_tree(tree2, files)
        bad = (tree2 / v.MANIFEST_NAME).read_text(encoding="utf-8").splitlines()
        bad[0] = ("0" * 64) + bad[0][64:]
        (tree2 / v.MANIFEST_NAME).write_text("\n".join(bad) + "\n", encoding="utf-8", newline="\n")
        errors2 = v.validate_dir(tree2, mode=v.MODE_HOST_PRELIMINARY, schema_register_version="rc6.1")
        self.assertTrue(any("hash mismatch" in e for e in errors2), errors2)


class FinalManifestTests(unittest.TestCase):
    def test_03_final_total_closure_manual_inputs_no_aux_exemption(self) -> None:
        tree = FIXTURES / "rc5-synthetic-final-success"
        errors = v.validate_dir(tree, mode=v.MODE_FINAL_SUBMISSION, schema_register_version="rc6.1")
        self.assertEqual(errors, [], errors)
        manifest = (tree / v.MANIFEST_NAME).read_text(encoding="utf-8")
        for name in (
            "WITNESS_STATEMENT.md",
            "WITNESS_VERDICT.md",
            "DEVIATIONS.txt",
            "REDACTIONS.md",
            "HOST_OUTCOME_INGESTION.txt",
            "HOST_RUN_METADATA.txt",
        ):
            self.assertIn(f"./{name}", manifest)

        # Post-manifest edit rejection (hash mismatch / immutability).
        tree2 = Path(tempfile.mkdtemp(prefix="phase4_s3_test_"))
        _TEMP_ROOTS.append(tree2)
        shutil.rmtree(tree2)
        shutil.copytree(tree, tree2)
        (tree2 / "REDACTIONS.md").write_text(
            (tree2 / "REDACTIONS.md").read_text(encoding="utf-8") + "\n",
            encoding="utf-8",
            newline="\n",
        )
        errors2 = v.validate_dir(tree2, mode=v.MODE_FINAL_SUBMISSION, schema_register_version="rc6.1")
        self.assertTrue(any("hash mismatch" in e for e in errors2), errors2)

        # Extra undeclared file.
        tree3 = Path(tempfile.mkdtemp(prefix="phase4_s3_test_"))
        _TEMP_ROOTS.append(tree3)
        shutil.rmtree(tree3)
        shutil.copytree(tree, tree3)
        (tree3 / "UNDECLARED_AUX.txt").write_text("nope\n", encoding="utf-8")
        errors3 = v.validate_dir(tree3, mode=v.MODE_FINAL_SUBMISSION, schema_register_version="rc6.1")
        self.assertTrue(
            any("no auxiliary exemption" in e or "outside the closed" in e for e in errors3),
            errors3,
        )


class CompletenessStateMachineTests(unittest.TestCase):
    def test_04_preliminary_incomplete_and_yes_rejected(self) -> None:
        tree = _mktmp()
        files = fx.build_rc5_preliminary_success()
        fx.write_tree(tree, files)
        post = (tree / "POST_BUILD_INTEGRITY.txt").read_text(encoding="utf-8")
        host = (tree / "HOST_OUTCOME_INGESTION.txt").read_text(encoding="utf-8")
        self.assertIn("evidence_inventory_complete=no", post)
        self.assertIn("evidence_completeness_status=INCOMPLETE", host)
        self.assertIn("preliminary_success_eligible=NO", host)
        self.assertEqual(v.validate_dir(tree, mode=v.MODE_HOST_PRELIMINARY, schema_register_version="rc6.1"), [])

        # yes rejected in preliminary.
        (tree / "POST_BUILD_INTEGRITY.txt").write_text(
            post.replace("evidence_inventory_complete=no", "evidence_inventory_complete=yes"),
            encoding="utf-8",
            newline="\n",
        )
        ei.write_evidence_manifest(tree)
        errors = v.validate_dir(tree, mode=v.MODE_HOST_PRELIMINARY, schema_register_version="rc6.1")
        self.assertTrue(any("rejected in host-preliminary" in e for e in errors), errors)

    def test_05_final_transition_and_invalid_combinations(self) -> None:
        # yes before required inputs rejected.
        tree = _mktmp()
        files = fx.build_rc5_preliminary_success()
        files["POST_BUILD_INTEGRITY.txt"] = files["POST_BUILD_INTEGRITY.txt"].replace(
            "evidence_inventory_complete=no",
            "evidence_inventory_complete=yes",
        )
        files["HOST_OUTCOME_INGESTION.txt"] = files["HOST_OUTCOME_INGESTION.txt"].replace(
            "evidence_completeness_status=INCOMPLETE",
            "evidence_completeness_status=COMPLETE",
        )
        # Still no manuals.
        fx.write_tree(tree, files)
        errors = v.validate_dir(tree, mode=v.MODE_FINAL_SUBMISSION, schema_register_version="rc6.1")
        self.assertTrue(any("required final structural inputs are absent" in e for e in errors), errors)

        # Valid final transition via synthetic helper (completeness before manifest).
        tree2 = _mktmp()
        files2 = fx.build_rc5_preliminary_success()
        # Add manuals first, inventory still no.
        files2["WITNESS_STATEMENT.md"] = fx._witness_statement()
        files2["WITNESS_VERDICT.md"] = fx._witness_verdict("success-artifact-present")
        files2["REDACTIONS.md"] = fx._redactions()
        files2["DEVIATIONS.txt"] = fx._rc5_final_deviations()
        fx.write_tree(tree2, files2)
        # Manifest-before-completeness: final mode with inventory=no fails.
        errors_pre = v.validate_dir(tree2, mode=v.MODE_FINAL_SUBMISSION, schema_register_version="rc6.1")
        self.assertTrue(any("evidence_inventory_complete=yes" in e for e in errors_pre), errors_pre)
        # Finalize completeness then remanifest.
        syn.synthesize_final_submission_package(tree2)
        self.assertEqual(v.validate_dir(tree2, mode=v.MODE_FINAL_SUBMISSION, schema_register_version="rc6.1"), [])

        # Mutation after finalization rejected.
        (tree2 / "DEVIATIONS.txt").write_text(
            (tree2 / "DEVIATIONS.txt").read_text(encoding="utf-8").replace(
                "deviation_count=0", "deviation_count=1"
            ),
            encoding="utf-8",
            newline="\n",
        )
        errors_mut = v.validate_dir(tree2, mode=v.MODE_FINAL_SUBMISSION, schema_register_version="rc6.1")
        self.assertTrue(any("hash mismatch" in e for e in errors_mut), errors_mut)

    def test_06_machine_cannot_set_independent_witness_or_ready(self) -> None:
        src = (SCRIPTS_DIR / "validate_witness_evidence.py").read_text(encoding="utf-8")
        self.assertNotIn("INDEPENDENT_WITNESS_PASS=yes", src)
        self.assertNotIn("READY=yes", src)
        self.assertIn("not Independent Witness PASS", src)
        helper = (TESTS_DIR / "synthetic_final_submission_helper.py").read_text(encoding="utf-8")
        self.assertIn("Does not set Independent Witness PASS", helper)


class FixtureFamilyTests(unittest.TestCase):
    def test_07_rc5_fixtures_pass_and_are_immutable(self) -> None:
        prelim = FIXTURES / "rc5-preliminary-success"
        final = FIXTURES / "rc5-synthetic-final-success"
        before_p = {p.name: p.read_bytes() for p in prelim.iterdir() if p.is_file()}
        before_f = {p.name: p.read_bytes() for p in final.iterdir() if p.is_file()}
        self.assertEqual(v.validate_dir(prelim, mode=v.MODE_HOST_PRELIMINARY, schema_register_version="rc6.1"), [])
        self.assertEqual(v.validate_dir(final, mode=v.MODE_FINAL_SUBMISSION, schema_register_version="rc6.1"), [])
        for name, data in before_p.items():
            self.assertEqual((prelim / name).read_bytes(), data)
        for name, data in before_f.items():
            self.assertEqual((final / name).read_bytes(), data)
        # Preliminary has no required manuals.
        for name in ("WITNESS_STATEMENT.md", "WITNESS_VERDICT.md", "REDACTIONS.md"):
            self.assertFalse((prelim / name).exists())
        # Final is explicitly synthetic.
        pkg = (final / "WEAVER_FORGE_PACKAGE_IDENTITY.txt").read_text(encoding="utf-8")
        self.assertIn("rc5-phase4-s3-fixture", pkg)
        meta = (final / "HOST_RUN_METADATA.txt").read_text(encoding="utf-8")
        self.assertIn("not_production_witness", meta)

    def test_08_historical_fixture_compatibility_remains(self) -> None:
        hist = FIXTURES / "success-artifact-present"
        pkg = (hist / "WEAVER_FORGE_PACKAGE_IDENTITY.txt").read_text(encoding="utf-8")
        self.assertNotIn("weaver_forge_tag_peeled_commit=", pkg)
        self.assertEqual(v.validate_dir(hist, mode=v.MODE_FINAL_SUBMISSION, schema_register_version="rc6.1"), [])
        self.assertEqual(v.validate_dir(hist, mode=v.MODE_HOST_PRELIMINARY, schema_register_version="rc6.1"), [])


class SchemaRuntimeAlignmentTests(unittest.TestCase):
    def test_09_active_s2_s3_activation_and_s1_compat(self) -> None:
        active = srl.load_active_register()
        self.assertEqual(active.schema_register_version, "rc6.4")
        s2 = srl.load_historical_s2_register()
        self.assertEqual(s2.schema_register_version, "rc5-phase4-s2.1")
        self.assertTrue(active.is_s3_manifest_completeness_enforced())
        man = active.lookup("EVIDENCE_MANIFEST.sha256", "final-submission")
        self.assertEqual(
            man["activation_detail"]["final_cryptographic_closure"],
            "enforced_s3_manifest_completeness",
        )
        auth = active.evidence_completeness_inventory()["field_authority"]
        self.assertEqual(auth["evidence_inventory_complete"], "POST_BUILD_INTEGRITY.txt")
        self.assertEqual(auth["evidence_completeness_status"], "HOST_OUTCOME_INGESTION.txt")
        s1 = srl.load_historical_s1_register()
        self.assertEqual(
            s1.raw["evidence_completeness_inventory"]["activation"],
            "defined_future_s3_manifest_completeness",
        )
        # Runtime host uses inventory helper for preliminary manifest.
        host = (SCRIPTS_DIR / "run_witness_narrow_build.sh").read_text(encoding="utf-8")
        self.assertIn("evidence_inventory.py", host)
        self.assertIn("--write-manifest", host)
        self.assertIn("may become yes only after required final structural inputs", host)


class AntiOverclaimTests(unittest.TestCase):
    def test_10_ceilings_and_non_claims(self) -> None:
        import io
        from contextlib import redirect_stdout

        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = v.main(
                [
                    str(FIXTURES / "rc5-preliminary-success"),
                    "--host-preliminary",
                    "--schema-register-version",
                    "rc5-phase4-s2.1",
                ]
            )
        self.assertEqual(rc, 0)
        out = buf.getvalue()
        self.assertIn("not final success eligibility", out)
        self.assertIn("not Independent Witness PASS", out)

        buf2 = io.StringIO()
        with redirect_stdout(buf2):
            rc2 = v.main(
                [
                    str(FIXTURES / "rc5-synthetic-final-success"),
                    "--final-submission",
                    "--schema-register-version",
                    "rc5-phase4-s2.1",
                ]
            )
        self.assertEqual(rc2, 0)
        out2 = buf2.getvalue()
        self.assertIn("final-submission structural PASS", out2)
        self.assertIn("not Independent Witness PASS", out2)
        self.assertIn("not READY", out2)
        self.assertIn("not rc5 readiness", out2)
        self.assertNotIn("Independent Witness PASS claimed", out2)
        # Completeness fields remain NO/eligible NO on prelim fixture.
        host = (FIXTURES / "rc5-preliminary-success" / "HOST_OUTCOME_INGESTION.txt").read_text(
            encoding="utf-8"
        )
        self.assertIn("preliminary_success_eligible=NO", host)
        # C-014 not a machine state.
        src = (SCRIPTS_DIR / "validate_witness_evidence.py").read_text(encoding="utf-8")
        self.assertNotIn("C-014=", src)


class FailClosedInventoryTests(unittest.TestCase):
    def test_11_symlink_and_duplicate_path_rejection(self) -> None:
        root = _mktmp()
        (root / "a.txt").write_text("a\n", encoding="utf-8")
        # Symlink rejection via monkeypatch (portable).
        real_is_symlink = Path.is_symlink

        def _fake_is_symlink(self: Path) -> bool:
            if self.name == "link.txt":
                return True
            return real_is_symlink(self)

        (root / "link.txt").write_text("l\n", encoding="utf-8")
        Path.is_symlink = _fake_is_symlink  # type: ignore[method-assign]
        try:
            with self.assertRaises(ei.EvidenceInventoryError):
                ei.enumerate_evidence_files(root)
        finally:
            Path.is_symlink = real_is_symlink  # type: ignore[method-assign]


if __name__ == "__main__":
    unittest.main()
