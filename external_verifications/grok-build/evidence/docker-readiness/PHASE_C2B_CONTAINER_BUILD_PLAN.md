# Phase C2B Container Build Plan — DEFINED ONLY (do not execute in C2A)

| Field | Value |
|-------|-------|
| Plan date | 2026-07-18 |
| Status | **PLAN ONLY — not executed** |
| Pinned source | `C:\dev\external-verification-targets\grok-build` @ `98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce` |
| Pinned image | `docker.io/library/rust@sha256:6ca5ad23231207874325a751b9df584d51cd42c066c74c6963c264e3233c3e8e` (**linux/amd64 platform manifest** digest; not multi-arch index; not config blob) |
| Work root | `C:\dev\external-verification-work\grok-build-98c3b24\` |

**Forbidden until authorized:** any step below on the live host/container as part of C2A.

Milestones:

| ID | Name | Success criteria (future) |
|----|------|---------------------------|
| C2B-1 | Container/toolchain bootstrap | Daemon up; image pulled+verified; git/cmake/pkg-config present as needed; Rust 1.92.0; DotSlash on PATH |
| C2B-2 | Dependency acquisition | `cargo fetch` (or equivalent) completes with logs; network use recorded |
| C2B-3 | Narrow compile check | `cargo check -p xai-grok-pager-bin` exit code + logs; source tree still clean |
| C2B-4 | Optional release build | Only after C2B-3 review authorization: `cargo build -p xai-grok-pager-bin --release` |

---

## Shared host variables (PowerShell)

```powershell
$PIN    = '98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce'
$SRC    = 'C:\dev\external-verification-targets\grok-build'
$WORK   = 'C:\dev\external-verification-work\grok-build-98c3b24'
$IMG    = 'docker.io/library/rust@sha256:6ca5ad23231207874325a751b9df584d51cd42c066c74c6963c264e3233c3e8e'
$LOGS   = Join-Path $WORK 'logs'
New-Item -ItemType Directory -Force -Path $LOGS,(Join-Path $WORK 'target'),(Join-Path $WORK 'cargo-home'),(Join-Path $WORK 'dotslash-cache') | Out-Null
```

---

## 0. Preconditions (host)

```powershell
# Start Docker Desktop manually if needed, then:
docker info
docker version
# Expect Server section non-null; context desktop-linux

# Source pin validation
Set-Location $SRC
git rev-parse HEAD   # must equal $PIN
git status --short   # must be empty
git diff --exit-code # must exit 0
```

Capture to `$LOGS\precheck-before.txt`.

Stop if pin dirty or HEAD mismatch.

---

## C2B-1 — Container / toolchain bootstrap

### 1.1 Pull and verify image

```powershell
docker pull $IMG
docker image inspect $IMG --format 'Id={{.Id}} RepoDigests={{json .RepoDigests}} Arch={{.Architecture}} Os={{.Os}} Size={{.Size}} Created={{.Created}}' |
  Tee-Object -FilePath (Join-Path $LOGS 'container-identity.txt')
