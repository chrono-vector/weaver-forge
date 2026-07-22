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

## EVIDENCE_MANIFEST.sha256

After collecting evidence files, generate from within the evidence directory:

```bash
find . -type f ! -name 'EVIDENCE_MANIFEST.sha256' -print0 | sort -z | xargs -0 sha256sum > EVIDENCE_MANIFEST.sha256
```

The host helper performs an equivalent step automatically.

## Tests

Run from repository root (uses temporary directories only):

```bash
python -m unittest discover -s external_verifications/grok-build/witness-package/scripts/tests -p 'test_*.py'
```

Do not commit synthetic fixture trees.
