# CODEX_WVMA_V1_C11_EQUIVALENT_MUTANT_AMENDMENT_20261002

## AMENDMENT IDENTITY

**Amendment ID:** `CODEX_WVMA_V1_C11_EQUIVALENT_MUTANT_AMENDMENT_20261002`

**Status:** Implementation-authoritative additive architecture amendment for one C11 source-mutation obligation. Not an implementation and not a modification of accepted R4.

**Reviewed accepted HEAD:** `52bfe754c476b28cad4d61eec34249ea64359576`

**R4 Human Final:** `6140502e915c9668960d00aef7fcd48fd14cc69f`

## PRESERVED RECORDS

This amendment does not edit, replace, or reinterpret:

- `docs/next/CODEX_WEAVER_VERIFIER_MUTATION_ASSURANCE_V1_PLAN_20260929.md`
- `docs/next/CODEX_WVMA_V1_ARCHITECTURE_AMENDMENT_20260929.md`

Those documents remain immutable historical evidence. The historical C11-S2 specification remains preserved there. This amendment records that specification as equivalent on the accepted HEAD and excludes it from required critical kills.

## REASON FOR AMENDMENT

The saved B2 C11-S2 source mutant replaces:

```python
verify_ok = hash_ok and bool(semantic.get("ok")) and txn_ok
```

with:

```python
verify_ok = hash_ok and bool(semantic.get("ok"))
```

On the accepted verifier that mutant is equivalent. This is a blueprint defect, not a product defect.

Accepted `AuditOrchestrator.verify_run` in `audit_lifecycle/orchestrator.py`:

- sets `freeze_sums_ok` to false when `validate_freeze_transaction` is not `PRE_FREEZE` and its `ok` flag is false;
- sets `hash_ok` from root SHA-256 verification and `freeze_sums_ok is not False`;
- sets `txn_ok` from that same transaction's `verify_ok` flag.

Accepted `validate_freeze_transaction` sets `ok` and `verify_ok` to the same boolean on every return. `PRE_FREEZE` is `verify_ok` true. Every failure return is `FREEZE_INCOMPLETE` with both flags false.

Accepted `verify_semantics` sets its `ok` flag only when `verify_r4b_at_root` is ok. Accepted `verify_r4b_at_root` returns not ok when the freeze transaction is not ok.

Therefore a failed freeze transaction forces both `hash_ok == false` and `semantic_ok == false`. Dropping only `txn_ok` cannot make top-level `verify_ok` true. The transaction-only canary is unreachable without changing accepted product semantics.

No in-scope replacement source mutant was found. A replacement that also drops the semantic conjunct is not a transaction-only canary. `expectation.py` and `r4b_verify.py` are not C11 source-mutation targets.

C11-S1, the deletion of the semantic conjunct, remains non-equivalent. Its canary is reachable: integrity and the freeze transaction pass while semantic recomputation fails, and the mutant produces `verify_ok == true`.

C07 remains the separate freeze-transaction property. It is not evidence that the removed C11-S2 source mutant was killed.

## IMPLEMENTATION-AUTHORITY PRECEDENCE

WVMA-V1 implementation authority is, in order:

1. the original WVMA-V1 plan;
2. the existing committed C08/C06 architecture amendment;
3. this C11 amendment.

This amendment controls only the C11 source-mutation obligation affected by the equivalent C11-S2 mutant. Where it conflicts with the earlier records, it governs that obligation only. Every other plan and C08/C06 requirement remains unchanged.

## REQUIRED C11 CORRECTION

C11 remains: top-level verification must not ignore material verification failure.

For WVMA-V1 source-mutation assurance:

- retain C11-S1, the non-equivalent semantic-conjunct deletion, as a required critical source mutant;
- classify the original txn_ok-only C11-S2 deletion as `EQUIVALENT_MUTANT`;
- do not count that equivalent mutant as `DETECTED`;
- do not seal it as a required critical kill;
- do not invent a replacement source mutation outside the committed C11 target, `orchestrator.verify_run`;
- keep C07 as the separate freeze-transaction and finalization property;
- do not claim that C07 proves the removed C11 source-mutant behavior;
- do not change accepted product semantics to make C11-S2 non-equivalent.

`EQUIVALENT_MUTANT` is recorded through the existing `INVALID_MUTANT` result class when a valid mutation does not demonstrate an independent property violation. It is not a new result-class enum and it is not a kill.

## B2 CORRECTED FIXED SOURCE SET

B2 requires exactly three non-equivalent source mutations:

- C06-S1
- C06-S2
- C11-S1

B2 must also record, by test, that historical C11-S2 is equivalent on accepted source semantics and is excluded from required critical kills.

## ACCEPTANCE CONSEQUENCE

B2 acceptance requires:

- the three remaining fixed source mutants reproduce their exact preimage and postimage digests;
- each declared replacement matches exactly once;
- each required mutant has its independent property observation;
- no equivalent critical mutant is counted as a kill;
- C11-S2 equivalence is explicitly tested and recorded;
- the C07 transaction catalog remains separately passing.

## EXPLICIT NONCLAIMS

This amendment does not:

- weaken R3 or R4;
- alter Human Final;
- change VECTOR or EIG;
- change C01-C10;
- redefine `semantic_ok`;
- redefine `hash_ok`;
- redefine `txn_ok`;
- retarget C11 source mutation into `r4b_verify.py` or `expectation.py`;
- claim transaction independence where the accepted implementation structurally couples the predicates;
- authorize equivalent-mutant counting as `DETECTED` or as any other kill.

## R3, R4, VECTOR, AND EIG BOUNDARIES

- R3 remains closed.
- R4 remains closed.
- Accepted product code must not be modified to manufacture a non-equivalent C11-S2.
- VECTOR must not be modified.
- EIG must not be modified.
- The original WVMA plan must not be modified.
- The existing C08/C06 amendment must not be modified.
- A1, A2, and B1 remain accepted and frozen.
