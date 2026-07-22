# Witness requirements — Grok Build narrow rebuild

## Independence

| Requirement | Rule |
|-------------|------|
| Person | Not the owner / package author of this verification package |
| Host | Your own machine, VM, or cloud instance (not the owner’s) |
| Source clone | Fresh clone of public Grok Build at the pinned commit |
| Build target | New empty directory for `CARGO_TARGET_DIR` |
| Owner caches | Do **not** copy owner Cargo registry, target dirs, Docker volumes, or binaries |
| Product auth | None; no API keys, OAuth, or browser login |

Public image digests and public crates.io downloads are allowed. Disclosing that you downloaded them is required.

## Fixed identities (mandatory match)

| Item | Required value |
|------|----------------|
| Grok Build URL | `https://github.com/xai-org/grok-build` |
| Commit | `98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce` |
| Image | `docker.io/library/rust@sha256:6ca5ad23231207874325a751b9df584d51cd42c066c74c6963c264e3233c3e8e` |
| Package | `xai-grok-pager-bin` |
| Command | `cargo build -p xai-grok-pager-bin --locked` |
| Env | `CARGO_INCREMENTAL=0` |
| Target | Empty `CARGO_TARGET_DIR` before build |

## Recommended platform (owner-observed; not hard minima)

| Item | Guidance |
|------|----------|
| Host OS | Linux or Windows with Docker Desktop + Linux containers; macOS with Docker may work but is less documented in this package |
| Architecture | `linux/amd64` container (owner evidence used this) |
| Docker | Required for the documented route |
| Disk | Allow **substantial** free space (owner caches/targets reached multi‑GB; recommend tens of GB free) |
| RAM | Owner runs used multi‑GB container memory; recommend **≥8–16 GiB** host RAM as practical |
| Time | Build may take **well over one hour** (owner clean rebuild ~85 minutes cargo time) |
| Network | Required for image pull, apt, rustup components if needed, crates/git deps, DotSlash/protoc fetch |
| Offline | Completely offline-from-empty-cache reproduction is **not** established |
| Windows native | **BLOCKED** — do not attempt as the documented path |

## Bootstrap components (documented from owner evidence)

| Component | Pin / note |
|-----------|------------|
| Rust image | Digest-pinned (mandatory) |
| DotSlash | Owner used **0.5.7** via `cargo install dotslash --version 0.5.7 --locked` |
| protoc | Via in-tree DotSlash `bin/protoc`; expect **libprotoc 29.3** after DotSlash fetch |
| LF hygiene | If source is checked out with CRLF, LF-normalize DotSlash shebang files under a **writable work copy** (do not permanently alter the source mount if RO) |
| apt packages (Debian-based image) | Owner used: `ca-certificates` `git` `build-essential` `pkg-config` `cmake` `curl` `perl` (exact distro package versions **not** pinned) |

## Integrity checks (mandatory)

- `git rev-parse HEAD` equals pinned commit
- `git status` clean (detached HEAD OK)
- Record SHA-256 of `Cargo.lock` (owner Phase B: `1512bb4fef0c1166c6a15a3398da9593903be1759b759ce78d9958913e61b421`)
- After build: source still clean; `Cargo.lock` unchanged

## Product execution

**Forbidden.** Do not run `xai-grok-pager` with or without arguments (including `--version`, `--help`, `-h`).
