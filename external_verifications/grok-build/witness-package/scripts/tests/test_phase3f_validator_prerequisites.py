#!/usr/bin/env python3
"""Phase 3F-A validator prerequisite tests (Pi-adjudicated plan).

Safety contract:
- Python standard library only
- Temporary workspaces are children of scripts/tests/ (phase3f_test_*)
- Validator exercised only against isolated fixture directories
- No real Docker, Cargo, rustc, compiler, host Witness workflow, product,
  bootstrap, ldd, package manager, network, or Independent Witness execution
- Phase 3F-B host gating is asserted only as current-source supersession in
  test_22; validator still writes no evidence
- Validator must not write into evidence
- Cleanup of repository-local temps on success and failure
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path, PurePosixPath

TESTS_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = TESTS_DIR.parent
sys.path.insert(0, str(SCRIPTS_DIR))
sys.path.insert(0, str(TESTS_DIR))

import fixtures_lib as fx  # noqa: E402
import evidence_inventory as ei  # noqa: E402
from schema_register_loader import load_active_register  # noqa: E402
import validate_witness_evidence as v  # noqa: E402

HOST = v.HOST_OUTCOME_INGESTION_NAME
HOST_SCRIPT = SCRIPTS_DIR / "run_witness_narrow_build.sh"
VALIDATOR = SCRIPTS_DIR / "validate_witness_evidence.py"


def _cleanup_phase3f_temps() -> None:
    for path in TESTS_DIR.glob("phase3f_test_*"):
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)


def _read_current_field(path: Path, key: str) -> str:
    values = [line.partition("=")[2] for line in path.read_text(encoding="utf-8").splitlines()
              if line.startswith(key + "=")]
    if len(values) != 1:
        raise AssertionError(f"{path.name}: expected exactly one {key}")
    return values[0]


class Phase3FValidatorPrerequisites(unittest.TestCase):
    def setUp(self) -> None:
        self._temps: list[Path] = []

    def tearDown(self) -> None:
        for path in self._temps:
            if path.exists():
                shutil.rmtree(path, ignore_errors=True)
        self._temps.clear()
        _cleanup_phase3f_temps()

    def _tmpdir(self) -> Path:
        path = Path(tempfile.mkdtemp(prefix="phase3f_test_", dir=str(TESTS_DIR)))
        self._temps.append(path)
        return path

    def _write_success(self) -> Path:
        tmp = self._tmpdir()
        fx.build_and_write(tmp, "success-artifact-present")
        return tmp

    def _fixed_git(self, *args: str) -> bytes:
        """Read local objects only: no checkout, filters, configuration or fetch."""
        self.assertIn(args[0], {"rev-parse", "ls-tree", "cat-file"})
        cp = subprocess.run(
            ["git", "--no-optional-locks", "-C", str(SCRIPTS_DIR.parents[3]), *args],
            capture_output=True, timeout=30, check=True,
        )
        return cp.stdout

    def _write_current_success(self, mode: str) -> Path:
        return self._derive_current_fixture(mode)

    def _derive_current_fixture(self, mode: str, *, eligibility_negative: bool = False) -> Path:
        """Stage 2A recipe v1: fixed blob payload, then manifest, then binding.

        Only the two derived seal files differ for a positive control. The
        negative control additionally changes exactly one Host-owned value.
        No source fixture or historical builder is edited or normalized.
        """
        commit = "319c6dcb92c5152225076b99a465436ba55924b3"
        package = "external_verifications/grok-build/witness-package/"
        fixture, tree_oid, file_count = {
            "host-preliminary": ("rc6-r6-synthetic-preliminary", "679ecd08cc9ae419c4fe293c52f1f86c76318125", 26),
            "final-submission": ("rc6-r6-synthetic-final", "670f818ae0ff0efbfb8ab95d206163eba6883252", 30),
        }[mode]
        schema_oid = "3db5051448b667d7c40e02f1813da9f622829314"
        manifest_name = "EVIDENCE_MANIFEST.sha256"
        binding_name = "WEAVER_FORGE_FINAL_BINDING.txt"
        excluded = {manifest_name, binding_name}
        tree = self._tmpdir()
        audit: dict = {
            "recipe": "fixed-git-blob-derived-fixture-v1", "test_id": self.id(),
            "commit": commit, "tree_oid": tree_oid, "fixture": fixture, "mode": mode,
            "eligibility_negative": eligibility_negative, "sources": {}, "checks": {},
            "status": "INCOMPLETE",
        }

        def digest(data: bytes) -> str:
            return hashlib.sha256(data).hexdigest()

        def fields(data: bytes) -> dict[str, str]:
            # Parsing is for assertions only; payload writing always uses raw bytes.
            result: dict[str, str] = {}
            for line in data.decode("utf-8").splitlines():
                if "=" in line:
                    key, value = line.split("=", 1)
                    self.assertNotIn(key, result, "duplicate source field")
                    result[key] = value
            return result

        def read_blob(oid: str) -> bytes:
            raw = self._fixed_git("cat-file", "blob", oid)
            header = b"blob " + str(len(raw)).encode("ascii") + bytes([0])
            self.assertEqual(hashlib.sha1(header + raw).hexdigest(), oid)
            return raw

        try:
            self.assertEqual(self._fixed_git("cat-file", "-t", commit).strip(), b"commit")
            source_path = package + "scripts/tests/fixtures/" + fixture
            self.assertEqual(self._fixed_git("rev-parse", commit + ":" + source_path).decode().strip(), tree_oid)
            self.assertEqual(self._fixed_git("rev-parse", commit + ":" + package + "schemas/canonical_schema_register_rc6.json").decode().strip(), schema_oid)
            schema = read_blob(schema_oid)
            self.assertEqual(json.loads(schema)["schema_register_version"], "rc6.5")
            self.assertEqual(v.SCHEMA_REGISTER_VERSION, "rc6.5")
            audit["schema"] = {"blob_oid": schema_oid, "raw_sha256": digest(schema), "version": "rc6.5"}
            sources: dict[str, bytes] = {}
            folded: set[str] = set()
            listing = self._fixed_git("ls-tree", "-r", "-z", tree_oid)
            for entry in listing.split(bytes([0])):
                if not entry:
                    continue
                meta, raw_name = entry.split(bytes([9]), 1)
                permissions, kind, raw_oid = meta.split()
                self.assertEqual((permissions, kind), (b"100644", b"blob"), "only regular fixture blobs are allowed")
                name = raw_name.decode("utf-8")
                path = PurePosixPath(name)
                self.assertTrue(name.isascii() and not path.is_absolute())
                self.assertEqual(path.as_posix(), name)
                self.assertNotIn(chr(92), name)
                self.assertNotIn(":", name)
                for part in name.split("/"):
                    self.assertNotIn(part, {"", ".", ".."})
                    self.assertNotEqual(part.casefold(), ".git")
                    self.assertEqual(part, part.rstrip(" ."))
                    self.assertFalse(any(ord(char) < 32 for char in part))
                    self.assertNotIn(part.split(".", 1)[0].upper(),
                                     {"CON", "PRN", "AUX", "NUL", *["COM" + str(i) for i in range(1, 10)], *["LPT" + str(i) for i in range(1, 10)]})
                self.assertNotIn(name.casefold(), folded, "case-insensitive path collision")
                folded.add(name.casefold())
                oid = raw_oid.decode("ascii")
                raw = read_blob(oid)
                sources[name] = raw
                audit["sources"][name] = {"blob_oid": oid, "raw_sha256": digest(raw), "bytes": len(raw)}
            self.assertEqual(len(sources), file_count)
            self.assertTrue(excluded <= sources.keys())
            audit["checks"]["fixed_input_identity_and_paths"] = True

            payload = {name: raw for name, raw in sources.items() if name not in excluded}
            host = fields(payload[HOST])
            post = fields(payload["POST_BUILD_INTEGRITY.txt"])
            self.assertEqual(host["preliminary_success_eligible"], "NO")
            self.assertEqual(host["evidence_completeness_status"], "INCOMPLETE" if mode == "host-preliminary" else "COMPLETE")
            self.assertEqual(post["evidence_inventory_complete"], "no" if mode == "host-preliminary" else "yes")
            if mode == "final-submission":
                dev_sha = digest(payload["DEVIATIONS.txt"])
                idx_sha = digest(payload["REDACTIONS_INDEX.txt"])
                self.assertEqual(dev_sha, "dd293b6e000cdbcbc3ba9f2d23f9f2f3b3dd60b55283b48adc1e78139ffaca03")
                self.assertEqual(idx_sha, "f9d3a263aa440f9b52d3f14bdaa8a66dc96f78be8029cb10e942ea0da1fcb229")
                statement = fields(payload["WITNESS_STATEMENT.md"])
                verdict = fields(payload["WITNESS_VERDICT.md"])
                for record in (statement, verdict):
                    self.assertEqual(record["deviations_sha256"], dev_sha)
                    self.assertEqual(record["redactions_index_sha256"], idx_sha)
                    self.assertEqual(record["statement_identity_sha256"], "8febcd5f5fa32198e415934f4bcc13619bdb1d559f79b5afca234c27d8f8281c")
                stmt_sha = digest(payload["WITNESS_STATEMENT.md"])
                self.assertEqual(stmt_sha, "53fb09d9d643a63232404a6d68a3147d9455472bc3f8603bf6195ca9b7f2728b")
                self.assertEqual(verdict["witness_statement_sha256"], stmt_sha)
                self.assertEqual(fields(payload["DEVIATIONS.txt"])["preliminary_deviations_sha256"], "e5fa05d7cd64c68cd782c37d571bf3e90da80a95d6a88a59e6fc73a0f2b98733")
                audit["known_final_deviations_sha256"] = dev_sha
            else:
                self.assertTrue({"WITNESS_STATEMENT.md", "WITNESS_VERDICT.md", "REDACTIONS_INDEX.txt"}.isdisjoint(payload))
            audit["checks"]["mode_and_existing_manual_bindings"] = True

            if eligibility_negative:
                self.assertEqual(mode, "host-preliminary")
                old = b"preliminary_success_eligible=NO\n"
                self.assertEqual(payload[HOST].count(old), 1)
                payload[HOST] = payload[HOST].replace(old, b"preliminary_success_eligible=YES\n", 1)
            self.assertEqual(list(tree.iterdir()), [])
            for name, raw in payload.items():
                path = tree / name
                path.parent.mkdir(parents=True, exist_ok=True)
                with path.open("xb") as handle:
                    handle.write(raw)
            self.assertFalse((tree / manifest_name).exists())
            self.assertFalse((tree / binding_name).exists())
            manifest = ei.write_evidence_manifest(tree, nested_classes=load_active_register().nested_class_records())

            # Independent oracle: fixed source set and hashlib, NOT inventory enumeration/hash helpers.
            expected_lines = [digest(payload[name]) + "  ./" + name for name in sorted(payload)]
            expected_manifest = ("\n".join(expected_lines) + "\n").encode("ascii")
            self.assertEqual(manifest.read_bytes(), expected_manifest)
            manifest_sha = digest(manifest.read_bytes())
            template = sources[binding_name]
            binding, count = re.subn(
                b"^final_manifest_sha256=[0-9a-f]{64}$",
                b"final_manifest_sha256=" + manifest_sha.encode("ascii"),
                template, flags=re.MULTILINE,
            )
            self.assertEqual(count, 1)
            with (tree / binding_name).open("xb") as handle:
                handle.write(binding)
            self.assertEqual(fields(binding)["final_manifest_sha256"], manifest_sha)
            # Independent line-wise comparison: only the one permitted template field changes.
            old_lines, new_lines = template.splitlines(keepends=True), binding.splitlines(keepends=True)
            self.assertEqual(len(old_lines), len(new_lines))
            hash_lines = 0
            for old_line, new_line in zip(old_lines, new_lines):
                if old_line.startswith(b"final_manifest_sha256="):
                    hash_lines += 1
                    self.assertEqual(new_line, b"final_manifest_sha256=" + manifest_sha.encode("ascii") + bytes([10]))
                else:
                    self.assertEqual(new_line, old_line)
            self.assertEqual(hash_lines, 1)
            actual = {p.relative_to(tree).as_posix(): p.read_bytes() for p in tree.rglob("*") if p.is_file()}
            self.assertFalse(any(p.is_symlink() for p in tree.rglob("*")))
            self.assertEqual(set(actual), set(sources))
            for name, expected in payload.items():
                self.assertEqual(actual[name], expected, name)
                if not (eligibility_negative and name == HOST):
                    self.assertEqual(actual[name], sources[name], name)
            self.assertEqual(len(expected_lines), file_count - 2)
            audit["checks"].update({"payload_bytes_and_file_sets": True, "independent_manifest_bytes_hashes_and_exclusions": True, "final_binding_hash_and_other_fields": True})
            audit["manifest_sha256"] = manifest_sha
            audit["status"] = "PASS"
            return tree
        except BaseException as exc:
            audit["failure"] = repr(exc)
            audit["status"] = "FAIL"
            raise
        finally:
            audit["derived_files"] = {p.relative_to(tree).as_posix(): {"sha256": digest(p.read_bytes()), "bytes": p.stat().st_size} for p in tree.rglob("*") if p.is_file()}
            evidence = os.environ.get("WF_STAGE2A_ORACLE_DIR")
            if evidence:
                directory = Path(evidence)
                self.assertTrue(directory.is_dir() and not directory.is_symlink())
                with (directory / ("oracle-" + tree.name + ".json")).open("x", encoding="utf-8", newline="\n") as handle:
                    json.dump(audit, handle, ensure_ascii=False, indent=2)
                    handle.write("\n")

    def _host_lines(self, tree: Path) -> list[str]:
        return (tree / HOST).read_text(encoding="utf-8").splitlines()

    def _rewrite_host(self, tree: Path, lines: list[str]) -> None:
        text = "\n".join(lines) + "\n"
        (tree / HOST).write_text(text, encoding="utf-8", newline="\n")
        # Refresh manifest hash for HOST_OUTCOME when listed.
        files = {
            p.name: p.read_text(encoding="utf-8")
            for p in tree.iterdir()
            if p.is_file() and p.name != v.MANIFEST_NAME
        }
        fx.write_tree(tree, files)

    # ------------------------------------------------------------------
    # Explicit outcome / no inference
    # ------------------------------------------------------------------
    def test_01_explicit_outcome_accepted(self) -> None:
        tree = self._write_current_success("final-submission")
        errors = v.validate_dir(tree)
        self.assertEqual(errors, [], errors)

    def test_02_missing_outcome_rejected(self) -> None:
        tree = self._write_success()
        bec = tree / "BUILD_EXIT_CODE.txt"
        bec.write_text(
            "\n".join(l for l in bec.read_text(encoding="utf-8").splitlines() if not l.startswith("outcome="))
            + "\n",
            encoding="utf-8",
            newline="\n",
        )
        files = {
            p.name: p.read_text(encoding="utf-8")
            for p in tree.iterdir()
            if p.is_file() and p.name != v.MANIFEST_NAME
        }
        fx.write_tree(tree, files)
        errors = v.validate_dir(tree)
        self.assertTrue(any("explicit 'outcome'" in e for e in errors), errors)

    def test_03_empty_outcome_rejected(self) -> None:
        tree = self._write_success()
        bec = tree / "BUILD_EXIT_CODE.txt"
        text = bec.read_text(encoding="utf-8").replace(
            "outcome=CARGO_SUCCEEDED_ARTIFACT_PRESENT", "outcome="
        )
        bec.write_text(text, encoding="utf-8", newline="\n")
        files = {
            p.name: p.read_text(encoding="utf-8")
            for p in tree.iterdir()
            if p.is_file() and p.name != v.MANIFEST_NAME
        }
        fx.write_tree(tree, files)
        errors = v.validate_dir(tree)
        self.assertTrue(any("empty" in e.lower() and "outcome" in e.lower() for e in errors), errors)

    def test_04_malformed_outcome_rejected(self) -> None:
        tree = self._write_success()
        bec = tree / "BUILD_EXIT_CODE.txt"
        text = bec.read_text(encoding="utf-8").replace(
            "outcome=CARGO_SUCCEEDED_ARTIFACT_PRESENT", "outcome=NOT A VALID TOKEN"
        )
        bec.write_text(text, encoding="utf-8", newline="\n")
        files = {
            p.name: p.read_text(encoding="utf-8")
            for p in tree.iterdir()
            if p.is_file() and p.name != v.MANIFEST_NAME
        }
        fx.write_tree(tree, files)
        errors = v.validate_dir(tree)
        self.assertTrue(any("not an allowed" in e or "unsupported" in e.lower() for e in errors), errors)

    def test_05_unsupported_outcome_rejected(self) -> None:
        tree = self._write_success()
        bec = tree / "BUILD_EXIT_CODE.txt"
        text = bec.read_text(encoding="utf-8").replace(
            "outcome=CARGO_SUCCEEDED_ARTIFACT_PRESENT", "outcome=SUCCESS"
        )
        bec.write_text(text, encoding="utf-8", newline="\n")
        files = {
            p.name: p.read_text(encoding="utf-8")
            for p in tree.iterdir()
            if p.is_file() and p.name != v.MANIFEST_NAME
        }
        fx.write_tree(tree, files)
        errors = v.validate_dir(tree)
        self.assertTrue(any("SUCCESS" in e for e in errors), errors)

    def test_06_prior_inference_combinations_no_longer_produce_outcome(self) -> None:
        """Former cargo_started/build_status inference pairs must not yield outcome."""
        cases = [
            ("NO", "BUILD_NOT_STARTED"),
            ("NO", "INFRASTRUCTURE_FAILURE"),
            ("YES", "FAILED"),
        ]
        for cargo_started, build_status in cases:
            with self.subTest(cargo_started=cargo_started, build_status=build_status):
                tree = self._tmpdir()
                files = fx.build_scenario("success-artifact-present")
                # Strip explicit outcome; leave secondary fields that previously inferred.
                lines = [
                    l
                    for l in files["BUILD_EXIT_CODE.txt"].splitlines()
                    if not l.startswith("outcome=")
                ]
                rebuilt = []
                for l in lines:
                    if l.startswith("cargo_started="):
                        rebuilt.append(f"cargo_started={cargo_started}")
                    elif l.startswith("build_status="):
                        rebuilt.append(f"build_status={build_status}")
                    else:
                        rebuilt.append(l)
                files["BUILD_EXIT_CODE.txt"] = "\n".join(rebuilt) + "\n"
                fx.write_tree(tree, files)
                errors = v.validate_dir(tree)
                self.assertTrue(errors, "expected fail-closed without explicit outcome")
                self.assertTrue(
                    any("explicit 'outcome'" in e or "inference" in e.lower() for e in errors),
                    errors,
                )
                # Must not silently accept as structural PASS via inference.
                self.assertNotEqual(errors, [])

    def test_07_contradictory_explicit_outcome_and_secondary_fields_rejected(self) -> None:
        tree = self._write_success()
        bec = tree / "BUILD_EXIT_CODE.txt"
        text = bec.read_text(encoding="utf-8").replace("cargo_started=YES", "cargo_started=NO")
        bec.write_text(text, encoding="utf-8", newline="\n")
        files = {
            p.name: p.read_text(encoding="utf-8")
            for p in tree.iterdir()
            if p.is_file() and p.name != v.MANIFEST_NAME
        }
        fx.write_tree(tree, files)
        errors = v.validate_dir(tree)
        self.assertTrue(any("cargo_started" in e for e in errors), errors)
        # Outcome must remain the explicit value — contradiction fails, not repair.
        self.assertFalse(any("inferred" in e.lower() for e in errors), errors)

    # Stage 2A: lock the current explicit-only implementation, not runtime compliance.
    def test_26_stage2a_determine_outcome_never_infers(self) -> None:
        contract = json.loads(
            (SCRIPTS_DIR.parent / "AUTHORITATIVE_OUTCOME_CONTRACT.json").read_text(encoding="utf-8")
        )
        invalid = [None, {}, {"outcome": ""}, {"outcome": "SUCCESS"}]
        invalid += [{"outcome": row["value"]} for row in contract["nonterminal_sentinels"]]
        invalid += [
            {"cargo_started": "NO", "build_status": "BUILD_NOT_STARTED"},
            {"cargo_started": "YES", "build_status": "COMPLETE", "cargo_exit_code": "0"},
            {"cargo_started": "YES", "build_status": "FAILED", "cargo_exit_code": "17"},
            {"docker_exit_code": "0"},
            {"docker_exit_code": "23"},
        ]
        for fields in invalid:
            with self.subTest(fields=fields):
                errors: list[str] = []
                self.assertIsNone(v.determine_outcome(fields, errors))
                self.assertTrue(errors, "missing/invalid outcome must report an error")
        for row in contract["terminal_outcomes"]:
            with self.subTest(explicit=row["value"]):
                errors = []
                self.assertEqual(v.determine_outcome({"outcome": row["value"]}, errors), row["value"])
                self.assertEqual(errors, [])

    def test_27_stage2a_invalid_outcome_both_modes_cli_and_bytes(self) -> None:
        contract = json.loads(
            (SCRIPTS_DIR.parent / "AUTHORITATIVE_OUTCOME_CONTRACT.json").read_text(encoding="utf-8")
        )
        cases = [
            ("missing", None, "explicit 'outcome'"),
            ("empty", "outcome=", "empty"),
            ("unsupported", "outcome=SUCCESS", "not an allowed"),
            ("malformed", "outcome=NOT A VALID TOKEN", "not an allowed"),
            ("duplicate-same", "outcome=CARGO_SUCCEEDED_ARTIFACT_PRESENT\noutcome=CARGO_SUCCEEDED_ARTIFACT_PRESENT", "duplicate key 'outcome'"),
            ("duplicate-different", "outcome=CARGO_SUCCEEDED_ARTIFACT_PRESENT\noutcome=CARGO_FAILED", "duplicate key 'outcome'"),
        ]
        cases += [("sentinel-" + row["value"], "outcome=" + row["value"], "not an allowed")
                  for row in contract["nonterminal_sentinels"]]
        # Leave success-shaped Cargo facts, and test both zero/nonzero Docker exits:
        # neither may supply a missing authoritative outcome.
        cases += [("docker-" + code, None, "explicit 'outcome'") for code in ("0", "23")]
        for mode in ("host-preliminary", "final-submission"):
            for label, replacement, diagnostic in cases:
                with self.subTest(mode=mode, case=label):
                    tree = self._tmpdir()
                    files = fx.build_scenario("success-artifact-present")
                    lines = [line for line in files["BUILD_EXIT_CODE.txt"].splitlines()
                             if not line.startswith("outcome=")]
                    if replacement is not None:
                        lines.append(replacement)
                    files["BUILD_EXIT_CODE.txt"] = "\n".join(lines) + "\n"
                    if label.startswith("docker-"):
                        code = label.removeprefix("docker-")
                        files["DOCKER_EXIT_CODE.txt"] = "\n".join(
                            "docker_exit_code=" + code if line.startswith("docker_exit_code=") else line
                            for line in files["DOCKER_EXIT_CODE.txt"].splitlines()
                        ) + "\n"
                    fx.write_tree(tree, files)
                    before = {p.relative_to(tree).as_posix(): p.read_bytes()
                              for p in tree.rglob("*") if p.is_file()}
                    errors = v.validate_dir(tree, mode=mode)
                    self.assertTrue(any(diagnostic in error for error in errors), errors)
                    cp = subprocess.run(
                        [sys.executable, "-B", str(VALIDATOR), str(tree), "--" + mode],
                        capture_output=True, text=True, encoding="utf-8", errors="replace",
                        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}, timeout=30,
                    )
                    self.assertNotEqual(cp.returncode, 0, cp.stdout + cp.stderr)
                    self.assertIn("STRUCTURAL VALIDATION: FAIL", cp.stdout)
                    self.assertIn(diagnostic, cp.stdout)
                    after = {p.relative_to(tree).as_posix(): p.read_bytes()
                             for p in tree.rglob("*") if p.is_file()}
                    self.assertEqual(after, before, "validator must not repair evidence")

    # ------------------------------------------------------------------
    # HOST_OUTCOME closed aux + structure
    # ------------------------------------------------------------------
    def test_08_host_outcome_accepted_as_declared_closed_auxiliary(self) -> None:
        tree = self._write_current_success("final-submission")
        self.assertTrue((tree / HOST).is_file())
        self.assertIn(HOST, v.CLOSED_AUX_EVIDENCE_FILES)
        errors = v.validate_dir(tree)
        self.assertEqual(errors, [], errors)
        # Listed in manifest must not be rejected as undeclared aux.
        manifest = (tree / v.MANIFEST_NAME).read_text(encoding="utf-8")
        self.assertIn(f"./{HOST}", manifest)

    def test_09_host_outcome_missing_fields_rejected(self) -> None:
        tree = self._write_success()
        lines = [l for l in self._host_lines(tree) if not l.startswith("failure_stage=")]
        self._rewrite_host(tree, lines)
        errors = v.validate_dir(tree)
        self.assertTrue(any("missing required field 'failure_stage'" in e for e in errors), errors)

    def test_10_host_outcome_extra_fields_rejected(self) -> None:
        tree = self._write_success()
        lines = self._host_lines(tree) + ["extra_field=nope"]
        self._rewrite_host(tree, lines)
        errors = v.validate_dir(tree)
        self.assertTrue(any("unknown/extra field 'extra_field'" in e for e in errors), errors)

    def test_11_host_outcome_duplicate_fields_rejected(self) -> None:
        tree = self._write_success()
        lines = self._host_lines(tree) + ["status=OK"]
        self._rewrite_host(tree, lines)
        errors = v.validate_dir(tree)
        self.assertTrue(any("duplicate key 'status'" in e for e in errors), errors)

    def test_12_illegal_host_status_rejected(self) -> None:
        tree = self._write_success()
        lines = [
            "host_infrastructure_status=BANANA" if l.startswith("host_infrastructure_status=") else l
            for l in self._host_lines(tree)
        ]
        self._rewrite_host(tree, lines)
        errors = v.validate_dir(tree)
        self.assertTrue(any("host_infrastructure_status" in e for e in errors), errors)

    def test_13_illegal_container_result_status_rejected(self) -> None:
        tree = self._write_success()
        lines = [
            "container_result_presence=MAYBE" if l.startswith("container_result_presence=") else l
            for l in self._host_lines(tree)
        ]
        self._rewrite_host(tree, lines)
        errors = v.validate_dir(tree)
        self.assertTrue(any("container_result_presence" in e for e in errors), errors)

    def test_14_outcome_disagreement_rejected(self) -> None:
        tree = self._write_success()
        lines = [
            "container_outcome=CARGO_FAILED" if l.startswith("container_outcome=") else l
            for l in self._host_lines(tree)
        ]
        self._rewrite_host(tree, lines)
        errors = v.validate_dir(tree)
        self.assertTrue(any("disagrees with authoritative" in e for e in errors), errors)

    # ------------------------------------------------------------------
    # Host-preliminary / automatable RC4B-017 subset
    # ------------------------------------------------------------------
    def test_15_host_preliminary_pass_requires_post_build_status_ok(self) -> None:
        tree = self._write_success()
        post = tree / "POST_BUILD_INTEGRITY.txt"
        text = post.read_text(encoding="utf-8")
        text = text.replace("status=OK", "status=FAILED").replace(
            "post_build_integrity_ok=yes", "post_build_integrity_ok=no"
        )
        post.write_text(text, encoding="utf-8", newline="\n")
        files = {
            p.name: p.read_text(encoding="utf-8")
            for p in tree.iterdir()
            if p.is_file() and p.name != v.MANIFEST_NAME
        }
        fx.write_tree(tree, files)
        errors = v.validate_dir(tree, host_preliminary=True)
        self.assertTrue(
            any("host-preliminary structural PASS requires status=OK" in e for e in errors),
            errors,
        )

    def test_16_host_preliminary_pass_requires_post_build_integrity_ok_yes(self) -> None:
        tree = self._write_success()
        # Contradictory OK/no is already a schema error; also covered by subset.
        post = tree / "POST_BUILD_INTEGRITY.txt"
        text = post.read_text(encoding="utf-8").replace(
            "post_build_integrity_ok=yes", "post_build_integrity_ok=no"
        )
        post.write_text(text, encoding="utf-8", newline="\n")
        files = {
            p.name: p.read_text(encoding="utf-8")
            for p in tree.iterdir()
            if p.is_file() and p.name != v.MANIFEST_NAME
        }
        fx.write_tree(tree, files)
        errors = v.validate_dir(tree, host_preliminary=True)
        self.assertTrue(
            any("post_build_integrity_ok" in e for e in errors),
            errors,
        )

    def test_17_host_preliminary_enforces_source_lock_subset(self) -> None:
        tree = self._write_success()
        post = tree / "POST_BUILD_INTEGRITY.txt"
        text = post.read_text(encoding="utf-8").replace(
            "source_head_unchanged=yes", "source_head_unchanged=no"
        )
        post.write_text(text, encoding="utf-8", newline="\n")
        files = {
            p.name: p.read_text(encoding="utf-8")
            for p in tree.iterdir()
            if p.is_file() and p.name != v.MANIFEST_NAME
        }
        fx.write_tree(tree, files)
        errors = v.validate_dir(tree, host_preliminary=True)
        self.assertTrue(any("source_head_unchanged=yes" in e for e in errors), errors)

    def test_18_host_outcome_statuses_must_match_post_build_ok_conditions(self) -> None:
        tree = self._write_success()
        lines = [
            "post_build_integrity_status=FAILED" if l.startswith("post_build_integrity_status=") else l
            for l in self._host_lines(tree)
        ]
        self._rewrite_host(tree, lines)
        errors = v.validate_dir(tree, host_preliminary=True)
        self.assertTrue(
            any("post_build_integrity_status=OK" in e for e in errors),
            errors,
        )

    def test_19_evidence_inventory_complete_not_required_for_host_preliminary_pass(self) -> None:
        tree = self._write_current_success("host-preliminary")
        post = (tree / "POST_BUILD_INTEGRITY.txt").read_text(encoding="utf-8")
        self.assertIn("evidence_inventory_complete=no", post)
        errors = v.validate_dir(tree, host_preliminary=True)
        self.assertEqual(errors, [], errors)
        self.assertFalse(any("evidence_inventory_complete=yes" in e for e in errors))

    def test_20_preliminary_success_eligible_remains_no_not_final_eligibility(self) -> None:
        tree = self._write_current_success("host-preliminary")
        host = (tree / HOST).read_text(encoding="utf-8")
        self.assertIn("preliminary_success_eligible=NO", host)
        errors = v.validate_dir(tree, host_preliminary=True)
        self.assertEqual(errors, [], errors)
        # A separately constructed/sealed negative tree changes only eligibility.
        negative = self._derive_current_fixture("host-preliminary", eligibility_negative=True)
        self.assertNotEqual(tree, negative)
        before = {p.relative_to(tree).as_posix(): p.read_bytes() for p in tree.rglob("*") if p.is_file()}
        errors_yes = v.validate_dir(negative, host_preliminary=True)
        target_errors = [error for error in errors_yes if error.startswith(
            "HOST_OUTCOME_INGESTION.txt: preliminary_success_eligible must remain NO"
        )]
        self.assertTrue(target_errors, errors_yes)
        self.assertEqual(errors_yes, target_errors, "unrelated schema errors must not prove the negative")
        self.assertEqual(
            {p.relative_to(tree).as_posix(): p.read_bytes() for p in tree.rglob("*") if p.is_file()}, before,
        )

    # ------------------------------------------------------------------
    # Boundaries: no-write, no host gating, closed aux still closed
    # ------------------------------------------------------------------
    def test_21_validator_writes_no_evidence(self) -> None:
        tree = self._write_current_success("host-preliminary")
        before = {
            p.relative_to(tree).as_posix(): (p.stat().st_mtime_ns, p.read_bytes())
            for p in tree.rglob("*")
            if p.is_file()
        }
        errors = v.validate_dir(tree, host_preliminary=True)
        self.assertEqual(errors, [], errors)
        after_names = {p.relative_to(tree).as_posix() for p in tree.rglob("*") if p.is_file()}
        self.assertEqual(after_names, set(before))
        for name, (mtime, data) in before.items():
            p = tree / name
            self.assertEqual(p.read_bytes(), data)
            self.assertEqual(p.stat().st_mtime_ns, mtime)
        self.assertNotIn("VALIDATOR_RESULT.txt", after_names)
        src = VALIDATOR.read_text(encoding="utf-8")
        self.assertIn("writes only to its own stdout/stderr", src)
        self.assertIn("never writes into the", src)
        self.assertIn("evidence directory it is validating", src)
        self.assertNotIn("VALIDATOR_RESULT", src)
        self.assertIsNone(re.search(r"evidence_dir[^\n]*\.write_", src))

    def test_22_host_gating_deferred_from_3f_a_implemented_in_3f_b(self) -> None:
        # Phase 3F-A historical boundary: validator itself still writes no VALIDATOR_RESULT.
        src = VALIDATOR.read_text(encoding="utf-8")
        self.assertNotIn("VALIDATOR_RESULT", src)
        self.assertIn("writes only to its own stdout/stderr", src)
        # Current host source after Phase 3F-B: repository validator is invoked in
        # host-preliminary mode and host exit is validator-gated.
        host = HOST_SCRIPT.read_text(encoding="utf-8")
        self.assertIsNotNone(
            re.search(
                r"(?:^|\n)\s*(?:\"\$\{?py\}?\"|\$\{?py\}?|python3?)[^\n]*--host-preliminary",
                host,
            )
            or ("--host-preliminary" in host and "invoke_host_preliminary_validator" in host)
        )
        self.assertIn("--host-preliminary", host)
        self.assertIn("VALIDATOR_RESULT", host)
        self.assertIn("invoke_host_preliminary_validator", host)
        self.assertIn("evaluate_host_automated_structural_gate", host)
        self.assertIn("STRUCTURAL VALIDATION: PASS", host)
        self.assertIn('if [[ "${POST_BUILD_INTEGRITY_OK}" != "yes" ]]; then', host)
        self.assertIn('HOST_VALIDATOR_GATE_OK', host)

    def test_23_closed_auxiliary_inventory_still_rejects_unrelated_extra_files(self) -> None:
        tree = self._write_success()
        extra = tree / "SOMETHING_ELSE.txt"
        extra.write_text("hello\n", encoding="utf-8", newline="\n")
        digest = v.sha256_file(extra)
        mpath = tree / v.MANIFEST_NAME
        mpath.write_text(
            mpath.read_text(encoding="utf-8") + f"{digest}  ./SOMETHING_ELSE.txt\n",
            encoding="utf-8",
            newline="\n",
        )
        errors = v.validate_dir(tree)
        self.assertTrue(any("outside the closed" in e for e in errors), errors)

    def test_24_host_preliminary_pass_on_success_fixture(self) -> None:
        tree = self._write_current_success("host-preliminary")
        errors = v.validate_dir(tree, host_preliminary=True)
        self.assertEqual(errors, [], errors)
        rc = v.main([str(tree), "--host-preliminary"])
        self.assertEqual(rc, 0)

    def test_25_source_or_lock_changed_must_be_no_for_host_preliminary(self) -> None:
        tree = self._write_success()
        post = tree / "POST_BUILD_INTEGRITY.txt"
        text = post.read_text(encoding="utf-8").replace(
            "source_or_lock_changed=no", "source_or_lock_changed=yes"
        )
        post.write_text(text, encoding="utf-8", newline="\n")
        files = {
            p.name: p.read_text(encoding="utf-8")
            for p in tree.iterdir()
            if p.is_file() and p.name != v.MANIFEST_NAME
        }
        fx.write_tree(tree, files)
        errors = v.validate_dir(tree, host_preliminary=True)
        self.assertTrue(any("source_or_lock_changed=no" in e for e in errors), errors)


if __name__ == "__main__":
    try:
        unittest.main(verbosity=2, exit=False)
    finally:
        _cleanup_phase3f_temps()
