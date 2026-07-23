# Verdict — xAI Grok Build

| Field | Value |
|-------|-------|
| Target slug | `grok-build` |
| Verdict status | **Owner-side build axes PASS; Witness package NOT READY (`1.0.0-rc4` / fixed tag `grok-build-witness-v1.0.0-rc4` → `039b46737c5968a81fb756d7a6d1d0dd57b6ad96`); rc4 static blind audit COMPLETE — final disposition NOT READY (40 integrated blockers); Phase 0 audit intake COMPLETE; Phase 1 documentation remediation on `main`; technical implementation remediation NOT YET BEGUN; `main` prepared toward possible future rc5 candidate (rc5 tag does not exist); no Independent Witness reproduction; C-014 NOT_STARTED; overall PARTIAL** |
| Issued by | Weaver Forge documentation package author |
| Role | Owner-side evaluator (not independent witness) |
| Verdict date | `2026-07-23` (RC5 Phase 1 — release/status truthfulness remediation on `main`) |
| Source pin | **`98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce`** |

---

## Multi-axis

| Axis | Verdict | Notes |
|------|---------|-------|
| Source authenticity | `PASS` | |
| Artifact integrity | `PARTIAL` | Local hashes; two owner binaries differ |
| Owner-side narrow rebuild | `PASS` | C2D-1 |
| Build reproducibility | **`PARTIAL`** | Not bit-identical; **no independent witness run yet** |
| Functional | `NOT_STARTED` | |
| Security | `NOT_STARTED` | |
| Independent witness | **`NOT_STARTED`** | C-014 unchanged |
| Witness package readiness | **NOT READY — `1.0.0-rc4`; fixed tag `grok-build-witness-v1.0.0-rc4` → `039b46737c5968a81fb756d7a6d1d0dd57b6ad96`; rc4 static disposition NOT READY (40 blockers; C-027 audit-recording only)** | C2E-1 **READY WITH LIMITATIONS** superseded; rc1–rc4 preserved as immutable tags; each has a recorded NOT READY audit (C-024–C-027); Phase 1 docs remediation on `main`; rc5 tag does not exist |
| Operational readiness | `NOT_STARTED` | |
| Windows readiness | `BLOCKED` | |
| Static startup | `PARTIAL` | |
| Artifact variance analysis | `PASS` | |
| **Overall** | **`PARTIAL`** | |

## Claim rollup (scope-separated)

| Scope | IDs / status | Does not imply |
|-------|--------------|----------------|
| Documentation / owner build axes | C-001–C-011, C-013, C-016–C-018, C-020–C-021 PASS; C-015 BLOCKED; C-019 PARTIAL; C-012 NOT_STARTED | Package readiness; Independent Witness |
| Historical readiness audit | C-022 HISTORICAL PASS / CURRENT READINESS SUPERSEDED | Current package READY |
| Audit-recording claims only | C-023–C-027 PASS (`AUDIT_RECORDED`); each underlying audit **NOT READY**; C-027 `claim_scope=AUDIT_RECORDING`, `package_readiness_effect=NONE`, `independent_witness_effect=NONE`, `c014_effect=NONE` | Package readiness; remediation completion; Independent Witness |
| Remediation-completion claims | **none registered** (Phase 1 docs remediation does not create a readiness claim) | Technical blocker closure beyond RC4B-001/002/003 docs status |
| Package-readiness status | **NOT READY** (rc4 static disposition) | — |
| Independent Witness status | C-014 **NOT_STARTED**; reproduction **NOT PERFORMED**; PASS **NONE** | — |

| ID | Status |
|----|--------|
| C-001–C-011 | PASS (docs) |
| C-012 | NOT_STARTED |
| C-013 | PASS |
| C-014 | **NOT_STARTED** (Independent Witness) |
| C-015 | BLOCKED |
| C-016–C-018 | PASS |
| C-019 | PARTIAL |
| C-020–C-021 | PASS |
| C-022 | **PASS** (C2E-1 owner-side readiness audit only); **effective package readiness superseded — NOT READY**; HISTORICAL |
| C-023 | **PASS** (blind audit intake recorded only) |
| C-024 | **PASS** (rc1 repeat blind audit recording only; audit verdict **NOT READY**); rc1 preserved immutable |
| C-025 | **PASS** (rc2 integrated four-batch static blind audit recording only; audit verdict **NOT READY**); rc2 preserved immutable |
| C-026 | **PASS** (display label `AUDIT_RECORDED` — rc3 integrated four-batch static blind audit recording only; audit verdict **NOT READY**); rc3 preserved immutable |
| C-027 | **PASS** (display label `AUDIT_RECORDED` — claim_scope=`AUDIT_RECORDING`; rc4 integrated four-batch static blind audit recording only; final disposition **NOT READY**; 40 blockers; package_readiness_effect=`NONE`; independent_witness_effect=`NONE`; c014_effect=`NONE`); does **not** establish package readiness or Independent Witness PASS |

A numerical PASS rollup that includes C-023–C-027 must **not** be read as package readiness.

## Where a Witness starts

`external_verifications/grok-build/witness-package/README.md`

## C2E-5 status (historical phase label)

**HISTORICAL (C2E-5 contemporaneous banner, retained for chronology):**
`RC3 INTEGRATED STATIC BLIND-AUDIT RECORDED — RC4 PACKAGE CONTENT UNDER PREPARATION — NOT READY PENDING RC4 COMMIT, TAG AND RE-AUDIT`

That banner described the pre-publication / pre-rc4-audit state. It is **not** current status.

C-026 records the rc3 integrated four-batch static audit intake (verdict NOT READY; audit preserved under `evidence/rc3-static-blind-audit/`); C-024 and C-025 remain preserved unchanged.

### HISTORICAL PRE-TAG STATE

Prior wording in this section described rc3 as package content prepared with a canonical tag name assigned, pending its repeat blind audit. That audit has since completed (NOT READY, C-026); rc3 is immutable history. Pre-publication wording also described rc4 as package content under preparation; that wording is superseded by the current-state section below.

## RC5 Phase 0 status

**RC4 STATIC BLIND AUDIT COMPLETE — FINAL DISPOSITION NOT READY — 40 INTEGRATED BLOCKERS RECORDED**

C-027 records the rc4 integrated four-batch Source Weaver static blind audit intake under `evidence/rc4-static-blind-audit/` (`claim_scope=AUDIT_RECORDING`). Final static disposition **NOT READY**. Independent Witness reproduction **NOT PERFORMED**. C-014 remains **`NOT_STARTED`**. No Independent Witness PASS is claimed.

## RC5 Phase 1 status (current)

**RC4 FIXED IMMUTABLE — STATIC DISPOSITION NOT READY — PHASE 1 DOCUMENTATION/STATUS-TRUTHFULNESS REMEDIATION ON MAIN — TECHNICAL IMPLEMENTATION REMEDIATION NOT YET BEGUN — RC5 TAG DOES NOT EXIST — C-014 NOT_STARTED**

Current release identity: annotated tag `grok-build-witness-v1.0.0-rc4` → commit `039b46737c5968a81fb756d7a6d1d0dd57b6ad96`. Phase 1 corrects current-facing prospective/pending wording and immutable-history gaps associated with RC4B-001/002/003 only. It does **not** close technical blockers RC4B-004–RC4B-040, does **not** claim package readiness, and does **not** create or imply an rc5 tag.

---

**Witness is attestation, not authority. Package remains NOT READY (rc4 static disposition). RC5 tag does not exist. C-014 NOT_STARTED. Do not begin Phase 2 until instructed.**
