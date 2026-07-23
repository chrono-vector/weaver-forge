RC4 BATCH 1 — PART 4 OF 4
1. Part-4 scope

This final part consolidates RC4 Batch 1 only. No new build, container, validator, script, or product execution was performed. No repository content was modified.
This part:

confirms completion of the original Batch-1 scope;
confirms review of the required minimum files;
consolidates confirmed strengths;
preserves every blocker and non-fatal limitation identified in Parts 1–3;
specifies mandatory corrections and recommended hardening;
identifies matters explicitly deferred to Batch 2;
does not issue a final package-readiness verdict.
2. Files and findings carried forward

The Batch-1 audit included the required public, normative, implementation, template, validator, and test surfaces, including:

README.md
external_verifications/grok-build/README.md
external_verifications/grok-build/VERDICT.md
external_verifications/grok-build/RESULTS.md
external_verifications/grok-build/CLAIM_REGISTER.md
external_verifications/grok-build/REPRODUCTION.md
external_verifications/grok-build/WITNESS_HANDOFF.md
external_verifications/grok-build/witness-package/README.md
external_verifications/grok-build/witness-package/WITNESS_PACKAGE_VERSION.md
external_verifications/grok-build/witness-package/WITNESS_REQUIREMENTS.md
external_verifications/grok-build/witness-package/WITNESS_RUNBOOK.md
external_verifications/grok-build/witness-package/WITNESS_CLASSIFICATION.md
external_verifications/grok-build/witness-package/WITNESS_PACKAGE_MANIFEST.md
external_verifications/grok-build/witness-package/PACKAGE_READINESS_POLICY.md
external_verifications/grok-build/witness-package/scripts/run_witness_narrow_build.sh
external_verifications/grok-build/witness-package/scripts/validate_witness_evidence.py
external_verifications/grok-build/witness-package/scripts/tests/test_validate_witness_evidence.py
external_verifications/grok-build/witness-package/templates/WEAVER_FORGE_PACKAGE_IDENTITY.txt
external_verifications/grok-build/witness-package/templates/DEVIATIONS.txt
relevant golden fixtures, fixture builders, validator documentation, change logs, and remediation notes.
templates/HOST_RUN_METADATA.txt was confirmed absent. HOST_RUN_METADATA.txt is generated as auxiliary evidence but has no normative template or validator schema.
3. Original Batch-1 scope completion check

All 20 original Batch-1 scope items were inspected:

Transfer/archive identity — inspected and previously verified.
rc1–rc4 immutable history — inspected.
rc4 package version and canonical tag — inspected.
Annotated-tag resolution — inspected in policy and script.
Detached package HEAD and clean clone enforcement — inspected.
Absence of self-referential commit placeholders — inspected.
Time-stable tag wording — inspected.
Public discoverability — inspected.
Canonical platform boundaries — inspected.
Canonical fixed-value enforcement — inspected.
Noncanonical-deviation behavior — inspected.
Witness-ID validation — inspected.
WORK_ROOT safety — inspected.
Managed-child symlink safety — inspected.
Fresh Weaver Forge clone and rc4 resolution — inspected.
Fresh Grok Build clone and pinned detached checkout — inspected.
Direct detached-state probes — inspected.
Source HEAD, clean tree, and Cargo.lock enforcement before Docker — inspected.
Isolated work/cache/target/evidence paths — inspected.
Host-side safety and contract-test coverage — inspected.
All minimum files named in the Batch-1 instructions were reviewed. No requested Batch-1 topic was omitted.
4. Confirmed strengths

The following controls were substantively confirmed:

Package version is consistently 1.0.0-rc4.

Canonical tag is consistently:

grok-build-witness-v1.0.0-rc4

Package authority is declared as:

annotated_tag_resolution

The script resolves:

refs/tags/grok-build-witness-v1.0.0-rc4^{commit}
Canonical fixed values are stored as immutable shell constants.
Environment variables cannot silently alter canonical identities.

A differing override either aborts or requires explicit:

--noncanonical-deviation
Accepted deviations record changed fields and prevent PASS.
Weaver Forge URL mismatch receives FAIL-level treatment.

WITNESS_ID uses:

^[a-z0-9][a-z0-9._-]{0,63}$
Dangerous WORK_ROOT values are rejected.
Root, home, system-prefix, repository-overlap, and WSL drive-root protections are present.
Nonempty WORK_ROOT reset requires explicit authorization.
Only deterministic managed children are reset.
Symlinked managed children are unlinked instead of recursively followed.
Weaver Forge is freshly cloned.
The rc4 tag is resolved and checked out detached.
Package detached state is directly probed.
Package HEAD must equal the resolved tag commit.
Package clone must be clean.
Optional external expected commit cannot replace annotated-tag authority.
Grok Build is freshly cloned.

