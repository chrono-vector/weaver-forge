"""Synthetic unit tests for validate_witness_evidence.py (no real Witness data).

Every fixture body is FILE-SPECIFIC: no single generic text block is reused
across unrelated evidence files, so a validator regression that accepts a
shared/generic body for every file would be caught here (RB-020 / RB-027).
"""

import io
import re
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from validate_witness_evidence import (  # noqa: E402
    EXACT_BUILD_CMD,
    EXPECTED_CARGO_LOCK_SHA256,
    EXPECTED_GROK_COMMIT,
    EXPECTED_IMAGE_DIGEST,
    MANIFEST_NAME,
    REQUIRED_FILES,
    main,
    parse_verdict_selection,
    sha256_file,
    validate_dir,
)

WEAVER_COMMIT = "89127c78c3a11492892de7e3b5f0dee18d71775a"
RUN_ID = "run-2026-07-22-001"
WITNESS_ID = "witness01"
ARTIFACT_SHA = "a" * 64
DESCRIPTOR_SHA_A = "b" * 64
DESCRIPTOR_SHA_B = "c" * 64


# ---------------------------------------------------------------------------
# File-specific fixture bodies (one function per evidence file; no sharing)
# ---------------------------------------------------------------------------


def _weaver_forge_package_identity() -> str:
    return (
        "evidence_schema_version=1\n"
        f"witness_id={WITNESS_ID}\n"
        f"run_id={RUN_ID}\n"
        "package_version=1.0.0-rc3\n"
        "weaver_forge_url=https://github.com/chrono-vector/weaver-forge.git\n"
        "weaver_forge_tag_requested=grok-build-witness-v1.0.0-rc3\n"
        f"weaver_forge_commit_resolved={WEAVER_COMMIT}\n"
        f"package_clone_head={WEAVER_COMMIT}\n"
        "package_clone_detached=yes\n"
        "package_clone_clean_status=yes\n"
        "tag_head_match=yes\n"
        "package_commit_authority=annotated_tag_resolution\n"
        f"grok_build_source_commit_expected={EXPECTED_GROK_COMMIT}\n"
        "canonical_run=yes\n"
    )


def _source_acquisition() -> str:
    return (
        "evidence_schema_version=1\n"
        "weaver_forge_url=https://github.com/chrono-vector/weaver-forge.git\n"
        "weaver_forge_tag_requested=grok-build-witness-v1.0.0-rc3\n"
        f"weaver_forge_commit_resolved={WEAVER_COMMIT}\n"
        f"package_clone_head={WEAVER_COMMIT}\n"
        "package_clone_clean_status=yes\n"
        "tag_head_match=yes\n"
        "package_commit_authority=annotated_tag_resolution\n"
        "grok_build_url=https://github.com/xai-org/grok-build.git\n"
        f"grok_build_commit_requested={EXPECTED_GROK_COMMIT}\n"
        f"grok_build_commit_observed={EXPECTED_GROK_COMMIT}\n"
        "grok_build_clean_tree=yes\n"
        "fresh_clones=yes\n"
    )


def _source_identity() -> str:
    return (
        "evidence_schema_version=1\n"
        f"grok_build_commit_expected={EXPECTED_GROK_COMMIT}\n"
        f"grok_build_commit_observed={EXPECTED_GROK_COMMIT}\n"
        f"cargo_lock_sha256_expected={EXPECTED_CARGO_LOCK_SHA256}\n"
        f"cargo_lock_sha256_observed={EXPECTED_CARGO_LOCK_SHA256}\n"
    )


def _image_identity() -> str:
    return (
        "evidence_schema_version=1\n"
        f"requested_image_string=docker.io/library/rust@sha256:{EXPECTED_IMAGE_DIGEST}\n"
        f"requested_digest=sha256:{EXPECTED_IMAGE_DIGEST}\n"
        "docker_pull_exit_code=0\n"
        "image_id=sha256:deadbeef00000000000000000000000000000000000000000000000000dead\n"
        f"repo_digests=docker.io/library/rust@sha256:{EXPECTED_IMAGE_DIGEST}\n"
        "os=linux\n"
        "architecture=amd64\n"
        "platform=linux/amd64\n"
        "digest_match_expected=yes\n"
        "platform_match_expected=yes\n"
    )


def _environment() -> str:
    return (
        "evidence_schema_version=1\n"
        f"witness_id={WITNESS_ID}\n"
        "host_os=Ubuntu 24.04\n"
        "host_arch=x86_64\n"
        "host_docker_client_version=29.4.3\n"
        "host_docker_server_version=29.4.3\n"
        "container_os_release=Debian GNU/Linux\n"
        "rustc_version=1.92.0\n"
        "cargo_version=1.92.0\n"
        "product_executed=NO\n"
        "ldd_used=NO\n"
    )


def _bootstrap() -> str:
    return (
        "evidence_schema_version=1\n"
        "apt_packages=ca-certificates git build-essential pkg-config cmake curl perl file binutils\n"
        "dotslash_version=0.5.7\n"
        "dotslash_binary_path=/root/.cargo/bin/dotslash\n"
        "protoc_descriptor_src=/src/bin/protoc\n"
        "protoc_descriptor_writable=yes\n"
        f"protoc_descriptor_src_sha256={DESCRIPTOR_SHA_A}\n"
        f"protoc_descriptor_lf_sha256={DESCRIPTOR_SHA_B}\n"
        "PROTOC=/work/protoc\n"
        "protoc_version_output=libprotoc 29.3\n"
        "protoc_version_exit_code=0\n"
        "product_executed=NO\n"
    )


def _clean_target_proof() -> str:
    return (
        "evidence_schema_version=1\n"
        "cargo_target_dir_absolute=/work/cargo-target\n"
        "required_entry_count=0\n"
        "observed_entry_count_host=0\n"
        "observed_entry_count_container=0\n"
        "proof_failed=no\n"
    )


def _build_command() -> str:
    return (
        "evidence_schema_version=1\n"
        f"exact_build_command={EXACT_BUILD_CMD}\n"
        "cargo_incremental=0\n"
        "working_directory=/src\n"
        "product_executed=NO\n"
    )


