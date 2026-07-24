# Witness runbook — Grok Build narrow clean rebuild (1.0.0-rc4)

**Package status:** **RC4 FIXED IMMUTABLE — STATIC BLIND AUDIT COMPLETE — FINAL DISPOSITION NOT READY (40 BLOCKERS) — PHASE 1 DOCUMENTATION REMEDIATION ON MAIN — TECHNICAL IMPLEMENTATION REMEDIATION NOT YET BEGUN — RC5 TAG DOES NOT EXIST — C-014 NOT_STARTED**

Canonical package tag: `grok-build-witness-v1.0.0-rc4` → fixed commit `039b46737c5968a81fb756d7a6d1d0dd57b6ad96`
(`canonical_package_tag=grok-build-witness-v1.0.0-rc4`). Availability verified by annotated-tag
resolution; canonical execution requires successful resolution; if resolution fails, canonical
execution stops. The tag is immutable. `package_commit_authority=annotated_tag_resolution`
(resolved commit is the fixed rc4 release identity).
`grok-build-witness-v1.0.0-rc4` static blind audit is **COMPLETE** with final disposition
**NOT READY** (40 integrated blockers; C-027; `evidence/rc4-static-blind-audit/`).
`grok-build-witness-v1.0.0-rc3` remains fixed at `77221a224bbd6194cfafb81f6ecb58c800e5bc13`
(integrated four-batch static audit verdict **NOT READY**; audit preserved under
`evidence/rc3-static-blind-audit/`).
`grok-build-witness-v1.0.0-rc2` remains fixed at `255b357c9ee33c4a9e34b5d9b6e396c53cfe494e`
(integrated four-batch static blind audit verdict **NOT READY**).
`grok-build-witness-v1.0.0-rc1` remains fixed at `89127c78c3a11492892de7e3b5f0dee18d71775a`
(repeat audit verdict **NOT READY**). rc1–rc4 are **immutable releases** and must not be moved,
deleted, or force-updated. Phase 0 audit intake is complete. Phase 1 documentation and
release/status remediation is being performed on `main`. Technical implementation remediation of
scripts, schemas, validators, tests, and execution controls has not begun. `main` is being
prepared toward a possible future rc5 candidate; **no rc5 tag exists**. Independent Witness
reproduction **NOT PERFORMED**. Independent Witness PASS **NONE**. C-014 **NOT_STARTED**. Overall
**PARTIAL**.

**Upstream warning:** Normal Grok Build product commands (`xai-grok-pager`, `grok`, `--version`,
`--help`, TUI, login, agents, OAuth, models, update) are **outside Witness scope** and **must
not** be run.

---

## Canonical platform

| Route | Status |
|-------|--------|
| Linux x86_64 host + Docker | **Canonical** |
| WSL2 Linux shell + Docker Desktop (Linux containers) | **Canonical** |
| PowerShell-only host orchestration | **Noncanonical** for 1.0.0-rc4 |
| Windows-native `cargo` | **BLOCKED** |
| macOS Docker | **Unvalidated / noncanonical** |

All builds run **inside** `linux/amd64` Docker (`--platform linux/amd64`).

---

## Canonical constants (immutable; never assigned from the environment)

These live in `scripts/run_witness_narrow_build.sh` as `readonly` shell variables. Any
`EFFECTIVE_*` value used for a run defaults to its canonical counterpart; an environment-variable
override only takes effect when `--noncanonical-deviation` is also passed, and any accepted
deviation sets `canonical_run=NO` for the whole run.

| Constant | Value |
|----------|-------|
| `CANONICAL_WEAVER_FORGE_URL` | `https://github.com/chrono-vector/weaver-forge.git` |
| `CANONICAL_WEAVER_FORGE_TAG` | `grok-build-witness-v1.0.0-rc4` |
| `CANONICAL_GROK_BUILD_URL` | `https://github.com/xai-org/grok-build.git` |
| `CANONICAL_GROK_BUILD_COMMIT` | `98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce` |
| `CANONICAL_RUST_IMAGE` | `docker.io/library/rust@sha256:6ca5ad23231207874325a751b9df584d51cd42c066c74c6963c264e3233c3e8e` |
| `CANONICAL_EXPECTED_CARGO_LOCK_SHA256` | `1512bb4fef0c1166c6a15a3398da9593903be1759b759ce78d9958913e61b421` |
| `CANONICAL_BUILD_CMD` | `cargo build -p xai-grok-pager-bin --locked` |
| `CANONICAL_EXPECTED_RUSTC_VERSION` | `1.92.0` |
| `CANONICAL_EXPECTED_DOTSLASH_VERSION` | `0.5.7` |

