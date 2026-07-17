# Dependency acquisition risk review (static only)

Date: 2026-07-17
Pin: `98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce`
Path: `C:\dev\external-verification-targets\grok-build`

**Methods used:** text inspection of `Cargo.toml`, `Cargo.lock`, `build.rs` paths, `third_party/`.
**Not used:** `cargo metadata`, `cargo fetch`, network downloads, dependency installation.

---

## 1. Lockfile and workspace size

| Item | Finding |
|------|---------|
| `Cargo.lock` present | **Yes** (353616 bytes) |
| Workspace members (`Cargo.toml` members array) | **79** paths |
| `[[package]]` / name entries in lock (approx) | **1271** `name =` lines |
| `source =` lines in lock | **1192** |

## 2. Dependency source classes (Cargo.lock)

| Source class | Count (source lines) | Notes |
|--------------|---------------------:|-------|
| `registry+…` (crates.io style) | **1190** | Dominates graph |
| `git+…` | **2** | Same git URL repeated (package + maybe variant) |
| path / other source lines | 0 among `source =` lines | Workspace members are path crates without registry sources |

### Git dependency observed

```text
source = "git+https://github.com/helix-editor/nucleo.git?rev=5b74652#5b74652e482f7c07d827f18c6d21e7540c242c69"
```

Pinned revision fragment: `5b74652e482f7c07d827f18c6d21e7540c242c69` (from lock URL).

## 3. Vendored / in-tree third_party

| Path | Role |
|------|------|
| `third_party/` | Present: `dagre_rust`, `graphlib_rust`, `mermaid-to-svg`, `ordered_hashmap`, notices |
| `vendor/` | **Not present** as a full cargo vendor directory |

In-tree third_party reduces some dependency surface but **does not** replace crates.io for the bulk of the lockfile.

## 4. build.rs scripts (in-tree)

Count: **6**

| Path | Static note |
|------|-------------|
| `crates/codegen/xai-grok-pager-bin/build.rs` | Invokes `git rev-parse` for version string; no C compile |
| `crates/codegen/xai-grok-version/build.rs` | Env-only |
| `crates/codegen/xai-grok-tools/build.rs` | Bundling logic for ripgrep/bfs/ugrep (may involve download/bundle paths in full file; not executed) |
| `xai-grok-pager`, `xai-grok-shell`, `xai-grok-tools-api` | present (not fully audited line-by-line) |

## 5. Native / FFI indicators in lock (name presence only)

Packages present in lock including: `cc`, `cmake`, `pkg-config`, `bindgen`, `libsqlite3-sys`, `libz-sys`, `zstd-sys`, `ring`, `prost-build`, `tonic-build`, `protobuf`, `winapi`, `windows`, `tikv-jemallocator`, `libloading`.

**Implication:** First successful Windows build is **likely** to need a working C/C++ toolchain / linker (MSVC or equivalent), not only `rustc`. This host has **no** visible MSVC/SDK (see `WINDOWS_BUILD_READINESS.md`).

## 6. Network requirements

| Question | Assessment |
|----------|------------|
| Would first build need network? | **Yes, very likely** — nearly all lock sources are registry; plus git source for nucleo; DotSlash may fetch protoc; tools build.rs may fetch/bundle assets |
| Offline build possible from current tree alone? | **No evidence of full vendoring** — offline build **not** supportable from current tree state without a prior populated cargo cache / vendor dir (not present) |
| `cargo metadata` this phase | **Omitted** — risk of network or index interaction; static lock inspection used instead |

## 7. Authentication vs compile

| Concern | Separate? |
|---------|-----------|
| Source compile / `cargo check` | Can be attempted without product API auth once toolchains exist |
| Product AI service / browser auth | Documented for **first launch** of the binary (README → authentication guide) — **separate** from compilation success |
| Phase C2 scope (planned) | Compilation only; **no** product authentication |

## 8. Risks for Phase C2

1. Registry + git network dependency acquisition
2. MSVC/Windows SDK missing on this host
3. Rust toolchain missing
4. DotSlash / protoc hermetic tools
5. Windows best-effort upstream posture
6. Large workspace — prefer `-p xai-grok-pager-bin` not full workspace

## 9. What this review does not prove

- Exact compile-time failures or successes
- That every native crate will link
- Security of any dependency
- Offline reproducibility
