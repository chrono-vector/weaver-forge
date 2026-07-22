# Startup Boundary Summary — Phase C2C-1 (corrected whole-session)

| Field | Value |
|-------|-------|
| Date | 2026-07-22 |
| Correction | documentation-only whole-session disclosure |
| Classification | **STATIC STARTUP PARTIAL** |
| Source pin | `98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce` |
| Artifact SHA-256 | `1efcd864606d3894b685ed3ec8c6b23e7e0aceeabdc04c4c8fc991c65df4389b` |
| Canonical evidence | `evidence/startup-boundary/` only |
| Draft evidence dir | `evidence/safe-startup/` — **does not exist** (already discarded) |

## Whole-session chronology

1. **Draft attempt:** product binary executed six times (version/help family) in Docker with network disabled and disposable `HOME=/work/c2c1-home`.
2. **Discard:** draft evidence and related package edits removed; clean Weaver baseline restored.
3. **Final gated procedure:** static inspection + source safety gate; **product not executed again**.

## Draft observations

| Item | Result |
|------|--------|
| Draft CLI observational result | **PASS** (all six exit 0) |
| Version string | `grok 0.2.102 (98c3b24)` |
| JSON version | `{"currentVersion":"0.2.102 (98c3b24)","channel":"unknown"}` |
| Help | exit 0; "Grok Build TUI" |
| Product auth | **NOT REQUESTED / NOT REQUIRED** for observed version/help |
| External network isolation | **PASS WITH STRUCTURAL LIMITS** (`--network=none`; no syscall proof) |
| Filesystem-side-effect-free startup | **FAIL** (writes under disposable `$HOME/.grok`) |
| Protocol conformance | **FAIL** (six invocations; max one authorized) |

Exact draft commands:

```text
/work/cargo-target/debug/xai-grok-pager --version
/work/cargo-target/debug/xai-grok-pager -V
/work/cargo-target/debug/xai-grok-pager version
/work/cargo-target/debug/xai-grok-pager version --json
/work/cargo-target/debug/xai-grok-pager --help
/work/cargo-target/debug/xai-grok-pager -h
```

## Protocol deviation

Authorization for the gated design allowed **at most one** product invocation after a passing safety gate. The draft ran **six** invocations before that gate and is therefore **non-conformant**. Draft isolation success is not protocol PASS.

## Final safety-gate analysis

CLI parsing occurs only after application initialization (`memory_trace::start`, `validate_requirements`, Sentry init, user-guide extraction, crash-handler / active_sessions bookkeeping, Tokio runtime). Therefore:

- Safe pre-initialization CLI boundary: **NOT ESTABLISHED**
- Final gated execution: **NOT EXECUTED — SAFETY GATE NOT SATISFIED**

## Filesystem side effects

Draft wrote under disposable `$HOME/.grok` (user-guide material; active_sessions). No claim of side-effect-free startup is permitted.

## Network observation limits

External network was structurally disabled during draft. Absence of network syscalls is **not** proven.

## Conservative classification

| Axis | Classification |
|------|----------------|
| Draft CLI observational | PASS |
| External network isolation (draft) | PASS WITH STRUCTURAL LIMITS |
| Product authentication (draft version/help) | NOT REQUESTED / NOT REQUIRED |
| Filesystem-side-effect-free startup | FAIL |
| Protocol conformance | FAIL |
| Final gated execution | NOT EXECUTED — SAFETY GATE NOT SATISFIED |
| Safe pre-initialization CLI boundary | NOT ESTABLISHED |
| Static startup boundary | **STATIC STARTUP PARTIAL** |
| C-019 | **PARTIAL** |
| Overall Grok Build verification | **PARTIAL** |

### Required conservative statement

The fixed C2B-4 binary returned version/help-family responses during an earlier non-conformant isolated draft attempt. That attempt exceeded the one-invocation authorization and produced disposable-home filesystem side effects. Subsequent source inspection showed that CLI parsing occurs only after application initialization, so no product invocation was authorized during the final gated procedure. The static startup boundary therefore remains PARTIAL.

## What remains unverified

- Normal TUI startup
- Login / OAuth
- Agent execution / prompts / model access
- Update behavior / API connectivity
- Functional correctness
- Service / production readiness
- Security
- Absence of network syscalls
- Filesystem-side-effect-free startup
- Clean-room or bit-identical rebuild
- Windows native readiness
- Independent witness

Do not upgrade Functional, Security, Operational readiness, Production readiness, Independent Witness, Windows readiness, Authentication, or Network functionality merely because draft help/version exited 0.
