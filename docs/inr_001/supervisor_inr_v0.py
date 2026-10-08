"""INR-001 v0 trusted supervisor. The trust boundary is this PROCESS, not Python.

Intended invocation (normally by ``capture_inr_v0``, or directly by an operator):

    python -I -S -B <worktree>/docs/inr_001/supervisor_inr_v0.py \
        --event-id ID --repository REPO --out EXPORT.json [--ledger PATH] [--work-dir DIR]

Every argument is a NON-TRUST parameter (names and locations). The supervisor
accepts no evidence, snapshot, capture record, provenance, report or classification
from argv, stdin, environment or files. Inside one execution path (``supervise``)
it loads and pins the frozen profile, generates the challenge, reserves the event
in the ledger, measures Git, stages the pinned bytes, launches every target child
itself, reads stdout/stderr/return code directly from the Popen it created, derives
each predicate and the classification from those local values, and emits the report.

There is no evidence object, registry, token or "verify(evidence)" API: nothing
outside ``supervise`` can contribute a PASS-relevant fact, and per-case derivation
happens on the values of the child that was just launched.

Result semantics: every required predicate starts NOT_ESTABLISHED; PASS is the
conjunction of all required predicates explicitly established with no FAIL,
BLOCKED, UNCONFIRMED, contradiction or missing evidence. Zero checks never PASS.
``supervisor_process`` is established only when this code runs as ``__main__`` of
an isolated (-I -S -B) interpreter started on this file. That check is defence in
depth, NOT the boundary: an in-process importer controls its own interpreter and
whatever it computes is caller-controlled self-attestation that no INR consumer
accepts (``capture_inr_v0`` only relays the stdout of the supervisor process it
launched, and ``validate_inr_v0`` treats any disk report as INFORMATIONAL_RECHECK).

Non-origin, shared-state absence and all-writer isolation have no supervisor-owned
evidence source in v0 and are always UNCONFIRMED, so the overall INR result cannot
be PASS in v0. The supervisor's own code, stdlib, OS and local Git installation are
the declared trust base (no hostile-host resistance in v0).
"""
from __future__ import annotations

import os
import sys

if __name__ == "__main__":
    # Never read cached bytecode (no __pycache__ lookups) for modules imported from
    # here on; -B already prevents writing it.
    sys.pycache_prefix = os.devnull

import argparse  # noqa: E402
import base64  # noqa: E402
import hashlib  # noqa: E402
import json  # noqa: E402
from pathlib import Path  # noqa: E402
import secrets  # noqa: E402
import shutil  # noqa: E402
import stat  # noqa: E402
import subprocess  # noqa: E402
import tempfile  # noqa: E402
import time  # noqa: E402

if __name__ == "__main__":  # -I does not put the script directory on sys.path
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from docs.inr_001 import ledger  # noqa: E402
from docs.inr_001.input_cases import case_bytes  # noqa: E402
from docs.inr_001.schema_check import check  # noqa: E402

ROOT = Path(__file__).resolve().parent
SUPERVISOR = Path(__file__).resolve()
TARGET_SHA = "c5e1cfa2fb52874fe9c97e0eade6a120c12cb27b"
PROFILE_DIGEST = "25fa116108c8014904b52302e8f5f583d332bf5de72583551494119b863ae4bb"
ORIGIN_DIGEST = "8512b8a1954673be69e0ab0c9486935eff07e4d91cecdcec6f0a4b50694c8a03"
DEFAULT_GIT = Path("C:/Program Files/Git/cmd/git.exe" if os.name == "nt" else "/usr/bin/git")
PROBE = ROOT / "runtime_probe.py"
CHILD_TIMEOUT_SECONDS = 300
EVENT_SCHEMA_VERSION = "inr.event.v0.r3"
RESULT_SCHEMA_VERSION = "inr.supervisor.result.v0.r3"
FROZEN_PYTHON = (3, 11)
# Supervisor-owned argv template; the profile template must equal it and every
# actual Popen argv must equal it formatted with supervisor-derived values.
ARGV_TEMPLATE = ("{python}", "-I", "-S", "-B", "{probe}", "{source}", "{input}", "{repository}")
LOCAL_PREDICATES = (
    "supervisor_process",        # running as the isolated supervisor process
    "profile_pinned",            # frozen profile/origin loaded, schema-valid, digest-pinned
    "event_challenge",           # fresh challenge, single open ledger reservation, no replay
    "git_runtime",               # pinned Git measured before/after, children resolve it
    "target_identity",           # pinned target bytes / repository at TARGET_SHA
    "runtime_identity",          # frozen Python 3.11 for supervisor and every child, flags
    "child_launched",            # a real child process was launched for every case
    "child_provenance",          # child output bound to this event/challenge/case/nonce
    "argv_exact",                # executed argv/cwd/env equal supervisor-derived values
    "capture_complete",          # streams + reports captured, lifecycle complete/ordered
    "mandatory_cases_executed",  # executed case list == frozen mandatory list, in order
    "module_identity",           # executed source/input/probe bytes re-measured
    "refusal_semantics",         # exact expected errors / return codes per case
)
EXTERNAL_PREDICATES = ("non_origin", "shared_state_absence", "all_writer_isolation")
REQUIRED_PREDICATES = LOCAL_PREDICATES + EXTERNAL_PREDICATES
LIFECYCLE = ("EVENT_START", "BINDINGS_RECORDED", "ENVIRONMENT_RECORDED",
             "ACQUISITION_VERIFIED", "FREEZE_START", "COMMAND_EXECUTION_BEGIN",
             "EXECUTION_COMPLETE", "POST_MEASUREMENT", "CAPTURE_COMPLETE")
