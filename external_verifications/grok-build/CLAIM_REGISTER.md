# Claim Register — xAI Grok Build

| Field | Value |
|-------|-------|
| Target slug | `grok-build` |
| Project | Grok Build |
| Brand string (primary sources) | SpaceXAI (distinct from GitHub org `xai-org` and Cargo authors `"xAI"`) |
| Claimed canonical repository | https://github.com/xai-org/grok-build |
| Pinned commit | `98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce` |
| Current verification state | Windows BLOCKED; C-013/C-018/C-020–C-021/C-023/C-024/C-025 PASS; C-022 HISTORICAL PASS / CURRENT READINESS SUPERSEDED; C-019 PARTIAL; C-014 Independent Witness NOT_STARTED; Witness package NOT READY — package version `1.0.0-rc3`; canonical tag `grok-build-witness-v1.0.0-rc3` (availability verified by tag resolution); pending fixed-tag repeat blind audit; rc1 and rc2 preserved as immutable historical releases, each with a recorded NOT READY audit; overall PARTIAL |
| Register status | C-022 historical PASS superseded for readiness; C-023 prior blind-audit intake PASS; C-024 rc1 repeat audit intake PASS (audit verdict NOT READY); C-025 rc2 integrated four-batch static blind audit intake PASS (audit verdict NOT READY); C-014 still NOT_STARTED; C-019 PARTIAL; C-015 BLOCKED |
| Maintained by | Weaver Forge documentation package author |
| Role | Owner-side (not independent witness) |
| Last updated | `2026-07-22` (C2E-4B) |
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
| C-013 | Documented validation succeeds at pin (`cargo check -p xai-grok-pager-bin`) | `test_result` | `PASS` |
| C-014 | Independent witness reproduces pin + procedure | `independent_witness_result` | `NOT_STARTED` |
| C-015 | Windows host build-environment readiness for documented cargo commands | `runtime_observation` | `BLOCKED` |
| C-016 | Docker/Linux isolated image + toolchain readiness (pinned pull + rustc/cargo) | `runtime_observation` | `PASS` |
| C-017 | Isolated container bootstrap: native packages + DotSlash + protoc | `runtime_observation` | `PASS` |
| C-018 | Narrow isolated `cargo build -p xai-grok-pager-bin` produces binary | `build_result` | `PASS` |
| C-019 | Static startup boundary for help/version flags on built binary | `runtime_observation` | `PARTIAL` |
| C-020 | Clean non-incremental second narrow rebuild succeeds at pin | `build_result` | `PASS` |
| C-021 | Static variance between C2B-4 and C2D-1 artifacts is analyzed without product execution | `source_code_observation` | `PASS` |
| C-022 | Independent Witness package readiness for public narrow rebuild | `publisher_statement` | `HISTORICAL PASS` / `CURRENT READINESS SUPERSEDED` |
| C-023 | Public-entry-point blind audit of Witness package | `publisher_statement` | `PASS` |
| C-024 | RC1 repeat public-entry-point blind audit | `publisher_statement` | `PASS` |
| C-025 | RC2 integrated four-batch static blind audit | `publisher_statement` | `PASS` (display label `AUDIT_RECORDED` — audit completed and recorded; audit verdict itself was **NOT READY**; **not** package-readiness PASS; **not** Independent Witness; C-014 remains `NOT_STARTED`. Status column keeps `PASS` for register compatibility with this explanation.) |

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
| Exact claim | At pinned commit, `cargo check -p xai-grok-pager-bin` succeeds. |
| Source of claim | README / open-source page |
| Evidence class | `test_result` / build validation observation |
| Verification method | Isolated Docker Linux container; RO source; recorded logs |
| Expected output | Exit code 0; Finished summary |
| Actual result | Exit **0**; `Finished dev profile ... in 70m 07s`; 0 warning lines; Cargo.lock unchanged. Evidence: `evidence/cargo-check/`. |
| Status | **`PASS`** (scope: **only** this command; owner-side) |
| Limitations | Not `cargo build --release`; not tests; not runtime; not independent witness; first-run network used |
| What the result does not establish | Full build reproducibility; functional product behavior; C-012 release build |

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

### C-016 — Docker/Linux isolated image + toolchain readiness

