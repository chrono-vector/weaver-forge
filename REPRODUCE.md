# Reproducing Weaver Forge

## Requirements

- Git on `PATH` (the validator checks cited `Commit:` hashes via `git cat-file`)
- Python 3.11 or newer (stdlib only — no `pip install` or virtual environment required)
- Network access to clone from GitHub and to view the Actions tab

## Clone

Use a **full** clone so every cited `Commit:` hash is present locally. Shallow clones (`git clone --depth 1 …`) fail commit-existence checks.

```bash
git clone https://github.com/chrono-vector/weaver-forge.git
cd weaver-forge
```

On Linux or macOS, use `python3` if `python` is not Python 3.

## Run the Validator

From the repository root (or from `scripts/`):

```bash
python scripts/validate_receipts.py
```

Every receipt should report `PASS`. Exit code `0` means all passed; `1` means at least one failure.

## Run the Coverage Checker

Optional inventory report (referenced in `PROJECT_METRICS.md`):

```bash
python scripts/check_receipt_coverage.py
```

Exit code `0` means the inventory ran successfully. Warnings about inventory drift are expected and do not fail the run.

## GitHub Actions

Open https://github.com/chrono-vector/weaver-forge/actions — the **Validate Receipts** workflow on the latest `main` commit should show a successful run.

Every push to `main` runs the validator with full git history (`fetch-depth: 0`).

## Expected Evidence

- Receipt validation passes (one `PASS` line per file in `receipts/`).
- Commit existence validation passes (built into the validator; requires a full clone).
- GitHub Actions **Validate Receipts** workflow succeeds on `main`.
- `STATUS.md` reflects the current project state.
- `PROJECT_METRICS.md` reflects the current measurable evidence.

## Witness review

Independent reviewers should complete [WITNESS_REVIEW_TEMPLATE.md](WITNESS_REVIEW_TEMPLATE.md) and share the filled template via pull request or another agreed channel.

## What this proves

Another person can reproduce the local validation process.

## What this does NOT prove

This does not prove:

- Independent witness review.
- External audit.
- Production readiness.
- Correctness beyond the validated evidence boundaries.