def _build_environment() -> str:
    return (
        "evidence_schema_version=1\n"
        "HOME=/root\n"
        "CARGO_HOME=/work/cargo-home\n"
        "CARGO_TARGET_DIR=/work/cargo-target\n"
        "CARGO_INCREMENTAL=0\n"
        "DOTSLASH_CACHE=/work/dotslash-cache\n"
        "PROTOC=/work/protoc\n"
        "docker_platform=linux/amd64\n"
        "network_mode=bridge\n"
        f"rust_image=docker.io/library/rust@sha256:{EXPECTED_IMAGE_DIGEST}\n"
    )


def _post_build_integrity() -> str:
    return (
        "evidence_schema_version=1\n"
        f"source_head_before={EXPECTED_GROK_COMMIT}\n"
        f"source_head_after={EXPECTED_GROK_COMMIT}\n"
        "source_clean_before=yes\n"
        "source_clean_after=yes\n"
        f"cargo_lock_sha256_before={EXPECTED_CARGO_LOCK_SHA256}\n"
        f"cargo_lock_sha256_after={EXPECTED_CARGO_LOCK_SHA256}\n"
        "source_or_lock_changed=no\n"
        "artifact_exists=yes\n"
        "evidence_inventory_complete=yes\n"
    )


def _witness_statement(*, ai_used: str = "yes", ai_detail: str = "AI used to draft templates; commands independently verified.", human_review: str = "yes") -> str:
    lines = [
        "evidence_schema_version=1",
        "witness_identity_or_handle=Jane Doe (@janedoe)",
        "not_package_owner=yes",
        "not_owner_side_reproducer=yes",
        "witness_controlled_host=yes",
        f"ai_assistance_used={ai_used}",
    ]
    if ai_detail:
        lines.append(f"ai_assistance_detail={ai_detail}")
    lines.extend(
        [
            f"human_review_completed={human_review}",
            "product_executed=NO",
            "ldd_used=NO",
        ]
    )
    return "\n".join(lines) + "\n"


def _witness_verdict(*, verdict_block: str = "Witness proposed verdict: INDETERMINATE\n") -> str:
    return (
        "evidence_schema_version=1\n"
        f"run_id={RUN_ID}\n"
        "package_tag=grok-build-witness-v1.0.0-rc3\n"
        f"weaver_forge_commit={WEAVER_COMMIT}\n"
        f"grok_build_commit={EXPECTED_GROK_COMMIT}\n"
        "product_executed=NO\n"
        "ldd_used=NO\n"
        "maintainer_intake_verdict=pending\n"
        "\n"
        f"{verdict_block}"
        "\n## Justification\n\n(reference classification precedence)\n"
    )


def _deviations(*, block: str = "deviation_state=NONE\n") -> str:
    return "evidence_schema_version=1\n" + block


def _redactions(*, block: str = "redaction_state=NONE\n") -> str:
    return "evidence_schema_version=1\nsemantic_integrity_declaration=yes\n" + block


# ---------------------------------------------------------------------------
# Outcome-sensitive fixture bodies
# ---------------------------------------------------------------------------


def _docker_exit_code(outcome: str, *, docker_exit_code: str = "0", failure_stage: str = "N/A") -> str:
    return (
        "evidence_schema_version=1\n"
        "docker_started_utc=2026-07-22T00:00:00Z\n"
        "docker_finished_utc=2026-07-22T01:00:00Z\n"
        f"docker_exit_code={docker_exit_code}\n"
        "container_platform=linux/amd64\n"
        "network_mode=bridge\n"
        "product_executed=NO\n"
        "ldd_used=NO\n"
        f"outcome={outcome}\n"
        f"failure_stage={failure_stage}\n"
    )


def _build_exit_code(outcome: str, *, cargo_started: str, build_status: str, cargo_exit_code: str, failure_stage: str) -> str:
    return (
        "evidence_schema_version=1\n"
        f"cargo_started={cargo_started}\n"
        f"outcome={outcome}\n"
        f"build_status={build_status}\n"
        f"cargo_exit_code={cargo_exit_code}\n"
        f"failure_stage={failure_stage}\n"
    )


def _build_timing(outcome: str, *, with_cargo: bool) -> str:
    lines = [
        "evidence_schema_version=1",
        f"outcome={outcome}",
        "docker_started_utc=2026-07-22T00:00:00Z",
        "docker_finished_utc=2026-07-22T01:00:00Z",
    ]
    if with_cargo:
        lines.append("cargo_started_utc=2026-07-22T00:05:00Z")
        lines.append("cargo_finished_utc=2026-07-22T00:55:00Z")
    return "\n".join(lines) + "\n"


def _artifact_identity(outcome: str) -> str:
    if outcome == "CARGO_SUCCEEDED_ARTIFACT_PRESENT":
        return (
            "evidence_schema_version=1\n"
            "applicable=yes\n"
            "artifact_present=yes\n"
            "product_executed=NO\n"
            "ldd_used=NO\n"
            "artifact_path=/work/cargo-target/debug/xai-grok-pager\n"
            "artifact_filename=xai-grok-pager\n"
            "artifact_size_bytes=600647920\n"
            f"artifact_sha256={ARTIFACT_SHA}\n"
        )
    if outcome == "CARGO_SUCCEEDED_ARTIFACT_MISSING":
        return (
            "evidence_schema_version=1\n"
            "applicable=yes\n"
            "artifact_present=no\n"
            "product_executed=NO\n"
            "ldd_used=NO\n"
            "reason=cargo reported success but no artifact was found at the expected path\n"
        )
    return (
        "evidence_schema_version=1\n"
        "applicable=no\n"
        "artifact_present=no\n"
        "product_executed=NO\n"
        "ldd_used=NO\n"
        "reason=cargo did not complete successfully; no artifact was produced\n"
    )


def _static_artifact_inspection(outcome: str) -> str:
    if outcome == "CARGO_SUCCEEDED_ARTIFACT_PRESENT":
        return (
            "evidence_schema_version=1\n"
            "inspection_applicable=yes\n"
            "artifact_present=yes\n"
            "artifact_path=/work/cargo-target/debug/xai-grok-pager\n"
            "file_output=ELF 64-bit LSB executable\n"
            "file_exit_code=0\n"
            "readelf_h=ELF Header\n"
            "readelf_h_exit_code=0\n"
            "readelf_n=Notes\n"
            "readelf_n_exit_code=0\n"
            "readelf_d=Dynamic\n"
            "readelf_d_exit_code=0\n"
            "objdump_f=file format elf64-x86-64\n"
            "objdump_f_exit_code=0\n"
            "product_executed=NO\n"
            "ldd_used=NO\n"
        )
    return (
        "evidence_schema_version=1\n"
        "inspection_applicable=no\n"
        "artifact_present=no\n"
        "reason=no artifact was produced for this outcome\n"
        "product_executed=NO\n"
        "ldd_used=NO\n"
    )


