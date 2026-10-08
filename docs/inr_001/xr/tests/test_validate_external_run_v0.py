"""INR-XR-001 adapter tests: 20 named adversarial tests plus focused tests.

Every fixture is synthetic. It is built in a temporary directory prefixed
``inrxr001_t_`` and removed afterwards. No real external run is executed.

Test 20 (a valid synthetic fixture) yields an ADAPTER/BUNDLE PASS only. It is NOT
an INR external reconstruction PASS, and it shows exactly the limit of a disk bundle:
a fabricated but fully consistent bundle passes the adapter. The adapter verifies
internal consistency and hash binding, not provenance.
"""
from __future__ import annotations

import base64
import functools
import io
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest import mock

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from docs.inr_001 import supervisor_inr_v0 as sup  # noqa: E402
from docs.inr_001.schema_check import check  # noqa: E402
from docs.inr_001.xr import collect_bundle_v0 as collect  # noqa: E402
from docs.inr_001.xr import validate_external_run_v0 as xr  # noqa: E402

TMP_PREFIX = "inrxr001_t_"
EVENT_ID = "INR-XR-EVT-0001"
NOT_BEFORE = "2026-10-08T00:30:00Z"
ROOT = "/home/runner/work/_temp/inrxr"
TOOLING = ROOT + "/tooling"
TARGET = ROOT + "/target"
STAGE = ROOT + "/stage/inr-local-x1y2z3"
PYTHON = "/opt/hostedtoolcache/Python/3.11.9/x64/bin/python3.11"
GIT = "/usr/bin/git"
PY_SHA = sup.digest(b"synthetic python executable")
GIT_SHA = sup.digest(b"synthetic git executable")
SUPERVISOR_PID = 4100
CHALLENGE = sup.digest(b"inrxr001 synthetic challenge")
CONFIG_KEYS = ["core.repositoryformatversion", "core.filemode", "core.bare", "remote.origin.url"]
RAW = {role: path for role, path in xr.SINGLETON_PATHS.items()}


def rmtree(path):
    def onexc(func, target, _exc):
        os.chmod(target, stat.S_IWRITE)
        func(target)
    if sys.version_info >= (3, 12):
        shutil.rmtree(path, onexc=onexc)
    else:  # pragma: no cover
        shutil.rmtree(path, onerror=lambda f, p, e: onexc(f, p, e))


def read_target_file(name):
    """Pinned PSM bytes from the local repository's Git objects at TARGET_SHA."""
    return sup._git(sup.DEFAULT_GIT.resolve(), REPO, "show", f"{sup.TARGET_SHA}:docs/portfolio_state/{name}")


@functools.lru_cache(maxsize=1)
def target_files():
    digests = xr.trusted_configuration()["target_file_digests"]
    pairs = tuple((name, read_target_file(name)) for name in sorted(digests))
    if any(sup.digest(data) != digests[name] for name, data in pairs):
        raise ValueError("pinned target bytes unavailable")
    return pairs


def _target_available():
    try:
        target_files()
        return True
    except (OSError, ValueError, subprocess.SubprocessError):
        return False


TARGET_AVAILABLE = _target_available()
NEEDS_TARGET = unittest.skipUnless(TARGET_AVAILABLE, "pinned PSM target bytes unavailable (local Git at TARGET_SHA)")


