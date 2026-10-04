# Claim / Subject Association Record v0 — Human Design Freeze

Date:
2026-10-04

Design freeze:
HUMAN_DESIGN_FREEZE_ACCEPTED

This document records a Human Design Freeze decision explicitly made by the human authority. It does not record an AI acceptance decision. It is not implementation acceptance and it is not a Human Final for an implementation.

Scope:
CSAR-v0 design only

Implementation status:
NOT_AUTHORIZED / NOT_READY

Human decision date:
2026-10-04

Repository:
C:\dev\Weaver\weaver-forge-r4

Base repo HEAD before record:
20d0f8ae86b5f07bce56a838844be0a35fcc53d0

DSDS prerequisite fixed SHA:
a7d5d63ebd7aeefc6b6fd83d7cfe30191eee51b0

CSAR-v0 remains not ready for implementation until the separate receiver prerequisite is frozen.

## Frozen six-field schema

All six fields are required. The record has no optional, null, default, alias, or extra field.

1. `schema_version` is the exact builtin str `csar.v0`.
2. `authority` is the exact builtin bool `False`.
3. `claim_digest_csar_v0`
4. `subject_digest_csar_v0`
5. `limitations`
6. `association_digest_csar_v0`

## Frozen limitations

Exact order:

1. `presented_bytes_only`
2. `not_support`
3. `not_sufficiency`
4. `not_completeness`
5. `not_truth`
6. `not_correspondence`
7. `not_independence`
8. `not_admission`
9. `not_authority`
10. `not_verification`
11. `not_human_final`
12. `not_creator_time_or_order`
13. `not_legacy_digest_equivalence`
14. `not_historical_closed_receipt_binding`
15. `omission_not_detected_here`
16. `not_freshness`
17. `not_replacement_or_post_hoc_detection`

The limitations array is a hashed semantic declaration. It does not technically force downstream consumers to respect those semantics.

## Frozen producer contract

Inputs are exactly:

- one R4 claim dict
- one presented subject bytes

The claim digest is computed only via the accepted DSDS `digest_r4_claim_body`. The subject digest is computed only via the accepted DSDS `digest_presented_subject_bytes`. The association digest is computed only via the accepted DSDS `CSAR_RECORD` domain. The producer takes no caller-provided digest input.

## Frozen validation vocabulary

- `CSAR_STRUCTURALLY_CONSISTENT`
- `CSAR_REPRODUCED_FROM_SUPPLIED_INPUTS`

These results do not use the words verified, valid, pass, or accepted, and they are not a bool ok.

`CSAR_STRUCTURALLY_CONSISTENT` is internal consistency only and does not establish inner-digest provenance. `CSAR_REPRODUCED_FROM_SUPPLIED_INPUTS` means only that the supplied original inputs reproduce all six fields.

## Frozen strict parse and encoding

- The record is an exact builtin dict.
- Keys are exact builtin str values.
- The key set is exactly the six schema keys.
- `authority` is the exact builtin bool `False`.
- Digest values are exact builtin str values.
- Digest syntax is an ASCII fullmatch of `[0-9a-f]{64}`.
- `limitations` is an exact builtin list of exact builtin str entries in the exact order above.
- Subclasses are rejected where exact builtin types are required.
- Duplicate JSON object keys are rejected.
- Canonical serialization is `json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("utf-8")`.
- The canonical bytes have no trailing newline.
- Accepted serialized bytes must equal that canonical re-encoding.
- The CSAR preimage is the canonical five-field object excluding `association_digest_csar_v0`.

## Frozen receiver prerequisite

Any future receiver receipt that embeds CSAR-v0:

- embeds exactly one complete six-field CSAR record inside self-digest coverage
- always has the original R4 claim dict and the original presented subject bytes at creation
- always runs full recomputation at creation
- requires exact equality with the embedded six-field record
- fails closed when an original input is missing
- fails closed on mismatch
- never treats structural consistency alone as authorization for receiver creation
- does not accept digest-only embedding
- gains no success, result, or authority meaning from CSAR presence
- may replay a record, and replay is not freshness
- leaves historical CLOSED receipts unbound

This invariant is frozen. The future receiver receipt type, its name, and its complete self-digest design are a separate new scope.

