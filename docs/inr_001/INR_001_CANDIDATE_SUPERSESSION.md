# INR-001 Implementation Candidate Supersession Record

Status: RECORD (append-only intent; earlier records are preserved, not deleted)

This record does not create Independent Witness admission, Human Final or production
permission, and does not claim an INR PASS.

| candidate | commit | status | basis |
|---|---|---|---|
| C1 | `c0747cc2b206ddd84aee2c04265813541cb21c7e` | FAILED | Independent review found 7 material issues; its own 20/20 local tests were insufficient. |
| C2 | `99418b4ff852e9938d785725b49eef124fa841c3` | **FAILED / NOT CLOSED** | Independent targeted review (finding M1): the verifier was fully self-attested. A hand-written synthetic event with no child process reached `PASS` (its own test `test_valid_synthetic_event_passes_predicate` asserted this). Challenge, byte identity, module identity, Git, isolation, non-origin, capture-provenance and classification facts were all read from executor-controlled JSON; `--challenge-value` was caller-supplied; challenge reuse was only checked when the caller passed `used_challenges`. |
| C2-uncommitted | (Codex working tree on top of C2, never committed) | NOT CLOSED, recovered | Direction was sound but incomplete: the event schema was not updated (every honest run failed the shape check), a writable module-global `_SESSIONS` registry let in-process callers mint synthetic snapshots (M2), assurance gaps were producer-declared, and negative controls accepted any error with rc=2 (M3; the HUMAN_FINAL control was refused by the generic top-level-schema rule). These files were preserved and built upon in C3. |
| C3 | the commit that adds this record (r2) | CANDIDATE — not independently reviewed | Fused trusted capture/verification, minted single-use child evidence, exact refusal binding, persistent ledger, re-frozen profile. See `INR_001_IMPLEMENTATION_MATRIX_R2.md`. |

## Effect on earlier documents

- `INR_001_IMPLEMENTATION_MATRIX.md` (C2) claimed `18 / 18 PASS`. That claim is
  **withdrawn**. The file is kept as the historical record of C2 with a superseded banner.
- The synthetic-PASS test pattern of C1/C2 is removed from
  `tests/test_validate_inr_v0.py`; no test constructs PASS-capable evidence.
- The design documents (`INR_001_FINAL_CLOSURE_ADDENDUM.md`,
  `INR_001_CLOSURE_MATRIX.md`) are unchanged; they record design closure, not
  implementation closure.

## Boundary

INR_PASS_CLAIMED: NO. NON_ORIGIN_RUN_EXECUTED: NO. HUMAN_FINAL_CREATED: NO.
