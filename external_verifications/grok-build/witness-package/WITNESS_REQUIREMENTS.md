# Witness requirements — Grok Build narrow rebuild (Future Candidate 1 / WF-FC-01)

## Current package status

**FUTURE CANDIDATE 1 GOVERNANCE-SELECTED (Weaver Forge Future Candidate 1 / WF-FC-01 / `weaver-forge-fc-01`) — ANNOTATED TAG CREATED AND PUBLISHED (peel `f178cde13391445f319b1b1138ee920a02b32874`) — PACKAGE/ARCHIVE/BUNDLE NOT YET CREATED — NOT READY — INDEPENDENT WITNESS HANDOFF NOT AUTHORIZED — C-014 NOT_STARTED — NO FINDING CLEAR/CLOSED — RC8/RC7/RC6 HISTORICAL ONLY — NO RELEASE READINESS, PRODUCTION READINESS, RC9, OR INDEPENDENT WITNESS PASS CLAIMED**

Active Future Candidate requirements use package version `WF-FC-01` and expected tag `weaver-forge-fc-01` (Repository Owner G-3 identity authority; successor to RC8 only; RC9 NOT IMPLIED). Annotated tag **`weaver-forge-fc-01`** is CREATED AND PUBLISHED (peel `f178cde13391445f319b1b1138ee920a02b32874`); package/archive/bundle are not yet created and must not be fabricated as existing. Historical RC8 remains an immutable static-audit candidate: `1.0.0-rc8` /
Normative mapping: **WF-FC-01 -> weaver-forge-fc-01**. Candidate name: **Weaver Forge Future Candidate 1**.
`grok-build-witness-v1.0.0-rc8`; annotated tag object
`8113d952d3b127d32e138dbf804141f5d1dfb26f`; peeled commit
`1de4b4d9523711418390f8331c95988523ef4481`; tree
`87b40d8a32ca536a4cdba0eee474f6171c62f6bb`; `package_commit_authority=annotated_tag_resolution`.
RC8 artifact generation and verification passed, but that result is not a formal Source Weaver
audit, not a formal Source Weaver READY decision, not a formal Source Weaver NOT READY decision,
not Independent Witness PASS, and not release or production readiness. RC6 remains immutable
historical **NOT READY**. RC7 remains immutable historical **NOT READY** after completed Source
Weaver audit and is not eligible for Independent Witness handoff. Independent Witness handoff is
**not authorized**. Independent Witness reproduction **NOT PERFORMED**. Independent Witness PASS
**NONE**. C-014 remains **`NOT_STARTED`**. Overall **PARTIAL**. Package is not ready for
Independent Witness handoff. No finding or blocker is CLEAR/CLOSED.

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

## Authoritative outcome ownership (Phase 3B contract)

Normative machine contract: [AUTHORITATIVE_OUTCOME_CONTRACT.json](AUTHORITATIVE_OUTCOME_CONTRACT.json)
(see also [PHASE_3B_OUTCOME_OWNERSHIP_CONTRACT.md](../evidence/rc5-remediation/PHASE_3B_OUTCOME_OWNERSHIP_CONTRACT.md)).

