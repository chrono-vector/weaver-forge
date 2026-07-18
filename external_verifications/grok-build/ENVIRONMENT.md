# Environment Identity — xAI Grok Build

| Field | Value |
|-------|-------|
| Target slug | `grok-build` |
| Environment record status | **Windows BLOCKED; bootstrap PASS; cargo check PASS (C2B-3)** |
| Recorded by | Weaver Forge documentation package author |
| Role | Owner-side inspector (not independent witness) |
| Record date | 2026-07-18 (C2B-3) |
| Pinned target commit | `98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce` |
| Evidence (Windows C1) | `evidence/environment-readiness/` |
| Evidence (Docker C2A) | `evidence/docker-readiness/` |
| Evidence (Container toolchain C2B-1) | `evidence/container-toolchain/` |
| Evidence (Container bootstrap C2B-2) | `evidence/container-bootstrap/` |
| Evidence (Cargo check C2B-3) | `evidence/cargo-check/` |
| Work root | `C:\dev\external-verification-work\grok-build-98c3b24\` |
| Phase C2 (Windows native) | **`BLOCKED`** |
| Phase C2B-1 (image + toolchain) | **`PASS`** |
| Phase C2B-2 (bootstrap) | **`PASS`** |
| Phase C2B-3 (cargo check) | **`PASS`** (exit 0; ~70m) |

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

See `evidence/environment-readiness/HOST_TOOLCHAIN_INVENTORY.txt` (C1; unchanged).

| Tool | Available | Version / note |
|------|-----------|----------------|
| git | Yes | 2.53.0.windows.3 |
| rustc | **No** | command not found on Windows host |
| cargo | **No** | command not found on Windows host |
| rustup | **No** | command not found |
| cl (MSVC) | **No** | not found |
| cmake / ninja / make / perl / pkg-config | **No** | not found |
| python | Yes | 3.14.3 (not a documented build prereq) |
| node / npm | Yes | v24.14.1 / 11.11.0 (not documented build prereqs) |
| DotSlash | **No** | not on host PATH |
| protoc on PATH | **No** | |
| Docker client | Yes | **29.4.3** |
| Docker daemon (C2B-1) | **Yes** | server **29.4.3**; was stopped during C2A |

## 4. Windows compiler / SDK

See `WINDOWS_BUILD_READINESS.md` (C1).

| Check | Result |
|-------|--------|
| vswhere | Missing |
| Visual Studio / Build Tools install dirs | Not present |
| Windows Kits 10 | Not present |
| VC/SDK env vars | Unset |

## 5. Docker / WSL (C2A + C2B-1)

| Field | Value |
|-------|-------|
| Docker client | 29.4.3 |
| Docker server (C2B-1) | **29.4.3** |
| Backend | **linux/amd64 on WSL2** |
| Active context (C2A) | `desktop-linux` |
| Image pull | **Succeeded** for pinned platform manifest |

## 6. Pinned Linux container image

| Field | Value |
|-------|-------|
| Pull/run pin | `docker.io/library/rust@sha256:6ca5ad23231207874325a751b9df584d51cd42c066c74c6963c264e3233c3e8e` |
| Digest class | linux/amd64 **platform manifest** |
| RepoDigest match | **Yes** |
| OS / Arch | linux / amd64 |
| Created | 2026-01-13T06:12:13.194813512Z |
| Config RUST_VERSION | 1.92.0 |
| Local pull (C2B-1) | **Yes** |
| Custom image | **No** |

## 7. Toolchain inside pinned image (C2B-1)

| Field | Value |
|-------|-------|
| rustc (direct) | 1.92.0 (ded5c06cf 2025-12-08) |
| cargo (direct) | 1.92.0 (344c4567c 2025-10-21) |
| Host triple | x86_64-unknown-linux-gnu |
| LLVM | 21.1.3 |
| Container OS (cargo) | Debian 13.0.0 |
| `bash -lc` rustc | **command not found** (PATH anomaly only; see `LOGIN_SHELL_PATH_ANOMALY.md`) |
| DotSlash (C2B-2, CARGO_HOME) | **0.5.7** at `/work/cargo-home/bin/dotslash` |
| protoc (C2B-2) | **libprotoc 29.3** via DotSlash (LF-safe wrapper) |
| Native packages (C2B-2 container) | ca-certificates, git, perl (present); build-essential, pkg-config, cmake, curl installed/upgraded |
| Grok Build source mounted (C2B-2) | **Yes, read-only** |
| Grok Build cargo check (C2B-3) | **`cargo check -p xai-grok-pager-bin` exit 0** |
| Grok Build cargo build/run/test | **Not run** |

## 8. Target pin toolchain (docs)

| Field | Value |
|-------|-------|
| rust-toolchain.toml channel | **1.92.0** |
| Components | rustfmt, clippy |
| Workspace edition | **2024** |
| Lockfile | present |

## 9. Isolation

| Field | Value |
|-------|-------|
| Source path | `C:\dev\external-verification-targets\grok-build` |
| Mounted into container this phase | **No** |
| Planned work root | `C:\dev\external-verification-work\grok-build-98c3b24\` |
| Isolation policy | `evidence/docker-readiness/DOCKER_ISOLATION_POLICY.md` |

## 10. Credentials / network

| Field | Value |
|-------|-------|
| Product/API credentials used | **No** |
| Network for image pull | **Yes** (C2B-1 pull) |
| Network for cargo/deps of Grok Build | **No** |

## 11. Environment readiness verdicts

| Axis / path | Verdict |
|-------------|---------|
| Windows host build readiness | **`BLOCKED`** |
| Docker/Linux **image + toolchain** readiness | **`PASS`** |
| Container **bootstrap** readiness | **`PASS`** |
| Phase C2B-3 cargo check | **`PASS`** (exit 0) |
| Phase C2B-1 | **`PASS`** |
| Phase C2B-2 | **`PASS`** |

**Does not prove:** release build; functional/security readiness; independent witness.

## Change Log

| Date | Change |
|------|--------|
| 2026-07-17 | Phase B / C1 notes |
| 2026-07-17 | Full Windows readiness inventory (`BLOCKED`) |
| 2026-07-18 | Phase C2A Docker/Linux pin (`PARTIAL`) |
| 2026-07-18 | Phase C2B-1 pull + rustc/cargo verify (image/toolchain **PASS**) |
| 2026-07-18 | Phase C2B-2 packages + DotSlash 0.5.7 + protoc 29.3 (bootstrap **PASS**) |
| 2026-07-18 | Phase C2B-3 `cargo check -p xai-grok-pager-bin` exit 0 |

---

**Evidence before authority.**
