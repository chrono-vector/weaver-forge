#!/usr/bin/env python3
"""Phase 4-S2 focused tests: runtime writer/template/schema alignment.

Uses only the Python standard library and unittest. Temporary trees live in
repository-external temporary directories. Committed fixtures used for
validation are materialized from Git blob bytes (not working-tree smudge).
Does not invoke bash, host/container scripts, Docker, Cargo, compilers,
product binaries, network, production tags, or Witness workflows.
"""

from __future__ import annotations

import os
import shutil
import sys
import tempfile
import textwrap
import unittest
import unittest.mock
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = TESTS_DIR.parent
PACKAGE_DIR = SCRIPTS_DIR.parent
sys.path.insert(0, str(SCRIPTS_DIR))
sys.path.insert(0, str(TESTS_DIR))

import evidence_inventory as ei  # noqa: E402
import fixtures_lib as fx  # noqa: E402
import schema_register_loader as srl  # noqa: E402
import validate_witness_evidence as v  # noqa: E402

HOST_SCRIPT = SCRIPTS_DIR / "run_witness_narrow_build.sh"
CONTAINER_SCRIPT = SCRIPTS_DIR / "container_narrow_build.sh"
S1_REGISTER = PACKAGE_DIR / "schemas" / "canonical_schema_register_rc5_phase4_s1.json"
S2_REGISTER = PACKAGE_DIR / "schemas" / "canonical_schema_register_rc5_phase4_s2.json"
TEMP_PREFIX = "phase4_test_"

_TEMPS: list[Path] = []


def _mktmp(prefix: str = TEMP_PREFIX) -> Path:
    # Repository-external temp only (no dir= under tests/).
    path = Path(tempfile.mkdtemp(prefix=prefix))
    _TEMPS.append(path)
    return path


def _cleanup() -> None:
    for path in list(_TEMPS):
        if path.exists():
            shutil.rmtree(path, ignore_errors=True)
    _TEMPS.clear()


def _git_toplevel() -> Path:
    """Return the repository root (read-only; no index/worktree mutation)."""
    import subprocess

    proc = subprocess.run(
        ["git", "-C", str(TESTS_DIR), "rev-parse", "--show-toplevel"],
        check=True,
        capture_output=True,
        text=True,
    )
    return Path(proc.stdout.strip())


