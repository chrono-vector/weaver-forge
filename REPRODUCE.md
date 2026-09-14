# Reproducing Weaver Forge

This guide describes how to reproduce the published Weaver Forge **product** checks from a clean checkout.

It is a documentation guide only. Local PASS results do not grant external authority, independent-witness acceptance, production deployment authorization, or completeness of every possible claim family.

Product status remains `WEAVER_FORGE_COMPLETE` as stated in [`README.md`](README.md).

---

## Requirements

- Python **3.10+** (stdlib only for `audit_lifecycle/`)
- Git on `PATH` when validating historical receipts
- A checkout of this repository

---

## Product reproduction (required)

From the repository root:

### 1. Lifecycle unit tests

```bash
python -m unittest audit_lifecycle.tests.test_lifecycle -v
```

Expected: **13 tests OK**.

### 2. CLI help

```bash
python -m audit_lifecycle.cli --help
```

Expected: exit code `0`.

### 3. Sanitized `hash_claim` example

```bash
# Write output OUTSIDE the source tree (do not use examples/hash_claim/runs/)
OUT="${TMPDIR:-/tmp}/weaver-forge-hash-claim-runs"
mkdir -p "$OUT"

python -m audit_lifecycle.cli run \
  --request examples/hash_claim/request.json \
  --out "$OUT"

python -m audit_lifecycle.cli verify \
  --run "$OUT/<audit_id>"
```

With `human_review_required: false` in the sample request, a successful `run` auto-freezes once. A second freeze must fail closed (`FREEZE_ALREADY_EXISTS`).

See [`examples/hash_claim/README.md`](examples/hash_claim/README.md).

---

## Optional receipt validation

Historical daily receipts under `receipts/` may be checked with:

```bash
python scripts/validate_receipts.py
```

Optional inventory:

```bash
python scripts/check_receipt_coverage.py
```

Use a **full** clone when commit-existence checks matter. Shallow clones may omit older cited commits.

A successful local receipt validator run is local validation evidence only. It is not independent-witness acceptance and not production readiness.

---

## What reproduction can support

- The lifecycle unittest suite passed in the observed environment
- The CLI help entrypoint exited successfully
- The sanitized `hash_claim` example produced a frozen package that `verify` accepted
- Receipt files (if checked) satisfied the local validator at the time run

Record the commit identity, commands, date, environment, and captured output with any claim.

## What this guide does not prove

- Independent Witness acceptance
- Production deployment authorization
- That every possible audit claim family is supported
- Cryptographic end-to-end notarization beyond SHA-256 package binding
- Completeness of historical claim-to-commit mapping beyond what tools report
