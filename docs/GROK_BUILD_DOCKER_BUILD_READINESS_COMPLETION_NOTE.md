# Completion Note — Grok Build Phase C2A: Docker / Linux Isolated Build Readiness and Image Pinning

| Field | Value |
|-------|-------|
| Phase | **C2A** — Docker/Linux isolated build readiness + image pinning |
| Date | 2026-07-18 |
| Source pin | `98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce` |
| Clone path | `C:\dev\external-verification-targets\grok-build` |
| Pin precheck | **PASS** (exact HEAD, clean, `git diff --exit-code` 0) |
| Docker/Linux build readiness | **`PARTIAL`** |
| Phase C2B readiness | **`READY_WITH_LIMITATIONS`** |
| Windows host readiness | **`BLOCKED`** (unchanged) |
| Build / functional reproduction | **`NOT_STARTED`** |
| Compiled Grok Build | **No** |
| cargo build/check/test/run | **No** |
| xAI / product authentication | **No** |
| Host software installed | **No** |
| Custom image built | **No** |
| Image pulled locally | **No** (daemon stopped) |
| Independent verification | **Not claimed** |
| Evidence directory | `external_verifications/grok-build/evidence/docker-readiness/` |
| Canonical completion note | this file |

---

## 1. Source pin

| Check | Result |
|-------|--------|
| External HEAD | `98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce` |
| Required pin | `98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce` |
| Working tree | Clean (`git status --short` empty; `git diff --exit-code` 0) |
| Remote | `origin` → `https://github.com/xai-org/grok-build.git` |
| Source tree modified this phase | **No** |
| Git fetch/pull this phase | **No** |

Weaver Forge precheck: working tree clean at start of phase; HEAD recorded in package docs for this revision’s documentation updates only (no commit required by task).

---

## 2. Docker / WSL readiness

| Item | Status |
|------|--------|
| Docker client | **29.4.3** present; works without elevation for client commands |
| Docker server/engine | **Not running** (`com.docker.service` Stopped; named pipe missing) |
| Active context | `desktop-linux` (Linux containers intended) |
| Compose / buildx | v5.1.4 / v0.33.0-desktop.1 |
| WSL | **2.6.3.0**; default version 2 |
| Distros | `Ubuntu` Stopped (WSL2); `docker-desktop` Stopped (WSL2) |
| Engine CPUs/memory/storage/security options | **Unknown** until daemon start |
| Daemon access | **Unavailable this phase** |

---

## 3. Selected container image and digest

| Field | Value |
|-------|-------|
| Strategy | Official Docker image **A**: `library/rust` tag `1.92.0` |
| Rejected for first path | Slim/Alpine; project Dockerfile (none); silent improvisation |
| **Immutable pull pin (linux/amd64 platform manifest)** | `docker.io/library/rust@sha256:6ca5ad23231207874325a751b9df584d51cd42c066c74c6963c264e3233c3e8e` |
| Multi-arch index digest (not preferred pull for this host) | `sha256:f58923369ba295ae1f60bc49d03f2c955a5c93a0b7d49acfb2b2a65bebaf350d` |
| Config blob digest (**not** a docker pull/run reference) | `sha256:45dfd6a3b0ca04ba914df344b1f01d32092a33c56b067f88d738e4707b8dbec7` |
| OS/Arch | linux / amd64 |
| Created | 2026-01-13T06:12:13Z (image config) |
| Size (Hub compressed) | ~591904291 bytes |
| Provenance | Docker Official Image; label `org.opencontainers.image.source=https://github.com/rust-lang/docker-rust` |
| Local Image ID | N/A (not pulled) |

Resolution method: Docker Hub tag API + registry manifest/config fetch. **No `docker pull`.**

---

## 4. Native package plan (not installed)

Likely required for Linux compile path: `ca-certificates`, `git`, `build-essential`, `pkg-config`, `cmake`, and possibly `curl`.
Optional/fallback: system `protobuf-compiler`, `libssl-dev` (not preferred — project favors rustls/aws-lc), `libsqlite3-dev`, `perl`, `clang`.

Full table: `evidence/docker-readiness/LINUX_NATIVE_DEPENDENCY_PLAN.md`.

---

## 5. DotSlash / protoc plan (not installed / not executed)

