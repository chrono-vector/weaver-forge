RC4 STATIC BLIND AUDIT — BATCH 3 OF 4 — PART 3
1. Part-3 scope

This final Batch-3 part consolidates the evidence-inventory, schema, manifest, provenance, manual-form, verdict, deviation, redaction, correction, maintainer-intake, submission-lifecycle, and testing findings from Parts 1–2.
No new execution was performed. No Docker command, compiler, bootstrap tool, Witness script, validator, validator test, ldd, or Grok Build product was run. No file, commit, or tag was modified.
All Batch-1 and Batch-2 blockers and limitations remain in force unchanged. This section does not re-audit or restate their detailed technical basis.

2. Files and findings carried forward

Batch 3 reviewed the required normative, template, generator, validator, policy, lifecycle, fixture, and test surfaces, including:

external_verifications/grok-build/witness-package/WITNESS_PACKAGE_MANIFEST.md
external_verifications/grok-build/witness-package/WITNESS_REQUIREMENTS.md
external_verifications/grok-build/witness-package/WITNESS_RUNBOOK.md
external_verifications/grok-build/witness-package/WITNESS_SUBMISSION.md
external_verifications/grok-build/witness-package/WITNESS_CLASSIFICATION.md
external_verifications/grok-build/witness-package/PACKAGE_READINESS_POLICY.md
external_verifications/grok-build/witness-package/CORRECTION_LEDGER.md
external_verifications/grok-build/witness-package/MAINTAINER_INTAKE_POLICY.md
external_verifications/grok-build/witness-package/scripts/run_witness_narrow_build.sh
external_verifications/grok-build/witness-package/scripts/container_narrow_build.sh
external_verifications/grok-build/witness-package/scripts/validate_witness_evidence.py
external_verifications/grok-build/witness-package/scripts/VALIDATOR.md
external_verifications/grok-build/witness-package/scripts/tests/test_validate_witness_evidence.py
all files under external_verifications/grok-build/witness-package/templates/
relevant golden fixtures and fixture builders.
The following evidence contracts were specifically covered:
ENVIRONMENT.txt
WEAVER_FORGE_PACKAGE_IDENTITY.txt
SOURCE_ACQUISITION.txt
SOURCE_IDENTITY.txt
IMAGE_IDENTITY.txt
BOOTSTRAP.txt
CLEAN_TARGET_PROOF.txt
BUILD_COMMAND.txt
BUILD_ENVIRONMENT.txt
BUILD_EXIT_CODE.txt
DOCKER_EXIT_CODE.txt
BUILD_TIMING.txt
ARTIFACT_IDENTITY.txt
STATIC_ARTIFACT_INSPECTION.txt
POST_BUILD_INTEGRITY.txt
DEVIATIONS.txt
WITNESS_STATEMENT.md
WITNESS_VERDICT.md
REDACTIONS.md
EVIDENCE_MANIFEST.sha256
optional auxiliary evidence.
3. Batch-3 scope completion confirmation

All requested Batch-3 topics were inspected:

mandatory, optional, manual, and auxiliary inventory;
template/generator/validator consistency;
supported-outcome applicability;
NOT_REACHED handling;
required/unknown/duplicate/missing/conflicting keys;
value and capitalization vocabularies;
authoritative outcome representation;
current-run provenance;
closed-inventory behavior;
manifest grammar and parsing;
special filenames and object types;
final-manifest lifecycle;
validator-output location;
manual-form requirements;
Witness independence and AI-assistance declarations;
run and identity binding;
verdict vocabulary and ceiling;
PASS prevention;
deviation indexing and aggregation;
redaction restrictions;
correction and supersession lifecycle;
maintainer-intake separation;
negative-outcome submission;
fixture and behavioral-test coverage.
No requested Batch-3 scope item remains uninspected.
4. Confirmed strengths

The following Batch-3 controls are substantively sound:

