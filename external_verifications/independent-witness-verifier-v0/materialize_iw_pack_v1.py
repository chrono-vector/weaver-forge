#!/usr/bin/env python3
"""Materialize iw-pack-v1 frozen bundle + maintainer structural dry-run (no witness handoff)."""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from independent_witness_verifier_v0 import (  # noqa: E402
    AUTHORITY_SUBSET,
    FROZEN_CAW_COMMIT,
    IW_VERIFIER_VERSION,
    PACK_FORMAT_VERSION,
    PACK_SCHEMA,
    PRIMARY_CHAIN_ID,
    RUNTIME_METHODS,
    RUNTIME_TARGETS,
    SELECTED_RUNTIME_PATHS,
    SELECTED_STATIC_PATHS,
    build_minimal_pack,
    digest,
    verify_independent_witness_v0,
)

PACK_ROOT = HERE / "iw-pack-v1"
SCHEMA_SRC = HERE / "schemas"


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def write_json(path: Path, obj: object) -> None:
    write(path, json.dumps(obj, indent=2, ensure_ascii=True) + "\n")


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def git_info() -> dict[str, str]:
    forge = HERE.parents[1]
    def _g(*args: str) -> str:
        return subprocess.check_output(["git", *args], cwd=forge, text=True).strip()
    try:
        return {
            "commit": _g("rev-parse", "HEAD"),
            "tree": _g("rev-parse", "HEAD^{tree}"),
            "parent": _g("rev-parse", "HEAD^"),
            "branch": _g("rev-parse", "--abbrev-ref", "HEAD"),
            "status_dirty": bool(_g("status", "--porcelain")),
        }
    except Exception as e:  # noqa: BLE001
        return {"error": str(e), "commit": "UNKNOWN", "tree": "UNKNOWN"}


