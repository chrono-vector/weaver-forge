# Verdict — xAI Grok Build

| Field | Value |
|-------|-------|
| Target slug | `grok-build` |
| Verdict status | **Narrow build/check/clean-rebuild PASS; variance analysis PASS; static startup PARTIAL; overall PARTIAL** |
| Issued by | Weaver Forge documentation package author |
| Role | Owner-side evaluator (not independent witness) |
| Verdict date | `2026-07-22` (C2D-2) |
| Source pin | **`98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce`** |

---

## Multi-axis

| Axis | Verdict | Notes |
|------|---------|-------|
| Source authenticity | `PASS` | |
| Artifact integrity | `PARTIAL` | Two owner-side hashes; no publisher digests |
| Owner-side narrow rebuild | `PASS` | C2D-1 |
| Build reproducibility | **`PARTIAL`** | Clean rebuild OK; not bit-identical; path metadata a supported partial contributor; unique full cause not established; no witness |
| Functional | `NOT_STARTED` | |
| Security | `NOT_STARTED` | |
| Independent witness | `NOT_STARTED` | |
| Operational readiness | `NOT_STARTED` | |
| Windows readiness | `BLOCKED` | |
| Static startup boundary | `PARTIAL` | C2C-1 |
| Artifact variance analysis | **`PASS`** | C2D-2 static only |
| **Overall** | **`PARTIAL`** | |

## Claim rollup

| ID | Status |
|----|--------|
| C-001–C-011 | PASS (docs) |
| C-012 | NOT_STARTED |
| C-013 | PASS |
| C-014 | NOT_STARTED |
| C-015 | BLOCKED |
| C-016–C-018 | PASS |
| C-019 | PARTIAL |
| C-020 | PASS (clean rebuild) |
| C-021 | **PASS** (variance analysis completed; ROOT_CAUSE_LIKELY = partial contribution only) |

## Artifacts

| Build | Size | SHA-256 | `.text` |
|-------|-----:|---------|---------|
| C2B-4 | 600647920 | `1efcd864…` | differs from C2D-1 |
| C2D-1 | 600515304 | `eebdbe81…` | differs from C2B-4 |

Embedded paths: `/work/cargo-target/...` (old) vs `/work/cargo-target-c2d1/...` (new). Product not executed in C2D-2.

---

**Witness is attestation, not authority.**
