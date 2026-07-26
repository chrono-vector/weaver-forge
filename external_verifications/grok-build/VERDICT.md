# Verdict — xAI Grok Build

| Field | Value |
|-------|-------|
| Target slug | `grok-build` |
| Verdict status | **Owner-side build axes PASS; Witness package NOT READY — RC5 FIXED IMMUTABLE — NOT READY — Independent Witness handoff not authorized — C-014 NOT_STARTED — RC6-R1–R7 remediation implemented on `main` (pre-tag / prospective RC6 fixed candidate only) — RC6 tag/archive/bundle do not yet exist — NOT READY — Independent Witness reproduction NOT PERFORMED — Independent Witness PASS NONE; overall PARTIAL** |
| Issued by | Weaver Forge documentation package author |
| Role | Owner-side evaluator (not independent witness) |
| Verdict date | `2026-07-26` (RC6-R7 documentation/status alignment on `main`) |
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
| Witness package readiness | **NOT READY — RC5 FIXED_IMMUTABLE (tag `grok-build-witness-v1.0.0-rc5`; annotated tag object `9c01e314249f59945e93597af6ece2e3fb33e6cd`; peeled commit `5ae08cb8be9c1c97f25b9093bb5490a0ef195a07`; tree `97ad93d80480b23a49f1636ff55dae449202aa3c`; archive SHA-256 `5bf6e8f66795ba310ad5b149b721ca1930b5729ab3c568a20559d8dda40e0435`; transfer-bundle SHA-256 `5581b10788f0a3ee7a36982ac1b2468c658afc353fe88da3423298b60344bb2b`); Source Weaver disposition NOT READY; Independent Witness handoff not authorized; current `main` = pre-tag RC6-R1–R7 remediation only; RC6 tag/archive/bundle absent** | C2E-1 **READY WITH LIMITATIONS** superseded; rc1–rc5 preserved as immutable tags; each NOT READY; C-014 NOT_STARTED; findings not CLEAR/CLOSED by documentation alone |
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
| Remediation-completion claims | **none registered** (RC6-R1–R7 implementation/docs alignment does not create a readiness claim and does not mark findings CLEAR/CLOSED) | Finding/blocker CLEAR/CLOSED; RC6 READY; Independent Witness authorization |
| Package-readiness status | **NOT READY** (RC5 Source Weaver disposition; pre-tag RC6 remediation on `main` is not an immutable fixed candidate) | — |
| Independent Witness status | C-014 **NOT_STARTED**; reproduction **NOT PERFORMED**; PASS **NONE**; handoff **not authorized** | — |

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

## RC6-R7 status (current)

**RC5 FIXED IMMUTABLE — NOT READY — INDEPENDENT WITNESS HANDOFF NOT AUTHORIZED — C-014 NOT_STARTED — RC6-R1–R7 REMEDIATION IMPLEMENTED ON MAIN (PRE-TAG / PROSPECTIVE RC6 FIXED CANDIDATE ONLY) — RC6 TAG/ARCHIVE/BUNDLE DO NOT YET EXIST — NOT READY**

Last immutable release identity: tag `grok-build-witness-v1.0.0-rc5`; annotated tag object `9c01e314249f59945e93597af6ece2e3fb33e6cd`; peeled commit `5ae08cb8be9c1c97f25b9093bb5490a0ef195a07`; tree `97ad93d80480b23a49f1636ff55dae449202aa3c`; archive SHA-256 `5bf6e8f66795ba310ad5b149b721ca1930b5729ab3c568a20559d8dda40e0435`; transfer-bundle SHA-256 `5581b10788f0a3ee7a36982ac1b2468c658afc353fe88da3423298b60344bb2b`. Source Weaver ruled RC5 **NOT READY**. Independent
Witness handoff is **not authorized**. Independent Witness reproduction **NOT PERFORMED**.
Independent Witness PASS **NONE**. C-014 remains **`NOT_STARTED`**.

Current `main` hosts RC6-R1–R7 remediation implemented toward a prospective RC6 fixed candidate
only. R1–R6 were reviewed through Pi staged-diff conformance and committed/pushed. R7 is
documentation/status alignment only. Implementation completion is **not** finding CLEAR/CLOSED,
blocker clearance, RC6 READY, release approval, or Independent Witness authorization. An RC6
tag, archive, and transfer bundle **do not yet exist**. Source Weaver has **not** audited an
immutable RC6 fixed candidate. Do not describe current `main` as an immutable RC6 candidate or
approved handoff package.

Historical note: RC5 Phase 1 on `main` corrected rc4 prospective/pending wording associated with
RC4B-001/002/003 documentation manifestations only; that phase did **not** close technical
blockers and did **not** create RC5 (RC5 was created later and remains NOT READY).

---

**Witness is attestation, not authority. Package remains NOT READY (RC5 disposition; pre-tag RC6 remediation on main). Independent Witness handoff not authorized. C-014 NOT_STARTED. Findings remain subject to later immutable Source Weaver adjudication.**
