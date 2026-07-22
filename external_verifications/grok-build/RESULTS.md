# Results — xAI Grok Build

| Field | Value |
|-------|-------|
| Target slug | `grok-build` |
| Results status | **owner-side through C2D-2 PASS axes; Witness package NOT READY (`1.0.0-rc4` / canonical tag `grok-build-witness-v1.0.0-rc4`; rc4 package content under preparation); Independent Witness NOT_STARTED; overall PARTIAL** |
| Compiled by | Weaver Forge documentation package author |
| Role | Owner-side inspector (not independent witness) |
| Compilation date | `2026-07-22` (C2E-5) |
| Linked reproduction run ID | C2E-1 `run-20260722-witness-package-readiness` |
| Linked claim register | `CLAIM_REGISTER.md` |
| Pinned commit | `98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce` |

---

## 1. Run Metadata

| Field | Value |
|-------|-------|
| Source identity reference | `98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce` |
| Environment reference | `ENVIRONMENT.md` |
| Reproduction reference | `REPRODUCTION.md` |
| Execution authorized (build/run)? | check + build; C2C-1 product exec only if safety gate passes (≤1 invocation) |
| Execution performed | **check + build**; C2C-1: **draft** six version/help invocations (non-conformant); **final gate** product not re-executed |
| Phase C2C-1 static startup | **`PARTIAL`** (draft observations + final safety gate withhold; protocol FAIL) |
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
| Phase C2B-3 (cargo check) | **`PASS`** |
| Phase C2B-4 (cargo build) | **`PASS`** (exit 0; 43m 18s; incremental) |
| Phase C2D-1 (clean non-incremental rebuild) | **`PASS`** (exit 0; 85m 21s; BIT_IDENTICAL_NOT_OBSERVED) |
| Phase C2D-2 (static artifact variance) | **`PASS`** (15 identical / 30 differing sections; `.text` differs) |
| Phase C2E-1 (Witness package readiness) | **READY WITH LIMITATIONS** (historical; superseded) |
| Phase C2E-2 (Executability closure) | **NOT READY — remediation materials prepared; re-audit required** |
| Phase C2E-3 (rc1 repeat blind audit intake) | **NOT READY** (audit intake recorded; rc1 preserved immutable) |
| Phase C2E-4 (rc2 integrated four-batch static blind audit intake; rc3 package content) | **NOT READY** (audit intake recorded; rc2 preserved immutable; package version `1.0.0-rc3`; canonical tag `grok-build-witness-v1.0.0-rc3`) |
| Phase C2E-5 (rc3 integrated four-batch static audit intake; rc4 package content) | **NOT READY** (audit intake recorded; audit preserved under `evidence/rc3-static-blind-audit/`; rc3 preserved immutable; package version `1.0.0-rc4`; canonical tag `grok-build-witness-v1.0.0-rc4`) |

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
| C-012 | Broad/release build claims | `NOT_STARTED` | — |
| C-013 | Validation cargo check | `PASS` | evidence/cargo-check/ |
| C-014 | Independent witness | `NOT_STARTED` | — |
| C-015 | Windows host build env ready | `BLOCKED` | evidence/environment-readiness/ (C1) |
| C-016 | Docker/Linux image+toolchain ready | `PASS` | evidence/container-toolchain/ |
| C-017 | Container bootstrap packages/DotSlash/protoc | `PASS` | evidence/container-bootstrap/ |
| C-018 | Narrow cargo build | `PASS` | evidence/cargo-build/ |
| C-019 | Static startup boundary (help/version) | `PARTIAL` | evidence/startup-boundary/ |
| C-020 | Clean non-incremental narrow rebuild | `PASS` | evidence/clean-rebuild/ |
| C-021 | Static artifact variance analysis (C2B-4 vs C2D-1) | `PASS` | evidence/artifact-variance/ |
| C-022 | Independent Witness package readiness | `PASS` (C2E-1 audit only; **superseded for readiness**) | evidence/witness-package-readiness/ |
| C-023 | Public blind audit intake | `PASS` (recording only) | evidence/public-blind-audit/ |
| C-024 | RC1 repeat blind audit intake | `PASS` (recording only; audit verdict **NOT READY**) | evidence/rc1-repeat-blind-audit/ |
| C-025 | RC2 integrated four-batch static blind audit intake | `PASS` (recording only; audit verdict **NOT READY**) | evidence/rc2-static-blind-audit/; evidence/rc2-integrated-blind-audit-remediation/ |
| C-026 | RC3 integrated four-batch static blind audit | `PASS` (display label `AUDIT_RECORDED`; recording only; audit verdict **NOT READY**) | evidence/rc3-static-blind-audit/ |

## 3. Build Results

