"""R4-B Reconstructability Report and Review Disagreement (minimal).

Derived evidence only. Non-authoritative. Does not close R4.

## RECONSTRUCTABILITY_REPORT

- Schema: `r4.epistemic.reconstructability.v1`
- Artifact: `RECONSTRUCTABILITY_REPORT.json`
- `authority: false` always
- Derived from canonical lifecycle inputs; **recomputed on verify**
- Stored JSON alone is not proof — semantic verification recomputes and compares
- `reconstructable=true` means only that required bounded inputs are present and
  internally consistent
- `reconstructable` does **not** mean correct, safe, production-ready,
  independently validated, Human Final accepted, or authorized
- Independent evidence remains `count=0` / `NOT_CONFIGURED` (R4-A M1 preserved)

## REVIEW_DISAGREEMENT

- Schema: `r4.epistemic.review-disagreement.v1`
- Storage: `reviews/<record-digest>.json` (content-addressed, immutable)
- `authority: false` always
- Records are never rewritten; resolution creates a **successor** that references
  the prior `record_digest` / `disagreement_id`
- `AMBIGUOUS` and `UNRESOLVED` are valid terminal outcomes for a run
- Reviewer positions stay explicit — no synthetic consensus, no authority from
  agreement or reviewer count
- No Human Final automation; no execution authorization

R4-B outputs never alter VECTOR/EIG, Weaver PASS/FAIL, or claim epistemic status.
"""
