# R4-B Reconstructability Report and Review Disagreement (minimal)

Derived evidence only. Non-authoritative. Does not close R4.

## Canonical states

Exactly two bounded package states — never inferred from artifact presence/absence:

- `LEGACY_PRE_R4B` — `EXECUTION_MANIFEST.json` matches the **strict complete**
  pre-R4-B schema (`lifecycle=weaver_forge_audit_lifecycle_v0`) and has **no**
  `r4_b` object. Subset-shaped / incomplete manifests are rejected.
- `R4_B_ENABLED` — `EXECUTION_MANIFEST.json.r4_b` is present, enabled, carries
  contract marker `weaver_forge_audit_lifecycle_r4b_v1`, and passes schema
  `r4.epistemic.expectation.v1`.

Absence of R4-B artifacts never itself implies legacy.

### Frozen monotonic classification

For frozen runs, the frozen `MANIFEST.json` is the state anchor. Root `r4_b`
must exist and match the committed `r4_b_expectation_digest`. Removing root
`r4_b`, report, or reviews fails rather than selecting legacy. Legacy is
allowed only when **both** root and frozen package match the strict complete
pre-R4-B schema. Contradictory root/freeze markers fail closed.

## Expectation source

`EXECUTION_MANIFEST.json` is the **single** canonical R4-B expectation source.
The `r4_b` object is strictly validated before any artifact inspection.

Required when R4-B enabled:

- `contract_marker: weaver_forge_audit_lifecycle_r4b_v1`
- exactly one declared reconstructability report (path + digest)
- `expected_disagreement_record_digests` explicitly present (may be `[]`)
- `expected_disagreement_chain_heads` explicitly present (may be `[]`)
- `finalized_for_freeze: true` in frozen packages

Empty disagreement set (`[]`) is valid only when the expectation metadata is
explicitly present. Empty set ≠ missing expectation metadata.

## Freeze transaction

```text
PRE_FREEZE → FREEZE_IN_PROGRESS → FROZEN
```

Normative order:

1. Validate report and complete disagreement graph
2. Finalize `EXECUTION_MANIFEST.json.r4_b` — do **not** claim freeze completion
3. Write durable `FREEZE_INTENT.json` (contract marker + finalized manifest digest)
4. Bind root evidence
5. Build the package in a uniquely owned temporary freeze directory
6. Write final decision, evidence index, frozen manifest, freeze SHA sums
7. Validate every package digest and R4-B expectation binding
8. Atomically rename the temporary package to its final path
9. Write `FREEZE_STATUS.json` **last** with `state=FROZEN` and package bindings
10. Rebind root sums — do not mutate execution manifest or package afterward

`stages_completed_through="FREEZE"` and `freeze_performed=true` may appear
**only** in `FREEZE_STATUS.json`, never before step 9.

On interruption: preserve `FREEZE_INTENT.json` and `FAILURE.json`; remove only
an owned temporary directory before publication. Final package without status,
status without package, or incomplete intent is `FREEZE_INCOMPLETE`
(`verify_ok=false`). No automatic inference of completion or legacy.

Frozen `MANIFEST.json` and `FREEZE_STATUS.json` bind:
`contract_marker`, `r4_b_expectation_digest`, `frozen_manifest_digest`,
and freeze sums digest.

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

## Strict parsing / construction

No coercion. Field absent (constructor `_ABSENT` / key omitted) → documented
optional default may apply. Field present → must already have exact valid
type/shape (`None`, scalars, strings-as-lists, mappings-as-lists rejected).
Never call `list()` / `tuple()` / `dict()` / `str()` or falsey fallback before
validation. Factories finish by parsing generated dictionaries through the
canonical strict parser. Unknown fields rejected (except inside validated
`extra` mapping). Stored digests are required and never synthesized during
stored-evidence parsing.

## Non-authority

R4-B outputs never alter VECTOR/EIG, Weaver PASS/FAIL, Human Final, or
claim epistemic status, and never authorize execution.
