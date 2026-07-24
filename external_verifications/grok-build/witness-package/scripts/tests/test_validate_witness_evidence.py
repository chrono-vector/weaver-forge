"""Structural-validator test suite (1.0.0-rc4).

Covers:
  * schema-block CONTRACT tests (validator FILE_REQUIRED_FIELDS vs the exact
    BEGIN_SCHEMA_BLOCK / writer sections of the host and container scripts),
  * duplicate-key rejection,
  * outcome consistency across the outcome-bearing files,
  * golden-fixture validation (both the committed tests/fixtures/ trees and
    freshly built temp trees) for every required outcome / failure mode,
  * host-safety static assertions (canonical constants, readonly, overrides,
    WORK_ROOT guards) read from the shell script text,
  * manifest grammar / inventory,
  * machine verdict-ceiling enforcement,
  * redaction rules, and
  * upstream_product_commands_not_run enforcement.

Nothing here executes Docker/Cargo/Witness scripts.
"""

from __future__ import annotations

import os
import re
import sys
import tempfile
import unittest
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.dirname(HERE)
for p in (SCRIPTS, HERE):
    if p not in sys.path:
        sys.path.insert(0, p)

import validate_witness_evidence as v  # noqa: E402
import fixtures_lib as fx  # noqa: E402

HOST_SCRIPT = Path(SCRIPTS) / "run_witness_narrow_build.sh"
CONTAINER_SCRIPT = Path(SCRIPTS) / "container_narrow_build.sh"
FIXTURES = Path(HERE) / "fixtures"


# ---------------------------------------------------------------------------
# Shell schema-block extraction helpers
# ---------------------------------------------------------------------------

_KEY_RE = re.compile(r'echo\s+"([A-Za-z_][A-Za-z0-9_]*)=')
_BARE_KEY_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)=")


def schema_block_keys(text: str, name: str) -> set[str]:
    """Union of all `key=` names inside every
    `BEGIN_SCHEMA_BLOCK <name> ... END_SCHEMA_BLOCK` region.

    Supports both host ``echo "key=..."`` writers and container heredoc
    ``key=${var}`` schema blocks.
    """
    start_re = re.compile(r"BEGIN_SCHEMA_BLOCK\s+" + re.escape(name) + r"\b")
    keys: set[str] = set()
    inside = False
    for line in text.splitlines():
        if "END_SCHEMA_BLOCK" in line:
            inside = False
            continue
        if start_re.search(line):
            inside = True
            continue
        if inside:
            m = _KEY_RE.search(line)
            if m:
                keys.add(m.group(1))
                continue
            m = _BARE_KEY_RE.match(line.strip())
            if m:
                keys.add(m.group(1))
    return keys


def writer_block_keys(text: str, filename: str) -> set[str]:
    """Keys echoed in the `{ ... } > "${EVIDENCE_DIR}/<filename>"` writer with
    the most keys (used for writers that are not wrapped in a schema block,
    e.g. POST_BUILD_INTEGRITY.txt)."""
    lines = text.splitlines()
    redirect_re = re.compile(r"\}\s*>\s*\"?\$\{EVIDENCE_DIR\}/" + re.escape(filename))
    best: set[str] = set()
    for idx, line in enumerate(lines):
        if not redirect_re.search(line):
            continue
        keys: set[str] = set()
        j = idx - 1
        while j >= 0:
            m = _KEY_RE.search(lines[j])
            if m:
                keys.add(m.group(1))
            if lines[j].strip() == "{":
                break
            j -= 1
        if len(keys) > len(best):
            best = keys
    return best


# ---------------------------------------------------------------------------
# Tree helpers
# ---------------------------------------------------------------------------


def _mktree(scenario: str, overrides: "dict[str, str] | None" = None) -> Path:
    files = fx.build_scenario(scenario)
    if overrides:
        for k, val in overrides.items():
            if val is None:
                files.pop(k, None)
            else:
                files[k] = val
    tmp = Path(tempfile.mkdtemp())
    fx.write_tree(tmp, files)
    return tmp


