# Claim Register — xAI Grok Build

| Field | Value |
|-------|-------|
| Target slug | `grok-build` |
| Project | Grok Build |
| Brand string (primary sources) | SpaceXAI (distinct from GitHub org `xai-org` and Cargo authors `"xAI"`) |
| Claimed canonical repository | https://github.com/xai-org/grok-build |
| Pinned commit | `98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce` |
| Current verification state | Windows env BLOCKED; Docker/Linux PARTIAL; build/runtime not executed |
| Register status | Identity/docs PASS; C-015 Windows BLOCKED; C-016 Docker/Linux PARTIAL; build/runtime NOT_STARTED |
| Maintained by | Weaver Forge documentation package author |
| Role | Owner-side (not independent witness) |
| Last updated | `2026-07-18` (C2A) |
| Independent witness evaluation of claims | `NOT_STARTED` |

---

## Claim Index

| Claim ID | Short title | Evidence class | Status |
|----------|-------------|----------------|--------|
| C-001 | Public source availability | `source_code_observation` | `PASS` |
| C-002 | Official publisher association | `publisher_statement` + `source_code_observation` | `PASS` |
| C-003 | License Apache-2.0 at LICENSE | `source_code_observation` | `PASS` |
| C-004 | Immutable commit pin recorded | `source_code_observation` | `PASS` |
| C-005 | Implementation language Rust | `source_code_observation` | `PASS` |
| C-006 | CLI/TUI + agent runtime scope (documented) | `publisher_statement` | `PASS` (doc observation only) |
| C-007 | Headless / automation support (documented) | `publisher_statement` | `PASS` (doc observation only) |
| C-008 | Documented build command exists | `publisher_statement` | `PASS` (text recorded; **not executed**) |
| C-009 | Documented validation command exists | `publisher_statement` | `PASS` (text recorded; **not executed**) |
| C-010 | Platforms: macOS/Linux supported; Windows best-effort for source builds | `publisher_statement` | `PASS` (doc observation only) |
| C-011 | Authentication required on first launch (documented) | `publisher_statement` | `PASS` (doc observation only) |
| C-012 | Documented build succeeds at pin | `build_result` | `NOT_STARTED` |
| C-013 | Documented validation succeeds at pin | `test_result` | `NOT_STARTED` |
| C-014 | Independent witness reproduces pin + procedure | `independent_witness_result` | `NOT_STARTED` |
| C-015 | Windows host build-environment readiness for documented cargo commands | `runtime_observation` | `BLOCKED` |
| C-016 | Docker/Linux isolated build-environment readiness (image pin + C2B plan) | `runtime_observation` | `PARTIAL` |

---

## Claim Records

### C-001 — Public source availability

| Field | Value |
|-------|-------|
| Exact claim | Grok Build source code is publicly available at https://github.com/xai-org/grok-build without authentication for clone. |
| Source of claim | https://x.ai/news/grok-build-open-source ; https://x.ai/open-source ; successful public `git clone` |
| Evidence class | `source_code_observation` |
| Verification method | Full clone; record remote and clean tree |
| Acceptance criteria | Clone succeeds; origin URL matches; working tree readable |
| Expected output | Clean clone of public repo |
| Actual result | Clone OK to `C:\dev\external-verification-targets\grok-build`; origin `https://github.com/xai-org/grok-build.git` |
| Status | `PASS` |
| Operator role | Owner-side |
| Evidence pointers | `evidence/source-inspection/PINNED_SOURCE_METADATA.txt` |
| Limitations | Public clone ≠ endorsement of contents; visibility can change later |
| What the result does not establish | Build success, security, functional behavior |

### C-002 — Official brand association and repo linkage

