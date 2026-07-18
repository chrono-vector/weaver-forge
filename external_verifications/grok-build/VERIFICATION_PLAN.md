# Verification Plan — xAI Grok Build

| Field | Value |
|-------|-------|
| Target slug | `grok-build` |
| Project | **Grok Build** |
| Brand string (primary sources) | **SpaceXAI** (README/LICENSE/CONTRIBUTING/x.ai pages — not equated to org) |
| GitHub organization path | `xai-org` |
| Cargo authors field (sample) | `"xAI"` |
| Claimed canonical repository | **https://github.com/xai-org/grok-build** |
| Current verification state | **Windows BLOCKED; C-016/C-017 PASS; Grok cargo still not run** |
| Plan status | Through **C2B-2 bootstrap**; C2B-3 not started (`READY_WITH_LIMITATIONS`) |
| Package created | `2026-07-17` |
| Plan version / date | 2026-07-18 Phase C2B-2; pin `98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce` |
| Operator / author | Weaver Forge documentation package author |
| Operator role | Owner-side planner/inspector (not independent witness) |
| Independent witness status | `NOT_STARTED` |
| Weaver evidence level (target) | **E2 partial** — pin + readiness + pulled image/toolchain; build still unstarted |

Pinned full commit: **`98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce`**

Clone path: `C:\dev\external-verification-targets\grok-build`

Evidence: `evidence/source-inspection/`; `evidence/environment-readiness/`; `evidence/docker-readiness/`; `evidence/container-toolchain/`; `evidence/container-bootstrap/`

---

## 1. Purpose

**Phase B:** Freeze immutable public source identity without building.

**Phase C1:** Review Windows host build-environment readiness without installing toolchains or running cargo.

**Phase C2A:** Determine Docker Desktop/WSL Linux backend readiness; select and digest-pin a Linux base image; define Phase C2B procedure **without compiling**.

**Phase C2B-1:** Pull pinned image; verify RepoDigest; verify direct rustc/cargo 1.92.0.

**Phase C2B-2:** RO source mount; install native packages; install DotSlash 0.5.7; resolve protoc 29.3 via DotSlash (**no** Grok Build cargo check/build).

## 2. Target Summary

| Field | Value |
|-------|-------|
| Artifact type | public git repository (Rust workspace / coding agent harness and TUI) |
| Canonical name | Grok Build |
| Brand presentation | SpaceXAI (as stated in primary sources; see SOURCE_IDENTITY layers) |
| Repository org path | `xai-org` |
| Canonical URL | https://github.com/xai-org/grok-build |
| Intended verification depth this phase | through **container bootstrap** (no Grok Build compile) |

## 3. Scope

### In scope (Phase B — completed)

- [x] Official primary source inspection
- [x] Full read-only clone outside Weaver Forge
- [x] Full commit pin and key file SHA-256 recording
- [x] License path and SPDX identification
- [x] Static extraction of documented build/validation commands
- [x] Claim register refinement from primary sources

### In scope (Phase C1 — completed)

- [x] Windows host toolchain inventory
- [x] Static dependency acquisition risk review
- [x] Phase C2 host-oriented plan (not executed)
- [x] Evidence under `evidence/environment-readiness/`

### In scope (Phase C2A — this revision)

- [x] Re-verify pin without fetch/pull/modify
- [x] Docker client/daemon/context inventory
- [x] WSL backend status
- [x] Evaluate image strategies A/B/C; select official `rust:1.92.0`
- [x] Resolve immutable linux/amd64 **platform manifest** digest via registry metadata (no local pull — daemon down)
- [x] Native package plan, DotSlash/protoc plan, isolation policy, C2B command plan
- [x] Evidence under `evidence/docker-readiness/`
- [x] Completion note `docs/GROK_BUILD_DOCKER_BUILD_READINESS_COMPLETION_NOTE.md`
- [x] Pre-commit audit: split C-015 (Windows) vs C-016 (Docker/Linux)

### In scope (Phase C2B-1 — completed)

