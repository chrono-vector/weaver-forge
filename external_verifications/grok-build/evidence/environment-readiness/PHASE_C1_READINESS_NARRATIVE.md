# Phase C1 — Isolated Build Environment Readiness Narrative

Preserved from earlier C1 write-up (`build-environment-readiness/BUILD_ENV_READINESS.md`) during 2026-07-18 consolidation into `evidence/environment-readiness/`.

| Field | Value |
|-------|-------|
| Phase | **C1** — readiness review only |
| Dates | 2026-07-17 (inspection); 2026-07-18 (path consolidation) |
| Operator role | Owner-side (not independent witness) |
| Pinned commit | `98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce` |
| Clone path | `C:\dev\external-verification-targets\grok-build` |
| Pin re-verified | Yes — `git rev-parse HEAD` (no fetch/pull) matches pin; working tree clean |
| Grok Build built/run? | **No** |
| Toolchains installed this phase? | **No** |

---

## 1. Purpose

Assess whether an **isolated build environment** is ready to attempt documented source-build commands at the frozen pin, without executing those commands yet.

## 2. Documented prerequisites (from pin README / rust-toolchain.toml)

| Prerequisite | Documented source | Required for source build? |
|--------------|-------------------|----------------------------|
| Rust / rustup | README; `rust-toolchain.toml` channel **1.92.0** (+ rustfmt, clippy) | Yes (as documented) |
| DotSlash on PATH | README — required **before** building for hermetic `bin/` tools | Yes (as documented) |
| protoc | Via `bin/protoc` (DotSlash stub) or `PATH` / `$PROTOC` | Yes (as documented) |
| Network | Implicit for crate deps and DotSlash downloads | Likely yes for first build |
| Host OS | macOS and Linux **supported**; **Windows best-effort and not currently tested from this tree** | Host policy per README |

Documented commands (**not executed** in C1):

```text
cargo run -p xai-grok-pager-bin
cargo build -p xai-grok-pager-bin --release
cargo check -p xai-grok-pager-bin
cargo clippy -p <crate>
cargo fmt --all
```

## 3. Isolation posture

| Element | Status |
|---------|--------|
| Target tree outside Weaver Forge | Yes — `C:\dev\external-verification-targets\grok-build` |
| Weaver Forge tree not used as build cwd | Yes (this phase) |
| Dedicated VM | **Not prepared** |
| Dedicated container image | **Not prepared** (Docker CLI present on host but unused) |
| Clean CI runner | **Not prepared** |
| Credential boundary | Public clone only; no product auth; no RUSTUP/CARGO secrets set |

**Isolation readiness:** partial path isolation only — **not** a fully isolated build environment.

## 4. Host inventory (summary)

Canonical detail: `HOST_TOOLCHAIN_INVENTORY.txt` and early snapshot `HOST_TOOL_INVENTORY_EARLY_SNAPSHOT.txt`.

| Tool | Status |
|------|--------|
| git | **FOUND** 2.53.0.windows.3 |
| rustc / cargo / rustup | **MISSING** |
| DotSlash | **MISSING** |
| protoc on PATH | **MISSING** |
| In-tree `bin/protoc` | Present as DotSlash stub (~1616 bytes); unusable without DotSlash |
| Docker | FOUND 29.4.3 — unused |
| OS (observed) | Microsoft Windows 11 Home, version/build **10.0.26200** |
| Disk free (C:) | ~125+ GiB (early snapshot) |

## 5. Readiness matrix

| Gate | Result | Notes |
|------|--------|-------|
| Immutable pin still present | `PASS` | Full commit verified |
| Documented prereqs identified | `PASS` | From primary tree docs |
| Host has rustup/cargo/rustc | **blocker** | Missing |
| Host has DotSlash | **blocker** | Missing |
| MSVC / Windows SDK visible | **blocker** | Not visible (see `WINDOWS_BUILD_READINESS.md`) |
| Host is preferred build OS (macOS/Linux) | risk | Windows best-effort per README |
| Isolated container/VM ready | gap | Not prepared |
| Ready to authorize Phase C2 cargo on this host | **`BLOCKED`** | Multiple tool + platform gaps |

## 6. Overall C1 conclusion

| Field | Value |
|-------|-------|
| C1 review completed? | **Yes** |
| Build environment ready? | **No** |
| Environment readiness | **`BLOCKED`** |
| Recommended next step | Isolated Linux/macOS (preferred) or fully tooled Windows; re-inventory; then C2 only if authorized |

## 7. Evidence boundaries

### What was observed
- Pin still at `98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce`
- Tool presence/absence on this Windows host
- Documented requirements at pin
- Docker available but unused

### What was not observed / not tested
- Any `cargo` / `rustc` / DotSlash install or build against the target
- Dependency resolution, protoc download, compile success/failure
- Product runtime or authentication

### What is not claimed
- Build or functional reproducibility
- Security review or independent witness
- That Windows cannot build (only that docs mark it best-effort and tools are missing here)

### Reproduction class
**Owner-side** readiness review (not independent witness).

## 8. Change log

| Date | Note |
|------|------|
| 2026-07-17 | Phase C1 readiness review recorded |
| 2026-07-18 | Consolidated into `evidence/environment-readiness/` |
