# Witness package release identity

| Field | Value |
|-------|-------|
| Package version | **1.0.0-rc1** |
| Proposed annotated tag | **`grok-build-witness-v1.0.0-rc1`** |
| Audited predecessor commit (blind audit baseline) | `0aaae298f0e543d4042302224ed075c1796a6016` |
| Grok Build source commit (upstream pin) | `98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce` |

## Tag policy

- The annotated tag **`grok-build-witness-v1.0.0-rc1` does not exist** during C2E-2 drafting on `main`.
- A Git commit cannot safely embed its own final release hash; the human maintainer creates the annotated tag **after** remediation review and push.
- The package remains **NOT READY** for blind execution until:
  1. The tag exists on `origin`, and
  2. A repeat blind audit confirms copyable executability.

## Evidence requirements after tag creation

Witness evidence must record:

| Field | Required |
|-------|----------|
| Package tag requested | `grok-build-witness-v1.0.0-rc1` (or successor) |
| Full Weaver Forge commit resolved from tag | 40-char lowercase git commit |
| Grok Build source commit | `98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce` |

Host helper `run_witness_narrow_build.sh` fails clearly if the tag is absent.
