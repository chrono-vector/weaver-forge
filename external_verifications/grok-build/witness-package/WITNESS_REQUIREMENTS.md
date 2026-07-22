# Witness requirements — Grok Build narrow rebuild (1.0.0-rc4)

## Current package status

**RC3 INTEGRATED STATIC BLIND-AUDIT RECORDED — RC4 PACKAGE CONTENT UNDER PREPARATION — NOT READY PENDING RC4 COMMIT, TAG AND RE-AUDIT**

Package version `1.0.0-rc4`; `canonical_package_tag=grok-build-witness-v1.0.0-rc4`;
`package_commit_authority=annotated_tag_resolution` (no embedded future rc4 commit). Tag
availability is verified by annotated-tag resolution; canonical execution requires successful
resolution; if resolution fails, canonical execution stops. After publication, the tag is
immutable. `grok-build-witness-v1.0.0-rc1` (`89127c78c3a11492892de7e3b5f0dee18d71775a`),
`grok-build-witness-v1.0.0-rc2` (`255b357c9ee33c4a9e34b5d9b6e396c53cfe494e`), and
`grok-build-witness-v1.0.0-rc3` (`77221a224bbd6194cfafb81f6ecb58c800e5bc13`; audit preserved under
`evidence/rc3-static-blind-audit/`) are preserved as **immutable historical releases**, each with
its own recorded **NOT READY** audit verdict. C-014 (Independent Witness) remains
**`NOT_STARTED`**. Overall **PARTIAL**. Package remains **NOT READY** until rc4 is committed,
tagged, and repeat-audited.

## Evidence schema

All structured evidence files declare `evidence_schema_version=1` (see
[scripts/VALIDATOR.md](scripts/VALIDATOR.md)). The four raw capture files
(`BUILD_STDOUT.txt`, `BUILD_STDERR.txt`, `CONTAINER_STDOUT.txt`, `CONTAINER_STDERR.txt`) are
exempt and may be empty. Every other required file must declare the schema version and satisfy
its own file-specific required-field set — a shared generic body cannot satisfy more than one
file's schema.

## Outcome model (outcome-sensitive evidence)

Every run resolves to exactly one of five outcomes, recorded identically in `BUILD_EXIT_CODE.txt`,
`DOCKER_EXIT_CODE.txt`, and `BUILD_TIMING.txt` (a mismatch across those three files is itself a
structural defect):

