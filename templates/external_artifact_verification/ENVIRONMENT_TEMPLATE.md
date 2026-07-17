# Environment Identity — [TARGET NAME]

| Field | Value |
|-------|-------|
| Target slug | `[target-slug]` |
| Environment record status | `NOT_STARTED` |
| Recorded by | |
| Role | Owner-side / Independent witness |
| Record date | `YYYY-MM-DD` |
| Tied to reproduction run ID | (link to REPRODUCTION.md section when known) |

Capture environment **before** or **at the start of** reproduction. Do not backfill invented values.

---

## 1. Host Platform

| Field | Value |
|-------|-------|
| OS name | |
| OS version | |
| OS build / kernel | |
| Architecture | x86_64 / arm64 / other |
| Hostname (optional / redacted) | |
| Machine class | laptop / desktop / CI / VM / container / other |

## 2. Shell

| Field | Value |
|-------|-------|
| Shell name | bash / zsh / PowerShell / cmd / other |
| Shell version | |
| Login vs non-login notes | |

## 3. CPU / GPU

| Field | Value |
|-------|-------|
| CPU model | |
| CPU cores / threads | |
| CPU flags relevant to target (if any) | |
| GPU model | none / … |
| GPU driver / CUDA / ROCm (if any) | |
| GPU status | `NOT_APPLICABLE` / recorded / `NOT_STARTED` |

## 4. Language and Runtime Versions

| Runtime | Version command | Observed version | Status |
|---------|-----------------|------------------|--------|
| | | | `NOT_STARTED` |

Examples to include when relevant: Python, Node, Java, Rustc, Go, .NET, CUDA toolkit.

## 5. Package-Manager Versions

| Tool | Version command | Observed version | Status |
|------|-----------------|------------------|--------|
| | | | `NOT_STARTED` |

Examples: pip, npm, pnpm, yarn, cargo, go, apt, brew, winget, conda.

## 6. Dependency-Lock Identity

| Field | Value |
|-------|-------|
| Lockfile path(s) | |
| Lockfile hash (algorithm + value) | |
| Lockfile status | present / missing / `NOT_STARTED` / `NOT_APPLICABLE` |
| Install command (documented) | |
| Install command (actually used) | |
| Deviation from lock? | No / Yes (describe) |

## 7. Environment Variables

Record only variables that affect the verification. **Redact secrets.** Prefer names + whether set, not secret values.

| Variable | Set? | Value or redaction policy | Required by target docs? |
|----------|------|---------------------------|--------------------------|
| | Yes / No | `[REDACTED]` / value / unset | Yes / No / Unknown |

## 8. Precision Mode

| Field | Value |
|-------|-------|
| Floating-point mode / flags | |
| Mixed precision settings | |
| Determinism flags | |
| Status | `NOT_STARTED` / `NOT_APPLICABLE` / recorded |

## 9. Random Seed

| Field | Value |
|-------|-------|
| Seed required by procedure? | Yes / No / Unknown |
| Seed value(s) | |
| Seed source | documented / chosen by operator / `NOT_APPLICABLE` |
| Status | `NOT_STARTED` / `NOT_APPLICABLE` / recorded |

## 10. Network Requirements

| Field | Value |
|-------|-------|
| Network required? | Yes / No / Partial |
| Endpoints needed | |
| Offline mode possible? | Yes / No / Unknown |
| Proxy / firewall constraints | |
| Network status during run | online / offline / restricted / `NOT_STARTED` |

## 11. Credentials and Authentication Boundaries

| Field | Value |
|-------|-------|
| Credentials required? | Yes / No / Unknown |
| Credential types | API key / OAuth / SSH / none / other |
| Where credentials are stored | (path or secret manager — never paste secrets) |
| Auth boundary | public-only / authenticated read / write access |
| Credentials used in this run? | No / Yes |
| Status | `NOT_STARTED` / `NOT_APPLICABLE` / recorded |

**Rule:** Prefer public, credential-free verification when the target allows it. If credentials are required, state what cannot be reproduced without them.

## 12. Sandbox or Isolation Method

| Field | Value |
|-------|-------|
| Isolation method | none / venv / container / VM / sandbox / other |
| Image or base environment ID | |
| Working directory root | |
| Privilege level | user / admin / root |
| Isolation status | `NOT_STARTED` / recorded / `NOT_APPLICABLE` |

## 13. Toolchain Snapshot Commands

List exact commands used to capture versions (paste outputs into evidence store or appendix).

```text
# Example placeholders — replace with actual commands when run
# python --version
# git --version
```

| Command | Exit code | Output preserved at | Status |
|---------|-----------|---------------------|--------|
| | | | `NOT_STARTED` |

## 14. Environment Risks

| Risk ID | Description | Impact on reproducibility |
|---------|-------------|---------------------------|
| ER-001 | | |

## 15. What This Environment Record Proves

```text
[Only that environment fields were captured as stated — not that the target works.]
```

## 16. What This Environment Record Does NOT Prove

- Correctness of the target
- Completeness of hidden dependencies
- That another machine will match this environment
- Independent witness confirmation
- Security of the host or supply chain

## Change Log

| Date | Change | Author |
|------|--------|--------|
| YYYY-MM-DD | Initial environment shell | |

---

**Evidence before authority.**
