# RC1 repeat blind audit — scope

## In scope

- `external_verifications/grok-build/witness-package/` runbook, manifest, submission, templates, and bash/Python scripts at tag `grok-build-witness-v1.0.0-rc1` (`89127c78c3a11492892de7e3b5f0dee18d71775a`)
- Clean-target hygiene, bootstrap Cargo target separation, host evidence generation contracts, evidence manifest lifecycle, validator completeness

## Out of scope

- Executing Docker, Cargo, DotSlash, protoc, or product binaries
- Running Witness host/container scripts
- Changing claim C-014 from `NOT_STARTED`
- Moving or recreating tag `grok-build-witness-v1.0.0-rc1`