The required evidence-file list is broadly consistent between the manifest documentation and validator.
Mandatory manual files are clearly distinguished from automated evidence.
Duplicate structured keys are rejected.
Missing required keys are rejected where explicitly declared.
Manifest hashes require 64 lowercase hexadecimal characters.
Manifest lines require two spaces and a safe relative path.
Absolute paths, traversal, backslashes, whitespace paths, self-inclusion, and duplicate manifest entries are rejected.
Symlinks are rejected by the validator.
Unlisted regular files outside the closed inventory are rejected.
Mandatory files other than the manifest must be listed.
Artifact-inapplicable outcomes have explicit nonfabricated representations.
Five build outcomes are consistently named.
The core BUILD_EXIT_CODE.txt outcome rules define Cargo-started, build-status, and Cargo-exit expectations.
Verdict outcome must match BUILD_EXIT_CODE.txt.
Proposed verdict above the computed or recorded ceiling is rejected.
Cargo failure and missing artifact receive FAIL ceilings.
build-not-started and infrastructure failure receive INDETERMINATE ceilings.
failed static inspection reduces the ceiling to PARTIAL.
product execution, ldd, and upstream product-command prohibitions are represented in the manual forms.
AI assistance can be disclosed, while human review remains mandatory.
Negative outcomes may be submitted without being upgraded for appearance.
Witness verdict, maintainer intake, and overall package acceptance are conceptually separate.
Original negative or invalid submissions are normatively intended to remain preserved.
These strengths do not overcome the blockers below.
5. Outcome-by-outcome submission matrix
Outcome	All mandatory files automatically finalized	Explicit inapplicable schema	NOT_REACHED may remain	Manual reconstruction required	One run ID across all files	Manifest covers every submitted file	Validator fails closed	Ceiling correctly recomputed	Incorrect PASS risk
BUILD_NOT_STARTED	No	Partial	Yes	Possible/likely on some failure paths	No global binding	No	Partial	Core outcome ceiling yes; deviations/integrity incomplete	PASS normally blocked by INDETERMINATE ceiling, but package completeness remains defective
INFRASTRUCTURE_FAILURE	No	Partial	Yes	Yes on unexpected or invalid-outcome paths	No global binding	No	Partial	Core outcome ceiling yes	PASS blocked by INDETERMINATE ceiling, but evidence may remain incomplete
CARGO_FAILED	Usually yes on ordinary coded path	Yes for artifact/static files	Normally no	Not normally	No global binding	No	Partial	Core FAIL ceiling yes; deviations not aggregated	PASS blocked by core outcome
CARGO_SUCCEEDED_ARTIFACT_MISSING	Usually yes on ordinary path	Yes	Normally no	Not normally	No global binding	No	Partial	Core FAIL ceiling yes	PASS blocked by core outcome
Artifact present, static inspection failed	Usually yes	Static evidence is applicable but failed	No	Not normally	No global binding	No	Partial	PARTIAL ceiling is computed	PASS blocked for detected static failure
Successful artifact-present	Ordinary files can be finalized	Fully applicable	No expected placeholder	Manual forms and final manifest still required	No machine-wide binding	No	No, not for every normative condition	Incomplete: canonical/deviation/redaction/post-build conditions can be missed	Yes, unsupported PASS eligibility remains possible
Outcome matrix conclusion

Not every supported outcome can currently produce one complete, truthful, final submission without manual reconstruction.
The most serious gaps affect:

unexpected pre-Cargo/container infrastructure failures;
invalid or missing container outcome handling;
generic NOT_REACHED placeholder survival;
host-generated deviation conversion;
manual identity binding;
optional auxiliary manifest omission;
current-run provenance;
normative PASS recomputation.
6. Complete Batch-3 blockers
Evidence inventory and manifest
Optional auxiliary files may exist without manifest coverage.
The final manifest therefore does not necessarily cover every submitted file.
Empty directories and some special filesystem objects can remain outside manifest coverage.
Host closed-inventory enforcement examines only top-level regular files.
Optional auxiliary filenames can receive redirected validator output without mandatory manifest coverage.
Final evidence-directory provenance is not machine-bound to one run.
Manifest hashes prove current bytes, not current-run origin.
evidence_inventory_complete has a circular and contradictory finalization lifecycle.
Schema and generator alignment
Exact generator/template/validator field equality is not enforced.
Unknown and extra structured keys are accepted.
Load-bearing generated fields can remain outside validator semantics.
Template fields and validator-required fields are not consistently equal.
Contract tests generally establish required-key inclusion rather than exact schema equality.
Synthetic fixtures do not prove actual host/container generator output.
Outcome authority and applicability
The validator infers missing or invalid outcomes instead of failing closed.
One complete authoritative outcome tuple is not enforced across all outcome-bearing files.
NOT_REACHED placeholders can survive in final submissions.
BOOTSTRAP.txt, BUILD_COMMAND.txt, and BUILD_ENVIRONMENT.txt lack explicit final not-applicable schemas for unreached stages.
Some failure paths do not finalize every mandatory file.
Some failure packages require manual reconstruction.
Global current-run ID consistency is absent.
Manual form identity binding
WITNESS_STATEMENT.md has no run ID or authoritative outcome.
WITNESS_VERDICT.md run ID is not compared with package identity run ID.
Verdict package tag is not required to equal the fixed rc4 tag or package identity.
Verdict Weaver Forge commit is not cross-checked against package identity or the fixed tag commit.
ai_assistance_detail and upstream_product_commands_not_run are not consistently represented in the required-field schema.
Manual forms can be copied from another run without complete machine detection.
Verdict and PASS prevention
Machine ceiling ignores DEVIATIONS.txt.
canonical_run=no does not independently prohibit PASS.
deviation_state=PRESENT does not independently prohibit PASS.
NONMATERIAL_DISCLOSED can incorrectly retain a PASS deviation ceiling.
Per-deviation ceilings are not automatically aggregated.
General mandatory-evidence incompleteness is not a direct machine-ceiling input.
The validator does not recompute the full normative PASS checklist.
Full post-build integrity failure is not independently enforced in every case.
A successful-looking outcome can retain unsupported PASS eligibility.
Not every normative PASS-preventing condition is independently machine-enforced.
Deviation schema
Host-generated DEVIATIONS.txt does not match the indexed normative schema.
deviation_state=NONE does not reject indexed deviation entries.
Deviation indices need not be numeric.
Deviation indices need not be contiguous.
Orphan deviation fields may be ignored.
Canonical identity impact is self-declared rather than independently derived.
Deviation ceilings are not aggregated into the verdict ceiling.
Manual reconstruction is required to convert host output into normative deviation records.
Redaction
Exact build-command redaction is not prohibited by the implemented keyword set.
Package tag, URL, platform, architecture, and broader identity redactions are incompletely prohibited.
Redaction declarations are not cryptographically or structurally bound to the exact redacted key.
Declared replacement markers need not match the actual marker in the target file.
Misleading redaction labels can evade prohibited-category checks.
Structurally valid evidence can still conceal critical information.
Maintainer intake and correction lifecycle
Initial maintainer_intake_verdict=pending is not contextually enforced.
Validator accepts later intake states in a new submission.
Policy instructs maintainers to mutate WITNESS_VERDICT.md after acceptance.
That mutation conflicts with original-evidence immutability.
Manifest regeneration after intake mutation is unspecified.
Correction-ledger requirements are not machine-enforced.
Original evidence preservation and in-place intake mutation are mutually inconsistent.
The correction/supersession lifecycle is not coherent and noncircular.
Tests
Tests do not prove actual manifest-complete submissions for every outcome.
Tests do not prove mixed-run rejection.
Tests do not prove exact schema equality.
Tests do not prove actual host/container failure finalization.
Tests do not prove canonical-run PASS prevention.
Tests do not prove deviation aggregation.
Tests do not prove numeric contiguous deviation indexing.
Tests do not prove manual run-ID equality.
Tests do not prove initial pending intake.
Tests do not prove correction-ledger and supersession lifecycle.
7. Complete Batch-3 non-fatal limitations
Independence remains a human self-attestation.
Human identity or handle is nonempty but not externally verified.
AI-assistance detail is free text.
Human justification prose is not semantically validated.
A Witness may conservatively propose a verdict below the machine ceiling.
“First matching row governs” wording is less precise than the validator’s stricter-verdict allowance.
Failure-stage values are not centrally enumerated.
Status vocabularies vary by file.
Capitalization intentionally mixes yes/no and YES/NO.
Markdown-compatible parsing ignores prose and malformed pseudo-fields.
Image-pull documentation inaccurately says pull logs occur only on failure.
Manifest generation supports broader filenames than validator grammar permits.
Validator output location depends on caller discipline.
Manifest self-integrity depends on an outer commit, archive, or external digest.
Post-validation immutability is procedural.
Privacy-safe redactions can reduce diagnostic detail.
Redaction prohibition relies on substring matching.
Historical intake revalidation would need a distinct mode.
Git history is relied upon to preserve earlier evidence states.
Synthetic fixtures share assumptions with their fixture builder.
Manual forms require human copying of several automated identity values.
The validator can reject structural defects but cannot prove factual independence or truthfulness.
8. Mandatory corrections
Correction 8.1 — Require manifest coverage for every submitted regular file
Path:
WITNESS_PACKAGE_MANIFEST.md
scripts/validate_witness_evidence.py
manifest tests
Heading/function:
auxiliary inventory;
validate_manifest
Precise change:
Remove the exemption allowing auxiliary files to remain unlisted.
Every regular file under EVIDENCE_DIR, except EVIDENCE_MANIFEST.sha256 itself, must have exactly one manifest entry.
Classification: Mandatory
Why:
The manifest must cryptographically close the complete submission.
Correction 8.2 — Reject every unexpected filesystem object
Path:
scripts/validate_witness_evidence.py
host closed-inventory function
Function:
check_no_symlinks
validate_manifest
enforce_closed_aux_inventory
Precise change:
Recursively reject:
directories other than the evidence root;
nested files;
symlinks;
FIFOs;
sockets;
block devices;
character devices;
any unknown filesystem object.
Classification: Mandatory
Why:
Every submitted object must be manifest-addressable and policy-authorized.
Correction 8.3 — Define exact allowed keys for every structured file
Path:
validator;
all templates;
schema documentation
Function:
replace minimum-only FILE_REQUIRED_FIELDS with exact per-file schemas
Precise change:
Define, per file:
required keys;
optional keys;
allowed values;
conditional keys;
forbidden keys.
Classification: Mandatory
Why:
Unknown load-bearing assertions must not be silently accepted.
Correction 8.4 — Enforce exact generator/template/validator equality
Path:
both Witness scripts;
all templates;
validator;
tests
Test:
new exact-schema contract tests