def _witness_verdict(outcome: str, ceiling: str, proposed: str) -> str:
    return (
        "evidence_schema_version=1\n"
        "run_id=run-2026-07-22-001\n"
        f"package_tag={fx.TAG}\n"
        f"weaver_forge_commit={fx.WEAVER}\n"
        f"grok_build_commit={fx.GROK}\n"
        f"outcome={outcome}\n"
        f"verdict_ceiling={ceiling}\n"
        "product_executed=NO\n"
        "ldd_used=NO\n"
        "maintainer_intake_verdict=pending\n"
        f"\nWitness proposed verdict: {proposed}\n"
    )


# ---------------------------------------------------------------------------
# Contract tests (validator schema <-> shell script schema blocks)
# ---------------------------------------------------------------------------


class ContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.host = HOST_SCRIPT.read_text(encoding="utf-8")
        cls.container = CONTAINER_SCRIPT.read_text(encoding="utf-8")

    def test_container_generated_clean_target_keys_match_schema(self):
        self.assertEqual(
            schema_block_keys(self.container, "CLEAN_TARGET"),
            set(v.FILE_REQUIRED_FIELDS["CLEAN_TARGET_PROOF.txt"]),
        )

    def test_container_generated_build_environment_keys_match_schema(self):
        self.assertEqual(
            schema_block_keys(self.container, "BUILD_ENVIRONMENT"),
            set(v.FILE_REQUIRED_FIELDS["BUILD_ENVIRONMENT.txt"]),
        )

    def test_container_generated_timing_keys_match_schema(self):
        self.assertEqual(
            schema_block_keys(self.container, "BUILD_TIMING"),
            set(v.FILE_REQUIRED_FIELDS["BUILD_TIMING.txt"]),
        )

    def test_container_generated_build_exit_code_keys_match_schema(self):
        self.assertEqual(
            schema_block_keys(self.container, "BUILD_EXIT_CODE"),
            set(v.FILE_REQUIRED_FIELDS["BUILD_EXIT_CODE.txt"]),
        )

    def test_container_generated_static_inspection_keys_match_schema(self):
        # The validator splits STATIC's schema between FILE_REQUIRED_FIELDS
        # (always non-empty) and STATIC_ARTIFACT_INSPECTION_ALWAYS_PRESENT_KEYS
        # (present but legitimately empty when applicable=no). Their union is
        # the full container schema block.
        validator_keys = set(v.FILE_REQUIRED_FIELDS["STATIC_ARTIFACT_INSPECTION.txt"]) | set(
            v.STATIC_ARTIFACT_INSPECTION_ALWAYS_PRESENT_KEYS
        )
        self.assertEqual(
            schema_block_keys(self.container, "STATIC_ARTIFACT_INSPECTION"),
            validator_keys,
        )

    def test_host_generated_image_identity_keys_match_schema(self):
        self.assertEqual(
            schema_block_keys(self.host, "IMAGE_IDENTITY"),
            set(v.FILE_REQUIRED_FIELDS["IMAGE_IDENTITY.txt"]),
        )

    def test_host_generated_environment_keys_match_schema(self):
        # ENVIRONMENT is dual-owned: host writes one block, the container
        # appends a second. The union must exactly cover the required set.
        union = schema_block_keys(self.host, "ENVIRONMENT") | schema_block_keys(
            self.container, "ENVIRONMENT"
        )
        self.assertEqual(union, set(v.FILE_REQUIRED_FIELDS["ENVIRONMENT.txt"]))

    def test_host_generated_post_build_integrity_keys_match_schema(self):
        emitted = writer_block_keys(self.host, "POST_BUILD_INTEGRITY.txt")
        required = set(v.FILE_REQUIRED_FIELDS["POST_BUILD_INTEGRITY.txt"])
        # Phase 3E: exact equality (not one-way required-subset inclusion).
        self.assertEqual(emitted, required, f"host writer keys {emitted} != schema {required}")

    def test_image_identity_uses_rc4_key_names(self):
        keys = schema_block_keys(self.host, "IMAGE_IDENTITY")
        self.assertIn("inspect_image_id_command", keys)
        self.assertNotIn("inspect_id_command", keys)
        self.assertIn("inspect_repo_digests_command", keys)
        self.assertNotIn("inspect_repodigests_command", keys)


# ---------------------------------------------------------------------------
# parse_kv / duplicate-key tests
# ---------------------------------------------------------------------------


