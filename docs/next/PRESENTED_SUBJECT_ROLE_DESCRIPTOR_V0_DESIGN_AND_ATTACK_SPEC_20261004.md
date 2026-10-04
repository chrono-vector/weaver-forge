# Presented-Subject Role Descriptor v0 — Design Candidate and Attack Spec

Date:
2026-10-04

Design status:
CANDIDATE / AWAITING HUMAN DESIGN FREEZE

This document is not a Human Design Freeze. It does not authorize implementation. It does not record a human acceptance decision.

Repository:
C:\dev\Weaver\weaver-forge-r4

Base HEAD:
b0bd535b12ac4dde5639ecd49a78eb345dba9190

Asked scopes that this candidate does not freeze:

- A. Claim–Evidence Compatibility Receipt v0
- B. Claim Support Bound v0

Recommended next scope:
Presented-Subject Role Descriptor v0 (PSRD-v0)

DESIGN_STATUS for the asked compatibility and support scopes:
PREREQUISITE_REQUIRED

## Why A and B are not the next freeze

CLOSED prerequisites now bind one R4 claim body to one presented subject and carry that association. They still do not represent evidence identity, evidence type, or evidence-set selection.

Repository facts used for this decision:

- R4 claim bodies are `r4.epistemic.claim.v1`. `digest_r4_claim_body` commits to `claim_id`, `statement`, `claim_kind`, `epistemic_status`, `scope`, `authority`, `evidence_refs`, `provenance_refs`, `notes`, and the optional `workflow_state` / `extra` shapes allowed by DSDS-v0. `claim_kind` is the closed set `DOCUMENT_IDENTITY`, `FORMAL`, `IMPLEMENTATION`, `EMPIRICAL`, `NORMATIVE`, `SYMBOLIC`, `HISTORICAL`. `epistemic_status` is the closed set `REPORTED`, `SPECIFIED`, `OBSERVED`, `REPRODUCED`, `VERIFIED_SCOPE`, `AMBIGUOUS`, `UNRESOLVED`. `evidence_refs` and `provenance_refs` are opaque caller strings. DSDS sorts and dedupes them. That is not a binding from those strings to presented bytes.
- `digest_presented_subject_bytes` commits to nonempty exact bytes and no path, text, or archive decoding. The subject has no kind, media, schema, or identifier separate from those bytes.
- CSAR-v0 stores `claim_digest_csar_v0` and `subject_digest_csar_v0` plus code-owned limitations that include `presented_bytes_only`, `not_support`, and `omission_not_detected_here`. It retains neither the claim nor the subject. It does not interpret the subject bytes.
- ACR-v0 carries exactly one complete CSAR and an ACD receipt digest. It retains neither original. Its limitations include `not_support`, `replay_not_distinguished`, and `not_historical_closed_receipt_binding`.
- DSDS-v0 domains are only `R4_CLAIM_BODY`, `PRESENTED_SUBJECT_BYTES`, and `CSAR_RECORD`. ACD-v0 is only the carriage tag `weaver.acr.digest.v0`.
- EBD-v0 relations are only `DEPENDS_ON`, `BOUNDS`, `SUCCESSOR_OF`, `CITES`, and `CONTRADICTS`. `SUPPORTS` and `VERIFIES` are forbidden. `GRAPH_COMPLETE` means only that schema-derived required digest references resolve to body-backed nodes.
- Recovery Execution Receipt v0 has a private pre-state `evidence_kind` set: `ARTIFACT`, `CONFIG`, `FREEZE_SHA256SUMS`, `CAMPAIGN_INTEGRITY`, `OTHER_BOUNDED`. That set is part of a CLOSED receipt. It is not a general evidence taxonomy.

A compatibility receipt would need a frozen rule from a claim kind to an evidence kind. No CLOSED evidence kind exists for presented bytes. A rule that accepts every byte string for every claim kind would make the digest decorative. A rule that treats the association as compatibility would rename CSAR and would not be distinguishable from support. Caller-chosen subjects and `evidence_refs` still omit contradicting material. Explicit limitations would not make a compatibility or support tag safe, because the tag itself would be the misleading machine result.

B is not available for the same reason. EBD already refuses `SUPPORTS`. A support bound over a caller-selected subject or ref list cannot show that omitted evidence was considered. This candidate does not create a support predicate, a lower bound, or an evidence set.

The smallest next machine question is therefore not compatibility and not support. It is a single-subject role declaration that does not take a claim.

