# Completion Note — Grok Build Phase C2B-1: Pinned Container Image Pull and Toolchain Verification

| Field | Value |
|-------|-------|
| Phase | **C2B-1** — pinned image pull + Rust toolchain verification |
| Date | 2026-07-18 |
| Source pin | `98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce` |
| Source mounted in container | **No** |
| Image pin | `docker.io/library/rust@sha256:6ca5ad23231207874325a751b9df584d51cd42c066c74c6963c264e3233c3e8e` |
| Pull / RepoDigest | **Succeeded / matched** |
| rustc / cargo in image (direct) | **1.92.0 / 1.92.0** |
| DotSlash / packages installed | **No** |
| cargo against Grok Build | **No** |
| Authentication | **No** |
| Independent verification | **Not claimed** |
| Evidence | `external_verifications/grok-build/evidence/container-toolchain/` |

---

## 1. Observed engine and image

| Item | Value |
|------|-------|
| Docker Desktop server | 29.4.3 |
| Backend | linux/amd64 on WSL2 |
| Image OS / arch | linux / amd64 |
| Created | 2026-01-13T06:12:13.194813512Z |
| Config RUST_VERSION | 1.92.0 |
| rustc | 1.92.0 (ded5c06cf 2025-12-08); host x86_64-unknown-linux-gnu; LLVM 21.1.3 |
| cargo | 1.92.0 (344c4567c 2025-10-21); Debian 13.0.0 |

## 2. Shell/PATH anomaly (not a failure)

`bash -lc` reported `rustc: command not found`. Direct `rustc` / `cargo` succeeded. Classified as login-shell PATH hygiene for future recipes — **not** a toolchain or build failure. See `LOGIN_SHELL_PATH_ANOMALY.md`.

## 3. Readiness and claims

| Item | Status |
|------|--------|
| Source authenticity | PASS |
| Artifact integrity | PARTIAL |
| Windows readiness (C-015) | **BLOCKED** |
| Docker/Linux image+toolchain readiness (C-016 scope) | **PASS** (image/toolchain only) |
| Build reproducibility | **NOT_STARTED** |
| Functional reproducibility | **NOT_STARTED** |
| Claim verification | **PARTIAL** |
| Overall | **PARTIAL** |

## 4. What this phase does not prove

- Grok Build compiles or `cargo check` succeeds
- DotSlash/protoc path works
- Native package set is complete
- Offline reproducibility
- Security or independent witness

## 5. Recommended next step

Authorize **C2B-2** under isolation policy: RO source mount, minimal packages + DotSlash if needed, dependency acquisition — still no product auth; **C2B-3** `cargo check -p xai-grok-pager-bin` only after C2B-2 review. Prefer PATH-safe `docker run` recipes (avoid bare `bash -lc` without exporting cargo PATH).

---

**Evidence before authority. Image/toolchain PASS is not build PASS.**
