"""INR-001 v0 verifier (remediated candidate).

Security rule: executor-controlled event values are not trusted facts.  PASS is
code-derived only from trusted frozen configuration plus capture/evidence records
that are internally checked.  This verifier is INR-local tooling only; it does
not claim non-origin reconstruction PASS, IW acceptance, Human Final, or
production permission.
"""
from __future__ import annotations

import hashlib, json, os, sys
from pathlib import Path
from typing import Any

TARGET_SHA = "c5e1cfa2fb52874fe9c97e0eade6a120c12cb27b"
TRUSTED_PROFILE_ID = "INR_TARGET_PROFILE_PSM_001_V0"
TRUSTED_PROFILE_DIGEST = "2e2e75e246694fdd4d39d52bf3d5f6f65642dcbb3ef4621f258aed7724537634"
TRUSTED_ORIGIN_SET_ID = "INR_ORIGIN_SET_PSM_001_V0"
TRUSTED_ORIGIN_SET_DIGEST = "8512b8a1954673be69e0ab0c9486935eff07e4d91cecdcec6f0a4b50694c8a03"
RESULTS = {"PASS", "FAIL", "UNCONFIRMED", "BLOCKED"}
QUALIFYING_RUNNERS = {"SEPARATE_PHYSICAL_MACHINE", "FRESH_HOSTED_RUNNER"}
ROOT = Path(__file__).resolve().parent
PROFILE_PATH = ROOT / "profiles" / "psm_001_inr_target_profile_v0.json"
ORIGIN_PATH = ROOT / "origin" / "psm_001_origin_reference_set_v0.json"

class INRValidationError(ValueError): pass

