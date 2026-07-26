# Independent Witness Package — Grok Build (narrow clean rebuild)

| Field | Value |
|-------|-------|
| Last immutable package version | **1.0.0-rc6** |
| Last immutable canonical package tag | **`grok-build-witness-v1.0.0-rc6`** ([WITNESS_PACKAGE_VERSION.md](WITNESS_PACKAGE_VERSION.md)) |
| Annotated tag object ID | **`c9ce879bb25db54e3d8520f297a8f5d4035ac9a8`** |
| Peeled commit | **`7b76842bfa1adcedf0c00221cb574d9c3175b7e7`** |
| Tree | **`77369ab099414167df658b25eac3adcb4f264eb3`** |
| Archive SHA-256 | **`1f411f65735d6e2f8aeb0cb968d0e6b2108af00ef0a0264dc15daed114da0fee`** |
| Transfer-bundle SHA-256 | **`ed23824246563db17d9adb7e5b5c95b633077b79b2681c04c46d8de544de6d26`** |
| Package commit authority | **annotated_tag_resolution** (peeled commit is the fixed RC6 release identity; distinct from annotated tag object ID, archive identity, and transfer-bundle identity) |
| **Current package status** | **RC6 IMMUTABLE HISTORICAL — NOT READY — RC7 IMMUTABLE HISTORICAL — NOT READY AFTER COMPLETED SOURCE WEAVER AUDIT — RC7 NOT ELIGIBLE FOR INDEPENDENT WITNESS HANDOFF — INDEPENDENT WITNESS HANDOFF NOT AUTHORIZED — C-014 NOT_STARTED — NO FINDING/BLOCKER CLEAR/CLOSED — RC8 PROSPECTIVE/PRE-TAG NEXT CANDIDATE (`1.0.0-rc8` / `grok-build-witness-v1.0.0-rc8`) FIXED IN ACTIVE HOST/TEMPLATES AND VALIDATOR MAPPING — RC8 TAG/ARCHIVE/SIDECAR/TRANSFER BUNDLE DO NOT YET EXIST — NOT READY — NO INDEPENDENT WITNESS REPRODUCTION — NO INDEPENDENT WITNESS PASS — NO RELEASE, PRODUCTION READINESS, INDEPENDENT WITNESS PASS, OR C-014 COMPLETION** |
| Tag availability (RC6) | Fixed annotated tag; resolve `refs/tags/grok-build-witness-v1.0.0-rc6^{commit}` → `7b76842bfa1adcedf0c00221cb574d9c3175b7e7`; RC6 remains **NOT READY**; Independent Witness handoff **not authorized** |
| Immutable historical release: rc1 | `grok-build-witness-v1.0.0-rc1` → `89127c78c3a11492892de7e3b5f0dee18d71775a`; repeat blind audit verdict **NOT READY** |
| Immutable historical release: rc2 | `grok-build-witness-v1.0.0-rc2` → `255b357c9ee33c4a9e34b5d9b6e396c53cfe494e`; integrated four-batch static blind audit verdict **NOT READY** |
| Immutable historical release: rc3 | `grok-build-witness-v1.0.0-rc3` → `77221a224bbd6194cfafb81f6ecb58c800e5bc13`; integrated four-batch static audit verdict **NOT READY** (audit preserved under `evidence/rc3-static-blind-audit/`) |
| Immutable historical release: rc4 | `grok-build-witness-v1.0.0-rc4` → `039b46737c5968a81fb756d7a6d1d0dd57b6ad96`; integrated four-batch static blind audit verdict **NOT READY** (40 blockers; audit preserved under `evidence/rc4-static-blind-audit/`); Independent Witness reproduction **NOT PERFORMED** |
| Immutable historical release: rc5 | `grok-build-witness-v1.0.0-rc5` → peeled `5ae08cb8be9c1c97f25b9093bb5490a0ef195a07`; Source Weaver disposition **NOT READY**; Independent Witness handoff **not authorized**; Independent Witness reproduction **NOT PERFORMED** |
| Immutable release: rc6 (last tagged) | `grok-build-witness-v1.0.0-rc6` → peeled `7b76842bfa1adcedf0c00221cb574d9c3175b7e7`; disposition **NOT READY**; Independent Witness handoff **not authorized**; Independent Witness reproduction **NOT PERFORMED** |
| Current `main` | Pre-tag / prospective RC8 next-candidate only (`1.0.0-rc8` / `grok-build-witness-v1.0.0-rc8`); **not** tagged; **not** archived; **not** bundled; **not** READY; Independent Witness handoff **not authorized**; RC8 tag/archive/sidecar/transfer bundle do not yet exist |
| Historical C2E-1 status (superseded for readiness) | READY WITH LIMITATIONS — see blind audit intake |
| Independent Witness (C-014) | **`NOT_STARTED`** |
| Scope | Narrow clean rebuild of `xai-grok-pager-bin` only |
| Product execution | **Forbidden** |

