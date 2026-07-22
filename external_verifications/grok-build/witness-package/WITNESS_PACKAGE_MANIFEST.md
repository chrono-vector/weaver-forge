# Witness package manifest — required outputs (1.0.0-rc4)

Submit under:

```text
external_verifications/grok-build/witness-submissions/<run-id>/
```

## Evidence schema

Every structured file below declares `evidence_schema_version=1`. The validator
(`scripts/validate_witness_evidence.py`) enforces this per file, plus a **file-specific** required
field set — see `FILE_REQUIRED_FIELDS` in the script and [scripts/VALIDATOR.md](scripts/VALIDATOR.md).
A shared/generic body cannot satisfy more than one file's schema.

## Required files (normative — must exactly match the validator's `REQUIRED_FILES`)

| File | Purpose |
|------|---------|
| `WEAVER_FORGE_PACKAGE_IDENTITY.txt` | `witness_id`, `run_id`, package tag requested, resolved Weaver Forge commit, `canonical_run` |
| `ENVIRONMENT.txt` | Host OS/arch/Docker versions; container OS release; `rustc_version`/`cargo_version`; `product_executed=NO`; `ldd_used=NO` |
| `SOURCE_ACQUISITION.txt` | Clone URLs, UTC times, exact commands for **both** Weaver Forge package and Grok Build source |
| `SOURCE_IDENTITY.txt` | Grok Build `HEAD`, clean tree, `Cargo.lock` expected/observed SHA-256 |
| `IMAGE_IDENTITY.txt` | Docker client/server, requested digest, image ID, RepoDigests, platform match |
| `BOOTSTRAP.txt` | apt packages, DotSlash 0.5.7, protoc descriptor hashes, `PROTOC` path |
| `CLEAN_TARGET_PROOF.txt` | Absolute target path, host + container entry counts (both must be `0`) |
| `BUILD_COMMAND.txt` | Exact cargo command; `CARGO_INCREMENTAL=0`; working directory |
| `BUILD_ENVIRONMENT.txt` | `HOME`, `CARGO_*`, `DOTSLASH_CACHE`, `PROTOC`, docker platform/network mode, rust image |
| `BUILD_STDOUT.txt` / `BUILD_STDERR.txt` | Cargo-only logs (raw; schema-exempt; may be empty for `BUILD_NOT_STARTED`) |
| `DOCKER_EXIT_CODE.txt` | Docker exit code; outcome; failure stage; `product_executed=NO`; `ldd_used=NO` |
| `BUILD_EXIT_CODE.txt` | Authoritative `outcome`; `cargo_started`; `build_status`; `cargo_exit_code`; failure stage |
| `BUILD_TIMING.txt` | UTC start/end; outcome (must match `BUILD_EXIT_CODE.txt`); cargo start/finish once cargo has started |
| `CONTAINER_STDOUT.txt` / `CONTAINER_STDERR.txt` | Full Docker capture (raw; schema-exempt) |
| `ARTIFACT_IDENTITY.txt` | `applicable`/`artifact_present` per outcome; path/size/SHA-256 when present; `reason` when absent |
| `STATIC_ARTIFACT_INSPECTION.txt` | file/readelf/objdump exit codes when applicable; `reason` when not applicable |
| `POST_BUILD_INTEGRITY.txt` | Before/after source `HEAD`, clean status, `Cargo.lock` SHA-256; `source_or_lock_changed` |
| `WITNESS_STATEMENT.md` | Identity, independence declarations, AI-assistance disclosure, human review completion |
| `WITNESS_VERDICT.md` | Exact verdict-selection line; `run_id`; `package_tag`; `weaver_forge_commit`; `grok_build_commit`; `maintainer_intake_verdict=pending` at submission time |
| `DEVIATIONS.txt` | `deviation_state`; per-deviation description/severity/canonical-identity-impact/verdict-ceiling |
| `EVIDENCE_MANIFEST.sha256` | SHA-256 of all other evidence files (**final**, after manual files; regenerated once, not incrementally edited) |
| `REDACTIONS.md` | `redaction_state`; `semantic_integrity_declaration=yes`; per-redaction file/field/reason/marker |

