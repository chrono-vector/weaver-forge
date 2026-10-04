# Association Carriage Digest v0 — Human Design Freeze

Date:
2026-10-04

Design freeze:
HUMAN_DESIGN_FREEZE_ACCEPTED

This document records a Human Design Freeze decision explicitly made by the human authority. It does not record an AI acceptance decision. It is not implementation acceptance and it is not a Human Final for an implementation.

Scope:
Association Carriage Digest v0 (ACD-v0)

Package:
association_carriage_digest_v0

Implementation status:
NOT_AUTHORIZED

Human decision date:
2026-10-04

Repository:
C:\dev\Weaver\weaver-forge-r4

Base HEAD before record:
ba165499660d264e892576d8d677eea830763922

Implementation remains not authorized until a separate implementation batch is explicitly started and later reviewed.

## Frozen namespace

Code-owned ASCII tag:
`weaver.acr.digest.v0`

DST:
the ASCII bytes of `weaver.acr.digest.v0` followed by one NUL byte.

DST hex:
`7765617665722e6163722e6469676573742e763000`

There is no registry, no caller-selected domain, no domain-id slot, no prefix argument, and no expected-digest argument.

ACD-v0 does not extend, replace, or version the CLOSED DSDS-v0 registry.

## Frozen public API

Export exactly:

- `AssociationCarriageDigestError`
- `digest_association_carriage_preimage(preimage: bytes) -> str`

The digest function takes exactly one argument: preimage bytes.

There is no public `DOMAINS`, no public `PREFIX`, and no public generic domain-separated digest. No public or private helper may accept a caller-selected domain or prefix. A private helper, if any, must retain the same one-preimage semantic surface.

## Frozen preimage contract

- `type(preimage) is bytes`
- `len(preimage) >= 1`
- reject bytes subclasses
- reject bytearray
- reject memoryview
- reject str
- reject every other type
- reject empty bytes before hashing

ACD-v0 hashes exact bytes only. It does not parse, inspect, canonicalize, or repair JSON. Future ACR-v0 owns receipt preimage construction and canonicalization.

## Frozen digest construction

Digest input:
DST concatenated with the exact preimage bytes.

Digest:
SHA-256

Return:
lowercase hexadecimal SHA-256

The NUL delimiter is retained as fixed framing. No length prefix is added.

## Frozen error model

One failure code:
`ACD_PREIMAGE_REJECTED`

Exact-bytes and type failure message:
`preimage must be exact bytes`

Empty failure message:
`preimage is empty`

There is no success status. The successful return is only the lowercase digest string. This vocabulary does not use pass, valid, verified, or accepted.

## Frozen safe semantics

The same code-owned tag and the same exact preimage bytes produce the same lowercase SHA-256.

Within this tag, matching digests are treated as matching preimage commitments under the assumed collision resistance of SHA-256.

ACD-v0 does not claim mathematical injectivity.

An ACD-v0 digest is a separate semantic value class from:

- DSDS-v0 digests
- untagged canonical_digest
- file SHA-256
- other legacy receipt digests

## Frozen nonclaims

ACD-v0 does not establish:

- ACR schema correctness
- CSAR correctness
- CSAR reproduction
- creator identity
- creation time
- order
- pre-execution occurrence
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
- freshness
- non-replay
- external anchoring
- historical CLOSED-receipt binding
- equivalence with any other digest family
- proof that a receipt was created

The function sees bytes only.

## Frozen golden vector 1

Preimage:
single byte `0x61`

DST:
`weaver.acr.digest.v0` plus one NUL byte

Expected digest:
`686a6035076c8087092763cc4f069045f16ff767277fdcb4f7d7d2ee1a05f5fe`

Python hashlib and .NET SHA256 independently agreed on this design vector before this Human Design Freeze.

## Frozen golden vector 2

This vector is a digest-layer fixture only. It is not an ACR-v0 schema freeze. It commits to the exact 1346 UTF-8 preimage bytes below, with no trailing newline. If later ACR design changes, this vector does not move.

Expected digest:
`bdd4a8cfb4e319547a322e505c8e525de8d09cf58ec9880b8b719b0fedbe00e2`

Exact fixture text:

`{"authority":false,"csar_record":{"association_digest_csar_v0":"3f2c6ecc95ae64bfa7f89f414d88aa5c03cd884541257660cd3417bf747b8204","authority":false,"claim_digest_csar_v0":"d7af1740ffeed7854b6da2568c2ffe3790ea76d9d3b84f094d97e2328fbbb2bf","limitations":["presented_bytes_only","not_support","not_sufficiency","not_completeness","not_truth","not_correspondence","not_independence","not_admission","not_authority","not_verification","not_human_final","not_creator_time_or_order","not_legacy_digest_equivalence","not_historical_closed_receipt_binding","omission_not_detected_here","not_freshness","not_replacement_or_post_hoc_detection"],"schema_version":"csar.v0","subject_digest_csar_v0":"563fb5a4d734474c7b6e0c612ff117f379129a1eeccdaca8afecf8ade60919f1"},"limitations":["carries_exactly_one_nested_csar_v0","structural_consistency_is_not_reproduction","originals_not_retained","not_creator_time_or_order","not_pre_execution_occurrence","not_subject_correctness","not_truth","not_support","not_sufficiency","not_completeness","not_correspondence","not_independence","not_admission","not_authority","not_verification","not_human_final","not_freshness","replay_not_distinguished","not_external_anchor","not_historical_closed_receipt_binding","not_execution_success","not_legacy_digest_equivalence"],"schema_version":"association_carriage_receipt.v0"}`

Python hashlib and .NET SHA256 agreed on this exact fixture.

## Rejected alternatives

These constructions are not ACD-v0 golden vectors:

- `weaver.digest.v1:ASSOCIATION_CARRIAGE_RECEIPT`
- `weaver.digest.acr.v0:RECEIPT`
- DSDS-v0 `CSAR_RECORD`
- untagged canonical_digest
- untagged or file SHA-256

Prior candidate and probe outputs from those constructions are not ACD-v0 golden vectors.

## Boundary

This design freeze does not authorize ACD-v0 implementation, ACR-v0 implementation, CSAR-v0 implementation, or any change to a CLOSED scope.

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
- CSAR-v0 Human Design Freeze unchanged
- no public push
- no private push

## Change rule

Any future change to this frozen ACD-v0 design is a new scope and must not silently rewrite this record.

## Push status

NO. No public or remote push is authorized by this record.