class ParseKvTests(unittest.TestCase):
    def test_duplicate_key_same_value_rejected(self):
        fields, errors = v.parse_kv("a=1\na=1\n", "F")
        self.assertEqual(fields.get("a"), "1")
        self.assertTrue(any("duplicate key 'a'" in e for e in errors))

    def test_duplicate_key_conflicting_value_rejected(self):
        fields, errors = v.parse_kv("a=1\na=2\n", "F")
        self.assertTrue(any("duplicate key 'a'" in e for e in errors))
        self.assertTrue(any("conflicting" in e for e in errors))

    def test_no_last_value_wins(self):
        fields, _ = v.parse_kv("a=1\na=2\n", "F")
        self.assertEqual(fields.get("a"), "1")

    def test_duplicate_key_in_evidence_file_fails_validation(self):
        # Append a duplicate cargo_incremental line to BUILD_COMMAND.txt.
        files = fx.build_scenario("success-artifact-present")
        files["BUILD_COMMAND.txt"] = files["BUILD_COMMAND.txt"] + "cargo_incremental=0\n"
        tmp = Path(tempfile.mkdtemp())
        fx.write_tree(tmp, files)
        errors = v.validate_dir(tmp)
        self.assertTrue(any("duplicate key 'cargo_incremental'" in e for e in errors), errors)


# ---------------------------------------------------------------------------
# Golden fixtures
# ---------------------------------------------------------------------------


class GoldenFixtureTests(unittest.TestCase):
    def test_all_committed_fixtures_pass(self):
        for scenario in fx.ALL_SCENARIOS:
            with self.subTest(scenario=scenario):
                d = FIXTURES / scenario
                self.assertTrue(d.is_dir(), f"missing committed fixture: {d}")
                errors = v.validate_dir(d)
                self.assertEqual(errors, [], f"{scenario}: {errors}")

    def test_all_scenarios_build_and_pass(self):
        for scenario in fx.ALL_SCENARIOS:
            with self.subTest(scenario=scenario):
                tmp = _mktree(scenario)
                errors = v.validate_dir(tmp)
                self.assertEqual(errors, [], f"{scenario}: {errors}")

    def test_main_entrypoint_returns_zero_on_success_fixture(self):
        rc = v.main([str(FIXTURES / "success-artifact-present")])
        self.assertEqual(rc, 0)


# ---------------------------------------------------------------------------
# Outcome consistency
# ---------------------------------------------------------------------------