Grok Build is checked out at the pinned commit:

98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce
Grok Build detached state is directly probed.
Grok Build HEAD and clean state are enforced.
Cargo.lock is directly hashed and compared before image pull and container execution.
Work, cache, target, bootstrap, isolated HOME, source, package, and evidence paths are separated.
Host-side source-text contract tests cover many important implementation strings.
Validator fixtures and schema-contract tests provide useful static coverage, although not behavioral host execution coverage.
These strengths are real, but they do not eliminate the blockers below.
5. Complete Batch-1 blockers
Blocker 1 — Current normative documents still describe fixed rc4 as pending

Classification: BLOCKED
Current-facing documents inside the fixed rc4 tag still say rc4 is:

under preparation;
pending commit;
pending tag;
not yet published;
not ready until rc4 is committed and tagged.
Representative paths:
README.md
external_verifications/grok-build/README.md
external_verifications/grok-build/VERDICT.md
external_verifications/grok-build/witness-package/README.md
external_verifications/grok-build/witness-package/WITNESS_PACKAGE_VERSION.md
external_verifications/grok-build/witness-package/WITNESS_RUNBOOK.md
external_verifications/grok-build/witness-package/PACKAGE_READINESS_POLICY.md
This contradicts the fixed tag and commit actually being audited.
Blocker 2 — Change-log and status claims contradict current content

Classification: BLOCKED
Several change-log or remediation statements claim that pending-tag wording was removed or made time-stable, while contradictory current wording remains.
Representative paths:

external_verifications/grok-build/RESULTS.md
external_verifications/grok-build/CLAIM_REGISTER.md
external_verifications/grok-build/witness-package/WITNESS_RUNBOOK.md
external_verifications/grok-build/witness-package/PACKAGE_READINESS_POLICY.md
Blocker 3 — rc4 is not represented as an already-published immutable release

Classification: BLOCKED
The fixed rc4 snapshot defines rc4 immutability prospectively but does not record rc4 itself alongside rc1–rc3 as an already-published immutable tag/commit pair.
Relevant paths:

external_verifications/grok-build/witness-package/README.md
external_verifications/grok-build/witness-package/WITNESS_PACKAGE_VERSION.md
external_verifications/grok-build/README.md
external_verifications/grok-build/WITNESS_HANDOFF.md
Blocker 4 — Docker metadata commands execute before identity enforcement

Classification: BLOCKED
In:

external_verifications/grok-build/witness-package/scripts/run_witness_narrow_build.sh
function: record_host_environment
the script executes:
docker version
docker context show

before:

rc4 tag resolution;
package detached/HEAD/clean checks;
Grok Build detached/HEAD/clean checks;
direct Cargo.lock verification.
They are informational and failure-tolerant, but they still violate the literal requirement that no Docker execution occur before all required identity checks pass.
Blocker 5 — Raw annotated-tag object type is not enforced

Classification: BLOCKED
The script verifies:

refs/tags/<tag>^{commit}

but does not require:

git cat-file -t refs/tags/<tag>

to equal:

tag

Therefore a lightweight tag could satisfy the executable tag-to-commit check even though normative documents claim annotated-tag authority.

Blocker 6 — Generated DEVIATIONS.txt is incompatible with the normative schema

Classification: BLOCKED

Generator: scripts/run_witness_narrow_build.sh
Template: templates/DEVIATIONS.txt
Validator: scripts/validate_witness_evidence.py
The template and validator expect indexed deviation fields such as:
deviation_<n>_description
deviation_<n>_severity
deviation_<n>_canonical_identity_impact
deviation_<n>_verdict_ceiling

The host generator instead emits a different summary structure using:

changed_identity_field_count
canonical_run
verdict_ceiling

and changed-field text blocks.
The canonical generator, template, and validator are not aligned.

Blocker 7 — Rust and DotSlash deviation severity is insufficient

Classification: BLOCKED
Overrides to:

EXPECTED_RUSTC_VERSION
EXPECTED_DOTSLASH_VERSION

require explicit noncanonical mode but do not receive the host’s FAIL identity ceiling.
Changing either accepted version can materially alter:

