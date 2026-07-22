# Reproduction Record — xAI Grok Build

| Field | Value |
|-------|-------|
| Target slug | `grok-build` |
| Reproduction status | **`PARTIAL`** — check+build PASS; no product run |
| Run ID | C2B-4 `run-20260718-cargo-build` |
| Operator | Weaver Forge documentation package author |
| Role | **Owner-side reproduction** (source inspection) |
| Independence statement | Operator is external to the target project's authors; **not** an independent witness for Weaver Forge package claims (package author) |
| Start time | 2026-07-17 23:20:33 +09:00 (clone start) |
| End time | 2026-07-17 (inspection complete same calendar day) |
| Linked environment record | `ENVIRONMENT.md` |
| Linked source identity | `SOURCE_IDENTITY.md` |
| Pinned commit | `98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce` |

---

## 1. Official Procedure Reference

| Field | Value |
|-------|-------|
| Official docs URL or path | README at pin; https://x.ai/open-source ; https://github.com/xai-org/grok-build |
| Official procedure title / section | Building from source; Development; open-source command block |
| Procedure revision (commit) | `98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce` |
| Procedure status at run time | Clone/inspect followed; **build procedure not executed** |

## 2. Working Directory

| Field | Value |
|-------|-------|
| Repository / artifact root | `C:\dev\external-verification-targets\grok-build` (**owner-side historical path**) |
| Weaver package path | `external_verifications/grok-build/` (Weaver Forge repo) |

> **Witness note (C2E-4 / C2E-4B):** Owner-side log only. Witness package status is **NOT READY** — package version `1.0.0-rc3`; canonical tag `grok-build-witness-v1.0.0-rc3` (availability verified by annotated-tag resolution). `grok-build-witness-v1.0.0-rc1` and `grok-build-witness-v1.0.0-rc2` are immutable historical releases, each with a recorded **NOT READY** audit. Canonical Witness procedure: **`witness-package/WITNESS_RUNBOOK.md`** and **`scripts/run_witness_narrow_build.sh`** (canonical execution requires successful tag resolution). No Witness execution has occurred. C-014 **NOT_STARTED**.

## 3. Command Sequence (executed)

| Step | Working directory | Command | Exit code | Status | Notes |
|------|-------------------|---------|-----------|--------|-------|
| 1 | `C:\dev\external-verification-targets` | `git clone https://github.com/xai-org/grok-build.git C:\dev\external-verification-targets\grok-build` | 0 | `PASS` | Full clone |
| 2 | clone root | `git remote -v` | 0 | `PASS` | origin URLs recorded |
| 3 | clone root | `git status` | 0 | `PASS` | clean; up to date with origin/main |
| 4 | clone root | `git rev-parse HEAD` | 0 | `PASS` | `98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce` |
| 5 | clone root | `git log -1` / tag / submodule queries | 0 | `PASS` | metadata |
| 6 | clone root | SHA-256 of key files via `Get-FileHash` | 0 | `PASS` | see evidence |
| 7 | clone root | Static read of README, LICENSE, Cargo.toml, etc. | 0 | `PASS` | no cargo |
| 8 | clone root | `git rev-parse HEAD`; `git status --short`; `git diff --exit-code`; submodule/describe | 0 | `PASS` | pin match; clean |
| 9 | readiness host | version probes: git, rustc, cargo, rustup, cl, cmake, ninja, make, perl, pkg-config, python, node, npm | mixed | `PASS` (inventory) | most build tools unavailable |
| 10 | readiness host | vswhere / VS+SDK path existence; env var presence | 0 | `PASS` (inventory) | MSVC/SDK not visible |
| 11 | clone root | static Cargo.lock/Cargo.toml/build.rs review | 0 | `PASS` | no cargo network |
| 12 | clone root | C2A pin recheck: `git rev-parse HEAD`; `git status --short`; `git diff --exit-code`; `git remote -v` | 0 | `PASS` | HEAD pin match; clean |
| 13 | readiness host | `docker version`; `docker context ls/show`; `docker info` (daemon fail); service status | mixed | `PASS` (inventory) | client 29.4.3; daemon stopped |
| 14 | readiness host | `wsl --status`; `wsl --version`; `wsl -l -v` | 0 | `PASS` (inventory) | WSL2 present; distros stopped |
| 15 | network (registry) | Docker Hub + registry v2 manifest/config for `library/rust:1.92.0` | 0 | `PASS` | digest pin; **no docker pull** |
| 16 | pinned tree | static native dep / DotSlash / protoc / isolation plan authoring | 0 | `PASS` | plans only |
| 17 | readiness host | C2B-1: Docker engine available (server 29.4.3, linux/amd64 WSL2) | 0 | `PASS` | observed |
| 18 | readiness host | `docker pull` pinned platform-manifest image | 0 | `PASS` | RepoDigest match |
| 19 | container | image inspect (OS/arch/created/RUST_VERSION) | 0 | `PASS` | linux/amd64; 1.92.0 |
| 20 | container | direct `rustc` / `cargo` version | 0 | `PASS` | 1.92.0 / 1.92.0 |
| 21 | container | `bash -lc` rustc | non-zero | `PASS` (anomaly log) | PATH only; not toolchain fail |
| 22 | host | C2B-2 source integrity before | 0 | `PASS` | pin + Phase B hashes |
| 23 | container | disposable bootstrap: apt + DotSlash 0.5.7 + tool probes | 0 | `PASS` | docker run exit 0 |
| 24 | container | protoc first via RO `bin/protoc` | 127 | `FAIL` then mitigated | CRLF shebang |
| 25 | container | protoc via LF DotSlash wrapper | 0 | `PASS` | libprotoc 29.3 |
| 26 | host | C2B-2 source integrity after | 0 | `PASS` | unchanged |
| 27 | host | C2B-3 precheck pin/hashes/image | 0 | `PASS` | |
| 28 | container | C2B-3 bootstrap + `cargo check -p xai-grok-pager-bin` | **0** | `PASS` | 70m 07s Finished |
| 29 | host | C2B-3 post integrity | 0 | `PASS` | lock/hashes clean |
| 30 | container | C2B-4 `cargo build -p xai-grok-pager-bin` | **0** | `PASS` | 43m 18s; binary produced |
| 31 | host | C2B-4 post integrity + artifact hash | 0 | `PASS` | binary not executed |

