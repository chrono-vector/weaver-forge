"""INR-XR-001 v0 trusted XR verifier PROCESS: the one-way integration point into INR.

Intended invocation (normally through ``launch``, or directly by an operator):

    python -I -S -B <worktree>/docs/inr_001/xr/xr_verifier_v0.py --bundle DIR \
        --event-id ID --not-before UTC --expected-head-sha SHA

The trust boundary is this PROCESS, exactly as for ``supervisor_inr_v0`` (Python
privacy, immutability, closures or capability objects are NOT the boundary). Every
argument is a non-trust parameter: a bundle location and operator parameters. The
verifier accepts no XR result, adapter result, assurance object or external
predicate from argv, stdin (never read), environment or files. The GitHub token
in ``INR_XR_GITHUB_TOKEN`` is a credential, not evidence.

Inside one execution path (``verify_external_event``) it does the following:

1. Runs the XR structural validation and evidence derivation on the bundle.
2. Runs the GitHub Actions provider verification and the bundle-to-run binding,
   always through ``GitHubProvider.from_environment()`` when started as a process.
   No mock or offline switch exists.
3. Derives the INR-001 predicates for the EXTERNAL event with the accepted
   ``supervisor_inr_v0.Findings`` semantics:
   * the external predicates (``non_origin``, ``shared_state_absence``,
     ``all_writer_isolation``) come only from provider-verified XR assurance
     predicates;
   * each local predicate needs both the provider-bound supervisor report and the
     XR re-derivation.

The predicates are established only when this code runs as ``__main__`` of an
isolated (-I -S -B) interpreter started on this file. An in-process caller controls
its own interpreter and its own objects, so whatever it computes is caller-controlled:
``result_kind`` becomes IN_PROCESS_NOT_TRUSTED and every INR predicate stays
UNCONFIRMED. ``launch`` relays the report only when it is bound to the process it
started (pid, event ID, exit status, result kind).

The accepted INR-001 local tooling is not modified. A local supervisor run still
reports its own (origin) environment's external predicates as UNCONFIRMED. This
verifier classifies the external event described by a provider-bound bundle.
"""
from __future__ import annotations

import os
import sys

if __name__ == "__main__":
    sys.pycache_prefix = os.devnull

import argparse  # noqa: E402
import json  # noqa: E402
from pathlib import Path  # noqa: E402
import re  # noqa: E402
import subprocess  # noqa: E402

if __name__ == "__main__":  # -I does not put the script directory on sys.path
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from docs.inr_001 import supervisor_inr_v0 as sup  # noqa: E402
from docs.inr_001.xr import provider_github_v0 as provider_github  # noqa: E402
from docs.inr_001.xr import validate_external_run_v0 as xr  # noqa: E402

VERIFIER = Path(__file__).resolve()
INTERPRETER_FLAGS = ("-I", "-S", "-B")
VERIFIER_TIMEOUT_SECONDS = 600
REPORT_SCHEMA_VERSION = "inr.xr.verifier.result.v0"
TRUSTED_KIND = "XR_VERIFIER_PROCESS"
UNTRUSTED_KIND = "IN_PROCESS_NOT_TRUSTED"
_HEX64 = re.compile(r"[0-9a-f]{64}")

# INR predicate <- XR assurance predicates (all must be PASS). Local predicates also
# require the provider-bound supervisor report to show PASS for the same name.
INR_EXTERNAL_SOURCES = {
    "non_origin": ("runner_identity_established", "fresh_hosted_runner_established",
                   "fresh_workspace_established", "independent_acquisition_established"),
    "shared_state_absence": ("no_shared_mutable_state_established",),
    "all_writer_isolation": ("all_writer_isolation_established",),
}
INR_LOCAL_SOURCES = {name: ("current_event_capture_established",) for name in sup.LOCAL_PREDICATES}
INR_LOCAL_SOURCES.update({"git_runtime": ("git_identity_established", "current_event_capture_established"),
                          "target_identity": ("independent_acquisition_established",
                                              "current_event_capture_established"),
                          "runtime_identity": ("python_311_established", "current_event_capture_established")})
