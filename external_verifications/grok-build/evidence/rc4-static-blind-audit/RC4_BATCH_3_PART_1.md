RC4 STATIC BLIND AUDIT — BATCH 3 OF 4 — PART 1
Part-1 scope

This part inspected the evidence inventory, file schemas, generators, validator contracts, fixture model, and manifest lifecycle for the fixed rc4 snapshot.
The purpose was to determine whether each supported outcome can be represented as one truthful, structurally complete evidence package without manually fabricating inapplicable evidence.
No Witness script, validator, validator test, Docker command, compiler, bootstrap tool, product, or static-analysis command was executed.

1. Mandatory automated evidence inventory
Finding 1.1 — The normative required-file list and validator REQUIRED_FILES are aligned

Classification: CLEAR

Path: external_verifications/grok-build/witness-package/WITNESS_PACKAGE_MANIFEST.md
Heading: Required files
Lines: 16–41
Path: external_verifications/grok-build/witness-package/scripts/validate_witness_evidence.py
Constant: REQUIRED_FILES
Lines: 83–108
Both define the same 25 required files:
19 automated structured/raw evidence files;
four manual files;
the final manifest;
redaction evidence.
Finding 1.2 — Host automated initialization covers 19 automated files

Classification: CLEAR

Path: scripts/run_witness_narrow_build.sh
Constant: MANDATORY_EVIDENCE_FILES
Lines: 80–104
The host initializes:
package, environment, source, image, bootstrap, target, build, Docker, artifact, inspection, and post-build files.
Raw stream files are included.
Finding 1.3 — Manual files are correctly excluded from automated placeholder initialization

Classification: CLEAR

Path: same
Comment/arrays
Lines: 106–121
The host does not claim to complete:
WITNESS_STATEMENT.md;
WITNESS_VERDICT.md;
REDACTIONS.md;
final EVIDENCE_MANIFEST.sha256.
DEVIATIONS.txt is host-generated separately.
Finding 1.4 — The host’s automated inventory is not itself the complete submission inventory

Classification: CLEAR
The host produces preliminary automated evidence. A structurally complete submission additionally requires:

all manual forms;
final manifest regeneration;
final structural validation.
2. Optional automated and auxiliary inventory
Finding 2.1 — The validator defines a closed four-file auxiliary set

Classification: CLEAR

Path: scripts/validate_witness_evidence.py
Constant: CLOSED_AUX_EVIDENCE_FILES
Lines: 37–51
Allowed auxiliary files:
HOST_RUN_METADATA.txt
IMAGE_PULL_STDOUT.txt
IMAGE_PULL_STDERR.txt
CARGO_LOCK_INTEGRITY.txt
Finding 2.2 — Normative documentation describes the same four files

Classification: CLEAR

Path: WITNESS_PACKAGE_MANIFEST.md
Heading: Optional (host-only auxiliary; closed inventory)
Lines: 43–54
Finding 2.3 — Documentation inaccurately says pull logs are present only on pull failure

Classification: AMBIGUOUS

Path: WITNESS_PACKAGE_MANIFEST.md
Lines: 47–49
The table says:
IMAGE_PULL_STDOUT.txt / IMAGE_PULL_STDERR.txt — present only on pull failure

The host writes both around every pull attempt, including successful pulls.
The inventory remains closed, but the presence rule is inaccurate.

Finding 2.4 — Optional auxiliary files are not required to appear in the manifest

Classification: BLOCKED

Path: WITNESS_PACKAGE_MANIFEST.md
Lines: 43–49
Path: validator
Function: validate_manifest
Lines: 1594–1601
The validator exempts every member of CLOSED_AUX_EVIDENCE_FILES from the unlisted-file check:
if rel == MANIFEST_NAME or rel in CLOSED_AUX_EVIDENCE_FILES:
    continue

Therefore an auxiliary file can be present in the submitted evidence directory but absent from EVIDENCE_MANIFEST.sha256.