### Documented but **not** executed

```text
cargo run -p xai-grok-pager-bin
cargo build -p xai-grok-pager-bin --release
cargo clippy / cargo fmt / cargo test
```

Status: still `NOT_STARTED`.

### Raw command log (summary)

```text
git clone https://github.com/xai-org/grok-build.git C:\dev\external-verification-targets\grok-build
# CLONE_START=2026-07-17 23:20:33 +09:00
# CLONE_END=2026-07-17 23:20:56 +09:00
# HEAD=98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce
```

Full structured fields: `evidence/source-inspection/PINNED_SOURCE_METADATA.txt`.

## 4. Stdout / Stderr Preservation

| Step | Location | Status |
|------|----------|--------|
| Clone + pin metadata | `evidence/source-inspection/PINNED_SOURCE_METADATA.txt` | preserved (summary) |
| File hashes | `evidence/source-inspection/FILE_HASHES_SHA256.txt` | preserved |
| Tree listing | `evidence/source-inspection/TOP_LEVEL_TREE.txt` | preserved |
| Narrative | `evidence/source-inspection/PRIMARY_SOURCE_INSPECTION.md` | preserved |

## 5. Exit Codes Summary

| Step | Expected | Actual | Match? |
|------|----------|--------|--------|
| git clone | 0 | 0 | yes |
| git rev-parse HEAD | 0 | 0 | yes |
| cargo * | n/a | not run | `NOT_STARTED` |

## 6. Deviations from Official Procedure

| Deviation ID | Description | Impact |
|--------------|-------------|--------|
| D-001 | Official build/validate commands intentionally not run (Phase B scope) | Build axes remain `NOT_STARTED` |
| D-002 | Used PowerShell `Get-FileHash` instead of publisher checksum tool (none published) | Local integrity only |

## 7. Blocked Steps

| Block ID | Step | Blocker | Status |
|----------|------|---------|--------|
| BK-001 | cargo build/check/run | Not authorized for C2B execution in C2A; Windows tools missing | `BLOCKED` |
| BK-002 | product authentication | Not authorized; no credentials | `BLOCKED` |
| BK-003 | rustup/cargo/rustc on Windows host | MISSING on host | `BLOCKED` |
| BK-004 | DotSlash / protoc path on host | MISSING on host | `BLOCKED` |
| BK-005 | docker pull / toolchain probe | C2B-1 | **resolved** |
| BK-006 | cargo against Grok Build / DotSlash / packages | Not in C2B-1 scope | open (C2B-2+) |

## 8. Cleanup Procedure

| Field | Value |
|-------|-------|
| Cleanup required? | No (external clone retained for pin reference) |
| Residual artifacts | External clone at documented path; Weaver evidence metadata only |
| Cleanup status | `NOT_APPLICABLE` |

## 9. Evidence Produced

