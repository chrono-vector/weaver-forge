# Login-shell PATH anomaly (Phase C2B-1)

| Field | Value |
|-------|-------|
| Date | 2026-07-18 |
| Image | `docker.io/library/rust@sha256:6ca5ad23231207874325a751b9df584d51cd42c066c74c6963c264e3233c3e8e` |
| Severity | Low (operational hygiene for future `docker run` recipes) |
| Classification | **Shell/PATH observation only** — **not** a toolchain failure, image pin failure, or build failure |

---

## Observation

| Invocation style | Result |
|------------------|--------|
| `bash -lc '… rustc …'` (login shell) | **`rustc: command not found`** |
| Direct `rustc` / `cargo` in the container (non-login / default image PATH) | **Succeeded** — rustc 1.92.0, cargo 1.92.0 |

## Interpretation

The official Rust image places toolchains on a PATH that is present for the default non-login container entry, but a **login shell** (`bash -lc`) may reset or omit `/usr/local/cargo/bin` (or equivalent) depending on profile scripts.

This does **not** mean:

- the pinned image lacks Rust 1.92.0
- the pull digest is wrong
- Grok Build failed to compile (compile was not attempted)

## Phase C2B implication (future recipes only)

Prefer one of:

1. Direct `docker run … rustc --version` / `cargo --version` without `bash -lc`, or
2. Explicit `ENV PATH` / `export PATH="/usr/local/cargo/bin:$PATH"` before cargo, or
3. Non-login `bash -c` with PATH export

Do not treat the login-shell miss as a C2B-1 blocker for image/toolchain readiness.

## What was not done

- No change to the official image
- No custom Dockerfile
- No Grok Build cargo execution
- No claim that `bash -lc` is broken on Debian generally