NONCLAIMS = ("local INR tooling run only", "not a non-origin reconstruction",
             "not independent reproduction", "not IW admission", "not Human Final",
             "not production permission")
_REJECTED_GIT_CONFIG_PREFIXES = ("include", "extensions.", "alias.")
_REJECTED_GIT_CONFIG_KEYS = frozenset({"core.worktree", "core.fsmonitor", "core.alternaterefscommand"})
_REAL_POPEN = subprocess.Popen  # defence in depth for in-process runs only


class BlockedError(ValueError):
    """A condition that stops the supervised run (recorded as BLOCKED)."""


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def _load_json(path):
    return json.loads(Path(path).read_bytes())


# --- result semantics -----------------------------------------------------------

class Findings:
    """Per-run predicate ledger. Default for every predicate: NOT_ESTABLISHED.

    PASS is conjunctive: every required predicate explicitly established and no
    issue anywhere. An empty Findings is UNCONFIRMED. Establishing a predicate that
    already has an issue is a contradiction (FAIL). The resulting dict is a report,
    not evidence: nothing in INR accepts it as input.
    """

    LEVELS = ("blocked", "fail", "unconfirmed")

    def __init__(self, required=REQUIRED_PREDICATES, local=LOCAL_PREDICATES):
        self.required = tuple(required)
        self.local = tuple(name for name in local if name in self.required)
        self.issues = {name: {level: [] for level in self.LEVELS} for name in self.required}
        self.established = {name: False for name in self.required}
        self.contradictions = []

    def add(self, predicate, level, message):
        self.issues[predicate][level].append(f"{predicate}: {message}")

    def has_issue(self, predicate):
        return any(self.issues[predicate][level] for level in self.LEVELS)

    def establish(self, predicate):
        if self.has_issue(predicate):
            self.contradictions.append(f"{predicate}: established while carrying an issue")
            return
        self.established[predicate] = True

    def status(self, predicate):
        issues = self.issues[predicate]
        if issues["blocked"]:
            return "BLOCKED"
        if issues["fail"]:
            return "FAIL"
        if issues["unconfirmed"]:
            return "UNCONFIRMED"
        return "PASS" if self.established[predicate] else "NOT_ESTABLISHED"

    def _classify(self, names):
        statuses = [self.status(name) for name in names]
        if not names:
            return "UNCONFIRMED"
        if "BLOCKED" in statuses:
            return "BLOCKED"
        if "FAIL" in statuses or self.contradictions:
            return "FAIL"
        if any(status != "PASS" for status in statuses):
            return "UNCONFIRMED"
        return "PASS"

    def collect(self, level):
        return [m for n in self.required for m in self.issues[n][level]]

    def result(self):
        derived = self._classify(self.required)
        not_established = [n for n in self.required if self.status(n) == "NOT_ESTABLISHED"]
        return {"schema_version": RESULT_SCHEMA_VERSION,
                "derived_result": derived, "pass_allowed": derived == "PASS",
                "local_controls_result": self._classify(self.local),
                "predicates": {n: self.status(n) for n in self.required},
                "not_established": not_established,
                "blocked": self.collect("blocked"), "fail": self.collect("fail"),
                "unconfirmed": self.collect("unconfirmed"),
                "contradictions": list(self.contradictions),
                "nonclaims": list(NONCLAIMS)}


