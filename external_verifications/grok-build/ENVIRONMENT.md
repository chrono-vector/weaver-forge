# Environment Identity — xAI Grok Build

| Field | Value |
|-------|-------|
| Target slug | `grok-build` |
| Environment record status | **Readiness inspection complete; build env `BLOCKED`** |
| Recorded by | Weaver Forge documentation package author |
| Role | Owner-side inspector (not independent witness) |
| Record date | 2026-07-17 |
| Pinned target commit | `98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce` |
| Evidence | `evidence/environment-readiness/` (canonical Phase C1) |
| Phase C2 readiness | **`BLOCKED`** |

---

## 1. Host Platform

| Field | Value |
|-------|-------|
| OS | Microsoft Windows 11 Home |
| Version / build | 10.0.26200 / Build 26200 (NT 10.0.26200.0) |
| Architecture | 64-bit |
| Documented build-host fit | Windows source builds **best-effort; not currently tested from this tree** (README at pin) |

## 2. Shell

| Field | Value |
|-------|-------|
| Shell | Windows PowerShell 5.1.26100.8875 (Desktop) |

## 3. Toolchain inventory (read-only)

See `evidence/environment-readiness/HOST_TOOLCHAIN_INVENTORY.txt`.

| Tool | Available | Version / note |
|------|-----------|----------------|
| git | Yes | 2.53.0.windows.3 |
| rustc | **No** | command not found |
| cargo | **No** | command not found |
| rustup | **No** | command not found |
| cl (MSVC) | **No** | not found |
| cmake / ninja / make / perl / pkg-config | **No** | not found |
| python | Yes | 3.14.3 (not a documented build prereq) |
| node / npm | Yes | v24.14.1 / 11.11.0 (not documented build prereqs) |
| DotSlash | **No** | not on PATH |
| protoc on PATH | **No** | |
| Docker | Yes | 29.4.3 (unused) |

## 4. Windows compiler / SDK

See `WINDOWS_BUILD_READINESS.md`.

| Check | Result |
|-------|--------|
| vswhere | Missing |
| Visual Studio / Build Tools install dirs | Not present |
| Windows Kits 10 | Not present |
| VC/SDK env vars | Unset |

## 5. Target pin toolchain (docs)

| Field | Value |
|-------|-------|
| rust-toolchain.toml channel | **1.92.0** |
| Components | rustfmt, clippy |
| Workspace edition | **2024** |
| Lockfile | present |

## 6. Isolation

| Field | Value |
|-------|-------|
| Source path | `C:\dev\external-verification-targets\grok-build` (unchanged this phase) |
| Planned `CARGO_TARGET_DIR` | `C:\dev\external-verification-work\grok-build-98c3b24\target` (not created) |
| VM/container prepared | No |

## 7. Credentials / network

| Field | Value |
|-------|-------|
| Product/API credentials used | **No** |
| Network used for cargo/deps | **No** (static inspection only) |
| Future first build network | Likely required (registry + git + DotSlash) |

## 8. Environment readiness verdict

| Field | Value |
|-------|-------|
| Environment readiness | **`BLOCKED`** |
| Rationale | Missing rustup/cargo/rustc, DotSlash, MSVC/Windows SDK; Windows best-effort host |

## 9. What this proves / does not prove

**Proves:** Current host inventory vs documented prereqs; pin still clean.
**Does not prove:** Build success, functional behavior, security, independent witness.

## Change Log

| Date | Change |
|------|--------|
| 2026-07-17 | Phase B / C1 notes |
| 2026-07-17 | Full Windows readiness inventory (`BLOCKED`) |

---

**Evidence before authority.**
