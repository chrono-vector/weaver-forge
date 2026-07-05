# Weaver Forge Project Metrics

Factual snapshot of measurable project health as of 2026-07-05. Bounded by repository artifacts, local validation output, and public GitHub state.

## Repository

| Item | Value |
|------|-------|
| Default branch | `main` |
| Public repository | Yes — [chrono-vector/weaver-forge](https://github.com/chrono-vector/weaver-forge) |
| Current status | Working tree clean |

## Evidence

| Metric | Status | Evidence |
|--------|--------|----------|
| Total receipts | ✅ | 10 files in `receipts/` |
| Receipt validator | ✅ | `scripts/validate_receipts.py` — all receipts PASS locally |
| Receipt coverage checker | ✅ | `scripts/check_receipt_coverage.py` — inventory and drift warnings; mapping not yet enforceable |
| Commit binding validation | ✅ | Validator flags missing/malformed/unreachable `Commit:` hashes; coverage checker warns when HEAD outpaces receipt binding |
| Commit existence validation | ✅ | Validator checks `Commit:` hashes via `git cat-file` |
| GitHub Actions | ✅ | `.github/workflows/validate-receipts.yml` — 5 workflow runs on `main`, all passing |
| Witness reviews | ✅ | `WITNESS_REVIEW.md`, `WITNESS_REVIEW_TEMPLATE.md`, `receipts/2026-06-30-first-witness-review.md` |
| Independent witness reviews | ❌ | No completed review from an uninvolved reviewer (owner-authored witness work only) |

## Current Evidence Ladder

| Level | Status |
|-------|--------|
| E0 | ✅ |
| E1 | ✅ |
| E2 | ✅ |
| E3 | ✅ |
| E4 | ⏳ |
| E5 | ⏳ |

## Current Health

| Check | Result |
|-------|--------|
| Validator | PASS |
| GitHub Actions | PASS |
| Receipt Coverage | Inventory and drift warnings — exact commit-to-receipt mapping is not yet enforceable |

## Receipt Coverage Checker

Inventory report for commits on `HEAD` and Markdown files under `receipts/`:

```bash
python scripts/check_receipt_coverage.py
```

Reports total commits, total receipt files, latest commit, latest receipt binding, and coverage status. Emits warnings for inventory drift and when HEAD is newer than the latest receipt-bound commit. Exit code `0` means the inventory ran successfully. It does not claim complete coverage or full traceability; mapping remains not yet enforceable.

## Current Highest Priority

Independent witness reproduction (E4)

## Notes

These metrics describe the current repository state only. They do not claim production readiness, external validation, or long-term operational guarantees.
