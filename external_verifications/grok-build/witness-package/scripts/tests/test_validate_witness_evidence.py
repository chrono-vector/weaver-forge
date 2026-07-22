"""Synthetic unit tests for validate_witness_evidence.py (no real Witness data)."""

import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from validate_witness_evidence import (
    EXACT_BUILD_CMD,
    EXPECTED_GROK_COMMIT,
    MANIFEST_NAME,
    REQUIRED_FILES,
    parse_verdict_selection,
    validate_dir,
)


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _write_manifest(root: Path) -> None:
    lines: list[str] = []
    for name in sorted(REQUIRED_FILES):
        if name == MANIFEST_NAME:
            continue
        path = root / name
        digest = _sha256_bytes(path.read_bytes())
        lines.append(f"{digest}  ./{name}")
    (root / MANIFEST_NAME).write_text("\n".join(lines) + "\n", encoding="utf-8")


def _minimal_valid_tree(root: Path, verdict_line: str = "Witness proposed verdict: INDETERMINATE\n") -> None:
    grok = EXPECTED_GROK_COMMIT
    digest = "6ca5ad23231207874325a751b9df584d51cd42c066c74c6963c264e3233c3e8e"
    wf = "89127c78c3a11492892de7e3b5f0dee18d71775a"
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
        "SOURCE_ACQUISITION.txt": f"weaver_forge_url=https://github.com/chrono-vector/weaver-forge.git\n{common}",
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
        "WITNESS_VERDICT.md": verdict_line,
    }
    for name, body in files.items():
        (root / name).write_text(body, encoding="utf-8")
    _write_manifest(root)


class ValidateWitnessEvidenceTests(unittest.TestCase):
    def test_minimal_synthetic_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _minimal_valid_tree(root)
            errors = validate_dir(root)
            self.assertEqual(errors, [])

    def test_missing_source_identity_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _minimal_valid_tree(root)
            (root / "SOURCE_IDENTITY.txt").unlink()
            errors = validate_dir(root)
            self.assertTrue(any("SOURCE_IDENTITY" in e for e in errors))

    def test_missing_source_acquisition_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _minimal_valid_tree(root)
            (root / "SOURCE_ACQUISITION.txt").unlink()
            errors = validate_dir(root)
            self.assertTrue(any("SOURCE_ACQUISITION" in e for e in errors))

    def test_missing_image_identity_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _minimal_valid_tree(root)
            (root / "IMAGE_IDENTITY.txt").unlink()
            errors = validate_dir(root)
            self.assertTrue(any("IMAGE_IDENTITY" in e for e in errors))

    def test_manifest_wrong_hash_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _minimal_valid_tree(root)
            manifest = root / MANIFEST_NAME
            text = manifest.read_text(encoding="utf-8")
            manifest.write_text(text.replace("a", "b", 1), encoding="utf-8")
            errors = validate_dir(root)
            self.assertTrue(any("hash mismatch" in e for e in errors))

    def test_manifest_missing_entry_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _minimal_valid_tree(root)
            lines = [
                ln
                for ln in (root / MANIFEST_NAME).read_text(encoding="utf-8").splitlines()
                if "DEVIATIONS.txt" not in ln
            ]
            (root / MANIFEST_NAME).write_text("\n".join(lines) + "\n", encoding="utf-8")
            errors = validate_dir(root)
            self.assertTrue(any("missing mandatory entry" in e for e in errors))

    def test_manifest_duplicate_entry_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _minimal_valid_tree(root)
            manifest = root / MANIFEST_NAME
            first = manifest.read_text(encoding="utf-8").splitlines()[0]
            manifest.write_text(first + "\n" + first + "\n", encoding="utf-8")
            errors = validate_dir(root)
            self.assertTrue(any("duplicate entry" in e for e in errors))

    def test_manifest_unsafe_path_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _minimal_valid_tree(root)
            manifest = root / MANIFEST_NAME
            line = manifest.read_text(encoding="utf-8").splitlines()[0]
            bad = line.rsplit(" ", 1)[0] + "  ../escape.txt"
            manifest.write_text(bad + "\n", encoding="utf-8")
            errors = validate_dir(root)
            self.assertTrue(any("unsafe" in e for e in errors))

    def test_verdict_one_valid(self) -> None:
        text = "Witness proposed verdict: PASS\n"
        matches, errs = parse_verdict_selection(text)
        self.assertEqual(matches, ["PASS"])
        self.assertEqual(errs, [])

    def test_verdict_missing_selection(self) -> None:
        text = "Discussion: PASS might apply but not selected.\n"
        _, errs = parse_verdict_selection(text)
        self.assertTrue(errs)

    def test_verdict_duplicate_selection(self) -> None:
        text = "Witness proposed verdict: PASS\nWitness proposed verdict: FAIL\n"
        matches, errs = parse_verdict_selection(text)
        self.assertEqual(len(matches), 2)
        self.assertTrue(any("Duplicate" in e for e in errs))

    def test_verdict_invalid_value(self) -> None:
        text = "Witness proposed verdict: MAYBE\n"
        matches, errs = parse_verdict_selection(text)
        self.assertEqual(len(matches), 1)
        self.assertTrue(any("Invalid" in e for e in errs))


if __name__ == "__main__":
    unittest.main()