_OUTCOME_SPECS = {
    "BUILD_NOT_STARTED": dict(
        docker_exit_code="1",
        cargo_started="NO",
        build_status="BUILD_NOT_STARTED",
        cargo_exit_code="N/A",
        failure_stage="bootstrap_protoc_resolution",
        with_cargo_timing=False,
    ),
    "CARGO_FAILED": dict(
        docker_exit_code="101",
        cargo_started="YES",
        build_status="FAILED",
        cargo_exit_code="101",
        failure_stage="cargo_build",
        with_cargo_timing=True,
    ),
    "CARGO_SUCCEEDED_ARTIFACT_MISSING": dict(
        docker_exit_code="0",
        cargo_started="YES",
        build_status="COMPLETE",
        cargo_exit_code="0",
        failure_stage="artifact_missing",
        with_cargo_timing=True,
    ),
    "CARGO_SUCCEEDED_ARTIFACT_PRESENT": dict(
        docker_exit_code="0",
        cargo_started="YES",
        build_status="COMPLETE",
        cargo_exit_code="0",
        failure_stage="N/A",
        with_cargo_timing=True,
    ),
    "INFRASTRUCTURE_FAILURE": dict(
        docker_exit_code="125",
        cargo_started="NO",
        build_status="INFRASTRUCTURE_FAILURE",
        cargo_exit_code="N/A",
        failure_stage="docker_daemon_unreachable",
        with_cargo_timing=False,
    ),
}


def build_tree(outcome: str = "CARGO_SUCCEEDED_ARTIFACT_PRESENT", **overrides: str) -> dict[str, str]:
    """Return {filename: content} for a fully valid evidence tree at the
    given outcome. `overrides` replaces individual file bodies wholesale."""
    spec = _OUTCOME_SPECS[outcome]
    files = {
        "WEAVER_FORGE_PACKAGE_IDENTITY.txt": _weaver_forge_package_identity(),
        "ENVIRONMENT.txt": _environment(),
        "SOURCE_ACQUISITION.txt": _source_acquisition(),
        "SOURCE_IDENTITY.txt": _source_identity(),
        "IMAGE_IDENTITY.txt": _image_identity(),
        "BOOTSTRAP.txt": _bootstrap(),
        "CLEAN_TARGET_PROOF.txt": _clean_target_proof(),
        "BUILD_COMMAND.txt": _build_command(),
        "BUILD_ENVIRONMENT.txt": _build_environment(),
        "BUILD_STDOUT.txt": "cargo build stdout (synthetic)\n",
        "BUILD_STDERR.txt": "cargo build stderr (synthetic)\n",
        "DOCKER_EXIT_CODE.txt": _docker_exit_code(
            outcome, docker_exit_code=spec["docker_exit_code"], failure_stage=spec["failure_stage"]
        ),
        "BUILD_EXIT_CODE.txt": _build_exit_code(
            outcome,
            cargo_started=spec["cargo_started"],
            build_status=spec["build_status"],
            cargo_exit_code=spec["cargo_exit_code"],
            failure_stage=spec["failure_stage"],
        ),
        "BUILD_TIMING.txt": _build_timing(outcome, with_cargo=spec["with_cargo_timing"]),
        "CONTAINER_STDOUT.txt": "docker run stdout (synthetic)\n",
        "CONTAINER_STDERR.txt": "docker run stderr (synthetic)\n",
        "ARTIFACT_IDENTITY.txt": _artifact_identity(outcome),
        "STATIC_ARTIFACT_INSPECTION.txt": _static_artifact_inspection(outcome),
        "POST_BUILD_INTEGRITY.txt": _post_build_integrity(),
        "WITNESS_STATEMENT.md": _witness_statement(),
        "WITNESS_VERDICT.md": _witness_verdict(),
        "DEVIATIONS.txt": _deviations(),
        "REDACTIONS.md": _redactions(),
    }
    files.update(overrides)
    return files


def write_tree(root: Path, files: dict[str, str]) -> None:
    for name, body in files.items():
        (root / name).write_text(body, encoding="utf-8")
    write_manifest(root, files)


def write_manifest(root: Path, files: dict[str, str]) -> None:
    lines = []
    for name in files:
        if name == MANIFEST_NAME:
            continue
        digest = sha256_file(root / name)
        lines.append(f"{digest}  ./{name}")
    (root / MANIFEST_NAME).write_text("\n".join(lines) + "\n", encoding="utf-8")


class BaseTreeTests(unittest.TestCase):
    def make_tree(self, outcome: str = "CARGO_SUCCEEDED_ARTIFACT_PRESENT", **overrides: str) -> Path:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        write_tree(root, build_tree(outcome, **overrides))
        return root


# ---------------------------------------------------------------------------
# Fully valid packages per outcome
# ---------------------------------------------------------------------------


class ValidPackageTests(BaseTreeTests):
    def test_fully_valid_cargo_succeeded_artifact_present(self) -> None:
        root = self.make_tree("CARGO_SUCCEEDED_ARTIFACT_PRESENT")
        self.assertEqual(validate_dir(root), [])

    def test_valid_build_not_started(self) -> None:
        root = self.make_tree("BUILD_NOT_STARTED")
        self.assertEqual(validate_dir(root), [])

    def test_valid_cargo_failed(self) -> None:
        root = self.make_tree("CARGO_FAILED")
        self.assertEqual(validate_dir(root), [])

    def test_valid_artifact_missing(self) -> None:
        root = self.make_tree("CARGO_SUCCEEDED_ARTIFACT_MISSING")
        self.assertEqual(validate_dir(root), [])

    def test_valid_infrastructure_failure(self) -> None:
        root = self.make_tree("INFRASTRUCTURE_FAILURE")
        self.assertEqual(validate_dir(root), [])

    def test_each_outcome_schema_round_trip(self) -> None:
        for outcome in _OUTCOME_SPECS:
            with self.subTest(outcome=outcome):
                root = self.make_tree(outcome)
                self.assertEqual(validate_dir(root), [], msg=f"outcome={outcome}")


# ---------------------------------------------------------------------------
# Missing required files
# ---------------------------------------------------------------------------