def valid_parts():
    """A complete, internally consistent synthetic bundle as editable parts (path -> value)."""
    t = xr.trusted_configuration()
    targets = dict(target_files())
    record = json.loads(targets[xr.EXAMPLE_FILE])
    required = sorted({s["git_commit"] for s in record["source_records"]}
                      | {s["git_commit"] for s in record["revision_provenance"]})
    validator = t["target_file_digests"][xr.VALIDATOR_FILE]
    base = 10 ** 12
    lifecycle = {name: base + i * 1000 for i, name in enumerate(sup.LIFECYCLE[:6])}
    clock = lifecycle["COMMAND_EXECUTION_BEGIN"] + 1000
    records = []
    for index, spec in enumerate(t["cases"], 1):
        cid = spec["case_id"]
        nonce = sup.digest(cid.encode())[:32]
        errors = list(spec["expected_errors"])
        argv = [PYTHON, "-I", "-S", "-B", TOOLING + "/" + xr.PROBE_REL, STAGE + "/" + xr.VALIDATOR_FILE,
                STAGE + "/" + cid + ".json", TARGET]
        identity = {"target_preloaded": False, "site_loaded": False, "sitecustomize_loaded": False,
                    "usercustomize_loaded": False, "isolated": 1, "no_site": 1, "dont_write_bytecode": True,
                    "python_version": [3, 11, 9], "python_executable": PYTHON, "cwd": STAGE, "git_which": GIT,
                    "git_shadowing": [], "git_environment": [["GIT_NO_REPLACE_OBJECTS", "1"]],
                    "source_sha256": validator, "post_source_sha256": validator, "source_path": argv[5],
                    "input_sha256": spec["input_digest"]}
        stdout = (json.dumps({"event_id": EVENT_ID, "challenge": CHALLENGE, "case_id": cid, "case_nonce": nonce,
                              "identity": identity, "errors": errors}, sort_keys=True) + "\n").encode("ascii")
        records.append({"case_id": cid, "command_id": "CMD_" + cid, "sequence": index, "event_id": EVENT_ID,
                        "challenge": CHALLENGE, "case_nonce": nonce, "argv": argv, "popen_args": list(argv),
                        "cwd": STAGE, "env_path": "/usr/bin", "env_git": [["GIT_NO_REPLACE_OBJECTS", "1"]],
                        "child_pid": SUPERVISOR_PID + index, "return_code": 2 if errors else 0,
                        "start_ns": clock, "end_ns": clock + 500,
                        "stdout_base64": base64.b64encode(stdout).decode("ascii"), "stderr_base64": "",
                        "stdout_sha256": sup.digest(stdout), "stderr_sha256": sup.digest(b"")})
        clock += 1000
    lifecycle.update({"EXECUTION_COMPLETE": clock, "POST_MEASUREMENT": clock + 1000,
                      "CAPTURE_COMPLETE": clock + 2000})
    findings = sup.Findings()
    sup._assess_external(findings)
    for name in sup.LOCAL_PREDICATES:
        findings.establish(name)
    export = {"schema_version": sup.EVENT_SCHEMA_VERSION, "inr_event_id": EVENT_ID, "target_sha": sup.TARGET_SHA,
              "accepted_target_profile_binding": {"target_profile_id": t["target_profile_id"],
                                                  "target_profile_digest": sup.PROFILE_DIGEST},
              "accepted_origin_reference_binding": {"origin_reference_set_id": t["origin_reference_set_id"],
                                                    "origin_reference_set_digest": sup.ORIGIN_DIGEST},
              "challenge": CHALLENGE, "ledger_reservation_entry_sha256": sup.digest(b"reservation"),
              "supervisor": {"pid": SUPERVISOR_PID, "executable": PYTHON, "python_version": [3, 11, 9],
                             "isolated": 1, "no_site": 1, "dont_write_bytecode": True,
                             "is_supervisor_process": True},
              "lifecycle": lifecycle,
              "git_probe": {"executable": GIT, "executable_sha256": GIT_SHA, "version": "git version 2.51.0",
                            "repository_root": TARGET, "head": sup.TARGET_SHA, "common_git_dir": TARGET + "/.git",
                            "config_keys": list(CONFIG_KEYS), "required_objects": required},
              "measurements": {"distribution_files": dict(t["target_file_digests"]),
                               "source_before_sha256": validator, "source_after_sha256": validator,
                               "probe_sha256": t["tooling_digests"][xr.PROBE_REL],
                               "python_executable_sha256": PY_SHA},
              "capture_records": records, "verification": sup._report(findings, EVENT_ID, True, SUPERVISOR_PID),
              "nonclaims": list(sup.NONCLAIMS)}
    parts = {}
    for rel, data in collect.event_files(export, started_at="2026-10-08T01:10:00Z",
                                         completed_at="2026-10-08T01:12:00Z",
                                         supervisor_sha256=t["tooling_digests"][xr.SUPERVISOR_REL],
                                         event_complete_ns=clock + 3000).items():
        parts[rel] = json.loads(data) if rel.endswith(".json") else data
    source = "https://github.com/" + t["repository"] + ".git"
    parts[RAW["acquisition_log"]] = "\n".join([
        xr.ACQUISITION_LOG_HEADER, "method: git-clone", "source: " + source, "ref: " + sup.TARGET_SHA,
        "$ git init " + TARGET, f"$ git -C {TARGET} remote add origin {source}",
        f"$ git -C {TARGET} fetch --no-tags origin {sup.TARGET_SHA}", "> From " + source,
        f"$ git -C {TARGET} checkout --detach {sup.TARGET_SHA}", "head: " + sup.TARGET_SHA, ""])
    parts[RAW["runner_identity"]] = {
        "schema_version": "inr.xr.raw.runner_identity.v0", "provider": "github-actions",
        "runner_environment": "github-hosted", "repository": t["repository"], "workflow_run_id": "18000000001",
        "workflow_run_attempt": 1, "job_id": "51000000001", "runner_name": "GitHub Actions 1000001",
        "runner_os": "Linux", "runner_arch": "X64", "image_os": "ubuntu24", "image_version": "20260928.1",
        "boot_time": "2026-10-08T00:58:00Z", "job_started_at": "2026-10-08T01:00:00Z"}
    parts[RAW["workspace_provenance"]] = {
        "schema_version": "inr.xr.raw.workspace_provenance.v0", "workspace_path": ROOT,
        "workspace_created_at": "2026-10-08T01:01:00Z", "initial_listing": [],
        "acquisition_started_at": "2026-10-08T01:01:05Z", "acquisition_completed_at": "2026-10-08T01:02:00Z",
        "inherited_writable_paths": [], "cache_restore_events": [], "prior_job_artifacts": []}
    flags = {"writable_by_principal": False, "writable_by_others": False, "symlink": False,
             "reparse_point": False, "link_count": 1}
    entries = [dict(flags, category="target_files", path="target/docs/portfolio_state/" + name, kind="file",
                    sha256=digest) for name, digest in sorted(t["target_file_digests"].items())]
    for category, paths in xr.TOOLING_ENTRIES.items():
        entries.extend(dict(flags, category=category, path="tooling/" + rel, kind="file",
                            sha256=t["tooling_digests"][rel]) for rel in paths)
    entries.append(dict(flags, category="execution_tree", path="tooling/docs/inr_001", kind="dir", sha256=""))
    entries.append(dict(flags, category="git_objects", path="target/.git/objects", kind="dir", sha256=""))
    tree_digest = xr.protected_tree_digest(entries)
    parts[RAW["isolation_checks"]] = {
        "schema_version": "inr.xr.raw.isolation_checks.v0",
        "execution_principal": {"user": "runner", "uid": "1001", "is_admin": False},
        "mounts": [{"mount_point": "/", "source": "/dev/root", "fs_type": "ext4", "writable": True,
                    "shared": False, "network": False},
                   {"mount_point": "/mnt", "source": "/dev/sdb1", "fs_type": "ext4", "writable": True,
                    "shared": False, "network": False}],
        "package_caches": [], "build_caches": [],
        "git_object_store": {"path": TARGET + "/.git/objects", "shared": False, "alternates": []},
        "origin_snapshot_restored": False,
        "protected_tree": {"root": ROOT, "categories_covered": list(xr.PROTECTED_CATEGORIES), "entries": entries,
                           "parent_chain": [{"path": ROOT, "writable_by_principal": False,
                                             "writable_by_others": False},
                                            {"path": "/home/runner/work/_temp", "writable_by_principal": False,
                                             "writable_by_others": False}],
                           "freeze_digest": tree_digest, "post_execution_digest": tree_digest}}
    parts[RAW["python_identity"]] = {
        "schema_version": "inr.xr.raw.python_identity.v0", "version": [3, 11, 9],
        "version_string": "3.11.9 (main, Sep 30 2026, 10:00:00) [GCC 13.3.0]", "implementation": "CPython",
        "executable": PYTHON, "executable_sha256": PY_SHA}
    parts[RAW["git_identity"]] = {
        "schema_version": "inr.xr.raw.git_identity.v0", "executable": GIT, "executable_sha256": GIT_SHA,
        "which_git": GIT, "version": "git version 2.51.0", "environment": [], "repository_root": TARGET,
        "dot_git_kind": "directory", "remote_url": source, "head": sup.TARGET_SHA,
        "required_objects": [{"object": sha, "type": "commit", "present": True}
                             for sha in [sup.TARGET_SHA, *required]],
        "replace_refs": [], "alternates": [], "grafts": [], "shallow": False, "worktree_status": [],
        "config_keys": list(CONFIG_KEYS)}
    for name, data in targets.items():
        parts[xr.TARGET_PATH.format(name)] = data
    return parts


