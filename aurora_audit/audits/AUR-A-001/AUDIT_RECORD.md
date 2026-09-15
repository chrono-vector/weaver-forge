# AUR-A-001 — Audit Record

**Record type:** Human-readable Aurora audit record (references canonical Weaver evidence; does not duplicate the frozen package).  
**Recorded (UTC):** `2026-09-15T05:30:00Z`

## Identity

| Field | Value |
| --- | --- |
| Claim ID | `AUR-A-001` |
| Weaver Audit ID | `WFA-20260915T042439Z-8BE7790F` |
| Target | `aurora_audit/frozen_sources/aurora_overflow_manifest.md` (Source A — LUX Manifest) |
| Claim classification | `A_DOCUMENT_PROVENANCE` — **DOCUMENT IDENTITY ONLY** (intake route `VERIFIABLE_NOW`; Weaver adapter `hash_claim`) |

## Digests

| Field | Value |
| --- | --- |
| Expected SHA-256 | `a38e9f918bed135b5e5a90580830611923c81866aeecb5b8b7b35edd3552d3de` |
| Observed SHA-256 | `a38e9f918bed135b5e5a90580830611923c81866aeecb5b8b7b35edd3552d3de` |

## Lifecycle results

| Vector / gate | Result |
| --- | --- |
| `POSITIVE_DIGEST_MATCH` | PASS |
| `NC1_WRONG_DIGEST_REJECTED` | PASS |
| `T1_TAMPER_CHANGES_DIGEST` | PASS |
| `R1_REHASH_REPRODUCTION` | PASS |
| `BV1_PROTECTED_BOUNDARY_WRITE_DENIED` | PASS |
| Independent verification | `RECORDED_NOT_RUN` / `NOT_CLAIMED` (not claimed for this audit) |
| Human review | `ACCEPTED` (`aurora-first-audit-operator`) |
| Broader classification on pass | `CLAIM_SUPPORTED_PARTIAL` (not promoted to FULL) |
| Freeze | Performed — `FREEZE_STATUS.freeze_performed = true` |

## Final verdict

**PASS — DOCUMENT IDENTITY ONLY**

Reason recorded in lifecycle: `ALL_REQUIRED_VECTORS_PASS`.

## Scope limitation

PASS applies **only** to SHA-256 identity of frozen Source A (`aurora_overflow_manifest.md`).

This audit does **not** assert:

- Aurora / ZOREL civic truth
- Historical claims
- Frequency validation (including 777 Hz)
- 3×3 / 6×6 / 9×9 mechanism function
- Civic / economic implementation
- Any unsupported claim verification

**HASH MATCH ≠ CONTENT TRUTH.**  
**INDIVIDUAL AUDIT PASS ≠ AURORA COMPLETE.**

## Canonical paths

| Role | Path |
| --- | --- |
| Canonical run | `aurora_audit/runs/WFA-20260915T042439Z-8BE7790F` |
| Canonical frozen package | `aurora_audit/runs/WFA-20260915T042439Z-8BE7790F/freeze/WFA-20260915T042439Z-8BE7790F_FROZEN` |

## Frozen package identity

| Artifact | Digest |
| --- | --- |
| Frozen package `SHA256SUMS.txt` digest (`FREEZE_STATUS.sha256sums_digest`) | `5b5b695a50bf03b98bffad8027ad753f719b5ef9ddff82d4f4850fa98bc6c8ae` |
| Frozen `MANIFEST.json` SHA-256 | `4e2e8a3faa20b64e9a7db8d75f3941aeae2b0a4e0d455c289532e235eb667e2a` |
| `FINAL_DECISION.json` SHA-256 (per MANIFEST) | `0d5b468d83f8351ca7263dad768ae1d8b695ed2a40af39a3eb4b1d7c313cecac` |
| `FINAL_EVIDENCE_INDEX.json` SHA-256 (per MANIFEST) | `ae7b0e29cf33af9ef018d5bd59345705609297c5369d5a2a27e68362fdc92734` |

## Material blockers

**none**

## Related non-canonical references

- Request artifact: `aurora_audit/audits/AUR-A-001/AUR_A_001_REQUEST.json`
- Index entry: `aurora_audit/AUDIT_INDEX.md`