Precise change:
For each generated structured file:

emitted keys == template keys == validator allowed keys

after accounting for explicitly documented conditional fields.

Classification: Mandatory
Why:
Prevents silent schema drift.
Correction 8.5 — Reject unknown and extra keys
Path: validator
Function: per-file schema validation
Precise change:
Any structured key outside the exact allowed set must fail validation.
Classification: Mandatory
Why:
Unvalidated assertions cannot coexist with a closed evidence contract.
Correction 8.6 — Require exactly one explicit outcome and remove inference
Path: validator
Function: determine_outcome
Precise change:
Delete conservative inference.
Require exactly one valid explicit outcome in every outcome-bearing file.
Classification: Mandatory
Why:
Outcome authority must fail closed.
Correction 8.7 — Define one complete authoritative outcome tuple
Path:
validator;
BUILD_EXIT_CODE.txt;
BUILD_TIMING.txt;
DOCKER_EXIT_CODE.txt;
WITNESS_VERDICT.md;
post-build and artifact schemas

Precise change:
Define and cross-check:

outcome
cargo_started
build_status
cargo_exit_code
docker_exit_code
failure_stage
artifact_present
static_inspection_status
post_build_integrity_ok

with exact outcome-specific rules.

Classification: Mandatory
Why:
One coherent result must appear throughout the package.
Correction 8.8 — Replace NOT_REACHED with explicit final schemas
Path:
BOOTSTRAP.txt
BUILD_COMMAND.txt
BUILD_ENVIRONMENT.txt
generators and validator

Precise change:
Use:

status=NOT_APPLICABLE
stage_reached=no
reason=<exact failure stage>

plus outcome/run identity fields.
Final submissions must reject generic initialization placeholders.

