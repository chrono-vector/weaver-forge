# Witness Handoff — xAI Grok Build

| Field | Value |
|-------|-------|
| Target slug | `grok-build` |
| Handoff status | **Owner-side results complete through C2D-2; Witness package NOT READY — `1.0.0-rc3` / canonical tag `grok-build-witness-v1.0.0-rc3`; Independent Witness NOT_STARTED** |
| Prepared by | Weaver Forge documentation package author |
| Preparer role | Owner-side package author (not the witness) |
| Prepared date | `2026-07-22` |
| Verification-plan version / date | Phase C2E-4 2026-07-22 |
| Current package version | `1.0.0-rc3` (canonical package tag `grok-build-witness-v1.0.0-rc3`; availability verified by annotated-tag resolution) |
| Immutable historical releases | `grok-build-witness-v1.0.0-rc1` → NOT READY repeat audit (C-024); `grok-build-witness-v1.0.0-rc2` → NOT READY integrated four-batch static audit (C-025) |
| Independent witness | *unassigned* |
| Witness completion status | `NOT_STARTED` |
| **Canonical Witness package** | **`external_verifications/grok-build/witness-package/README.md`** |

Pinned commit: **`98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce`**

---

## 1. Independence Requirements

Witness must have no authorship on reviewed target commits, no authorship on owner-side package claims being attested, must not be the owner-side reproducer for the witnessed run, and must claim only direct observations.

**Contributor ≠ Witness. Owner-side ≠ Independent witness. This handoff ≠ E4 completion.**

---

## 2. Package Inventory

| Item | Path / URL | Present? |
|------|------------|----------|
| Verification plan | `VERIFICATION_PLAN.md` | Yes |
| Source identity | `SOURCE_IDENTITY.md` | Yes |
| Claim register | `CLAIM_REGISTER.md` | Yes |
| Environment | `ENVIRONMENT.md` | Yes |
| Reproduction | `REPRODUCTION.md` | Yes |
| Results | `RESULTS.md` | Yes |
| Verdict | `VERDICT.md` | Yes |
| Evidence (Phase B) | `evidence/source-inspection/` | Yes |
| Evidence (Phase C1 env readiness) | `evidence/environment-readiness/` | Yes |
| Evidence (Phase C2A Docker readiness) | `evidence/docker-readiness/` | Yes |
| Evidence (Phase C2B-1 container toolchain) | `evidence/container-toolchain/` | Yes |
| Evidence (Phase C2B-2 container bootstrap) | `evidence/container-bootstrap/` | Yes |
| Evidence (Phase C2B-3 cargo check) | `evidence/cargo-check/` | Yes |
| Evidence (Phase C2B-4 cargo build) | `evidence/cargo-build/` | Yes |
| Evidence (Phase C2C-1 startup boundary) | `evidence/startup-boundary/` | Yes |
| Evidence (Phase C2D-1 clean rebuild) | `evidence/clean-rebuild/` | Yes |
| Evidence (Phase C2D-2 artifact variance) | `evidence/artifact-variance/` | Yes |
| C2B-4 completion note | `docs/GROK_BUILD_NARROW_CARGO_BUILD_COMPLETION_NOTE.md` | Yes |
| C2C-1 completion note | `docs/GROK_BUILD_STARTUP_BOUNDARY_COMPLETION_NOTE.md` | Yes |
| C2D-1 completion note | `docs/GROK_BUILD_CLEAN_REBUILD_COMPLETION_NOTE.md` | Yes |
| C2D-2 completion note | `docs/GROK_BUILD_ARTIFACT_VARIANCE_ANALYSIS_COMPLETION_NOTE.md` | Yes |
| **Witness package (canonical)** | **`witness-package/README.md` + runbook** | **Yes (C2E-1)** |
| Witness readiness evidence | `evidence/witness-package-readiness/` | Yes |
| C2E-1 completion note | `docs/GROK_BUILD_WITNESS_PACKAGE_READINESS_AUDIT_COMPLETION_NOTE.md` | Yes |
| Official target | https://github.com/xai-org/grok-build | Yes |

---

## 3. Pinned Source Reference

