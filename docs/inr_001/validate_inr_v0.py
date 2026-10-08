"""Fail-closed INR-001 v0 verifier.

* ``_verify_live(session)`` is the verifier half of the fused path in
  trusted_capture._run_and_verify. It derives every PASS-relevant fact itself
  (trusted configuration, re-measurement, independently derived argv, exact
  refusal messages) and accepts child evidence only as evidence objects minted by
  trusted_capture._launch, each consumable exactly once.
* ``recheck_export(export)`` re-checks a JSON export loaded from disk (schema and
  ledger consistency). It can never return PASS: disk data is not live evidence.
* Non-origin, shared-state absence and all-writer isolation are verifier-owned and
  take no input at all; v0 has no objective evidence source for them, so they are
  always UNCONFIRMED and the overall INR result can never be PASS in v0.
"""
from __future__ import annotations

import base64
import json
import os
from pathlib import Path
import sys

from . import ledger
from . import trusted_capture as producer
from .schema_check import check

TARGET_SHA = producer.TARGET_SHA
ROOT = Path(__file__).resolve().parent
RESULTS = ("PASS", "FAIL", "UNCONFIRMED", "BLOCKED")
LIFECYCLE = ("EVENT_START", "BINDINGS_RECORDED", "ENVIRONMENT_RECORDED",
             "ACQUISITION_VERIFIED", "FREEZE_START", "COMMAND_EXECUTION_BEGIN",
             "EXECUTION_COMPLETE", "POST_MEASUREMENT", "CAPTURE_COMPLETE", "EVENT_COMPLETE")
# Verifier-owned argv template; the profile template must equal it, and the actual
# Popen argv must equal this template formatted with verifier-derived values.
ARGV_TEMPLATE = ("{python}", "-I", "-S", "-B", "{probe}", "{source}", "{input}", "{repository}")
LOCAL_COMPONENTS = ("trusted_configuration", "challenge_ledger", "git_runtime", "acquisition",
                    "python_policy", "child_execution_binding", "argv_binding",
                    "module_identity", "refusal_semantics")
EXTERNAL_COMPONENTS = ("non_origin", "shared_state_absence", "all_writer_isolation")
NONCLAIMS = ("not a non-origin reconstruction", "not independent reproduction",
             "not IW admission", "not Human Final", "not production permission")


def load_schema():
    return json.loads((ROOT / "schema/inr_event_v0.schema.json").read_bytes())


def _precedence(blocked, fail, unconfirmed):
    return "BLOCKED" if blocked else "FAIL" if fail else "UNCONFIRMED" if unconfirmed else "PASS"


# --- verifier-owned external assurance (no inputs, by construction) ------------

def _assess_non_origin():
    return "UNCONFIRMED", "non-origin: no verifier-owned objective non-origin evidence source in v0"


def _assess_shared_state_absence():
    return "UNCONFIRMED", "shared state: no verifier-owned evidence that no shared writable origin state exists"


def _assess_all_writer_isolation():
    return "UNCONFIRMED", "isolation: read-only staging does not establish all-writer immutability"


class _Findings:
    def __init__(self):
        self.items = {name: {"blocked": [], "fail": [], "unconfirmed": []}
                      for name in LOCAL_COMPONENTS + EXTERNAL_COMPONENTS}

    def add(self, component, level, message):
        self.items[component][level].append(f"{component}: {message}")

    def status(self, component):
        f = self.items[component]
        return _precedence(f["blocked"], f["fail"], f["unconfirmed"])

    def result(self, schema_version="inr.verifier.result.v0.r2"):
        collect = lambda names, level: [m for n in names for m in self.items[n][level]]
        names = LOCAL_COMPONENTS + EXTERNAL_COMPONENTS
        blocked, fail, unconfirmed = (collect(names, lvl) for lvl in ("blocked", "fail", "unconfirmed"))
        derived = _precedence(blocked, fail, unconfirmed)
        local = _precedence(*(collect(LOCAL_COMPONENTS, lvl) for lvl in ("blocked", "fail", "unconfirmed")))
        return {"schema_version": schema_version, "derived_result": derived,
                "pass_allowed": derived == "PASS", "local_controls_result": local,
                "components": {n: self.status(n) for n in names},
                "blocked": blocked, "fail": fail, "unconfirmed": unconfirmed,
                "nonclaims": list(NONCLAIMS)}


def _external(findings):
    for component, assess in (("non_origin", _assess_non_origin),
                              ("shared_state_absence", _assess_shared_state_absence),
                              ("all_writer_isolation", _assess_all_writer_isolation)):
        status, message = assess()
        if status != "PASS":
            findings.add(component, "unconfirmed", message)


