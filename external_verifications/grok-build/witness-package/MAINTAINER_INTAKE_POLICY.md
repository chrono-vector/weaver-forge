# Maintainer intake policy (1.0.0-rc3)

This document governs how a **maintainer** (not the Witness, not the package author acting as
Witness) reviews and dispositions a submitted Witness evidence package. It is distinct from
[WITNESS_CLASSIFICATION.md](WITNESS_CLASSIFICATION.md) (governs the Witness's own proposed
verdict) and from [PACKAGE_READINESS_POLICY.md](PACKAGE_READINESS_POLICY.md) (governs the
package as a whole). The Witness proposed verdict and the maintainer intake verdict are **always
recorded as separate values** and are never merged into one field.

## Reviewer identity

- The reviewer is a Weaver Forge maintainer with commit/merge authority over `main`, acting in a
  **maintainer** capacity, distinct from any Witness role they may have played elsewhere.
- The reviewer's identity (name/handle) and the review UTC timestamp must be recorded in the PR
  thread and, upon merge, in the claim register update (see below).
- If the same individual is both the submitting Witness and the reviewing maintainer, intake must
  be recorded as `DISPUTED` pending a second, independent maintainer review — self-intake by the
  submitting Witness is never sufficient by itself.

## Independence expectation

- The reviewing maintainer must not be the package owner acting *as* the Witness for that same
  submission, and must not have authored the specific evidence being reviewed.
- The reviewer is expected to have no undisclosed conflict of interest with the outcome of the
  specific submission (e.g. is not personally invested in a particular verdict being accepted).
- Independence gaps must be disclosed in the PR thread rather than silently accepted.

## Validator-output review

- The reviewer re-runs (or requests re-running of) the structural validator
  (`scripts/validate_witness_evidence.py`) against the submitted evidence directory and confirms
  the exit code and printed report independently of anything the submitter claims.
- Structural `PASS` from the validator is a **prerequisite** for acceptance but is never
  sufficient by itself — the validator explicitly does not prove execution, independence, or
  truthfulness (see [scripts/VALIDATOR.md](scripts/VALIDATOR.md)).
- Validator output reviewed during intake must have been captured **outside** the evidence
  directory, consistent with [WITNESS_PACKAGE_MANIFEST.md](WITNESS_PACKAGE_MANIFEST.md).

## Evidence review

The reviewer reads, at minimum:

- `WEAVER_FORGE_PACKAGE_IDENTITY.txt` and `SOURCE_ACQUISITION.txt`/`SOURCE_IDENTITY.txt` for
  tag/commit/`Cargo.lock` consistency against the canonical values in
  [WITNESS_REQUIREMENTS.md](WITNESS_REQUIREMENTS.md).
- `IMAGE_IDENTITY.txt` for digest/platform match.
- `BUILD_EXIT_CODE.txt`, `DOCKER_EXIT_CODE.txt`, `BUILD_TIMING.txt` for outcome consistency.
- `ARTIFACT_IDENTITY.txt`/`STATIC_ARTIFACT_INSPECTION.txt`, `POST_BUILD_INTEGRITY.txt`.
- `WITNESS_STATEMENT.md` for independence, AI-assistance disclosure, and human-review completion.
- `DEVIATIONS.txt` and `REDACTIONS.md` in full, including every enumerated deviation/redaction
  entry, not only the summary fields.
- The PR description fields required by [WITNESS_SUBMISSION.md](WITNESS_SUBMISSION.md).

## Classification application

- The reviewer independently re-derives the expected proposed verdict from
  [WITNESS_CLASSIFICATION.md](WITNESS_CLASSIFICATION.md) using the evidence as recorded, and
  compares it to the Witness's selected line in `WITNESS_VERDICT.md`.
- A mismatch between the reviewer's independent derivation and the Witness's proposed verdict does
  **not** get silently corrected in place. It is recorded (see Disagreement recording, below) and
  either resolved via a correction request to the Witness or accepted with the discrepancy
  documented.

## Intake values (enumerated; exactly one applies per submission)

| Value | Meaning |
|-------|---------|
| `PENDING` | Submitted; not yet reviewed. Matches the required `maintainer_intake_verdict=pending` field in `WITNESS_VERDICT.md` at submission time. |
| `ACCEPTED` | Reviewed; structural validator PASS confirmed; classification independently re-derived and consistent (or consistent within a documented, accepted rationale); evidence merged as public historical record. |
| `REJECTED` | Reviewed; not merged. Structural failure, unresolved independence concern, or a proven prohibited condition (product execution, `ldd` use, falsification) that the Witness does not correct. |
| `CORRECTION_REQUESTED` | Reviewed; specific, itemized defects identified; maintainer has asked the Witness for a correction (new commit/PR, per [CORRECTION_LEDGER.md](CORRECTION_LEDGER.md)) rather than outright rejecting. |
| `DISPUTED` | Reviewer and Witness (or two reviewers) disagree on classification or acceptability; both positions are recorded; not merged until resolved or explicitly merged-with-recorded-dispute. |
| `SUPERSEDED` | A previously `ACCEPTED` submission has been superseded by a later correction per the correction ledger; the original record remains, annotated as superseded, never deleted. |

