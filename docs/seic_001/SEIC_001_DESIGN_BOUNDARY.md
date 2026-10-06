# SEIC-001 Design Boundary

SEIC-001 is an additive, non-authoritative hardening layer in the existing
`audit_lifecycle.epistemic` scope. It does not replace or reinterpret any CLOSED
Weaver contract.

## Epoch Model

An `evaluator_epoch.v0` record identifies one immutable accepted base commit,
`c_E`. It pins the exact checker bytes, evaluator entrypoints, evaluator semantic
surface (ESS), non-semantic external imports, and closure policy. The record is
canonical JSON loaded from a regular, non-symlink trusted epoch file outside the
proposal repository. Direct bytes and proposal-local epoch paths are rejected.
It never selects `HEAD`, and the implementation does not derive `c_E` from the
current branch.

The executing checker must have the same SHA-256 as the checker blob stored at
`c_E` and pinned by the epoch record. A mismatch yields `EPOCH_MISMATCH`. An
unapproved epoch yields `REQUIRE_HUMAN_REVIEW`; it cannot approve itself.

Proposal content is read from Git objects. The changed-path set `M(P)` is always
the cumulative tree difference from `c_E` to the proposal commit. Proposal-local
commit boundaries do not change that comparison.

## ESS Model

Every ESS entry has exactly:

```json
{"relative_path":"...","sha256":"..."}
```

Paths are normalized repository-relative UTF-8 paths with `/` separators. They
cannot be absolute, contain `.` or `..` components, repeat after normalization,
or resolve to a symlink. Entries are unique and sorted by UTF-8 bytes. Digests
are lowercase SHA-256 over exact Git blob bytes.

The checker, evaluator entrypoints, epoch declaration paths, repo-local imported
helpers, and statically identified semantic data files must be covered by ESS.
External imports may be listed only when the trusted epoch explicitly classifies
them as non-semantic. Unlisted, unresolved, dynamic, generated, or shadow reach
cannot produce `PASS`.

## Evaluation Boundary

SEIC-v0:

- verifies the canonical epoch and ESS against `c_E`;
- rejects checker, epoch declaration, evaluator, config, schema, table, helper,
  and other ESS changes with `CLOSURE_HIT`;
- rejects non-empty caller semantic input;
- resolves bounded static Python imports and direct semantic reads from trusted
  evaluator entrypoints;
- returns `UNKNOWN_REACH` for dynamic loading, path manipulation, unresolved
  imports, shadow ambiguity, or unbound semantic reads;
- emits one canonical `evaluator_closure.v0` receipt;
- performs only read-only Git object inspection and file reads.

The implementation does not execute proposal code, write protected state,
provide a service, use a database, or require network access.

## Nonclaims

No disposition grants authorization, correctness, merge approval, policy
approval, Human Final, independent reproduction, production authorization, new
Weaver authority, or a higher evidence level. `PASS` means only that this bounded
v0 checker detected no closure violation under the pinned epoch.

No new digest domain is introduced. The receipt and epoch/ESS bindings reuse
the repository's existing canonical JSON and generic SHA-256 mechanisms.

Exact evidence ceiling:
`LOCAL_SEIC_V0_IMPLEMENTATION_AND_SYNTHETIC_VALIDATION_AT_PINNED_REPOSITORY_STATE`.
