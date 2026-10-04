# Evidence-Kind Derivation Prerequisite — D0 Design and Attack Spec

Date:
2026-10-04

Design status:
CANDIDATE / NOT A HUMAN DESIGN FREEZE

DESIGN_STATUS:
PREREQUISITE_REQUIRED

This document is not a Human Design Freeze. It does not authorize implementation. It does not record a human acceptance decision. It defines no producer, no record, and no success tag.

Repository:
C:\dev\Weaver\weaver-forge-r4

Base HEAD:
f4f81a737a67ab494f9fe1da5c66a15d1a280eb4

PSRD-v0 Human Final:
docs/next/PSRD_V0_HUMAN_FINAL_20261004.md

PSRD-v0 fixed implementation SHA:
649c5c5c255f91c4422989857ae8b6b5a1077f05

Asked scopes that this candidate does not freeze:

- A. Claim–Evidence Compatibility v0
- B. Evidence Role Descriptor v0, including any rename of presented bytes to `EVIDENCE`

Recommended next scope:
Evidence-Kind Derivation Prerequisite

## Recommended scope

The next scope is the missing derivation prerequisite, not a new receipt.

Claim–Evidence Compatibility v0 stays unfrozen. An Evidence Role Descriptor stays unfrozen. No package, schema version, digest tag, or public function is proposed.

A later receipt may be considered only after a derivation function exists that code can check. That function is not this document.

## Machine question

Does any CLOSED function derive an evidence kind from these exact presented bytes, or from their pairing with an R4 claim, without treating `UNINTERPRETED_PRESENTED_BYTES` as evidence?

The answer on this tree is no. The question does not ask whether the bytes are relevant, sufficient, complete, true, independent, fresh, admissible, supportive, or compatible with a claim.

## Why PSRD is not sufficient

PSRD-v0 commits one code-owned role, `UNINTERPRETED_PRESENTED_BYTES`, to `digest_presented_subject_bytes` of one exact nonempty byte string. That role is not an evidence kind. The Human Final states that descriptor existence is not evidence classification and that `UNINTERPRETED_PRESENTED_BYTES` is not an evidence role.

Compatibility between a claim and “evidence” needs an evidence side. Using the PSRD role as that side would interpret uninterpreted bytes as evidence. This candidate stops that promotion.

PSRD also takes no claim. Pairing a caller-selected claim with a PSRD does not create a kind. CSAR-v0 already binds one R4 claim digest to one presented-subject digest, and ACR-v0 carries that association. Adding the PSRD role beside them would restate two CLOSED facts. It would not show that the bytes are evidence or that the claim kind fits them.

## Repository facts used

These facts are read from the current CLOSED surface. This candidate does not change them.