def serialise(parts):
    files = {}
    for rel, value in parts.items():
        if isinstance(value, (dict, list)):
            files[rel] = collect.json_bytes(value)
        elif isinstance(value, str):
            files[rel] = value.encode("utf-8")
        else:
            files[rel] = value
    return files


def load_manifest(bundle):
    return json.loads((bundle / xr.MANIFEST_NAME).read_bytes())


def save_manifest(bundle, manifest):
    (bundle / xr.MANIFEST_NAME).write_bytes(collect.json_bytes(manifest))


def rebind(bundle, rel):
    """Re-hash one raw file into manifest + sha256sums (a consistent, re-bound edit)."""
    manifest = load_manifest(bundle)
    data = (bundle / rel).read_bytes()
    for entry in manifest["evidence_files"]:
        if entry["path"] == rel:
            entry["sha256"] = sup.digest(data)
    sums = "".join(f"{e['sha256']}  {e['path']}\n" for e in manifest["evidence_files"]
                   if e["role"] != "sha256sums").encode("ascii")
    (bundle / RAW["sha256sums"]).write_bytes(sums)
    for entry in manifest["evidence_files"]:
        if entry["role"] == "sha256sums":
            entry["sha256"] = sup.digest(sums)
    save_manifest(bundle, manifest)


class BundleCase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix=TMP_PREFIX))
        self.addCleanup(rmtree, self.tmp)
        self.counter = 0

    def build(self, parts=None, *, declarations=None, event_id=EVENT_ID, edit=None):
        parts = valid_parts() if parts is None else parts
        if edit is not None:
            edit(parts)
        self.counter += 1
        bundle = self.tmp / f"bundle{self.counter}"
        collect.write_bundle(bundle, serialise(parts), inr_event_id=event_id, bundle_id="XR-SYNTH-0001",
                             runner_declarations=declarations)
        return bundle

    def validate(self, bundle, *, expected_event_id=EVENT_ID, not_before=NOT_BEFORE):
        before = sorted(p.relative_to(bundle).as_posix() for p in bundle.rglob("*"))
        result = xr.validate_bundle(bundle, expected_event_id=expected_event_id, not_before=not_before)
        after = sorted(p.relative_to(bundle).as_posix() for p in bundle.rglob("*"))
        self.assertEqual(before, after, "adapter must not write into the bundle")
        self.assertEqual(check(result, xr.load_schema()["$defs"]["adapter_result"]), [], result)
        self.assertIs(result["inr_external_reconstruction_pass"], False)
        self.assertIs(result["fresh_local_inr_pass"], False)
        self.assertEqual(result["adapter_bundle_pass"], result["classification"] == "PASS")
        if result["classification"] == "PASS":
            self.assertEqual(set(result["predicates"].values()) | set(result["gates"].values()), {"PASS"})
        return result

    def assertClass(self, result, classification, **statuses):
        self.assertEqual(result["classification"], classification, json.dumps(result, indent=1))
        self.assertFalse(result["adapter_bundle_pass"] and classification != "PASS")
        for name, status in statuses.items():
            actual = result["predicates"].get(name, result["gates"].get(name))
            self.assertEqual(actual, status, f"{name}: {json.dumps(result, indent=1)}")

    def messages(self, result):
        return "\n".join(result["blocked"] + result["fail"] + result["unconfirmed"])


