# Witness package manifest — required outputs

Submit under:

```text
external_verifications/grok-build/witness-submissions/<witness-id>-<yyyy-mm-dd>/
```

## Required files

| File | Purpose |
|------|---------|
| `WITNESS_STATEMENT.md` | Identity, independence, AI-tool disclosure |
| `ENVIRONMENT.txt` | Host/Docker environment |
| `SOURCE_ACQUISITION.txt` | Clone commands and timestamps |
| `SOURCE_IDENTITY.txt` | HEAD, clean tree, key file hashes |
| `IMAGE_IDENTITY.txt` | Pull + RepoDigest / inspect |
| `BOOTSTRAP.txt` | apt, DotSlash, protoc, versions |
| `CLEAN_TARGET_PROOF.txt` | Empty target dir before build |
| `BUILD_COMMAND.txt` | Exact docker/cargo commands and env |
| `BUILD_ENVIRONMENT.txt` | Env vars, mounts, network mode |
| `BUILD_STDOUT.txt` | Raw cargo/docker stdout |
| `BUILD_STDERR.txt` | Raw cargo/docker stderr |
| `BUILD_EXIT_CODE.txt` | Exit codes |
| `BUILD_TIMING.txt` | Start/end/elapsed |
| `ARTIFACT_IDENTITY.txt` | Path, size, SHA-256 |
| `STATIC_ARTIFACT_INSPECTION.txt` | file/readelf (no ldd, no run) |
| `POST_BUILD_INTEGRITY.txt` | Pin/clean/lock after build |
| `DEVIATIONS.txt` | Any procedure changes |
| `WITNESS_VERDICT.md` | PASS/PARTIAL/FAIL/INDETERMINATE with justification |

## Optional

- Network/dependency download notes
- Resource observations (disk/RAM)

## Forbidden in Git

- Product binary blobs (~600 MB)
- Full Cargo registry or target trees
- Secrets
