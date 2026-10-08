"""INR-XR-001 v0 bundle collection and hashing helper (the single XR helper).

The helper takes three inputs: the event export that the INR-001 r3 supervisor wrote
on the external runner, the runner observation files, and the target files acquired
there. It splits the export into the XR raw event files, then writes
raw/sha256sums.txt and external_run_manifest.json. It prints the bundle digest (SHA-256 of the
manifest). The workflow must upload the bundle as the GitHub Actions artifact named
``inr-xr-bundle-<bundle_digest>`` (the R2 bundle-to-run binding).

It derives nothing and asserts nothing. The manifest carries references and hash
bindings only, and every predicate and classification is derived later by
validate_external_run_v0.py. EVENT_COMPLETE is a bundle-level marker this helper
writes after the supervisor has exited (the r3 supervisor lifecycle ends at
CAPTURE_COMPLETE).
"""
from __future__ import annotations

import argparse
import base64
import json
from pathlib import Path
import sys
import time

if __name__ == "__main__":  # pragma: no cover - CLI only
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from docs.inr_001 import supervisor_inr_v0 as sup  # noqa: E402
from docs.inr_001.xr import provider_github_v0 as provider_github  # noqa: E402
from docs.inr_001.xr import validate_external_run_v0 as xr  # noqa: E402

OBSERVATION_FILES = ("acquisition.log", "runner_identity.json", "workspace_provenance.json",
                     "isolation_checks.json", "python_identity.json", "git_identity.json")
CAPTURE_FIELDS = ("case_id", "command_id", "sequence", "event_id", "challenge", "case_nonce", "argv",
                  "popen_args", "cwd", "env_path", "env_git", "child_pid", "return_code", "start_ns",
                  "end_ns", "stdout_sha256", "stderr_sha256")


def json_bytes(value):
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def role_for(rel):
    for role, path in xr.SINGLETON_PATHS.items():
        if rel == path:
            return role
    for role, pattern in xr.PER_CASE_PATHS.items():
        prefix, _, suffix = pattern.partition("{}")
        if rel.startswith(prefix) and rel.endswith(suffix):
            return role
    if rel.startswith("raw/target/"):
        return "target_file"
    raise ValueError("not an XR evidence path: " + rel)


def event_files(export, *, started_at, completed_at, supervisor_sha256, supervisor_path, event_complete_ns=None):
    """Split one INR-001 r3 supervisor export into XR raw event files (path -> bytes)."""
    event_id, challenge = export["inr_event_id"], export["challenge"]
    files = {"raw/event_start.json": json_bytes({
        "schema_version": "inr.xr.raw.event_start.v0", "inr_event_id": event_id, "challenge": challenge,
        "ledger_reservation_entry_sha256": export["ledger_reservation_entry_sha256"],
        "started_at": started_at, "event_start_ns": export["lifecycle"]["EVENT_START"],
        "target_sha": export["target_sha"],
        "accepted_target_profile_binding": export["accepted_target_profile_binding"],
        "accepted_origin_reference_binding": export["accepted_origin_reference_binding"],
        "supervisor": export["supervisor"], "supervisor_sha256": supervisor_sha256,
        "supervisor_path": supervisor_path})}
    for record in export["capture_records"]:
        cid = record["case_id"]
        files[xr.PER_CASE_PATHS["stdout"].format(cid)] = base64.b64decode(record["stdout_base64"], validate=True)
        files[xr.PER_CASE_PATHS["stderr"].format(cid)] = base64.b64decode(record["stderr_base64"], validate=True)
        capture = {"schema_version": "inr.xr.raw.command_result.v0"}
        capture.update({key: record[key] for key in CAPTURE_FIELDS})
        files[xr.PER_CASE_PATHS["command_result"].format(cid)] = json_bytes(capture)
    files["raw/post_measurement.json"] = json_bytes({
        "schema_version": "inr.xr.raw.post_measurement.v0", "inr_event_id": event_id, "challenge": challenge,
        "lifecycle": export["lifecycle"], "measurements": export["measurements"],
        "git_probe": export["git_probe"]})
    files["raw/event_complete.json"] = json_bytes({
        "schema_version": "inr.xr.raw.event_complete.v0", "inr_event_id": event_id, "challenge": challenge,
        "completed_at": completed_at,
        "event_complete_ns": time.monotonic_ns() if event_complete_ns is None else event_complete_ns,
        "supervisor_report": export["verification"]})
    return files