compiler behavior;
dependency/bootstrap behavior;
toolchain identity;
reproducibility.
The current severity treatment is weaker than their actual effect.
Blocker 8 — Preexisting evidence directory is not atomically rejected

Classification: BLOCKED
The host uses:

mkdir -p "${EVIDENCE_DIR}"

and therefore merges into an existing directory.
It does not require the directory to be absent or empty.

Blocker 9 — Evidence collision can mix current and prior run content

Classification: BLOCKED
Mandatory files are rewritten individually, but prior:

auxiliary files;
logs;
manual forms;
manifests;
allowed filenames
may survive until overwritten—or may never be overwritten if execution stops early.
Closed inventory checks filenames, not current-run provenance.
Blocker 10 — Behavioral host-safety coverage is missing

Classification: BLOCKED
The suite lacks behavioral tests for:

canonical override rejection;
explicit noncanonical acceptance;
canonical_run=NO generation;
verdict-ceiling calculation;
valid/invalid Witness-ID cases;
dangerous WORK_ROOT paths;
repository ancestor/descendant paths;
WSL drive roots;
nonempty-reset authorization;
symlink target survival;
package detached probe;
annotated versus lightweight tags;
evidence-directory collision;
Docker command ordering.
Blocker 11 — No actual host-generated noncanonical evidence test exists

Classification: BLOCKED
No behavioral or golden test proves that actual host-generated:

DEVIATIONS.txt;
WEAVER_FORGE_PACKAGE_IDENTITY.txt;
HOST_RUN_METADATA.txt
match templates, validator expectations, and verdict-ceiling policy in a noncanonical run.
Blocker 12 — Public and remediation statements overclaim closure

Classification: BLOCKED
Current change logs and status summaries claim closure of:

time-stable tag wording;
some host-orchestrator remediation;
fixture/test alignment
more broadly than the inspected implementation supports.
6. Complete Batch-1 non-fatal limitations
Public discoverability is strong, but stale pre-publication wording creates uncertainty about whether rc4 is the intended fixed audit target.
rc4 immutability is defined prospectively rather than represented as an already-published state.
canonical_run uses lowercase in package identity but uppercase in host metadata and generated deviations.
The machine verdict ceiling covers identity overrides only; complete classification still depends on manual application of policy.
Rust/DotSlash override handling conflicts with stricter fixed-version expectations elsewhere.
The evidence run-ID fallback uses only UTC time to the second and can collide.
HOST_RUN_METADATA.txt has no normative template or validator schema.
Contract tests inspect source-text key presence rather than actual runtime output.
Golden fixtures are synthetic and share assumptions with their fixture builder.
Witness-ID behavior lacks a valid/invalid behavioral matrix.
WORK_ROOT dangerous-path and repository-overlap behavior lacks a behavioral matrix.
Nonempty-reset authorization lacks behavioral tests.
Managed-child symlink safety lacks an external-target survival test.
Package detached-state probing lacks a dedicated isolated test.
Annotated-tag versus lightweight-tag behavior lacks testing.
Docker command ordering lacks a test.
Closed-inventory validation checks allowed filenames, not current-run provenance.
canonical_run vocabulary is not normalized.
“Fixtures cannot drift” is true only relative to the shared builder, not relative to the actual shell scripts.
Docker metadata-query failures are converted to UNKNOWN; this is acceptable only while those fields remain strictly informational.
The host’s tag dereference proves commit resolution but not raw tag type.
Evidence-directory randomness is not relied upon through atomic creation.
Some host safety controls are well implemented but only textually tested.
Optional auxiliary evidence carries load-bearing information without schema validation.
7. Mandatory corrections
Mandatory correction 1 — Replace current rc4 pending wording
Exact paths:
README.md
external_verifications/grok-build/README.md
external_verifications/grok-build/VERDICT.md
external_verifications/grok-build/RESULTS.md
external_verifications/grok-build/CLAIM_REGISTER.md
external_verifications/grok-build/WITNESS_HANDOFF.md
external_verifications/grok-build/witness-package/README.md
external_verifications/grok-build/witness-package/WITNESS_PACKAGE_VERSION.md
external_verifications/grok-build/witness-package/WITNESS_RUNBOOK.md
external_verifications/grok-build/witness-package/PACKAGE_READINESS_POLICY.md
Heading/field:
current status banners;
release status paragraphs;
change-log assertions;
package identity summaries.

Precise change:
Replace statements such as:

rc4 package content under preparation
pending rc4 commit and tag
until rc4 is committed and tagged

