# Evidence Binding DAG v0 — Human Final

Date:
2026-10-03

Status:
HUMAN_REVIEW_ACCEPTED

Fixed implementation SHA:
d37714a40e8336f6affe960896a1e8a22d46e8f0

Parent:
e503e128062c0cc129ba23c5b775f4565c666be9

Repository:
C:\dev\Weaver\weaver-forge-r4

Scope:
Evidence Binding DAG v0

Final technical review:
ACCEPT

Tests:
- Evidence Binding DAG v0: 137 passed
- Tested-Envelope v0 regression: 37 passed
- Recovery Preflight v0 regression: 43 passed
- Independent Verification Preflight v0 regression: 49 passed
- Conducting Receipt v0 regression: 72 passed
- Recovery Execution Receipt v0 regression: 95 passed
- Scoped pytest across the six packages: 433 passed, 43 subtests passed
- Full-repo pytest intentionally not used as acceptance criterion for R3

Material findings:
NONE

Accepted boundaries:
- R3 unchanged / CLOSED
- R4 unchanged / CLOSED
- WVMA-V1 unchanged / CLOSED
- Tested-Envelope Receipt v0 unchanged / CLOSED
- Recovery Preflight v0 unchanged / CLOSED
- Independent Verification Preflight v0 unchanged / CLOSED
- Conducting Receipt v0 unchanged / CLOSED
- Recovery Execution Receipt v0 unchanged / CLOSED
- VECTOR unchanged
- EIG unchanged
- accepted baseline unchanged
- no public push
- no private push

## Core semantics

Evidence Binding DAG v0 preserves:

- authority = false
- GraphComplete != Verified
- Citation != Verification
- Receipt != Admission
- HumanFinalCitation != TechnicalStatus
- ContradictionPresent != Winner
- label-only reference != digest identity
- EXTERNAL_REF != resolved body-backed evidence
- source-local PASS / RECOVERED_BOUNDED remain source-local only

Evidence Binding DAG v0 is a structural provenance/index layer only.

It does not issue a global truth/safety/recovery/acceptance verdict.

## Node model

First-class node kinds:

- RECEIPT
- CLAIM
- ARTIFACT
- EXTERNAL_REF

RECEIPT_ONLY internal model:

- Conducting challenge/revision/human_selection stay internal
- IVP CHALLENGE assumptions_attacked stay internal
- IVP counterexample body/digest stay internal
- no RECORD/subnode model in v0

Recognized receipt schema bodies must use the RECEIPT path and cannot be downgraded to ARTIFACT/CLAIM.

Unknown schemas may be ARTIFACT, but carry no receipt semantics.

## Supported receipt schemas

Closed allowlist:

- tested_envelope.v0
- recovery_preflight.v0
- independent_verification_preflight.v0
- conducting_receipt.v0
- recovery_execution_receipt.v0

Current valid builder outputs are compatible:

- TE 12/12
- RP 13/13
- IVP 22/22
- CR 17/17
- RER 34/34

## Receipt digest semantics

For TE/RP/IVP:

- no receipt_digest
- node_digest = canonical_digest(full body)

For CR/RER:

- source receipt_digest required
- validated as canonical_digest(body excluding receipt_digest)
- DAG node_digest separately hashes full body
- source_reported_digest is accepted only after validation

Old CLOSED receipts were not modified.

## Required-reference semantics

- required digest references are schema-derived
- caller cannot suppress required references
- caller cannot mint SOURCE_DERIVED edges
- missing body-backed target => GRAPH_INCOMPLETE
- EXTERNAL_REF-only target => DIGEST_ONLY_EXTERNAL / unresolved
- label-only refs never resolve by matching labels
- CITES does not satisfy required dependency by itself

structure_status:

- GRAPH_COMPLETE
- GRAPH_INCOMPLETE

GRAPH_COMPLETE means only:
all schema-derived required digest references are resolved to body-backed nodes.

It does NOT mean:

- verified
- safe
- trusted
- accepted
- recovered

## Relation model

Supported relations:

- DEPENDS_ON
- BOUNDS
- SUCCESSOR_OF
- CITES
- CONTRADICTS

