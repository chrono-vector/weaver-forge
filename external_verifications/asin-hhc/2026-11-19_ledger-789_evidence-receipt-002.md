# ASIN-HHC Ledger 789 — evidence receipt 002 (uploaded workflow artifact)

**Date reviewed:** 2026-11-19 (JST)
**Source:** Owner-supplied `asin-hhc-ledger-789-replay-output.zip` (not fetched directly from GitHub Actions).
**Review type:** Offline ZIP inspection, cryptographic hashing, stdout-content comparison.
**Verdict:** **BOUNDED REPLAY OUTPUT MATCH — PASS; FORMAL INDEPENDENT WITNESS — NOT CLAIMED; JOB LOGS — NOT REVIEWED.**

## Object identifiers and digests

- Reviewer repository: `chrono-vector/weaver-forge`
- Reviewer workflow source commit: `cc8d6dc99d27006c04e851efc801232bbbc0da94`
- Reviewer branch: `development/independent-verification-v2`
- External repo: `dbottrader/ASIN-HHC-Agent-Mesh`
- External pinned commit: `a9b0787078dc9db9d33eac272a2c005c165acef4`
- Owner-supplied ZIP filename: `asin-hhc-ledger-789-replay-output.zip`
- ZIP size: **389 bytes**
- ZIP SHA-256: `8e9438d30ca48535ca10551cd958df1c12ad5357f4b554dd4b1b6b29d896ad7c`
- ZIP file listing: exactly one regular entry `asin-replay-output.txt`
- Extracted entry length: **377 bytes**
- Extracted entry SHA-256: `eb7fc249f46f39838adf9136690a2799ab3212c2b4241700fa0f4a32bd34401e`
- Exact extracted stdout preserved in this reviewer branch at [evidence/asin-replay-output.txt](evidence/asin-replay-output.txt).
- The original ZIP bytes are **not uploaded to GitHub by this record**; retain the owner-supplied ZIP separately with its SHA-256 until the raw workflow log/run identity has also been archived.

## Results directly observed from the uploaded artifact

```text
inputs=/home/runner/work/weaver-forge/weaver-forge/asin-source/artifacts/ledger-789-replay/ledger-789.json
rows=789
tip=7ff43e4de6bb8cd1fa68c9514af4876741a1aa203377cc4fbec40c179aabefcb
expected_tip=7ff43e4de6bb8cd1fa68c9514af4876741a1aa203377cc4fbec40c179aabefcb
expected_height=789
result=PASS
label=SELF-CHECK
note=This pass is a self-check, not an independent verification.
```

- The reported height is 789 and the reported tip matches the pinned expected tip.
- The output itself declares `label=SELF-CHECK`; preserve that label in any quotation and downstream verdict.
- The preceding GitHub Actions #1 screen supplied by the owner showed a successful run on commit `cc8d6dc`; it did not expose the exact run ID or each job step's raw logs.
- The workflow source contains strict checks for input SHA-256, height, tip, result and an in-memory mutation test. **The negative-control stdout is not in this artifact**; a job-level success indication alone does not substitute for retaining its log.

## Evidence boundaries

**Observed PASS:** An uploaded artifact's intact contained stdout reports `rows=789`, the expected exact `tip`, and `result=PASS`. Its bytes and the enclosing ZIP have been hashed by the reviewer independently of the originating script.

**Not yet independently established from retained raw material:** Exact GitHub Actions run ID and job logs; the unmodified external input file's SHA-256 as observed in the actual run log; actual mutation-test stdout (`NEGATIVE_CONTROL=PASS`); authenticated attachment of this uploaded ZIP to an exact GitHub Actions run. The source workflow and owner screenshot are separate evidence of configuration and run-level success, not a substitute for logs.

**Not claimed:** Real-world truth of 789 activities, trusted origin of each ledger entry, independent human witness accreditation, RC8 READY, production authorization, correctness of external networks.

**Next evidence step:** Preserve GitHub Actions #1 exact run URL, downloadable raw job logs and their hashes. If unattainable, leave those rows `INCOMPLETE` rather than implying they were examined.

## Preservation boundary

Historical RC8 tag, main, Ryan/Claude witness evidence and unresolved SHA-256 discrepancy remain unchanged. This receipt does not modify external source files or promote any other project.
