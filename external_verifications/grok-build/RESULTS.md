# Results — xAI Grok Build

| Field | Value |
|-------|-------|
| Target slug | `grok-build` |
| Results status | **Phase B recorded** |
| Compiled by | Weaver Forge documentation package author |
| Role | Owner-side inspector (not independent witness) |
| Compilation date | `2026-07-17` |
| Linked reproduction run ID | `run-20260717-phase-b-source-pin` |
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

## 3. Build Results

| Check | Status | Evidence |
|-------|--------|----------|
| Dependencies installed as documented | `NOT_STARTED` | |
| Build command completed | `NOT_STARTED` | |
| Build artifacts produced | `NOT_STARTED` | |
| Build reproducibility (repeat run) | `NOT_STARTED` | |

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

## 7. Failures, Warnings, and Anomalies

| ID | Severity | Description | Status |
|----|----------|-------------|--------|
| A-001 | low | Zero GitHub Releases/tags at inspection | open (informational) |
| A-002 | medium | No publisher tree checksums or signed tags | open |
| A-003 | medium | Windows source builds documented best-effort | open for future build phase |

## 8. Blockers

| Block ID | Description | Blocks | Status |
|----------|-------------|--------|--------|
| BK-001 | Build/run not authorized in Phase B | C-012, C-013; build/functional axes | `BLOCKED` for those axes |
| BK-002 | Independent witness unassigned | C-014 | open |

## 9. Aggregate Counts

| Status | Claims |
|--------|-------:|
| `NOT_STARTED` | 3 |
| `PASS` | 11 |
| `PARTIAL` | 0 |
| `FAIL` | 0 |
| `BLOCKED` | 0 (claims); build steps blocked by plan |
| `NOT_APPLICABLE` | integrity sub-checks as above |

## 10. Owner-Side vs Independent Witness

| Result class | Status | Notes |
|--------------|--------|-------|
| Owner-side reproduction results | `PARTIAL` | Clone/inspect only |
| Independent witness results | `NOT_STARTED` | |

| Field | Value |
|-------|-------|
| Reproduction class for **this** results file | **Owner-side reproduction** (source inspection) |
| Operator is uninvolved third party for package? | No (package author) |

## 11. Mandatory Evidence Boundaries

### 11.1 What was observed

```text
- Public clone of https://github.com/xai-org/grok-build at full commit
  98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce (subject: Synced from monorepo).
- Official pages https://x.ai/news/grok-build-open-source and
  https://x.ai/open-source linking to that repository and describing open source.
- Root LICENSE Apache-2.0; workspace license Apache-2.0; Cargo edition 2024;
  rust-toolchain 1.92.0; Cargo.lock present; key file SHA-256 values.
- Documented cargo build/check/clippy/fmt command strings in README/open-source page.
- No GitHub releases or tags; no submodules; clean working tree at pin.
```

### 11.2 What was not observed

```text
- Successful or failed cargo build/check/test output
- Running grok / xai-grok-pager binary behavior
- Authentication browser flow
- Publisher-published SHA-256 for the git tree or signed tags
- Independent witness attestation
```

### 11.3 What was not tested

```text
- All build, lint, format, unit/integration tests
- Headless mode, tool-call dispatch, MCP, plugins at runtime
- Install scripts and prebuilt binaries
- Multi-OS source builds
- Security properties
```

### 11.4 What is not claimed

```text
- Build reproducibility, functional reproducibility
- Security review or operational readiness
- Independent verification (E4)
- Overall product PASS
- That main remains at this commit forever
```

### 11.5 Reproduction class

| Class | Selected |
|-------|----------|
| Owner-side reproduction | ☑ (clone/inspect) |
| Independent reproduction | ☐ |
| Neither | ☐ |

## 12. What These Results Prove

- Phase B identity pin and primary-source documentation claims as in the claim register.
- Local integrity hashes for key files at the pin.

## 13. What These Results Do NOT Prove

- Build/functional success
- Security or production readiness
- Independent witness confirmation

## Change Log

| Date | Change | Author |
|------|--------|--------|
| 2026-07-17 | Initial empty shell | Weaver Forge documentation package author |
| 2026-07-17 | Phase B results | Weaver Forge documentation package author |

---

**No hype without evidence.**