- R4 claim schema is `r4.epistemic.claim.v1`. `claim_kind` is the closed set `DOCUMENT_IDENTITY`, `FORMAL`, `IMPLEMENTATION`, `EMPIRICAL`, `NORMATIVE`, `SYMBOLIC`, `HISTORICAL`. `epistemic_status` is the closed set `REPORTED`, `SPECIFIED`, `OBSERVED`, `REPRODUCED`, `VERIFIED_SCOPE`, `AMBIGUOUS`, `UNRESOLVED`. Membership is a string check. The parser does not inspect presented bytes, and it does not derive a kind from them.
- `evidence_refs` and `provenance_refs` are opaque caller strings. DSDS-v0 sorts and dedupes them inside the claim body. That normalization does not bind a string to presented bytes.
- `assert_no_silent_status_promotion` takes `evidence_present` as a caller boolean. It does not hash or classify a subject.
- Legacy claim reading does not synthesize `claim_kind` or `epistemic_status`.
- R4 relation types include `SUPPORTS`, `CONTRADICTS`, `DEPENDS_ON`, `ANALOGOUS_TO`, `CAUSES`, `REFINES`, and `SUPERSEDES`. A relation-as-claim still uses opaque `evidence_refs`. The label `SUPPORTS` does not evaluate presented bytes. It is not a compatibility result.
- Provenance admission is `INDEPENDENT_EVIDENCE_ADMISSION_STATUS = NOT_CONFIGURED`. Independent evidence count stays 0. No claimant-controlled basis, ref, digest, lineage, or metadata may raise it. `SELF_DECLARED_INDEPENDENCE` is not a positive qualification. Provenance parent kinds `ARTIFACT` and `SOURCE` are graph roles, not a classifier of arbitrary presented bytes.
- DSDS-v0 domains are only `R4_CLAIM_BODY`, `PRESENTED_SUBJECT_BYTES`, and `CSAR_RECORD`. `digest_presented_subject_bytes` hashes nonempty exact bytes and does no path, text, or archive decoding.
- CSAR-v0 stores a claim digest, a subject digest, and code-owned limitations that include `presented_bytes_only` and `not_support`. It does not store an evidence kind.
- ACD-v0 is only the carriage tag `weaver.acr.digest.v0`. ACR-v0 carries one CSAR. Neither one classifies bytes.
- EBD-v0 node kinds are `RECEIPT`, `CLAIM`, `ARTIFACT`, and `EXTERNAL_REF`. Relations are `DEPENDS_ON`, `BOUNDS`, `SUCCESSOR_OF`, `CITES`, and `CONTRADICTS`. `SUPPORTS` and `VERIFIES` are forbidden relations. `GRAPH_COMPLETE` means required digest references resolve. It does not mean the omitted world was checked.
- Recovery Execution Receipt v0 has a private pre-state set `ARTIFACT`, `CONFIG`, `FREEZE_SHA256SUMS`, `CAMPAIGN_INTEGRITY`, `OTHER_BOUNDED`. The caller supplies `evidence_kind`. The code checks set membership and hashes the body. It does not infer the kind from the body. That set is not a general evidence taxonomy.
- PSRD-v0 limitations include `role_not_inferred_from_bytes`, `not_evidence_selection`, `not_compatibility`, `not_support`, `not_claim_binding`, `not_rer_evidence_kind`, and `not_ebd_relation`.

## Decision

### Option A

Claim–Evidence Compatibility v0 is not the next freeze.

A result that is weaker than support, relevance, sufficiency, truth, verification, admission, authority, completeness, and independence still needs an evidence side. The only typed subject role is `UNINTERPRETED_PRESENTED_BYTES`. Treating that role as evidence is the promotion this candidate stops.

A matrix from `claim_kind` to that single role has no CLOSED rule. Accepting every kind makes the digest decorative and restates CSAR. Accepting only some kinds would be a new policy. `claim_kind` is caller-selected enum membership, so the caller could pick the kind that the policy accepts. That is semantic self-ratification through the claim, not a check of the bytes.

No safe compatibility tag is available. This candidate defines none.

### Option B

An Evidence Role Descriptor is not the next freeze.

Who would assign the role: the bytes do not. PSRD and DSDS do not inspect contents. R4 does not assign it. EBD node kinds and RER pre-state kinds are caller-supplied vocabulary inside CLOSED receipts, and those vocabularies are not this registry.

On what machine-observable basis: none on this tree. The observable commitments are exact bytes, the presented-subject digest, the R4 claim-body digest, the CSAR association, the ACR carriage digest, and the PSRD role. None of those is an evidence kind.

Can code verify a role from the bytes: no. There is no CLOSED classifier, media registry, or schema sniff. Every nonempty subject shares one PSRD role.

A caller-selected kind would be an assertion. Hashing that assertion would not verify it. A receipt that says the hash matched would look like evidence status. That is the self-ratification this candidate refuses.

A single code-owned label such as `EVIDENCE`, applied to every nonempty subject, would rename `UNINTERPRETED_PRESENTED_BYTES`. The label would be decorative because no validator chooses it from the bytes. A longer code-owned list that code cannot choose among returns the choice to the caller.

