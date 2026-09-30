# CODEX_WVMA_V1_ARCHITECTURE_AMENDMENT_20260929

## AMENDMENT IDENTITY

**Amendment ID:** `CODEX_WVMA_V1_ARCHITECTURE_AMENDMENT_20260929`

**Status:** Implementation-authoritative additive architecture amendment; not an implementation and not a modification of accepted R4.

**R4 Human Final:** `6140502e915c9668960d00aef7fcd48fd14cc69f`

## ORIGINAL PLAN

**Original plan path:**

`docs/next/CODEX_WEAVER_VERIFIER_MUTATION_ASSURANCE_V1_PLAN_20260929.md`

**Original plan commit:**

`1562694dc1acaa244384105d64d4f0c3190b12b0`

The original plan and its commit remain immutable historical architecture evidence. This amendment does not edit, replace, squash, or reinterpret that historical record.

## REASON FOR AMENDMENT

Repository-grounded implementation planning identified a material mismatch between the original `WVMA-C08` property and accepted R4 behavior.

The original property required rejection of a mismatched Human Review binding. Accepted R4 does not validate reviewer identity or bind `HUMAN_REVIEW.json` to an audit ID, decision digest, artifact digest, target, or scope.

Keeping the original C08 meaning would require changing accepted R4. R4 is closed and must not be modified for WVMA-V1.

This amendment narrows C08 to the Human Review status-gate behavior that accepted R4 actually enforces.

## CONFIRMED REPOSITORY EVIDENCE

The reviewed Human Review paths are:

- `audit_lifecycle/review_gate.py`
- `audit_lifecycle/semantic_verification.py`
- `AuditOrchestrator.freeze_run`
- `AuditOrchestrator.verify_run`

When policy requires Human Review, accepted R4 enforces:

1. `HUMAN_REVIEW.json` must exist before freeze.
2. Its contents must be readable as JSON and object-like for gate processing.
3. Its `status` value must normalize to `ACCEPTED`.
4. Missing, malformed, absent-status, rejected, or unknown-status review data prevents valid freeze completion.
5. Verification of a frozen package fails when the required review is missing or has a non-accepted status.

Accepted R4 does not enforce:

- reviewer identity or authenticity;
- proof that a human produced the record;
- exact audit-ID binding;
- decision or artifact digest binding;
- target or scope binding;
- freshness;
- replay resistance;
- signatures or trusted key custody;
- semantic validation of arbitrary review-supplied metadata.

A review containing unrelated audit or digest metadata can still pass when its status is `ACCEPTED`. That behavior is outside the revised C08 property.

## SUPERSEDED C08 MEANING

The following original implementation-authoritative meaning is superseded:

> Required Human Review cannot be omitted or forged into acceptance.

The associated requirement to reject a mismatched review binding is also superseded for WVMA-V1.

The terms `forged`, `authenticated`, and `mismatched binding` must not be used as claims about accepted R4 behavior.

## REVISED WVMA-C08 PROPERTY

**Property ID:** `WVMA-C08`

> When policy requires Human Review, freeze cannot complete without a readable Human Review object whose status normalizes to `ACCEPTED`; verification of a frozen package fails when that review is missing or has a non-accepted status.

**Targets:**

- `audit_lifecycle/review_gate.py`
- `audit_lifecycle/semantic_verification.py`
- `AuditOrchestrator.freeze_run`
- `AuditOrchestrator.verify_run`

This is a status-gate assurance property. It is not an identity, authenticity, provenance, or semantic-binding property.

## REVISED C08 MUTATION MODEL

Allowed critical C08 mutations are:

1. Delete required `HUMAN_REVIEW.json` before freeze.
2. Replace it with invalid JSON.
3. Replace it with a non-object JSON value.
4. Remove the `status` field.
5. Set `status` to `REJECTED`.
6. Set `status` to an unknown or otherwise non-accepted value.
7. Remove the required review from a valid frozen disposable copy.
8. Change the review status in a valid frozen disposable copy to a non-accepted value.
9. Rebind permitted integrity manifests only where necessary to isolate semantic verification from byte-integrity rejection.

Changes limited to any of the following are not violations of revised C08:

- `audit_id`;
- `decision_digest`;
- `reviewer`;
- `notes`;
- any other ignored or unbound field.

Such mutations must be excluded from the critical catalog or classified `INVALID_MUTANT`. They must never be classified `SURVIVED`.

All mutations remain confined to disposable copies. Accepted runs, frozen evidence, R4 code, and historical records must not be modified.

## REVISED C08 ORACLE MODEL

For each C08 case, the unmutated oracle must establish:

1. The applicable policy actually requires Human Review.
2. The intended mutation was applied exactly.
3. The preimage and postimage digests match the sealed case definition.
4. A pre-freeze invalid review prevents valid freeze completion.
5. Failed pre-freeze cases do not create a valid completed freeze package.
6. A frozen-copy missing or non-accepted review produces:
   - `semantic_ok=false`; and
   - `verify_ok=false`.
7. A malformed-input process failure counts as detection only when the case's expected rejection predicate explicitly defines that conservative failure.
8. Integrity success alone cannot satisfy the Human Review property.
9. Stored verifier or runner success text cannot establish `DETECTED`.

An `ACCEPTED` record with changed unbound metadata does not violate revised C08 and must not be used as a critical survivor test.

## C08 ACCEPTANCE CONSEQUENCE

C08 is MATERIAL.

Any missing or non-accepted required Human Review that:

- permits valid freeze completion;
- produces an accepted final package;
- yields `semantic_ok=true`; or
- yields `verify_ok=true`