class MissingFileTests(BaseTreeTests):
    def test_missing_source_acquisition_fails(self) -> None:
        root = self.make_tree()
        (root / "SOURCE_ACQUISITION.txt").unlink()
        errors = validate_dir(root)
        self.assertTrue(any("SOURCE_ACQUISITION" in e for e in errors))

    def test_missing_image_identity_fails(self) -> None:
        root = self.make_tree()
        (root / "IMAGE_IDENTITY.txt").unlink()
        errors = validate_dir(root)
        self.assertTrue(any("IMAGE_IDENTITY" in e for e in errors))

    def test_missing_environment_fails(self) -> None:
        root = self.make_tree()
        (root / "ENVIRONMENT.txt").unlink()
        errors = validate_dir(root)
        self.assertTrue(any("ENVIRONMENT" in e for e in errors))


# ---------------------------------------------------------------------------
# Per-file schema isolation: a generic/wrong body must not satisfy an
# unrelated file's schema (RB-020).
# ---------------------------------------------------------------------------


class SchemaIsolationTests(BaseTreeTests):
    def test_generic_body_does_not_satisfy_source_acquisition(self) -> None:
        root = self.make_tree(**{"SOURCE_ACQUISITION.txt": "evidence_schema_version=1\nproduct_executed=NO\nldd_used=NO\n"})
        errors = validate_dir(root)
        self.assertTrue(any("SOURCE_ACQUISITION.txt" in e and "missing required field" in e for e in errors))

    def test_generic_body_does_not_satisfy_image_identity(self) -> None:
        root = self.make_tree(**{"IMAGE_IDENTITY.txt": "evidence_schema_version=1\nproduct_executed=NO\nldd_used=NO\n"})
        errors = validate_dir(root)
        self.assertTrue(any("IMAGE_IDENTITY.txt" in e and "missing required field" in e for e in errors))


# ---------------------------------------------------------------------------
# Manifest grammar
# ---------------------------------------------------------------------------


class ManifestGrammarTests(BaseTreeTests):
    def _manifest_lines(self, root: Path) -> list[str]:
        return (root / MANIFEST_NAME).read_text(encoding="utf-8").splitlines()

    def _rewrite_manifest(self, root: Path, lines: list[str]) -> None:
        (root / MANIFEST_NAME).write_text("\n".join(lines) + "\n", encoding="utf-8")

    def test_wrong_hash_fails(self) -> None:
        root = self.make_tree()
        manifest = root / MANIFEST_NAME
        text = manifest.read_text(encoding="utf-8")
        manifest.write_text(text.replace("0", "1", 1), encoding="utf-8")
        errors = validate_dir(root)
        self.assertTrue(any("hash mismatch" in e for e in errors))

    def test_missing_manifest_entry_fails(self) -> None:
        root = self.make_tree()
        lines = [ln for ln in self._manifest_lines(root) if "DEVIATIONS.txt" not in ln]
        self._rewrite_manifest(root, lines)
        errors = validate_dir(root)
        self.assertTrue(any("missing mandatory entry" in e for e in errors))

    def test_duplicate_entry_fails(self) -> None:
        root = self.make_tree()
        lines = self._manifest_lines(root)
        first = lines[0]
        self._rewrite_manifest(root, lines + [first])
        errors = validate_dir(root)
        self.assertTrue(any("duplicate entry" in e for e in errors))

    def test_unix_absolute_path_fails(self) -> None:
        root = self.make_tree()
        lines = self._manifest_lines(root)
        digest = lines[0].split()[0]
        lines[0] = f"{digest}  /etc/passwd"
        self._rewrite_manifest(root, lines)
        errors = validate_dir(root)
        self.assertTrue(any("relative" in e or "malformed" in e for e in errors))

    def test_windows_absolute_path_fails(self) -> None:
        root = self.make_tree()
        lines = self._manifest_lines(root)
        digest = lines[0].split()[0]
        lines[0] = f"{digest}  C:/evidence/WEAVER_FORGE_PACKAGE_IDENTITY.txt"
        self._rewrite_manifest(root, lines)
        errors = validate_dir(root)
        self.assertTrue(any("relative" in e or "malformed" in e for e in errors))

    def test_parent_traversal_fails(self) -> None:
        root = self.make_tree()
        lines = self._manifest_lines(root)
        digest = lines[0].split()[0]
        lines[0] = f"{digest}  ./../escape.txt"
        self._rewrite_manifest(root, lines)
        errors = validate_dir(root)
        self.assertTrue(any("parent traversal" in e for e in errors))

    def test_manifest_self_entry_fails(self) -> None:
        root = self.make_tree()
        lines = self._manifest_lines(root)
        digest = lines[0].split()[0]
        lines.append(f"{digest}  ./{MANIFEST_NAME}")
        self._rewrite_manifest(root, lines)
        errors = validate_dir(root)
        self.assertTrue(any("must not list itself" in e for e in errors))

    def test_unsafe_filename_fails(self) -> None:
        root = self.make_tree()
        lines = self._manifest_lines(root)
        digest = lines[0].split()[0]
        lines[0] = f"{digest}  ./weird$name!.txt"
        self._rewrite_manifest(root, lines)
        errors = validate_dir(root)
        self.assertTrue(any("unsafe filename" in e for e in errors))

    def test_missing_listed_file_fails(self) -> None:
        root = self.make_tree()
        lines = self._manifest_lines(root)
        digest = lines[0].split()[0]
        lines.append(f"{digest}  ./NOT_ON_DISK.txt")
        self._rewrite_manifest(root, lines)
        errors = validate_dir(root)
        self.assertTrue(any("missing on disk" in e for e in errors))

    def test_unexpected_unlisted_file_fails(self) -> None:
        root = self.make_tree()
        (root / "EXTRA_UNLISTED.txt").write_text("surprise\n", encoding="utf-8")
        errors = validate_dir(root)
        self.assertTrue(any("Unlisted regular evidence file" in e for e in errors))

    def test_extra_manifest_tokens_fail(self) -> None:
        root = self.make_tree()
        lines = self._manifest_lines(root)
        digest = lines[0].split()[0]
        lines[0] = f"{digest}  ./WEAVER_FORGE_PACKAGE_IDENTITY.txt  extra_token"
        self._rewrite_manifest(root, lines)
        errors = validate_dir(root)
        self.assertTrue(any("extra tokens" in e or "malformed" in e for e in errors))

    def test_uppercase_digest_fails(self) -> None:
        root = self.make_tree()
        lines = self._manifest_lines(root)
        digest, rel = lines[0].split("  ", 1)
        lines[0] = f"{digest.upper()}  {rel}"
        self._rewrite_manifest(root, lines)
        errors = validate_dir(root)
        self.assertTrue(any("lowercase" in e for e in errors))

    def test_backslash_path_fails(self) -> None:
        root = self.make_tree()
        lines = self._manifest_lines(root)
        digest = lines[0].split()[0]
        lines[0] = f"{digest}  .\\WEAVER_FORGE_PACKAGE_IDENTITY.txt"
        self._rewrite_manifest(root, lines)
        errors = validate_dir(root)
        self.assertTrue(any("backslash" in e for e in errors))

    def test_symlink_rejected(self) -> None:
        root = self.make_tree()
        target = root / "WEAVER_FORGE_PACKAGE_IDENTITY.txt"
        link = root / "SYMLINK_EVIDENCE.txt"
        try:
            link.symlink_to(target)
        except OSError:
            self.skipTest("Symlink creation not permitted in this environment (insufficient privilege)")
        errors = validate_dir(root)
        self.assertTrue(any("Symlink" in e for e in errors))