@NEEDS_TARGET
class AdversarialTests(BundleCase):
    """INR-XR-001 section 18: the 20 required adversarial attempts."""

    def test_adv_01_fresh_true_without_evidence(self):
        def edit(parts):
            parts[RAW["workspace_provenance"]] = {"schema_version": "inr.xr.raw.workspace_provenance.v0",
                                                  "workspace_path": ROOT,
                                                  "runner_declarations": {"fresh": True,
                                                                          "fresh_workspace_established": "PASS"}}
            parts[RAW["runner_identity"]]["runner_declarations"] = {"fresh": True, "fresh_runner": True}
        result = self.validate(self.build(edit=edit, declarations={"fresh": True}))
        self.assertClass(result, "UNCONFIRMED", fresh_hosted_runner_candidate="UNCONFIRMED",
                         fresh_workspace_established="UNCONFIRMED")
        self.assertTrue(any("fresh" in item for item in result["ignored_runner_declarations"]))
        # A top-level self-assertion in raw evidence is rejected, not ignored.
        parts = valid_parts()
        parts[RAW["workspace_provenance"]]["fresh"] = True
        result = self.validate(self.build(parts))
        self.assertClass(result, "UNCONFIRMED", fresh_workspace_established="UNCONFIRMED")
        self.assertIn("self-assertion field rejected", self.messages(result))

    def test_adv_02_non_origin_true_without_evidence(self):
        def edit(parts):
            del parts[RAW["isolation_checks"]]
            parts[RAW["runner_identity"]]["runner_declarations"] = {"non_origin": True}
        result = self.validate(self.build(edit=edit, declarations={"non_origin": True}))
        self.assertClass(result, "UNCONFIRMED", no_shared_origin_filesystem_evidence="UNCONFIRMED",
                         no_shared_mutable_cache_evidence="UNCONFIRMED")
        bundle = self.build()
        manifest = load_manifest(bundle)
        manifest["non_origin"] = True
        save_manifest(bundle, manifest)
        result = self.validate(bundle)
        self.assertClass(result, "FAIL", bundle_integrity="FAIL")
        self.assertIn("self-assertion field rejected", self.messages(result))

    def test_adv_03_all_writer_isolation_true_without_evidence(self):
        def edit(parts):
            iso = parts[RAW["isolation_checks"]]
            tree = iso["protected_tree"]
            tree["entries"] = [e for e in tree["entries"] if e["category"] == "execution_tree"]
            tree["categories_covered"] = ["execution_tree"]
            tree["freeze_digest"] = tree["post_execution_digest"] = xr.protected_tree_digest(tree["entries"])
            iso["runner_declarations"] = {"all_writer_isolation": True,
                                          "protected_tree_isolation_established": "PASS"}
        result = self.validate(self.build(edit=edit, declarations={"all_writer_isolation": True}))
        self.assertClass(result, "UNCONFIRMED", protected_tree_isolation_established="UNCONFIRMED")

    def test_adv_04_missing_runner_identity(self):
        result = self.validate(self.build(edit=lambda parts: parts.pop(RAW["runner_identity"])))
        self.assertClass(result, "UNCONFIRMED", runner_identity_established="UNCONFIRMED",
                         fresh_hosted_runner_candidate="UNCONFIRMED", bundle_integrity="UNCONFIRMED")

    def test_adv_05_reused_workspace_evidence(self):
        def edit(parts):
            wp = parts[RAW["workspace_provenance"]]
            wp["initial_listing"] = [".git", "docs", "README.md"]
            wp["workspace_created_at"] = "2026-10-01T09:00:00Z"
        result = self.validate(self.build(edit=edit))
        self.assertClass(result, "FAIL", fresh_workspace_established="FAIL")

    def test_adv_06_shared_mutable_cache_detected(self):
        def edit(parts):
            parts[RAW["isolation_checks"]]["package_caches"] = [
                {"path": "/home/runner/.cache/pip", "restored": True, "shared": True}]
            parts[RAW["workspace_provenance"]]["cache_restore_events"] = ["actions/cache restore pip-3.11"]
        result = self.validate(self.build(edit=edit))
        self.assertClass(result, "FAIL", no_shared_mutable_cache_evidence="FAIL",
                         fresh_hosted_runner_candidate="FAIL")

    def test_adv_07_origin_worktree_copied(self):
        def edit(parts):
            parts[RAW["acquisition_log"]] = "\n".join([
                xr.ACQUISITION_LOG_HEADER, "method: git-clone", "source: file:///C:/dev/_tmp/weaver-gzse-001",
                "ref: " + sup.TARGET_SHA, "$ cp -r /mnt/origin/weaver-gzse-001 " + TARGET,
                "head: " + sup.TARGET_SHA, ""])
        result = self.validate(self.build(edit=edit))
        self.assertClass(result, "FAIL", independent_acquisition_established="FAIL")

    def test_adv_08_wrong_target_sha(self):
        other = "1" * 40

        def edit(parts):
            parts[RAW["git_identity"]]["head"] = other
            parts[RAW["post_measurement"]]["git_probe"]["head"] = other
            parts[RAW["acquisition_log"]] = parts[RAW["acquisition_log"]].replace(sup.TARGET_SHA, other)
        result = self.validate(self.build(edit=edit))
        self.assertClass(result, "BLOCKED", independent_acquisition_established="BLOCKED",
                         git_identity_established="BLOCKED")

    def test_adv_09_missing_required_object(self):
        def edit(parts):
            objects = parts[RAW["git_identity"]]["required_objects"]
            objects[-1]["present"] = False
        result = self.validate(self.build(edit=edit))
        self.assertClass(result, "BLOCKED", independent_acquisition_established="BLOCKED")
        self.assertIn("required target object unavailable", self.messages(result))

    def test_adv_10_python_314(self):
        def edit(parts):
            parts[RAW["python_identity"]].update(version=[3, 14, 0], version_string="3.14.0 (main) [GCC]")
            parts[RAW["event_start"]]["supervisor"]["python_version"] = [3, 14, 0]
        result = self.validate(self.build(edit=edit))
        self.assertClass(result, "BLOCKED", python_311_established="BLOCKED")
        for version in ([3, 10, 12], [3, 12, 7], [3, 13, 1]):
            parts = valid_parts()
            parts[RAW["python_identity"]].update(version=version,
                                                 version_string=".".join(map(str, version)) + " x")
            self.assertClass(self.validate(self.build(parts)), "BLOCKED", python_311_established="BLOCKED")

    def test_adv_11_git_unavailable(self):
        result = self.validate(self.build(edit=lambda parts: parts.pop(RAW["git_identity"])))
        self.assertClass(result, "BLOCKED", git_identity_established="BLOCKED")
        parts = valid_parts()
        parts[RAW["git_identity"]]["version"] = "git: command not found"
        self.assertClass(self.validate(self.build(parts)), "BLOCKED", git_identity_established="BLOCKED")

    def test_adv_12_alternate_origin_reference_supplied(self):
        bundle = self.build()
        manifest = load_manifest(bundle)
        manifest["accepted_origin_reference"] = {"origin_reference_set_id": "INR_ORIGIN_SET_ALTERNATE",
                                                 "origin_reference_set_digest": "0" * 64}
        save_manifest(bundle, manifest)
        result = self.validate(bundle)
        self.assertClass(result, "UNCONFIRMED", trusted_reference_binding="UNCONFIRMED")
        self.assertEqual(result["trusted_configuration"]["origin_reference_set_id"], "INR_ORIGIN_SET_PSM_001_V0")
        self.assertEqual(result["trusted_configuration"]["origin_reference_set_digest"], sup.ORIGIN_DIGEST)

    def test_adv_13_raw_evidence_hash_mismatch(self):
        bundle = self.build()
        path = bundle / RAW["python_identity"]
        path.write_bytes(path.read_bytes().replace(b"3.11.9", b"3.11.8"))
        result = self.validate(bundle)
        self.assertClass(result, "FAIL", bundle_integrity="FAIL")
        self.assertEqual(set(result["predicates"].values()), {"NOT_ESTABLISHED"})
        self.assertIn("hash mismatch", self.messages(result))

    def test_adv_14_missing_event_complete(self):
        result = self.validate(self.build(edit=lambda parts: parts.pop(RAW["event_complete"])))
        self.assertClass(result, "UNCONFIRMED", current_event_capture_established="UNCONFIRMED")
        self.assertIn("EVENT_COMPLETE absent", self.messages(result))

    def test_adv_15_missing_child_provenance(self):
        case = "PSM_NEG_HUMAN_FINAL_INFERENCE"
        result = self.validate(self.build(
            edit=lambda parts: parts.pop(xr.PER_CASE_PATHS["command_result"].format(case))))
        self.assertClass(result, "UNCONFIRMED", current_event_capture_established="UNCONFIRMED")
        self.assertIn(case + ": child provenance absent", self.messages(result))

    def test_adv_16_path_traversal_in_manifest(self):
        for bad in ("raw/../raw/runner_identity.json", "../outside/runner_identity.json",
                    "raw/./runner_identity.json", "raw//runner_identity.json"):
            bundle = self.build()
            manifest = load_manifest(bundle)
            for entry in manifest["evidence_files"]:
                if entry["path"] == RAW["runner_identity"]:
                    entry["path"] = bad
            save_manifest(bundle, manifest)
            result = self.validate(bundle)
            self.assertClass(result, "FAIL", bundle_integrity="FAIL")
            self.assertIn("path traversal", self.messages(result))

    def test_adv_17_absolute_evidence_path(self):
        for bad in ("/etc/passwd", "C:/Windows/win.ini", "C:\\Windows\\win.ini", "\\\\server\\share\\x.json"):
            bundle = self.build()
            manifest = load_manifest(bundle)
            manifest["evidence_files"][0]["path"] = bad
            save_manifest(bundle, manifest)
            result = self.validate(bundle)
            self.assertClass(result, "FAIL", bundle_integrity="FAIL")
            self.assertIn("evidence path rejected", self.messages(result))

    def test_adv_18_duplicate_evidence_entry(self):
        bundle = self.build()
        manifest = load_manifest(bundle)
        manifest["evidence_files"].append(dict(manifest["evidence_files"][0]))
        save_manifest(bundle, manifest)
        result = self.validate(bundle)
        self.assertClass(result, "FAIL", bundle_integrity="FAIL")
        self.assertIn("duplicate evidence entry", self.messages(result))
        bundle = self.build()
        manifest = load_manifest(bundle)
        twin = dict(manifest["evidence_files"][0], path=manifest["evidence_files"][0]["path"].upper())
        manifest["evidence_files"].append(twin)
        save_manifest(bundle, manifest)
        self.assertClass(self.validate(bundle), "FAIL", bundle_integrity="FAIL")

    def test_adv_19_stale_historical_event_bundle(self):
        # (a) the event predates the operator's run request
        result = self.validate(self.build(), not_before="2026-10-08T02:00:00Z")
        self.assertClass(result, "FAIL", current_event_capture_established="FAIL")
        self.assertIn("stale/historical", self.messages(result))
        # (b) a bundle for another (older) event ID
        result = self.validate(self.build(), expected_event_id="INR-XR-EVT-0002")
        self.assertClass(result, "FAIL", current_event_capture_established="FAIL")

        # (c) a historical event imported into a new runner job
        def edit(parts):
            parts[RAW["event_start"]]["started_at"] = "2026-09-01T10:00:00Z"
            parts[RAW["event_complete"]]["completed_at"] = "2026-09-01T10:02:00Z"
        result = self.validate(self.build(edit=edit), not_before="2026-08-01T00:00:00Z")
        self.assertClass(result, "FAIL", current_event_capture_established="FAIL")
        self.assertIn("historical event imported", self.messages(result))
        # (d) no operator binding at all: never PASS
        result = self.validate(self.build(), expected_event_id=None, not_before=None)
        self.assertClass(result, "UNCONFIRMED", current_event_capture_established="UNCONFIRMED")

    def test_adv_20_valid_synthetic_fixture_adapter_pass_only(self):
        """ADAPTER/BUNDLE PASS only - NOT an INR external reconstruction PASS."""
        result = self.validate(self.build())
        self.assertClass(result, "PASS", **{name: "PASS" for name in xr.PREDICATES + xr.GATES})
        self.assertEqual(result["classification_scope"], "ADAPTER_BUNDLE_ONLY")
        self.assertIs(result["inr_external_reconstruction_pass"], False)
        self.assertIs(result["fresh_local_inr_pass"], False)
        self.assertIn("not an INR external reconstruction PASS", result["nonclaims"])
        self.assertIn("disk bundle verified by internal consistency and hash binding only; "
                      "no provider-signed attestation", result["nonclaims"])
        self.assertEqual(result["ignored_runner_declarations"], [])


