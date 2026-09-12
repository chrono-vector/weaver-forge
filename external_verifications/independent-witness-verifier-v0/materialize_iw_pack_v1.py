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
PACK_ROOT_RELATIVE = "iw-pack-v1"
SCHEMA_SRC = HERE / "schemas"

# Seal exclusions: never hashed into CONTENT_MANIFEST payload
SEAL_METADATA_NAMES = {
    "manifests/PACK_FREEZE.json",
    "manifests/PACK_SEAL.json",
    "manifests/CONTENT_MANIFEST.json",
    "manifests/PACK_MANIFEST.json",
}
HISTORICAL_RECORD_NAMES = {
    "manifests/maintainer-structural-dry-run-result.json",
}

P0014_FORK_BLOCK = 11685854
P0030_FORK_BLOCK = 11686270
AUTH_REF_BLOCK = int(AUTHORITY_SUBSET["REFERENCE_BLOCK"])


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


def _classify_file(rel: str) -> str:
    if rel in SEAL_METADATA_NAMES:
        return "SEAL_METADATA"
    if rel in HISTORICAL_RECORD_NAMES:
        return "HISTORICAL_RECORD"
    if rel.startswith("reference-disclosure/"):
        return "OUT_OF_SCOPE"  # sealed comparison; not hashed into pre-run CONTENT_MANIFEST payload class as annex-ok
    return "HASHED_PAYLOAD"


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
    creation_run_id = f"IWMAT-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"

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
- PACK_ROOT (relative): `{PACK_ROOT_RELATIVE}`

## Seal model

- `CONTENT_MANIFEST`: hash of reproducibility payload files (HASHED_PAYLOAD)
- `PACK_SEAL`: binds content_manifest_digest + canonical git commit/tree + schema/version pins
- `PACK_ROOT_DIGEST`: digest of sealed metadata model (see PACK_FREEZE / PACK_SEAL)
- Dry-run result is HISTORICAL_RECORD / SEAL_METADATA annex — not hashed into CONTENT_MANIFEST payload

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
Self-declared independence alone is insufficient — external submission receipt required for IW_ACCEPTED.
MAINTAINER_ORIGIN must be != YES.

## How to run

