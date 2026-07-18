# Results — xAI Grok Build

| Field | Value |
|-------|-------|
| Target slug | `grok-build` |
| Results status | **cargo check PASS (C2B-3); overall PARTIAL** |
| Compiled by | Weaver Forge documentation package author |
| Role | Owner-side inspector (not independent witness) |
| Compilation date | `2026-07-18` (C2B-3) |
| Linked reproduction run ID | C2B-3 `run-20260718-cargo-check` |
| Linked claim register | `CLAIM_REGISTER.md` |
| Pinned commit | `98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce` |

---

## 1. Run Metadata

| Field | Value |
|-------|-------|
| Source identity reference | `98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce` |
| Environment reference | `ENVIRONMENT.md` |
| Reproduction reference | `REPRODUCTION.md` |
| Execution authorized (build/run)? | **Yes — only `cargo check -p xai-grok-pager-bin`** |
| Execution performed (build/run)? | **check only** (no build/run/test) |
| Clone/inspect authorized? | Yes |
| Clone/inspect performed? | Yes |
| Env readiness inventory authorized? | Yes (C1 + C2A + C2B-1) |
| Env readiness inventory performed? | Yes |
| Windows build environment ready? | **No (`BLOCKED`)** |
| Docker/Linux image+toolchain readiness | **`PASS`** (C2B-1) |
| Container bootstrap readiness | **`PASS`** (C2B-2) |
| Phase C2 (Windows native) readiness | **`BLOCKED`** |
| Phase C2B-1 (pull + rustc/cargo) | **`PASS`** |
| Phase C2B-2 (packages/DotSlash/protoc) | **`PASS`** |
| Phase C2B-3 (cargo check) | **`PASS`** (exit 0; 70m 07s) |

## 2. Per-Claim Results

| Claim ID | Short | Status | Evidence pointer |
|----------|-------|--------|------------------|
| C-001 | Public source available | `PASS` | PINNED_SOURCE_METADATA |
| C-002 | Official publisher association | `PASS` | OFFICIAL_SOURCE_REFERENCES; news/open-source |
| C-003 | Apache-2.0 LICENSE | `PASS` | LICENSE hash |
| C-004 | Commit pin | `PASS` | full SHA recorded |
| C-005 | Rust workspace | `PASS` | Cargo.toml; rust-toolchain.toml |
| C-006 | CLI/TUI/agent scope (docs) | `PASS` | README; news |
| C-007 | Headless documented | `PASS` | README |
| C-008 | Build command documented | `PASS` | text only |
| C-009 | Validation commands documented | `PASS` | text only |
| C-010 | Platform statements | `PASS` | README |
| C-011 | Auth documented | `PASS` | README |
| C-012 | Build succeeds (release/full) | `NOT_STARTED` | — |
| C-013 | Validation `cargo check -p xai-grok-pager-bin` | `PASS` | evidence/cargo-check/ |
| C-017 | Container bootstrap | `PASS` | evidence/container-bootstrap/ |
| C-014 | Independent witness | `NOT_STARTED` | — |
| C-015 | Windows host build env ready | `BLOCKED` | evidence/environment-readiness/ (C1) |
| C-016 | Docker/Linux image+toolchain ready | `PASS` | evidence/container-toolchain/ |
| C-017 | Container bootstrap packages/DotSlash/protoc | `PASS` | evidence/container-bootstrap/ |

## 3. Build Results

| Check | Status | Evidence |
|-------|--------|----------|
| Dependencies acquired (check run) | `PASS` | network crates.io; lock unchanged |
| `cargo check -p xai-grok-pager-bin` | `PASS` | exit 0; 70m 07s |
| Release/full build | `NOT_STARTED` | |
| Build reproducibility (repeat) | `NOT_STARTED` | single run only → axis PARTIAL |
| Windows build-env readiness | `BLOCKED` | |
| Docker image+toolchain | `PASS` | |
| Bootstrap | `PASS` | |

## 4. Test Results

| Suite / check | Status | Log path |
|---------------|--------|----------|
| cargo check -p xai-grok-pager-bin | `PASS` | evidence/cargo-check/ |
| cargo build/test/clippy/fmt | `NOT_STARTED` | |

## 5. Runtime / Functional Observations

| Observation ID | Status | Notes |
|----------------|--------|-------|
| O-001 product run | `NOT_STARTED` | No binary execution |

## 6. Integrity and Identity Results

| Check | Status | Evidence |
|-------|--------|----------|
| Canonical URL resolved / cloned | `PASS` | public clone |
| Full commit / version recorded | `PASS` | `98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce` |
| Key file hashes recorded | `PASS` | FILE_HASHES_SHA256.txt |
| Hash verified vs publisher digest | `NOT_APPLICABLE` | none published for tree |
| Signature verified | `NOT_APPLICABLE` | no signed tag/HEAD sig observed |
| Git tree OID recorded | `PASS` | `b40a1962cb8061b85c2354850ab4d5707f48414b` |
| Container image digest pin | `PASS` (registry + local) | PINNED_IMAGE_METADATA.txt; PINNED_IMAGE_PULL_RESULT.txt |
| Local image pull verify | `PASS` | RepoDigest matched platform manifest pin |

## 7. Failures, Warnings, and Anomalies

