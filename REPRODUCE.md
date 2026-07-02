# Reproducing Weaver Forge

## Requirements

- Git
- Python 3.11 or newer

## Clone

```bash
git clone https://github.com/chrono-vector/weaver-forge.git
cd weaver-forge
```

## Run the Validator

```bash
python scripts/validate_receipts.py
```

Every receipt should report `PASS`.

## GitHub Actions

Every push to the `main` branch automatically runs the receipt validator in GitHub Actions. The `Validate Receipts` workflow should complete successfully.

## Expected Evidence

- Receipt validation passes.
- Commit existence validation passes.
- GitHub Actions succeeds.
- `STATUS.md` reflects the current project state.
- `PROJECT_METRICS.md` reflects the current measurable evidence.

## What this proves

Another person can reproduce the local validation process.

## What this does NOT prove

This does not prove:

- Independent witness review.
- External audit.
- Production readiness.
- Correctness beyond the validated evidence boundaries.
