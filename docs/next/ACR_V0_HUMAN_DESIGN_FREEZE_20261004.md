# Association Carriage Receipt v0 — Human Design Freeze

Date:
2026-10-04

Design freeze:
HUMAN_DESIGN_FREEZE_ACCEPTED

This document records a Human Design Freeze decision explicitly made by the human authority. It does not record an AI acceptance decision. It is not implementation acceptance and it is not a Human Final for an implementation.

Scope:
Association Carriage Receipt v0 (ACR-v0)

schema_version:
`association_carriage_receipt.v0`

Implementation status:
NOT_AUTHORIZED

READY_FOR_IMPLEMENTATION:
NO

Next prerequisite:
CSAR-v0 implementation / Human Final

Human decision date:
2026-10-04

Repository:
C:\dev\Weaver\weaver-forge-r4

Base HEAD before record:
d17a17126176471a5d8b57cd58228991747205ef

The design is frozen. ACR-v0 implementation remains unauthorized and not ready. No CLOSED scope is changed or reinterpreted by this record.

## Frozen five-field schema

All five fields are required. The record has no optional, null, default, alias, or extra field.

1. `schema_version` is the exact builtin str `association_carriage_receipt.v0`.
2. `authority` is the exact builtin bool `False`.
3. `csar_record` is exactly one complete frozen six-field CSAR-v0 record.
4. `limitations`
5. `receipt_digest` is an exact builtin str matching `[0-9a-f]{64}` and equal to the CLOSED ACD-v0 digest of the canonical four-field preimage.

The embedded CSAR-v0 record remains the frozen six-field contract:

1. `schema_version` is the exact builtin str `csar.v0`.
2. `authority` is the exact builtin bool `False`.
3. `claim_digest_csar_v0`
4. `subject_digest_csar_v0`
5. `limitations`
6. `association_digest_csar_v0`

CSAR strict canonicalization, parse, and reproduction semantics remain frozen. `CSAR_STRUCTURALLY_CONSISTENT` and `CSAR_REPRODUCED_FROM_SUPPLIED_INPUTS` are not weakened or reinterpreted.

## Frozen limitations

Exact order:

1. `carries_exactly_one_nested_csar_v0`
2. `structural_consistency_is_not_reproduction`
3. `originals_not_retained`
4. `not_creator_time_or_order`
5. `not_pre_execution_occurrence`
6. `not_subject_correctness`
7. `not_truth`
8. `not_support`
9. `not_sufficiency`
10. `not_completeness`
11. `not_correspondence`
12. `not_independence`
13. `not_admission`
14. `not_authority`
15. `not_verification`
16. `not_human_final`
17. `not_freshness`
18. `replay_not_distinguished`
19. `not_external_anchor`
20. `not_historical_closed_receipt_binding`
21. `not_execution_success`
22. `not_legacy_digest_equivalence`

The limitations array is a hashed semantic declaration. It does not itself enforce those semantics.

## Frozen creation contract

Inputs are exactly:

- one original R4 claim dict
- one original presented-subject exact builtin bytes object
- one complete embedded CSAR-v0 record

Creation accepts no caller-provided claim digest, subject digest, association digest, receipt digest, limitations list, path, or filename.

Sequence:

1. Strictly parse and validate the supplied CSAR under frozen CSAR-v0.
2. Fully recompute the CSAR from the original claim dict and the original subject bytes using the frozen CSAR producer contract.
3. Require exact six-field equality.
4. Build the four-field ACR preimage: `schema_version`, `authority`, `csar_record`, `limitations`.
5. Canonically serialize that preimage.
6. Pass those exact non-empty builtin bytes to the CLOSED ACD-v0 public function `digest_association_carriage_preimage(preimage: bytes) -> str`.
7. Store the returned lowercase 64-hex string as `receipt_digest`.
8. Emit exactly one canonical five-field ACR record.

Any missing original, parse failure, recomputation failure, inequality, type failure, or canonicalization failure fails closed and emits no receipt.

Structural consistency never authorizes creation.

ACR retains neither the original claim dict nor the original subject bytes. ACR adds no second R4 claim canonicalizer.

## Frozen canonical JSON

Canonical serialization is `json.dumps(object, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("utf-8")`.

The canonical bytes have no trailing newline.

This rule applies to both:

- the four-field receipt-digest preimage
- the complete five-field serialized ACR record

Strict serialized-byte acceptance compares the original undecoded raw input bytes with the canonical UTF-8 re-encoding. The following fail closed:

- BOM
- UTF-16
- whitespace variants
- insertion-order alternatives
- a trailing newline
- noncanonical escapes
- duplicate keys
- extra or missing fields
- wrong exact builtin types or subclasses
- wrong limitations or order
- malformed digests
- invalid nested-CSAR forms

Insertion-order serialization is not accepted merely because its byte length matches.

