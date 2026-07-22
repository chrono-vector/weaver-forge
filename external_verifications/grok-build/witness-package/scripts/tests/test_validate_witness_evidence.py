"""Synthetic unit tests for validate_witness_evidence.py (no real Witness data)."""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from validate_witness_evidence import EXACT_BUILD_CMD, EXPECTED_GROK_COMMIT, validate_dir


def _minimal_valid_tree(root: Path) -> None:
    grok = EXPECTED_GROK_COMMIT
    digest = "6ca5ad23231207874325a751b9df584d51cd42c066c74c6963c264e3233c3e8e"
    wf = "0aaae298f0e543d4042302224ed075c1796a6016"
    common = f"""
product_executed=NO
ldd_used=NO
CARGO_INCREMENTAL=0
{EXACT_BUILD_CMD}
cargo_incremental=0
grok_build_commit={grok}
image_digest=sha256:{digest}
"""
    files = {
        "WEAVER_FORGE_PACKAGE_IDENTITY.txt": f"weaver_forge_commit_resolved={wf}\n{common}",
        "SOURCE_IDENTITY.txt": f"grok_build_commit_observed={grok}\n{common}",
        "IMAGE_IDENTITY.txt": f"repo_digest=sha256:{digest}\n{common}",
        "ENVIRONMENT.txt": common,
        "BOOTSTRAP.txt": common,
        "CLEAN_TARGET_PROOF.txt": "required_entry_count=0\nobserved_entry_count=0\n" + common,
        "BUILD_COMMAND.txt": common,
        "BUILD_ENVIRONMENT.txt": common,
        "BUILD_STDOUT.txt": "synthetic\n",
        "BUILD_STDERR.txt": "synthetic\n",
        "BUILD_EXIT_CODE.txt": "cargo_started=YES\n0\n" + common,
        "BUILD_TIMING.txt": common,
        "CONTAINER_STDOUT.txt": "synthetic\n",
        "CONTAINER_STDERR.txt": "synthetic\n",
        "DOCKER_EXIT_CODE.txt": "0\n",
        "ARTIFACT_IDENTITY.txt": common,
        "STATIC_ARTIFACT_INSPECTION.txt": common,
        "POST_BUILD_INTEGRITY.txt": common,
        "DEVIATIONS.txt": "none\n",
        "REDACTIONS.md": "# none\n",
        "WITNESS_STATEMENT.md": "independence=yes\n",
        "WITNESS_VERDICT.md": "proposed_verdict=INDETERMINATE\n",
        "EVIDENCE_MANIFEST.sha256": "a" * 64 + "  ./WITNESS_STATEMENT.md\n",
    }
    for name, body in files.items():
        (root / name).write_text(body, encoding="utf-8")


class ValidateWitnessEvidenceTests(unittest.TestCase):
    def test_minimal_synthetic_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _minimal_valid_tree(root)
            errors = validate_dir(root)
            self.assertEqual(errors, [])

    def test_missing_file_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _minimal_valid_tree(root)
            (root / "SOURCE_IDENTITY.txt").unlink()
            errors = validate_dir(root)
            self.assertTrue(any("SOURCE_IDENTITY" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
