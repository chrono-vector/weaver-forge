# Exact-Bytes Witness Verification Prerequisite — D0

Date:
2026-10-05

Design status:
CANDIDATE / NOT A HUMAN DESIGN FREEZE

DESIGN_STATUS:
PREREQUISITE_REQUIRED

This document is not a Human Design Freeze. It does not authorize implementation. It does not record a human acceptance decision. It defines no producer, no record, no schema, no digest, and no success tag.

Repository:
C:\dev\Weaver\weaver-forge-r4

Base HEAD:
6a864398f80fc9fb1dee1bec45894b2926af7ba0

SUBP-v0 Human Final:
docs/next/SUBP_V0_HUMAN_FINAL_20261004.md

SUBP-v0 fixed implementation SHA:
fd758c417c1a593a95b2808bfd998ca16a7041e5

SUBP-v0 status:
CLOSED

Asked directions that this candidate does not freeze:

- A. Strict Canonical JSON Object Predicate v0
- B. Weaver Schema Recognition Predicate v0
- Claim–Evidence Compatibility v0

Recommended next scope:
Exact-Bytes Witness Verification Prerequisite

## Machine question

Does any CLOSED function verify an external witness over these exact supplied bytes, as distinct from hashing the bytes, accepting a caller kind, or matching a closed schema name?

The answer on this tree is no.

## What later decision this enables

A checked external witness is the first machine decision SUBP-v0 cannot make: these exact bytes have a witness that code checked, separate from “these bytes are nonempty strict UTF-8 with no leading UTF-8 BOM.”

That decision is the smallest gate that keeps a later evidence type from being a hashed caller sentence. It does not decide evidence kind, claim compatibility, key trust, signer identity, freshness, replay, or truth.

No smaller byte grammar opens that gate. Canonical JSON and closed-schema recognition add shape facts. They do not tell a checked witness from a caller label.

## Why SUBP-v0 is not sufficient

SUBP-v0 certifies one code-owned predicate, `NON_EMPTY_STRICT_UTF8_NO_BOM`, for one exact `bytes` value. The predicate is `SINGLE_PREDICATE_NON_EXCLUSIVE`. Valid UTF-8 is not meaningful text, not a log, not a measurement, and not evidence.

The same bytes remain eligible for every R4 `claim_kind`. SUBP does not read `claim_kind`. Changing the claim kind does not change the predicate. That is why compatibility stays unfrozen.

## Repository answers

These facts are read from the current CLOSED surface. This candidate does not change them.

1. Byte-derived predicates that exist are narrow. DSDS-v0 `digest_presented_subject_bytes` commits to nonempty exact bytes and does not decode them. SUBP-v0 adds only nonempty strict UTF-8 with no leading `EF BB BF`. PSRD-v0’s role `UNINTERPRETED_PRESENTED_BYTES` is a code-owned constant. It is not inferred from the bytes.

2. There is no single strict canonical JSON grammar for arbitrary presented bytes. `canonical_dumps` normalizes set-like claim fields and calls `json.dumps` without `allow_nan=False`. `canonical_loads` is `json.loads`. WVMA-V1 `canonical_bytes` canonicalizes in-memory objects, rejects `bytes`, and is not a parser of presented bytes. CSAR-v0, ACR-v0, PSRD-v0, and SUBP-v0 each encode only their own record, with `allow_nan=False` and duplicate-key rejection. Those four parsers do not agree to become one presented-byte grammar.

3. None of those canonicalizers is stable enough to expose as a general syntax predicate. Using one of them on arbitrary bytes would either change a CLOSED regime or add a new one. A syntax success would still not be an evidence status.

4. Closed receipt identity is recognizable only by that receipt’s own parser. `parse_csar`, `parse_acr`, `parse_psrd`, and `parse_subp` accept canonical bytes of their own schemas. They do not accept a caller schema name. Structural success does not require the original subject bytes of an embedded digest. Anyone who can write the canonical JSON can produce bytes the parser accepts.

5. “These bytes match schema X” can be a code-derived structural fact inside the CLOSED parser. It is not “this object was authentically produced by X.” A new recognizer that returns the schema name would restate structural success and invite that second reading. This candidate does not add that recognizer.

