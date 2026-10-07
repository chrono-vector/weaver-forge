from __future__ import annotations

import hashlib
import json
import socket
import subprocess
import tempfile
import unittest
import urllib.request
from pathlib import Path
from unittest import mock

from tools.wacp import generator as wacp


class WACPTests(unittest.TestCase):
    def setUp(self) -> None:
        self._temporary = tempfile.TemporaryDirectory(prefix="wacp-001-")
        self.sandbox = Path(self._temporary.name)
        self.root = self.sandbox / "repo"
        self.root.mkdir()
        self._git("init", "-q")
        self._git("config", "user.email", "wacp@example.invalid")
        self._git("config", "user.name", "WACP Test")
        self._write("scope/a.txt", b"base\n")
        self._write("scope/status.md", b"69/69 PASS\n")
        self._write("other.txt", b"unchanged\n")
        self.base = self._commit("base")
        self._write("scope/a.txt", b"head\n")
        self.head = self._commit("head")
        self._counter = 0

    def tearDown(self) -> None:
        self._temporary.cleanup()

    def _git(self, *arguments: str, input_bytes: bytes | None = None) -> str:
        result = subprocess.run(
            ["git", *arguments], cwd=self.root, input=input_bytes,
            capture_output=True, text=input_bytes is None, check=False,
        )
        if result.returncode:
            stderr = result.stderr if isinstance(result.stderr, str) else result.stderr.decode()
            self.fail(stderr)
        stdout = result.stdout if isinstance(result.stdout, str) else result.stdout.decode()
        return stdout.strip()

    def _write(self, path: str, content: bytes) -> None:
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)

    def _commit(self, message: str) -> str:
        self._git("add", "-A")
        self._git("commit", "-q", "-m", message)
        return self._git("rev-parse", "HEAD")

    def _manifest(self, **updates) -> dict:
        value = {
            "schema_version": wacp.SCHEMA_VERSION,
            "scope_id": "WACP-TEST",
            "base": self.base,
            "head": self.head,
            "review_mode": "independent_review",
            "include": ["scope/**"],
            "exclude": [],
            "max_bytes": 100_000,
            "clean_worktree_required": True,
        }
        value.update(updates)
        return value

    def _generate(self, manifest: dict | bytes | None = None, *, output_name: str | None = None):
        self._counter += 1
        manifest_path = self.sandbox / f"manifest-{self._counter}.json"
        if isinstance(manifest, bytes):
            manifest_path.write_bytes(manifest)
        else:
            manifest_path.write_text(json.dumps(manifest or self._manifest()), encoding="utf-8")
        output = self.sandbox / (output_name or f"pack-{self._counter}")
        return wacp.generate_pack(self.root, manifest_path, output), output

    def _pack_manifest(self, output: Path) -> dict:
        return json.loads((output / "PACK_MANIFEST.json").read_text(encoding="utf-8"))

    def _assert_mutant_killed(self, expected, actual) -> None:
        with self.assertRaises(AssertionError):
            self.assertEqual(expected, actual)

    def test_normal_pack_ready_generation(self) -> None:
        result, output = self._generate()
        self.assertEqual("PACK_READY", result.status)
        self.assertEqual(set(wacp.ARTIFACT_NAMES), {path.name for path in output.iterdir()})

    def test_exact_base_head_binding(self) -> None:
        _result, output = self._generate()
        manifest = self._pack_manifest(output)
        self.assertEqual(self.base, manifest["base_sha"])
        self.assertEqual(self.head, manifest["head_sha"])
        self.assertEqual("BASE_IS_ANCESTOR", manifest["base_head_relationship"])

    def test_missing_base_is_invalid(self) -> None:
        result, _ = self._generate(self._manifest(base="f" * 40))
        self.assertEqual("INVALID", result.status)

    def test_missing_head_is_invalid(self) -> None:
        result, _ = self._generate(self._manifest(head="e" * 40))
        self.assertEqual("INVALID", result.status)

    def test_malformed_manifest_is_invalid(self) -> None:
        result, _ = self._generate(b"{")
        self.assertEqual("INVALID", result.status)

    def test_path_traversal_is_invalid(self) -> None:
        result, _ = self._generate(self._manifest(include=["../scope/a.txt"]))
        self.assertEqual("INVALID", result.status)

    def test_absolute_paths_are_invalid(self) -> None:
        for path in ["/scope/a.txt", "C:/scope/a.txt", "scope\\a.txt"]:
            with self.subTest(path=path):
                result, _ = self._generate(self._manifest(include=[path]))
                self.assertEqual("INVALID", result.status)

    def test_selected_symlink_is_invalid(self) -> None:
        blob = self._git("hash-object", "-w", "--stdin", input_bytes=b"scope/a.txt")
        self._git("update-index", "--add", "--cacheinfo", f"120000,{blob},scope/link")
        self._git("commit", "-q", "-m", "symlink")
        self.head = self._git("rev-parse", "HEAD")
        result, _ = self._generate(self._manifest(include=["scope/link"]))
        self.assertEqual("INVALID", result.status)

    def test_duplicate_normalized_path_is_invalid(self) -> None:
        result, _ = self._generate(self._manifest(include=["scope/a.txt", "scope/a.txt"]))
        self.assertEqual("INVALID", result.status)

    def test_unmatched_include_is_invalid(self) -> None:
        result, _ = self._generate(self._manifest(include=["missing/**"]))
        self.assertEqual("INVALID", result.status)

    def test_unmatched_exclude_is_allowed(self) -> None:
        result, _ = self._generate(self._manifest(exclude=["missing/**"]))
        self.assertEqual("PACK_READY", result.status)

    def test_out_of_scope_changed_file_is_incomplete(self) -> None:
        self._write("other.txt", b"changed\n")
        self.head = self._commit("other change")
        result, output = self._generate()
        self.assertEqual("PACK_INCOMPLETE", result.status)
        self.assertEqual(["other.txt"], self._pack_manifest(output)["out_of_scope_changed_files"])

    def test_excluded_changed_file_is_incomplete(self) -> None:
        result, output = self._generate(self._manifest(exclude=["scope/a.txt"]))
        self.assertEqual("PACK_INCOMPLETE", result.status)
        self.assertEqual(["scope/a.txt"], self._pack_manifest(output)["excluded_changed_files"])

    def test_required_status_source_not_selected_is_incomplete(self) -> None:
        result, output = self._generate(self._manifest(required_status_files=["other.txt"]))
        self.assertEqual("PACK_INCOMPLETE", result.status)
        self.assertTrue(self._pack_manifest(output)["missing_required_sources"])

    def test_budget_exceeded_is_too_large_without_truncation(self) -> None:
        result, output = self._generate(self._manifest(max_bytes=1))
        self.assertEqual("PACK_TOO_LARGE", result.status)
        self.assertIn(b"-base", (output / "DIFF.patch").read_bytes())
        self.assertGreater(self._pack_manifest(output)["generated_byte_size"], 1)

    def test_deterministic_ordering(self) -> None:
        _result, output = self._generate(self._manifest(include=["scope/status.md", "scope/a.txt"]))
        self.assertEqual(["scope/a.txt", "scope/status.md"], self._pack_manifest(output)["selected_files"])

    def test_manifest_is_canonical_json(self) -> None:
        _result, output = self._generate()
        raw = (output / "PACK_MANIFEST.json").read_bytes()
        parsed = json.loads(raw)
        self.assertEqual(wacp._json_bytes(parsed), raw)

    def test_exact_sha256_inventory(self) -> None:
        _result, output = self._generate()
        manifest = self._pack_manifest(output)
        entry = next(item for item in manifest["selected_file_inventory"] if item["path"] == "scope/a.txt")
        self.assertEqual(hashlib.sha256(b"base\n").hexdigest(), entry["base_sha256"])
        self.assertEqual(hashlib.sha256(b"head\n").hexdigest(), entry["head_sha256"])
        for artifact in manifest["generated_artifact_inventory"]:
            content = (output / artifact["name"]).read_bytes()
            self.assertEqual(hashlib.sha256(content).hexdigest(), artifact["sha256"])

    def test_dirty_worktree_policy(self) -> None:
        self._write("dirty.txt", b"dirty\n")
        result, _ = self._generate()
        self.assertEqual("INVALID", result.status)
        result, _ = self._generate(self._manifest(clean_worktree_required=False))
        self.assertEqual("PACK_READY", result.status)

    def test_all_review_modes(self) -> None:
        for mode in sorted(wacp.REVIEW_MODES):
            with self.subTest(mode=mode):
                result, output = self._generate(self._manifest(review_mode=mode))
                self.assertEqual("PACK_READY", result.status)
                self.assertEqual(mode, self._pack_manifest(output)["review_mode"])

    def test_unrelated_file_is_excluded(self) -> None:
        _result, output = self._generate()
        manifest = self._pack_manifest(output)
        self.assertNotIn("other.txt", manifest["selected_files"])
        self.assertNotIn(b"other.txt", (output / "DIFF.patch").read_bytes())

    def test_claim_boundary_is_always_present(self) -> None:
        _result, output = self._generate()
        self.assertEqual((), wacp.verify_pack(output))
        text = (output / "CLAIM_BOUNDARY.md").read_text(encoding="utf-8")
        self.assertIn("does NOT", text)
        self.assertIn("replace reviewer judgment", text)

    def test_network_is_not_used(self) -> None:
        with mock.patch.object(socket, "create_connection", side_effect=AssertionError("network")), mock.patch.object(urllib.request, "urlopen", side_effect=AssertionError("network")):
            result, _ = self._generate()
        self.assertEqual("PACK_READY", result.status)

    def test_no_silent_truncation(self) -> None:
        normal, normal_output = self._generate(output_name="normal")
        large, large_output = self._generate(self._manifest(max_bytes=1), output_name="large")
        self.assertEqual("PACK_READY", normal.status)
        self.assertEqual("PACK_TOO_LARGE", large.status)
        self.assertEqual((normal_output / "DIFF.patch").read_bytes(), (large_output / "DIFF.patch").read_bytes())

    def test_repeat_generation_is_byte_identical(self) -> None:
        first, first_output = self._generate(output_name="first")
        second, second_output = self._generate(output_name="second")
        self.assertEqual(first.pack_id, second.pack_id)
        for name in wacp.ARTIFACT_NAMES:
            self.assertEqual((first_output / name).read_bytes(), (second_output / name).read_bytes())

    def test_open_findings_without_source_is_explicit(self) -> None:
        _result, output = self._generate()
        self.assertIn("NO_FINDING_SOURCE_SUPPLIED", (output / "OPEN_FINDINGS.md").read_text())
        self.assertNotIn("NO_OPEN_FINDINGS", (output / "OPEN_FINDINGS.md").read_text())

    def test_unavailable_declared_finding_source_is_not_called_unsupplied(self) -> None:
        result, output = self._generate(self._manifest(finding_sources=["other.txt"]))
        self.assertEqual("PACK_INCOMPLETE", result.status)
        text = (output / "OPEN_FINDINGS.md").read_text()
        self.assertIn("DECLARED_FINDING_SOURCE_UNAVAILABLE", text)
        self.assertNotIn("NO_FINDING_SOURCE_SUPPLIED", text)

    def test_supplied_test_status_is_recorded_not_verified(self) -> None:
        supplied = {"commands": ["python -m unittest"], "status": "PASS", "source": "Human", "date": "2026-10-07"}
        _result, output = self._generate(self._manifest(test_status=supplied))
        text = (output / "TEST_STATUS.md").read_text()
        self.assertIn("python -m unittest", text)
        self.assertIn("did not independently verify", text)

    def test_pack_id_is_integrity_only(self) -> None:
        _result, output = self._generate()
        manifest = self._pack_manifest(output)
        self.assertRegex(manifest["pack_id"], r"^[0-9a-f]{64}$")
        self.assertIn("not_authorization", manifest["nonclaims"])

    # Required mutation assurance.
    def test_mutant_ignore_out_of_scope_change_is_killed(self) -> None:
        self._write("other.txt", b"changed\n")
        self.head = self._commit("other change")
        original = wacp._changed_paths
        with mock.patch.object(wacp, "_changed_paths", side_effect=lambda root, base, head: tuple(path for path in original(root, base, head) if path != "other.txt")):
            actual, _ = self._generate()
        self._assert_mutant_killed("PACK_INCOMPLETE", actual.status)
        self.assertEqual("PACK_READY", actual.status)

    def test_mutant_allow_path_traversal_is_killed(self) -> None:
        raw = json.dumps(self._manifest(include=["../scope/a.txt"])).encode()
        with self.assertRaises(wacp.WACPError):
            wacp._parse_manifest(raw)
        with mock.patch.object(wacp, "_validate_pattern", side_effect=lambda value, _label: value):
            parsed = wacp._parse_manifest(raw)
        self._assert_mutant_killed(None, parsed)

    def test_mutant_allow_selected_symlink_is_killed(self) -> None:
        blob = self._git("hash-object", "-w", "--stdin", input_bytes=b"scope/a.txt")
        self._git("update-index", "--add", "--cacheinfo", f"120000,{blob},scope/link")
        self._git("commit", "-q", "-m", "symlink")
        self.head = self._git("rev-parse", "HEAD")
        original = wacp._blob

        def mutant(root, commit, path, tree):
            if tree.get(path, (None,))[0] == "120000":
                return b"scope/a.txt"
            return original(root, commit, path, tree)

        with mock.patch.object(wacp, "_blob", side_effect=mutant):
            actual, _ = self._generate(
                self._manifest(include=["scope/**"], clean_worktree_required=False)
            )
        self._assert_mutant_killed("INVALID", actual.status)
        self.assertEqual("PACK_READY", actual.status)

    def test_mutant_skip_artifact_hash_verification_is_killed(self) -> None:
        _result, output = self._generate()
        (output / "DIFF.patch").write_bytes(b"tampered")
        errors = wacp.verify_pack(output)
        self.assertTrue(errors)
        with mock.patch.object(wacp, "verify_pack", return_value=()):
            mutant_errors = wacp.verify_pack(output)
        self._assert_mutant_killed(errors, mutant_errors)

    def test_mutant_silent_budget_acceptance_is_killed(self) -> None:
        original = wacp._build_pack

        def mutant(**kwargs):
            body, artifacts = original(**kwargs)
            body["completeness_status"] = "PACK_READY"
            return body, artifacts

        with mock.patch.object(wacp, "_build_pack", side_effect=mutant):
            actual, _ = self._generate(self._manifest(max_bytes=1))
        self._assert_mutant_killed("PACK_TOO_LARGE", actual.status)
        self.assertEqual("PACK_READY", actual.status)

    def test_mutant_missing_claim_boundary_is_killed(self) -> None:
        _result, output = self._generate()
        (output / "CLAIM_BOUNDARY.md").unlink()
        errors = wacp.verify_pack(output)
        self.assertIn("missing or malformed claim boundary", errors)
        mutant_errors = tuple(error for error in errors if error != "missing or malformed claim boundary")
        self._assert_mutant_killed(errors, mutant_errors)


if __name__ == "__main__":
    unittest.main()