# ---------------------------------------------------------------------------
# Verdict parsing
# ---------------------------------------------------------------------------


class VerdictParsingTests(unittest.TestCase):
    def test_exact_uppercase_pass_valid(self) -> None:
        matches, errs = parse_verdict_selection("Witness proposed verdict: PASS\n")
        self.assertEqual(matches, ["PASS"])
        self.assertEqual(errs, [])

    def test_exact_uppercase_partial_valid(self) -> None:
        matches, errs = parse_verdict_selection("Witness proposed verdict: PARTIAL\n")
        self.assertEqual(matches, ["PARTIAL"])
        self.assertEqual(errs, [])

    def test_exact_uppercase_fail_valid(self) -> None:
        matches, errs = parse_verdict_selection("Witness proposed verdict: FAIL\n")
        self.assertEqual(matches, ["FAIL"])
        self.assertEqual(errs, [])

    def test_exact_uppercase_indeterminate_valid(self) -> None:
        matches, errs = parse_verdict_selection("Witness proposed verdict: INDETERMINATE\n")
        self.assertEqual(matches, ["INDETERMINATE"])
        self.assertEqual(errs, [])

    def test_missing_verdict_fails(self) -> None:
        _, errs = parse_verdict_selection("Discussion: no formal selection line here.\n")
        self.assertTrue(errs)

    def test_duplicate_verdict_fails(self) -> None:
        text = "Witness proposed verdict: PASS\nWitness proposed verdict: FAIL\n"
        matches, errs = parse_verdict_selection(text)
        self.assertEqual(len(matches), 2)
        self.assertTrue(any("Duplicate" in e for e in errs))

    def test_lowercase_verdict_rejected(self) -> None:
        _, errs = parse_verdict_selection("Witness proposed verdict: pass\n")
        self.assertTrue(any("Invalid" in e for e in errs))

    def test_mixed_case_verdict_rejected(self) -> None:
        _, errs = parse_verdict_selection("Witness proposed verdict: Pass\n")
        self.assertTrue(any("Invalid" in e for e in errs))

    def test_invalid_verdict_value_rejected(self) -> None:
        _, errs = parse_verdict_selection("Witness proposed verdict: MAYBE\n")
        self.assertTrue(any("Invalid" in e for e in errs))

    def test_explanatory_words_elsewhere_still_valid_if_exact_line_present(self) -> None:
        text = (
            "Discussion: some might argue this should pass, others say Fail.\n"
            "Witness proposed verdict: PASS\n"
            "Further discussion mentions fail and PARTIAL informally.\n"
        )
        matches, errs = parse_verdict_selection(text)
        self.assertEqual(matches, ["PASS"])
        self.assertEqual(errs, [])


class WitnessVerdictFileTests(BaseTreeTests):
    def test_explanatory_words_in_full_tree_still_passes(self) -> None:
        body = _witness_verdict(
            verdict_block=(
                "Some background: a pass here would be surprising given fail-prone history.\n\n"
                "Witness proposed verdict: PASS\n"
            )
        )
        root = self.make_tree(**{"WITNESS_VERDICT.md": body})
        self.assertEqual(validate_dir(root), [])

    def test_lowercase_verdict_in_full_tree_fails(self) -> None:
        body = _witness_verdict(verdict_block="Witness proposed verdict: pass\n")
        root = self.make_tree(**{"WITNESS_VERDICT.md": body})
        errors = validate_dir(root)
        self.assertTrue(any("Invalid witness proposed verdict" in e for e in errors))

    def test_missing_maintainer_intake_pending_fails(self) -> None:
        body = _witness_verdict().replace("maintainer_intake_verdict=pending\n", "maintainer_intake_verdict=approved\n")
        root = self.make_tree(**{"WITNESS_VERDICT.md": body})
        errors = validate_dir(root)
        self.assertTrue(any("maintainer_intake_verdict" in e for e in errors))

    def test_wrong_grok_build_commit_fails(self) -> None:
        body = _witness_verdict().replace(EXPECTED_GROK_COMMIT, "0" * 40)
        root = self.make_tree(**{"WITNESS_VERDICT.md": body})
        errors = validate_dir(root)
        self.assertTrue(any("grok_build_commit" in e for e in errors))


# ---------------------------------------------------------------------------
# WITNESS_STATEMENT.md — independence, AI disclosure, human review
# ---------------------------------------------------------------------------


