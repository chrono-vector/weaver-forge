# Independent Witness Package — Grok Build (narrow clean rebuild)

| Field | Value |
|-------|-------|
| Last immutable package version | **1.0.0-rc5** |
| Last immutable canonical package tag | **`grok-build-witness-v1.0.0-rc5`** ([WITNESS_PACKAGE_VERSION.md](WITNESS_PACKAGE_VERSION.md)) |
| Annotated tag object ID | **`9c01e314249f59945e93597af6ece2e3fb33e6cd`** |
| Peeled commit | **`5ae08cb8be9c1c97f25b9093bb5490a0ef195a07`** |
| Tree | **`97ad93d80480b23a49f1636ff55dae449202aa3c`** |
| Archive SHA-256 | **`5bf6e8f66795ba310ad5b149b721ca1930b5729ab3c568a20559d8dda40e0435`** |
| Transfer-bundle SHA-256 | **`5581b10788f0a3ee7a36982ac1b2468c658afc353fe88da3423298b60344bb2b`** |
| Package commit authority | **annotated_tag_resolution** (peeled commit is the fixed RC5 release identity; distinct from annotated tag object ID, archive identity, and transfer-bundle identity) |
| **Current package status** | **RC5 FIXED IMMUTABLE — NOT READY — INDEPENDENT WITNESS HANDOFF NOT AUTHORIZED — C-014 NOT_STARTED — RC6-R1–R7 REMEDIATION IMPLEMENTED ON MAIN (PRE-TAG / PROSPECTIVE RC6 FIXED CANDIDATE ONLY) — RC6 TAG/ARCHIVE/BUNDLE DO NOT YET EXIST — NOT READY — NO INDEPENDENT WITNESS REPRODUCTION — NO INDEPENDENT WITNESS PASS** |
| Tag availability (RC5) | Fixed annotated tag; resolve `refs/tags/grok-build-witness-v1.0.0-rc5^{commit}` → `5ae08cb8be9c1c97f25b9093bb5490a0ef195a07`; canonical execution against RC5 requires successful resolution; if resolution fails, canonical execution stops |
| Immutable historical release: rc1 | `grok-build-witness-v1.0.0-rc1` → `89127c78c3a11492892de7e3b5f0dee18d71775a`; repeat blind audit verdict **NOT READY** |
| Immutable historical release: rc2 | `grok-build-witness-v1.0.0-rc2` → `255b357c9ee33c4a9e34b5d9b6e396c53cfe494e`; integrated four-batch static blind audit verdict **NOT READY** |
| Immutable historical release: rc3 | `grok-build-witness-v1.0.0-rc3` → `77221a224bbd6194cfafb81f6ecb58c800e5bc13`; integrated four-batch static audit verdict **NOT READY** (audit preserved under `evidence/rc3-static-blind-audit/`) |
| Immutable historical release: rc4 | `grok-build-witness-v1.0.0-rc4` → `039b46737c5968a81fb756d7a6d1d0dd57b6ad96`; integrated four-batch static blind audit verdict **NOT READY** (40 blockers; audit preserved under `evidence/rc4-static-blind-audit/`); Independent Witness reproduction **NOT PERFORMED** |
| Immutable release: rc5 (last tagged) | `grok-build-witness-v1.0.0-rc5` → peeled `5ae08cb8be9c1c97f25b9093bb5490a0ef195a07`; Source Weaver disposition **NOT READY**; Independent Witness handoff **not authorized**; Independent Witness reproduction **NOT PERFORMED** |
| Current `main` | Pre-tag RC6-R1–R7 remediation / prospective RC6 fixed candidate only; **not** tagged; **not** archived; **not** bundled; **not** READY; Independent Witness handoff **not authorized** |
| Historical C2E-1 status (superseded for readiness) | READY WITH LIMITATIONS — see blind audit intake |
| Independent Witness (C-014) | **`NOT_STARTED`** |
| Scope | Narrow clean rebuild of `xai-grok-pager-bin` only |
| Product execution | **Forbidden** |

---

## Who this is for

An independent person (not the package owner) who rebuilds `xai-grok-pager` from public pins on **their own** Linux or WSL2 host using **linux/amd64** Docker.

**Independent Witness handoff is not authorized** for RC5 or for current pre-tag `main`. PowerShell-native Witness execution is not canonical for the immutable RC5 package. Windows-native Rust build remains **BLOCKED**. macOS Docker is **unvalidated / noncanonical**.

## Canonical entry points

| Role | Value |
|------|------|
| Weaver Forge URL | `https://github.com/chrono-vector/weaver-forge.git` |
| Package path | `external_verifications/grok-build/witness-package/` |
| Last immutable canonical package tag | `grok-build-witness-v1.0.0-rc5` |
| Grok Build URL | `https://github.com/xai-org/grok-build.git` |
| Grok Build commit | `98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce` |

Do **not** start from an unpinned `main` tip alone. For the last immutable tagged package, resolve the **annotated package tag** `grok-build-witness-v1.0.0-rc5` (or a maintainer-directed noncanonical override with explicit deviation disclosure). Canonical execution requires that resolution to succeed; if resolution fails, canonical execution stops. Current `main` is not a substitute package identity and is not authorized for Independent Witness handoff.

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

- **NOT READY** — RC5 Source Weaver disposition remains **NOT READY**. This is not package-readiness PASS.
- RC5 Independent Witness handoff is **not authorized**. Independent Witness reproduction **NOT PERFORMED**. Independent Witness PASS **NONE**. C-014 **`NOT_STARTED`**.
- RC6-R1–R7 remediation is implemented on `main` (R1–R6 reviewed through Pi staged-diff conformance and committed/pushed; R7 is documentation/status alignment). Implementation completion is **not** finding CLEAR/CLOSED, blocker clearance, RC6 READY, release approval, or Independent Witness authorization.
- Current `main` is a pre-tag / prospective RC6 fixed-candidate remediation state only. RC6 tag, archive, and transfer bundle **do not yet exist**.
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

All five tags are immutable and must not be moved, deleted, or force-updated. Later `main`-branch status/audit/remediation records are outside the RC5 tagged snapshot; see [WITNESS_PACKAGE_VERSION.md](WITNESS_PACKAGE_VERSION.md). **RC6 tag does not yet exist.**

### HISTORICAL PRE-TAG / PRE-RC5 STATE

Earlier revisions of this document described rc3/rc4/rc5 prospectively (“tag pending,” “tag does not yet exist,” “Phase 1 documentation only,” “technical remediation not yet begun”). Those states are superseded: rc1–rc5 are immutable **NOT READY** history; RC5 Independent Witness handoff is not authorized; current `main` is pre-tag RC6-R1–R7 remediation only.

## Owner artifact hashes (historical only)

Not acceptance criteria for Witness PASS. See prior README table in git history / owner evidence.