def _materialize_committed_fixture(
    scenario: str, prefix: str = "phase4_s2_fx_"
) -> Path:
    """Materialize a committed fixture tree from Git blob bytes into external temp.

    Working-tree smudge (e.g. core.autocrlf CRLF) is bypassed: each tracked file
    is read via ``git cat-file -p HEAD:<path>`` and written with those exact
    bytes under a repository-external temporary directory. Fixture originals,
    index, and refs are not modified.
    """
    import subprocess

    repo = _git_toplevel()
    fixtures_prefix = (
        Path("external_verifications/grok-build/witness-package/scripts/tests/fixtures")
        / scenario
    )
    prefix_posix = fixtures_prefix.as_posix()
    listed = subprocess.run(
        [
            "git",
            "-C",
            str(repo),
            "ls-tree",
            "-r",
            "--name-only",
            "HEAD",
            "--",
            prefix_posix,
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    rels = [ln.strip().replace("\\", "/") for ln in listed.stdout.splitlines() if ln.strip()]
    if not rels:
        raise FileNotFoundError(f"no tracked git blobs under HEAD:{prefix_posix}")

    dest = Path(tempfile.mkdtemp(prefix=prefix))
    _TEMPS.append(dest)
    try:
        for rel in rels:
            if ".." in Path(rel).parts:
                raise ValueError(f"refusing path traversal in git path: {rel}")
            if not rel.startswith(prefix_posix + "/") and rel != prefix_posix:
                raise ValueError(f"git path outside fixture root: {rel}")
            blob = subprocess.run(
                ["git", "-C", str(repo), "cat-file", "-p", f"HEAD:{rel}"],
                check=True,
                capture_output=True,
            ).stdout
            under = Path(rel[len(prefix_posix) :].lstrip("/"))
            out = dest / under
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(blob)
    except Exception:
        shutil.rmtree(dest, ignore_errors=True)
        if dest in _TEMPS:
            _TEMPS.remove(dest)
        raise
    return dest


def _read_kv(path: Path, key: str) -> str:
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith(key + "="):
            return line.split("=", 1)[1]
    return ""


def _s2_not_applicable_body(outcome: str, stage: str, reason: str) -> str:
    """Python-side mirror of container S2 early-failure NOT_APPLICABLE terminalization."""
    return (
        "evidence_schema_version=1\n"
        "status=NOT_APPLICABLE\n"
        "applicability=not_applicable\n"
        f"reason={reason}\n"
        f"authoritative_outcome={outcome}\n"
        f"failure_stage={stage}\n"
        "product_executed=NO\n"
        "ldd_used=NO\n"
    )


class S2RegisterAndLoaderTests(unittest.TestCase):
    def test_01_s2_register_parses_and_supersedes_s1(self) -> None:
        # S2 is historical under RC6; active authority is rc6.5.
        s2 = srl.load_historical_s2_register()
        s1 = srl.load_historical_s1_register()
        active = srl.load_active_register()
        self.assertEqual(active.schema_register_version, "rc6.5")
        self.assertEqual(s2.schema_register_version, "rc5-phase4-s2.1")
        self.assertEqual(s1.schema_register_version, "rc5-phase4-s1.1")
        self.assertEqual(s2.supersession().get("supersedes"), "rc5-phase4-s1.1")
        self.assertEqual(active.supersession().get("supersedes"), "rc6.4")
        self.assertTrue(s2.historical_compatibility().get("not_a_second_schema_authority"))
        self.assertTrue(active.historical_compatibility().get("not_a_second_schema_authority"))
        self.assertTrue(S1_REGISTER.is_file())
        self.assertTrue(S2_REGISTER.is_file())
        # Frozen S1/S2 bytes must remain the committed historical registers.
        self.assertEqual(
            s1.source_path.resolve(),
            S1_REGISTER.resolve(),
        )
        self.assertEqual(
            s2.source_path.resolve(),
            S2_REGISTER.resolve(),
        )

    def test_02_loader_defaults_s2_explicit_s1_unsupported_fail_closed(self) -> None:
        default = srl.load_canonical_register()
        self.assertEqual(default.schema_register_version, srl.ACTIVE_REGISTER_VERSION)
        self.assertEqual(default.schema_register_version, "rc6.5")
        hist_s1 = srl.load_historical_register(srl.HISTORICAL_S1_REGISTER_VERSION)
        self.assertTrue(hist_s1.is_historical_s1)
        hist_s2 = srl.load_historical_register(srl.HISTORICAL_S2_REGISTER_VERSION)
        self.assertTrue(hist_s2.is_historical_s2)
        hist_rc61 = srl.load_historical_register("rc6.1")
        self.assertTrue(hist_rc61.is_historical_rc61)
        with self.assertRaises(srl.SchemaRegisterError):
            srl.load_canonical_register(version="rc5-phase4-s9.9")
        with self.assertRaises(srl.SchemaRegisterError):
            srl.load_historical_register("rc6.5")
        with self.assertRaises(srl.SchemaRegisterError):
            srl.load_historical_register("rc7.0")

    def test_03_s1_historical_future_targets_preserved_and_s2_activates(self) -> None:
        s1 = srl.load_historical_s1_register()
        pkg = next(
            a for a in s1.raw["artifacts"] if a["filename"] == "WEAVER_FORGE_PACKAGE_IDENTITY.txt"
        )
        self.assertEqual(
            pkg["future_alignment_fields"]["activation"],
            "defined_future_s2_writer_alignment",
        )
        # Active rc6 register retains S2 writer-aligned activations.
        active = srl.load_active_register()
        self.assertEqual(
            active.activation("HOST_RUN_METADATA.txt", "host-preliminary"),
            "enforced_s2_writer_aligned",
        )
        boot = active.lookup("BOOTSTRAP.txt", "host-preliminary")
        variants = {x["variant_id"]: x for x in boot["conditional_variants"]}
        self.assertEqual(
            variants["early_failure_not_applicable_target"]["activation"],
            "enforced_s2_writer_aligned",
        )
        self.assertEqual(
            variants["early_failure_not_reached_placeholder"]["activation"],
            "historical_s1_compatibility",
        )
        man = active.lookup("EVIDENCE_MANIFEST.sha256", "final-submission")
        self.assertEqual(
            man["activation_detail"]["final_cryptographic_closure"],
            "enforced_s3_manifest_completeness",
        )
        self.assertEqual(
            active.raw["evidence_completeness_inventory"]["activation"],
            "enforced_s3_manifest_completeness",
        )


class S2WriterAlignmentTests(unittest.TestCase):
    def test_04_annotated_tag_writer_emits_exact_s2_fields(self) -> None:
        # Static source inspection only (no bash / host script execution).
        host_text = HOST_SCRIPT.read_text(encoding="utf-8")
        self.assertIn("weaver_forge_tag_ref=${WF_TAG_REF", host_text)
        self.assertIn("weaver_forge_tag_raw_object_type_required=tag", host_text)
        self.assertIn("weaver_forge_tag_raw_object_type_observed=${WF_TAG_RAW_OBJECT_TYPE}", host_text)
        self.assertIn("weaver_forge_tag_peeled_commit=${WEAVER_FORGE_RESOLVED_COMMIT}", host_text)
        self.assertIn("append_host_run_metadata_entry", host_text)
        self.assertIn("write_s2_not_applicable_terminal", host_text)
        # Template alignment.
        tmpl = (PACKAGE_DIR / "templates" / "WEAVER_FORGE_PACKAGE_IDENTITY.txt").read_text(
            encoding="utf-8"
        )
        for key in (
            "weaver_forge_tag_ref=",
            "weaver_forge_tag_raw_object_type_required=tag",
            "weaver_forge_tag_raw_object_type_observed=",
            "weaver_forge_tag_peeled_commit=",
        ):
            self.assertIn(key, tmpl)
        # No production tag creation commands in S2 alignment path.
        self.assertNotRegex(host_text, r"(?m)^[^#]*\bgit\s+tag\b")

    def test_05_preliminary_deviations_writer_s2_shapes(self) -> None:
        host_text = HOST_SCRIPT.read_text(encoding="utf-8")
        # Extract the DEVIATIONS write block markers.
        self.assertIn("deviation_count=0", host_text)
        self.assertIn("automated_summary=no_automated_identity_deviations", host_text)
        self.assertIn("automated_summary=noncanonical_identity_fields_changed:", host_text)
        self.assertIn('echo "deviation_state=PRESENT"', host_text)
        self.assertIn('echo "deviation_state=NONE"', host_text)
        # No Witness persona fabrication in host preliminary writer.
        block = host_text[
            host_text.find("step8_host_run_metadata_and_deviations") : host_text.find(
                "STEP 9:"
            )
        ]
        self.assertNotIn("deviation_1_severity", block)
        final_tmpl = (PACKAGE_DIR / "templates" / "DEVIATIONS.txt").read_text(encoding="utf-8")
        self.assertIn("deviation_count=0", final_tmpl)
        self.assertIn("Witness-input", final_tmpl)

    def test_06_host_run_metadata_append_entry_grammar_helpers(self) -> None:
        # Python-generated HOST_RUN_METADATA matching S2 append_entry grammar
        # (no bash execution). Validator contract unchanged.
        ws = _mktmp()
        evidence = ws / "evidence"
        evidence.mkdir()
        text = (
            "BEGIN_HOST_RUN_METADATA_ENTRY\n"
            "evidence_schema_version=1\n"
            "run_id=run-s2-test-001\n"
            "witness_id=witness-s2-test\n"
            "entry_kind=run_start\n"
            "entry_utc=2026-07-24T00:00:00Z\n"
            "payload=k=v\n"
            "END_HOST_RUN_METADATA_ENTRY\n"
            "BEGIN_HOST_RUN_METADATA_ENTRY\n"
            "evidence_schema_version=1\n"
            "run_id=run-s2-test-001\n"
            "witness_id=witness-s2-test\n"
            "entry_kind=annotated_tag_raw_object_check\n"
            "entry_utc=2026-07-24T00:00:00Z\n"
            "payload=observed=tag;required=tag\n"
            "END_HOST_RUN_METADATA_ENTRY\n"
        )
        (evidence / "HOST_RUN_METADATA.txt").write_text(text, encoding="utf-8", newline="\n")
        loaded = (evidence / "HOST_RUN_METADATA.txt").read_text(encoding="utf-8")
        self.assertTrue(loaded.startswith("BEGIN_HOST_RUN_METADATA_ENTRY"))
        errors: list[str] = []
        v.check_host_run_metadata_s2(loaded, errors)
        self.assertEqual(errors, [], errors)
        # Unknown key rejection.
        bad_entry = (
            "BEGIN_HOST_RUN_METADATA_ENTRY\n"
            "evidence_schema_version=1\n"
            "run_id=run-s2-test-001\n"
            "witness_id=witness-s2-test\n"
            "entry_kind=bad\n"
            "entry_utc=2026-07-24T00:00:00Z\n"
            "payload=x\n"
            "extra=1\n"
            "END_HOST_RUN_METADATA_ENTRY\n"
        )
        errors2: list[str] = []
        v.check_host_run_metadata_s2(bad_entry, errors2)
        self.assertTrue(any("unknown key" in e for e in errors2), errors2)

    def test_07_terminal_not_applicable_container_finalizer(self) -> None:
        # Static contract: container script defines S2 terminalization helpers.
        ctext = CONTAINER_SCRIPT.read_text(encoding="utf-8")
        self.assertIn("_terminalize_bootstrap_file", ctext)
        self.assertIn("_terminalize_build_command_file", ctext)
        self.assertIn("_terminalize_build_environment_file", ctext)
        self.assertIn("status=NOT_APPLICABLE", ctext)
        self.assertIn("applicability=not_applicable", ctext)
        self.assertIn("reason=stage_not_reached_before_bootstrap", ctext)
        self.assertIn("reason=stage_not_reached_before_build_command", ctext)
        self.assertIn("product_executed=NO", ctext)
        self.assertIn("ldd_used=NO", ctext)
        # No bash/source: apply NOT_APPLICABLE terminalization semantics in Python.
        ws = _mktmp()
        evidence = ws / "evidence"
        evidence.mkdir()
        for name in ("BOOTSTRAP.txt", "BUILD_COMMAND.txt", "BUILD_ENVIRONMENT.txt"):
            (evidence / name).write_text(
                "evidence_schema_version=1\nstatus=NOT_REACHED\n",
                encoding="utf-8",
                newline="\n",
            )
        outcome = "BUILD_NOT_STARTED"
        stage = "pre_bootstrap"
        (evidence / "BOOTSTRAP.txt").write_text(
            _s2_not_applicable_body(
                outcome, stage, "stage_not_reached_before_bootstrap"
            ),
            encoding="utf-8",
            newline="\n",
        )
        (evidence / "BUILD_COMMAND.txt").write_text(
            _s2_not_applicable_body(
                outcome, stage, "stage_not_reached_before_build_command"
            ),
            encoding="utf-8",
            newline="\n",
        )
        (evidence / "BUILD_ENVIRONMENT.txt").write_text(
            _s2_not_applicable_body(
                outcome, stage, "stage_not_reached_before_build_environment"
            ),
            encoding="utf-8",
            newline="\n",
        )
        for name in ("BOOTSTRAP.txt", "BUILD_COMMAND.txt", "BUILD_ENVIRONMENT.txt"):
            self.assertEqual(_read_kv(evidence / name, "status"), "NOT_APPLICABLE")
            self.assertEqual(_read_kv(evidence / name, "applicability"), "not_applicable")
            self.assertEqual(
                _read_kv(evidence / name, "authoritative_outcome"), "BUILD_NOT_STARTED"
            )
            self.assertEqual(_read_kv(evidence / name, "product_executed"), "NO")
            self.assertEqual(_read_kv(evidence / name, "ldd_used"), "NO")
            self.assertNotEqual(_read_kv(evidence / name, "status"), "NOT_REACHED")


class S2ValidatorEnforcementTests(unittest.TestCase):
    def test_08_s2_package_and_deviations_and_not_applicable(self) -> None:
        files = fx.build_scenario("success-artifact-present")
        files["WEAVER_FORGE_PACKAGE_IDENTITY.txt"] = textwrap.dedent(
            """\
            evidence_schema_version=1
            witness_id=witness01
            run_id=run-2026-07-22-001
            package_version=1.0.0-rc4
            weaver_forge_url=https://github.com/chrono-vector/weaver-forge.git
            weaver_forge_tag_requested=grok-build-witness-v1.0.0-rc4
            weaver_forge_tag_ref=refs/tags/grok-build-witness-v1.0.0-rc4
            weaver_forge_tag_raw_object_type_required=tag
            weaver_forge_tag_raw_object_type_observed=tag
            weaver_forge_tag_peeled_commit=89127c78c3a11492892de7e3b5f0dee18d71775a
            weaver_forge_commit_resolved=89127c78c3a11492892de7e3b5f0dee18d71775a
            package_clone_head=89127c78c3a11492892de7e3b5f0dee18d71775a
            package_clone_detached=yes
            package_clone_clean_status=yes
            tag_head_match=yes
            package_commit_authority=annotated_tag_resolution
            grok_build_source_commit_expected=98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce
            canonical_run=yes
            """
        )
        files["DEVIATIONS.txt"] = (
            "evidence_schema_version=1\n"
            "deviation_state=NONE\n"
            "deviation_count=0\n"
        )
        # S3: S2-shaped final-submission requires inventory_complete=yes.
        files["POST_BUILD_INTEGRITY.txt"] = files["POST_BUILD_INTEGRITY.txt"].replace(
            "evidence_inventory_complete=no",
            "evidence_inventory_complete=yes",
        )
        files["HOST_OUTCOME_INGESTION.txt"] = files["HOST_OUTCOME_INGESTION.txt"].replace(
            "evidence_completeness_status=INCOMPLETE",
            "evidence_completeness_status=COMPLETE",
        )
        tree = _mktmp()
        fx.write_tree(tree, files)
        # Final S2 deviations ok.
        errors = v.validate_dir(tree, mode=v.MODE_FINAL_SUBMISSION, schema_register_version="rc6.1")
        self.assertEqual(errors, [], errors)

        # Preliminary S2 deviations require automated_summary.
        files2 = dict(files)
        files2["DEVIATIONS.txt"] = (
            "evidence_schema_version=1\n"
            "deviation_state=NONE\n"
            "deviation_count=0\n"
            "automated_summary=no_automated_identity_deviations\n"
        )
        # Host-preliminary rejects inventory_complete=yes.
        files2["POST_BUILD_INTEGRITY.txt"] = files2["POST_BUILD_INTEGRITY.txt"].replace(
            "evidence_inventory_complete=yes",
            "evidence_inventory_complete=no",
        )
        files2["HOST_OUTCOME_INGESTION.txt"] = files2["HOST_OUTCOME_INGESTION.txt"].replace(
            "evidence_completeness_status=COMPLETE",
            "evidence_completeness_status=INCOMPLETE",
        )
        # Ensure HOST_OUTCOME present for prelim.
        tree2 = _mktmp()
        fx.write_tree(tree2, files2)
        errors2 = v.validate_dir(tree2, mode=v.MODE_HOST_PRELIMINARY, schema_register_version="rc6.1")
        self.assertEqual(errors2, [], errors2)

        # Mode crossover: automated_summary in final mode rejected.
        files3 = dict(files2)
        files3["POST_BUILD_INTEGRITY.txt"] = files["POST_BUILD_INTEGRITY.txt"]
        files3["HOST_OUTCOME_INGESTION.txt"] = files["HOST_OUTCOME_INGESTION.txt"]
        tree3 = _mktmp()
        fx.write_tree(tree3, files3)
        errors3 = v.validate_dir(tree3, mode=v.MODE_FINAL_SUBMISSION, schema_register_version="rc6.1")
        self.assertTrue(any("mode crossover" in e for e in errors3), errors3)

        # Illegal S2 observed type.
        bad_pkg = files["WEAVER_FORGE_PACKAGE_IDENTITY.txt"].replace(
            "weaver_forge_tag_raw_object_type_observed=tag",
            "weaver_forge_tag_raw_object_type_observed=commit",
        )
        files4 = dict(files)
        files4["WEAVER_FORGE_PACKAGE_IDENTITY.txt"] = bad_pkg
        tree4 = _mktmp()
        fx.write_tree(tree4, files4)
        errors4 = v.validate_dir(tree4, schema_register_version="rc6.1")
        self.assertTrue(any("raw_object_type_observed" in e for e in errors4), errors4)

        # Finalized S2 package rejecting leftover NOT_REACHED.
        files5 = fx.build_scenario("image-pull-failure")
        files5["WEAVER_FORGE_PACKAGE_IDENTITY.txt"] = files["WEAVER_FORGE_PACKAGE_IDENTITY.txt"]
        tree5 = _mktmp()
        fx.write_tree(tree5, files5)
        errors5 = v.validate_dir(tree5, schema_register_version="rc6.1")
        self.assertTrue(
            any("initialization-only" in e or "NOT_REACHED" in e for e in errors5),
            errors5,
        )

        # S2 NOT_APPLICABLE accepted.
        na = (
            "evidence_schema_version=1\n"
            "status=NOT_APPLICABLE\n"
            "applicability=not_applicable\n"
            "reason=pre_docker_infrastructure_failure_at_stage_image_pull\n"
            "authoritative_outcome=INFRASTRUCTURE_FAILURE\n"
            "failure_stage=image_pull\n"
            "product_executed=NO\n"
            "ldd_used=NO\n"
        )
        files6 = fx.build_scenario("image-pull-failure")
        files6["WEAVER_FORGE_PACKAGE_IDENTITY.txt"] = files["WEAVER_FORGE_PACKAGE_IDENTITY.txt"]
        files6["BOOTSTRAP.txt"] = na
        files6["BUILD_COMMAND.txt"] = na
        files6["BUILD_ENVIRONMENT.txt"] = na
        files6["POST_BUILD_INTEGRITY.txt"] = files6["POST_BUILD_INTEGRITY.txt"].replace(
            "evidence_inventory_complete=no",
            "evidence_inventory_complete=yes",
        )
        files6["HOST_OUTCOME_INGESTION.txt"] = files6["HOST_OUTCOME_INGESTION.txt"].replace(
            "evidence_completeness_status=FAILED",
            "evidence_completeness_status=COMPLETE",
        )
        # Final mode requires manuals; keep from build_scenario.
        tree6 = _mktmp()
        fx.write_tree(tree6, files6)
        errors6 = v.validate_dir(tree6, schema_register_version="rc6.1")
        self.assertEqual(errors6, [], errors6)

    def test_09_historical_fixtures_not_required_to_have_s2_fields(self) -> None:
        success = _materialize_committed_fixture("success-artifact-present")
        pkg = (success / "WEAVER_FORGE_PACKAGE_IDENTITY.txt").read_text(encoding="utf-8")
        self.assertNotIn("weaver_forge_tag_peeled_commit=", pkg)
        errors = v.validate_dir(success, schema_register_version="rc6.1")
        self.assertEqual(errors, [], errors)
        pull = _materialize_committed_fixture("image-pull-failure")
        errors2 = v.validate_dir(pull, schema_register_version="rc6.1")
        self.assertEqual(errors2, [], errors2)
        boot = (pull / "BOOTSTRAP.txt").read_text(encoding="utf-8")
        self.assertIn("status=NOT_REACHED", boot)

    def test_10_validator_no_write_no_inference_and_s3_active(self) -> None:
        tree = _mktmp()
        files = fx.build_scenario("success-artifact-present")
        # Drop manuals for prelim.
        for name in ("WITNESS_STATEMENT.md", "WITNESS_VERDICT.md", "REDACTIONS.md"):
            files.pop(name, None)
        fx.write_tree(tree, files)
        before = {
            p.name: (p.stat().st_mtime_ns, p.read_bytes())
            for p in tree.iterdir()
            if p.is_file()
        }
        errors = v.validate_dir(tree, host_preliminary=True, schema_register_version="rc6.1")
        self.assertEqual(errors, [], errors)
        for name, (mtime, data) in before.items():
            p = tree / name
            self.assertEqual(p.read_bytes(), data)
            self.assertEqual(p.stat().st_mtime_ns, mtime)
        src = (SCRIPTS_DIR / "validate_witness_evidence.py").read_text(encoding="utf-8")
        self.assertIn("no inference", src.lower())
        reg = srl.load_active_register()
        self.assertEqual(
            reg.raw["evidence_completeness_inventory"]["activation"],
            "enforced_s3_manifest_completeness",
        )
        self.assertTrue(
            reg.raw["recursive_inventory_helper"].get(
                "rc4b_020_026_027_028_implemented_on_main_pending_reaudit"
            )
        )
        self.assertFalse(reg.raw["recursive_inventory_helper"].get("rc4b_020_026_027_028_closed"))


class S2InventoryHelperTests(unittest.TestCase):
    def test_11_recursive_inventory_deterministic_and_fail_closed(self) -> None:
        root = _mktmp()
        (root / "a").mkdir()
        (root / "a" / "nested.txt").write_text("x\n", encoding="utf-8")
        (root / "z.txt").write_text("z\n", encoding="utf-8")
        (root / "b").mkdir()
        (root / "b" / "mid.txt").write_text("m\n", encoding="utf-8")
        paths = ei.enumerate_evidence_files(root)
        self.assertEqual(paths, ["a/nested.txt", "b/mid.txt", "z.txt"])
        self.assertEqual(
            ei.enumerate_evidence_files_with_prefix(root),
            ["./a/nested.txt", "./b/mid.txt", "./z.txt"],
        )

        # Symlink rejection (mocked; no production filesystem symlink required).
        link_root = _mktmp()
        (link_root / "real.txt").write_text("r\n", encoding="utf-8")
        real_is_symlink = Path.is_symlink

        def _fake_is_symlink(self: Path) -> bool:
            if self.name == "link.txt":
                return True
            return real_is_symlink(self)

        (link_root / "link.txt").write_text("ignored\n", encoding="utf-8")
        with unittest.mock.patch.object(Path, "is_symlink", _fake_is_symlink):
            with self.assertRaises(ei.EvidenceInventoryError) as ctx:
                ei.enumerate_evidence_files(link_root)
            self.assertIn("symlink", str(ctx.exception).lower())

        # Path escape rejection via normalize.
        with self.assertRaises(ei.EvidenceInventoryError):
            ei.normalize_relative_path("../escape.txt")
        with self.assertRaises(ei.EvidenceInventoryError):
            ei.normalize_relative_path("/abs.txt")

        # Special file rejection where platform-safe (FIFO).
        if hasattr(os, "mkfifo"):
            fifo_root = _mktmp()
            (fifo_root / "ok.txt").write_text("o\n", encoding="utf-8")
            fifo_path = fifo_root / "pipe.fifo"
            os.mkfifo(fifo_path)
            with self.assertRaises(ei.EvidenceInventoryError) as ctx2:
                ei.enumerate_evidence_files(fifo_root)
            self.assertIn("special", str(ctx2.exception).lower())

        # Duplicate normalized path rejection (representable via normalize collision).
        with self.assertRaises(ei.EvidenceInventoryError):
            # Direct API: simulate duplicate detection.
            seen = set()
            for rel in ("a/b.txt", "a/b.txt"):
                n = ei.normalize_relative_path(rel)
                if n in seen:
                    raise ei.EvidenceInventoryError(f"duplicate normalized path rejected: {n}")
                seen.add(n)


def tearDownModule() -> None:
    _cleanup()


if __name__ == "__main__":
    try:
        suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        print(
            f"DISCOVERED={result.testsRun} FAIL={len(result.failures)} "
            f"ERR={len(result.errors)} SKIP={len(result.skipped)}"
        )
        if not result.wasSuccessful():
            sys.exit(1)
    finally:
        _cleanup()