class OutcomeConsistencyTests(unittest.TestCase):
    def test_docker_outcome_disagreement_fails(self):
        files = fx.build_scenario("success-artifact-present")
        files["DOCKER_EXIT_CODE.txt"] = files["DOCKER_EXIT_CODE.txt"].replace(
            "outcome=CARGO_SUCCEEDED_ARTIFACT_PRESENT", "outcome=CARGO_FAILED"
        )
        tmp = Path(tempfile.mkdtemp())
        fx.write_tree(tmp, files)
        errors = v.validate_dir(tmp)
        self.assertTrue(any("DOCKER_EXIT_CODE.txt: outcome" in e for e in errors), errors)

    def test_timing_outcome_disagreement_fails(self):
        files = fx.build_scenario("success-artifact-present")
        files["BUILD_TIMING.txt"] = files["BUILD_TIMING.txt"].replace(
            "outcome=CARGO_SUCCEEDED_ARTIFACT_PRESENT", "outcome=BUILD_NOT_STARTED"
        )
        tmp = Path(tempfile.mkdtemp())
        fx.write_tree(tmp, files)
        errors = v.validate_dir(tmp)
        self.assertTrue(any("BUILD_TIMING.txt: outcome" in e for e in errors), errors)

    def test_missing_outcome_fails(self):
        files = fx.build_scenario("success-artifact-present")
        files["BUILD_EXIT_CODE.txt"] = "\n".join(
            l for l in files["BUILD_EXIT_CODE.txt"].splitlines() if not l.startswith("outcome=")
        ) + "\n"
        # Phase 3F-A: secondary cargo_started/build_status must not produce an
        # outcome when explicit outcome= is absent (inference removed).
        tmp = Path(tempfile.mkdtemp())
        fx.write_tree(tmp, files)
        errors = v.validate_dir(tmp)
        self.assertTrue(any("explicit 'outcome'" in e or "outcome" in e.lower() for e in errors), errors)
        self.assertTrue(
            any("inference" in e.lower() or "explicit" in e.lower() for e in errors),
            errors,
        )

    def test_invalid_outcome_value_fails(self):
        files = fx.build_scenario("success-artifact-present")
        files["BUILD_EXIT_CODE.txt"] = files["BUILD_EXIT_CODE.txt"].replace(
            "outcome=CARGO_SUCCEEDED_ARTIFACT_PRESENT", "outcome=BANANA"
        )
        tmp = Path(tempfile.mkdtemp())
        fx.write_tree(tmp, files)
        errors = v.validate_dir(tmp)
        self.assertTrue(errors)

    def test_duplicate_outcome_line_fails(self):
        files = fx.build_scenario("success-artifact-present")
        files["BUILD_EXIT_CODE.txt"] = (
            files["BUILD_EXIT_CODE.txt"] + "outcome=CARGO_SUCCEEDED_ARTIFACT_PRESENT\n"
        )
        tmp = Path(tempfile.mkdtemp())
        fx.write_tree(tmp, files)
        errors = v.validate_dir(tmp)
        self.assertTrue(any("duplicate key 'outcome'" in e for e in errors), errors)

    def test_witness_verdict_outcome_mismatch_fails(self):
        files = fx.build_scenario("success-artifact-present")
        files["WITNESS_VERDICT.md"] = _witness_verdict(
            "CARGO_FAILED", "FAIL", "FAIL"
        )
        tmp = Path(tempfile.mkdtemp())
        fx.write_tree(tmp, files)
        errors = v.validate_dir(tmp)
        self.assertTrue(any("WITNESS_VERDICT.md: outcome" in e for e in errors), errors)


# ---------------------------------------------------------------------------
# Verdict ceiling
# ---------------------------------------------------------------------------


class VerdictCeilingTests(unittest.TestCase):
    def test_compute_ceiling_success(self):
        self.assertEqual(
            v.compute_verdict_ceiling("CARGO_SUCCEEDED_ARTIFACT_PRESENT", False, False, False),
            "PASS",
        )

    def test_compute_ceiling_static_incomplete_partial(self):
        self.assertEqual(
            v.compute_verdict_ceiling("CARGO_SUCCEEDED_ARTIFACT_PRESENT", False, False, True),
            "PARTIAL",
        )

    def test_compute_ceiling_cargo_failed_fail(self):
        self.assertEqual(v.compute_verdict_ceiling("CARGO_FAILED", False, False, False), "FAIL")

    def test_compute_ceiling_missing_artifact_fail(self):
        self.assertEqual(
            v.compute_verdict_ceiling("CARGO_SUCCEEDED_ARTIFACT_MISSING", False, False, False),
            "FAIL",
        )

    def test_compute_ceiling_not_started_indeterminate(self):
        self.assertEqual(
            v.compute_verdict_ceiling("BUILD_NOT_STARTED", False, False, False), "INDETERMINATE"
        )
        self.assertEqual(
            v.compute_verdict_ceiling("INFRASTRUCTURE_FAILURE", False, False, False),
            "INDETERMINATE",
        )

    def test_compute_ceiling_prohibited_fail(self):
        self.assertEqual(
            v.compute_verdict_ceiling("CARGO_SUCCEEDED_ARTIFACT_PRESENT", True, False, False),
            "FAIL",
        )

    def test_compute_ceiling_identity_mismatch_fail(self):
        self.assertEqual(
            v.compute_verdict_ceiling("CARGO_SUCCEEDED_ARTIFACT_PRESENT", False, True, False),
            "FAIL",
        )

    def test_proposed_verdict_above_ceiling_rejected(self):
        # static-inspection-incomplete has ceiling PARTIAL; proposing PASS fails.
        files = fx.build_scenario("static-inspection-incomplete")
        files["WITNESS_VERDICT.md"] = _witness_verdict(
            "CARGO_SUCCEEDED_ARTIFACT_PRESENT", "PASS", "PASS"
        )
        tmp = Path(tempfile.mkdtemp())
        fx.write_tree(tmp, files)
        errors = v.validate_dir(tmp)
        self.assertTrue(any("exceeds the machine-computed verdict" in e for e in errors), errors)

    def test_proposed_pass_on_cargo_failed_rejected(self):
        files = fx.build_scenario("cargo-failed")
        files["WITNESS_VERDICT.md"] = _witness_verdict("CARGO_FAILED", "PASS", "PASS")
        tmp = Path(tempfile.mkdtemp())
        fx.write_tree(tmp, files)
        errors = v.validate_dir(tmp)
        self.assertTrue(any("exceeds" in e for e in errors), errors)