| Field | Value |
|-------|-------|
| Canonical repository URL | https://github.com/xai-org/grok-build |
| Source-control owner | `xai-org` |
| Branch | `main` (pin is commit, not floating tip) |
| Tag | none |
| **Full commit ID** | **`98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce`** |
| Docs revision used | same commit README + https://x.ai/open-source (fetched 2026-07-17) |
| Pin freeze date | 2026-07-17 |
| Pin status | **frozen** for this package revision |

---

## 4. Artifact Hash

| Field | Value |
|-------|-------|
| Artifact type | git commit / tree |
| Hash algorithm | git commit SHA-1 ID; git tree OID; SHA-256 of key files |
| Full commit | `98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce` |
| Tree OID | `b40a1962cb8061b85c2354850ab4d5707f48414b` |
| Key file SHA-256 list | `evidence/source-inspection/FILE_HASHES_SHA256.txt` |
| Hash source | self-computed after acquire; publisher digests not found |
| Signature | none observed |
| Hash status | recorded (`PARTIAL` integrity — no publisher checksum match) |

---

## 5. Environment Prerequisites

| Prerequisite | Required value / constraint | Status |
|--------------|----------------------------|--------|
| OS | Any with git for identity re-check; **macOS/Linux preferred** for source build (Windows best-effort) | documented |
| Git | Full clone capability | required |
| Rust | channel **1.92.0** via rust-toolchain.toml / rustup | **required before cargo** |
| DotSlash | on PATH before build | **required as documented** |
| Preferred isolated path (owner-side C2B) | Docker Desktop Linux + pinned `rust@sha256:6ca5ad23231207874325a751b9df584d51cd42c066c74c6963c264e3233c3e8e` | **pulled C2B-1**; rustc/cargo 1.92.0 verified direct |
| protoc | via bin/protoc DotSlash or PATH/PROTOC | required as documented; **not installed C2B-1** |
| Network | HTTPS to GitHub (clone); crates/DotSlash likely for build | |
| Credentials | none for public clone | public-only preferred |
| Cargo.lock | use tree as-is | present at pin |
| Owner-side C1 note | Inventoried Windows host **lacks** rustup/cargo/dotslash — do not assume witness host matches | Windows path `BLOCKED` |
| Owner-side C2A note | Image digest pinned via registry | historical |
| Owner-side C2B-1 note | Pull + RepoDigest match; rustc/cargo 1.92.0; avoid bare `bash -lc` without PATH | image/toolchain `PASS` |
| Owner-side C2B-2 note | packages; DotSlash 0.5.7; protoc 29.3; use LF-safe DotSlash for `bin/protoc` on Windows mounts | bootstrap `PASS` |

---

## 6. Exact Verification Commands

### 6.1 Identity re-check (executable now)

```text
git clone https://github.com/xai-org/grok-build.git grok-build
cd grok-build
git checkout 98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce
git rev-parse HEAD
# expect: 98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce
git status
# expect: clean (detached HEAD OK)
```

Optional hash recompute for `README.md`, `LICENSE`, `Cargo.toml`, `Cargo.lock` vs `FILE_HASHES_SHA256.txt`.

### 6.2 Build/validate (documented; **not** Phase B witness scope until authorized)

```text
cargo run -p xai-grok-pager-bin
cargo check -p xai-grok-pager-bin
cargo clippy -p <crate>
cargo fmt --all
```

Command set status: identity commands **frozen**; build commands **documented only** / execution `NOT_STARTED`.

### 6.3 Container path (owner-side)

**C2B-1 done (owner-side):** pull pin; verify RepoDigest; direct rustc/cargo 1.92.0. See `evidence/container-toolchain/`.

```text
docker pull docker.io/library/rust@sha256:6ca5ad23231207874325a751b9df584d51cd42c066c74c6963c264e3233c3e8e
# prefer direct rustc/cargo or export PATH — bare bash -lc may miss cargo bin
```

**C2B-2 done:** packages + DotSlash 0.5.7 + protoc 29.3 (see `evidence/container-bootstrap/`).

**C2B-3/C2B-4 done (owner-side):** check + incremental build exit 0; artifact hash in `evidence/cargo-build/`.

**C2C-1 done (owner-side; whole-session):** non-conformant draft ran six version/help product commands (exit 0; disposable HOME side effects); draft evidence discarded. Final gated procedure: static inspect + safety gate FAIL (parse after init); product **not** re-executed. Classification **STATIC STARTUP PARTIAL**; C-019 **PARTIAL**. Canonical evidence: `evidence/startup-boundary/` only (no `evidence/safe-startup/`).

