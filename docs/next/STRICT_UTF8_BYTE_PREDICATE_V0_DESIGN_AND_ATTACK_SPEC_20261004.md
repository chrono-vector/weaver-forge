# Strict UTF-8 Byte Predicate v0 — Design Candidate and Attack Spec

Date:
2026-10-04

Design status:
CANDIDATE / AWAITING HUMAN DESIGN FREEZE

This document is not a Human Design Freeze. It does not authorize implementation. It does not record a human acceptance decision.

Repository:
C:\dev\Weaver\weaver-forge-r4

Base HEAD:
0ef5aa657b84a8543e6b601539d56a8ae11d395a

Prior D0:
docs/next/EVIDENCE_KIND_DERIVATION_PREREQUISITE_D0_20261004.md

D0 remains in force. No CLOSED function derives an evidence kind. This candidate does not supply one.

## Recommended scope

Exact name:
Strict UTF-8 Byte Predicate v0 (SUBP-v0)

Package name for a future implementation, not created in this batch:
`strict_utf8_byte_predicate_v0`

Schema:
`strict_utf8_byte_predicate.v0`

Rejected alternatives:

- `OPAQUE_BYTES` restates CLOSED PSRD-v0. It adds no grammar fact.
- A multi-format registry, including UTF-8 plus JSON plus magic bytes, forces a winner among polyglots. v0 does not open that registry.
- Exact byte length is already fixed by the bytes a digest commits to. A length field is easy and is not a later-compatibility prerequisite.
- A strict JSON object predicate would be a new byte parser. The tree already has `canonical_dumps`, WVMA-V1 `canonical_bytes`, and the receipt-family `json.dumps` parameters. None of those is a parser of arbitrary presented bytes. Adding one would be a second canonicalization regime and would be easy to misread as a record or as evidence.

## Machine question

Do these exact supplied bytes satisfy the one code-owned predicate nonempty strict UTF-8 with no leading UTF-8 BOM?

The question is a byte grammar question. It does not ask whether the bytes are meaningful, textual evidence, JSON, relevant, sufficient, true, or compatible with a claim.

## Why this is useful later

Later work that wants to read presented bytes as text otherwise chooses a decode ad hoc: error replacement, BOM stripping, a locale encoding, or a caller MIME charset. Those choices are heuristics or declared metadata.

This predicate freezes one positive certificate: the exact bytes decoded under the strict UTF-8 codec, they were nonempty, and they did not start with the UTF-8 BOM. A later layer may require that certificate before any text handling. The certificate is still not an evidence kind, not a meaning, and not compatibility.

That is the smallest machine-verifiable fact this tree can add before any evidence-kind layer. Claim–Evidence Compatibility stays unauthorized.

## Stop-condition check

- The predicate is one frozen grammar, not a heuristic sniff.
- Cross-grammar ambiguity is bounded by non-exclusion: other grammars are not checked and cannot change this result.
- Intra-grammar failure is rejection. Strict UTF-8 has one decode or no decode.
- Caller MIME, filename, and kind are not inputs, so the record does not restate them.
- The fact is not already in PSRD-v0. PSRD commits uninterpreted bytes and does not record this grammar result.
- The safety boundary is in the code-owned token and the limitation list. The success tags are not format-as-evidence words.

No stop condition fired. The candidate is ready to wait for a human design-freeze decision. This document does not perform that freeze.

## Categories

1. Byte-derived fact. The predicate is derived only from the exact bytes by the algorithm below.
2. Declared metadata. MIME type, filename, extension, source name, and words such as `LOG` or `measurement` are not accepted. Hashing them would not verify them. v0 excludes them.
3. Externally attested fact. A signature, device, custody chain, or provenance source is not inferred from these bytes. v0 has no such field.

Categories 2 and 3 are not collapsed into category 1.

## Exact inputs

The only semantic input is one presented subject as exact builtin `bytes`.

No claim, claim kind, format, kind, role, MIME type, filename, path, digest, limitations, authority, domain, prefix, or tag argument is accepted.

## Derived property

One code-owned token, inserted by the producer:

`NON_EMPTY_STRICT_UTF8_NO_BOM`

The token means only that the algorithm below returned hold. It does not mean text-as-evidence, language, or JSON.

The decoded Unicode string is not stored. The original bytes are not stored.

## Derivation algorithm

The codec is the strict UTF-8 decoder. Overlong encodings, surrogate code units, and truncated sequences fail that decoder. The implementation must not use `replace`, `ignore`, `surrogateescape`, or a homemade UTF-8 parser. It must not normalize Unicode.

Order:

1. Reject a subject whose type is not exact builtin `bytes`.
2. Reject empty bytes. Empty input is well-formed UTF-8 and still fails this predicate.
3. Reject a subject that begins with the three bytes `EF BB BF`. Do not strip those bytes and retry.
4. Decode the exact bytes as strict UTF-8. A decode error rejects the subject.
5. Discard the decoded string.
6. Compute `presented_subject_digest` only with CLOSED `digest_presented_subject_bytes`.
7. Build the five-field preimage and the private-tag digest defined below.
8. Emit one six-field record.

Any failure emits no record. A failure code is not a format kind such as `BINARY` or `NOT_TEXT`.

## Ambiguity behavior

Policy:
SINGLE_PREDICATE_NON_EXCLUSIVE

One byte sequence may also satisfy another grammar. v0 does not detect that and does not reject it. The result stays the one token. No second label is emitted. No heuristic chooses a winner.

Ambiguity inside this grammar is rejection: the strict decoder fails, or the BOM rule fails, or the bytes are empty. There is no “best decode.”

## Exact record

All six fields are required. There is no optional, null, default, alias, or extra field.

1. `schema_version` is the exact builtin str `strict_utf8_byte_predicate.v0`.
2. `authority` is the exact builtin bool `False`.
3. `utf8_predicate` is the exact builtin str `NON_EMPTY_STRICT_UTF8_NO_BOM`.
4. `presented_subject_digest` is the exact builtin str returned by CLOSED `digest_presented_subject_bytes`.
5. `limitations` is the exact code-owned list below, in this order.
6. `predicate_digest` is the exact builtin str matching `[0-9a-f]{64}` and equal to the SUBP tag digest of the canonical five-field preimage.

The preimage excludes `predicate_digest`. Its members are `schema_version`, `authority`, `utf8_predicate`, `presented_subject_digest`, and `limitations`.

## Exact types

- The record is an exact builtin dict.
- Every key is an exact builtin str.
- `authority` is an exact builtin bool, and that value is `False`. `0` is rejected.
- The schema, the predicate token, the digest, and every limitation element are exact builtin str values. `str` subclasses are rejected.
- `limitations` is an exact builtin list. Subclasses of `list` are rejected.
- The creation subject is exact builtin `bytes`. `bytearray`, `memoryview`, and `bytes` subclasses are rejected.
- Serialized input is exact builtin `bytes`.

## Code-owned constants

Predicate token, the only member of this registry:

- `NON_EMPTY_STRICT_UTF8_NO_BOM`

The producer inserts it. The caller cannot choose it.

BOM prefix:

- the exact bytes `EF BB BF`

Private tag, not a public constant:

- `weaver.subp.digest.v0` plus one NUL byte

These are not members of the registry and must be rejected if supplied as the predicate token, even when a digest is recomputed:

- `EVIDENCE`, `TEXT`, `LOG`, `JSON`, `UTF8_TEXT`
- R4 `claim_kind` values
- EBD node kinds and relations
- RER pre-state kinds
- the PSRD role `UNINTERPRETED_PRESENTED_BYTES`

That last rejection does not change PSRD. It stops this record from storing the PSRD role as if this predicate were that role.

## Limitations

Exact order:

1. `nonempty_strict_utf8_no_bom_only`
2. `decoded_text_not_retained`
3. `originals_not_retained`
4. `no_unicode_normalization`
5. `nul_not_terminator`
6. `not_exclusive_grammar`
7. `not_json`
8. `not_mime_or_filename`
9. `not_meaning_or_language`
10. `not_evidence_kind`
11. `not_evidence_selection`
12. `not_compatibility`
13. `not_support`
14. `not_relevance`
15. `not_sufficiency`
16. `not_completeness`
17. `not_truth`
18. `not_authority`
19. `not_admission`
20. `not_verification`
21. `not_human_final`
22. `not_claim_binding`
23. `not_psrd_role_reinterpretation`
24. `not_omission_or_contradiction_detection`
25. `not_duplicate_or_order`
26. `not_replay_or_freshness`
27. `not_external_anchor`
28. `not_self_production_detection`
29. `not_legacy_digest_equivalence`

The list is a hashed declaration. It does not inspect the world, a claim, or another grammar.

## Creation contract

Sequence:

1. Run the derivation algorithm.
2. On hold, emit the six-field record.
3. On any miss, raise the closed error and emit no record.

Creation does not call `produce_psrd`. It does not parse JSON. It does not open a path.

## Parser contract

`parse` accepts one exact byte string.

1. Reject non-bytes.
2. Reject undecodable UTF-8.
3. Reject JSON that is not one object, and reject duplicate keys.
4. Run the structural check.
5. Require the raw bytes to equal the canonical re-encoding of the record.

This parse is of the descriptor record. It is not a parse of the presented subject. Structural success of a parsed object does not accept noncanonical record bytes.

