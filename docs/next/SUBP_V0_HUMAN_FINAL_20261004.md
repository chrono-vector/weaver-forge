# Strict UTF-8 Byte Predicate v0 — Human Final

Date:
2026-10-04

Human Final:
HUMAN_REVIEW_ACCEPTED

This document records a Human Final decision explicitly made by the human authority. It does not record an AI acceptance decision. The independent reviewer is not the Human Final authority.

HUMAN_REVIEW_ACCEPTED accepts the frozen SUBP-v0 contract and its implementation and tested envelope within this scope. It records only the frozen machine question:

Do these exact supplied bytes satisfy the one code-owned predicate nonempty strict UTF-8 with no leading UTF-8 BOM?

This acceptance does not establish meaningful text, natural language, JSON, a log, evidence, an evidence kind, a MIME or media type, filename or type correctness, provenance, authenticity, support, relevance, sufficiency, completeness, truth, authority, independence, freshness, admission, verification, or Human Final semantics.

The predicate is one code-owned fact derived from exact supplied bytes only. It is SINGLE_PREDICATE_NON_EXCLUSIVE. Success is not an exclusive format classification. Other grammars may also hold.

Caller format selector:
NO

Caller metadata influence:
NO

Heuristic sniffing:
NO

Evidence kind introduced:
NO

PSRD reinterpretation:
NO

`UNINTERPRETED_PRESENTED_BYTES` is not this token, and this token is not that role. Structural consistency is not supplied-input reproduction. Supplied-input reproduction is not independent reproduction. A grammar hold is not evidence classification.

Fixed reviewed implementation SHA:
fd758c417c1a593a95b2808bfd998ca16a7041e5

This Human Final documentation commit is a later save. It does not replace that fixed implementation SHA. No later production or test commit is part of this acceptance.

Repository:
C:\dev\Weaver\weaver-forge-r4

Scope:
Strict UTF-8 Byte Predicate v0 (SUBP-v0) only

Design document:
docs/next/STRICT_UTF8_BYTE_PREDICATE_V0_DESIGN_AND_ATTACK_SPEC_20261004.md

Design commit:
bd0b893e11b3594a769935f68dcf878d9d17314e

Human Design Freeze:
ACCEPTED

Freeze document:
docs/next/SUBP_V0_HUMAN_DESIGN_FREEZE_20261004.md

Design-freeze save commit:
1d264055402aced9b967d09810fcdb780d8dfbb4

Material blockers:
0

SUBP-v0 status after this record:
CLOSED

## Implementation history

- design candidate: bd0b893e11b3594a769935f68dcf878d9d17314e
- Human Design Freeze save: 1d264055402aced9b967d09810fcdb780d8dfbb4
- implementation, 27 planned attack tests, and fixed reviewed SHA: fd758c417c1a593a95b2808bfd998ca16a7041e5

The fixed reviewed tree is the implementation commit.

## Review history

Final independent review:
VERDICT ACCEPT. MATERIAL_FINDINGS 0. CLOSED_SCOPE_SAFETY PASS. READY_FOR_HUMAN_FINAL YES.

The independent review is not this Human Final. The read-only review instruction was not fully obeyed. The deviation is recorded below. It did not leave the reviewed tree modified.

Planned attack tests SUBP-A01 through SUBP-A27:
27/27 PASS. None skipped. None xfailed.

The 27 planned items are attack tests. They are not source-code mutation-harness mutants.

Independent source-mutation final classification:
15 executed. 14 KILLED. 1 EQUIVALENT (S06). 0 SURVIVED.

## S06 correction

The implementation-batch report classified all 15 source mutations as KILLED. Independent review determined S06 is observationally EQUIVALENT under the frozen contract because structural validation already fixes the other relevant fields. A variant that removed the structural precondition was killed.

This correction is NONMATERIAL. It does not change the accepted semantics. S06 is not counted as KILLED.

## Nonmaterial process deviation

Classification:
NONMATERIAL_PROCESS_DEVIATION

This is a review-process deviation. It is not a production defect.

