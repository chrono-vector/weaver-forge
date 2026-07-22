# Verdict — xAI Grok Build

| Field | Value |
|-------|-------|
| Target slug | `grok-build` |
| Verdict status | **Narrow check+build+clean-rebuild PASS; static startup PARTIAL; overall PARTIAL** |
| Issued by | Weaver Forge documentation package author |
| Role | Owner-side evaluator (not independent witness) |
| Verdict date | `2026-07-22` (C2D-1) |
| Source pin | **`98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce`** |

---

## Multi-axis

| Axis | Verdict | Notes |
|------|---------|-------|
| Source authenticity | `PASS` | |
| Artifact integrity | `PARTIAL` | Local hashes only; two owner-side artifacts with different digests |
| Owner-side narrow rebuild | **`PASS`** | C2D-1 clean non-incremental second build exit 0 |
| Build reproducibility | **`PARTIAL`** | Owner-side clean rebuild succeeded; **not** bit-identical; no independent witness |
| Functional reproducibility | `NOT_STARTED` | Product not executed in C2D-1 |
| Claim verification | `PARTIAL` | C-013/C-018/C-020 PASS; C-019 PARTIAL; C-012/C-014 open; C-015 BLOCKED |
| Security | `NOT_STARTED` | |
| Independent witness | `NOT_STARTED` | |
| Operational readiness | `NOT_STARTED` | |
| Windows readiness | `BLOCKED` | |
| Docker/bootstrap | `PASS` | |
| Static startup boundary | **`PARTIAL`** | C2C-1 whole-session |
| **Overall** | **`PARTIAL`** | Never overall PASS |

## Claim rollup

| ID | Status |
|----|--------|
| C-001–C-011 | PASS (docs) |
| C-012 | NOT_STARTED |
| C-013 | PASS (cargo check) |
| C-014 | NOT_STARTED |
| C-015 | BLOCKED |
| C-016–C-017 | PASS |
| C-018 | PASS (narrow build, incremental) |
| C-019 | PARTIAL (static startup) |
| C-020 | **PASS** (clean non-incremental rebuild; not bit-identical) |

## Artifacts (owner-side; not official release)

| Build | Size | SHA-256 |
|-------|-----:|---------|
| C2B-4 incremental | 600647920 | `1efcd864606d3894b685ed3ec8c6b23e7e0aceeabdc04c4c8fc991c65df4389b` |
| C2D-1 clean | 600515304 | `eebdbe81a8fc34645a2f3c72aad36825d692fbef594a6c540f77ffaa42c18dad` |

Bit-identical: **NOT OBSERVED**. Product binary not executed in C2D-1.

---

**Witness is attestation, not authority.**
