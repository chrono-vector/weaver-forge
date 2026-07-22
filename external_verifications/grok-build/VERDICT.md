# Verdict — xAI Grok Build

| Field | Value |
|-------|-------|
| Target slug | `grok-build` |
| Verdict status | **Narrow check+build PASS; static startup PARTIAL; overall PARTIAL** |
| Issued by | Weaver Forge documentation package author |
| Role | Owner-side evaluator (not independent witness) |
| Verdict date | `2026-07-22` (C2C-1 corrected whole-session) |
| Source pin | **`98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce`** |

---

## Multi-axis

| Axis | Verdict | Notes |
|------|---------|-------|
| Source authenticity | `PASS` | |
| Artifact integrity | `PARTIAL` | No publisher digests; local binary hash recorded only as owner-side build |
| Build reproducibility | **`PARTIAL`** | Successful check + incremental build; not clean-room/bit-identical/repeat |
| Functional reproducibility | `NOT_STARTED` | Draft help/version is not functional product verification |
| Claim verification | `PARTIAL` | C-013/C-018 PASS; C-019 PARTIAL; C-012/C-014 open; C-015 BLOCKED |
| Security | `NOT_STARTED` | Not upgraded by C2C-1 |
| Independent witness | `NOT_STARTED` | |
| Operational readiness | `NOT_STARTED` | |
| Windows readiness | `BLOCKED` | |
| Docker/bootstrap | `PASS` | |
| Static startup boundary | **`PARTIAL`** | Draft help/version observed non-conformantly; pre-init boundary not established; final gate withheld |
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
| C-019 | **PARTIAL** (draft observations + final gate withhold; not PASS) |

## Produced binary (owner-side; not official release)

- `xai-grok-pager` 600647920 bytes
- SHA-256 `1efcd864606d3894b685ed3ec8c6b23e7e0aceeabdc04c4c8fc991c65df4389b`
- **Whole session:** six non-conformant draft version/help invocations (exit 0; side effects under disposable HOME); final gated procedure did **not** re-execute
- See `evidence/startup-boundary/WHOLE_SESSION_HISTORY.txt`

## Required conservative statement

The fixed C2B-4 binary returned version/help-family responses during an earlier non-conformant isolated draft attempt. That attempt exceeded the one-invocation authorization and produced disposable-home filesystem side effects. Subsequent source inspection showed that CLI parsing occurs only after application initialization, so no product invocation was authorized during the final gated procedure. The static startup boundary therefore remains PARTIAL.

---

**Witness is attestation, not authority.**