That contract defines terminal outcome vocabulary, producer ownership, the complete authoritative
result tuple, no-inference / no-overwrite rules, and success eligibility for **future** rc5
remediation (Phases 3C–3F). **Phase 3C on `main` implements container terminal finalization**
(`finalize_container_terminal_outcome`): every supported container terminal path must finalize
container-owned evidence with no final provisional values in applicable container-owned fields.
**Phase 3D on `main` implements host outcome ingestion**: the host parses the complete container
result tuple, records host-owned `HOST_OUTCOME_INGESTION.txt`, preserves valid container-owned
`BUILD_EXIT_CODE.txt` byte-for-byte after post-Docker host integrity failures, and fails closed on
missing/invalid/contradictory container results without fabricating a replacement outcome.
Host infrastructure and source-integrity failures are recorded in separate host-owned fields.
`preliminary_success_eligible` remains `NO` in Phase 3D. **Phase 3E on `main` makes
`POST_BUILD_INTEGRITY.txt` host-owned, complete, truthful, and schema-aligned**:
`status=OK` if and only if `post_build_integrity_ok=yes`; all finalized failure paths use
`status=FAILED` (never `NOT_APPLICABLE` as a final status); `HOST_OUTCOME_INGESTION.txt`
`post_build_integrity_status` is synchronized with the final POST_BUILD record; the container
remains a POST_BUILD non-writer. **Phase 3F-A on `main` removes validator outcome inference**
and requires an explicit authoritative `outcome=`; accepts and structurally validates
`HOST_OUTCOME_INGESTION.txt` as closed auxiliary; and enforces the automatable RC4B-017
host-preliminary structural subset without requiring `evidence_inventory_complete=yes`.
Host-preliminary structural PASS is distinct from final Witness validation and is not
Independent Witness PASS or final success eligibility. `preliminary_success_eligible`
remains `NO`. The validator still writes no evidence. **Phase 3F-B on `main` makes host
exit 0 depend on the complete adjudicated automated gate and explicit validator structural
PASS:** after automated host evidence and the preliminary manifest are finalized, the host
invokes the repository validator with `--host-preliminary`, captures stdout/stderr outside
`EVIDENCE_DIR`, writes a fresh host-owned `VALIDATOR_RESULT.txt` outside `EVIDENCE_DIR`
(not in the manifest), and requires validator process exit 0 **plus** exactly one definitive
`STRUCTURAL VALIDATION: PASS` line (validator process exit 0 alone is insufficient). Host
exit 0 means only automated host package structural validation succeeded; it is not final
success eligibility, not final Witness validation, and not Independent Witness PASS.
`preliminary_success_eligible` remains `NO` even when host exit is 0. Evidence inventory
completion and the final Witness lifecycle remain later work. **Phase 3G on `main` adds
generator-backed automated preliminary integration coverage:** declarative scenarios exercise
committed sourced container/host writers, real local `--host-preliminary` validator as the
primary success-integration proof (mocks only for parser/fault-unit rejection), stale/spoof/
mixed-run rejection, and limited full-main fail-closed smoke with Docker/Cargo/product
prohibited via PATH-first shims. Host exit 0 remains preliminary automated structural success
only; `preliminary_success_eligible` remains `NO`; final manual Witness submission and
Independent Witness work remain later. **Phase 4-S1/S2/S3 on `main` activate canonical schema
authority, S2 writer/template alignment, and S3 preliminary/final manifest totality with the
non-circular completeness state machine:** `--host-preliminary` rejects
`evidence_inventory_complete=yes`; `--final-submission` requires S2-shaped packages to finalize
completeness before the final manifest; no final auxiliary exemption for S2-shaped packages;
validator captures/`VALIDATOR_RESULT` remain outside `EVIDENCE_DIR`; structural PASS ceilings
exclude Independent Witness PASS, READY, and rc5 readiness. Synthetic final fixtures are test
artifacts only. **RC6-R2 on `main` adds Host incomplete-package finalization policy:** when a
run is signal-aborted or otherwise cannot produce complete truthful terminal evidence, the Host
writes a Host-owned runtime control record at
`${WORK_ROOT}/tmp/host-incomplete/${RUN_ID}/PACKAGE_INCOMPLETE.txt` (outside `EVIDENCE_DIR`).
The marker is not Witness evidence, is not schema-register bound, and must never be written or
modified by the container, Witness, or validator. Incomplete evidence must not be resumed or
manually reconstructed into a final package; rerun requires a new `EVIDENCE_DIR`. The marker is
retained as Host-owned historical negative operational evidence. Validator inputs are unchanged
(implicit final-submission prohibition). **Active requirements target Future Candidate 1 (WF-FC-01). RC6 and RC7 are immutable historical NOT READY candidates; RC8 is an immutable historical static-audit candidate with no formal Source Weaver READY/NOT READY decision.** Independent Witness reproduction has not occurred; Independent Witness
PASS is not claimed; C-014 remains `NOT_STARTED`; Independent Witness handoff is not authorized.

## Failure submissions are supported and expected

A truthful Witness submission recording `BUILD_NOT_STARTED`, `CARGO_FAILED`,
`CARGO_SUCCEEDED_ARTIFACT_MISSING`, or `INFRASTRUCTURE_FAILURE` is a **valid, complete, and
welcome** submission. Structural validator PASS does not require a successful build — it requires
that the recorded outcome be internally consistent and that every mandatory file for that outcome
be present and correctly filled in. Discouraging, hiding, or silently upgrading a truthful negative
outcome is itself a `PROHIBITED`-severity violation (see [WITNESS_CLASSIFICATION.md](WITNESS_CLASSIFICATION.md)).

## Canonical platform

| Environment | Witness route |
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
| Weaver package revision | Resolve the effective **annotated tag** for active Future Candidate (`weaver-forge-fc-01` for `WF-FC-01`) when that tag exists and is separately authorized; raw object type must be `tag`; canonical execution stops if resolution or type check fails. Historical package evidence remains bound to its declared historical tag. This document does not authorize Independent Witness handoff, READY, RC9, or C-014. |
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
| `WEAVER_FORGE_TAG` | `weaver-forge-fc-01` |
| `PACKAGE_VERSION` | `WF-FC-01` |
| Weaver Forge package commit | **Derived at runtime** from `refs/tags/weaver-forge-fc-01^{commit}` only after the annotated tag exists and `git cat-file -t refs/tags/weaver-forge-fc-01` equals `tag`; detached `HEAD` must equal that resolved commit; package clone must be clean. Until the tag exists, commit/tag-object fields remain not yet determinable (do not fabricate). The package does **not** embed its own future commit hash (`package_commit_authority=annotated_tag_resolution`). Historical evidence remains bound to its declared historical tag. |
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