**C2D-1 done (owner-side):** clean non-incremental `cargo build -p xai-grok-pager-bin --locked` with empty target and `CARGO_INCREMENTAL=0`; exit 0 in 85m 21s; new artifact SHA-256 `eebdbe81a8fc34645a2f3c72aad36825d692fbef594a6c540f77ffaa42c18dad` (**differs** from C2B-4). **CLEAN REBUILD PASS**; **BIT_IDENTICAL_NOT_OBSERVED**. Product **not** executed. Evidence: `evidence/clean-rebuild/`.

**C2D-2 done (owner-side):** static variance analysis of C2B-4 vs C2D-1 artifacts (no execution, no `ldd`, no rebuild). 15 identical / 30 differing sections; **`.text` differs**; GNU Build IDs differ (identifier of distinct linked outputs, not a root cause); embedded paths `/work/cargo-target` vs `/work/cargo-target-c2d1` (supported likely metadata contributor). Executable/relocation differences documented without isolating incremental-vs-clean as sole cause. **ARTIFACT VARIANCE ANALYSIS PASS**; root-cause confidence **LIKELY** (partial; unique full cause not established). Evidence: `evidence/artifact-variance/`.

**C2E-1 done (owner-side package audit):** Independent Witness package prepared at `witness-package/` (public entry points, fixed identities, portable runbook, templates, classification, submission, redaction). Classification **WITNESS PACKAGE READY WITH LIMITATIONS** — this classification was later **superseded**. **Independent Witness remains `NOT_STARTED`.** A new Witness must follow **`witness-package/README.md`** and **`WITNESS_RUNBOOK.md`** only — not owner `C:\dev\...` evidence paths.

**C2E-2/C2E-3 done (owner-side audit intake):** A public-entry-point blind audit (C-023) and a repeat blind audit against immutable tag `grok-build-witness-v1.0.0-rc1` (commit `89127c78c3a11492892de7e3b5f0dee18d71775a`; C-024) were recorded. Both audit verdicts were **NOT READY**. `grok-build-witness-v1.0.0-rc1` is preserved as an **immutable historical release**.

**C2E-4 done (owner-side audit intake; rc3 package content prepared):** An integrated four-batch static blind audit against immutable tag `grok-build-witness-v1.0.0-rc2` (commit `255b357c9ee33c4a9e34b5d9b6e396c53cfe494e`; C-025) was recorded. Audit verdict **NOT READY**. `grok-build-witness-v1.0.0-rc2` is preserved as an **immutable historical release**. No Docker, cargo, rustc, rustup, DotSlash, protoc, `ldd`, witness scripts, or product execution occurred during this audit intake. Package version is **`1.0.0-rc3`**; canonical package tag is **`grok-build-witness-v1.0.0-rc3`** (availability verified by tag resolution). **Independent Witness (C-014) remains `NOT_STARTED`.**

**C2E-4B (tagged-snapshot wording finalization):** Normative release-facing documents use time-stable identity language so the fixed tagged snapshot does not assert “tag absent/pending” as a current fact. Later `main`-branch status/audit records remain outside the tagged snapshot.

---

## 7. Expected Machine-Readable Outputs

| Step | Expected | Source |
|------|----------|--------|
| `git rev-parse HEAD` | `98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce` | this pin |
| SHA-256 README.md | `1bb63fa93716ab25796f43eeb22871a60c0ca59b3bc41872f22e33bf68d6e64a` | FILE_HASHES |
| SHA-256 LICENSE | `f481edaaea56bb9fadac0191287f3b243a4bf63114a707a2b2a267fbfea598d5` | FILE_HASHES |
| SHA-256 Cargo.toml | `6eaaed53c43fb4ae42d50378bacbfdda614c3a385a02ee41d9077c30010b7ae8` | FILE_HASHES |
| SHA-256 Cargo.lock | `1512bb4fef0c1166c6a15a3398da9593903be1759b759ce78d9958913e61b421` | FILE_HASHES |
| cargo * | **unknown — not yet measured** | NOT_STARTED |

---

## 8. Tolerances

| Check | Tolerance |
|-------|-----------|
| Commit ID | exact match |
| File SHA-256 | exact match |
| cargo results | not defined until build phase |