| ID | Severity | Description | Status |
|----|----------|-------------|--------|
| A-001 | low | Zero GitHub Releases/tags at inspection | open (informational) |
| A-002 | medium | No publisher tree checksums or signed tags | open |
| A-003 | medium | Windows source builds documented best-effort | open for future build phase |
| A-004 | low | Docker daemon was stopped during C2A | resolved for C2B-1 (daemon available) |
| A-005 | low | `bash -lc` → `rustc: command not found`; direct rustc OK | open (PATH hygiene) |
| A-006 | medium | Windows CRLF on `bin/protoc` shebang breaks Linux DotSlash until LF-safe copy | mitigated for C2B-3 recipes |

## 8. Blockers

| Block ID | Description | Blocks | Status |
|----------|-------------|--------|--------|
| BK-001 | Grok Build cargo check/build not authorized / not started | C-012, C-013 | open |
| BK-002 | Independent witness unassigned | C-014 | open |
| BK-003 | rustup/cargo/rustc/dotslash missing on Windows host | C-015 | `BLOCKED` |
| BK-004 | Windows best-effort host | future Windows build claims | open risk |
| BK-005 | MSVC / Windows SDK not visible | Windows native link | `BLOCKED` |
| BK-006 | First build likely needs network (no full vendor) | offline C2 | open |
| BK-007 | Docker daemon stopped; image not pulled | C2B-1 | **resolved** (C2B-1) |
| BK-008 | DotSlash / native packages not yet in container path | C2B-2 | **resolved** (C2B-2) |
| BK-009 | Grok Build cargo check not run | C2B-3 | open |
| BK-010 | CRLF DotSlash shebang on Windows mount | C2B-3 recipes | open (mitigation known) |

## 9. Aggregate Counts

| Status | Claims |
|--------|-------:|
| `NOT_STARTED` | 2 |
| `PASS` | 14 (incl. C-013, C-016, C-017) |
| `PARTIAL` | 0 |
| `FAIL` | 0 |
| `BLOCKED` | 1 (C-015 Windows host) |
| `NOT_APPLICABLE` | integrity sub-checks as above |

## 10. Owner-Side vs Independent Witness

| Result class | Status | Notes |
|--------------|--------|-------|
| Owner-side reproduction results | `PARTIAL` | Clone/inspect + readiness + image pull/toolchain; no Grok cargo |
| Independent witness results | `NOT_STARTED` | |

| Field | Value |
|-------|-------|
| Reproduction class for **this** results file | **Owner-side reproduction** (inspection + readiness) |
| Operator is uninvolved third party for package? | No (package author) |

## 11. Mandatory Evidence Boundaries

### 11.1 What was observed

```text
- Pin 98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce intact; external tree clean.
- Windows host still missing rustc/cargo/DotSlash/MSVC (C-015 BLOCKED).
- C2B-1: Docker server 29.4.3 linux/amd64 WSL2; pull of pinned platform manifest succeeded; RepoDigest match.
- rustc 1.92.0 / cargo 1.92.0 direct in image; bash -lc rustc not found (PATH only).
- C2B-2: RO source mount; apt packages; DotSlash 0.5.7; protoc 29.3 (LF-safe DotSlash path); source integrity PASS.
- No cargo check/build against Grok Build; no product auth.
```

### 11.2 What was not observed

```text
- Successful or failed cargo build/check/test output for Grok Build
- Running grok / xai-grok-pager binary behavior
- Authentication browser flow
- Publisher-published SHA-256 for the git tree or signed tags
- Independent witness attestation
- DotSlash install; native package install; dependency acquisition
```

### 11.3 What was not tested

```text
- cargo check/build/test/run against Grok Build
- DotSlash / protoc hermetic path
- Full native dependency package set
- Headless mode, tool-call dispatch, MCP, plugins at runtime
- Install scripts and prebuilt binaries
- Security properties
```

### 11.4 What is not claimed

```text
- Build reproducibility, functional reproducibility
- Security review or product operational readiness
- Independent verification (E4)
- That cargo will succeed after packages/DotSlash/deps (C2B-2/C2B-3)
- That Windows host is ready (C-015 is BLOCKED)
- That full isolated build path is complete (only image+toolchain PASS)
- Overall product PASS
```

### 11.5 Reproduction class

| Class | Selected |
|-------|----------|
| Owner-side reproduction | ☑ |
| Independent reproduction | ☐ |
| Neither | ☐ |

## 12. Phase C2B-1 Image / Toolchain Summary

| Field | Value |
|-------|-------|
| Selected image | `docker.io/library/rust@sha256:6ca5ad23231207874325a751b9df584d51cd42c066c74c6963c264e3233c3e8e` |
| Pull performed | **Yes** |
| RepoDigest match | **Yes** |
| rustc / cargo | 1.92.0 / 1.92.0 (direct) |
| Custom image | No |
| Grok Build cargo | Not run |

## Change Log

| Date | Change |
|------|--------|
| 2026-07-17 | Phase B + C1 results |
| 2026-07-18 | Phase C2A Docker readiness results |
| 2026-07-18 | Phase C2B-1 pull + toolchain verification |
| 2026-07-18 | Phase C2B-2 container bootstrap |
| 2026-07-18 | Phase C2B-3 cargo check exit 0 |

---

**Evidence before authority.**
