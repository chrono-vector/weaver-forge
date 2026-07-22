# Witness package manifest — required outputs (1.0.0-rc2)

Submit under:

```text
external_verifications/grok-build/witness-submissions/<run-id>/
```

## Required files

| File | Purpose |
|------|---------|
| `WITNESS_STATEMENT.md` | Identity, independence, AI assistance, human review |
| `WEAVER_FORGE_PACKAGE_IDENTITY.txt` | Tag requested, resolved Weaver commit, package version |
| `ENVIRONMENT.txt` | Host OS/arch/resources; container OS/arch |
| `SOURCE_ACQUISITION.txt` | Clone URLs, UTC times, exact commands |
| `SOURCE_IDENTITY.txt` | HEAD, clean tree, Cargo.lock expected/observed SHA-256 |
| `IMAGE_IDENTITY.txt` | Docker client/server, platform, image ID, RepoDigest |
| `BOOTSTRAP.txt` | apt, DotSlash 0.5.7, bootstrap vs Grok target dirs, protoc descriptor hashes, `PROTOC` path |
| `CLEAN_TARGET_PROOF.txt` | Absolute target path, listing, find, entry count = 0 (host + container + pre-build recheck) |
| `BUILD_COMMAND.txt` | Exact cargo command; `CARGO_INCREMENTAL=0` |
| `BUILD_ENVIRONMENT.txt` | HOME, CARGO_*, BOOTSTRAP_CARGO_TARGET_DIR, DOTSLASH_CACHE, PROTOC, mounts, network |
| `CONTAINER_STDOUT.txt` / `CONTAINER_STDERR.txt` | Docker streams |
| `DOCKER_EXIT_CODE.txt` | Docker exit code |
| `BUILD_STDOUT.txt` / `BUILD_STDERR.txt` | Cargo streams |
| `BUILD_EXIT_CODE.txt` | Cargo exit; `cargo_started` yes/no |
| `BUILD_TIMING.txt` | UTC start/end, elapsed, command |
| `ARTIFACT_IDENTITY.txt` | Path, size, SHA-256, Build ID if known |
| `STATIC_ARTIFACT_INSPECTION.txt` | file/readelf/objdump; `product_executed=NO`; `ldd_used=NO` |
| `POST_BUILD_INTEGRITY.txt` | Before/after source and Cargo.lock |
| `DEVIATIONS.txt` | Procedure changes |
| `WITNESS_VERDICT.md` | Single line `Witness proposed verdict: PASS|PARTIAL|FAIL|INDETERMINATE` |
| `REDACTIONS.md` | Redaction log |
| `EVIDENCE_MANIFEST.sha256` | SHA-256 of all other evidence files (**final**, after manual files) |

## Release tag policy

- **`grok-build-witness-v1.0.0-rc1`** remains at `89127c78c3a11492892de7e3b5f0dee18d71775a` (repeat audit **NOT READY**).
- Witness must record package tag **`grok-build-witness-v1.0.0-rc2`** (once published) and the **full Weaver commit** resolved from that tag.

## Preliminary vs final manifest

The host orchestrator may write a **preliminary** manifest before manual files are complete. Regenerate after finalizing mandatory files:

```bash
cd "${EVIDENCE_DIR}" && find . -type f ! -name 'EVIDENCE_MANIFEST.sha256' -print0 | sort -z | xargs -0 sha256sum > EVIDENCE_MANIFEST.sha256
```

The structural validator verifies the **final** manifest (hashes recomputed; mandatory files listed).

## Validator

Run [scripts/validate_witness_evidence.py](scripts/validate_witness_evidence.py) before submission.

## Forbidden in Git

- Product binary blobs (~600 MB)
- Cargo registry / target trees
- Secrets

See also [PACKAGE_FILE_MANIFEST.txt](PACKAGE_FILE_MANIFEST.txt) for package file inventory.