def _canon(x: Any) -> bytes:
    return json.dumps(x, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()

def _digest_bytes(b: bytes) -> str: return hashlib.sha256(b).hexdigest()
def _digest_without(obj: dict[str, Any], *keys: str) -> str:
    return _digest_bytes(_canon({k:v for k,v in obj.items() if k not in keys}))
def _load(path: str | Path) -> Any: return json.loads(Path(path).read_text(encoding="utf-8"))
def load_profile() -> dict[str, Any]: return _load(PROFILE_PATH)
def load_origin() -> dict[str, Any]: return _load(ORIGIN_PATH)

def verify_profile(profile: dict[str, Any]) -> list[str]:
    e=[]
    if profile.get("target_sha") != TARGET_SHA: e.append("profile target mismatch")
    if profile.get("target_profile_id") != TRUSTED_PROFILE_ID: e.append("unknown profile id")
    if profile.get("target_profile_digest") != TRUSTED_PROFILE_DIGEST: e.append("profile digest field mismatch")
    if _digest_without(profile,"target_profile_digest") != TRUSTED_PROFILE_DIGEST: e.append("profile digest mismatch")
    cases=profile.get("required_cases", [])
    ids=[c.get("case_id") for c in cases]
    if len(ids)!=10 or len(set(ids))!=10: e.append("required case inventory invalid")
    cmd_ids=[c.get("command_id") for c in profile.get("command_inventory", [])]
    if len(cmd_ids)!=10 or len(set(cmd_ids))!=10: e.append("command inventory invalid")
    if any(c.get("mandatory_execution") is not True for c in cases): e.append("required case optionalized")
    return e

def verify_origin(origin: dict[str, Any]) -> list[str]:
    e=[]
    if origin.get("target_sha") != TARGET_SHA: e.append("origin target mismatch")
    if origin.get("origin_reference_set_id") != TRUSTED_ORIGIN_SET_ID: e.append("unknown origin set")
    if origin.get("origin_reference_set_digest") != TRUSTED_ORIGIN_SET_DIGEST: e.append("origin digest field mismatch")
    if _digest_without(origin,"origin_reference_set_digest") != TRUSTED_ORIGIN_SET_DIGEST: e.append("origin digest mismatch")
    if not origin.get("origins"): e.append("origin coverage missing")
    return e

def _read_evidence_file(base: Path, ref: str) -> bytes | None:
    if not isinstance(ref, str) or not ref: return None
    p = Path(ref)
    if not p.is_absolute(): p = base / p
    try:
        rp = p.resolve()
        # Keep evidence under supplied base when relative. Absolute is allowed for
        # captured external events but must exist.
        return rp.read_bytes()
    except OSError:
        return None

def _capture_record_ok(rec: dict[str, Any], event_id: str, challenge: str, base: Path) -> list[str]:
    e=[]
    if rec.get("schema_version") != "inr.capture_record.v0": e.append("bad capture schema")
    if rec.get("event_id") != event_id: e.append("capture event mismatch")
    if rec.get("run_challenge_value") != challenge: e.append("capture challenge mismatch")
    if rec.get("target_process_launched") is not True: e.append("capture did not launch target")
    if rec.get("pid_observed_by_capture") is not True: e.append("child process provenance absent")
    if not isinstance(rec.get("command"), list) or not rec.get("command"): e.append("capture command absent")
    if not isinstance(rec.get("return_code"), int): e.append("capture return code absent")
    if not (isinstance(rec.get("start_time_ns"), int) and isinstance(rec.get("end_time_ns"), int) and rec["start_time_ns"] <= rec["end_time_ns"]): e.append("capture time invalid")
    for stream in ("stdout", "stderr"):
        data=_read_evidence_file(base, rec.get(stream+"_ref"))
        if data is None: e.append(stream+" evidence missing")
        elif _digest_bytes(data) != rec.get(stream+"_sha256"): e.append(stream+" evidence hash mismatch")
    return e

def validate_event(event: dict[str, Any], profile: dict[str, Any] | None=None, origin: dict[str, Any] | None=None, evidence_base: str | Path | None=None, used_challenges: set[str] | None=None) -> dict[str, Any]:
    profile=profile or load_profile(); origin=origin or load_origin(); errors=[]; blocked=[]; fail=[]; unconfirmed=[]
    errors += verify_profile(profile); errors += verify_origin(origin)
    base=Path(evidence_base or event.get("evidence_base") or ".")
    event_id=event.get("inr_event_id")
    if event.get("schema_version") != "inr.event.v0": unconfirmed.append("bad schema_version")
    if event.get("target_sha") != TARGET_SHA: unconfirmed.append("target sha mismatch")
    b=event.get("accepted_target_profile_binding", {})
    if b.get("target_profile_id")!=TRUSTED_PROFILE_ID or b.get("target_profile_digest")!=TRUSTED_PROFILE_DIGEST: unconfirmed.append("trusted profile binding mismatch")
    ob=event.get("accepted_origin_reference_binding", {})
    if ob.get("origin_reference_set_id")!=TRUSTED_ORIGIN_SET_ID or ob.get("origin_reference_set_digest")!=TRUSTED_ORIGIN_SET_DIGEST: unconfirmed.append("trusted origin binding mismatch")

    # Challenge must be capture-owned, current, single-use, not merely an event flag.
    ch=event.get("trusted_challenge_record", {})
    challenge=ch.get("run_challenge_value")
    if not (ch.get("generated_by") == "capture_inr_v0" and ch.get("generated_before_target_execution") is True and ch.get("bound_event_id") == event_id and ch.get("bound_target_sha") == TARGET_SHA and ch.get("bound_profile_digest") == TRUSTED_PROFILE_DIGEST and ch.get("bound_origin_reference_set_digest") == TRUSTED_ORIGIN_SET_DIGEST and ch.get("single_use") is True):
        unconfirmed.append("trusted challenge binding invalid")
    if used_challenges is not None and challenge in used_challenges: fail.append("challenge reuse")

    lc=event.get("lifecycle", {})
    order=["EVENT_START","BINDINGS_RECORDED","ENVIRONMENT_RECORDED","ACQUISITION_VERIFIED","FREEZE_START","COMMAND_EXECUTION_BEGIN","EXECUTION_COMPLETE","POST_MEASUREMENT","CAPTURE_COMPLETE","EVENT_COMPLETE"]
    times=[]
    for k in order:
        v=lc.get(k)
        if not isinstance(v, int): unconfirmed.append(f"missing lifecycle {k}")
        else: times.append(v)
    if len(times)==len(order) and times != sorted(times): fail.append("lifecycle order invalid")

    bi=event.get("byte_identity_evidence", {})
    for k in ("distribution_sha256","executed_sha256","post_execution_sha256"):
        if not bi.get(k): unconfirmed.append("byte identity missing "+k)
    if bi.get("post_execution_sha256") and bi.get("executed_sha256") and bi.get("post_execution_sha256") != bi.get("executed_sha256"): fail.append("executed bytes changed")
    if bi.get("measured_by") != "capture_inr_v0": unconfirmed.append("byte identity not capture-measured")

    im=event.get("module_execution_evidence", {})
    if not (im.get("fresh_interpreter") is True and im.get("target_preloaded_before_import") is False and im.get("sitecustomize") == "ABSENT" and im.get("usercustomize") == "ABSENT" and im.get("bytecode_policy") == "SOURCE_BACKED_NO_STALE_PYC" and im.get("loader_policy") == "STANDARD_SOURCE_LOADER" and im.get("source_digest") and im.get("source_digest") == im.get("executed_source_digest") and im.get("resolved_origin") and im.get("resolved_origin") == im.get("measured_path") and im.get("runtime_probe") == "capture_import_probe"):
        unconfirmed.append("module execution chain unproven")

    git=event.get("git_runtime_evidence", {})
    if not (git.get("measured_by") == "capture_inr_v0" and git.get("resolved_git") and git.get("git_version") and git.get("repository_path") and git.get("repository_head") == TARGET_SHA and git.get("required_objects_available") is True and git.get("git_dir") in (None, "") and git.get("git_work_tree") in (None, "") and git.get("replace_refs") == [] and git.get("alternates") == [] and git.get("path_resolution_verified") is True):
        blocked.append("git runtime identity unavailable")

    iso=event.get("protected_set_isolation_evidence", {})
    if not (iso.get("measured_by") == "capture_inr_v0" and iso.get("all_writer_isolation_evidence") == "ESTABLISHED" and iso.get("tree_read_only") is True and iso.get("shared_writable_aliases") == [] and iso.get("writable_parent_paths") == [] and iso.get("symlink_or_junction_paths") == [] and iso.get("hardlink_aliases") == [] and iso.get("network_or_shared_paths") == []):
        unconfirmed.append("protected set isolation insufficient")

    no=event.get("non_origin_evidence", {})
    if no.get("runner_class") not in {"SEPARATE_PHYSICAL_MACHINE","FRESH_HOSTED_RUNNER"}: unconfirmed.append("runner class not qualifying")
    if not (no.get("origin_host_is_execution_host") is False and no.get("source_independently_acquired") is True and no.get("evidence_generated_on_runner") is True and no.get("origin_reference_prefrozen") is True and no.get("shared_mutable_state_evidence") == [] and no.get("workspace_provenance") == "FRESH_NON_ORIGIN_WORKSPACE" and no.get("origin_worktree_copied") is False):
        unconfirmed.append("non-origin evidence insufficient")

    # Capture records are the trusted execution source.
    records=event.get("capture_records", [])
    if not isinstance(records, list) or not records: unconfirmed.append("capture records missing")
    for rec in records:
        unconfirmed += _capture_record_ok(rec, event_id, challenge, base)
    rec_by_cmd={r.get("command_id"):r for r in records if isinstance(r, dict)}
    if len(rec_by_cmd) != len(records): fail.append("duplicate capture command_id")

    prof_cases={c["case_id"]:c for c in profile["required_cases"]}
    profile_cmd={c["case_id"]:c["command_id"] for c in profile["command_inventory"]}
    bindings=event.get("case_result_bindings", [])
    seen_cases={}; seq=[]; seen_cmd=set()
    for r in bindings:
        cid=r.get("case_id"); cmd=r.get("command_id"); seq.append(r.get("sequence"))
        if cid in seen_cases: fail.append("duplicate case result")
        seen_cases[cid]=r
        if cmd in seen_cmd: fail.append("duplicate command result")
        seen_cmd.add(cmd)
        if r.get("expected_from_profile") is not True: fail.append("executor-defined expectation")
        if r.get("event_id") != event_id or r.get("challenge_value") != challenge: fail.append("case result replay/cross-event")
        cap=rec_by_cmd.get(cmd)
        if not cap: unconfirmed.append("missing capture for command "+str(cmd)); continue
        if r.get("return_code") != cap.get("return_code"): fail.append("return code not from capture")
        if r.get("stdout_sha256") != cap.get("stdout_sha256") or r.get("stderr_sha256") != cap.get("stderr_sha256"): fail.append("stream hash not from capture")
    if sorted(seq) != list(range(1,len(seq)+1)): fail.append("command sequence invalid")
    for cid, spec in prof_cases.items():
        r=seen_cases.get(cid); expected_cmd=profile_cmd.get(cid)
        if not r: unconfirmed.append("missing required case "+cid); continue
        if r.get("command_id") != expected_cmd: fail.append("renamed command id")
        if r.get("observed_classification") != spec.get("expected_classification"): fail.append("case expectation mismatch "+cid)
        if r.get("return_code") not in spec.get("accepted_return_codes", []): fail.append("return code mismatch "+cid)
        if r.get("input_digest") != spec.get("input_digest"): fail.append("input digest mismatch "+cid)
        if r.get("mandatory_execution") is not True: fail.append("case optionalized "+cid)
    for x in event.get("extra_command_records", []) or []:
        if x.get("state_changing") is True: fail.append("state-changing extra command")
    rep=event.get("repair_detection_evidence", {})
    if rep.get("repair_detected") is True or rep.get("target_digest_change") is True or rep.get("environment_change") is True or rep.get("input_change") is True: fail.append("repair/mutation detected")
    if any(r.get("prior_failed_or_blocked_rerun") for r in bindings): fail.append("rerun laundering")

    # Code-owned result precedence. Event final_result is informational only.
    all_errors=errors+blocked+fail+unconfirmed
    if blocked: derived="BLOCKED"
    elif fail: derived="FAIL"
    elif unconfirmed or errors: derived="UNCONFIRMED"
    else: derived="PASS"
    pass_allowed = derived == "PASS"
    return {"schema_version":"inr.verifier.result.v0","derived_result":derived,"pass_allowed":pass_allowed,"errors":all_errors,"blocked":blocked,"fail":fail,"unconfirmed":unconfirmed,"event_claimed_final_result":event.get("final_result"),"nonclaims":["INR local verifier PASS is not IW acceptance","INR local verifier PASS is not Human Final","INR local verifier PASS is not production permission"]}

def main(argv: list[str]) -> int:
    if len(argv)!=2:
        print("usage: validate_inr_v0.py EVENT.json", file=sys.stderr); return 2
    event_path=Path(argv[1])
    res=validate_event(_load(event_path), evidence_base=event_path.parent)
    print(json.dumps(res, indent=2, sort_keys=True))
    return 0 if res["pass_allowed"] else 1
if __name__ == "__main__": raise SystemExit(main(sys.argv))
