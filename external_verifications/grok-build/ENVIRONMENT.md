# Environment Identity — xAI Grok Build

| Field | Value |
|-------|-------|
| Target slug | `grok-build` |
| Environment record status | **Inspection host recorded; build environment `NOT_STARTED`** |
| Recorded by | Weaver Forge documentation package author |
| Role | Owner-side inspector (not independent witness) |
| Record date | `2026-07-17` |
| Tied to reproduction run ID | Phase B clone/inspect only (`REPRODUCTION.md`) |
| Pinned target commit | `98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce` |

This record describes the **owner-side inspection host** used for git clone and static file reads. It is **not** a frozen build environment for cargo.

---

## 1. Host Platform (inspection)

| Field | Value |
|-------|-------|
| OS name | Windows |
| OS version | Windows 10 (build not re-verified this phase; prior Weaver audits used build 26200) |
| Architecture | x86_64 (host used for clone) |
| Machine class | desktop / workstation |

## 2. Shell

| Field | Value |
|-------|-------|
| Shell name | PowerShell |
| Shell version | host default (not required for pin fidelity) |

## 3. CPU / GPU

| Field | Value |
|-------|-------|
| GPU status | `NOT_APPLICABLE` for Phase B identity work |

## 4. Language and Runtime Versions

| Runtime | Version command | Observed version | Status |
|---------|-----------------|------------------|--------|
| Git | `git --version` | present on PATH (clone succeeded) | recorded for clone only |
| Rust / cargo | — | **not captured** (build not authorized) | `NOT_STARTED` |
| DotSlash | — | **not installed/checked for build** | `NOT_STARTED` |

## 5. Package-Manager Versions

| Tool | Status |
|------|--------|
| cargo / rustup | `NOT_STARTED` (build phase) |

## 6. Dependency-Lock Identity (target tree)

| Field | Value |
|-------|-------|
| Lockfile path(s) | `Cargo.lock` at repo root (in external clone) |
| Lockfile size | 353616 bytes |
| Lockfile SHA-256 | `1512bb4fef0c1166c6a15a3398da9593903be1759b759ce78d9958913e61b421` |
| Lockfile status | present at pin |
| Install command (documented) | implicit via `cargo` build commands (not run) |
| Deviation from lock? | N/A (no install) |

## 7. Environment Variables

| Variable | Set? | Notes |
|----------|------|-------|
| Product credentials / auth tokens | No | Auth not used; public clone only |
| `PROTOC` | unknown / unused | build not run |

## 8. Precision Mode

| Status | `NOT_APPLICABLE` (Phase B) |

## 9. Random Seed

| Status | `NOT_APPLICABLE` (Phase B) |

## 10. Network Requirements

| Field | Value |
|-------|-------|
| Network required for Phase B? | Yes (git clone; HTTPS fetch of official pages) |
| Endpoints used | github.com; x.ai; api.github.com |
| Offline mode | Not used |
| Network status during run | online |

## 11. Credentials and Authentication Boundaries

| Field | Value |
|-------|-------|
| Credentials required for public clone? | No |
| Auth boundary this phase | **public-only** |
| Credentials used? | **No** |
| Product auth (browser login) | Documented for first launch; **not exercised** |

## 12. Sandbox or Isolation Method

| Field | Value |
|-------|-------|
| Isolation method | External directory outside Weaver Forge tree |
| Working directory root | `C:\dev\external-verification-targets\grok-build` |
| Privilege level | user |
| Isolation status | recorded for clone path |

## 13. Documented target prerequisites (for future build phase; not installed)

From README at pin:

- Rust via `rust-toolchain.toml` channel **1.92.0**
- DotSlash on PATH before build
- protoc via `bin/protoc` / DotSlash or `$PROTOC`
- macOS/Linux preferred; Windows best-effort

## 14. Environment Risks

| Risk ID | Description | Impact |
|---------|-------------|--------|
| ER-001 | Inspection host ≠ future build host | Build phase must re-record full toolchain |
| ER-002 | Windows best-effort for source builds | May block or PARTIAL future Windows build claims |
| ER-003 | Network/DotSlash needs for hermetic tools | Offline builds may fail |

## 15. What This Environment Record Proves

- Clone/inspection was possible on this Windows PowerShell host without target credentials.

## 16. What This Environment Record Does NOT Prove

- That Rust/cargo/dotslash are installed or compatible
- That a build would succeed here
- Independent witness environment parity

## Change Log

| Date | Change | Author |
|------|--------|--------|
| 2026-07-17 | Shell only | Weaver Forge documentation package author |
| 2026-07-17 | Phase B inspection host + lockfile identity | Weaver Forge documentation package author |

---

**Evidence before authority.**