Finding 2.5 — The final manifest does not necessarily cover every submitted file

Classification: BLOCKED
The requested confirmation cannot be made.
A structurally passing manifest may omit:

HOST_RUN_METADATA.txt;
image pull stdout/stderr;
CARGO_LOCK_INTEGRITY.txt.
That contradicts a complete cryptographic inventory model for the submitted directory.
3. Manual evidence inventory
Finding 3.1 — Four manual files are consistently identified

Classification: CLEAR

Paths:
WITNESS_PACKAGE_MANIFEST.md:58–62, 99–103
WITNESS_RUNBOOK.md:369–377
WITNESS_SUBMISSION.md:75–85
Manual files:
WITNESS_STATEMENT.md
WITNESS_VERDICT.md
DEVIATIONS.txt
REDACTIONS.md

DEVIATIONS.txt may be prepopulated by the host but still requires Witness review/finalization.

Finding 3.2 — Manual forms are mandatory before the final manifest

Classification: CLEAR
The documented lifecycle requires completion of all four forms before regeneration of the final manifest.

Finding 3.3 — Validator requires all manual files on disk and in the manifest

Classification: CLEAR

Path: validator
Lines: 1614–1619, 1566–1570
Missing files or manifest entries fail structural validation.
Finding 3.4 — Manual truthfulness cannot be established structurally

Classification: CLEAR WITH LIMITATIONS
The validator can enforce:

required fields;
exact vocabularies;
selected cross-file equality;
verdict ceiling.
It cannot prove independence, human review, or factual truthfulness.
4. Template inventory and schema declarations
Finding 4.1 — A template exists for every required structured file

Classification: CLEAR
The templates/ directory contains templates for every structured required file except:

raw logs;
EVIDENCE_MANIFEST.sha256.
Finding 4.2 — No template exists for optional HOST_RUN_METADATA.txt

Classification: CLEAR WITH LIMITATIONS
This was carried forward from Batch 1.
It remains an auxiliary file containing significant run identity and lifecycle information without a normative field schema.

Finding 4.3 — Every structured required file must declare schema version 1

Classification: CLEAR

Path: WITNESS_PACKAGE_MANIFEST.md
Lines: 9–14
Path: validator
Constants/functions: SCHEMA_VERSIONED_FILES, check_schema_version
Lines: 110–114, 347–353
Finding 4.4 — Raw logs and manifest are deliberately schema-exempt

Classification: CLEAR
Raw stream files may be empty and need not contain key-value records.

5. Generator/template/validator key equality
Finding 5.1 — Exact key equality is not enforced

Classification: BLOCKED

Path: validator
Functions: require_fields, validation loop
Lines: 313–327, 1652–1657
The validator requires a minimum set of fields. It does not reject unknown or extra structured keys.
Thus:
generator keys == template keys == validator keys

is not an enforced invariant.

Finding 5.2 — Contract tests generally check required-key inclusion, not equality

Classification: BLOCKED

Path: scripts/tests/test_validate_witness_evidence.py
Contract tests, especially POST_BUILD contract
Representative lines: 128–202
The contract pattern checks that validator-required keys are present in generator blocks. Extra generated keys and template omissions can survive.
Finding 5.3 — Load-bearing generated fields may remain outside validator semantics

Classification: BLOCKED
Confirmed examples carried from Batch 2:

POST_BUILD_INTEGRITY.txt generates additional technical-gate fields not fully represented by the template or validator.
DOCKER_EXIT_CODE.txt generates outcome_source, which is not required by the template/schema.
HOST_RUN_METADATA.txt has no schema at all.
Finding 5.4 — Template fields are not always validator-required

Classification: CLEAR WITH LIMITATIONS
Examples:

SOURCE_IDENTITY.txt template includes status, but it is not in that file’s required-field tuple.
DOCKER_EXIT_CODE.txt template includes status, but it is not required.
IMAGE_IDENTITY.txt template includes product_executed and ldd_used, while its file-specific required tuple omits them.
WITNESS_STATEMENT.md includes upstream_product_commands_not_run, but that field is not in its required tuple.
Some may be checked indirectly, but template-to-schema exactness is absent.
Finding 5.5 — Unknown extra keys are accepted

Classification: BLOCKED
parse_kv collects syntactically valid extra keys, but no per-file allowed-key set exists.
A submission can therefore contain unrecognized structured assertions without structural failure.

Finding 5.6 — Malformed key-like lines may be ignored

Classification: CLEAR WITH LIMITATIONS

Path: validator
Function: parse_kv
Lines: 236–272
Lines are ignored when:
they lack =;
the left side is not a valid identifier;
they are markdown/table lines.
This supports markdown forms, but unrecognized pseudo-fields can exist as prose without schema treatment.
6. Duplicate, conflicting, missing, and extra keys
Finding 6.1 — Duplicate valid keys are rejected

Classification: CLEAR

Path: validator
Function: parse_kv
Lines: 240–270
Both identical duplicates and conflicting duplicates produce errors.
Finding 6.2 — First value is retained only for continued diagnostics

Classification: CLEAR
There is no last-value-wins behavior.

Finding 6.3 — Missing required keys are rejected

Classification: CLEAR

Function: require_fields
Lines: 313–317
Finding 6.4 — Conditionally empty fields can be required to exist

Classification: CLEAR

Function: require_present
Lines: 319–327
This supports explicit not-applicable shapes.
Finding 6.5 — Extra fields are not rejected

Classification: BLOCKED
No file-specific allowed-field set or exact schema equality exists.

Finding 6.6 — Semantic conflicts in different field names are only caught when explicitly programmed

Classification: CLEAR WITH LIMITATIONS
For example:

outcome is cross-checked in several files;
many auxiliary or extra fields are not.
7. Outcome vocabulary and tuple schemas
Finding 7.1 — Five supported outcomes are consistently enumerated

Classification: CLEAR

Path: validator
OUTCOME_VALUES
Lines: 116–124
BUILD_NOT_STARTED
CARGO_FAILED
CARGO_SUCCEEDED_ARTIFACT_MISSING
CARGO_SUCCEEDED_ARTIFACT_PRESENT
INFRASTRUCTURE_FAILURE
Finding 7.2 — Core BUILD_EXIT_CODE tuple rules are defined

Classification: CLEAR

Path: validator
OUTCOME_RULES
Lines: 126–153
The rules define:
cargo_started;
build_status;
cargo_exit_code
for all five outcomes.
Finding 7.3 — Static-inspection failure is not a separate outcome

Classification: CLEAR
It is represented as:

outcome=CARGO_SUCCEEDED_ARTIFACT_PRESENT
status=FAILED
inspection_complete=no

with a nonzero Docker/container exit and a reduced verdict ceiling.

Finding 7.4 — Exactly one explicit outcome is not mandatory to the validator

Classification: BLOCKED

Path: validator
Function: determine_outcome
Lines: 928–954
When outcome is absent or invalid, the validator attempts to infer:
BUILD_NOT_STARTED;
INFRASTRUCTURE_FAILURE;
CARGO_FAILED
from cargo_started and build_status.
This contradicts the normative statement that every submission declares exactly one outcome.
Finding 7.5 — Missing explicit outcome still generates an error in some later checks, but inference remains authoritative for subsequent validation

Classification: AMBIGUOUS
FILE_REQUIRED_FIELDS requires outcome, so missing outcome should also trigger a missing-field error.
However, the inference changes downstream interpretation and can mask the intended “no authoritative outcome” semantics.
The validator should fail closed without inference.

Finding 7.6 — Complete cross-file outcome tuples are not fully schema-defined

Classification: BLOCKED
The validator defines the principal BUILD_EXIT_CODE.txt tuple, but does not establish one complete normalized tuple across:

BUILD_EXIT_CODE.txt;
BUILD_TIMING.txt;
DOCKER_EXIT_CODE.txt;
POST_BUILD_INTEGRITY.txt;
artifact/static evidence.
Some fields are cross-checked; others are not.
8. Outcome-specific applicability
Finding 8.1 — Artifact-missing and non-started outcomes use explicit inapplicable evidence

Classification: CLEAR

Path: WITNESS_PACKAGE_MANIFEST.md
Lines: 74–80
ARTIFACT_IDENTITY.txt and STATIC_ARTIFACT_INSPECTION.txt must not be omitted.
They require:
applicable=no
artifact_present=no
reason=<nonempty>
Finding 8.2 — Cargo failure can be represented without fabricated artifact data

Classification: CLEAR
The artifact and static-inspection files have not-applicable forms.

Finding 8.3 — Cargo-zero/artifact-missing can be represented truthfully

Classification: CLEAR
No fake size, hash, file, readelf, or objdump output is required.

Finding 8.4 — Artifact-present/static-inspection-failed can be represented truthfully

Classification: CLEAR WITH LIMITATIONS
The build outcome remains artifact-present, while:

inspection status is failed;
failed commands and exits are recorded;
PASS is prohibited.
Finding 8.5 — Successful artifact-present outcome has the fullest schema

Classification: CLEAR
Artifact identity and every required static command become applicable.

Finding 8.6 — Generic infrastructure failure is not fully normalized for every file

Classification: BLOCKED
Carried forward from Batch 2:

unexpected container failures may leave mandatory files as placeholders;
invalid/missing outcome finalization is incomplete;
generated generic fallback records do not always equal each normal template schema.
9. NOT_REACHED placeholder policy
Finding 9.1 — Host initializes automated files to status=NOT_REACHED

Classification: CLEAR

Path: host script
Function: init_mandatory_evidence
Lines: 868–877
Finding 9.2 — Validator expressly permits final NOT_REACHED placeholders in three files

Classification: BLOCKED

Path: validator
Constants/functions:
PLACEHOLDER_ELIGIBLE_FILES
placeholder_skip
Lines: 59–67, 330–344
Permitted files:
BOOTSTRAP.txt
BUILD_COMMAND.txt
BUILD_ENVIRONMENT.txt

Permitted outcomes:

BUILD_NOT_STARTED
INFRASTRUCTURE_FAILURE

Their complete file-specific schemas and semantic checks are skipped.

Finding 9.3 — A preliminary placeholder can therefore survive into a structurally passing final submission

Classification: BLOCKED
The placeholder is treated as truthful evidence that the stage was not reached, but it is not an outcome-finalized file-specific schema.
This conflicts with:

“every mandatory file receives a schema-valid final state”;
the package’s overall purpose of one complete final evidence package per outcome.
Finding 9.4 — Placeholder allowance avoids manual fabrication

Classification: CLEAR WITH LIMITATIONS
The underlying intent is valid: a stage never reached should not require fabricated tool values.
The correct solution is an explicit file-specific applicable=no or stage_reached=no schema, not a generic initializer placeholder.

Finding 9.5 — Only three files receive the placeholder exception

Classification: CLEAR
Other structured files must meet their required-field sets even on negative outcomes.

10. Field capitalization and vocabulary
Finding 10.1 — Capitalization is intentionally mixed among field families

Classification: CLEAR WITH LIMITATIONS
Examples:

yes|no for many truth declarations;
YES|NO for cargo_started, product_executed, and ldd_used;
uppercase outcome/status vocabularies;
lowercase pending for maintainer intake.
This is schema-driven but increases implementation friction.
Finding 10.2 — canonical_run remains inconsistent

Classification: BLOCKED
Carried from Batch 1:

package identity uses yes|no;
host metadata/deviation output uses YES|NO.
Finding 10.3 — Failure-stage vocabularies are not centrally enumerated

