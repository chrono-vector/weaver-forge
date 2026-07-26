#!/usr/bin/env python3
"""RC6-R4 tests: typed nested classes and empty-directory rejection.

Uses only the Python standard library and local controlled temporary directories.
Does not invoke Docker, Cargo, compilers, product binaries, network, or Witness
workflows. Synthetic only — not Independent Witness evidence.
"""

from __future__ import annotations

import hashlib
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
RC62_REGISTER = PACKAGE_DIR / "schemas" / "canonical_schema_register_rc6.2.json"
FIXTURES = TESTS_DIR / "fixtures"
HOST_SCRIPT = SCRIPTS_DIR / "run_witness_narrow_build.sh"

_TEMPS: list[Path] = []


def _mktmp(prefix: str = "rc6r4_test_") -> Path:
    path = Path(tempfile.mkdtemp(prefix=prefix, dir=str(TESTS_DIR)))
    _TEMPS.append(path)
    return path


def _cleanup() -> None:
    for path in _TEMPS:
        if path.exists():
            shutil.rmtree(path, ignore_errors=True)
    _TEMPS.clear()
    for path in TESTS_DIR.glob("rc6r4_test_*"):
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)


def _copy_fixture(name: str) -> Path:
    src = FIXTURES / name
    dst = _mktmp()
    shutil.rmtree(dst)
    shutil.copytree(src, dst)
    return dst


def _support_record(
    *,
    class_id: str,
    purpose: str,
    owner: str,
    run_id: str,
    summary: str = "ok",
) -> str:
    return (
        "evidence_schema_version=1\n"
        f"class_id={class_id}\n"
        f"purpose={purpose}\n"
        f"owner={owner}\n"
        f"run_id={run_id}\n"
        "status=OK\n"
        f"summary={summary}\n"
    )


def _rebuild_seal(tree: Path) -> None:
    fb = tree / "WEAVER_FORGE_FINAL_BINDING.txt"
    if fb.exists():
        fb.unlink()
    classes = srl.load_active_register().nested_class_records()
    ei.write_evidence_manifest(tree, reject_empty_directories=True, nested_classes=classes)
    digest = hashlib.sha256((tree / "EVIDENCE_MANIFEST.sha256").read_bytes()).hexdigest()
    # Minimal final binding fields reused from fixture template when present.
    pkg = (tree / "WEAVER_FORGE_PACKAGE_IDENTITY.txt").read_text(encoding="utf-8")
    run_id = next(line.split("=", 1)[1] for line in pkg.splitlines() if line.startswith("run_id="))
    tag_object = next(
        line.split("=", 1)[1]
        for line in pkg.splitlines()
        if line.startswith("weaver_forge_tag_object_id=")
    )
    fb.write_text(
        (
            "evidence_schema_version=1\n"
            f"run_id={run_id}\n"
            f"tag_object_id={tag_object}\n"
            "evidence_manifest_ref=EVIDENCE_MANIFEST.sha256\n"
            f"final_manifest_sha256={digest}\n"
            "status=OK\n"
            "authoritative_outcome=CARGO_SUCCEEDED_ARTIFACT_PRESENT\n"
            "package_identity_ref=WEAVER_FORGE_PACKAGE_IDENTITY.txt\n"
            "source_identity_ref=SOURCE_IDENTITY.txt\n"
            "artifact_identity_ref=ARTIFACT_IDENTITY.txt\n"
            "post_build_integrity_ref=POST_BUILD_INTEGRITY.txt\n"
            "host_outcome_ingestion_ref=HOST_OUTCOME_INGESTION.txt\n"
            "build_exit_code_ref=BUILD_EXIT_CODE.txt\n"
        ),
        encoding="utf-8",
        newline="\n",
    )


