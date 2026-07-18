# Verdict — xAI Grok Build

| Field | Value |
|-------|-------|
| Target slug | `grok-build` |
| Verdict status | **Narrow check+build PASS; overall PARTIAL** |
| Issued by | Weaver Forge documentation package author |
| Role | Owner-side evaluator (not independent witness) |
| Verdict date | `2026-07-18` |
| Source pin | **`98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce`** |

---

## Multi-axis

| Axis | Verdict | Notes |
|------|---------|-------|
| Source authenticity | `PASS` | |
| Artifact integrity | `PARTIAL` | No publisher digests; local binary hash recorded only as owner-side build |
| Build reproducibility | **`PARTIAL`** | Successful check + incremental build; not clean-room/bit-identical/repeat |
| Functional reproducibility | `NOT_STARTED` | Binary **not** executed |
| Claim verification | `PARTIAL` | C-013/C-018 PASS; C-012/C-014 open; C-015 BLOCKED |
| Security | `NOT_STARTED` | |
| Independent witness | `NOT_STARTED` | |
| Operational readiness | `NOT_STARTED` | |
| Windows readiness | `BLOCKED` | |
| Docker/bootstrap | `PASS` | |
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

## Produced binary (owner-side; not official release)

- `xai-grok-pager` 600647920 bytes
- SHA-256 `1efcd864606d3894b685ed3ec8c6b23e7e0aceeabdc04c4c8fc991c65df4389b`
- Path under external work target only; **not run**

---

**Witness is attestation, not authority.**