**Package commit authority:** the annotated tag (`annotated_tag_resolution`). Canonical mode
resolves `refs/tags/grok-build-witness-v1.0.0-rc4^{commit}`, checks out that commit detached,
requires `HEAD` to equal the resolved commit, and requires a clean package clone.
The tagged package does **not** embed its own future commit hash. If resolution fails, canonical
execution stops. After publication, the tag is immutable.

**Optional additional verification only:** `WEAVER_FORGE_EXTERNAL_EXPECTED_COMMIT` (env).
When set to a full 40-char commit, it must equal the resolved tag commit and detached
`HEAD`; mismatch is fatal. It is **not** required for canonical execution and must **not**
be stored as a placeholder inside the fixed tagged package. Its absence does not weaken
tag→HEAD consistency checks.

## `--noncanonical-deviation`

Any of the nine canonical fields above may be overridden via an identically-named environment variable
(`WEAVER_FORGE_URL`, `WEAVER_FORGE_TAG`, `GROK_BUILD_URL`,
`GROK_BUILD_COMMIT`, `RUST_IMAGE`, `EXPECTED_CARGO_LOCK_SHA256`, `BUILD_CMD`,
`EXPECTED_RUSTC_VERSION`, `EXPECTED_DOTSLASH_VERSION`), but the override is only **accepted**
when `--noncanonical-deviation` is also passed on the command line. Without the flag, any
detected deviation is a **fatal error (exit `2`)** — the script refuses to silently run with an
environment-variable override.

When accepted:

- `canonical_run=NO` is recorded in `HOST_RUN_METADATA.txt` and `WEAVER_FORGE_PACKAGE_IDENTITY.txt`.
- Every changed field is listed in `DEVIATIONS.txt` under `--- changed identity fields ---`.
- The proposed Witness verdict is capped at **PARTIAL** by default, escalated to **FAIL** for any
  of `WEAVER_FORGE_TAG`, `GROK_BUILD_URL`, `GROK_BUILD_COMMIT`, `RUST_IMAGE`, `EXPECTED_CARGO_LOCK_SHA256`, or
  `BUILD_CMD` — see [WITNESS_CLASSIFICATION.md](WITNESS_CLASSIFICATION.md).
- `--noncanonical-deviation` does **not** bypass tag→resolved-commit→detached-`HEAD` integrity
  for the **effective** package tag. Effective tag and resolved commit are still recorded;
  PASS remains prohibited.

## `WITNESS_ID` regex

```text
^[a-z0-9][a-z0-9._-]{0,63}$
```