- DEPENDS_ON / BOUNDS / SUCCESSOR_OF form the dependency DAG
- only that subset must be acyclic
- CITES / CONTRADICTS are annotation edges
- annotation edges do not affect structure_status
- no SUPPORTS / VERIFIES / SELECTS / CHALLENGES / RESPONDS_TO in v0
- no majority vote / winner selection
- contradiction preserves both endpoints

## Tested-Envelope binding rule

BOUNDS from Tested-Envelope:

- binds to scope body digest
- not to claim_id
- claim_id remains label-only

A Tested-Envelope PASS remains local to that receipt/scope.

## IVP REPRODUCTION / CHALLENGE semantics

Supported verification_kind:

- REPRODUCTION
- CHALLENGE

For CHALLENGE:

- authority=false
- admission_status=NOT_CONFIGURED
- structural_candidate=false
- classification=CHALLENGE_RECORDED
- source_execution_summary.evidence_digest is a schema-derived required dependency
- assumptions_attacked remain internal
- counterexample data remain internal
- no first-class subrecords in v0

Independent Evidence Admission remains separate and unopened.

## Contradiction semantics

- contradiction_present is orthogonal to structure_status
- GRAPH_COMPLETE + contradiction_present=true is valid
- contradictions require rationale
- both endpoints remain preserved
- no winner
- no invalidation
- no majority vote

## Global verdict boundary

DAG-level output does NOT emit:

PASS
SAFE
TRUSTED
VERIFIED
RECOVERED
ACCEPTED
HUMAN_REVIEW_ACCEPTED

and does NOT emit:

admission_status
independent_evidence_count
human_final_status

Source-local values remain inside source node bodies only.

## Human Final boundary

Human Final references:

- may be cited as artifact/reference material
- do not affect structure_status
- do not create technical verification
- do not create admission
- do not alter authority

This Human Final acceptance applies only to Evidence Binding DAG v0 itself.

## Nonmaterial limitations

The following limitations are NONMATERIAL. They do not reopen Evidence Binding DAG v0. They are reference records, not remediation tasks.

1. Some CHALLENGE / REPRODUCTION guards have correct live behavior but lack direct mutation-test detection, including:
   - counterexample digest/body equality
   - assumptions_attacked duplicate rejection
   - claim_id mismatch rejection
   - CHALLENGE source-summary extra-key rejection
   - REPRODUCTION classification reopening to CHALLENGE_RECORDED
   - some internal-only counterexample dependency guards

2. Recovery Preflight nested digest_observation / cited_decision keys are not fully closed beyond current accepted semantics.

3. Tested-Envelope result and source_result are not required to be equal by DAG validator even though current builder emits matching values.

4. Conducting Receipt REVISION_SELECTED / selection_present consistency is not fully re-derived by DAG.

5. Recovery Execution Receipt expected_digest vs digest(body) is not independently re-derived by DAG; source receipt validation remains source-local.

6. Some optional shapes were not observed in current compatibility fixtures:
   - certain Tested-Envelope expected_sha256 variants
   - some Conducting target_artifact_digest forms
   - some Recovery immutable_version / independent_verification_ref forms

7. Self-digests establish structural consistency, not author identity or trusted signing.

8. v0 does not model receipt-internal records as first-class graph nodes.

## Explicit non-claims

Human Final acceptance does NOT mean:

- global verification
- system safety
- production safety
- Independent Evidence Admission
- independent_evidence_count > 0
- authority transfer
- restore/recovery execution
- graph database
- orchestration
- external backend execution
- PKI/signing/key custody certification
- contradiction resolution
- Human Final for any prior scope
- VECTOR/EIG authority change

## Human Final statement

Evidence Binding DAG v0 は、上記のnonmaterial limitationを含む決められた範囲で完成・確認済みとして正式に受け入れます。

HUMAN_REVIEW_ACCEPTED

This Human Final is authoritative for this scope.

## Record

- This document is a documentation-only record.
- No implementation bytes, tests, or accepted historical artifacts were changed by this record.
- Do not reopen or modify any accepted scope.