| Field | Value |
|-------|-------|
| Exact claim | Official x.ai pages and the pinned repository README present Grok Build under the brand string **SpaceXAI** and link the public source to `https://github.com/xai-org/grok-build`. These layers are not claimed to be the same legal entity as Cargo authors `"xAI"` or org path `xai-org`. |
| Source of claim | https://x.ai/news/grok-build-open-source ; https://x.ai/open-source ; README: “Grok Build is SpaceXAI's terminal-based AI coding agent”; LICENSE: `Copyright 2023-2026 SpaceXAI`; CONTRIBUTING: “SpaceXAI develops this software internally”; Cargo authors `["xAI"]` |
| Evidence class | `publisher_statement` (with supporting `source_code_observation` of README/LICENSE/CONTRIBUTING) |
| Verification method | Read official pages and tree files at pin; record each identity layer separately |
| Acceptance criteria | Repo URL linked from official pages; SpaceXAI string present in stated sources; org path and Cargo authors recorded without collapse |
| Expected output | Matching links; distinct identity layers documented |
| Actual result | News (Jul 15, 2026) and open-source page link to the GitHub repo; README/LICENSE/CONTRIBUTING use **SpaceXAI**; GitHub path is **xai-org**; Cargo authors **xAI** |
| Status | `PASS` |
| Limitations | No corporate legal-entity audit; SpaceXAI ≠ proven identical to xAI or xai-org |
| What the result does not establish | Legal identity merger; supply-chain integrity beyond public linkage |

### C-003 — License Apache-2.0

| Field | Value |
|-------|-------|
| Exact claim | First-party code is licensed under Apache License, Version 2.0; license text at repository root `LICENSE`. |
| Source of claim | README License section; `LICENSE` file; GitHub API `spdx_id=Apache-2.0`; workspace `license = "Apache-2.0"` |
| Evidence class | `source_code_observation` |
| Verification method | Read `LICENSE` header and SPDX-related fields at pin |
| Acceptance criteria | Apache-2.0 text present at `LICENSE`; consistent SPDX signals |
| Expected output | Apache-2.0 identification |
| Actual result | Confirmed; SHA-256 of `LICENSE` recorded |
| Status | `PASS` |
| Limitations | Third-party/vendored code under separate notices |
| What the result does not establish | Legal advice for a specific use; complete third-party license audit |

### C-004 — Immutable commit pin

| Field | Value |
|-------|-------|
| Exact claim | A full 40-character git commit ID for the reviewed public tree can be recorded and re-checked. |
| Source of claim | Framework identity requirements; `git rev-parse HEAD` |
| Evidence class | `source_code_observation` |
| Verification method | Full clone; record HEAD; optional later `git cat-file -t` |
| Acceptance criteria | 40-char ID recorded; tree clean at pin |
| Expected output | Full SHA |
| Actual result | `98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce` |
| Status | `PASS` |
| Limitations | Pin is point-in-time; `main` may move |
| What the result does not establish | Build/test success at that pin |

### C-005 — Implementation language Rust

| Field | Value |
|-------|-------|
| Exact claim | The published repository contains Rust source for the `grok` CLI/TUI and agent runtime (Cargo workspace). |
| Source of claim | README: "This repository contains the Rust source…"; root `Cargo.toml` workspace; `rust-toolchain.toml` |
| Evidence class | `source_code_observation` |
| Verification method | Static inspection of Cargo workspace files at pin |
| Acceptance criteria | Cargo workspace and Rust toolchain pin present |
| Expected output | Rust/Cargo layout |
| Actual result | Workspace members present; edition `2024`; toolchain channel `1.92.0`; `Cargo.lock` present |
| Status | `PASS` |
| Limitations | Language mix may include other files; percentages not independently remeasured beyond GitHub UI note |
| What the result does not establish | That the project builds with the pinned toolchain |

### C-006 — CLI/TUI and agent runtime scope (documented)