This candidate does not create `EVIDENCE` by renaming bytes.

### Option C

The smaller prerequisite is a derivation function that does not yet exist.

The function would have to map machine-observable inputs to an evidence kind. The inputs available today do not determine such a kind. Until that function exists outside a caller label and outside a one-label rename, there is nothing for a receipt to commit to.

This candidate is that prerequisite statement. It is not an implementation of the function.

## Exact inputs

None.

The candidate accepts no claim, no claim kind, no subject, no path, no evidence set, no evidence identifier, no role, no kind, no digest, and no limitations list.

## Exact record keys

None.

There is no optional, null, default, alias, or extra field, because there is no record.

## Exact builtin types

None are introduced.

Existing CLOSED types stay where they are. Presented subjects remain exact builtin bytes inside PSRD-v0 and DSDS-v0. Claim bodies remain R4 mappings. This candidate does not accept `bytearray`, `memoryview`, a `bytes` subclass, or a path string, because it accepts no subject at all.

## Closed enums and registries

No new registry is opened.

The following CLOSED sets are not an evidence-kind registry and are not imported as one:

- R4 `claim_kind`
- R4 `epistemic_status`
- R4 relation types, including the label `SUPPORTS`
- provenance parent kinds and independence-basis labels
- EBD node kinds and relations
- RER pre-state `evidence_kind`
- the PSRD role `UNINTERPRETED_PRESENTED_BYTES`

`UNINTERPRETED_PRESENTED_BYTES` stays the PSRD role. It is not renamed and not widened.

## Who controls each semantic field

No new semantic field exists.

Control of the existing fields, stated so they are not reused by accident:

- `claim_kind` is selected by the claim’s author and checked only for closed-set membership.
- `epistemic_status` is selected by the claim’s author and checked only for closed-set membership. `VERIFIED_SCOPE` does not mean presented bytes were verified.
- `evidence_refs` are selected by the caller. They are not resolved to bytes.
- RER `evidence_kind` is selected by the caller of that CLOSED receipt.
- EBD node kind and relation are selected by the caller of that CLOSED graph.
- `presented_subject_role` is inserted by PSRD-v0. The caller cannot choose it. The only value is `UNINTERPRETED_PRESENTED_BYTES`.
- `INDEPENDENT_EVIDENCE_ADMISSION_STATUS` is code-owned and is `NOT_CONFIGURED`. Callers cannot raise the independent-evidence count.

## Creation contract

There is no creation function.

No future code in this scope may hash a caller assertion and return a record. No code may stamp `EVIDENCE` on presented bytes. No code may return a compatibility tag for a claim kind and a PSRD.

Absence of a producer is the contract. A call that expects a producer does not gain a record from this candidate.

## Parser contract

There is no parser, because there is no serialization.

Existing parsers for R4, CSAR-v0, ACR-v0, and PSRD-v0 stay on their own records. This candidate does not extend them.

## Structural consistency and reproduction

There is no structural tag and no reproduction tag.

Structural consistency of a PSRD is not evidence classification. Supplied-input reproduction of a PSRD, CSAR, or ACR is not compatibility and is not independent reproduction. A well-formed digest is not truth.

## Canonicalization

No new canonicalization is defined.

The candidate must not add a canonical form whose digest could be read as evidence status. Existing canonical JSON for CLOSED receipts stays inside those receipts.

## Digest and value-class strategy

No new digest, tag, domain, prefix, or value class is defined.

The candidate must not add a DSDS domain. It must not reuse `weaver.psrd.digest.v0`, `weaver.acr.digest.v0`, `CSAR_RECORD`, `R4_CLAIM_BODY`, `PRESENTED_SUBJECT_BYTES`, or untagged `canonical_digest` as a compatibility or evidence-kind digest.

Cited PSRD values below are anchors from the CLOSED Human Final. They are not redefined, and they are not a new golden receipt.

