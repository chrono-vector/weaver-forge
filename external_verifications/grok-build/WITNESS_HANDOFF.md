# Witness Handoff — xAI Grok Build

| Field | Value |
|-------|-------|
| Target slug | `grok-build` |
| Handoff status | **Pin ready; Windows env BLOCKED; Docker/Linux PARTIAL with image digest pin; cargo not witness-executable yet** |
| Prepared by | Weaver Forge documentation package author |
| Preparer role | Owner-side package author (not the witness) |
| Prepared date | `2026-07-18` |
| Verification-plan version / date | `VERIFICATION_PLAN.md` Phase C2A 2026-07-18 |
| Independent witness | *unassigned* |
| Witness completion status | `NOT_STARTED` |

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
| C2A completion note | `docs/GROK_BUILD_DOCKER_BUILD_READINESS_COMPLETION_NOTE.md` | Yes |
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
| Preferred isolated path (owner-side C2B) | Docker Desktop Linux + pinned `rust@sha256:6ca5ad23231207874325a751b9df584d51cd42c066c74c6963c264e3233c3e8e` | planned; daemon must be running |
| protoc | via bin/protoc DotSlash or PATH/PROTOC | required as documented |
| Network | HTTPS to GitHub (clone); crates/DotSlash likely for build | |
| Credentials | none for public clone | public-only preferred |
| Cargo.lock | use tree as-is | present at pin |
| Owner-side C1 note | Inventoried Windows host **lacks** rustup/cargo/dotslash — do not assume witness host matches | Windows path `BLOCKED` |
| Owner-side C2A note | Docker client present; daemon stopped; image digest pinned; C2B plan defined | Docker path `PARTIAL` |

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

### 6.3 Container path (owner-side C2B plan; **not** executed in C2A)

See `evidence/docker-readiness/PHASE_C2B_CONTAINER_BUILD_PLAN.md`.

```text
docker pull docker.io/library/rust@sha256:6ca5ad23231207874325a751b9df584d51cd42c066c74c6963c264e3233c3e8e
# then isolated cargo check -p xai-grok-pager-bin with RO source mount
```

Status: procedure **defined**; execution `NOT_STARTED`.

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
| KL-002 | Build not yet authorized; Windows env BLOCKED; Docker PARTIAL | open |
| KL-003 | Windows source builds best-effort per upstream docs | open |
| KL-006 | rustup/cargo/dotslash missing on owner-side Windows host | open |
| KL-007 | Docker daemon stopped during C2A; local image not pulled | open |
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

---

**E4 is not complete because this handoff exists. E4 requires execution by an uninvolved third party.**