# ---------------------------------------------------------------------------
# Manifest
# ---------------------------------------------------------------------------


class ManifestTests(unittest.TestCase):
    def _tree(self, scenario="success-artifact-present"):
        tmp = _mktree(scenario)
        return tmp

    def test_single_space_manifest_line_rejected(self):
        tmp = self._tree()
        mpath = tmp / v.MANIFEST_NAME
        text = mpath.read_text(encoding="utf-8")
        # collapse the mandatory two-space separator to one on the first line.
        first, _, rest = text.partition("\n")
        first_bad = first.replace("  ./", " ./", 1)
        mpath.write_text(first_bad + "\n" + rest, encoding="utf-8")
        errors = v.validate_dir(tmp)
        self.assertTrue(any("malformed line" in e for e in errors), errors)

    def test_hash_mismatch_rejected(self):
        tmp = self._tree()
        (tmp / "DEVIATIONS.txt").write_text(
            "evidence_schema_version=1\ndeviation_state=NONE\n# tampered\n", encoding="utf-8"
        )
        errors = v.validate_dir(tmp)
        self.assertTrue(any("hash mismatch" in e for e in errors), errors)

    def test_missing_manifest_entry_rejected(self):
        tmp = self._tree()
        mpath = tmp / v.MANIFEST_NAME
        lines = [l for l in mpath.read_text(encoding="utf-8").splitlines() if "DEVIATIONS.txt" not in l]
        mpath.write_text("\n".join(lines) + "\n", encoding="utf-8")
        errors = v.validate_dir(tmp)
        self.assertTrue(any("missing mandatory entry for DEVIATIONS.txt" in e for e in errors), errors)

    def test_prohibited_aux_file_rejected(self):
        tmp = self._tree()
        (tmp / "BOOTSTRAP_PROTOC_VERSION.txt").write_text("libprotoc 29.3\n", encoding="utf-8")
        errors = v.validate_dir(tmp)
        self.assertTrue(
            any("BOOTSTRAP_PROTOC_VERSION.txt must never appear" in e for e in errors), errors
        )

    def test_undeclared_aux_in_manifest_rejected(self):
        tmp = self._tree()
        extra = tmp / "SOMETHING_ELSE.txt"
        extra.write_text("hello\n", encoding="utf-8")
        digest = v.sha256_file(extra)
        mpath = tmp / v.MANIFEST_NAME
        mpath.write_text(
            mpath.read_text(encoding="utf-8") + f"{digest}  ./SOMETHING_ELSE.txt\n", encoding="utf-8"
        )
        errors = v.validate_dir(tmp)
        self.assertTrue(any("outside the closed" in e for e in errors), errors)

    def test_allowed_aux_file_accepted(self):
        tmp = self._tree()
        (tmp / "HOST_RUN_METADATA.txt").write_text("run metadata\n", encoding="utf-8")
        errors = v.validate_dir(tmp)
        self.assertEqual(errors, [], errors)


# ---------------------------------------------------------------------------
# Redactions
# ---------------------------------------------------------------------------


