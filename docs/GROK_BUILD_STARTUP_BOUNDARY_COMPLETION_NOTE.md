# Completion Note — Grok Build Phase C2C-1: Static Startup Boundary (corrected)

| Field | Value |
|-------|-------|
| Phase | **C2C-1** (static startup boundary) |
| Date | 2026-07-22 |
| Correction | documentation-only whole-session disclosure |
| Weaver HEAD (package base) | `73b60ddfb9835251cfe062f37bf43ed53b7b3745` |
| Source pin | `98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce` |
| Artifact SHA-256 | `1efcd864606d3894b685ed3ec8c6b23e7e0aceeabdc04c4c8fc991c65df4389b` |
| Classification | **STATIC STARTUP PARTIAL** |
| C-019 | **PARTIAL** |
| Evidence | `external_verifications/grok-build/evidence/startup-boundary/` only |
| Draft evidence dir | `evidence/safe-startup/` — **does not exist** (already discarded) |

---

## Conservative statement

The fixed C2B-4 binary returned version/help-family responses during an earlier **non-conformant** isolated draft attempt. That attempt exceeded the one-invocation authorization and produced disposable-home filesystem side effects. Subsequent source inspection showed that CLI parsing occurs only after application initialization, so no product invocation was authorized during the final gated procedure. The static startup boundary therefore remains **PARTIAL**.

## Whole-session chronology

1. **Draft (non-conformant):** six product CLI commands (`--version`, `-V`, `version`, `version --json`, `--help`, `-h`) under Docker `--network=none` and disposable `HOME=/work/c2c1-home`; all exited 0; version `grok 0.2.102 (98c3b24)`; writes under `$HOME/.grok`.
2. **Discard:** draft package noise and `evidence/safe-startup/` removed.
3. **Final gate:** static inspect + source safety analysis; product **not** re-executed.

## Classifications

| Item | Classification |
|------|----------------|
| Draft CLI observational result | PASS |
| External network isolation (draft) | PASS WITH STRUCTURAL LIMITS |
| Product authentication (draft version/help) | NOT REQUESTED / NOT REQUIRED |
| Filesystem-side-effect-free startup | FAIL |
| Protocol conformance | FAIL |
| Final gated execution | NOT EXECUTED — SAFETY GATE NOT SATISFIED |
| Safe pre-initialization CLI boundary | NOT ESTABLISHED |
| Static startup boundary | STATIC STARTUP PARTIAL |
| Overall verification | PARTIAL |

## Multi-axis (not upgraded by C2C-1)

| Axis | Status |
|------|--------|
| Source authenticity | PASS (prior) |
| Build (check/build) | PASS narrow (prior C2B-3/4) |
| Functional | **NOT_STARTED** |
| Security | **NOT_STARTED** |
| Operational / production readiness | **NOT_STARTED** |
| Independent witness | **NOT_STARTED** |
| Windows readiness | **BLOCKED** |
| Static startup boundary | **PARTIAL** |
| Overall | **PARTIAL** |

## What this phase does not verify

Normal TUI startup; login/OAuth; agent/prompts/models; update; API connectivity; functional correctness; service/production readiness; security; absence of network syscalls; filesystem-side-effect-free startup; clean-room/bit-identical rebuild; Windows native readiness.

---

**Evidence before authority. Draft observational success ≠ protocol PASS ≠ overall PASS.**
