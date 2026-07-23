RC4 STATIC BLIND AUDIT — BATCH 3 OF 4 — PART 2
Part-2 scope

This part inspected only the manual Witness forms, verdict and classification policy, deviation and redaction models, correction lifecycle, maintainer intake separation, validator enforcement, fixtures, and associated tests.
No Docker command, compiler, bootstrap tool, Witness script, validator, validator test, ldd, or Grok Build product was executed. No files, commits, or tags were modified.

1. WITNESS_STATEMENT.md contract
Finding 1.1 — Core independence declarations are mandatory

Classification: CLEAR

Path: external_verifications/grok-build/witness-package/templates/WITNESS_STATEMENT.md
Fields: not_package_owner, not_owner_side_reproducer, witness_controlled_host
Lines: 13–24
Validator: scripts/validate_witness_evidence.py
Function: check_witness_statement
Lines: 1100–1117
All three declarations must equal:
yes
Finding 1.2 — Independence is self-attested, not independently proved

Classification: CLEAR WITH LIMITATIONS

Path: validator
Function: check_witness_statement
Lines: 1100–1117
The validator confirms the declarations’ presence and vocabulary. It cannot prove:
host ownership;
absence of owner control;
absence of owner-side reproduction;
the Witness’s real-world identity.
Maintainer review is required to assess contradictions.
Finding 1.3 — AI assistance must be disclosed

Classification: CLEAR

Template: templates/WITNESS_STATEMENT.md
Lines: 9–11, 19–21
Validator: lines 1107–1112
Allowed values:
ai_assistance_used=yes|no

When yes, ai_assistance_detail must be nonempty.

Finding 1.4 — ai_assistance_detail is not in the validator’s required-field tuple

Classification: BLOCKED

Path: validator
FILE_REQUIRED_FIELDS["WITNESS_STATEMENT.md"]
Lines: 610–620
The template always contains:
ai_assistance_detail=

but the required-field tuple omits it.
When ai_assistance_used=yes, the semantic checker requires a nonempty value. When no, the key can be missing entirely and still validate.
Generator/template/validator exact-field equality is therefore not maintained.

Finding 1.5 — Human review is mandatory

Classification: CLEAR

Template: lines 9–11, 21
Validator: line 1112
human_review_completed=yes

is required.

Finding 1.6 — An AI-only reviewer cannot truthfully satisfy Independent Witness form requirements

Classification: CLEAR
A nonhuman or AI-only process cannot truthfully set:

human_review_completed=yes
witness_identity_or_handle=<human or accountable public handle>

without an actual human review.
AI assistance is permitted, but it does not replace the human Witness.

Finding 1.7 — Product, ldd, and upstream product-command prohibitions are declared

Classification: CLEAR
Required:

product_executed=NO
ldd_used=NO
upstream_product_commands_not_run=yes
Finding 1.8 — upstream_product_commands_not_run is omitted from required fields

Classification: BLOCKED

Template: templates/WITNESS_STATEMENT.md:24
Validator required tuple: validate_witness_evidence.py:610–620
Semantic check: 1115–1117
The semantic checker treats a missing value as failure, so ordinary validation still detects omission. However, the normative required-field declaration and validator field schema disagree.
Finding 1.9 — The statement has no run ID or outcome

Classification: BLOCKED

Path: templates/WITNESS_STATEMENT.md
Lines: 13–24
The form cannot be machine-linked directly to:
WEAVER_FORGE_PACKAGE_IDENTITY.txt run ID;
WITNESS_VERDICT.md run ID;
the authoritative build outcome.
A copied statement from another run can remain structurally valid if its general declarations are unchanged.
2. WITNESS_VERDICT.md contract
Finding 2.1 — Exactly one proposed-verdict line is required

Classification: CLEAR

Template: templates/WITNESS_VERDICT.md:30
Validator:
VERDICT_LINE_RE: line 165
parse_verdict_selection: lines 1456–1481
The validator rejects:
no proposed-verdict line;
more than one line;
lowercase or mixed-case values.
Finding 2.2 — Proposed verdict vocabulary excludes BLOCKED

Classification: CLEAR
Allowed:

PASS
PARTIAL
FAIL
INDETERMINATE

BLOCKED is a package/readiness or workflow state, not a Witness proposed build verdict.

Finding 2.3 — WITNESS_VERDICT.md contains one explicit outcome field

Classification: CLEAR

Template: lines 17–28
Validator required fields: 621–632
Semantic check: 1242–1246
Finding 2.4 — Verdict outcome must equal BUILD_EXIT_CODE.txt outcome

Classification: CLEAR

Validator: lines 1242–1246
A disagreement is structurally rejected.
Finding 2.5 — Verdict run ID is not compared with package identity run ID

Classification: BLOCKED