class Rc6R4SchemaAuthorityTests(unittest.TestCase):
    def tearDown(self) -> None:
        _cleanup()

    def test_01_active_default_is_rc6_4(self) -> None:
        active = srl.load_active_register()
        self.assertEqual(active.schema_register_version, "rc6.5")
        self.assertEqual(v.SCHEMA_REGISTER_VERSION, "rc6.5")
        self.assertTrue(active.enforces_typed_nested_classes())
        self.assertTrue(active.enforces_empty_directory_rejection())
        self.assertEqual(
            {c["class_id"] for c in active.nested_class_records()},
            {"host_support_record", "container_support_record"},
        )

    def test_02_historical_rc62_explicit_only(self) -> None:
        hist = srl.load_historical_register("rc6.2")
        self.assertTrue(hist.is_historical_rc62)
        self.assertFalse(hist.enforces_typed_nested_classes())
        self.assertEqual(hist.source_path.resolve(), RC62_REGISTER.resolve())
        with self.assertRaises(srl.SchemaRegisterError):
            srl.load_historical_register("rc6.5")
        reject = v.validate_dir(FIXTURES / "rc6-r6-synthetic-final", schema_register_version="rc6.5")
        self.assertTrue(any("active authority" in e for e in reject), reject)

    def test_03_active_and_historical_fixtures(self) -> None:
        self.assertEqual(v.validate_dir(FIXTURES / "rc6-r6-synthetic-final"), [])
        self.assertEqual(
            v.validate_dir(FIXTURES / "rc6-r6-synthetic-preliminary", host_preliminary=True),
            [],
        )
        self.assertEqual(
            v.validate_dir(FIXTURES / "rc6-r4-synthetic-final", schema_register_version="rc6.3"),
            [],
        )
        self.assertEqual(
            v.validate_dir(
                FIXTURES / "rc6-r4-synthetic-preliminary",
                host_preliminary=True,
                schema_register_version="rc6.3",
            ),
            [],
        )
        # Historical rc6.2 semantics via explicit loader; r3 bytes unchanged.
        self.assertEqual(
            v.validate_dir(FIXTURES / "rc6-r3-synthetic-final", schema_register_version="rc6.2"),
            [],
        )
        hist_pkg = (FIXTURES / "rc6-r3-synthetic-final" / "WEAVER_FORGE_PACKAGE_IDENTITY.txt").read_bytes()
        self.assertTrue(hist_pkg)


class Rc6R4NestedClassTests(unittest.TestCase):
    def tearDown(self) -> None:
        _cleanup()

    def test_04_arbitrary_listed_hashed_nested_rejected(self) -> None:
        tree = _copy_fixture("rc6-r6-synthetic-final")
        nested = tree / "nested"
        nested.mkdir()
        (nested / "extra.txt").write_text("hello\n", encoding="utf-8", newline="\n")
        fb = tree / "WEAVER_FORGE_FINAL_BINDING.txt"
        old_fb = fb.read_text(encoding="utf-8") if fb.exists() else ""
        if fb.exists():
            fb.unlink()
        # Intentionally bypass class enforcement to create listed+hashed unauthorized nested file.
        ei.write_evidence_manifest(tree, reject_empty_directories=True, nested_classes=None)
        digest = hashlib.sha256((tree / "EVIDENCE_MANIFEST.sha256").read_bytes()).hexdigest()
        if "final_manifest_sha256=" in old_fb:
            fb.write_text(
                "\n".join(
                    f"final_manifest_sha256={digest}"
                    if line.startswith("final_manifest_sha256=")
                    else line
                    for line in old_fb.splitlines()
                )
                + "\n",
                encoding="utf-8",
                newline="\n",
            )
        else:
            _rebuild_seal(tree)
        errors = v.validate_dir(tree)
        self.assertTrue(
            any("Unauthorized nested" in e or "typed-class" in e or "typed class" in e for e in errors),
            errors,
        )

    def test_05_unknown_prefix_and_path_class_mismatch(self) -> None:
        tree = _copy_fixture("rc6-r6-synthetic-final")
        bad = tree / "unknown_prefix"
        bad.mkdir()
        (bad / "x.txt").write_text("a=b\n", encoding="utf-8", newline="\n")
        with self.assertRaises(ei.EvidenceInventoryError):
            ei.write_evidence_manifest(
                tree,
                reject_empty_directories=True,
                nested_classes=srl.load_active_register().nested_class_records(),
            )
        tree2 = _copy_fixture("rc6-r6-synthetic-final")
        run_id = next(
            line.split("=", 1)[1]
            for line in (tree2 / "WEAVER_FORGE_PACKAGE_IDENTITY.txt").read_text(encoding="utf-8").splitlines()
            if line.startswith("run_id=")
        )
        # Wrong class_id under host_support prefix.
        (tree2 / "host_support" / "aux_note.txt").write_text(
            _support_record(
                class_id="container_support_record",
                purpose="container_owned_supporting_nested_evidence",
                owner="container",
                run_id=run_id,
            ),
            encoding="utf-8",
            newline="\n",
        )
        _rebuild_seal(tree2)
        errors = v.validate_dir(tree2)
        self.assertTrue(any("class_id" in e for e in errors), errors)

    def test_06_malformed_class_content_and_run_id_binding(self) -> None:
        tree = _copy_fixture("rc6-r6-synthetic-final")
        (tree / "host_support" / "aux_note.txt").write_text(
            "evidence_schema_version=1\nclass_id=host_support_record\n",
            encoding="utf-8",
            newline="\n",
        )
        _rebuild_seal(tree)
        errors = v.validate_dir(tree)
        self.assertTrue(any("host_support/aux_note.txt" in e for e in errors), errors)

        tree2 = _copy_fixture("rc6-r6-synthetic-final")
        (tree2 / "host_support" / "aux_note.txt").write_text(
            _support_record(
                class_id="host_support_record",
                purpose="host_owned_supporting_nested_evidence",
                owner="host",
                run_id="other-run-id-token",
            ),
            encoding="utf-8",
            newline="\n",
        )
        _rebuild_seal(tree2)
        errors2 = v.validate_dir(tree2)
        self.assertTrue(any("run_id" in e for e in errors2), errors2)

    def test_07_manifest_missing_extra_nested_entries(self) -> None:
        tree = _copy_fixture("rc6-r6-synthetic-final")
        man = tree / "EVIDENCE_MANIFEST.sha256"
        lines = [ln for ln in man.read_text(encoding="utf-8").splitlines() if ln.strip()]
        # Drop nested entry.
        kept = [ln for ln in lines if "host_support/aux_note.txt" not in ln]
        man.write_text("\n".join(kept) + "\n", encoding="utf-8", newline="\n")
        errors = v.validate_dir(tree)
        self.assertTrue(any("host_support/aux_note.txt" in e for e in errors), errors)

        tree2 = _copy_fixture("rc6-r6-synthetic-final")
        man2 = tree2 / "EVIDENCE_MANIFEST.sha256"
        man2.write_text(
            man2.read_text(encoding="utf-8")
            + ("a" * 64)
            + "  ./host_support/ghost.txt\n",
            encoding="utf-8",
            newline="\n",
        )
        errors2 = v.validate_dir(tree2)
        self.assertTrue(
            any("ghost.txt" in e or "missing on disk" in e or "typed-class" in e for e in errors2),
            errors2,
        )