## Machine question

Does this descriptor commit the one code-owned role `UNINTERPRETED_PRESENTED_BYTES` to the CLOSED presented-subject digest of these exact supplied bytes?

The question is structural and reproductive only. It does not ask whether the bytes are relevant, sufficient, complete, true, independent, fresh, admissible, or supportive.

## Why this is minimal

PSRD-v0 adds one commitment that the CLOSED layers do not make: the subject digest is tied to one code-owned role and to a code-owned limitation list, under a new tag that is neither DSDS nor ACD.

It adds no claim input, no evidence set, no caller-chosen role, no second identifier, and no relation edge. A later compatibility scope would be a new version if a human later freezes more roles. v0 must not grow those roles silently.

## Exact record

All six fields are required. There is no optional, null, default, alias, or extra field.

1. `schema_version` is the exact builtin str `presented_subject_role_descriptor.v0`.
2. `authority` is the exact builtin bool `False`.
3. `presented_subject_role` is the exact builtin str `UNINTERPRETED_PRESENTED_BYTES`.
4. `subject_digest_psrd_v0` is the exact builtin str returned by CLOSED `digest_presented_subject_bytes`.
5. `limitations` is the exact code-owned list below, in this order.
6. `descriptor_digest_psrd_v0` is the exact builtin str matching `[0-9a-f]{64}` and equal to the PSRD tag digest of the canonical five-field preimage.

The preimage excludes `descriptor_digest_psrd_v0`. Its members are `schema_version`, `authority`, `presented_subject_role`, `subject_digest_psrd_v0`, and `limitations`.

## Exact types

- The record is an exact builtin dict.
- Every key is an exact builtin str.
- `authority` is an exact builtin bool, and that value is `False`. `0` is rejected.
- Role, schema, both digests, and every limitation element are exact builtin str values. `str` subclasses are rejected.
- `limitations` is an exact builtin list. Subclasses of `list` are rejected.
- The creation subject is exact builtin `bytes`. `bytearray`, `memoryview`, and `bytes` subclasses are rejected.
- Serialized input is exact builtin `bytes`.

## Closed registry

`presented_subject_role` has one value:

- `UNINTERPRETED_PRESENTED_BYTES`

The following are not members of this registry and must be rejected if supplied as the role, even when the descriptor digest is recomputed:

- R4 `claim_kind` values, including `EMPIRICAL`
- EBD node kinds and relations, including `RECEIPT`, `CLAIM`, `ARTIFACT`, `EXTERNAL_REF`, `CITES`, `CONTRADICTS`, and `SUPPORTS`
- RER pre-state kinds, including `ARTIFACT`, `CONFIG`, `FREEZE_SHA256SUMS`, `CAMPAIGN_INTEGRITY`, and `OTHER_BOUNDED`
- free strings such as `COMPATIBLE`, `SUPPORTED`, or `TEXT`

Creation does not accept a role argument. The producer inserts the one code-owned value. Role substitution is a structural and parse attack, not a creation option.

## Limitations

Exact order:

1. `uninterpreted_presented_bytes_only`
2. `role_not_inferred_from_bytes`
3. `not_evidence_selection`
4. `not_compatibility`
5. `not_support`
6. `not_sufficiency`
7. `not_completeness`
8. `not_truth`
9. `not_correspondence`
10. `not_independence`
11. `not_admission`
12. `not_authority`
13. `not_verification`
14. `not_human_final`
15. `not_claim_binding`
16. `not_omission_detection`
17. `not_contradiction_detection`
18. `not_duplicate_detection`
19. `not_order`
20. `not_replay_distinction`
21. `not_freshness`
22. `not_external_anchor`
23. `not_self_production_detection`
24. `not_relevance`
25. `not_creator_time_or_order`
26. `not_legacy_digest_equivalence`
27. `not_historical_closed_receipt_binding`
28. `not_rer_evidence_kind`
29. `not_ebd_relation`
30. `originals_not_retained`

The list is a hashed declaration. It does not itself inspect other evidence, other claims, or the world.

## Canonicalization

Canonical serialization is `json.dumps(object, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("utf-8")`.

The canonical bytes have no trailing newline.

This rule applies to the five-field preimage and to the six-field record.

Strict serialized-byte acceptance compares the original undecoded raw bytes with the canonical UTF-8 re-encoding. BOM, UTF-16, whitespace, insertion order, a trailing newline, noncanonical escapes, duplicate keys, extra or missing fields, wrong exact types or subclasses, a wrong role, wrong limitations or order, and malformed digests fail closed.