## Host preflight identity closure (Phase 2A on `main`)

Implementation note (historical Phase 2A). **Active identity is WF-FC-01 / weaver-forge-fc-01. RC6/RC7/RC8 remain historical only; Independent Witness handoff is not authorized; RC9 NOT IMPLIED.** The
rc4 tag is unchanged. This does **not** claim that rc4 was corrected.

Before **any** Docker CLI invocation (including `docker version` / `docker context show`
metadata), the host orchestrator must close an explicit identity gate after all of:

1. exact package tag ref exists
2. raw tag object type is exactly `tag` (`git cat-file -t refs/tags/<tag>` — annotated only;
   lightweight tags whose peeled type is `commit` are rejected)
3. tag resolves to one commit
4. package checkout detached; package `HEAD` equals resolved tag commit; package tree clean
5. Grok Build checkout detached; `HEAD` equals pinned commit; tree clean
6. direct pre-Docker `Cargo.lock` hash equals the canonical expected hash

Ordinary non-Docker host facts may be recorded earlier. Docker metadata failures after the gate
may remain informational `UNKNOWN`. Final `EVIDENCE_DIR` must be created atomically (plain
`mkdir` of a never-before-existing run directory under an optional `mkdir -p` parent). A
preexisting selected directory is never merged, reused, reset, or overwritten; collision either
retries with a new run ID or aborts before writing evidence.

## Source-mount isolation (Phase 2B on `main`)

Implementation note (historical Phase 2B). **Active identity is WF-FC-01 / weaver-forge-fc-01. RC6/RC7/RC8 remain historical only; Independent Witness handoff is not authorized; RC9 NOT IMPLIED.** This does **not** claim final closure before repeat static audit.

- The Grok Build checkout is mounted **exactly once**, read-only, at `/src`.
- A broad `WORK_ROOT` → `/work` writable mount is **prohibited**.
- Writable mount **sources** must not equal, contain, or be contained by either the Grok Build
  checkout or the Weaver Forge package checkout (`WF_DIR`).
- Writable mount **targets** must not equal `/src`, lie inside `/src`, or be an ancestor of `/src`.
- Writable cargo-target, bootstrap-target, HOME/`CARGO_HOME`, TMPDIR, bootstrap, DotSlash cache,
  and evidence mounts are **explicit and narrowly scoped**.
- Mount-plan validation runs **before** `docker run` (fail closed; no Docker run on failure).
- Docker `--mount` encoding is comma-delimited (`type=bind,src=...,dst=...,readonly`). Source,
  destination, and mode field values must not contain comma, CR, or LF. Ordinary spaces remain
  supported via Bash array argument preservation (one argv element per `--mount` value). This
  package does not escape comma-bearing values; such fields are rejected before argv construction.
- Required mount sources must **already exist** before validation. The validator does not create
  missing bind sources. Absence is distinct from canonicalization failure.
- Source canonicalization failure is **fatal**. Unresolved textual paths are never used as a
  fallback. All such failures occur before Docker is invoked.
- Pre- and post-container source `HEAD` and clean-tree checks are required; post-Docker `HEAD`
  drift or a dirty tree is an infrastructure/integrity failure and is not PASS-capable.

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
| main (Phase 2A; not an rc5 release) | Host preflight: no Docker CLI before identity closure; raw annotated-tag type `tag` mandatory; atomic fresh `EVIDENCE_DIR`. **Does not** correct or re-tag rc4; **not an RC5/RC6 release**; does **not** close blockers; contemporaneous note: RC5 tag did not yet exist at that phase |
| main (Phase 2B; not an rc5 release) | Source-mount isolation: no broad `WORK_ROOT`→`/work`; `/src` read-only once; fail-closed mount-plan validation before Docker; comma/CR/LF mount-field rejection; required sources must pre-exist; canonicalization failure fatal with no textual fallback. **not an RC5/RC6 release**; does **not** close blockers; contemporaneous note: RC5 tag did not yet exist at that phase |
| main (RC6-R7 docs; not an RC6 release) | Historical identity/status wording alignment; **does not** close blockers; C-014 NOT_STARTED. Later lifecycle documents supersede prospective RC6/RC7/RC8 wording. |
| main (RC8 lifecycle-boundary docs; not RC9) | RC6/RC7 immutable historical **NOT READY**; RC8 immutable static-audit candidate; RC8 artifact generation and verification passed within lifecycle boundary only; no formal Source Weaver READY/NOT READY decision for RC8; Independent Witness not authorized/performed; C-014 NOT_STARTED; no finding/blocker CLEAR/CLOSED; no release or production readiness claim |
