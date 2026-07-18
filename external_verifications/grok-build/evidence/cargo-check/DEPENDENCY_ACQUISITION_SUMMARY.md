# Dependency acquisition summary — C2B-3

| Field | Value |
|-------|-------|
| Date | 2026-07-18 |
| Command | `cargo check -p xai-grok-pager-bin` |
| Network | **Authorized and used** |

## Observed network uses

| Purpose | Evidence |
|---------|----------|
| apt package retrieval | bootstrap-apt (trixie mirrors) |
| Rustup components for toolchain file | clippy/rustfmt/std aarch64 in toolchain-verify |
| crates.io downloads | **919** `Downloaded` lines in cargo stderr |
| git dependency (nucleo, lock-pinned) | expected via Cargo.lock; network allowed |
| DotSlash protoc | cache already populated from C2B-2; PROTOC path under `dotslash-cache` |

## Not accessed

- xAI product/API services
- Product authentication endpoints

## Lockfile / source

| Item | Result |
|------|--------|
| Cargo.lock changed | **No** (Phase B SHA-256 match) |
| Source tree dirty | **No** |
| Writable outputs location | External `cargo-home`, `cargo-target` only |

## Classification

First-run dependency acquisition **succeeded** as part of the single authorized `cargo check`. Offline-from-empty-cache was not claimed.