class RedactionTests(unittest.TestCase):
    def test_unlogged_redaction_marker_rejected(self):
        files = fx.build_scenario("success-artifact-present")
        files["ARTIFACT_IDENTITY.txt"] = files["ARTIFACT_IDENTITY.txt"].replace(
            "gnu_build_id=abcdef0123456789", "gnu_build_id=[REDACTED: build id]"
        )
        tmp = Path(tempfile.mkdtemp())
        fx.write_tree(tmp, files)
        errors = v.validate_dir(tmp)
        self.assertTrue(any("[REDACTED" in e for e in errors), errors)

    def test_prohibited_category_redaction_rejected(self):
        files = fx.build_scenario("success-artifact-present")
        files["REDACTIONS.md"] = (
            "evidence_schema_version=1\n"
            "redaction_state=PRESENT\n"
            "semantic_integrity_declaration=yes\n"
            "redaction_1_file=ARTIFACT_IDENTITY.txt\n"
            "redaction_1_field=artifact_sha256\n"
            "redaction_1_reason=privacy\n"
            "redaction_1_replacement_marker=[REDACTED: sha]\n"
        )
        tmp = Path(tempfile.mkdtemp())
        fx.write_tree(tmp, files)
        errors = v.validate_dir(tmp)
        self.assertTrue(any("prohibited category" in e for e in errors), errors)

    def test_valid_present_redaction_accepted(self):
        files = fx.build_scenario("success-artifact-present")
        files["ENVIRONMENT.txt"] = files["ENVIRONMENT.txt"].replace(
            "host_cpu=AMD Ryzen 9 7950X 16-Core Processor",
            "host_cpu=[REDACTED: cpu model]",
        )
        files["REDACTIONS.md"] = (
            "evidence_schema_version=1\n"
            "redaction_state=PRESENT\n"
            "semantic_integrity_declaration=yes\n"
            "redaction_1_file=ENVIRONMENT.txt\n"
            "redaction_1_field=host_cpu\n"
            "redaction_1_reason=host hardware privacy\n"
            "redaction_1_replacement_marker=[REDACTED: cpu model]\n"
        )
        tmp = Path(tempfile.mkdtemp())
        fx.write_tree(tmp, files)
        errors = v.validate_dir(tmp)
        self.assertEqual(errors, [], errors)


# ---------------------------------------------------------------------------
# upstream_product_commands_not_run
# ---------------------------------------------------------------------------


class UpstreamProductCommandsTests(unittest.TestCase):
    def test_statement_upstream_not_yes_rejected(self):
        files = fx.build_scenario("success-artifact-present")
        files["WITNESS_STATEMENT.md"] = files["WITNESS_STATEMENT.md"].replace(
            "upstream_product_commands_not_run=yes", "upstream_product_commands_not_run=no"
        )
        tmp = Path(tempfile.mkdtemp())
        fx.write_tree(tmp, files)
        errors = v.validate_dir(tmp)
        self.assertTrue(
            any("upstream_product_commands_not_run must be yes" in e for e in errors), errors
        )

    def test_environment_upstream_not_yes_rejected(self):
        files = fx.build_scenario("success-artifact-present")
        files["ENVIRONMENT.txt"] = files["ENVIRONMENT.txt"].replace(
            "upstream_product_commands_not_run=yes", "upstream_product_commands_not_run=no"
        )
        tmp = Path(tempfile.mkdtemp())
        fx.write_tree(tmp, files)
        errors = v.validate_dir(tmp)
        self.assertTrue(
            any("upstream_product_commands_not_run must be yes" in e for e in errors), errors
        )

    def test_statement_upstream_no_flags_ceiling_fail(self):
        # upstream=no on the statement drives the machine ceiling to FAIL, so a
        # proposed PASS is rejected.
        files = fx.build_scenario("success-artifact-present")
        files["WITNESS_STATEMENT.md"] = files["WITNESS_STATEMENT.md"].replace(
            "upstream_product_commands_not_run=yes", "upstream_product_commands_not_run=no"
        )
        tmp = Path(tempfile.mkdtemp())
        fx.write_tree(tmp, files)
        errors = v.validate_dir(tmp)
        self.assertTrue(any("exceeds" in e for e in errors), errors)


# ---------------------------------------------------------------------------
# product_executed / ldd enforcement
# ---------------------------------------------------------------------------


class ProductLddTests(unittest.TestCase):
    def test_product_executed_yes_rejected(self):
        files = fx.build_scenario("success-artifact-present")
        files["ARTIFACT_IDENTITY.txt"] = files["ARTIFACT_IDENTITY.txt"].replace(
            "product_executed=NO", "product_executed=YES"
        )
        tmp = Path(tempfile.mkdtemp())
        fx.write_tree(tmp, files)
        errors = v.validate_dir(tmp)
        self.assertTrue(errors)

    def test_ldd_used_yes_rejected(self):
        files = fx.build_scenario("success-artifact-present")
        files["DOCKER_EXIT_CODE.txt"] = files["DOCKER_EXIT_CODE.txt"].replace(
            "ldd_used=NO", "ldd_used=YES"
        )
        tmp = Path(tempfile.mkdtemp())
        fx.write_tree(tmp, files)
        errors = v.validate_dir(tmp)
        self.assertTrue(errors)


