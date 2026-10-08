"""INR-XR-001 tests (R2): provider trust anchor, INR integration, protected-inventory binding,
the 20 named adversarial tests, and focused/static tests.

Every fixture is synthetic. It is built in a temporary directory prefixed
``inrxr001_t_`` and removed afterwards. No real external run is executed and no
network call is made.

UNIT-TEST TRUST SUBSTITUTES. ``UnitTestTrustSubstituteProvider`` stands in for
GitHub's REST API, and ``trusted_process_substitute()`` stands in for the
verifier-process identity. Both exist only in this test module. They are passed
in-process and cannot be selected from any production CLI, environment variable or
file. A PASS reached with them is a unit-test PASS of the derivation logic, not
provider verification. Real provider verification remains UNCONFIRMED until a real
run.

R2 semantic changes to the earlier 20 adversarial tests:

* ``classification`` is replaced by ``external_assurance``.
* The evidence predicates are renamed ``*_evidence``.
* Tests 1-19 run under the substitute provider so that each verdict comes from the
  injected defect.
* Test 20 runs with NO provider and expects structural PASS with assurance
  UNCONFIRMED (it was ADAPTER/BUNDLE PASS in 304de4d).
"""
from __future__ import annotations

import base64
import copy
import functools
import io
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest import mock

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from docs.inr_001 import supervisor_inr_v0 as sup  # noqa: E402
from docs.inr_001.schema_check import check  # noqa: E402
from docs.inr_001.xr import collect_bundle_v0 as collect  # noqa: E402
from docs.inr_001.xr import provider_github_v0 as gh  # noqa: E402
from docs.inr_001.xr import validate_external_run_v0 as xr  # noqa: E402
from docs.inr_001.xr import xr_verifier_v0 as verifier  # noqa: E402

TMP_PREFIX = "inrxr001_t_"
EVENT_ID = "INR-XR-EVT-0001"
NOT_BEFORE = "2026-10-08T00:30:00Z"
HEAD_SHA = "a1b2c3d4" * 5
ROOT = "/home/runner/work/_temp/inrxr"
TOOLING = ROOT + "/tooling"
TARGET = ROOT + "/target"
STAGE_ROOT = ROOT + "/stage"
STAGE = STAGE_ROOT + "/inr-local-x1y2z3"
PYTHON = "/opt/hostedtoolcache/Python/3.11.9/x64/bin/python3.11"
GIT = "/usr/bin/git"
DEVICE = "2049"
PY_SHA = sup.digest(b"synthetic python executable")
GIT_SHA = sup.digest(b"synthetic git executable")
SUPERVISOR_PID = 4100
CHALLENGE = sup.digest(b"inrxr001 synthetic challenge")
CONFIG_KEYS = ["core.repositoryformatversion", "core.filemode", "core.bare", "remote.origin.url"]
RAW = {role: path for role, path in xr.SINGLETON_PATHS.items()}
RUN_ID, JOB_ID = 18000000001, 51000000001
RUNNER_NAME = "GitHub Actions 1000001"
PARENTS = [ROOT, TARGET, TARGET + "/docs", TARGET + "/docs/portfolio_state",
           TARGET + "/docs/portfolio_state/schema", TARGET + "/.git", TOOLING, TOOLING + "/docs",
           TOOLING + "/docs/inr_001", TOOLING + "/docs/inr_001/profiles", TOOLING + "/docs/inr_001/origin"]


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


def protected_entries(t):
    """Absolute-path inventory bound to the fixture's actual runtime paths."""
    flags = {"writable_by_principal": False, "writable_by_others": False, "symlink": False,
             "reparse_point": False, "link_count": 1, "device": DEVICE}

    def entry(category, path, kind="dir", sha256="", **changes):
        return dict(flags, category=category, path=path, kind=kind, sha256=sha256, **changes)
    entries = [entry("target_tree", TARGET)]
    entries += [entry("target_files", TARGET + "/docs/portfolio_state/" + name, "file", digest)
                for name, digest in sorted(t["target_file_digests"].items())]
    entries += [entry("git_directory", TARGET + "/.git"), entry("git_objects", TARGET + "/.git/objects")]
    entries += [entry(category, TOOLING + "/" + rel, "file", t["tooling_digests"][rel])
                for category, rel in xr.TOOLING_BINDINGS]
    entries.append(entry("execution_tree", STAGE_ROOT, writable_by_principal=True))
    return entries


def parent_record(path, **changes):
    return dict({"path": path, "writable_by_principal": False, "writable_by_others": False, "symlink": False,
                 "reparse_point": False, "device": DEVICE}, **changes)


def refreeze(tree):
    tree["freeze_digest"] = tree["post_execution_digest"] = xr.protected_tree_digest(tree["entries"])


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
                                         supervisor_path=TOOLING + "/" + xr.SUPERVISOR_REL,
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
        "runner_environment": "github-hosted", "repository": t["repository"], "workflow_run_id": str(RUN_ID),
        "workflow_run_attempt": 1, "job_id": str(JOB_ID), "runner_name": RUNNER_NAME,
        "runner_os": "Linux", "runner_arch": "X64", "image_os": "ubuntu24", "image_version": "20260928.1",
        "boot_time": "2026-10-08T00:58:00Z", "job_started_at": "2026-10-08T01:00:00Z",
        "head_sha": HEAD_SHA, "workflow_path": gh.WORKFLOW_PATH}
    parts[RAW["workspace_provenance"]] = {
        "schema_version": "inr.xr.raw.workspace_provenance.v0", "workspace_path": ROOT,
        "workspace_created_at": "2026-10-08T01:01:00Z", "initial_listing": [],
        "acquisition_started_at": "2026-10-08T01:01:05Z", "acquisition_completed_at": "2026-10-08T01:02:00Z",
        "inherited_writable_paths": [], "cache_restore_events": [], "prior_job_artifacts": []}
    entries = protected_entries(t)
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
                           "parent_chain": [parent_record(path) for path in PARENTS],
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


def bundle_digest(bundle):
    path = Path(bundle) / xr.MANIFEST_NAME
    return sup.digest(path.read_bytes()) if path.is_file() else "0" * 64


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


# --- UNIT-TEST TRUST SUBSTITUTES (test module only; unreachable from production paths) ---

class UnitTestTrustSubstituteProvider:
    """UNIT-TEST TRUST SUBSTITUTE for the GitHub REST API (never used outside tests).

    Serves fixed JSON documents for exact API paths. A path it does not know raises
    ``ProviderUnavailable``, which models an unreachable provider or a 404.
    """

    def __init__(self, documents):
        self.documents = documents
        self.requested = []

    def get_json(self, path):
        self.requested.append(path)
        if path not in self.documents:
            raise gh.ProviderUnavailable("unit-test substitute: unknown provider path " + path)
        return copy.deepcopy(self.documents[path])


def substitute_documents(digest, repository=None):
    """GitHub-shaped documents for the fixture run (unit-test trust substitute data)."""
    repository = repository or xr.trusted_configuration()["repository"]
    run = {"id": RUN_ID, "run_attempt": 1, "repository": {"full_name": repository}, "head_sha": HEAD_SHA,
           "path": gh.WORKFLOW_PATH, "status": "completed", "conclusion": "success",
           "created_at": "2026-10-08T00:59:30Z", "run_started_at": "2026-10-08T00:59:40Z"}
    job = {"id": JOB_ID, "run_id": RUN_ID, "run_attempt": 1, "head_sha": HEAD_SHA, "runner_name": RUNNER_NAME,
           "runner_group_name": gh.HOSTED_RUNNER_GROUP, "labels": ["ubuntu-24.04"], "status": "completed",
           "conclusion": "success", "started_at": "2026-10-08T01:00:00Z", "completed_at": "2026-10-08T01:20:00Z"}
    artifact = {"id": 4100000001, "name": gh.ARTIFACT_PREFIX + digest, "size_in_bytes": 48213, "expired": False,
                "created_at": "2026-10-08T01:13:00Z", "workflow_run": {"id": RUN_ID, "head_sha": HEAD_SHA}}
    return {"run": run, "job": job, "artifacts": {"total_count": 1, "artifacts": [artifact]}}


