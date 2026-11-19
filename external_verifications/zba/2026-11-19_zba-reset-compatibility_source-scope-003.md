# ZBA Reset Compatibility 0.1 — source-scope record 003

**Reviewed:** 2026-11-19 JST  
**Execution status:** **NOT VERIFIED** until the actual Actions run, logs and result archive have been reviewed.

## Pinned provenance

- Source: `ResearchForumOnline/research@60c343237cbf17ee3ec2969c009ec026840d618e` (commit resolved from public main on review date, explicitly pinned; the public main may advance).
- Public source: `artifacts/zba-reset-compatibility-0.1/verify_reset_algebra.py`.
- Git blob identity of source as reviewed: `22dce35c19093930b6c86632fa70484c257e9659` (Git SHA-1, not SHA-256).
- Public README says 496 finite validator cases and 248 synthesis cases. Its 36-state distribution is **formula-derived, not exhaustive over 2^36 validators**. Do not conflate.
- Research has a manuscript and disclosed AI assistance; source reproducibility is not equivalent to independent mathematical proof or peer review.
- Reuse the existing Weaver Forge development branch `development/independent-verification-v2` only. No modifications to RC8/main/historical receipts.

## New workflow

`.github/workflows/zba-reset-compatibility.yml`:

1. Pin source at the exact commit and print source script SHA-256.
2. Run the original author reference verifier, demand 496/248 results, five finite cases n=4..8 and the explicit 36-state **formula-only** disclosure.
3. Add an independently written finite oracle for **n=4 only**, enumerating 16 validators with a separate composition and closure algorithm, compare histogram with original result and reject an intentionally malformed histogram. This is a narrow cross-implementation comparison (unlike the 496/248 original reference tests) and does not establish universal correctness.
4. Collect completed job log, output archive, SHA-256 manifest, and metadata to an Actions artifact (retention 90 days).

**Do not claim PASS** from the presence of this workflow. After run execution, separately review GitHub job success, raw logs, SHA-256 manifest, inner output and artifact provenance. Persistent retention of raw ZIP still needs separate controlled archival.

## Prior linked verification

ZBA 1.1 Run #1, ID `44480524971`, has a source-scope record 001 and validated evidence record 002. This is a *different* bounded test. ASIN-HHC Ledger 789 remains separate.