@NEEDS_TARGET
class FocusedTests(BundleCase):
    """Focused tests for individual derivation rules."""

    def test_declarations_are_informational_only_both_ways(self):
        declarations = {"fresh": False, "non_origin": False, "classification": "FAIL"}
        parts = valid_parts()
        parts[RAW["runner_identity"]]["runner_declarations"] = {"fresh": False}
        result = self.validate(self.build(parts, declarations=declarations))
        self.assertClass(result, "PASS")
        self.assertEqual(len(result["ignored_runner_declarations"]), 2)

    def test_manifest_classification_field_rejected(self):
        for key, value in (("classification", "PASS"), ("derived_predicates", {}),
                           ("current_event_capture_established", "PASS"), ("git_verified", True)):
            bundle = self.build()
            manifest = load_manifest(bundle)
            manifest[key] = value
            save_manifest(bundle, manifest)
            result = self.validate(bundle)
            self.assertClass(result, "FAIL", bundle_integrity="FAIL")
            self.assertIn("self-assertion field rejected", self.messages(result))

    def test_raw_predicate_field_makes_evidence_inadmissible(self):
        parts = valid_parts()
        parts[RAW["git_identity"]]["git_identity_established"] = "PASS"
        result = self.validate(self.build(parts))
        self.assertClass(result, "BLOCKED", git_identity_established="BLOCKED")
        self.assertIn("self-assertion field rejected", self.messages(result))

    def test_supervisor_report_is_negative_only(self):
        parts = valid_parts()
        report = parts[RAW["event_complete"]]["supervisor_report"]
        report.update(derived_result="PASS", pass_allowed=True,
                      predicates={name: "PASS" for name in sup.REQUIRED_PREDICATES})
        result = self.validate(self.build(parts))
        self.assertClass(result, "FAIL", current_event_capture_established="FAIL")
        parts = valid_parts()
        parts[RAW["event_complete"]]["supervisor_report"]["predicates"]["refusal_semantics"] = "FAIL"
        self.assertClass(self.validate(self.build(parts)), "FAIL", current_event_capture_established="FAIL")
        parts = valid_parts()
        parts[RAW["event_complete"]]["supervisor_report"]["result_kind"] = "IN_PROCESS_NOT_TRUSTED"
        self.assertClass(self.validate(self.build(parts)), "UNCONFIRMED",
                         current_event_capture_established="UNCONFIRMED")

    def test_unbound_extra_file_rejected(self):
        bundle = self.build()
        (bundle / "raw" / "extra_evidence.json").write_bytes(b"{}\n")
        result = self.validate(bundle)
        self.assertClass(result, "FAIL", bundle_integrity="FAIL")
        self.assertIn("unbound file", self.messages(result))

    def test_substituted_evidence_role_rejected(self):
        bundle = self.build()
        (bundle / "raw" / "alt_identity.json").write_bytes((bundle / RAW["runner_identity"]).read_bytes())
        manifest = load_manifest(bundle)
        for entry in manifest["evidence_files"]:
            if entry["path"] == RAW["runner_identity"]:
                entry["path"] = "raw/alt_identity.json"
        save_manifest(bundle, manifest)
        (bundle / RAW["runner_identity"]).unlink()
        result = self.validate(bundle)
        self.assertClass(result, "FAIL", bundle_integrity="FAIL")
        self.assertIn("unknown or substituted evidence entry", self.messages(result))

    def test_unknown_case_record_rejected(self):
        bundle = self.build()
        rel = "raw/command_results/PSM_INVENTED_CASE.capture.json"
        (bundle / rel).write_bytes(b"{}\n")
        manifest = load_manifest(bundle)
        manifest["evidence_files"].append({"role": "command_result", "path": rel, "sha256": sup.digest(b"{}\n")})
        save_manifest(bundle, manifest)
        self.assertClass(self.validate(bundle), "FAIL", bundle_integrity="FAIL")

    def test_sha256sums_disagreement_rejected(self):
        bundle = self.build()
        sums = bundle / RAW["sha256sums"]
        lines = sums.read_bytes().decode("ascii").splitlines(keepends=True)
        sums.write_bytes("".join(lines[1:]).encode("ascii"))
        manifest = load_manifest(bundle)
        for entry in manifest["evidence_files"]:
            if entry["role"] == "sha256sums":
                entry["sha256"] = sup.digest(sums.read_bytes())
        save_manifest(bundle, manifest)
        result = self.validate(bundle)
        self.assertClass(result, "FAIL", bundle_integrity="FAIL")
        self.assertIn("sha256sums.txt disagrees", self.messages(result))

    def test_bound_file_missing_on_disk(self):
        bundle = self.build()
        (bundle / RAW["isolation_checks"]).unlink()
        result = self.validate(bundle)
        self.assertClass(result, "UNCONFIRMED", bundle_integrity="UNCONFIRMED",
                         protected_tree_isolation_established="UNCONFIRMED")

    def test_symlink_escape_rejected(self):
        bundle = self.build()
        outside = self.tmp / "outside_runner_identity.json"
        target = bundle / RAW["runner_identity"]
        outside.write_bytes(target.read_bytes())
        target.unlink()
        try:
            os.symlink(outside, target)
        except (OSError, NotImplementedError):
            self.skipTest("symlink creation not permitted on this host")
        result = self.validate(bundle)
        self.assertClass(result, "FAIL", bundle_integrity="FAIL")
        self.assertIn("symlink", self.messages(result))

    def test_junction_escape_rejected(self):
        if os.name != "nt":
            self.skipTest("directory junctions exist on Windows only (symlink variant covers POSIX)")
        import _winapi
        bundle = self.build()
        outside = self.tmp / "outside_stdout"
        shutil.copytree(bundle / "raw" / "stdout", outside)
        rmtree(bundle / "raw" / "stdout")
        _winapi.CreateJunction(str(outside), str(bundle / "raw" / "stdout"))
        result = self.validate(bundle)
        self.assertClass(result, "FAIL", bundle_integrity="FAIL")
        self.assertIn("symlink/junction", self.messages(result))

    def test_duplicate_json_key_inadmissible(self):
        bundle = self.build()
        path = bundle / RAW["runner_identity"]
        path.write_bytes(path.read_bytes().replace(b'"provider": "github-actions"',
                                                   b'"provider": "github-actions", "provider": "x"'))
        rebind(bundle, RAW["runner_identity"])
        result = self.validate(bundle)
        self.assertClass(result, "UNCONFIRMED", runner_identity_established="UNCONFIRMED")
        self.assertIn("duplicate JSON key", self.messages(result))

    def test_operator_parameters_required(self):
        self.assertClass(self.validate(self.build(), expected_event_id=None), "UNCONFIRMED",
                         current_event_capture_established="UNCONFIRMED")
        self.assertClass(self.validate(self.build(), not_before=None), "UNCONFIRMED",
                         current_event_capture_established="UNCONFIRMED")
        self.assertClass(self.validate(self.build(), not_before="yesterday"), "UNCONFIRMED",
                         current_event_capture_established="UNCONFIRMED")

    def test_self_hosted_or_unknown_runner(self):
        parts = valid_parts()
        parts[RAW["runner_identity"]]["runner_environment"] = "self-hosted"
        self.assertClass(self.validate(self.build(parts)), "FAIL", fresh_hosted_runner_candidate="FAIL")
        parts = valid_parts()
        parts[RAW["runner_identity"]]["provider"] = "my-laptop"
        self.assertClass(self.validate(self.build(parts)), "UNCONFIRMED",
                         runner_identity_established="UNCONFIRMED", fresh_hosted_runner_candidate="UNCONFIRMED")
        parts = valid_parts()
        parts[RAW["runner_identity"]]["boot_time"] = "2026-10-01T00:00:00Z"
        self.assertClass(self.validate(self.build(parts)), "UNCONFIRMED",
                         fresh_hosted_runner_candidate="UNCONFIRMED")
        parts = valid_parts()
        parts[RAW["workspace_provenance"]]["prior_job_artifacts"] = ["/home/runner/work/other-repo"]
        self.assertClass(self.validate(self.build(parts)), "FAIL", fresh_hosted_runner_candidate="FAIL")

    def test_linked_worktree_or_dirty_checkout(self):
        parts = valid_parts()
        parts[RAW["git_identity"]]["dot_git_kind"] = "file"
        self.assertClass(self.validate(self.build(parts)), "FAIL", fresh_workspace_established="FAIL")
        parts = valid_parts()
        parts[RAW["git_identity"]]["worktree_status"] = ["?? docs/origin_only_note.md"]
        self.assertClass(self.validate(self.build(parts)), "FAIL", fresh_workspace_established="FAIL")

    def test_non_authoritative_or_shared_acquisition(self):
        parts = valid_parts()
        parts[RAW["acquisition_log"]] = parts[RAW["acquisition_log"]].replace(
            "github.com/chrono-vector/weaver-forge", "github.com/someone/fork")
        parts[RAW["git_identity"]]["remote_url"] = "https://github.com/someone/fork.git"
        self.assertClass(self.validate(self.build(parts)), "UNCONFIRMED",
                         independent_acquisition_established="UNCONFIRMED")
        parts = valid_parts()
        parts[RAW["acquisition_log"]] = parts[RAW["acquisition_log"]].replace(
            "fetch --no-tags", "fetch --reference /mnt/origin/.git --no-tags")
        self.assertClass(self.validate(self.build(parts)), "FAIL", independent_acquisition_established="FAIL")
        parts = valid_parts()
        parts[RAW["acquisition_log"]] = "method: git-clone\n"
        self.assertClass(self.validate(self.build(parts)), "UNCONFIRMED",
                         independent_acquisition_established="UNCONFIRMED")

    def test_target_file_digest_mismatch_blocked(self):
        parts = valid_parts()
        parts[xr.TARGET_PATH.format("validate_psm_v0.py")] += b"\n# mutated\n"
        self.assertClass(self.validate(self.build(parts)), "BLOCKED",
                         independent_acquisition_established="BLOCKED")

    def test_writable_network_mount_and_shared_object_store(self):
        parts = valid_parts()
        parts[RAW["isolation_checks"]]["mounts"].append(
            {"mount_point": ROOT, "source": "origin-host:/export/weaver", "fs_type": "nfs4", "writable": True,
             "shared": False, "network": False})
        result = self.validate(self.build(parts))
        self.assertClass(result, "FAIL", no_shared_origin_filesystem_evidence="FAIL",
                         protected_tree_isolation_established="FAIL")
        parts = valid_parts()
        parts[RAW["isolation_checks"]]["git_object_store"]["alternates"] = ["/mnt/origin/.git/objects"]
        self.assertClass(self.validate(self.build(parts)), "FAIL", no_shared_origin_filesystem_evidence="FAIL")

    def test_protected_tree_rules(self):
        def entry_edit(**changes):
            parts = valid_parts()
            tree = parts[RAW["isolation_checks"]]["protected_tree"]
            tree["entries"][0].update(changes)
            return parts
        self.assertClass(self.validate(self.build(entry_edit(writable_by_principal=True))), "UNCONFIRMED",
                         protected_tree_isolation_established="UNCONFIRMED")
        for changes in ({"writable_by_others": True}, {"link_count": 2}, {"symlink": True},
                        {"reparse_point": True}):
            self.assertClass(self.validate(self.build(entry_edit(**changes))), "FAIL",
                             protected_tree_isolation_established="FAIL")
        parts = valid_parts()
        parts[RAW["isolation_checks"]]["protected_tree"]["post_execution_digest"] = "f" * 64
        self.assertClass(self.validate(self.build(parts)), "FAIL", protected_tree_isolation_established="FAIL")
        parts = valid_parts()
        parts[RAW["isolation_checks"]]["protected_tree"]["parent_chain"][0]["writable_by_principal"] = True
        self.assertClass(self.validate(self.build(parts)), "UNCONFIRMED",
                         protected_tree_isolation_established="UNCONFIRMED")
        parts = valid_parts()
        parts[RAW["isolation_checks"]]["execution_principal"]["is_admin"] = True
        self.assertClass(self.validate(self.build(parts)), "UNCONFIRMED",
                         protected_tree_isolation_established="UNCONFIRMED")

    def test_git_ambiguity_blocked(self):
        for key, value in (("replace_refs", ["refs/replace/" + "2" * 40]), ("which_git", "/usr/local/bin/git"),
                           ("environment", [["GIT_DIR", "/tmp/x"]]), ("shallow", True),
                           ("config_keys", CONFIG_KEYS + ["include.path"])):
            parts = valid_parts()
            parts[RAW["git_identity"]][key] = value
            if key == "config_keys":
                parts[RAW["post_measurement"]]["git_probe"]["config_keys"] = value
            self.assertClass(self.validate(self.build(parts)), "BLOCKED", git_identity_established="BLOCKED")

    def test_python_implementation_and_inconsistency(self):
        parts = valid_parts()
        parts[RAW["python_identity"]]["implementation"] = "PyPy"
        self.assertClass(self.validate(self.build(parts)), "BLOCKED", python_311_established="BLOCKED")
        parts = valid_parts()
        parts[RAW["python_identity"]]["executable_sha256"] = "e" * 64
        self.assertClass(self.validate(self.build(parts)), "FAIL", python_311_established="FAIL")

    def test_child_replay_argv_and_refusal_drift(self):
        case = "PSM_REQUIRED_PRODUCTION_NONCLAIM"
        stdout_rel = xr.PER_CASE_PATHS["stdout"].format(case)
        record_rel = xr.PER_CASE_PATHS["command_result"].format(case)

        def restream(parts, report):
            data = (json.dumps(report, sort_keys=True) + "\n").encode("ascii")
            parts[stdout_rel] = data
            parts[record_rel]["stdout_sha256"] = sup.digest(data)
        parts = valid_parts()
        report = json.loads(parts[stdout_rel])
        restream(parts, dict(report, challenge="0" * 64))
        self.assertClass(self.validate(self.build(parts)), "FAIL", current_event_capture_established="FAIL")
        parts = valid_parts()
        restream(parts, dict(report, errors=[]))
        self.assertClass(self.validate(self.build(parts)), "FAIL", current_event_capture_established="FAIL")
        parts = valid_parts()
        parts[record_rel]["argv"][1] = "-E"
        parts[record_rel]["popen_args"][1] = "-E"
        self.assertClass(self.validate(self.build(parts)), "FAIL", current_event_capture_established="FAIL")
        parts = valid_parts()
        parts[stdout_rel] = b"tampered but re-hashed\n"
        self.assertClass(self.validate(self.build(parts)), "FAIL", current_event_capture_established="FAIL")

    def test_event_profile_binding_mismatch_unconfirmed(self):
        parts = valid_parts()
        parts[RAW["event_start"]]["accepted_target_profile_binding"]["target_profile_digest"] = "a" * 64
        self.assertClass(self.validate(self.build(parts)), "UNCONFIRMED",
                         current_event_capture_established="UNCONFIRMED")

    def test_lifecycle_order_and_event_complete_order(self):
        parts = valid_parts()
        lifecycle = parts[RAW["post_measurement"]]["lifecycle"]
        lifecycle["FREEZE_START"], lifecycle["ACQUISITION_VERIFIED"] = (lifecycle["ACQUISITION_VERIFIED"],
                                                                        lifecycle["FREEZE_START"])
        self.assertClass(self.validate(self.build(parts)), "FAIL", current_event_capture_established="FAIL")
        parts = valid_parts()
        parts[RAW["event_complete"]]["event_complete_ns"] = 1
        self.assertClass(self.validate(self.build(parts)), "FAIL", current_event_capture_established="FAIL")

    def test_trusted_configuration_unavailable_blocks(self):
        with mock.patch.object(sup, "configuration", side_effect=ValueError("trusted configuration digest mismatch")):
            result = xr.validate_bundle(self.tmp, expected_event_id=EVENT_ID, not_before=NOT_BEFORE)
        self.assertEqual(result["classification"], "BLOCKED")
        self.assertEqual(result["gates"]["trusted_reference_binding"], "BLOCKED")
        self.assertEqual(check(result, xr.load_schema()["$defs"]["adapter_result"]), [])

    def test_missing_bundle_and_manifest(self):
        result = self.validate_missing(self.tmp / "absent")
        self.assertEqual(result["classification"], "UNCONFIRMED")
        empty = self.tmp / "empty"
        empty.mkdir()
        self.assertEqual(self.validate_missing(empty)["gates"]["bundle_integrity"], "UNCONFIRMED")

    def validate_missing(self, path):
        return xr.validate_bundle(path, expected_event_id=EVENT_ID, not_before=NOT_BEFORE)

    def test_cli_exit_codes(self):
        bundle = self.build()
        with redirect_stdout(io.StringIO()) as out:
            self.assertEqual(xr.main([str(bundle), "--expected-event-id", EVENT_ID, "--not-before", NOT_BEFORE]), 0)
        self.assertEqual(json.loads(out.getvalue())["classification_scope"], "ADAPTER_BUNDLE_ONLY")
        with redirect_stdout(io.StringIO()):
            self.assertEqual(xr.main([str(bundle), "--expected-event-id", "OTHER", "--not-before", NOT_BEFORE]), 1)

    def test_helper_refuses_existing_output_and_unsafe_paths(self):
        bundle = self.build()
        with self.assertRaises(FileExistsError):
            collect.write_bundle(bundle, {}, inr_event_id=EVENT_ID, bundle_id="x")
        with self.assertRaises(ValueError):
            collect.write_bundle(self.tmp / "unsafe", {"raw/../x": b""}, inr_event_id=EVENT_ID, bundle_id="x")

    def test_predicate_and_role_sets_are_closed(self):
        schema = xr.load_schema()
        self.assertEqual(tuple(schema["$defs"]["adapter_result"]["properties"]["predicates"]["required"]),
                         xr.PREDICATES)
        self.assertEqual(len(xr.PREDICATES), 10)
        roles = schema["properties"]["evidence_files"]["items"]["properties"]["role"]["enum"]
        self.assertEqual(set(roles), set(xr.SINGLETON_PATHS) | set(xr.PER_CASE_PATHS) | {"target_file"})
        for name in ("raw_runner_identity", "raw_git_identity", "raw_event_start", "adapter_result"):
            self.assertIs(schema["$defs"][name]["additionalProperties"], False)
        self.assertIs(schema["additionalProperties"], False)