def _assess_external(findings):
    """No supervisor-owned evidence source exists in v0; no inputs by construction."""
    findings.add("non_origin", "unconfirmed",
                 "no supervisor-owned objective non-origin evidence source in v0")
    findings.add("shared_state_absence", "unconfirmed",
                 "no supervisor-owned evidence that no shared writable origin state exists")
    findings.add("all_writer_isolation", "unconfirmed",
                 "read-only staging does not establish all-writer immutability")


def refusal_problems(spec, errors):
    """Exact refusal semantics; returns problems only (never establishes anything)."""
    if type(errors) is not list or any(type(e) is not str for e in errors):
        return ["child error list missing/malformed"]
    problems = []
    derived = "PASS" if not errors else "FAIL"
    if derived != spec["expected_classification"]:
        problems.append(f"{spec['case_id']}: derived classification {derived} != {spec['expected_classification']}")
    if errors != spec["expected_errors"]:
        problems.append(f"{spec['case_id']}: refusal reason differs from the frozen intended refusal")
    return problems


# --- trusted configuration and measurement ----------------------------------------

def configuration():
    """Load the frozen profile/origin; both digests are pinned in this file."""
    profile = _load_json(ROOT / "profiles/psm_001_inr_target_profile_v0.json")
    origin = _load_json(ROOT / "origin/psm_001_origin_reference_set_v0.json")
    for value, schema in ((profile, "inr_target_profile_v0.schema.json"),
                          (origin, "inr_origin_reference_v0.schema.json")):
        problems = check(value, _load_json(ROOT / "schema" / schema))
        if problems:
            raise ValueError("trusted configuration schema violation: " + "; ".join(problems))
    for value, field, expected in ((profile, "target_profile_digest", PROFILE_DIGEST),
                                   (origin, "origin_reference_set_digest", ORIGIN_DIGEST)):
        raw = {k: v for k, v in value.items() if k != field}
        if value.get(field) != expected or digest(canonical(raw)) != expected:
            raise ValueError("trusted configuration digest mismatch")
        if value.get("target_sha") != TARGET_SHA:
            raise ValueError("trusted configuration target mismatch")
    return profile, origin


def _git(executable, repository, *args):
    cp = subprocess.run([str(executable), "--no-optional-locks", "--no-replace-objects", *args],
                        cwd=repository, capture_output=True, timeout=60, check=False)
    if cp.returncode:
        raise ValueError("Git probe failed: " + " ".join(args))
    return cp.stdout


def _git_config_keys(raw):
    tokens = raw.split(b"\0")
    keys = []
    for item in tokens[1::2]:  # -z --show-origin: origin NUL key LF value NUL
        keys.append(item.split(b"\n", 1)[0].decode("utf-8", "replace").lower())
    return keys


def probe_git(repository):
    """Measure the pinned Git before any target execution; never run a PATH wrapper."""
    repository = Path(repository).resolve()
    selected = shutil.which("git")
    if not selected or Path(selected).resolve() != DEFAULT_GIT.resolve():
        raise ValueError("Git PATH resolution is not the trusted local installation")
    influences = sorted(k for k in os.environ if k.upper().startswith("GIT_"))
    if influences:
        raise ValueError("Git environment influence: " + ", ".join(influences))
    executable = DEFAULT_GIT.resolve(strict=True)
    before = digest(executable.read_bytes())
    root = _git(executable, repository, "rev-parse", "--show-toplevel").decode().strip()
    head = _git(executable, repository, "rev-parse", "HEAD").decode().strip()
    config = _git(executable, repository, "config", "--show-origin", "--list", "-z")
    for key in _git_config_keys(config):
        if key.startswith(_REJECTED_GIT_CONFIG_PREFIXES) or key in _REJECTED_GIT_CONFIG_KEYS:
            raise ValueError("unresolved Git configuration influence: " + key)
    replacements = _git(executable, repository, "for-each-ref", "refs/replace").decode()
    common = _git(executable, repository, "rev-parse", "--git-common-dir").decode().strip()
    common_path = Path(common)
    if not common_path.is_absolute():
        common_path = repository / common_path
    common_path = common_path.resolve()
    for name in ("objects/info/alternates", "info/grafts"):
        candidate = common_path / name
        if candidate.exists() and candidate.read_bytes().strip():
            raise ValueError("Git object-store influence: " + name)
    if replacements:
        raise ValueError("Git replace refs present")
    _git(executable, repository, "cat-file", "-e", TARGET_SHA + "^{commit}")
    version = _git(executable, repository, "--version").decode().strip()
    if digest(executable.read_bytes()) != before:
        raise ValueError("Git executable changed during probe")
    return {"executable": str(executable), "executable_sha256": before, "version": version,
            "repository_root": str(Path(root).resolve()), "head": head,
            "common_git_dir": str(common_path), "config_keys": _git_config_keys(config)}


