# Reproduction Record — xAI Grok Build

| Field | Value |
|-------|-------|
| Target slug | `grok-build` |
| Reproduction status | **`PARTIAL`** — pin precheck + readiness only; cargo `NOT_STARTED`; env **`BLOCKED`** |
| Run ID | Phase B pin; env readiness `run-20260717-env-readiness` |
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
| Repository / artifact root | `C:\dev\external-verification-targets\grok-build` |
| Weaver package path | `external_verifications/grok-build/` (Weaver Forge repo) |

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

### Documented but **not** executed (official build/validate)

```text
cargo install dotslash
cargo run -p xai-grok-pager-bin
cargo build -p xai-grok-pager-bin --release
cargo check -p xai-grok-pager-bin
cargo clippy -p <crate>
cargo fmt --all
```

Status: `NOT_STARTED` / blocked by Phase B authorization.

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
| BK-001 | cargo build/check/run | Env not ready + not authorized for C2 | `BLOCKED` |
| BK-002 | product authentication | Not authorized; no credentials | `BLOCKED` |
| BK-003 | rustup/cargo/rustc | MISSING on host | `BLOCKED` |
| BK-004 | DotSlash / protoc path | MISSING | `BLOCKED` |

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

## 10. Reproduction Outcome (This Run)

| Outcome | Selected |
|---------|----------|
| `NOT_STARTED` | ☐ |
| `BLOCKED` | ☐ |
| `PASS` | ☐ |
| `PARTIAL` | ☑ |
| `FAIL` | ☐ |
| `NOT_APPLICABLE` | ☐ |

Justification: Clone/pin and Phase C1 readiness inventory succeeded as documentation; cargo execution blocked by missing tools and plan authorization.

## 11. What This Reproduction Proves

- Public full clone and commit pin at `98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce`.
- Static reading of license, workspace, and documented commands at that pin.
- Owner-side host lacks rustup/cargo/dotslash; build env readiness is `BLOCKED`.

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
