"""INR-XR-001 v0 external-run bundle adapter (validation and derivation only).

SCOPE (read first)
------------------
This adapter checks a disk bundle that an external runner produced. It checks four
things: the hash binding and path safety of the bundle, its binding to the trusted
INR-001 configuration committed in this repository, the ten bounded external
predicates it derives itself from raw evidence, and a fail-closed classification.

A PASS from this adapter is an ADAPTER/BUNDLE PASS ONLY:

* It is NOT an INR external reconstruction PASS and NOT a fresh local INR PASS. The
  result carries ``inr_external_reconstruction_pass: false`` and
  ``fresh_local_inr_pass: false`` as constants.
* A disk bundle is checked only for internal consistency and hash binding. In v0
  nothing provider-signed binds the bundle to the runner it describes, so a
  fabricated but fully consistent bundle would also pass (the synthetic fixture in
  test 20 shows exactly that).
* Runner self-declarations never create PASS. A ``runner_declarations`` object is
  INFORMATIONAL: it is echoed under ``ignored_runner_declarations`` and never read
  by any derivation. Any other field outside the strict schemas is REJECTED, and
  that includes fields named after a derived predicate or a classification
  (``fresh``, ``non_origin``, ``all_writer_isolation``, ``git_verified``,
  ``classification`` ...). A manifest that carries one fails its schema, which is
  FAIL. A raw evidence file that carries one is inadmissible, so every predicate
  that depends on it stays not established.
* The supervisor report inside ``raw/event_complete.json`` is the INR-001 r3
  supervisor result. It is used only to LOWER a result, never to raise one.

The trusted target, profile, origin and tooling digests come only from the committed
INR configuration, loaded through ``supervisor_inr_v0.configuration()``, which
checks the schema and the pinned digests. They are never taken from the bundle.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
from pathlib import Path, PurePosixPath
import re
import sys

if __name__ == "__main__":  # pragma: no cover - CLI only
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from docs.inr_001 import supervisor_inr_v0 as sup  # noqa: E402
from docs.inr_001.schema_check import check  # noqa: E402

XR_ROOT = Path(__file__).resolve().parent
REPO_ROOT = sup.ROOT.parents[1]
SCHEMA_PATH = XR_ROOT / "schema" / "external_run_manifest_v0.schema.json"
INR_EVENT_SCHEMA_PATH = sup.ROOT / "schema" / "inr_event_v0.schema.json"
MANIFEST_NAME = "external_run_manifest.json"
RESULT_SCHEMA_VERSION = "inr.xr.adapter_result.v0"

# The fixed, bounded predicate list (INR-XR-001 section 15). Nothing else is derived.
PREDICATES = (
    "runner_identity_established",
    "fresh_hosted_runner_candidate",
    "fresh_workspace_established",
    "independent_acquisition_established",
    "no_shared_origin_filesystem_evidence",
    "no_shared_mutable_cache_evidence",
    "python_311_established",
    "git_identity_established",
    "protected_tree_isolation_established",
    "current_event_capture_established",
)
# Adapter-owned preconditions; reported separately from the predicates.
GATES = ("bundle_integrity", "trusted_reference_binding")

SINGLETON_PATHS = {
    "acquisition_log": "raw/acquisition.log",
    "runner_identity": "raw/runner_identity.json",
    "workspace_provenance": "raw/workspace_provenance.json",
    "isolation_checks": "raw/isolation_checks.json",
    "python_identity": "raw/python_identity.json",
    "git_identity": "raw/git_identity.json",
    "event_start": "raw/event_start.json",
    "post_measurement": "raw/post_measurement.json",
    "event_complete": "raw/event_complete.json",
    "sha256sums": "raw/sha256sums.txt",
}
PER_CASE_PATHS = {
    "command_result": "raw/command_results/{}.capture.json",
    "stdout": "raw/stdout/{}.stdout",
    "stderr": "raw/stderr/{}.stderr",
}
TARGET_PATH = "raw/target/{}"
RAW_JSON_DEFS = {
    "runner_identity": "raw_runner_identity",
    "workspace_provenance": "raw_workspace_provenance",
    "isolation_checks": "raw_isolation_checks",
    "python_identity": "raw_python_identity",
    "git_identity": "raw_git_identity",
    "event_start": "raw_event_start",
    "post_measurement": "raw_post_measurement",
    "event_complete": "raw_event_complete",
}
EXAMPLE_FILE = "portfolio_state_v0.example.json"
VALIDATOR_FILE = "validate_psm_v0.py"

KNOWN_HOSTED_PROVIDERS = frozenset({"github-actions"})
HOSTED_ENVIRONMENT = "github-hosted"
FRESH_BOOT_WINDOW_SECONDS = 4 * 3600
ACQUISITION_LOG_HEADER = "# inr-xr acquisition log v0"
ACQUISITION_FIELDS = ("method", "source", "ref", "head")
ACQUISITION_METHODS = frozenset({"git-clone", "git-fetch"})
NETWORK_FS_TYPES = frozenset({"nfs", "nfs4", "cifs", "smb", "smbfs", "smb3", "9p", "fuse.sshfs",
                              "sshfs", "virtiofs", "afs", "glusterfs", "ceph", "drvfs", "vboxsf"})
PROTECTED_CATEGORIES = ("target_files", "profile_origin_binding", "inputs", "command_inventory",
                        "capture_configuration", "execution_tree", "git_objects")
# Protected-tree layout (relative to protected_tree.root): tooling checkout + target clone.
TOOLING_ENTRIES = {
    "capture_configuration": ("docs/inr_001/supervisor_inr_v0.py", "docs/inr_001/runtime_probe.py"),
    "profile_origin_binding": ("docs/inr_001/profiles/psm_001_inr_target_profile_v0.json",
                               "docs/inr_001/origin/psm_001_origin_reference_set_v0.json"),
    "inputs": ("docs/inr_001/input_cases.py",),
    "command_inventory": ("docs/inr_001/profiles/psm_001_inr_target_profile_v0.json",),
}
TOOLING_PREFIX = "tooling/"
TARGET_PREFIX = "target/"
SUPERVISOR_REL = "docs/inr_001/supervisor_inr_v0.py"
PROBE_REL = "docs/inr_001/runtime_probe.py"

_COPY_COMMAND = re.compile(
    r"(?:^|[\s;&|(])(?:cp|rsync|robocopy|xcopy|copy|copy-item|scp|ditto|mv|move|move-item|ln|mklink)(?=\s|$)",
    re.IGNORECASE)
_SHARED_STORE_OPTION = re.compile(r"(?:^|\s)(?:--reference(?:-if-able)?|--shared|-s|--local|-l)(?=\s|=|$)")
_GIT_ACQUIRE = re.compile(r"(?:^|[\s;&|])git(?:\s.*)?\s(?:clone|fetch)(?=\s|$)")
_SELF_ASSERTION = re.compile(
    r"(?:^|_)(?:fresh|non_origin|origin|isolation|verified|established|candidate|classification|"
    r"verdict|assurance|pass|predicates?|derived|trusted|attested)(?:_|$)", re.IGNORECASE)
_DRIVE = re.compile(r"^[A-Za-z]:[\\/]")

NONCLAIMS = (
    "adapter/bundle result only",
    "not an INR external reconstruction PASS",
    "not a fresh local INR PASS",
    "disk bundle verified by internal consistency and hash binding only; no provider-signed attestation",
    "runner self-declarations are informational only and never create PASS",
    "not IW admission",
    "not Human Final",
    "not production permission",
)


# --- small utilities ---------------------------------------------------------------

def _strict_json(data):
    """UTF-8 JSON object/array; duplicate keys, BOM and non-finite numbers rejected."""
    def pairs(items):
        out = {}
        for key, value in items:
            if key in out:
                raise ValueError("duplicate JSON key: " + key)
            out[key] = value
        return out

    def no_constant(name):
        raise ValueError("non-finite JSON number: " + name)

    return json.loads(data.decode("utf-8"), object_pairs_hook=pairs, parse_constant=no_constant)


def _lf_digest(path):
    """Digest of a committed text file as its LF blob (Windows autocrlf-insensitive)."""
    return sup.digest(Path(path).read_bytes().replace(b"\r\n", b"\n"))


def _timestamp(value):
    """RFC 3339 UTC ('...Z') to POSIX seconds, or None."""
    if type(value) is not str or not value.endswith("Z"):
        return None
    main, _, fraction = value[:-1].partition(".")
    try:
        moment = _dt.datetime.strptime(main, "%Y-%m-%dT%H:%M:%S").replace(tzinfo=_dt.timezone.utc)
    except ValueError:
        return None
    if fraction and not fraction.isdigit():
        return None
    return moment.timestamp() + (float("0." + fraction) if fraction else 0.0)


def _is_absolute(path):
    return type(path) is str and (path.startswith("/") or bool(_DRIVE.match(path)))


def _norm(path):
    return path.replace("\\", "/").rstrip("/")


def _within(child, parent):
    if type(child) is not str or type(parent) is not str or not parent:
        return False
    c, p = _norm(child), _norm(parent)
    if _DRIVE.match(child) or _DRIVE.match(parent):
        c, p = c.casefold(), p.casefold()
    return c == p or c.startswith(p + "/")


def _path_problem(rel):
    """Relative POSIX path inside the bundle; returns a problem or None."""
    if type(rel) is not str or not rel:
        return "empty path"
    if "\\" in rel or "\0" in rel or ":" in rel:
        return "backslash, NUL or colon in path (absolute or drive path)"
    if rel.startswith("/") or PurePosixPath(rel).is_absolute():
        return "absolute path"
    if any(part in ("", ".", "..") for part in rel.split("/")):
        return "path traversal or non-normalised path"
    return None


def _is_link(path):
    is_junction = getattr(path, "is_junction", None)
    return path.is_symlink() or bool(is_junction and is_junction())


def _schema_problems(value, schema):
    problems = []
    for problem in check(value, schema):
        key = problem.rpartition(": unknown ")[2] if ": unknown " in problem else None
        if key is not None and _SELF_ASSERTION.search(key):
            problems.append(problem + " (self-assertion field rejected; derived predicates and "
                            "classifications are adapter-owned, never runner input)")
        else:
            problems.append(problem)
    return sorted(problems)


def load_schema():
    return _strict_json(SCHEMA_PATH.read_bytes())


def trusted_configuration():
    """Trusted values from the committed INR configuration only (never from a bundle)."""
    profile, origin = sup.configuration()
    repositories = sorted({item.get("repository") for item in origin["origins"]}, key=str)
    if len(repositories) != 1 or type(repositories[0]) is not str or not repositories[0]:
        raise ValueError("trusted origin set does not name exactly one repository")
    if {tuple(c["argv"]) for c in profile["command_inventory"]} != {sup.ARGV_TEMPLATE}:
        raise ValueError("trusted profile argv template differs from the supervisor template")
    tooling = {}
    for paths in TOOLING_ENTRIES.values():
        for rel in paths:
            tooling[rel] = _lf_digest(REPO_ROOT / rel)
    return {"target_sha": sup.TARGET_SHA,
            "target_profile_id": profile["target_profile_id"],
            "target_profile_digest": sup.PROFILE_DIGEST,
            "origin_reference_set_id": origin["origin_reference_set_id"],
            "origin_reference_set_digest": sup.ORIGIN_DIGEST,
            "repository": repositories[0],
            "target_file_digests": dict(profile["target_file_digests"]),
            "cases": [dict(case) for case in profile["required_cases"]],
            "commands": [dict(command) for command in profile["command_inventory"]],
            "tooling_digests": tooling}


def expected_paths(trusted):
    """Every admissible evidence path and its role (closed set from trusted config)."""
    paths = {path: role for role, path in SINGLETON_PATHS.items()}
    for case in trusted["cases"]:
        for role, pattern in PER_CASE_PATHS.items():
            paths[pattern.format(case["case_id"])] = role
    for name in trusted["target_file_digests"]:
        paths[TARGET_PATH.format(name)] = "target_file"
    return paths


def parse_sha256sums(data):
    listed = {}
    for line in data.decode("ascii").split("\n"):
        if not line:
            continue
        match = re.fullmatch(r"([0-9a-f]{64}) [ *](.+)", line)
        if match is None or match.group(2) in listed or _path_problem(match.group(2)):
            raise ValueError("malformed sha256sums line")
        listed[match.group(2)] = match.group(1)
    return listed


# --- bundle integrity -----------------------------------------------------------------

def _load_bundle(root, trusted, schema, findings):
    """Path safety + hash binding. Returns (manifest, files) or None (rejected)."""
    gate = "bundle_integrity"
    root = Path(root)
    if _is_link(root) or not root.is_dir():
        findings.add(gate, "unconfirmed", "bundle directory missing")
        return None
    base = root.resolve()
    manifest_path = root / MANIFEST_NAME
    if _is_link(manifest_path):
        findings.add(gate, "fail", "manifest is a symlink")
        return None
    if not manifest_path.is_file():
        findings.add(gate, "unconfirmed", "external_run_manifest.json missing")
        return None
    try:
        manifest = _strict_json(manifest_path.read_bytes())
    except (OSError, ValueError) as exc:
        findings.add(gate, "fail", f"manifest unparsable: {exc}")
        return None
    problems = _schema_problems(manifest, schema)
    if problems:
        for problem in problems:
            findings.add(gate, "fail", "manifest schema violation: " + problem)
        return None
    expected = expected_paths(trusted)
    seen, folded, files = set(), set(), {}
    rejected = False
    for entry in manifest["evidence_files"]:
        rel, role = entry["path"], entry["role"]
        problem = _path_problem(rel)
        if problem:
            findings.add(gate, "fail", f"evidence path rejected ({problem}): {rel!r}")
            rejected = True
            continue
        if rel in seen or rel.casefold() in folded:
            findings.add(gate, "fail", f"duplicate evidence entry: {rel}")
            rejected = True
            continue
        seen.add(rel)
        folded.add(rel.casefold())
        if expected.get(rel) != role:
            findings.add(gate, "fail", f"unknown or substituted evidence entry: role {role} at {rel}")
            rejected = True
            continue
        current, link = root, None
        for part in rel.split("/"):
            current = current / part
            if _is_link(current):
                link = current
                break
        if link is not None:
            findings.add(gate, "fail", f"symlink/junction in evidence path: {rel}")
            rejected = True
            continue
        target = root.joinpath(*rel.split("/"))
        if not target.exists():
            findings.add(gate, "unconfirmed", f"bound evidence file missing: {rel}")
            continue
        try:
            inside = target.is_file() and target.resolve(strict=True).is_relative_to(base)
        except OSError:
            inside = False
        if not inside:
            findings.add(gate, "fail", f"evidence is not a regular file inside the bundle: {rel}")
            rejected = True
            continue
        data = target.read_bytes()
        if sup.digest(data) != entry["sha256"]:
            findings.add(gate, "fail", f"raw evidence hash mismatch (tamper evidence): {rel}")
            rejected = True
            continue
        files[rel] = data
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        for name in sorted(dirnames + filenames):
            full = Path(dirpath) / name
            rel = full.relative_to(root).as_posix()
            if _is_link(full):
                findings.add(gate, "fail", f"symlink/junction inside the bundle: {rel}")
                rejected = True
            elif name in filenames and rel != MANIFEST_NAME and rel not in seen:
                findings.add(gate, "fail", f"unbound file in bundle (evidence substitution): {rel}")
                rejected = True
    sums = files.get(SINGLETON_PATHS["sha256sums"])
    if sums is not None:
        try:
            listed = parse_sha256sums(sums)
        except (UnicodeError, ValueError) as exc:
            findings.add(gate, "fail", f"raw/sha256sums.txt malformed: {exc}")
            rejected = True
        else:
            bound = {e["path"]: e["sha256"] for e in manifest["evidence_files"] if e["role"] != "sha256sums"}
            if listed != bound:
                findings.add(gate, "fail", "raw/sha256sums.txt disagrees with the manifest bindings")
                rejected = True
    for rel in expected:
        if rel not in seen:
            findings.add(gate, "unconfirmed", f"required evidence absent: {rel}")
    if rejected:
        return None
    if not findings.has_issue(gate):
        findings.establish(gate)
    return manifest, files


class _Evidence:
    """Admitted, schema-valid raw evidence (immutable after construction)."""

    def __init__(self, manifest, files, trusted, schema):
        self.manifest = manifest
        self.files = files
        self.trusted = trusted
        self.docs, self.problems, self.ignored = {}, {}, []
        if "runner_declarations" in manifest:
            self.ignored.append(MANIFEST_NAME + ":runner_declarations="
                                + json.dumps(manifest["runner_declarations"], sort_keys=True))
        for role, def_name in RAW_JSON_DEFS.items():
            self._parse(role, SINGLETON_PATHS[role], schema["$defs"][def_name])
        for case in trusted["cases"]:
            rel = PER_CASE_PATHS["command_result"].format(case["case_id"])
            self._parse(("command_result", case["case_id"]), rel, schema["$defs"]["raw_command_result"])

    def _parse(self, key, rel, schema):
        data = self.files.get(rel)
        if data is None:
            self.docs[key], self.problems[key] = None, [f"{rel}: evidence absent or not admitted"]
            return
        try:
            value = _strict_json(data)
        except ValueError as exc:
            self.docs[key], self.problems[key] = None, [f"{rel}: unparsable ({exc})"]
            return
        problems = _schema_problems(value, schema)
        if problems:
            self.docs[key], self.problems[key] = None, [f"{rel}: {p}" for p in problems]
            return
        if type(value) is dict and "runner_declarations" in value:
            self.ignored.append(rel + ":runner_declarations="
                                + json.dumps(value["runner_declarations"], sort_keys=True))
        self.docs[key], self.problems[key] = value, []

    def need(self, findings, predicate, key, level="unconfirmed"):
        value = self.docs.get(key)
        if value is None:
            for message in self.problems.get(key) or [f"{key}: evidence absent"]:
                findings.add(predicate, level, message)
        return value

    def stream(self, kind, case_id):
        return self.files.get(PER_CASE_PATHS[kind].format(case_id))

    def child_report(self, case_id):
        data = self.stream("stdout", case_id)
        try:
            report = json.loads(data.decode("ascii"))
        except (AttributeError, UnicodeError, ValueError):
            return None
        if type(report) is not dict or type(report.get("identity")) is not dict:
            return None
        return report

    def target_bytes(self, name):
        return self.files.get(TARGET_PATH.format(name))

    def required_objects(self):
        """Required commits from the digest-verified pinned example (as the supervisor)."""
        data = self.target_bytes(EXAMPLE_FILE)
        if data is None or sup.digest(data) != self.trusted["target_file_digests"].get(EXAMPLE_FILE):
            return None
        record = json.loads(data)
        return sorted({s["git_commit"] for s in record["source_records"]}
                      | {s["git_commit"] for s in record["revision_provenance"]})


def _finish(findings, predicate):
    if not findings.has_issue(predicate):
        findings.establish(predicate)


# --- predicate derivations (adapter-owned; each establishes only with no issue) ----

def _derive_trusted_binding(f, ev):
    gate, t, m = "trusted_reference_binding", ev.trusted, ev.manifest
    if m["target_sha"] != t["target_sha"]:
        f.add(gate, "blocked", "manifest target SHA is not the trusted TARGET_SHA")
    if m["accepted_origin_reference"] != {"origin_reference_set_id": t["origin_reference_set_id"],
                                          "origin_reference_set_digest": t["origin_reference_set_digest"]}:
        f.add(gate, "unconfirmed", "origin reference is not the trusted accepted origin reference set "
                                   "(alternate, stale or executor-selected origin)")
    if m["accepted_target_profile_reference"] != {"target_profile_id": t["target_profile_id"],
                                                  "target_profile_digest": t["target_profile_digest"]}:
        f.add(gate, "unconfirmed", "target profile reference is not the trusted pinned profile")
    _finish(f, gate)


def _derive_runner_identity(f, ev):
    p = "runner_identity_established"
    ri = ev.need(f, p, "runner_identity")
    if ri is None:
        return
    if ri["provider"] not in KNOWN_HOSTED_PROVIDERS:
        f.add(p, "unconfirmed", f"provider {ri['provider']!r} is not a known hosted CI provider")
    if ri["workflow_run_attempt"] < 1:
        f.add(p, "unconfirmed", "workflow run attempt invalid")
    if _timestamp(ri["boot_time"]) is None or _timestamp(ri["job_started_at"]) is None:
        f.add(p, "unconfirmed", "provisioning/job start time unparsable")
    _finish(f, p)


def _derive_fresh_runner(f, ev):
    p = "fresh_hosted_runner_candidate"
    ri = ev.need(f, p, "runner_identity")
    wp = ev.need(f, p, "workspace_provenance")
    if ri is not None:
        if ri["runner_environment"] == "self-hosted":
            f.add(p, "fail", "runner evidence says self-hosted: not a fresh hosted runner")
        elif ri["runner_environment"] != HOSTED_ENVIRONMENT:
            f.add(p, "unconfirmed", "runner environment not established as provider-hosted")
        if ri["provider"] not in KNOWN_HOSTED_PROVIDERS:
            f.add(p, "unconfirmed", "provider unknown; hosted provisioning not established")
        boot, start = _timestamp(ri["boot_time"]), _timestamp(ri["job_started_at"])
        if boot is None or start is None:
            f.add(p, "unconfirmed", "provisioning/job start time unparsable")
        elif boot > start:
            f.add(p, "fail", "runner boot time after job start (inconsistent provisioning evidence)")
        elif start - boot > FRESH_BOOT_WINDOW_SECONDS:
            f.add(p, "unconfirmed", "runner machine booted more than 4h before the job; freshness not established")
    if wp is not None:
        if wp["prior_job_artifacts"]:
            f.add(p, "fail", "artifacts of a previous job on the runner (reused runner)")
        if wp["cache_restore_events"]:
            f.add(p, "fail", "mutable cache restored into the job")
        if wp["inherited_writable_paths"]:
            f.add(p, "fail", "inherited writable state on the runner")
    _finish(f, p)


def _derive_fresh_workspace(f, ev):
    p = "fresh_workspace_established"
    wp = ev.need(f, p, "workspace_provenance")
    ri = ev.need(f, p, "runner_identity")
    gi = ev.need(f, p, "git_identity")
    if wp is not None:
        if wp["initial_listing"]:
            f.add(p, "fail", "workspace not empty before acquisition (reused workspace)")
        if wp["inherited_writable_paths"]:
            f.add(p, "fail", "inherited writable workspace paths")
        created, began, done = (_timestamp(wp[k]) for k in
                                ("workspace_created_at", "acquisition_started_at", "acquisition_completed_at"))
        if None in (created, began, done):
            f.add(p, "unconfirmed", "workspace/acquisition timing unparsable")
        elif not created <= began <= done:
            f.add(p, "fail", "workspace creation/acquisition timing out of order")
        elif ri is not None and _timestamp(ri["job_started_at"]) is not None \
                and created < _timestamp(ri["job_started_at"]):
            f.add(p, "fail", "workspace created before this job started (inherited workspace)")
    if gi is not None:
        if gi["dot_git_kind"] != "directory":
            f.add(p, "fail", "acquired .git is a file (linked worktree of another checkout)")
        if gi["worktree_status"]:
            f.add(p, "fail", "acquired worktree not clean (modified or untracked files present)")
        if wp is not None and not _within(gi["repository_root"], wp["workspace_path"]):
            f.add(p, "unconfirmed", "acquired repository is not inside the fresh workspace")
    _finish(f, p)


def parse_acquisition_log(data):
    text = data.decode("utf-8")
    lines = text.split("\n")
    if not lines or lines[0] != ACQUISITION_LOG_HEADER:
        raise ValueError("missing acquisition log header")
    fields, commands = {}, []
    for line in lines[1:]:
        if not line or line.startswith("> "):
            continue
        if line.startswith("$ "):
            commands.append(line[2:])
            continue
        key, sep, value = line.partition(": ")
        if not sep or key not in ACQUISITION_FIELDS or key in fields or not value:
            raise ValueError("unrecognised or duplicate acquisition log line")
        fields[key] = value
    if set(fields) != set(ACQUISITION_FIELDS) or not commands:
        raise ValueError("acquisition log lacks method/source/ref/head or commands")
    return fields, commands


def _derive_acquisition(f, ev):
    p, t = "independent_acquisition_established", ev.trusted
    target = t["target_sha"]
    data = ev.files.get(SINGLETON_PATHS["acquisition_log"])
    fields = commands = None
    if data is None:
        f.add(p, "unconfirmed", "raw/acquisition.log absent or not admitted")
    else:
        try:
            fields, commands = parse_acquisition_log(data)
        except (UnicodeError, ValueError) as exc:
            f.add(p, "unconfirmed", f"raw/acquisition.log unparsable: {exc}")
    authoritative = re.compile(r"https://github\.com/" + re.escape(t["repository"]) + r"(?:\.git)?")
    if fields is not None:
        source = fields["source"]
        if fields["method"] not in ACQUISITION_METHODS:
            f.add(p, "unconfirmed", "acquisition method is not an independent Git acquisition")
        if source.startswith(("file:", "/", "\\", ".")) or _DRIVE.match(source):
            f.add(p, "fail", "acquired from a local path (origin worktree copy)")
        elif authoritative.fullmatch(source) is None:
            f.add(p, "unconfirmed", "acquisition source is not the authoritative repository")
        for command in commands:
            if _COPY_COMMAND.search(command):
                f.add(p, "fail", f"copy/link command in acquisition (origin worktree copied): {command}")
            if "file://" in command or (_GIT_ACQUIRE.search(command) and _SHARED_STORE_OPTION.search(command)):
                f.add(p, "fail", f"acquisition shares a local object store or path: {command}")
        if not any(_GIT_ACQUIRE.search(command) for command in commands):
            f.add(p, "unconfirmed", "no git clone/fetch command in the acquisition log")
        if fields["ref"] != target or fields["head"] != target:
            f.add(p, "blocked", "acquisition ref/HEAD is not the trusted TARGET_SHA")
    gi = ev.need(f, p, "git_identity")
    required = ev.required_objects()
    if required is None:
        f.add(p, "unconfirmed", "trusted required-object set unavailable (pinned example not admitted)")
    for name, want in sorted(t["target_file_digests"].items()):
        data = ev.target_bytes(name)
        if data is None:
            f.add(p, "unconfirmed", f"acquired target file absent: {name}")
        elif sup.digest(data) != want:
            f.add(p, "blocked", f"acquired target file differs from the pinned profile digest: {name}")
    if gi is not None:
        if gi["head"] != target:
            f.add(p, "blocked", "acquired repository HEAD is not TARGET_SHA")
        if fields is not None:
            if gi["head"] != fields["head"]:
                f.add(p, "fail", "Git HEAD contradicts the acquisition log")
            if _norm(gi["remote_url"]).removesuffix(".git") != _norm(fields["source"]).removesuffix(".git"):
                f.add(p, "fail", "repository remote contradicts the logged acquisition source")
        if required is not None:
            present = {o["object"] for o in gi["required_objects"] if o["present"] and o["type"] == "commit"}
            for sha in [target, *required]:
                if sha not in present:
                    f.add(p, "blocked", f"required target object unavailable: {sha}")
    pm = ev.docs.get("post_measurement")
    if pm is not None:
        if pm["measurements"]["distribution_files"] != t["target_file_digests"]:
            f.add(p, "blocked", "event-measured target digests differ from the pinned profile")
        if pm["git_probe"]["head"] != target:
            f.add(p, "blocked", "event Git probe HEAD is not TARGET_SHA")
        if required is not None and pm["git_probe"]["required_objects"] != required:
            f.add(p, "fail", "event required-object set contradicts the pinned example")
    _finish(f, p)


def _derive_no_shared_origin(f, ev):
    p = "no_shared_origin_filesystem_evidence"
    iso = ev.need(f, p, "isolation_checks")
    gi = ev.need(f, p, "git_identity")
    if iso is not None:
        for mount in iso["mounts"]:
            network = mount["network"] or mount["fs_type"].lower() in NETWORK_FS_TYPES
            if mount["writable"] and (mount["shared"] or network):
                f.add(p, "fail", f"writable shared/network filesystem mounted: {mount['mount_point']} "
                                 f"({mount['fs_type']})")
        store = iso["git_object_store"]
        if store["shared"] or store["alternates"]:
            f.add(p, "fail", "Git object store shared with another repository")
        if iso["origin_snapshot_restored"]:
            f.add(p, "fail", "origin snapshot restored into the runner")
    if gi is not None and gi["alternates"]:
        f.add(p, "fail", "Git alternates point at another object store")
    _finish(f, p)


def _derive_no_shared_cache(f, ev):
    p = "no_shared_mutable_cache_evidence"
    iso = ev.need(f, p, "isolation_checks")
    wp = ev.need(f, p, "workspace_provenance")
    if iso is not None:
        for cache in iso["package_caches"] + iso["build_caches"]:
            if cache["restored"]:
                f.add(p, "fail", f"restored mutable cache: {cache['path']}")
            if cache["shared"]:
                f.add(p, "fail", f"shared mutable cache: {cache['path']}")
    if wp is not None and wp["cache_restore_events"]:
        f.add(p, "fail", "cache restore events recorded for the job")
    _finish(f, p)


def _derive_python(f, ev):
    p = "python_311_established"
    py = ev.need(f, p, "python_identity", level="blocked")
    if py is None:
        return
    version = py["version"]
    if tuple(version[:2]) != sup.FROZEN_PYTHON:
        f.add(p, "blocked", f"runner Python {'.'.join(map(str, version[:3]))} is outside frozen 3.11.x")
    if py["implementation"].lower() != "cpython":
        f.add(p, "blocked", "Python implementation is not CPython (frozen policy unknown)")
    if not py["version_string"].startswith(".".join(map(str, version[:3]))):
        f.add(p, "fail", "Python version string contradicts the version")
    if not _is_absolute(py["executable"]):
        f.add(p, "unconfirmed", "Python executable path not absolute")
    es, pm = ev.docs.get("event_start"), ev.docs.get("post_measurement")
    if es is not None:
        if es["supervisor"]["python_version"] != version or es["supervisor"]["executable"] != py["executable"]:
            f.add(p, "fail", "supervisor interpreter contradicts the recorded Python identity")
    if pm is not None and pm["measurements"]["python_executable_sha256"] != py["executable_sha256"]:
        f.add(p, "fail", "event-measured interpreter digest contradicts the Python identity")
    for case in ev.trusted["cases"]:
        report = ev.child_report(case["case_id"])
        if report is None:
            continue
        observed = report["identity"]
        if observed.get("python_version") != version or observed.get("python_executable") != py["executable"]:
            f.add(p, "fail", f"{case['case_id']}: child interpreter contradicts the Python identity")
    _finish(f, p)


def _derive_git(f, ev):
    p = "git_identity_established"
    gi = ev.need(f, p, "git_identity", level="blocked")
    if gi is None:
        return
    if not _is_absolute(gi["executable"]):
        f.add(p, "blocked", "Git executable path not absolute")
    if gi["which_git"] != gi["executable"]:
        f.add(p, "blocked", "PATH Git differs from the measured executable (ambiguous)")
    if re.match(r"git version [0-9]+\.[0-9]+", gi["version"]) is None:
        f.add(p, "blocked", "Git version unavailable")
    if gi["environment"]:
        f.add(p, "blocked", "GIT_* environment influence present")
    if gi["replace_refs"] or gi["alternates"] or gi["grafts"]:
        f.add(p, "blocked", "replace refs, alternates or grafts influence object identity")
    if gi["shallow"]:
        f.add(p, "blocked", "shallow repository: required history not established")
    for key in gi["config_keys"]:
        key = key.lower()
        if key.startswith(sup._REJECTED_GIT_CONFIG_PREFIXES) or key in sup._REJECTED_GIT_CONFIG_KEYS:
            f.add(p, "blocked", f"unresolved Git configuration influence: {key}")
    if gi["head"] != ev.trusted["target_sha"]:
        f.add(p, "blocked", "repository HEAD is not TARGET_SHA")
    pm = ev.docs.get("post_measurement")
    if pm is not None:
        probe = pm["git_probe"]
        for key in ("executable", "executable_sha256", "version", "repository_root", "head", "config_keys"):
            if probe[key] != gi[key]:
                f.add(p, "fail", f"event Git probe {key} contradicts the Git identity")
    for case in ev.trusted["cases"]:
        report = ev.child_report(case["case_id"])
        if report is None:
            continue
        observed = report["identity"]
        if (observed.get("git_which") != gi["executable"] or observed.get("git_shadowing") != []
                or observed.get("git_environment") != [["GIT_NO_REPLACE_OBJECTS", "1"]]):
            f.add(p, "fail", f"{case['case_id']}: child Git resolution contradicts the Git identity")
    _finish(f, p)


def protected_tree_digest(entries):
    """Adapter rule: digest over (category, path, kind, sha256), sorted."""
    rows = sorted([e["category"], e["path"], e["kind"], e["sha256"]] for e in entries)
    return sup.digest(sup.canonical(rows))


def _derive_protected_tree(f, ev):
    p, t = "protected_tree_isolation_established", ev.trusted
    iso = ev.need(f, p, "isolation_checks")
    if iso is None:
        return
    tree = iso["protected_tree"]
    if iso["execution_principal"]["is_admin"]:
        f.add(p, "unconfirmed", "administrative execution principal can bypass permissions")
    covered = tree["categories_covered"]
    if sorted(covered) != sorted(PROTECTED_CATEGORIES) or len(set(covered)) != len(covered):
        f.add(p, "unconfirmed", "protected categories not all covered")
    by_category = {}
    for entry in tree["entries"]:
        label = f"{entry['category']}:{entry['path']}"
        by_category.setdefault(entry["category"], {})[entry["path"]] = entry
        if _path_problem(entry["path"]):
            f.add(p, "fail", f"protected entry path not relative to the protected root: {label}")
        if entry["symlink"] or entry["reparse_point"]:
            f.add(p, "fail", f"protected entry is a symlink/junction: {label}")
        if entry["kind"] == "file" and entry["link_count"] != 1:
            f.add(p, "fail", f"protected file has extra hard links: {label}")
        if entry["kind"] == "file" and not entry["sha256"]:
            f.add(p, "unconfirmed", f"protected file digest missing: {label}")
        if entry["writable_by_others"]:
            f.add(p, "fail", f"protected entry writable by another principal: {label}")
        if entry["writable_by_principal"]:
            f.add(p, "unconfirmed", f"protected entry writable by the execution principal: {label}")
    for category in PROTECTED_CATEGORIES:
        if not by_category.get(category):
            f.add(p, "unconfirmed", f"no protected entries for {category}")
    named = [("target_files", TARGET_PREFIX + "docs/portfolio_state/" + name, want)
             for name, want in sorted(t["target_file_digests"].items())]
    for category, paths in TOOLING_ENTRIES.items():
        named.extend((category, TOOLING_PREFIX + rel, t["tooling_digests"][rel]) for rel in paths)
    for category, rel, want in named:
        entry = by_category.get(category, {}).get(rel)
        if entry is None:
            f.add(p, "unconfirmed", f"protected entry missing: {category}:{rel}")
        elif entry["kind"] != "file" or entry["sha256"] != want:
            f.add(p, "fail", f"protected entry differs from the trusted digest: {category}:{rel}")
    for parent in tree["parent_chain"]:
        if parent["writable_by_others"]:
            f.add(p, "fail", f"protected parent writable by another principal: {parent['path']}")
        if parent["writable_by_principal"]:
            f.add(p, "unconfirmed", f"writable parent (replacement risk not excluded): {parent['path']}")
    for mount in iso["mounts"]:
        network = mount["network"] or mount["fs_type"].lower() in NETWORK_FS_TYPES
        if mount["writable"] and (mount["shared"] or network) and _within(tree["root"], mount["mount_point"]):
            f.add(p, "fail", f"protected tree on a writable shared/network mount: {mount['mount_point']}")
    for cache in iso["package_caches"] + iso["build_caches"]:
        if cache["restored"] and (_within(cache["path"], tree["root"]) or _within(tree["root"], cache["path"])):
            f.add(p, "fail", f"restored cache overlaps the protected tree: {cache['path']}")
    gi = ev.docs.get("git_identity")
    if gi is not None and not _within(gi["repository_root"], tree["root"]):
        f.add(p, "unconfirmed", "acquired repository not inside the protected tree")
    computed = protected_tree_digest(tree["entries"])
    if tree["freeze_digest"] != computed:
        f.add(p, "fail", "freeze digest does not match the recorded protected entries")
    if tree["post_execution_digest"] != tree["freeze_digest"]:
        f.add(p, "fail", "protected tree changed between freeze and post measurement")
    _finish(f, p)


def _expected_argv(ev, case_id, record):
    """Structural argv derivation from ARGV_TEMPLATE and the recorded identities."""
    argv = record["argv"]
    py, gi = ev.docs["python_identity"], ev.docs["git_identity"]
    if len(argv) != len(sup.ARGV_TEMPLATE) or argv != record["popen_args"]:
        return False
    stage = _norm(record["cwd"])
    git_dir = _norm(gi["executable"]).rpartition("/")[0]
    return (argv[0] == py["executable"] and argv[1:4] == list(sup.ARGV_TEMPLATE[1:4])
            and _norm(argv[4]).endswith("/" + PROBE_REL)
            and _norm(argv[5]) == stage + "/" + VALIDATOR_FILE
            and _norm(argv[6]) == stage + "/" + case_id + ".json"
            and argv[7] == gi["repository_root"]
            and _norm(record["env_path"]) == git_dir)


def _derive_event(f, ev, expected_event_id, not_before):
    p, t, m = "current_event_capture_established", ev.trusted, ev.manifest
    es = ev.need(f, p, "event_start")
    pm = ev.need(f, p, "post_measurement")
    ec = ev.docs.get("event_complete")
    if ec is None:
        f.add(p, "unconfirmed", "EVENT_COMPLETE absent or not admitted: incomplete lifecycle")
        for message in ev.problems.get("event_complete", []):
            f.add(p, "unconfirmed", message)
    event_id = m["inr_event_id"]
    if expected_event_id is None:
        f.add(p, "unconfirmed", "no operator-issued expected event ID: current-event binding not established")
    elif event_id != expected_event_id:
        f.add(p, "fail", "bundle belongs to another event than the operator-issued one (stale/historical)")
    if not_before is None:
        f.add(p, "unconfirmed", "no operator not-before time: staleness not excluded")
    ri, wp = ev.docs.get("runner_identity"), ev.docs.get("workspace_provenance")
    challenge = es["challenge"] if es is not None else None
    for name, doc in (("event_start", es), ("post_measurement", pm), ("event_complete", ec)):
        if doc is not None and (doc["inr_event_id"] != event_id
                                or (challenge is not None and doc["challenge"] != challenge)):
            f.add(p, "fail", f"{name} bound to another event/challenge")
    started = None
    if es is not None:
        if es["target_sha"] != t["target_sha"]:
            f.add(p, "blocked", "event target SHA is not TARGET_SHA")
        if es["accepted_target_profile_binding"] != {"target_profile_id": t["target_profile_id"],
                                                     "target_profile_digest": t["target_profile_digest"]} \
                or es["accepted_origin_reference_binding"] != {
                    "origin_reference_set_id": t["origin_reference_set_id"],
                    "origin_reference_set_digest": t["origin_reference_set_digest"]}:
            f.add(p, "unconfirmed", "event bound to a different profile/origin than the trusted configuration")
        s = es["supervisor"]
        if not (s["is_supervisor_process"] is True and s["isolated"] == 1 and s["no_site"] == 1
                and s["dont_write_bytecode"] is True and s["pid"] > 0):
            f.add(p, "unconfirmed", "event not produced by an isolated INR supervisor process")
        if es["supervisor_sha256"] != t["tooling_digests"][SUPERVISOR_REL]:
            f.add(p, "unconfirmed", "INR supervisor differs from the accepted tooling")
        started = _timestamp(es["started_at"])
        if started is None:
            f.add(p, "unconfirmed", "event start time unparsable")
        else:
            job = _timestamp(ri["job_started_at"]) if ri is not None else None
            if job is not None and started < job:
                f.add(p, "fail", "event started before this runner job (historical event imported)")
            acquired = _timestamp(wp["acquisition_completed_at"]) if wp is not None else None
            if acquired is not None and started < acquired:
                f.add(p, "fail", "event started before acquisition completed")
            if not_before is not None and started < not_before:
                f.add(p, "fail", "event predates the operator's run request (stale/historical bundle)")
    lifecycle = pm["lifecycle"] if pm is not None else None
    if pm is not None:
        if any(lifecycle[a] > lifecycle[b] for a, b in zip(sup.LIFECYCLE, sup.LIFECYCLE[1:])):
            f.add(p, "fail", "supervisor lifecycle out of order")
        if es is not None and lifecycle["EVENT_START"] != es["event_start_ns"]:
            f.add(p, "fail", "EVENT_START contradicts the post-measurement lifecycle")
        meas = pm["measurements"]
        validator = t["target_file_digests"][VALIDATOR_FILE]
        if meas["source_before_sha256"] != validator or meas["source_after_sha256"] != validator:
            f.add(p, "fail", "executed source before/after measurement differs from the pinned validator")
        if meas["probe_sha256"] != t["tooling_digests"][PROBE_REL]:
            f.add(p, "unconfirmed", "runtime probe differs from the accepted tooling")
    if ec is not None:
        done = _timestamp(ec["completed_at"])
        if done is None or (started is not None and done < started):
            f.add(p, "fail", "EVENT_COMPLETE time missing or before EVENT_START")
        if lifecycle is not None and ec["event_complete_ns"] < lifecycle["CAPTURE_COMPLETE"]:
            f.add(p, "fail", "EVENT_COMPLETE precedes CAPTURE_COMPLETE")
        _check_supervisor_report(f, p, ec["supervisor_report"], event_id,
                                 es["supervisor"]["pid"] if es is not None else None)
    _check_children(f, p, ev, es, lifecycle)
    _finish(f, p)


def _check_supervisor_report(f, p, report, event_id, supervisor_pid):
    """Negative-only use of the INR-001 r3 supervisor result (can lower, never raise)."""
    schema = _strict_json(INR_EVENT_SCHEMA_PATH.read_bytes())["properties"]["verification"]
    problems = check(report, schema)
    if problems:
        f.add(p, "unconfirmed", "supervisor report is not a valid INR-001 r3 supervisor result")
        return
    if report["result_kind"] != "FRESH_SUPERVISOR_RUN":
        f.add(p, "unconfirmed", "supervisor report is not a fresh supervisor-process run")
    if report["event_id"] != event_id or report["supervisor_pid"] != supervisor_pid:
        f.add(p, "fail", "supervisor report bound to another event/supervisor")
    for name in sup.LOCAL_PREDICATES:
        status = report["predicates"][name]
        if status == "FAIL":
            f.add(p, "fail", f"supervisor reported local predicate {name} FAIL")
        elif status != "PASS":
            f.add(p, "unconfirmed", f"supervisor did not establish local predicate {name}")
    if report["pass_allowed"] or any(report["predicates"][n] != "UNCONFIRMED" for n in sup.EXTERNAL_PREDICATES):
        f.add(p, "fail", "supervisor report contradicts INR-001 v0 semantics (external predicates are never "
                         "supervisor-established)")


def _check_children(f, p, ev, es, lifecycle):
    t = ev.trusted
    challenge = es["challenge"] if es is not None else None
    supervisor_pid = es["supervisor"]["pid"] if es is not None else None
    validator = t["target_file_digests"][VALIDATOR_FILE]
    commands = {c["case_id"]: c for c in t["commands"]}
    previous_end = None
    for index, spec in enumerate(t["cases"], 1):
        cid = spec["case_id"]
        record = ev.docs.get(("command_result", cid))
        stdout, stderr = ev.stream("stdout", cid), ev.stream("stderr", cid)
        if record is None or stdout is None or stderr is None:
            f.add(p, "unconfirmed", f"{cid}: child provenance absent (capture record or streams missing)")
            for message in ev.problems.get(("command_result", cid), []):
                f.add(p, "unconfirmed", message)
            continue
        command = commands.get(cid, {})
        if (record["case_id"] != cid or record["command_id"] != command.get("command_id")
                or record["sequence"] != index or command.get("sequence") != index):
            f.add(p, "fail", f"{cid}: capture record does not match the closed command inventory")
        if record["event_id"] != ev.manifest["inr_event_id"] or (challenge is not None
                                                                 and record["challenge"] != challenge):
            f.add(p, "fail", f"{cid}: capture record bound to another event/challenge (replay)")
        if sup.digest(stdout) != record["stdout_sha256"] or sup.digest(stderr) != record["stderr_sha256"]:
            f.add(p, "fail", f"{cid}: captured streams contradict the capture record digests")
        if record["child_pid"] <= 0 or record["child_pid"] == supervisor_pid:
            f.add(p, "fail", f"{cid}: child process identity missing or equal to the supervisor")
        if record["start_ns"] > record["end_ns"] or (previous_end is not None and record["start_ns"] < previous_end):
            f.add(p, "fail", f"{cid}: child timing out of order")
        if lifecycle is not None and not (lifecycle["COMMAND_EXECUTION_BEGIN"] <= record["start_ns"]
                                          and record["end_ns"] <= lifecycle["EXECUTION_COMPLETE"]):
            f.add(p, "fail", f"{cid}: child ran outside the supervisor execution window")
        previous_end = record["end_ns"]
        if ev.docs.get("python_identity") is None or ev.docs.get("git_identity") is None:
            f.add(p, "unconfirmed", f"{cid}: argv cannot be derived (Python/Git identity not admitted)")
        elif not _expected_argv(ev, cid, record):
            f.add(p, "fail", f"{cid}: executed argv/PATH differs from the supervisor-derived template")
        if record["env_git"] != [["GIT_NO_REPLACE_OBJECTS", "1"]]:
            f.add(p, "fail", f"{cid}: child Git environment not exact")
        report = ev.child_report(cid)
        if report is None:
            f.add(p, "unconfirmed", f"{cid}: child runtime report missing")
            continue
        if (report.get("event_id") != record["event_id"] or report.get("challenge") != record["challenge"]
                or report.get("case_id") != cid or report.get("case_nonce") != record["case_nonce"]):
            f.add(p, "fail", f"{cid}: child output not bound to this launch (replay)")
        errors = report.get("errors")
        for problem in sup.refusal_problems(spec, errors):
            f.add(p, "fail", problem)
        rc = record["return_code"]
        if rc not in spec["accepted_return_codes"] or (rc == 0) != (errors == []):
            f.add(p, "fail", f"{cid}: return code contradicts the expected refusal semantics")
        observed = report["identity"]
        expected = {"source_sha256": validator, "post_source_sha256": validator,
                    "input_sha256": spec["input_digest"], "target_preloaded": False, "site_loaded": False,
                    "sitecustomize_loaded": False, "usercustomize_loaded": False, "isolated": 1,
                    "no_site": 1, "dont_write_bytecode": True}
        for key, want in expected.items():
            if observed.get(key) != want or type(observed.get(key)) is not type(want):
                f.add(p, "fail", f"{cid}: child identity {key} mismatch")
        if len(record["argv"]) < 6 or observed.get("source_path") != record["argv"][5]:
            f.add(p, "fail", f"{cid}: executed source path mismatch")
        if observed.get("cwd") != record["cwd"]:
            f.add(p, "fail", f"{cid}: child working directory mismatch")


# --- entry point ------------------------------------------------------------------------

def _result(findings, trusted, ignored):
    derived = findings.result()["derived_result"]
    t = trusted or {"target_sha": sup.TARGET_SHA, "target_profile_id": "UNAVAILABLE",
                    "target_profile_digest": sup.PROFILE_DIGEST, "origin_reference_set_id": "UNAVAILABLE",
                    "origin_reference_set_digest": sup.ORIGIN_DIGEST}
    return {"schema_version": RESULT_SCHEMA_VERSION,
            "result_kind": "EXTERNAL_BUNDLE_ADAPTER_RESULT",
            "classification": derived,
            "classification_scope": "ADAPTER_BUNDLE_ONLY",
            "adapter_bundle_pass": derived == "PASS",
            "inr_external_reconstruction_pass": False,
            "fresh_local_inr_pass": False,
            "gates": {name: findings.status(name) for name in GATES},
            "predicates": {name: findings.status(name) for name in PREDICATES},
            "blocked": findings.collect("blocked"), "fail": findings.collect("fail"),
            "unconfirmed": findings.collect("unconfirmed"),
            "contradictions": list(findings.contradictions),
            "ignored_runner_declarations": list(ignored),
            "trusted_configuration": {k: t[k] for k in ("target_sha", "target_profile_id",
                                                        "target_profile_digest", "origin_reference_set_id",
                                                        "origin_reference_set_digest")},
            "nonclaims": list(NONCLAIMS)}


def validate_bundle(bundle_dir, *, expected_event_id=None, not_before=None):
    """Classify one external-run bundle. Read-only; writes nothing.

    ``expected_event_id`` and ``not_before`` are operator parameters, not evidence.
    The operator issues the event ID for a run and records when the run was requested.
    Without them the current-event predicate stays not established.
    """
    findings = sup.Findings(required=GATES + PREDICATES, local=())
    try:
        trusted = trusted_configuration()
        schema = load_schema()
    except (OSError, ValueError, KeyError, TypeError) as exc:
        findings.add("trusted_reference_binding", "blocked", f"trusted INR configuration unavailable: {exc}")
        return _result(findings, None, [])
    loaded = _load_bundle(bundle_dir, trusted, schema, findings)
    if loaded is None:
        return _result(findings, trusted, [])
    evidence = _Evidence(*loaded, trusted, schema)
    boundary = _timestamp(not_before) if not_before is not None else None
    if not_before is not None and boundary is None:
        findings.add("current_event_capture_established", "unconfirmed", "operator not-before time invalid")
    _derive_trusted_binding(findings, evidence)
    _derive_runner_identity(findings, evidence)
    _derive_fresh_runner(findings, evidence)
    _derive_fresh_workspace(findings, evidence)
    _derive_acquisition(findings, evidence)
    _derive_no_shared_origin(findings, evidence)
    _derive_no_shared_cache(findings, evidence)
    _derive_python(findings, evidence)
    _derive_git(findings, evidence)
    _derive_protected_tree(findings, evidence)
    _derive_event(findings, evidence, expected_event_id, boundary)
    return _result(findings, trusted, evidence.ignored)


def main(argv=None):
    parser = argparse.ArgumentParser(prog="validate_external_run_v0", allow_abbrev=False,
                                     description="INR-XR-001 adapter: ADAPTER/BUNDLE result only.")
    parser.add_argument("bundle", type=Path)
    parser.add_argument("--expected-event-id", required=True)
    parser.add_argument("--not-before", required=True, help="RFC 3339 UTC time the operator requested the run")
    args = parser.parse_args(argv)
    result = validate_bundle(args.bundle, expected_event_id=args.expected_event_id, not_before=args.not_before)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["adapter_bundle_pass"] else 1


if __name__ == "__main__":  # pragma: no cover - CLI only
    raise SystemExit(main())