def child_environment(git_executable):
    env = {k: v for k, v in os.environ.items()
           if not k.upper().startswith(("PYTHON", "GIT_", "INR_"))}
    env["PATH"] = str(Path(git_executable).parent)
    env["GIT_NO_REPLACE_OBJECTS"] = "1"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


def _command_argv(command, values):
    """Launch-side argv from the frozen profile (checked against ARGV_TEMPLATE)."""
    return [part.format_map(values) for part in command["argv"]]


def _same_path(a, b):
    return (type(a) is str and type(b) is str
            and os.path.normcase(os.path.abspath(a)) == os.path.normcase(os.path.abspath(b)))


def _process_identity():
    """Observed facts about this interpreter (defence in depth, not the boundary)."""
    main = sys.modules.get("__main__")
    main_file = getattr(main, "__file__", None)
    argv0 = sys.argv[0] if sys.argv else ""
    facts = {"pid": os.getpid(), "executable": str(Path(sys.executable).resolve()),
             "python_version": list(sys.version_info[:3]),
             "isolated": sys.flags.isolated, "no_site": sys.flags.no_site,
             "dont_write_bytecode": bool(sys.dont_write_bytecode),
             "argv0": argv0, "main_file": main_file if type(main_file) is str else None}
    facts["is_supervisor_process"] = (
        facts["isolated"] == 1 and facts["no_site"] == 1 and facts["dont_write_bytecode"]
        and _same_path(argv0, str(SUPERVISOR)) and _same_path(facts["main_file"], str(SUPERVISOR))
        and __name__ == "__main__" and "site" not in sys.modules)
    return facts


def _record(case_id, command_id, sequence, event_id, challenge, nonce, argv, child, cwd, env,
            start, end, stdout, stderr):
    return {"case_id": case_id, "command_id": command_id, "sequence": sequence,
            "event_id": event_id, "challenge": challenge, "case_nonce": nonce,
            "argv": list(argv), "popen_args": [str(p) for p in child.args], "cwd": str(cwd),
            "env_path": env.get("PATH", ""),
            "env_git": [[k, v] for k, v in sorted(env.items()) if k.upper().startswith("GIT_")],
            "child_pid": child.pid, "return_code": child.returncode,
            "start_ns": start, "end_ns": end,
            "stdout_base64": base64.b64encode(stdout).decode("ascii"),
            "stderr_base64": base64.b64encode(stderr).decode("ascii"),
            "stdout_sha256": digest(stdout), "stderr_sha256": digest(stderr)}


# --- the single supervised execution path -------------------------------------------

def _report(findings, event_id, supervisor_ok, pid):
    result = findings.result()
    result.update({"event_id": event_id if type(event_id) is str else None,
                   "result_kind": "FRESH_SUPERVISOR_RUN" if supervisor_ok else "IN_PROCESS_NOT_TRUSTED",
                   "supervisor_pid": pid})
    return result


