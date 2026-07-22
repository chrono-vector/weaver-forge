# Completion Note — Grok Build Phase C2D-2: Static Artifact Variance Analysis

| Field | Value |
|-------|-------|
| Phase | **C2D-2** |
| Date | 2026-07-22 |
| Weaver HEAD | `b3e432f2c9887b04908faaf6afe15f240bd80ce9` |
| Classification | **ARTIFACT VARIANCE ANALYSIS PASS** |
| Root-cause confidence | **ROOT_CAUSE_LIKELY** |
| Claim | **C-021** |
| Evidence | `external_verifications/grok-build/evidence/artifact-variance/` |
| Product executed | **No** |
| Cargo / rebuild | **No** |

---

## Artifacts

| | C2B-4 | C2D-1 |
|--|-------|-------|
| Path | `...\cargo-target\debug\xai-grok-pager` | `...\c2d1-clean-rebuild\cargo-target\debug\xai-grok-pager` |
| Size | 600647920 | 600515304 |
| SHA-256 | `1efcd864…f4389b` | `eebdbe81…c18dad` |
| Build ID | `29e028f3…` | `989dd4be…` |

## Key static results

- Sections: **15 identical / 30 differing**
- **`.text` hash and size differ** (not executable-text-identical)
- NEEDED libraries identical; no RPATH/RUNPATH
- The GNU Build IDs differ, confirming that the linked ELF outputs are distinct (observed identifier of variance, **not** an independently established root cause)
- Embedded paths: old `/work/cargo-target/...` vs new `/work/cargo-target-c2d1/...`
- Debug/string/symbol tables differ widely

## Interpretation

Static comparison completed. Distinct absolute target-directory paths are a **supported likely contributor** to at least some debug/string metadata variance. Executable text, relocation, and layout metadata also differ across the two documented build contexts; the analysis does **not** isolate whether that resulted from incremental state, cached dependency artifacts, absolute paths, link ordering, build-environment variation, or a combination. A unique root cause for every differing byte is **not** established.

## Unchanged axes

Functional, Security, Operational readiness, Independent Witness, Windows readiness remain not upgraded. Overall **PARTIAL**.

---

**Evidence before authority. Static variance analysis ≠ functional equivalence ≠ bit-reproducibility claim.**
