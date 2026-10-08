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
| C3 (r3 status update) | `1ce1651f01496d76d07d358bdc6361e0dcdf16af` | **FAILED / NOT CLOSED** | Independent Codex review found 2 material issues. (A) Synthetic trust mint: the provenance registry lived in mutable Python closure state (`_launch_factory`), so closure introspection could register synthetic evidence without a real child, and an empty `_Findings().result()` returned PASS. (B) The profile case `PSM_NEG_HUMAN_FINAL_PRODUCTION_INFERENCE` claimed a production property that the pinned PSM validator does not enforce (it has no rule rejecting a positive production-permission assertion). The row above is kept unchanged as the original r2 record. |
| C4 | the commit that adds this row (r3) | CANDIDATE — not independently reviewed | Process boundary (trusted supervisor subprocess, `supervisor_inr_v0.py`); evidence-taking APIs removed; conjunctive default-UNCONFIRMED result; launcher pid binding; profile narrowed to `PSM_NEG_HUMAN_FINAL_INFERENCE` + `PSM_REQUIRED_PRODUCTION_NONCLAIM` (R3 re-freeze); ledger head record. See `INR_001_IMPLEMENTATION_MATRIX_R3.md`. |

## Effect on earlier documents

- `INR_001_IMPLEMENTATION_MATRIX.md` (C2) claimed `18 / 18 PASS`. That claim is
  **withdrawn**. The file is kept as the historical record of C2 with a superseded banner.
- The synthetic-PASS test pattern of C1/C2 is removed from
  `tests/test_validate_inr_v0.py`; no test constructs PASS-capable evidence.
- `INR_001_IMPLEMENTATION_MATRIX_R2.md` (C3) is kept with a superseded banner; its
  PASS rows for evidence minting are withdrawn by the C3 status update above. The
  current record is `INR_001_IMPLEMENTATION_MATRIX_R3.md`.
- `INR_001_PROFILE_REFREEZE_R2.md` is kept unchanged. The profile was re-frozen again
  in `INR_001_PROFILE_REFREEZE_R3.md` (bae309aa... -> 25fa1161...).
- `trusted_capture.py` (C3) was removed in C4; its configuration/measurement code
  moved into `supervisor_inr_v0.py`, and its evidence object and registry were dropped.
- The design documents (`INR_001_FINAL_CLOSURE_ADDENDUM.md`,
  `INR_001_CLOSURE_MATRIX.md`) are unchanged; they record design closure, not
  implementation closure.

## Boundary

INR_PASS_CLAIMED: NO. NON_ORIGIN_RUN_EXECUTED: NO. HUMAN_FINAL_CREATED: NO.