An insertion-order encoding of the same values has the same byte length and is not canonical.

## Digest and binding

`subject_digest_psrd_v0` is only `digest_presented_subject_bytes(subject)`. Empty bytes fail through that CLOSED function. PSRD does not reimplement that hash.

`descriptor_digest_psrd_v0` is SHA-256 over the code-owned tag `weaver.psrd.digest.v0`, one NUL byte, and the canonical five-field preimage. The tag is not a DSDS domain and not the ACD tag. The implementation keeps the tag private. The public API has no domain, prefix, tag, or expected-digest argument.

The descriptor digest is a separate value from:

- the presented-subject digest
- DSDS `R4_CLAIM_BODY`, `PRESENTED_SUBJECT_BYTES`, and `CSAR_RECORD` over the same preimage
- ACD `digest_association_carriage_preimage` over the same preimage
- untagged SHA-256 of the preimage or of the full record
- legacy `canonical_digest`

Matching descriptor digests mean the same tag and the same preimage bytes under assumed SHA-256 collision resistance. PSRD-v0 claims no mathematical injectivity.

For the same subject bytes, `subject_digest_psrd_v0` equals the DSDS presented-subject digest and may equal a CSAR `subject_digest_csar_v0`. That equality is the shared CLOSED function. It is not a claim binding, not a CSAR embedding, and not legacy-digest equivalence.

## Result tags

Success tags, exact builtin str, not a bool:

- `PSRD_STRUCTURALLY_CONSISTENT`
- `PSRD_REPRODUCED_FROM_SUPPLIED_INPUTS`

Closed failure code:

- `PSRD_REJECTED`

`PSRD_STRUCTURALLY_CONSISTENT` consults no subject bytes. It checks the six-field schema, exact types, the one role, the limitation list and order, both digest syntaxes, and equality of `descriptor_digest_psrd_v0` with the recomputed tag digest.

`PSRD_REPRODUCED_FROM_SUPPLIED_INPUTS` requires the structural tag's conditions, recomputation from the supplied subject bytes, and exact six-field equality. It is supplied-input reproduction only. It is not independent reproduction.

The machine vocabulary does not use SUPPORTED, SUFFICIENT, TRUE, VERIFIED, ADMITTED, AUTHORITATIVE, COMPLETE, INDEPENDENT, FRESH, BEST_EVIDENCE, WINNER, HUMAN_ACCEPTED, PASS, VALID, or ACCEPTED.

## Nonclaims

PSRD-v0 does not establish compatibility, support, sufficiency, completeness, truth, correspondence, independence, admission, authority, verification, Human Final, claim binding, evidence selection, omission detection, contradiction detection, duplicate detection, order, replay distinction, freshness, external anchoring, self-production detection, relevance, creator identity, creation time, byte interpretation, historical CLOSED-receipt binding, or legacy digest equivalence.

A descriptor is not evidence admission. A role is not a classification inferred from the bytes. PASS is not authority. Evidence is not authority. A receipt is not admission. Citation is not verification.

## Creation contract

The only input is one presented subject as exact builtin bytes.

Creation accepts no claim, claim digest, subject digest, role, limitations, authority, domain, prefix, path, filename, evidence set, or evidence identifier.

Sequence:

1. Reject a subject that is not exact builtin bytes.
2. Compute `subject_digest_psrd_v0` only with `digest_presented_subject_bytes`.
3. Build the five-field preimage with the code-owned schema, `authority=False`, the one role, that digest, and `list` of the code-owned limitations.
4. Canonically serialize the preimage.
5. Compute `descriptor_digest_psrd_v0` with the private PSRD tag.
6. Emit one six-field record.

Any type failure, empty subject, or digest failure emits no record.

## Parser contract

`parse` accepts one exact byte string.

1. Reject non-bytes.
2. Reject undecodable UTF-8.
3. Reject JSON that is not one object, and reject duplicate keys.
4. Run the structural check.
5. Require the raw bytes to equal the canonical re-encoding.

Structural success of a parsed object does not accept noncanonical bytes.

## Reproduction

Reproduction inputs are the record and the original subject bytes.

1. Require `PSRD_STRUCTURALLY_CONSISTENT`.
2. Recompute with the creation contract.
3. Require exact six-field equality.