def _rejected_result(reason):
    findings = _Findings()
    findings.add("challenge_ledger", "fail", reason)
    for name in LOCAL_COMPONENTS:
        if name != "challenge_ledger":
            findings.add(name, "unconfirmed", "not executed: event rejected before execution")
    _external(findings)
    return findings.result()


def _sha(path):
    return producer.digest(Path(path).read_bytes())


def _same_path(a, b):
    return a is not None and b is not None and os.path.normcase(os.path.abspath(a)) == os.path.normcase(os.path.abspath(b))


def _refusal_findings(spec, errors):
    """Exact refusal semantics: the child's error list must equal the frozen list."""
    problems = []
    if type(errors) is not list or any(type(e) is not str for e in errors):
        return ["child error list missing/malformed"]
    derived = "PASS" if not errors else "FAIL"
    if derived != spec["expected_classification"]:
        problems.append(f"{spec['case_id']}: derived classification {derived} != {spec['expected_classification']}")
    if errors != spec["expected_errors"]:
        problems.append(f"{spec['case_id']}: refusal reason differs from the frozen intended refusal")
    return problems


def _verify_live(session):
    findings = _Findings()
    _external(findings)
    # 1. trusted configuration (verifier loads it itself; session copies are ignored)
    try:
        profile, origin = producer.configuration()
    except (OSError, ValueError) as exc:
        findings.add("trusted_configuration", "blocked", str(exc))
        return findings.result()
    templates = {tuple(c["argv"]) for c in profile["command_inventory"]}
    if templates != {ARGV_TEMPLATE}:
        findings.add("trusted_configuration", "fail", "profile argv template differs from verifier template")
    lifecycle = session.get("lifecycle", {})
    # 2. ledger: reservation must exist, belong to this challenge and still be open
    try:
        reserved, completed = ledger.lookup(ledger.resolve_path(session.get("ledger_path")),
                                            session.get("event_id"))
    except (ledger.LedgerError, OSError, TypeError) as exc:
        reserved, completed = None, None
        findings.add("challenge_ledger", "fail", str(exc))
    if (reserved is None or reserved["challenge"] != session.get("challenge")
            or reserved["entry_sha256"] != session.get("ledger_reservation_entry_sha256")):
        findings.add("challenge_ledger", "fail", "no matching ledger reservation for event/challenge")
    if completed is not None:
        findings.add("challenge_ledger", "fail", "event already completed; verification replay refused")
    for reason in session.get("blocked_reasons", []):
        findings.add("acquisition", "blocked", "capture blocked: " + reason)
    for reason in session.get("failure_reasons", []):
        findings.add("module_identity", "fail", "capture measured: " + reason)
    # 3. Git runtime: re-measure the pinned executable
    git = session.get("git") or {}
    if not git:
        findings.add("git_runtime", "blocked", "Git runtime not measured")
    else:
        try:
            pinned = producer.DEFAULT_GIT.resolve(strict=True)
            if not _same_path(git.get("executable"), str(pinned)) or _sha(pinned) != git.get("executable_sha256"):
                findings.add("git_runtime", "fail", "Git executable differs from measured pinned Git")
        except OSError as exc:
            findings.add("git_runtime", "blocked", str(exc))
        if any(k.upper().startswith("GIT_") for k in os.environ):
            findings.add("git_runtime", "blocked", "Git environment influence in verifier")
        # 4. acquisition
        if git.get("head") != TARGET_SHA:
            findings.add("acquisition", "blocked", "acquisition repository HEAD is not TARGET_SHA")
    if session.get("measurements", {}).get("distribution_files") != profile["target_file_digests"]:
        findings.add("acquisition", "unconfirmed", "distribution file digests not established")
    # 5. Python policy (supervisor + every child)
    if sys.version_info[:2] != (3, 11):
        findings.add("python_policy", "blocked", "supervisor Python is not frozen 3.11.x")
    # lifecycle ordering
    if any(type(lifecycle.get(k)) is not int for k in LIFECYCLE):
        findings.add("child_execution_binding", "unconfirmed", "incomplete lifecycle")
    elif any(lifecycle[a] > lifecycle[b] for a, b in zip(LIFECYCLE, LIFECYCLE[1:])):
        findings.add("child_execution_binding", "fail", "reversed lifecycle")
    # 6. verifier-derived trusted values
    stage = session.get("stage")
    source_digest = profile["target_file_digests"]["validate_psm_v0.py"]
    trusted = None
    if stage is None or not git:
        findings.add("argv_binding", "unconfirmed", "no staged execution to bind")
    else:
        stage = Path(stage)
        trusted = {"python": str(Path(sys.executable).resolve()), "probe": str((ROOT / "runtime_probe.py").resolve()),
                   "source": str((stage / "validate_psm_v0.py").resolve()), "repository": str(Path(git["repository_root"]))}
        try:
            if _sha(trusted["source"]) != source_digest:
                findings.add("module_identity", "fail", "staged source re-measurement mismatch")
            if _sha(trusted["probe"]) != session.get("measurements", {}).get("probe_sha256"):
                findings.add("module_identity", "fail", "probe re-measurement mismatch")
        except OSError as exc:
            findings.add("module_identity", "unconfirmed", "re-measurement unavailable: " + str(exc))
    for key in ("source_before_sha256", "source_after_sha256"):
        if session.get("measurements", {}).get(key) != source_digest:
            findings.add("module_identity", "unconfirmed", key + " not established")
    # 7. per-case child evidence
    evidence = list(session.get("evidence", []))
    cases, commands = profile["required_cases"], profile["command_inventory"]
    if len(evidence) != len(cases):
        findings.add("child_execution_binding", "unconfirmed", "incomplete/extraneous child evidence set")
    for index, item in enumerate(evidence):
        if not producer._take_evidence(item):
            findings.add("child_execution_binding", "unconfirmed",
                         f"record {index + 1}: evidence not minted by the live launch path or already consumed")
            continue
        if index >= len(cases):
            findings.add("child_execution_binding", "fail", "unknown/extra child execution")
            continue
        spec, command = cases[index], commands[index]
        cid = spec["case_id"]
        if (item.case_id != cid or command["case_id"] != cid or item.command_id != command["command_id"]
                or item.sequence != command["sequence"] or item.sequence != index + 1):
            findings.add("child_execution_binding", "fail", f"{cid}: case/command/order mismatch")
        if item.event_id != session.get("event_id") or item.challenge != session.get("challenge"):
            findings.add("child_execution_binding", "fail", f"{cid}: launch not bound to current event/challenge")
        begin, done = lifecycle.get("COMMAND_EXECUTION_BEGIN"), lifecycle.get("EXECUTION_COMPLETE")
        if type(begin) is not int or type(done) is not int or not begin <= item.start_ns <= item.end_ns <= done:
            findings.add("child_execution_binding", "fail", f"{cid}: execution outside current event window")
        if item.return_code not in spec["accepted_return_codes"]:
            findings.add("refusal_semantics", "fail", f"{cid}: unexpected return code {item.return_code}")
        # argv: verifier-derived expectation vs the argv actually passed to Popen
        if trusted is not None:
            values = dict(trusted, input=str((stage / (cid + ".json")).resolve()))
            expected = tuple(part.format_map(values) for part in ARGV_TEMPLATE)
            if tuple(item.argv) != expected or tuple(item.popen_args) != expected:
                findings.add("argv_binding", "fail", f"{cid}: executed argv differs from verifier-derived argv")
            if not _same_path(item.cwd, str(stage)):
                findings.add("argv_binding", "fail", f"{cid}: child cwd is not the staging directory")
            if not _same_path(item.env_path, str(Path(git["executable"]).parent)):
                findings.add("argv_binding", "fail", f"{cid}: child PATH is not the pinned Git directory only")
            if tuple(item.env_git) != (("GIT_NO_REPLACE_OBJECTS", "1"),):
                findings.add("argv_binding", "fail", f"{cid}: child Git environment not exactly GIT_NO_REPLACE_OBJECTS=1")
            if tuple(item.env_python) != (("PYTHONDONTWRITEBYTECODE", "1"),):
                findings.add("argv_binding", "fail", f"{cid}: child Python environment not exactly PYTHONDONTWRITEBYTECODE=1")
            try:
                if _sha(values["input"]) != spec["input_digest"]:
                    findings.add("module_identity", "fail", f"{cid}: staged input re-measurement mismatch")
            except OSError as exc:
                findings.add("module_identity", "unconfirmed", f"{cid}: input re-measurement unavailable: {exc}")
        # child report
        try:
            report = json.loads(item.stdout.decode("ascii"))
            identity, errors = report["identity"], report["errors"]
            if type(identity) is not dict:
                raise ValueError
        except (KeyError, TypeError, UnicodeError, ValueError):
            findings.add("child_execution_binding", "unconfirmed", f"{cid}: child runtime report missing")
            continue
        if (report.get("event_id") != session.get("event_id") or report.get("challenge") != session.get("challenge")
                or report.get("case_id") != cid or report.get("case_nonce") != item.case_nonce):
            findings.add("child_execution_binding", "fail", f"{cid}: child output not produced by this launch (replay)")
        if ((item.return_code == 0) != (errors == [])) or item.return_code not in (0, 2):
            findings.add("refusal_semantics", "fail", f"{cid}: return code contradicts child errors")
        for problem in _refusal_findings(spec, errors):
            findings.add("refusal_semantics", "fail", problem)
        checks = (
            ("source_sha256", source_digest), ("post_source_sha256", source_digest),
            ("input_sha256", spec["input_digest"]), ("target_preloaded", False),
            ("site_loaded", False), ("sitecustomize_loaded", False), ("usercustomize_loaded", False),
            ("isolated", 1), ("no_site", 1), ("dont_write_bytecode", True),
            ("git_shadowing", []), ("git_environment", [["GIT_NO_REPLACE_OBJECTS", "1"]]))
        for key, want in checks:
            if identity.get(key) != want or type(identity.get(key)) is not type(want):
                findings.add("module_identity", "fail", f"{cid}: child identity {key} mismatch")
        if trusted is not None:
            if not _same_path(identity.get("source_path"), trusted["source"]):
                findings.add("module_identity", "fail", f"{cid}: executed source path mismatch")
            if not _same_path(identity.get("python_executable"), trusted["python"]):
                findings.add("module_identity", "fail", f"{cid}: child interpreter mismatch")
            if not _same_path(identity.get("git_which"), git.get("executable")):
                findings.add("git_runtime", "fail", f"{cid}: child resolves a Git other than the measured one")
        version = identity.get("python_version")
        if type(version) is not list or version[:2] != [3, 11]:
            findings.add("python_policy", "blocked", f"{cid}: child runtime outside frozen Python 3.11.x")
    return findings.result()