def substitute_provider(bundle=None, *, digest=None, edit=None, repository=None):
    repository = repository or xr.trusted_configuration()["repository"]
    digest = digest if digest is not None else bundle_digest(bundle)
    docs = substitute_documents(digest, repository)
    if edit is not None:
        edit(docs)
    base = f"/repos/{repository}/actions"
    return UnitTestTrustSubstituteProvider({
        f"{base}/runs/{RUN_ID}/attempts/1": docs["run"],
        f"{base}/jobs/{JOB_ID}": docs["job"],
        f"{base}/runs/{RUN_ID}/artifacts?name={gh.ARTIFACT_PREFIX}{digest}": docs["artifacts"]})


def trusted_process_substitute():
    """UNIT-TEST TRUST SUBSTITUTE for the verifier-process identity (in-process tests only)."""
    return mock.patch.object(verifier, "_process_identity",
                             return_value={"pid": os.getpid(), "is_verifier_process": True})


SUBSTITUTE = object()  # sentinel: build the substitute provider from the bundle at validation time


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

    def validate(self, bundle, *, expected_event_id=EVENT_ID, not_before=NOT_BEFORE, provider=SUBSTITUTE,
                 expected_head_sha=HEAD_SHA):
        if provider is SUBSTITUTE:
            provider = substitute_provider(bundle)
        before = sorted(p.relative_to(bundle).as_posix() for p in bundle.rglob("*")) if bundle.exists() else []
        result = xr.validate_bundle(bundle, expected_event_id=expected_event_id, not_before=not_before,
                                    expected_head_sha=expected_head_sha, provider=provider)
        after = sorted(p.relative_to(bundle).as_posix() for p in bundle.rglob("*")) if bundle.exists() else []
        self.assertEqual(before, after, "adapter must not write into the bundle")
        self.assertEqual(check(result, xr.load_schema()["$defs"]["adapter_result"]), [], result)
        self.assertIs(result["inr_external_reconstruction_pass"], False)
        self.assertIs(result["fresh_local_inr_pass"], False)
        self.assertEqual(result["external_assurance_pass"], result["external_assurance"] == "PASS")
        self.assertEqual(result["structural_bundle"] == "PASS", result["gates"]["bundle_integrity"] == "PASS")
        if result["external_assurance"] == "PASS":
            self.assertEqual(set(result["evidence_predicates"].values()) | set(result["gates"].values())
                             | set(result["assurance_predicates"].values()), {"PASS"})
        return result

    def status(self, result, name):
        for group in ("evidence_predicates", "gates", "assurance_predicates"):
            if name in result[group]:
                return result[group][name]
        return result[name]

    def assertClass(self, result, classification, **statuses):
        self.assertEqual(result["external_assurance"], classification, json.dumps(result, indent=1))
        for name, status in statuses.items():
            self.assertEqual(self.status(result, name), status, f"{name}: {json.dumps(result, indent=1)}")

    def messages(self, result):
        return "\n".join(result["blocked"] + result["fail"] + result["unconfirmed"])


@NEEDS_TARGET
class ProviderTests(BundleCase):
    """Section 12 tests 1-7 (provider trust anchor and bundle-to-run binding) plus provider extras."""

    def test_p01_synthetic_bundle_structural_pass_assurance_unconfirmed(self):
        result = self.validate(self.build(), provider=None)
        self.assertEqual(result["structural_bundle"], "PASS")
        self.assertEqual(set(result["evidence_predicates"].values()), {"PASS"})
        self.assertClass(result, "UNCONFIRMED", provider_provenance="UNCONFIRMED", bundle_run_binding="UNCONFIRMED")
        self.assertEqual(set(result["assurance_predicates"].values()), {"UNCONFIRMED"})
        self.assertIsNone(result["provider_run"])

    def test_p02_fake_github_metadata_in_bundle_only(self):
        def edit(parts):
            parts[RAW["runner_identity"]].update(workflow_run_id="99999999999", job_id="88888888888",
                                                 runner_name="GitHub Actions 7", head_sha="f" * 40)
            parts[RAW["runner_identity"]]["runner_declarations"] = {"github_verified": True}
        bundle = self.build(edit=edit, declarations={"provider_attested": True})
        result = self.validate(bundle, provider=None)
        self.assertEqual(result["structural_bundle"], "PASS")
        self.assertClass(result, "UNCONFIRMED", provider_provenance="UNCONFIRMED")
        # Provider asked but has no record of the claimed run/job: never PASS.
        result = self.validate(bundle, provider=substitute_provider(bundle))
        self.assertIn(result["external_assurance"], ("BLOCKED", "UNCONFIRMED"))
        self.assertFalse(result["external_assurance_pass"])
        # The real transport without a credential: BLOCKED, and no network call is made.
        with mock.patch.dict(os.environ, {}, clear=False), \
                mock.patch.object(gh.urllib.request, "build_opener", side_effect=AssertionError("network")):
            os.environ.pop(gh.TOKEN_ENV, None)
            result = self.validate(self.build(), provider=gh.GitHubProvider.from_environment())
        self.assertClass(result, "BLOCKED", provider_provenance="BLOCKED", bundle_run_binding="BLOCKED")

    def test_p03_run_exists_but_bundle_digest_not_bound(self):
        bundle = self.build()
        for edit in (lambda d: d["artifacts"].update(artifacts=[], total_count=0),
                     lambda d: d["artifacts"]["artifacts"][0].update(name=gh.ARTIFACT_PREFIX + "e" * 64),
                     lambda d: d["artifacts"]["artifacts"].append(dict(d["artifacts"]["artifacts"][0], id=2))):
            result = self.validate(bundle, provider=substitute_provider(bundle, edit=edit))
            self.assertClass(result, "UNCONFIRMED", provider_provenance="PASS", bundle_run_binding="UNCONFIRMED")
        # The run published a DIFFERENT bundle (other digest); this one is not bound.
        result = self.validate(bundle, provider=substitute_provider(digest="d" * 64))
        self.assertNotEqual(result["external_assurance"], "PASS")
        self.assertNotEqual(result["bundle_run_binding"], "PASS")

    def test_p04_run_or_job_mismatch(self):
        bundle = self.build()
        for edit in (lambda d: d["job"].update(run_id=RUN_ID + 1),
                     lambda d: d["job"].update(run_attempt=2),
                     lambda d: d["run"].update(id=RUN_ID + 7),
                     lambda d: d["job"].update(id=JOB_ID + 1),
                     lambda d: d["job"].update(runner_name="GitHub Actions 2")):
            result = self.validate(bundle, provider=substitute_provider(bundle, edit=edit))
            self.assertClass(result, "FAIL", provider_provenance="FAIL")
            self.assertNotEqual(result["bundle_run_binding"], "PASS")

    def test_p05_commit_sha_mismatch_fails(self):
        bundle = self.build()
        result = self.validate(bundle, provider=substitute_provider(
            bundle, edit=lambda d: (d["run"].update(head_sha="b" * 40), d["job"].update(head_sha="b" * 40))))
        self.assertClass(result, "FAIL", provider_provenance="FAIL")
        self.assertIn("head SHA differs", self.messages(result))
        result = self.validate(bundle, expected_head_sha="c" * 40)
        self.assertClass(result, "FAIL", provider_provenance="FAIL")
        self.assertIn("operator-designated workflow commit", self.messages(result))
        result = self.validate(bundle, provider=substitute_provider(
            bundle, edit=lambda d: d["run"].update(path=".github/workflows/other.yml")))
        self.assertClass(result, "FAIL", provider_provenance="FAIL")

    def test_p06_stale_run_unconfirmed(self):
        bundle = self.build()

        def stale(docs):
            docs["run"].update(created_at="2026-10-08T00:10:00Z", run_started_at="2026-10-08T00:10:05Z")
        result = self.validate(bundle, provider=substitute_provider(bundle, edit=stale))
        self.assertClass(result, "UNCONFIRMED", provider_provenance="UNCONFIRMED")
        self.assertIn("stale run", self.messages(result))
        for edit in (lambda d: d["job"].update(conclusion="failure"), lambda d: d["run"].update(status="in_progress")):
            result = self.validate(bundle, provider=substitute_provider(bundle, edit=edit))
            self.assertClass(result, "UNCONFIRMED", provider_provenance="UNCONFIRMED")
        result = self.validate(bundle, expected_head_sha=None)
        self.assertClass(result, "UNCONFIRMED", provider_provenance="UNCONFIRMED")

    def test_p07_valid_mocked_binding_assurance_pass_unit_test_only(self):
        """UNIT-TEST PASS under a trust substitute; not provider verification."""
        bundle = self.build()
        provider = substitute_provider(bundle)
        result = self.validate(bundle, provider=provider)
        self.assertClass(result, "PASS", structural_bundle="PASS", provider_provenance="PASS",
                         bundle_run_binding="PASS")
        self.assertEqual(set(result["assurance_predicates"].values()), {"PASS"})
        self.assertEqual(result["provider_run"]["artifact_name"], gh.ARTIFACT_PREFIX + bundle_digest(bundle))
        self.assertEqual(result["bundle_digest"], bundle_digest(bundle))
        repo = xr.trusted_configuration()["repository"]
        self.assertEqual(provider.requested, [
            f"/repos/{repo}/actions/runs/{RUN_ID}/attempts/1", f"/repos/{repo}/actions/jobs/{JOB_ID}",
            f"/repos/{repo}/actions/runs/{RUN_ID}/artifacts?name={gh.ARTIFACT_PREFIX}{bundle_digest(bundle)}"])

    def test_provider_hosted_runner_and_windows(self):
        bundle = self.build()
        for edit in (lambda d: d["job"].update(runner_group_name="Default"),
                     lambda d: d["job"].update(started_at="2026-10-08T01:11:00Z"),
                     lambda d: d["artifacts"]["artifacts"][0].update(created_at="2026-10-08T02:00:00Z"),
                     lambda d: d["artifacts"]["artifacts"][0]["workflow_run"].update(id=RUN_ID + 1)):
            result = self.validate(bundle, provider=substitute_provider(bundle, edit=edit))
            self.assertClass(result, "FAIL")
        result = self.validate(bundle, provider=substitute_provider(
            bundle, edit=lambda d: d["artifacts"]["artifacts"][0].update(expired=True)))
        self.assertClass(result, "UNCONFIRMED", bundle_run_binding="UNCONFIRMED")
        result = self.validate(bundle, provider=substitute_provider(
            bundle, edit=lambda d: d["run"].update(repository={"full_name": "someone/fork"})))
        self.assertClass(result, "FAIL", provider_provenance="FAIL")

    def test_provider_tampered_manifest_changes_digest(self):
        bundle = self.build()
        provider = substitute_provider(bundle)
        manifest = load_manifest(bundle)
        manifest["bundle_id"] = "XR-SYNTH-0002"
        save_manifest(bundle, manifest)
        result = self.validate(bundle, provider=provider)
        self.assertNotEqual(result["external_assurance"], "PASS")
        self.assertNotEqual(result["bundle_run_binding"], "PASS")


