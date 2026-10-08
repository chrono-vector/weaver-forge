"""INR-001 v0 verifier.

Non-authoritative local tooling for validating INR event records against the
frozen PSM-001 target profile.  It does not run a reconstruction, admit IW
evidence, create Human Final, or grant production permission.
"""
from __future__ import annotations

import json, hashlib, os, sys
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

class INRValidationError(ValueError):
    pass

def _canon(x: Any) -> bytes:
    return json.dumps(x, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()

def digest_json_without(obj: dict[str, Any], *keys: str) -> str:
    return hashlib.sha256(_canon({k:v for k,v in obj.items() if k not in keys})).hexdigest()

def load_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))

def load_profile() -> dict[str, Any]: return load_json(PROFILE_PATH)
def load_origin() -> dict[str, Any]: return load_json(ORIGIN_PATH)

def verify_profile(profile: dict[str, Any]) -> list[str]:
    e=[]
    if profile.get("target_sha") != TARGET_SHA: e.append("profile target mismatch")
    if profile.get("target_profile_id") != TRUSTED_PROFILE_ID: e.append("unknown profile id")
    if profile.get("target_profile_digest") != TRUSTED_PROFILE_DIGEST: e.append("profile digest field mismatch")
    if digest_json_without(profile, "target_profile_digest") != TRUSTED_PROFILE_DIGEST: e.append("profile digest mismatch")
    ids=[c.get("case_id") for c in profile.get("required_cases", [])]
    if len(ids)!=10 or len(set(ids))!=10: e.append("required case inventory invalid")
    if any(c.get("mandatory_execution") is not True for c in profile.get("required_cases", [])): e.append("required case optionalized")
    return e

def verify_origin(origin: dict[str, Any]) -> list[str]:
    e=[]
    if origin.get("target_sha") != TARGET_SHA: e.append("origin target mismatch")
    if origin.get("origin_reference_set_id") != TRUSTED_ORIGIN_SET_ID: e.append("unknown origin set")
    if origin.get("origin_reference_set_digest") != TRUSTED_ORIGIN_SET_DIGEST: e.append("origin digest field mismatch")
    if digest_json_without(origin, "origin_reference_set_digest") != TRUSTED_ORIGIN_SET_DIGEST: e.append("origin digest mismatch")
    if not origin.get("origins"): e.append("origin coverage missing")
    return e

