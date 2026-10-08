"""INR-001 v0 fused trusted capture + verification (local tooling only).

Trust path (the only path that can produce PASS-capable evidence):

    capture_inr_v0.main
      -> _run_and_verify            (non-exported fused entry)
         -> configuration(), probe_git()       trusted config + measured Git
         -> ledger.reserve()                   persistent single-use event/challenge
         -> _launch()                          spawns the real child itself and mints
                                               the only evidence object type
         -> validate_inr_v0._verify_live()     verifier-owned derivation; consumes
                                               each evidence object exactly once
         -> ledger.complete()                  records the outcome (PASS or not)

There is no module-global writable registry, no token API and no public
``validate(event, token)``. JSON exports/events loaded from disk can only be
re-checked (validate_inr_v0.recheck_export) and never yield PASS.

The supervising Python process, its code, stdlib, OS and the local Git
installation are the declared trust base (no hostile-host resistance in v0).
Non-origin, shared-state absence and all-writer isolation have no verifier-owned
evidence source in v0 and therefore always remain UNCONFIRMED.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
from pathlib import Path
import secrets
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import types
import weakref

from . import ledger
from .input_cases import case_bytes
from .schema_check import check

ROOT = Path(__file__).resolve().parent
TARGET_SHA = "c5e1cfa2fb52874fe9c97e0eade6a120c12cb27b"
PROFILE_DIGEST = "bae309aa9a8f04f64990359d75f1e262945b8bf68149229f1a3023de207dc4ca"
ORIGIN_DIGEST = "8512b8a1954673be69e0ab0c9486935eff07e4d91cecdcec6f0a4b50694c8a03"
DEFAULT_GIT = Path("C:/Program Files/Git/cmd/git.exe" if os.name == "nt" else "/usr/bin/git")
PROBE = ROOT / "runtime_probe.py"
CHILD_TIMEOUT_SECONDS = 300
_REJECTED_GIT_CONFIG_PREFIXES = ("include", "extensions.", "alias.")
_REJECTED_GIT_CONFIG_KEYS = frozenset({"core.worktree", "core.fsmonitor", "core.alternaterefscommand"})


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def _load_json(path):
    return json.loads(Path(path).read_bytes())


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


def _child_environment(git_executable):
    env = {k: v for k, v in os.environ.items()
           if not k.upper().startswith(("PYTHON", "GIT_", "INR_"))}
    env["PATH"] = str(Path(git_executable).parent)
    env["GIT_NO_REPLACE_OBJECTS"] = "1"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


def _capture_argv(command, values):
    """Capture-side argv construction (the verifier derives its own independently)."""
    return [part.format_map(values) for part in command["argv"]]


def _jsonable(value):
    if isinstance(value, bytes):
        return {"b64": base64.b64encode(value).decode("ascii")}
    if isinstance(value, (tuple, list)):
        return [_jsonable(item) for item in value]
    return value


def _launch_factory():
    minted = weakref.WeakKeyDictionary()   # closure-private; only launch() adds
    real_popen = subprocess.Popen          # captured at import

    class _Evidence:
        """Frozen record of one real child execution; cannot be constructed directly."""
        __slots__ = ("_fields", "__weakref__")

        def __init__(self, *args, **kwargs):
            raise TypeError("INR evidence is minted only inside the live launch path")

        def __setattr__(self, name, value):
            raise AttributeError("INR evidence is frozen")

        def __delattr__(self, name):
            raise AttributeError("INR evidence is frozen")

        def __getattr__(self, name):
            try:
                return object.__getattribute__(self, "_fields")[name]
            except KeyError:
                raise AttributeError(name) from None

    def fingerprint(fields):
        return digest(canonical({k: _jsonable(v) for k, v in fields.items()}))

    def launch(argv, *, env, cwd, case_id, command_id, sequence, event_id, challenge):
        argv = tuple(str(part) for part in argv)
        env = dict(env)
        case_nonce = secrets.token_hex(16)
        env.update({"INR_EVENT_ID": event_id, "INR_RUN_CHALLENGE": challenge,
                    "INR_CASE_ID": case_id, "INR_CASE_NONCE": case_nonce})
        start = time.monotonic_ns()
        child = subprocess.Popen(list(argv), stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, env=env, cwd=str(cwd), shell=False)
        if type(child) is not real_popen:
            raise ValueError("launched child is not a real subprocess.Popen process")
        try:
            stdout, stderr = child.communicate(timeout=CHILD_TIMEOUT_SECONDS)
        except subprocess.TimeoutExpired:
            child.kill()
            child.communicate()
            raise ValueError("target execution timeout") from None
        end = time.monotonic_ns()
        pid, rc = child.pid, child.returncode
        if type(pid) is not int or pid <= 0 or type(rc) is not int:
            raise ValueError("child process provenance missing")
        if type(stdout) is not bytes or type(stderr) is not bytes:
            raise ValueError("child streams were not captured as bytes")
        popen_args = tuple(str(part) for part in child.args)
        fields = types.MappingProxyType({
            "case_id": case_id, "command_id": command_id, "sequence": sequence,
            "event_id": event_id, "challenge": challenge, "case_nonce": case_nonce,
            "argv": argv, "popen_args": popen_args, "cwd": str(cwd),
            "env_path": env.get("PATH", ""),
            "env_git": tuple((k, v) for k, v in sorted(env.items()) if k.upper().startswith("GIT_")),
            "env_python": tuple((k, v) for k, v in sorted(env.items()) if k.upper().startswith("PYTHON")),
            "child_pid": pid, "return_code": rc, "start_ns": start, "end_ns": end,
            "stdout": stdout, "stderr": stderr})
        evidence = object.__new__(_Evidence)
        object.__setattr__(evidence, "_fields", fields)
        minted[evidence] = fingerprint(fields)
        return evidence

    def take(evidence):
        """True exactly once for an unmodified evidence object minted by launch()."""
        if type(evidence) is not _Evidence:
            return False
        expected = minted.pop(evidence, None)
        return expected is not None and expected == fingerprint(
            object.__getattribute__(evidence, "_fields"))

    return _Evidence, launch, take


_Evidence, _launch, _take_evidence = _launch_factory()
del _launch_factory


def _export_record(evidence):
    return {"case_id": evidence.case_id, "command_id": evidence.command_id,
            "sequence": evidence.sequence, "event_id": evidence.event_id,
            "challenge": evidence.challenge, "case_nonce": evidence.case_nonce,
            "argv": list(evidence.argv), "popen_args": list(evidence.popen_args),
            "cwd": evidence.cwd, "env_path": evidence.env_path,
            "env_git": [list(item) for item in evidence.env_git],
            "child_pid": evidence.child_pid, "return_code": evidence.return_code,
            "start_ns": evidence.start_ns, "end_ns": evidence.end_ns,
            "stdout_base64": base64.b64encode(evidence.stdout).decode("ascii"),
            "stderr_base64": base64.b64encode(evidence.stderr).decode("ascii"),
            "stdout_sha256": digest(evidence.stdout), "stderr_sha256": digest(evidence.stderr)}


def _execute(session, profile, repository_arg):
    """Measure, stage and launch every frozen command. Raises on blocking conditions."""
    lifecycle = session["lifecycle"]
    git = probe_git(repository_arg)
    session["git"] = git
    lifecycle["ENVIRONMENT_RECORDED"] = time.monotonic_ns()
    repository = Path(git["repository_root"])
    executable = Path(git["executable"])
    files = {}
    for name, expected in profile["target_file_digests"].items():
        path = "docs/portfolio_state/" + name
        tree = _git(executable, repository, "ls-tree", TARGET_SHA, "--", path)
        if not tree.startswith((b"100644 blob ", b"100755 blob ")):
            raise ValueError("target must be a regular Git blob")
        raw = _git(executable, repository, "show", TARGET_SHA + ":" + path)
        if digest(raw) != expected:
            raise ValueError("pinned source digest mismatch")
        files[name] = raw
    accepted = files["portfolio_state_v0.example.json"]
    record = json.loads(accepted)
    required = sorted({s["git_commit"] for s in record["source_records"]}
                      | {s["git_commit"] for s in record["revision_provenance"]})
    for revision in required:
        _git(executable, repository, "cat-file", "-e", revision + "^{commit}")
    session["git"]["required_objects"] = required
    session["measurements"]["distribution_files"] = {k: digest(v) for k, v in files.items()}
    lifecycle["ACQUISITION_VERIFIED"] = time.monotonic_ns()
    stage = session["stage"]
    source = stage / "validate_psm_v0.py"
    source.write_bytes(files["validate_psm_v0.py"])
    inputs = {}
    for case in profile["required_cases"]:
        data = case_bytes(case["case_id"], accepted)
        if digest(data) != case["input_digest"]:
            raise ValueError("closed input digest mismatch")
        path = stage / (case["case_id"] + ".json")
        path.write_bytes(data)
        inputs[case["case_id"]] = path
    lifecycle["FREEZE_START"] = time.monotonic_ns()
    for path in (source, *inputs.values()):
        path.chmod(stat.S_IREAD)
    session["measurements"]["source_before_sha256"] = digest(source.read_bytes())
    session["measurements"]["probe_sha256"] = digest(PROBE.read_bytes())
    session["measurements"]["python_executable_sha256"] = digest(Path(sys.executable).read_bytes())
    env = _child_environment(executable)
    values = {"python": str(Path(sys.executable).resolve()), "probe": str(PROBE.resolve()),
              "source": str(source.resolve()), "repository": str(repository)}
    lifecycle["COMMAND_EXECUTION_BEGIN"] = time.monotonic_ns()
    for index, (case, command) in enumerate(zip(profile["required_cases"],
                                               profile["command_inventory"], strict=True), 1):
        if command["case_id"] != case["case_id"] or command["sequence"] != index:
            raise ValueError("invalid closed command inventory")
        values["input"] = str(inputs[case["case_id"]].resolve())
        session["evidence"].append(_launch(
            _capture_argv(command, values), env=env, cwd=stage, case_id=case["case_id"],
            command_id=command["command_id"], sequence=index,
            event_id=session["event_id"], challenge=session["challenge"]))
    lifecycle["EXECUTION_COMPLETE"] = time.monotonic_ns()
    session["measurements"]["source_after_sha256"] = digest(source.read_bytes())
    if digest(PROBE.read_bytes()) != session["measurements"]["probe_sha256"]:
        session["failure_reasons"].append("trusted probe changed during execution")
    if digest(Path(sys.executable).read_bytes()) != session["measurements"]["python_executable_sha256"]:
        session["failure_reasons"].append("Python runtime changed during execution")
    lifecycle["POST_MEASUREMENT"] = time.monotonic_ns()


def _build_export(session, profile, origin, result):
    return {"schema_version": "inr.event.v0.r2", "inr_event_id": session["event_id"],
            "target_sha": TARGET_SHA,
            "accepted_target_profile_binding": {
                "target_profile_id": profile.get("target_profile_id", ""),
                "target_profile_digest": PROFILE_DIGEST},
            "accepted_origin_reference_binding": {
                "origin_reference_set_id": origin.get("origin_reference_set_id", ""),
                "origin_reference_set_digest": ORIGIN_DIGEST},
            "challenge": session["challenge"],
            "ledger_reservation_entry_sha256": session["ledger_reservation_entry_sha256"],
            "lifecycle": dict(session["lifecycle"]), "git_probe": dict(session["git"]),
            "measurements": dict(session["measurements"]),
            "capture_records": [_export_record(e) for e in session["evidence"]
                                if type(e) is _Evidence],
            "blocked_reasons": list(session["blocked_reasons"]),
            "failure_reasons": list(session["failure_reasons"]),
            "verification": result,
            "nonclaims": ["local INR tooling run only", "not a non-origin reconstruction",
                          "not independent reproduction", "not IW admission",
                          "not Human Final", "not production permission"]}


def _run_and_verify(repository, event_id, *, ledger_path=None, work_dir=None):
    """Fused capture + verification. Returns (result, export or None)."""
    from . import validate_inr_v0 as verifier

    if type(event_id) is not str or not event_id.strip():
        raise ValueError("non-empty event ID required")
    ledger_file = ledger.resolve_path(ledger_path)
    lifecycle = {"EVENT_START": time.monotonic_ns()}
    challenge = secrets.token_hex(32)
    try:
        reservation = ledger.reserve(ledger_file, event_id, challenge)
    except ledger.LedgerError as exc:
        return verifier._rejected_result(str(exc)), None
    lifecycle["BINDINGS_RECORDED"] = time.monotonic_ns()
    session = {"event_id": event_id, "challenge": challenge, "ledger_path": str(ledger_file),
               "ledger_reservation_entry_sha256": reservation["entry_sha256"],
               "lifecycle": lifecycle, "git": {}, "measurements": {}, "evidence": [],
               "blocked_reasons": [], "failure_reasons": [], "stage": None}
    profile, origin, result = {}, {}, None
    try:
        try:
            profile, origin = configuration()
            with tempfile.TemporaryDirectory(prefix="inr-local-", dir=work_dir) as directory:
                session["stage"] = Path(directory).resolve()
                try:
                    _execute(session, profile, repository)
                except (OSError, ValueError, KeyError, subprocess.SubprocessError) as exc:
                    session["blocked_reasons"].append(str(exc))
                lifecycle["CAPTURE_COMPLETE"] = time.monotonic_ns()
                lifecycle["EVENT_COMPLETE"] = time.monotonic_ns()
                # Verify while the staged bytes still exist so the verifier can re-measure.
                result = verifier._verify_live(session)
        except (OSError, ValueError, KeyError) as exc:
            session["blocked_reasons"].append(str(exc))
            result = verifier._verify_live(session)
        export = _build_export(session, profile, origin, result)
        ledger.complete(ledger_file, event_id, challenge, {
            "derived_result": result["derived_result"],
            "local_controls_result": result["local_controls_result"],
            "export_sha256": digest(canonical(export))})
        return result, export
    except BaseException:
        # Record the non-PASS attempt; complete() refuses if it was already recorded.
        try:
            ledger.complete(ledger_file, event_id, challenge,
                            {"derived_result": "BLOCKED", "local_controls_result": "BLOCKED",
                             "export_sha256": "0" * 64})
        except ledger.LedgerError:
            pass
        raise