def write_bundle(out_dir, files, *, inr_event_id, bundle_id, runner_declarations=None):
    """Write raw files, raw/sha256sums.txt and the manifest. Refuses an existing directory."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=False)
    profile, origin = sup.configuration()
    entries = []
    for rel in sorted(files):
        if xr._path_problem(rel) or not rel.startswith("raw/"):
            raise ValueError("unsafe evidence path: " + rel)
        target = out.joinpath(*rel.split("/"))
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(files[rel])
        entries.append({"role": role_for(rel), "path": rel, "sha256": sup.digest(files[rel])})
    sums = "".join(f"{e['sha256']}  {e['path']}\n" for e in entries).encode("ascii")
    sums_rel = xr.SINGLETON_PATHS["sha256sums"]
    out.joinpath(*sums_rel.split("/")).write_bytes(sums)
    entries.append({"role": "sha256sums", "path": sums_rel, "sha256": sup.digest(sums)})
    manifest = {"schema_version": "inr.xr.external_run_manifest.v0", "bundle_id": bundle_id,
                "inr_event_id": inr_event_id, "target_sha": sup.TARGET_SHA,
                "accepted_target_profile_reference": {"target_profile_id": profile["target_profile_id"],
                                                      "target_profile_digest": sup.PROFILE_DIGEST},
                "accepted_origin_reference": {"origin_reference_set_id": origin["origin_reference_set_id"],
                                              "origin_reference_set_digest": sup.ORIGIN_DIGEST},
                "evidence_files": entries}
    if runner_declarations is not None:
        manifest["runner_declarations"] = runner_declarations
    (out / xr.MANIFEST_NAME).write_bytes(json_bytes(manifest))
    return manifest


def collect(export_path, observations, target_repository, out_dir, *, started_at, completed_at, bundle_id):
    export = json.loads(Path(export_path).read_bytes())
    files = event_files(export, started_at=started_at, completed_at=completed_at,
                        supervisor_sha256=sup.digest(sup.SUPERVISOR.read_bytes()),
                        supervisor_path=str(sup.SUPERVISOR))
    for name in OBSERVATION_FILES:
        files["raw/" + name] = (Path(observations) / name).read_bytes()
    profile = sup.configuration()[0]
    for name in profile["target_file_digests"]:
        source = Path(target_repository, "docs", "portfolio_state", *name.split("/"))
        files[xr.TARGET_PATH.format(name)] = source.read_bytes()
    return write_bundle(out_dir, files, inr_event_id=export["inr_event_id"], bundle_id=bundle_id)


def main(argv=None):
    parser = argparse.ArgumentParser(prog="collect_bundle_v0", allow_abbrev=False)
    parser.add_argument("--export", required=True, type=Path)
    parser.add_argument("--observations", required=True, type=Path)
    parser.add_argument("--target-repository", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--started-at", required=True)
    parser.add_argument("--completed-at", required=True)
    parser.add_argument("--bundle-id", required=True)
    args = parser.parse_args(argv)
    manifest = collect(args.export, args.observations, args.target_repository, args.out,
                       started_at=args.started_at, completed_at=args.completed_at, bundle_id=args.bundle_id)
    bundle_digest = sup.digest((args.out / xr.MANIFEST_NAME).read_bytes())
    print(json.dumps({"bundle": str(args.out), "evidence_files": len(manifest["evidence_files"]),
                      "bundle_digest": bundle_digest,
                      "artifact_name": provider_github.ARTIFACT_PREFIX + bundle_digest}))
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI only
    raise SystemExit(main())