class WitnessStatementTests(BaseTreeTests):
    def test_missing_independence_statement_fails(self) -> None:
        body = _witness_statement().replace("not_package_owner=yes\n", "")
        root = self.make_tree(**{"WITNESS_STATEMENT.md": body})
        errors = validate_dir(root)
        self.assertTrue(any("not_package_owner" in e for e in errors))

    def test_not_package_owner_no_fails(self) -> None:
        body = _witness_statement().replace("not_package_owner=yes", "not_package_owner=no")
        root = self.make_tree(**{"WITNESS_STATEMENT.md": body})
        errors = validate_dir(root)
        self.assertTrue(any("not_package_owner" in e for e in errors))

    def test_ai_assistance_yes_with_detail_passes(self) -> None:
        body = _witness_statement(ai_used="yes", ai_detail="Used AI to format tables; commands run manually.")
        root = self.make_tree(**{"WITNESS_STATEMENT.md": body})
        self.assertEqual(validate_dir(root), [])

    def test_ai_assistance_yes_without_detail_fails(self) -> None:
        body = _witness_statement(ai_used="yes", ai_detail="")
        root = self.make_tree(**{"WITNESS_STATEMENT.md": body})
        errors = validate_dir(root)
        self.assertTrue(any("ai_assistance_detail" in e for e in errors))

    def test_ai_assistance_no_without_detail_passes(self) -> None:
        body = _witness_statement(ai_used="no", ai_detail="")
        root = self.make_tree(**{"WITNESS_STATEMENT.md": body})
        self.assertEqual(validate_dir(root), [])

    def test_human_review_no_fails(self) -> None:
        body = _witness_statement(human_review="no")
        root = self.make_tree(**{"WITNESS_STATEMENT.md": body})
        errors = validate_dir(root)
        self.assertTrue(any("human_review_completed" in e for e in errors))


# ---------------------------------------------------------------------------
# DEVIATIONS.txt — severity ceilings
# ---------------------------------------------------------------------------


class DeviationsTests(BaseTreeTests):
    def test_deviation_state_none_passes(self) -> None:
        root = self.make_tree(**{"DEVIATIONS.txt": _deviations()})
        self.assertEqual(validate_dir(root), [])

    def test_nonmaterial_disclosed_with_pass_ceiling_ok(self) -> None:
        block = (
            "deviation_state=PRESENT\n"
            "deviation_1_description=Used -j 2 instead of default parallelism\n"
            "deviation_1_severity=NONMATERIAL_DISCLOSED\n"
            "deviation_1_canonical_identity_impact=no\n"
            "deviation_1_verdict_ceiling=PASS\n"
        )
        root = self.make_tree(**{"DEVIATIONS.txt": _deviations(block=block)})
        self.assertEqual(validate_dir(root), [])

    def test_material_noncanonical_with_pass_ceiling_fails(self) -> None:
        block = (
            "deviation_state=PRESENT\n"
            "deviation_1_description=Built a different crate than pinned\n"
            "deviation_1_severity=MATERIAL_NONCANONICAL\n"
            "deviation_1_canonical_identity_impact=yes\n"
            "deviation_1_verdict_ceiling=PASS\n"
        )
        root = self.make_tree(**{"DEVIATIONS.txt": _deviations(block=block)})
        errors = validate_dir(root)
        self.assertTrue(any("forbids a PASS verdict_ceiling" in e for e in errors))

    def test_material_noncanonical_with_partial_ceiling_ok(self) -> None:
        block = (
            "deviation_state=PRESENT\n"
            "deviation_1_description=Built a different crate than pinned\n"
            "deviation_1_severity=MATERIAL_NONCANONICAL\n"
            "deviation_1_canonical_identity_impact=yes\n"
            "deviation_1_verdict_ceiling=PARTIAL\n"
        )
        root = self.make_tree(**{"DEVIATIONS.txt": _deviations(block=block)})
        self.assertEqual(validate_dir(root), [])

    def test_prohibited_with_fail_ceiling_ok(self) -> None:
        block = (
            "deviation_state=PRESENT\n"
            "deviation_1_description=Executed the product binary\n"
            "deviation_1_severity=PROHIBITED\n"
            "deviation_1_canonical_identity_impact=yes\n"
            "deviation_1_verdict_ceiling=FAIL\n"
        )
        root = self.make_tree(**{"DEVIATIONS.txt": _deviations(block=block)})
        self.assertEqual(validate_dir(root), [])

    def test_prohibited_with_non_fail_ceiling_fails(self) -> None:
        block = (
            "deviation_state=PRESENT\n"
            "deviation_1_description=Executed the product binary\n"
            "deviation_1_severity=PROHIBITED\n"
            "deviation_1_canonical_identity_impact=yes\n"
            "deviation_1_verdict_ceiling=INDETERMINATE\n"
        )
        root = self.make_tree(**{"DEVIATIONS.txt": _deviations(block=block)})
        errors = validate_dir(root)
        self.assertTrue(any("requires verdict_ceiling=FAIL" in e for e in errors))

    def test_present_state_without_entries_fails(self) -> None:
        root = self.make_tree(**{"DEVIATIONS.txt": _deviations(block="deviation_state=PRESENT\n")})
        errors = validate_dir(root)
        self.assertTrue(any("no enumerated deviation_<n>_* entries" in e for e in errors))

    def test_invalid_deviation_state_fails(self) -> None:
        root = self.make_tree(**{"DEVIATIONS.txt": _deviations(block="deviation_state=MAYBE\n")})
        errors = validate_dir(root)
        self.assertTrue(any("deviation_state must be NONE or PRESENT" in e for e in errors))


# ---------------------------------------------------------------------------
# REDACTIONS.md
# ---------------------------------------------------------------------------


class RedactionsTests(BaseTreeTests):
    def test_redaction_state_none_passes(self) -> None:
        root = self.make_tree(**{"REDACTIONS.md": _redactions()})
        self.assertEqual(validate_dir(root), [])

    def test_valid_disclosed_redaction_passes(self) -> None:
        block = (
            "redaction_state=PRESENT\n"
            "redaction_1_file=ENVIRONMENT.txt\n"
            "redaction_1_field=host_docker_client_version\n"
            "redaction_1_reason=Contains an internal build label unrelated to the pin\n"
            "redaction_1_replacement_marker=[REDACTED: internal build label]\n"
        )
        root = self.make_tree(**{"REDACTIONS.md": _redactions(block=block)})
        self.assertEqual(validate_dir(root), [])

    def test_prohibited_redaction_of_commit_fails(self) -> None:
        block = (
            "redaction_state=PRESENT\n"
            "redaction_1_file=SOURCE_IDENTITY.txt\n"
            "redaction_1_field=grok_build_commit_observed\n"
            "redaction_1_reason=Witness preferred not to disclose the observed commit\n"
            "redaction_1_replacement_marker=[REDACTED: commit]\n"
        )
        root = self.make_tree(**{"REDACTIONS.md": _redactions(block=block)})
        errors = validate_dir(root)
        self.assertTrue(any("prohibited category" in e for e in errors))

    def test_missing_visible_marker_fails(self) -> None:
        block = (
            "redaction_state=PRESENT\n"
            "redaction_1_file=ENVIRONMENT.txt\n"
            "redaction_1_field=host_ram_gib\n"
            "redaction_1_reason=Unrelated host detail\n"
            "redaction_1_replacement_marker=removed\n"
        )
        root = self.make_tree(**{"REDACTIONS.md": _redactions(block=block)})
        errors = validate_dir(root)
        self.assertTrue(any("visible" in e for e in errors))

    def test_missing_semantic_integrity_declaration_fails(self) -> None:
        body = "evidence_schema_version=1\nredaction_state=NONE\n"
        root = self.make_tree(**{"REDACTIONS.md": body})
        errors = validate_dir(root)
        self.assertTrue(any("semantic_integrity_declaration" in e for e in errors))


