# Environment Identity — xAI Grok Build

| Field | Value |
|-------|-------|
| Target slug | `grok-build` |
| Environment record status | `NOT_STARTED` |
| Recorded by | Weaver Forge documentation package author |
| Role | Owner-side planner (not independent witness) |
| Record date | `2026-07-17` |
| Tied to reproduction run ID | *none — no reproduction authorized* |

Capture environment **before** or **at the start of** reproduction. Do not backfill invented values.

**This file is a shell only.** No verification run has been performed. Host details of the package author's machine are **not** claimed as a Grok Build reproduction environment.

---

## 1. Host Platform

| Field | Value |
|-------|-------|
| OS name | *not recorded for a Grok Build run* |
| OS version | |
| OS build / kernel | |
| Architecture | |
| Hostname (optional / redacted) | |
| Machine class | |

Status: `NOT_STARTED`

## 2. Shell

| Field | Value |
|-------|-------|
| Shell name | |
| Shell version | |
| Login vs non-login notes | |

Status: `NOT_STARTED`

## 3. CPU / GPU

| Field | Value |
|-------|-------|
| CPU model | |
| CPU cores / threads | |
| CPU flags relevant to target (if any) | |
| GPU model | |
| GPU driver / CUDA / ROCm (if any) | |
| GPU status | `NOT_STARTED` |

## 4. Language and Runtime Versions

| Runtime | Version command | Observed version | Status |
|---------|-----------------|------------------|--------|
| *to be filled from official Grok Build requirements when known* | | | `NOT_STARTED` |

## 5. Package-Manager Versions

| Tool | Version command | Observed version | Status |
|------|-----------------|------------------|--------|
| | | | `NOT_STARTED` |

## 6. Dependency-Lock Identity

| Field | Value |
|-------|-------|
| Lockfile path(s) | *unknown — target not acquired* |
| Lockfile hash (algorithm + value) | *not invented* |
| Lockfile status | `NOT_STARTED` |
| Install command (documented) | *unknown* |
| Install command (actually used) | *none* |
| Deviation from lock? | N/A |

## 7. Environment Variables

| Variable | Set? | Value or redaction policy | Required by target docs? |
|----------|------|---------------------------|--------------------------|
| *none recorded* | | | Unknown |

## 8. Precision Mode

| Field | Value |
|-------|-------|
| Floating-point mode / flags | |
| Mixed precision settings | |
| Determinism flags | |
| Status | `NOT_STARTED` / may become `NOT_APPLICABLE` after docs review |

## 9. Random Seed

| Field | Value |
|-------|-------|
| Seed required by procedure? | Unknown |
| Seed value(s) | |
| Seed source | `NOT_APPLICABLE` until procedure known |
| Status | `NOT_STARTED` |

## 10. Network Requirements

| Field | Value |
|-------|-------|
| Network required? | Likely yes for clone (planned); not executed |
| Endpoints needed | `https://github.com/xai-org/grok-build` (planned) |
| Offline mode possible? | Unknown |
| Proxy / firewall constraints | |
| Network status during run | `NOT_STARTED` (no run) |

## 11. Credentials and Authentication Boundaries

| Field | Value |
|-------|-------|
| Credentials required? | Unknown (prefer public clone when authorized) |
| Credential types | none planned for public read |
| Where credentials are stored | N/A |
| Auth boundary | public-only preferred |
| Credentials used in this run? | **No** (no run) |
| Status | `NOT_STARTED` |

## 12. Sandbox or Isolation Method

| Field | Value |
|-------|-------|
| Isolation method | *to be chosen at execution time* |
| Image or base environment ID | |
| Working directory root | |
| Privilege level | |
| Isolation status | `NOT_STARTED` |

## 13. Toolchain Snapshot Commands

```text
# Not executed. Placeholders for a future authorized run only:
# git --version
# <language runtime> --version
# <package manager> --version
```

| Command | Exit code | Output preserved at | Status |
|---------|-----------|---------------------|--------|
| | | | `NOT_STARTED` |

## 14. Environment Risks

| Risk ID | Description | Impact on reproducibility |
|---------|-------------|---------------------------|
| ER-001 | Requirements unknown until official docs observed | Cannot prepare matching environment yet |
| ER-002 | No isolation plan frozen | Future runs may differ silently |
| ER-003 | Execution currently unauthorized | Environment identity cannot advance past `NOT_STARTED` |

## 15. What This Environment Record Proves

- That environment capture is required before a credible reproduction and has not yet been performed for Grok Build under this package.

## 16. What This Environment Record Does NOT Prove

- Any fact about a machine that ran Grok Build
- Correctness of the target
- Completeness of hidden dependencies
- That another machine will match a future environment
- Independent witness confirmation
- Security of any host

## Change Log

| Date | Change | Author |
|------|--------|--------|
| 2026-07-17 | Initial environment shell; no run | Weaver Forge documentation package author |

---

**Evidence before authority.**