## Structural consistency and reproduction

Success tags, exact builtin str, not a bool:

- `SUBP_STRUCTURALLY_CONSISTENT`
- `SUBP_REPRODUCED_FROM_SUPPLIED_INPUTS`

Closed failure code:

- `SUBP_REJECTED`

`SUBP_STRUCTURALLY_CONSISTENT` consults no subject bytes. It checks the six-field schema, exact types, the one token, the limitation list and order, digest syntax, and equality of `predicate_digest` with the recomputed tag digest. It does not decode UTF-8. It does not prove the presented-subject digest came from bytes that hold the predicate.

`SUBP_REPRODUCED_FROM_SUPPLIED_INPUTS` requires the structural tag's conditions, reruns creation on the supplied bytes, and requires exact six-field equality. Comparing only `presented_subject_digest` is not reproduction. Structural consistency does not authorize skipping reproduction.

Field checks run before digest equality, so a recomputed digest does not hide a bad token, a bad authority value, or a bad limitation list.

## Canonicalization

The presented subject is not canonicalized. Whitespace, NFC, and key order inside the subject are different byte strings when the bytes differ.

The descriptor record uses the receipt-family encoding already used by CSAR-v0, ACR-v0, and PSRD-v0:

`json.dumps(object, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("utf-8")`

The canonical record bytes have no trailing newline.

This encoding is not `canonical_dumps` and not WVMA-V1 `canonical_bytes`. Those CLOSED functions are not applied to the subject and not applied to this record. `canonical_dumps` normalizes set-like claim fields. Using it here would mix a claim canonicalizer into a byte predicate.

## Digest and value-class strategy

`presented_subject_digest` is only `digest_presented_subject_bytes(subject)`.

`predicate_digest` is SHA-256 over the code-owned tag `weaver.subp.digest.v0`, one NUL byte, and the canonical five-field preimage. The tag is private. The public API has no domain, prefix, tag, or expected-digest argument.

The predicate digest is a separate value from:

- the presented-subject digest
- DSDS `R4_CLAIM_BODY`, `PRESENTED_SUBJECT_BYTES`, and `CSAR_RECORD` over the same preimage
- ACD `digest_association_carriage_preimage` over the same preimage
- the PSRD tag `weaver.psrd.digest.v0` over the same preimage
- untagged SHA-256 of the preimage or of the full record
- legacy `canonical_digest`

For the same subject bytes, `presented_subject_digest` may equal a PSRD `subject_digest_psrd_v0` or a CSAR `subject_digest_csar_v0`. That equality is the shared CLOSED function. It is not a PSRD embedding, not a role change, and not legacy-digest equivalence.

## Public API shape

Functions:

- `produce_subp(subject: bytes) -> dict`
- `parse_subp(raw: bytes) -> dict`
- `subp_structurally_consistent(record: dict) -> str`
- `subp_reproduced_from_supplied_inputs(record: dict, subject: bytes) -> str`

Closed error type: `SubpError`, code `SUBP_REJECTED`.

No public digest function, tag, domain registry, canonicalizer, or format selector. The private tag helper accepts only the preimage bytes it already built.

## Relationship to PSRD and DSDS

The predicate stands on the bytes. It does not take a PSRD record and does not require PSRD reproduction.

PSRD-v0 stays CLOSED. `UNINTERPRETED_PRESENTED_BYTES` is not reinterpreted as this token, and this token is not stored as that role.

DSDS-v0 is used only through `digest_presented_subject_bytes` and `DomainSeparatedDigestError`. No domain is added. Empty bytes still fail through the nonempty rule here before a digest is required; if a digest call rejects them, the wrapper is still `SUBP_REJECTED` and no record.

Binding a full PSRD into this record would restate the uninterpreted role beside a grammar fact and would invite a reader to treat the role as UTF-8. That binding is decorative. It is not in v0.

## Relationship to R4 claims

No claim input.

`claim_kind`, `epistemic_status`, and `evidence_refs` are not consulted. This layer does not decide relevance, compatibility, support, contradiction, sufficiency, or truth.

R4 relation label `SUPPORTS` and EBD's forbidden `SUPPORTS` edge are unchanged. Provenance admission stays `NOT_CONFIGURED`.

## External-attestation boundary

No signature, timestamp, device, path stat, or external witness is an input or a field. A grammar hold is not attestation. `not_external_anchor` is a limitation, not a check that an anchor exists.

## Caller-metadata boundary

Excluded entirely. A caller string `kind=LOG` or `mime=application/json` has no parameter to land in. The derived token does not change when such a string is offered, because the call fails before derivation.

The system must not hash `LOG` or `application/json` and return “LOG verified” or “JSON verified.” Those sentences are not results of v0.