## Success and failure tags

Success tags:
none

Failure tags:
none

A machine success tag would be the misleading result. In particular, this candidate does not define `COMPATIBLE`, `EVIDENCE`, `EVIDENCE_KIND_DERIVED`, `SUPPORTED`, `RELEVANT`, `SUFFICIENT`, `TRUE`, `VERIFIED`, `ADMITTED`, `AUTHORITATIVE`, `COMPLETE`, `INDEPENDENT`, `FRESH`, `PASS`, `VALID`, or `ACCEPTED`.

`PREREQUISITE_REQUIRED` is the design status of this document. It is not a runtime tag.

## Nonclaims

This candidate does not establish compatibility, an evidence kind, an evidence role, evidence identity, support, relevance, sufficiency, completeness, truth, correspondence, independence, admission, authority, verification, Human Final, claim binding, omission detection, contradiction detection, duplicate detection, order, replay distinction, freshness, external anchoring, self-production detection, or legacy digest equivalence.

Hashing an assertion does not verify the assertion. A well-formed descriptor is not evidence status. `UNINTERPRETED_PRESENTED_BYTES` is not evidence. PASS is not authority. Evidence is not authority. A receipt is not admission. Citation is not verification. `GRAPH_COMPLETE` is not verification. Caller selection is not completeness. Association is not support. Carriage is not support. Compatibility is not support. Support is not truth. Support is not authority.

## Caller-selection boundary

Detected by the absence of an API:

- a caller role or kind argument
- a caller claim used as proof of compatibility
- one subject, a list of subjects, or a tuple of subjects presented as an evidence set
- an empty subject presented as an empty evidence set
- an extra identifier, contradiction flag, or claim kind attached to a new record

Explicitly not detected, and not solved by this candidate:

- cherry-picked other material
- omitted contradicting material
- duplicates
- reordered items
- replay
- the same bytes under another name
- the same semantic item in another encoding
- time relative to a claim
- absence of an external anchor
- self-produced bytes
- post-hoc bytes
- structurally well-formed but irrelevant bytes

Set-level completeness is outside this scope. The scope does not handle one item as a set, and it does not handle a set. Caller-selection risk remains explicitly unresolved.

## Evidence-status boundary

Presented bytes are not given evidence status. The PSRD role is not an evidence role. RER `evidence_kind` and EBD `ARTIFACT` are not promoted. Provenance admission stays `NOT_CONFIGURED`.

No field on a new record can say that evidence was admitted, selected, or found sufficient. No such record is defined.

## Claim-kind boundary

`claim_kind` is a closed descriptive set. It is not a normative compatibility policy. A caller can choose any member without showing that the claim body or the presented bytes satisfy that kind.

No claim-kind/evidence-kind matrix is defined. No rule from `EMPIRICAL`, `FORMAL`, or any other member to presented bytes is defined. `epistemic_status` is not a substitute for that matrix.

## Contradiction and omission boundary

This candidate has no contradiction field and no second subject. It cannot drop, rank, or resolve a contradiction. EBD `CONTRADICTS` stays the CLOSED caller-declared edge. `ContradictionPresent` is not a winner. Omission of a contradicting item is not detected. An empty set is not a proof that nothing contradicts the claim.

## Duplication, order, and replay

This candidate has no item list, so it has no order and no duplicate key inside a set. Replay of the same bytes remains a PSRD property: the same descriptor is reproduced, and that is not freshness. Two encodings of one semantic item are not identified. The same bytes under a second identifier are not collapsed.

## CLOSED and legacy separation

This candidate does not modify or reinterpret R3, R4, WVMA-V1, Tested-Envelope Receipt v0, Recovery Preflight v0, Independent Verification Preflight v0, Conducting Receipt v0, Recovery Execution Receipt v0, Evidence Binding DAG v0, DSDS-v0, ACD-v0, CSAR-v0, ACR-v0, or PSRD-v0.