| Outcome | Meaning | Witness classification effect |
|---------|---------|-------------------------------|
| `BUILD_NOT_STARTED` | Docker/bootstrap ran but cargo was never invoked | Typically **INDETERMINATE** (see [WITNESS_CLASSIFICATION.md](WITNESS_CLASSIFICATION.md)) |
| `CARGO_FAILED` | Cargo started and exited non-zero | **FAIL** |
| `CARGO_SUCCEEDED_ARTIFACT_MISSING` | Cargo exited `0` but the expected artifact is absent | **FAIL** |
| `CARGO_SUCCEEDED_ARTIFACT_PRESENT` | Cargo exited `0` and the artifact is present and inspected | Eligible for **PASS**/**PARTIAL** per classification |
| `INFRASTRUCTURE_FAILURE` | An environment/infrastructure fault (e.g. image pull failure) prevented the build | Typically **INDETERMINATE** |

Evidence requirements are **outcome-sensitive**: `ARTIFACT_IDENTITY.txt` and
`STATIC_ARTIFACT_INSPECTION.txt` require `applicable=no`/`artifact_present=no` plus a non-empty
`reason=` for every outcome except `CARGO_SUCCEEDED_ARTIFACT_PRESENT`; `BUILD_TIMING.txt` requires
`cargo_started_utc`/`cargo_finished_utc` only once cargo has actually started. Every mandatory
evidence file is initialized to a `status=NOT_REACHED` placeholder **before** any fallible
host/container operation begins, so a run that fails early still produces a complete, honest
evidence set rather than missing files.

## Failure submissions are supported and expected

A truthful Witness submission recording `BUILD_NOT_STARTED`, `CARGO_FAILED`,
`CARGO_SUCCEEDED_ARTIFACT_MISSING`, or `INFRASTRUCTURE_FAILURE` is a **valid, complete, and
welcome** submission. Structural validator PASS does not require a successful build — it requires
that the recorded outcome be internally consistent and that every mandatory file for that outcome
be present and correctly filled in. Discouraging, hiding, or silently upgrading a truthful negative
outcome is itself a `PROHIBITED`-severity violation (see [WITNESS_CLASSIFICATION.md](WITNESS_CLASSIFICATION.md)).

## Canonical platform

| Environment | Witness 1.0.0-rc4 |
|-------------|---------------------|
| Linux x86_64 + Docker | **Canonical** |
| WSL2 bash + Docker Desktop Linux containers | **Canonical** |
| PowerShell-native orchestration | **Not canonical** |
| Windows-native Rust/cargo | **BLOCKED** |
| macOS Docker | **Unvalidated / noncanonical** |

Container platform: **`linux/amd64`**.

## Independence

| Requirement | Rule |
|-------------|------|
| Person | Not the owner / package author |
| Host | Witness-owned machine, VM, or cloud |
| Weaver package revision | Resolve **annotated tag** `grok-build-witness-v1.0.0-rc4` (publication verified by tag resolution; canonical execution stops if resolution fails) |
| Grok source | Fresh clone at `98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce` |
| Target | New empty `CARGO_TARGET_DIR` |
| Owner caches | **Forbidden** as inputs |
| Product / auth | **Forbidden** |

## Fixed identities (canonical constants)

These are immutable constants in `scripts/run_witness_narrow_build.sh` and are never assigned
from the environment. Any effective value that differs from its canonical counterpart requires
the explicit `--noncanonical-deviation` flag; without it the host orchestrator refuses to run.

| Item | Required value |
|------|----------------|
| `WEAVER_FORGE_URL` | `https://github.com/chrono-vector/weaver-forge.git` |
| `WEAVER_FORGE_TAG` | `grok-build-witness-v1.0.0-rc4` |
| Weaver Forge package commit | **Derived at runtime** from `refs/tags/grok-build-witness-v1.0.0-rc4^{commit}`; detached `HEAD` must equal that resolved commit; package clone must be clean. The tagged package does **not** embed its own future commit hash (`package_commit_authority=annotated_tag_resolution`). |
| `GROK_BUILD_URL` | `https://github.com/xai-org/grok-build.git` |
| `GROK_BUILD_COMMIT` | `98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce` |
| `RUST_IMAGE` | `docker.io/library/rust@sha256:6ca5ad23231207874325a751b9df584d51cd42c066c74c6963c264e3233c3e8e` |
| `EXPECTED_CARGO_LOCK_SHA256` | `1512bb4fef0c1166c6a15a3398da9593903be1759b759ce78d9958913e61b421` |
| `BUILD_CMD` | `cargo build -p xai-grok-pager-bin --locked` |
| `EXPECTED_RUSTC_VERSION` | `1.92.0` |
| `EXPECTED_DOTSLASH_VERSION` | `0.5.7` |
| Package | `xai-grok-pager-bin` |
| Env | `CARGO_INCREMENTAL=0` |

Optional additional verification input only: `WEAVER_FORGE_EXTERNAL_EXPECTED_COMMIT`. Not required for canonical execution. When supplied, mismatch with the resolved tag commit / detached `HEAD` is fatal. Must not be stored as a placeholder inside the fixed tagged package.

## `WITNESS_ID` and `WORK_ROOT` safety

- `WITNESS_ID` must match `^[a-z0-9][a-z0-9._-]{0,63}$`, must not contain path separators
  (`/`, `\`), `..`, whitespace, control characters, or start with a dash. Violations are a
  fatal argument error (exit `2`) before any evidence directory is created.
- `WORK_ROOT` must be an absolute path, must not resolve to `/`, the home directory, a
  `/home/<user>` or `/root` path, a WSL drive-root mount (`/mnt/<letter>`), any system prefix
  (`/bin`, `/etc`, `/usr`, `/var`, etc.), the Weaver Forge package repository itself, or an
  ancestor/descendant of that repository. Resolution follows symlinks in every existing path
  component before these checks run, so a symlinked path cannot bypass the guard.
- A **non-empty** `WORK_ROOT` is refused by default. Proceeding requires
  `--allow-nonempty-work-root` plus either typed confirmation of the exact resolved path or
  `--force-work-root-reset` for non-interactive sessions. The exact managed deletion targets are
  disclosed before any deletion occurs.

## RUSTUP_HOME policy

- **Do not** set `RUSTUP_HOME` to an empty Witness work directory.
- Preserve the digest-pinned Rust image's built-in toolchain.
- Record the **effective** `RUSTUP_HOME` without overriding it in scripts.

## Bootstrap components

| Component | Specification |
|-----------|-----------------|
| apt packages | `ca-certificates`, `git`, `build-essential`, `pkg-config`, `cmake`, `curl`, `perl`, `file`, `binutils` — versions **not pinned** (disclosed limitation) |
| DotSlash | **0.5.7** via `cargo install dotslash --version 0.5.7 --locked` into isolated `CARGO_HOME` |
| protoc | LF-normalized **writable** copy of `/src/bin/protoc`; `PROTOC` set to that path; descriptor executes via `#!/usr/bin/env dotslash` |

## Docker image pull is fatal on failure

`docker pull --platform linux/amd64 <RUST_IMAGE>` failure of any kind is **fatal**: the host
orchestrator records `IMAGE_IDENTITY.txt` with `status=FAILED`, sets outcome
`INFRASTRUCTURE_FAILURE`, and aborts. There is **no** fallback to a cached or locally-present
image under any circumstance — a Witness run must always attempt the pull and must never silently
substitute an already-local image for the pinned digest.

## Network (disclosed)

Required for: image pull, apt, DotSlash install, protoc payload fetch, Cargo registry/git
dependencies.

Completely offline-from-empty-cache reproduction: **NOT ESTABLISHED**.

## Product execution

**Forbidden** — including `--version`, `--help`, `-h`, TUI, login, agents, OAuth, models, update
on `xai-grok-pager` / `grok`.

## Static tools

`file`, `readelf`, `objdump` allowed on the built artifact, only when outcome is
`CARGO_SUCCEEDED_ARTIFACT_PRESENT`. **Never execute** the artifact. **`ldd` forbidden.**

## Change log

| Version | Change |
|---------|--------|
| 1.0.0-rc2 | Prior canonical-platform, independence, fixed-identity, bootstrap, and network sections |
| 1.0.0-rc3 | Added evidence-schema-version section; outcome model and outcome-sensitivity table; explicit failure-submissions-supported policy; `WITNESS_ID`/`WORK_ROOT` safety rules matching the host orchestrator; image-pull-is-fatal policy; canonical-constants table reconciled with `scripts/run_witness_narrow_build.sh` |
| 1.0.0-rc4 | Status/identity advanced to `1.0.0-rc4` / `grok-build-witness-v1.0.0-rc4`; rc3 recorded as immutable NOT READY history; time-stable annotated-tag resolution wording; no Independent Witness reproduction |