## Nonclaims

SUBP-v0 does not establish an evidence kind, evidence identity, meaning, language, JSON syntax, MIME type, filename, exclusivity over other grammars, compatibility, support, relevance, sufficiency, completeness, truth, correspondence, independence, admission, authority, verification, Human Final, claim binding, PSRD-role change, omission detection, contradiction detection, duplicate detection, order, replay distinction, freshness, external anchoring, self-production detection, or legacy digest equivalence.

Valid UTF-8 is not meaningful text. JSON syntax is not checked. A file extension is not a format. A MIME string is not a verified type. Magic bytes are not consulted. Parseability of this grammar is not truth. An image or container that happens to be valid UTF-8 is not given provenance. A schema shape is not evidence status.

PASS is not authority. Evidence is not authority. A receipt is not admission. Citation is not verification. Structural consistency is not reproduction. Supplied-input reproduction is not independent reproduction.

## Caller-selection boundary

The caller selects the bytes. v0 does not turn that selection into a complete set. Cherry-picking, omitted contradictions, duplicates, reordering, replay, alternate encodings of one meaning, self-produced bytes, and post-hoc bytes are explicitly unresolved. One subject has no set.

## Golden vectors

Candidate vectors, computed with CLOSED `digest_presented_subject_bytes`, CLOSED `domain_separated_digest`, CLOSED `digest_association_carriage_preimage`, and SHA-256 under the tag defined above. Human Design Freeze has not accepted them.

Primary subject: the single byte `0x61`.

`presented_subject_digest`:

`563fb5a4d734474c7b6e0c612ff117f379129a1eeccdaca8afecf8ade60919f1`

Canonical five-field preimage: 891 UTF-8 bytes, no CR, no trailing newline.

Exact preimage text:

`{"authority":false,"limitations":["nonempty_strict_utf8_no_bom_only","decoded_text_not_retained","originals_not_retained","no_unicode_normalization","nul_not_terminator","not_exclusive_grammar","not_json","not_mime_or_filename","not_meaning_or_language","not_evidence_kind","not_evidence_selection","not_compatibility","not_support","not_relevance","not_sufficiency","not_completeness","not_truth","not_authority","not_admission","not_verification","not_human_final","not_claim_binding","not_psrd_role_reinterpretation","not_omission_or_contradiction_detection","not_duplicate_or_order","not_replay_or_freshness","not_external_anchor","not_self_production_detection","not_legacy_digest_equivalence"],"presented_subject_digest":"563fb5a4d734474c7b6e0c612ff117f379129a1eeccdaca8afecf8ade60919f1","schema_version":"strict_utf8_byte_predicate.v0","utf8_predicate":"NON_EMPTY_STRICT_UTF8_NO_BOM"}`

Candidate predicate digest:

`609fe06b490a1f8cbc269a5db3b2ab3a791da82b7d4059e5ae63e6e6d7ac1c41`

Complete canonical six-field record: 977 UTF-8 bytes, no trailing newline.

Exact record text:

`{"authority":false,"limitations":["nonempty_strict_utf8_no_bom_only","decoded_text_not_retained","originals_not_retained","no_unicode_normalization","nul_not_terminator","not_exclusive_grammar","not_json","not_mime_or_filename","not_meaning_or_language","not_evidence_kind","not_evidence_selection","not_compatibility","not_support","not_relevance","not_sufficiency","not_completeness","not_truth","not_authority","not_admission","not_verification","not_human_final","not_claim_binding","not_psrd_role_reinterpretation","not_omission_or_contradiction_detection","not_duplicate_or_order","not_replay_or_freshness","not_external_anchor","not_self_production_detection","not_legacy_digest_equivalence"],"predicate_digest":"609fe06b490a1f8cbc269a5db3b2ab3a791da82b7d4059e5ae63e6e6d7ac1c41","presented_subject_digest":"563fb5a4d734474c7b6e0c612ff117f379129a1eeccdaca8afecf8ade60919f1","schema_version":"strict_utf8_byte_predicate.v0","utf8_predicate":"NON_EMPTY_STRICT_UTF8_NO_BOM"}`

Ordinary SHA-256 fingerprint of those exact record bytes:

`11f3251ebb757b39043655d6b333da5b95e7c34fec34936c68df6dddd7933262`

This fingerprint is not the predicate digest.

Rejected substitutes of the 891-byte preimage, none of which is the predicate digest:

