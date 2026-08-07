# Independent Witness Package — Grok Build (narrow clean rebuild)

| Field | Value |
|-------|-------|
| Governance-selected Future Candidate | **Weaver Forge Future Candidate 1** / **WF-FC-01** / **`weaver-forge-fc-01`** |
| Future Candidate implementation state | **annotated tag CREATED AND PUBLISHED; package / archive / bundle NOT YET CREATED** |
| Normative mapping | **WF-FC-01 -> weaver-forge-fc-01** |
| Identity authority | **Repository Owner** (G-3) |
| Relationship to RC8 | **successor candidate only** |
| Relationship to RC9 | **NOT IMPLIED** |
| Last immutable historical static-audit candidate (RC8) | **1.0.0-rc8** / **`grok-build-witness-v1.0.0-rc8`** |
| RC8 annotated tag object ID | **`8113d952d3b127d32e138dbf804141f5d1dfb26f`** |
| RC8 peeled commit | **`1de4b4d9523711418390f8331c95988523ef4481`** |
| RC8 tree | **`87b40d8a32ca536a4cdba0eee474f6171c62f6bb`** |
| Last immutable historical NOT READY package version | **1.0.0-rc6** |
| Last immutable historical NOT READY canonical package tag | **`grok-build-witness-v1.0.0-rc6`** ([WITNESS_PACKAGE_VERSION.md](WITNESS_PACKAGE_VERSION.md)) |
| RC6 annotated tag object ID | **`c9ce879bb25db54e3d8520f297a8f5d4035ac9a8`** |
| RC6 peeled commit | **`7b76842bfa1adcedf0c00221cb574d9c3175b7e7`** |
| RC6 tree | **`77369ab099414167df658b25eac3adcb4f264eb3`** |
| RC6 archive SHA-256 | **`1f411f65735d6e2f8aeb0cb968d0e6b2108af00ef0a0264dc15daed114da0fee`** |
| RC6 transfer-bundle SHA-256 | **`ed23824246563db17d9adb7e5b5c95b633077b79b2681c04c46d8de544de6d26`** |
| Package commit authority | **annotated_tag_resolution** for tagged package identities; peeled commits are distinct from annotated tag object IDs, archive identities, sidecar identities, and transfer-bundle identities |
| **Current package status** | **FUTURE CANDIDATE 1 GOVERNANCE-SELECTED (Weaver Forge Future Candidate 1 / WF-FC-01 / weaver-forge-fc-01) — ANNOTATED TAG CREATED AND PUBLISHED (peel f178cde13391445f319b1b1138ee920a02b32874) — PACKAGE/ARCHIVE/BUNDLE NOT YET CREATED — NOT READY — INDEPENDENT WITNESS HANDOFF NOT AUTHORIZED — C-014 NOT_STARTED — NO FINDING/BLOCKER CLEAR/CLOSED — RC8/RC7/RC6 IMMUTABLE HISTORICAL ONLY — NO RELEASE, PRODUCTION READINESS, INDEPENDENT WITNESS PASS, RC9, OR C-014 COMPLETION** |
| Tag availability (RC6) | Fixed annotated tag; resolve `refs/tags/grok-build-witness-v1.0.0-rc6^{commit}` → `7b76842bfa1adcedf0c00221cb574d9c3175b7e7`; RC6 remains **NOT READY**; Independent Witness handoff **not authorized** |
| Immutable historical release: rc1 | `grok-build-witness-v1.0.0-rc1` → `89127c78c3a11492892de7e3b5f0dee18d71775a`; repeat blind audit verdict **NOT READY** |
| Immutable historical release: rc2 | `grok-build-witness-v1.0.0-rc2` → `255b357c9ee33c4a9e34b5d9b6e396c53cfe494e`; integrated four-batch static blind audit verdict **NOT READY** |
| Immutable historical release: rc3 | `grok-build-witness-v1.0.0-rc3` → `77221a224bbd6194cfafb81f6ecb58c800e5bc13`; integrated four-batch static audit verdict **NOT READY** (audit preserved under `evidence/rc3-static-blind-audit/`) |
| Immutable historical release: rc4 | `grok-build-witness-v1.0.0-rc4` → `039b46737c5968a81fb756d7a6d1d0dd57b6ad96`; integrated four-batch static blind audit verdict **NOT READY** (40 blockers; audit preserved under `evidence/rc4-static-blind-audit/`); Independent Witness reproduction **NOT PERFORMED** |
| Immutable historical release: rc5 | `grok-build-witness-v1.0.0-rc5` → peeled `5ae08cb8be9c1c97f25b9093bb5490a0ef195a07`; Source Weaver disposition **NOT READY**; Independent Witness handoff **not authorized**; Independent Witness reproduction **NOT PERFORMED** |
| Immutable release: rc6 (last tagged) | `grok-build-witness-v1.0.0-rc6` → peeled `7b76842bfa1adcedf0c00221cb574d9c3175b7e7`; disposition **NOT READY**; Independent Witness handoff **not authorized**; Independent Witness reproduction **NOT PERFORMED** |
| Active surfaces | Future Candidate 1 identity on Host/templates; annotated tag created and published; package/archive/bundle not yet created; not RC9; not READY; not release-approved; not authorized for Independent Witness handoff |
| Historical C2E-1 status (superseded for readiness) | READY WITH LIMITATIONS — see blind audit intake |
| Independent Witness (C-014) | **`NOT_STARTED`** |
| Scope | Narrow clean rebuild of `xai-grok-pager-bin` only |
| Product execution | **Forbidden** |