Classification: Mandatory
Why:
Unreached stages require truthful final evidence, not preliminary placeholders.
Correction 8.9 — Add one immutable run ID to every evidence file
Path:
all templates;
both generators;
validator;
manual forms
Field: run_id
Precise change:
Require the exact same run ID in every structured and manual evidence file.
For raw logs, bind them through a manifest metadata table or a companion per-file record.
Classification: Mandatory
Why:
Prevents mixed-run assembly and copied forms.
Correction 8.10 — Atomically create and provenance-bind the evidence directory
Path: host script
Function:
run-ID creation;
evidence initialization
Precise change:
Atomically create an absent directory, reject collisions, write a creation record, and require all generated files to carry the same run ID.
Classification: Mandatory
Why:
Prevents prior/current evidence mixing.
Correction 8.11 — Make evidence_inventory_complete lifecycle noncircular
Path:
WITNESS_PACKAGE_MANIFEST.md
WITNESS_RUNBOOK.md
POST_BUILD_INTEGRITY.txt
Precise change:
Define:
manual forms finalized;
evidence_inventory_complete=yes written;
final manifest generated;
validator run externally;
no further mutation.
Do not claim that the field can be set only after validation.
Classification: Mandatory
Why:
Current ordering requires editing after validation and invalidating the manifest.
Correction 8.12 — Finalize all mandatory files on every failure path
Path:
host script;
container script
Function:
all failure finalizers
Precise change:
Add one schema-aware finalizer covering every mandatory automated file for every supported outcome and unexpected failure.
Classification: Mandatory
Why:
Failure evidence must not require manual reconstruction.
Correction 8.13 — Bind WITNESS_STATEMENT.md to the run and outcome
Path:
templates/WITNESS_STATEMENT.md
validator

Fields:

run_id
package_tag
weaver_forge_commit
grok_build_commit
outcome
Classification: Mandatory
Why:
Prevents reuse of a statement from another run.
Correction 8.14 — Cross-check all WITNESS_VERDICT.md identity fields
Path:
template;
validator
Fields:
run_id;
package_tag;
weaver_forge_commit;
grok_build_commit;
outcome
Precise change:
Require exact equality with package identity, source identity, and authoritative outcome evidence.
Classification: Mandatory
Why:
Manual verdict must refer to this exact run.
Correction 8.15 — Enforce initial maintainer intake as pending
Path:
validator;
WITNESS_VERDICT.md;
intake policy

Precise change:
In initial-submission mode, only:

maintainer_intake_verdict=pending

is valid.
Historical intake must use a separate external record or validator mode.

Classification: Mandatory
Why:
A Witness must not predeclare maintainer acceptance.
Correction 8.16 — Align DEVIATIONS.txt generator, template, and validator
Path:
host script;
templates/DEVIATIONS.txt;
validator;
tests
Precise change:
Generate the exact indexed schema directly. No manual conversion.
Classification: Mandatory
Why:
Deviations are verdict-bearing evidence.
Correction 8.17 — Require numeric contiguous deviation indices
Path: validator
Function: check_deviations

Precise change:
Require:

1..deviation_count

with no gaps, nonnumeric indices, duplicates, or undeclared entries.

Classification: Mandatory
Why:
Ensures complete deterministic parsing.
Correction 8.18 — Reject orphan deviation fields
Path: validator
Precise change:
Discover indices from every deviation_<n>_* key and require the full exact record for each.
Classification: Mandatory
Why:
Prevents ignored deviation assertions.
Correction 8.19 — Aggregate deviation ceilings automatically
Path:
validator;
classification policy
Precise change:
Compute the strictest per-deviation ceiling and include it in the final machine ceiling.
Classification: Mandatory
Why:
Manual synchronization is insufficient.
Correction 8.20 — Prevent PASS for all noncanonical/deviation-present runs
Path: validator
Function: verdict-ceiling computation

Precise change:
Require:

canonical_run=yes
deviation_state=NONE

for PASS eligibility.

Classification: Mandatory
Why:
This is an explicit normative PASS condition.
Correction 8.21 — Enforce NONMATERIAL_DISCLOSED → PARTIAL
Path:
validator;
tests
Precise change:
Set maximum ceiling PARTIAL for this severity.
Classification: Mandatory
Why:
Current implementation conflicts with policy.
Correction 8.22 — Recompute the complete normative PASS checklist
Path:
validator;
WITNESS_CLASSIFICATION.md
Precise change:
Machine-check every PASS requirement:
canonical run;
no deviations;
complete mandatory evidence;
no placeholders;
manifest valid;
exact identity;
static inspection complete;
all four post-build checks yes;
no prohibited execution;
manual forms bound to the run;
redactions semantically permitted.
Classification: Mandatory
Why:
PASS must not depend on unverified manual interpretation.
Correction 8.23 — Enforce full post-build PASS prevention
Path:
validator;
POST_BUILD_INTEGRITY.txt;
host writer

