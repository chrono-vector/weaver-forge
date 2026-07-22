# Witness evidence validator

| Item | Path |
|------|------|
| Validator | `scripts/validate_witness_evidence.py` |
| Synthetic tests | `scripts/tests/test_validate_witness_evidence.py` |

## Usage

```bash
python external_verifications/grok-build/witness-package/scripts/validate_witness_evidence.py \
  /path/to/evidence/run-id
```

Exit code `0` means **structural PASS** only.

## What it does not prove

- That Docker or Cargo actually ran
- Witness independence
- Truthfulness of logs or hashes
- Independent Witness (C-014) completion

## Required files

Must match [WITNESS_PACKAGE_MANIFEST.md](../WITNESS_PACKAGE_MANIFEST.md), including `SOURCE_ACQUISITION.txt`, `IMAGE_IDENTITY.txt`, and `ENVIRONMENT.txt`.

## EVIDENCE_MANIFEST.sha256

The host helper may write a **preliminary** manifest. After all mandatory evidence files are finalized, regenerate from within the evidence directory:

```bash
cd /path/to/evidence/run-id && find . -type f ! -name 'EVIDENCE_MANIFEST.sha256' -print0 | sort -z | xargs -0 sha256sum > EVIDENCE_MANIFEST.sha256
```

The validator **recomputes** SHA-256 for every manifest line, requires each mandatory file to be listed, rejects duplicate or unsafe paths, rejects listing the manifest itself, and **fails** on unlisted regular evidence files. `HOST_RUN_METADATA.txt` is optional in the manifest (host-only auxiliary).

## WITNESS_VERDICT.md

Exactly one selection line must appear:

```text
Witness proposed verdict: PASS
```

(or `PARTIAL`, `FAIL`, `INDETERMINATE`). Explanatory uses of those words elsewhere are ignored.

## Tests

Run from repository root (uses temporary directories only):

```bash
python -m unittest discover -s external_verifications/grok-build/witness-package/scripts/tests -p 'test_*.py'
```

Do not commit synthetic fixture trees.