| Field | Value |
|-------|-------|
| Exact claim | A **Docker Desktop Linux** path can pull and run the **pinned** official `rust` image (`library/rust` linux/amd64 platform manifest `sha256:6ca5ad23231207874325a751b9df584d51cd42c066c74c6963c264e3233c3e8e`) such that **direct** `rustc`/`cargo` report channel **1.92.0**, matching `rust-toolchain.toml` at commit `98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce`, without product authentication. |
| Source of claim | README (macOS/Linux supported hosts); `rust-toolchain.toml`; Phase C2A pin; Phase C2B-1 pull |
| Evidence class | `runtime_observation` (daemon + image identity + tool versions; **not** a Grok Build build result) |
| Verification method | Docker engine available; `docker pull` of platform-manifest pin; RepoDigest match; local inspect; direct rustc/cargo --version in container |
| Acceptance criteria for this claim's `PASS` | Daemon up; pin pulled; RepoDigest matches; rustc and cargo 1.92.0 observed via direct invocation |
| Expected output | Pull + version evidence under `evidence/container-toolchain/` |
| Actual result | Server **29.4.3**, linux/amd64 WSL2; pull **succeeded**; RepoDigest **matched** pin; OS linux, arch amd64, created 2026-01-13T06:12:13.194813512Z, RUST_VERSION 1.92.0; rustc 1.92.0 / cargo 1.92.0 (direct). `bash -lc` → `rustc: command not found` (**PATH anomaly only**). **No** source mount, DotSlash, packages, or cargo against Grok Build. |
| Status | **`PASS`** (scope: **image + toolchain only**) |
| Operator role | Owner-side |
| Evidence pointers | `evidence/container-toolchain/*`; `evidence/docker-readiness/*` (C2A pin); `ENVIRONMENT.md`; `docs/GROK_BUILD_CONTAINER_TOOLCHAIN_VERIFICATION_COMPLETION_NOTE.md` |
| Limitations | PASS does **not** include DotSlash, native packages, dependency fetch, or `cargo check` on Grok Build; login-shell PATH requires care; isolation planning ≠ security audit |
| What the result does not establish | Windows readiness (C-015); bootstrap (C-017); C-012/C-013; functional/security/witness axes |

### C-018 — Narrow isolated cargo build of xai-grok-pager-bin

| Field | Value |
|-------|-------|
| Exact claim | In the recorded isolated Docker Linux environment (pinned image, RO source at `98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce`, retained external caches), the command `cargo build -p xai-grok-pager-bin` (dev profile) completes with exit 0 and produces the `xai-grok-pager` binary under the external target directory. |
| Source of claim | README build command family; Phase C2B-4 execution |
| Evidence class | `build_result` |
| Verification method | Disposable container; RO mount; logs; artifact hash |
| Actual result | Exit **0**; Finished in **43m 18s**; artifact `xai-grok-pager` 600647920 bytes; SHA-256 `1efcd864606d3894b685ed3ec8c6b23e7e0aceeabdc04c4c8fc991c65df4389b`; not executed. Classification: owner-side **incremental** (not clean-room). |
| Status | **`PASS`** (scope: this crate + command + environment only) |
| Limitations | Not workspace-wide; not `--release`; not bit-reproducible; not official release; not functional/auth/security/witness |
| Evidence | `evidence/cargo-build/*` |

### C-019 — Static startup boundary (help / version)

| Field | Value |
|-------|-------|
| Exact claim | The C2B-4 binary answers a permitted static CLI flag (`--version` preferred, else `--help`/`-h`) at a pure CLI boundary without prior application init (config, telemetry, filesystem side effects, network init), under a protocol-conformant at-most-one gated invocation. |
| Source of claim | Phase C2C-1 static startup boundary procedure |
| Evidence class | `runtime_observation` + `source_code_observation` |
| Verification method | Source-level CLI safety gate before any authorized execution; at most one product invocation only if gate passes; whole-session disclosure of any draft runs |
| Actual result | **Whole session (canonical history B):** (1) Non-conformant **draft** attempt executed six version/help-family commands under Docker `--network=none` + disposable HOME; all exited 0; version `grok 0.2.102 (98c3b24)`; writes under `$HOME/.grok`. Protocol conformance **FAIL** (six > one). (2) Final gated procedure: static ELF inspection; safety gate **FAIL** because CLI parse occurs only after init; product **not** re-executed. Safe pre-initialization CLI boundary **NOT ESTABLISHED**. Classification: **STATIC STARTUP PARTIAL**. |
| Status | **`PARTIAL`** (not PASS) |
| Operator role | Owner-side |
| Evidence pointers | `evidence/startup-boundary/*` (incl. WHOLE_SESSION_HISTORY.txt, PROTOCOL_DEVIATION.txt, DRAFT_EXECUTION_OBSERVATIONS.txt); `docs/GROK_BUILD_STARTUP_BOUNDARY_COMPLETION_NOTE.md` |
| Limitations | Draft observational success is not protocol PASS; not filesystem-side-effect-free; no syscall-level network proof; not functional/auth/security/witness |
| What the result does not establish | Functional readiness; production readiness; safe pre-init CLI boundary; that version/help is free of side effects |

