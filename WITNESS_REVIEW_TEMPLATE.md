# Witness Review Template

## Reviewer

Name / handle:

Date:

Independent from author? Yes / No

Relationship to project:

## Repository

Repository URL:

Commit reviewed:

Branch:

## Reproduction Steps

- Cloned the repository (full clone — not `--depth 1`; commit-existence checks need full history)
- Confirmed Python 3.11+ available (stdlib only; no `pip install` required)
- Ran from repository root:
  `python scripts/validate_receipts.py`
- Ran optional inventory:
  `python scripts/check_receipt_coverage.py`
- Checked GitHub Actions: https://github.com/chrono-vector/weaver-forge/actions (workflow **Validate Receipts** on `main`)
- Reviewed STATUS.md
- Reviewed PROJECT_METRICS.md
- Reviewed REPRODUCE.md

## Results

Validator result:

GitHub Actions result:

Receipts reviewed:

Any failures:

## What this confirms

State only what was directly reproduced or verified.

## What this does NOT confirm

State what was not verified, including:

- Production readiness
- External audit
- Long-term consistency
- Correctness beyond current validator boundaries

## Witness Conclusion

Choose one:

- Reproduced
- Partially reproduced
- Not reproduced

## Notes

Additional observations:

## Signature

Name / handle:

Optional signature / fingerprint:

---

**Rules**

- Do not claim authority beyond reproduced evidence.
- Witness is attestation, not authority.
- Contributor does not equal witness.