class ProviderTransportTests(unittest.TestCase):
    """The real transport, exercised without any network access."""

    def test_no_token_raises_before_any_network_call(self):
        with mock.patch.object(gh.urllib.request, "build_opener", side_effect=AssertionError("network")):
            with self.assertRaises(gh.ProviderUnavailable):
                gh.GitHubProvider(None).get_json("/repos/a/b/actions/jobs/1")
            with self.assertRaises(gh.ProviderUnavailable):
                gh.GitHubProvider("").get_json("/repos/a/b/actions/jobs/1")

    def test_only_fixed_endpoints_on_fixed_origin(self):
        with mock.patch.object(gh.urllib.request, "build_opener", side_effect=AssertionError("network")):
            for bad in ("/user", "/repos/a/b/actions/runs/1/logs", "https://evil.example/repos/a/b/actions/jobs/1",
                        "/repos/a/b/actions/jobs/1/../../../x", "/repos/a/b/actions/jobs/x"):
                with self.assertRaises(gh.ProviderUnavailable):
                    gh.GitHubProvider("t0ken").get_json(bad)

    def test_request_shape_and_response_origin(self):
        seen = []

        class Response:
            def __init__(self, url, body=b'{"id": 1}', status=200):
                self.url, self.body, self.status = url, body, status

            def geturl(self):
                return self.url

            def read(self, _n):
                return self.body

            def __enter__(self):
                return self

            def __exit__(self, *_):
                return False

        def opener_for(response):
            class Opener:
                def open(self, request, timeout):
                    seen.append((request.full_url, request.get_method(), dict(request.header_items()), timeout))
                    return response
            return lambda *handlers: Opener()
        with mock.patch.object(gh.urllib.request, "build_opener",
                               opener_for(Response("https://api.github.com/repos/a/b/actions/jobs/1"))):
            self.assertEqual(gh.GitHubProvider("t0ken").get_json("/repos/a/b/actions/jobs/1"), {"id": 1})
        url, method, headers, timeout = seen[0]
        self.assertEqual((url, method, timeout), ("https://api.github.com/repos/a/b/actions/jobs/1", "GET", 30))
        self.assertEqual(headers["Authorization"], "Bearer t0ken")
        for response in (Response("https://evil.example/x"), Response("http://api.github.com/x"),
                         Response("https://api.github.com/x", body=b"[1]"),
                         Response("https://api.github.com/x", status=203)):
            with mock.patch.object(gh.urllib.request, "build_opener", opener_for(response)):
                with self.assertRaises(gh.ProviderUnavailable):
                    gh.GitHubProvider("t0ken").get_json("/repos/a/b/actions/jobs/1")

    def test_redirects_refused(self):
        with self.assertRaises(gh.ProviderUnavailable):
            gh._NoRedirect().redirect_request(None, None, 302, "Found", {}, "https://evil.example/")

    def test_no_mock_switch_in_production_paths(self):
        for main in (verifier.main, xr.main):
            out = io.StringIO()
            with redirect_stdout(out), self.assertRaises(SystemExit):
                main(["--help"])
            options = set(re.findall(r"(?<![\w-])(--?[a-z][a-z-]*)", out.getvalue()))
            self.assertLessEqual(options, {"-h", "--help", "--bundle", "--event-id", "--not-before",
                                           "--expected-head-sha", "--expected-event-id"}, options)
        for module in (gh, verifier, xr, collect):
            source = Path(module.__file__).read_text(encoding="utf-8")
            self.assertNotIn("UnitTestTrustSubstitute", source)
            self.assertNotIn("unittest", source)
            environ_uses = re.findall(r"os\.environ[^\n]*", source)
            allowed = {"os.environ.get(TOKEN_ENV))", "os.environ), shell=False)"}
            self.assertLessEqual(set(u.strip() for u in environ_uses), allowed, environ_uses)
        self.assertEqual(Path(verifier.__file__).read_text(encoding="utf-8").count("from_environment()"), 2)