- untagged SHA-256: `18d3768c5f152f85ade2c54d5aa70a92c507592803ccc421687de970ce67eff4`
- DSDS `CSAR_RECORD`: `0fe15dc0924914120491166b78ae775509b1dd98da4d4f88ef7c4f1efcbae35a`
- DSDS `PRESENTED_SUBJECT_BYTES`: `6a8ea1a974e8e51b8b10e2bf53fdf093cd346b0bd6089bb4b0811a768d734aee`
- DSDS `R4_CLAIM_BODY`: `07a9b123090945947992dbb06da20e6f40e97aa405db31f3b00fb75d611830e5`
- ACD-v0: `544854b281bbcfc3f0b43cbbd4bc3f3f7a6ee5f58a54c33334fe9267526bf6b8`
- PSRD tag over the same preimage: `c37620aba1c5ef9ec89fd89cfc65d9e58c274e2e83f1b1bb62e4d9596cf9f3cc`

Other subjects used by the attack spec, same token, different digests:

- embedded NUL `00`: presented-subject digest `b26694270ce77bf5fa0789ab31a1b32698757eeee19f7772a95664bf9d4bd878`, predicate digest `3347fee5ad69a67f297e4283f6fcc35f9357333d4f12b18eeeb065e3f1ea015d`
- ASCII JSON object `{"a":1}`: presented-subject digest `cb7cdd2decff9f81d1a59d46d3646a08faf710a77fa25e6a53581275ece239e9`, predicate digest `849e56c4841977ffdf9e11613cd4e1508aa7396b1bfd605a733ffcce1f08d3d6`
- leading space `20 61`: presented-subject digest `3b705acaaa4d4065c19f1037ae3c8b689f85e3a28b9ef5645daf0793dd07e242`, predicate digest `590632b746f160bce6c9c829d4bede0603c888e017db5d2832878a5d8bf08ae5`
- ASCII `NaN`: presented-subject digest `01e926aba615a058c92cc0d2ec465161e209b80d1df97666217ec369133cf434`, predicate digest `98b58d918f99ca3886d21a3b7e5b8cfa9b522a54dfbcbd99ba72e4459a8caa3e`
- duplicate-key JSON text `{"a":1,"a":2}`: presented-subject digest `713a9609dae790bd041be03f954f368933bf1dad9f1864c3e51fa57d469d01ef`, predicate digest `add113b34dc371a79e6f924b983d0a1db4d8118868564ccbe7167b1a21475a83`

Subjects that hold no record: empty bytes; `EF BB BF` followed by `61`; byte `FF`; overlong `C0 80`; UTF-16 encoding of `a`.

## Dependency gate

Implementation waits for a Human Design Freeze of this candidate, or of a revised candidate.

A future implementation may use CLOSED `digest_presented_subject_bytes` and `DomainSeparatedDigestError` only from DSDS-v0. It must not change DSDS, PSRD, ACD, CSAR, ACR, EBD, RER, R4, or WVMA-V1. It must not call `produce_psrd`, `canonical_dumps`, or `canonical_digest`.

This document does not schedule Human Final. It does not authorize Claim–Evidence Compatibility or an evidence-kind receipt.

## Human Design Freeze readiness

The SUBP-v0 candidate is internally coherent and is waiting for a human design-freeze decision.

Evidence-kind derivation remains a missing later prerequisite. This grammar fact does not close it.

## Attack and mutation spec

Two lists are specified. They are not the same list.

Planned attack tests are behavior specifications. Count: 27. Identifiers: `SUBP-A01` through `SUBP-A27`.

Planned source-code mutation operators are production edits for a future implementation batch. Count: 15. Identifiers: `SUBP-S01` through `SUBP-S15`.

This design batch does not implement a package, does not run the attack tests, and does not apply the source mutations.

For a field attack, recompute `predicate_digest` when the mutation changes the five-field preimage, show that the stored digest matches that recomputation, and expect rejection for the named rule rather than for a stale digest. When the attack says the digest stays unchanged, leave it unchanged so a digest check cannot be mistaken for the field rule.

### Planned attack tests

### SUBP-A01

Attack: call creation with `kind=LOG` or `format=UTF8_TEXT`, and with the subject byte `0x61`.
Expected: `TypeError` and no record. The result text is not `LOG verified`.
Invariant: a caller format word is not a parameter.
Boundary control: no digest of the word `LOG` is computed.

### SUBP-A02

Attack: pass `filename=notes.log` or the path `C:/missing/subject.bin`, including as the subject.
Expected: `TypeError` for the keyword. `SUBP_REJECTED` for a path string used as the subject. The cause is not `OSError`.
Invariant: an extension is not a format.
Boundary control: the path is not opened, so no file digest appears.

### SUBP-A03

Attack: call creation with `mime=application/json` and subject byte `0x61`.
Expected: `TypeError` and no record. The result text is not `JSON verified`.
Invariant: a MIME string is declared metadata and is excluded.
Boundary control: `application/json` is not hashed.

### SUBP-A04

