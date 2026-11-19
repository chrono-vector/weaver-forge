# Independent Verification v2 — GPT-assisted operating guide

Status: WORK IN PROGRESS / NOT QUALIFIED
Scope: `development/independent-verification-v2` only

## Preservation boundary

- Historical RC8 tag `grok-build-witness-v1.0.0-rc8` and its tree are immutable evidence.
- Do not edit historical receipts, witness transcripts, original evidence, existing worktrees, or `main`.
- Ryan/Claude's reported 15/15 PASS is a *scoped reported result*, **not** an accepted independent-witness PASS. Independence confirmation and the original `wf-witness-transcript.txt` / SHA-256 mismatch remain unresolved.
- No existing CAW, VECTOR, Job Agent, or external-project verification is promoted by this branch or its CI.

## Start from a pinned commit

Record the repository URL, commit SHA, branch, OS, Python version, time, commands, exit codes, and relevant output before making any claim. A branch name alone is not a reproducible pin.

For local Windows PowerShell or a Linux/macOS shell, run these commands from a *separate, clean checkout*:

```sh
git rev-parse HEAD
git status --porcelain
python --version
python -m unittest audit_lifecycle.tests.test_lifecycle
python scripts/validate_receipts.py
python scripts/check_receipt_coverage.py
git status --porcelain
```

Run only on trusted source and a disposable workspace. If anything changes tracked evidence, stop, preserve the logs, and report the mutation rather than silently reverting it. Some tests may produce temporary artifacts; inspect them before cleanup.

## CI

The optional `.github/workflows/independent-verification-v2.yml` workflow targets Python 3.11 on Ubuntu and Windows. Check the GitHub Actions run *for the exact commit* and both OS jobs. Workflow presence does not establish a PASS; a missing run is **NOT VERIFIED**, not PASS. An unsuccessful run is **FAIL** or **BLOCKED** according to the evidence.

The pre-existing `.github/workflows/validate-receipts.yml` remains unchanged.

## Claim labels

- **PASS** — executed at the pinned SHA, expected checks passed, raw logs or an independently inspectable run are available; this is still a *bounded test result*.
- **FAIL** — a specified expected check failed.
- **BLOCKED** — cannot execute because of a concrete prerequisite or environment limitation.
- **INCOMPLETE** — executed but necessary evidence, scope, or checks are missing.
- **NOT VERIFIED** — no execution evidence was reviewed.
- **REPORTED** — a contributor's result was received but not independently reproduced.

Never convert a code review, screenshot, or a self-reported PASS into independent witness qualification.

## Efficient GPT workflow

1. Ask GPT to inspect a specific GitHub commit and selected files only; do not repeat a full repository audit.
2. Define *one exact claim* and the minimum test or artifact needed to assess it.
3. Run the existing test locally, in an isolated environment, or through a pinned GitHub Actions job. GPT reasoning alone is not execution evidence.
4. Send the resulting logs, SHA-256 values, and exact SHA to GPT for an evidence-limited report.
5. Save a new receipt separately; never rewrite the original receipts or the old RC8 witness package.

### Minimal review request for GPT

> Review ONLY repo chrono-vector/weaver-forge at commit <SHA> for the claim <CLAIM>. Read the relevant source files, supplied logs, and SHA-256 evidence. Do not assume any test ran unless a real run/log is provided. Return PASS/FAIL/BLOCKED/INCOMPLETE/NOT VERIFIED/REPORTED with precise scope, evidence, and remaining limitations. Do not modify the RC8 tag, main, receipts, or evidence.

## Not yet implemented in v2

- External repository download, pinning, and source integrity verification.
- ASIN-HHC Ledger 789 adapter and replay.
- Zero Boundary Algebra adapter or tests.
- A full cross-component VECTOR / Job Agent / Integration Harness qualification.
- Independent human witness attestation or operational authorization.

Each requires a separate bounded implementation and fresh evidence. Do not claim these capabilities from the workflow file or this guide.
