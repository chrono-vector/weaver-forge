# Verdict — xAI Grok Build

| Field | Value |
|-------|-------|
| Target slug | `grok-build` |
| Verdict status | **Owner-side build axes PASS; Witness package NOT READY (`1.0.0-rc4` / canonical tag `grok-build-witness-v1.0.0-rc4`; rc4 package content under preparation); C-014 NOT_STARTED; overall PARTIAL** |
| Issued by | Weaver Forge documentation package author |
| Role | Owner-side evaluator (not independent witness) |
| Verdict date | `2026-07-22` (C2E-5 rc4 preparation; rc3 integrated four-batch static audit recorded NOT READY) |
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
| Witness package readiness | **NOT READY — `1.0.0-rc4`; canonical tag `grok-build-witness-v1.0.0-rc4`; rc4 package content under preparation** | C2E-1 **READY WITH LIMITATIONS** superseded; rc1, rc2, and rc3 preserved as immutable historical releases, each with a recorded NOT READY audit (C-024, C-025, C-026) |
| Operational readiness | `NOT_STARTED` | |
| Windows readiness | `BLOCKED` | |
| Static startup | `PARTIAL` | |
| Artifact variance analysis | `PASS` | |
| **Overall** | **`PARTIAL`** | |

## Claim rollup

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

## Where a Witness starts

`external_verifications/grok-build/witness-package/README.md`

## C2E-5 status

**RC3 INTEGRATED STATIC BLIND-AUDIT RECORDED — RC4 PACKAGE CONTENT UNDER PREPARATION — NOT READY PENDING RC4 COMMIT, TAG AND RE-AUDIT**

Package version **`1.0.0-rc4`**; canonical package tag **`grok-build-witness-v1.0.0-rc4`** (availability verified by annotated-tag resolution; canonical execution requires successful resolution; if resolution fails, canonical execution stops; after publication the tag is immutable). Package commit authority is `annotated_tag_resolution` — no embedded future rc4 commit. C-026 records the rc3 integrated four-batch static audit intake (verdict NOT READY; audit preserved under `evidence/rc3-static-blind-audit/`); C-024 (rc1 repeat audit) and C-025 (rc2 integrated audit) remain preserved unchanged. Later `main`-branch status/audit records are outside the rc4 tagged snapshot once it exists.

### HISTORICAL PRE-TAG STATE

Prior wording in this section described rc3 as package content prepared with a canonical tag name assigned, pending its repeat blind audit. That audit has since completed (NOT READY, C-026); rc3 is now immutable history and rc4 is the package content under preparation.

---

**Witness is attestation, not authority. Package remains NOT READY until rc4 is committed, tagged, and repeat-audited. C-014 NOT_STARTED.**
