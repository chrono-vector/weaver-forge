# WACP-001 Verification

- Baseline: `9d2e0f85c719307ba12e1ff6fb8b2e8f3ca833d8`
- Branch: `tooling/wacp-001-context-pack`
- Placement: `tools/wacp/`
- Network dependency: `NO`
- New authority: `NO`
- New digest domain: `NO`
- Evidence semantics changed: `NO`
- CLOSED scope reopened: `NO`

## Focused tests

Command:

```powershell
python -m unittest tools.wacp.test_wacp -v
```

Result: `35/35 PASS`.

Coverage includes all four statuses, exact base/head resolution, malformed and
missing revisions, traversal/absolute/duplicate/unmatched paths, selected
symlinks, out-of-scope and excluded changes, missing required sources, budget
overflow without truncation, deterministic ordering and canonical JSON, exact
SHA-256 inventories, dirty-worktree policy, all three review modes, unrelated
file exclusion, mandatory claim boundary, no network use, and byte-identical
repeat generation.

## Mutation assurance

Result: `6/6 KILLED`.

1. Ignore an out-of-scope changed file.
2. Allow path traversal.
3. Allow a selected symlink.
4. Skip generated artifact hash verification.
5. Accept an over-budget pack instead of failing without truncation.
6. Allow a missing or malformed claim boundary.

## SEIC R1 to R2 demo

Manifest: `docs/wacp_001/SEIC_R2_DEMO_SCOPE.json`

Generated pack: `docs/wacp_001/demo_pack/`

- Status: `PACK_READY`
- Pack ID: `b453a45db731e38e827196e85a977dc64a42e4b937c478211b837aeddff7a927`
- Base: `de61774360d04ead15762200676c73bd0b5ffd6a`
- Head: `28c09d005c3002f518523856f01515fd957f33d7`
- Mode: `independent_review`
- Selected files: `3`
- Changed files: `3`
- Out-of-scope changed files: `0`
- Generated size: `20,434 / 250,000` bytes
- Artifact verification errors: `0`

The demo shows tool behavior only. It does not establish that the pack was
sufficient for the complete SEIC review and does not independently reproduce
the supplied historical SEIC test results.

## Existing Weaver validation

- `audit_lifecycle.tests.test_epistemic_r4a`,
  `audit_lifecycle.tests.test_epistemic_r4b`, and
  `audit_lifecycle.tests.test_lifecycle`: `231/231 PASS`.
- `python scripts/check_ci_supply_chain.py`: `PASS`.
- `python scripts/validate_receipts.py`: `15/15 PASS`.

## Evidence ceiling

Local implementation, synthetic tests, mutation controls, local regression
validation, and one deterministic local dogfood pack only.

Not claimed: independent reproduction, completeness, correctness, safety,
authority, evidence promotion, Human Final, merge permission, or production
authorization.