Precise change:
PASS requires:

source_head_unchanged=yes
source_clean_after=yes
cargo_lock_unchanged=yes
cargo_lock_post_matches_expected=yes
post_build_integrity_ok=yes
status=OK
Classification: Mandatory
Why:
Current evidence and validator can disagree.
Correction 8.24 — Bind redactions to exact file, key, and marker
Path:
REDACTIONS.md;
validator

Precise change:
Require:

redaction_<n>_file
redaction_<n>_key
redaction_<n>_original_value_sha256
redaction_<n>_replacement_marker
redaction_<n>_reason

Verify the exact marker occurs at the exact key in the named file.

Classification: Mandatory
Why:
Free-text declarations are too easy to mislabel.
Correction 8.25 — Expand prohibited redaction categories
Path:
template;
validator
Precise change:
Explicitly prohibit redaction of:
commands;
tags;
repository URLs;
platform;
OS;
architecture;
all identities;
hashes and digests;
exits;
outcomes;
statuses;
failure stages;
verdicts;
run IDs;
deviation severity and ceiling.
Classification: Mandatory
Why:
Critical reproducibility evidence must remain visible.
Correction 8.26 — Move maintainer intake to immutable external metadata
Path:
WITNESS_VERDICT.md;
MAINTAINER_INTAKE_POLICY.md;
manifest policy

Precise change:
Keep Witness evidence immutable with:

maintainer_intake_verdict=pending

Create a separate append-only maintainer intake record outside the original evidence manifest or in a separately versioned intake package.

Classification: Mandatory
Why:
Maintainer acceptance must not mutate Witness evidence.
Correction 8.27 — Define append-only correction and supersession packages
Path:
CORRECTION_LEDGER.md;
submission policy;
validator
Precise change:
Each correction must:
preserve the original package;
create a new run/package ID;
include the original manifest digest;
state supersession reason;
include a new complete manifest;
never edit original evidence.
Classification: Mandatory
Why:
Removes the mutation contradiction.
Correction 8.28 — Add behavioral tests using actual writers
Path: scripts/tests/
Precise change:
Invoke real isolated host/container writer functions with mocked external commands and validate the resulting evidence.
Classification: Mandatory
Why:
Source-text and synthetic fixtures do not prove runtime contracts.
Correction 8.29 — Add mixed-run rejection tests
Path: validator tests
Precise change:
Combine valid files from two run IDs and require rejection even if other identities match.
Classification: Mandatory
Why:
Directly verifies current-run binding.
Correction 8.30 — Add manifest-complete submission tests for every outcome
Path:
fixture builder;
validator tests
Precise change:
Produce one actual generator-backed complete directory for:
BUILD_NOT_STARTED;
INFRASTRUCTURE_FAILURE;
CARGO_FAILED;
artifact missing;
static-inspection failed;
successful artifact-present.
Require:
no placeholders;
exact schema;
all files finalized;
all regular files manifested;
correct verdict ceiling.
Classification: Mandatory
Why:
This is the central Batch-3 contract.
9. Recommended hardening
Hardening 9.1 — Centralize all field vocabularies
Paths: validator and schema documentation
Change:
Define central enums for:
status;
failure stage;
applicability;
yes/no casing;
intake state.
Classification: Hardening
Why:
Reduces vocabulary drift.
Hardening 9.2 — Use one canonical casing convention
Paths: all templates and generators
Change:
Prefer lowercase yes|no for boolean declarations and reserve uppercase for outcome/status enums.
Classification: Hardening
Why:
Simplifies parsing and review.
Hardening 9.3 — Add a machine-readable schema specification
Path: new schema file under witness-package/
Change:
Publish JSON Schema, TOML schema, or equivalent for all evidence files and outcome rules.
Classification: Hardening
Why:
Makes exact-field contracts auditable outside Python source.
Hardening 9.4 — Add signed final-submission metadata
Path: submission policy
Change:
Record:
final manifest digest;
run ID;
Witness identity;
submission timestamp;
package commit/tag
in a detached signed statement.
Classification: Hardening
Why:
Strengthens post-validation immutability.
Hardening 9.5 — Separate preliminary and final evidence directories
Path: runbook and host script
Change:
Produce automated evidence in a staging directory, then create a new immutable final directory after manual completion.
Classification: Hardening
Why:
Clarifies finalization and prevents accidental mutation.
Hardening 9.6 — Add a validator mode for historical intake records
Path: validator
Change:
Distinguish:
initial Witness submission;
maintainer intake record;
corrected/superseding package.
Classification: Hardening
Why:
Prevents lifecycle states from being conflated.
Hardening 9.7 — Hash raw logs into structured companion records
Path: manifest and auxiliary schema
Change:
Add byte count and SHA-256 for raw stdout/stderr files.
Classification: Hardening
Why:
Gives raw evidence explicit semantic binding.
Hardening 9.8 — Require normalized human identity metadata
Path: Witness statement
Change:
Add optional organization, public profile, contact method, and conflict-of-interest declaration.
Classification: Hardening
Why:
Improves independent-review credibility without pretending identity can be fully machine-proved.
10. Items explicitly deferred to Batch 4