## Optional (host-only auxiliary; closed inventory — not required in the manifest)

| File | Purpose |
|------|---------|
| `HOST_RUN_METADATA.txt` | Canonical vs. effective identity dump, `WORK_ROOT` deletion-target disclosure, manifest-lifecycle notes. Excluded from mandatory manifest entries (`MANIFEST_OPTIONAL_EVIDENCE`), but if present must not be a symlink and, if listed, its hash must match. |
| `IMAGE_PULL_STDOUT.txt` / `IMAGE_PULL_STDERR.txt` | Raw `docker pull` capture; present only on pull failure |
| `CARGO_LOCK_INTEGRITY.txt` | Direct pre/post-Docker `Cargo.lock` SHA-256 comparison performed by the host (supplements `SOURCE_IDENTITY.txt`/`POST_BUILD_INTEGRITY.txt`) |

There is **no** `BOOTSTRAP_PROTOC_VERSION.txt` under `EVIDENCE_DIR`. The closed auxiliary inventory above is exhaustive for optional host-only files: `HOST_RUN_METADATA.txt`, `IMAGE_PULL_STDOUT.txt`, `IMAGE_PULL_STDERR.txt`, `CARGO_LOCK_INTEGRITY.txt`.

Any regular file present in the evidence directory that is **not** one of the required files above
and **not** in this optional list is a structural failure (`Unlisted regular evidence file`).

## `evidence_inventory_complete` lifecycle

`evidence_inventory_complete` must **not** be set to `yes` before:

1. automated evidence capture is complete,
2. all manual forms are complete (`WITNESS_STATEMENT.md`, `WITNESS_VERDICT.md`, `DEVIATIONS.txt`, `REDACTIONS.md`), and
3. the **final** `EVIDENCE_MANIFEST.sha256` has been regenerated.

The host may leave `evidence_inventory_complete=no` until finalization. Setting it to `yes` earlier is a defect.

## Outcome requirements