- Documented install: `cargo install dotslash` (or prebuilt packages per dotslash-cli.com).
- Pin DotSlash by version at C2B-1 install time; record version in logs.
- Primary protoc path: in-tree `bin/protoc` DotSlash wrapper → protobuf **v29.3** linux-x86_64 artifact digest `3e866620c5be27664f3d2fa2d656b5f3e09b5152b42f1bedbf427b333e90021a`.
- Fallback: `$PROTOC` or system `protoc` on PATH (`find_protoc.rs`).
- Closest to official docs: DotSlash + `bin/protoc`.

---

## 6. Network and isolation rules

- Source mount **read-only**; `CARGO_TARGET_DIR` / `CARGO_HOME` / DotSlash cache on separate writable work root under `C:\dev\external-verification-work\grok-build-98c3b24\`.
- First dep acquisition **requires network**; prefer network off only after caches populated.
- **No** xAI credentials, home mounts, SSH/git credentials, Docker socket, privileged mode, or host networking.
- Capture logs, exit codes, image identity; before/after source integrity checks.
- Details: `DOCKER_ISOLATION_POLICY.md`, `PHASE_C2B_CONTAINER_BUILD_PLAN.md`.

---

## 7. Unresolved blockers

| ID | Blocker | Impact |
|----|---------|--------|
| B-D001 | Docker daemon stopped | Cannot pull/verify local image or run containers until Docker Desktop started |
| B-D002 | Local image not present | C2B-1 must pull pin |
| B-W001 | Windows native toolchain missing | Windows host path remains BLOCKED |
| B-C001 | Build not executed | Build/functional axes still NOT_STARTED |

Non-blockers for planning: official `rust:1.92.0` exists and is digest-pinned; WSL2 backend installed.

---

## 8. Phase C2B readiness verdict

### **`READY_WITH_LIMITATIONS`**

Ready to **authorize and execute** C2B after:

1. Operator starts Docker Desktop and confirms `docker info` shows a Server section
2. Pull of the pinned digest succeeds and is verified
3. C2B-1…C2B-3 proceed under isolation policy

Not pure **READY** because this phase could not prove daemon-backed pull/run.
Not **BLOCKED** for the container path: client, WSL2 install, image digest, and full procedure exist.

---

## 9. What was pulled or inspected

| Action | Done? |
|--------|-------|
| Registry/Hub metadata for `rust:1.92.0` digests | **Yes** |
| Image config blob (architecture/OS/created/labels) | **Yes** |
| `docker pull` | **No** |
| Container run | **No** |
| apt / rustup / DotSlash install | **No** |
| cargo against Grok Build | **No** |

---

## 10. What was not installed, built, authenticated, or executed

- No host software installation
- No custom Dockerfile build
- No Grok Build compilation or binary execution
- No cargo build/check/test/run
- No DotSlash/protoc execution
- No xAI authentication or API credentials
- No modification of pinned source tree
- No git fetch/pull of new commits on the target
- No commit of Weaver Forge changes (task leaves unstaged)
- No security audit (isolation planning ≠ security review)

---

## 11. Claims and multi-axis verdict

| Claim | Scope | Status |
|-------|-------|--------|
| C-015 | **Windows host** build-environment readiness | **`BLOCKED`** |
| C-016 | **Docker/Linux** isolated build-environment readiness | **`PARTIAL`** (C2B procedure: `READY_WITH_LIMITATIONS`) |

| Axis | Status |
|------|--------|
| Source authenticity | `PASS` |
| Artifact integrity | `PARTIAL` |
| Build reproducibility | `NOT_STARTED` |
| Functional reproducibility | `NOT_STARTED` |
| Windows environment readiness | `BLOCKED` |
| Docker/Linux build readiness | **`PARTIAL`** |
| Claim verification | `PARTIAL` |
| Security review | `NOT_STARTED` |
| Independent-witness | `NOT_STARTED` |
| Operational readiness | `NOT_STARTED` |
| **Overall** | **`PARTIAL`** (never PASS this phase) |

---

## 12. Recommended exact next action

1. Start Docker Desktop; wait until `docker info` reports Server Version and CPUs/Memory.
2. Execute **C2B-1 only** from `evidence/docker-readiness/PHASE_C2B_CONTAINER_BUILD_PLAN.md`: pull pinned image, verify digest, inventory tools, install minimal missing packages + DotSlash.
3. Do **not** jump to full workspace builds; after C2B-1 review, run C2B-2 then C2B-3 (`cargo check -p xai-grok-pager-bin`) under isolation policy.
4. Keep Windows native path BLOCKED unless a separate authorized host toolchain install occurs.

---

**Evidence before authority. Isolation planning is not a security audit. Owner-side readiness is not independent witness.**