| Field | Value |
|-------|-------|
| Exact claim | Publisher documents Grok Build as a terminal-based AI coding agent / TUI with agent loop, tools, and extension system (skills, plugins, hooks, MCP, subagents). |
| Source of claim | https://x.ai/news/grok-build-open-source ; README opening + layout table |
| Evidence class | `publisher_statement` |
| Verification method | Quote docs; future: static path existence / runtime tests (not this phase) |
| Acceptance criteria | Documentation states CLI/TUI + agent runtime scope |
| Expected output | Documented scope language |
| Actual result | News and README describe TUI, agent loop, tool-call dispatch, extension system; layout lists `xai-grok-shell` agent runtime and tools crates |
| Status | `PASS` (documentation/source path observation only) |
| Limitations | Paths observed statically; runtime tool-call dispatch **not** executed |
| What the result does not establish | Correct runtime behavior of tools or agent loop |

### C-007 — Headless / automation support (documented)

| Field | Value |
|-------|-------|
| Exact claim | Publisher documents headless operation for scripting/CI (and related entry points). |
| Source of claim | README lines on headless scripting/CI; layout `xai-grok-shell` “leader/stdio/headless entry points”; user guide headless mode mention |
| Evidence class | `publisher_statement` |
| Verification method | Doc inspection now; future runtime headless smoke test |
| Acceptance criteria | Docs assert headless/scripting capability |
| Expected output | Documented headless support |
| Actual result | README and layout table document headless entry points |
| Status | `PASS` (doc observation only) |
| Limitations | Headless mode not run |
| What the result does not establish | CI suitability or headless reliability |

### C-008 — Documented build command exists

| Field | Value |
|-------|-------|
| Exact claim | Official documentation states a build/run command: `cargo run -p xai-grok-pager-bin` (and release build variant). |
| Source of claim | README “Building from source”; https://x.ai/open-source command block |
| Evidence class | `publisher_statement` |
| Verification method | Record exact command text; future: execute in isolated env |
| Acceptance criteria | Exact command text captured from primary docs |
| Expected output | Documented cargo command string |
| Actual result | Commands recorded; **not executed** |
| Status | `PASS` for “command is documented”; build success remains separate claim C-012 |
| Limitations | Does not mean build works |
| What the result does not establish | Build reproducibility |

### C-009 — Documented validation command exists

| Field | Value |
|-------|-------|
| Exact claim | Official documentation states validation/lint/format commands including `cargo check -p xai-grok-pager-bin`, `cargo clippy -p <crate>`, `cargo fmt --all`. |
| Source of claim | README Development section; https://x.ai/open-source |
| Evidence class | `publisher_statement` |
| Verification method | Record text; future: execute |
| Acceptance criteria | Exact commands captured |
| Expected output | Documented cargo check/clippy/fmt |
| Actual result | Commands recorded; **not executed** |
| Status | `PASS` for documentation presence; success is C-013 |
| Limitations | Not run |
| What the result does not establish | Clean check/clippy/fmt at pin |

### C-010 — Supported platforms (documented)

| Field | Value |
|-------|-------|
| Exact claim | macOS and Linux are supported build hosts; Windows source builds are best-effort and not currently tested from this tree. Prebuilt binaries are documented for macOS, Linux, and Windows. |
| Source of claim | README Building from source / Installing sections |
| Evidence class | `publisher_statement` |
| Verification method | Doc quote; future multi-OS builds |
| Acceptance criteria | Platform statements recorded accurately |
| Expected output | macOS/Linux supported; Windows best-effort for source |
| Actual result | Exact README statements recorded in evidence |
| Status | `PASS` (doc observation) |
| Limitations | No platform build attempted |
| What the result does not establish | Actual Windows/macOS/Linux build outcomes |

### C-011 — Authentication requirements (documented)

| Field | Value |
|-------|-------|
| Exact claim | On first launch the product opens a browser to authenticate (per README / authentication guide pointer). |
| Source of claim | README Building from source closing paragraph; path `crates/codegen/xai-grok-pager/docs/user-guide/02-authentication.md` |
| Evidence class | `publisher_statement` |
| Verification method | Doc inspection; future: runtime observation (not Phase B) |
| Acceptance criteria | Auth requirement documented |
| Expected output | Documented browser auth on first launch |
| Actual result | README states browser authentication on first launch |
| Status | `PASS` (doc observation) |
| Limitations | Auth flow not exercised; local-first inference claims on news page not tested |
| What the result does not establish | Auth success, account requirements, or offline operation |

