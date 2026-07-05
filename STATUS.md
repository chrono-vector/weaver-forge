# Weaver Forge Status

Concise snapshot of project state as of 2026-07-05. Claims below are bounded by receipts in `receipts/` and artifacts in this repository.

## Current Evidence Level

| Level | Status | Meaning |
|-------|--------|---------|
| E0 | ✅ Concept | Proof-of-work community model defined |
| E1 | ✅ Specification | Templates, contributing rules, and receipt format documented |
| E2 | ✅ Local execution | `python scripts/validate_receipts.py` runs locally and enforces receipt structure |
| E3 | ✅ Receipt-backed candidate | Daily receipts cite commits; validator checks commit object existence |
| E4 | ⏳ Independent reproduction | No uninvolved witness has reproduced key validation steps yet |
| E5 | ⏳ External audit | No third-party audit on record |

## Current Components

| Component | Status |
|-----------|--------|
| GitHub Repository | ✅ [chrono-vector/weaver-forge](https://github.com/chrono-vector/weaver-forge) |
| Receipts | ✅ `receipts/` — daily build receipts with required sections and `Commit:` lines |
| Receipt Validator | ✅ `scripts/validate_receipts.py` |
| Receipt Coverage Checker | ✅ `scripts/check_receipt_coverage.py` — inventory and drift warnings; mapping not yet enforceable |
| Commit Binding Validation | ✅ Validator distinguishes missing, malformed, and unreachable `Commit:` hashes; coverage checker warns when HEAD outpaces receipt binding |
| Commit Existence Validation | ✅ Validator checks `Commit:` hashes via `git cat-file` |
| GitHub Actions CI | ✅ `.github/workflows/validate-receipts.yml` — runs validator on push and PR |
| Witness Review | ✅ `WITNESS_REVIEW.md` and expanded `WITNESS_REVIEW_TEMPLATE.md` (owner-authored; not independent) |

## Current Principles

**Build. Test. Commit. Receipt. Repeat.**

**No commit. No claim. No receipt. No authority.**

**Evidence before authority.**

## Current Priority

Highest priority: **independent witness reproduction (E4)** — an uninvolved reviewer repeating clone, validator run, and spot-checks without authorship on the cited commits.

## Not Yet Proven

- Full one-to-one commit-to-receipt traceability (inventory drift is reported, not enforced)
- Independent witness reproduction
- External audit
- Long-term daily consistency
- Production deployment