## Frozen safe digest wording

Within the CSAR_RECORD domain, matching association digests are treated as matching CSAR record commitments under the assumed collision resistance of SHA-256. CSAR-v0 does not claim mathematical injectivity.

## Nonclaims

CSAR-v0 does not establish:

- creator identity
- creation time
- order
- pre-execution occurrence
- authenticity
- subject correctness
- primary-subject selection
- byte interpretation or logical-artifact identity
- claim truth
- support
- sufficiency
- completeness
- correspondence
- independence
- admission
- authority
- technical verification
- Human Final
- legacy untagged digest equivalence
- historical CLOSED-receipt binding
- freshness
- omission detection
- replacement detection
- post-hoc rebuild detection

Also:

- Replay is allowed.
- Limitations are declarations, not enforcement on other consumers.
- CSAR inherits accepted DSDS/R4 claim-body equivalences and does not add a second claim canonicalization.

## Frozen design golden vector

Claim input:

`{"schema_version":"r4.epistemic.claim.v1","claim_id":"c1","statement":"s","claim_kind":"EMPIRICAL","epistemic_status":"REPORTED","scope":"scope-text","authority":false}`

Presented subject:

single byte `0x61`

`claim_digest_csar_v0`:

`d7af1740ffeed7854b6da2568c2ffe3790ea76d9d3b84f094d97e2328fbbb2bf`

`subject_digest_csar_v0`:

`563fb5a4d734474c7b6e0c612ff117f379129a1eeccdaca8afecf8ade60919f1`

`association_digest_csar_v0`:

`3f2c6ecc95ae64bfa7f89f414d88aa5c03cd884541257660cd3417bf747b8204`

Canonical preimage text, 624 UTF-8 bytes, no trailing newline:

`{"authority":false,"claim_digest_csar_v0":"d7af1740ffeed7854b6da2568c2ffe3790ea76d9d3b84f094d97e2328fbbb2bf","limitations":["presented_bytes_only","not_support","not_sufficiency","not_completeness","not_truth","not_correspondence","not_independence","not_admission","not_authority","not_verification","not_human_final","not_creator_time_or_order","not_legacy_digest_equivalence","not_historical_closed_receipt_binding","omission_not_detected_here","not_freshness","not_replacement_or_post_hoc_detection"],"schema_version":"csar.v0","subject_digest_csar_v0":"563fb5a4d734474c7b6e0c612ff117f379129a1eeccdaca8afecf8ade60919f1"}`

Canonical six-field record text, 720 UTF-8 bytes, no trailing newline:

`{"association_digest_csar_v0":"3f2c6ecc95ae64bfa7f89f414d88aa5c03cd884541257660cd3417bf747b8204","authority":false,"claim_digest_csar_v0":"d7af1740ffeed7854b6da2568c2ffe3790ea76d9d3b84f094d97e2328fbbb2bf","limitations":["presented_bytes_only","not_support","not_sufficiency","not_completeness","not_truth","not_correspondence","not_independence","not_admission","not_authority","not_verification","not_human_final","not_creator_time_or_order","not_legacy_digest_equivalence","not_historical_closed_receipt_binding","omission_not_detected_here","not_freshness","not_replacement_or_post_hoc_detection"],"schema_version":"csar.v0","subject_digest_csar_v0":"563fb5a4d734474c7b6e0c612ff117f379129a1eeccdaca8afecf8ade60919f1"}`

The prior adversarial probe value beginning `2dcf866c` is not the golden vector.

## Implementation gate

CSAR-v0 implementation remains blocked until a separate additive receiver scope freezes:

- receipt type and name
- exactly-one full CSAR record embedding
- self-digest coverage
- mandatory original inputs
- mandatory full recomputation
- fail-closed missing and mismatch behavior
- result semantics independent of CSAR
- historical CLOSED receipts unbound

## Boundary

This design freeze does not authorize CSAR implementation, a receiver implementation, admission, authority, signatures, or EBD integration.

Unchanged CLOSED boundaries:

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
- no public push
- no private push

## Change rule

Any future change to this frozen CSAR-v0 design is a new scope and must not silently rewrite this record.

## Push status

NO. No public or remote push is authorized by this record.
