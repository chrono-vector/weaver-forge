# Witness package release identity

| Field | Value |
|-------|-------|
| Package version | **1.0.0-rc2** |
| Proposed annotated tag | **`grok-build-witness-v1.0.0-rc2`** |
| Prior audited tag (immutable) | **`grok-build-witness-v1.0.0-rc1`** → `89127c78c3a11492892de7e3b5f0dee18d71775a` |
| rc1 repeat blind audit verdict | **NOT READY** |
| Grok Build source commit (upstream pin) | `98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce` |

## Tag policy

- **`grok-build-witness-v1.0.0-rc2` does not exist** during C2E-3 drafting on `main`.
- **`grok-build-witness-v1.0.0-rc1` must not be moved**, deleted, or force-updated.
- The human maintainer creates the **rc2** annotated tag **after** remediation review, commit, and push.
- The package remains **NOT READY** for blind execution until:
  1. **rc2** exists on `origin`, and
  2. A repeat blind audit confirms copyable executability.

## Evidence requirements after rc2 tag creation

Witness evidence must record:

| Field | Required |
|-------|----------|
| Package tag requested | `grok-build-witness-v1.0.0-rc2` |
| Full Weaver Forge commit resolved from tag | 40-char lowercase git commit |
| Grok Build source commit | `98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce` |

Host helper `run_witness_narrow_build.sh` fails clearly if the requested tag is absent.