It does not embed those receipts into a new compatibility object. It does not cite historical CLOSED receipts as evidence. Legacy claim compatibility remains a reader of old claims. It is not a Claim–Evidence Compatibility engine.

## Golden vectors

No new golden record, preimage, or digest is defined. Inventing one would create the decorative value this candidate refuses.

CLOSED PSRD-v0 anchors, cited and not redefined, for subject byte `0x61`:

- `subject_digest_psrd_v0`: `563fb5a4d734474c7b6e0c612ff117f379129a1eeccdaca8afecf8ade60919f1`
- role: `UNINTERPRETED_PRESENTED_BYTES`
- canonical five-field preimage: 917 UTF-8 bytes
- `descriptor_digest_psrd_v0`: `b586f3c45f548220b75b7c00bfed1e0e7b9f713a077d9d53f9534bf02eaeac80`
- canonical six-field record: 1012 UTF-8 bytes
- ordinary SHA-256 fingerprint of that record: `5dc9cf4907c977de3f3672eecb19dbb10adb4ae72069778a71aef2f8d4bb034d`

That fingerprint is not the PSRD descriptor digest, and it is not an evidence-kind digest.

## Implementation dependency gate

Implementation is not authorized.

A later design may open a receipt only when all of the following are already true:

1. A derivation function exists and is itself frozen.
2. The function does not take a caller role, kind, claim kind, or evidence-set argument.
3. The function does not map every nonempty byte string to one evidence label.
4. The function does not treat `UNINTERPRETED_PRESENTED_BYTES` as evidence.
5. The function does not import RER `evidence_kind`, EBD node kinds, or R4 `claim_kind` as its registry.
6. The result tag is still weaker than support, relevance, sufficiency, truth, verification, admission, authority, completeness, and independence.
7. Set-level omission and contradiction remain explicit nonclaims unless a separate frozen scope handles them.

Until then, Claim–Evidence Compatibility v0 and Evidence Role Descriptor v0 stay unauthorized. This document does not schedule Human Final.

## Human Design Freeze readiness

A and B are not ready for Human Design Freeze.

This prerequisite statement is internally coherent and is waiting only as a design record. It is not offered as a frozen schema. Human Design Freeze of a receipt is not performed.

## Attack and mutation spec

Two lists are specified. They are not the same list.

Planned attack tests are behavior specifications. They are not source-code mutations. Count: 25. Identifiers: `EKDP-A01` through `EKDP-A25`.

Planned source-code mutation operators are edits a future implementation batch must apply to production code if a receipt is ever authorized. They are not attack-test names. Count: 12. Identifiers: `EKDP-S01` through `EKDP-S12`.

This design batch does not implement a package, does not run the attack tests, and does not apply the source mutations. There is no producer against which a test could pass.

For every attack below, no unrelated digest is recomputed into a new record. The digest-consistency rule is: do not mint a digest for the mutated assertion. A digest that matches a CLOSED PSRD, CSAR, ACR, DSDS, or ACD value is not success. Expected result for every attack test is the same: no new record and no success tag.

### Planned attack tests

### EKDP-A01

Attack: a caller supplies the label `EVIDENCE` or `evidence` with subject byte `0x61` and asks for a receipt.
Expected: no record and no success tag.
Invariant: hashing the caller’s evidence assertion does not verify it.
Digest note: no new digest is computed. The CLOSED PSRD descriptor digest stays a role digest, not evidence status.

### EKDP-A02

Attack: substitute the role or kind with `ARTIFACT`, `CONFIG`, `EMPIRICAL`, `RECEIPT`, `SUPPORTS`, `COMPATIBLE`, and `EVIDENCE`, including a `str` subclass of each.
Expected: no record and no success tag.
Invariant: CLOSED vocabularies and support words are not an evidence-kind registry.
Digest note: recomputing a digest under the substituted word is not performed. A matching digest would be the self-ratifying case this test forbids.