Classification: CLEAR WITH LIMITATIONS
Outcome values are centrally defined, but failure_stage is generally a free-form nonempty token/string checked only in selected contexts.

Finding 10.4 — Status vocabularies differ by file

Classification: CLEAR WITH LIMITATIONS
There is no universal:

OK|FAILED|NOT_REACHED|RECORDED

schema applied consistently across all structured files.

11. Current-run provenance
Finding 11.1 — run_id is required only in selected manual/package files

Classification: CLEAR WITH LIMITATIONS
Required in:

WEAVER_FORGE_PACKAGE_IDENTITY.txt;
WITNESS_VERDICT.md.
It is not required in every generated evidence file.
Finding 11.2 — Validator does not require one run ID across the complete inventory

Classification: BLOCKED
There is no global machine check that every submitted evidence file:

was generated for one run;
shares one immutable run_id;
was freshly created during that run.
Finding 11.3 — Manifest hashes content but does not establish current-run origin

Classification: CLEAR WITH LIMITATIONS
A correct hash proves the listed bytes at validation time, not when or by which run they were generated.

Finding 11.4 — Existing evidence-directory collision compounds the provenance gap

Classification: BLOCKED
Carried from Batch 1:

preexisting EVIDENCE_DIR is merged;
allowed prior files may survive;
no universal run ID distinguishes mixed generations.
12. Closed-inventory enforcement
Finding 12.1 — Validator rejects unlisted regular files

Classification: CLEAR

Path: validator
Function: validate_manifest
Lines: 1594–1601
Finding 12.2 — Validator rejects manifest-listed files outside the closed set

Classification: CLEAR

Lines: 1572–1583
Listing an undeclared file does not authorize it.
Finding 12.3 — Validator rejects symlinks anywhere in the evidence tree

Classification: CLEAR

Function: check_no_symlinks
Lines: 1524–1530
Finding 12.4 — Hidden regular files are rejected unless explicitly allowed

Classification: CLEAR
A file such as:

.DS_Store
.validator.log

is a regular unlisted file and fails.

Finding 12.5 — Directories themselves are not rejected

Classification: CLEAR WITH LIMITATIONS

Path: validator
Recursive walks: 1527, 1594
Empty directories can remain in the evidence tree:
they are not listed in the manifest;
they are not rejected;
they have no hash coverage.
Finding 12.6 — Nested regular files are rejected by the validator

Classification: CLEAR
Even though the filename grammar permits safe subpaths, the closed inventory contains only top-level names, so nested files fall outside the allowed set.

Finding 12.7 — Host closed-inventory check is weaker than validator enforcement

Classification: BLOCKED

Path: host script
Function: enforce_closed_aux_inventory
Lines: 1730–1747
The host checks only:
find "${EVIDENCE_DIR}" -maxdepth 1 -type f

It does not inspect:

nested files;
directories;
symlinks;
special filesystem objects.
The later validator is stricter, but host success is not conditioned on validator success.
Finding 12.8 — Duplicate filenames on disk are naturally impossible at one path

Classification: CLEAR
Duplicate manifest entries are separately rejected.

Finding 12.9 — Special filesystem objects are not comprehensively rejected

Classification: CLEAR WITH LIMITATIONS
The validator explicitly rejects symlinks and handles regular files.
It does not explicitly reject:

FIFOs;
sockets;
device nodes
inside the evidence directory.
They are neither regular files nor symlinks and can be ignored by inventory and manifest logic.
13. Manifest grammar
Finding 13.1 — Exact digest grammar is enforced

Classification: CLEAR

Path: validator
Regex/constants:
SHA256_RE
MANIFEST_LINE_RE
Lines: 212–220, 1489–1506
Required:
<64 lowercase hexadecimal characters><two spaces>./<safe path>
Finding 13.2 — Manifest self-inclusion is rejected

Classification: CLEAR

Function: parse_manifest_line
Lines: 1519–1520
Finding 13.3 — Duplicate manifest paths are rejected

Classification: CLEAR