---

## Who this is for

An independent person (not the package owner) who rebuilds `xai-grok-pager` from public pins on **their own** Linux or WSL2 host using **linux/amd64** Docker.

**Independent Witness handoff is not authorized** for RC6, RC5, RC7 (immutable historical **NOT READY** after completed Source Weaver audit; not eligible for Independent Witness handoff), or for current pre-tag `main` (prospective RC8). PowerShell-native Witness execution is not canonical for the immutable RC6 package. Windows-native Rust build remains **BLOCKED**. macOS Docker is **unvalidated / noncanonical**.

## Canonical entry points

| Role | Value |
|------|------|
| Weaver Forge URL | `https://github.com/chrono-vector/weaver-forge.git` |
| Package path | `external_verifications/grok-build/witness-package/` |
| Last immutable canonical package tag | `grok-build-witness-v1.0.0-rc6` |
| Grok Build URL | `https://github.com/xai-org/grok-build.git` |
| Grok Build commit | `98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce` |

Do **not** start from an unpinned `main` tip alone. For the last immutable tagged package, resolve the **annotated package tag** `grok-build-witness-v1.0.0-rc6` (or a maintainer-directed noncanonical override with explicit deviation disclosure). Canonical execution requires that resolution to succeed; if resolution fails, canonical execution stops. Current `main` is not a substitute package identity and is not authorized for Independent Witness handoff. RC6 remains **NOT READY**.

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

## Read next

1. [WITNESS_PACKAGE_VERSION.md](WITNESS_PACKAGE_VERSION.md)
2. [WITNESS_REQUIREMENTS.md](WITNESS_REQUIREMENTS.md)
3. [WITNESS_RUNBOOK.md](WITNESS_RUNBOOK.md)
4. [WITNESS_CLASSIFICATION.md](WITNESS_CLASSIFICATION.md)
5. [WITNESS_SUBMISSION.md](WITNESS_SUBMISSION.md)
6. [WITNESS_SECURITY_AND_REDACTION.md](WITNESS_SECURITY_AND_REDACTION.md)
7. [WITNESS_PACKAGE_MANIFEST.md](WITNESS_PACKAGE_MANIFEST.md)
8. [scripts/VALIDATOR.md](scripts/VALIDATOR.md)
9. [templates/](templates/) and [templates/REDACTIONS.md](templates/REDACTIONS.md)

## Explicit non-claims

- **NOT READY** — RC6 disposition remains **NOT READY**. This is not package-readiness PASS.
- RC6 Independent Witness handoff is **not authorized**. Independent Witness reproduction **NOT PERFORMED**. Independent Witness PASS **NONE**. C-014 **`NOT_STARTED`**. No finding CLEAR/CLOSED.
- RC7 is immutable historical **NOT READY** after completed Source Weaver audit and is **not eligible** for Independent Witness handoff. That is **not** finding CLEAR/CLOSED, blocker clearance, READY, release approval, or Independent Witness authorization.
- RC8 next-candidate identity is fixed in active Host/templates and validator mapping on `main`. That is **not** finding CLEAR/CLOSED, blocker clearance, RC6/RC7/RC8 READY, release approval, or Independent Witness authorization.
- Current `main` is a pre-tag / prospective RC8 next-candidate remediation state only. RC8 tag, archive, sidecar, and transfer bundle **do not yet exist**. Independent Witness handoff is **not authorized**. No release, production readiness, Independent Witness PASS, or C-014 completion is claimed.
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

All six tags are immutable and must not be moved, deleted, or force-updated. Later `main`-branch status/audit/remediation records are outside the RC6 tagged snapshot; see [WITNESS_PACKAGE_VERSION.md](WITNESS_PACKAGE_VERSION.md). RC7 is immutable historical **NOT READY** after completed Source Weaver audit and is not eligible for Independent Witness handoff. **RC8 tag/archive/sidecar/transfer bundle do not yet exist.**

### HISTORICAL PRE-TAG / PRE-RC6 STATE

Earlier revisions of this document described rc3/rc4/rc5/rc6 prospectively (“tag pending,” “tag does not yet exist,” “Phase 1 documentation only,” “technical remediation not yet begun,” “prospective RC6”). Those states are superseded: rc1–rc6 are immutable **NOT READY** history; RC6 Independent Witness handoff is not authorized; RC7 is immutable historical **NOT READY** after completed Source Weaver audit and is not eligible for Independent Witness handoff; current `main` is pre-tag / prospective RC8 next-candidate only.

## Owner artifact hashes (historical only)

Not acceptance criteria for Witness PASS. See prior README table in git history / owner evidence.