## Acceptance

Acceptance requires all of:

1. Structural validator `PASS` against the final manifest, independently re-run.
2. Independence, AI-assistance, and human-review declarations present and not contradicted by the
   evidence.
3. No proven `PROHIBITED`-severity condition.
4. The maintainer's independently re-derived classification is recorded alongside the Witness's
   proposed verdict (identical or explicitly reconciled with rationale).
5. Redaction review confirms no material defect, deviation, mismatch, failure, or independence
   conflict was hidden, altered, or softened (see
   [WITNESS_SECURITY_AND_REDACTION.md](WITNESS_SECURITY_AND_REDACTION.md)).

On acceptance, the maintainer merges the PR and updates `WITNESS_VERDICT.md`'s
`maintainer_intake_verdict` field (via a maintainer-authored follow-up commit, never by rewriting
the Witness's original commit) from `pending` to `accepted`, and records the merge commit SHA.

## Rejection

Rejection requires the maintainer to record, in the PR thread and in the claim register:

- The specific defect(s) that caused rejection (cite exact file/field).
- Whether the defect is structural (validator would also have failed with correct enforcement),
  procedural (independence/AI/human-review concern), or a proven prohibited condition.
- That the submission's evidence is **not** deleted from the PR history even if the PR itself is
  closed unmerged — a rejected submission's existence and reasoning remain part of the public,
  auditable record via the closed PR, never silently erased.

## Request for correction

- Used when the submission is fundamentally sound but contains a specific, itemized, correctable
  defect (e.g. a missing field, an incorrect but honestly-recorded value, an incomplete redaction
  log).
- The maintainer opens a specific, itemized request in the PR thread.
- The Witness (or, if unavailable, the maintainer with the Witness's knowledge) submits a
  correction per [CORRECTION_LEDGER.md](CORRECTION_LEDGER.md) — corrections always **append**;
  the original submission and its evidence manifest hash are never edited or erased.

## Disagreement recording

- Any disagreement between the Witness's proposed verdict and the maintainer's independently
  derived classification is recorded verbatim (both values, both rationales) in the PR thread and
  carried into the claim register entry for that submission.
- Disagreements are never resolved by silently overwriting the Witness's original
  `WITNESS_VERDICT.md`. If the maintainer's classification differs, the maintainer records their
  own classification alongside, with rationale, and both remain visible.

## Merge procedure

1. Confirm structural validator PASS (independently re-run, output captured outside the evidence
   directory).
2. Complete the evidence review and classification application above.
3. Record the intake value (`ACCEPTED`, `REJECTED`, `CORRECTION_REQUESTED`, or `DISPUTED`) in the
   PR thread with rationale.
4. If `ACCEPTED`: merge the PR unmodified; then, in a **separate** maintainer-authored commit,
   update `maintainer_intake_verdict` and record the merge SHA. Do not amend or force-push the
   Witness's commit.
5. Update the claim register (`CLAIM_REGISTER.md`) to reference the new submission, its run ID,
   its Witness-proposed verdict, and its maintainer-intake verdict.
6. Evaluate the C-014 transition rule (below).

## C-014 transition rule

- **C-014 (Independent Witness) remains `NOT_STARTED` until at least one submission reaches
  intake value `ACCEPTED` with a Witness-proposed verdict of `PASS` or `PARTIAL`** (a `PARTIAL`
  acceptance moves C-014 to a status explicitly labeled as partial/limited, never to an
  unqualified `PASS`; a `FAIL`/`INDETERMINATE`-verdict acceptance records that a Witness attempt
  occurred and was truthfully reported, but does not by itself satisfy C-014).
- C-014 must never be marked complete, `PASS`, or any status implying successful independent
  reproduction based on: an audit of the package (C-022 through C-025 and any successor audits),
  a maintainer's own testing, or any submission still at `PENDING`, `REJECTED`,
  `CORRECTION_REQUESTED`, or `DISPUTED` intake.
- The specific accepted run ID(s) that satisfy C-014 must be cited by run ID in the claim register
  entry for C-014 at the moment of transition.

## Required public history

- Every submission PR, whether accepted, rejected, or superseded, remains part of the repository's
  public, auditable history (via GitHub PR/issue history) and is never force-deleted.
- The claim register and this package's status documents must, at all times, be reconcilable
  against that public PR/commit history — a reader must be able to trace every readiness or
  C-014 status claim back to a specific commit, tag, and (once merged) PR.
- Corrections and disagreements are additive to this history per
  [CORRECTION_LEDGER.md](CORRECTION_LEDGER.md); nothing in the intake process authorizes deleting
  or rewriting previously published evidence or verdicts.

## Change log

| Version | Change |
|---------|--------|
| 1.0.0-rc3 | Created. Defines reviewer identity, independence expectation, validator-output/evidence review, classification application, enumerated intake values, acceptance/rejection/correction-request/disagreement/merge procedures, C-014 transition rule, and required public history. |