1. Read `instructions/PROCEDURE.md`
2. Verify `frozen-inputs/` digests and toolchain profile
3. Produce outputs into a copy of `witness-output-template/`
4. Do **not** open `reference-disclosure/` until your output pack is frozen
5. Submit pack with external submission receipt for IW verifier adjudication

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
            "selected": {
                "AUTHORITY_ID": AUTHORITY_SUBSET["AUTHORITY_ID"],
                "CONTRACT": AUTHORITY_SUBSET["CONTRACT"],
                "ADDRESS": AUTHORITY_SUBSET["ADDRESS"],
                "READ_METHOD": AUTHORITY_SUBSET["READ_METHOD"],
                "SELECTOR": AUTHORITY_SUBSET["SELECTOR"],
                "CHAIN_ID": AUTHORITY_SUBSET["CHAIN_ID"],
                "REFERENCE_BLOCK": AUTHORITY_SUBSET["REFERENCE_BLOCK"],
            },
            "visible_pre_run": {
                "target": AUTHORITY_SUBSET["ADDRESS"],
                "method": "owner()",
                "chain_id": PRIMARY_CHAIN_ID,
                "block": AUTH_REF_BLOCK,
                "abi_source": "CAW tree at frozen commit / Ownable owner()",
            },
            "expected_owner_policy": "REVEAL_AFTER_FREEZE_IN_reference-disclosure",
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

    # R4 toolchain profile
    write_json(
        PACK_ROOT / "frozen-inputs/toolchain-profile.json",
        {
            "schema_version": "iw-toolchain-profile-v0",
            "scope": "IW_v1_BOUNDED_D_required_tools_only",
            "tools": [
                {
                    "TOOL": "Node",
                    "VERSION_RANGE": "22.0.0 (.nvmrc) / >=18 engines floor",
                    "WHY": "CAW hardhat/ethers if used",
                    "SOURCE_OF_PIN": "CAW .nvmrc 22.0.0 at commit e2074718; engines >=18 if present",
                    "INSTALL_EXPECTATION": "nvm/fnm or system node",
                    "FALLBACK_ALLOWED": "YES→anvil path",
                    "NETWORK_REQUIRED": "NO for install from lock",
                },
                {
                    "TOOL": "npm",
                    "VERSION_RANGE": "lockfile-aligned",
                    "WHY": "CAW deps",
                    "SOURCE_OF_PIN": "CAW package-lock at e2074718",
                    "INSTALL_EXPECTATION": "from CAW tree",
                    "FALLBACK_ALLOWED": "—",
                    "NETWORK_REQUIRED": "optional registry once",
                },
                {
                    "TOOL": "Hardhat",
                    "VERSION_RANGE": "^2.22.18 (CAW package.json)",
                    "WHY": "local fork path (CAW)",
                    "SOURCE_OF_PIN": f"CAW commit {FROZEN_CAW_COMMIT} package.json",
                    "INSTALL_EXPECTATION": "npm from CAW lock",
                    "FALLBACK_ALLOWED": "YES→Anvil/Foundry",
                    "NETWORK_REQUIRED": "fork RPC read-only allowed",
                },
                {
                    "TOOL": "Anvil (Foundry)",
                    "VERSION_RANGE": "Foundry stable",
                    "WHY": "allowed local-fork fallback for IW runtime",
                    "SOURCE_OF_PIN": "toolchain-profile",
                    "INSTALL_EXPECTATION": "foundryup",
                    "FALLBACK_ALLOWED": "YES mutual with Hardhat",
                    "NETWORK_REQUIRED": "fork RPC read-only allowed",
                },
                {
                    "TOOL": "ethers",
                    "VERSION_RANGE": "^6.16.0 (CAW package.json)",
                    "WHY": "encode/eth_call",
                    "SOURCE_OF_PIN": f"CAW commit {FROZEN_CAW_COMMIT} package.json",
                    "INSTALL_EXPECTATION": "npm from CAW lock",
                    "FALLBACK_ALLOWED": "YES→viem/cast among approved",
                    "NETWORK_REQUIRED": "NO",
                },
                {
                    "TOOL": "viem / cast",
                    "VERSION_RANGE": "from CAW lock or Foundry cast",
                    "WHY": "encode/eth_call alternate",
                    "SOURCE_OF_PIN": "CAW lock / foundry",
                    "INSTALL_EXPECTATION": "—",
                    "FALLBACK_ALLOWED": "YES among approved",
                    "NETWORK_REQUIRED": "NO",
                },
                {
                    "TOOL": "Python",
                    "VERSION_RANGE": ">=3.11,<3.15",
                    "WHY": "IW verifier",
                    "SOURCE_OF_PIN": "freeze / IW v1 requirement",
                    "INSTALL_EXPECTATION": "system/venv",
                    "FALLBACK_ALLOWED": "NO",
                    "NETWORK_REQUIRED": "NO",
                },
                {
                    "TOOL": "Git",
                    "VERSION_RANGE": ">=2.40",
                    "WHY": "checkout pins",
                    "SOURCE_OF_PIN": "documented",
                    "INSTALL_EXPECTATION": "system",
                    "FALLBACK_ALLOWED": "NO for commit pin",
                    "NETWORK_REQUIRED": "NO",
                },
                {
                    "TOOL": "CAW package.json + lockfile",
                    "VERSION_RANGE": f"EXTERNAL_FROZEN_PIN at CAW commit {FROZEN_CAW_COMMIT}",
                    "WHY": "deps (hardhat ^2.22.18, ethers ^6.16.0)",
                    "SOURCE_OF_PIN": "CAW commit",
                    "INSTALL_EXPECTATION": "checkout CAW",
                    "FALLBACK_ALLOWED": "NO",
                    "NETWORK_REQUIRED": "NO",
                },
                {
                    "TOOL": "Hardhat config",
                    "VERSION_RANGE": "from CAW tree",
                    "WHY": "if hardhat path",
                    "SOURCE_OF_PIN": "CAW",
                    "INSTALL_EXPECTATION": "—",
                    "FALLBACK_ALLOWED": "—",
                    "NETWORK_REQUIRED": "—",
                },
                {
                    "TOOL": "solc",
                    "VERSION_RANGE": "NOT_REQUIRED if ABI artifacts exist",
                    "WHY": "—",
                    "SOURCE_OF_PIN": "—",
                    "INSTALL_EXPECTATION": "—",
                    "FALLBACK_ALLOWED": "—",
                    "NETWORK_REQUIRED": "—",
                },
            ],
            "caw_freeze_pins": {
                "CAW_COMMIT": FROZEN_CAW_COMMIT,
                "hardhat": "^2.22.18",
                "ethers": "^6.16.0",
                "nvmrc": "22.0.0",
                "python_min": ">=3.11",
                "anvil_foundry": "allowed_fallback_for_local_fork",
            },
        },
    )

    write_json(
        PACK_ROOT / "frozen-inputs/dependency-input-boundary.json",
        {
            "schema_version": "iw-dependency-input-boundary-v0",
            "classifications": [
                {"item": "CAW source tree at frozen commit", "class": "EXTERNAL_FROZEN_PIN"},
                {"item": "CAW package.json + package-lock.json", "class": "EXTERNAL_FROZEN_PIN"},
                {"item": "CAW hardhat ^2.22.18 / ethers ^6.16.0", "class": "EXTERNAL_FROZEN_PIN"},
                {"item": "Weaver IW verifier module", "class": "PACK_MEMBER"},
                {"item": "IW schemas", "class": "PACK_MEMBER"},
                {"item": "fixture-specs", "class": "PACK_MEMBER"},
                {"item": "path-sot comparison references", "class": "PACK_MEMBER"},
                {"item": "procedure inputs", "class": "PACK_MEMBER"},
                {"item": "solc compiler", "class": "NOT_REQUIRED"},
                {"item": "full CAW test suite", "class": "NOT_REQUIRED"},
                {"item": "untracked local modules", "class": "OUT_OF_SCOPE"},
            ],
        },
    )

    write_json(
        PACK_ROOT / "frozen-inputs/external-submission-provenance-schema.json",
        {
            "schema_version": "iw-external-submission-provenance-v0",
            "required_receipt_fields": [
                "SUBMISSION_RECEIPT_ID",
                "SUBMISSION_CHANNEL_CLASS",
                "SUBMISSION_TIMESTAMP",
                "PACK_DIGEST_RECEIVED",
                "OUTPUT_DIGEST_SUBMITTED",
                "SUBMITTER_ROLE",
                "MAINTAINER_ORIGIN",
                "ACCEPTANCE_ELIGIBLE",
            ],
            "acceptance_rules": {
                "MAINTAINER_ORIGIN": "must be != YES",
                "ACCEPTANCE_ELIGIBLE": "must be YES",
                "self_declared_independence": "insufficient without valid external receipt",
            },
        },
    )

    write_json(
        PACK_ROOT / "frozen-inputs/failure-history-policy.json",
        {
            "schema_version": "iw-failure-history-policy-v0",
            "FAILURE_HISTORY_ASSURANCE": "SUBMITTED_HISTORY_PRESERVED",
            "forbidden_claim": "COMPLETE_HISTORY_CRYPTOGRAPHICALLY_PROVEN",
            "ATTEMPT_ID_POLICY": "retain ATTEMPT_ID; PRIOR_ATTEMPT_ID / prior_failure_id on retries; append-only",
            "note": "Later PASS does not erase earlier failure",
        },
    )

    write_json(
        PACK_ROOT / "frozen-inputs/pack-boundary.json",
        {
            "schema_version": "iw-pack-boundary-v0",
            "PACK_ROOT": PACK_ROOT_RELATIVE,
            "PACK_ROOT_NOTE": "ALWAYS relative (iw-pack-v1 or .); never absolute Windows/Unix path",
            "file_classes": ["HASHED_PAYLOAD", "SEAL_METADATA", "HISTORICAL_RECORD", "OUT_OF_SCOPE"],
            "seal_model": {
                "CONTENT_MANIFEST": "hash HASHED_PAYLOAD files excluding seal/dry-run annex",
                "PACK_SEAL": "content_manifest_digest + git commit/tree + versions + CAW commit + creation_run_id",
                "PACK_ROOT_DIGEST": "digest of sealed metadata model in PACK_SEAL/PACK_FREEZE",
            },
            "dry_run_classification": "HISTORICAL_RECORD / SEAL_METADATA annex",
        },
    )

    write_json(
        PACK_ROOT / "frozen-inputs/untracked-exclusion-proof.json",
        {
            "schema_version": "iw-untracked-exclusion-proof-v0",
            "modules": [
                {"path": "local untracked experiments", "class": "OUT_OF_SCOPE", "may_influence_acceptance": False},
                {"path": "CAW working-tree dirty files", "class": "OUT_OF_SCOPE", "may_influence_acceptance": False},
                {"path": "maintainer dry-run annex", "class": "HISTORICAL_RECORD", "may_influence_acceptance": False},
                {"path": "iw-pack-v1 HASHED_PAYLOAD", "class": "PACK_MEMBER", "may_influence_acceptance": True},
            ],
            "note": "Verifier must ignore influence_from_untracked_module / env flags outside sealed pack",
        },
    )

    # path SoT — POST_RUN comparison reference only (no COMPLETE leak)
    write_json(
        PACK_ROOT / "frozen-inputs/path-sot/wrps-v0-p0014.json",
        {
            "PATH_ID": "wrps-v0-p0014",
            "CONTRACT": "CawProfileMarketplace",
            "METHOD": RUNTIME_METHODS["wrps-v0-p0014"],
            "TARGET_ADDRESS": RUNTIME_TARGETS["wrps-v0-p0014"],
            "CHAIN_ID": PRIMARY_CHAIN_ID,
            "ROLE": "POST_RUN_COMPARISON_REFERENCE_ONLY",
            "STATIC_STATUS_REFERENCE": "COMPARISON_ONLY",
            "NOT_PROOF_SOURCE": True,
            "labels": {
                "INPUT_SOURCE": "CAW frozen commit + procedure",
                "DERIVED_BY_WITNESS": "callsite/method/target/ABI/args from CAW + fixture-spec",
                "POST_RUN_COMPARISON": "path-sot reference only after derivation",
            },
            "note": "Witness regenerates static binding from CAW source; path-sot is not sole proof",
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
            "ROLE": "POST_RUN_COMPARISON_REFERENCE_ONLY",
            "STATIC_STATUS_REFERENCE": "COMPARISON_ONLY",
            "NOT_PROOF_SOURCE": True,
            "labels": {
                "INPUT_SOURCE": "CAW frozen commit + procedure",
                "DERIVED_BY_WITNESS": "callsite/method/target/ABI/args from CAW + fixture-spec",
                "POST_RUN_COMPARISON": "path-sot reference only after derivation",
            },
            "note": "Witness regenerates static binding from CAW source; path-sot is not sole proof",
        },
    )

    # fixture specs — concrete deterministic values for encoding; expected hash sealed
    write_json(
        PACK_ROOT / "frozen-inputs/fixture-specs/p0014-createListing.json",
        {
            "PATH_ID": "wrps-v0-p0014",
            "method": RUNTIME_METHODS["wrps-v0-p0014"],
            "target": RUNTIME_TARGETS["wrps-v0-p0014"],
            "abi_hint": "createListing(uint32,uint8,address,uint256,uint256,uint64)",
            "fixture_policy": "Deterministic synthetic fixture for local encoding; not a live listing",
            "fork_block": P0014_FORK_BLOCK,
            "chain_id": PRIMARY_CHAIN_ID,
            "params_template": {
                "profileId": 42,
                "listingType": 0,
                "paymentToken": "0x0000000000000000000000000000000000000000",
                "price": "1000000000000000000",
                "amount": "0",
                "deadline": "86400",
            },
            "ui_inputs_reference": {
                "tokenId": 42,
                "listingType": 0,
                "paymentToken": "0x0000000000000000000000000000000000000000",
                "startPrice": "1.0",
                "durationHours": "24",
            },
            "expected_calldata_sha256": "REVEAL_AFTER_RUN_SEE_reference-disclosure",
            "note": "Do not place expected PASS / success verdict here",
        },
    )
    write_json(
        PACK_ROOT / "frozen-inputs/fixture-specs/p0030-mint.json",
        {
            "PATH_ID": "wrps-v0-p0030",
            "method": RUNTIME_METHODS["wrps-v0-p0030"],
            "target": RUNTIME_TARGETS["wrps-v0-p0030"],
            "selector_hint": "keccak256(mint(address,uint256))[:4] == 0x40c10f19",
            "fork_block": P0030_FORK_BLOCK,
            "chain_id": PRIMARY_CHAIN_ID,
            "params_template": {
                "to": "0x1111111111111111111111111111111111111111",
                "amount": "10000000000000000000000000000",
                "amount_human": "10000000000",
                "parseUnits_decimals": 18,
            },
            "expected_calldata_sha256": "REVEAL_AFTER_RUN_SEE_reference-disclosure",
            "note": "Do not place expected PASS / success verdict here",
        },
    )

    # copy schemas into pack
    for src in SCHEMA_SRC.glob("*.json"):
        shutil.copy2(src, PACK_ROOT / "schemas" / src.name)
        shutil.copy2(src, PACK_ROOT / "frozen-inputs/schemas" / src.name)

    # instructions — full upgraded PROCEDURE
    write(
        PACK_ROOT / "instructions/PROCEDURE.md",
        f"""# IW v1 Procedure (BOUNDED_D)

Bias rule: Do **not** force a PASS. Record honest observations.
Do **not** open `reference-disclosure/` until your witness output pack is frozen.

## STATIC common labels (anti-circularity)

For both static paths:

- **INPUT SOURCE**: CAW frozen commit `{FROZEN_CAW_COMMIT}` (+ Weaver pin in `frozen-inputs/weaver-pin.json`)
- **DERIVED BY WITNESS**: callsite / method / target / ABI / args reconstructed from CAW + fixture-spec
- **POST-RUN COMPARISON**: `frozen-inputs/path-sot/*.json` is a reference-only comparison aid AFTER derivation — **not** a sole proof source and **not** a substitute for witness-derived static results

Path-sot uses `ROLE: POST_RUN_COMPARISON_REFERENCE_ONLY` / `STATIC_STATUS_REFERENCE: COMPARISON_ONLY`.

---

## A. STATIC p0014

- **INPUT SOURCE**: CAW source commit `{FROZEN_CAW_COMMIT}`; Weaver pin; path-id `wrps-v0-p0014`
- **DERIVED BY WITNESS**: verify `CawProfileMarketplace.createListing` binding (target `{RUNTIME_TARGETS["wrps-v0-p0014"]}`, method `{RUNTIME_METHODS["wrps-v0-p0014"]}`, ABI from CAW)
- **OUTPUT**: `static-reproduction-results.json` entry for `wrps-v0-p0014`
- **POST-RUN COMPARISON**: path-sot reference only after derivation
- **SAFETY BOUNDARY**: `NO_NETWORK`

## B. STATIC p0030

- **INPUT SOURCE**: same CAW commit / Weaver pin; path-id `wrps-v0-p0030`
- **DERIVED BY WITNESS**: verify `MintableCaw.mint` binding (target `{RUNTIME_TARGETS["wrps-v0-p0030"]}`, selector `0x40c10f19`, ABI from CAW)
- **OUTPUT**: `static-reproduction-results.json` entry for `wrps-v0-p0030`
- **POST-RUN COMPARISON**: path-sot reference only after derivation
- **SAFETY BOUNDARY**: `NO_NETWORK`

---

## C. p0014 runtime (createListing) — full explicit procedure

Operational constants (encoding / fork pins — **not** a pre-declared must-PASS verdict):

- CAW source commit: `{FROZEN_CAW_COMMIT}`
- Weaver pin: see `frozen-inputs/weaver-pin.json`
- Chain: `{PRIMARY_CHAIN_ID}` (Sepolia)
- Fixed fork block: `{P0014_FORK_BLOCK}`
- Target address: `{RUNTIME_TARGETS["wrps-v0-p0014"]}`
- Method / ABI: `{RUNTIME_METHODS["wrps-v0-p0014"]}` from CAW artifacts
- Deterministic fixture: `frozen-inputs/fixture-specs/p0014-createListing.json` (profileId=42, listingType=0, ETH paymentToken, price=1e18, duration=86400)
- Tooling: **Foundry anvil preferred** (Foundry stable) **OR** Hardhat from CAW lock; document tool + version in environment.json

Steps:

1. Checkout CAW at frozen commit; confirm Weaver pin recorded
2. Load ABI + deterministic fixture; encode calldata locally; record calldata hash (calldata_sha256)
3. Start local fork at fixed block `{P0014_FORK_BLOCK}` (read-only RPC allowed for fork source)
4. Owner resolution for the profile/token under test
5. Impersonation of resolved owner (local only — no real wallet / key / credential)
6. Ownership verification before mutation
7. Approval setup; local approval tx to marketplace (LOCAL_FORK_BOUNDED_MUTATION only)
8. Take snapshot
9. Execute `createListing(...)` on local fork
10. Capture return / event / state observations (honest success OR revert)
11. Snapshot revert; post-revert verification that fork state restored
12. Write raw evidence outputs (runtime-input / dispatch / execution results + evidence digests)
13. Failure recording: append failure-log / retry-log with ATTEMPT_ID / PRIOR_ATTEMPT_ID policy — never delete prior failures

Expected success/revert classification comparison is sealed in `reference-disclosure/` — do not treat fixture-spec as a must-PASS oracle.

**SAFETY**: no live broadcast; REAL_WALLET=NO; REAL_PRIVATE_KEY=NO; LIVE_MUTATION=NO outside local fork.

---

## D. p0030 runtime (mint) — eth_call success shape

Operational constants:

- Target: `{RUNTIME_TARGETS["wrps-v0-p0030"]}`
- ABI: `mint(address,uint256)` / selector `0x40c10f19`
- `parseUnits(amount, 18)` — fixture amount_human `10000000000` → wei in fixture-spec
- Deterministic fixture: `frozen-inputs/fixture-specs/p0030-mint.json`
- Fixed block: `{P0030_FORK_BLOCK}` (from p0030 evidence; authority subset uses `{AUTH_REF_BLOCK}`)
- Fork source: local fork RPC read-only allowed

Steps:

1. Encode mint calldata from fixture; record calldata hash
2. Local fork at fixed block; `eth_call` (LOCAL_FORK_READ_ONLY)
3. Capture raw return / returndata
4. Record runtime input/dispatch/execution results
5. Failure recording as above

Do **not** expose or assume expected PASS verdict before freeze.

---

## E. Authority read-only subset (AUTH-005)

- Visible pre-run: target `{AUTHORITY_SUBSET["ADDRESS"]}`, method `owner()`, chain `{PRIMARY_CHAIN_ID}`, block `{AUTH_REF_BLOCK}`, ABI/source from CAW Ownable
- Action: read-only `eth_call` of `owner()`; record 20-byte address; **do not** claim holder identity
- Expected owner reveal: **only** in `reference-disclosure/` after freeze
- OUTPUT: `authority-read-results.json`
- SAFETY: read-only; no privileged execution

---

## Finalization

Capture environment, failure-log, retry-log, digests, attestation, **external submission receipt**, manifest.
`FAILURE_HISTORY_ASSURANCE` = `SUBMITTED_HISTORY_PRESERVED` (never claim `COMPLETE_HISTORY_CRYPTOGRAPHICALLY_PROVEN`).
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

## External submission receipt (required for IW_ACCEPTED)

Receipt fields: SUBMISSION_RECEIPT_ID, SUBMISSION_CHANNEL_CLASS, SUBMISSION_TIMESTAMP,
PACK_DIGEST_RECEIVED, OUTPUT_DIGEST_SUBMITTED, SUBMITTER_ROLE, MAINTAINER_ORIGIN, ACCEPTANCE_ELIGIBLE.

Rules:

- MAINTAINER_ORIGIN must be != YES
- ACCEPTANCE_ELIGIBLE must be YES
- Digests non-empty and matching
- **Self-declared independence alone is insufficient** without a valid external submission receipt
""",
    )
    write(
        PACK_ROOT / "instructions/FAILURES.md",
        """# Failure handling

Categories: REPRODUCTION_PASS, REPRODUCTION_MISMATCH, ENVIRONMENT_BLOCKED, DEPENDENCY_BLOCKED, RPC_BLOCKED, SOURCE_MISMATCH, RUNTIME_MISMATCH, UNEXPECTED_RESULT, WITNESS_ABORTED.

Rules:

- Failed attempts must not be deleted or silently overwritten
- Retries append to retry-log with prior_failure_id / PRIOR_ATTEMPT_ID
- Later PASS does not erase earlier failure
- ATTEMPT_ID policy: retain identifiers across attempts

## Assurance

- `FAILURE_HISTORY_ASSURANCE` = `SUBMITTED_HISTORY_PRESERVED`
- Never claim `COMPLETE_HISTORY_CRYPTOGRAPHICALLY_PROVEN`
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

**Visible before run**: frozen commit/version, PATH_IDs, targets/methods, fixture specs (encoding inputs), chain/block requirements, procedure, schema/output requirements, toolchain profile.

**Reveal after witness output frozen**: exact expected derived hashes/results and expected owner address in `reference-disclosure/`.

Protected pre-run (must NOT appear in fixture-specs / path-sot):

- Expected PASS / success verdict
- Expected owner address as comparison oracle
- `STATIC_STATUS_REFERENCE: COMPLETE` in path-sot (use COMPARISON_ONLY)

Do not make execution impossible merely to achieve blindness.

External submission: MAINTAINER_ORIGIN != YES; self-declared independence insufficient.
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
            "note": "No expected derived result hashes here; external_submission_receipt required for IW_ACCEPTED",
        },
    )

    # reference disclosure (sealed comparison material)
    write(
        PACK_ROOT / "reference-disclosure/README.md",
        """# Reference disclosure (reveal after witness output frozen)

Open only after the witness has frozen their output pack.

Contains comparison/reference material for MATCHED adjudication, including expected owner for AUTH-005.
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
                    "expected_owner_reveal": "AFTER_FREEZE_ONLY",
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

    # --- Two-level seal: CONTENT_MANIFEST then PACK_SEAL / PACK_FREEZE ---
    # First pass: classify all current files (before seal/dry-run annex exist)
    all_members: dict[str, str] = {}
    file_classes: dict[str, str] = {}
    for p in sorted(PACK_ROOT.rglob("*")):
        if p.is_file():
            rel = str(p.relative_to(PACK_ROOT)).replace("\\", "/")
            all_members[rel] = file_sha256(p)
            file_classes[rel] = _classify_file(rel)

    hashed_payload = {
        rel: digest_val
        for rel, digest_val in all_members.items()
        if file_classes.get(rel) == "HASHED_PAYLOAD"
    }
    content_manifest = {
        "schema_version": "iw-content-manifest-v0",
        "pack_format_version": PACK_FORMAT_VERSION,
        "file_class": "HASHED_PAYLOAD",
        "excludes": sorted(SEAL_METADATA_NAMES | HISTORICAL_RECORD_NAMES),
        "exclude_note": (
            "Seal metadata and maintainer dry-run HISTORICAL_RECORD annex are not hashed into CONTENT_MANIFEST payload"
        ),
        "files": hashed_payload,
        "file_classes_overview": {
            "HASHED_PAYLOAD": "reproducibility payload",
            "SEAL_METADATA": "PACK_FREEZE / PACK_SEAL / CONTENT_MANIFEST / PACK_MANIFEST",
            "HISTORICAL_RECORD": "maintainer structural dry-run result annex",
            "OUT_OF_SCOPE": "reference-disclosure pre-run sealed comparison materials",
        },
    }
    # Treat reference-disclosure as hashed for integrity but documented as comparison annex;
    # R3 says hash reproducibility payload EXCEPT seal files — reference-disclosure stays in payload
    # unless classified OUT_OF_SCOPE. Reclassify OUT_OF_SCOPE out of hashed_payload:
    hashed_payload = {
        rel: digest_val
        for rel, digest_val in all_members.items()
        if _classify_file(rel) == "HASHED_PAYLOAD"
    }
    content_manifest["files"] = hashed_payload
    content_manifest_digest = digest({k: v for k, v in content_manifest.items() if k != "content_manifest_digest"})
    content_manifest["content_manifest_digest"] = content_manifest_digest
    write_json(PACK_ROOT / "manifests/CONTENT_MANIFEST.json", content_manifest)

    pack_seal = {
        "schema_version": "iw-pack-seal-v0",
        "content_manifest_digest": content_manifest_digest,
        "WEAVER_COMMIT": weaver_commit,
        "WEAVER_TREE": weaver_tree,
        "CAW_COMMIT": FROZEN_CAW_COMMIT,
        "IW_VERIFIER_VERSION": IW_VERIFIER_VERSION,
        "PACK_FORMAT_VERSION": PACK_FORMAT_VERSION,
        "PACK_SCHEMA": PACK_SCHEMA,
        "SCHEMA_VERSIONS": [PACK_SCHEMA, "weaver-independent-witness-verifier-v0"],
        "creation_run_id": creation_run_id,
        "PACK_ROOT": PACK_ROOT_RELATIVE,
        "file_class": "SEAL_METADATA",
    }
    pack_seal_digest = digest({k: v for k, v in pack_seal.items() if k != "PACK_SEAL_DIGEST"})
    pack_seal["PACK_SEAL_DIGEST"] = pack_seal_digest
    # PACK_ROOT_DIGEST derived from sealed metadata model
    pack_root_digest = digest(
        {
            "content_manifest_digest": content_manifest_digest,
            "PACK_SEAL_DIGEST": pack_seal_digest,
            "PACK_ROOT": PACK_ROOT_RELATIVE,
            "CAW_COMMIT": FROZEN_CAW_COMMIT,
            "WEAVER_COMMIT": weaver_commit,
            "WEAVER_TREE": weaver_tree,
            "IW_VERIFIER_VERSION": IW_VERIFIER_VERSION,
            "PACK_FORMAT_VERSION": PACK_FORMAT_VERSION,
        }
    )
    pack_seal["PACK_ROOT_DIGEST"] = pack_root_digest
    write_json(PACK_ROOT / "manifests/PACK_SEAL.json", pack_seal)

    # Legacy PACK_MANIFEST retained for compatibility (full file list snapshot)
    members_now: dict[str, str] = {}
    for p in sorted(PACK_ROOT.rglob("*")):
        if p.is_file():
            rel = str(p.relative_to(PACK_ROOT)).replace("\\", "/")
            members_now[rel] = file_sha256(p)
            file_classes[rel] = _classify_file(rel)
    pack_manifest = {
        "schema_version": "iw-pack-manifest-v0",
        "pack_format_version": PACK_FORMAT_VERSION,
        "CAW_COMMIT": FROZEN_CAW_COMMIT,
        "WEAVER_COMMIT_AT_MATERIALIZATION": weaver_commit,
        "WEAVER_TREE_AT_MATERIALIZATION": weaver_tree,
        "IW_VERIFIER_VERSION": IW_VERIFIER_VERSION,
        "CONTENT_MANIFEST_DIGEST": content_manifest_digest,
        "PACK_SEAL_DIGEST": pack_seal_digest,
        "file_classes": file_classes,
        "members": members_now,
    }
    pack_manifest["manifest_digest"] = digest({k: v for k, v in pack_manifest.items() if k != "manifest_digest"})
    write_json(PACK_ROOT / "manifests/PACK_MANIFEST.json", pack_manifest)

    freeze = {
        "PACK_VERSION": PACK_FORMAT_VERSION,
        "PACK_ROOT": PACK_ROOT_RELATIVE,
        "PACK_ROOT_NOTE": "relative path only — never absolute filesystem path",
        "PACK_ROOT_DIGEST": pack_root_digest,
        "CONTENT_MANIFEST_DIGEST": content_manifest_digest,
        "PACK_SEAL_DIGEST": pack_seal_digest,
        "MANIFEST_DIGEST": pack_manifest["manifest_digest"],
        "CAW_COMMIT": FROZEN_CAW_COMMIT,
        "WEAVER_COMMIT": weaver_commit,
        "WEAVER_TREE": weaver_tree,
        "IW_VERIFIER_VERSION": IW_VERIFIER_VERSION,
        "SCHEMA_VERSIONS": [PACK_SCHEMA, "weaver-independent-witness-verifier-v0"],
        "creation_run_id": creation_run_id,
        "file_classes": {
            "HASHED_PAYLOAD": "reproducibility content hashed into CONTENT_MANIFEST",
            "SEAL_METADATA": "CONTENT_MANIFEST / PACK_SEAL / PACK_FREEZE / PACK_MANIFEST",
            "HISTORICAL_RECORD": "maintainer dry-run annex (not in CONTENT_MANIFEST payload)",
            "OUT_OF_SCOPE": "untracked / excluded modules",
        },
        "member_count": len(members_now),
        "created_at": now(),
    }
    write_json(PACK_ROOT / "manifests/PACK_FREEZE.json", freeze)

    # structural dry-run pack (maintainer) — HISTORICAL_RECORD annex
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
    dry_pack["frozen_input_verification"]["CONTENT_MANIFEST_DIGEST"] = content_manifest_digest
    dry_pack["frozen_input_verification"]["PACK_SEAL_DIGEST"] = pack_seal_digest
    dry_result = verify_independent_witness_v0(
        {
            "schema_version": "weaver-independent-witness-verifier-v0",
            "independent_witness_pack": dry_pack,
            "expected_frozen_boundary": dry_pack["frozen_input_verification"],
        }
    )
    dry_result["annex_class"] = "HISTORICAL_RECORD"
    dry_result["seal_role"] = "SEAL_METADATA_ANNEX_NOT_IN_CONTENT_MANIFEST"
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
        "content_manifest_digest": content_manifest_digest,
        "pack_seal_digest": pack_seal_digest,
    }


if __name__ == "__main__":
    out = materialize()
    print(
        json.dumps(
            {
                "ok": True,
                "freeze": out["freeze"],
                "dry_IW_STATUS": out["dry_run"]["IW_STATUS"],
                "dry_independence": out["dry_run"].get("dry_run_independence"),
                "incomplete": out["incomplete_status"],
                "matched": out["matched_status"],
                "PACK_ROOT": out["freeze"]["PACK_ROOT"],
            },
            indent=2,
        )
    )
