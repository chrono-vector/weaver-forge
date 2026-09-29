# R4-B Reconstructability Report and Review Disagreement (minimal)

Derived evidence only. Non-authoritative. Does not close R4.

## Canonical states

Exactly two bounded states — never inferred from artifact presence/absence:

- `LEGACY_PRE_R4B` — `EXECUTION_MANIFEST.json` matches the allowlisted legacy
  shape/version (`lifecycle=weaver_forge_audit_lifecycle_v0`) and has **no**
  `r4_b` object.
- `R4_B_ENABLED` — `EXECUTION_MANIFEST.json.r4_b` is present, enabled, and
  passes schema `r4.epistemic.expectation.v1`.

Absence of R4-B artifacts never itself implies legacy.

## Expectation source

`EXECUTION_MANIFEST.json` is the **single** canonical R4-B expectation source.
The `r4_b` object is strictly validated before any artifact inspection.

Required when R4-B enabled:

- exactly one declared reconstructability report (path + digest)
- `expected_disagreement_record_digests` explicitly present (may be `[]`)
- `expected_disagreement_chain_heads` explicitly present (may be `[]`)
- `finalized_for_freeze: true` in frozen packages

Empty disagreement set (`[]`) is valid only when the expectation metadata is
explicitly present. Empty set ≠ missing expectation metadata.

## Freeze order

1. Construct/finalize the R4-B expectation object
2. Finalize `EXECUTION_MANIFEST.json` (including `r4_b`)
3. Generate frozen evidence index
4. Bind finalized manifest + expected R4-B artifacts into the freeze package
5. Write `FREEZE_STATUS.json` as the freeze-completion record

After frozen evidence index creation, `EXECUTION_MANIFEST.json` must not be
mutated.

## RECONSTRUCTABILITY_REPORT

- Schema: `r4.epistemic.reconstructability.v1`
- Artifact: `RECONSTRUCTABILITY_REPORT.json`
- **Required** when `R4_B_ENABLED`
- `authority: false` always
- Canonical path: `strict_parse_report` → expected path/digest check →
  `derive_expected_report` → exact semantic comparison
- Stored JSON alone is not proof
- Reproduction command templates are code-owned only; the verifier never
  executes arbitrary stored command text
- `independent_evidence_count = 0` / admission `NOT_CONFIGURED` (R4-A M1)
- `reconstructable` remains non-authoritative

## REVIEW_DISAGREEMENT

- Schema: `r4.epistemic.review-disagreement.v1`
- Storage: `reviews/<record-digest>.json` (content-addressed, **immutable**)
- `authority: false` always
- Canonical path: `strict_parse_record` → filename/content binding →
  expected-set equality → `verify_chain_graph`
- Records are never rewritten; resolution creates a **successor**
- Exclusive create semantics (no overwrite-capable write); same-bytes may be
  idempotent; different bytes fail closed
- Unique `disagreement_id`, unique `record_digest`, unique reviewer IDs per record
- Actual digest set under `reviews/` must equal
  `expected_disagreement_record_digests` exactly
- Successor creation must not remove predecessor expectation
- At most one successor per predecessor; terminal `RESOLVED_BY_SUCCESSOR`
  must not have another successor
- Across chain preserve: `subject_id`, `scope`, `category`, chain root
- `AMBIGUOUS` / `UNRESOLVED` are valid terminal outcomes
- No synthetic consensus; no reviewer-majority authority
- No Human Final automation; no execution authorization

## Strict parsing

No coercion. Field absent → documented optional default may apply.
Field present → must already have exact valid type/shape. Unknown fields
rejected (except inside validated `extra` mapping). Stored digests are
required and never synthesized during stored-evidence parsing.

## Non-authority

R4-B outputs never alter VECTOR/EIG, Weaver PASS/FAIL, Human Final, or
claim epistemic status, and never authorize execution.