- [x] Docker engine available (server 29.4.3; linux/amd64 WSL2)
- [x] Pull pinned platform-manifest image; verify RepoDigest
- [x] Local image inspect (OS/arch/created/RUST_VERSION)
- [x] Direct rustc/cargo 1.92.0 verification
- [x] Record login-shell PATH anomaly (`bash -lc`)
- [x] Evidence under `evidence/container-toolchain/`
- [x] Completion note `docs/GROK_BUILD_CONTAINER_TOOLCHAIN_VERIFICATION_COMPLETION_NOTE.md`

### In scope (Phase C2B-2 — completed)

- [x] Isolated work dirs under `C:\dev\external-verification-work\grok-build-98c3b24\`
- [x] Disposable container: RO source + writable work volumes; no home/socket/privileged/host-net
- [x] apt packages (ca-certificates, git, build-essential, pkg-config, cmake, curl, perl)
- [x] DotSlash `0.5.7` via `cargo install --version 0.5.7 --locked`
- [x] protoc via DotSlash (LF-safe wrapper after CRLF first-fail)
- [x] Native tool version probes; source integrity before/after
- [x] Evidence `evidence/container-bootstrap/`; completion note

### Out of scope (through C2B-2)

- Compiling Grok Build; any `cargo build/check/test/run` against the target
- Installing host software; starting containers for compile
- Building a custom image
- Authenticating with xAI / product APIs
- Modifying pinned Grok Build source; git fetch/pull of new commits
- Security audit (isolation planning is not security review)
- Independent witness / E4
- Committing Weaver Forge changes

## 4. Evidence Chain Checklist

| Chain link | Status | Notes / evidence pointer |
|------------|--------|--------------------------|
| Source | `PASS` | Official pages + public GitHub org/repo |
| Artifact | `PASS` | Full clone at documented path |
| Identity and Version | `PASS` | Full commit `98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce` |
| Hash or Immutable Reference | `PARTIAL` | Commit + tree OID + local file SHA-256; no publisher checksums/signed tags |
| Claim | `PARTIAL` | C-015 BLOCKED; C-016/C-017 PASS; C-012–C-014 NOT_STARTED |
| Test | `NOT_STARTED` | Not authorized |
| Reproduction | `PARTIAL` | Clone/inspect + readiness + Docker pin; not build |
| Evidence | `PASS` | source-inspection + environment-readiness + docker-readiness |
| Receipt | `NOT_STARTED` | |
| Verdict | `PARTIAL` | Overall not PASS |
| Independent Witness | `NOT_STARTED` | |

## 5. Roles and Independence

| Role | Name / handle | Independent from target authors? | Independent from this package author? |
|------|---------------|----------------------------------|----------------------------------------|
| Package author / inspector | Weaver Forge documentation package author | Yes relative to target authors (external inspector) | N/A |
| Owner-side reproducer (build) | *unassigned* | — | — |
| Independent witness | *unassigned* | Required: Yes | Required: Yes |

**Rule:** Owner-side inspection is not independent third-party witness.

## 6. Package Files

| File | Status |
|------|--------|
| `SOURCE_IDENTITY.md` | Pin complete (unchanged this phase unless factual fix) |
| `CLAIM_REGISTER.md` | C-015 BLOCKED; C-016/C-017 PASS |
| `ENVIRONMENT.md` | Through C2B-2 |
| `REPRODUCTION.md` | Through C2B-2 |
| `RESULTS.md` | Through C2B-2 |
| `VERDICT.md` | Multi-axis; overall `PARTIAL` |
| `WITNESS_HANDOFF.md` | C2B-2 notes |
| `evidence/docker-readiness/*` | C2A |
| `evidence/container-toolchain/*` | C2B-1 |
| `evidence/container-bootstrap/*` | C2B-2 |

## 7. Planned Procedure

**Phase A** — documentation shell (done).

**Phase B** — primary-source inspection + commit pin (done).

**Phase C1** — Windows host readiness **`BLOCKED`** (done; claim **C-015**).

**Phase C2A** — Docker/Linux readiness + image pin (done).

**Phase C2B-1** — pull + rustc/cargo (done; **C-016 PASS**).

**Phase C2B-2** — packages/DotSlash/protoc (done; **C-017 PASS**).

**Phase C2B-3** — `cargo check -p xai-grok-pager-bin` (**READY_WITH_LIMITATIONS**; not started).

**Phase C2B-4** — optional release build only after C2B-3 review.

**Phase D** — independent witness after executable frozen procedure exists.

## 8. Blocking Conditions

| Blocker ID | Description | Status | Resolution path |
|------------|-------------|--------|-----------------|
| B-001 | Cargo execution not authorized until env path ready | open for build | C2B after daemon start + C2B-1 |
| B-002 | Full commit unknown | **resolved** | Pin recorded |
| B-003 | Official procedure text unknown | **resolved** | README |
| B-004 | Independent witness unassigned | open | After executable procedure |
| B-005 | License unknown | **resolved** | Apache-2.0 |
| B-006 | rustup/cargo/rustc missing on Windows host | `BLOCKED` (C-015) | Prefer Linux container C2B |
| B-007 | DotSlash missing on host | open on host; planned in container | C2B-1 |
| B-008 | Windows host vs supported macOS/Linux builds | open risk | Prefer Linux isolation |
| B-009 | No container image prepared | **resolved as pin** | Platform manifest digest recorded; pull in C2B-1 |
| B-010 | Docker daemon stopped | **resolved** (C2B-1) | Engine available |
| B-011 | DotSlash / packages | **resolved** (C2B-2) | — |
| B-012 | Grok cargo check not done | open | C2B-3 |
| B-013 | CRLF DotSlash shebang on Windows mount | open | LF-safe recipe for C2B-3 |

## 9. Authorization Boundaries

| Action | Authorized C2A? | Performed? |
|--------|-----------------|------------|
| Re-verify pin (no fetch) | Yes | Yes |
| Docker/WSL status commands | Yes | Yes |
| Registry metadata / digest resolve | Yes | Yes |
| Pull selected base image only if daemon available | Yes (authorized) | **No** (daemon unavailable) |
| Build custom image | **No** | No |
| cargo / compile Grok Build | **No** | No |
| Install host software | **No** | No |
| Use credentials / paid APIs | **No** | No |
| Modify target source | **No** | No |
| Update Weaver Forge package docs | Yes | Yes |
| Commit | **No** | No |

## 10. Success Criteria for Phase C2A

- [x] Pin precheck PASS
- [x] Docker/WSL inventory recorded
- [x] Image strategy selected with rationale
- [x] Immutable linux/amd64 platform manifest digest recorded (registry path)
- [x] Native + DotSlash/protoc + isolation + C2B plans written
- [x] Package docs + completion note updated
- [x] C-015 vs C-016 claim split clarified
- [x] No compile / no source mutation / no commit

## 11. What This Plan Proves (through C2A)

- Identity pin and readiness inventories (Windows + Docker).
- A reproducible Linux image reference by **platform manifest** digest for future isolated compile attempts.

## 12. What This Plan Does NOT Prove

- Build or functional reproducibility
- Security review
- Independent verification
- Operational readiness
- That Docker daemon will successfully pull/run on first start
- Truth of untested product behavior claims

## 13. Change Log

| Date | Change | Author |
|------|--------|--------|
| 2026-07-17 | Initial documentation-only plan | Weaver Forge documentation package author |
| 2026-07-17 | Phase B primary-source pin | Weaver Forge documentation package author |
| 2026-07-17 | Phase C1 build-env readiness (`BLOCKED`) | Weaver Forge documentation package author |
| 2026-07-17 | Expanded Windows readiness + C2 plan; still BLOCKED | Weaver Forge documentation package author |
| 2026-07-18 | Phase C2A Docker/Linux readiness + image pin | Weaver Forge documentation package author |
| 2026-07-18 | Pre-commit audit: C-015 Windows-only; C-016 Docker/Linux; encoding fix | Weaver Forge documentation package author |
| 2026-07-18 | Phase C2B-1 image pull + toolchain verification | Weaver Forge documentation package author |
| 2026-07-18 | Phase C2B-2 container bootstrap | Weaver Forge documentation package author |

---

**No commit. No claim. No receipt. No authority.**
