#!/usr/bin/env python3
"""RC6-R3 focused tests: provenance tuple, final binding, schema evolution.

Uses only the Python standard library and local controlled temporary directories.
Does not invoke Docker, Cargo, compilers, product binaries, network, or Witness
workflows. Synthetic only — not Independent Witness evidence.
"""

from __future__ import annotations

import hashlib
import re
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

import evidence_inventory as ei  # noqa: E402
import schema_register_loader as srl  # noqa: E402
import validate_witness_evidence as v  # noqa: E402

RC6_REGISTER = PACKAGE_DIR / "schemas" / "canonical_schema_register_rc6.json"
RC61_REGISTER = PACKAGE_DIR / "schemas" / "canonical_schema_register_rc6.1.json"
FIXTURES = TESTS_DIR / "fixtures"
HOST_SCRIPT = SCRIPTS_DIR / "run_witness_narrow_build.sh"
CONTAINER_SCRIPT = SCRIPTS_DIR / "container_narrow_build.sh"

_TEMPS: list[Path] = []


def _mktmp(prefix: str = "rc6r3_test_") -> Path:
    path = Path(tempfile.mkdtemp(prefix=prefix, dir=str(TESTS_DIR)))
    _TEMPS.append(path)
    return path


def _cleanup() -> None:
    for path in _TEMPS:
        if path.exists():
            shutil.rmtree(path, ignore_errors=True)
    _TEMPS.clear()
    for path in TESTS_DIR.glob("rc6r3_test_*"):
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)


def _copy_fixture(name: str) -> Path:
    src = FIXTURES / name
    dst = _mktmp()
    # Replace empty temp dir with a full copy of the fixture tree.
    shutil.rmtree(dst)
    shutil.copytree(src, dst)
    return dst


class Rc6R3SchemaAuthorityTests(unittest.TestCase):
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
        self.assertEqual(v.SCHEMA_REGISTER_VERSION, "rc6.4")
        self.assertEqual(active.supersession().get("supersedes"), "rc6.3")
        hist = active.historical_compatibility()
        self.assertEqual(hist.get("active_authority"), "rc6.4")
        self.assertEqual(hist.get("immediate_predecessor_version"), "rc6.3")
        self.assertEqual(
            set(hist.get("historical_register_versions") or []),
            {"rc6.3", "rc6.2", "rc6.1", "rc5-phase4-s2.1", "rc5-phase4-s1.1"},
        )

    def test_02_historical_rc61_s2_s1_explicit_only(self) -> None:
        rc61 = srl.load_historical_register("rc6.1")
        s2 = srl.load_historical_register("rc5-phase4-s2.1")
        s1 = srl.load_historical_register("rc5-phase4-s1.1")
        self.assertTrue(rc61.is_historical_rc61)
        self.assertFalse(rc61.is_active_authority)
        self.assertEqual(rc61.source_path.resolve(), RC61_REGISTER.resolve())
        self.assertTrue(s2.is_historical_s2)
        self.assertTrue(s1.is_historical_s1)
        with self.assertRaises(srl.SchemaRegisterError):
            srl.load_historical_register("rc6.4")
        with self.assertRaises(srl.SchemaRegisterError):
            srl.load_historical_register("rc7.0")

    def test_03_one_active_register_file(self) -> None:
        active_files = list((PACKAGE_DIR / "schemas").glob("canonical_schema_register_rc6.json"))
        self.assertEqual(len(active_files), 1)
        self.assertTrue(RC61_REGISTER.is_file())
        frozen = RC61_REGISTER.read_bytes()
        self.assertIn(b'"schema_register_version": "rc6.1"', frozen)
        active = RC6_REGISTER.read_text(encoding="utf-8")
        self.assertIn('"schema_register_version": "rc6.4"', active)
        self.assertIn("WEAVER_FORGE_FINAL_BINDING.txt", active)

    def test_04_active_fixtures_pass_historical_bytes_preserved(self) -> None:
        self.assertEqual(
            v.validate_dir(FIXTURES / "rc6-r3-synthetic-final", schema_register_version="rc6.3"),
            [],
        )
        self.assertEqual(
            v.validate_dir(
                FIXTURES / "rc6-r3-synthetic-preliminary",
                host_preliminary=True,
                schema_register_version="rc6.3",
            ),
            [],
        )
        self.assertEqual(v.validate_dir(FIXTURES / "rc6-r5-synthetic-final"), [])
        self.assertEqual(
            v.validate_dir(FIXTURES / "rc6-r5-synthetic-preliminary", host_preliminary=True),
            [],
        )
        hist_pkg = (FIXTURES / "rc6-r1-synthetic-final" / "WEAVER_FORGE_PACKAGE_IDENTITY.txt").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("weaver_forge_tag_object_id", hist_pkg)
        # Non-R3 evidence must not auto-downgrade under default/active validation.
        active_r1 = v.validate_dir(FIXTURES / "rc6-r1-synthetic-final")
        self.assertTrue(any("WEAVER_FORGE_FINAL_BINDING.txt" in e for e in active_r1), active_r1)
        active_hist = v.validate_dir(FIXTURES / "success-artifact-present")
        self.assertTrue(any("WEAVER_FORGE_FINAL_BINDING.txt" in e for e in active_hist), active_hist)
        # Explicit historical loader paths remain compatible; fixture bytes unchanged.
        self.assertEqual(
            v.validate_dir(FIXTURES / "rc6-r1-synthetic-final", schema_register_version="rc6.1"),
            [],
        )
        self.assertEqual(
            v.validate_dir(FIXTURES / "success-artifact-present", schema_register_version="rc6.1"),
            [],
        )
        self.assertEqual(
            v.validate_dir(
                FIXTURES / "rc5-synthetic-final-success",
                schema_register_version="rc5-phase4-s2.1",
            ),
            [],
        )


