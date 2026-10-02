"""B2 integrated acceptance for the three non-equivalent source mutants.

The historical C11-S2 deletion is executed only to record equivalence.
It is not a required critical kill.
"""

from __future__ import annotations

import hashlib
import subprocess
import unittest
from pathlib import Path

from wvma_v1.source_cases import (
    EQUIVALENT_MUTANT,
    HISTORICAL_C11_S2,
    REPO_ROOT,
    REQUIRED_SOURCE_CASE_IDS,
    SourceCaseOutcome,
    record_c11_s2_equivalence,
    run_required_case,
    run_unrelated_failure,
    source_mutation,
)

_PROTECTED = (
    REPO_ROOT / "audit_lifecycle",
    REPO_ROOT / "campaign_runner_v0",
    REPO_ROOT / "aurora_audit",
    REPO_ROOT / "docs" / "next" / "CODEX_WEAVER_VERIFIER_MUTATION_ASSURANCE_V1_PLAN_20260929.md",
    REPO_ROOT / "docs" / "next" / "CODEX_WVMA_V1_ARCHITECTURE_AMENDMENT_20260929.md",
    REPO_ROOT
    / "docs"
    / "next"
    / "CODEX_WVMA_V1_C11_EQUIVALENT_MUTANT_AMENDMENT_20261002.md",
    REPO_ROOT / "wvma_v1" / "catalogs" / "WVMA_V1_CATALOG.json",
)
_ALLOWED_UNTRACKED = {
    "wvma_v1/source_cases.py",
    "wvma_v1/source_probe.py",
    "wvma_v1/tests/test_source_catalog.py",
    "wvma_v1/tests/test_integrated_wvma.py",
}
_INVENTORY: dict[str, str] | None = None


def _git_status_lines() -> list[str]:
    proc = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "status", "--porcelain"],
        check=True,
        capture_output=True,
        text=True,
    )
    return [line for line in proc.stdout.splitlines() if line.strip()]


def _assert_only_b2_additions() -> None:
    lines = _git_status_lines()
    unexpected = []
    for line in lines:
        # Porcelain is XY<space>path. Untracked additions are "??".
        if not line.startswith("??"):
            unexpected.append(line)
            continue
        path = line[3:].replace("\\", "/")
        if path not in _ALLOWED_UNTRACKED:
            unexpected.append(line)
    if unexpected:
        raise AssertionError(f"worktree changed outside B2 additions: {lines}")
    diff = subprocess.run(
        [
            "git",
            "-C",
            str(REPO_ROOT),
            "diff",
            "--exit-code",
            "--",
            "audit_lifecycle",
            "campaign_runner_v0",
            "aurora_audit",
            "docs/next",
            "wvma_v1",
        ],
        capture_output=True,
    )
    if diff.returncode != 0:
        text = diff.stdout.decode("utf-8", errors="replace")[:500]
        raise AssertionError(f"tracked diff outside B2 additions: {text}")


def _inventory(paths: tuple[Path, ...]) -> dict[str, str]:
    """Hash protected files, including names outside the WVMA path grammar."""
    out: dict[str, str] = {}
    for raw in paths:
        if raw.is_file():
            out[raw.relative_to(REPO_ROOT).as_posix()] = hashlib.sha256(raw.read_bytes()).hexdigest()
            continue
        for path in sorted(raw.rglob("*")):
            if not path.is_file():
                continue
            if "__pycache__" in path.parts or path.suffix == ".pyc":
                continue
            rel = path.relative_to(REPO_ROOT).as_posix()
            out[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
    return out


def setUpModule() -> None:
    global _INVENTORY
    _INVENTORY = _inventory(_PROTECTED)


def tearDownModule() -> None:
    if _INVENTORY is None:
        raise AssertionError("protected inventory was not snapshotted")
    current = _inventory(_PROTECTED)
    if current != _INVENTORY:
        missing = sorted(set(_INVENTORY) - set(current))
        added = sorted(set(current) - set(_INVENTORY))
        changed = sorted(
            key for key in set(_INVENTORY) & set(current) if _INVENTORY[key] != current[key]
        )
        raise AssertionError(
            f"protected inventory changed missing={missing[:5]} added={added[:5]} changed={changed[:8]}"
        )


class TestIntegratedSourceAcceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _assert_only_b2_additions()

    @classmethod
    def tearDownClass(cls):
        _assert_only_b2_additions()
        if _INVENTORY is None:
            raise AssertionError("protected inventory was not snapshotted")
        if _inventory(_PROTECTED) != _INVENTORY:
            raise AssertionError("protected inventory changed during integrated acceptance")

    def _assert_detected(self, case_id: str) -> SourceCaseOutcome:
        outcome = run_required_case(case_id)
        spec = source_mutation(case_id)
        self.assertEqual(outcome.result_class, "DETECTED", outcome.detail)
        self.assertTrue(outcome.property_violated, outcome.detail)
        self.assertTrue(outcome.module_inside_export, outcome.detail)
        self.assertFalse(outcome.probe_inside_export, outcome.detail)
        self.assertFalse(outcome.wvma_loaded_from_export, outcome.detail)
        self.assertEqual(outcome.module_sha256, spec.postimage_sha256, outcome.detail)
        self.assertIsNone(outcome.equivalent_label)
        return outcome

    def test_c06_s1_detected_from_mutated_export(self):
        self._assert_detected("C06-S1")

    def test_c06_s2_detected_from_mutated_export(self):
        self._assert_detected("C06-S2")

    def test_c11_s1_detected_from_mutated_export(self):
        self._assert_detected("C11-S1")

    def test_historical_c11_s2_is_equivalent_and_excluded(self):
        outcome = record_c11_s2_equivalence()
        self.assertEqual(outcome.case_id, "C11-S2")
        self.assertEqual(outcome.equivalent_label, EQUIVALENT_MUTANT)
        self.assertEqual(outcome.result_class, "INVALID_MUTANT", outcome.detail)
        self.assertNotEqual(outcome.result_class, "DETECTED")
        self.assertFalse(outcome.property_violated)
        self.assertFalse(HISTORICAL_C11_S2.critical)
        self.assertNotIn("C11-S2", REQUIRED_SOURCE_CASE_IDS)
        self.assertEqual(REQUIRED_SOURCE_CASE_IDS, ("C06-S1", "C06-S2", "C11-S1"))
        self.assertTrue(outcome.module_inside_export, outcome.detail)
        self.assertFalse(outcome.wvma_loaded_from_export)
        self.assertEqual(outcome.module_sha256, HISTORICAL_C11_S2.postimage_sha256)

    def test_unrelated_failure_cannot_be_detected(self):
        outcome = run_unrelated_failure()
        self.assertNotEqual(outcome.result_class, "DETECTED", outcome.detail)
        self.assertFalse(outcome.property_violated)
        self.assertFalse(outcome.wvma_loaded_from_export, outcome.detail)
        self.assertEqual(outcome.result_class, "INVALID_MUTANT", outcome.detail)


if __name__ == "__main__":
    unittest.main()