Validator:
package identity run ID format check: lines 681–684
verdict run ID format check: lines 1222–1223
There is no cross-file equality check between:
WITNESS_VERDICT.md:run_id
WEAVER_FORGE_PACKAGE_IDENTITY.txt:run_id

Thus the verdict can identify a different syntactically valid run.

Finding 2.6 — Verdict package tag is checked only against grammar

Classification: BLOCKED

Validator: lines 1224–1226
It checks:
^grok-build-witness-v\d+\.\d+\.\d+(-rc\d+)?$

but does not require the exact rc4 tag or equality with package identity.
A different well-formed package tag can appear in WITNESS_VERDICT.md.

Finding 2.7 — Verdict Weaver Forge commit is checked only for hex format

Classification: BLOCKED

Validator: lines 1227–1229
It is not compared with:
the tag-resolved Weaver Forge commit;
package identity evidence;
the fixed rc4 commit.
Finding 2.8 — Grok Build commit is fixed exactly

Classification: CLEAR

Validator: line 1230
It must equal:
98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce
Finding 2.9 — Product and ldd declarations are exact

Classification: CLEAR

Validator: lines 1231–1232
Both must be:
NO
3. Maintainer intake field
Finding 3.1 — Template says new submissions must use pending

Classification: CLEAR

Path: templates/WITNESS_VERDICT.md
Lines: 13, 27
Finding 3.2 — Validator accepts all six lifecycle states

Classification: BLOCKED

Validator:
MAINTAINER_INTAKE_VALUES: lines 167–174
check: lines 1234–1240
Accepted:
pending
accepted
rejected
correction_requested
disputed
superseded

The validator does not distinguish:

initial Witness submission;
later historical revalidation.
A brand-new submission can therefore contain accepted or superseded and still validate structurally.
Finding 3.3 — Witness and maintainer roles are normatively separated

Classification: CLEAR

Path: WITNESS_CLASSIFICATION.md
Lines: 14–17, 75–76
Path: MAINTAINER_INTAKE_POLICY.md
Lines: 54–86
The Witness proposes a verdict. The maintainer assigns intake separately.
Finding 3.4 — Maintainer cannot silently replace the Witness verdict

Classification: CLEAR

Path: MAINTAINER_INTAKE_POLICY.md
Lines: 56–62, 116–123
Any disagreement must remain visible with both positions and rationales.
Finding 3.5 — Intake-policy update procedure conflicts with immutable evidence rules

Classification: BLOCKED

Path: MAINTAINER_INTAKE_POLICY.md
Lines: 91–93, 132–134
It instructs a maintainer to update:
maintainer_intake_verdict=pending

to:

accepted

inside WITNESS_VERDICT.md through a follow-up commit.
But:

the final manifest hashes WITNESS_VERDICT.md;
post-validation edits are prohibited;
CORRECTION_LEDGER.md says original evidence is never modified.
Changing the form invalidates the original manifest unless the manifest is regenerated, which would create a changed evidence package.
4. Verdict ceiling and precedence
Finding 4.1 — Machine ceiling is independently recomputed for a limited set of conditions

Classification: CLEAR WITH LIMITATIONS

Validator:
detect_prohibited_violation: lines 1125–1143
detect_identity_mismatch: lines 1146–1179
compute_verdict_ceiling: lines 1182–1209
It recomputes ceilings for:
product or ldd use;
upstream command use;
selected identity mismatches;
principal build outcome;
static-inspection completeness.
Finding 4.2 — Proposed verdict above machine ceiling is rejected

Classification: CLEAR

Validator: lines 1257–1265
Finding 4.3 — Proposed verdict above recorded ceiling is rejected

Classification: CLEAR

Validator: lines 1252–1271
The effective ceiling is the stricter of:
machine-computed ceiling;
manually recorded ceiling.
Finding 4.4 — A manually understated verdict is accepted

Classification: CLEAR WITH LIMITATIONS
Because a ceiling means the best permitted verdict, the validator accepts any lower-ranked verdict.
Examples:

machine ceiling PASS, proposed FAIL;
machine ceiling PARTIAL, proposed INDETERMINATE.
This is conservative but differs from language in WITNESS_CLASSIFICATION.md saying the first matching row “governs” the proposed verdict.
Finding 4.5 — A manually overstated verdict is rejected

Classification: CLEAR
Both machine and recorded ceilings are applied.

Finding 4.6 — Recorded ceiling need not equal the machine ceiling

Classification: CLEAR WITH LIMITATIONS
The Witness may record a stricter ceiling. A looser recorded ceiling does not override a stricter machine result.

Finding 4.7 — Machine ceiling does not include deviation evidence

Classification: BLOCKED

Validator: compute_verdict_ceiling
Lines: 1182–1209
Inputs are only:
outcome
prohibited
identity_mismatch
static_inspection_incomplete