Comparing only `subject_digest_psrd_v0` is not reproduction. Structural consistency does not authorize a caller to skip reproduction, and reproduction is not available from the record alone.

Original bytes are not retained in the record.

## Caller-selection boundary

Detected and rejected:

- a role outside the one-value registry
- a caller-supplied role, claim, claim kind, digest, path, or evidence identifier argument
- more than one subject, including a one-item list and a longer list
- an empty subject
- an extra field that could carry a second identifier, a contradiction flag, or a claim kind

Explicitly not detected:

- cherry-picked other evidence
- omitted contradicting evidence
- duplicated evidence outside this one subject
- reordered evidence
- replay
- the same bytes named by another system
- evidence time relative to a claim
- absence of an external anchor
- self-produced bytes
- semantic irrelevance of the bytes

v0 does not solve those by assertion. It has no set and no claim, so it cannot return a result that looks like a selected evidence set.

## Contradiction boundary

PSRD-v0 has no contradiction field and no second subject. It cannot drop, rank, or resolve a contradiction. EBD `CONTRADICTS` remains the CLOSED annotation edge and is not redefined. `ContradictionPresent` is not a winner, and this record does not say that a contradiction is absent.

## Duplication, order, and replay

One subject has no order. Replaying the same bytes reproduces the same descriptor and is not freshness. Two descriptors are outside this record. Duplicate detection across descriptors is not a v0 result.

## Legacy and CLOSED-scope separation

This candidate does not modify or reinterpret R3, R4, WVMA-V1, Tested-Envelope Receipt v0, Recovery Preflight v0, Independent Verification Preflight v0, Conducting Receipt v0, Recovery Execution Receipt v0, Evidence Binding DAG v0, DSDS-v0, ACD-v0, CSAR-v0, or ACR-v0.

It does not embed a CSAR or an ACR. It does not cite historical CLOSED receipts as evidence. It does not treat RER `evidence_kind`, EBD node kinds, or R4 `evidence_refs` as this role registry.

## Public API shape

Package name for a future implementation, not created in this batch:

`presented_subject_role_descriptor_v0`

Functions:

- `produce_psrd(subject: bytes) -> dict`
- `parse_psrd(raw: bytes) -> dict`
- `psrd_structurally_consistent(record: dict) -> str`
- `psrd_reproduced_from_supplied_inputs(record: dict, subject: bytes) -> str`

Closed error type: `PsrdError`, code `PSRD_REJECTED`.

No public digest function, tag, domain registry, or canonicalizer. The private tag helper accepts only the preimage bytes it already built.

## Candidate golden vector

Subject: the single byte `0x61`.

`subject_digest_psrd_v0`, from CLOSED `digest_presented_subject_bytes`:

`563fb5a4d734474c7b6e0c612ff117f379129a1eeccdaca8afecf8ade60919f1`

Canonical five-field preimage: 917 UTF-8 bytes, no CR, no trailing newline.

Exact preimage text:

`{"authority":false,"limitations":["uninterpreted_presented_bytes_only","role_not_inferred_from_bytes","not_evidence_selection","not_compatibility","not_support","not_sufficiency","not_completeness","not_truth","not_correspondence","not_independence","not_admission","not_authority","not_verification","not_human_final","not_claim_binding","not_omission_detection","not_contradiction_detection","not_duplicate_detection","not_order","not_replay_distinction","not_freshness","not_external_anchor","not_self_production_detection","not_relevance","not_creator_time_or_order","not_legacy_digest_equivalence","not_historical_closed_receipt_binding","not_rer_evidence_kind","not_ebd_relation","originals_not_retained"],"presented_subject_role":"UNINTERPRETED_PRESENTED_BYTES","schema_version":"presented_subject_role_descriptor.v0","subject_digest_psrd_v0":"563fb5a4d734474c7b6e0c612ff117f379129a1eeccdaca8afecf8ade60919f1"}`

Candidate descriptor digest:

`b586f3c45f548220b75b7c00bfed1e0e7b9f713a077d9d53f9534bf02eaeac80`

Complete canonical six-field record: 1012 UTF-8 bytes, no trailing newline.

Exact record text:

`{"authority":false,"descriptor_digest_psrd_v0":"b586f3c45f548220b75b7c00bfed1e0e7b9f713a077d9d53f9534bf02eaeac80","limitations":["uninterpreted_presented_bytes_only","role_not_inferred_from_bytes","not_evidence_selection","not_compatibility","not_support","not_sufficiency","not_completeness","not_truth","not_correspondence","not_independence","not_admission","not_authority","not_verification","not_human_final","not_claim_binding","not_omission_detection","not_contradiction_detection","not_duplicate_detection","not_order","not_replay_distinction","not_freshness","not_external_anchor","not_self_production_detection","not_relevance","not_creator_time_or_order","not_legacy_digest_equivalence","not_historical_closed_receipt_binding","not_rer_evidence_kind","not_ebd_relation","originals_not_retained"],"presented_subject_role":"UNINTERPRETED_PRESENTED_BYTES","schema_version":"presented_subject_role_descriptor.v0","subject_digest_psrd_v0":"563fb5a4d734474c7b6e0c612ff117f379129a1eeccdaca8afecf8ade60919f1"}`

Ordinary SHA-256 fingerprint of those exact record bytes:

`5dc9cf4907c977de3f3672eecb19dbb10adb4ae72069778a71aef2f8d4bb034d`

This fingerprint is not the descriptor digest.

Rejected substitutes of the 917-byte preimage, none of which is the descriptor digest:

- untagged SHA-256: `0402643c4c28721f1a995e3759dbd55fa4ee5161ee7a13c1000afc8ed236e841`
- DSDS `CSAR_RECORD`: `d557763e023e4026da108ef8e025095062beb689b0e9615ba7815959b100dafa`
- DSDS `PRESENTED_SUBJECT_BYTES`: `5dd3393219a8e54c6676f6808f850fce64a9be4d894d9c37b7714b7c762c6df0`
- DSDS `R4_CLAIM_BODY`: `538cdf46933a831c58138cfe4defdc14057c9c724e4cd3ed253df17e5a06c0de`
- ACD-v0: `836f7eca54aa147a21760d64c524df51968497d0184d518fc8ac8963053783c0`

These values are candidate vectors computed against CLOSED digest functions and the tag defined above. Human Design Freeze has not accepted them.

## Implementation dependency gate

A future implementation may use CLOSED `digest_presented_subject_bytes` and `DomainSeparatedDigestError` only. It must not change DSDS, ACD, CSAR, ACR, EBD, or RER.

No implementation is authorized by this candidate. Authorization requires a later Human Design Freeze of this candidate, or of a revised candidate. The future batch, once authorized, is one implementation plus the attack matrix below, then one independent read-only review. This document does not schedule Human Final.

## Human Design Freeze readiness

The PSRD-v0 candidate is internally coherent and is waiting for a human design-freeze decision.

A and B are not ready for that decision. They remain blocked on this missing single-subject role commitment, and they remain blocked on omission and contradiction, which v0 does not claim to close.

## Attack and mutation spec

The future implementation batch must run this matrix before independent review. Each field attack recomputes `descriptor_digest_psrd_v0` with the private PSRD tag over the mutated five-field preimage when the mutation changes that preimage, then shows the stored digest matches that recomputation, then expects rejection for the named rule rather than for a stale digest. The subject byte remains `0x61` unless a row says otherwise. The claim is never an input.

Expected closed failure is `PsrdError` with code `PSRD_REJECTED`, and no record is returned on creation failure. Do not use a support, authority, admission, or verification tag as a success result.

### PSRD-M01

Attack: `authority=0`, descriptor digest recomputed.
Expected: structural rejection, and reproduction from `b"a"` rejection.
Invariant: exact `False`, not numeric zero.
Digest note: JSON `0` and `false` differ, so the recomputed digest differs from the golden descriptor digest.

### PSRD-M02

Attack: `authority=True`, descriptor digest recomputed.
Expected: structural rejection.
Invariant: authority cannot be turned on.
Digest note: same recomputation rule as M01.

### PSRD-M03

Attack: `presented_subject_role` is a `str` subclass whose text is `UNINTERPRETED_PRESENTED_BYTES`, descriptor digest recomputed.
Expected: structural rejection.
Invariant: exact builtin str for the role.
Digest note: the subclass serializes as the same text, so the digest stays the golden digest. Rejection must not depend on a digest mismatch.

### PSRD-M04

Attack: limitations element 0 is a `str` subclass with `__eq__` always true and text `authority_granted`, descriptor digest recomputed.
Expected: structural rejection. Reproduction from `b"a"` also rejects.
Invariant: exact limitation strings, not equality-lying subclasses.
Digest note: the recomputed digest differs from the golden digest because the text differs. Parse of the canonical bytes still rejects after JSON loads a builtin str.