Function: validate_manifest
Lines: 1552–1564
Finding 13.4 — Absolute paths, traversal, backslashes, and empty segments are rejected

Classification: CLEAR

Lines: 1492–1518
Finding 13.5 — Spaces, tabs, and newlines are not permitted in manifest paths

Classification: CLEAR
Any whitespace in the relative path is rejected.

Finding 13.6 — Safe filename alphabet is deliberately narrow

Classification: CLEAR
Allowed:

A–Z a–z 0–9 . _ -

and / between path segments.

Finding 13.7 — Manifest generation uses NUL-safe discovery and sorting

Classification: CLEAR

Paths:
WITNESS_PACKAGE_MANIFEST.md:104–108
host script 1753–1757
Command:
find ... -print0 | sort -z | xargs -0 sha256sum
Finding 13.8 — Generator supports more filenames than validator permits

Classification: CLEAR WITH LIMITATIONS
The shell command can discover names containing spaces and many special characters, but sha256sum output for unusual names may be escaped and the validator will reject the path.
Because the permitted inventory uses fixed safe names, this is acceptable only if closed inventory is enforced first.

14. Manifest lifecycle
Finding 14.1 — Preliminary and final manifests are clearly distinguished

Classification: CLEAR

Paths:
WITNESS_PACKAGE_MANIFEST.md:97–113
WITNESS_RUNBOOK.md:367–390
Finding 14.2 — Preliminary manifest is automatically generated after automated capture

Classification: CLEAR

Path: host script
Lines: 1750–1764
Finding 14.3 — Final manifest regeneration is manual

Classification: CLEAR
The Witness must regenerate it after manual files and redaction review.

Finding 14.4 — Final manifest excludes itself

Classification: CLEAR

Finding 14.5 — Final manifest must contain every mandatory nonmanifest file

Classification: CLEAR

Path: validator
Lines: 1566–1570
Finding 14.6 — Final manifest need not contain optional auxiliary files

Classification: BLOCKED
This prevents the manifest from proving the complete directory inventory.

Finding 14.7 — Files can change after manifest generation and before validation

Classification: CLEAR WITH LIMITATIONS
The validator detects such changes through hash mismatch.

Finding 14.8 — Files can change after a passing validator run without an intrinsic filesystem lock

Classification: CLEAR WITH LIMITATIONS
Documentation prohibits later edits and requires correction-ledger handling, but the package does not cryptographically or filesystem-enforce immutability after validation.
A later change is detected only if:

the manifest is revalidated;
the containing commit/archive hash is independently checked.
15. Validator output location
Finding 15.1 — Documentation consistently requires validator output outside EVIDENCE_DIR

Classification: CLEAR

Paths:
WITNESS_PACKAGE_MANIFEST.md:110–121
WITNESS_RUNBOOK.md:355–363
WITNESS_SUBMISSION.md:66–85
Finding 15.2 — Validator itself writes only stdout/stderr

Classification: CLEAR

Path: validator
main
Lines: 1743–1755
It does not write an evidence file.
Finding 15.3 — Shell redirection can still contaminate EVIDENCE_DIR

Classification: CLEAR WITH LIMITATIONS
The validator cannot control where the caller redirects stdout/stderr.

Finding 15.4 — Ordinary redirected validator output would be detected as an unlisted file

Classification: CLEAR
A new validator.log inside EVIDENCE_DIR would fail closed-inventory validation.

Finding 15.5 — Redirecting into an allowed auxiliary filename is not categorically prevented

Classification: BLOCKED
Because optional auxiliary files may:

be unlisted;
be present without manifest coverage,
validator output redirected into a name such as HOST_RUN_METADATA.txt could contaminate evidence while remaining within the allowed inventory.
Concurrent rewriting would likely create hash or parsing issues when listed, but omission from the manifest is permitted.
16. Manifest coverage and post-manifest mutation
Finding 16.1 — All mandatory files are required to be covered

Classification: CLEAR

