# evaluator_epoch.v0 and evaluator_closure.v0

## Epoch Record

The trusted input is a regular, non-symlink file outside the proposal repository.
Its content is exact canonical UTF-8 JSON with these closed fields:

```json
{
  "accepted_base_commit": "<40 lowercase hex>",
  "approval_status": "HUMAN_APPROVED | UNAPPROVED",
  "authority": false,
  "checker": {
    "relative_path": "audit_lifecycle/epistemic/evaluator_closure.py",
    "sha256": "<64 lowercase hex>",
    "source": "ACCEPTED_BASE"
  },
  "closure_policy": {
    "epoch_declaration_paths": ["<canonical repo-relative path>"],
    "non_semantic_paths": ["<canonical repo-relative path>"]
  },
  "epoch_id": "<non-empty identity>",
  "ess": [
    {"relative_path": "<canonical repo-relative path>", "sha256": "<64 lowercase hex>"}
  ],
  "evaluator_entrypoints": ["<canonical repo-relative path>"],
  "human_approval_ref": "<non-empty reference>",
  "schema_version": "evaluator_epoch.v0",
  "semantic_config": {
    "caller_semantic_input": "REJECT",
    "non_semantic_external_imports": ["<top-level import name>"]
  }
}
```

The checker path, every entrypoint, and every epoch declaration path must also
be an ESS member. All set-like path/name lists and ESS entries are unique and
bytewise UTF-8 sorted. The record itself is a trusted artifact; proposal content
cannot supply or override its semantic values.

An implementation commit does not become a human-approved epoch merely by
matching this format. A successor epoch requires a distinct Human approval
reference and retains prior receipts unchanged.

## Closure Receipt

`evaluator_closure.v0` is a non-authoritative canonical record containing:

- epoch and proposal identities;
- generic digests of the exact epoch bytes, checker, and ESS inventory;
- cumulative changed paths from `c_E`;
- closure hits and unresolved reach findings;
- one closed disposition;
- code-owned limitations;
- a generic canonical receipt digest.

Closed dispositions:

- `PASS`
- `CLOSURE_HIT`
- `UNKNOWN_REACH`
- `CALLER_SEMANTIC_INPUT`
- `EPOCH_MISMATCH`
- `REQUIRE_HUMAN_REVIEW`
- `INVALID`

Every receipt has `authority: false`. No disposition authorizes a proposal,
approves a merge or policy, establishes correctness, or creates Human Final.