---

## 9. Known Limitations

| ID | Limitation | Status |
|----|------------|--------|
| KL-001 | No signed tags / publisher tree checksums | open |
| KL-002 | Grok Build cargo not run; Windows BLOCKED; image/toolchain PASS only | open |
| KL-003 | Windows source builds best-effort per upstream docs | open |
| KL-006 | rustup/cargo/dotslash missing on owner-side Windows host | open |
| KL-007 | C2A daemon stopped — resolved for C2B-1 pull | closed for C2B-1 |
| KL-008 | Login-shell PATH may omit rustc; use direct or export PATH | open |
| KL-009 | DotSlash/packages bootstrap done; Grok deps/cargo check not | open (C2B-3) |
| KL-011 | CRLF shebang on Windows-mounted DotSlash files | open (mitigation: LF copy / PROTOC) |
| KL-004 | Auth may be required for interactive product use | open |
| KL-005 | Owner-side results are not substitute for witness | open |

---

## 10. Independence Declaration

| Field | Value |
|-------|-------|
| Witness name / handle | *unassigned* |
| Declaration | not completed |

Template text remains for future witness (see template). Declaration status: `NOT_STARTED`.

---

## 11. Result-Submission Procedure

| Field | Value |
|-------|-------|
| Submission channel | PR updating `external_verifications/grok-build/` or agreed path |
| Required artifacts | completed handoff, environment, transcripts, exit codes, hash recompute |
| Redaction | no secrets |

### Submission checklist (identity-only witness)

- [x] Pinned source reference recorded
- [x] Artifact hash / key hashes recorded
- [ ] Witness independence declaration completed
- [ ] Witness re-ran identity commands
- [ ] Build axes (if in scope) still separate

---

## 12. Witness Results

| Claim ID or step | Status |
|------------------|--------|
| *none — witness not run* | `NOT_STARTED` |

All axes under witness column: `NOT_STARTED`.

---

## 13. Mandatory Evidence Boundaries (Witness)

### 13.1 What was observed

```text
Nothing by an independent witness. Owner-side Phase B only.
```

### 13.2 What was not observed

```text
Independent re-clone attestation; independent hash recompute by third party.
```

### 13.3 What was not tested

```text
Full witness procedure; all build/runtime tests.
```

### 13.4 What is not claimed

```text
Independent verification; E4; build success; security; production readiness.
```

### 13.5 Reproduction class

| Class | Selected |
|-------|----------|
| Independent reproduction | ☐ |
| Owner-side reproduction | ☐ (witness section) |
| Neither / blocked | ☑ (no witness run) |

---

## 14. Witness Conclusion

| Conclusion | Selected |
|------------|----------|
| `NOT_STARTED` | ☑ |
| `BLOCKED` | ☐ |
| Reproduced (`PASS`) | ☐ |
| Partially reproduced (`PARTIAL`) | ☐ |
| Not reproduced (`FAIL`) | ☐ |
| `NOT_APPLICABLE` | ☐ |

---

## 15–16. Handoff proves / does not prove

**Proves:** pin and identity re-check procedure are written for a future witness.
**Does not prove:** that independent verification occurred, E4, build success, or security.

## Change Log

| Date | Change | Author |
|------|--------|--------|
| 2026-07-17 | Shell | Weaver Forge documentation package author |
| 2026-07-17 | Phase B pin + identity commands frozen | Weaver Forge documentation package author |
| 2026-07-17 | Phase C1 env readiness BLOCKED noted | Weaver Forge documentation package author |
| 2026-07-22 | Phase C2E-2/C2E-3: public blind audit (C-023) and rc1 repeat blind audit (C-024) recorded; both NOT READY; rc1 preserved immutable | Weaver Forge documentation package author |
| 2026-07-22 | Phase C2E-4: rc2 integrated four-batch static blind audit (C-025) recorded; verdict NOT READY; rc2 preserved immutable; package version `1.0.0-rc3` / canonical tag `grok-build-witness-v1.0.0-rc3`; C-014 still NOT_STARTED | Weaver Forge documentation package author |
| 2026-07-22 | Phase C2E-4B: tagged-snapshot release-wording finalization | Weaver Forge documentation package author |

---

**E4 is not complete because this handoff exists. E4 requires execution by an uninvolved third party.**