with time-stable language that reflects the existing fixed release, for example:

RC4 is fixed at annotated tag grok-build-witness-v1.0.0-rc4.
Package readiness remains subject to independent static audit and any later authorized reproduction.
Status: Mandatory
Why it matters:
The current tagged snapshot contradicts its own release state and misleads independent auditors.
Mandatory correction 2 — Add rc4 to immutable release history
Exact paths:
external_verifications/grok-build/witness-package/README.md
external_verifications/grok-build/witness-package/WITNESS_PACKAGE_VERSION.md
external_verifications/grok-build/README.md
external_verifications/grok-build/WITNESS_HANDOFF.md
Heading:
Historical immutable releases
release identity/history tables.

Precise change:
Add:

grok-build-witness-v1.0.0-rc4
039b46737c5968a81fb756d7a6d1d0dd57b6ad96

as the current fixed immutable release.
Do not assign a final readiness outcome unless separately established.
A suitable state is:

fixed and under static audit
Status: Mandatory
Why it matters:
The package must accurately represent the immutability of the exact tag being audited.
Mandatory correction 3 — Resolve Docker metadata-query ordering
Exact path:
external_verifications/grok-build/witness-package/scripts/run_witness_narrow_build.sh
Function:
record_host_environment
main-stage ordering.

Precise change:
Move:

docker version
docker context show

until after:

package tag resolution;
package detached/HEAD/clean verification;
Grok Build detached/HEAD/clean verification;
direct Cargo.lock hash verification.
Alternatively, explicitly redefine the policy to permit non-mutating Docker metadata queries before identity checks, but the stricter and clearer correction is to move them.
Related documentation:
WITNESS_RUNBOOK.md
WITNESS_REQUIREMENTS.md
Status: Mandatory
Why it matters:
The current implementation does not satisfy the literal no-Docker-before-identity contract.
Mandatory correction 4 — Enforce raw annotated-tag object type
Exact path:
scripts/run_witness_narrow_build.sh
Function/block:
Weaver Forge tag-resolution stage.

Precise change:
Before accepting the tag, run:

git -C "${WF_DIR}" cat-file -t "refs/tags/${EFFECTIVE_WEAVER_FORGE_TAG}"

Require exact output:

tag

Record:

tag_object_type=tag

in WEAVER_FORGE_PACKAGE_IDENTITY.txt.
Abort before Docker if the object type is not tag.

Related validator/template changes:
templates/WEAVER_FORGE_PACKAGE_IDENTITY.txt
scripts/validate_witness_evidence.py
scripts/tests/test_validate_witness_evidence.py
Status: Mandatory
Why it matters:
^{commit} alone accepts lightweight tags and does not prove annotated-tag authority.
Mandatory correction 5 — Align DEVIATIONS.txt generator, template, and validator
Exact paths:
scripts/run_witness_narrow_build.sh
templates/DEVIATIONS.txt
scripts/validate_witness_evidence.py
scripts/tests/test_validate_witness_evidence.py
Function/field:
host deviation writer;
validator deviation parser;
indexed deviation fields.

Precise change:
Choose one schema and enforce it everywhere.
Recommended form:

deviation_state=PRESENT
canonical_run=no
deviation_count=<n>
deviation_1_field=<field>
deviation_1_canonical_value=<value>
deviation_1_effective_value=<value>
deviation_1_description=<description>
deviation_1_severity=FAIL|PARTIAL
deviation_1_canonical_identity_impact=yes|no
deviation_1_verdict_ceiling=FAIL|PARTIAL

For no deviation:

deviation_state=NONE
canonical_run=yes
deviation_count=0

The validator must reject:

missing indexes;
duplicate indexes;
count mismatches;
invalid severity;
PASS ceiling when deviations exist.
Status: Mandatory
Why it matters:
The current canonical generator cannot reliably produce the normative deviation evidence required by the validator.
Mandatory correction 6 — Make Rust/DotSlash deviations FAIL-level or non-permissible
Exact paths:
scripts/run_witness_narrow_build.sh
WITNESS_CLASSIFICATION.md
WITNESS_REQUIREMENTS.md
WITNESS_RUNBOOK.md
scripts/validate_witness_evidence.py
Function/field:
compute_verdict_ceiling
canonical fixed-value list;
toolchain version validation.

Precise change:
Either:

prohibit overrides entirely for canonical and noncanonical Witness runs; or

classify any changed expected Rust or DotSlash version as:

severity=FAIL
canonical_run=no
verdict_ceiling=FAIL