6. No CLOSED cryptographic signature or witness verifier exists on this surface. Digests are SHA-256 commitments. Provenance `EXTERNAL_WITNESS_RECEIPT` is an independence-basis label. While `INDEPENDENT_EVIDENCE_ADMISSION_STATUS` is `NOT_CONFIGURED`, that label is not a positive qualification, and claimant-controlled inputs cannot raise `independent_evidence_count` above 0. IVP rejects a caller field `claims_independent_witness` with `IVP_SCOPE_VIOLATION`. Its limitation list includes `external witness admission`.

7. Without an external witness check, the tree cannot establish that bytes are a log, a test result, a measurement, or evidence; that a schema-shaped object was produced by a Weaver component; that an R4 `claim_kind` fits the bytes; or that the bytes are independent, fresh, or admitted.

## Decision

### Option A

A Strict Canonical JSON Object Predicate is not the next scope.

There is no already-frozen canonicalization rule for arbitrary bytes. The three existing regimes are claim normalization, WVMA object bytes, and per-receipt encoding. A fourth parser would be a new grammar.

The later decision it would enable is “these UTF-8 bytes are one canonical JSON object.” SUBP-v0 already accepts those bytes when they are strict UTF-8. The added fact does not choose an evidence kind, does not bind a claim, and does not check a witness. It is an encoding fact with no path to compatibility. The minimality rule stops it.

### Option B

A Weaver Schema Recognition Predicate is not the next scope.

The CLOSED parsers already answer “do these bytes match this one schema?” for their own records. Wrapping those answers in a new kind label does not create a new machine fact. It creates a name that is easy to read as provenance.

Schema match stays structural. It does not show who produced the bytes. Using the match as authenticity, or as evidence kind, is the self-ratification this candidate refuses.

### Option C

The smallest missing prerequisite is an external witness check over exact bytes.

The check’s inputs, once a later design chooses an algorithm, are the exact subject bytes plus witness material that is not inside those bytes and not a caller kind, MIME type, filename, or schema name. The check’s only result is whether that witness commits to those exact bytes.

This document does not choose the algorithm, the key type, or the byte layout. The tree has no CLOSED verifier to reuse. Inventing one here would freeze cryptography without a reviewed choice.

Explicitly deferred, and not bundled into this prerequisite:

- key trust and registry
- signer, device, or service identity
- execution provenance
- source binding beyond the exact bytes
- timestamp and freshness
- anti-replay
- a further external anchor
- evidence kind
- claim compatibility

### Option D

No smaller byte predicate is justified. Length, media type, magic bytes, and language are either already fixed by the exact bytes or are caller metadata. SUBP-v0 records those nonclaims.

## Claim–evidence compatibility

CLAIM_EVIDENCE_COMPATIBILITY_READY:
NO

Evidence status, evidence kind, and relevance remain caller-shaped or absent. No CLOSED matrix maps `claim_kind` to presented bytes. Contradictory and omitted material are not detected. The same bytes can be paired with another claim kind. Schema recognition is not authenticity. Compatibility stays unfrozen.

## Claim kind

R4 `claim_kind` is caller-selectable. `EpistemicClaimRecord.from_dict` requires a string in the closed set `DOCUMENT_IDENTITY`, `FORMAL`, `IMPLEMENTATION`, `EMPIRICAL`, `NORMATIVE`, `SYMBOLIC`, `HISTORICAL`. Membership is the check. The parser does not read presented bytes.

`formal_and_symbolic_are_distinct` only reports that two members differ. It assigns no compatibility.

`assert_no_silent_status_promotion` takes `evidence_present` as a caller boolean. `VERIFIED_SCOPE` does not mean bytes were verified.

`evidence_refs` are caller strings. DSDS-v0 may sort and dedupe them inside a claim body. That does not bind a string to presented bytes.

R4 relation label `SUPPORTS` does not evaluate bytes. EBD forbids `SUPPORTS` and `VERIFIES`. Neither label is a compatibility result.

R4_CLAIM_KIND_CALLER_SELECTABLE:
YES

R4_CLAIM_KIND_HAS_CLOSED_COMPATIBILITY_SEMANTICS:
NO

## Exact inputs

None.

This candidate accepts no subject, witness, signature, public key, claim, claim kind, schema name, path, role, MIME type, filename, or limitations list.

## Exact record keys

None.

## Success and failure tags

Success tags:
none

Failure tags:
none

`PREREQUISITE_REQUIRED` is the design status of this document. It is not a runtime tag.