# ---------------------------------------------------------------------------
# Missing-file / structural
# ---------------------------------------------------------------------------


class StructuralTests(unittest.TestCase):
    def test_missing_required_file_rejected(self):
        tmp = _mktree("success-artifact-present")
        (tmp / "SOURCE_IDENTITY.txt").unlink()
        # keep manifest consistent so we exercise the required-file check
        errors = v.validate_dir(tmp)
        self.assertTrue(any("SOURCE_IDENTITY.txt" in e for e in errors), errors)

    def test_cargo_exit_code_na_alias_rejected(self):
        files = fx.build_scenario("build-not-started")
        files["BUILD_EXIT_CODE.txt"] = files["BUILD_EXIT_CODE.txt"].replace(
            "cargo_exit_code=NOT_APPLICABLE", "cargo_exit_code=N/A"
        )
        tmp = Path(tempfile.mkdtemp())
        fx.write_tree(tmp, files)
        errors = v.validate_dir(tmp)
        self.assertTrue(any("cargo_exit_code" in e for e in errors), errors)


# ---------------------------------------------------------------------------
# Host-safety static assertions (read from the shell scripts, never executed)
# ---------------------------------------------------------------------------


class HostSafetyStaticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.host = HOST_SCRIPT.read_text(encoding="utf-8")
        cls.container = CONTAINER_SCRIPT.read_text(encoding="utf-8")

    def test_strict_bash_mode(self):
        self.assertIn("set -Eeuo pipefail", self.host)

    def test_canonical_constants_present_and_readonly(self):
        self.assertIn('readonly PACKAGE_VERSION="1.0.0-rc4"', self.host)
        self.assertIn('readonly CANONICAL_WEAVER_FORGE_TAG="grok-build-witness-v1.0.0-rc4"', self.host)
        self.assertIn(f'readonly CANONICAL_GROK_BUILD_COMMIT="{fx.GROK}"', self.host)
        self.assertIn(f'readonly CANONICAL_CARGO_LOCK_SHA256="{fx.LOCK}"', self.host)
        self.assertIn(f'readonly CANONICAL_BUILD_CMD="{fx.BUILD_CMD}"', self.host)
        self.assertIn(fx.IMG, self.host)

    def test_constants_self_check_present(self):
        self.assertIn("CANONICAL_IMAGE_DIGEST is not embedded in CANONICAL_RUST_IMAGE", self.host)

    def test_override_requires_noncanonical_flag(self):
        self.assertIn("overridden without --noncanonical-deviation", self.host)

    def test_noncanonical_pass_prohibition_and_url_fail_severity(self):
        self.assertIn("Witness proposed verdict PASS is PREVENTED", self.host)
        self.assertIn("WEAVER_FORGE_URL", self.host)
        self.assertIn('VERDICT_CEILING="FAIL"', self.host)
        self.assertIn("compute_verdict_ceiling", self.host)

    def test_work_root_guards_present(self):
        for needle in (
            "WORK_ROOT must not resolve to /",
            "WORK_ROOT must not be the package repository",
            "WORK_ROOT must be an absolute path",
            "WORK_ROOT must not resolve to the home directory",
            "WORK_ROOT must not resolve to a WSL drive-root mount",
            "WORK_ROOT must not resolve within a system prefix",
            "WORK_ROOT must not be an ancestor of the package repository",
            "WORK_ROOT must not be located inside the package repository",
        ):
            self.assertIn(needle, self.host, needle)

    def test_witness_id_validation_present(self):
        self.assertIn("validate_witness_id", self.host)
        self.assertIn("witness-id must not contain path separators", self.host)
        self.assertIn("witness-id must not contain '..'", self.host)
        self.assertIn("witness-id must not contain whitespace", self.host)

    def test_managed_child_symlink_policy_present(self):
        self.assertIn("safe_reset_managed_path", self.host)
        self.assertIn("NEVER followed", self.host)
        self.assertIn('[[ -L "${p}" ]]', self.host)
        self.assertIn('rm -f -- "${p}"', self.host)

    def test_missing_tag_and_tag_head_mismatch_finalizers_present(self):
        self.assertIn('finalize_pre_docker_infrastructure_failure "weaver_forge_tag_resolution"', self.host)
        self.assertIn('finalize_pre_docker_infrastructure_failure "weaver_forge_tag_head_mismatch"', self.host)

    def test_dirty_package_and_grok_clone_finalizers_present(self):
        self.assertIn('finalize_pre_docker_infrastructure_failure "weaver_forge_dirty_clone"', self.host)
        self.assertIn('finalize_pre_docker_infrastructure_failure "grok_build_dirty_clone"', self.host)

    def test_wrong_grok_commit_and_cargo_lock_finalizers_present(self):
        self.assertIn('finalize_pre_docker_infrastructure_failure "grok_build_commit_mismatch"', self.host)
        self.assertIn('finalize_pre_docker_infrastructure_failure "cargo_lock_pre_docker_mismatch"', self.host)
        self.assertIn("cargo_lock_post_matches_expected", self.host)
        self.assertIn("CARGO_LOCK_AFTER", self.host)

    def test_grok_detached_probe_present(self):
        self.assertIn('git -C "${SRC_DIR}" symbolic-ref -q HEAD', self.host)
        self.assertIn("grok_build_detached_head", self.host)
        self.assertIn('finalize_pre_docker_infrastructure_failure "grok_build_detached_head_check"', self.host)

    def test_host_preserves_container_outcome_authority(self):
        # Phase 3D: parse_container_result_tuple supersedes parse_container_outcome.
        self.assertIn("parse_container_result_tuple", self.host)
        self.assertIn("invalid_or_missing_container_outcome", self.host)
        self.assertIn("outcome_field_missing", self.host)
        self.assertIn("outcome_field_duplicated", self.host)
        self.assertIn("unsupported_outcome_", self.host)
        self.assertIn(
            "ordinary outcome from cargo_started/artifact-presence/raw Docker exit code alone",
            self.host,
        )

    def test_no_cached_image_fallback(self):
        self.assertIn("cached_image_fallback_used=NO", self.host)

    def test_image_pull_and_identity_failure_finalizers_present(self):
        self.assertIn('finalize_pre_docker_infrastructure_failure "image_pull"', self.host)
        self.assertIn('finalize_pre_docker_infrastructure_failure "image_identity_enforcement"', self.host)

    def test_no_embedded_future_rc4_commit(self):
        self.assertNotIn("PLACEHOLDER_UNTIL_RC4_TAGGED", self.host)
        self.assertNotIn("CANONICAL_WEAVER_FORGE_EXPECTED_COMMIT=", self.host)

    def test_container_uses_pipefail(self):
        self.assertIn("pipefail", self.container)


class DeviationCeilingTests(unittest.TestCase):
    def test_verdict_above_deviation_ceiling_rejected(self):
        files = fx.build_scenario("success-artifact-present")
        files["DEVIATIONS.txt"] = (
            "evidence_schema_version=1\n"
            "deviation_state=PRESENT\n"
            "deviation_1_description=noncanonical identity override accepted with flag\n"
            "deviation_1_severity=MATERIAL_NONCANONICAL\n"
            "deviation_1_canonical_identity_impact=yes\n"
            "deviation_1_verdict_ceiling=PARTIAL\n"
        )
        # Proposed PASS with recorded ceiling PARTIAL must fail (above deviation ceiling).
        # _witness_verdict(outcome, ceiling, proposed)
        files["WITNESS_VERDICT.md"] = _witness_verdict(
            "CARGO_SUCCEEDED_ARTIFACT_PRESENT", "PARTIAL", "PASS"
        )
        tmp = Path(tempfile.mkdtemp())
        fx.write_tree(tmp, files)
        errors = v.validate_dir(tmp)
        self.assertTrue(
            any("exceeds the recorded verdict_ceiling" in e or "PARTIAL" in e for e in errors),
            errors,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