Every submission declares exactly one outcome (`BUILD_NOT_STARTED`, `CARGO_FAILED`,
`CARGO_SUCCEEDED_ARTIFACT_MISSING`, `CARGO_SUCCEEDED_ARTIFACT_PRESENT`, `INFRASTRUCTURE_FAILURE`),
identical across `BUILD_EXIT_CODE.txt`, `DOCKER_EXIT_CODE.txt`, and `BUILD_TIMING.txt`. See
[WITNESS_REQUIREMENTS.md](WITNESS_REQUIREMENTS.md#outcome-model-outcome-sensitive-evidence) for
the full outcome-sensitivity table.

## Failure submissions are supported

A complete, truthful submission recording any outcome other than
`CARGO_SUCCEEDED_ARTIFACT_PRESENT` is fully acceptable and structurally validated on equal
footing with a successful build. `ARTIFACT_IDENTITY.txt` and `STATIC_ARTIFACT_INSPECTION.txt`
require `applicable=no`/`artifact_present=no` plus a non-empty `reason` for those outcomes rather
than being omitted.

## Release tag policy

- **`grok-build-witness-v1.0.0-rc1`** remains at `89127c78c3a11492892de7e3b5f0dee18d71775a`
  (repeat audit **NOT READY**). Immutable historical release.
- **`grok-build-witness-v1.0.0-rc2`** remains at `255b357c9ee33c4a9e34b5d9b6e396c53cfe494e`
  (integrated four-batch static blind audit **NOT READY**). Immutable historical release.
- **`grok-build-witness-v1.0.0-rc3`** remains at `77221a224bbd6194cfafb81f6ecb58c800e5bc13`
  (integrated four-batch static audit **NOT READY**; audit preserved under
  `evidence/rc3-static-blind-audit/`). Immutable historical release.
- Witness must record package tag **`grok-build-witness-v1.0.0-rc4`** and the
  **full Weaver commit** resolved from that annotated tag. Tag availability is verified by Git
  resolution; canonical execution requires successful resolution; if resolution fails, canonical
  execution stops. After publication, the tag is immutable.
  `package_commit_authority=annotated_tag_resolution` (no embedded future rc4 commit).

## Final manifest lifecycle

1. Preliminary manifest written automatically after automated capture (covers automated files
   only).
2. Manual files completed (`WITNESS_STATEMENT.md`, `WITNESS_VERDICT.md`, `DEVIATIONS.txt`,
   `REDACTIONS.md`).
3. Redaction review completed per [WITNESS_SECURITY_AND_REDACTION.md](WITNESS_SECURITY_AND_REDACTION.md).
4. Final manifest regenerated:

   ```bash
   cd "${EVIDENCE_DIR}" && find . -type f ! -name 'EVIDENCE_MANIFEST.sha256' -print0 | sort -z | xargs -0 sha256sum > EVIDENCE_MANIFEST.sha256
   ```

5. Structural validator run against the **final** manifest only, with validator output captured
   **outside** `EVIDENCE_DIR`.
6. No further edits inside `EVIDENCE_DIR` after a passing validator run; any later correction
   follows [CORRECTION_LEDGER.md](CORRECTION_LEDGER.md).

## Validator-output policy

The validator (`scripts/validate_witness_evidence.py`) writes **only** to its own stdout/stderr
and never modifies the evidence directory it validates, including the manifest itself.
Regenerating `EVIDENCE_MANIFEST.sha256` is always a separate, manual Witness step performed
**before** the validator is run — never the other way around, and validator output must never be
redirected into `EVIDENCE_DIR` at any stage.

## Package identity for this manifest revision

| Field | Value |
|-------|-------|
| Package version | `1.0.0-rc4` |
| Canonical package tag | `grok-build-witness-v1.0.0-rc4` |
| Package commit authority | `annotated_tag_resolution` (no embedded future rc4 commit) |
| Package readiness | **NOT READY** until rc4 committed, tagged, and repeat-audited |
| Independent Witness (C-014) | `NOT_STARTED` |
| Overall | `PARTIAL` |
| `evidence_schema_version` | `1` |
| Grok Build commit | `98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce` |
| Rust image digest | `sha256:6ca5ad23231207874325a751b9df584d51cd42c066c74c6963c264e3233c3e8e` |
| Expected `Cargo.lock` SHA-256 | `1512bb4fef0c1166c6a15a3398da9593903be1759b759ce78d9958913e61b421` |

## Forbidden in Git

- Product binary blobs (~600 MB)
- Cargo registry / target trees
- Secrets

See also [PACKAGE_FILE_MANIFEST.txt](PACKAGE_FILE_MANIFEST.txt) for the package file inventory,
[PACKAGE_READINESS_POLICY.md](PACKAGE_READINESS_POLICY.md) for package-level readiness rules, and
[MAINTAINER_INTAKE_POLICY.md](MAINTAINER_INTAKE_POLICY.md) for how a submitted manifest is
reviewed after receipt.

## Change log

| Version | Change |
|---------|--------|
| 1.0.0-rc2 | Prior required-files table, preliminary/final manifest note, release tag policy |
| 1.0.0-rc3 | Reconciled required-files list exactly against `validate_witness_evidence.py` `REQUIRED_FILES`; added optional host-only auxiliary file section; added outcome requirements and failure-submissions-supported sections; added explicit numbered final-manifest lifecycle; added validator-output policy; added package-identity table; added cross-links to the new readiness/maintainer-intake/correction-ledger policy docs |
| 1.0.0-rc4 | Status/identity advanced to `1.0.0-rc4` / `grok-build-witness-v1.0.0-rc4`; rc3 immutable NOT READY history; closed auxiliary inventory noted; `evidence_inventory_complete` lifecycle; no `BOOTSTRAP_PROTOC_VERSION.txt` |