### PSRD-M05

Attack: `schema_version` is a `str` subclass of the exact schema text, descriptor digest recomputed.
Expected: structural rejection.
Invariant: exact builtin schema string.
Digest note: serialized text matches, so the digest remains golden.

### PSRD-M06

Attack: `descriptor_digest_psrd_v0` is a `str` subclass of the golden digest.
Expected: structural rejection as malformed digest text.
Invariant: exact builtin digest string. A lowercase conversion must not accept the subclass.

### PSRD-M07

Attack: extra key `note` or `evidence_id`, five-field digest recomputed and unchanged.
Expected: structural rejection for the key set.
Invariant: no second identifier and no extra field.
Digest note: the extra key is outside the preimage, so a stale-digest check would miss it.

### PSRD-M08

Attack: delete `limitations`.
Expected: structural rejection for the key set.
Invariant: all six fields are required.

### PSRD-M09

Attack: reverse `limitations`, descriptor digest recomputed.
Expected: structural rejection and reproduction rejection.
Invariant: limitation order.
Digest note: the recomputed digest differs from the golden digest.

### PSRD-M10

Attack: duplicate `schema_version` in the raw JSON object.
Expected: parse rejection for a duplicate key.
Invariant: strict JSON objects.

### PSRD-M11

Attack: whitespace, trailing newline, `\u` escape of an unchanged limitation character, BOM, and UTF-16, each applied to the golden record bytes.
Expected: parse rejection. Where `json.loads` still yields the same values, structural consistency of that object succeeds and the byte check fails.
Invariant: raw canonical bytes.

### PSRD-M12

Attack: one insertion-order serialization of the golden values with the same 1012-byte length.
Expected: structural consistency of the parsed object succeeds, and parse rejects the raw bytes.
Invariant: sort-key canonicalization, not length.

### PSRD-M13

Attack: store the untagged SHA-256 of the golden preimage as `descriptor_digest_psrd_v0`.
Expected: structural rejection.
Invariant: the private PSRD tag is not raw SHA-256.
Digest note: the substitute is the 64-hex value listed above, so syntax is well formed.

### PSRD-M14

Attack: store the DSDS `CSAR_RECORD` digest of the golden preimage as `descriptor_digest_psrd_v0`.
Expected: structural rejection.
Invariant: no CSAR domain reuse.

### PSRD-M15

Attack: store the DSDS `PRESENTED_SUBJECT_BYTES` digest of the golden preimage as `descriptor_digest_psrd_v0`.
Expected: structural rejection.
Invariant: the subject-byte domain over the preimage is not the descriptor digest.

### PSRD-M16

Attack: store the DSDS `R4_CLAIM_BODY` digest of the golden preimage as `descriptor_digest_psrd_v0`.
Expected: structural rejection.
Invariant: a claim-body domain does not certify this descriptor.

### PSRD-M17

Attack: store the ACD digest of the golden preimage as `descriptor_digest_psrd_v0`.
Expected: structural rejection.
Invariant: carriage digest is not this descriptor digest.

### PSRD-M18

Attack: store `subject_digest_psrd_v0` into `descriptor_digest_psrd_v0`.
Expected: structural rejection.
Invariant: the subject digest is not the descriptor digest.

### PSRD-M19

Attack: compare the ordinary SHA-256 fingerprint of the golden record with `descriptor_digest_psrd_v0`, and inspect the implementation for `canonical_digest`.
Expected: the fingerprint differs, and the implementation does not call `canonical_digest`.
Invariant: no legacy untagged digest equivalence.

### PSRD-M20

Attack: call creation with an evidence set, `evidence_refs`, or an omission argument.
Expected: `TypeError`, and no record.
Invariant: omission and selection are not representable successes.

### PSRD-M21

Attack: pass a one-item list, a two-item list, and a tuple of subject bytes.
Expected: `PSRD_REJECTED`, no record.
Invariant: one exact byte string, so reorder and duplicate inputs have no acceptance path.

### PSRD-M22

Attack: the M07 `evidence_id` case, stated again as the multiple-identifier attack.
Expected: key-set rejection with a consistent five-field digest.
Invariant: the same bytes do not gain another identifier inside v0.

### PSRD-M23

Attack: pass a claim dict, a `claim_kind` keyword, and a record with extra `claim_kind`.
Expected: creation `TypeError` or `PSRD_REJECTED` with no record; structural rejection of the extra key.
Invariant: claim-kind substitution is outside the input contract.