This candidate does not define `COMPATIBLE`, `EVIDENCE`, `LOG`, `MEASUREMENT`, `TEXT`, `JSON`, `VERIFIED`, `SUPPORTED`, `RELEVANT`, `SUFFICIENT`, `TRUE`, `ADMITTED`, `AUTHORITATIVE`, `PROVENANCE`, `AUTHENTIC`, `FRESH`, `INDEPENDENT`, or `WITNESS_VERIFIED`.

## Nonclaims

This candidate does not establish an evidence kind, a witness, a signature, provenance, authenticity, compatibility, support, relevance, sufficiency, completeness, truth, authority, independence, freshness, admission, verification, or Human Final.

UTF-8 is not text evidence. JSON syntax is not a trustworthy record. A schema name is not production by that schema’s component. A hash of a sentence is not verification of the sentence. `EXTERNAL_WITNESS_RECEIPT` is not a verified witness. `NOT_CONFIGURED` is not a disproof that witnesses exist in the world.

## Semantic self-ratification

The forbidden pattern remains:

- caller says the bytes are a log, a test result, a measurement, or evidence
- code hashes or stores that sentence
- a later layer says the log or the evidence was verified

This candidate has no field that can store the sentence and no tag that can return the verification.

A caller schema name, a SUBP token, or a successful `parse_csar` is the same pattern if a new layer promotes it to provenance or evidence. This candidate does not perform that promotion.

## Attack and mutation spec

Two lists are specified. They are not the same list.

Planned attack tests are behavior specifications for this refusal. Count: 15. Identifiers: `EWVP-A01` through `EWVP-A15`.

Planned source-code mutation operators are edits that would violate this refusal if a package were added. Count: 13. Identifiers: `EWVP-S01` through `EWVP-S13`.

This design batch does not implement a package, does not run the attack tests, and does not apply the source mutations.

### Planned attack tests

### EWVP-A01

Attack: offer subject byte `0x61` with `kind=LOG` or `mime=application/json`.
Expected: no record and no tag. The result is not `LOG verified` or `JSON verified`.
Invariant: a caller kind or MIME type is not a witness.
Boundary control: the caller string is not hashed.

### EWVP-A02

Attack: offer the ASCII object `{"a":1}` as a presented subject.
Expected: this scope adds no JSON-object predicate and no canonicality tag.
Invariant: canonical JSON syntax is not the missing witness.
Boundary control: `canonical_dumps`, WVMA-V1 `canonical_bytes`, and the receipt-family encoder are not applied to the subject by this scope.

### EWVP-A03

Attack: pass `schema=csar.v0` or `schema=strict_utf8_byte_predicate.v0`.
Expected: no parameter accepts the name. No provenance tag is returned.
Invariant: a schema name is caller metadata.
Boundary control: the name is not written into a digest.

### EWVP-A04

Attack: take bytes that `parse_csar` or `parse_subp` already accepts and ask this scope to classify them.
Expected: this scope returns no schema kind, no authenticity tag, and no evidence tag. The CLOSED parsers stay on their own records.
Invariant: structural match is not production by that component.
Boundary control: this scope does not call those parsers in order to mint a new label.

### EWVP-A05

Attack: take a SUBP-v0 success for byte `0x61` and ask for text evidence, a log, or a measurement.
Expected: the SUBP token remains `NON_EMPTY_STRICT_UTF8_NO_BOM`. This scope adds no second label.
Invariant: UTF-8 is not evidence.
Boundary control: SUBP-v0 is not reinterpreted.

### EWVP-A06

Attack: pair one subject with R4 `claim_kind` `FORMAL` and again with `EMPIRICAL`.
Expected: no compatibility result exists for either pair.
Invariant: claim-kind membership is not compatibility.
Boundary control: the two caller kinds do not produce two tags.

### EWVP-A07

Attack: pass `witness=EXTERNAL_WITNESS_RECEIPT` or a `signature` string.
Expected: no verification tag. `independent_evidence_count` is not raised by this scope.
Invariant: a witness label is not a witness check.
Boundary control: provenance admission stays `NOT_CONFIGURED`.

### EWVP-A08

Attack: hash the sentence `this is a measurement` and present the digest as verification.
Expected: the digest is not a success tag and not a witness result.
Invariant: hashing an assertion does not verify it.
Boundary control: no new domain, prefix, or tag is defined for the sentence.

### EWVP-A09

Attack: offer duplicate-key JSON `{"a":1,"a":2}` and a noncanonical encoding of the same object with extra whitespace.
Expected: this scope selects neither encoding and defines no canonical regime.
Invariant: presented-byte canonicalization stays inside CLOSED receipts.
Boundary control: neither `canonical_dumps` nor WVMA-V1 `canonical_bytes` becomes a presented-byte parser here.