### EKDP-A03

Attack: for each R4 `claim_kind`, pair the minimal claim with subject byte `0x61` and request compatibility.
Expected: no record and no success tag for every kind, including `EMPIRICAL` and `FORMAL`.
Invariant: choosing `claim_kind` does not select a compatibility result.
Digest note: the CLOSED claim-body digest and the CLOSED subject digest may both be well formed. Their pair is not a compatibility digest.

### EKDP-A04

Attack: if a later draft introduces `authority`, set it to integer `0` and also to `True`.
Expected: this candidate has no authority field. A later draft must reject integer `0` as exact `False` and must reject `True`.
Invariant: exact builtin `False` is the only authority value if a record ever exists. This candidate does not create that record.
Digest note: JSON `0` and `false` differ. This test must not accept either value by recomputing a digest.

### EKDP-A05

Attack: present a `str` subclass of `UNINTERPRETED_PRESENTED_BYTES`, a `str` subclass whose `__eq__` always returns true and whose text is `EVIDENCE`, and an enum-like subclass of a claim kind.
Expected: no record and no success tag.
Invariant: equality and subclassing do not promote a label into a kind.
Digest note: a subclass that serializes as the same text must not become success merely because a digest matches.

### EKDP-A06

Attack: pass `bytearray`, `memoryview`, a `bytes` subclass, and the path string `C:/missing/subject.bin` as the subject of an evidence or compatibility call.
Expected: no record and no success tag. No `OSError` from opening the path is a result.
Invariant: byte-like aliases and paths are not evidence subjects.
Digest note: no digest is computed from the alias.

### EKDP-A07

Attack: add `evidence_id`, `note`, `claim_kind`, or `contradiction_present`, and delete any field a later draft treats as required.
Expected: no record and no success tag.
Invariant: extra and missing fields do not create an evidence identity.
Digest note: a five-field or six-field digest that ignores the extra key must not pass.

### EKDP-A08

Attack: duplicate a key in raw JSON, including `schema_version` or `evidence_kind`.
Expected: no parser accepts the object.
Invariant: duplicate keys are not a second identity.
Digest note: no canonical re-encoding of the last duplicate becomes success.

### EKDP-A09

Attack: whitespace, a trailing newline, a `\u` escape, a BOM, and UTF-16 around any later serialization of subject byte `0x61`.
Expected: no parser accepts the bytes as a new record.
Invariant: noncanonical bytes are not a second value class.
Digest note: if a JSON parser would yield the same values, that value match is still not success, because this candidate has no canonical record.

### EKDP-A10

Attack: reverse a limitation list that includes `not_evidence` or `not_compatibility`.
Expected: no record. A later draft must reject the reversed order even when its digest is recomputed.
Invariant: limitation order is not a caller-controlled weakening.
Digest note: a recomputed digest over the reversed list must not hide the order check, and this candidate does not mint that digest.

### EKDP-A11

Attack: present the untagged SHA-256 of the PSRD preimage, each DSDS domain over that preimage, the ACD digest of that preimage, the subject digest, and the ordinary record fingerprint as if one of them were an evidence-kind digest.
Expected: no success tag. Those values stay distinct from each other and from evidence status.
Invariant: an existing value class is not an evidence-kind class.
Digest note: the cited CLOSED values are the consistent inputs. None of them is accepted as a new digest.

### EKDP-A12

Attack: compare `canonical_digest` of a claim, a file SHA-256, or the PSRD fingerprint with a proposed compatibility digest.
Expected: no equivalence is defined.
Invariant: legacy untagged digests are not this decision.
Digest note: the fingerprint beginning `5dc9cf49` and ending `034d` is only the cited PSRD record fingerprint.

### EKDP-A13