def recheck_export(export, *, ledger_path=None):
    """Re-check a disk export. Never PASS: disk data is not live trusted evidence."""
    fail, blocked = [], []
    unconfirmed = ["recheck: a JSON export is not live trusted evidence and can never yield PASS"]
    problems = check(export, load_schema())
    if problems:
        fail.extend("schema: " + p for p in problems)
    else:
        try:
            reserved, completed = ledger.lookup(ledger.resolve_path(ledger_path), export["inr_event_id"])
        except (ledger.LedgerError, OSError) as exc:
            reserved, completed = None, None
            fail.append("ledger: " + str(exc))
        if (reserved is None or completed is None
                or reserved["challenge"] != export["challenge"]
                or completed["challenge"] != export["challenge"]
                or reserved["entry_sha256"] != export["ledger_reservation_entry_sha256"]
                or completed["detail"].get("export_sha256") != producer.digest(producer.canonical(export))):
            fail.append("ledger: export not recorded in the ledger or altered after capture")
        else:
            recorded = completed["detail"].get("derived_result")
            if recorded == "BLOCKED":
                blocked.append("ledger: recorded live result was BLOCKED")
            elif recorded == "FAIL":
                fail.append("ledger: recorded live result was FAIL")
        for record in export["capture_records"]:
            for stream in ("stdout", "stderr"):
                try:
                    raw = base64.b64decode(record[stream + "_base64"], validate=True)
                except ValueError:
                    fail.append("recheck: invalid stream encoding")
                    continue
                if producer.digest(raw) != record[stream + "_sha256"]:
                    fail.append("recheck: stream changed after capture")
    derived = _precedence(blocked, fail, unconfirmed)
    return {"schema_version": "inr.verifier.recheck.v0.r2", "derived_result": derived,
            "pass_allowed": False, "blocked": blocked, "fail": fail, "unconfirmed": unconfirmed,
            "nonclaims": list(NONCLAIMS)}


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    ledger_path = None
    if len(args) == 3 and args[1] == "--ledger":
        ledger_path = args[2]
    elif len(args) != 1:
        print("usage: python -m docs.inr_001.validate_inr_v0 EXPORT.json [--ledger PATH]", file=sys.stderr)
        return 2
    try:
        export = json.loads(Path(args[0]).read_bytes())
        result = recheck_export(export, ledger_path=ledger_path)
    except (OSError, UnicodeError, ValueError) as exc:
        result = {"schema_version": "inr.verifier.recheck.v0.r2", "derived_result": "FAIL",
                  "pass_allowed": False, "blocked": [], "fail": [str(exc)], "unconfirmed": [],
                  "nonclaims": list(NONCLAIMS)}
    print(json.dumps(result, sort_keys=True, indent=2))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