Attack: subject is the single NUL byte, which is strict UTF-8 and not a word.
Expected: a record whose token is `NON_EMPTY_STRICT_UTF8_NO_BOM`, whose presented-subject digest is `b26694270ce77bf5fa0789ab31a1b32698757eeee19f7772a95664bf9d4bd878`, and whose predicate digest is `3347fee5ad69a67f297e4283f6fcc35f9357333d4f12b18eeeb065e3f1ea015d`. Success tags are only the two SUBP tags.
Invariant: grammar hold is not meaning.
Boundary control: the decoded string is absent from the record.

### SUBP-A05

Attack: subject is the ASCII bytes of `{`, which is not a JSON value, and subject is the ASCII bytes of `NaN`.
Expected: both hold the same token. The `NaN` presented-subject digest is `01e926aba615a058c92cc0d2ec465161e209b80d1df97666217ec369133cf434` and its predicate digest is `98b58d918f99ca3886d21a3b7e5b8cfa9b522a54dfbcbd99ba72e4459a8caa3e`. Neither result says JSON.
Invariant: invalid JSON is still only this UTF-8 predicate when the bytes decode.
Boundary control: no JSON parser is required to accept or reject these subjects.

### SUBP-A06

Attack: subject is the ASCII byte `31` (the character `1`) and subject is the ASCII bytes of `{"a":1}`.
Expected: both hold the same token. The object’s presented-subject digest is `cb7cdd2decff9f81d1a59d46d3646a08faf710a77fa25e6a53581275ece239e9` and its predicate digest is `849e56c4841977ffdf9e11613cd4e1508aa7396b1bfd605a733ffcce1f08d3d6`. No field says scalar or object.
Invariant: v0 has no JSON-value branch.
Boundary control: the two digests differ because the bytes differ, not because a type tag was chosen.

### SUBP-A07

Attack: subject is the ASCII bytes of `{"a":1,"a":2}`.
Expected: the predicate holds. Presented-subject digest `713a9609dae790bd041be03f954f368933bf1dad9f1864c3e51fa57d469d01ef`. Predicate digest `add113b34dc371a79e6f924b983d0a1db4d8118868564ccbe7167b1a21475a83`. Duplicate keys are not rejected and not resolved.
Invariant: JSON duplicate-key policy belongs to record parsers, not to this subject predicate.
Boundary control: the subject is not passed through `json.loads`.

### SUBP-A08

Attack: the `NaN` subject from A05, and the ASCII bytes of `Infinity`.
Expected: grammar hold only. No JSON number is accepted or rejected. `allow_nan` is not consulted for the subject.
Invariant: those spellings are UTF-8 bytes, not JSON tokens, inside v0.
Boundary control: the record canonicalizer’s `allow_nan=False` applies to the descriptor record, which contains no float.

### SUBP-A09

Attack: subject is `EF BB BF 61`.
Expected: `SUBP_REJECTED` and no record. The implementation does not strip the prefix and certify `a`.
Invariant: a leading UTF-8 BOM is outside the predicate.
Boundary control: the failure is the BOM rule, not a charset guess.

### SUBP-A10

Attack: subject is the UTF-16 encoding of `a`, including its BOM.
Expected: `SUBP_REJECTED` and no record.
Invariant: UTF-16 is not accepted as an alternate encoding of the same character.
Boundary control: no transcode into UTF-8 is attempted.

### SUBP-A11

Attack: subject is the single byte `FF`, and subject is the overlong sequence `C0 80`.
Expected: `SUBP_REJECTED` and no record for both.
Invariant: strict UTF-8 failure is not repaired.
Boundary control: `replace` and `ignore` are not success paths.

### SUBP-A12

Attack: the NUL subject from A04.
Expected: the record is emitted. The limitation list includes `nul_not_terminator`. The result does not say the string ended before the NUL.
Invariant: U+0000 is well-formed UTF-8 and is not a C-string end.
Boundary control: the stored digests are the A04 pair, not a digest of a stripped subject.

### SUBP-A13

Attack: subject is `61 00 62` and subject is `61`.
Expected: both may hold. Their presented-subject digests differ. The extra bytes are part of the subject, not trailing junk after a value.
Invariant: there is no value terminator in this grammar.
Boundary control: no parser consumes a prefix and ignores a suffix.

### SUBP-A14

Attack: subject is the byte `20` followed by `61`.
Expected: the predicate holds and is not equal to the `0x61` record. Presented-subject digest `3b705acaaa4d4065c19f1037ae3c8b689f85e3a28b9ef5645daf0793dd07e242`. Predicate digest `590632b746f160bce6c9c829d4bede0603c888e017db5d2832878a5d8bf08ae5`.
Invariant: whitespace is not canonicalized away.
Boundary control: NFC and space-stripping are not applied. The two predicate digests differ.