class StaticTests(unittest.TestCase):
    """Checks that need no pinned target bytes."""

    def test_path_rules(self):
        for bad in ("", "/abs", "C:/x", "a\\b", "a/../b", "./a", "a//b", "a/", "x:y", "a/./b"):
            self.assertIsNotNone(xr._path_problem(bad), bad)
        self.assertIsNone(xr._path_problem("raw/target/schema/portfolio_state_metadata_v0.schema.json"))

    def test_trusted_configuration_comes_from_committed_config(self):
        t = xr.trusted_configuration()
        self.assertEqual(t["target_sha"], "c5e1cfa2fb52874fe9c97e0eade6a120c12cb27b")
        self.assertEqual(t["origin_reference_set_id"], "INR_ORIGIN_SET_PSM_001_V0")
        self.assertEqual(t["origin_reference_set_digest"], sup.ORIGIN_DIGEST)
        self.assertEqual(t["target_profile_digest"], sup.PROFILE_DIGEST)
        self.assertEqual(len(t["cases"]), 11)

    def test_self_assertion_names_detected(self):
        for key in ("fresh", "non_origin", "all_writer_isolation", "git_verified", "classification",
                    "fresh_hosted_runner_candidate", "derived_predicates", "verdict"):
            self.assertTrue(xr._SELF_ASSERTION.search(key), key)

    def test_acquisition_log_parser(self):
        good = "\n".join([xr.ACQUISITION_LOG_HEADER, "method: git-clone", "source: s", "ref: r", "$ git clone s",
                          "head: h", ""]).encode()
        fields, commands = xr.parse_acquisition_log(good)
        self.assertEqual(fields["method"], "git-clone")
        for bad in (b"method: git-clone\n", good + b"head: again\n", good + b"free text\n"):
            with self.assertRaises(ValueError):
                xr.parse_acquisition_log(bad)

    def test_strict_json(self):
        for bad in (b'{"a": 1, "a": 2}', b'\xef\xbb\xbf{}', b'{"a": NaN}', b'\xff'):
            with self.assertRaises(ValueError):
                xr._strict_json(bad)

    def test_sha256sums_parser(self):
        line = ("a" * 64 + "  raw/x.json\n").encode()
        self.assertEqual(xr.parse_sha256sums(line), {"raw/x.json": "a" * 64})
        for bad in (line + line, ("a" * 64 + "  ../x\n").encode(), b"zz  raw/x\n"):
            with self.assertRaises(ValueError):
                xr.parse_sha256sums(bad)


if __name__ == "__main__":
    unittest.main()