@NEEDS_TARGET
class IntegrationTests(BundleCase):
    """Section 12 tests 8-11: the one-way XR -> INR integration (XR verifier process)."""

    def verify(self, bundle, event_id=EVENT_ID, *, provider=SUBSTITUTE):
        provider = substitute_provider(bundle) if provider is SUBSTITUTE else provider
        with trusted_process_substitute():
            report = verifier.verify_external_event(bundle, event_id, NOT_BEFORE, HEAD_SHA, provider)
        self.assertEqual(report["result_kind"], verifier.TRUSTED_KIND)
        return report

    def assessment(self, bundle):
        return xr.validate_bundle(bundle, expected_event_id=EVENT_ID, not_before=NOT_BEFORE,
                                  expected_head_sha=HEAD_SHA, provider=substitute_provider(bundle))

    def derive(self, assessment, event_id=EVENT_ID, process_trusted=True):
        findings = sup.Findings()
        verifier.derive_inr_predicates(findings, assessment, event_id=event_id, process_trusted=process_trusted)
        return findings.result()

    def test_i00_positive_control_unit_test_substitutes(self):
        report = self.verify(self.build())
        self.assertEqual(report["derived_result"], "PASS", json.dumps(report, indent=1))
        self.assertEqual(set(report["predicates"]), set(sup.REQUIRED_PREDICATES))
        for name in sup.EXTERNAL_PREDICATES:
            self.assertEqual(report["predicates"][name], "PASS")

    def test_i08_wrong_event_id_rejected(self):
        bundle = self.build()
        report = self.verify(bundle, "INR-XR-EVT-0002")
        self.assertFalse(report["pass_allowed"])
        self.assertEqual(report["derived_result"], "FAIL")
        self.assertIn("XR event ID differs", "\n".join(report["fail"]))
        result = self.derive(self.assessment(bundle), event_id="INR-XR-EVT-0002")
        self.assertEqual(result["derived_result"], "FAIL")

    def test_i09_wrong_target_sha_rejected(self):
        report = self.verify(self.build(edit=lambda p: p[RAW["event_start"]].update(target_sha="2" * 40)))
        self.assertFalse(report["pass_allowed"])
        self.assertIn(report["derived_result"], ("FAIL", "BLOCKED"))
        self.assertIn("XR target SHA differs", "\n".join(report["fail"]))
        assessment = self.assessment(self.build())
        assessment["bound_event"]["target_sha"] = "2" * 40
        self.assertEqual(self.derive(assessment)["derived_result"], "FAIL")

    def test_i10_wrong_profile_digest_rejected(self):
        def edit(parts):
            parts[RAW["event_start"]]["accepted_target_profile_binding"]["target_profile_digest"] = "a" * 64
        report = self.verify(self.build(edit=edit))
        self.assertEqual(report["derived_result"], "FAIL")
        self.assertIn("XR profile digest differs", "\n".join(report["fail"]))
        for key, value in (("target_profile_digest", "a" * 64), ("origin_reference_set_digest", "b" * 64)):
            assessment = self.assessment(self.build())
            assessment["bound_event"][key] = value
            self.assertEqual(self.derive(assessment)["derived_result"], "FAIL")

    def test_i11_plain_json_reconstruction_rejected(self):
        bundle = self.build()
        pass_assessment = self.assessment(bundle)
        self.assertEqual(pass_assessment["external_assurance"], "PASS")
        replay = json.loads(json.dumps(pass_assessment))
        # (a) a reconstructed/plain-JSON result outside the verifier process establishes nothing
        result = self.derive(replay, process_trusted=False)
        self.assertEqual(result["derived_result"], "UNCONFIRMED")
        self.assertEqual(set(result["predicates"].values()), {"UNCONFIRMED"})
        # (b) the in-process verifier path (no process identity) is not trusted
        report = verifier.verify_external_event(bundle, EVENT_ID, NOT_BEFORE, HEAD_SHA, substitute_provider(bundle))
        self.assertEqual(report["result_kind"], verifier.UNTRUSTED_KIND)
        self.assertEqual(report["derived_result"], "UNCONFIRMED")
        # (c) no argv input can carry an XR result or predicate
        for extra in (["--xr-result", "r.json"], ["--assessment", "{}"], ["--non-origin", "PASS"]):
            with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                verifier.main(["--bundle", str(bundle), "--event-id", EVENT_ID, "--not-before", NOT_BEFORE,
                               "--expected-head-sha", HEAD_SHA, *extra])
        # (d) a result smuggled into the bundle is a structural FAIL
        forged = self.build()
        manifest = load_manifest(forged)
        manifest["external_assurance"] = "PASS"
        save_manifest(forged, manifest)
        report = self.verify(forged)
        self.assertEqual(report["xr"]["structural_bundle"], "FAIL")
        self.assertFalse(report["pass_allowed"])
        forged = self.build()
        (forged / "raw" / "xr_result.json").write_bytes(json.dumps(replay).encode())
        self.assertEqual(self.verify(forged)["xr"]["structural_bundle"], "FAIL")
        # (e) a plain JSON report replayed to the launcher is not bound to the launched process
        trusted = self.verify(bundle)
        for report, pid in ((dict(trusted), trusted["verifier_pid"] + 1),
                            (dict(trusted, result_kind=verifier.UNTRUSTED_KIND), trusted["verifier_pid"]),
                            (dict(trusted, event_id="OTHER"), trusted["verifier_pid"])):
            accepted = verifier.accept_report(report, child_pid=pid, returncode=0, event_id=EVENT_ID)
            self.assertEqual(accepted["result_kind"], "LAUNCHER_BINDING_FAILURE")
            self.assertFalse(accepted["pass_allowed"])
        accepted = verifier.accept_report(dict(trusted), child_pid=trusted["verifier_pid"], returncode=1,
                                          event_id=EVENT_ID)
        self.assertEqual(accepted["result_kind"], "LAUNCHER_BINDING_FAILURE")
        # (f) the accepted INR supervisor still has no external evidence input
        findings = sup.Findings()
        with mock.patch.dict(os.environ, {"INR_XR_RESULT": json.dumps(replay)}):
            sup._assess_external(findings)
        self.assertEqual({findings.status(n) for n in sup.EXTERNAL_PREDICATES}, {"UNCONFIRMED"})

    def test_integration_requires_bound_digest_and_run(self):
        bundle = self.build()
        for key, value in (("bundle_digest", ""), ("provider_run", None),
                           ("provider_run", {"run_id": RUN_ID, "artifact_name": gh.ARTIFACT_PREFIX + "0" * 64})):
            assessment = self.assessment(bundle)
            assessment[key] = value
            self.assertEqual(self.derive(assessment)["derived_result"], "FAIL", key)
        for key in ("provider_provenance", "bundle_run_binding", "structural_bundle"):
            assessment = self.assessment(bundle)
            assessment[key] = "UNCONFIRMED"
            self.assertNotEqual(self.derive(assessment)["derived_result"], "PASS", key)
        report = self.verify(bundle, provider=None)
        self.assertEqual(report["derived_result"], "UNCONFIRMED")
        report = self.verify(bundle, provider=substitute_provider(
            bundle, edit=lambda d: d["run"].update(created_at="2026-10-08T00:01:00Z",
                                                   run_started_at="2026-10-08T00:01:30Z")))
        self.assertEqual(report["derived_result"], "UNCONFIRMED")

    def test_real_verifier_process_without_token_is_blocked_never_pass(self):
        bundle = self.build()
        env = {k: v for k, v in os.environ.items() if k != gh.TOKEN_ENV}
        with mock.patch.dict(os.environ, env, clear=True):
            report = verifier.launch(bundle, EVENT_ID, NOT_BEFORE, HEAD_SHA)
        self.assertEqual(report["result_kind"], verifier.TRUSTED_KIND, json.dumps(report, indent=1))
        self.assertEqual(report["xr"]["structural_bundle"], "PASS")
        self.assertEqual(report["xr"]["provider_provenance"], "BLOCKED")
        self.assertEqual(report["derived_result"], "BLOCKED")
        self.assertFalse(report["pass_allowed"])