### SUBP-A15

Attack: subject is the ASCII bytes of `{"a":1}`, which is UTF-8 and also a JSON object.
Expected: one token, the A06 object digests, and limitation `not_exclusive_grammar`. No second format label.
Invariant: a polyglot does not create a choice.
Boundary control: magic-byte sniffing is not used to prefer JSON or to reject UTF-8.

### SUBP-A16

Attack: `produce_subp(b"")`.
Expected: `SUBP_REJECTED` and no record.
Invariant: empty UTF-8 is not this predicate.
Boundary control: no digest of the empty preimage is returned as success.

### SUBP-A17

Attack: `bytearray`, `memoryview`, and a `bytes` subclass of `0x61`.
Expected: `SUBP_REJECTED`, no record, cause is not `OSError`.
Invariant: only exact builtin `bytes` enter the decoder.
Boundary control: the objects are not coerced with `bytes(...)` before the type check.

### SUBP-A18

Attack: `utf8_predicate` is a `str` subclass of the exact token, and a `str` subclass of `EVIDENCE` whose `__eq__` always returns true. Recompute the digest for the `EVIDENCE` text. The exact-token subclass keeps the golden predicate digest.
Expected: structural rejection for the token rule in both cases. The exact-token case must not depend on digest mismatch.
Invariant: exact builtin str. Equality cannot promote `EVIDENCE`.
Boundary control: the golden digest stays in the exact-token case so a stale-digest check would miss it.

### SUBP-A19

Attack: `authority` is integer `0` with the digest recomputed, and integer `0` with the golden digest left unchanged.
Expected: structural rejection for the authority rule in both cases. Reproduction from `b"a"` rejects. Python equality of `False` and `0` is not acceptance.
Invariant: exact `False`.
Boundary control: the unchanged-digest case must not be reported only as a digest mismatch.

### SUBP-A20

Attack: add `mime` or `evidence_id` while leaving the five-field digest equal to the golden predicate digest. Delete `limitations`.
Expected: structural rejection for the key set.
Invariant: no metadata field and no missing declaration.
Boundary control: the extra-key digest is unchanged, so a digest compare would miss it.

### SUBP-A21

Attack: store each rejected substitute listed above as `predicate_digest`, and store the presented-subject digest in that field.
Expected: structural rejection because the private tag does not match. The substitutes are well-formed lowercase hex.
Invariant: those value classes are not this predicate digest.
Boundary control: syntax is valid, so the failure is the tag compare.

### SUBP-A22

Attack: replace `utf8_predicate` with `EVIDENCE` and leave `predicate_digest` equal to the golden digest.
Expected: rejection for the token rule, not for “predicate digest does not reproduce.”
Invariant: a stale digest must not become a pass, and must not hide the token rule.
Boundary control: the digest is intentionally the golden value.

### SUBP-A23

Attack: structural check of the golden record with no subject, and reproduction of the NUL record using subject `0x61`.
Expected: structural result is only `SUBP_STRUCTURALLY_CONSISTENT`. Reproduction rejects. The NUL digests differ from the golden digests.
Invariant: structural consistency does not decode and is not reproduction.
Boundary control: the golden structural check has no opportunity to call the decoder.

### SUBP-A24

Attack: reproduction of a golden record whose predicate digest is `0` repeated 64 times, and reproduction of a record whose token was changed to `EVIDENCE` while the predicate digest was recomputed and the presented-subject digest was left golden.
Expected: both reject. A comparison of only `presented_subject_digest` would accept the second.
Invariant: reproduction reruns creation and compares all six fields.
Boundary control: the second record’s subject digest matches `0x61`, so the miss has to be the token or the predicate digest.

### SUBP-A25

Attack: read the golden success tags and search the record for `EVIDENCE`, `TEXT`, `VERIFIED`, `SUPPORTED`, `ADMITTED`, and `AUTHORITATIVE`.
Expected: the tags are only `SUBP_STRUCTURALLY_CONSISTENT` and `SUBP_REPRODUCED_FROM_SUPPLIED_INPUTS`. Neither is a bool. The token is `NON_EMPTY_STRICT_UTF8_NO_BOM`.
Invariant: a grammar hold is not an evidence kind.
Boundary control: the record’s limitation `not_evidence_kind` is present and is not itself a positive evidence tag.

### SUBP-A26

Attack: ask the result words `TRUE`, `SUPPORTED`, and `AUTHORITATIVE` for subject `0x61`.
Expected: those words are absent from the success tags and from the token.
Invariant: parseability under this grammar is not truth, support, or authority.
Boundary control: the golden predicate digest can match and still not be those words.