class Rc6R3ProvenanceBindingTests(unittest.TestCase):
    def tearDown(self) -> None:
        _cleanup()

    def test_05_final_binding_manifest_hash_and_non_circular(self) -> None:
        tree = _copy_fixture("rc6-r5-synthetic-final")
        man = tree / "EVIDENCE_MANIFEST.sha256"
        fb = tree / "WEAVER_FORGE_FINAL_BINDING.txt"
        expected = hashlib.sha256(man.read_bytes()).hexdigest()
        text = fb.read_text(encoding="utf-8")
        self.assertIn(f"final_manifest_sha256={expected}", text)
        listed = man.read_text(encoding="utf-8")
        self.assertNotIn("WEAVER_FORGE_FINAL_BINDING.txt", listed)
        self.assertNotIn("EVIDENCE_MANIFEST.sha256\n", listed.replace("  ./EVIDENCE_MANIFEST.sha256", ""))
        # inventory helper excludes final binding
        lines = ei.build_manifest_lines(tree)
        self.assertTrue(all("WEAVER_FORGE_FINAL_BINDING.txt" not in ln for ln in lines))
        self.assertEqual(v.validate_dir(tree), [])

    def test_06_manifest_hash_mismatch_fail_closed(self) -> None:
        tree = _copy_fixture("rc6-r5-synthetic-final")
        fb = tree / "WEAVER_FORGE_FINAL_BINDING.txt"
        text = fb.read_text(encoding="utf-8")
        text = re.sub(
            r"^final_manifest_sha256=.*$",
            "final_manifest_sha256=" + ("a" * 64),
            text,
            flags=re.M,
        )
        fb.write_text(text, encoding="utf-8", newline="\n")
        errors = v.validate_dir(tree)
        self.assertTrue(any("final_manifest_sha256" in e for e in errors), errors)

    def test_07_missing_final_binding_fail_closed_for_r3(self) -> None:
        tree = _copy_fixture("rc6-r5-synthetic-final")
        (tree / "WEAVER_FORGE_FINAL_BINDING.txt").unlink()
        errors = v.validate_dir(tree)
        self.assertTrue(any("WEAVER_FORGE_FINAL_BINDING.txt" in e for e in errors), errors)

    def test_08_run_id_mismatch_fail_closed(self) -> None:
        tree = _copy_fixture("rc6-r5-synthetic-final")
        be = tree / "BUILD_EXIT_CODE.txt"
        text = be.read_text(encoding="utf-8")
        text = re.sub(r"^run_id=.*$", "run_id=other-run-id-token", text, flags=re.M)
        be.write_text(text, encoding="utf-8", newline="\n")
        # rebuild final binding? not needed — cross-bind should fail first
        errors = v.validate_dir(tree)
        self.assertTrue(any("run_id" in e for e in errors), errors)

    def test_09_source_commit_mismatch_fail_closed(self) -> None:
        tree = _copy_fixture("rc6-r5-synthetic-final")
        src = tree / "SOURCE_IDENTITY.txt"
        text = src.read_text(encoding="utf-8")
        text = re.sub(
            r"^grok_build_commit_observed=.*$",
            "grok_build_commit_observed=" + ("b" * 40),
            text,
            flags=re.M,
        )
        src.write_text(text, encoding="utf-8", newline="\n")
        errors = v.validate_dir(tree)
        self.assertTrue(any("grok_build_commit" in e for e in errors), errors)

    def test_10_mechanical_manual_form_refs(self) -> None:
        stmt = (FIXTURES / "rc6-r3-synthetic-final" / "WITNESS_STATEMENT.md").read_text(
            encoding="utf-8"
        )
        verd = (FIXTURES / "rc6-r3-synthetic-final" / "WITNESS_VERDICT.md").read_text(
            encoding="utf-8"
        )
        for text in (stmt, verd):
            self.assertIn("run_id=run-rc6-r3-schema-synthetic-001", text)
            self.assertIn("package_identity_ref=WEAVER_FORGE_PACKAGE_IDENTITY.txt", text)
            self.assertIn("final_binding_ref=WEAVER_FORGE_FINAL_BINDING.txt", text)

    def test_11_host_container_source_echo_and_no_fallback(self) -> None:
        host = HOST_SCRIPT.read_text(encoding="utf-8")
        container = CONTAINER_SCRIPT.read_text(encoding="utf-8")
        self.assertIn('-e RUN_ID="${RUN_ID}"', host)
        self.assertIn("missing_run_id", host)
        self.assertIn("mismatch_run_id", host)
        self.assertNotIn('PARSED_RUN_ID="${RUN_ID}"', host)
        self.assertNotIn("PARSED_RUN_ID:-${RUN_ID", host)
        self.assertIn("container_run_id=${PARSED_RUN_ID}", host)
        self.assertIn("run_id=${RUN_ID}", host)
        self.assertIn("run_id=${RUN_ID}", container)
        self.assertIn("run_id_validation", container)
        self.assertIn("is_safe_token", container)
        self.assertIn("write_weaver_forge_final_binding", host)
        self.assertIn("weaver_forge_tag_object_id", host)
        self.assertIn("authoritative_outcome=", host)

    def test_12_evidence_cannot_select_historical_authority(self) -> None:
        tree = _copy_fixture("rc6-r5-synthetic-final")
        env = tree / "ENVIRONMENT.txt"
        env.write_text(
            env.read_text(encoding="utf-8") + "schema_register_version=rc6.1\n",
            encoding="utf-8",
            newline="\n",
        )
        errors = v.validate_dir(tree)
        self.assertEqual(v.SCHEMA_REGISTER_VERSION, "rc6.4")
        self.assertTrue(any("schema_register_version" in e for e in errors), errors)

    def test_13_default_validation_never_selects_rc61_by_shape(self) -> None:
        # Omitting R3 markers must fail under active rc6.4 — not silently use rc6.1.
        tree = _copy_fixture("rc6-r1-synthetic-final")
        self.assertFalse(v.package_is_r3_shaped({}, evidence_dir=tree))
        errors = v.validate_dir(tree)
        self.assertTrue(any("WEAVER_FORGE_FINAL_BINDING.txt" in e for e in errors), errors)
        # Explicit historical API still accepts the same bytes.
        self.assertEqual(v.validate_dir(tree, schema_register_version="rc6.1"), [])
        # Active version cannot be requested through the historical API.
        reject_active = v.validate_dir(tree, schema_register_version="rc6.4")
        self.assertTrue(any("active authority" in e for e in reject_active), reject_active)
        unsupported = v.validate_dir(tree, schema_register_version="rc7.0")
        self.assertTrue(any("unsupported schema_register_version" in e for e in unsupported), unsupported)

    def test_14_host_finalization_order_metadata_before_manifest_seal(self) -> None:
        host = HOST_SCRIPT.read_text(encoding="utf-8")
        step21 = host.split("STEP 21:", 1)[1].split("STEP 21b", 1)[0]
        meta_pos = step21.find('append_host_run_metadata_entry "preliminary_manifest_generated"')
        bind_meta_pos = step21.find('append_host_run_metadata_entry "final_binding_written"')
        manifest_pos = step21.find("evidence_inventory.py")
        if manifest_pos < 0:
            manifest_pos = step21.find("EVIDENCE_MANIFEST.sha256")
        final_pos = step21.find("write_weaver_forge_final_binding")
        self.assertGreaterEqual(meta_pos, 0)
        self.assertGreaterEqual(bind_meta_pos, 0)
        self.assertGreater(manifest_pos, bind_meta_pos)
        self.assertGreater(manifest_pos, meta_pos)
        self.assertGreater(final_pos, manifest_pos)
        # No post-seal HOST_RUN_METADATA mutation in the finalization sequence.
        after_final = step21[final_pos:]
        self.assertNotIn("append_host_run_metadata_entry", after_final)
        # Isolated FM-C seal: mutate covered file after binding → validator fail-closed.
        tree = _copy_fixture("rc6-r5-synthetic-final")
        man = tree / "EVIDENCE_MANIFEST.sha256"
        expected = hashlib.sha256(man.read_bytes()).hexdigest()
        fb = (tree / "WEAVER_FORGE_FINAL_BINDING.txt").read_text(encoding="utf-8")
        self.assertIn(f"final_manifest_sha256={expected}", fb)
        meta = tree / "HOST_RUN_METADATA.txt"
        meta.write_text(meta.read_text(encoding="utf-8") + "\n# post-seal mutation\n", encoding="utf-8")
        errors = v.validate_dir(tree)
        self.assertTrue(
            any("EVIDENCE_MANIFEST" in e or "manifest" in e.lower() or "sha256" in e.lower() for e in errors),
            errors,
        )


if __name__ == "__main__":
    unittest.main()
