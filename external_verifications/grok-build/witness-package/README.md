# Independent Witness Package — Grok Build (narrow clean rebuild)

| Field | Value |
|-------|-------|
| Package version | **1.0.0-rc4** |
| Canonical package tag | **`grok-build-witness-v1.0.0-rc4`** ([WITNESS_PACKAGE_VERSION.md](WITNESS_PACKAGE_VERSION.md)) |
| Fixed tagged commit | **`039b46737c5968a81fb756d7a6d1d0dd57b6ad96`** |
| Package commit authority | **annotated_tag_resolution** (resolved commit is the fixed rc4 release identity) |
| **Current package status** | **RC4 FIXED IMMUTABLE — STATIC BLIND AUDIT COMPLETE — FINAL DISPOSITION NOT READY (40 BLOCKERS) — PHASE 1 DOCUMENTATION REMEDIATION ON MAIN — TECHNICAL IMPLEMENTATION REMEDIATION NOT YET BEGUN — RC5 TAG DOES NOT EXIST — C-014 NOT_STARTED** |
| Tag availability | Fixed annotated tag; resolve `refs/tags/grok-build-witness-v1.0.0-rc4^{commit}` → `039b46737c5968a81fb756d7a6d1d0dd57b6ad96`; canonical execution requires successful resolution; if resolution fails, canonical execution stops |
| Immutable historical release: rc1 | `grok-build-witness-v1.0.0-rc1` → `89127c78c3a11492892de7e3b5f0dee18d71775a`; repeat blind audit verdict **NOT READY** |
| Immutable historical release: rc2 | `grok-build-witness-v1.0.0-rc2` → `255b357c9ee33c4a9e34b5d9b6e396c53cfe494e`; integrated four-batch static blind audit verdict **NOT READY** |
| Immutable historical release: rc3 | `grok-build-witness-v1.0.0-rc3` → `77221a224bbd6194cfafb81f6ecb58c800e5bc13`; integrated four-batch static audit verdict **NOT READY** (audit preserved under `evidence/rc3-static-blind-audit/`) |
| Immutable release: rc4 (current fixed) | `grok-build-witness-v1.0.0-rc4` → `039b46737c5968a81fb756d7a6d1d0dd57b6ad96`; integrated four-batch static blind audit verdict **NOT READY** (40 blockers; audit preserved under `evidence/rc4-static-blind-audit/`); Independent Witness reproduction **NOT PERFORMED** |
| Historical C2E-1 status (superseded for readiness) | READY WITH LIMITATIONS — see blind audit intake |
| Independent Witness (C-014) | **`NOT_STARTED`** |
| Scope | Narrow clean rebuild of `xai-grok-pager-bin` only |
| Product execution | **Forbidden** |

---

## Who this is for

An independent person (not the package owner) who rebuilds `xai-grok-pager` from public pins on **their own** Linux or WSL2 host using **linux/amd64** Docker.

**PowerShell-native Witness execution is not canonical for 1.0.0-rc4.** Windows-native Rust build remains **BLOCKED**. macOS Docker is **unvalidated / noncanonical**.

## Canonical entry points

| Role | Value |
|------|------|
| Weaver Forge URL | `https://github.com/chrono-vector/weaver-forge.git` |
| Package path | `external_verifications/grok-build/witness-package/` |
| Canonical package tag | `grok-build-witness-v1.0.0-rc4` |
| Grok Build URL | `https://github.com/xai-org/grok-build.git` |
| Grok Build commit | `98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce` |

Do **not** start from an unpinned `main` tip alone. Resolve the **annotated package tag** `grok-build-witness-v1.0.0-rc4` (or a maintainer-directed noncanonical override with explicit deviation disclosure). Canonical execution requires that resolution to succeed; if resolution fails, canonical execution stops.

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

- **NOT READY** — rc4 static disposition remains **NOT READY** (40 integrated blockers). This is not package-readiness PASS.
- Phase 0 audit intake is complete. Phase 1 documentation and release/status remediation is being performed on `main`. Technical implementation remediation of scripts, schemas, validators, tests, and execution controls has not begun. `main` is being prepared toward a possible future rc5 candidate; **no rc5 tag exists**.
- C-014 Independent Witness **not started**; Independent Witness reproduction **NOT PERFORMED**; Independent Witness PASS **NONE**.
- No bit-identical reproducibility requirement vs owner hashes.
- Upstream product commands (`grok`, login, agents, etc.) are **out of scope** and must not be run during Witness rebuild.
- This package does not embed its own Weaver Forge commit hash; commit identity is resolved from the annotated tag at execution/audit time.

## Immutable releases

| Tag | Commit | Release state | Audit performed | Verdict | IW reproduction | C-014 |
|-----|--------|---------------|------------------|---------|-----------------|-------|
| `grok-build-witness-v1.0.0-rc1` | `89127c78c3a11492892de7e3b5f0dee18d71775a` | FIXED_IMMUTABLE | Repeat public-entry-point blind audit | **NOT READY** | NOT_PERFORMED | NOT_STARTED |
| `grok-build-witness-v1.0.0-rc2` | `255b357c9ee33c4a9e34b5d9b6e396c53cfe494e` | FIXED_IMMUTABLE | Integrated four-batch static blind audit | **NOT READY** | NOT_PERFORMED | NOT_STARTED |
| `grok-build-witness-v1.0.0-rc3` | `77221a224bbd6194cfafb81f6ecb58c800e5bc13` | FIXED_IMMUTABLE | Integrated four-batch static audit (preserved under `evidence/rc3-static-blind-audit/`) | **NOT READY** | NOT_PERFORMED | NOT_STARTED |
| `grok-build-witness-v1.0.0-rc4` | `039b46737c5968a81fb756d7a6d1d0dd57b6ad96` | FIXED_IMMUTABLE | Integrated four-batch static blind audit (preserved under `evidence/rc4-static-blind-audit/`; 40 blockers) | **NOT READY** | NOT_PERFORMED | NOT_STARTED |

All four tags are immutable and must not be moved, deleted, or force-updated. Later `main`-branch status/audit/remediation records are outside the rc4 tagged snapshot; see [WITNESS_PACKAGE_VERSION.md](WITNESS_PACKAGE_VERSION.md). **rc5 tag does not exist.**

### HISTORICAL PRE-TAG STATE

Earlier revisions of this document described rc3 as package content prepared with a canonical tag name assigned, pending its repeat blind audit, and used language such as "rc3 tag pending" or "before/until rc3 tag exists." That state is superseded: the rc3 tag was published, audited (verdict **NOT READY**, see table above), and is now immutable history. Separately, pre-publication wording described rc4 as “package content under preparation” / “pending commit, tag, and re-audit.” That prospective wording is superseded: rc4 is the fixed immutable release in the table above (static disposition **NOT READY**). Phase 0 audit intake is complete. Phase 1 documentation and release/status remediation is being performed on `main`. Technical implementation remediation of scripts, schemas, validators, tests, and execution controls has not begun. `main` is being prepared toward a possible future rc5 candidate; **no rc5 tag exists**.

## Owner artifact hashes (historical only)

Not acceptance criteria for Witness PASS. See prior README table in git history / owner evidence.
