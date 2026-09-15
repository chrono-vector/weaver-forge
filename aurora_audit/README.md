# Aurora Audit — Permanent Storage

**Storage root:** `aurora_audit/`  
**Established (UTC):** `2026-09-15T05:30:00Z`  
**Status:** `STORAGE_FINALIZED` — verification program advanced; AUR-A-001 and AUR-A-002 document-identity audits completed; sandbox batch recorded without civic PASS promotion.

This directory is the permanent Aurora Overflow audit workspace. It is **outside** Weaver Forge product code.

## Permanent epistemic rules

| Rule | Meaning |
| --- | --- |
| **SOURCE ≠ CLAIM** | A frozen source file is an identity boundary, not a set of verified claims. |
| **CLASSIFICATION ≠ VERDICT** | Intake classification and routing do not decide PASS / FAIL / INCONCLUSIVE. |
| **PILOT ≠ VERIFIED EVIDENCE** | Pilot design under `pilots/` is experimental/design work, not verified evidence. |
| **HASH MATCH ≠ CONTENT TRUTH** | Cryptographic identity of bytes does not establish civic, historical, scientific, or implementation truth of the text. |
| **INCONCLUSIVE ≠ PASS** | Missing or insufficient evidence is not success. |
| **UNSUPPORTED ≠ FALSE** | Adapter/support gaps do not authorize declaring a claim false. |
| **INDIVIDUAL AUDIT PASS ≠ AURORA COMPLETE** | One claim PASS (including AUR-A-001) does not complete the overall Aurora audit. |

## Directory roles

| Path | Role |
| --- | --- |
| `runs/` | **Canonical Weaver evidence.** Lifecycle artifacts from Weaver Forge audit runs. Do not move, rename, rewrite, or regenerate. |
| `audits/` | **Human-readable audit records** and index references to canonical runs. Do not duplicate entire frozen packages here. |
| `frozen_sources/` | **Immutable source boundary.** Exact Source A / Source B bytes plus `SOURCE_MANIFEST.json`. |
| `intake/` | **Claim inventory / classification.** 23-claim register, routing, compatibility, and intake provenance. |
| `pilots/` | **Experimental / design work only.** Not verified evidence. |
| `final/` | **Reserved** for the eventual overall Aurora completion package only. |
| `AUDIT_INDEX.md` | Canonical Aurora audit index (completed and future entries). |
| `README.md` | This permanent storage contract. |

## Current completed audits

- **AUR-A-001** — PASS — DOCUMENT IDENTITY ONLY — see `audits/AUR-A-001/AUDIT_RECORD.md` and `AUDIT_INDEX.md`.
- **AUR-A-002** — PASS — DOCUMENT IDENTITY / TEXTUAL PRESENCE ONLY — see `audits/AUR-A-002/AUDIT_RECORD.md` (author-stated checksum ≠ cryptographic digest).

## Operational dashboard

- `AURORA_VERIFICATION_MATRIX.md` — all 23 claims
- `sandbox_harness/` — external protocol simulations (≠ civic truth)
- `pilots/3x3/` — design only, not launched

## Non-goals

- Do not rerun or modify AUR-A-001 / `runs/WFA-20260915T042439Z-8BE7790F`.
- Do not modify frozen AUR-A-002 canonical run evidence after verify.
- Do not modify Weaver Forge product code.
- Do not treat individual PASSes, protocol sims, or pilot design as Aurora overall completion.
- Do not populate `final/` as overall Aurora FINAL without explicit authorization.
