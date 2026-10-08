"""Trusted child-side probe for the one pinned PSM source, not a plugin loader.

Launched by trusted_capture._launch as ``python -I -S -B runtime_probe.py SOURCE
INPUT REPOSITORY``. It reports raw observations only; it does not classify. The
verifier derives the classification and compares the exact refusal messages.
"""
from __future__ import annotations

import hashlib
import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys

TARGET_MODULE = "inr_pinned_psm_target"


def _git_shadowing():
    """Executables that Windows CreateProcess would pick before PATH for "git"."""
    if os.name != "nt":
        return []
    root = os.environ.get("SystemRoot") or os.environ.get("SYSTEMROOT") or "C:\\Windows"
    candidates = [Path(sys.executable).resolve().parent, Path.cwd(),
                  Path(root) / "System32", Path(root) / "System", Path(root)]
    return sorted({str(path / "git.exe") for path in candidates if (path / "git.exe").exists()})


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 3:
        return 3
    source, input_path, repository = map(Path, args)
    observed = {
        "target_preloaded": TARGET_MODULE in sys.modules,
        "site_loaded": "site" in sys.modules,
        "sitecustomize_loaded": "sitecustomize" in sys.modules,
        "usercustomize_loaded": "usercustomize" in sys.modules,
        "isolated": sys.flags.isolated,
        "no_site": sys.flags.no_site,
        "dont_write_bytecode": sys.dont_write_bytecode,
        "python_version": list(sys.version_info[:3]),
        "python_executable": str(Path(sys.executable).resolve()),
        "cwd": str(Path.cwd().resolve()),
        "git_which": shutil.which("git"),
        "git_shadowing": _git_shadowing(),
        "git_environment": sorted([k, v] for k, v in os.environ.items() if k.upper().startswith("GIT_")),
    }
    raw = source.read_bytes()
    loader = importlib.machinery.SourceFileLoader(TARGET_MODULE, str(source.resolve()))
    spec = importlib.util.spec_from_loader(TARGET_MODULE, loader)
    module = importlib.util.module_from_spec(spec)
    # Compile exactly the bytes that were hashed: never a cached code object/pyc.
    exec(compile(raw, str(source.resolve()), "exec"), module.__dict__)
    try:
        record = module.load_record(input_path)
        errors = list(module.validate_record(record, repository))
    except (OSError, UnicodeError, ValueError) as exc:
        errors = [str(exc)]
    observed.update({
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "post_source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "source_path": str(source.resolve()),
        "input_sha256": hashlib.sha256(input_path.read_bytes()).hexdigest(),
    })
    print(json.dumps({"event_id": os.environ.get("INR_EVENT_ID"),
                      "challenge": os.environ.get("INR_RUN_CHALLENGE"),
                      "case_id": os.environ.get("INR_CASE_ID"),
                      "case_nonce": os.environ.get("INR_CASE_NONCE"),
                      "identity": observed, "errors": errors}, sort_keys=True))
    return 2 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
