# Source Identity — xAI Grok Build

| Field | Value |
|-------|-------|
| Target slug | `grok-build` |
| Project | **Grok Build** (`grok` CLI/TUI) |
| Brand / product presentation (as stated) | **SpaceXAI** — string appears in inspected primary sources listed below; **not** equated here to GitHub org or Cargo authors |
| Copyright notice (LICENSE) | `Copyright 2023-2026 SpaceXAI` |
| Cargo package authors field | `"xAI"` (e.g. `xai-grok-pager-bin` crate) |
| GitHub organization (repository owner path) | `xai-org` |
| Claimed canonical repository | **https://github.com/xai-org/grok-build** |
| Current verification state | **Phase B pin held; Phase C1 build-env readiness BLOCKED; build not run** |
| Identity status | **Pinned** — full commit recorded; live primary sources inspected |
| Recorded by | Weaver Forge documentation package author |
| Role | Owner-side inspector (not independent witness) |
| Record date | `2026-07-17` |
| Independent verification of identity | `NOT_STARTED` |

Evidence directory: `evidence/source-inspection/`

---

## 1. Identity layers (do not collapse)

These are **distinct** fields observed at pin. Equivalence is **not** claimed.

| Layer | Observed value | Exact primary-source pointer |
|-------|----------------|------------------------------|
| Brand / product presentation | String **SpaceXAI** in product copy | README: “**Grok Build** is SpaceXAI's terminal-based AI coding agent”; CONTRIBUTING: “SpaceXAI develops this software internally”; https://x.ai/news/grok-build-open-source and https://x.ai/open-source (Phase B inspection: SpaceXAI wording on those pages) |
| Copyright holder line | `Copyright 2023-2026 SpaceXAI` | Root `LICENSE` line 1 |
| Cargo authors | `authors = ["xAI"]` | `crates/codegen/xai-grok-pager-bin/Cargo.toml` |
| GitHub organization / repository owner path | `xai-org` | https://github.com/xai-org/grok-build ; clone origin |
| Website host | `x.ai` | Official pages and README links (domain identity ≠ org path ≠ copyright string) |

| Field | Value |
|-------|-------|
| Publisher type | company (as presented; no legal-entity audit) |
| Official website / news | https://x.ai/news/grok-build-open-source ; https://x.ai/open-source |
| Source confidence | **high** that the public repo is the open-source tree linked from those pages |
| Confidence basis | Official x.ai pages link to this GitHub repo; README/LICENSE/CONTRIBUTING use string SpaceXAI; Cargo authors use `"xAI"`; GitHub path is `xai-org` — layers recorded separately |
| What is not claimed | That SpaceXAI, xAI, and xai-org are the same legal entity |

## 2. Canonical Repository or Release URL

| Field | Value |
|-------|-------|
| Canonical repository URL | https://github.com/xai-org/grok-build |
| Canonical release / download URL | Prebuilt install via https://x.ai/cli (scripts); **no GitHub Releases** published at inspection time |
| Mirror URLs (if any) | none recorded |
| Docs / project page URL | https://docs.x.ai/build/overview ; https://x.ai/cli ; https://x.ai/open-source |
| How canonicity was established | Official announcement and open-source page both link to `xai-org/grok-build`; repo public and cloneable |

## 3. Source-Control Owner

| Field | Value |
|-------|-------|
| Hosting platform | GitHub |
| Organization or user | `xai-org` |
| Repository name | `grok-build` |
| Visibility | **public** |
| Default branch (as advertised and observed) | `main` |
| Owner verification notes | Org path matches announcement links; no separate legal-entity audit performed |

## 4. Artifact Acquisition Method

| Field | Value |
|-------|-------|
| Planned acquisition method | full `git clone` |
| Exact acquisition command | `git clone https://github.com/xai-org/grok-build.git C:\dev\external-verification-targets\grok-build` |
| Acquisition performed? | **Yes** (read-only) |
| Acquisition date | 2026-07-17 23:20:33–23:20:56 +09:00 |
| Acquisition location (path) | `C:\dev\external-verification-targets\grok-build` |
| Network conditions | online |
| Status | `PASS` (clone succeeded; clean tree at pin) |

## 5. License

| Field | Value |
|-------|-------|
| License name / SPDX ID | Apache License, Version 2.0 / **Apache-2.0** |
| License file path in artifact | `LICENSE` (repository root) |
| License URL | http://www.apache.org/licenses/ (referenced in LICENSE text) |
| License status | **confirmed** in tree + GitHub API `apache-2.0` + workspace `license = "Apache-2.0"` |
| Restrictions relevant to verification | Third-party/vendored code under separate notices (`THIRD-PARTY-NOTICES`, etc.); external contributions not accepted (`CONTRIBUTING.md`) |
| LICENSE SHA-256 | `f481edaaea56bb9fadac0191287f3b243a4bf63114a707a2b2a267fbfea598d5` |

