# Aurora Audit Index

**Canonical index for:** `aurora_audit/`  
**Updated (UTC):** `2026-09-15T04:50:00Z`  
**Rule:** Each completed individual audit is indexed here. Index entries reference `runs/` evidence; they do not replace it. Sandbox/protocol records reference harness results and are **not** Weaver lifecycle PASS packages.

## Entry schema (required for every future entry)

| Field | Description |
| --- | --- |
| Claim ID | e.g. `AUR-A-00N` |
| Weaver Audit ID | `WFA-…` lifecycle audit id (or `none`) |
| Target | Pinned/frozen path evaluated |
| Classification | Intake / claim-type classification (≠ verdict) |
| Verification mechanism | Adapter / method used |
| Status | e.g. `COMPLETED`, `IN_PROGRESS`, `BLOCKED`, `INCONCLUSIVE` |
| Verdict | Lifecycle / human-accepted outcome (or none) |
| Canonical evidence path | Path under `runs/` or sandbox harness |
| Package/manifest digest | Frozen package digest where supported |
| Material blockers | Blocking issues, or `none` |

## Completed Weaver lifecycle audits

### AUR-A-001

| Field | Value |
| --- | --- |
| Claim ID | `AUR-A-001` |
| Weaver Audit ID | `WFA-20260915T042439Z-8BE7790F` |
| Target | `aurora_audit/frozen_sources/aurora_overflow_manifest.md` (Source A) |
| Classification | `A_DOCUMENT_PROVENANCE` — DOCUMENT IDENTITY ONLY (`hash_claim` / `CLAIM_SUPPORTED_PARTIAL` on pass; not content-truth) |
| Verification mechanism | Weaver `hash_claim` lifecycle (`verify_digest`) + required vectors + human review |
| Status | `COMPLETED` |
| Verdict | `PASS` — DOCUMENT IDENTITY ONLY |
| Canonical evidence path | `aurora_audit/runs/WFA-20260915T042439Z-8BE7790F` |
| Canonical frozen package | `aurora_audit/runs/WFA-20260915T042439Z-8BE7790F/freeze/WFA-20260915T042439Z-8BE7790F_FROZEN` |
| Package/manifest digest | Frozen `SHA256SUMS.txt` digest `5b5b695a50bf03b98bffad8027ad753f719b5ef9ddff82d4f4850fa98bc6c8ae`; `MANIFEST.json` SHA-256 `4e2e8a3faa20b64e9a7db8d75f3941aeae2b0a4e0d455c289532e235eb667e2a` |
| Material blockers | `none` |
| Human-readable record | `aurora_audit/audits/AUR-A-001/AUDIT_RECORD.md` |

### AUR-A-002

| Field | Value |
| --- | --- |
| Claim ID | `AUR-A-002` |
| Weaver Audit ID | `WFA-20260915T043650Z-C49CA863` |
| Target | `aurora_audit/frozen_sources/aurora_overflow_manifest.md` (Source A) |
| Classification | `A_DOCUMENT_PROVENANCE` — DOCUMENT IDENTITY / TEXTUAL PRESENCE ONLY (`hash_claim`; author-stated checksum ≠ cryptographic digest) |
| Verification mechanism | Weaver `hash_claim` lifecycle (`verify_digest`) + required vectors + human review + textual presence observation |
| Status | `COMPLETED` |
| Verdict | `PASS` — DOCUMENT IDENTITY / TEXTUAL PRESENCE ONLY |
| Canonical evidence path | `aurora_audit/runs/WFA-20260915T043650Z-C49CA863` |
| Canonical frozen package | `aurora_audit/runs/WFA-20260915T043650Z-C49CA863/freeze/WFA-20260915T043650Z-C49CA863_FROZEN` |
| Package/manifest digest | Frozen `SHA256SUMS.txt` digest `2c0abec238b749811c0bd19793df751721d9f81a9cfbea3e73d0f5d94bf63643`; `MANIFEST.json` SHA-256 `5edf8f7f4dd0b1442a9b71203828a17f1f7cfe66611d478af2bf9715d5c06cf8` |
| Material blockers | `none` |
| Human-readable record | `aurora_audit/audits/AUR-A-002/AUDIT_RECORD.md` |

## Sandbox / protocol records (not Weaver lifecycle PASS)

| Claim ID | Status | Verdict | Evidence | Record |
| --- | --- | --- | --- | --- |
| AUR-A-005 | INCONCLUSIVE (civic); protocol sim executed | none (civic) | `sandbox_harness/results/HARNESS_RESULT_LATEST.json` | `audits/AUR-A-005/AUDIT_RECORD.md` |
| AUR-A-009 | INCONCLUSIVE (civic); protocol sim executed | none (civic) | same harness | `audits/AUR-A-009/AUDIT_RECORD.md` |
| AUR-A-012 | INCONCLUSIVE (civic); protocol sim executed | none (civic) | same harness | `audits/AUR-A-012/AUDIT_RECORD.md` |
| AUR-A-018 | INCONCLUSIVE (civic); protocol sim executed | none (civic) | same harness | `audits/AUR-A-018/AUDIT_RECORD.md` |
| AUR-A-021 | READY_FOR_SANDBOX | none | `pilots/3x3/AURORA_3X3_PILOT_SPEC.md` | `audits/AUR-A-021/AUDIT_RECORD.md` |

## Triaged only (see matrix)

Remaining claims AUR-A-003,004,006,007,008,010,011,013–017,019,020,022, AUR-B-REL-001: intake route preserved; no unsupported promotion to PASS. Dashboard: `aurora_audit/AURORA_VERIFICATION_MATRIX.md`.

## Overall Aurora status

**INDIVIDUAL AUDIT PASS ≠ AURORA COMPLETE.**  
Two document-identity PASSes do not freeze or complete the overall Aurora audit. `final/` remains reserved and empty of completion packages. Protocol harness results are not real-world validation.