Finding 16.2 — All actual submitted files are not required to be covered

Classification: BLOCKED
Optional auxiliary evidence is the exception.

Finding 16.3 — Manifest validation checks listed file hashes directly

Classification: CLEAR

Path: validator
Lines: 1585–1592
Finding 16.4 — Manifest has no self-hash

Classification: CLEAR
Self-exclusion is correct and unavoidable.
The manifest’s own integrity must be established through:

submission commit;
archive digest;
external record.
Finding 16.5 — evidence_inventory_complete is not automatically moved to yes

Classification: CLEAR WITH LIMITATIONS

Path: host script
Lines: 1677–1723
The automated run always writes:
evidence_inventory_complete=no
Finding 16.6 — Finalization procedure does not specify a canonical writer for updating that field

Classification: AMBIGUOUS
Documentation says the field may become yes only after:

manual files complete;
final manifest regenerated;
final validation.
But the final manifest must be generated before validation, while changing POST_BUILD_INTEGRITY.txt to yes after validation would invalidate the manifest.
The correct order is therefore unclear:
set it to yes;
generate manifest;
validate.
Yet at step 1 the final manifest has not validated.
Finding 16.7 — The inventory-complete lifecycle is circular

Classification: BLOCKED

Path: WITNESS_PACKAGE_MANIFEST.md
Lines: 56–64
It says evidence_inventory_complete=yes must not be set before the final manifest has been regenerated.
The host note says it can become yes only after the final manifest validates.
But after validation, editing the field requires manifest regeneration and revalidation.
No noncircular, exact procedure is defined.
17. Failure submissions and inapplicable evidence
Finding 17.1 — Negative outcomes are explicitly welcome

Classification: CLEAR

Paths:
WITNESS_PACKAGE_MANIFEST.md:74–80
WITNESS_SUBMISSION.md:49–53
Finding 17.2 — Artifact and static evidence have explicit not-applicable models

Classification: CLEAR
No fabrication is required for:

missing artifact;
Cargo not started;
Cargo failure;
infrastructure failure.
Finding 17.3 — Bootstrap/build-environment nonapplicability lacks explicit final schemas

Classification: BLOCKED
Instead of dedicated final records such as:

status=NOT_APPLICABLE
stage_reached=no
reason=<failure stage>

the validator permits the generic initialization state:

status=NOT_REACHED

and skips the normal schema.

Finding 17.4 — Not every failure submission can be produced completely by the current generators

Classification: BLOCKED
Carried from Batch 2:

unexpected container failures can leave placeholders;
invalid/missing outcomes receive incomplete host finalization;
complete post-build evidence may be absent.
Finding 17.5 — Manual reconstruction would be required for some structurally complete failure packages

Classification: BLOCKED
For failure paths not comprehensively finalized by the scripts, a Witness would need to:

interpret the failure;
replace placeholders;
align fields manually;
regenerate the manifest.
That violates the Batch-3 purpose of producing a complete truthful package without manual fabrication or reconstruction.
18. Golden fixtures and generator contracts
Finding 18.1 — Golden fixtures cover multiple positive and negative scenarios

Classification: CLEAR

Path: scripts/VALIDATOR.md
Lines: 391–416
Documented scenarios include:
successful artifact;
build not started;
Cargo failure;
artifact missing;
infrastructure failure;
static-inspection incomplete;
image identity failures.
Finding 18.2 — Fixtures are synthetic

Classification: CLEAR WITH LIMITATIONS
They are generated by fixtures_lib.py, not captured from actual host/container writers.

Finding 18.3 — Generator contract tests inspect source blocks

Classification: CLEAR WITH LIMITATIONS
They establish selected key presence in script text.

Finding 18.4 — Tests do not prove complete generator/template equality

Classification: BLOCKED
They do not:

reject extra generator keys;
detect all template-only fields;
exercise every failure writer;
prove all runtime branches produce one exact schema.
Finding 18.5 — Tests do not prove manifest coverage of optional auxiliary evidence

