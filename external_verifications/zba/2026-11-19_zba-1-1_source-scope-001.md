# Zero Boundary Algebra 1.1 — source-scope record 001

**Review date:** 2026-11-19 JST  
**Status:** **NOT VERIFIED (execution evidence outstanding)**

## Pinned source and evidence

- Author: Shafaet Brady Hussain; source repository: `ResearchForumOnline/research`.
- Public tag: `zba-v1.1.0`, resolved via GitHub compare endpoint to commit `c13c6ffe58850216124f9b58fa8185c5c03d7a5d`. Workflow uses **the commit SHA**, not the floating tag.
- Publication: `papers/zero-boundary-algebra-formal-specification-1.1.md`; executable reference: `artifacts/zba-1.1/property_check.py` and `zba_reference.py`.
- Git blob hashes for the source at pinned commit: `property_check.py` = `f96faaeabd471139f33c41fab0b8c7d7fc7be852`, `zba_reference.py` = `2b3255d33571f548e9b3858c56da7a880ebc4a7e`.
- Public README declares 144 structural states, three properties each 144/144, a six-event valid chain, and 14/14 adversarial mutation/topology cases. These values are **source claims until executed externally**.
- Reference license: project's catalog identifies author's original code as MIT and paper as CC BY 4.0, with original notices preserved.

## Newly configured bounded tests

Workflow: `.github/workflows/zba-1-1-reference.yml` on `development/independent-verification-v2`.

1. Checkout `ResearchForumOnline/research` at full pinned SHA and verify checkout HEAD.
2. Run published `python property_check.py` in Python 3.11, check exact structural counts, chain acceptance and 14 rejection cases.
3. Additional positive/negative probe: using the published verifier on an unaltered six-record reference chain and a deep-copy with the last record's operation altered; require acceptance of original, rejection of changed record, and proof input was not changed.
4. Package bounded result JSON and fixtures, then collect completed job log, zipped result and SHA-256 manifest into a temporary 90-day Actions artifact.

**Not independent verification:** both the published 14 cases and the additional negative case use the author's own reference implementation and verifier. This can demonstrate repeatability and one additional negative outcome, **not correctness of the cryptographic design**, signatures, key custody, trusted anchoring, full protocol coverage, or independent research review.

## Next gate

Require an exact GitHub Actions run ID, both jobs successful, original artifacts, SHA-256 manifest verified. Until that evidence is inspected, the ZBA result is **NOT VERIFIED**. Never infer PASS from workflow presence or claimed public counts.

No historical Weaver Forge RC8, main, receipts, or previous ASIN-HHC evidence were edited.
