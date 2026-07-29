# Verdict — xAI Grok Build

| Field | Value |
|-------|-------|
| Target slug | `grok-build` |
| Verdict status | **Owner-side build axes PASS; Witness package lifecycle PARTIAL — RC6 immutable historical NOT READY — RC7 immutable historical NOT READY after completed Source Weaver audit; RC7 not eligible for Independent Witness handoff — Independent Witness handoff not authorized — C-014 NOT_STARTED — no finding CLEAR/CLOSED — RC8 immutable static-audit candidate (`1.0.0-rc8` / `grok-build-witness-v1.0.0-rc8`) — RC8 artifact generation and verification passed — accepted non-authoritative advisory technical evaluation — formal Source Weaver audit not performed for RC8 — no formal Source Weaver READY/NOT READY decision for RC8 — NOT READY for Independent Witness handoff — Independent Witness reproduction NOT PERFORMED — Independent Witness PASS NONE; no release readiness or production readiness claimed; overall PARTIAL** |
| Issued by | Weaver Forge documentation package author |
| Role | Owner-side evaluator (not independent witness) |
| Verdict date | `2026-07-29` (RC8 lifecycle-boundary documentation alignment) |
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
| Witness package lifecycle | **PARTIAL — RC6 immutable historical NOT READY; RC7 immutable historical NOT READY after completed Source Weaver audit and not eligible for Independent Witness handoff; RC8 immutable static-audit candidate (`grok-build-witness-v1.0.0-rc8`; annotated tag object `8113d952d3b127d32e138dbf804141f5d1dfb26f`; peeled commit `1de4b4d9523711418390f8331c95988523ef4481`; tree `87b40d8a32ca536a4cdba0eee474f6171c62f6bb`); RC8 artifact generation and verification passed; accepted non-authoritative advisory technical evaluation; formal Source Weaver audit not performed for RC8; no formal Source Weaver READY/NOT READY decision for RC8; Independent Witness handoff not authorized** | C2E-1 **READY WITH LIMITATIONS** superseded; rc1–rc7 preserved as immutable history; RC6/RC7 NOT READY; RC8 static-audit candidate only; C-014 NOT_STARTED; findings not CLEAR/CLOSED by documentation alone |
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
| Remediation-completion claims | **none registered** (identity/validator alignment and documentation alignment do not create a readiness claim and do not mark findings CLEAR/CLOSED) | Finding/blocker CLEAR/CLOSED; RC6/RC7/RC8 READY; Independent Witness authorization |
| Package-readiness status | **PARTIAL / not ready for Independent Witness handoff** (RC6/RC7 historical NOT READY; RC8 immutable static-audit candidate only; no formal Source Weaver READY/NOT READY decision for RC8) | Formal Source Weaver READY/NOT READY decision for RC8; release readiness; production readiness |
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

## RC8 lifecycle status (current)

**RC6 IMMUTABLE HISTORICAL — NOT READY — RC7 IMMUTABLE HISTORICAL — NOT READY AFTER COMPLETED SOURCE WEAVER AUDIT — RC7 NOT ELIGIBLE FOR INDEPENDENT WITNESS HANDOFF — INDEPENDENT WITNESS HANDOFF NOT AUTHORIZED — C-014 NOT_STARTED — NO FINDING CLEAR/CLOSED — RC8 IMMUTABLE STATIC-AUDIT CANDIDATE (`1.0.0-rc8` / `grok-build-witness-v1.0.0-rc8`) — RC8 ARTIFACT GENERATION AND VERIFICATION PASSED — ACCEPTED NON-AUTHORITATIVE ADVISORY TECHNICAL EVALUATION — FORMAL SOURCE WEAVER AUDIT NOT PERFORMED FOR RC8 — NO FORMAL SOURCE WEAVER READY/NOT READY DECISION FOR RC8 — NOT READY FOR INDEPENDENT WITNESS HANDOFF**

RC8 immutable static-audit candidate identity: tag `grok-build-witness-v1.0.0-rc8`; annotated tag object `8113d952d3b127d32e138dbf804141f5d1dfb26f`; peeled commit `1de4b4d9523711418390f8331c95988523ef4481`; tree `87b40d8a32ca536a4cdba0eee474f6171c62f6bb`. RC8 artifact generation and verification passed, but that result is not a formal Source Weaver audit, not a formal Source Weaver READY decision, not a formal Source Weaver NOT READY decision, not Independent Witness PASS, and not release or production readiness.

RC6 and RC7 remain immutable historical **NOT READY** candidates. RC7 completed Source Weaver static audit and is not eligible for Independent Witness handoff. Independent Witness handoff is **not authorized**. Independent Witness reproduction **NOT PERFORMED**. Independent Witness PASS **NONE**. C-014 remains **`NOT_STARTED`**. No finding or blocker is CLEAR/CLOSED.

Current `main` is a post-RC8 documentation/status surface only. It is not RC9, not READY, not release-approved, and not authorized for Independent Witness handoff.

Historical note: RC5 Phase 1 on `main` corrected rc4 prospective/pending wording associated with RC4B-001/002/003 documentation manifestations only; that phase did **not** close technical blockers and did **not** create RC5 (RC5 was created later and remains NOT READY). RC6 and RC7 were later published as immutable historical NOT READY candidates; RC8 was later published as an immutable static-audit candidate.

---

**Witness is attestation, not authority. Package lifecycle remains PARTIAL and not authorized for Independent Witness handoff. RC6 and RC7 remain immutable historical NOT READY candidates. RC8 remains an immutable static-audit candidate with no formal Source Weaver READY/NOT READY decision. C-014 remains NOT_STARTED. Findings remain subject to later formal adjudication and are not CLEAR/CLOSED by documentation.**
