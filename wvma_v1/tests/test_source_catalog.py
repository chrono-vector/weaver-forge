"""B2 source-mutation byte contract. Does not execute product verifiers."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from wvma_v1.artifact_cases import CATALOG_PATH
from wvma_v1.mutations import MutationApplication
from wvma_v1.source_cases import (
    EQUIVALENT_MUTANT,
    HISTORICAL_C11_S2,
    PROBE_PATH,
    REPO_ROOT,
    REQUIRED_SOURCE_CASE_IDS,
    SOURCE_MUTATIONS,
    SourceApplyError,
    apply_source_mutation,
    classify_source_observation,
    exact_replace,
    git_blob_bytes,
    sha256_bytes,
    source_mutation,
)
from wvma_v1.workspace import export_tracked_tree

_SOURCE_CASE_IDS = ("C06-S1", "C06-S2", "C11-S1", "C11-S2")


class TestSourceByteContract(unittest.TestCase):
    def test_required_set_excludes_historical_c11_s2(self):
        self.assertEqual(REQUIRED_SOURCE_CASE_IDS, ("C06-S1", "C06-S2", "C11-S1"))
        self.assertEqual(tuple(spec.case_id for spec in SOURCE_MUTATIONS), REQUIRED_SOURCE_CASE_IDS)
        self.assertTrue(all(spec.critical for spec in SOURCE_MUTATIONS))
        self.assertFalse(HISTORICAL_C11_S2.critical)
        self.assertNotIn(HISTORICAL_C11_S2.case_id, REQUIRED_SOURCE_CASE_IDS)
        self.assertEqual(HISTORICAL_C11_S2.case_id, "C11-S2")

    def test_git_blobs_match_sealed_preimages_and_single_replacements(self):
        seen: set[str] = set()
        for spec in (*SOURCE_MUTATIONS, HISTORICAL_C11_S2):
            blob = git_blob_bytes(REPO_ROOT, spec.target_relative_path)
            self.assertEqual(sha256_bytes(blob), spec.preimage_sha256, spec.case_id)
            self.assertEqual(blob.count(spec.find), 1, spec.case_id)
            updated = exact_replace(blob, spec.find, spec.replace)
            self.assertEqual(sha256_bytes(updated), spec.postimage_sha256, spec.case_id)
            self.assertNotEqual(spec.preimage_sha256, spec.postimage_sha256)
            seen.add(spec.case_id)
        self.assertEqual(seen, set(_SOURCE_CASE_IDS))

    def test_zero_or_multiple_matches_are_apply_error(self):
        spec = source_mutation("C11-S1")
        with self.assertRaises(SourceApplyError) as zero:
            exact_replace(b"no-match", spec.find, spec.replace)
        self.assertIn("APPLY_ERROR", str(zero.exception))
        doubled = spec.find + spec.find
        with self.assertRaises(SourceApplyError) as many:
            exact_replace(doubled, spec.find, spec.replace)
        self.assertIn("match count 2", str(many.exception))
        with self.assertRaises(SourceApplyError) as empty:
            exact_replace(spec.find, b"", spec.replace)
        self.assertIn("empty find", str(empty.exception))

    def test_apply_uses_git_export_bytes_once(self):
        specs = (*SOURCE_MUTATIONS, HISTORICAL_C11_S2)
        pathspecs = tuple(sorted({spec.target_relative_path for spec in specs}))
        with tempfile.TemporaryDirectory(prefix="wvma-b2-bytes-") as td:
            dest = Path(td) / "export"
            dest.mkdir()
            export_tracked_tree(
                repo_root=REPO_ROOT,
                revision="HEAD",
                destination=dest,
                pathspecs=pathspecs,
            )
            for spec in specs:
                target = dest / spec.target_relative_path
                original = target.read_bytes()
                self.assertEqual(original, git_blob_bytes(REPO_ROOT, spec.target_relative_path))
                applied = apply_source_mutation(dest, spec)
                self.assertTrue(applied.applied)
                self.assertEqual(applied.operation_enum, "REPLACE_EXACT_BYTES")
                self.assertEqual(applied.preimage_sha256, spec.preimage_sha256)
                self.assertEqual(applied.postimage_sha256, spec.postimage_sha256)
                self.assertEqual(sha256_bytes(target.read_bytes()), spec.postimage_sha256)
                with self.assertRaises(SourceApplyError):
                    apply_source_mutation(dest, spec)
                target.write_bytes(original)

    def test_b1_catalog_does_not_absorb_source_cases(self):
        raw = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
        self.assertEqual(raw["catalog_id"], "WVMA-V1-ARTIFACT-B1")
        self.assertFalse(raw["authority"])
        mutations = raw["mutations"]
        self.assertEqual(len(mutations), 30)
        ids = {row["case_id"] for row in mutations}
        self.assertTrue(ids.isdisjoint(_SOURCE_CASE_IDS))


class TestSourceClassificationGuard(unittest.TestCase):
    def _application(self, case_id: str) -> MutationApplication:
        spec = source_mutation(case_id)
        return MutationApplication(
            case_id=spec.case_id,
            operation_enum="REPLACE_EXACT_BYTES",
            target_relative_path=spec.target_relative_path,
            preimage_sha256=spec.preimage_sha256,
            postimage_sha256=spec.postimage_sha256,
            applied=True,
        )

    def test_apply_error_classifies_apply_error(self):
        spec = source_mutation("C06-S1")
        result = classify_source_observation(
            spec,
            export_root=REPO_ROOT,
            application=None,
            baseline=None,
            mutant=None,
            apply_error=True,
        )
        self.assertEqual(result, "APPLY_ERROR")

    def test_unrelated_self_claimed_detected_is_not_detected(self):
        spec = source_mutation("C06-S1")
        with tempfile.TemporaryDirectory(prefix="wvma-b2-guard-") as td:
            export = Path(td)
            mutant = {
                "case_id": "UNRELATED",
                "observation": {
                    "entry_point": "strict_parse_r4b_expectation",
                    "accepted": True,
                    "digests": ["cd" * 32],
                    "error_type": None,
                },
                "unrelated_failure": True,
                "error": "unrelated_runtime_failure",
                "self_claimed_result": "DETECTED",
                "probe_exit_code": 0,
                "module_file": str(export / spec.target_relative_path),
                "probe_file": str(PROBE_PATH),
                "module_sha256": spec.postimage_sha256,
                "wvma_loaded_from_export": False,
            }
            baseline = {
                "observation": {
                    "accepted": False,
                    "error_type": "R4BExpectationError",
                }
            }
            result = classify_source_observation(
                spec,
                export_root=export,
                application=self._application(spec.case_id),
                baseline=baseline,
                mutant=mutant,
            )
        self.assertNotEqual(result, "DETECTED")
        self.assertEqual(result, "INVALID_MUTANT")
        self.assertNotEqual(result, EQUIVALENT_MUTANT)

    def test_probe_exception_is_not_detected(self):
        spec = source_mutation("C06-S2")
        with tempfile.TemporaryDirectory(prefix="wvma-b2-exec-") as td:
            result = classify_source_observation(
                spec,
                export_root=Path(td),
                application=self._application(spec.case_id),
                baseline={"observation": {}},
                mutant={
                    "case_id": spec.case_id,
                    "observation": None,
                    "error": "RuntimeError: boom",
                    "unrelated_failure": False,
                    "self_claimed_result": "DETECTED",
                    "probe_exit_code": 1,
                    "module_file": str(Path(td) / "missing.py"),
                    "probe_file": str(PROBE_PATH),
                    "module_sha256": spec.postimage_sha256,
                    "wvma_loaded_from_export": False,
                },
            )
        self.assertEqual(result, "EXECUTION_ERROR")
        self.assertNotEqual(result, "DETECTED")


if __name__ == "__main__":
    unittest.main()
