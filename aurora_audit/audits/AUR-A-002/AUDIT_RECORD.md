# AUR-A-002 — Audit Record

**Record type:** Human-readable Aurora audit record (references canonical Weaver evidence; does not duplicate the frozen package).  
**Recorded (UTC):** `2026-09-15T04:37:30Z`

## Identity

| Field | Value |
| --- | --- |
| Claim ID | `AUR-A-002` |
| Weaver Audit ID | `WFA-20260915T043650Z-C49CA863` |
| Target | `aurora_audit/frozen_sources/aurora_overflow_manifest.md` (Source A — LUX Manifest) |
| Claim classification | `A_DOCUMENT_PROVENANCE` — **DOCUMENT IDENTITY / TEXTUAL PRESENCE ONLY** (intake route `VERIFIABLE_NOW`; Weaver adapter `hash_claim`) |

## Digests

| Field | Value |
| --- | --- |
| Expected SHA-256 | `a38e9f918bed135b5e5a90580830611923c81866aeecb5b8b7b35edd3552d3de` |
| Observed SHA-256 | `a38e9f918bed135b5e5a90580830611923c81866aeecb5b8b7b35edd3552d3de` |

## Textual presence (non-cryptographic)

| Field | Value |
| --- | --- |
| Author-stated string | `Checksum: 1.00000 Permanent Flow` |
| Present in pinned Source A bytes | **Yes** (header line: `### Version: 1.0.0-Stable // Checksum: 1.00000 Permanent Flow`) |
| Cryptographic digest interpretation | **Not supported** — author-stated “checksum” is not a hash algorithm digest |

## Lifecycle results

| Vector / gate | Result |
| --- | --- |
| `POSITIVE_DIGEST_MATCH` | PASS |
| `NC1_WRONG_DIGEST_REJECTED` | PASS |
| `T1_TAMPER_CHANGES_DIGEST` | PASS |
| `R1_REHASH_REPRODUCTION` | PASS |
| `BV1_PROTECTED_BOUNDARY_WRITE_DENIED` | PASS |
| Independent verification | `RECORDED_NOT_RUN` / `NOT_CLAIMED` (not claimed for this audit) |
| Human review | `ACCEPTED` (`aurora-verification-program-operator`) |
| Broader classification on pass | `CLAIM_SUPPORTED_PARTIAL` (not promoted to FULL) |
| Freeze | Performed — `FREEZE_STATUS.freeze_performed = true` |
| Verify | `verify_ok = true` |

## Final verdict

**PASS — DOCUMENT IDENTITY / TEXTUAL PRESENCE ONLY**

Reason recorded in lifecycle: `ALL_REQUIRED_VECTORS_PASS`.

## Scope limitation

PASS applies **only** to:

1. SHA-256 identity of frozen Source A (`aurora_overflow_manifest.md`)
2. Observable textual presence of the author-stated string `Checksum: 1.00000 Permanent Flow` in those bytes

This audit does **not** assert:

- That `1.00000 Permanent Flow` is a cryptographic checksum/digest
- Aurora / ZOREL civic truth
- Historical claims
- Frequency validation (including 777 Hz)
- 3×3 / 6×6 / 9×9 mechanism function
- Civic / economic implementation
- Any unsupported claim verification

**HASH MATCH ≠ CONTENT TRUTH.**  
**AUTHOR-STATED CHECKSUM ≠ CRYPTOGRAPHIC DIGEST.**  
**INDIVIDUAL AUDIT PASS ≠ AURORA COMPLETE.**

## Canonical paths

| Role | Path |
| --- | --- |
| Canonical run | `aurora_audit/runs/WFA-20260915T043650Z-C49CA863` |
| Canonical frozen package | `aurora_audit/runs/WFA-20260915T043650Z-C49CA863/freeze/WFA-20260915T043650Z-C49CA863_FROZEN` |

## Frozen package identity

| Artifact | Digest |
| --- | --- |
| Frozen package `SHA256SUMS.txt` digest (`FREEZE_STATUS.sha256sums_digest`) | `2c0abec238b749811c0bd19793df751721d9f81a9cfbea3e73d0f5d94bf63643` |
| Frozen `MANIFEST.json` SHA-256 | `5edf8f7f4dd0b1442a9b71203828a17f1f7cfe66611d478af2bf9715d5c06cf8` |
| `FINAL_DECISION.json` SHA-256 | `3d0dc52d57c0dc40606c2377b79fda261fe601d5971812849d5c5cbcfd8e8eab` |
| `FINAL_EVIDENCE_INDEX.json` SHA-256 | `bb443ecaa6048e39bfce3daa0dd454f818c9c94218b6ce3462ac05133ae7ca0f` |

## Material blockers

**none**

## Related non-canonical references

- Request artifact: `aurora_audit/audits/AUR-A-002/AUR_A_002_REQUEST.json`
- Index entry: `aurora_audit/AUDIT_INDEX.md`
