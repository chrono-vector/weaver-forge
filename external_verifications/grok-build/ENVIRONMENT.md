# Environment Identity — xAI Grok Build

| Field | Value |
|-------|-------|
| Target slug | `grok-build` |
| Environment record status | **Windows host BLOCKED; Docker/Linux readiness PARTIAL (daemon stopped; image pin via registry)** |
| Recorded by | Weaver Forge documentation package author |
| Role | Owner-side inspector (not independent witness) |
| Record date | 2026-07-18 (C2A); prior C1 2026-07-17 |
| Pinned target commit | `98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce` |
| Evidence (Windows C1) | `evidence/environment-readiness/` |
| Evidence (Docker C2A) | `evidence/docker-readiness/` |
| Phase C2 (Windows native) | **`BLOCKED`** |
| Phase C2B (Linux container) | **`READY_WITH_LIMITATIONS`** (plan+image pin; daemon start + pull deferred) |

---

## 1. Host Platform

| Field | Value |
|-------|-------|
| OS | Microsoft Windows 11 Home |
| Version / build | 10.0.26200 / Build 26200 (NT 10.0.26200.0) |
| Architecture | 64-bit (amd64) |
| Documented build-host fit | Windows source builds **best-effort; not currently tested from this tree** (README at pin) |

## 2. Shell

| Field | Value |
|-------|-------|
| Shell | Windows PowerShell 5.1.26100.8875 (Desktop) |
| Process elevated | No (C2A observation) |

## 3. Toolchain inventory (Windows host, read-only)

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
| Docker client | Yes | **29.4.3** |
| Docker daemon | **No** | `com.docker.service` Stopped; pipe missing |

## 4. Windows compiler / SDK

See `WINDOWS_BUILD_READINESS.md`.

| Check | Result |
|-------|--------|
| vswhere | Missing |
| Visual Studio / Build Tools install dirs | Not present |
| Windows Kits 10 | Not present |
| VC/SDK env vars | Unset |

## 5. Docker / WSL (Phase C2A)

See `evidence/docker-readiness/DOCKER_HOST_INVENTORY.txt`, `WSL_BACKEND_STATUS.txt`.

| Field | Value |
|-------|-------|
| Docker client | 29.4.3 (windows/amd64) |
| Docker server/engine | **Unavailable** (daemon stopped) |
| Active context | `desktop-linux` |
| Container mode (intended) | Linux |
| Compose | v5.1.4 |
| buildx | v0.33.0-desktop.1 |
| WSL | 2.6.3.0; kernel 6.6.87.2-1 |
| Default WSL distro | Ubuntu (Stopped, WSL2) |
| docker-desktop distro | Stopped, WSL2 |
| Docker CPUs/memory/storage driver/security options | **Unknown** until daemon start |
| Client works without elevation | Yes (client-only commands) |

## 6. Pinned Linux container image (C2A)

See `CONTAINER_IMAGE_SELECTION.md`, `PINNED_IMAGE_METADATA.txt`.

| Field | Value |
|-------|-------|
| Registry / repo | `docker.io` / `library/rust` |
| Tag (reference) | `1.92.0` |
| **linux/amd64 platform manifest pin (pull/run)** | `sha256:6ca5ad23231207874325a751b9df584d51cd42c066c74c6963c264e3233c3e8e` |
| Multi-arch index digest | `sha256:f58923369ba295ae1f60bc49d03f2c955a5c93a0b7d49acfb2b2a65bebaf350d` |
| Config blob digest (metadata only; not pullable) | `sha256:45dfd6a3b0ca04ba914df344b1f01d32092a33c56b067f88d738e4707b8dbec7` |
| OS/Arch | linux/amd64 |
| Created (config) | 2026-01-13T06:12:13Z |
| Local pull | **Not performed** |
| Custom image | **Not built** |

## 7. Target pin toolchain (docs)

| Field | Value |
|-------|-------|
| rust-toolchain.toml channel | **1.92.0** |
| Components | rustfmt, clippy |
| Workspace edition | **2024** |
| Lockfile | present |

## 8. Isolation

| Field | Value |
|-------|-------|
| Source path | `C:\dev\external-verification-targets\grok-build` (unchanged this phase) |
| Planned work root | `C:\dev\external-verification-work\grok-build-98c3b24\` (not populated with build outputs) |
| Planned `CARGO_TARGET_DIR` | `...\grok-build-98c3b24\target` (outside source) |
| VM/container prepared | **Image identity pinned**; daemon not running; no container launched for compile |
| Isolation policy | `evidence/docker-readiness/DOCKER_ISOLATION_POLICY.md` |

## 9. Credentials / network

| Field | Value |
|-------|-------|
| Product/API credentials used | **No** |
| Network used for cargo/deps | **No** |
| Network used for registry metadata | **Yes** (Docker Hub / registry v2 API for digests only) |
| Future first build network | Required (registry + git + DotSlash + possibly apt) |

## 10. Environment readiness verdicts

| Axis / path | Verdict |
|-------------|---------|
| Windows host build readiness | **`BLOCKED`** |
| Docker/Linux build readiness | **`PARTIAL`** |
| Phase C2B readiness | **`READY_WITH_LIMITATIONS`** |

**Rationale (Docker/Linux PARTIAL):** Client, WSL2 backend install, and official `rust:1.92.0` digest pin are established; engine daemon is stopped so pull/run/resource fields and local image verify remain incomplete.

**Rationale (C2B READY_WITH_LIMITATIONS):** Copy-pasteable C2B plan exists with immutable image digest; operator must start Docker Desktop, pull the pin, and execute C2B-1+ under isolation policy. Not fully READY because daemon was not available to prove pull/run on this host during C2A.

## 11. What this proves / does not prove

**Proves:** Host Docker/WSL inventory; selected official image digests via registry metadata; static native/DotSlash plans; isolation and C2B procedure text.

**Does not prove:** Build success, functional behavior, security audit, independent witness, daemon-backed resource numbers, local image presence.

## Change Log

| Date | Change |
|------|--------|
| 2026-07-17 | Phase B / C1 notes |
| 2026-07-17 | Full Windows readiness inventory (`BLOCKED`) |
| 2026-07-18 | Phase C2A Docker/Linux readiness + image pin (`PARTIAL` / C2B `READY_WITH_LIMITATIONS`) |

---

**Evidence before authority.**
