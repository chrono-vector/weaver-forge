# Primary Source Inspection — Grok Build (Phase B)

| Field | Value |
|-------|-------|
| Phase | B — source inspection and commit pinning only |
| Inspection date | 2026-07-17 |
| Operator role | Owner-side inspector (not independent witness) |
| Clone destination | `C:\dev\external-verification-targets\grok-build` |
| Pinned full commit | `98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce` |
| Build/execute authorized? | **No** |
| Independent verification claimed? | **No** |

---

## 1. Conflict check (clone destination)

| Check | Result |
|-------|--------|
| `C:\dev\external-verification-targets\grok-build` before work | **Did not exist** |
| Parent `C:\dev\external-verification-targets` | Created for this phase |
| Overwrite risk | None |

## 2. Canonical identity (from official sources)

| Field | Finding | Source |
|-------|---------|--------|
| Brand string **SpaceXAI** (do not equate to org/authors) | Appears in README (“SpaceXAI's terminal-based AI coding agent”; “SpaceXAI monorepo”; logo alt “SpaceXAI logo”), CONTRIBUTING (“SpaceXAI develops this software internally”), LICENSE copyright line, and Phase B-inspected x.ai news/open-source pages | README; CONTRIBUTING; LICENSE; https://x.ai/news/grok-build-open-source ; https://x.ai/open-source |
| Copyright holder line | `Copyright 2023-2026 SpaceXAI` | LICENSE line 1 |
| Cargo authors | `authors = ["xAI"]` | `crates/codegen/xai-grok-pager-bin/Cargo.toml` |
| GitHub organization / repository owner path | `xai-org` (distinct from brand string and Cargo authors) | https://github.com/xai-org/grok-build ; GitHub API |
| Canonical GitHub org/repo | `xai-org/grok-build` | All primary URLs + GitHub API |
| Visibility | **Public** (`private: false`) | GitHub API + clone without credentials |
| Official announcement URL | https://x.ai/news/grok-build-open-source (Jul 15, 2026) | primary |
| Official project/docs URLs | https://x.ai/open-source ; https://x.ai/cli ; https://docs.x.ai/build/overview | primary + README |
| Default branch | `main` | GitHub API; local `git symbolic-ref` |
| License name | Apache License, Version 2.0 (SPDX Apache-2.0) | `LICENSE`; GitHub API `apache-2.0`; workspace `license = "Apache-2.0"` |
| Exact LICENSE path | `/LICENSE` (repository root) | clone tree |
| Releases published on GitHub | **0** | GitHub API releases |
| Tags | **0** local and via API | `git tag`; API |
| Signed tags | None observed | local git |
| Commit signatures | No GPG signature trailer observed on HEAD via `git log --show-signature` | local git |
| Publisher checksums for tree | None observed for the git commit/tree | inspection |
| Release assets on GitHub Releases | N/A (no releases) | API |
| Prebuilt install channels | Documented install scripts at x.ai/cli (not executed this phase) | README |

## 3. Clone and pin

| Field | Value |
|-------|-------|
| Exact clone command | `git clone https://github.com/xai-org/grok-build.git C:\dev\external-verification-targets\grok-build` |
| Clone start | 2026-07-17 23:20:33 +09:00 |
| Clone end | 2026-07-17 23:20:56 +09:00 |
| Origin URL | `https://github.com/xai-org/grok-build.git` |
| Default branch | `main` |
| Full HEAD commit | `98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce` |
| Short commit | `98c3b24` |
| Commit date | `2026-07-17T14:19:50+01:00` |
| Commit subject | `Synced from monorepo` |
| Tag at HEAD | none |
| Working tree | clean; up to date with `origin/main` |
| Submodules | none (no `.gitmodules`) |
| Commits on branch | 3 |
| `SOURCE_REV` (monorepo SHA recorded in tree) | `124d85bc5dc6e7805560215fcc6d5413944920e1` |
| Git tree OID | `b40a1962cb8061b85c2354850ab4d5707f48414b` |

**No further pull after pin** for this package revision.

## 4. Source-tree identity (static only)

### 4.1 SHA-256 of key files

See `FILE_HASHES_SHA256.txt`. Minimum required:

| Path | SHA-256 | Bytes |
|------|---------|------:|
| README.md | `1bb63fa93716ab25796f43eeb22871a60c0ca59b3bc41872f22e33bf68d6e64a` | 5897 |
| LICENSE | `f481edaaea56bb9fadac0191287f3b243a4bf63114a707a2b2a267fbfea598d5` | 11592 |
| Cargo.toml | `6eaaed53c43fb4ae42d50378bacbfdda614c3a385a02ee41d9077c30010b7ae8` | 15983 |
| Cargo.lock | `1512bb4fef0c1166c6a15a3398da9593903be1759b759ce78d9958913e61b421` | 353616 |

### 4.2 Top-level layout

Directories: `.cargo`, `.git`, `bin`, `crates`, `prod`, `third_party`
Files: `.gitignore`, `Cargo.lock`, `Cargo.toml`, `clippy.toml`, `CONTRIBUTING.md`, `LICENSE`, `README.md`, `rustfmt.toml`, `rust-toolchain.toml`, `SECURITY.md`, `SOURCE_REV`, `THIRD-PARTY-NOTICES`

Full listing: `TOP_LEVEL_TREE.txt`.

### 4.3 Workspace / language (static)

| Field | Value |
|-------|-------|
| Implementation language (declared) | Rust (README; ~99.6% language stat on GitHub page) |
| Workspace edition | `2024` (`[workspace.package]` in root `Cargo.toml`) |
| Workspace license field | `Apache-2.0` |
| `rust-version` in workspace.package | **not present** |
| Toolchain pin | `rust-toolchain.toml` channel `1.92.0` (+ rustfmt, clippy) |
| Lockfile | **present** — root `Cargo.lock` |
| Composition-root package | `xai-grok-pager-bin` version `0.2.102` (static read of crate `Cargo.toml`) |
| Binary name (artifact) | `xai-grok-pager` (official installs ship as `grok` per README) |

### 4.4 Documented build / validation commands (not executed)

From README and https://x.ai/open-source (quoted intent; exact text in those sources):

```text
cargo run -p xai-grok-pager-bin              # build + launch the TUI
cargo build -p xai-grok-pager-bin --release  # release binary
cargo check -p xai-grok-pager-bin            # fast validation
cargo clippy -p <crate>                     # lint
cargo fmt --all                             # format
```

Also documented: `cargo install dotslash` prerequisite; DotSlash/`bin/protoc` for protoc.

### 4.5 Platforms and auth (documented; not tested)

| Topic | Documented statement |
|-------|----------------------|
| Supported build hosts | macOS and Linux supported; **Windows builds best-effort and not currently tested from this tree** (README) |
| Prebuilt binaries | Published for macOS, Linux, and Windows via install scripts (README) — **install not run** |
| Authentication | On first launch, opens browser to authenticate (README → authentication guide) — **not run** |
| Network | Clone required network; build likely needs network for crates/DotSlash — **build not run** |
| Headless | README claims headless for scripting/CI; user guide path lists headless mode — **not executed** |

### 4.6 CONTRIBUTING (static)

External contributions not accepted; tree published for source transparency and local builds under Apache-2.0.

## 5. What was not executed

- No `cargo` / `rustc` / `dotslash` / install scripts
- No Grok Build binary run, tests, clippy, or fmt
- No authentication flows
- No dependency installation
- No modification of the external clone beyond read-only git metadata commands
- No recursive copy of Grok Build into Weaver Forge

## 6. Reproduction class

**Owner-side source inspection** (not independent witness).

## 7. Limits of this inspection

- Does not prove build or functional reproducibility
- Does not prove security properties
- Does not prove monorepo `SOURCE_REV` object exists outside this published tree
- Does not verify install-script or prebuilt binary integrity
- Floating `main` may move after this pin; package freezes **this** commit only