The validator must independently enforce the same result.

Status: Mandatory
Why it matters:
These values materially define the accepted execution environment.
Mandatory correction 7 — Atomically reject preexisting EVIDENCE_DIR
Exact path:
scripts/run_witness_narrow_build.sh
Function/field:
short_run_id
EVIDENCE_DIR
evidence initialization.

Precise change:
Replace:

mkdir -p "${EVIDENCE_DIR}"

with an atomic creation that fails if the directory exists:

mkdir "${EVIDENCE_DIR}"

Ensure the parent exists separately.
On collision:

generate a new random run ID; or
abort before creating or modifying evidence.
Status: Mandatory
Why it matters:
A run must never merge into prior evidence.
Mandatory correction 8 — Guarantee current-run provenance for every evidence file
Exact paths:
scripts/run_witness_narrow_build.sh
WITNESS_PACKAGE_MANIFEST.md
relevant evidence templates;
scripts/validate_witness_evidence.py
Function/field:
evidence initialization;
closed inventory;
manifest generation.

Precise change:
Add a unique immutable:

run_id=<value>

to every generated automated evidence file.
Require:

identical run_id across all files;
evidence directory absent before run;
all automated files newly created in the current run;
no prior manual forms present before automated completion;
manifest generated only after inventory closure.
Validator must cross-check run IDs.
Status: Mandatory
Why it matters:
Filename closure alone does not prove one coherent run.
Mandatory correction 9 — Add behavioral host-safety tests
Exact path:
scripts/tests/test_validate_witness_evidence.py
or a new dedicated host-orchestrator test file.
Tests required:
canonical mismatch abort without flag;
explicit noncanonical acceptance;
changed-field recording;
correct canonical_run=no;
correct verdict ceiling;
Witness-ID valid/invalid matrix;
dangerous WORK_ROOT matrix;
repository ancestor/descendant matrix;
WSL drive-root matrix;
reset authorization paths;
managed-child symlink target survival;
package detached-state probe;
annotated/lightweight tag distinction;
evidence-directory collision rejection;
no Docker command before identity closure.
Precise change:
Extract load-bearing host functions into a testable shell library or invoke the script with mocked commands and temporary repositories.
Status: Mandatory
Why it matters:
Source-string assertions do not prove actual control flow or failure behavior.
Mandatory correction 10 — Test actual host-generated noncanonical evidence
Exact paths:
scripts/run_witness_narrow_build.sh
scripts/tests/test_validate_witness_evidence.py
golden fixtures.
Test:
new host-output integration/golden test.
Precise change:
Generate evidence through the actual host writer paths using mocked external commands, then validate:
DEVIATIONS.txt;
WEAVER_FORGE_PACKAGE_IDENTITY.txt;
HOST_RUN_METADATA.txt;
verdict ceiling;
indexed deviation fields;
run ID consistency.
Status: Mandatory
Why it matters:
Synthetic fixture builders currently test their own assumptions rather than actual host output.
Mandatory correction 11 — Correct overclaiming status and change-log statements
Exact paths:
RESULTS.md
CLAIM_REGISTER.md
WITNESS_RUNBOOK.md
PACKAGE_READINESS_POLICY.md
host-script header comments where applicable.
Heading:
rc4 remediation entries;
change logs;
closure summaries.

Precise change:
Replace claims such as:

time-stable wording applied
pending-tag wording removed
blocker closed
cannot drift

with narrowly accurate statements, for example:

source-text contract assertions added;
behavioral host execution remains untested.
Status: Mandatory
Why it matters:
Audit records must not claim stronger closure than the implementation supports.
8. Recommended hardening
Hardening 1 — Normalize canonical_run
Paths:
scripts/run_witness_narrow_build.sh
templates/WEAVER_FORGE_PACKAGE_IDENTITY.txt
templates/DEVIATIONS.txt
validator schemas.

Change:
Use exactly:

canonical_run=yes|no

everywhere.

Status: Hardening
Why:
Removes unnecessary vocabulary inconsistency.
Hardening 2 — Add a normative HOST_RUN_METADATA.txt template
Paths:
new templates/HOST_RUN_METADATA.txt
WITNESS_PACKAGE_MANIFEST.md
validator.
Change:
Define required fields, value vocabularies, and whether it is mandatory or optional.
Status: Hardening
Why:
It currently contains important identity and lifecycle data without schema control.
Hardening 3 — Remove weak run-ID fallback
Path:
run_witness_narrow_build.sh
Function:
short_run_id
Change:
Require a cryptographically random suffix or use mktemp -d; do not fall back to second-resolution timestamps.
Status: Hardening
Why:
Reduces collision risk and simplifies atomic evidence creation.
Hardening 4 — Add a dedicated package detached-probe test
Path:
host static/behavioral test suite.