---

## Who this is for

This document is retained as package documentation for the Grok Build narrow clean rebuild evidence chain. It is not an active Independent Witness handoff authorization.

**Independent Witness handoff is not authorized** for RC6, RC5, RC7 (immutable historical **NOT READY** after completed Source Weaver audit; not eligible for Independent Witness handoff), RC8 (immutable static-audit candidate; no formal Source Weaver READY/NOT READY decision), or current `main`. PowerShell-native Witness execution is not canonical for the immutable RC6 package. Windows-native Rust build remains **BLOCKED**. macOS Docker is **unvalidated / noncanonical**.

## Canonical entry points

| Role | Value |
|------|------|
| Weaver Forge URL | `https://github.com/chrono-vector/weaver-forge.git` |
| Package path | `external_verifications/grok-build/witness-package/` |
| Active Future Candidate tag (CREATED AND PUBLISHED; peel `f178cde13391445f319b1b1138ee920a02b32874`) | `weaver-forge-fc-01` |
| Last immutable historical canonical package tag | `grok-build-witness-v1.0.0-rc6` |
| Grok Build URL | `https://github.com/xai-org/grok-build.git` |
| Grok Build commit | `98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce` |

Do **not** start from an unpinned `main` tip alone. For Future Candidate 1, resolve the **annotated package tag** `weaver-forge-fc-01` (CREATED AND PUBLISHED; peel `f178cde13391445f319b1b1138ee920a02b32874`). Package/archive/bundle are not yet created; Independent Witness handoff is not authorized. Historical immutable packages continue to use their historical tags (e.g. `grok-build-witness-v1.0.0-rc6`). Canonical execution requires successful annotated-tag resolution; if resolution fails, canonical execution stops. Floating `main` is not a substitute package identity and is not authorized for Independent Witness handoff.

## Fixed identities

| Item | Value |
|------|------|
| Rust image | `docker.io/library/rust@sha256:6ca5ad23231207874325a751b9df584d51cd42c066c74c6963c264e3233c3e8e` |
| Rust version | **1.92.0** |
| Package | `xai-grok-pager-bin` |
| Binary | `xai-grok-pager` |
| Build | `cargo build -p xai-grok-pager-bin --locked` |
| Env | `CARGO_INCREMENTAL=0` |
| Target | **New empty** `CARGO_TARGET_DIR` |

## Read next (canonical navigation)

1. [WITNESS_PACKAGE_VERSION.md](WITNESS_PACKAGE_VERSION.md) — Future Candidate 1 identity anchor
2. [WITNESS_REQUIREMENTS.md](WITNESS_REQUIREMENTS.md)
3. [WITNESS_PACKAGE_MANIFEST.md](WITNESS_PACKAGE_MANIFEST.md) — package contract manifest
4. [PACKAGE_FILE_MANIFEST.txt](PACKAGE_FILE_MANIFEST.txt) — source-package inventory
5. [WITNESS_RUNBOOK.md](WITNESS_RUNBOOK.md)
6. [scripts/VALIDATOR.md](scripts/VALIDATOR.md) — validator contract (pair with `validate_witness_evidence.py`)
7. [WITNESS_CLASSIFICATION.md](WITNESS_CLASSIFICATION.md)
8. [WITNESS_SUBMISSION.md](WITNESS_SUBMISSION.md)
9. [WITNESS_SECURITY_AND_REDACTION.md](WITNESS_SECURITY_AND_REDACTION.md)
10. [templates/](templates/) and [templates/REDACTIONS.md](templates/REDACTIONS.md)

## Explicit non-claims

