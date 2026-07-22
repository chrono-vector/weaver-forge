# Completion Note — Grok Build Phase C2D-1: Clean Non-Incremental Rebuild

| Field | Value |
|-------|-------|
| Phase | **C2D-1** |
| Date | 2026-07-22 |
| Weaver HEAD (base) | `673e393f9349af1d04485b7c17d69ea9cc839060` |
| Source pin | `98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce` |
| Image | `docker.io/library/rust@sha256:6ca5ad23231207874325a751b9df584d51cd42c066c74c6963c264e3233c3e8e` |
| Classification | **CLEAN REBUILD PASS** |
| Bit-identical | **BIT_IDENTICAL_NOT_OBSERVED** |
| Product executed | **No** |
| Evidence | `external_verifications/grok-build/evidence/clean-rebuild/` |

---

## Command (successful run)

```text
cargo build -p xai-grok-pager-bin --locked -j 2
CARGO_INCREMENTAL=0
CARGO_TARGET_DIR=<new empty phase dir>
```

Exit **0** in **85m 21s**. New empty target (C2B-4 target not mounted). Dependency registry cache reused (disclosed). Network bridge available (disclosed).

## Artifacts

| | C2B-4 (prior) | C2D-1 (new) |
|--|---------------|-------------|
| Name | `xai-grok-pager` | `xai-grok-pager` |
| Size | 600647920 | **600515304** |
| SHA-256 | `1efcd864…f4389b` | `eebdbe81…c18dad` |
| Match | — | **hash no; size no** |
| Format | ELF x86-64 pie | same class |

## Multi-axis

| Axis | Status |
|------|--------|
| Owner-side narrow rebuild | **PASS** |
| Build reproducibility overall | **PARTIAL** (no witness; not bit-identical) |
| Functional / security / ops / witness / Windows | **unchanged** |
| Overall | **PARTIAL** |

## What this does not verify

Application functionality, startup, authentication, API connectivity, security, production readiness, Windows-native readiness, independent witness, universal bit-for-bit reproducibility.

---

**Evidence before authority. Second owner-side success ≠ bit-identical ≠ overall PASS.**
