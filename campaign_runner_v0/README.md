# Campaign Runner v0 — Weaver Forge Operational V1

External campaign orchestration around existing Aurora intake and frozen evidence.

**Does not** modify `audit_lifecycle/`, rewrite frozen packages, or integrate Job Agent / VECTOR.

## One invocation

```bash
python -m campaign_runner_v0 run --workspace aurora_audit --policy campaign_runner_v0/policies/aurora_default.json
```

Dry-run (writes nothing):

```bash
python -m campaign_runner_v0 run --workspace aurora_audit --dry-run
```

## Outputs

Under `aurora_audit/campaigns/<campaign_id>/`:

- `VERIFICATION_PLAN.json`
- `CAMPAIGN_STATE.json`
- `EVIDENCE_REGISTER.json`
- `BLOCKER_QUEUE.json`
- `CAMPAIGN_REPORT.json`
- `CAMPAIGN_MATRIX.md` / `CAMPAIGN_INDEX.md` (derived views)
- `worker_receipts.jsonl`

## Epistemic rules (enforced in code)

- UNSUPPORTED ≠ PASS/FAIL
- INCONCLUSIVE ≠ PASS without new sufficient evidence
- HASH MATCH ≠ CONTENT TRUTH
- PROTOCOL HARNESS PASS ≠ CIVIC PASS
- PROPOSAL ≠ IMPLEMENTED
- CLASSIFICATION ≠ VERDICT
- AI PLAN ≠ EVIDENCE
- TEXT PRESENCE ≠ CLAIM TRUTH
- HUMAN AUTHORIZATION ≠ CLAIM TRUTH
- STATE ≠ EVIDENCE (CAMPAIGN_STATE alone never justifies PASS/FAIL)

Campaign-specific facts (reuse bindings, protocol-bound claims, human-auth claims,
optional expected claim count) live in workspace `intake/CAMPAIGN_BINDINGS.json`.
Source hashes are taken from `frozen_sources/SOURCE_MANIFEST.json`.

## Tests

```bash
python -m pytest campaign_runner_v0/tests -q
```
