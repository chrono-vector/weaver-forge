# Witness submission — Grok Build (1.0.0-rc1)

## Run ID

```text
<github-user-or-witness-id>-<UTC-YYYYMMDD>-<short-run-id>
```

Example: `alice-20260722-a1b2c3`

Host helper generates this automatically.

## Primary method (preferred)

1. Fork `https://github.com/chrono-vector/weaver-forge`.
2. Branch: `independent-witness/<run-id>`
3. Evidence directory:

```text
external_verifications/grok-build/witness-submissions/<run-id>/
```

4. Pull request title:

```text
Independent Grok Build Witness: <run-id>
```

5. PR description **must** include:

| Field | Required |
|-------|----------|
| Package tag | e.g. `grok-build-witness-v1.0.0-rc1` |
| Resolved Weaver Forge commit | 40-char commit from tag |
| Grok Build source commit | `98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce` |
| Proposed verdict | PASS / PARTIAL / FAIL / INDETERMINATE |
| `product_executed` | `NO` |
| `ldd_used` | `NO` |
| Deviations | Summary or pointer to `DEVIATIONS.txt` |

## Required files (minimum)

- `EVIDENCE_MANIFEST.sha256`
- `WEAVER_FORGE_PACKAGE_IDENTITY.txt`
- `SOURCE_IDENTITY.txt`
- Full set per [WITNESS_PACKAGE_MANIFEST.md](WITNESS_PACKAGE_MANIFEST.md)
- `REDACTIONS.md`

Run structural validator:

```bash
python external_verifications/grok-build/witness-package/scripts/validate_witness_evidence.py \
  external_verifications/grok-build/witness-submissions/<run-id>/
```

Structural PASS does not prove execution or independence.

## Corrections policy

- Preserve original commits; **append** corrections (new commits or addendum files).
- Do **not** silently erase failed runs or negative evidence.
- Accepted public evidence becomes **immutable historical evidence** (subsequent corrections reference it).

## Fallback archive

1. ZIP/tar the evidence directory.
2. Record archive SHA-256 **before** extraction on the receiving side.
3. Private delivery is **not** public independent verification until published in the repository with auditable history.

## Must not modify

- Owner historical `evidence/` trees
- Pinned Grok Build source or `Cargo.lock` in upstream clone used as evidence
- Owner claim IDs (add Witness claims separately)

## Bit-identical note

Witness PASS does **not** require matching owner artifact SHA-256 values.