During the independent read-only final review, the reviewer ran `campaign_runner_v0` outside the required review scope while trying to explain broader regression counts.

That run wrote to the worktree:

- 8 tracked files under `aurora_audit/campaigns/aurora_operational_v1` were modified
- 7 untracked `b1_*` directories were created
- 1 ignored directory was created
- pre-existing ignored `aurora_*_test` scratch contents were overwritten

Reviewer response:

- diff and untracked material was backed up outside the repo at `/workspace/subpf/backup/`
- the affected tracked directory was restored to HEAD
- the created directories were removed
- final HEAD remained `fd758c417c1a593a95b2808bfd998ca16a7041e5`
- final git status was clean
- ignored scratch contents that existed before the test could not be restored

This Human Final save does not delete `/workspace/subpf/backup/`. It does not touch ignored scratch paths. It does not claim that those overwritten ignored contents were restored.

Reason the deviation is nonmaterial:

- no accepted SUBP production semantics changed
- no protected CLOSED scope remained modified
- the reviewed HEAD remained unchanged
- the final worktree was clean
- material findings remained 0

Lesson:
Future read-only reviews must not run write-producing or unknown broader suites merely to reconcile test-count differences. Prefer known safe focused and regression suites, isolated temporary copies or worktrees, or inspect the test before execution.

## Accepted evidence

- SUBP focused tests: 29 passed, 39 subtests passed, 0 failed
- PSRD-v0 regression: 39 passed, 37 subtests passed
- DSDS-v0 regression: 36 passed, 19 subtests passed
- CSAR-v0 regression: 45 passed, 15 subtests passed
- ACD-v0 regression: 21 passed, 5 subtests passed
- ACR-v0 regression: 27 passed, 28 subtests passed
- independent broader review: 861 passed, 186 subtests
- the prior 664 passed and 43 subtests count is the broader count excluding the six focused suites
- canonical five-field preimage: 891 UTF-8 bytes, no trailing newline
- canonical six-field SUBP record: 977 UTF-8 bytes, no trailing newline
- CLOSED scope changed: NO
- production and tests unchanged by this documentation-only save
- worktree clean before this documentation-only save
- pushed: NO

Golden values:

- `presented_subject_digest`: `563fb5a4d734474c7b6e0c612ff117f379129a1eeccdaca8afecf8ade60919f1`
- `predicate_digest`: `609fe06b490a1f8cbc269a5db3b2ab3a791da82b7d4059e5ae63e6e6d7ac1c41`
- ordinary SHA-256 fingerprint of the exact canonical record bytes: `11f3251ebb757b39043655d6b333da5b95e7c34fec34936c68df6dddd7933262`

The ordinary SHA-256 fingerprint is a byte fingerprint of the canonical record. It is not the semantic predicate digest.

These are the recorded results against the frozen SUBP golden vector. This Human Final does not add a new independent reproduction, a formal proof, or an external anchoring claim.

## Boundary

This Human Final accepts only the defined SUBP-v0 implementation scope at the fixed SHA above.

The predicate does not establish meaningful text, natural language, JSON, a log, evidence, an evidence kind, a MIME or media type, provenance, authenticity, support, relevance, sufficiency, completeness, truth, authority, independence, freshness, admission, verification, or Human Final.

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
- Association Carriage Receipt v0 unchanged / CLOSED
- PSRD-v0 unchanged / CLOSED
- SUBP-v0 Human Design Freeze unchanged
- SUBP-v0 design document unchanged
- SUBP-v0 production unchanged by this record
- SUBP-v0 tests unchanged by this record
- no public push
- no private push

## Closure

After this record is saved, SUBP-v0 is CLOSED for this defined scope. No further implementation or broad review is authorized under SUBP-v0. Any future enhancement is a new scope or version rather than silent modification of this accepted implementation.

## Change rule

Any future change to accepted SUBP-v0 implementation semantics is a new scope or version and must not silently rewrite this Human Final.

## Push status

NO. No public or remote push is authorized by this record. No push had been performed at the time of this acceptance.