| Check | Status | Evidence |
|-------|--------|----------|
| Dependencies acquired (check run) | `PASS` | network crates.io; lock unchanged |
| `cargo check -p xai-grok-pager-bin` | `PASS` | C2B-3 |
| `cargo build -p xai-grok-pager-bin` | `PASS` | C2B-4 incremental; artifact hash recorded |
| Clean rebuild `cargo build -p xai-grok-pager-bin --locked` + `CARGO_INCREMENTAL=0` | `PASS` | C2D-1; new empty target; 85m 21s |
| Bit-identical C2B-4 vs C2D-1 | **NOT_OBSERVED** | sizes/hashes differ |
| Release (`--release`) / full workspace | `NOT_STARTED` | |
| Build reproducibility (clean-room/bit-identical/witness) | axis **PARTIAL** | owner-side clean rebuild PASS; not bit-identical; no witness |
| Windows build-env readiness | `BLOCKED` | |
| Docker image+toolchain | `PASS` | |
| Bootstrap | `PASS` | |

## 4. Test Results

| Suite / check | Status | Log path |
|---------------|--------|----------|
| cargo check -p xai-grok-pager-bin | `PASS` | evidence/cargo-check/ |
| cargo build -p xai-grok-pager-bin | `PASS` | evidence/cargo-build/ |
| cargo test/run/clippy/fmt | `NOT_STARTED` | |

## 5. Runtime / Functional Observations

| Observation ID | Status | Notes |
|----------------|--------|-------|
| O-001 product TUI / auth / agent | `NOT_STARTED` | Not run |
| O-002 draft version/help (non-conformant) | observational **PASS**; protocol **FAIL** | six cmds; `grok 0.2.102 (98c3b24)`; `$HOME/.grok` writes |
| O-003 final gated product CLI | **NOT EXECUTED** | SAFETY GATE NOT SATISFIED |
| O-004 safe pre-init CLI boundary | **NOT ESTABLISHED** | parse after init |

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
| `NOT_STARTED` | 2 (C-012, C-014) |
| `BLOCKED` | 1 (C-015) |
| `PASS` | 21 (docs + C-013 + C-016–C-018 + C-020 + C-021 + C-023 + C-024 + C-025 + C-026) |
| `HISTORICAL SUPERSEDED` | 1 (C-022) |
| `PARTIAL` | 1 (C-019) |
| `FAIL` | 0 |
| `NOT_APPLICABLE` | integrity sub-checks as above |
| **Total** | **26** |

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
- Pin 98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce intact; C2B-3/4 check+build PASS (prior).
- C2C-1 draft (non-conformant): six version/help product commands under --network=none + disposable HOME;
  exit 0; version grok 0.2.102 (98c3b24); writes under $HOME/.grok.
- C2C-1 final gate: parse after init; product NOT re-executed; STATIC STARTUP PARTIAL.
- Draft evidence/safe-startup discarded; canonical evidence only under evidence/startup-boundary/.
```

### 11.2 What was not observed

```text
- Protocol-conformant single gated help/version after pre-init safety PASS
- Filesystem-side-effect-free startup
- Syscall-level proof of no network activity
- TUI bare launch; login/OAuth; agent; models; update; product API auth
- Independent witness attestation
```

### 11.3 What was not tested

```text
- Normal TUI startup; login/OAuth; agent/prompts/models; update; API connectivity
- Functional correctness; service/production readiness; security
- cargo test/run/clippy/fmt; --release rebuild
- Windows native readiness
```

### 11.4 What is not claimed

```text
- C-019 PASS or static startup PASS
- Protocol-conformant C2C-1 product execution
- Filesystem-side-effect-free CLI startup
- Functional / security / production / witness readiness
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
| 2026-07-18 | Phase C2B-4 cargo build exit 0 (incremental) |
| 2026-07-22 | Phase C2C-1 static startup PARTIAL (execution withheld; safety gate) |
| 2026-07-22 | C2C-1 whole-session disclosure correction (draft six invocations recorded) |
| 2026-07-22 | Phase C2D-1 clean non-incremental rebuild PASS (bit-identical not observed) |
| 2026-07-22 | Phase C2D-2 static artifact variance analysis PASS | |
| 2026-07-22 | Phase C2E-1 Witness package readiness READY WITH LIMITATIONS; C-014 still NOT_STARTED | |
| 2026-07-22 | Phase C2E-2/C2E-3: public blind audit (C-023) and rc1 repeat blind audit (C-024) recorded; both NOT READY; package NOT READY | |
| 2026-07-22 | Phase C2E-4: rc2 integrated four-batch static blind audit (C-025) recorded; verdict NOT READY; rc1 and rc2 preserved as immutable historical releases; package version `1.0.0-rc3` / canonical tag `grok-build-witness-v1.0.0-rc3`; C-014 still NOT_STARTED; per-claim table de-duplicated and reordered; aggregate counts recalculated to 25 | |
| 2026-07-22 | Phase C2E-4B: tagged-snapshot release-wording finalization (time-stable rc3 identity language; no normative “tag absent/pending” assertions) | |
| 2026-07-22 | Phase C2E-5: rc3 integrated four-batch static blind audit (C-026) recorded; verdict NOT READY; audit preserved under `evidence/rc3-static-blind-audit/`; rc1, rc2, and rc3 preserved as immutable historical releases; package version `1.0.0-rc4` / canonical tag `grok-build-witness-v1.0.0-rc4`; C-014 still NOT_STARTED; aggregate counts recalculated to 26; time-stable rc4 identity wording applied (no normative “tag absent/pending” assertions) | |

---

**Evidence before authority.**