## Frozen result vocabulary

`ACR_STRUCTURALLY_CONSISTENT` requires:

- the exact five-field schema
- exact builtin types
- the exact limitations list and order
- exactly one nested CSAR that is `CSAR_STRUCTURALLY_CONSISTENT` under frozen CSAR strict validation
- `receipt_digest` equal to the CLOSED ACD-v0 digest of the canonical four-field ACR preimage

Checking `receipt_digest` alone is insufficient.

`ACR_STRUCTURALLY_CONSISTENT` consults no originals and does not establish reproduction.

`ACR_REPRODUCED_FROM_SUPPLIED_INPUTS` requires:

- the original claim dict and the original subject bytes
- full frozen CSAR recomputation
- exact six-field equality with the nested CSAR
- all ACR structural conditions
- outer ACD digest reproduction

This is supplied-input reproduction only. It is not independent reproduction.

These results do not use a bool ok. The machine vocabulary does not use PASS, VALID, VERIFIED, or ACCEPTED.

## Frozen embedding

Exactly one complete six-field CSAR-v0 record is embedded. All six CSAR fields are covered by `receipt_digest`.

The following are invalid:

- zero or multiple nested CSAR records
- a digest-only CSAR reference
- a path or external reference
- a nested CSAR outside digest coverage

## Frozen ACD integration

The outer receipt digest uses only the CLOSED ACD-v0 public function `digest_association_carriage_preimage(preimage: bytes) -> str`.

ACR does not reproduce ACD hashing logic. The outer ACR digest does not use DSDS `CSAR_RECORD`, untagged `canonical_digest`, file SHA-256, or a legacy digest.

## Frozen safe semantics

Matching ACR receipt digests are matching ACR preimage commitments under the fixed ACD tag and the assumed collision resistance of SHA-256.

ACR-v0 claims no mathematical injectivity.

An ACR receipt digest remains a separate value class from a CSAR association digest, any other DSDS-v0 digest, untagged `canonical_digest`, file SHA-256, and legacy receipt digests.

## Frozen nonclaims

ACR-v0 does not establish:

- creator identity
- creation time
- order
- pre-execution occurrence
- subject correctness
- truth
- support
- sufficiency
- completeness
- correspondence
- independence
- admission
- authority
- technical verification
- Human Final
- freshness
- replay distinction
- external anchoring
- historical CLOSED-receipt binding
- execution success
- legacy digest equivalence
- post-hoc rebuild detection

Originals are not retained. Limitations are declarations, not enforcement by themselves.

## Runtime dependency gate

This Human Design Freeze does not require a CSAR implementation.

ACR-v0 implementation is not authorized.

Before ACR implementation can be authorized, the frozen CSAR-v0 parser, structural checker, and producer contract must have a reviewed Human-Final implementation available as the dependency.

ACR must not duplicate, fork, or independently reimplement CSAR producer or parser semantics.

Until then, `READY_FOR_IMPLEMENTATION` remains NO.

## Frozen golden vector

Inputs are the frozen CSAR-v0 golden claim dict and the presented subject byte `0x61`, together with the frozen 720-byte six-field CSAR record. The ACR record does not retain those inputs.

Canonical four-field preimage:
1346 UTF-8 bytes, no CR, no trailing newline.

Exact preimage text:

`{"authority":false,"csar_record":{"association_digest_csar_v0":"3f2c6ecc95ae64bfa7f89f414d88aa5c03cd884541257660cd3417bf747b8204","authority":false,"claim_digest_csar_v0":"d7af1740ffeed7854b6da2568c2ffe3790ea76d9d3b84f094d97e2328fbbb2bf","limitations":["presented_bytes_only","not_support","not_sufficiency","not_completeness","not_truth","not_correspondence","not_independence","not_admission","not_authority","not_verification","not_human_final","not_creator_time_or_order","not_legacy_digest_equivalence","not_historical_closed_receipt_binding","omission_not_detected_here","not_freshness","not_replacement_or_post_hoc_detection"],"schema_version":"csar.v0","subject_digest_csar_v0":"563fb5a4d734474c7b6e0c612ff117f379129a1eeccdaca8afecf8ade60919f1"},"limitations":["carries_exactly_one_nested_csar_v0","structural_consistency_is_not_reproduction","originals_not_retained","not_creator_time_or_order","not_pre_execution_occurrence","not_subject_correctness","not_truth","not_support","not_sufficiency","not_completeness","not_correspondence","not_independence","not_admission","not_authority","not_verification","not_human_final","not_freshness","replay_not_distinguished","not_external_anchor","not_historical_closed_receipt_binding","not_execution_success","not_legacy_digest_equivalence"],"schema_version":"association_carriage_receipt.v0"}`

ACR receipt digest:
`bdd4a8cfb4e319547a322e505c8e525de8d09cf58ec9880b8b719b0fedbe00e2`

