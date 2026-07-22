# Independent Witness Package — Grok Build (narrow clean rebuild)

| Field | Value |
|-------|-------|
| Package version | **1.0.0-rc3** |
| Canonical package tag | **`grok-build-witness-v1.0.0-rc3`** ([WITNESS_PACKAGE_VERSION.md](WITNESS_PACKAGE_VERSION.md)) |
| Package commit authority | **annotated_tag_resolution** |
| **Current package status** | **NOT READY** — pending fixed-tag repeat blind audit and readiness gates |
| Tag availability | Verified by resolving `refs/tags/grok-build-witness-v1.0.0-rc3^{commit}`; canonical execution requires successful resolution |
| Immutable historical release: rc1 | `grok-build-witness-v1.0.0-rc1` → `89127c78c3a11492892de7e3b5f0dee18d71775a`; repeat blind audit verdict **NOT READY** |
| Immutable historical release: rc2 | `grok-build-witness-v1.0.0-rc2` → `255b357c9ee33c4a9e34b5d9b6e396c53cfe494e`; integrated four-batch static blind audit verdict **NOT READY** |
| Historical C2E-1 status (superseded for readiness) | READY WITH LIMITATIONS — see blind audit intake |
| Independent Witness (C-014) | **`NOT_STARTED`** |
| Scope | Narrow clean rebuild of `xai-grok-pager-bin` only |
| Product execution | **Forbidden** |

---

## Who this is for

An independent person (not the package owner) who rebuilds `xai-grok-pager` from public pins on **their own** Linux or WSL2 host using **linux/amd64** Docker.

**PowerShell-native Witness execution is not canonical for 1.0.0-rc3.** Windows-native Rust build remains **BLOCKED**. macOS Docker is **unvalidated / noncanonical**.

## Canonical entry points

| Role | Value |
|------|--------|
| Weaver Forge URL | `https://github.com/chrono-vector/weaver-forge.git` |
| Package path | `external_verifications/grok-build/witness-package/` |
| Canonical package tag | `grok-build-witness-v1.0.0-rc3` |
| Grok Build URL | `https://github.com/xai-org/grok-build.git` |
| Grok Build commit | `98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce` |

Do **not** start from an unpinned `main` tip alone. Resolve the **annotated package tag** `grok-build-witness-v1.0.0-rc3` (or a maintainer-directed noncanonical override with explicit deviation disclosure).

## Fixed identities

| Item | Value |
|------|--------|
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

- **NOT READY** until fixed-tag repeat blind audit and required readiness gates succeed.
- C-014 Independent Witness **not started**.
- No bit-identical reproducibility requirement vs owner hashes.
- Upstream product commands (`grok`, login, agents, etc.) are **out of scope** and must not be run during Witness rebuild.
- This package does not embed its own Weaver Forge commit hash; commit identity is resolved from the annotated tag at execution/audit time.

## Historical immutable releases

| Tag | Commit | Audit performed | Verdict |
|-----|--------|------------------|---------|
| `grok-build-witness-v1.0.0-rc1` | `89127c78c3a11492892de7e3b5f0dee18d71775a` | Repeat public-entry-point blind audit | **NOT READY** |
| `grok-build-witness-v1.0.0-rc2` | `255b357c9ee33c4a9e34b5d9b6e396c53cfe494e` | Integrated four-batch static blind audit | **NOT READY** |

Both tags are immutable and must not be moved, deleted, or force-updated. Later `main`-branch status/audit records are outside the rc3 tagged snapshot; see [WITNESS_PACKAGE_VERSION.md](WITNESS_PACKAGE_VERSION.md).

## Owner artifact hashes (historical only)

Not acceptance criteria for Witness PASS. See prior README table in git history / owner evidence.
