# Correction ledger — format and policy (1.0.0-rc3)

This is an **immutable, append-only** ledger format for corrections to previously accepted Witness
evidence or maintainer intake decisions. It exists because accepted public evidence becomes
**immutable historical evidence** (see [WITNESS_SUBMISSION.md](WITNESS_SUBMISSION.md)) — a
discovered error, omission, or clarification is never fixed by editing or deleting the original
record. It is fixed by **appending a correction entry** that references the original by commit and
evidence-manifest hash, and that is itself immutable once recorded.

## Core rule

**Corrections append; they never erase original negative evidence.** A correction entry may
supersede a prior entry's *current relevance*, but the prior entry's content, commit reference,
and manifest hash remain permanently in this ledger and in git history. This applies with equal
force whether the original evidence was favorable or unfavorable (a `FAIL`/`INDETERMINATE`
submission's negative evidence is never erased by a later correction, even a correction that
itself records a subsequent successful run).

## Where this ledger lives

- The canonical ledger is this file, appended to via ordinary commits (never `--amend`, never
  force-push, never history rewrite).
- Each Witness submission directory may additionally carry its own local
  `CORRECTION_LEDGER_ENTRIES.txt` (optional) cross-referencing entries here by entry ID, but this
  file is the single authoritative index across all submissions.

## Entry format (template)

Copy this block for every new correction. Fields are free text but **all fields are mandatory**;
leave none blank. `entry_id` must be unique and monotonically increasing (`CL-0001`, `CL-0002`,
...).

```text
### <entry_id>

| Field | Value |
|-------|-------|
| entry_id | CL-XXXX |
| recorded_utc | <UTC timestamp this ledger entry was committed> |
| original_commit | <full 40-char commit SHA of the ORIGINAL accepted submission/evidence> |
| original_evidence_manifest_sha256 | <SHA-256 of the original EVIDENCE_MANIFEST.sha256 file itself, or of its content, as recorded at original acceptance> |
| original_run_id | <run-id of the original submission, e.g. alice-20260722-a1b2c3> |
| correction_commit | <full 40-char commit SHA of the CORRECTION> |
| corrected_evidence_manifest_sha256 | <SHA-256 of the corrected EVIDENCE_MANIFEST.sha256, if the correction includes new/regenerated evidence; "N/A" if the correction is textual/administrative only> |
| reason | <why this correction is needed: what was wrong, missing, or newly discovered> |
| affected_files | <explicit list of file paths changed or added by this correction> |
| supersession_relationship | one of: ADDENDUM (adds information; original stands unchanged) | CLARIFICATION (explains/reinterprets original without changing its facts) | PARTIAL_SUPERSESSION (specific fields of the original are now understood differently; original text is NOT deleted) | FULL_SUPERSESSION (a new run/submission replaces the original for acceptance purposes; original remains as immutable historical record and is marked superseded, not deleted) |
| original_negative_evidence_preserved | yes (mandatory; must always be "yes" — a correction that would set this to "no" is invalid and must be rejected by the maintainer) |
| maintainer_reviewer | <maintainer identity who reviewed and merged this correction> |
| maintainer_intake_verdict_for_correction | PENDING | ACCEPTED | REJECTED | CORRECTION_REQUESTED | DISPUTED (per MAINTAINER_INTAKE_POLICY.md) |
```

## Example (illustrative only — not a real entry)

```text
### CL-0001

| Field | Value |
|-------|-------|
| entry_id | CL-0001 |
| recorded_utc | 2026-08-01T12:00:00Z |
| original_commit | 0000000000000000000000000000000000000000 |
| original_evidence_manifest_sha256 | 1111111111111111111111111111111111111111111111111111111111111111 |
| original_run_id | example-witness-20260731-abc123 |
| correction_commit | 2222222222222222222222222222222222222222 |
| corrected_evidence_manifest_sha256 | 3333333333333333333333333333333333333333333333333333333333333333 |
| reason | Original REDACTIONS.md omitted a redaction log entry for a redacted local username in ENVIRONMENT.txt; the redaction marker was present but unlogged. |
| affected_files | external_verifications/grok-build/witness-submissions/example-witness-20260731-abc123/REDACTIONS.md |
| supersession_relationship | ADDENDUM |
| original_negative_evidence_preserved | yes |
| maintainer_reviewer | example-maintainer-handle |
| maintainer_intake_verdict_for_correction | ACCEPTED |
```

## Policy rules

1. **Append-only.** New entries are added at the bottom of the "Ledger entries" section below (or
   in a dated sub-file if this document grows large; the index in this file must then point to
   it). Existing entries are never edited in place except to fix an entry's own typo via a
   further correction entry that explicitly targets the ledger entry itself.
2. **No deletion.** A ledger entry, once committed, is never removed, even if later found to be in
   error. An erroneous ledger entry is corrected by a subsequent entry that references it.
3. **Original evidence is never modified.** The correction ledger references the original
   evidence's commit and manifest hash; it does not, and must not, involve editing the files at
   that original commit.
4. **Negative evidence is permanent.** `original_negative_evidence_preserved=yes` is mandatory on
   every entry. A correction may add context, add a superseding successful run, or fix a
   clerical/administrative error, but it can never cause a previously recorded `FAIL`,
   `INDETERMINATE`, deviation, or redaction disclosure to disappear from the historical record.
5. **Supersession is explicit, not implicit.** `FULL_SUPERSESSION` must name exactly what replaces
   the original for acceptance purposes (a new run ID / commit), and the original submission's
   status must be explicitly annotated as superseded (e.g. in the claim register), never silently
   dropped from view.
6. **Maintainer review required.** Every correction entry requires its own maintainer intake
   review per [MAINTAINER_INTAKE_POLICY.md](MAINTAINER_INTAKE_POLICY.md) before being marked
   `ACCEPTED` in this ledger.
7. **PR description linkage.** Any PR that introduces a correction must link to the specific
   ledger entry ID it adds (see [WITNESS_SUBMISSION.md](WITNESS_SUBMISSION.md)).

## Ledger entries

_No entries recorded yet. This ledger is part of the 1.0.0-rc3 package policy set; the first
submission that requires a correction appends here. Do not fabricate ledger rows._

## Change log

| Version | Change |
|---------|--------|
| 1.0.0-rc3 | Created. Defines the append-only correction entry format (original commit, original evidence manifest SHA-256, correction commit, corrected manifest SHA-256, reason, affected files, supersession relationship) and the policy rules guaranteeing corrections append and never erase original negative evidence. |