### C-012 — Documented build succeeds at pin

| Field | Value |
|-------|-------|
| Exact claim | At pinned commit, following documented build commands produces a successful build per documented criteria. |
| Source of claim | README build commands |
| Evidence class | `build_result` |
| Verification method | Isolated env; run exact documented cargo commands; preserve logs |
| Acceptance criteria | Exit 0 (or documented success) with logs |
| Expected output | unknown until run — do not invent |
| Actual result | `NOT_STARTED` |
| Status | `NOT_STARTED` |
| Limitations | Phase B forbids execution |
| What the result does not establish | (unevaluated) |

### C-013 — Documented validation succeeds at pin

| Field | Value |
|-------|-------|
| Exact claim | At pinned commit, `cargo check -p xai-grok-pager-bin` (and related documented checks if in scope) succeed. |
| Source of claim | README / open-source page |
| Evidence class | `test_result` |
| Verification method | Isolated env execution with logs |
| Expected output | unknown until run |
| Actual result | `NOT_STARTED` |
| Status | `NOT_STARTED` |
| Limitations | Phase B forbids execution |
| What the result does not establish | (unevaluated) |

### C-014 — Independent witness

| Field | Value |
|-------|-------|
| Exact claim | An uninvolved third party can reproduce pin verification and (when authorized) documented procedures with independence declaration. |
| Source of claim | Weaver Forge E4 standard; `WITNESS_HANDOFF.md` |
| Evidence class | `independent_witness_result` |
| Verification method | Uninvolved witness package |
| Expected output | Completed witness handoff |
| Actual result | `NOT_STARTED` |
| Status | `NOT_STARTED` |
| Limitations | Package author cannot satisfy |
| What the result does not establish | (unevaluated) |

### C-015 — Windows host build-environment readiness

| Field | Value |
|-------|-------|
| Exact claim | The **inventoried Windows host** satisfies documented source-build prerequisites (Rust/rustup at channel 1.92.0, DotSlash on PATH, protoc resolution, and a visible MSVC/Windows SDK / C linker when native crates require one) and is ready to attempt documented cargo commands at commit `98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce` without product authentication. |
| Source of claim | README Building from source (Windows best-effort); `rust-toolchain.toml`; Phase C1 host inventory |
| Evidence class | `runtime_observation` (host tool presence; not a project build result) |
| Verification method | Inventory host tools; VS/SDK discovery; re-verify pin; compare to documented prereqs (Phase C1; unchanged) |
| Acceptance criteria | On this Windows host: rustup/cargo/rustc present; DotSlash on PATH; protoc resolvable; MSVC/SDK visible if native link required; pin intact |
| Expected output | Inventory showing required Windows host tools present |
| Actual result | Pin OK (clean). **Missing on Windows host:** rustc/cargo/rustup, DotSlash, protoc, MSVC (`cl`), Windows SDK, vswhere. Historical C1 evidence under `evidence/environment-readiness/` is authoritative and was **not** rewritten. |
| Status | **`BLOCKED`** |
| Operator role | Owner-side |
| Evidence pointers | `evidence/environment-readiness/*` (C1); `ENVIRONMENT.md` (Windows sections) |
| Limitations | Windows readiness ≠ Docker/Linux path (see **C-016**); readiness ≠ build success |
| What the result does not establish | Container path readiness (C-016); that cargo would pass after installs; security; independent witness |

**Scope note (C2A audit):** C-015 is the **Windows host** readiness claim established in Phase C1. It must remain **`BLOCKED`**. Docker/Linux isolation is tracked separately as **C-016**.

### C-016 — Docker/Linux isolated build-environment readiness