### C-020 — Clean non-incremental narrow rebuild

| Field | Value |
|-------|-------|
| Exact claim | At pin `98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce` in the pinned Rust image, a second owner-side `cargo build -p xai-grok-pager-bin --locked` with a **new empty** `CARGO_TARGET_DIR` and **`CARGO_INCREMENTAL=0`** completes with exit 0 and produces `xai-grok-pager` without modifying source or Cargo.lock. |
| Source of claim | Phase C2D-1 clean rebuild verification |
| Evidence class | `build_result` |
| Verification method | Disposable Docker; RO source; empty phase-specific target; CARGO_INCREMENTAL=0; logs; artifact hash vs C2B-4 |
| Actual result | Exit **0**; Finished **85m 21s**; artifact 600515304 bytes; SHA-256 `eebdbe81a8fc34645a2f3c72aad36825d692fbef594a6c540f77ffaa42c18dad`. Filename/arch match prior artifact; **SHA/size differ** from C2B-4. Bit-identical: **NOT OBSERVED**. Product not executed. |
| Status | **`PASS`** (owner-side clean rebuild only; does **not** require hash identity) |
| Limitations | Reused cargo-home/dotslash caches; network bridge available; `-j 2` used; not offline-from-empty-registry; not bit-identical; not independent witness; not release profile |
| Evidence | `evidence/clean-rebuild/*`; `docs/GROK_BUILD_CLEAN_REBUILD_COMPLETION_NOTE.md` |
| What the result does not establish | Universal bit-for-bit reproducibility; functional/security/witness/production readiness |

### C-021 — Static artifact variance analysis (C2B-4 vs C2D-1)

| Field | Value |
|-------|-------|
| Exact claim | Static comparison of the authenticated C2B-4 and C2D-1 artifacts was completed. Thirty of forty-five ELF sections differed, including `.text` and relocation-related sections. Distinct embedded target paths and widespread metadata variance were identified as supported contributors, but a unique root cause for all differing bytes was not established. This claim does not establish bit-identical reproducibility or functional equivalence. |
| Source of claim | Phase C2D-2 procedure |
| Evidence class | `source_code_observation` (static binary inspection) |
| Verification method | Docker network-none; RO mounts; readelf/objdump/nm/strings; section range hashing |
| Actual result | Identity PASS. 45 sections: **15 identical**, **30 differing**. `.text` differs (size+hash). GNU Build IDs differ (observed identifier of distinct linked outputs, not a standalone root cause). NEEDED match. Paths show old `/work/cargo-target/...` vs new `/work/cargo-target-c2d1/...` (supported likely contributor to some metadata variance). Executable/relocation differences documented across two build contexts without isolating incremental-vs-clean as the sole cause. Root-cause confidence **LIKELY** (partial; not unique/complete). Classification **ARTIFACT VARIANCE ANALYSIS PASS**. |
| Status | **`PASS`** (analysis completeness; not a bit-identical or functional claim) |
| Limitations | No disassembly of full `.text`; no DWARF semantic normalization; filtered strings only; Docker OOM avoided by range hashing |
| Evidence | `evidence/artifact-variance/*`; `docs/GROK_BUILD_ARTIFACT_VARIANCE_ANALYSIS_COMPLETION_NOTE.md` |
| What the result does not establish | Functional equivalence; executable-code equivalence; unique root cause for all bytes; that path normalization alone yields bit-identity; independent witness |

### C-022 — Independent Witness package readiness