Attack: take a structurally consistent PSRD for byte `0x61` and read it as reproduction of compatibility, or as reproduction of an evidence kind.
Expected: the PSRD structural tag stays `PSRD_STRUCTURALLY_CONSISTENT` only. No compatibility tag is returned.
Invariant: structural consistency is not reproduction, and neither one is evidence classification.
Digest note: the PSRD descriptor digest may match. That match is the stale-success case this test rejects.

### EKDP-A14

Attack: accept a bundle when only `subject_digest_psrd_v0`, or only the claim digest, matches the supplied inputs.
Expected: no success tag.
Invariant: subset equality is not reproduction of a joint claim.
Digest note: keep the matched digest equal to the CLOSED value so the test is not a stale-digest miss.

### EKDP-A15

Attack: request a result word `SUPPORTED` or a field `support` for a claim and subject byte `0x61`.
Expected: no success tag.
Invariant: compatibility language does not become support. EBD `SUPPORTS` stays forbidden. The R4 relation label `SUPPORTS` is not executed against the bytes.
Digest note: no support digest is defined.

### EKDP-A16

Attack: request `RELEVANT`, `SUFFICIENT`, or `TRUE` for the same pair.
Expected: no success tag.
Invariant: a structural pairing is not relevance, sufficiency, or truth.
Digest note: well-formed CLOSED digests remain well formed and are not those results.

### EKDP-A17

Attack: request `AUTHORITATIVE`, `ADMITTED`, or `VERIFIED`, or set authority to true.
Expected: no success tag. Provenance admission stays `NOT_CONFIGURED`.
Invariant: a receipt is not admission, authority, or verification.
Digest note: no digest is promoted to those words.

### EKDP-A18

Attack: supply one subject and omit a second subject that a caller could have marked contradictory.
Expected: no result says the contradiction is absent, resolved, or considered.
Invariant: omission of a contradiction is outside this scope.
Digest note: a digest of the supplied subject alone must not read as completeness.

### EKDP-A19

Attack: supply a one-item list and a longer caller-selected list of byte strings.
Expected: no evidence-set record.
Invariant: a caller-selected subset is not a complete set.
Digest note: hashing the list in caller order must not become success.

### EKDP-A20

Attack: supply the same subject bytes twice in one list.
Expected: no duplicate-detection success.
Invariant: one digest repeated is not a uniqueness proof across evidence.
Digest note: no set-canonical digest is defined.

### EKDP-A21

Attack: supply two different subjects in both orders.
Expected: no order-normalized success.
Invariant: this scope has no item order to bless.
Digest note: equal sorted digests must not be invented to hide order.

### EKDP-A22

Attack: call the same subject twice, including replay after a delay.
Expected: no freshness tag. PSRD reproduction of the same bytes stays PSRD reproduction.
Invariant: replay is not distinguished here.
Digest note: an identical CLOSED descriptor digest is not freshness.

### EKDP-A23

Attack: bind subject byte `0x61` to two identifiers, two evidence refs, or two encodings of the same text.
Expected: no identity collapse and no evidence identity.
Invariant: the same bytes under another name are not resolved.
Digest note: one presented-subject digest for the same bytes is the CLOSED DSDS fact. It is not a second identity check.

### EKDP-A24

Attack: keep a CLOSED PSRD or CSAR digest unchanged while changing the surrounding label to `EVIDENCE`, `COMPATIBLE`, or `SUPPORTED`.
Expected: the unchanged digest does not produce success.
Invariant: a stale digest must not be reported as a failed digest while the label change is accepted, and it must not be accepted because the digest still matches.
Digest note: this is the stale-digest false-positive control. The digest is intentionally left consistent with the CLOSED record. Success is still forbidden.

### EKDP-A25

Attack: look for a public function, parameter, package attribute, class method, or callable named with `domain`, `prefix`, `tag`, `digest`, `role`, `kind`, `authority`, `canonical`, or `hash` that selects an evidence kind or a compatibility rule.
Expected: this candidate exports nothing. No such selector is added to a CLOSED package.
Invariant: no hidden selector ratifies a caller label.
Digest note: a private helper that hashes a caller kind is still a selector. None is specified.