DEVIATIONS.txt is not supplied to the computation.

Finding 4.8 — canonical_run=no is not itself a machine PASS blocker

Classification: BLOCKED
The ceiling logic does not directly inspect:

WEAVER_FORGE_PACKAGE_IDENTITY.txt:canonical_run

A noncanonical run can remain machine-PASS-eligible when its deviation does not trigger the validator’s selected identity-mismatch detectors.

Finding 4.9 — deviation_state=PRESENT is not itself a machine PASS blocker

Classification: BLOCKED
Normative policy requires:

canonical_run=yes
deviation_state=NONE

for PASS.
The validator does not independently enforce either condition as part of the machine ceiling.

Finding 4.10 — NONMATERIAL_DISCLOSED can incorrectly retain a PASS deviation ceiling

Classification: BLOCKED

Policy: WITNESS_CLASSIFICATION.md:28–30, 60–65
NONMATERIAL_DISCLOSED must cap the verdict at PARTIAL.
Validator: check_deviations, lines 1295–1307
Only:
MATERIAL_NONCANONICAL
PROHIBITED

are placed in DEVIATION_SEVERITY_FORBIDS_PASS.
Thus:

deviation_1_severity=NONMATERIAL_DISCLOSED
deviation_1_verdict_ceiling=PASS

is structurally accepted.

Finding 4.11 — Machine and normative ceilings can disagree

Classification: BLOCKED
The policy itself acknowledges orchestrator-policy disagreement at:

WITNESS_CLASSIFICATION.md:81–82
The validator introduces additional disagreement because deviation severity and canonical-run state are not incorporated into its machine ceiling.
5. Outcome-specific proposed verdicts
Finding 5.1 — Cargo failure ceiling is FAIL

Classification: CLEAR

Validator: lines 1203–1204
Finding 5.2 — Missing artifact ceiling is FAIL

Classification: CLEAR

Finding 5.3 — Build-not-started and infrastructure failure ceilings are INDETERMINATE

Classification: CLEAR

Validator: lines 1205–1206
Finding 5.4 — Static-inspection failure ceiling is PARTIAL

Classification: CLEAR

Validator: lines 1207–1208
Finding 5.5 — Successful artifact-present run can be PASS-eligible

Classification: CLEAR WITH LIMITATIONS
Only if no earlier machine-detected condition applies.
The validator does not independently check every normative PASS condition.

Finding 5.6 — BLOCKED has no eligibility in WITNESS_VERDICT.md

Classification: CLEAR
Blocked execution conditions map to:

BUILD_NOT_STARTED;
INFRASTRUCTURE_FAILURE;
proposed INDETERMINATE;
or to an external readiness state.
6. PASS-prevention analysis
Finding 6.1 — Missing mandatory files cause validator failure

Classification: CLEAR

Validator: lines 1614–1619
A structurally accepted package cannot omit a required file.
Finding 6.2 — Manifest defects cause validator failure

Classification: CLEAR
A proposed PASS line may remain textually present, but the package does not validate.

Finding 6.3 — Validator errors prevent structural validator PASS

Classification: CLEAR
The validator returns nonzero when errors exist.

Finding 6.4 — Permitted NOT_REACHED placeholders do not automatically prevent a PASS proposal

Classification: CLEAR WITH LIMITATIONS
Placeholder eligibility is limited to:

BUILD_NOT_STARTED
INFRASTRUCTURE_FAILURE

whose machine ceiling is INDETERMINATE.
Therefore those particular placeholders cannot coexist with a validator-accepted proposed PASS under normal outcome consistency.

Finding 6.5 — Other incomplete evidence may not always reduce the computed ceiling

Classification: BLOCKED
Normative policy says any mandatory evidence incompleteness caps the verdict at PARTIAL or INDETERMINATE.
The machine ceiling does not receive a general:

mandatory_evidence_incomplete

signal.
Many structural errors make the validator fail, but the computed ceiling can still display PASS before final error aggregation.

Finding 6.6 — PASS is not structurally impossible for every noncanonical run

Classification: BLOCKED
Because:

canonical_run=no is not a direct ceiling input;
deviation state is not a direct ceiling input;
Rust/DotSlash and other nonidentity procedural deviations may evade identity mismatch detection.
Finding 6.7 — PASS is structurally impossible after detected static-inspection failure

Classification: CLEAR
The machine ceiling becomes PARTIAL.

Finding 6.8 — PASS is not independently prevented for every post-build integrity failure

Classification: BLOCKED
Carried from Batch 2:

not all four post-build conditions are explicitly required;
POST_BUILD_INTEGRITY.txt can say status=OK while its gate is false;
some generated gate fields are not validator-enforced.
Finding 6.9 — PASS checklist is more complete than machine enforcement

Classification: BLOCKED