| Field | Value |
|-------|-------|
| Exact claim | The independent Witness package was audited for public entry points, fixed identities, portability, bootstrap requirements, clean-build boundaries, evidence templates, classification rules, submission procedure, and secret handling. The resulting status describes package readiness only and does not establish that an independent Witness reproduction has occurred. |
| Source of claim | Phase C2E-1 audit |
| Evidence class | `publisher_statement` / package documentation observation |
| Verification method | Documentation inventory; consistency/portability audit; creation of `witness-package/`; no Witness execution |
| Actual result | Canonical package at `witness-package/`. Classification **WITNESS PACKAGE READY WITH LIMITATIONS**. Independent Witness (C-014) remains **`NOT_STARTED`**. Limitations: unpinned apt versions; network deps; offline not established; resource guidance is recommended/observed. |
| Status | **`HISTORICAL PASS` / `CURRENT READINESS SUPERSEDED`** (C2E-1 readiness audit completion only; not a current effective package-readiness PASS) |
| **Current effective readiness (C2E-2)** | **NOT READY** under public blind-executability standard (see C-023; `evidence/public-blind-audit/`) |
| Evidence | `evidence/witness-package-readiness/*`; `witness-package/*`; `docs/GROK_BUILD_WITNESS_PACKAGE_READINESS_AUDIT_COMPLETION_NOTE.md` |
| What the result does not establish | That any third party has rebuilt Grok Build; **current** package READY; Independent Witness PASS; overall package PASS |

### C-023 — Public-entry-point blind audit of Witness package

| Field | Value |
|-------|-------|
| Exact claim | An external AI-assisted public-entry-point blind audit reviewed the published Witness package at Weaver Forge revision **`0aaae298f0e543d4042302224ed075c1796a6016`**. It found the package conceptually strong but **NOT READY** for blind execution because Docker, bootstrap, environment, logging, and evidence-template details were incomplete. This claim records **completion and intake of the audit only**; it does **not** establish independent reproduction. |
| Source of claim | Owner-supplied Source Weaver GPT response; C2E-2 intake |
| Evidence class | `publisher_statement` (external AI-assisted documentation review) |
| Verification method | Record audit provenance, scope, findings, blockers; no build |
| Actual result | Verdict **NOT READY** for blind executability; C-014 remains **`NOT_STARTED`** |
| Status | **`PASS`** (audit intake and recording complete — **not** package READY) |
| Evidence | `evidence/public-blind-audit/*`; `evidence/witness-runbook-executability-closure/*` |
| What the result does not establish | Independent Witness; build success; that remediation closed all gaps without re-audit |

### C-024 — RC1 repeat public-entry-point blind audit

| Field | Value |
|-------|-------|
| Exact claim | A repeat public-entry-point blind audit reviewed the Witness package at immutable tag **`grok-build-witness-v1.0.0-rc1`** (commit `89127c78c3a11492892de7e3b5f0dee18d71775a`). The audit recorded material clean-target, evidence-generation, and validator gaps. |
| Source of claim | C2E-3 static review; `evidence/rc1-repeat-blind-audit/` |
| Evidence class | `publisher_statement` (documentation + static script review) |
| Verification method | Record provenance, scope, findings, blockers; no build or script execution |
| Actual result | Audit verdict **NOT READY**; C-014 remains **`NOT_STARTED`** |
| Status | **`PASS`** (repeat audit completion and recording only — **not** package READY; **not** Independent Witness reproduction) |
| Evidence | `evidence/rc1-repeat-blind-audit/*`; `evidence/rc1-blind-audit-defect-closure/*` |
| What the result does not establish | Package readiness PASS; rc2 readiness; Independent Witness PASS |

### C-025 — RC2 integrated four-batch static blind audit

