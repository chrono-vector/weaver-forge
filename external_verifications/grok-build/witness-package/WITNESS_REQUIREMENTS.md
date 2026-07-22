# Witness requirements — Grok Build narrow rebuild (1.0.0-rc2)

## Current package status

**WITNESS PACKAGE NOT READY — EXECUTABILITY REMEDIATION IN PROGRESS**

C2E-1 recorded **READY WITH LIMITATIONS** (superseded for current readiness). C-014 remains **`NOT_STARTED`**.

## Canonical platform

| Environment | Witness 1.0.0-rc2 |
|-------------|---------------------|
| Linux x86_64 + Docker | **Canonical** |
| WSL2 bash + Docker Desktop Linux containers | **Canonical** |
| PowerShell-native orchestration | **Not canonical** |
| Windows-native Rust/cargo | **BLOCKED** |
| macOS Docker | **Unvalidated / noncanonical** |

Container platform: **`linux/amd64`**.

## Independence

| Requirement | Rule |
|-------------|------|
| Person | Not the owner / package author |
| Host | Witness-owned machine, VM, or cloud |
| Weaver package revision | Resolve **annotated tag** `grok-build-witness-v1.0.0-rc2` (once published) |
| Grok source | Fresh clone at `98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce` |
| Target | New empty `CARGO_TARGET_DIR` |
| Owner caches | **Forbidden** as inputs |
| Product / auth | **Forbidden** |

## Fixed identities

| Item | Required value |
|------|----------------|
| Grok Build URL | `https://github.com/xai-org/grok-build` |
| Commit | `98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce` |
| Image | `docker.io/library/rust@sha256:6ca5ad23231207874325a751b9df584d51cd42c066c74c6963c264e3233c3e8e` |
| Rust | **1.92.0** |
| Package | `xai-grok-pager-bin` |
| Command | `cargo build -p xai-grok-pager-bin --locked` |
| Env | `CARGO_INCREMENTAL=0` |

Expected `Cargo.lock` SHA-256: `1512bb4fef0c1166c6a15a3398da9593903be1759b759ce78d9958913e61b421`

## RUSTUP_HOME policy

- **Do not** set `RUSTUP_HOME` to an empty Witness work directory.
- Preserve the digest-pinned Rust image’s built-in toolchain.
- Record the **effective** `RUSTUP_HOME` without overriding it in scripts.

## Bootstrap components

| Component | Specification |
|-----------|-----------------|
| apt packages | `ca-certificates`, `git`, `build-essential`, `pkg-config`, `cmake`, `curl`, `perl`, `file`, `binutils` — versions **not pinned** (limitation) |
| DotSlash | **0.5.7** via `cargo install dotslash --version 0.5.7 --locked` into isolated `CARGO_HOME` |
| protoc | LF-normalized **writable** copy of `/src/bin/protoc`; `PROTOC` set to that path; descriptor executes via `#!/usr/bin/env dotslash` |

## Network (disclosed)

Required for: image pull, apt, DotSlash install, protoc payload fetch, Cargo registry/git dependencies.

Completely offline-from-empty-cache reproduction: **NOT ESTABLISHED**.

## Product execution

**Forbidden** — including `--version`, `--help`, `-h`, TUI, login, agents, OAuth, models, update on `xai-grok-pager` / `grok`.

## Static tools

`file`, `readelf`, `objdump` allowed on the built artifact. **`ldd` forbidden.**