@NEEDS_TARGET
class IsolationBindingTests(BundleCase):
    """Section 12 tests 12-16: protected inventory bound to the actual execution paths (M3)."""

    def edit_tree(self, change):
        parts = valid_parts()
        iso = parts[RAW["isolation_checks"]]
        change(iso["protected_tree"], iso, parts)
        refreeze(iso["protected_tree"])
        return parts

    def assertProtected(self, parts, classification, needle=None):
        result = self.validate(self.build(parts))
        self.assertClass(result, classification, protected_tree_isolation_evidence=classification)
        self.assertEqual(result["assurance_predicates"]["all_writer_isolation_established"], classification)
        if needle:
            self.assertIn(needle, self.messages(result))
        return result

    def test_b12_unrelated_target_path(self):
        def change(tree, _iso, _parts):
            for entry in tree["entries"]:
                if entry["category"] in ("target_files", "target_tree"):
                    entry["path"] = entry["path"].replace(TARGET, ROOT + "/decoy")
        self.assertProtected(self.edit_tree(change), "FAIL", "unrelated path substituted for target_files")

        def change_one(tree, _iso, _parts):
            entry = next(e for e in tree["entries"] if e["path"].endswith("/" + xr.VALIDATOR_FILE))
            entry["path"] = ROOT + "/decoy/docs/portfolio_state/" + xr.VALIDATOR_FILE
        self.assertProtected(self.edit_tree(change_one), "FAIL", "inventory path not used by execution")

    def test_b13_unrelated_git_object_store(self):
        def change(tree, iso, _parts):
            for entry in tree["entries"]:
                if entry["category"] == "git_objects":
                    entry["path"] = ROOT + "/mirror.git/objects"
            iso["git_object_store"]["path"] = ROOT + "/mirror.git/objects"
        self.assertProtected(self.edit_tree(change), "FAIL", "unrelated path substituted for git_objects")

        def runtime_common(tree, _iso, parts):
            parts[RAW["post_measurement"]]["git_probe"]["common_git_dir"] = "/home/runner/shared/weaver.git"
        self.assertProtected(self.edit_tree(runtime_common), "FAIL")

    def test_b14_missing_parent_chain(self):
        def drop_one(tree, _iso, _parts):
            tree["parent_chain"] = [p for p in tree["parent_chain"] if p["path"] != TARGET + "/docs"]
        self.assertProtected(self.edit_tree(drop_one), "UNCONFIRMED", "partial parent chain")

        def root_only(tree, _iso, _parts):
            tree["parent_chain"] = [parent_record(ROOT)]
        self.assertProtected(self.edit_tree(root_only), "UNCONFIRMED", "partial parent chain")

        def no_root(tree, _iso, _parts):
            tree["parent_chain"] = [p for p in tree["parent_chain"] if p["path"] != ROOT]
        self.assertProtected(self.edit_tree(no_root), "UNCONFIRMED", "mount identity of the bounded workspace root")

        def unrelated(tree, _iso, _parts):
            tree["parent_chain"].append(parent_record(ROOT + "/elsewhere"))
        self.assertProtected(self.edit_tree(unrelated), "FAIL", "parent record not on any protected execution path")

        def junction(tree, _iso, _parts):
            tree["parent_chain"][2]["reparse_point"] = True
        self.assertProtected(self.edit_tree(junction), "FAIL")

        def mount(tree, _iso, _parts):
            tree["parent_chain"][3]["device"] = "2050"
        self.assertProtected(self.edit_tree(mount), "UNCONFIRMED", "mount boundary")

    def test_b15_capture_path_outside_inventory(self):
        case = "PSM_REQUIRED_PRODUCTION_NONCLAIM"
        record_rel = xr.PER_CASE_PATHS["command_result"].format(case)
        parts = valid_parts()
        probe = "/tmp/elsewhere/" + xr.PROBE_REL
        parts[record_rel]["argv"][4] = probe
        parts[record_rel]["popen_args"][4] = probe
        self.assertProtected(parts, "FAIL", "capture probe path outside the protected inventory")
        parts = valid_parts()
        parts[RAW["event_start"]]["supervisor_path"] = "/opt/other-checkout/" + xr.SUPERVISOR_REL
        self.assertProtected(parts, "FAIL", "unrelated path substituted")
        parts = valid_parts()
        parts[RAW["event_start"]]["supervisor_path"] = TOOLING + "/run_me.py"
        self.assertProtected(parts, "UNCONFIRMED", "does not identify an INR tooling checkout")
        parts = valid_parts()
        parts[record_rel]["cwd"] = ROOT + "/other/inr-local-q"
        self.assertNotEqual(self.validate(self.build(parts))["evidence_predicates"]
                            ["protected_tree_isolation_evidence"], "PASS")

    def test_b16_partial_inventory_unconfirmed(self):
        def drop_category(tree, _iso, _parts):
            tree["entries"] = [e for e in tree["entries"] if e["category"] != "git_directory"]
            tree["categories_covered"] = [c for c in xr.PROTECTED_CATEGORIES if c != "git_directory"]
        self.assertProtected(self.edit_tree(drop_category), "UNCONFIRMED", "protected inventory lacks git_directory")

        def drop_file(tree, _iso, _parts):
            tree["entries"] = [e for e in tree["entries"] if not e["path"].endswith("/" + xr.EXAMPLE_FILE)]
        self.assertProtected(self.edit_tree(drop_file), "UNCONFIRMED", "protected inventory lacks target_files")

        def drop_capture_config(tree, _iso, _parts):
            tree["entries"] = [e for e in tree["entries"] if e["category"] != "capture_configuration"]
        self.assertProtected(self.edit_tree(drop_capture_config), "UNCONFIRMED")
        parts = valid_parts()
        parts.pop(RAW["post_measurement"])
        result = self.validate(self.build(parts))
        self.assertEqual(result["evidence_predicates"]["protected_tree_isolation_evidence"], "UNCONFIRMED")

    def test_inventory_rules_extra_and_digest(self):
        def extra(tree, _iso, _parts):
            tree["entries"].append(dict(tree["entries"][-1], category="inputs", kind="file", sha256="1" * 64,
                                        path=TOOLING + "/docs/inr_001/unused_input.py", writable_by_principal=False))
        self.assertProtected(self.edit_tree(extra), "FAIL", "inventory path not used by execution")

        def wrong_digest(tree, _iso, _parts):
            next(e for e in tree["entries"] if e["category"] == "inputs")["sha256"] = "2" * 64
        self.assertProtected(self.edit_tree(wrong_digest), "FAIL", "differs from the actual/trusted object")

        def writable_target(tree, _iso, _parts):
            tree["entries"][0]["writable_by_principal"] = True
        self.assertProtected(self.edit_tree(writable_target), "UNCONFIRMED")

        def relative(tree, _iso, _parts):
            tree["entries"][0]["path"] = "target"
        self.assertProtected(self.edit_tree(relative), "FAIL")

        def other_root(tree, _iso, _parts):
            tree["root"] = TARGET
        self.assertProtected(self.edit_tree(other_root), "FAIL", "not the bounded workspace root")


