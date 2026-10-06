# evaluator_epoch.v0 and evaluator_closure.v0

## Epoch Record

The epoch input is a regular, non-symlink file outside the proposal repository.
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
    "epoch_declaration_paths": ["<canonical repo-relative path>"]
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
bytewise UTF-8 sorted. Proposal content cannot supply or override the record's
semantic values.

`non_semantic_paths` is not part of `evaluator_epoch.v0`; a record that carries
it fails the closed schema as `INVALID`.

## Trusted Approval Binding

The epoch record never authenticates itself. The checker additionally requires
`trusted_epoch_sha256`: the plain lowercase SHA-256 of the exact epoch record
bytes, supplied by the caller from the Human approval record that is held
outside the proposal repository and outside the epoch file.

Human approval is represented by the independently protected binding,
not by a string inside the epoch file.

- Missing binding: `REQUIRE_HUMAN_REVIEW` (fail closed, before the record is
  interpreted).
- Malformed binding (not an exact lowercase 64-hex string): `INVALID`.
- Binding does not match the exact epoch bytes (substituted, edited, or
  re-serialized record): `EPOCH_MISMATCH`.
- `approval_status` and `human_approval_ref` are descriptive only. They cannot
  establish trust. A bound record that describes itself as `UNAPPROVED` is still
  treated conservatively as `REQUIRE_HUMAN_REVIEW`: descriptive fields may
  withhold trust but never create it.

The binding reuses the existing generic plain SHA-256 over exact bytes, the
same form already used for checker and ESS pins. It is not a new digest domain
and not a new authority; it only records which exact bytes a Human approved.

An implementation commit does not become a human-approved epoch merely by
matching this format. A successor epoch requires a new Human approval binding
and retains prior receipts unchanged.

## Closure Receipt

`evaluator_closure.v0` is a non-authoritative canonical record containing:

- epoch and proposal identities;
- generic digests of the exact epoch bytes, checker, and ESS inventory;
- cumulative changed paths from `c_E`;
- closure hits and unresolved reach findings;
- one closed disposition;
- code-owned limitations;
- a generic canonical receipt digest.

When the approval binding is missing or does not match, the receipt carries
`epoch_id` and `accepted_base_commit` as `UNRESOLVED`; untrusted epoch contents
are not echoed as identities.

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