def validate_event(event: dict[str, Any], profile: dict[str, Any] | None=None, origin: dict[str, Any] | None=None) -> dict[str, Any]:
    profile = profile or load_profile(); origin = origin or load_origin(); errors=[]
    errors += verify_profile(profile); errors += verify_origin(origin)
    if event.get("schema_version") != "inr.event.v0": errors.append("bad schema_version")
    if event.get("target_sha") != TARGET_SHA: errors.append("target sha mismatch")
    b=event.get("accepted_target_profile_binding", {})
    if b.get("target_profile_id") != TRUSTED_PROFILE_ID or b.get("target_profile_digest") != TRUSTED_PROFILE_DIGEST: errors.append("trusted profile binding mismatch")
    ob=event.get("accepted_origin_reference_binding", {})
    if ob.get("origin_reference_set_id") != TRUSTED_ORIGIN_SET_ID or ob.get("origin_reference_set_digest") != TRUSTED_ORIGIN_SET_DIGEST: errors.append("trusted origin binding mismatch")
    # lifecycle and challenge freshness
    lc=event.get("lifecycle", {})
    for k in ("EVENT_START","FREEZE_START","CAPTURE_COMPLETE","EVENT_COMPLETE"):
        if not lc.get(k): errors.append(f"missing lifecycle {k}")
    ch=event.get("run_challenge", {})
    if not (ch.get("run_challenge_id") and ch.get("run_challenge_value") and ch.get("single_use") is True and ch.get("bound_event_id") == event.get("inr_event_id") and ch.get("reuse_status") == "UNUSED"):
        errors.append("run challenge not single-use current-event bound")
    # byte identity
    bi=event.get("byte_identity", {})
    if not (bi.get("distribution_sha256") and bi.get("executed_sha256") and bi.get("executed_bytes_bound") is True and bi.get("post_execution_sha256") == bi.get("executed_sha256")):
        errors.append("executed byte identity unbound")
    # module/import binding
    im=event.get("module_execution", {})
    if not (im.get("fresh_interpreter") is True and im.get("target_preloaded") is False and im.get("sitecustomize") == "ABSENT" and im.get("usercustomize") == "ABSENT" and im.get("bytecode_policy") == "SOURCE_BACKED_NO_STALE_PYC" and im.get("loader_policy") == "STANDARD_SOURCE_LOADER" and im.get("source_digest") == im.get("executed_source_digest") and im.get("resolved_origin") == im.get("measured_path")):
        errors.append("module execution binding invalid")
    # git contract
    git=event.get("git_runtime", {})
    if not (git.get("resolved_git") and git.get("git_version") and git.get("repository_head") == TARGET_SHA and git.get("git_dir_redirect") is False and git.get("git_work_tree_redirect") is False and git.get("replace_refs") == [] and git.get("wrapper_risk") is False):
        errors.append("git runtime contract invalid")
    # protected set / all writer isolation
    ps=event.get("protected_set_isolation", {})
    if not (ps.get("all_writer_isolation") is True and ps.get("tree_read_only") is True and ps.get("shared_writable_aliases") == [] and ps.get("writable_parent_risk") is False and ps.get("symlink_or_junction_risk") is False and ps.get("hardlink_alias_risk") is False):
        errors.append("protected set isolation insufficient")
    # non-origin policy
    no=event.get("non_origin", {})
    if no.get("runner_class") not in QUALIFYING_RUNNERS or no.get("origin_host_is_execution_host") is not False or no.get("shared_mutable_state") != [] or no.get("source_independently_acquired") is not True or no.get("evidence_generated_on_runner") is not True or no.get("origin_reference_prefrozen") is not True:
        errors.append("non-origin acceptance insufficient")
    # capture must launch target process and not replay old outputs
    cap=event.get("capture_provenance", {})
    if not (cap.get("capture_launched_target") is True and cap.get("direct_stdout_stderr") is True and cap.get("exit_status_from_child") is True and cap.get("historical_output_only") is False and cap.get("event_id") == event.get("inr_event_id") and cap.get("challenge_value") == ch.get("run_challenge_value")):
        errors.append("target process capture binding invalid")
    # command/result one-to-one binding
    prof_cases={c["case_id"]:c for c in profile["required_cases"]}
    results=event.get("case_result_bindings", [])
    seen_cases={}; seen_cmd=set(); seq=[]
    for r in results:
        cid=r.get("case_id"); cmd=r.get("command_id"); seq.append(r.get("sequence"))
        if cid in seen_cases: errors.append("duplicate case result")
        seen_cases[cid]=r
        if cmd in seen_cmd: errors.append("duplicate command_id")
        seen_cmd.add(cmd)
        if r.get("expected_from_profile") is not True: errors.append("executor-defined expectation")
        if r.get("event_id") != event.get("inr_event_id") or r.get("challenge_value") != ch.get("run_challenge_value"): errors.append("result not current-event bound")
    if sorted(seq) != list(range(1, len(seq)+1)): errors.append("non-contiguous command sequence")
    for cid, spec in prof_cases.items():
        r=seen_cases.get(cid)
        if not r: errors.append(f"missing required case {cid}"); continue
        if r.get("observed_classification") != spec.get("expected_classification"): errors.append(f"case expectation mismatch {cid}")
        if r.get("return_code") not in spec.get("accepted_return_codes", []): errors.append(f"return code mismatch {cid}")
        if r.get("mandatory_execution") is not True: errors.append(f"case optionalized {cid}")
    if event.get("extra_command_records") not in ([], None):
        if any(x.get("state_changing") for x in event.get("extra_command_records", [])): errors.append("state-changing extra command")
    if event.get("repair_detection", {}).get("repair_detected") is True: errors.append("repair detected")
    if any(r.get("prior_failed_or_blocked_rerun") for r in results): errors.append("rerun laundering")
    claimed=event.get("final_result")
    if claimed not in RESULTS: errors.append("invalid claimed final_result")
    derived="PASS" if not errors else ("FAIL" if any("expectation mismatch" in x or "repair" in x or "rerun" in x for x in errors) else "UNCONFIRMED")
    if claimed == "PASS" and derived != "PASS": errors.append("PASS forbidden by predicate")
    return {"schema_version":"inr.verifier.result.v0","derived_result":"PASS" if not errors else derived,"pass_allowed": not errors,"errors":errors,"nonclaims":["INR PASS is not IW acceptance","INR PASS is not Human Final","INR PASS is not production permission"]}

def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: validate_inr_v0.py EVENT.json", file=sys.stderr); return 2
    res=validate_event(load_json(argv[1])); print(json.dumps(res, indent=2, sort_keys=True))
    return 0 if res["pass_allowed"] else 1
if __name__ == "__main__": raise SystemExit(main(sys.argv))
