"""Minimal INR-001 v0 capture helper.

The helper launches a target process and directly captures stdout/stderr/exit
status into a current-event record. It is local tooling only and does not make a
non-origin PASS claim.
"""
from __future__ import annotations
import argparse, hashlib, json, os, secrets, subprocess, sys, time
from pathlib import Path

def sha_bytes(b: bytes) -> str: return hashlib.sha256(b).hexdigest()

def main(argv=None) -> int:
    p=argparse.ArgumentParser()
    p.add_argument('--event-id', required=True)
    p.add_argument('--command-id', required=True)
    p.add_argument('--out-dir', required=True)
    p.add_argument('command', nargs=argparse.REMAINDER)
    ns=p.parse_args(argv)
    if not ns.command: raise SystemExit('command required')
    out=Path(ns.out_dir); out.mkdir(parents=True, exist_ok=True)
    challenge_id='inr-chal-'+secrets.token_hex(8); challenge=secrets.token_hex(32)
    start=time.time_ns()
    proc=subprocess.run(ns.command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)
    end=time.time_ns()
    stdout_path=out/(ns.command_id+'.stdout'); stderr_path=out/(ns.command_id+'.stderr')
    stdout_path.write_bytes(proc.stdout); stderr_path.write_bytes(proc.stderr)
    rec={'schema_version':'inr.capture_record.v0','event_id':ns.event_id,'command_id':ns.command_id,'run_challenge_id':challenge_id,'run_challenge_value':challenge,'target_process_launched':True,'pid_observed_by_capture':True,'command':ns.command,'start_time_ns':start,'end_time_ns':end,'return_code':proc.returncode,'stdout_ref':str(stdout_path),'stderr_ref':str(stderr_path),'stdout_sha256':sha_bytes(proc.stdout),'stderr_sha256':sha_bytes(proc.stderr),'capture_process':{'sys_executable':sys.executable,'pid':os.getpid()},'nonclaims':['capture record alone is not INR PASS','capture record alone is not IW acceptance']}
    (out/(ns.command_id+'.capture.json')).write_text(json.dumps(rec,indent=2,sort_keys=True)+'\n', encoding='utf-8')
    return proc.returncode
if __name__ == '__main__': raise SystemExit(main())