- **NOT READY** — Future Candidate 1 is governance-selected; annotated tag is created and published; package/archive/bundle are not yet created. This is not package-readiness PASS.
- RC6 Independent Witness handoff is **not authorized**. Independent Witness reproduction **NOT PERFORMED**. Independent Witness PASS **NONE**. C-014 **`NOT_STARTED`**. No finding CLEAR/CLOSED.
- RC7 is immutable historical **NOT READY** after completed Source Weaver audit and is **not eligible** for Independent Witness handoff. That is **not** finding CLEAR/CLOSED, blocker clearance, READY, release approval, or Independent Witness authorization.
- RC8 is an immutable static-audit candidate. RC8 artifact generation and verification passed, but that is **not** a formal Source Weaver audit, **not** finding CLEAR/CLOSED, **not** blocker clearance, **not** RC8 READY, **not** release approval, and **not** Independent Witness authorization.
- Active surfaces carry Future Candidate 1 identity. Annotated tag **`weaver-forge-fc-01`** is created and published; package/archive/bundle are **not** yet created; **not** RC9; not READY; not release-approved; not authorized for Independent Witness handoff. No release, production readiness, Independent Witness PASS, or C-014 completion is claimed.
- No bit-identical reproducibility requirement vs owner hashes.
- Upstream product commands (`grok`, login, agents, etc.) are **out of scope** and must not be run during Witness rebuild.
- This package does not embed its own Weaver Forge commit hash; commit identity is resolved from the annotated tag at execution/audit time.

## Immutable releases

| Tag | Peeled commit | Release state | Audit performed | Verdict | IW reproduction | C-014 |
|-----|---------------|---------------|------------------|---------|-----------------|-------|
| `grok-build-witness-v1.0.0-rc1` | `89127c78c3a11492892de7e3b5f0dee18d71775a` | FIXED_IMMUTABLE | Repeat public-entry-point blind audit | **NOT READY** | NOT_PERFORMED | NOT_STARTED |
| `grok-build-witness-v1.0.0-rc2` | `255b357c9ee33c4a9e34b5d9b6e396c53cfe494e` | FIXED_IMMUTABLE | Integrated four-batch static blind audit | **NOT READY** | NOT_PERFORMED | NOT_STARTED |
| `grok-build-witness-v1.0.0-rc3` | `77221a224bbd6194cfafb81f6ecb58c800e5bc13` | FIXED_IMMUTABLE | Integrated four-batch static audit (preserved under `evidence/rc3-static-blind-audit/`) | **NOT READY** | NOT_PERFORMED | NOT_STARTED |
| `grok-build-witness-v1.0.0-rc4` | `039b46737c5968a81fb756d7a6d1d0dd57b6ad96` | FIXED_IMMUTABLE | Integrated four-batch static blind audit (preserved under `evidence/rc4-static-blind-audit/`; 40 blockers) | **NOT READY** | NOT_PERFORMED | NOT_STARTED |
| `grok-build-witness-v1.0.0-rc5` | `5ae08cb8be9c1c97f25b9093bb5490a0ef195a07` | FIXED_IMMUTABLE | Source Weaver static audit of tagged RC5 | **NOT READY** | NOT_PERFORMED | NOT_STARTED |
| `grok-build-witness-v1.0.0-rc6` | `7b76842bfa1adcedf0c00221cb574d9c3175b7e7` | FIXED_IMMUTABLE | Immutable candidate published | **NOT READY** | NOT_PERFORMED | NOT_STARTED |
| `grok-build-witness-v1.0.0-rc7` | `4316b976b086cb7116cabe0c8deaa47159001c09` | FIXED_IMMUTABLE | Source Weaver static audit of tagged RC7 | **NOT READY** | NOT_PERFORMED | NOT_STARTED |
| `grok-build-witness-v1.0.0-rc8` | `1de4b4d9523711418390f8331c95988523ef4481` | FIXED_IMMUTABLE static-audit candidate | Artifact generation/verification passed; accepted non-authoritative advisory technical evaluation; formal Source Weaver audit not performed | **No formal Source Weaver READY/NOT READY decision for RC8** | NOT_PERFORMED | NOT_STARTED |

All listed tags are immutable and must not be moved, deleted, or force-updated. Later `main`-branch status records are outside the immutable tagged snapshots; see [STATUS.md](../../../STATUS.md) and [REPRODUCE.md](../../../REPRODUCE.md). RC7 is immutable historical **NOT READY** after completed Source Weaver audit and is not eligible for Independent Witness handoff. RC8 is an immutable static-audit candidate; RC8 artifact generation and verification passed, but formal Source Weaver audit was not performed for RC8 and no formal Source Weaver READY/NOT READY decision exists for RC8.

### HISTORICAL PRE-TAG / PRE-RC6 STATE

Earlier revisions of this document described rc3/rc4/rc5/rc6 prospectively (“tag pending,” “tag does not yet exist,” “Phase 1 documentation only,” “technical remediation not yet begun,” “prospective RC6”) and later described RC8 as pre-tag/prospective. Those states are superseded: rc1–rc6 are immutable **NOT READY** history; RC6 Independent Witness handoff is not authorized; RC7 is immutable historical **NOT READY** after completed Source Weaver audit and is not eligible for Independent Witness handoff; RC8 is an immutable static-audit candidate with passed artifact generation/verification, no formal Source Weaver audit, no formal Source Weaver READY/NOT READY decision, and no Independent Witness authorization.

## Owner artifact hashes (historical only)

Not acceptance criteria for Witness PASS. See prior README table in git history / owner evidence.