def supervise(event_id, repository, *, ledger_path=None, work_dir=None):
    """Run one supervised event. Returns (result, export or None).

    Takes only non-trust parameters. All PASS-relevant facts are produced here, from
    children launched here; there is no way to pass evidence in.
    """
    findings = Findings()
    _assess_external(findings)
    identity = _process_identity()
    if identity["is_supervisor_process"]:
        supervisor_ok = True
    else:
        supervisor_ok = False
        findings.add("supervisor_process", "unconfirmed",
                     "not running as __main__ of an isolated -I -S -B supervisor process; "
                     "in-process/imported execution is caller-controlled and never PASS-capable")
    if tuple(identity["python_version"][:2]) != FROZEN_PYTHON:
        findings.add("runtime_identity", "blocked", "supervisor Python is not frozen 3.11.x")

    if type(event_id) is not str or not event_id.strip():
        findings.add("event_challenge", "fail", "non-empty event ID required")
        return _report(findings, event_id, supervisor_ok, identity["pid"]), None
    lifecycle = {"EVENT_START": time.monotonic_ns()}
    challenge = secrets.token_hex(32)
    try:
        ledger_file = ledger.resolve_path(ledger_path)
        reservation = ledger.reserve(ledger_file, event_id, challenge)
    except (ledger.LedgerError, OSError) as exc:
        findings.add("event_challenge", "fail", str(exc))
        return _report(findings, event_id, supervisor_ok, identity["pid"]), None
    lifecycle["BINDINGS_RECORDED"] = time.monotonic_ns()

    profile, origin, git, measurements, records = {}, {}, {}, {}, []
    counts = {"launched": 0, "provenance": 0, "argv": 0, "captured": 0, "refusal": 0,
              "module": 0, "runtime": 0, "git": 0}
    executed_cases = []
    config_ok = False
    export = None
    try:
        try:
            profile, origin = configuration()
            if {tuple(c["argv"]) for c in profile["command_inventory"]} != {ARGV_TEMPLATE}:
                findings.add("profile_pinned", "fail", "profile argv template differs from supervisor template")
            else:
                config_ok = True
        except (OSError, ValueError, KeyError) as exc:
            findings.add("profile_pinned", "blocked", str(exc))
        cases = profile.get("required_cases", []) if config_ok else []
        commands = profile.get("command_inventory", []) if config_ok else []
        mandatory = [c["case_id"] for c in cases if c.get("mandatory_execution") is True]
        stage_cm = tempfile.TemporaryDirectory(prefix="inr-local-", dir=work_dir) if config_ok else None
        stage = None
        try:
            if stage_cm is not None:
                stage = Path(stage_cm.__enter__()).resolve()
                try:
                    try:
                        git = probe_git(repository)
                    except (OSError, ValueError, subprocess.SubprocessError) as exc:
                        findings.add("git_runtime", "blocked", str(exc))
                        raise BlockedError("Git runtime not measured") from None
                    lifecycle["ENVIRONMENT_RECORDED"] = time.monotonic_ns()
                    repo = Path(git["repository_root"])
                    executable = Path(git["executable"])
                    if git["head"] != TARGET_SHA:
                        findings.add("target_identity", "blocked", "acquisition repository HEAD is not TARGET_SHA")
                    files = {}
                    try:
                        for name, expected in profile["target_file_digests"].items():
                            path = "docs/portfolio_state/" + name
                            tree = _git(executable, repo, "ls-tree", TARGET_SHA, "--", path)
                            if not tree.startswith((b"100644 blob ", b"100755 blob ")):
                                raise ValueError("target must be a regular Git blob: " + name)
                            raw = _git(executable, repo, "show", TARGET_SHA + ":" + path)
                            if digest(raw) != expected:
                                raise ValueError("pinned source digest mismatch: " + name)
                            files[name] = raw
                        accepted = files["portfolio_state_v0.example.json"]
                        record = json.loads(accepted)
                        required = sorted({s["git_commit"] for s in record["source_records"]}
                                          | {s["git_commit"] for s in record["revision_provenance"]})
                        for revision in required:
                            _git(executable, repo, "cat-file", "-e", revision + "^{commit}")
                    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as exc:
                        findings.add("target_identity", "blocked", str(exc))
                        raise BlockedError("acquisition failed") from None
                    git["required_objects"] = required
                    measurements["distribution_files"] = {k: digest(v) for k, v in files.items()}
                    lifecycle["ACQUISITION_VERIFIED"] = time.monotonic_ns()
                    source = stage / "validate_psm_v0.py"
                    source.write_bytes(files["validate_psm_v0.py"])
                    inputs = {}
                    for case in cases:
                        data = case_bytes(case["case_id"], accepted)
                        if digest(data) != case["input_digest"]:
                            findings.add("module_identity", "blocked", case["case_id"] + ": closed input digest mismatch")
                            raise BlockedError("closed input digest mismatch")
                        path = stage / (case["case_id"] + ".json")
                        path.write_bytes(data)
                        inputs[case["case_id"]] = path
                    lifecycle["FREEZE_START"] = time.monotonic_ns()
                    for path in (source, *inputs.values()):
                        path.chmod(stat.S_IREAD)
                    source_digest = profile["target_file_digests"]["validate_psm_v0.py"]
                    measurements["source_before_sha256"] = digest(source.read_bytes())
                    measurements["probe_sha256"] = digest(PROBE.read_bytes())
                    measurements["python_executable_sha256"] = digest(Path(sys.executable).read_bytes())
                    env = child_environment(executable)
                    # Supervisor-derived values; the expected argv is derived from
                    # ARGV_TEMPLATE, independently of the profile template used to launch.
                    trusted = {"python": str(Path(sys.executable).resolve()), "probe": str(PROBE.resolve()),
                               "source": str(source.resolve()), "repository": str(repo)}
                    lifecycle["COMMAND_EXECUTION_BEGIN"] = time.monotonic_ns()
                    if len(cases) != len(commands):
                        findings.add("mandatory_cases_executed", "fail", "case/command inventory length mismatch")
                    for index, (spec, command) in enumerate(zip(cases, commands), 1):
                        cid = spec["case_id"]
                        if command["case_id"] != cid or command["sequence"] != index:
                            findings.add("mandatory_cases_executed", "fail", f"{cid}: invalid closed command inventory")
                            break
                        values = dict(trusted, input=str(inputs[cid].resolve()))
                        expected_argv = [part.format_map(values) for part in ARGV_TEMPLATE]
                        argv = [str(p) for p in _command_argv(command, values)]
                        nonce = secrets.token_hex(16)
                        case_env = dict(env, INR_EVENT_ID=event_id, INR_RUN_CHALLENGE=challenge,
                                        INR_CASE_ID=cid, INR_CASE_NONCE=nonce)
                        start = time.monotonic_ns()
                        try:
                            child = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                                     stderr=subprocess.PIPE, env=case_env, cwd=str(stage),
                                                     shell=False)
                        except (OSError, ValueError, subprocess.SubprocessError) as exc:
                            findings.add("child_launched", "blocked", f"{cid}: launch failed: {exc}")
                            raise BlockedError("child launch failed") from None
                        if type(child) is not _REAL_POPEN:
                            findings.add("child_launched", "blocked",
                                         f"{cid}: launched child is not a real subprocess.Popen process")
                            raise BlockedError("no real child")
                        try:
                            stdout, stderr = child.communicate(timeout=CHILD_TIMEOUT_SECONDS)
                        except subprocess.TimeoutExpired:
                            child.kill()
                            child.communicate()
                            findings.add("child_launched", "blocked", f"{cid}: target execution timeout")
                            raise BlockedError("timeout") from None
                        end = time.monotonic_ns()
                        pid, rc = child.pid, child.returncode
                        if type(pid) is not int or pid <= 0 or type(rc) is not int or pid == os.getpid():
                            findings.add("child_launched", "blocked", f"{cid}: child process provenance missing")
                            raise BlockedError("child provenance missing")
                        counts["launched"] += 1
                        executed_cases.append(cid)
                        if type(stdout) is not bytes or type(stderr) is not bytes:
                            findings.add("capture_complete", "unconfirmed", f"{cid}: streams not captured as bytes")
                            continue
                        records.append(_record(cid, command["command_id"], index, event_id, challenge, nonce,
                                               argv, child, stage, case_env, start, end, stdout, stderr))
                        # argv / cwd / environment: derived values vs what Popen actually ran
                        popen_args = [str(p) for p in child.args] if isinstance(child.args, (list, tuple)) else None
                        argv_problem = False
                        if argv != expected_argv or popen_args != expected_argv:
                            findings.add("argv_exact", "fail", f"{cid}: executed argv differs from supervisor-derived argv")
                            argv_problem = True
                        if case_env.get("PATH") != str(executable.parent):
                            findings.add("argv_exact", "fail", f"{cid}: child PATH is not the pinned Git directory only")
                            argv_problem = True
                        git_env = sorted((k, v) for k, v in case_env.items() if k.upper().startswith("GIT_"))
                        py_env = sorted((k, v) for k, v in case_env.items() if k.upper().startswith("PYTHON"))
                        if git_env != [("GIT_NO_REPLACE_OBJECTS", "1")] or py_env != [("PYTHONDONTWRITEBYTECODE", "1")]:
                            findings.add("argv_exact", "fail", f"{cid}: child Git/Python environment not exact")
                            argv_problem = True
                        if not argv_problem:
                            counts["argv"] += 1
                        # child report (raw observations; classification is derived here)
                        try:
                            report = json.loads(stdout.decode("ascii"))
                            observed, errors = report["identity"], report["errors"]
                            if type(observed) is not dict or type(report) is not dict:
                                raise ValueError
                        except (KeyError, TypeError, UnicodeError, ValueError):
                            findings.add("capture_complete", "unconfirmed", f"{cid}: child runtime report missing")
                            continue
                        counts["captured"] += 1
                        if (report.get("event_id") != event_id or report.get("challenge") != challenge
                                or report.get("case_id") != cid or report.get("case_nonce") != nonce
                                or not lifecycle["COMMAND_EXECUTION_BEGIN"] <= start <= end):
                            findings.add("child_provenance", "fail", f"{cid}: child output not produced by this launch (replay)")
                        else:
                            counts["provenance"] += 1
                        refusal = list(refusal_problems(spec, errors))
                        if rc not in spec["accepted_return_codes"]:
                            refusal.append(f"{cid}: unexpected return code {rc}")
                        if ((rc == 0) != (errors == [])) or rc not in (0, 2):
                            refusal.append(f"{cid}: return code contradicts child errors")
                        for problem in refusal:
                            findings.add("refusal_semantics", "fail", problem)
                        if not refusal:
                            counts["refusal"] += 1
                        module_problem = False
                        checks = (("source_sha256", source_digest), ("post_source_sha256", source_digest),
                                  ("input_sha256", spec["input_digest"]), ("target_preloaded", False))
                        for key, want in checks:
                            if observed.get(key) != want or type(observed.get(key)) is not type(want):
                                findings.add("module_identity", "fail", f"{cid}: child identity {key} mismatch")
                                module_problem = True
                        if not _same_path(observed.get("source_path"), trusted["source"]):
                            findings.add("module_identity", "fail", f"{cid}: executed source path mismatch")
                            module_problem = True
                        try:
                            if digest(Path(values["input"]).read_bytes()) != spec["input_digest"]:
                                findings.add("module_identity", "fail", f"{cid}: staged input re-measurement mismatch")
                                module_problem = True
                        except OSError as exc:
                            findings.add("module_identity", "unconfirmed", f"{cid}: input re-measurement unavailable: {exc}")
                            module_problem = True
                        if not module_problem:
                            counts["module"] += 1
                        runtime_problem = False
                        for key, want in (("site_loaded", False), ("sitecustomize_loaded", False),
                                          ("usercustomize_loaded", False), ("isolated", 1), ("no_site", 1),
                                          ("dont_write_bytecode", True)):
                            if observed.get(key) != want or type(observed.get(key)) is not type(want):
                                findings.add("runtime_identity", "fail", f"{cid}: child identity {key} mismatch")
                                runtime_problem = True
                        if not _same_path(observed.get("python_executable"), trusted["python"]):
                            findings.add("runtime_identity", "fail", f"{cid}: child interpreter mismatch")
                            runtime_problem = True
                        version = observed.get("python_version")
                        if type(version) is not list or tuple(version[:2]) != FROZEN_PYTHON:
                            findings.add("runtime_identity", "blocked", f"{cid}: child runtime outside frozen Python 3.11.x")
                            runtime_problem = True
                        if not runtime_problem:
                            counts["runtime"] += 1
                        if (_same_path(observed.get("git_which"), git["executable"])
                                and observed.get("git_shadowing") == []
                                and observed.get("git_environment") == [["GIT_NO_REPLACE_OBJECTS", "1"]]):
                            counts["git"] += 1
                        else:
                            findings.add("git_runtime", "fail", f"{cid}: child Git resolution/environment differs from the measured Git")
                    lifecycle["EXECUTION_COMPLETE"] = time.monotonic_ns()
                    measurements["source_after_sha256"] = digest(source.read_bytes())
                    if measurements["source_before_sha256"] != source_digest or measurements["source_after_sha256"] != source_digest:
                        findings.add("module_identity", "fail", "staged source before/after measurement mismatch")
                    if digest(PROBE.read_bytes()) != measurements["probe_sha256"]:
                        findings.add("module_identity", "fail", "trusted probe changed during execution")
                    if digest(Path(sys.executable).read_bytes()) != measurements["python_executable_sha256"]:
                        findings.add("runtime_identity", "fail", "Python runtime changed during execution")
                    try:
                        if digest(executable.read_bytes()) != git["executable_sha256"]:
                            findings.add("git_runtime", "fail", "Git executable changed during the event")
                    except OSError as exc:
                        findings.add("git_runtime", "blocked", str(exc))
                    if any(k.upper().startswith("GIT_") for k in os.environ):
                        findings.add("git_runtime", "blocked", "Git environment influence in supervisor")
                    lifecycle["POST_MEASUREMENT"] = time.monotonic_ns()
                except BlockedError:
                    pass
        finally:
            if stage_cm is not None:
                stage_cm.__exit__(None, None, None)
        lifecycle["CAPTURE_COMPLETE"] = time.monotonic_ns()

        # --- conjunctive establishment (only from the counts of this run) -------------
        n = len(cases)
        if supervisor_ok:
            findings.establish("supervisor_process")
        if config_ok:
            findings.establish("profile_pinned")
        try:
            reserved, completed = ledger.lookup(ledger_file, event_id)
            if (reserved is not None and completed is None and reserved["challenge"] == challenge
                    and reserved["entry_sha256"] == reservation["entry_sha256"]):
                findings.establish("event_challenge")
            else:
                findings.add("event_challenge", "fail", "ledger reservation missing, mismatched or already completed")
        except (ledger.LedgerError, OSError) as exc:
            findings.add("event_challenge", "fail", str(exc))
        if n and git and counts["git"] == n:
            findings.establish("git_runtime")
        if n and git and git.get("head") == TARGET_SHA and measurements.get("distribution_files") == profile.get("target_file_digests"):
            findings.establish("target_identity")
        if n and counts["runtime"] == n:
            findings.establish("runtime_identity")
        if n and counts["launched"] == n:
            findings.establish("child_launched")
        if n and counts["provenance"] == n:
            findings.establish("child_provenance")
        if n and counts["argv"] == n:
            findings.establish("argv_exact")
        complete_lifecycle = all(type(lifecycle.get(k)) is int for k in LIFECYCLE) and all(
            lifecycle[a] <= lifecycle[b] for a, b in zip(LIFECYCLE, LIFECYCLE[1:]))
        if n and counts["captured"] == n and len(records) == n and complete_lifecycle:
            findings.establish("capture_complete")
        if n and mandatory and executed_cases == mandatory == [c["case_id"] for c in cases]:
            findings.establish("mandatory_cases_executed")
        elif n and not findings.has_issue("mandatory_cases_executed"):
            findings.add("mandatory_cases_executed", "unconfirmed",
                         f"executed {len(executed_cases)} of {len(mandatory)} mandatory cases")
        if n and counts["module"] == n:
            findings.establish("module_identity")
        if n and counts["refusal"] == n:
            findings.establish("refusal_semantics")

        result = _report(findings, event_id, supervisor_ok, identity["pid"])
        export = {"schema_version": EVENT_SCHEMA_VERSION, "inr_event_id": event_id,
                  "target_sha": TARGET_SHA,
                  "accepted_target_profile_binding": {
                      "target_profile_id": profile.get("target_profile_id", ""),
                      "target_profile_digest": PROFILE_DIGEST},
                  "accepted_origin_reference_binding": {
                      "origin_reference_set_id": origin.get("origin_reference_set_id", ""),
                      "origin_reference_set_digest": ORIGIN_DIGEST},
                  "challenge": challenge,
                  "ledger_reservation_entry_sha256": reservation["entry_sha256"],
                  "supervisor": {k: identity[k] for k in ("pid", "executable", "python_version", "isolated",
                                                           "no_site", "dont_write_bytecode",
                                                           "is_supervisor_process")},
                  "lifecycle": dict(lifecycle), "git_probe": dict(git),
                  "measurements": dict(measurements), "capture_records": records,
                  "verification": result, "nonclaims": list(NONCLAIMS)}
        ledger.complete(ledger_file, event_id, challenge, {
            "derived_result": result["derived_result"],
            "local_controls_result": result["local_controls_result"],
            "result_kind": result["result_kind"],
            "export_sha256": digest(canonical(export))})
        return result, export
    except BaseException:
        try:
            ledger.complete(ledger_file, event_id, challenge,
                            {"derived_result": "BLOCKED", "local_controls_result": "BLOCKED",
                             "result_kind": "ABORTED", "export_sha256": "0" * 64})
        except (ledger.LedgerError, OSError):
            pass
        raise


def main(argv=None):
    """Supervisor entry. Only non-trust parameters; stdin is never read."""
    parser = argparse.ArgumentParser(prog="supervisor_inr_v0", allow_abbrev=False)
    parser.add_argument("--event-id", required=True)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--ledger", type=Path, default=None)
    parser.add_argument("--work-dir", type=Path, default=None)
    args = parser.parse_args(argv)
    if args.out.exists():
        parser.error("refusing to overwrite an existing event export")
    result, export = supervise(args.event_id, args.repository, ledger_path=args.ledger,
                               work_dir=args.work_dir)
    if export is not None:
        with args.out.open("x", encoding="utf-8", newline="\n") as handle:
            json.dump(export, handle, indent=2, sort_keys=True)
            handle.write("\n")
    print(json.dumps(result, sort_keys=True))
    return 0 if result["pass_allowed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