# ---------------------------------------------------------------------------
# Outcome cross-checks
# ---------------------------------------------------------------------------


class OutcomeCrossCheckTests(BaseTreeTests):
    def test_docker_outcome_mismatch_fails(self) -> None:
        root = self.make_tree("CARGO_SUCCEEDED_ARTIFACT_PRESENT")
        text = (root / "DOCKER_EXIT_CODE.txt").read_text(encoding="utf-8")
        text = text.replace(
            "outcome=CARGO_SUCCEEDED_ARTIFACT_PRESENT", "outcome=CARGO_SUCCEEDED_ARTIFACT_MISSING"
        )
        (root / "DOCKER_EXIT_CODE.txt").write_text(text, encoding="utf-8")
        write_manifest(root, {n: (root / n).read_text(encoding="utf-8") for n in REQUIRED_FILES if n != MANIFEST_NAME})
        errors = validate_dir(root)
        self.assertTrue(any("outcome" in e and "does not match" in e for e in errors))

    def test_wrong_cargo_exit_code_for_success_fails(self) -> None:
        root = self.make_tree(
            "CARGO_SUCCEEDED_ARTIFACT_PRESENT",
            **{
                "BUILD_EXIT_CODE.txt": _build_exit_code(
                    "CARGO_SUCCEEDED_ARTIFACT_PRESENT",
                    cargo_started="YES",
                    build_status="COMPLETE",
                    cargo_exit_code="1",
                    failure_stage="N/A",
                )
            },
        )
        errors = validate_dir(root)
        self.assertTrue(any("cargo_exit_code must be '0'" in e for e in errors))

    def test_zero_exit_code_for_cargo_failed_fails(self) -> None:
        root = self.make_tree(
            "CARGO_FAILED",
            **{
                "BUILD_EXIT_CODE.txt": _build_exit_code(
                    "CARGO_FAILED",
                    cargo_started="YES",
                    build_status="FAILED",
                    cargo_exit_code="0",
                    failure_stage="cargo_build",
                )
            },
        )
        errors = validate_dir(root)
        self.assertTrue(any("nonzero numeric value" in e for e in errors))

    def test_bare_numeric_docker_exit_code_file_fails(self) -> None:
        root = self.make_tree("CARGO_SUCCEEDED_ARTIFACT_PRESENT", **{"DOCKER_EXIT_CODE.txt": "0\n"})
        errors = validate_dir(root)
        self.assertTrue(any("bare unlabelled numeric-only file" in e for e in errors))


# ---------------------------------------------------------------------------
# main()
# ---------------------------------------------------------------------------


class MainTests(BaseTreeTests):
    def test_main_returns_zero_on_success(self) -> None:
        root = self.make_tree()
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = main([str(root)])
        self.assertEqual(rc, 0)
        self.assertIn("STRUCTURAL VALIDATION: PASS", buf.getvalue())

    def test_main_returns_one_on_failure(self) -> None:
        root = self.make_tree()
        (root / "SOURCE_ACQUISITION.txt").unlink()
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = main([str(root)])
        self.assertEqual(rc, 1)
        self.assertIn("STRUCTURAL VALIDATION: FAIL", buf.getvalue())

    def test_report_text_lists_errors(self) -> None:
        root = self.make_tree()
        (root / "IMAGE_IDENTITY.txt").unlink()
        buf = io.StringIO()
        with redirect_stdout(buf):
            main([str(root)])
        output = buf.getvalue()
        self.assertIn("STRUCTURAL VALIDATION: FAIL", output)
        self.assertIn("IMAGE_IDENTITY.txt", output)
        self.assertIn("does not prove", output)


# ---------------------------------------------------------------------------
# C2E-4A release-identity self-reference policy (static / synthetic)
# ---------------------------------------------------------------------------