Also rejected regardless of regex match: path separators (`/`, `\`), the substring `..`,
whitespace, control characters, or a leading dash. Violations exit `2` before any work directory
or evidence file is touched.

## `WORK_ROOT` safety

`WORK_ROOT` is validated **before any deletion occurs**:

- Must be an absolute path.
- Resolved (symlinks in every existing path component followed) value must not equal `/`, the
  resolved `$HOME`, `/home/<user>`, `/root`, a WSL drive-root mount (`/mnt/<letter>`), or any
  system prefix (`/bin`, `/boot`, `/dev`, `/etc`, `/lib*`, `/proc`, `/run`, `/sbin`, `/sys`,
  `/usr*`, `/var`).
- Must not equal, contain, or be contained by the Weaver Forge package repository root.
- A **non-empty** top-level `WORK_ROOT` is refused unless `--allow-nonempty-work-root` is passed;
  even then, the exact managed deletion targets (`weaver-forge/`, `grok-build-src/`,
  `cargo-home/`, `cargo-target/`, `bootstrap-cargo-target/`, `dotslash-cache/`, `home/`,
  `bootstrap/`) are disclosed and either typed confirmation of the resolved path or
  `--force-work-root-reset` is required before anything is deleted.

---

## One copyable host block (Linux / WSL2 bash)

Assign variables and invoke the host orchestrator. Replace `YOUR_WITNESS_ID` and choose an
**empty** work root **outside** any Weaver Forge clone.

```bash
export WEAVER_FORGE_URL="https://github.com/chrono-vector/weaver-forge.git"
export WEAVER_FORGE_TAG="grok-build-witness-v1.0.0-rc4"
export GROK_BUILD_URL="https://github.com/xai-org/grok-build.git"
export GROK_BUILD_COMMIT="98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce"
export RUST_IMAGE="docker.io/library/rust@sha256:6ca5ad23231207874325a751b9df584d51cd42c066c74c6963c264e3233c3e8e"
export WORK_ROOT="/var/tmp/grok-witness-work"

# Canonical execution: clone Weaver Forge only to obtain scripts, or run from an existing
# checkout of the tagged commit resolved via annotated-tag resolution.
WF_CHECKOUT="/var/tmp/weaver-forge-tag-checkout"
git clone "${WEAVER_FORGE_URL}" "${WF_CHECKOUT}"
git -C "${WF_CHECKOUT}" fetch --tags origin
git -C "${WF_CHECKOUT}" checkout "refs/tags/${WEAVER_FORGE_TAG}"

bash "${WF_CHECKOUT}/external_verifications/grok-build/witness-package/scripts/run_witness_narrow_build.sh" \
  --work-root "${WORK_ROOT}" \
  YOUR_WITNESS_ID
```

**Exact invocation (once variables are set):**

```bash
bash external_verifications/grok-build/witness-package/scripts/run_witness_narrow_build.sh \
  --work-root "${WORK_ROOT}" \
  YOUR_WITNESS_ID
```

If the requested `WEAVER_FORGE_TAG` cannot be resolved on `origin`, or its raw object type is not
exactly `tag`, the host script fails clearly with `exit 3` and records
`WEAVER_FORGE_PACKAGE_IDENTITY.txt` accordingly (missing tag:
`reason=requested_tag_not_present_on_origin`; non-annotated:
`reason=package_tag_raw_object_type_not_annotated_tag`). Canonical execution requires successful
annotated-tag resolution; if resolution fails, canonical execution stops.

### Run ID and evidence directory

Format: `<witness-id>-<UTC-YYYYMMDD>-<strong-random-suffix>`

Evidence directory (host helper default):

```text
${WORK_ROOT}/evidence/<run-id>/
```

**Atomic freshness (Phase 2A on `main`):** the evidence parent may be created with `mkdir -p`,
but the final `EVIDENCE_DIR` is created with plain `mkdir` so the selected run directory did not
previously exist. Collisions are retried with a new run ID or abort before any evidence write.
Existing evidence directories are never merged, reset, reused, or partially overwritten. The
allocated basename is the actual `run_id` recorded by the host. (Full run-ID propagation into
every evidence file remains open for later phases.)

Copy completed templates + logs into the submission path per [WITNESS_SUBMISSION.md](WITNESS_SUBMISSION.md).

### Identity closure before any Docker CLI (Phase 2A on `main`)

Implementation on `main` toward a possible future rc5 candidate. **RC4 remains NOT READY.** This
does **not** claim rc4 was corrected.

No Docker CLI invocation — including `docker version` and `docker context show` — occurs until
package tag existence, **raw annotated-tag object type `tag`**, tag→commit resolution, package
detached/`HEAD`/clean checks, Grok Build detached/`HEAD`/clean checks, and pre-Docker
`Cargo.lock` hash equality have all succeeded and `IDENTITY_GATE_CLOSED=yes` is set. Non-Docker
host OS/shell facts may be recorded earlier.

If the requested `WEAVER_FORGE_TAG` is missing, is not raw object type `tag` (for example a
lightweight tag), or fails later identity checks, the run aborts as pre-Docker infrastructure
failure **without** invoking Docker.

## Directory layout (host helper)

| Variable | Typical path under `WORK_ROOT` |
|----------|--------------------------------|
| `WF_DIR` | `weaver-forge/` (fresh clone; resolves tag) |
| `SRC_DIR` | `grok-build-src/` (fresh clone at pin) |
| `CARGO_HOME_DIR` | `cargo-home/` |
| `CARGO_TARGET_DIR` | `cargo-target/` (Grok Build only; must be empty before build) |
| `BOOTSTRAP_CARGO_TARGET_DIR` | `bootstrap-cargo-target/` (DotSlash `cargo install` only) |
| `DOTSLASH_CACHE_DIR` | `dotslash-cache/` |
| `HOME_DIR` | `home/` |
| `BOOTSTRAP_DIR` | `bootstrap/` (LF protoc descriptor copy) |
| `EVIDENCE_DIR` | `evidence/<run-id>/` |

---

## Evidence initialization (before any fallible operation)

Before any host or container operation that can fail, every file in
`MANDATORY_EVIDENCE_FILES` is initialized to:

```text
evidence_schema_version=1
status=NOT_REACHED
applicable=no
reason=stage_not_reached
product_executed=NO
ldd_used=NO
```

This guarantees that an early failure still leaves a complete, honest, non-empty evidence set —
no mandatory file is ever silently absent because a later stage never ran.

---

## Docker contract (single container run)

The host script runs **one** disposable container. Mounts are a structured Bash argv of
`--mount` bind entries (argument boundaries preserved; no `eval`). Mount-plan validation runs
**before** `docker run`.

| Flag / mount | Value |
|--------------|--------|
| `--rm` | yes |
| `--platform` | `linux/amd64` |
| `--network` | `bridge` |
| Source (exactly once, read-only) | `--mount type=bind,src=${SRC_DIR},dst=/src,readonly` |
| Package runner (read-only file) | `--mount type=bind,src=.../container_narrow_build.sh,dst=/witness/container_narrow_build.sh,readonly` |
| Cargo target (rw) | `--mount type=bind,src=${CARGO_TARGET_DIR},dst=/work/cargo-target` |
| Bootstrap cargo target (rw) | `--mount type=bind,src=${BOOTSTRAP_CARGO_TARGET_DIR},dst=/work/bootstrap-cargo-target` |
| Cargo home (rw) | `--mount type=bind,src=${CARGO_HOME_DIR},dst=/work/cargo-home` |
| HOME (rw) | `--mount type=bind,src=${HOME_DIR},dst=/work/home` |
| DotSlash cache (rw) | `--mount type=bind,src=${DOTSLASH_CACHE_DIR},dst=/work/dotslash-cache` |
| Bootstrap dir (rw) | `--mount type=bind,src=${BOOTSTRAP_DIR},dst=/work/bootstrap` |
| TMPDIR (rw) | `--mount type=bind,src=${TMP_DIR},dst=/work/tmp` |
| Evidence (rw) | `--mount type=bind,src=${EVIDENCE_DIR},dst=/evidence` |
| Broad `WORK_ROOT` → `/work` | **prohibited** |
| `-w` | `/src` |
| `HOME` | `/work/home` |
| `CARGO_HOME` | `/work/cargo-home` |
| `CARGO_TARGET_DIR` | `/work/cargo-target` (Grok Build Cargo only) |
| `BOOTSTRAP_CARGO_TARGET_DIR` | `/work/bootstrap-cargo-target` (DotSlash install only) |
| `CARGO_INCREMENTAL` | `0` |
| `DOTSLASH_CACHE` | `/work/dotslash-cache` |
| `TMPDIR` | `/work/tmp` |
| `PATH` | `/work/cargo-home/bin:` + image cargo paths |
| `RUSTUP_HOME` | **Do not** set to empty work dir — preserve image toolchain; record effective value |

Writable mount **sources** must not equal, contain, or be contained by either checkout.
Writable mount **targets** must not overlap `/src`. Pre/post source `HEAD` and clean-tree
checks are required after Docker returns.

Docker `--mount` values are comma-delimited. Source, destination, and mode fields must not
contain comma, CR, or LF; ordinary spaces remain supported through Bash array argument
preservation. Comma-bearing values are rejected before Docker argv construction (no escaping).
Required mount sources must already exist before validation; the validator does not create
missing bind sources. Canonicalization failure is fatal; unresolved textual paths are never
used as fallback. All mount-plan failures occur before Docker is invoked.

**Docker image pull is fatal.** `docker pull --platform linux/amd64 <image>` failure of any kind
aborts the run with `IMAGE_IDENTITY.txt` recording `status=FAILED`, outcome
`INFRASTRUCTURE_FAILURE`, and **no** fallback to a cached/local image. Image identity (digest,
platform) is also re-verified via `docker inspect` immediately before `docker run`; a mismatch
aborts before the container starts.

Phase 2B implementation is on `main` toward a possible future rc5 candidate. **RC4 remains NOT
READY.** **No rc5 tag exists.** Final closure requires repeat static audit.

---

## Outcome model

Every run resolves to exactly one outcome, recorded consistently in `BUILD_EXIT_CODE.txt`,
`DOCKER_EXIT_CODE.txt`, and `BUILD_TIMING.txt`:

| Outcome | Meaning |
|---------|---------|
| `BUILD_NOT_STARTED` | Docker/bootstrap ran but cargo was never invoked |
| `CARGO_FAILED` | Cargo started and exited non-zero |
| `CARGO_SUCCEEDED_ARTIFACT_MISSING` | Cargo exited `0` but the expected artifact was not found |
| `CARGO_SUCCEEDED_ARTIFACT_PRESENT` | Cargo exited `0` and the artifact was found and inspected |
| `INFRASTRUCTURE_FAILURE` | An environment/infrastructure fault (not a cargo/bootstrap failure) prevented the build |

See [WITNESS_REQUIREMENTS.md](WITNESS_REQUIREMENTS.md#outcome-model-outcome-sensitive-evidence)
for the outcome-sensitivity table and [WITNESS_CLASSIFICATION.md](WITNESS_CLASSIFICATION.md) for
how each outcome maps to a proposed verdict. **Truthful failure submissions are supported and
expected** — a `BUILD_NOT_STARTED`, `CARGO_FAILED`, or `INFRASTRUCTURE_FAILURE` outcome, correctly
and completely documented, is a valid Witness submission.

### Authoritative outcome ownership (Phase 3B contract)

Normative contract: [AUTHORITATIVE_OUTCOME_CONTRACT.json](AUTHORITATIVE_OUTCOME_CONTRACT.json).
It locks vocabulary, ownership, result tuple, and no-inference/no-overwrite rules for future rc5
work. **Phase 3C on `main` implements container terminal finalization** per that contract: every
supported container terminal path finalizes container-owned evidence; no final provisional values
are allowed in applicable container-owned fields. **Phase 3D on `main` implements host outcome
ingestion**: the host preserves valid container outcomes, records separate host infrastructure and
source-integrity state in `HOST_OUTCOME_INGESTION.txt`, and fails closed on missing/invalid
container results without fabrication. The host ingestion record is preliminary and does not imply
PASS. **Phase 3E on `main` makes `POST_BUILD_INTEGRITY.txt` host-owned, complete, truthful, and
schema-aligned**: `status=OK` iff `post_build_integrity_ok=yes`; finalized failure paths use
`status=FAILED`; `HOST_OUTCOME_INGESTION` `post_build_integrity_status` is synchronized; the
container remains a POST_BUILD non-writer. **Phase 3F-A on `main` removes validator outcome
inference**, requires explicit authoritative `outcome=`, accepts and structurally validates
`HOST_OUTCOME_INGESTION.txt`, and enforces the automatable RC4B-017 host-preliminary subset
without requiring `evidence_inventory_complete=yes`. Host-preliminary structural PASS is not
final Witness validation, not Independent Witness PASS, and not final success eligibility.
`preliminary_success_eligible` remains `NO`. The validator still writes no evidence.
**Phase 3F-B on `main` makes host exit 0 depend on the complete adjudicated automated gate
and explicit validator structural PASS:** after preliminary manifest finalization the host
invokes `--host-preliminary`, captures stdout/stderr outside `EVIDENCE_DIR`, writes
host-owned `VALIDATOR_RESULT.txt` outside `EVIDENCE_DIR` (never in the manifest), and
requires validator process exit 0 plus exactly one definitive `STRUCTURAL VALIDATION: PASS`
line (exit 0 alone is insufficient). Host exit 0 is not final success eligibility and not
Independent Witness PASS; `preliminary_success_eligible` remains `NO`. Evidence inventory
completion and final Witness lifecycle remain later work.
**Phase 3G on `main` adds generator-backed automated preliminary integration coverage:**
declarative scenarios exercise committed sourced writers, real local `--host-preliminary`
validator as primary success-integration proof (mocks only for parser/fault-unit categories),
stale/spoof/mixed-run rejection, and limited full-main fail-closed smoke; Docker/Cargo/product
are mocked/prohibited in tests. Host exit 0 remains preliminary automated structural success
only; `preliminary_success_eligible` remains `NO`; final manual Witness submission and
Independent Witness work remain later.
**RC4 remains NOT READY. No rc5 tag exists.** Independent Witness reproduction has not
occurred; Independent Witness PASS is not claimed; C-014 remains `NOT_STARTED`. Do not claim
end-to-end Independent Witness compliance from Phase 3G alone.

---

## Evidence filenames (required)

| File | Role |
|------|------|
| `WEAVER_FORGE_PACKAGE_IDENTITY.txt` | Tag + resolved Weaver commit; `canonical_run` |
| `SOURCE_ACQUISITION.txt` | Clone/fetch/checkout commands and UTC times (both repos) |
| `SOURCE_IDENTITY.txt` | Grok pin + `Cargo.lock` hash (expected vs. observed) |
| `IMAGE_IDENTITY.txt` | Digest-pinned pull + `docker inspect` |
| `ENVIRONMENT.txt` | Host + container environment |
| `BOOTSTRAP.txt` | apt, DotSlash 0.5.7, protoc descriptor hashes, `PROTOC` path |
| `CLEAN_TARGET_PROOF.txt` | Host + container empty-target proof |
| `BUILD_COMMAND.txt` | Exact cargo command; `CARGO_INCREMENTAL=0` |
| `BUILD_ENVIRONMENT.txt` | `HOME`, `CARGO_*`, `DOTSLASH_CACHE`, `PROTOC`, mounts, network |
| `CONTAINER_STDOUT.txt` / `CONTAINER_STDERR.txt` | Full Docker capture (raw; schema-exempt) |
| `DOCKER_EXIT_CODE.txt` | Docker exit code; outcome; failure stage |
| `BUILD_STDOUT.txt` / `BUILD_STDERR.txt` | Cargo-only logs (raw; schema-exempt) |
| `BUILD_EXIT_CODE.txt` | Cargo exit; `cargo_started`; outcome; failure stage |
| `BUILD_TIMING.txt` | UTC start/end, elapsed, outcome |
| `ARTIFACT_IDENTITY.txt` | Path, size, SHA-256 when present; `reason` when absent |
| `STATIC_ARTIFACT_INSPECTION.txt` | file/readelf/objdump when present; `reason` when absent |
| `POST_BUILD_INTEGRITY.txt` | Before/after source and `Cargo.lock` |
| `WITNESS_STATEMENT.md` | Identity, independence, AI assistance, human review |
| `WITNESS_VERDICT.md` | Single line `Witness proposed verdict: PASS\|PARTIAL\|FAIL\|INDETERMINATE`; `maintainer_intake_verdict=pending` |
| `DEVIATIONS.txt` | Procedure changes; severity + ceiling per deviation |
| `REDACTIONS.md` | Redaction log |
| `EVIDENCE_MANIFEST.sha256` | Checksum manifest (**final**, after manual files) |
| `HOST_RUN_METADATA.txt` | Host-only auxiliary run record (**optional**; not required in the manifest) |

See [WITNESS_PACKAGE_MANIFEST.md](WITNESS_PACKAGE_MANIFEST.md) for the full normative list.

---

## Bootstrap (container)

Noninteractive `apt-get install` (versions **not** pinned — record observed):

`ca-certificates`, `git`, `build-essential`, `pkg-config`, `cmake`, `curl`, `perl`, `file`, `binutils`

| Component | Pin |
|-----------|-----|
| DotSlash | `CARGO_TARGET_DIR=/work/bootstrap-cargo-target cargo install dotslash --version 0.5.7 --locked` into isolated `CARGO_HOME` (must **not** write to `/work/cargo-target`) |
| protoc | Copy `/src/bin/protoc` → writable LF file under `/work/bootstrap/`; `chmod +x`; `export PROTOC=<that path>`; version probe via descriptor only |

**Do not** modify `/src`. **Do not** run the product binary.

---

## Build command (exact)

```bash
cargo build -p xai-grok-pager-bin --locked
```

With `CARGO_INCREMENTAL=0`. No `-j 2` in the canonical command (optional parallelism is a
`NONMATERIAL_DISCLOSED` deviation if used, capped at PARTIAL).

Separate `cargo fetch --locked` is **omitted**; fresh `CARGO_HOME` still requires network during
the locked build. Completely offline reproduction is **NOT ESTABLISHED**.

---

## Failure behavior

| Condition | Behavior |
|-----------|----------|
| Missing `WEAVER_FORGE_TAG` on origin | Host script **exit 3** with clear message and the list of available `grok-build-witness-*` tags |
| Non-empty `WORK_ROOT` | Refused unless `--allow-nonempty-work-root` (plus typed confirmation or `--force-work-root-reset`) |
| Unsafe `WORK_ROOT` (`/`, `$HOME`, system prefix, WSL drive root, Weaver repo) | **exit 2** |
| Weaver Forge package clone tree not clean, or commit mismatch (once pinned) | **exit 3** |
| `Cargo.lock` SHA-256 mismatch before Docker | **exit 4** |
| Grok Build source commit mismatch or dirty tree after checkout | **exit 4** |
| Host pre-build target directory not empty | **exit 5** |
| `docker pull` non-zero exit | **Fatal**; `INFRASTRUCTURE_FAILURE`; no fallback image |
| Image identity/platform mismatch before `docker run` | **exit 8**; container never started |
| Non-empty Grok Build target before build (in-container) | Stop; record failure; `BUILD_NOT_STARTED`; no Grok Build Cargo |
| Bootstrap failure | `cargo_started=NO`, `BUILD_NOT_STARTED`, container exit ≠ 0 |
| Post-build integrity failure (source/lock changed) | Final exit code `9`; classification per [WITNESS_CLASSIFICATION.md](WITNESS_CLASSIFICATION.md) |
| Any unexpected/uncaught failure | `ERR` trap records `UNEXPECTED_FAILURE` with `failing_stage` and best-effort outcome rather than leaving evidence silently incomplete |

---

## Optional / noncanonical alternatives

Manual step-by-step Docker without the host script is **unvalidated**. Owner historical paths
under `../evidence/` are **not** Witness commands.

---

## Static inspection (after successful build only)

Applicable only when outcome is `CARGO_SUCCEEDED_ARTIFACT_PRESENT`. Record path, size, SHA-256,
`file`, `readelf -h`, `readelf -n`, `readelf -d`, `objdump -f`. **Never execute** the artifact.
**`ldd` forbidden.** For every other outcome, `STATIC_ARTIFACT_INSPECTION.txt` records
`inspection_applicable=no` and `artifact_present=no` with a non-empty `reason`.

---

## Validator output stays outside `EVIDENCE_DIR`

The structural validator (`scripts/validate_witness_evidence.py`) writes **only** to its own
stdout/stderr. It never writes, creates, or modifies any file inside the evidence directory it
validates. Validator invocations must capture their output **outside** `EVIDENCE_DIR` (e.g. to a
separate log file or the terminal) at every stage of a run — before the preliminary manifest,
before finalization, and for any re-run after redaction review. Never redirect validator
stdout/stderr into `EVIDENCE_DIR`, and never write validator output into the evidence tree even
after the final manifest has been generated.

---

## Evidence manifest lifecycle (exact)

1. The host orchestrator writes a **preliminary** `EVIDENCE_MANIFEST.sha256` immediately after
   automated capture finishes, covering only the automated evidence files. At this point the
   manual files (`WITNESS_STATEMENT.md`, `WITNESS_VERDICT.md`, `DEVIATIONS.txt`, `REDACTIONS.md`)
   may still be incomplete or absent from the manifest.
2. The Witness completes every manual file.
3. The Witness completes the redaction review per
   [WITNESS_SECURITY_AND_REDACTION.md](WITNESS_SECURITY_AND_REDACTION.md).
4. The Witness regenerates the **final** manifest from inside the evidence directory (excludes
   the manifest file itself):

   ```bash
   cd "${EVIDENCE_DIR}" && find . -type f ! -name 'EVIDENCE_MANIFEST.sha256' -print0 | sort -z | xargs -0 sha256sum > EVIDENCE_MANIFEST.sha256
   ```

5. The structural validator is run **only** against this final manifest, with its own output
   captured outside `EVIDENCE_DIR`. The validator recomputes SHA-256 for every listed file and
   fails on mismatch, missing entries, unsafe paths, duplicates, symlinks, or an unlisted regular
   evidence file (`HOST_RUN_METADATA.txt` is the sole documented optional exception — see
   [scripts/VALIDATOR.md](scripts/VALIDATOR.md)).
6. No further evidence-directory edits occur after step 5 passes; any correction after this point
   follows [CORRECTION_LEDGER.md](CORRECTION_LEDGER.md), never an in-place edit of accepted
   evidence.

---

## Package remains NOT READY (rc4 static disposition)

This runbook describes the **procedure** a Witness would follow once a candidate package is
suitable for Independent Witness handoff. The fixed rc4 package itself remains **NOT READY**
(static disposition; 40 integrated blockers). Phase 0 audit intake is complete. Phase 1
documentation and release/status remediation is being performed on `main`. Technical
implementation remediation of scripts, schemas, validators, tests, and execution controls has not
begun. `main` is being prepared toward a possible future rc5 candidate; **no rc5 tag exists**.
Independent Witness reproduction has **NOT** been performed. C-014 remains **`NOT_STARTED`**.

Canonical execution requires successful annotated-tag resolution of
`grok-build-witness-v1.0.0-rc4` → `039b46737c5968a81fb756d7a6d1d0dd57b6ad96`. If resolution
fails, canonical execution stops (host script `exit 3` by design). The tag is immutable. Later
`main`-branch status/audit/remediation records are outside the tagged snapshot.

### HISTORICAL PRE-TAG STATE

Earlier revisions of this section used “until/before/after rc3 tag exists” and “do not attempt a
live run against `main` before the rc3 tag exists” as current normative identity language. That
language is superseded: rc3 was tagged and audited **NOT READY** (C-026). Separately,
pre-publication wording described rc4 as “package content under preparation” / “pending commit,
tag, and re-audit.” That prospective wording is superseded: rc4 is fixed and immutable at the
identity above, statically audited **NOT READY** (C-027).

## Change log

| Version | Change |
|---------|--------|
| 1.0.0-rc2 | Prior canonical-platform, host-block, directory-layout, Docker-contract, bootstrap, build-command, failure-behavior, and manifest-lifecycle sections |
| 1.0.0-rc3 | Added canonical-constants table; `--noncanonical-deviation` section; `WITNESS_ID` regex; `WORK_ROOT` safety enumeration; evidence-initialization-before-fallible-operations section; outcome model; validator-output-outside-`EVIDENCE_DIR` policy made explicit; exact numbered manifest-lifecycle steps; image-pull-fatal and image-identity-recheck behavior documented; expanded failure-behavior table with exit codes |
| 1.0.0-rc4 | Status/identity advanced to `1.0.0-rc4` / `grok-build-witness-v1.0.0-rc4`; rc3 recorded as immutable NOT READY history; annotated-tag resolution wording. **Historical note:** contemporaneous change-log text claimed removal of normative pre-tag “tag exists/pending” assertions; the rc4 static blind audit later found remaining prospective/pending status banners and related closure overclaims (RC4B-001/002/003). Phase 1 documentation on `main` corrects those current-facing statements without altering this tagged snapshot. |
| main (Phase 2A; not an rc5 release) | Document host identity-gate-before-Docker-CLI, raw annotated-tag type enforcement, and atomic `EVIDENCE_DIR` allocation. **RC4 remains NOT READY**; **rc5 tag does not exist** |
| main (Phase 2B; not an rc5 release) | Document narrow bind mounts, mount-plan validation before Docker, comma/CR/LF mount-field prohibition (spaces allowed via argv arrays), required pre-existing mount sources, and fatal canonicalization without textual fallback. **RC4 remains NOT READY**; **rc5 tag does not exist** |
| main (Phase 3C; not an rc5 release) | Document container terminal finalization on `main` per Phase 3B contract; host ingestion still noncompliant until Phase 3D; validator/`POST_BUILD` unchanged. **RC4 remains NOT READY**; **rc5 tag does not exist** |
| main (Phase 3D; not an rc5 release) | Document host outcome ingestion / no-overwrite on `main`; host preserves valid container outcomes; separate host infrastructure/source-integrity fields; invalid/missing results fail closed without fabrication; ingestion record is preliminary and does not imply PASS; `POST_BUILD`/validator gating remain pending. **RC4 remains NOT READY**; **rc5 tag does not exist** |
| main (Phase 3E; not an rc5 release) | Document host-owned complete truthful schema-aligned `POST_BUILD_INTEGRITY.txt` on `main`; `status=OK` iff `post_build_integrity_ok=yes`; finalized failures use `status=FAILED`; `HOST_OUTCOME_INGESTION` synchronized; container remains non-writer; validator is schema consumer only; validator-gated host success remains Phase 3F; `preliminary_success_eligible` remains `NO`. **RC4 remains NOT READY**; **rc5 tag does not exist** |
| main (Phase 3F-A; not an rc5 release) | Document validator explicit-outcome requirement (inference removed); `HOST_OUTCOME_INGESTION.txt` closed-aux acceptance + structural validation; host-preliminary structural mode and automatable RC4B-017 subset without `evidence_inventory_complete=yes`; validator still writes no evidence; host invocation/exit gating deferred to Phase 3F-B; `preliminary_success_eligible` remains `NO`. **RC4 remains NOT READY**; **rc5 tag does not exist** |
| main (Phase 3F-B; not an rc5 release) | Document host invocation of `--host-preliminary` after preliminary manifest; host-owned `VALIDATOR_RESULT.txt` + stdout/stderr captures outside `EVIDENCE_DIR`; host exit 0 requires validator process exit 0 **plus** exact `STRUCTURAL VALIDATION: PASS` and the adjudicated automated gates; validator process exit 0 alone insufficient; `preliminary_success_eligible` remains `NO`; host exit 0 ≠ final success eligibility / Independent Witness PASS. **RC4 remains NOT READY**; **rc5 tag does not exist** |
| main (Phase 3G; not an rc5 release) | Document generator-backed Phase 3G automated preliminary integration on `main`: sourced writers + real local `--host-preliminary` validator primary; Docker/Cargo/product mocked/prohibited in tests; host exit 0 = preliminary automated structural success only; `preliminary_success_eligible` remains `NO`; final manual Witness submission and Independent Witness remain later. **RC4 remains NOT READY**; **rc5 tag does not exist** |
