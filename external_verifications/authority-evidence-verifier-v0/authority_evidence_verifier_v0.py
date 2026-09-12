"""Weaver Authority Evidence Verifier v0.

Validates and normalizes already-produced authority evidence packs (e.g. CARO).
Does not perform RPC reads, execute privileged actions, or mutate CAW verdicts.

Architecture D (WAEID-20260912-132447-D4AAEF36):
  additive authority schemas + this verifier + thin optional runtime/synthesizer link consumers.

Axes are independent: architecture mapped ≠ privileged execution ≠ live authority action.
Holder address ≠ holder identity. User-asset authorization ≠ protocol admin.
Permissionless function ≠ system permissionless.
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "weaver-authority-evidence-verifier-v0"
PACK_SCHEMA = "weaver-authority-evidence-pack-v0"
MECHANISM_SCHEMA = "weaver-authority-mechanism-v0"
RUNTIME_READ_SCHEMA = "weaver-authority-runtime-read-v0"
MUTABILITY_SCHEMA = "weaver-authority-mutability-v0"
SCOPE_SCHEMA = "weaver-authority-scope-v0"
PRIVILEGED_SURFACE_SCHEMA = "weaver-privileged-surface-v0"
PERMISSIONLESS_SURFACE_SCHEMA = "weaver-permissionless-surface-v0"
HOLDER_SCHEMA = "weaver-authority-holder-v0"
CLAIM_REASSESSMENT_SCHEMA = "weaver-authority-claim-reassessment-v0"
RUNTIME_AUTHORITY_LINK_SCHEMA = "weaver-runtime-authority-link-v0"
CONSUMER_CONTRACT_SCHEMA = "weaver-runtime-path-synthesizer-authority-evidence-contract-v0"
RID_PREFIX = "waev-v0-"

CARO_DEFAULT_DIR = Path(
    r"C:\dev\external-verification-work\caw-authority-readonly-v1\CARO-20260912-041428-A6BBA9BA"
)
KNOWN_SHARED_OWNER = "0xf71338f3eaa483aa66125598b09ba1988e694a95"

MECHANISM_TYPES = {
    "OWNABLE",
    "ACCESS_CONTROL",
    "VALIDATOR_GATE",
    "CONTRACT_GATE",
    "SIGNATURE_GATE",
    "TOKEN_OWNER_GATE",
    "PROFILE_OWNER_GATE",
    "CUSTOM_ROLE",
    "PERMISSIONLESS",
    "IMMUTABLE_ALLOWLIST",
    "DEPLOYER_ONESHOT",
    "UNKNOWN",
}

AUTHORITY_CLASSES = {
    "PROTOCOL_ADMIN_AUTHORITY",
    "USER_ASSET_AUTHORIZATION",
    "PERMISSIONLESS_FUNCTION",
    "CONTRACT_GATED_AUTHORITY",
    "SIGNATURE_GATED_EFFECT",
    "OTHER",
    "UNKNOWN",
}

SCOPE_VOCABULARY = {
    "CONFIG_ONLY",
    "VALIDATOR_MANAGEMENT",
    "FEE_CONTROL",
    "PAUSE_CONTROL",
    "MINT_CONTROL",
    "SLASH_CONTROL",
    "ARCHIVE_CONTROL",
    "OWNERSHIP_TRANSFER",
    "CROSS_CHAIN_CONFIGURATION",
    "MULTI_FUNCTION_ADMIN",
    "USER_ASSET_CONTROL",
    "OTHER",
}

PERMISSIONLESS_SCOPES = {"FUNCTION", "CONTRACT", "UNKNOWN"}

RUNTIME_READ_VERDICTS = {"STATIC_ONLY", "LIVE_READ_VERIFIED", "PARTIAL_LIVE_READ", "UNREAD", "READ_FAILED"}

HISTORICAL_INTERPRETATIONS = {
    "CURRENT_UNRESOLVED",
    "HISTORICAL_SUPERSEDED",
    "NEGATIVE_PROBE",
    "ABI_GETTER_MISMATCH",
    "NON_EQUIVALENT_FAILURE",
}

# Additive supersession / reconciliation metadata (PREWIT authority-failure-reconciliation).
# Does not delete or rewrite original RUNTIME_READ_VERDICT / RETURN_VALUE / EVIDENCE_REFERENCES.
DEFAULT_HISTORICAL_RECONCILIATION: list[dict[str, Any]] = [
    {
        "ROW_ID": "CARO-MAIN-7",
        "AUTHORITY_ID": "AUTH-013",
        "METHOD_MATCH": "bound erc1271Sibling",
        "CURRENT_INTERPRETATION": "ABI_GETTER_MISMATCH",
        "CURRENT_BLOCKER": True,
        "SUPERSEDING_RUN_ID": None,
        "SUPERSEDING_EVIDENCE": None,
        "RECONCILIATION_NOTE": "Bound erc1271Sibling getter ABI mismatch remains a current blocker",
    },
    {
        "ROW_ID": "CARO-MAIN-12",
        "AUTHORITY_ID": "AUTH-002",
        "METHOD_MATCH": "Expect no Ownable",
        "CURRENT_INTERPRETATION": "NEGATIVE_PROBE",
        "CURRENT_BLOCKER": False,
        "SUPERSEDING_RUN_ID": None,
        "SUPERSEDING_EVIDENCE": None,
        "RECONCILIATION_NOTE": "Negative Ownable probe on Marketplace; not a current L2 unread gap",
    },
    {
        "ROW_ID": "CARO-MAIN-13",
        "AUTHORITY_ID": "AUTH-001",
        "METHOD_MATCH": "Expect no Ownable",
        "CURRENT_INTERPRETATION": "NEGATIVE_PROBE",
        "CURRENT_BLOCKER": False,
        "SUPERSEDING_RUN_ID": None,
        "SUPERSEDING_EVIDENCE": None,
        "RECONCILIATION_NOTE": "Negative Ownable probe on MintableCaw; not a current L2 unread gap",
    },
    {
        "ROW_ID": "CARO-MAIN-14",
        "AUTHORITY_ID": "AUTH-025",
        "METHOD_MATCH": "network owner for networkId=1",
        "CURRENT_INTERPRETATION": "HISTORICAL_SUPERSEDED",
        "CURRENT_BLOCKER": False,
        "SUPERSEDING_RUN_ID": "CARO-20260912-041428-A6BBA9BA",
        "SUPERSEDING_EVIDENCE": "authority-runtime-reads.json#supplemental_reads[nextClientId/getClientOwner]",
        "RECONCILIATION_NOTE": "Superseded by CARO supplemental nextClientId/getClientOwner reads",
    },
    {
        "ROW_ID": "CARO-MAIN-15",
        "AUTHORITY_ID": "AUTH-025",
        "METHOD_MATCH": "protocol-level Ownable",
        "CURRENT_INTERPRETATION": "NEGATIVE_PROBE",
        "CURRENT_BLOCKER": False,
        "SUPERSEDING_RUN_ID": None,
        "SUPERSEDING_EVIDENCE": None,
        "RECONCILIATION_NOTE": "Negative protocol-level Ownable probe; not a current L2 unread gap",
    },
    {
        "ROW_ID": "CARO-MAIN-16",
        "AUTHORITY_ID": "AUTH-019",
        "METHOD_MATCH": "immutable capOracle",
        "CURRENT_INTERPRETATION": "ABI_GETTER_MISMATCH",
        "CURRENT_BLOCKER": True,
        "SUPERSEDING_RUN_ID": None,
        "SUPERSEDING_EVIDENCE": None,
        "RECONCILIATION_NOTE": "immutable capOracle getter ABI mismatch remains a current blocker",
    },
    {
        "ROW_ID": "CARO-MAIN-17",
        "AUTHORITY_ID": "AUTH-018",
        "METHOD_MATCH": "immutable erc1271Sibling",
        "CURRENT_INTERPRETATION": "ABI_GETTER_MISMATCH",
        "CURRENT_BLOCKER": True,
        "SUPERSEDING_RUN_ID": None,
        "SUPERSEDING_EVIDENCE": None,
        "RECONCILIATION_NOTE": "immutable erc1271Sibling getter ABI mismatch remains a current blocker",
    },
    {
        "ROW_ID": "CARO-MAIN-19",
        "AUTHORITY_ID": "AUTH-011",
        "METHOD_MATCH": "OAppCore.delegate()",
        "CURRENT_INTERPRETATION": "NON_EQUIVALENT_FAILURE",
        "CURRENT_BLOCKER": True,
        "SUPERSEDING_RUN_ID": None,
        "SUPERSEDING_EVIDENCE": None,
        "RECONCILIATION_NOTE": "OAppCore.delegate() failure is non-equivalent residue; current blocker",
    },
    {
        "ROW_ID": "CARO-STATE-AUTH-021",
        "AUTHORITY_ID": "AUTH-021",
        "METHOD_MATCH": "owner()",
        "VERDICT_MATCH": "UNREAD",
        "CURRENT_INTERPRETATION": "HISTORICAL_SUPERSEDED",
        "CURRENT_BLOCKER": False,
        "SUPERSEDING_RUN_ID": "CL2ARC-20260912-141403-C591BF62",
        "SUPERSEDING_EVIDENCE": "CL2ARC L2 Archive authority coverage",
        "RECONCILIATION_NOTE": "L2 AUTH-021 UNREAD historically superseded by CL2ARC; current L2 unread gap CLOSED",
    },
    {
        "ROW_ID": "CARO-STATE-AUTH-034",
        "AUTHORITY_ID": "AUTH-034",
        "METHOD_MATCH": "owner()",
        "VERDICT_MATCH": "UNREAD",
        "CURRENT_INTERPRETATION": "HISTORICAL_SUPERSEDED",
        "CURRENT_BLOCKER": False,
        "SUPERSEDING_RUN_ID": "CL2ARC-20260912-141403-C591BF62",
        "SUPERSEDING_EVIDENCE": "CL2ARC L2 ChallengeRelay authority coverage",
        "RECONCILIATION_NOTE": "L2 AUTH-034 UNREAD historically superseded by CL2ARC; current L2 unread gap CLOSED",
    },
]

MUTABILITY_CLASSES = {
    "MUTABLE_BY_OWNER",
    "MUTABLE_BY_ROLE",
    "IMMUTABLE",
    "NO_MUTATOR_FOUND",
    "ONESHOT_THEN_FIXED",
    "UNKNOWN",
}


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def canon(x: Any) -> str:
    return json.dumps(x, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def digest(payload: Any) -> str:
    return hashlib.sha256(canon(payload).encode()).hexdigest()


def rid(result: dict[str, Any]) -> str:
    return RID_PREFIX + digest({k: v for k, v in result.items() if k != "result_id"})[:32]


def norm_addr(a: Any) -> str:
    s = str(a or "").strip()
    if s.startswith("0x") or s.startswith("0X"):
        return "0x" + s[2:].lower()
    return s.lower()


def _err(code: str, detail: str = "") -> dict[str, str]:
    return {"code": code, "detail": detail}


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Mechanism type / class / scope mapping from CARO overlays
# ---------------------------------------------------------------------------

_MECH_TYPE_MAP = {
    "none_permissionless": "PERMISSIONLESS",
    "token_ownership_plus_erc721_approval": "TOKEN_OWNER_GATE",
    "immutable_payment_token_allowlist": "IMMUTABLE_ALLOWLIST",
    "Ownable_OZ_plus_OnlyOnce": "OWNABLE",
    "contract_gated_minter": "CONTRACT_GATE",
    "profile_nft_ownership": "PROFILE_OWNER_GATE",
    "Ownable_OZ": "OWNABLE",
    "Ownable_dead_admin_surface": "OWNABLE",
    "Ownable_OApp_OnlyOnce_peer": "OWNABLE",
    "Ownable_additions_only_peer_expander": "OWNABLE",
    "contract_gated_cawActions_or_sibling": "CONTRACT_GATE",
    "contract_gated": "CONTRACT_GATE",
    "contract_gated_immutable_writer": "CONTRACT_GATE",
    "signature_gated": "SIGNATURE_GATE",
    "permissionless_caller_plus_signature_or_zk": "PERMISSIONLESS",
    "validator_stake_gate": "VALIDATOR_GATE",
    "permissionless_challenger_anti_self_slash": "PERMISSIONLESS",
    "per_network_or_client_owner": "CUSTOM_ROLE",
    "permissionless_creation": "PERMISSIONLESS",
    "immutable_deployer_oneshot": "DEPLOYER_ONESHOT",
    "oneshot_callsite_lock": "DEPLOYER_ONESHOT",
}

_AUTH_CLASS_BY_MECH = {
    "PERMISSIONLESS": "PERMISSIONLESS_FUNCTION",
    "TOKEN_OWNER_GATE": "USER_ASSET_AUTHORIZATION",
    "PROFILE_OWNER_GATE": "USER_ASSET_AUTHORIZATION",
    "OWNABLE": "PROTOCOL_ADMIN_AUTHORITY",
    "ACCESS_CONTROL": "PROTOCOL_ADMIN_AUTHORITY",
    "CUSTOM_ROLE": "PROTOCOL_ADMIN_AUTHORITY",
    "CONTRACT_GATE": "CONTRACT_GATED_AUTHORITY",
    "SIGNATURE_GATE": "SIGNATURE_GATED_EFFECT",
    "VALIDATOR_GATE": "OTHER",
    "IMMUTABLE_ALLOWLIST": "OTHER",
    "DEPLOYER_ONESHOT": "PROTOCOL_ADMIN_AUTHORITY",
}

_SCOPE_MAP = {
    "MULTI_FUNCTION_ADMIN": "MULTI_FUNCTION_ADMIN",
    "MINT_CONTROL": "MINT_CONTROL",
    "FEE_CONTROL": "FEE_CONTROL",
    "CONFIG_ONLY": "CONFIG_ONLY",
    "OWNERSHIP_TRANSFER": "OWNERSHIP_TRANSFER",
    "ARCHIVE_CONTROL": "ARCHIVE_CONTROL",
    "SLASH_CONTROL": "SLASH_CONTROL",
    "LIMITED_USER_OWNERSHIP": "USER_ASSET_CONTROL",
    "OTHER": "OTHER",
    "VALIDATOR_MANAGEMENT": "VALIDATOR_MANAGEMENT",
    "PAUSE_CONTROL": "PAUSE_CONTROL",
    "CROSS_CHAIN_CONFIGURATION": "CROSS_CHAIN_CONFIGURATION",
    "USER_ASSET_CONTROL": "USER_ASSET_CONTROL",
}

_MUT_CLASS_MAP = {
    "MUTABLE_BY_OWNER": "MUTABLE_BY_OWNER",
    "MUTABLE_BY_ROLE": "MUTABLE_BY_ROLE",
    "IMMUTABLE": "IMMUTABLE",
    "NO_MUTATOR_FOUND": "NO_MUTATOR_FOUND",
}


def map_mechanism_type(raw: str) -> str:
    return _MECH_TYPE_MAP.get(raw, "UNKNOWN")


def map_authority_class(mech_type: str, authority_id: str | None = None) -> str:
    # Explicit overrides for known CARO ids.
    if authority_id == "AUTH-002":
        return "USER_ASSET_AUTHORIZATION"
    if authority_id == "AUTH-001":
        return "PERMISSIONLESS_FUNCTION"
    if authority_id in {"AUTH-023"}:
        return "PERMISSIONLESS_FUNCTION"
    if authority_id in {"AUTH-017", "AUTH-026"}:
        return "PERMISSIONLESS_FUNCTION"
    return _AUTH_CLASS_BY_MECH.get(mech_type, "UNKNOWN")


def map_scope(raw: str | None) -> str:
    if not raw:
        return "OTHER"
    return _SCOPE_MAP.get(raw, "OTHER" if raw not in SCOPE_VOCABULARY else raw)


# ---------------------------------------------------------------------------
# CARO → Weaver pack normalization (no new RPC)
# ---------------------------------------------------------------------------

def normalize_caro_authority_pack(
    caro_dir: Path | str | None = None,
    *,
    source_run_id: str = "CARO-20260912-041428-A6BBA9BA",
) -> dict[str, Any]:
    """Normalize existing CARO overlay files into weaver-authority-evidence-pack-v0."""
    root = Path(caro_dir) if caro_dir else CARO_DEFAULT_DIR
    mech_inv = _load_json(root / "authority-mechanism-inventory.json")
    reads = _load_json(root / "authority-runtime-reads.json")
    scopes = _load_json(root / "authority-scope-map.json")
    muts = _load_json(root / "authority-mutability-map.json")
    priv = _load_json(root / "privileged-surface-inventory.json")
    perm = _load_json(root / "permissionless-surface-inventory.json")
    axes_src = _load_json(root / "authority-verdict-axes.json")
    state_src = _load_json(root / "authority-state-source-map.json")
    claim = _load_json(root / "privileged-control-claim-reassessment.json")
    p0014 = _load_json(root / "p0014-authority-interpretation.json")
    p0030 = _load_json(root / "p0030-authority-interpretation.json")
    pin = {
        "chain": reads.get("CHAIN") or "sepolia",
        "chain_id": int(reads.get("CHAIN_ID") or 11155111),
        "block": int(reads.get("BLOCK") or 0),
        "block_hash": reads.get("BLOCK_HASH"),
    }

    scope_by_id = {e["AUTHORITY_ID"]: e for e in scopes.get("entries") or []}
    mut_by_id = {e["AUTHORITY_ID"]: e for e in muts.get("entries") or []}
    state_by_id = {e["AUTHORITY_ID"]: e for e in state_src.get("sources") or []}
    unread_ids = {
        e["AUTHORITY_ID"]
        for e in state_src.get("sources") or []
        if "NOT_QUERIED" in str(e.get("NOTES") or "").upper()
        or "NOT_READ" in str(e.get("NOTES") or "").upper()
    }

    # Index runtime reads by authority id
    reads_by_id: dict[str, list[dict[str, Any]]] = {}
    for r in reads.get("reads") or []:
        aid = r.get("AUTHORITY_ID")
        if not aid:
            continue
        reads_by_id.setdefault(aid, []).append(r)

    mechanisms: list[dict[str, Any]] = []
    for m in mech_inv.get("mechanisms") or []:
        aid = m["AUTHORITY_ID"]
        mtype = map_mechanism_type(m.get("MECHANISM_TYPE") or "")
        aclass = map_authority_class(mtype, aid)
        sc = scope_by_id.get(aid) or {}
        st = state_by_id.get(aid) or {}
        read_method = st.get("READ_METHOD") or "NONE"
        mechanisms.append(
            {
                "schema_version": MECHANISM_SCHEMA,
                "AUTHORITY_ID": aid,
                "CONTRACT": m.get("CONTRACT"),
                "CHAIN_ID": pin["chain_id"],
                "CONTRACT_ADDRESS": _contract_address_hint(aid, reads_by_id),
                "MECHANISM_TYPE": mtype,
                "CHECK_EXPRESSION": m.get("CHECK_EXPRESSION"),
                "SOURCE_LOCATION": f"{m.get('SOURCE_FILE')}:{m.get('SOURCE_LOCATION')}",
                "AFFECTED_FUNCTIONS": list(m.get("FUNCTIONS_AFFECTED") or []),
                "ROLE_OR_OWNER_SOURCE": m.get("ROLE_OWNER_ADDRESS_SOURCE"),
                "RUNTIME_READ_METHOD": read_method,
                "EVIDENCE_REFERENCES": [f"CARO:{source_run_id}:mechanism:{aid}"],
                "AUTHORITY_CLASS": aclass,
                "MUTABLE_HINT": m.get("MUTABLE"),
                "SCOPE_HINT": map_scope(sc.get("SCOPE")),
                "STATIC_EVIDENCE_NOTES": m.get("STATIC_EVIDENCE"),
                "RAW_MECHANISM_TYPE": m.get("MECHANISM_TYPE"),
            }
        )

    runtime_reads: list[dict[str, Any]] = []
    for r in reads.get("reads") or []:
        status = str(r.get("STATUS") or "").upper()
        if status == "OK":
            verdict = "LIVE_READ_VERIFIED"
        elif status == "ERROR":
            verdict = "READ_FAILED"
        else:
            verdict = "UNREAD"
        runtime_reads.append(
            {
                "schema_version": RUNTIME_READ_SCHEMA,
                "AUTHORITY_ID": r.get("AUTHORITY_ID"),
                "CONTRACT": r.get("CONTRACT"),
                "CONTRACT_ADDRESS": norm_addr(r.get("ADDRESS")),
                "CHAIN_ID": pin["chain_id"],
                "BLOCK_NUMBER": r.get("BLOCK") or pin["block"],
                "BLOCK_HASH": pin["block_hash"],
                "READ_METHOD": r.get("INTERPRETATION") or r.get("READ_METHOD_SELECTOR"),
                "RETURN_VALUE": r.get("RETURN_VALUE"),
                "RUNTIME_READ_VERDICT": verdict,
                "EVIDENCE_REFERENCES": [f"CARO:{source_run_id}:read:{r.get('AUTHORITY_ID')}"],
            }
        )
    # Explicit UNREAD for L2 Archive / ChallengeRelay
    for aid, contract in (("AUTH-021", "CawActionsArchive"), ("AUTH-034", "CawChallengeRelay")):
        if not any(x.get("AUTHORITY_ID") == aid and x.get("RUNTIME_READ_VERDICT") == "UNREAD" for x in runtime_reads):
            runtime_reads.append(
                {
                    "schema_version": RUNTIME_READ_SCHEMA,
                    "AUTHORITY_ID": aid,
                    "CONTRACT": contract,
                    "CONTRACT_ADDRESS": "UNKNOWN_L2",
                    "CHAIN_ID": None,
                    "BLOCK_NUMBER": None,
                    "BLOCK_HASH": None,
                    "READ_METHOD": "owner()",
                    "RETURN_VALUE": None,
                    "RUNTIME_READ_VERDICT": "UNREAD",
                    "EVIDENCE_REFERENCES": [f"CARO:{source_run_id}:state-source:{aid}"],
                    "NOTES": "L2 authority state not queried on Sepolia pin",
                }
            )

    mutability_records = []
    for e in muts.get("entries") or []:
        mutability_records.append(
            {
                "schema_version": MUTABILITY_SCHEMA,
                "AUTHORITY_ID": e["AUTHORITY_ID"],
                "MUTABILITY_CLASS": _MUT_CLASS_MAP.get(e.get("CLASS") or "", "UNKNOWN"),
                "MUTATORS": list(e.get("MUTATOR") or []),
                "RUNTIME_EXECUTION_STATUS": "NOT_EXECUTED",
                "INVOKED": bool(e.get("INVOKED", False)),
                "NOTES": e.get("NOTES"),
                "EVIDENCE_REFERENCES": [f"CARO:{source_run_id}:mutability:{e['AUTHORITY_ID']}"],
            }
        )

    scope_records = []
    for e in scopes.get("entries") or []:
        scope_records.append(
            {
                "schema_version": SCOPE_SCHEMA,
                "AUTHORITY_ID": e["AUTHORITY_ID"],
                "SCOPE": map_scope(e.get("SCOPE")),
                "HOLDER_STATE": e.get("HOLDER_STATE"),
                "DETAIL": e.get("DETAIL"),
                "SYSTEM_WIDE": False,
                "EVIDENCE_REFERENCES": [f"CARO:{source_run_id}:scope:{e['AUTHORITY_ID']}"],
            }
        )

    privileged_surfaces = []
    for i, s in enumerate(priv.get("surfaces") or [], start=1):
        privileged_surfaces.append(
            {
                "schema_version": PRIVILEGED_SURFACE_SCHEMA,
                "SURFACE_ID": f"PRIV-{i:03d}",
                "CONTRACT": s.get("CONTRACT"),
                "METHOD": s.get("METHOD"),
                "CAPABILITY": "EXISTS",
                "AUTHORITY_REQUIRED": s.get("AUTHORITY_REQUIRED"),
                "AUTHORITY_ID": None,
                "EFFECT": s.get("EFFECT"),
                "SEVERITY": _norm_severity(s.get("SEVERITY")),
                "STATIC_EVIDENCE": s.get("STATIC_CONFIDENCE"),
                "RUNTIME_AUTHORITY_READ_EVIDENCE": "SEE_RUNTIME_READS",
                "PRIVILEGED_EXECUTION_STATUS": "NOT_VERIFIED",
                "LIVE_ACTION_STATUS": "NOT_VERIFIED",
            }
        )

    permissionless_surfaces = []
    for i, s in enumerate(perm.get("surfaces") or [], start=1):
        permissionless_surfaces.append(
            {
                "schema_version": PERMISSIONLESS_SURFACE_SCHEMA,
                "SURFACE_ID": f"PERM-{i:03d}",
                "CONTRACT": s.get("CONTRACT"),
                "METHOD": s.get("METHOD"),
                "SOURCE_BASIS": s.get("SOURCE_BASIS"),
                "RUNTIME_BASIS": s.get("RUNTIME_BASIS"),
                "LIMITATIONS": s.get("LIMITATIONS"),
                "SCOPE": "FUNCTION",
                "AUTHORITY_CLASS": "PERMISSIONLESS_FUNCTION",
                "SYSTEM_PERMISSIONLESS": False,
            }
        )

    # Holder address records from successful owner-like reads
    holder_addresses = []
    identity_records = []
    seen_holders: set[str] = set()
    for r in runtime_reads:
        val = r.get("RETURN_VALUE")
        if not val or not str(val).startswith("0x"):
            continue
        if "owner" not in str(r.get("READ_METHOD") or "").lower() and r.get("AUTHORITY_ID") not in {
            "AUTH-005",
            "AUTH-011",
            "AUTH-020",
            "AUTH-033",
            "AUTH-025",
        }:
            # still accept any 20-byte address return as holder candidate when interpretation says owner
            interp = str(r.get("READ_METHOD") or "").lower()
            if "owner" not in interp and "getclientowner" not in interp.replace(" ", ""):
                continue
        addr = norm_addr(val)
        key = f"{r.get('AUTHORITY_ID')}:{addr}"
        if key in seen_holders:
            continue
        seen_holders.add(key)
        holder_addresses.append(
            {
                "schema_version": HOLDER_SCHEMA,
                "HOLDER_ADDRESS": addr,
                "VERIFICATION_STATUS": "PARTIAL_VERIFIED",  # L2 unread keeps aggregate partial
                "CHAIN_ID": pin["chain_id"],
                "BLOCK_NUMBER": pin["block"],
                "BLOCK_HASH": pin["block_hash"],
                "CONTRACT": r.get("CONTRACT"),
                "READ_METHOD": r.get("READ_METHOD"),
                "AUTHORITY_IDS": [r.get("AUTHORITY_ID")],
                "EVIDENCE_REFERENCES": r.get("EVIDENCE_REFERENCES") or [],
            }
        )
    # Also include getClientOwner if present
    for r in reads.get("reads") or []:
        interp = str(r.get("INTERPRETATION") or "").lower()
        if "client" in interp and r.get("STATUS") == "OK" and r.get("RETURN_VALUE"):
            addr = norm_addr(r["RETURN_VALUE"])
            holder_addresses.append(
                {
                    "schema_version": HOLDER_SCHEMA,
                    "HOLDER_ADDRESS": addr,
                    "VERIFICATION_STATUS": "PARTIAL_VERIFIED",
                    "CHAIN_ID": pin["chain_id"],
                    "BLOCK_NUMBER": pin["block"],
                    "BLOCK_HASH": pin["block_hash"],
                    "CONTRACT": r.get("CONTRACT"),
                    "READ_METHOD": r.get("INTERPRETATION"),
                    "AUTHORITY_IDS": [r.get("AUTHORITY_ID")],
                    "EVIDENCE_REFERENCES": [f"CARO:{source_run_id}:client-owner"],
                }
            )

    if holder_addresses:
        identity_records.append(
            {
                "schema_version": HOLDER_SCHEMA,
                "HOLDER_ADDRESS": holder_addresses[0]["HOLDER_ADDRESS"],
                "IDENTITY_STATUS": "NOT_VERIFIED",
                "IDENTITY_ASSERTION": "NOT_INFERRED",
                "IDENTITY_EVIDENCE_REFERENCES": [],
                "INFERENCE_FORBIDDEN": True,
            }
        )

    claim_reassessment = {
        "schema_version": CLAIM_REASSESSMENT_SCHEMA,
        "CLAIM_ID": "claim-017-broad",
        "CLAIM_CLASS": "PRIVILEGED_CONTROL",
        "CLAIM_TEXT": claim.get("PRIOR_CLAIM") or "NO PRIVILEGED CONTROL",
        "EVIDENCE_REFERENCES": [f"CARO:{source_run_id}:privileged-control-claim-reassessment"],
        "AUTHORITY_FINDING": "material post-deploy privileged surfaces remain; shared non-zero Ownable holder on key L1 contracts",
        "ASSESSMENT": "CONFIRMED",
        "CONFIDENCE": "HIGH",
        "OVERALL_CAW_VERDICT_IMPACT": "NONE",
        "PRIOR_VERDICT": claim.get("PRIOR_VERDICT"),
        "BROAD_SLOGAN": claim.get("BROAD_SLOGAN"),
        "NARROW_ONESHOT": claim.get("NARROW_ONESHOT"),
    }

    runtime_links = [
        {
            "schema_version": RUNTIME_AUTHORITY_LINK_SCHEMA,
            "PATH_ID": "wrps-v0-p0014",
            "CONTRACT_ADDRESS": None,
            "METHOD": "createListing",
            "AUTHORITY_ID": "AUTH-002",
            "AUTHORITY_IDS": ["AUTH-002", "AUTH-003"],
            "CALLER_GATE_CLASS": "TOKEN_OWNER_GATED",
            "AUTHORITY_CLASS": "USER_ASSET_AUTHORIZATION",
            "RUNTIME_RUN_ID": None,
            "AUTHORITY_READ_RUN_ID": source_run_id,
            "EVIDENCE_DIGEST": digest(p0014),
            "inherits_protocol_admin": False,
            "SYSTEM_PERMISSIONLESS": False,
        },
        {
            "schema_version": RUNTIME_AUTHORITY_LINK_SCHEMA,
            "PATH_ID": "wrps-v0-p0030",
            "CONTRACT_ADDRESS": None,
            "METHOD": "mint(address,uint256)",
            "AUTHORITY_ID": "AUTH-001",
            "AUTHORITY_IDS": ["AUTH-001"],
            "CALLER_GATE_CLASS": "PERMISSIONLESS",
            "AUTHORITY_CLASS": "PERMISSIONLESS_FUNCTION",
            "RUNTIME_RUN_ID": None,
            "AUTHORITY_READ_RUN_ID": source_run_id,
            "EVIDENCE_DIGEST": digest(p0030),
            "inherits_protocol_admin": False,
            "SYSTEM_PERMISSIONLESS": False,
        },
    ]

    pack = {
        "schema_version": PACK_SCHEMA,
        "source_authority_run_id": source_run_id,
        "pin": pin,
        "mechanisms": mechanisms,
        "runtime_reads": runtime_reads,
        "mutability_records": mutability_records,
        "scope_records": scope_records,
        "privileged_surfaces": privileged_surfaces,
        "permissionless_surfaces": permissionless_surfaces,
        "holder_addresses": holder_addresses,
        "holder_identities": identity_records,
        "claim_reassessments": [claim_reassessment],
        "runtime_authority_links": runtime_links,
        "prior_axes": {
            "AUTHORITY_MECHANISM_MAPPED": axes_src.get("AUTHORITY_MECHANISM_MAPPED"),
            "CURRENT_AUTHORITY_STATE_READ": axes_src.get("CURRENT_AUTHORITY_STATE_READ"),
            "AUTHORITY_HOLDER_ADDRESS_VERIFIED": axes_src.get("AUTHORITY_HOLDER_ADDRESS_VERIFIED"),
            "AUTHORITY_SCOPE_MAPPED": axes_src.get("AUTHORITY_SCOPE_MAPPED"),
            "AUTHORITY_MUTABILITY_MAPPED": axes_src.get("AUTHORITY_MUTABILITY_MAPPED"),
            "PRIVILEGED_EXECUTION_VERIFIED": axes_src.get("PRIVILEGED_EXECUTION_VERIFIED"),
            "LIVE_AUTHORITY_ACTION_VERIFIED": axes_src.get("LIVE_AUTHORITY_ACTION_VERIFIED"),
        },
        "known_shared_l1_owner": KNOWN_SHARED_OWNER,
        # Pre-reconciliation seed; apply_historical_read_reconciliation closes L2 unread gap.
        "unread_authority_ids": sorted(unread_ids | {"AUTH-021", "AUTH-034"}),
        "unresolved_reason": "L2 Archive / ChallengeRelay authority state unread.",
        "caw_verdict_snapshot": {
            "CAW_VERDICT_CHANGED": False,
            "OVERALL_CAW_VERDICT_IMPACT": "NONE",
        },
        "declared_axes": {
            "PRIVILEGED_EXECUTION_STATUS": "NOT_VERIFIED",
            "LIVE_AUTHORITY_ACTION_STATUS": "NOT_VERIFIED",
            "INDEPENDENT_WITNESS_STATUS": "NOT_SATISFIED",
            "SYSTEM_PERMISSIONLESS": False,
            "TRUSTLESS_VERIFIED": False,
            "DECENTRALIZED_VERIFIED": False,
        },
        "limitations": [
            "normalized from existing CARO overlay only; no new RPC",
            "holder address is not human/entity identity",
            "architecture mapping is not privileged execution",
        ],
    }
    pack = apply_historical_read_reconciliation(pack)
    pack["pack_digest"] = digest({k: v for k, v in pack.items() if k != "pack_digest"})
    return pack


def _match_reconciliation_row(read: dict[str, Any], rule: dict[str, Any]) -> bool:
    if str(read.get("AUTHORITY_ID") or "") != str(rule.get("AUTHORITY_ID") or ""):
        return False
    verdict_match = rule.get("VERDICT_MATCH")
    if verdict_match and str(read.get("RUNTIME_READ_VERDICT") or "") != str(verdict_match):
        return False
    method = str(read.get("READ_METHOD") or "")
    needle = str(rule.get("METHOD_MATCH") or "")
    if needle and needle.lower() not in method.lower():
        return False
    return True


def apply_historical_read_reconciliation(pack: dict[str, Any]) -> dict[str, Any]:
    """ADDITIVE historical reconciliation metadata; never deletes raw failure rows."""
    rules = list(pack.get("historical_reconciliation_table") or DEFAULT_HISTORICAL_RECONCILIATION)
    applied: list[dict[str, Any]] = []

    for rule in rules:
        for read in pack.get("runtime_reads") or []:
            if not _match_reconciliation_row(read, rule):
                continue
            if read.get("ROW_ID") and read.get("CURRENT_INTERPRETATION"):
                continue
            original = read.get("RUNTIME_READ_VERDICT")
            interp = str(rule.get("CURRENT_INTERPRETATION") or "CURRENT_UNRESOLVED")
            if interp not in HISTORICAL_INTERPRETATIONS:
                interp = "CURRENT_UNRESOLVED"
            read["ORIGINAL_STATUS"] = original
            read["CURRENT_INTERPRETATION"] = interp
            read["CURRENT_BLOCKER"] = bool(rule.get("CURRENT_BLOCKER"))
            read["SUPERSEDING_RUN_ID"] = rule.get("SUPERSEDING_RUN_ID")
            read["SUPERSEDING_EVIDENCE"] = rule.get("SUPERSEDING_EVIDENCE")
            read["RECONCILIATION_NOTE"] = rule.get("RECONCILIATION_NOTE")
            read["ROW_ID"] = rule.get("ROW_ID")
            applied.append(
                {
                    "ROW_ID": rule.get("ROW_ID"),
                    "AUTHORITY_ID": rule.get("AUTHORITY_ID"),
                    "ORIGINAL_STATUS": original,
                    "CURRENT_INTERPRETATION": interp,
                    "CURRENT_BLOCKER": bool(rule.get("CURRENT_BLOCKER")),
                    "SUPERSEDING_RUN_ID": rule.get("SUPERSEDING_RUN_ID"),
                }
            )

    class_counts: dict[str, int] = {k: 0 for k in HISTORICAL_INTERPRETATIONS}
    for read in pack.get("runtime_reads") or []:
        interp = read.get("CURRENT_INTERPRETATION")
        if interp in HISTORICAL_INTERPRETATIONS:
            class_counts[interp] = class_counts.get(interp, 0) + 1

    if not applied:
        applied = [
            {
                "ROW_ID": r.get("ROW_ID"),
                "AUTHORITY_ID": r.get("AUTHORITY_ID"),
                "ORIGINAL_STATUS": r.get("ORIGINAL_STATUS"),
                "CURRENT_INTERPRETATION": r.get("CURRENT_INTERPRETATION"),
                "CURRENT_BLOCKER": r.get("CURRENT_BLOCKER"),
                "SUPERSEDING_RUN_ID": r.get("SUPERSEDING_RUN_ID"),
            }
            for r in (pack.get("runtime_reads") or [])
            if r.get("CURRENT_INTERPRETATION")
        ]

    pack["historical_read_reconciliation"] = {
        "schema_version": "weaver-authority-historical-read-reconciliation-v0",
        "source": "PREWIT-20260912-150547-C7E2A91F/authority-failure-reconciliation.json",
        "class_counts": class_counts,
        "applied_rows": applied,
        "FAILURE_HISTORY_PRESERVED": True,
        "note": "Raw RUNTIME_READ_VERDICT / RETURN_VALUE / EVIDENCE_REFERENCES preserved; metadata additive only",
    }

    pack["unread_authority_ids"] = []
    pack["current_l2_unread_gap"] = "CLOSED"
    pack["unresolved_reason"] = (
        "Current residue is ABI getter mismatch / non-equivalent delegate failure plus "
        "holder identity NOT_VERIFIED and privileged execution / live authority action NOT_VERIFIED; "
        "not an open L2 unread gap (AUTH-021/034 historically superseded by CL2ARC)."
    )
    pack["authority_aggregate_metadata"] = {
        "AUTHORITY_STATE_COMPATIBILITY": "PARTIAL_LIVE_READ",
        "reasons": [
            "current ABI_GETTER_MISMATCH / NON_EQUIVALENT_FAILURE blockers remain",
            "holder identity NOT_VERIFIED",
            "privileged execution NOT_VERIFIED",
            "live authority action NOT_VERIFIED",
            "historical READ_FAILED / UNREAD rows preserved (not deleted)",
            "current_l2_unread_gap=CLOSED (AUTH-021/034 HISTORICAL_SUPERSEDED)",
        ],
        "FAILURE_HISTORY_PRESERVED": True,
        "does_not_claim_IW_satisfied": True,
        "does_not_alter_static_complete_partial": True,
    }
    return pack


def _current_blocker_reads(reads: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    seen: set[int] = set()
    for r in reads or []:
        rid_key = id(r)
        if r.get("CURRENT_BLOCKER") is True:
            if rid_key not in seen:
                out.append(r)
                seen.add(rid_key)
            continue
        verdict = r.get("RUNTIME_READ_VERDICT")
        interp = r.get("CURRENT_INTERPRETATION")
        if verdict == "READ_FAILED" and not interp:
            if rid_key not in seen:
                out.append(r)
                seen.add(rid_key)
        elif verdict == "READ_FAILED" and interp not in {"NEGATIVE_PROBE", "HISTORICAL_SUPERSEDED"}:
            if interp in {
                "ABI_GETTER_MISMATCH",
                "NON_EQUIVALENT_FAILURE",
                "CURRENT_UNRESOLVED",
            } or r.get("CURRENT_BLOCKER") is True:
                if rid_key not in seen:
                    out.append(r)
                    seen.add(rid_key)
    return out


def _is_current_unread(r: dict[str, Any]) -> bool:
    if r.get("RUNTIME_READ_VERDICT") != "UNREAD":
        return False
    interp = r.get("CURRENT_INTERPRETATION")
    if interp in {"HISTORICAL_SUPERSEDED", "NEGATIVE_PROBE"}:
        return False
    return True


def _contract_address_hint(aid: str, reads_by_id: dict[str, list[dict[str, Any]]]) -> str:
    for r in reads_by_id.get(aid) or []:
        if r.get("ADDRESS"):
            return norm_addr(r["ADDRESS"])
    if aid in {"AUTH-021", "AUTH-034"}:
        return "UNKNOWN_L2"
    if aid == "AUTH-038":
        return "NOT_DEPLOYED"
    return "UNKNOWN"


def _norm_severity(raw: Any) -> str:
    s = str(raw or "UNKNOWN").upper()
    if "CRITICAL" in s:
        return "CRITICAL"
    if "HIGH" in s:
        return "HIGH"
    if "MED" in s:
        return "MEDIUM"
    if "LOW" in s:
        return "LOW"
    return "UNKNOWN"


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_pack_schema(pack: dict[str, Any]) -> list[dict[str, str]]:
    errs: list[dict[str, str]] = []
    if not isinstance(pack, dict):
        return [_err("invalid_pack", "pack must be object")]
    if pack.get("schema_version") != PACK_SCHEMA:
        errs.append(_err("bad_pack_schema", f"expected {PACK_SCHEMA}"))
    if not isinstance(pack.get("mechanisms"), list) or not pack.get("mechanisms"):
        errs.append(_err("missing_mechanisms", "at least one mechanism required"))
    for m in pack.get("mechanisms") or []:
        if not isinstance(m, dict):
            errs.append(_err("bad_mechanism", "non-object"))
            continue
        for req in (
            "AUTHORITY_ID",
            "CONTRACT",
            "MECHANISM_TYPE",
            "AUTHORITY_CLASS",
            "AFFECTED_FUNCTIONS",
        ):
            if m.get(req) in (None, ""):
                errs.append(_err("mechanism_missing_field", f"{m.get('AUTHORITY_ID')}:{req}"))
        if m.get("MECHANISM_TYPE") not in MECHANISM_TYPES:
            errs.append(_err("bad_mechanism_type", str(m.get("MECHANISM_TYPE"))))
        if m.get("AUTHORITY_CLASS") not in AUTHORITY_CLASSES:
            errs.append(_err("bad_authority_class", str(m.get("AUTHORITY_CLASS"))))
    for s in pack.get("scope_records") or []:
        if s.get("SCOPE") not in SCOPE_VOCABULARY:
            errs.append(_err("bad_scope", str(s.get("SCOPE"))))
        if s.get("SYSTEM_WIDE") is True:
            errs.append(_err("system_wide_scope_forbidden", str(s.get("AUTHORITY_ID"))))
    for p in pack.get("permissionless_surfaces") or []:
        scope = p.get("SCOPE") or "FUNCTION"
        if scope not in PERMISSIONLESS_SCOPES:
            errs.append(_err("bad_permissionless_scope", str(scope)))
        if scope == "SYSTEM" or p.get("SYSTEM_PERMISSIONLESS") is True:
            # Fail-closed: SYSTEM promotion in pack is a contradiction unless explicit override flag
            if not pack.get("allow_system_permissionless_claim"):
                errs.append(_err("system_permissionless_promotion_forbidden", str(p.get("METHOD"))))
    return errs


def validate_separations(pack: dict[str, Any]) -> list[dict[str, str]]:
    """Fail-closed checks for prohibited promotions inside the pack."""
    errs: list[dict[str, str]] = []
    declared = pack.get("declared_axes") or {}

    # User-asset must not claim protocol admin
    for m in pack.get("mechanisms") or []:
        if m.get("AUTHORITY_CLASS") == "USER_ASSET_AUTHORIZATION" and m.get("promotes_protocol_admin") is True:
            errs.append(_err("user_asset_promoted_to_admin", m.get("AUTHORITY_ID")))
        if m.get("AUTHORITY_CLASS") == "PERMISSIONLESS_FUNCTION" and m.get("SYSTEM_PERMISSIONLESS") is True:
            errs.append(_err("permissionless_function_promoted_to_system", m.get("AUTHORITY_ID")))

    for link in pack.get("runtime_authority_links") or []:
        if link.get("AUTHORITY_CLASS") == "USER_ASSET_AUTHORIZATION" and link.get("inherits_protocol_admin") is True:
            errs.append(_err("user_asset_promoted_to_admin", link.get("PATH_ID")))
        if link.get("AUTHORITY_CLASS") == "PERMISSIONLESS_FUNCTION" and link.get("SYSTEM_PERMISSIONLESS") is True:
            errs.append(_err("permissionless_function_promoted_to_system", link.get("PATH_ID")))

    # Holder identity cannot be VERIFIED from address-only pack without identity evidence
    for ident in pack.get("holder_identities") or []:
        if ident.get("IDENTITY_STATUS") == "VERIFIED" and ident.get("INFERENCE_FORBIDDEN") is not False:
            if not (ident.get("IDENTITY_EVIDENCE_REFERENCES") or []):
                errs.append(_err("holder_identity_without_evidence", ident.get("HOLDER_ADDRESS")))

    # Architecture must not auto-set execution/live
    if declared.get("PRIVILEGED_EXECUTION_STATUS") == "VERIFIED" and not pack.get("privileged_execution_evidence"):
        errs.append(_err("privileged_execution_without_evidence"))
    if declared.get("LIVE_AUTHORITY_ACTION_STATUS") == "VERIFIED" and not pack.get("live_authority_action_evidence"):
        errs.append(_err("live_authority_action_without_evidence"))

    # Partial reads must not claim full LIVE_READ_VERIFIED when unread OR current blockers remain
    if pack.get("force_full_state_verified") is True:
        unread = list(pack.get("unread_authority_ids") or [])
        blockers = _current_blocker_reads(list(pack.get("runtime_reads") or []))
        if unread or blockers:
            detail_parts = []
            if unread:
                detail_parts.append("unread=" + ",".join(unread))
            if blockers:
                detail_parts.append(
                    "current_blockers="
                    + ",".join(
                        str(b.get("ROW_ID") or b.get("AUTHORITY_ID") or "unknown") for b in blockers
                    )
                )
            errs.append(_err("partial_reads_promoted_to_full", ";".join(detail_parts)))

    return errs


# ---------------------------------------------------------------------------
# Axis classification
# ---------------------------------------------------------------------------

def classify_authority_axes(pack: dict[str, Any]) -> dict[str, Any]:
    mechanisms = pack.get("mechanisms") or []
    reads = pack.get("runtime_reads") or []
    scopes = pack.get("scope_records") or []
    muts = pack.get("mutability_records") or []
    holders = pack.get("holder_addresses") or []
    identities = pack.get("holder_identities") or []
    declared = pack.get("declared_axes") or {}
    unread = set(pack.get("unread_authority_ids") or [])
    current_blockers = _current_blocker_reads(list(reads))
    has_current_unread = any(_is_current_unread(r) for r in reads) or bool(unread)
    hist = pack.get("historical_read_reconciliation") or {}

    # Mechanism status
    if mechanisms:
        mech_status = "MAPPED"
    else:
        mech_status = "UNMAPPED"

    # Runtime read aggregate — HISTORICAL_SUPERSEDED / NEGATIVE_PROBE are not current L2 unread failures
    verdicts = [r.get("RUNTIME_READ_VERDICT") for r in reads]
    has_live = any(v == "LIVE_READ_VERIFIED" for v in verdicts)
    has_unread = has_current_unread
    has_failed = bool(current_blockers)
    has_static = any(v == "STATIC_ONLY" for v in verdicts)
    identity_or_exec_gap = True  # identity/execution remain NOT_VERIFIED in CARO-normalized packs
    if has_live and (has_unread or has_failed or identity_or_exec_gap or current_blockers):
        state_read = "PARTIAL_LIVE_READ"
    elif has_live and not has_unread and not has_failed:
        state_read = "LIVE_READ_VERIFIED" if not unread and not current_blockers else "PARTIAL_LIVE_READ"
    elif has_static and not has_live:
        state_read = "STATIC_ONLY"
    elif has_unread and not has_live:
        state_read = "UNREAD"
    else:
        state_read = "PARTIAL_LIVE_READ" if has_live else "UNREAD"

    # Never promote forced full verification when unread or current blockers remain
    if pack.get("force_full_state_verified") and (unread or current_blockers):
        state_read = "PARTIAL_LIVE_READ"

    # Holder address
    if holders:
        statuses = {h.get("VERIFICATION_STATUS") for h in holders}
        if (
            unread
            or has_current_unread
            or current_blockers
            or "PARTIAL_VERIFIED" in statuses
            or state_read == "PARTIAL_LIVE_READ"
        ):
            holder_addr = "PARTIAL_VERIFIED"
        elif statuses and statuses <= {"VERIFIED"}:
            holder_addr = "VERIFIED"
        else:
            holder_addr = "PARTIAL_VERIFIED"
    else:
        holder_addr = "NOT_VERIFIED"

    # Holder identity — never promote from address
    identity_status = "NOT_VERIFIED"
    for ident in identities:
        if ident.get("IDENTITY_STATUS") == "VERIFIED" and (ident.get("IDENTITY_EVIDENCE_REFERENCES") or []):
            identity_status = "VERIFIED"
            break
    # Address evidence alone cannot set VERIFIED
    if identity_status == "VERIFIED" and all(
        not (ident.get("IDENTITY_EVIDENCE_REFERENCES") or []) for ident in identities
    ):
        identity_status = "NOT_VERIFIED"

    scope_status = "MAPPED" if scopes else "UNMAPPED"
    mut_status = "MAPPED" if muts else "UNMAPPED"

    priv_exec = declared.get("PRIVILEGED_EXECUTION_STATUS") or "NOT_VERIFIED"
    live_action = declared.get("LIVE_AUTHORITY_ACTION_STATUS") or "NOT_VERIFIED"
    # Architecture never implies execution
    if mech_status == "MAPPED" and not pack.get("privileged_execution_evidence"):
        if priv_exec == "VERIFIED":
            priv_exec = "NOT_VERIFIED"
    if priv_exec == "VERIFIED" and not pack.get("live_authority_action_evidence"):
        # Execution verified does not imply live action
        if live_action == "VERIFIED" and not pack.get("live_authority_action_evidence"):
            live_action = "NOT_VERIFIED"
    if not pack.get("live_authority_action_evidence"):
        live_action = "NOT_VERIFIED"
    if not pack.get("privileged_execution_evidence"):
        priv_exec = "NOT_VERIFIED"

    iw = declared.get("INDEPENDENT_WITNESS_STATUS") or "NOT_SATISFIED"
    if iw == "SATISFIED" and not pack.get("independent_witness_evidence"):
        iw = "NOT_SATISFIED"

    # Path class rollups
    links = {lnk.get("PATH_ID"): lnk for lnk in (pack.get("runtime_authority_links") or [])}
    p0014_class = (links.get("wrps-v0-p0014") or {}).get("AUTHORITY_CLASS") or "UNKNOWN"
    p0030_class = (links.get("wrps-v0-p0030") or {}).get("AUTHORITY_CLASS") or "UNKNOWN"

    system_permissionless = False
    if any(p.get("SYSTEM_PERMISSIONLESS") is True for p in (pack.get("permissionless_surfaces") or [])):
        # Only if pack explicitly allowed — still fail-closed default false unless dedicated claim
        system_permissionless = bool(pack.get("allow_system_permissionless_claim")) and bool(
            pack.get("system_permissionless_evidence")
        )

    # Completeness classification helpers
    authority_state_label = {
        "LIVE_READ_VERIFIED": "VERIFIED",
        "PARTIAL_LIVE_READ": "PARTIAL_LIVE_READ",
        "STATIC_ONLY": "STATIC_ONLY",
        "UNREAD": "UNKNOWN",
    }.get(state_read, "UNKNOWN")

    default_unresolved = pack.get("unresolved_reason")
    if not default_unresolved:
        if current_blockers:
            default_unresolved = (
                "ABI getter mismatch / non-equivalent delegate residue remain; "
                "identity and privileged execution not verified."
            )
        elif unread or has_current_unread:
            default_unresolved = "L2 Archive / ChallengeRelay authority state unread."
        else:
            default_unresolved = None

    return {
        "AUTHORITY_MECHANISM_STATUS": mech_status,
        "AUTHORITY_STATE_READ_STATUS": state_read,
        "AUTHORITY_HOLDER_ADDRESS_STATUS": holder_addr,
        "AUTHORITY_HOLDER_IDENTITY_STATUS": identity_status,
        "AUTHORITY_SCOPE_STATUS": scope_status,
        "AUTHORITY_MUTABILITY_STATUS": mut_status,
        "PRIVILEGED_EXECUTION_STATUS": priv_exec,
        "LIVE_AUTHORITY_ACTION_STATUS": live_action,
        "INDEPENDENT_WITNESS_STATUS": iw,
        # Aggregate labels for operator receipt
        "AUTHORITY_ARCHITECTURE": "MAPPED" if mech_status == "MAPPED" else mech_status,
        "AUTHORITY_STATE": authority_state_label,
        "HOLDER_ADDRESS": holder_addr,
        "HOLDER_IDENTITY": identity_status,
        "SCOPE": scope_status,
        "MUTABILITY": mut_status,
        "PRIVILEGED_EXECUTION": priv_exec,
        "LIVE_AUTHORITY_ACTION": live_action,
        "P0014_AUTHORITY_CLASS": p0014_class,
        "P0030_AUTHORITY_CLASS": p0030_class,
        "SYSTEM_PERMISSIONLESS": system_permissionless,
        "TRUSTLESS_VERIFIED": False,
        "DECENTRALIZED_VERIFIED": False,
        "AUTHORITY_STATUS": "PARTIAL",  # coarse legacy; never VERIFIED from architecture alone
        # Independent verdict flags (semantics TASK 14)
        "AUTHORITY_ARCHITECTURE_MAPPED": mech_status == "MAPPED",
        "AUTHORITY_STATE_PARTIALLY_VERIFIED": state_read == "PARTIAL_LIVE_READ",
        "AUTHORITY_STATE_VERIFIED": state_read == "LIVE_READ_VERIFIED",
        "AUTHORITY_HOLDER_ADDRESS_VERIFIED": holder_addr == "VERIFIED",
        "AUTHORITY_SCOPE_VERIFIED": scope_status == "MAPPED",
        "AUTHORITY_MUTABILITY_VERIFIED": mut_status == "MAPPED",
        "PRIVILEGED_EXECUTION_VERIFIED": priv_exec == "VERIFIED",
        "LIVE_AUTHORITY_ACTION_VERIFIED": live_action == "VERIFIED",
        "unresolved_reason": default_unresolved,
        "CURRENT_L2_UNREAD_GAP": pack.get("current_l2_unread_gap")
        or ("OPEN" if has_current_unread or unread else "CLOSED"),
        "FAILURE_HISTORY_PRESERVED": True,
        "historical_reconciliation": {
            "class_counts": hist.get("class_counts") or {},
            "current_blocker_count": len(current_blockers),
            "current_blocker_row_ids": [
                str(b.get("ROW_ID") or b.get("AUTHORITY_ID")) for b in current_blockers
            ],
            "FAILURE_HISTORY_PRESERVED": True,
        },
        "counts": {
            "mechanisms": len(mechanisms),
            "runtime_reads": len(reads),
            "privileged_surfaces": len(pack.get("privileged_surfaces") or []),
            "permissionless_surfaces": len(pack.get("permissionless_surfaces") or []),
            "unread_authority_ids": len(unread),
            "current_blocker_failures": len(current_blockers),
        },
    }


def apply_authority_nonclaim_gates(axes: dict[str, Any], pack: dict[str, Any]) -> dict[str, Any]:
    gates = {
        "NG-AUTH-01": True,  # trustless blocked
        "NG-AUTH-02": True,  # decentralized blocked
        "NG-AUTH-03": True,  # system permissionless blocked
        "NG-AUTH-04": True,  # signer identity blocked
        "NG-AUTH-05": True,  # IW blocked
        "NG-AUTH-06": True,  # live tx blocked
        "NG-AUTH-07": True,  # CAW certified blocked
        "NG-AUTH-08": True,  # holder identity from address blocked
        "NG-AUTH-09": True,  # user-asset → protocol admin blocked
        "TRUSTLESS_VERIFIED": False,
        "DECENTRALIZED_VERIFIED": False,
        "SYSTEM_PERMISSIONLESS": False,
        "SIGNER_IDENTITY_PROMOTED": False,
        "IW_SATISFIED": False,
        "LIVE_TRANSACTION_PROMOTED": False,
        "CAW_CERTIFIED_PROMOTED": False,
        "HOLDER_IDENTITY_PROMOTED": False,
        "PROTOCOL_ADMIN_FROM_USER_ASSET": False,
        "ARCHITECTURE_PROMOTED_TO_EXECUTION": False,
        "EXECUTION_PROMOTED_TO_LIVE_ACTION": False,
        "PARTIAL_PROMOTED_TO_FULL_STATE": False,
    }

    axes["TRUSTLESS_VERIFIED"] = False
    axes["DECENTRALIZED_VERIFIED"] = False
    axes["SYSTEM_PERMISSIONLESS"] = False

    if axes.get("AUTHORITY_HOLDER_IDENTITY_STATUS") == "VERIFIED" and not pack.get("holder_identity_evidence"):
        axes["AUTHORITY_HOLDER_IDENTITY_STATUS"] = "NOT_VERIFIED"
        axes["HOLDER_IDENTITY"] = "NOT_VERIFIED"
        gates["HOLDER_IDENTITY_PROMOTED"] = False

    if axes.get("INDEPENDENT_WITNESS_STATUS") == "SATISFIED" and not pack.get("independent_witness_evidence"):
        axes["INDEPENDENT_WITNESS_STATUS"] = "NOT_SATISFIED"
    gates["IW_SATISFIED"] = axes.get("INDEPENDENT_WITNESS_STATUS") == "SATISFIED"

    # Architecture ⇏ execution
    if axes.get("AUTHORITY_ARCHITECTURE_MAPPED") and axes.get("PRIVILEGED_EXECUTION_STATUS") == "VERIFIED":
        if not pack.get("privileged_execution_evidence"):
            axes["PRIVILEGED_EXECUTION_STATUS"] = "NOT_VERIFIED"
            axes["PRIVILEGED_EXECUTION"] = "NOT_VERIFIED"
            axes["PRIVILEGED_EXECUTION_VERIFIED"] = False
            gates["ARCHITECTURE_PROMOTED_TO_EXECUTION"] = False

    # Execution ⇏ live action
    if axes.get("PRIVILEGED_EXECUTION_STATUS") == "VERIFIED" and axes.get("LIVE_AUTHORITY_ACTION_STATUS") == "VERIFIED":
        if not pack.get("live_authority_action_evidence"):
            axes["LIVE_AUTHORITY_ACTION_STATUS"] = "NOT_VERIFIED"
            axes["LIVE_AUTHORITY_ACTION"] = "NOT_VERIFIED"
            axes["LIVE_AUTHORITY_ACTION_VERIFIED"] = False
            gates["EXECUTION_PROMOTED_TO_LIVE_ACTION"] = False

    # Partial ⇏ full
    if axes.get("AUTHORITY_STATE_READ_STATUS") == "LIVE_READ_VERIFIED" and (
        (pack.get("unread_authority_ids") or [])
        or _current_blocker_reads(list(pack.get("runtime_reads") or []))
    ):
        axes["AUTHORITY_STATE_READ_STATUS"] = "PARTIAL_LIVE_READ"
        axes["AUTHORITY_STATE"] = "PARTIAL_LIVE_READ"
        axes["AUTHORITY_STATE_VERIFIED"] = False
        axes["AUTHORITY_STATE_PARTIALLY_VERIFIED"] = True
        gates["PARTIAL_PROMOTED_TO_FULL_STATE"] = False

    # User-asset ⇏ protocol admin
    for link in pack.get("runtime_authority_links") or []:
        if link.get("AUTHORITY_CLASS") == "USER_ASSET_AUTHORIZATION":
            if link.get("inherits_protocol_admin") or link.get("AUTHORITY_CLASS_PROMOTED") == "PROTOCOL_ADMIN_AUTHORITY":
                gates["PROTOCOL_ADMIN_FROM_USER_ASSET"] = False
                link["inherits_protocol_admin"] = False

    # Claim reassessment impact
    for cr in pack.get("claim_reassessments") or []:
        if cr.get("OVERALL_CAW_VERDICT_IMPACT") not in (None, "NONE"):
            # Force NONE unless dedicated override
            if not pack.get("allow_caw_verdict_impact"):
                cr["OVERALL_CAW_VERDICT_IMPACT"] = "NONE"
    gates["CAW_CERTIFIED_PROMOTED"] = False
    gates["CAW_VERDICT_CHANGED"] = bool((pack.get("caw_verdict_snapshot") or {}).get("CAW_VERDICT_CHANGED", False))

    # Coarse AUTHORITY_STATUS never VERIFIED from this module alone
    if axes.get("AUTHORITY_STATUS") == "VERIFIED" and not pack.get("allow_coarse_authority_verified"):
        axes["AUTHORITY_STATUS"] = "PARTIAL"

    return {"axes": axes, "nonclaim_gates": gates}


# ---------------------------------------------------------------------------
# Verify entrypoint
# ---------------------------------------------------------------------------

def verify_authority_evidence_v0(req: dict[str, Any]) -> dict[str, Any]:
    created = now()
    if not isinstance(req, dict) or req.get("schema_version") != SCHEMA_VERSION:
        r = {
            "schema_version": SCHEMA_VERSION,
            "result_id": "",
            "verification_status": "REJECTED",
            "reason_codes": ["invalid_input_or_schema"],
            "errors": [_err("invalid_input_or_schema")],
            "created_at": created,
        }
        r["result_id"] = rid(r)
        return r

    pack = req.get("authority_evidence_pack") or req.get("pack") or {}
    errors: list[dict[str, str]] = []
    errors.extend(validate_pack_schema(pack))
    if not errors:
        errors.extend(validate_separations(pack))

    if errors:
        r = {
            "schema_version": SCHEMA_VERSION,
            "result_id": "",
            "verification_status": "REJECTED",
            "source_authority_run_id": pack.get("source_authority_run_id"),
            "errors": errors,
            "reason_codes": sorted({e["code"] for e in errors}),
            "axes": {},
            "created_at": created,
            "network_used": False,
            "rpc_used": False,
            "new_authority_reads": False,
            "privileged_action_executed": False,
            "caw_source_mutated": False,
            "caw_verdict_changed": False,
        }
        r["result_id"] = rid(r)
        return r

    axes = classify_authority_axes(pack)
    gated = apply_authority_nonclaim_gates(axes, pack)
    axes = gated["axes"]

    claim_out = []
    for cr in pack.get("claim_reassessments") or []:
        claim_out.append(
            {
                "CLAIM_ID": cr.get("CLAIM_ID"),
                "CLAIM_CLASS": cr.get("CLAIM_CLASS"),
                "ASSESSMENT": cr.get("ASSESSMENT"),
                "CONFIDENCE": cr.get("CONFIDENCE"),
                "OVERALL_CAW_VERDICT_IMPACT": cr.get("OVERALL_CAW_VERDICT_IMPACT") or "NONE",
            }
        )

    links = pack.get("runtime_authority_links") or []
    consumer_contract = {
        "schema_version": CONSUMER_CONTRACT_SCHEMA,
        "join_key": "PATH_ID",
        "axes": {
            "AUTHORITY_MECHANISM_STATUS": axes["AUTHORITY_MECHANISM_STATUS"],
            "AUTHORITY_STATE_READ_STATUS": axes["AUTHORITY_STATE_READ_STATUS"],
            "AUTHORITY_HOLDER_ADDRESS_STATUS": axes["AUTHORITY_HOLDER_ADDRESS_STATUS"],
            "AUTHORITY_HOLDER_IDENTITY_STATUS": axes["AUTHORITY_HOLDER_IDENTITY_STATUS"],
            "AUTHORITY_SCOPE_STATUS": axes["AUTHORITY_SCOPE_STATUS"],
            "AUTHORITY_MUTABILITY_STATUS": axes["AUTHORITY_MUTABILITY_STATUS"],
            "PRIVILEGED_EXECUTION_STATUS": axes["PRIVILEGED_EXECUTION_STATUS"],
            "LIVE_AUTHORITY_ACTION_STATUS": axes["LIVE_AUTHORITY_ACTION_STATUS"],
            "AUTHORITY_STATUS": axes["AUTHORITY_STATUS"],
        },
        "runtime_authority_links": links,
        "do_not_merge_into_runtime_execution_status": True,
        "do_not_merge_into_static_path_status": True,
        "nonclaim_gates": gated["nonclaim_gates"],
    }

    r = {
        "schema_version": SCHEMA_VERSION,
        "result_id": "",
        "verification_status": "ACCEPTED",
        "source_authority_run_id": pack.get("source_authority_run_id"),
        "pin": pack.get("pin"),
        "pack_digest": pack.get("pack_digest") or digest(pack),
        "axes": axes,
        "AUTHORITY_MECHANISM_STATUS": axes["AUTHORITY_MECHANISM_STATUS"],
        "AUTHORITY_STATE_READ_STATUS": axes["AUTHORITY_STATE_READ_STATUS"],
        "AUTHORITY_HOLDER_ADDRESS_STATUS": axes["AUTHORITY_HOLDER_ADDRESS_STATUS"],
        "AUTHORITY_HOLDER_IDENTITY_STATUS": axes["AUTHORITY_HOLDER_IDENTITY_STATUS"],
        "AUTHORITY_SCOPE_STATUS": axes["AUTHORITY_SCOPE_STATUS"],
        "AUTHORITY_MUTABILITY_STATUS": axes["AUTHORITY_MUTABILITY_STATUS"],
        "PRIVILEGED_EXECUTION_STATUS": axes["PRIVILEGED_EXECUTION_STATUS"],
        "LIVE_AUTHORITY_ACTION_STATUS": axes["LIVE_AUTHORITY_ACTION_STATUS"],
        "AUTHORITY_ARCHITECTURE": axes["AUTHORITY_ARCHITECTURE"],
        "AUTHORITY_STATE": axes["AUTHORITY_STATE"],
        "HOLDER_ADDRESS": axes["HOLDER_ADDRESS"],
        "HOLDER_IDENTITY": axes["HOLDER_IDENTITY"],
        "SCOPE": axes["SCOPE"],
        "MUTABILITY": axes["MUTABILITY"],
        "P0014_AUTHORITY_CLASS": axes["P0014_AUTHORITY_CLASS"],
        "P0030_AUTHORITY_CLASS": axes["P0030_AUTHORITY_CLASS"],
        "SYSTEM_PERMISSIONLESS": axes["SYSTEM_PERMISSIONLESS"],
        "INDEPENDENT_WITNESS_STATUS": axes["INDEPENDENT_WITNESS_STATUS"],
        "TRUSTLESS_VERIFIED": False,
        "DECENTRALIZED_VERIFIED": False,
        "claim_reassessments": claim_out,
        "runtime_authority_links": links,
        "nonclaim_gates": gated["nonclaim_gates"],
        "consumer_contract": consumer_contract,
        "known_shared_l1_owner": pack.get("known_shared_l1_owner"),
        "unread_authority_ids": pack.get("unread_authority_ids") or [],
        "current_l2_unread_gap": pack.get("current_l2_unread_gap") or axes.get("CURRENT_L2_UNREAD_GAP"),
        "historical_reconciliation": axes.get("historical_reconciliation"),
        "unresolved_reason": axes.get("unresolved_reason"),
        "errors": [],
        "reason_codes": [],
        "network_used": False,
        "rpc_used": False,
        "new_authority_reads": False,
        "privileged_action_executed": False,
        "live_authority_action_verified": axes["LIVE_AUTHORITY_ACTION_STATUS"] == "VERIFIED",
        "caw_source_mutated": False,
        "caw_verdict_changed": False,
        "execution_authorized_beyond_implementation": False,
        "weaver_authority_support": {
            "EVIDENCE_VERIFICATION": "NATIVE",
            "EVIDENCE_COLLECTION": "EXTERNAL",
            "OVERALL": "PARTIAL",
        },
        "limitations": [
            "verifies existing authority evidence only; no RPC/network",
            "AUTHORITY_ARCHITECTURE_MAPPED does not imply PRIVILEGED_EXECUTION_VERIFIED",
            "PRIVILEGED_EXECUTION_VERIFIED does not imply LIVE_AUTHORITY_ACTION_VERIFIED",
            "holder address does not imply holder identity",
            "permissionless function does not imply system permissionless",
            "user-asset authorization does not imply protocol admin",
        ],
        "created_at": created,
        "design_run_id": req.get("design_run_id") or "WAEID-20260912-132447-D4AAEF36",
    }
    r["result_id"] = rid(r)
    return r


# ---------------------------------------------------------------------------
# Thin runtime ↔ authority link helpers
# ---------------------------------------------------------------------------

def attach_authority_link_to_runtime_verifier_result_v0(
    runtime_result: dict[str, Any],
    authority_result: dict[str, Any],
    *,
    path_id: str | None = None,
) -> dict[str, Any]:
    """Link-only: attach authority class/link to a runtime verifier result.

    Does not promote AUTHORITY_STATUS to VERIFIED, does not alter runtime execution axes.
    """
    out = json.loads(json.dumps(runtime_result))
    if authority_result.get("verification_status") != "ACCEPTED":
        out["authority_link_attach"] = {
            "status": "SKIPPED_REJECTED_AUTHORITY_VERIFIER",
            "authority_result_id": authority_result.get("result_id"),
        }
        return out

    pid = path_id or out.get("path_id")
    link = None
    for lnk in authority_result.get("runtime_authority_links") or []:
        if lnk.get("PATH_ID") == pid:
            link = lnk
            break

    axes = authority_result.get("axes") or {}
    # Preserve runtime axes
    runtime_exec_before = out.get("RUNTIME_EXECUTION_STATUS")
    auth_status_before = out.get("AUTHORITY_STATUS")

    out["authority_link"] = {
        "schema_version": RUNTIME_AUTHORITY_LINK_SCHEMA,
        "PATH_ID": pid,
        "link": link,
        "AUTHORITY_CLASS": (link or {}).get("AUTHORITY_CLASS"),
        "CALLER_GATE_CLASS": (link or {}).get("CALLER_GATE_CLASS"),
        "AUTHORITY_MECHANISM_STATUS": axes.get("AUTHORITY_MECHANISM_STATUS"),
        "AUTHORITY_STATE_READ_STATUS": axes.get("AUTHORITY_STATE_READ_STATUS"),
        "AUTHORITY_SCOPE_STATUS": axes.get("AUTHORITY_SCOPE_STATUS"),
        "authority_result_id": authority_result.get("result_id"),
        "do_not_merge_into_runtime_execution_status": True,
    }
    # Coarse AUTHORITY_STATUS may become PARTIAL from architecture, never VERIFIED here
    if auth_status_before != "VERIFIED":
        out["AUTHORITY_STATUS"] = "PARTIAL" if axes.get("AUTHORITY_ARCHITECTURE_MAPPED") else (
            auth_status_before or "NOT_VERIFIED"
        )
    if out.get("AUTHORITY_STATUS") == "VERIFIED" and not (out.get("nonclaim_gates") or {}).get(
        "AUTHORITY_VERIFIED_ALLOWED"
    ):
        out["AUTHORITY_STATUS"] = "PARTIAL"

    # Refuse upward class promotions
    aclass = (link or {}).get("AUTHORITY_CLASS")
    out["authority_link"]["PROTOCOL_ADMIN_AUTHORITY"] = aclass == "PROTOCOL_ADMIN_AUTHORITY"
    out["authority_link"]["SYSTEM_PERMISSIONLESS"] = False
    if runtime_exec_before is not None:
        out["RUNTIME_EXECUTION_STATUS"] = runtime_exec_before
    out["authority_link_attach"] = {"status": "ATTACHED", "path_id": pid}
    return out


def attach_authority_evidence_to_synthesizer_paths_v0(
    synthesizer_result: dict[str, Any],
    authority_result: dict[str, Any],
) -> dict[str, Any]:
    """Thin synthesizer consumer: attach independent authority fields by PATH_ID.

    Does NOT alter STATIC_PATH_STATUS / COMPLETE / PARTIAL based on authority evidence.
    """
    out = json.loads(json.dumps(synthesizer_result))
    if authority_result.get("verification_status") != "ACCEPTED":
        out["authority_evidence_attach"] = {
            "status": "SKIPPED_REJECTED_AUTHORITY_VERIFIER",
            "authority_result_id": authority_result.get("result_id"),
        }
        return out

    axes = authority_result.get("axes") or {}
    links_by_path = {
        lnk.get("PATH_ID"): lnk for lnk in (authority_result.get("runtime_authority_links") or [])
    }
    attached = 0
    for p in out.get("paths") or []:
        static_before = p.get("STATIC_PATH_STATUS")
        path_status_before = p.get("path_status")
        pid = p.get("path_id")
        link = links_by_path.get(pid)
        if not link:
            continue
        p["AUTHORITY_CLASS"] = link.get("AUTHORITY_CLASS")
        p["AUTHORITY_MECHANISM_STATUS"] = axes.get("AUTHORITY_MECHANISM_STATUS")
        p["AUTHORITY_STATE_READ_STATUS"] = axes.get("AUTHORITY_STATE_READ_STATUS")
        p["AUTHORITY_SCOPE_STATUS"] = axes.get("AUTHORITY_SCOPE_STATUS")
        p["AUTHORITY_HOLDER_ADDRESS_STATUS"] = axes.get("AUTHORITY_HOLDER_ADDRESS_STATUS")
        p["AUTHORITY_HOLDER_IDENTITY_STATUS"] = axes.get("AUTHORITY_HOLDER_IDENTITY_STATUS")
        p["AUTHORITY_MUTABILITY_STATUS"] = axes.get("AUTHORITY_MUTABILITY_STATUS")
        p["PRIVILEGED_EXECUTION_STATUS"] = axes.get("PRIVILEGED_EXECUTION_STATUS")
        p["LIVE_AUTHORITY_ACTION_STATUS"] = axes.get("LIVE_AUTHORITY_ACTION_STATUS")
        p["authority_evidence_result_id"] = authority_result.get("result_id")
        p["runtime_authority_link"] = link
        # Coarse AUTHORITY_STATUS: refine to PARTIAL at most
        if p.get("AUTHORITY_STATUS") != "VERIFIED":
            p["AUTHORITY_STATUS"] = "PARTIAL"
        if static_before is not None:
            p["STATIC_PATH_STATUS"] = static_before
        if path_status_before is not None:
            p["path_status"] = path_status_before
        attached += 1

    out["authority_evidence_attach"] = {
        "status": "ATTACHED",
        "paths_attached": attached,
        "authority_result_id": authority_result.get("result_id"),
        "do_not_alter_static_complete": True,
    }
    return out


def generalization_structural_check() -> dict[str, Any]:
    """Structural support check without empirical verification of all cases."""
    cases = [
        ("OWNABLE", "MECHANISM_TYPE=OWNABLE"),
        ("TOKEN_OWNER_GATE", "MECHANISM_TYPE=TOKEN_OWNER_GATE + USER_ASSET_AUTHORIZATION"),
        ("PROFILE_OWNER_GATE", "MECHANISM_TYPE=PROFILE_OWNER_GATE + USER_ASSET_AUTHORIZATION"),
        ("PERMISSIONLESS_FUNCTION", "PERMISSIONLESS + surface SCOPE=FUNCTION"),
        ("CUSTOM_ROLE", "MECHANISM_TYPE=CUSTOM_ROLE"),
        ("CONTRACT_GATE", "MECHANISM_TYPE=CONTRACT_GATE"),
        ("SIGNATURE_GATE", "MECHANISM_TYPE=SIGNATURE_GATE"),
        ("VALIDATOR_GATE", "MECHANISM_TYPE=VALIDATOR_GATE"),
        ("PARTIAL_LIVE_READ", "AUTHORITY_STATE_READ_STATUS=PARTIAL_LIVE_READ"),
        ("UNREAD_AUTHORITY_STATE", "RUNTIME_READ_VERDICT=UNREAD"),
        ("FUTURE_L2_AUTHORITY_READS", "same read model with L2 chain_id"),
    ]
    return {
        "empirically_verified_all": False,
        "structural_support": [
            {"case": c, "supported": True, "via": v, "empirically_verified": False} for c, v in cases
        ],
    }


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        sys.stderr.write(
            "usage:\n"
            "  authority_evidence_verifier_v0.py --emit-caro-pack [caro_dir]\n"
            "  authority_evidence_verifier_v0.py --verify-caro [caro_dir]\n"
            "  authority_evidence_verifier_v0.py <input.json>\n"
        )
        return 1
    if args[0] == "--emit-caro-pack":
        caro = args[1] if len(args) > 1 else None
        pack = normalize_caro_authority_pack(caro)
        print(json.dumps(pack, indent=2, ensure_ascii=True))
        return 0
    if args[0] == "--verify-caro":
        caro = args[1] if len(args) > 1 else None
        pack = normalize_caro_authority_pack(caro)
        res = verify_authority_evidence_v0(
            {"schema_version": SCHEMA_VERSION, "authority_evidence_pack": pack}
        )
        print(json.dumps(res, indent=2, ensure_ascii=True))
        return 0 if res.get("verification_status") == "ACCEPTED" else 3
    req = json.loads(Path(args[0]).read_text(encoding="utf-8"))
    res = verify_authority_evidence_v0(req)
    print(json.dumps(res, indent=2, ensure_ascii=True))
    return 0 if res.get("verification_status") == "ACCEPTED" else 3


if __name__ == "__main__":
    raise SystemExit(main())
