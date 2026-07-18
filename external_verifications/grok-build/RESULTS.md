# Results — xAI Grok Build

| Field | Value |
|-------|-------|
| Target slug | `grok-build` |
| Results status | **Pin + Windows readiness BLOCKED + Docker/Linux PARTIAL; cargo NOT_STARTED** |
| Compiled by | Weaver Forge documentation package author |
| Role | Owner-side inspector (not independent witness) |
| Compilation date | `2026-07-18` (C2A); prior C1/B `2026-07-17` |
| Linked reproduction run ID | Phase B pin; C1 `run-20260717-phase-c1-env-readiness`; C2A `run-20260718-docker-readiness` |
| Linked claim register | `CLAIM_REGISTER.md` |
| Pinned commit | `98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce` |

---

## 1. Run Metadata

| Field | Value |
|-------|-------|
| Source identity reference | `98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce` |
| Environment reference | `ENVIRONMENT.md` |
| Reproduction reference | `REPRODUCTION.md` |
| Execution authorized (build/run)? | **No** |
| Execution performed (build/run)? | **No** |
| Clone/inspect authorized? | Yes |
| Clone/inspect performed? | Yes |
| Env readiness inventory authorized? | Yes (C1 + C2A) |
| Env readiness inventory performed? | Yes |
| Windows build environment ready? | **No (`BLOCKED`)** |
| Docker/Linux build readiness | **`PARTIAL`** |
| Phase C2 (Windows native) readiness | **`BLOCKED`** |
| Phase C2B (container) readiness | **`READY_WITH_LIMITATIONS`** |

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
| C-012 | Build succeeds | `NOT_STARTED` | — |
| C-013 | Validation succeeds | `NOT_STARTED` | — |
| C-014 | Independent witness | `NOT_STARTED` | — |
| C-015 | Windows host build env ready | `BLOCKED` | evidence/environment-readiness/ (C1) |
| C-016 | Docker/Linux isolated env ready | `PARTIAL` | evidence/docker-readiness/; C2B READY_WITH_LIMITATIONS |

## 3. Build Results

| Check | Status | Evidence |
|-------|--------|----------|
| Dependencies installed as documented | `NOT_STARTED` | |
| Build command completed | `NOT_STARTED` | |
| Build artifacts produced | `NOT_STARTED` | |
| Build reproducibility (repeat run) | `NOT_STARTED` | |
| Windows build-env readiness | `BLOCKED` | missing rust, DotSlash, MSVC/SDK |
| Docker/Linux build-env readiness | `PARTIAL` | client+WSL+image pin; daemon stopped |

## 4. Test Results

| Suite / check | Status | Log path |
|---------------|--------|----------|
| cargo check / clippy / fmt / tests | `NOT_STARTED` | |

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
| Container image digest pin | `PASS` (registry metadata) | PINNED_IMAGE_METADATA.txt |
| Local image pull verify | `NOT_STARTED` | daemon stopped |

## 7. Failures, Warnings, and Anomalies

| ID | Severity | Description | Status |
|----|----------|-------------|--------|
| A-001 | low | Zero GitHub Releases/tags at inspection | open (informational) |
| A-002 | medium | No publisher tree checksums or signed tags | open |
| A-003 | medium | Windows source builds documented best-effort | open for future build phase |
| A-004 | medium | Docker daemon stopped during C2A | open — start Desktop for C2B |

## 8. Blockers

| Block ID | Description | Blocks | Status |
|----------|-------------|--------|--------|
| BK-001 | Build/run not authorized in C2A | C-012, C-013 | `BLOCKED` (auth boundary) |
| BK-002 | Independent witness unassigned | C-014 | open |
| BK-003 | rustup/cargo/rustc/dotslash missing on Windows host | C-015 | `BLOCKED` |
| BK-004 | Windows best-effort host | future Windows build claims | open risk |
| BK-005 | MSVC / Windows SDK not visible | Windows native link | `BLOCKED` |
| BK-006 | First build likely needs network (no full vendor) | offline C2 | open |
| BK-007 | Docker daemon stopped; image not pulled | C2B-1 pull/run | open |

## 9. Aggregate Counts

| Status | Claims |
|--------|-------:|
| `NOT_STARTED` | 3 |
| `PASS` | 11 |
| `PARTIAL` | 1 (C-016) |
| `FAIL` | 0 |
| `BLOCKED` | 1 (C-015 Windows host) |
| `NOT_APPLICABLE` | integrity sub-checks as above |

## 10. Owner-Side vs Independent Witness

| Result class | Status | Notes |
|--------------|--------|-------|
| Owner-side reproduction results | `PARTIAL` | Clone/inspect + readiness + Docker pin |
| Independent witness results | `NOT_STARTED` | |

| Field | Value |
|-------|-------|
| Reproduction class for **this** results file | **Owner-side reproduction** (inspection + readiness) |
| Operator is uninvolved third party for package? | No (package author) |

## 11. Mandatory Evidence Boundaries

### 11.1 What was observed

```text
- Pin precheck PASS: HEAD 98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce, clean.
- Host: Windows 11 Home; git/python/node present; rustc/cargo/rustup/cl/cmake/dotslash MISSING.
- Docker client 29.4.3; context desktop-linux; daemon STOPPED; WSL2 installed; Ubuntu and docker-desktop Stopped.
- Official rust:1.92.0 linux/amd64 digest sha256:6ca5ad23231207874325a751b9df584d51cd42c066c74c6963c264e3233c3e8e via registry API.
- C2B plan, isolation policy, native/DotSlash plans recorded; no cargo execution.
```

### 11.2 What was not observed

```text
- Successful or failed cargo build/check/test output
- Running grok / xai-grok-pager binary behavior
- Authentication browser flow
- Publisher-published SHA-256 for the git tree or signed tags
- Independent witness attestation
- Local docker pull success or container runtime resource numbers
```

### 11.3 What was not tested

```text
- All build, lint, format, unit/integration tests
- Toolchain installation procedures (host or container)
- Headless mode, tool-call dispatch, MCP, plugins at runtime
- Install scripts and prebuilt binaries
- Multi-OS source builds
- Security properties
```

### 11.4 What is not claimed

```text
- Build reproducibility, functional reproducibility
- Security review or product operational readiness
- Independent verification (E4)
- That cargo will succeed after container bootstrap
- That Windows host is ready (C-015 is BLOCKED)
- That Docker/Linux path is fully ready (C-016 is PARTIAL only)
- Overall product PASS
```

### 11.5 Reproduction class

| Class | Selected |
|-------|----------|
| Owner-side reproduction | ☑ |
| Independent reproduction | ☐ |
| Neither | ☐ |

## 12. Phase C2A Image Pin Summary

| Field | Value |
|-------|-------|
| Selected image | `docker.io/library/rust:1.92.0` |
| linux/amd64 digest | `sha256:6ca5ad23231207874325a751b9df584d51cd42c066c74c6963c264e3233c3e8e` |
| Pull performed | No |
| Custom image | No |

## Change Log

| Date | Change |
|------|--------|
| 2026-07-17 | Phase B + C1 results |
| 2026-07-18 | Phase C2A Docker readiness results |

---

**Evidence before authority.**