### EWVP-A10

Attack: attach two caller labels, `LOG` and `MEASUREMENT`, to the same bytes.
Expected: no kind record exists, so the labels cannot change a result.
Invariant: relabeling is not a machine fact.
Boundary control: the bytes are not stored under either label.

### EWVP-A11

Attack: omit a contradictory byte string, and replay an earlier subject.
Expected: this scope does not report omission detection, contradiction detection, or replay detection.
Invariant: those checks are not supplied by UTF-8 or by schema shape.
Boundary control: no tag says they were performed.

### EWVP-A12

Attack: offer a `str` subclass `EVIDENCE` whose equality always returns true.
Expected: no field accepts it. Equality does not create a kind.
Invariant: there is no token that a subclass can impersonate.
Boundary control: no digest is computed for the subclass.

### EWVP-A13

Attack: ask for `SUPPORTED`, `TRUE`, `VERIFIED`, `AUTHORITATIVE`, `PROVENANCE`, or `AUTHENTIC`.
Expected: none of those words is a success tag.
Invariant: a missing witness check is not a positive conclusion.
Boundary control: the design status `PREREQUISITE_REQUIRED` is not returned as a runtime tag.

### EWVP-A14

Attack: inspect the public surface introduced by this document.
Expected: no package, no producer, no parser, no digest function, and no selector.
Invariant: absence of an API is the contract.
Boundary control: CLOSED exports of SUBP-v0, PSRD-v0, CSAR-v0, ACR-v0, and DSDS-v0 stay unchanged.

### EWVP-A15

Attack: supply a public-key byte string and a detached signature byte string beside subject `0x61`.
Expected: this scope does not verify them and does not return `WITNESS_VERIFIED`.
Invariant: algorithm choice is not hidden inside this prerequisite statement.
Boundary control: no signature library is selected and no key is marked trusted.

Planned attack-test count:
15

### Planned source-code mutation operators

These operators are edits that would violate this refusal. They are not the 15 attack tests. This batch does not apply them.

### EWVP-S01

Operator: add a producer that hashes `kind` or `mime` into a record.
Killing test: `EWVP-A01`.

### EWVP-S02

Operator: accept a subject when it is one canonical JSON object and return a syntax tag.
Killing test: `EWVP-A02`.

### EWVP-S03

Operator: accept a caller schema name and store it as provenance.
Killing test: `EWVP-A03`.

### EWVP-S04

Operator: when `parse_csar` or `parse_subp` succeeds, return an authenticity or evidence label.
Killing test: `EWVP-A04`.

### EWVP-S05

Operator: map the SUBP token to `TEXT`, `LOG`, or `MEASUREMENT`.
Killing test: `EWVP-A05`.

### EWVP-S06

Operator: return `COMPATIBLE` when `claim_kind` is in the R4 set.
Killing test: `EWVP-A06`.

### EWVP-S07

Operator: treat the string `EXTERNAL_WITNESS_RECEIPT` as a verified witness.
Killing test: `EWVP-A07`.

### EWVP-S08

Operator: hash a caller sentence and return that digest as verification.
Killing test: `EWVP-A08`.

### EWVP-S09

Operator: parse presented bytes with `canonical_dumps` or WVMA-V1 `canonical_bytes`.
Killing test: `EWVP-A09`.

### EWVP-S10

Operator: store a caller label beside a digest and treat a label change as a new fact.
Killing test: `EWVP-A10`.

### EWVP-S11

Operator: return a tag that says omission, contradiction, or replay was checked.
Killing test: `EWVP-A11`.

### EWVP-S12

Operator: accept a `str` subclass by equality, or rename the refusal into `VERIFIED` or `PROVENANCE`.
Killing tests: `EWVP-A12` and `EWVP-A13`.

### EWVP-S13

Operator: compare or verify a supplied signature and return `WITNESS_VERIFIED`, or export a producer from this scope.
Killing tests: `EWVP-A14` and `EWVP-A15`.

Planned source-mutation count:
13

## Change rule

Any later witness algorithm, key registry, JSON-object predicate, schema recognizer, or claim-compatibility matrix is a new scope or version. It must not be slipped into SUBP-v0, PSRD-v0, or this refusal.

## Push status

NO. This candidate authorizes no public or private push.