NONCLAIMS = ("XR verifier result for one external event bundle",
             "provider trust rests on GitHub Actions and the reviewed workflow at the expected head SHA",
             "no hostile-host resistance", "not IW admission", "not Human Final", "not production permission")


def _same_path(a, b):
    return (type(a) is str and type(b) is str
            and os.path.normcase(os.path.abspath(a)) == os.path.normcase(os.path.abspath(b)))


def _process_identity():
    """Observed facts about this interpreter (defence in depth, not the boundary)."""
    main = sys.modules.get("__main__")
    main_file = getattr(main, "__file__", None)
    argv0 = sys.argv[0] if sys.argv else ""
    trusted = (sys.flags.isolated == 1 and sys.flags.no_site == 1 and bool(sys.dont_write_bytecode)
               and _same_path(argv0, str(VERIFIER)) and _same_path(main_file, str(VERIFIER))
               and __name__ == "__main__" and "site" not in sys.modules)
    return {"pid": os.getpid(), "is_verifier_process": trusted}


def _issue_level(assessment):
    status = assessment.get("external_assurance")
    return {"FAIL": "fail", "BLOCKED": "blocked"}.get(status, "unconfirmed")


def derive_inr_predicates(findings, assessment, *, event_id, process_trusted):
    """Map the XR assessment computed IN THIS VERIFIER CALL onto INR predicates.

    Only ``verify_external_event`` feeds this with the assessment it has just
    computed. An in-process call (``process_trusted`` False) establishes nothing.
    No JSON, file or argv value reaches this function in the verifier process.
    """
    names = sup.REQUIRED_PREDICATES
    if not process_trusted:
        for name in names:
            findings.add(name, "unconfirmed", "not the isolated XR verifier process: in-process results are "
                                              "caller-controlled and never establish INR predicates")
        return
    bound = assessment.get("bound_event") if type(assessment.get("bound_event")) is dict else {}
    run = assessment.get("provider_run") if type(assessment.get("provider_run")) is dict else {}
    digest = assessment.get("bundle_digest")
    level = _issue_level(assessment)
    problems = []
    for ok, message in (
            (assessment.get("structural_bundle") == "PASS", "XR structural bundle not PASS"),
            (assessment.get("provider_provenance") == "PASS", "XR result not provider-authenticated"),
            (assessment.get("bundle_run_binding") == "PASS", "bundle not bound to the verified provider run"),
            (assessment.get("external_assurance") == "PASS", "XR external assurance not PASS")):
        if not ok:
            problems.append((level, message))
    # A value that is absent is not established (assessment level); a value that is present
    # and differs, or is absent although its gate claims PASS, is a FAIL.
    for value, want, message in (
            (bound.get("inr_event_id"), event_id, "XR event ID differs from the INR event ID"),
            (bound.get("target_sha"), sup.TARGET_SHA, "XR target SHA differs from TARGET_SHA"),
            (bound.get("target_profile_digest"), sup.PROFILE_DIGEST, "XR profile digest differs from the pin"),
            (bound.get("origin_reference_set_digest"), sup.ORIGIN_DIGEST,
             "XR origin reference digest differs from the pin")):
        if value is None:
            problems.append((level, message.replace("differs from", "not bound to")))
        elif value != want:
            problems.append(("fail", message))
    if type(digest) is not str or _HEX64.fullmatch(digest) is None:
        problems.append(("fail" if assessment.get("structural_bundle") == "PASS" else level, "bundle digest missing"))
    if run.get("artifact_name") != provider_github.ARTIFACT_PREFIX + str(digest) or type(run.get("run_id")) is not int:
        problems.append(("fail" if assessment.get("bundle_run_binding") == "PASS" else level,
                         "provider run identity missing or not bound to the bundle digest"))
    if problems:
        for name in names:
            for issue_level, message in problems:
                findings.add(name, issue_level, message)
        return
    assurance = assessment["assurance_predicates"]
    reported = assessment.get("supervisor_report_predicates") or {}
    for name, sources in {**INR_LOCAL_SOURCES, **INR_EXTERNAL_SOURCES}.items():
        statuses = [assurance.get(source) for source in sources]
        if name in INR_LOCAL_SOURCES:
            statuses.append(reported.get(name))
        combined = xr.combine(statuses)
        if combined == "PASS":
            findings.establish(name)
        else:
            findings.add(name, {"FAIL": "fail", "BLOCKED": "blocked"}.get(combined, "unconfirmed"),
                         "XR/provider sources not all PASS: " + ", ".join(sources))