class Rc6R4EmptyDirectoryTests(unittest.TestCase):
    def tearDown(self) -> None:
        _cleanup()

    def test_08_empty_directory_rejected_before_manifest_and_validator(self) -> None:
        tree = _copy_fixture("rc6-r6-synthetic-final")
        (tree / "empty_child").mkdir()
        with self.assertRaises(ei.EvidenceInventoryError) as ctx:
            ei.write_evidence_manifest(
                tree,
                reject_empty_directories=True,
                nested_classes=srl.load_active_register().nested_class_records(),
            )
        self.assertIn("empty directory rejected", str(ctx.exception))

        tree2 = _copy_fixture("rc6-r6-synthetic-final")
        (tree2 / "host_support" / "empty_nested").mkdir()
        errors = v.validate_dir(tree2)
        self.assertTrue(any("Empty directory rejected" in e for e in errors), errors)

    def test_09_historical_empty_dir_not_enforced_under_rc62(self) -> None:
        tree = _copy_fixture("rc6-r3-synthetic-final")
        (tree / "empty_child").mkdir()
        # Historical rc6.2 validation does not apply R4-E1.
        errors = v.validate_dir(tree, schema_register_version="rc6.2")
        self.assertFalse(any("Empty directory" in e for e in errors), errors)

    def test_10_host_script_enforces_r4_inventory_flags(self) -> None:
        host = HOST_SCRIPT.read_text(encoding="utf-8")
        self.assertIn("--enforce-active-nested-classes", host)
        self.assertIn("empty directory", host.lower())
        self.assertIn("typed nested", host.lower())

    def test_11_r3_final_binding_and_exclusions_preserved(self) -> None:
        tree = _copy_fixture("rc6-r6-synthetic-final")
        man = (tree / "EVIDENCE_MANIFEST.sha256").read_text(encoding="utf-8")
        self.assertNotIn("WEAVER_FORGE_FINAL_BINDING.txt", man)
        self.assertNotIn("EVIDENCE_MANIFEST.sha256\n", man.replace("  ./EVIDENCE_MANIFEST.sha256", ""))
        expected = hashlib.sha256((tree / "EVIDENCE_MANIFEST.sha256").read_bytes()).hexdigest()
        fb = (tree / "WEAVER_FORGE_FINAL_BINDING.txt").read_text(encoding="utf-8")
        self.assertIn(f"final_manifest_sha256={expected}", fb)
        self.assertEqual(v.validate_dir(tree), [])

    def test_12_evidence_cannot_select_historical_authority(self) -> None:
        tree = _copy_fixture("rc6-r6-synthetic-final")
        env = tree / "ENVIRONMENT.txt"
        env.write_text(
            env.read_text(encoding="utf-8") + "schema_register_version=rc6.2\n",
            encoding="utf-8",
            newline="\n",
        )
        errors = v.validate_dir(tree)
        self.assertTrue(any("schema_register_version" in e for e in errors), errors)


if __name__ == "__main__":
    unittest.main()
