# Association Carriage Receipt v0 — Human Final

Date:
2026-10-04

Human Final:
HUMAN_REVIEW_ACCEPTED

This document records a Human Final decision explicitly made by the human authority. It does not record an AI acceptance decision.

HUMAN_REVIEW_ACCEPTED accepts the frozen ACR-v0 contract and its implementation and tested envelope within this scope. It does not establish truth, support, sufficiency, completeness, correspondence, independence, admission, authority, technical verification of external reality, freshness, replay distinction, external anchoring, historical CLOSED-receipt binding, execution success, creator identity, creation time or order, legacy digest equivalence, or post-hoc replacement detection.

PASS is not authority. Evidence is not authority. A receipt is not admission. This Human Final does not convert an ACR receipt into truth or authority.

Supplied-input reproduction remains supplied-input reproduction. It is not independent reproduction.

Fixed reviewed implementation SHA:
f4a05c22a9a982cd80cfaf2920659b2fe94f4565

Repository:
C:\dev\Weaver\weaver-forge-r4

Scope:
Association Carriage Receipt v0 (ACR-v0) only

Design freeze:
docs/next/ACR_V0_HUMAN_DESIGN_FREEZE_20261004.md

Design-freeze save commit:
e36c9a6c1d5d08a5c9a0faca2a78f35a6e2016af

Material blockers:
0

## Implementation history

- production origin: 17da3fc951eb31b9d4f69ad76a10208732070a04
- R1 test-only remediation / fixed reviewed implementation and test SHA: f4a05c22a9a982cd80cfaf2920659b2fe94f4565

Production implementation originated at 17da3fc951eb31b9d4f69ad76a10208732070a04. R1 was test-only. Production remained byte-identical to that implementation through the fixed SHA. The remediation strengthened tests. It did not change production semantics.

## Review history

Final review:
VERDICT ACCEPT. MUTANT_K KILLED. MATERIAL_FINDINGS NONE. NONMATERIAL_FINDINGS NONE. CLOSED_SCOPE_SAFETY PASS. READY_FOR_HUMAN_FINAL YES.

## Accepted evidence

- ACR focused tests: 27 passed, 28 subtests passed
- CSAR-v0 regression: 45 passed, 15 subtests passed
- ACD-v0 regression: 21 passed, 5 subtests passed
- DSDS-v0 regression: 36 passed, 19 subtests passed
- broader relevant regression: 793 passed, 110 subtests passed, 0 failed
- canonical four-field preimage: 1346 UTF-8 bytes, no trailing newline
- canonical five-field ACR record: 1430 UTF-8 bytes, no trailing newline
- production code changed during R1: NO
- CLOSED scope changed: NO
- worktree clean before this documentation-only save
- pushed: NO

Golden values:

- `receipt_digest`: `bdd4a8cfb4e319547a322e505c8e525de8d09cf58ec9880b8b719b0fedbe00e2`
- ordinary SHA-256 fingerprint of the exact canonical record bytes: `1c00d03fb1e4430bde21fc7cc79ae93dd42fd2c3d26d4d56cd9467b9159ae1fe`

The ordinary SHA-256 fingerprint is a byte fingerprint of the canonical record. It is not the semantic receipt digest.

These are the recorded results against the frozen ACR golden vector. This Human Final does not add a new independent reproduction, a formal proof, or an external anchoring claim.

## Boundary

This Human Final accepts only the defined ACR-v0 implementation scope at the fixed SHA above.

Accepted boundaries that remain unchanged:

- R3 unchanged / CLOSED
- R4 unchanged / CLOSED
- WVMA-V1 unchanged / CLOSED
- Tested-Envelope Receipt v0 unchanged / CLOSED
- Recovery Preflight v0 unchanged / CLOSED
- Independent Verification Preflight v0 unchanged / CLOSED
- Conducting Receipt v0 unchanged / CLOSED
- Recovery Execution Receipt v0 unchanged / CLOSED
- Evidence Binding DAG v0 unchanged / CLOSED
- Domain-Separated Digest Spec v0 unchanged / CLOSED
- Association Carriage Digest v0 unchanged / CLOSED
- Claim / Subject Association Record v0 unchanged / CLOSED
- ACR-v0 Human Design Freeze unchanged
- no public push
- no private push

## Future new-scope workflow

For future NEW scopes, the default workflow is:

1. Freeze, together with an adversarial attack and mutation specification.
2. One implementation batch: implementation, tests, planned mutations, and self-remediation.
3. One independent read-only final review.
4. Human Final.

Only a material finding may trigger one bounded remediation and targeted confirmation exception.

This workflow change applies to future new scopes. It is not applied retroactively to CLOSED scopes.

## Closure

After this record is saved, ACR-v0 is CLOSED for this defined scope. Any semantic change requires a new additive scope or version rather than silent modification of this accepted implementation.

## Change rule

Any future change to accepted ACR-v0 implementation semantics is a new scope or version and must not silently rewrite this Human Final.

## Push status

NO. No public or remote push is authorized by this record. No push had been performed at the time of this acceptance.