def materialize() -> dict:
    if PACK_ROOT.exists():
        shutil.rmtree(PACK_ROOT)
    for d in [
        "frozen-inputs/path-sot",
        "frozen-inputs/fixture-specs",
        "frozen-inputs/schemas",
        "instructions",
        "schemas",
        "expected-structure",
        "reference-disclosure",
        "witness-output-template",
        "verifier",
        "manifests",
    ]:
        (PACK_ROOT / d).mkdir(parents=True, exist_ok=True)

    gi = git_info()
    weaver_commit = gi.get("commit", "UNKNOWN")
    weaver_tree = gi.get("tree", "UNKNOWN")

    # --- README ---
    write(
        PACK_ROOT / "README.md",
        f"""# iw-pack-v1

Frozen Independent Witness pack for CAW BOUNDED_D scope.

## Scope

- Static: `{SELECTED_STATIC_PATHS[0]}`, `{SELECTED_STATIC_PATHS[1]}`
- Runtime: Marketplace `createListing` + MintableCaw `mint`
- Authority: AUTH-005 `CawProfile.owner()` read-only subset

## Frozen pins

- CAW commit: `{FROZEN_CAW_COMMIT}`
- Pack format: `{PACK_FORMAT_VERSION}`
- IW verifier: `{IW_VERIFIER_VERSION}`

## Nonclaims

Accepted IW reproduction (when performed by an external witness under separate authorization) does **not** imply CAW certified, trustless/decentralized verified, live tx verified, authority execution verified, system permissionless, security audit complete, or production safe.

## Safety

- REAL WALLET: NO
- REAL PRIVATE KEY: NO
- REAL CREDENTIAL: NO
- LIVE BROADCAST: NO
- LIVE MUTATION: NO

## Independence

Self-check ≠ Independent Verification. Maintainer dry-run ≠ Independent Witness.

## How to run

1. Read `instructions/PROCEDURE.md`
2. Verify `frozen-inputs/` digests
3. Produce outputs into a copy of `witness-output-template/`
4. Do **not** open `reference-disclosure/` until your output pack is frozen
5. Submit pack for IW verifier adjudication

Do not force a PASS. Record failures honestly.
""",
    )

    # --- frozen inputs ---
    write(PACK_ROOT / "frozen-inputs/caw-commit.txt", FROZEN_CAW_COMMIT + "\n")
    write_json(
        PACK_ROOT / "frozen-inputs/caw-tree-digest.json",
        {
            "CAW_COMMIT": FROZEN_CAW_COMMIT,
            "note": "Witness must check out this commit; tree digest verified against local CAW checkout",
        },
    )
    write_json(
        PACK_ROOT / "frozen-inputs/path-ids.json",
        {
            "static_paths": list(SELECTED_STATIC_PATHS),
            "runtime_paths": list(SELECTED_RUNTIME_PATHS),
            "methods": dict(RUNTIME_METHODS),
            "targets": dict(RUNTIME_TARGETS),
            "chain_id": PRIMARY_CHAIN_ID,
        },
    )
    write_json(
        PACK_ROOT / "frozen-inputs/authority-subset-targets.json",
        {
            "scope": "READ_ONLY_SUBSET",
            "selected": dict(AUTHORITY_SUBSET),
            "rationale": (
                "AUTH-005 CawProfile.owner() is a simple Ownable getter on a stable Sepolia "
                "deployed address already successfully read in CARO; representative of authority "
                "packaging without L2 multi-chain reproduction or privileged execution."
            ),
            "scope_limited_note": "One read ≠ full authority map verification",
            "forbidden": [
                "transferOwnership",
                "privileged execution",
                "identity inference",
                "live authority action",
            ],
        },
    )
    write_json(
        PACK_ROOT / "frozen-inputs/weaver-pin.json",
        {
            "WEAVER_COMMIT_AT_MATERIALIZATION": weaver_commit,
            "WEAVER_TREE_AT_MATERIALIZATION": weaver_tree,
            "note": "Final freeze record updated after IW implementation commit",
            "IW_VERIFIER_VERSION": IW_VERIFIER_VERSION,
            "PACK_FORMAT_VERSION": PACK_FORMAT_VERSION,
            "PACK_SCHEMA": PACK_SCHEMA,
        },
    )

    # path SoT summaries (frozen procedure inputs — not derived witness proof)
    write_json(
        PACK_ROOT / "frozen-inputs/path-sot/wrps-v0-p0014.json",
        {
            "PATH_ID": "wrps-v0-p0014",
            "CONTRACT": "CawProfileMarketplace",
            "METHOD": RUNTIME_METHODS["wrps-v0-p0014"],
            "TARGET_ADDRESS": RUNTIME_TARGETS["wrps-v0-p0014"],
            "CHAIN_ID": PRIMARY_CHAIN_ID,
            "STATIC_STATUS_REFERENCE": "COMPLETE",
            "note": "Witness regenerates static binding checks from CAW source at frozen commit",
        },
    )
    write_json(
        PACK_ROOT / "frozen-inputs/path-sot/wrps-v0-p0030.json",
        {
            "PATH_ID": "wrps-v0-p0030",
            "CONTRACT": "MintableCaw",
            "METHOD": RUNTIME_METHODS["wrps-v0-p0030"],
            "TARGET_ADDRESS": RUNTIME_TARGETS["wrps-v0-p0030"],
            "CHAIN_ID": PRIMARY_CHAIN_ID,
            "SELECTOR": "0x40c10f19",
            "STATIC_STATUS_REFERENCE": "COMPLETE",
            "note": "Witness regenerates static binding checks from CAW source at frozen commit",
        },
    )

    # fixture specs (inputs only — expected hashes sealed in reference-disclosure)
    write_json(
        PACK_ROOT / "frozen-inputs/fixture-specs/p0014-createListing.json",
        {
            "PATH_ID": "wrps-v0-p0014",
            "method": RUNTIME_METHODS["wrps-v0-p0014"],
            "target": RUNTIME_TARGETS["wrps-v0-p0014"],
            "abi_hint": "createListing(uint32,uint8,address,uint256,uint256,uint64)",
            "fixture_policy": "Use published synthetic fixture values from pack; encode locally",
            "params_template": {
                "profileId": "SYNTHETIC_UINT32",
                "listingType": "SYNTHETIC_UINT8",
                "paymentToken": "SYNTHETIC_ADDRESS",
                "price": "SYNTHETIC_UINT256",
                "amount": "SYNTHETIC_UINT256",
                "deadline": "SYNTHETIC_UINT64",
            },
            "expected_calldata_sha256": "REVEAL_AFTER_RUN_SEE_reference-disclosure",
        },
    )
    write_json(
        PACK_ROOT / "frozen-inputs/fixture-specs/p0030-mint.json",
        {
            "PATH_ID": "wrps-v0-p0030",
            "method": RUNTIME_METHODS["wrps-v0-p0030"],
            "target": RUNTIME_TARGETS["wrps-v0-p0030"],
            "selector_hint": "keccak256(mint(address,uint256))[:4] == 0x40c10f19",
            "params_template": {
                "to": "SYNTHETIC_ADDRESS",
                "amount": "SYNTHETIC_UINT256",
            },
            "expected_calldata_sha256": "REVEAL_AFTER_RUN_SEE_reference-disclosure",
        },
    )

    # copy schemas into pack
    for src in SCHEMA_SRC.glob("*.json"):
        shutil.copy2(src, PACK_ROOT / "schemas" / src.name)
        shutil.copy2(src, PACK_ROOT / "frozen-inputs/schemas" / src.name)

    # frozen input manifest (will finalize digests below)
    frozen_files = []
    for p in sorted((PACK_ROOT / "frozen-inputs").rglob("*")):
        if p.is_file() and p.name != "FROZEN_INPUT_MANIFEST.json":
            frozen_files.append(p)

    # instructions
    write(
        PACK_ROOT / "instructions/PROCEDURE.md",
        """# IW v1 Procedure (BOUNDED_D)

Bias rule: Do **not** force a PASS. Record honest observations.

## A. STATIC p0014

- **INPUT**: `frozen-inputs/path-sot/wrps-v0-p0014.json` + CAW checkout at frozen commit
- **ACTION**: Independently re-derive/verify static path binding for `CawProfileMarketplace.createListing`
- **OUTPUT**: `static-reproduction-results.json` entry for `wrps-v0-p0014`
- **PASS CONDITION**: Binding reconstructible; `REPRODUCTION_PASS` or explicit mismatch recorded
- **FAIL CONDITION**: Missing frozen source → `DEPENDENCY_BLOCKED` / `SOURCE_MISMATCH`
- **SAFETY BOUNDARY**: `NO_NETWORK`

## B. STATIC p0030

- **INPUT**: `frozen-inputs/path-sot/wrps-v0-p0030.json` + CAW checkout
- **ACTION**: Independently re-derive/verify static binding for `MintableCaw.mint`
- **OUTPUT**: `static-reproduction-results.json` entry for `wrps-v0-p0030`
- **PASS CONDITION**: Binding reconstructible
- **FAIL CONDITION**: `DEPENDENCY_BLOCKED` / `SOURCE_MISMATCH`
- **SAFETY BOUNDARY**: `NO_NETWORK`

## C. p0014 runtime input / dispatch / bounded local execution shape

- **INPUT**: fixture spec `p0014-createListing.json` + ABI from frozen CAW
- **ACTION**: Encode calldata locally; construct dispatch envelope; optional bounded local-fork simulation per published policy — **no broadcast**
- **OUTPUT**: `runtime-input-results.json`, `runtime-dispatch-results.json`, `runtime-execution-results.json` for p0014
- **PASS CONDITION**: Witness-produced artifacts present; honest observation of success/revert/block
- **FAIL CONDITION**: `RUNTIME_MISMATCH` / `RPC_BLOCKED` / `ENVIRONMENT_BLOCKED`
- **SAFETY BOUNDARY**: `NO_NETWORK` for encoding; `LOCAL_FORK_BOUNDED_MUTATION` only if required and local-only

## D. p0030 runtime input / read-only eth_call success shape

- **INPUT**: fixture spec `p0030-mint.json`
- **ACTION**: Encode `mint(address,uint256)` locally; ephemeral local fork `eth_call` — **no broadcast**
- **OUTPUT**: runtime input/dispatch/execution results for p0030
- **PASS CONDITION**: Selector/encoding + call observation recorded; `LIVE_MUTATION=false`
- **FAIL CONDITION**: `RPC_BLOCKED` / `RUNTIME_MISMATCH` / `UNEXPECTED_RESULT`
- **SAFETY BOUNDARY**: `LOCAL_FORK_READ_ONLY` or `NO_NETWORK` for encoding-only

## E. Authority read-only subset

- **INPUT**: `frozen-inputs/authority-subset-targets.json` (AUTH-005 `owner()`)
- **ACTION**: Read-only `eth_call` of `owner()`; record 20-byte address; **do not** claim holder identity
- **OUTPUT**: `authority-read-results.json`
- **PASS CONDITION**: Read attempt recorded under `READ_ONLY_NETWORK` / `LOCAL_FORK_READ_ONLY`
- **FAIL CONDITION**: `RPC_BLOCKED` / `SOURCE_MISMATCH`
- **SAFETY BOUNDARY**: Read-only; no privileged execution

## Finalization

Capture environment, failure-log, retry-log, digests, attestation, receipt, manifest.
Compare to `reference-disclosure/` **only after** output pack is frozen.
""",
    )
    write(
        PACK_ROOT / "instructions/NETWORK_RULES.md",
        """# Network rules

Allowed modes: `NO_NETWORK`, `READ_ONLY_NETWORK`, `LOCAL_FORK_READ_ONLY`, `LOCAL_FORK_BOUNDED_MUTATION` (only if procedure requires).

Forbidden: live mutation, broadcast, real wallet, real private key, real credentials.

IW v1 requires: REAL_WALLET=NO, REAL_PRIVATE_KEY=NO, REAL_CREDENTIAL=NO, LIVE_BROADCAST=NO, LIVE_MUTATION=NO.
""",
    )
    write(
        PACK_ROOT / "instructions/INDEPENDENCE.md",
        """# Independence criteria (all mandatory)

1. OPERATOR_INDEPENDENCE
2. ENVIRONMENT_INDEPENDENCE
3. EXECUTION_INDEPENDENCE
4. OBSERVATION_INDEPENDENCE
5. EVIDENCE_GENERATION_INDEPENDENCE
6. RESULT_SUBMISSION_INDEPENDENCE

Designated witness ≠ Independent Witness.
MATCHED ≠ ACCEPTED.
Maintainer dry-run ≠ Independent Witness.
Do not copy operator-derived results as primary proof.
""",
    )
    write(
        PACK_ROOT / "instructions/FAILURES.md",
        """# Failure handling

Categories: REPRODUCTION_PASS, REPRODUCTION_MISMATCH, ENVIRONMENT_BLOCKED, DEPENDENCY_BLOCKED, RPC_BLOCKED, SOURCE_MISMATCH, RUNTIME_MISMATCH, UNEXPECTED_RESULT, WITNESS_ABORTED.

Rules:
- Failed attempts must not be deleted or silently overwritten
- Retries append to retry-log with prior_failure_id
- Later PASS does not erase earlier failure
""",
    )
    write(
        PACK_ROOT / "instructions/NONCLAIMS.md",
        """# Nonclaim gates

IW acceptance must never automatically imply:

- CAW_CERTIFIED
- TRUSTLESS_VERIFIED
- DECENTRALIZED_VERIFIED
- LIVE_TRANSACTION_VERIFIED
- AUTHORITY_EXECUTION_VERIFIED
- SYSTEM_PERMISSIONLESS
- SECURITY_AUDIT_COMPLETE
- PRODUCTION_SAFE

Acceptance applies only to frozen IW v1 BOUNDED_D scope.
""",
    )
    write(
        PACK_ROOT / "instructions/DISCLOSURE.md",
        """# Semi-blind disclosure

**Visible before run**: frozen commit/version, PATH_IDs, targets/methods, fixture specs, chain/block requirements, procedure, schema/output requirements.

**Reveal after witness output frozen**: exact expected derived hashes/results in `reference-disclosure/`.

Do not make execution impossible merely to achieve blindness.
""",
    )

    # expected structure (no hashes)
    write_json(
        PACK_ROOT / "expected-structure/required-members.json",
        {
            "required_members": [
                "witness-run-metadata.json",
                "frozen-input-verification.json",
                "environment.json",
                "static-reproduction-results.json",
                "runtime-input-results.json",
                "runtime-dispatch-results.json",
                "runtime-execution-results.json",
                "authority-read-results.json",
                "failure-log.json",
                "retry-log.json",
                "evidence-digests.json",
                "witness-attestation.json",
                "witness-receipt.json",
                "manifest.json",
            ],
            "note": "No expected derived result hashes here",
        },
    )

    # reference disclosure (sealed comparison material)
    write(
        PACK_ROOT / "reference-disclosure/README.md",
        """# Reference disclosure (reveal after witness output frozen)

Open only after the witness has frozen their output pack.

Contains comparison/reference material for MATCHED adjudication.
Maintainer dry-run may inspect structurally; that does **not** satisfy Independent Witness.
""",
    )
    write_json(
        PACK_ROOT / "reference-disclosure/sealed-expected-outline.json",
        {
            "policy": "SEMI_BLIND",
            "reveal_after": "witness_output_frozen",
            "compare_classes": [
                "STATIC_REPRODUCTION",
                "RUNTIME_INPUT_REPRODUCTION",
                "RUNTIME_DISPATCH_REPRODUCTION",
                "RUNTIME_EXECUTION_REPRODUCTION",
                "AUTHORITY_READ_REPRODUCTION",
            ],
            "operator_reference_runs": {
                "p0014": {
                    "V-R0": "VR0P14-20260912-101043-DAE3021C",
                    "V-R1": "VR1P14-20260912-105756-3BDE465A",
                    "V-R2": "VR2P14-20260912-111514-D9C9AA04",
                    "V-R3": "VR3P14-20260912-112620-F16EA9AD",
                },
                "p0030": {
                    "V-R0": "VR0P30-20260912-121749-A0C772C8",
                    "V-R1": "VR1P30-20260912-122352-6904D21C",
                },
                "authority": {
                    "CARO": "CARO-20260912-041428-A6BBA9BA",
                    "AUTH_ID": "AUTH-005",
                },
            },
            "note": "Exact expected derived hashes intentionally omitted from pre-run visible surface; witness regenerates evidence.",
        },
    )

    # witness output template — placeholders only
    template_stubs = {
        "witness-run-metadata.json": {
            "run_id": "WITNESS_RUN_ID_PLACEHOLDER",
            "pack_version": PACK_FORMAT_VERSION,
            "witness_handle": "PLACEHOLDER",
            "witness_identity_class": "EXTERNAL_WITNESS_PLACEHOLDER",
            "designated_witness": False,
            "declared_independent": False,
            "status": "NOT_REACHED",
        },
        "environment.json": {
            "os_family": "NOT_REACHED",
            "arch": "NOT_REACHED",
            "python_version": "NOT_REACHED",
            "tool_versions": {},
        },
        "frozen-input-verification.json": {
            "status": "NOT_REACHED",
            "CAW_COMMIT": "",
            "checks": {},
        },
        "static-reproduction-results.json": {"status": "NOT_REACHED", "results": []},
        "runtime-input-results.json": {"status": "NOT_REACHED", "results": []},
        "runtime-dispatch-results.json": {"status": "NOT_REACHED", "results": []},
        "runtime-execution-results.json": {"status": "NOT_REACHED", "results": []},
        "authority-read-results.json": {"status": "NOT_REACHED", "results": []},
        "failure-log.json": {"status": "NOT_REACHED", "entries": []},
        "retry-log.json": {"status": "NOT_REACHED", "entries": []},
        "witness-attestation.json": {"status": "NOT_REACHED"},
        "witness-receipt.json": {"status": "NOT_REACHED"},
        "evidence-digests.json": {"status": "NOT_REACHED", "digests": {}},
        "manifest.json": {"status": "NOT_REACHED", "members": {}},
    }
    for name, obj in template_stubs.items():
        write_json(PACK_ROOT / "witness-output-template" / name, obj)
    write(
        PACK_ROOT / "witness-output-template/README.md",
        "Placeholder template only. Do not treat NOT_REACHED stubs as witness evidence.\n",
    )

    write(
        PACK_ROOT / "verifier/README.md",
        f"""# Verifier entrypoint

Module: `external_verifications/independent-witness-verifier-v0`

```bash
python ../independent_witness_verifier_v0.py <witness_pack.json> [expected_boundary.json]
```

Version: {IW_VERIFIER_VERSION}
""",
    )

    # FROZEN_INPUT_MANIFEST
    frozen_manifest = {"schema_version": "iw-frozen-input-manifest-v0", "files": {}}
    for p in sorted((PACK_ROOT / "frozen-inputs").rglob("*")):
        if p.is_file() and p.name != "FROZEN_INPUT_MANIFEST.json":
            rel = str(p.relative_to(PACK_ROOT / "frozen-inputs")).replace("\\", "/")
            frozen_manifest["files"][rel] = file_sha256(p)
    write_json(PACK_ROOT / "frozen-inputs/FROZEN_INPUT_MANIFEST.json", frozen_manifest)

    # pack-wide file digests
    members = {}
    for p in sorted(PACK_ROOT.rglob("*")):
        if p.is_file():
            rel = str(p.relative_to(PACK_ROOT)).replace("\\", "/")
            members[rel] = file_sha256(p)
    pack_manifest = {
        "schema_version": "iw-pack-manifest-v0",
        "pack_format_version": PACK_FORMAT_VERSION,
        "CAW_COMMIT": FROZEN_CAW_COMMIT,
        "WEAVER_COMMIT_AT_MATERIALIZATION": weaver_commit,
        "WEAVER_TREE_AT_MATERIALIZATION": weaver_tree,
        "IW_VERIFIER_VERSION": IW_VERIFIER_VERSION,
        "members": members,
    }
    pack_manifest["manifest_digest"] = digest({k: v for k, v in pack_manifest.items() if k != "manifest_digest"})
    write_json(PACK_ROOT / "manifests/PACK_MANIFEST.json", pack_manifest)

    # recompute root digest including manifests
    members2 = {}
    for p in sorted(PACK_ROOT.rglob("*")):
        if p.is_file():
            rel = str(p.relative_to(PACK_ROOT)).replace("\\", "/")
            members2[rel] = file_sha256(p)
    root_digest = digest(members2)

    freeze = {
        "PACK_VERSION": PACK_FORMAT_VERSION,
        "PACK_ROOT": str(PACK_ROOT).replace("\\", "/"),
        "PACK_ROOT_DIGEST": root_digest,
        "MANIFEST_DIGEST": pack_manifest["manifest_digest"],
        "CAW_COMMIT": FROZEN_CAW_COMMIT,
        "WEAVER_COMMIT": weaver_commit,
        "WEAVER_TREE": weaver_tree,
        "IW_VERIFIER_VERSION": IW_VERIFIER_VERSION,
        "SCHEMA_VERSIONS": [PACK_SCHEMA, "weaver-independent-witness-verifier-v0"],
        "member_count": len(members2),
        "created_at": now(),
    }
    write_json(PACK_ROOT / "manifests/PACK_FREEZE.json", freeze)

    # structural dry-run pack (maintainer)
    dry_pack = build_minimal_pack(
        witness_run_metadata={
            "run_id": "MAINTAINER-STRUCTURAL-DRY-RUN",
            "pack_version": PACK_FORMAT_VERSION,
            "witness_handle": "maintainer",
            "witness_identity_class": "MAINTAINER_DRY_RUN",
            "designated_witness": False,
            "declared_independent": False,
            "in_progress": False,
        }
    )
    dry_pack["frozen_input_verification"]["WEAVER_COMMIT"] = weaver_commit
    dry_pack["frozen_input_verification"]["WEAVER_TREE"] = weaver_tree
    dry_result = verify_independent_witness_v0(
        {
            "schema_version": "weaver-independent-witness-verifier-v0",
            "independent_witness_pack": dry_pack,
            "expected_frozen_boundary": dry_pack["frozen_input_verification"],
        }
    )
    write_json(PACK_ROOT / "manifests/maintainer-structural-dry-run-result.json", dry_result)

    incomplete = build_minimal_pack()
    incomplete["static_reproduction_results"] = incomplete["static_reproduction_results"][:1]
    from independent_witness_verifier_v0 import digest as dgst

    for key in ("static_reproduction_results",):
        dd = dgst(incomplete[key])
        incomplete["evidence_digests"][key] = dd
        incomplete["manifest"]["members"][key] = dd
    incomplete_result = verify_independent_witness_v0(
        {"schema_version": "weaver-independent-witness-verifier-v0", "independent_witness_pack": incomplete}
    )

    matched_only = build_minimal_pack()
    for axis in matched_only["independence"]["axes"]:
        matched_only["independence"]["axes"][axis] = {"status": "NOT_VERIFIED", "evidence": []}
    matched_result = verify_independent_witness_v0(
        {"schema_version": "weaver-independent-witness-verifier-v0", "independent_witness_pack": matched_only}
    )

    return {
        "freeze": freeze,
        "dry_run": dry_result,
        "incomplete_status": incomplete_result["IW_STATUS"],
        "matched_status": matched_result["IW_STATUS"],
        "git": gi,
    }


if __name__ == "__main__":
    out = materialize()
    print(json.dumps({"ok": True, "freeze": out["freeze"], "dry_IW_STATUS": out["dry_run"]["IW_STATUS"],
                      "dry_independence": out["dry_run"].get("dry_run_independence"),
                      "incomplete": out["incomplete_status"], "matched": out["matched_status"]}, indent=2))