| Evidence item | Location | Linked claims |
|---------------|----------|---------------|
| Pin metadata | `evidence/source-inspection/PINNED_SOURCE_METADATA.txt` | C-001, C-004 |
| File hashes | `evidence/source-inspection/FILE_HASHES_SHA256.txt` | C-003, C-004 |
| Tree | `evidence/source-inspection/TOP_LEVEL_TREE.txt` | C-005 |
| Inspection narrative | `evidence/source-inspection/PRIMARY_SOURCE_INSPECTION.md` | C-001–C-011 |
| Source refs | `evidence/source-inspection/OFFICIAL_SOURCE_REFERENCES.md` | C-002 |
| Host toolchain inventory | `evidence/environment-readiness/HOST_TOOLCHAIN_INVENTORY.txt` | C-015 |
| Early tool snapshot | `evidence/environment-readiness/HOST_TOOL_INVENTORY_EARLY_SNAPSHOT.txt` | C-015 |
| C1 readiness narrative | `evidence/environment-readiness/PHASE_C1_READINESS_NARRATIVE.md` | C-015 |
| Windows SDK/MSVC readiness | `evidence/environment-readiness/WINDOWS_BUILD_READINESS.md` | C-015 |
| Pin precheck | `evidence/environment-readiness/PINNED_TARGET_PRECHECK.txt` | C-004, C-015 |
| Dependency risk | `evidence/environment-readiness/DEPENDENCY_ACQUISITION_REVIEW.md` | C-015 |
| Phase C2 plan (not run) | `evidence/environment-readiness/PHASE_C2_ISOLATED_BUILD_PLAN.md` | C-012 future |
| Docker host inventory | `evidence/docker-readiness/DOCKER_HOST_INVENTORY.txt` | C-016 |
| WSL backend | `evidence/docker-readiness/WSL_BACKEND_STATUS.txt` | C-016 |
| Image selection | `evidence/docker-readiness/CONTAINER_IMAGE_SELECTION.md` | C-016 |
| Pinned image metadata | `evidence/docker-readiness/PINNED_IMAGE_METADATA.txt` | C-016 |
| Linux native deps plan | `evidence/docker-readiness/LINUX_NATIVE_DEPENDENCY_PLAN.md` | C-016 |
| DotSlash/protoc plan | `evidence/docker-readiness/DOTSLASH_PROTOC_PLAN.md` | C-016 |
| Isolation policy | `evidence/docker-readiness/DOCKER_ISOLATION_POLICY.md` | C-016 |
| Phase C2B plan | `evidence/docker-readiness/PHASE_C2B_CONTAINER_BUILD_PLAN.md` | C-016, C-012 future |
| Docker engine runtime | `evidence/container-toolchain/DOCKER_ENGINE_RUNTIME.txt` | C-016 |
| Pull result | `evidence/container-toolchain/PINNED_IMAGE_PULL_RESULT.txt` | C-016 |
| Local inspect | `evidence/container-toolchain/LOCAL_IMAGE_INSPECTION.txt` | C-016 |
| rustc / cargo versions | `evidence/container-toolchain/RUSTC_VERSION_OUTPUT.txt`; `CARGO_VERSION_OUTPUT.txt` | C-016 |
| PATH anomaly | `evidence/container-toolchain/LOGIN_SHELL_PATH_ANOMALY.md` | C-016 |
| C2B-1 summary | `evidence/container-toolchain/PHASE_C2B1_SUMMARY.md` | C-016 |
| C2B-2 docker command / apt / DotSlash / protoc / integrity | `evidence/container-bootstrap/*` | C-017 |
| C2B-3 cargo check logs | `evidence/cargo-check/*` | C-013 |
| C2B-4 cargo build logs + artifact metadata | `evidence/cargo-build/*` | C-018 |

## 10. Reproduction Outcome (This Run)

| Outcome | Selected |
|---------|----------|
| `NOT_STARTED` | ☐ |
| `BLOCKED` | ☐ |
| `PASS` | ☐ |
| `PARTIAL` | ☑ |
| `FAIL` | ☐ |
| `NOT_APPLICABLE` | ☐ |

Justification: Clone/pin and readiness inventories complete; C2B-1 pull and rustc/cargo 1.92.0 verified; Grok Build cargo still not run; Windows host still BLOCKED.

## 11. What This Reproduction Proves

- Public full clone and commit pin at `98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce`.
- Static reading of license, workspace, and documented commands at that pin.
- Pinned image pulled locally with matching RepoDigest; direct rustc/cargo 1.92.0 in container.
- C-013 check + C-018 build `PASS` (incremental); binary not run; Windows C-015 `BLOCKED`.

## 12. What This Reproduction Does NOT Prove

- Build or functional reproducibility
- Independent witness verification
- Security properties
- That cargo commands would succeed after tool install
- Product operational readiness

## 13. Operator Attestation

| Field | Value |
|-------|-------|
| I executed the clone/inspect commands listed | Yes |
| I preserved evidence as listed | Yes |
| I am an independent witness for this target package | **No** (package author) |
| I executed cargo build/test/run | **No** |
| Date | 2026-07-17 |

---

**Contributor ≠ Witness. Owner-side ≠ E4.**