### PSRD-M24

Attack: set `presented_subject_role` to `ARTIFACT`, `CONFIG`, `EMPIRICAL`, `RECEIPT`, `SUPPORTS`, and `COMPATIBLE`, each with a recomputed descriptor digest.
Expected: structural rejection for every substitute.
Invariant: CLOSED vocabularies and support words are not this registry.

### PSRD-M25

Attack: read both success results for the golden subject.
Expected: the two exact tags only. Neither is a bool. Neither text is a forbidden conclusion word.
Invariant: structural compatibility of this descriptor is not support, authority, admission, or verification.

### PSRD-M26

Attack: extra key `contradiction_present`, five-field digest unchanged.
Expected: structural rejection.
Invariant: a contradiction cannot be recorded or silently dropped here.

### PSRD-M27

Attack: `produce_psrd(b"")`.
Expected: `PSRD_REJECTED`, no record.
Invariant: empty input is not a descriptor. The failure may wrap the CLOSED empty-subject error.

### PSRD-M28

Attack: reproduction of a golden record whose `authority` was replaced with `0` and whose descriptor digest was left unchanged.
Expected: rejection.
Invariant: exact six-field reproduction, including the `False`/`0` distinction. Python equality alone would treat those records as equal.

### PSRD-M29

Attack: reproduction of a golden record whose descriptor digest is `0` repeated 64 times.
Expected: rejection.
Invariant: reproduction is not a subject-digest comparison alone.

### PSRD-M30

Attack: reproduction of a golden record whose limitations are reversed and whose descriptor digest is left unchanged.
Expected: rejection for the limitation rule.
Invariant: order is part of equality and of the structural gate.

### PSRD-M31

Attack: a record whose role is `ARTIFACT`, whose subject digest is still the golden subject digest, and whose descriptor digest was recomputed.
Expected: reproduction from `b"a"` rejects.
Invariant: a future mutant that checks only `subject_digest_psrd_v0` must fail this row, M28, and M30.

### PSRD-M32

Attack: parse the canonical bytes of the M01, M09, and M24 records.
Expected: each parse rejects.
Invariant: parse runs the structural gate. A canonical byte match is not enough.

### PSRD-M33

Attack: inspect public signatures and pass forbidden keywords including `domain`, `prefix`, `tag`, `digest`, `role`, `limitations`, `authority`, `path`, and `filename`.
Expected: creation parameters are exactly `subject`. Structural parameters are exactly `record`. Reproduction parameters are exactly `record` and `subject`. Forbidden keywords raise `TypeError`.
Invariant: no public generic selector.

### PSRD-M34

Attack: inspect the package exports, the module's public callables, and the error class.
Expected: exports are exactly the error type and the four functions above. No tag constant, domain registry, or generic digest callable is public. The error class has no hash method.
Invariant: no hidden package, class, or callable selector.

### PSRD-M35

Attack: uppercase the golden descriptor digest, and try short, long, and non-hex digests.
Expected: structural rejection as malformed digest text.
Invariant: lowercase syntax is checked before equality. Uppercase must not pass through `.lower()`.

### PSRD-M36

Attack: `bytearray`, `memoryview`, a `bytes` subclass, and a path string such as `C:/missing/subject.bin`.
Expected: `PSRD_REJECTED`, no record, and the cause is not `OSError`.
Invariant: no path read and no byte-like alias.

### PSRD-M37

Attack: structural check of the golden record without supplying the subject, and reproduction of a descriptor produced from `b"b"` using subject `b"a"`.
Expected: structural result is only `PSRD_STRUCTURALLY_CONSISTENT`. Reproduction from the other subject rejects. `b"b"` yields a different subject digest and a different descriptor digest.
Invariant: structural consistency is not reproduction, and the subject bytes are bound.

### PSRD-M38

Attack: on M01, M04, M09, and M24, assert that the rejection text is the field rule and does not say the descriptor digest failed to reproduce.
Expected: the named rule is reached.
Invariant: a consistent recomputed digest must not hide the intended failure and must not become a false pass.

Planned mutant count:
38

## Change rule

Any later addition of a role, a claim input, an evidence set, or a compatibility result is a new scope or version. It must not silently rewrite this candidate into Claim–Evidence Compatibility v0 or Claim Support Bound v0.

## Push status

NO. This candidate authorizes no public or private push.