Planned attack-test count:
25

### Planned source-code mutation operators

These operators are for a future implementation batch only. They are edits to production code. They are not the 25 attack tests above. This D0 does not apply them. A future batch may apply them only after a Human Design Freeze authorizes a real derivation. If that freeze never happens, these operators stay unapplied.

Each operator is a semantic bypass. The expected result after the edit is that the matching attack tests fail. A cosmetic rename is not in this set.

### EKDP-S01

Operator: change a producer so `UNINTERPRETED_PRESENTED_BYTES` is returned or stored as evidence kind.
Kills: `EKDP-A01` and `EKDP-A02` must fail while this edit is present.
Invariant: the PSRD role is not evidence.

### EKDP-S02

Operator: add a caller argument `evidence_kind` or `role` and hash it into the record.
Kills: `EKDP-A01` and `EKDP-A25` must fail while this edit is present.
Invariant: a caller label is not a derivation.

### EKDP-S03

Operator: stamp the code-owned string `EVIDENCE` on every nonempty subject and digest that stamp.
Kills: `EKDP-A01` must fail while this edit is present.
Invariant: one label for every subject is a rename, not a derivation.

### EKDP-S04

Operator: add a claim-kind matrix that returns a compatibility tag for one or more R4 kinds.
Kills: `EKDP-A03` must fail while this edit is present.
Invariant: no CLOSED matrix exists, so an added matrix is policy.

### EKDP-S05

Operator: return success when only the subject digest, or only the claim digest, matches.
Kills: `EKDP-A14` must fail while this edit is present.
Invariant: subset comparison is not joint reproduction.

### EKDP-S06

Operator: treat integer `0` as exact `False` for authority.
Kills: `EKDP-A04` must fail while this edit is present.
Invariant: `False` and `0` stay distinct if a record ever exists.

### EKDP-S07

Operator: accept a `str` subclass by equality or by `.lower()` for a role, kind, or digest.
Kills: `EKDP-A05` must fail while this edit is present.
Invariant: exact builtin `str` is required for any future label.

### EKDP-S08

Operator: return a reproduction or compatibility tag from the structural check alone.
Kills: `EKDP-A13` must fail while this edit is present.
Invariant: structural consistency is not reproduction and not compatibility.

### EKDP-S09

Operator: alias a result to `SUPPORTED`, `RELEVANT`, `SUFFICIENT`, `TRUE`, `VERIFIED`, `ADMITTED`, or `AUTHORITATIVE`.
Kills: `EKDP-A15`, `EKDP-A16`, and `EKDP-A17` must fail while this edit is present.
Invariant: no weaker structural tag is promoted to those words.

### EKDP-S10

Operator: ignore an extra key, a second subject, or an omitted sibling while emitting a digest of the remaining fields.
Kills: `EKDP-A07`, `EKDP-A18`, and `EKDP-A19` must fail while this edit is present.
Invariant: an ignored field must not look like a considered set.

### EKDP-S11

Operator: add a public parameter or callable that selects `domain`, `prefix`, `tag`, `kind`, `role`, or `authority`.
Kills: `EKDP-A25` must fail while this edit is present.
Invariant: no generic selector.

### EKDP-S12

Operator: compute the new digest with `canonical_digest`, a DSDS domain, the ACD tag, or the PSRD tag.
Kills: `EKDP-A11` and `EKDP-A12` must fail while this edit is present.
Invariant: existing value classes stay unmixed. No new digest is authorized by this candidate.

Planned source-mutation count:
12

## Change rule

Any later evidence kind, evidence role, claim input used as compatibility, or evidence set is a new scope or version. It must not silently rewrite this candidate into Claim–Evidence Compatibility v0, Claim Support Bound v0, or an Evidence Role Descriptor that renames presented bytes.

## Push status

NO. This candidate authorizes no public or private push.