Complete canonical five-field ACR record:
1430 UTF-8 bytes, no trailing newline.

Exact record text:

`{"authority":false,"csar_record":{"association_digest_csar_v0":"3f2c6ecc95ae64bfa7f89f414d88aa5c03cd884541257660cd3417bf747b8204","authority":false,"claim_digest_csar_v0":"d7af1740ffeed7854b6da2568c2ffe3790ea76d9d3b84f094d97e2328fbbb2bf","limitations":["presented_bytes_only","not_support","not_sufficiency","not_completeness","not_truth","not_correspondence","not_independence","not_admission","not_authority","not_verification","not_human_final","not_creator_time_or_order","not_legacy_digest_equivalence","not_historical_closed_receipt_binding","omission_not_detected_here","not_freshness","not_replacement_or_post_hoc_detection"],"schema_version":"csar.v0","subject_digest_csar_v0":"563fb5a4d734474c7b6e0c612ff117f379129a1eeccdaca8afecf8ade60919f1"},"limitations":["carries_exactly_one_nested_csar_v0","structural_consistency_is_not_reproduction","originals_not_retained","not_creator_time_or_order","not_pre_execution_occurrence","not_subject_correctness","not_truth","not_support","not_sufficiency","not_completeness","not_correspondence","not_independence","not_admission","not_authority","not_verification","not_human_final","not_freshness","replay_not_distinguished","not_external_anchor","not_historical_closed_receipt_binding","not_execution_success","not_legacy_digest_equivalence"],"receipt_digest":"bdd4a8cfb4e319547a322e505c8e525de8d09cf58ec9880b8b719b0fedbe00e2","schema_version":"association_carriage_receipt.v0"}`

Ordinary SHA-256 fingerprint of the exact complete canonical record bytes:
`1c00d03fb1e4430bde21fc7cc79ae93dd42fd2c3d26d4d56cd9467b9159ae1fe`

This ordinary SHA-256 is only a design-freeze byte fingerprint. It is not the ACR semantic receipt digest.

A rejected insertion-order serialization of this record has the same 1430-byte length, different bytes, and is not canonical.

Digest separation for the four-field preimage:

- ACD-v0: `bdd4a8cfb4e319547a322e505c8e525de8d09cf58ec9880b8b719b0fedbe00e2`
- untagged SHA-256: `251e9a7ca83bd9d0f44116a3f1782c491f9697e15c46190e29cee9aa84e239b7`
- DSDS `CSAR_RECORD`: `66946272d5bb6214dff312dbac3879562dec7a31bc77d605fefc6250cf79ae5e`

The untagged SHA-256 value and the DSDS `CSAR_RECORD` value are not ACR receipt digests.

The 1346-byte preimage is byte-identical to the CLOSED ACD-v0 digest-layer fixture 2. That fixture remains a digest-layer fixture. This record freezes the ACR golden vector. It does not move CLOSED ACD-v0.

## Review record

D1 design result:
DESIGN_FREEZE_CANDIDATE

D1 material findings:
NONE

D1 ready for Human Design Freeze:
YES

Initial independent review:
DEFER, only because the D1 candidate body was not available to the reviewer. That deferral was not a design rejection.

Targeted independent re-review with the D1 body:

- VERDICT: ACCEPT
- MATERIAL_FINDINGS: NONE
- RESULT_SEMANTICS_REVIEW: PASS
- PARSER_REVIEW: PASS
- FULL_RECORD_CANONICALIZATION: PASS
- LIMITATIONS_NONCLAIMS_REVIEW: PASS
- RUNTIME_DEPENDENCY_GATE: PASS
- INDEPENDENCE_WORDING: PASS
- GOLDEN_VECTOR: PASS
- CLOSED_SCOPE_SAFETY: PASS
- MISSING_BEFORE_HUMAN_DESIGN_FREEZE: NONE
- READY_FOR_HUMAN_DESIGN_FREEZE: YES
- READY_FOR_IMPLEMENTATION: NO

Nonmaterial reviewer clarifications incorporated into this freeze record:

- `receipt_digest` is explicitly lowercase 64-hex.
- Canonical serialized-byte comparison explicitly uses the raw input bytes against canonical re-encoding.
- The runtime dependency explicitly requires a reviewed Human-Final CSAR-v0 implementation.

These clarifications do not reopen or change CLOSED prerequisites.

## Boundary

This design freeze does not authorize ACR-v0 implementation, CSAR-v0 implementation, or any change to a CLOSED scope.

Unchanged boundaries:

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
- CSAR-v0 Human Design Freeze unchanged
- no public push
- no private push

## Change rule

Any future change to this frozen ACR-v0 design is a new scope and must not silently rewrite this record.

## Push status

NO. No public or remote push is authorized by this record.