Change:
Add a separate assertion and behavioral case for:

git symbolic-ref -q HEAD

on the Weaver Forge clone.

Status: Hardening
Why:
Grok Build has a dedicated check; package identity should have equivalent test visibility.
Hardening 5 — Add exact Witness-ID boundary cases
Path:
host safety test suite.
Change:
Test:
1 character;
64 characters;
65 characters;
uppercase;
leading punctuation;
slash;
backslash;
whitespace;
control characters;
traversal-like strings.
Status: Hardening
Why:
Protects evidence path construction.
Hardening 6 — Add real symlink-target survival test
Path:
host safety test suite.
Change:
Create a managed-child symlink to an external populated directory, reset it, and prove:
symlink removed;
target directory unchanged.
Status: Hardening
Why:
Confirms destructive-operation safety.
Hardening 7 — Clarify Docker metadata policy
Paths:
WITNESS_REQUIREMENTS.md
WITNESS_RUNBOOK.md
Change:
State explicitly whether:
all Docker CLI calls are prohibited before identity enforcement; or
only image/container operations are prohibited.
Status: Hardening
Why:
Eliminates ambiguity even after command reordering.
Hardening 8 — Narrow “cannot drift” language
Path:
scripts/VALIDATOR.md

Change:
Replace broad wording with:

committed fixtures and temporary test trees share one builder and therefore remain mutually consistent; this does not prove alignment with actual shell-generated runtime evidence.
Status: Hardening
Why:
Prevents test-scope overinterpretation.
Hardening 9 — Make machine classification more complete
Paths:
host script;
validator;
classification policy.
Change:
Encode more policy rules in machine-enforced verdict ceilings rather than relying primarily on manual Witness interpretation.
Status: Hardening
Why:
Reduces manual classification divergence.
Hardening 10 — Record Docker metadata query status explicitly
Paths:
HOST_RUN_METADATA.txt template and generator.

Change:
Record:

docker_metadata_query_status=SUCCESS|UNAVAILABLE|FAILED
docker_metadata_is_informational=yes
Status: Hardening
Why:
Makes the UNKNOWN fallback semantically explicit.
9. Items explicitly deferred to Batch 2

The following were not audited in Batch 1 and remain reserved for Batch 2:

pinned Rust image pull behavior;
image digest and platform enforcement;
Docker image inspection semantics;
cached-image fallback behavior;
container invocation details;
mount modes and container isolation;
network settings inside the build container;
Rust/Cargo runtime version verification;
DotSlash bootstrap download/install/runtime verification;
protoc bootstrap and version policy;
target-directory emptiness proof inside the container;
Cargo command execution;
Cargo exit-code capture;
artifact existence and type;
static artifact inspection;
prohibition of product execution;
prohibition of ldd;
post-build source and lock integrity;
final outcome generation;
image/container failure classification;
artifact outcome semantics;
Batch-2-specific schema and generator alignment.
No conclusion about those Batch-2 controls is made here.
10. Batch-1 conclusion without final package-readiness verdict

Every requested Batch-1 scope item was inspected, and every required minimum file was reviewed.
The Batch-1 implementation contains strong controls for:

canonical value gating;
fresh cloning;
detached-state enforcement;
HEAD and cleanliness checks;
pre-build Cargo.lock verification;
WORK_ROOT safety;
managed-child symlink handling;
noncanonical disclosure.
However, Batch-1 scope cannot be considered clean because the following remain unresolved:
contradictory rc4 publication wording;
incomplete rc4 immutable-history representation;
early Docker metadata execution;
absence of raw annotated-tag object-type enforcement;
DEVIATIONS.txt generator/template/validator incompatibility;
insufficient Rust/DotSlash deviation severity;
evidence-directory collision and mixed-run provenance risk;
lack of behavioral host-safety testing;
lack of actual host-generated noncanonical evidence testing;
overstated remediation and closure claims.
No final package-readiness verdict is issued.
RC4 BATCH 1 COMPLETE — NO FINAL READINESS VERDICT YET
No Independent Witness reproduction occurred.
No Independent Witness PASS is claimed.
C-014 remains NOT_STARTED.
Do not continue to Batch 2 until instructed.