@NEEDS_TARGET
class AdversarialTests(BundleCase):
    """INR-XR-001 section 18: the 20 required adversarial attempts (R2 semantics, see module docstring)."""

    def test_adv_01_fresh_true_without_evidence(self):
        def edit(parts):
            parts[RAW["workspace_provenance"]] = {"schema_version": "inr.xr.raw.workspace_provenance.v0",
                                                  "workspace_path": ROOT,
                                                  "runner_declarations": {"fresh": True,
                                                                          "fresh_workspace_evidence": "PASS"}}
            parts[RAW["runner_identity"]]["runner_declarations"] = {"fresh": True, "fresh_runner": True}
        result = self.validate(self.build(edit=edit, declarations={"fresh": True}))
        self.assertClass(result, "UNCONFIRMED", fresh_hosted_runner_evidence="UNCONFIRMED",
                         fresh_workspace_evidence="UNCONFIRMED")
        self.assertTrue(any("fresh" in item for item in result["ignored_runner_declarations"]))
        # A top-level self-assertion in raw evidence is rejected, not ignored.
        parts = valid_parts()
        parts[RAW["workspace_provenance"]]["fresh"] = True
        result = self.validate(self.build(parts))
        self.assertClass(result, "UNCONFIRMED", fresh_workspace_evidence="UNCONFIRMED")
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
                                          "protected_tree_isolation_evidence": "PASS"}
        result = self.validate(self.build(edit=edit, declarations={"all_writer_isolation": True}))
        self.assertClass(result, "UNCONFIRMED", protected_tree_isolation_evidence="UNCONFIRMED")

    def test_adv_04_missing_runner_identity(self):
        result = self.validate(self.build(edit=lambda parts: parts.pop(RAW["runner_identity"])))
        self.assertClass(result, "UNCONFIRMED", runner_identity_evidence="UNCONFIRMED",
                         fresh_hosted_runner_evidence="UNCONFIRMED", bundle_integrity="UNCONFIRMED")

    def test_adv_05_reused_workspace_evidence(self):
        def edit(parts):
            wp = parts[RAW["workspace_provenance"]]
            wp["initial_listing"] = [".git", "docs", "README.md"]
            wp["workspace_created_at"] = "2026-10-01T09:00:00Z"
        result = self.validate(self.build(edit=edit))
        self.assertClass(result, "FAIL", fresh_workspace_evidence="FAIL")

    def test_adv_06_shared_mutable_cache_detected(self):
        def edit(parts):
            parts[RAW["isolation_checks"]]["package_caches"] = [
                {"path": "/home/runner/.cache/pip", "restored": True, "shared": True}]
            parts[RAW["workspace_provenance"]]["cache_restore_events"] = ["actions/cache restore pip-3.11"]
        result = self.validate(self.build(edit=edit))
        self.assertClass(result, "FAIL", no_shared_mutable_cache_evidence="FAIL",
                         fresh_hosted_runner_evidence="FAIL")

    def test_adv_07_origin_worktree_copied(self):
        def edit(parts):
            parts[RAW["acquisition_log"]] = "\n".join([
                xr.ACQUISITION_LOG_HEADER, "method: git-clone", "source: file:///C:/dev/_tmp/weaver-gzse-001",
                "ref: " + sup.TARGET_SHA, "$ cp -r /mnt/origin/weaver-gzse-001 " + TARGET,
                "head: " + sup.TARGET_SHA, ""])
        result = self.validate(self.build(edit=edit))
        self.assertClass(result, "FAIL", independent_acquisition_evidence="FAIL")

    def test_adv_08_wrong_target_sha(self):
        other = "1" * 40

        def edit(parts):
            parts[RAW["git_identity"]]["head"] = other
            parts[RAW["post_measurement"]]["git_probe"]["head"] = other
            parts[RAW["acquisition_log"]] = parts[RAW["acquisition_log"]].replace(sup.TARGET_SHA, other)
        result = self.validate(self.build(edit=edit))
        self.assertClass(result, "BLOCKED", independent_acquisition_evidence="BLOCKED",
                         git_identity_evidence="BLOCKED")

    def test_adv_09_missing_required_object(self):
        def edit(parts):
            objects = parts[RAW["git_identity"]]["required_objects"]
            objects[-1]["present"] = False
        result = self.validate(self.build(edit=edit))
        self.assertClass(result, "BLOCKED", independent_acquisition_evidence="BLOCKED")
        self.assertIn("required target object unavailable", self.messages(result))

    def test_adv_10_python_314(self):
        def edit(parts):
            parts[RAW["python_identity"]].update(version=[3, 14, 0], version_string="3.14.0 (main) [GCC]")
            parts[RAW["event_start"]]["supervisor"]["python_version"] = [3, 14, 0]
        result = self.validate(self.build(edit=edit))
        self.assertClass(result, "BLOCKED", python_311_evidence="BLOCKED")
        for version in ([3, 10, 12], [3, 12, 7], [3, 13, 1]):
            parts = valid_parts()
            parts[RAW["python_identity"]].update(version=version,
                                                 version_string=".".join(map(str, version)) + " x")
            self.assertClass(self.validate(self.build(parts)), "BLOCKED", python_311_evidence="BLOCKED")

    def test_adv_11_git_unavailable(self):
        result = self.validate(self.build(edit=lambda parts: parts.pop(RAW["git_identity"])))
        self.assertClass(result, "BLOCKED", git_identity_evidence="BLOCKED")
        parts = valid_parts()
        parts[RAW["git_identity"]]["version"] = "git: command not found"
        self.assertClass(self.validate(self.build(parts)), "BLOCKED", git_identity_evidence="BLOCKED")

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
        self.assertEqual(set(result["evidence_predicates"].values()), {"NOT_ESTABLISHED"})
        self.assertEqual(result["structural_bundle"], "FAIL")
        self.assertIn("hash mismatch", self.messages(result))

    def test_adv_14_missing_event_complete(self):
        result = self.validate(self.build(edit=lambda parts: parts.pop(RAW["event_complete"])))
        self.assertClass(result, "UNCONFIRMED", current_event_capture_evidence="UNCONFIRMED")
        self.assertIn("EVENT_COMPLETE absent", self.messages(result))

    def test_adv_15_missing_child_provenance(self):
        case = "PSM_NEG_HUMAN_FINAL_INFERENCE"
        result = self.validate(self.build(
            edit=lambda parts: parts.pop(xr.PER_CASE_PATHS["command_result"].format(case))))
        self.assertClass(result, "UNCONFIRMED", current_event_capture_evidence="UNCONFIRMED")
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
        self.assertClass(result, "FAIL", current_event_capture_evidence="FAIL")
        self.assertIn("stale/historical", self.messages(result))
        # (b) a bundle for another (older) event ID
        result = self.validate(self.build(), expected_event_id="INR-XR-EVT-0002")
        self.assertClass(result, "FAIL", current_event_capture_evidence="FAIL")

        # (c) a historical event imported into a new runner job
        def edit(parts):
            parts[RAW["event_start"]]["started_at"] = "2026-09-01T10:00:00Z"
            parts[RAW["event_complete"]]["completed_at"] = "2026-09-01T10:02:00Z"
        result = self.validate(self.build(edit=edit), not_before="2026-08-01T00:00:00Z")
        self.assertClass(result, "FAIL", current_event_capture_evidence="FAIL")
        self.assertIn("historical event imported", self.messages(result))
        # (d) no operator binding at all: never PASS
        result = self.validate(self.build(), expected_event_id=None, not_before=None)
        self.assertClass(result, "UNCONFIRMED", current_event_capture_evidence="UNCONFIRMED")

    def test_adv_20_valid_synthetic_fixture_structural_pass_assurance_unconfirmed(self):
        """R2: a fully consistent synthetic bundle is STRUCTURAL PASS only; assurance stays UNCONFIRMED."""
        result = self.validate(self.build(), provider=None)
        self.assertEqual(result["structural_bundle"], "PASS")
        self.assertEqual(set(result["evidence_predicates"].values()), {"PASS"})
        self.assertClass(result, "UNCONFIRMED", bundle_integrity="PASS", trusted_reference_binding="PASS",
                         provider_provenance="UNCONFIRMED", bundle_run_binding="UNCONFIRMED")
        self.assertEqual(set(result["assurance_predicates"].values()), {"UNCONFIRMED"})
        self.assertFalse(result["external_assurance_pass"])
        self.assertIs(result["inr_external_reconstruction_pass"], False)
        self.assertIs(result["fresh_local_inr_pass"], False)
        self.assertIn("structural bundle validity is not external assurance", result["nonclaims"])
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
                           ("current_event_capture_evidence", "PASS"), ("git_verified", True)):
            bundle = self.build()
            manifest = load_manifest(bundle)
            manifest[key] = value
            save_manifest(bundle, manifest)
            result = self.validate(bundle)
            self.assertClass(result, "FAIL", bundle_integrity="FAIL")
            self.assertIn("self-assertion field rejected", self.messages(result))

    def test_raw_predicate_field_makes_evidence_inadmissible(self):
        parts = valid_parts()
        parts[RAW["git_identity"]]["git_identity_evidence"] = "PASS"
        result = self.validate(self.build(parts))
        self.assertClass(result, "BLOCKED", git_identity_evidence="BLOCKED")
        self.assertIn("self-assertion field rejected", self.messages(result))

    def test_supervisor_report_is_negative_only(self):
        parts = valid_parts()
        report = parts[RAW["event_complete"]]["supervisor_report"]
        report.update(derived_result="PASS", pass_allowed=True,
                      predicates={name: "PASS" for name in sup.REQUIRED_PREDICATES})
        result = self.validate(self.build(parts))
        self.assertClass(result, "FAIL", current_event_capture_evidence="FAIL")
        parts = valid_parts()
        parts[RAW["event_complete"]]["supervisor_report"]["predicates"]["refusal_semantics"] = "FAIL"
        self.assertClass(self.validate(self.build(parts)), "FAIL", current_event_capture_evidence="FAIL")
        parts = valid_parts()
        parts[RAW["event_complete"]]["supervisor_report"]["result_kind"] = "IN_PROCESS_NOT_TRUSTED"
        self.assertClass(self.validate(self.build(parts)), "UNCONFIRMED",
                         current_event_capture_evidence="UNCONFIRMED")

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
                         protected_tree_isolation_evidence="UNCONFIRMED")

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
        self.assertClass(result, "UNCONFIRMED", runner_identity_evidence="UNCONFIRMED")
        self.assertIn("duplicate JSON key", self.messages(result))

    def test_operator_parameters_required(self):
        self.assertClass(self.validate(self.build(), expected_event_id=None), "UNCONFIRMED",
                         current_event_capture_evidence="UNCONFIRMED")
        self.assertClass(self.validate(self.build(), not_before=None), "UNCONFIRMED",
                         current_event_capture_evidence="UNCONFIRMED")
        self.assertClass(self.validate(self.build(), not_before="yesterday"), "UNCONFIRMED",
                         current_event_capture_evidence="UNCONFIRMED")

    def test_self_hosted_or_unknown_runner(self):
        parts = valid_parts()
        parts[RAW["runner_identity"]]["runner_environment"] = "self-hosted"
        self.assertClass(self.validate(self.build(parts)), "FAIL", fresh_hosted_runner_evidence="FAIL")
        parts = valid_parts()
        parts[RAW["runner_identity"]]["provider"] = "my-laptop"
        self.assertClass(self.validate(self.build(parts)), "UNCONFIRMED",
                         runner_identity_evidence="UNCONFIRMED", fresh_hosted_runner_evidence="UNCONFIRMED")
        parts = valid_parts()
        parts[RAW["runner_identity"]]["boot_time"] = "2026-10-01T00:00:00Z"
        self.assertClass(self.validate(self.build(parts)), "UNCONFIRMED",
                         fresh_hosted_runner_evidence="UNCONFIRMED")
        parts = valid_parts()
        parts[RAW["workspace_provenance"]]["prior_job_artifacts"] = ["/home/runner/work/other-repo"]
        self.assertClass(self.validate(self.build(parts)), "FAIL", fresh_hosted_runner_evidence="FAIL")

    def test_linked_worktree_or_dirty_checkout(self):
        parts = valid_parts()
        parts[RAW["git_identity"]]["dot_git_kind"] = "file"
        self.assertClass(self.validate(self.build(parts)), "FAIL", fresh_workspace_evidence="FAIL")
        parts = valid_parts()
        parts[RAW["git_identity"]]["worktree_status"] = ["?? docs/origin_only_note.md"]
        self.assertClass(self.validate(self.build(parts)), "FAIL", fresh_workspace_evidence="FAIL")

    def test_non_authoritative_or_shared_acquisition(self):
        parts = valid_parts()
        parts[RAW["acquisition_log"]] = parts[RAW["acquisition_log"]].replace(
            "github.com/chrono-vector/weaver-forge", "github.com/someone/fork")
        parts[RAW["git_identity"]]["remote_url"] = "https://github.com/someone/fork.git"
        self.assertClass(self.validate(self.build(parts)), "UNCONFIRMED",
                         independent_acquisition_evidence="UNCONFIRMED")
        parts = valid_parts()
        parts[RAW["acquisition_log"]] = parts[RAW["acquisition_log"]].replace(
            "fetch --no-tags", "fetch --reference /mnt/origin/.git --no-tags")
        self.assertClass(self.validate(self.build(parts)), "FAIL", independent_acquisition_evidence="FAIL")
        parts = valid_parts()
        parts[RAW["acquisition_log"]] = "method: git-clone\n"
        self.assertClass(self.validate(self.build(parts)), "UNCONFIRMED",
                         independent_acquisition_evidence="UNCONFIRMED")

    def test_target_file_digest_mismatch_blocked(self):
        parts = valid_parts()
        parts[xr.TARGET_PATH.format("validate_psm_v0.py")] += b"\n# mutated\n"
        self.assertClass(self.validate(self.build(parts)), "BLOCKED",
                         independent_acquisition_evidence="BLOCKED")

    def test_writable_network_mount_and_shared_object_store(self):
        parts = valid_parts()
        parts[RAW["isolation_checks"]]["mounts"].append(
            {"mount_point": ROOT, "source": "origin-host:/export/weaver", "fs_type": "nfs4", "writable": True,
             "shared": False, "network": False})
        result = self.validate(self.build(parts))
        self.assertClass(result, "FAIL", no_shared_origin_filesystem_evidence="FAIL",
                         protected_tree_isolation_evidence="FAIL")
        parts = valid_parts()
        parts[RAW["isolation_checks"]]["git_object_store"]["alternates"] = ["/mnt/origin/.git/objects"]
        self.assertClass(self.validate(self.build(parts)), "FAIL", no_shared_origin_filesystem_evidence="FAIL")

    def test_protected_tree_rules(self):
        def entry_edit(**changes):
            parts = valid_parts()
            tree = parts[RAW["isolation_checks"]]["protected_tree"]
            next(e for e in tree["entries"] if e["kind"] == "file").update(changes)
            refreeze(tree)
            return parts
        self.assertClass(self.validate(self.build(entry_edit(writable_by_principal=True))), "UNCONFIRMED",
                         protected_tree_isolation_evidence="UNCONFIRMED")
        for changes in ({"writable_by_others": True}, {"link_count": 2}, {"symlink": True},
                        {"reparse_point": True}):
            self.assertClass(self.validate(self.build(entry_edit(**changes))), "FAIL",
                             protected_tree_isolation_evidence="FAIL")
        parts = valid_parts()
        parts[RAW["isolation_checks"]]["protected_tree"]["post_execution_digest"] = "f" * 64
        self.assertClass(self.validate(self.build(parts)), "FAIL", protected_tree_isolation_evidence="FAIL")
        parts = valid_parts()
        parts[RAW["isolation_checks"]]["protected_tree"]["parent_chain"][1]["writable_by_principal"] = True
        self.assertClass(self.validate(self.build(parts)), "UNCONFIRMED",
                         protected_tree_isolation_evidence="UNCONFIRMED")
        parts = valid_parts()
        parts[RAW["isolation_checks"]]["execution_principal"]["is_admin"] = True
        self.assertClass(self.validate(self.build(parts)), "UNCONFIRMED",
                         protected_tree_isolation_evidence="UNCONFIRMED")

    def test_git_ambiguity_blocked(self):
        for key, value in (("replace_refs", ["refs/replace/" + "2" * 40]), ("which_git", "/usr/local/bin/git"),
                           ("environment", [["GIT_DIR", "/tmp/x"]]), ("shallow", True),
                           ("config_keys", CONFIG_KEYS + ["include.path"])):
            parts = valid_parts()
            parts[RAW["git_identity"]][key] = value
            if key == "config_keys":
                parts[RAW["post_measurement"]]["git_probe"]["config_keys"] = value
            self.assertClass(self.validate(self.build(parts)), "BLOCKED", git_identity_evidence="BLOCKED")

    def test_python_implementation_and_inconsistency(self):
        parts = valid_parts()
        parts[RAW["python_identity"]]["implementation"] = "PyPy"
        self.assertClass(self.validate(self.build(parts)), "BLOCKED", python_311_evidence="BLOCKED")
        parts = valid_parts()
        parts[RAW["python_identity"]]["executable_sha256"] = "e" * 64
        self.assertClass(self.validate(self.build(parts)), "FAIL", python_311_evidence="FAIL")

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
        self.assertClass(self.validate(self.build(parts)), "FAIL", current_event_capture_evidence="FAIL")
        parts = valid_parts()
        restream(parts, dict(report, errors=[]))
        self.assertClass(self.validate(self.build(parts)), "FAIL", current_event_capture_evidence="FAIL")
        parts = valid_parts()
        parts[record_rel]["argv"][1] = "-E"
        parts[record_rel]["popen_args"][1] = "-E"
        self.assertClass(self.validate(self.build(parts)), "FAIL", current_event_capture_evidence="FAIL")
        parts = valid_parts()
        parts[stdout_rel] = b"tampered but re-hashed\n"
        self.assertClass(self.validate(self.build(parts)), "FAIL", current_event_capture_evidence="FAIL")

    def test_event_profile_binding_mismatch_unconfirmed(self):
        parts = valid_parts()
        parts[RAW["event_start"]]["accepted_target_profile_binding"]["target_profile_digest"] = "a" * 64
        self.assertClass(self.validate(self.build(parts)), "UNCONFIRMED",
                         current_event_capture_evidence="UNCONFIRMED")

    def test_lifecycle_order_and_event_complete_order(self):
        parts = valid_parts()
        lifecycle = parts[RAW["post_measurement"]]["lifecycle"]
        lifecycle["FREEZE_START"], lifecycle["ACQUISITION_VERIFIED"] = (lifecycle["ACQUISITION_VERIFIED"],
                                                                        lifecycle["FREEZE_START"])
        self.assertClass(self.validate(self.build(parts)), "FAIL", current_event_capture_evidence="FAIL")
        parts = valid_parts()
        parts[RAW["event_complete"]]["event_complete_ns"] = 1
        self.assertClass(self.validate(self.build(parts)), "FAIL", current_event_capture_evidence="FAIL")

    def test_trusted_configuration_unavailable_blocks(self):
        with mock.patch.object(sup, "configuration", side_effect=ValueError("trusted configuration digest mismatch")):
            result = xr.validate_bundle(self.tmp, expected_event_id=EVENT_ID, not_before=NOT_BEFORE)
        self.assertEqual(result["external_assurance"], "BLOCKED")
        self.assertEqual(result["structural_bundle"], "FAIL")
        self.assertEqual(result["gates"]["trusted_reference_binding"], "BLOCKED")
        self.assertEqual(check(result, xr.load_schema()["$defs"]["adapter_result"]), [])

    def test_missing_bundle_and_manifest(self):
        result = self.validate_missing(self.tmp / "absent")
        self.assertEqual(result["external_assurance"], "UNCONFIRMED")
        empty = self.tmp / "empty"
        empty.mkdir()
        self.assertEqual(self.validate_missing(empty)["gates"]["bundle_integrity"], "UNCONFIRMED")

    def validate_missing(self, path):
        return xr.validate_bundle(path, expected_event_id=EVENT_ID, not_before=NOT_BEFORE)

    def test_cli_uses_real_provider_and_never_passes_offline(self):
        bundle = self.build()
        args = [str(bundle), "--expected-event-id", EVENT_ID, "--not-before", NOT_BEFORE,
                "--expected-head-sha", HEAD_SHA]
        env = {k: v for k, v in os.environ.items() if k != gh.TOKEN_ENV}
        with mock.patch.dict(os.environ, env, clear=True), \
                mock.patch.object(gh.urllib.request, "build_opener", side_effect=AssertionError("network")), \
                redirect_stdout(io.StringIO()) as out:
            self.assertEqual(xr.main(args), 1)
        result = json.loads(out.getvalue())
        self.assertEqual((result["structural_bundle"], result["provider_provenance"], result["external_assurance"]),
                         ("PASS", "BLOCKED", "BLOCKED"))
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            xr.main(args[:5])

    def test_helper_refuses_existing_output_and_unsafe_paths(self):
        bundle = self.build()
        with self.assertRaises(FileExistsError):
            collect.write_bundle(bundle, {}, inr_event_id=EVENT_ID, bundle_id="x")
        with self.assertRaises(ValueError):
            collect.write_bundle(self.tmp / "unsafe", {"raw/../x": b""}, inr_event_id=EVENT_ID, bundle_id="x")

    def test_predicate_and_role_sets_are_closed(self):
        schema = xr.load_schema()
        props = schema["$defs"]["adapter_result"]["properties"]
        self.assertEqual(tuple(props["evidence_predicates"]["required"]), xr.EVIDENCE_PREDICATES)
        self.assertEqual(tuple(props["assurance_predicates"]["required"]), xr.ASSURANCE_PREDICATES)
        self.assertEqual(tuple(props["gates"]["required"]), xr.GATES)
        self.assertEqual(len(xr.EVIDENCE_PREDICATES), 10)
        self.assertTrue(all(name.endswith("_evidence") for name in xr.EVIDENCE_PREDICATES))
        self.assertTrue(all(name.endswith("_established") for name in xr.ASSURANCE_PREDICATES))
        self.assertEqual({s for sources in xr.ASSURANCE_SOURCES.values() for s in sources}
                         - {"no_shared_origin_filesystem_evidence", "no_shared_mutable_cache_evidence"},
                         set(xr.EVIDENCE_PREDICATES) - {"no_shared_origin_filesystem_evidence",
                                                        "no_shared_mutable_cache_evidence"})
        roles = schema["properties"]["evidence_files"]["items"]["properties"]["role"]["enum"]
        self.assertEqual(set(roles), set(xr.SINGLETON_PATHS) | set(xr.PER_CASE_PATHS) | {"target_file"})
        for name in ("raw_runner_identity", "raw_git_identity", "raw_event_start", "adapter_result"):
            self.assertIs(schema["$defs"][name]["additionalProperties"], False)
        self.assertIs(schema["additionalProperties"], False)
        categories = schema["$defs"]["raw_isolation_checks"]["properties"]["protected_tree"]["properties"]
        self.assertEqual(tuple(categories["categories_covered"]["items"]["enum"]), xr.PROTECTED_CATEGORIES)


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

    def test_combine_precedence(self):
        self.assertEqual(xr.combine(["PASS", "PASS"]), "PASS")
        self.assertEqual(xr.combine([]), "UNCONFIRMED")
        self.assertEqual(xr.combine(["PASS", "NOT_ESTABLISHED"]), "UNCONFIRMED")
        self.assertEqual(xr.combine(["UNCONFIRMED", "FAIL"]), "FAIL")
        self.assertEqual(xr.combine(["FAIL", "BLOCKED"]), "BLOCKED")
        self.assertEqual(xr.combine(["PASS", None]), "UNCONFIRMED")

    def test_verifier_outside_process_establishes_nothing(self):
        findings = sup.Findings()
        verifier.derive_inr_predicates(findings, {"external_assurance": "PASS"}, event_id=EVENT_ID,
                                       process_trusted=False)
        self.assertEqual(findings.result()["derived_result"], "UNCONFIRMED")
        self.assertFalse(verifier._process_identity()["is_verifier_process"])

    def test_self_assertion_names_detected(self):
        for key in ("fresh", "non_origin", "all_writer_isolation", "git_verified", "classification",
                    "fresh_hosted_runner_evidence", "derived_predicates", "verdict"):
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