class ReleaseIdentityPolicyTests(BaseTreeTests):
    """Static checks: tag is authority; no embedded future self-commit placeholder;
    normative release-facing wording is time-stable (C2E-4B)."""

    NORMATIVE_RELATIVE_PATHS = (
        "README.md",
        "WITNESS_PACKAGE_VERSION.md",
        "WITNESS_REQUIREMENTS.md",
        "WITNESS_RUNBOOK.md",
        "WITNESS_CLASSIFICATION.md",
        "WITNESS_SUBMISSION.md",
        "WITNESS_PACKAGE_MANIFEST.md",
        "PACKAGE_READINESS_POLICY.md",
        "MAINTAINER_INTAKE_POLICY.md",
        "PACKAGE_FILE_MANIFEST.txt",
        "scripts/VALIDATOR.md",
        "scripts/run_witness_narrow_build.sh",
    )

    # Patterns that would become false inside a published tagged snapshot if used as
    # current operational status of the rc3 package/tag itself.
    STALE_RC3_STATUS_PATTERNS = (
        re.compile(r"proposed\s+(annotated\s+)?tag", re.IGNORECASE),
        re.compile(r"tag\s+does\s+not\s+(yet\s+)?exist", re.IGNORECASE),
        re.compile(r"does\s+not\s+yet\s+exist", re.IGNORECASE),
        re.compile(r"rc3\s+tag\s+is\s+pending", re.IGNORECASE),
        re.compile(r"tag\s+pending", re.IGNORECASE),
        re.compile(r"current\s+candidate\s+`?1\.0\.0-rc3", re.IGNORECASE),
        re.compile(r"rc3\s+candidate\s+drafting", re.IGNORECASE),
    )

    @classmethod
    def setUpClass(cls) -> None:
        cls.package = Path(__file__).resolve().parents[2]
        cls.host_script = cls.package / "scripts" / "run_witness_narrow_build.sh"
        cls.host_text = cls.host_script.read_text(encoding="utf-8")
        cls.version_doc = (cls.package / "WITNESS_PACKAGE_VERSION.md").read_text(encoding="utf-8")
        cls.runbook = (cls.package / "WITNESS_RUNBOOK.md").read_text(encoding="utf-8")
        cls.requirements = (cls.package / "WITNESS_REQUIREMENTS.md").read_text(encoding="utf-8")
        cls.normative_texts: dict[str, str] = {}
        for rel in cls.NORMATIVE_RELATIVE_PATHS:
            path = cls.package / rel
            cls.normative_texts[rel] = path.read_text(encoding="utf-8")
        repo_root = cls.package.parents[2]
        cls.completion_note = (
            repo_root
            / "docs"
            / "GROK_BUILD_WITNESS_RC2_INTEGRATED_BLIND_AUDIT_REMEDIATION_COMPLETION_NOTE.md"
        ).read_text(encoding="utf-8")

    def test_canonical_rc3_tag_exact(self) -> None:
        self.assertIn(
            'CANONICAL_WEAVER_FORGE_TAG="grok-build-witness-v1.0.0-rc3"',
            self.host_text,
        )

    def test_no_required_self_commit_placeholder(self) -> None:
        self.assertNotIn("PLACEHOLDER_UNTIL_RC3_TAGGED", self.host_text)
        self.assertNotRegex(
            self.host_text,
            r"(?m)^\s*(readonly\s+)?CANONICAL_WEAVER_FORGE_EXPECTED_COMMIT=",
        )

    def test_package_commit_resolved_from_tag(self) -> None:
        self.assertIn("refs/tags/${EFFECTIVE_WEAVER_FORGE_TAG}^{commit}", self.host_text)
        self.assertIn("package_commit_authority=annotated_tag_resolution", self.host_text)

    def test_detached_head_must_equal_resolved_tag_commit(self) -> None:
        self.assertIn("checkout --detach", self.host_text)
        self.assertIn("tag_head_match", self.host_text)
        self.assertIn(
            "Detached HEAD (${WF_HEAD}) does not equal resolved tag commit",
            self.host_text,
        )

    def test_clean_package_clone_required(self) -> None:
        self.assertIn(
            "Weaver Forge package clone tree is not clean after detached checkout",
            self.host_text,
        )

    def test_optional_external_expected_commit_mismatch_fails(self) -> None:
        self.assertIn("WEAVER_FORGE_EXTERNAL_EXPECTED_COMMIT", self.host_text)
        self.assertIn("WEAVER_FORGE_EXTERNAL_EXPECTED_COMMIT mismatch", self.host_text)

    def test_canonical_execution_without_embedded_expected_self_commit(self) -> None:
        self.assertIn("package_commit_authority=annotated_tag_resolution", self.host_text)
        combined = self.version_doc + self.runbook + self.requirements
        self.assertNotIn("Fill `CANONICAL_WEAVER_FORGE_EXPECTED_COMMIT`", combined)
        self.assertNotIn("PLACEHOLDER_UNTIL_RC3_TAGGED", combined)

    def test_no_future_fill_own_commit_instruction(self) -> None:
        combined = self.version_doc + self.runbook + self.requirements
        pattern = re.compile(
            r"fill.{0,40}(expected|own|self).{0,20}commit.{0,40}(tag|package)",
            re.IGNORECASE,
        )
        self.assertIsNone(pattern.search(combined), "found fill-own-commit instruction")

    def test_normative_files_have_no_stale_rc3_absence_assertions(self) -> None:
        for rel, text in self.normative_texts.items():
            for pattern in self.STALE_RC3_STATUS_PATTERNS:
                match = pattern.search(text)
                if match is not None:
                    self.fail(f"{rel} contains stale rc3 status wording: {match.group(0)!r}")

    def test_normative_files_do_not_instruct_amend_or_recreate_rc3(self) -> None:
        instruct = re.compile(
            r"(?i)(must|should|then)\s+(amend|recreate|force-update)\s+(the\s+)?(rc3|tag)",
        )
        for rel, text in self.normative_texts.items():
            self.assertIsNone(
                instruct.search(text),
                f"{rel} instructs amending/recreating/force-updating rc3",
            )

    def test_later_main_status_outside_tagged_snapshot(self) -> None:
        self.assertRegex(
            self.version_doc,
            r"(?i)(not\s+part\s+of\s+the\s+rc3\s+tagged\s+snapshot|outside\s+the\s+(rc3\s+)?tagged\s+snapshot)",
        )

    def test_historical_pre_tag_label_in_completion_note(self) -> None:
        self.assertIn("HISTORICAL PRE-TAG STATE", self.completion_note)

    def test_tag_head_mismatch_fails_validation(self) -> None:
        bad_identity = (
            "evidence_schema_version=1\n"
            f"witness_id={WITNESS_ID}\n"
            f"run_id={RUN_ID}\n"
            "package_version=1.0.0-rc3\n"
            "weaver_forge_url=https://github.com/chrono-vector/weaver-forge.git\n"
            "weaver_forge_tag_requested=grok-build-witness-v1.0.0-rc3\n"
            f"weaver_forge_commit_resolved={WEAVER_COMMIT}\n"
            f"package_clone_head={'a' * 40}\n"
            "package_clone_detached=yes\n"
            "package_clone_clean_status=yes\n"
            "tag_head_match=no\n"
            "package_commit_authority=annotated_tag_resolution\n"
            f"grok_build_source_commit_expected={EXPECTED_GROK_COMMIT}\n"
            "canonical_run=yes\n"
        )
        root = self.make_tree(**{"WEAVER_FORGE_PACKAGE_IDENTITY.txt": bad_identity})
        errors = validate_dir(root)
        self.assertTrue(
            any("tag_head_match" in e or "must equal weaver_forge_commit_resolved" in e for e in errors),
            errors,
        )

    def test_placeholder_in_evidence_fails(self) -> None:
        root = self.make_tree()
        path = root / "DEVIATIONS.txt"
        path.write_text(
            path.read_text(encoding="utf-8") + "note=PLACEHOLDER_UNTIL_RC3_TAGGED\n",
            encoding="utf-8",
        )
        errors = validate_dir(root)
        self.assertTrue(
            any("PLACEHOLDER_UNTIL_RC3_TAGGED" in e or "hash mismatch" in e for e in errors),
            errors,
        )


if __name__ == "__main__":
    unittest.main()