Batch 4 remains responsible for the overall cross-batch consolidation and final static-audit disposition, including:

combining all Batch-1, Batch-2, and Batch-3 blockers;
determining whether the fixed rc4 package satisfies its stated readiness policy;
reconciling public claims against all static findings;
identifying the minimal remediation sequence;
distinguishing static package defects from matters requiring actual Independent Witness reproduction;
determining whether C-014 may advance from NOT_STARTED;
issuing the final static-audit conclusion, if authorized.
No Batch-4 inspection or conclusion is made here.
11. Batch-3 conclusion without final package-readiness verdict
Required special conclusions

Can every supported outcome currently produce a complete truthful submission without manual reconstruction?
No. Ordinary coded outcomes are better covered, but unexpected infrastructure failures, invalid/missing outcome paths, placeholder handling, and deviation conversion can require manual reconstruction.
Does the final manifest currently cover every submitted file?
No. Optional auxiliary files may remain present and unhashed.
Are all files machine-bound to one current run?
No. A global immutable run ID is not required across the complete evidence set.
Is exactly one authoritative outcome fail-closed?
No. The host is stricter, but the validator can infer missing or invalid outcomes and does not enforce one complete cross-file outcome tuple.
Is PASS structurally impossible under every normative PASS-preventing condition?
No. Noncanonical state, deviation presence, some deviation severities, complete post-build integrity, and other normative requirements are not all independently recomputed.
Are manual forms cryptographically and semantically bound to the same run?
No. The statement lacks run binding, and the verdict’s run ID, package tag, and Weaver Forge commit are not fully cross-checked.
Is the correction and maintainer-intake lifecycle noncircular?
No. In-place intake mutation conflicts with manifest integrity and original-evidence preservation.
Can a mixed-run package pass structural checks?
Potentially yes, where limited identity fields coincide and no global run-ID equality is enforced.
Can optional auxiliary evidence remain unhashed?
Yes.
Can manual forms be copied from another run without detection?
Yes, particularly WITNESS_STATEMENT.md; WITNESS_VERDICT.md is only partially bound.
Can maintainer intake mutate a validated package without a coherent manifest lifecycle?
Yes. Current policy authorizes a mutation but does not define a coherent immutable-manifest update model.
Are negative outcomes submit-able without owner reinterpretation or fabricated artifact evidence?
Normatively yes, and ordinary negative paths have useful explicit models. However, some failure paths still require manual reconstruction because mandatory finalization is incomplete.
Can Batch-3 scope be considered clean?
No. The evidence package is not yet guaranteed to be:

structurally complete for every outcome;
cryptographically closed over every submitted file;
current-run-bound;
free of preliminary placeholders;
protected from mixed-run composition;
fully fail-closed on outcome authority;
fully aligned with normative PASS rules;
immutable through correction and maintainer intake.
No overall final package-readiness verdict is issued.
RC4 BATCH 3 COMPLETE — NO FINAL READINESS VERDICT YET
No Independent Witness reproduction occurred.
No Independent Witness PASS is claimed.
C-014 remains NOT_STARTED.
Do not continue to Batch 4 until instructed.