## 6. Version Identity

| Field | Value |
|-------|-------|
| Advertised package version (pager-bin crate) | `0.2.102` (static read of `crates/codegen/xai-grok-pager-bin/Cargo.toml`) |
| Tag | **none** on repository at inspection |
| Branch | `main` |
| Full commit ID (40-char) | **`98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce`** |
| Short commit ID | `98c3b24` |
| Commit date | `2026-07-17T14:19:50+01:00` |
| Commit subject | `Synced from monorepo` |
| Commit ID verification method | `git rev-parse HEAD` after full clone; matches `origin/main` |
| Monorepo SOURCE_REV file | `124d85bc5dc6e7805560215fcc6d5413944920e1` (content of root `SOURCE_REV`) |
| Git tree OID | `b40a1962cb8061b85c2354850ab4d5707f48414b` |
| Version status | **pinned for this package revision** |

## 7. Artifact File Identity

Git tree pin is primary. Key file hashes (self-computed):

| Filename | Size (bytes) | SHA-256 |
|----------|-------------:|---------|
| README.md | 5897 | `1bb63fa93716ab25796f43eeb22871a60c0ca59b3bc41872f22e33bf68d6e64a` |
| LICENSE | 11592 | `f481edaaea56bb9fadac0191287f3b243a4bf63114a707a2b2a267fbfea598d5` |
| Cargo.toml | 15983 | `6eaaed53c43fb4ae42d50378bacbfdda614c3a385a02ee41d9077c30010b7ae8` |
| Cargo.lock | 353616 | `1512bb4fef0c1166c6a15a3398da9593903be1759b759ce78d9958913e61b421` |

Hash match vs publisher-published digests: **`NOT_APPLICABLE` / not available** — no publisher checksum list for this git tree was found. Status of self-hash record: recorded (`PASS` as local measurement only).

## 8. Signature and Signing Keys

| Field | Value |
|-------|-------|
| Signature present? | No signed tags; no GPG signature trailer observed on HEAD |
| Signature type | none observed for git pin |
| Verification status | `NOT_APPLICABLE` / none available to verify |

## 9. Hash or Immutable Reference Summary

| Reference type | Value | Status |
|----------------|-------|--------|
| Full commit ID | `98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce` | pinned |
| Git tree OID | `b40a1962cb8061b85c2354850ab4d5707f48414b` | recorded |
| Content hash of archive | not produced | `NOT_APPLICABLE` |
| Container digest | | `NOT_APPLICABLE` |
| Key file SHA-256 set | `evidence/source-inspection/FILE_HASHES_SHA256.txt` | recorded |

## 10. Source Confidence

| Dimension | Rating | Notes |
|-----------|--------|-------|
| Publisher legitimacy | high | Official x.ai announcement linkage |
| URL canonicity | high | Consistent across news, open-source page, clone |
| Version immutability | high for pin | Full commit frozen; `main` may move later |
| Integrity reference strength | medium | Git commit/tree + local file hashes; no publisher checksum / signed tag |
| Overall source confidence | **high for public source identity pin** | Not a security audit |

## 11. Unresolved Identity Risks

| Risk ID | Description | Severity | Status |
|---------|-------------|----------|--------|
| IR-001 | `main` may advance after pin | medium | accepted — package pins full commit |
| IR-002 | No signed tags or publisher tree checksums | medium | open |
| IR-003 | Tree is monorepo sync; `SOURCE_REV` not independently verified outside this repo | medium | open |
| IR-004 | Prebuilt install scripts / binaries not integrity-checked | medium | out of Phase B scope |
| IR-005 | Third-party/vendored licensing complexity | low–medium | notices present; not deep-audited |

## 12. What This Identity Record Proves

- Public repository `xai-org/grok-build` was cloned read-only and frozen at full commit `98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce`.
- Official x.ai pages inspected in Phase B link to this repository as the open-source Grok Build source; brand string SpaceXAI appears in README/LICENSE/CONTRIBUTING and on those pages as recorded above.
- Root `LICENSE` is Apache-2.0 text; key file SHA-256 values were computed locally at that pin.

## 13. What This Identity Record Does NOT Prove

- Build or functional reproducibility
- Security or supply-chain freedom from compromise
- Correctness of publisher product claims beyond quoted docs
- Integrity of prebuilt installers or binaries
- Independent witness confirmation
- Operational readiness

## 14. Change Log

| Date | Change | Author |
|------|--------|--------|
| 2026-07-17 | Intake shell only | Weaver Forge documentation package author |
| 2026-07-17 | Phase B: primary-source inspection and commit pin | Weaver Forge documentation package author |

---

**Evidence before authority.**