Classification: MISSING
No test requirement establishes:

every regular submitted file must have exactly one final manifest entry

because the validator explicitly exempts optional auxiliary files.

Finding 18.6 — Tests do not prove current-run provenance

Classification: MISSING
No test rejects a directory composed of individually valid files from different synthetic runs when the limited cross-file identities happen to agree.

19. Special confirmations
Generator keys exactly equal template and validator keys

Result: BLOCKED
Only minimum required-field inclusion is enforced.

Extra generated load-bearing fields validated

Result: BLOCKED
Not consistently.

Duplicate keys rejected

Result: CLEAR
Both identical and conflicting duplicates are rejected.

Exactly one explicit outcome mandatory

Result: BLOCKED
Validator inference exists.

Validator infers missing outcome

Result: CLEAR
It does so for three outcome shapes.

All outcome tuples schema-defined

Result: BLOCKED
Core BUILD_EXIT_CODE tuples are defined; the complete cross-file tuple is not.

NOT_REACHED may survive into final submission

Result: CLEAR
It is explicitly permitted for three files on two negative outcomes.

Every failure outcome can produce all required files truthfully

Result: BLOCKED
Not through current generators on every path.

Inapplicable evidence has an explicit schema

Result: CLEAR WITH LIMITATIONS
Artifact/static evidence does; bootstrap/build command/build environment use generic placeholders.

Final manifest covers complete closed inventory

Result: BLOCKED
Optional auxiliary files may be omitted.

Manifest parser safely handles every permitted filename

Result: CLEAR
All filenames permitted by the manifest grammar are handled.
The generator can encounter broader names, but those are rejected.

Validator report required outside EVIDENCE_DIR

Result: CLEAR
Documented consistently, but caller redirection is not preventively controlled.

Current-run provenance machine-checked

Result: BLOCKED
No global run provenance exists.

20. Newly identified Batch-3 Part-1 blockers
Optional auxiliary files can be present without any EVIDENCE_MANIFEST.sha256 entry, so the final manifest does not necessarily cover every submitted file.
Exact generator/template/validator field equality is not enforced; unknown and extra structured keys are accepted.
Contract tests generally prove required-key inclusion, not exact schema equality.
The validator infers a missing or invalid explicit outcome instead of failing closed immediately.
A complete authoritative outcome tuple is not defined and enforced across all outcome-bearing evidence files.
status=NOT_REACHED placeholders may survive into final submissions for BOOTSTRAP.txt, BUILD_COMMAND.txt, and BUILD_ENVIRONMENT.txt, bypassing their normal schemas.
No machine-enforced current-run provenance exists across all evidence files.
The host closed-inventory check covers only top-level regular files and does not inspect nested files, symlinks, directories, or special filesystem objects.
Optional auxiliary filenames can potentially be used to hold redirected validator output without mandatory manifest coverage.
The evidence_inventory_complete lifecycle is circular and lacks an exact noncontradictory finalization procedure.
Bootstrap/build-command/build-environment failure applicability uses generic placeholders rather than explicit final not-applicable schemas.
Some failure packages require manual evidence reconstruction because current generators do not finalize every mandatory file.
Golden fixtures and source-text contracts do not prove complete actual generator/schema equality or mixed-run rejection.
21. Newly identified Batch-3 Part-1 non-fatal limitations
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
22. Batch-1 blockers carried forward unchanged
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
23. Batch-2 blockers carried forward unchanged
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
24. Batch-1 non-fatal limitations carried forward unchanged
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
25. Batch-2 non-fatal limitations carried forward unchanged
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
No final Batch-3 conclusion is issued in Part 1.
No final package-readiness verdict is issued.
RC4 BATCH 3 — PART 1 COMPLETE
No Independent Witness reproduction occurred.
No Independent Witness PASS is claimed.
C-014 remains NOT_STARTED.
Do not continue to Part 2 until instructed.