Path: WITNESS_CLASSIFICATION.md
Lines: 84–103
The checklist requires:
all mandatory evidence non-placeholder;
structural validator PASS;
canonical_run=yes;
deviation_state=NONE;
complete post-build integrity.
The machine ceiling does not independently recompute all of these.
7. Deviation schema
Finding 7.1 — No-deviation state is explicit

Classification: CLEAR

Template: templates/DEVIATIONS.txt
Lines: 11–12
deviation_state=NONE
Finding 7.2 — deviation_state=NONE does not reject enumerated deviation entries

Classification: BLOCKED

Validator: check_deviations
Lines: 1274–1281
When state is NONE, the function returns immediately.
A file can contain:
deviation_state=NONE
deviation_1_description=...
deviation_1_severity=...

without deviation-semantic rejection.

Finding 7.3 — Present deviations require four principal fields

Classification: CLEAR
For every discovered severity index:

description;
severity;
canonical identity impact;
verdict ceiling.
Finding 7.4 — Indices are not required to be numeric

Classification: BLOCKED

Validator regex: line 1283
deviation_(\w+)_severity

Accepts indices such as:

alpha
x_1
Finding 7.5 — Indices are not required to be contiguous

Classification: BLOCKED
The validator accepts indices such as:

1
3
9

with no gap rejection.
This contradicts the template’s contiguous-index requirement.

Finding 7.6 — An entry without a severity field may be ignored

Classification: BLOCKED
Indices are discovered only from:

deviation_<n>_severity

An orphan:

deviation_2_description=...

does not create a checked index.
Unknown extra keys are accepted.

Finding 7.7 — Duplicate deviation keys are rejected generically

Classification: CLEAR
parse_kv rejects duplicate keys.

Finding 7.8 — Canonical identity impact is not semantically tied to actual identity evidence

Classification: BLOCKED
The validator checks only:

yes|no

It does not independently determine whether the described deviation changed a canonical identity.

Finding 7.9 — Per-deviation ceilings are not aggregated

Classification: BLOCKED
The validator validates each value’s vocabulary and limited severity rule, but does not compute the strictest deviation ceiling and compare it to:

WITNESS_VERDICT.md:verdict_ceiling;
the proposed verdict;
the machine ceiling.
The existing test manually sets the verdict’s recorded ceiling to PARTIAL, so it does not prove automatic aggregation.
Finding 7.10 — Host-generated deviations cannot be cleanly finalized without reconstruction

Classification: BLOCKED
Carried from Batch 1:
the host output uses a changed-field summary rather than the indexed normative schema.
The Witness must reinterpret and manually rewrite the generated output into a different structure.

8. Redaction model
Finding 8.1 — REDACTIONS.md can truthfully declare none

Classification: CLEAR
Required form:

redaction_state=NONE
semantic_integrity_declaration=yes

Validator additionally rejects any visible redaction marker elsewhere.

Finding 8.2 — Present redactions require indexed file, field, reason, and marker

Classification: CLEAR

Validator: lines 1319–1337
Finding 8.3 — Marker/declaration file-level consistency is checked

Classification: CLEAR

Validator: check_redaction_marker_consistency
Lines: 1352–1399
An undeclared marker or declaration without a marker fails.
Finding 8.4 — Prohibited categories include many critical values

Classification: CLEAR WITH LIMITATIONS

Template: templates/REDACTIONS.md:6–9
Validator keyword list: lines 182–202
Protected categories include:
commits;
digests and SHA-256;
exit codes;
independence;
artifact size/hash;
outcome;
build status;
failure stage;
verdicts;
canonical run;
verdict ceiling.
Finding 8.5 — Exact command redaction is not actually keyword-protected

Classification: BLOCKED
The validator’s error message says exact commands must never be redacted, but PROHIBITED_REDACTION_KEYWORDS does not contain:

command
build_command

A honestly declared redaction targeting build_command is not rejected by the shown keyword list.

Finding 8.6 — Package tags and general identity fields are incompletely protected

Classification: BLOCKED
The prohibited list contains:

commit;
digest;
canonical_run.
It does not generally contain:
tag
identity
URL
platform
architecture

A redaction of package_tag or another critical identity field can evade category rejection if the declaration uses that exact field name.

Finding 8.7 — Prohibited-category enforcement trusts the declaration text

Classification: BLOCKED

Validator: lines 1338–1349
It scans only:
redaction_<n>_field
redaction_<n>_reason

A misleading benign label can conceal a prohibited redaction in the target file.
The validator does not map the marker to the exact structured key or replaced bytes.

Finding 8.8 — Marker text is not required to equal the declared replacement marker

Classification: BLOCKED
The validator checks:

that the declared marker contains [REDACTED;
that the target file contains some redaction marker.
It does not require the exact declared marker to occur in that file.
Finding 8.9 — Redacted evidence can remain structurally valid

Classification: CLEAR WITH LIMITATIONS
This is intentional for privacy-safe, nonsemantic fields such as host CPU model.
However, the enforcement gaps above mean structural validity does not guarantee that critical evidence was not hidden.

9. Correction and post-validation mutation
Finding 9.1 — Post-validation editing is prohibited

Classification: CLEAR

Path: WITNESS_RUNBOOK.md
Lines: 383–390
After final validation passes, no further evidence-directory edits should occur.
Finding 9.2 — Every correction should regenerate relevant manifest coverage

Classification: CLEAR WITH LIMITATIONS
Corrections that include changed or regenerated evidence require a corrected manifest hash in the correction ledger.
The process is policy-driven, not validator-enforced.

Finding 9.3 — Correction ledger is not machine-enforced

Classification: BLOCKED

Path: CORRECTION_LEDGER.md
Lines: 1–103
It is not part of the required evidence inventory and the validator does not parse it.
The validator cannot enforce:
append-only behavior;
original-negative-evidence preservation;
original manifest references;
supersession relationship;
correction review.
Finding 9.4 — Original invalid or negative submissions are required to remain preserved

Classification: CLEAR

Path: CORRECTION_LEDGER.md
Lines: 12–16, 83–94
Path: MAINTAINER_INTAKE_POLICY.md
Lines: 95–104, 156–165
Finding 9.5 — Policy contains a direct mutation contradiction

Classification: BLOCKED

CORRECTION_LEDGER.md:83–89:
original evidence is never modified.
MAINTAINER_INTAKE_POLICY.md:91–93, 132–134:
update WITNESS_VERDICT.md after acceptance.
Both cannot be applied literally to the same evidence package.
Finding 9.6 — Manifest-regeneration requirements after intake mutation are unspecified

Classification: BLOCKED
Updating WITNESS_VERDICT.md invalidates:

EVIDENCE_MANIFEST.sha256

The policy does not state whether to:

regenerate the manifest;
retain the original manifest and add an external annotation;
create a separate intake metadata file.
Finding 9.7 — Prior submitted evidence can be changed in a later commit despite “merge unmodified”

Classification: AMBIGUOUS
The Witness commit remains in history, but the accepted tree’s evidence bytes change in the follow-up commit.
This preserves Git history but not a single immutable evidence-directory state.

10. Submission and negative outcomes
Finding 10.1 — Negative outcomes are explicitly accepted without upward reinterpretation

Classification: CLEAR

Path: WITNESS_CLASSIFICATION.md
Line: 78
Path: WITNESS_RUNBOOK.md
Lines: 239–253
A truthful:
FAIL;
INDETERMINATE;
negative outcome
must not be hidden or upgraded merely for appearance.
Finding 10.2 — Maintainer intake is separate from execution outcome

Classification: CLEAR
A submission with a negative Witness result can still be:

accepted as truthful historical evidence;
rejected for structural or independence defects;
without changing the recorded execution outcome.
Finding 10.3 — Package acceptance is separated from Witness execution result

Classification: CLEAR

Path: WITNESS_CLASSIFICATION.md
Lines: 105–115
A Witness PASS does not itself establish overall package readiness.
Finding 10.4 — Maintainer may classify differently but must document it

Classification: CLEAR
No silent upgrade is authorized.

Finding 10.5 — Initial intake state is represented inconsistently

Classification: BLOCKED
Documents require:

maintainer_intake_verdict=pending

for a new submission, but the validator accepts all lifecycle values without contextual distinction.

11. Manual forms across all supported outcomes
Finding 11.1 — WITNESS_STATEMENT.md can be truthfully completed for every outcome

Classification: CLEAR WITH LIMITATIONS
The declarations concern:

reviewer role;
host control;
prohibited execution;
AI assistance;
human review.
They are outcome-independent.
Finding 11.2 — WITNESS_VERDICT.md supports all five outcomes

Classification: CLEAR
Its outcome field uses the same five-value vocabulary.

Finding 11.3 — Manual forms require some values not directly generated into the forms

Classification: CLEAR
The Witness must copy or derive:

run ID;
Weaver Forge commit;
authoritative outcome;
verdict ceiling;
proposed verdict;
intake state.
Finding 11.4 — Copying those values is not fully cross-validated

Classification: BLOCKED
Only outcome and Grok Build commit receive strong equality/fixed checks.
Run ID, package tag, and Weaver Forge commit do not receive complete cross-file equality enforcement.

Finding 11.5 — Some failure outcomes cannot be finalized without manual reconstruction

Classification: BLOCKED
Carried forward from Parts 1 and Batch 2:

placeholders may survive;
unexpected failure finalizers are incomplete;
host deviation output requires conversion;
post-build evidence can remain contradictory.
12. Tests and fixtures
Finding 12.1 — Proposed verdict above machine ceiling is tested

Classification: CLEAR

Path: scripts/tests/test_validate_witness_evidence.py
Tests: lines 379–396
Finding 12.2 — Verdict/outcome mismatch is tested

Classification: CLEAR

Lines: 320–328
Finding 12.3 — Deviation-ceiling test relies on a manually synchronized verdict ceiling

Classification: BLOCKED

Lines: 711–733
The test creates:
deviation_1_verdict_ceiling=PARTIAL
WITNESS_VERDICT.md:verdict_ceiling=PARTIAL

It does not prove that the validator derives PARTIAL automatically from the deviation.

Finding 12.4 — No test proves NONMATERIAL_DISCLOSED forbids PASS

Classification: MISSING

Finding 12.5 — No test proves canonical_run=no forbids PASS

Classification: MISSING

Finding 12.6 — No test proves deviation_state=NONE rejects indexed entries

Classification: MISSING

Finding 12.7 — No test proves numeric contiguous deviation indexing

Classification: MISSING

Finding 12.8 — Redaction tests cover one prohibited and one permitted category

Classification: CLEAR WITH LIMITATIONS

Lines: 469–513
They do not test:
package tag;
exact build command;
misleading redaction labels;
marker-to-declaration exact equality.
Finding 12.9 — Witness and verdict fixtures are synthetic

Classification: CLEAR WITH LIMITATIONS

Path: scripts/tests/fixtures_lib.py
Functions: _witness_statement, _witness_verdict, _deviations, _redactions
Lines: approximately 853–923
They are not built from actual completed manual forms attached to actual host-generated evidence.
Finding 12.10 — No test cross-checks verdict run ID with package run ID

Classification: MISSING

Finding 12.11 — No test enforces initial intake pending

Classification: MISSING

Finding 12.12 — No test covers correction-ledger or post-validation mutation coherence

Classification: MISSING

13. Special confirmations
WITNESS_VERDICT.md contains exactly one explicit authoritative outcome

Result: CLEAR WITH LIMITATIONS
One outcome= key is required and duplicate keys are rejected. The validator’s general outcome inference remains a separate Batch-3 Part-1 blocker.

Verdict outcome equals BUILD_EXIT_CODE.txt

Result: CLEAR

Verdict run ID equals package identity run ID

Result: BLOCKED
No equality check exists.

Proposed verdict must be at or below machine ceiling

Result: CLEAR

PASS impossible whenever mandatory evidence is incomplete

Result: CLEAR WITH LIMITATIONS
A final validator PASS is impossible when the incompleteness generates a validator error. The machine ceiling itself does not independently encode every incompleteness condition.

PASS impossible whenever a permitted placeholder remains

Result: CLEAR
Permitted placeholders occur only with outcomes capped at INDETERMINATE.

PASS impossible for all noncanonical runs

Result: BLOCKED
canonical_run=no and all deviation states are not incorporated into machine ceiling computation.

PASS impossible after static-inspection failure

Result: CLEAR

PASS impossible when post-build integrity fails

Result: BLOCKED
Not every four-field post-build defect is independently enforced.

Validator independently detects every PASS-preventing condition

Result: BLOCKED
It omits several normative conditions.

AI-only work can be represented without false human independence

Result: CLEAR
It can be represented as AI-assisted work only when a human actually completes and attests to the review. AI-only work cannot truthfully claim Independent Witness status.

Every deviation has one exact indexed schema

Result: BLOCKED
Indices are not numeric/contiguous and orphan fields can be ignored.

Redactions prohibit hiding every identity/outcome/hash/exit/failure field

Result: BLOCKED
Coverage and declaration-binding are incomplete.

Correction and mutation rules are coherent and noncircular

Result: BLOCKED
The intake follow-up edit conflicts with manifest immutability and correction-ledger rules.

Negative outcomes can be submitted without owner reinterpretation

Result: CLEAR

14. Newly identified Batch-3 Part-2 blockers
WITNESS_STATEMENT.md omits run ID and outcome, preventing direct current-run binding.
ai_assistance_detail and upstream_product_commands_not_run are not consistently represented in the validator’s required-field schema.
WITNESS_VERDICT.md run ID is not compared with package identity run ID.
WITNESS_VERDICT.md package tag is grammar-checked but not required to equal the fixed rc4 tag or package identity.
WITNESS_VERDICT.md Weaver Forge commit is format-checked but not cross-checked against package identity or the fixed commit.
A new submission is not machine-required to use maintainer_intake_verdict=pending.
Machine verdict-ceiling computation ignores DEVIATIONS.txt.
canonical_run=no does not independently prohibit a machine PASS ceiling.
deviation_state=PRESENT does not independently prohibit PASS.
NONMATERIAL_DISCLOSED incorrectly permits a declared PASS ceiling despite normative PARTIAL policy.
General mandatory-evidence incompleteness is not an explicit machine-ceiling input.
Normative PASS checklist conditions are more extensive than validator machine enforcement.
deviation_state=NONE does not reject enumerated deviation entries.
Deviation indices are neither numeric nor required to be contiguous.
Orphan deviation fields can be ignored when no corresponding severity key exists.
Canonical identity impact is self-declared rather than checked against actual evidence.
Per-deviation ceilings are not automatically aggregated into the verdict ceiling.
Host-generated deviation evidence requires manual reconstruction into the normative indexed schema.
Exact build-command redaction is not prohibited by the implemented keyword set.
Package-tag and other critical identity redactions are incompletely prohibited.
Prohibited-redaction enforcement trusts manually supplied field/reason labels rather than binding to the actual redacted key.
Declared redaction markers need not exactly match markers in target files.
Correction-ledger requirements are not machine-enforced.
The instruction to update WITNESS_VERDICT.md after acceptance conflicts with original-evidence immutability.
Manifest regeneration after maintainer intake mutation is unspecified.
Initial maintainer intake status is represented inconsistently between policy and validator.
Manual verdict identity values other than outcome/Grok commit are not fully cross-validated.
Tests do not prove automatic deviation-ceiling computation, canonical-run PASS prevention, numeric contiguous deviation indices, run-ID equality, initial pending intake, or correction lifecycle coherence.
15. Newly identified Batch-3 Part-2 non-fatal limitations
Independence remains a human self-attestation subject to maintainer review.
A human may conservatively propose a verdict stricter than the machine ceiling.
The classification document’s “first matching row governs” wording is less clear than the validator’s “any stricter verdict is acceptable” rule.
AI assistance detail is free text and not normalized.
witness_identity_or_handle is nonempty but not token- or identity-verified.
failure_stage remains free-form and complicates exact classification precedence.
Redaction prohibition relies on substring matching.
Permitted privacy redactions may reduce diagnostic richness while remaining structurally valid.
Correction and intake guarantees depend heavily on Git and public PR history rather than evidence-directory validation.
Historical revalidation needs a distinct mode if non-pending intake values are to remain accepted.
Human justification prose is not semantically validated.
Manual forms are tested through synthetic fixtures, not actual finalized submissions.
16. Earlier blockers carried forward unchanged
Batch-1 blockers
Current normative documents still describe fixed rc4 as under preparation, pending commit/tag, or not yet published.
Change-log/status claims say pending wording was removed, but contradictory current wording remains.
rc4 is not represented as an already-published immutable release.
docker version and docker context show execute before package/source identity and Cargo.lock checks.
Raw annotated-tag object type is not enforced.
Host-generated DEVIATIONS.txt is incompatible with its normative template and validator schema.
Rust/DotSlash version deviations do not receive FAIL-level treatment.
A preexisting EVIDENCE_DIR is merged instead of atomically rejected.
Evidence-directory collision can mix prior/current run evidence.
Behavioral host-safety coverage is missing.
Actual host-generated noncanonical evidence is not tested.
Public/change-log statements overclaim closure.
Batch-2 blockers
The Grok Build source is reachable read-only at /src and read-write at /work/grok-build.
Unexpected container failures do not finalize every mandatory automated evidence file.
Invalid or missing container outcome handling does not comprehensively finalize evidence or capture post-build integrity.
Host success is not conditioned on validator success or full schema validation.
The host validates only outcome= rather than the full authoritative outcome tuple.
POST_BUILD_INTEGRITY.txt records status=OK even when its technical gate is false.
POST_BUILD_INTEGRITY generator, template, and validator fields are not aligned.
The validator does not explicitly require all four post-build integrity conditions to be yes.
Behavioral tests do not prove actual host/container outcome preservation, evidence finalization, mount isolation, or final exit behavior.
A global claim that false success is impossible is unsupported.
Batch-3 Part-1 blockers
Optional auxiliary files may be present without manifest coverage.
The final manifest does not necessarily cover every submitted file.
Generator, template, and validator exact-field equality is not enforced.
Unknown and extra structured keys are accepted.
The validator infers missing or invalid outcomes instead of failing closed.
A complete authoritative outcome tuple is not enforced across all outcome-bearing files.
NOT_REACHED placeholders may survive into final submissions.
No machine-enforced current-run provenance exists across all evidence.
Host closed-inventory enforcement checks only top-level regular files.
Optional auxiliary filenames may receive redirected validator output without mandatory manifest coverage.
evidence_inventory_complete has a circular finalization lifecycle.
Bootstrap/build-command/build-environment failures use generic placeholders rather than explicit final inapplicable schemas.
Some failure packages require manual reconstruction.
Exact generator/template/validator field equality is not enforced by contract tests.
A complete final inventory can omit allowed auxiliary evidence.
Empty directories and some special filesystem objects are outside manifest coverage.
Current-run origin is not established by the manifest.
Final post-validation immutability is procedural rather than intrinsically enforced.
17. Earlier non-fatal limitations carried forward unchanged
Batch-1 limitations
Public discoverability is strong, but stale pre-publication wording creates uncertainty.
rc4 immutability is defined prospectively rather than reflected as already published.
canonical_run capitalization differs across generated files.
The machine ceiling covers identity overrides only; full classification still depends on policy.
Rust/DotSlash override handling conflicts with stricter fixed-version expectations elsewhere.
The evidence run-ID fallback can collide within one second.
HOST_RUN_METADATA.txt has no normative template or validator schema.
Contract tests inspect source-text key presence rather than actual runtime output.
Golden fixtures are synthetic and share assumptions with their builder.
WITNESS_ID behavior lacks a valid/invalid behavioral matrix.
WORK_ROOT dangerous-path and repository-overlap behavior lacks a matrix.
Nonempty reset authorization lacks behavioral tests.
Managed-child symlink safety lacks target-survival testing.
Package detached-state probe lacks a dedicated isolated test.
Annotated-tag versus lightweight-tag behavior lacks testing.
Docker command ordering lacks a test.
Closed-inventory validation checks filenames, not current-run provenance.
canonical_run vocabulary is not normalized.
“Fixtures cannot drift” applies only relative to the shared builder, not the scripts.
Docker metadata-query failures are converted to UNKNOWN and remain acceptable only if informational.
Tag dereference proves commit resolution but not the raw annotated-tag object type.
Evidence-directory randomness is not backed by atomic creation.
Some strong host controls are only textually tested.
Optional auxiliary evidence carries load-bearing information without schema validation.
Batch-2 limitations
RepoDigest comparison uses substring matching instead of exact normalized member comparison.
Docker inspect stderr is discarded.
OS and architecture failures share a generic platform failure stage.
Image pull logs are not semantically validated.
Apt package versions are unpinned.
dpkg-query is best effort.
Apt and DotSlash detailed logs remain outside EVIDENCE_DIR.
RUSTUP_HOME is inherited from the image.
The full writable WORK_ROOT mount weakens path isolation beyond the source-alias blocker.
Evidence has multiple writable mount aliases.
Protoc output is not semantically version-pinned.
Cargo executes through bash -c.
Rust/Cargo version parsing captures only x.y.z, not full tool provenance.
Pre-Cargo BUILD_NOT_STARTED handlers generally collapse their own exit to 1 rather than preserving underlying bootstrap-tool exits.
Static-inspection failure keeps the artifact-present build outcome and relies on status/exit/ceiling to prohibit PASS.
Container and host duplicate expected constants and must remain synchronized.
Network mode is bridge, so dependency/bootstrap acquisition is not network-isolated.
Host outcome parsing defaults missing cargo_started to NO.
BUILD_TIMING tuple consistency is only partly validator-enforced.
Validator outcome inference is more permissive than host outcome authority.
Extra host-generated fields are not rejected merely because they are absent from templates.
Product/ldd prohibition is statically established, not behaviorally traced.
Batch-3 Part-1 limitations
Documentation says image pull logs are present only on pull failure, while the host writes them for every pull attempt.
Empty directories can remain in EVIDENCE_DIR without manifest coverage.
Special nonregular objects other than symlinks are not explicitly rejected.
The manifest generator accepts filesystem names broader than the validator’s permitted grammar.
Post-validation immutability is procedural rather than enforced.
Validator output location depends on caller redirection discipline.
Failure-stage values are not centrally enumerated.
Status vocabularies vary by file.
Field capitalization intentionally mixes lowercase and uppercase vocabularies.
Manifest self-integrity depends on the containing commit/archive or an external hash.
Synthetic fixtures prove structural expectations, not actual shell runtime output.
Markdown-compatible parsing ignores non-key prose and malformed pseudo-fields.
18. Batch-3 items remaining for Part 3

Part 3 remains to consolidate Batch 3 and inspect any still-unresolved cross-contract issues concerning:

whether one complete evidence package can be submitted for every supported outcome;
complete PASS/PARTIAL/FAIL/INDETERMINATE decision closure;
manifest, manual-form, validator, and submission lifecycle integration;
final Batch-3 blocker and limitation lists;
exact mandatory corrections for Batch-3 defects;
separation of mandatory corrections from recommended hardening;
confirmation of all Batch-3 scope completion.
Part 3 must not begin Batch 4 and must not issue the overall final package-readiness verdict.
RC4 BATCH 3 — PART 2 COMPLETE
No Independent Witness reproduction occurred.
No Independent Witness PASS is claimed.
C-014 remains NOT_STARTED.
Do not continue to Part 3 until instructed.