| Field | Value |
|-------|-------|
| Exact claim | An integrated four-batch public-entry-point static blind audit reviewed the Witness package at immutable tag **`grok-build-witness-v1.0.0-rc2`** (commit `255b357c9ee33c4a9e34b5d9b6e396c53cfe494e`). The audit was performed and its findings recorded; it did **not** execute Docker, cargo, rustc, rustup, DotSlash, protoc, `ldd`, witness scripts, or the product. |
| Source of claim | C2E-4 static review; `evidence/rc2-static-blind-audit/` (audit, batches 1–4); `evidence/rc2-integrated-blind-audit-remediation/` (intake) |
| Evidence class | `publisher_statement` (documentation + static review; no execution) |
| Verification method | Record provenance, scope, batch findings, blockers; no build, script, or Witness execution of any kind |
| Actual result | Audit verdict **NOT READY**; C-014 remains **`NOT_STARTED`**; `grok-build-witness-v1.0.0-rc2` preserved as an **immutable historical release** (must not be moved, deleted, or force-updated) |
| Status | **`PASS`** (display label `AUDIT_RECORDED` — audit completion and recording only; the audit's own verdict was **NOT READY**; this is **not** a package-readiness PASS and **not** an Independent Witness result; C-014 remains `NOT_STARTED`) |
| Evidence | `evidence/rc2-static-blind-audit/*` (27 blockers RB-001–RB-027 across 4 batches; `FINAL_AUDIT_VERDICT.md`); `evidence/rc2-integrated-blind-audit-remediation/*` (intake record) |
| What the result does not establish | Package readiness PASS; rc3 readiness; Independent Witness PASS; that rc2 itself is READY (it is not — rc2 is preserved as immutable history with a NOT READY audit) |

### C-017 — Isolated container bootstrap (packages, DotSlash, protoc)

| Field | Value |
|-------|-------|
| Exact claim | In a disposable container from the **pinned** image, with Grok Build source **read-only** and isolated work volumes, the documented **native** prerequisites can be installed, **DotSlash** can be installed at a recorded version, and **protoc** can be resolved via the in-tree DotSlash `bin/protoc` path (or an LF-safe equivalent of that hermetic path) to a version consistent with the pin’s provider entry (**protoc 29.3**), without running cargo check/build against Grok Build or using product authentication. |
| Source of claim | README Building from source; `bin/protoc`; Phase C2A plans; Phase C2B-2 execution |
| Evidence class | `runtime_observation` |
| Verification method | apt install; `cargo install dotslash --version 0.5.7 --locked`; DotSlash fetch/version of protoc; tool version probes; source integrity before/after |
| Acceptance criteria | Packages install exit 0; DotSlash version recorded; protoc version obtained via hermetic path; source pin clean after |
| Actual result | Packages OK. DotSlash **0.5.7** (checksum `981dcd6a72ea3aa94e09589be223e179d65827d9e3722968c81bf5f5e4609ddb`). Direct RO `bin/protoc` failed (CRLF shebang); **LF-normalized work copy** + DotSlash → **libprotoc 29.3**, digest match. Source integrity PASS. **No** Grok cargo check/deps. |
| Status | **`PASS`** (limitation: Windows CRLF shebang on `bin/protoc` requires LF-safe invocation for C2B-3) |
| Operator role | Owner-side |
| Evidence pointers | `evidence/container-bootstrap/*`; `docs/GROK_BUILD_CONTAINER_BOOTSTRAP_COMPLETION_NOTE.md` |
| Limitations | Not a compile success claim; CRLF hygiene for DotSlash files on Windows mounts; security not audited |
| What the result does not establish | C-012/C-013; functional correctness; offline build without caches |

---

## Aggregate Claim Status

| Status | Count |
|--------|------:|
| `NOT_STARTED` | 2 (C-012 full/release, C-014 Independent Witness) |
| `BLOCKED` | 1 (C-015) |
| `PASS` | 20 (11 docs + C-013 + C-016 + C-017 + C-018 + C-020 + C-021 + C-023 + C-024 + C-025) |
| `HISTORICAL PASS` / `CURRENT READINESS SUPERSEDED` | 1 (C-022 C2E-1 audit only; current package readiness NOT READY) |
| `PARTIAL` | 1 (C-019) |
| `FAIL` | 0 |
| `NOT_APPLICABLE` | 0 |
| **Total** | 25 |

Note: C-013/C-018/C-020 are **narrow** owner-side check/build only. C-019 is static startup PARTIAL. C-012 remains for broader build claims. C-015 Windows BLOCKED. C-022 is counted only under historical superseded status, not as a current effective package-readiness PASS. C-024 and C-025 are audit-intake recordings only (display label `AUDIT_RECORDED`); their underlying audits both returned **NOT READY**, and neither establishes package readiness or Independent Witness completion.

## Claims Explicitly Not Registered as Proven

| Deferred / excluded | Reason |
|---------------------|--------|
| Build reproducibility (witness / bit-identical) | Owner-side clean rebuild only; hashes differ; no witness |
| Functional tool-call correctness | Not executed |
| Security properties | Out of scope |
| Prebuilt binary integrity | Install scripts not run; no checksum verification this phase |

## What This Register Proves

- Identity/docs at pin `98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce`.
- **C-015** Windows host readiness **`BLOCKED`**.
- **C-016** image+toolchain **`PASS`**.
- **C-017** container bootstrap **`PASS`**.
- **C-013** narrow cargo check **`PASS`**.
- **C-018** narrow cargo build **`PASS`** (incremental; artifact hash recorded; not executed in C2B-4).
- **C-019** static startup boundary **`PARTIAL`**: draft version/help observed non-conformantly; pre-init boundary not established; final gated execution withheld.
- **C-020** clean non-incremental rebuild **`PASS`** (bit-identical **not** observed).
- **C-021** static artifact variance analysis **`PASS`** (`.text` differs; path metadata supported contributor; Build ID difference is identifier not cause; unique full root cause not established).
- **C-022** C2E-1 Witness package readiness audit **`HISTORICAL PASS` / `CURRENT READINESS SUPERSEDED`** (READY WITH LIMITATIONS **historical**); **current effective readiness NOT READY** (C2E-2 / C-023).
- **C-023** Blind audit intake **`PASS`** (recording only); does not establish reproduction.
- **C-024** RC1 repeat blind audit intake **`PASS`** (recording only; audit verdict **NOT READY**); does not establish package readiness.
- **C-025** RC2 integrated four-batch static blind audit intake **`PASS`** (recording only; audit verdict **NOT READY**); rc2 preserved as immutable historical release; does not establish package readiness.
- Package version is **`1.0.0-rc3`**; canonical package tag is **`grok-build-witness-v1.0.0-rc3`** (availability verified by annotated-tag resolution; package commit authority = annotated_tag_resolution). Package remains **NOT READY** pending fixed-tag repeat blind audit.
- **C-014 Independent Witness remains NOT_STARTED**.
- C-012 full/release and functional claims remain open/unstarted.

## What This Register Does NOT Prove

- Independent witness confirmation
- Security or product operational readiness
- That documented cargo commands against Grok Build succeed

## Change Log

| Date | Change | Author |
|------|--------|--------|
| 2026-07-17 | Skeleton register | Weaver Forge documentation package author |
| 2026-07-17 | Phase B primary-source claims C-001–C-014 | Weaver Forge documentation package author |
| 2026-07-17 | Phase C1 claim C-015 readiness `BLOCKED` | Weaver Forge documentation package author |
| 2026-07-18 | Phase C2A briefly set C-015 to PARTIAL (over-broad) | Weaver Forge documentation package author |
| 2026-07-18 | Pre-commit audit: C-015 Windows `BLOCKED`; C-016 Docker/Linux `PARTIAL` | Weaver Forge documentation package author |
| 2026-07-18 | Phase C2B-1: C-016 → `PASS` (image+toolchain only) | Weaver Forge documentation package author |
| 2026-07-18 | Phase C2B-2: C-017 container bootstrap `PASS` | Weaver Forge documentation package author |
| 2026-07-18 | Phase C2B-3: C-013 cargo check `PASS` | Weaver Forge documentation package author |
| 2026-07-18 | Phase C2B-4: C-018 cargo build `PASS` (incremental) | Weaver Forge documentation package author |
| 2026-07-22 | Phase C2C-1: C-019 static startup `PARTIAL` (exec withheld) | Weaver Forge documentation package author |
| 2026-07-22 | C2C-1 docs correction: whole-session draft disclosure; C-019 remains PARTIAL | Weaver Forge documentation package author |
| 2026-07-22 | Phase C2D-1: C-020 clean non-incremental rebuild `PASS` (not bit-identical) | Weaver Forge documentation package author |
| 2026-07-22 | Phase C2D-2: C-021 artifact variance analysis `PASS` | Weaver Forge documentation package author |
| 2026-07-22 | C2D-2 wording precision: Build ID not a root cause; `.text` not attributed to incremental-vs-clean alone | Weaver Forge documentation package author |
| 2026-07-22 | Phase C2E-1: C-022 Witness package readiness PASS; C-014 remains NOT_STARTED | Weaver Forge documentation package author |
| 2026-07-22 | Phase C2E-3: rc1 repeat audit intake C-024; rc2 defect closure drafting; package NOT READY | Weaver Forge documentation package author |
| 2026-07-22 | Phase C2E-4: rc2 integrated four-batch static blind audit intake C-025 (verdict NOT READY); rc1 and rc2 preserved as immutable historical releases, each with a recorded NOT READY audit; package version `1.0.0-rc3` / canonical tag `grok-build-witness-v1.0.0-rc3`; C-014 still NOT_STARTED; aggregate counts recalculated to 25 | Weaver Forge documentation package author |
| 2026-07-22 | Phase C2E-4B: tagged-snapshot release-wording finalization (time-stable rc3 identity language) | Weaver Forge documentation package author |

---

**No commit. No claim. No receipt. No authority.**