### SUBP-A27

Attack: inspect public signatures and package exports. Pass keywords `domain`, `prefix`, `tag`, `digest`, `role`, `kind`, `format`, `mime`, `filename`, `authority`, and `limitations`.
Expected: creation parameters are exactly `subject`. Structural parameters are exactly `record`. Reproduction parameters are exactly `record` and `subject`. Forbidden keywords raise `TypeError`. Exports are the error type and the four functions. No public tag, codec name, or digest callable. The error class has no hash method.
Invariant: no hidden selector.
Boundary control: module-level imports are not public selectors. A private helper that accepts a caller tag is a selector and is out of contract.

Record-byte attacks that sit on this same surface:

- Duplicate `schema_version` in the raw record JSON fails parse.
- Whitespace, a trailing newline, a `\u` escape, a BOM, and UTF-16 on the golden record bytes fail parse. Where a JSON parser still yields the same values, structural consistency of that object holds and the raw-byte check fails.
- One insertion-order encoding of the golden values has the same 977-byte length and is not canonical. Structural consistency of the parsed object holds. Parse rejects the raw bytes.
- Reversed limitations, with the predicate digest recomputed, fail the limitation rule.
- Uppercase predicate digest, and short, long, or non-hex digests, fail as malformed digest text before equality. `.lower()` must not accept them.

Planned attack-test count:
27

### Planned source-code mutation operators

These operators are for a future implementation batch after a Human Design Freeze. They are edits to production code. They are not the 27 attack tests. This D0-following design does not apply them.

Each operator is a semantic bypass. While the edit is present, the named attack test must fail.

### SUBP-S01

Operator: accept `bytearray`, `memoryview`, or a `bytes` subclass before the exact-type check.
Killing test: `SUBP-A17`.

### SUBP-S02

Operator: add a parameter `kind`, `format`, `mime`, or `filename` and hash its value into the record.
Killing tests: `SUBP-A01`, `SUBP-A02`, `SUBP-A03`, `SUBP-A27`.

### SUBP-S03

Operator: decode with `replace` or `ignore`, so invalid UTF-8 becomes a record.
Killing test: `SUBP-A11`.

### SUBP-S04

Operator: strip a leading `EF BB BF` and certify the remainder.
Killing test: `SUBP-A09`.

### SUBP-S05

Operator: NFC-normalize or strip ASCII whitespace before the digest.
Killing test: `SUBP-A14`.

### SUBP-S06

Operator: in reproduction, compare only `presented_subject_digest`.
Killing test: `SUBP-A24`.

### SUBP-S07

Operator: accept UTF-16 when a BOM is present by transcoding to UTF-8.
Killing test: `SUBP-A10`.

### SUBP-S08

Operator: treat integer `0` as exact `False`.
Killing test: `SUBP-A19`.

### SUBP-S09

Operator: accept a `str` subclass token by equality or by `.lower()`.
Killing test: `SUBP-A18`.

### SUBP-S10

Operator: return `SUBP_REPRODUCED_FROM_SUPPLIED_INPUTS` from the structural check without decoding.
Killing test: `SUBP-A23`.

### SUBP-S11

Operator: rename a success tag or the token to `EVIDENCE`, `TEXT`, `VERIFIED`, `SUPPORTED`, `TRUE`, or `AUTHORITATIVE`.
Killing tests: `SUBP-A25` and `SUBP-A26`.

### SUBP-S12

Operator: compute `predicate_digest` with `canonical_digest`, a DSDS domain, the ACD tag, or the PSRD tag.
Killing test: `SUBP-A21`.

### SUBP-S13

Operator: accept empty bytes.
Killing test: `SUBP-A16`.

### SUBP-S14

Operator: parse the subject as JSON and require an object.
Killing tests: `SUBP-A05` and `SUBP-A06`.

### SUBP-S15

Operator: store the decoded string or the original bytes in the record.
Killing tests: `SUBP-A04` and `SUBP-A20`.

Planned source-mutation count:
15

## Semantic self-ratification

The following calls are outside the creation signature:

- subject `0x61`, keyword `kind` equal to `LOG`
- subject `0x61`, keyword `mime` equal to `application/json`

Each raises `TypeError`. No record is returned. The caller strings are not hashed. The result is not “LOG verified” and not “JSON verified.”

If a later draft adds those keywords, `SUBP-S02` is a required source mutation and `SUBP-A01` through `SUBP-A03` must fail while it is present.

## Change rule

Any later evidence kind, format registry, JSON-object predicate, claim input, or caller MIME field is a new scope or version. It must not silently rewrite this candidate into Claim–Evidence Compatibility v0 or into an evidence-kind receipt.

## Push status

NO. This candidate authorizes no public or private push.