```

Confirm the **linux/amd64 platform manifest** digest `sha256:6ca5ad23231207874325a751b9df584d51cd42c066c74c6963c264e3233c3e8e` appears in RepoDigests or is the pulled reference.
Do **not** pull by config blob digest `sha256:45dfd6a3b0ca04ba914df344b1f01d32092a33c56b067f88d738e4707b8dbec7`.

### 1.2 Inventory tools inside image (read-only run)

```powershell
docker run --rm $IMG bash -lc 'rustc --version --verbose; cargo --version --verbose; rustup show; gcc --version; cmake --version; pkg-config --version; git --version; which protoc || true; which dotslash || true'
```

### 1.3 Bootstrap packages + DotSlash (network on)

Install only missing packages per `LINUX_NATIVE_DEPENDENCY_PLAN.md`. Example skeleton (adjust after inventory):

```powershell
docker run --rm `
  -v "${SRC}:/src:ro" `
  -v "${WORK}\cargo-home:/work/cargo-home" `
  -v "${WORK}\target:/work/target" `
  -v "${WORK}\dotslash-cache:/work/dotslash-cache" `
  -v "${LOGS}:/work/logs" `
  -e CARGO_HOME=/work/cargo-home `
  -e CARGO_TARGET_DIR=/work/target `
  -e DOTSLASH_CACHE=/work/dotslash-cache `
  -w /src `
  --network=bridge `
  $IMG `
  bash -lc @'
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
# Install only if missing — illustrative:
apt-get update
apt-get install -y --no-install-recommends ca-certificates git build-essential pkg-config cmake curl
rustc --version | tee /work/logs/rustc-version.txt
cargo install dotslash --locked 2>&1 | tee /work/logs/dotslash-install.log
# Prefer recording exact version; if --version flag unsupported, note that:
(command -v dotslash && dotslash --help) 2>&1 | tee /work/logs/dotslash-help.txt
'@
```

Notes:

- Do **not** pass xAI credentials.
- Do **not** mount Docker socket or home directories.
- Do **not** use `--privileged` or `--network=host`.
- If image already contains gcc/git, skip redundant apt packages.
- Rust must remain **1.92.0** (image pin + rust-toolchain.toml).

**C2B-1 exit:** toolchain inventory logs show rustc 1.92.0 and DotSlash available.

---

## C2B-2 — Dependency acquisition

```powershell
$sw = [Diagnostics.Stopwatch]::StartNew()
docker run --rm `
  -v "${SRC}:/src:ro" `
  -v "${WORK}\cargo-home:/work/cargo-home" `
  -v "${WORK}\target:/work/target" `
  -v "${WORK}\dotslash-cache:/work/dotslash-cache" `
  -v "${LOGS}:/work/logs" `
  -e CARGO_HOME=/work/cargo-home `
  -e CARGO_TARGET_DIR=/work/target `
  -e DOTSLASH_CACHE=/work/dotslash-cache `
  -e PATH="/work/cargo-home/bin:/usr/local/cargo/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin" `
  -w /src `
  --network=bridge `
  $IMG `
  bash -lc 'set -euo pipefail; cargo fetch -p xai-grok-pager-bin 2>&1 | tee /work/logs/c2b2-fetch.log; echo EXIT:$? | tee /work/logs/c2b2-fetch.exitcode.txt'
$sw.Stop()
$sw.Elapsed.ToString() | Set-Content (Join-Path $LOGS 'c2b2-elapsed.txt')
```

If `cargo fetch -p` is unsupported by the cargo version, use:

```text
cargo fetch
```

or proceed to C2B-3 with network on (first check downloads deps).

Record that network was required.

---

## C2B-3 — Narrowest initial compilation check

Documented README validation command:

```text
cargo check -p xai-grok-pager-bin
```

```powershell
$sw = [Diagnostics.Stopwatch]::StartNew()
docker run --rm `
  -v "${SRC}:/src:ro" `
  -v "${WORK}\cargo-home:/work/cargo-home" `
  -v "${WORK}\target:/work/target" `
  -v "${WORK}\dotslash-cache:/work/dotslash-cache" `
  -v "${LOGS}:/work/logs" `
  -e CARGO_HOME=/work/cargo-home `
  -e CARGO_TARGET_DIR=/work/target `
  -e DOTSLASH_CACHE=/work/dotslash-cache `
  -e PATH="/work/cargo-home/bin:/usr/local/cargo/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin" `
  -w /src `
  --network=bridge `
  $IMG `
  bash -lc 'set -euo pipefail; cargo check -p xai-grok-pager-bin 2>&1 | tee /work/logs/c2b3-cargo-check.log; echo EXIT:$? | tee /work/logs/c2b3-cargo-check.exitcode.txt'
$sw.Stop()
$sw.Elapsed.ToString() | Set-Content (Join-Path $LOGS 'c2b3-elapsed.txt')
```

After container exits (host):

```powershell
Set-Location $SRC
git rev-parse HEAD | Tee-Object (Join-Path $LOGS 'precheck-after.txt')
git status --short | Tee-Object -Append (Join-Path $LOGS 'precheck-after.txt')
git diff --exit-code
```

**Do not** run:

```text
cargo run -p xai-grok-pager-bin
cargo test
```

(no product auth, no TUI)

---

## C2B-4 — Optional build (only after C2B-3 review)

```text
cargo build -p xai-grok-pager-bin --release
```

Same mount/isolation pattern; separate log files; separate authorization in VERIFICATION_PLAN.

---

## Capture checklist (every milestone)

- [ ] stdout / stderr logs
- [ ] exit code
- [ ] elapsed time
- [ ] image digest / `docker version` server version
- [ ] rustc/cargo versions
- [ ] source tree before/after integrity

---

## Relationship to prior C2 plan

Host Windows native C2 (`evidence/environment-readiness/PHASE_C2_ISOLATED_BUILD_PLAN.md`) remains **BLOCKED** on MSVC/rustup host tools.

This C2B plan is the **Linux container path** preferred by upstream “macOS and Linux are supported build hosts”.

---

## Authorization gate

C2B execution requires:

1. Docker daemon running
2. Explicit phase authorization in package plan (C2A completes readiness definition only)
3. Continued ban on product API credentials and source tree mutation