| Field | Value |
|-------|-------|
| Exact claim | A **Docker Desktop Linux** isolated path (WSL2 backend, official pinned base image, native package plan, DotSlash/protoc plan, isolation policy) is ready enough to authorize Phase C2B container bootstrap toward documented cargo commands at commit `98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce` without product authentication. |
| Source of claim | README (macOS/Linux supported build hosts); Phase C2A Docker inventory + image pin |
| Evidence class | `runtime_observation` (daemon/client/image identity; not a project build result) |
| Verification method | Docker/WSL status; registry metadata digest pin for `library/rust:1.92.0` linux/amd64; static plans; no container compile |
| Acceptance criteria for `PASS` | Daemon available; pinned linux/amd64 image pulled and digest-verified locally; bootstrap path documented; isolation policy recorded |
| Current phase bar | C2A records inventory + immutable image pin + C2B plan without pull/run |
| Expected output | Docker readiness evidence + pinned pull reference |
| Actual result | Client 29.4.3; context `desktop-linux`; daemon **stopped**; WSL2 installed (`Ubuntu`/`docker-desktop` Stopped). Image pin via registry only: platform manifest `sha256:6ca5ad23231207874325a751b9df584d51cd42c066c74c6963c264e3233c3e8e` (**not** locally pulled). C2B plan written. No packages/DotSlash/cargo/container execution. |
| Status | **`PARTIAL`** (Phase C2B procedure readiness: **`READY_WITH_LIMITATIONS`**) |
| Operator role | Owner-side |
| Evidence pointers | `evidence/docker-readiness/*`; `ENVIRONMENT.md` (Docker sections); `docs/GROK_BUILD_DOCKER_BUILD_READINESS_COMPLETION_NOTE.md` |
| Limitations | Daemon not proven; local image absent; isolation planning ≠ security audit; readiness ≠ build success |
| What the result does not establish | Windows host readiness (C-015); cargo success; functional/security/witness axes |

---

## Aggregate Claim Status

| Status | Count |
|--------|------:|
| `NOT_STARTED` | 3 |
| `BLOCKED` | 1 (C-015) |
| `PASS` | 11 |
| `PARTIAL` | 1 (C-016) |
| `FAIL` | 0 |
| `NOT_APPLICABLE` | 0 |
| **Total** | 16 |

Note: Eleven `PASS` rows are **identity/documentation observations**, not build/runtime success. C-015/C-016 are readiness, not build.

## Claims Explicitly Not Registered as Proven

| Deferred / excluded | Reason |
|---------------------|--------|
| Build reproducibility | Not executed |
| Functional tool-call correctness | Not executed |
| Security properties | Out of scope |
| Prebuilt binary integrity | Install scripts not run; no checksum verification this phase |

## What This Register Proves

- Primary-source-backed identity and documentation claims were evaluated at pin `98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce`.
- **C-015** Windows host build-env readiness remains **`BLOCKED`** (Phase C1 evidence preserved).
- **C-016** Docker/Linux isolated readiness is **`PARTIAL`** (digest pin + plans; daemon not running; image not pulled).
- Build/runtime success claims remain unstarted.

## What This Register Does NOT Prove

- Independent witness confirmation
- Security or product operational readiness
- That documented cargo commands succeed

## Change Log

| Date | Change | Author |
|------|--------|--------|
| 2026-07-17 | Skeleton register | Weaver Forge documentation package author |
| 2026-07-17 | Phase B primary-source claims C-001–C-014 | Weaver Forge documentation package author |
| 2026-07-17 | Phase C1 claim C-015 readiness `BLOCKED` | Weaver Forge documentation package author |
| 2026-07-18 | Phase C2A briefly set C-015 to PARTIAL (over-broad) | Weaver Forge documentation package author |
| 2026-07-18 | Pre-commit audit: C-015 restored to Windows-only `BLOCKED`; added C-016 Docker/Linux `PARTIAL` | Weaver Forge documentation package author |

---

**No commit. No claim. No receipt. No authority.**