constitutes a critical `SURVIVED` result and blocks `ALL_CRITICAL_DETECTED`.

`INVALID_MUTANT`, `APPLY_ERROR`, `EXECUTION_ERROR`, `ORACLE_ERROR`, or `MISSING_RESULT` cannot satisfy C08 acceptance.

## C06 SCOPE CLARIFICATION

The original C06 wording is:

> PRESENT-invalid structured values never receive defaults or coercion.

For WVMA-V1 implementation, this property is restricted to the exact parser fields, factories, and verifier entry points explicitly sealed in the mutation catalog and implementation blueprint.

C06 must not be interpreted as a universal claim about every R4 value conversion, metadata field, or helper function.

Each C06 case must identify:

- the exact field;
- the exact parser or factory entry point;
- the invalid value class;
- the expected rejection;
- the direct oracle observation.

No uncatalogued R4 conversion behavior is included in C06.

## C01-C11 BOUNDED CONSISTENCY RESULT

The bounded architecture consistency review produced:

- `WVMA-C01`: valid.
- `WVMA-C02`: valid.
- `WVMA-C03`: valid.
- `WVMA-C04`: valid.
- `WVMA-C05`: valid.
- `WVMA-C06`: valid only under the catalogued scope defined above.
- `WVMA-C07`: valid.
- `WVMA-C08`: revised by this amendment.
- `WVMA-C09`: valid.
- `WVMA-C10`: valid.
- `WVMA-C11`: valid.

No second material instance of an unenforced security property was identified.

Catalog numbering remains `WVMA-C01` through `WVMA-C11`. C08 retains its identifier because a meaningful, implemented Human Review status-gate property remains available for mutation assurance.

## DEFERRED HUMAN REVIEW BINDING

The following capabilities are explicitly outside WVMA-V1:

- trusted reviewer identity;
- reviewer authentication;
- digital signatures;
- trusted key custody;
- audit-ID binding;
- decision-digest binding;
- artifact-digest binding;
- target or scope binding;
- freshness guarantees;
- replay prevention;
- revocation.

If pursued, these capabilities require a separate post-R4 architecture scope and independent review.

They must not be implemented indirectly through WVMA-V1, its runner, oracle, catalog, or result model.

## AUTHORITY AND NON-AUTHORITY

This amendment is an architecture correction for a non-authoritative assurance system.

WVMA artifacts continue to require `authority:false`.

WVMA may determine whether selected existing verifiers reject catalogued mutations. It cannot:

- authorize execution;
- establish Human acceptance;
- authenticate a reviewer;
- admit evidence;
- modify Weaver outcomes;
- establish Canonical, Published, or Deployed status;
- modify VECTOR or EIG authority.

## R3, R4, VECTOR, AND EIG BOUNDARIES

- R3 remains closed.
- R4 remains closed.
- Accepted R4 code must not be modified for WVMA-V1.
- VECTOR must not be modified.
- EIG must not be modified.
- The original WVMA plan commit must not be modified.
- Historical evidence and accepted frozen artifacts must remain unchanged.

This amendment changes only WVMA-V1 implementation authority for C08 and clarifies C06 scope.

## HUMAN FINAL BOUNDARY

Human Final remains manual and unchanged.

WVMA execution, mutation detection, verification success, or `ALL_CRITICAL_DETECTED` cannot create, imply, automate, replace, or modify Human Final.

## IMPLEMENTATION-AUTHORITY PRECEDENCE

WVMA-V1 implementation authority consists of:

1. the original WVMA plan at commit
   `1562694dc1acaa244384105d64d4f0c3190b12b0`; plus
2. this additive amendment.

Where the two records conflict:

- this amendment governs the meaning, mutation model, oracle model, and acceptance consequence of `WVMA-C08`;
- this amendment governs the implementation scope clarification for `WVMA-C06`;
- all other original plan requirements remain unchanged.

The historical original plan remains preserved as written.

## NONCLAIMS

This amendment does not:

- repair R4;
- reopen R4;
- reinterpret historical R4 acceptance;
- claim reviewer authenticity;
- claim trusted Human Review identity;
- add cryptographic review binding;
- add replay resistance;
- add external independence;
- add trusted evidence admission;
- change Human Final;
- change VECTOR;
- change EIG;
- reopen R3;
- establish Operational Hardening;
- establish production readiness;
- establish publication or deployment readiness.

## STOP CONDITIONS

STOP WVMA-V1 implementation if any of the following becomes necessary:

- modification of accepted R4 code;
- modification of the original WVMA plan;
- VECTOR modification;
- EIG modification;
- R3 or R4 reopening;
- Human Final semantic change;
- trusted reviewer identity;
- trusted evidence admission;
- cryptographic review binding;
- Operational Hardening;
- treating unbound review metadata as authenticated;
- treating an `INVALID_MUTANT` as `SURVIVED`;
- introducing a new unreviewed security property;
- any unresolved architecture ambiguity.

## AMENDMENT READINESS

This amendment resolves the known C08 architecture conflict without reopening R4 or weakening its historical acceptance.

It preserves the original plan as immutable evidence, retains the `C01-C11` catalog, narrows C08 to an existing enforceable status-gate property, and defers stronger Human Review binding to a separate future scope.

**MATERIAL_OPEN_QUESTIONS:** NONE

**READY_FOR_MECHANICAL_AMENDMENT_SAVE:** YES

**READY_FOR_CURSOR_BATCH_A1:** NO until this amendment is mechanically saved, independently verified, committed, and pinned.