def verify_external_event(bundle, event_id, not_before, expected_head_sha, provider):
    """The single verifier execution path. Returns the report dict."""
    identity = _process_identity()
    findings = sup.Findings()
    assessment = xr.validate_bundle(bundle, expected_event_id=event_id, not_before=not_before,
                                    expected_head_sha=expected_head_sha, provider=provider)
    derive_inr_predicates(findings, assessment, event_id=event_id, process_trusted=identity["is_verifier_process"])
    report = findings.result()
    report.update({"schema_version": REPORT_SCHEMA_VERSION,
                   "result_kind": TRUSTED_KIND if identity["is_verifier_process"] else UNTRUSTED_KIND,
                   "event_id": event_id, "verifier_pid": identity["pid"],
                   "bundle_digest": assessment.get("bundle_digest", ""),
                   "provider_run": assessment.get("provider_run"),
                   "xr": {key: assessment.get(key) for key in ("structural_bundle", "provider_provenance",
                                                                "bundle_run_binding", "external_assurance")},
                   "nonclaims": list(NONCLAIMS)})
    return report


def verifier_command(bundle, event_id, not_before, expected_head_sha):
    return [str(Path(sys.executable).resolve()), *INTERPRETER_FLAGS, str(VERIFIER),
            "--bundle", str(Path(bundle).resolve()), "--event-id", str(event_id),
            "--not-before", str(not_before), "--expected-head-sha", str(expected_head_sha)]


def _binding_failure(event_id, reason, returncode=None):
    return {"schema_version": REPORT_SCHEMA_VERSION, "result_kind": "LAUNCHER_BINDING_FAILURE",
            "derived_result": "UNCONFIRMED", "pass_allowed": False, "event_id": event_id,
            "unconfirmed": ["launcher: " + reason], "verifier_returncode": returncode}


def accept_report(report, *, child_pid, returncode, event_id):
    """Launcher-side binding: the report must come from the process this launcher started."""
    if type(report) is not dict:
        return _binding_failure(event_id, "verifier produced no report", returncode)
    if report.get("verifier_pid") != child_pid or report.get("event_id") != event_id:
        return _binding_failure(event_id, "report is not bound to the launched verifier process", returncode)
    if report.get("result_kind") != TRUSTED_KIND:
        return _binding_failure(event_id, "launched verifier did not run as the isolated verifier process",
                                returncode)
    if bool(report.get("pass_allowed")) != (returncode == 0):
        return _binding_failure(event_id, "verifier exit status contradicts its report", returncode)
    return report


def launch(bundle, event_id, not_before, expected_head_sha):
    """Start the verifier process and relay its report only if bound to that process."""
    child = subprocess.Popen(verifier_command(bundle, event_id, not_before, expected_head_sha),
                             stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             env=dict(os.environ), shell=False)
    try:
        stdout, _stderr = child.communicate(timeout=VERIFIER_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired:
        child.kill()
        child.communicate()
        return _binding_failure(event_id, "verifier timeout")
    try:
        report = json.loads(stdout.decode("utf-8").strip().splitlines()[-1])
    except (IndexError, UnicodeError, ValueError):
        report = None
    return accept_report(report, child_pid=child.pid, returncode=child.returncode, event_id=event_id)


def main(argv=None):
    parser = argparse.ArgumentParser(prog="xr_verifier_v0", allow_abbrev=False)
    parser.add_argument("--bundle", required=True, type=Path)
    parser.add_argument("--event-id", required=True)
    parser.add_argument("--not-before", required=True)
    parser.add_argument("--expected-head-sha", required=True)
    args = parser.parse_args(argv)
    report = verify_external_event(args.bundle, args.event_id, args.not_before, args.expected_head_sha,
                                   provider_github.GitHubProvider.from_environment())
    print(json.dumps(report, sort_keys=True))
    return 0 if report["pass_allowed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
