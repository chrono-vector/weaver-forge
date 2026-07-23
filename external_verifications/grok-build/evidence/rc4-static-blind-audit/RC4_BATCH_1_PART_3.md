RC4 BATCH 1 — PART 3 OF 4
Part-3 scope

This part inspected only the remaining Batch-1 cross-document, schema, and test consistency surrounding the host orchestrator. It did not begin the Batch-2 image, container bootstrap, Cargo, artifact, or outcome audit.
No script, validator, test, Docker command, build tool, or product was executed.

1. Policy treatment of Docker metadata queries before identity enforcement
Finding 1.1 — The package does not explicitly authorize pre-identity Docker metadata queries

Classification: AMBIGUOUS

Path: external_verifications/grok-build/witness-package/WITNESS_RUNBOOK.md
Heading: Docker contract
Lines: approximately 206–231
Path: external_verifications/grok-build/witness-package/WITNESS_REQUIREMENTS.md
Headings: image identity and Docker requirements
The documentation describes:
image pull;
image inspection;
platform verification;
container execution;
but does not clearly state that docker version and docker context show may run before package/source identity validation.
There is therefore no explicit policy exception to the requested ordering.
Finding 1.2 — The script labels the metadata queries as environment recording

Classification: CLEAR

Path: external_verifications/grok-build/witness-package/scripts/run_witness_narrow_build.sh
Function: record_host_environment
Lines: 1008–1027
The commands populate:
docker_client
docker_server
docker_ctx

for ENVIRONMENT.txt.
They are informational host-environment facts rather than package/source identity gates.

Finding 1.3 — These queries are not load-bearing for package or source identity

Classification: CLEAR

Path: same
Function: record_host_environment
Lines: 1019–1027
Their results do not control:
tag resolution;
package HEAD;
Grok Build commit;
source cleanliness;
Cargo.lock;
image digest;
build command.
Failures are converted to UNKNOWN.
Finding 1.4 — Failure of the metadata queries is ignored

Classification: CLEAR

Path: same
Lines: 1020–1022
Each command uses:
... 2>/dev/null || echo UNKNOWN

Therefore:

Docker unavailable;
daemon unavailable;
context failure;
formatting failure
does not abort at this point.
Finding 1.5 — The early queries may still contact the Docker daemon

Classification: CLEAR WITH LIMITATIONS
docker version may query both client and server, and docker context show invokes the Docker CLI.
They do not start a container, but they are still Docker executions and may access daemon configuration before identity checks.

Finding 1.6 — Moving the queries is required to satisfy the documented strict ordering

Classification: BLOCKED

Script ordering:
environment recording: approximately 1072–1073;
package/source checks: 1075–1301;
image pull: around 1391;
docker run: around 1477–1494.
If the required contract is literally:
no Docker execution before all required identity checks pass

then docker version and docker context show must be moved after:

rc4 tag resolution;
package detached/HEAD/clean checks;
Grok Build detached/HEAD/clean checks;
pre-Docker Cargo.lock match.
Alternatively, the policy would need to distinguish harmless Docker metadata queries from image/container execution. The current documents do not make that distinction explicit enough.
2. Raw annotated-tag object-type enforcement
Finding 2.1 — The script resolves the exact tag commit

Classification: CLEAR

Path: scripts/run_witness_narrow_build.sh
Tag resolution
Lines: approximately 1087–1114
It resolves:
refs/tags/${EFFECTIVE_WEAVER_FORGE_TAG}^{commit}

and validates the resulting 40-character lowercase commit.

Finding 2.2 — The script does not inspect the raw tag object type

Classification: MISSING

Path: same
Tag-resolution block
Lines: approximately 1087–1114
No command equivalent to:
git cat-file -t refs/tags/${EFFECTIVE_WEAVER_FORGE_TAG}

is present.

Finding 2.3 — ^{commit} does not prove the tag is annotated

Classification: CLEAR WITH LIMITATIONS
Both annotated and lightweight tags can dereference to a commit using ^{commit}.
The script proves:

the ref exists;
it ultimately names a commit;
the checked-out HEAD matches that commit.
It does not independently prove that the raw ref object is a tag object.
Finding 2.4 — Normative wording repeatedly calls the tag annotated

Classification: AMBIGUOUS
Representative paths:

WITNESS_REQUIREMENTS.md:77, 93
WITNESS_RUNBOOK.md:57–66
WITNESS_PACKAGE_VERSION.md, package identity section
WITNESS_PACKAGE_MANIFEST.md:92–95
The documents use:
annotated tag
annotated_tag_resolution

as an asserted authority model, but the host script enforces only tag-to-commit resolution.

Finding 2.5 — Direct object-type enforcement should be added

Classification: BLOCKED
To make the executable contract match the normative wording, the host should require:

git -C "${WF_DIR}" cat-file -t "refs/tags/${EFFECTIVE_WEAVER_FORGE_TAG}"

to output exactly:

tag

before checkout or Docker-related operations.
Failure should finalize a pre-Docker infrastructure or canonical-identity failure and record the observed object type.

3. canonical_run vocabulary consistency
Finding 3.1 — Normative package-identity template uses lowercase

Classification: CLEAR

Path: templates/WEAVER_FORGE_PACKAGE_IDENTITY.txt
Field: canonical_run
Lines: 4, 21
Vocabulary:
yes
no
Finding 3.2 — Validator requires lowercase in package identity

Classification: CLEAR

Path: scripts/validate_witness_evidence.py
Function: check_weaver_forge_package_identity
Lines: 708–712
Accepted values:
yes
no
Finding 3.3 — Generated package identity matches the validator

Classification: CLEAR

Path: scripts/run_witness_narrow_build.sh
WEAVER_FORGE_PACKAGE_IDENTITY.txt writer
Line: approximately 1171
It writes lowercase:
canonical_run=yes|no
Finding 3.4 — Host metadata and generated deviations use uppercase

Classification: CLEAR WITH LIMITATIONS

Path: host script
HOST_RUN_METADATA.txt writer
Line: 889
DEVIATIONS.txt writer
Line: 938
final metadata
Line: 1766
These use:
YES
NO
Finding 3.5 — HOST_RUN_METADATA.txt has no normative template

Classification: CLEAR WITH LIMITATIONS

Expected path: templates/HOST_RUN_METADATA.txt
Result: absent
HOST_RUN_METADATA.txt is optional auxiliary evidence, so absence of a template is documented. However, its use of a differently cased canonical_run vocabulary is not constrained by a schema.
Finding 3.6 — Generated DEVIATIONS.txt does not match its normative template structure

Classification: BLOCKED

Template: templates/DEVIATIONS.txt:1–12
Generator: host script 934–955
The template requires indexed entries when deviations are present:
deviation_<n>_description
deviation_<n>_severity
deviation_<n>_canonical_identity_impact
deviation_<n>_verdict_ceiling

The generator instead writes:

canonical_run=YES|NO
verdict_ceiling=...
changed_identity_field_count=...
--- changed identity fields ---

without the required indexed deviation fields.
This is more serious than capitalization alone: the canonical host-generated deviation file is not the normative submission form expected by the validator.

Finding 3.7 — canonical_run should have one vocabulary everywhere

Classification: CLEAR WITH LIMITATIONS
The cleanest repair is:

canonical_run=yes|no

across all evidence files and templates.
Uppercase should be reserved for fields whose schema explicitly defines uppercase, such as some execution declarations.

4. Rust and DotSlash expected-version deviation severity
Finding 4.1 — Both values are canonical fixed defaults

Classification: CLEAR

Path: host script
Constants: lines 50–51
Effective values: lines 71–72
EXPECTED_RUSTC_VERSION=1.92.0
EXPECTED_DOTSLASH_VERSION=0.5.7
Finding 4.2 — Both pass through the explicit override gate

Classification: CLEAR

Path: host script
apply_identity_gate
Lines: 595–596
A differing value requires --noncanonical-deviation.
Finding 4.3 — Neither receives the host’s FAIL identity ceiling

Classification: CLEAR WITH LIMITATIONS

Path: host script
compute_verdict_ceiling
Lines: 253–278
The FAIL list includes:
URLs;
tags/commits;
image;
lock hash;
build command.
It omits:
EXPECTED_RUSTC_VERSION
EXPECTED_DOTSLASH_VERSION

Thus an accepted change normally receives PARTIAL from the host.

Finding 4.4 — Classification policy does not list them as canonical identity fields

Classification: CLEAR

Path: WITNESS_CLASSIFICATION.md
Deviation table
Lines: 28–31
The enumerated identity fields similarly omit Rust/DotSlash expected versions.
Finding 4.5 — Changing these versions can materially alter the accepted execution

Classification: BLOCKED
A changed expected Rust version can cause the container to accept a different compiler/toolchain.
A changed expected DotSlash version can cause it to install and accept a different bootstrap executable.
These are not cosmetic differences. They can alter:

dependency resolution behavior;
compilation behavior;
bootstrap execution;
reproducibility.
The severity model should not treat them as ordinary nonidentity PARTIAL deviations merely because the repository/image/lock remain unchanged.
Finding 4.6 — Validator pins DotSlash independently

Classification: CLEAR WITH LIMITATIONS

Path: scripts/validate_witness_evidence.py
Constant: line 33
Semantic check: line approximately 830
The validator expects DotSlash 0.5.7 in final evidence.
This means an orchestrator-approved alternative expected version would likely conflict with validator expectations, creating another host-policy-validator mismatch.
Finding 4.7 — Rust-version pinning also requires consistent validator treatment

Classification: CLEAR WITH LIMITATIONS
The final evidence schema records Rust/Cargo versions, but the host’s override model should not permit a disclosed alternative that the validator or canonical requirements still treat as fixed.

5. Run-ID and evidence-directory collision handling
Finding 5.1 — Run ID has a randomized primary path

Classification: CLEAR

Path: host script
Function: short_run_id
Lines: 837–847
Preferred suffix:
openssl rand -hex 3

This gives six hexadecimal characters.

Finding 5.2 — Fallback uses only UTC time to the second

Classification: CLEAR WITH LIMITATIONS

Lines: 840–842
Fallback:
date -u +%H%M%S

Two runs for the same Witness on the same date within one second can collide.

Finding 5.3 — Preexisting EVIDENCE_DIR is merged, not rejected or reset

Classification: BLOCKED

Path: host script
Lines: 857, 865
The script performs:
mkdir -p "${WORK_ROOT}" "${EVIDENCE_DIR}"

It does not require the directory to be absent or empty.
It also does not call safe_reset_managed_path for the selected run directory.

Finding 5.4 — Mandatory files are overwritten individually

Classification: CLEAR

Lines: 871–877
init_mandatory_evidence rewrites each mandatory file with a NOT_REACHED placeholder.
Finding 5.5 — Existing auxiliary or manual files remain

Classification: BLOCKED
A colliding evidence directory may already contain:

HOST_RUN_METADATA.txt;
image-pull logs;
CARGO_LOCK_INTEGRITY.txt;
WITNESS_STATEMENT.md;
WITNESS_VERDICT.md;
REDACTIONS.md;
an old manifest;
unknown files.
The initialization loop does not remove them.
Finding 5.6 — Closed inventory detects only unlisted regular files at the end

Classification: CLEAR WITH LIMITATIONS

Path: host script
Function: enforce_closed_aux_inventory
Lines: 1730–1748
It scans:
find "${EVIDENCE_DIR}" -maxdepth 1 -type f

and aborts for filenames outside the automated allow-list.
This can detect unknown regular files, but it does not prove that allowed files belong to the current run.

Finding 5.7 — Manual files can trigger a late abort during automated execution

Classification: BLOCKED
The function’s allowed list includes:

mandatory automated files;
optional automated files;
DEVIATIONS.txt.
It does not include:
WITNESS_STATEMENT.md
WITNESS_VERDICT.md
REDACTIONS.md
EVIDENCE_MANIFEST.sha256

If these remain from a colliding prior run, the script aborts only near the end.

Finding 5.8 — A prior allowed auxiliary file may be silently overwritten or appended

Classification: BLOCKED
Examples:

HOST_RUN_METADATA.txt is overwritten initially, then appended later.
old image logs are overwritten only if those stages are reached.
an old CARGO_LOCK_INTEGRITY.txt may be overwritten at its writer stage.
A failure before all writers run can leave mixed-generation evidence.
Finding 5.9 — Collision can weaken closed-inventory and run-integrity guarantees

Classification: BLOCKED
The closed inventory guarantees only that filenames are allowed, not that:

every file was freshly created;
no prior-run content survived;
all fields correspond to one run;
manual forms match the current run.
A preexisting run directory therefore risks mixed evidence even when the final filename inventory is closed.
Finding 5.10 — Evidence directory should be created atomically

Classification: CLEAR
Required correction:

mkdir "${EVIDENCE_DIR}"

without -p, after confirming its parent exists.
If it already exists, abort before evidence initialization.
A stronger design would create a random temporary run directory atomically and then record its finalized ID.

6. Exact host-safety test coverage
Finding 6.1 — Canonical override rejection has only a textual assertion

Classification: CLEAR WITH LIMITATIONS

Path: scripts/tests/test_validate_witness_evidence.py
Test: test_override_requires_noncanonical_flag
Lines: 635–636
It verifies only that an error string exists.
Finding 6.2 — Explicit noncanonical acceptance is not behaviorally tested

Classification: MISSING
No test proves a mismatch:

aborts without the flag;
proceeds with the flag;
records the changed field.
Finding 6.3 — canonical_run=NO evidence generation is not tested

Classification: MISSING
The test suite does not parse actual host-generated:

HOST_RUN_METADATA.txt;
DEVIATIONS.txt;
WEAVER_FORGE_PACKAGE_IDENTITY.txt
for one noncanonical scenario.
Finding 6.4 — Host verdict-ceiling computation is not behaviorally tested

Classification: MISSING

Static test: lines 638–642
Validator ceiling test: lines 711–733
The validator test proves a manually constructed proposed PASS above PARTIAL is rejected.
It does not prove the host computes the correct ceiling for each override.
Finding 6.5 — WITNESS_ID matrix is missing

Classification: MISSING

Existing test: 657–662
Only textual presence is checked.
No valid/invalid matrix exists.
Finding 6.6 — Dangerous WORK_ROOT matrix is missing

Classification: MISSING

Existing test: 644–655
Only guard messages are checked.
No actual path-resolution cases are exercised.
Finding 6.7 — Repository ancestor/descendant matrix is missing

Classification: MISSING
The tests do not exercise:

exact repo root;
ancestor;
descendant;
symlink alias to any of them.
Finding 6.8 — WSL drive-root matrix is missing

Classification: MISSING
No direct cases such as:

/mnt/c
/mnt/C
/mnt/cc
/mnt/c/subdir

are tested against expected accept/reject behavior.

Finding 6.9 — Nonempty-reset authorization is not behaviorally tested

Classification: MISSING
No test proves:

nonempty root aborts without authorization;
interactive exact confirmation succeeds;
incorrect confirmation aborts;
noninteractive mode requires force;
only managed children are removed.
Finding 6.10 — Managed-child symlink target survival is not tested

Classification: MISSING

Existing static test: 663–667
No external target directory is created and verified untouched.
Finding 6.11 — Package detached-state probe lacks a dedicated test

Classification: MISSING
The suite has:

test_grok_detached_probe_present

but no matching package-clone detached-probe assertion.

Finding 6.12 — Annotated tag object type is not tested

Classification: MISSING
No fixture or shell-contract test distinguishes:

annotated tag;
lightweight tag.
Finding 6.13 — Evidence-directory collision is not tested

Classification: MISSING
No test precreates the selected run directory and checks whether the script rejects, resets, or merges it.

Finding 6.14 — Docker command ordering is not tested

Classification: MISSING
No source-order assertion verifies that every docker invocation occurs after all package/source/lock checks.

Finding 6.15 — Existing host tests are accurately described as static

Classification: CLEAR

Test file: lines 610–619
The heading explicitly says:
read from the shell scripts, never executed
7. Golden fixtures and actual host-generated fields
Finding 7.1 — RC4 adds script/schema contract tests

Classification: CLEAR

Path: scripts/tests/test_validate_witness_evidence.py
Class: ContractTests
Lines: 128–202
These extract keys from host/container writer blocks and compare them with validator schemas for selected evidence files.
Finding 7.2 — Contract tests cover several formerly mismatched files

Classification: CLEAR
Covered:

CLEAN_TARGET_PROOF.txt;
BUILD_ENVIRONMENT.txt;
BUILD_TIMING.txt;
BUILD_EXIT_CODE.txt;
STATIC_ARTIFACT_INSPECTION.txt;
IMAGE_IDENTITY.txt;
ENVIRONMENT.txt;
POST_BUILD_INTEGRITY.txt.
Finding 7.3 — Contract tests inspect source text, not actual shell output

Classification: CLEAR WITH LIMITATIONS

Helper functions: lines 47–91
They parse:
echo "key=..."

inside source blocks.
They do not execute the host or container generators.
Therefore they prove writer-key presence, not:

runtime branch completeness;
exact emitted values;
duplicate keys across branches;
quoting behavior;
failure-path output.
Finding 7.4 — Golden fixtures are synthetic

Classification: CLEAR WITH LIMITATIONS

Test header: lines 8–9
Fixture helper: lines 99–109
Golden-fixture tests: lines 235–257
Scenarios are constructed through:
fixtures_lib.py

and written into temporary or committed fixture trees.
They are not captured outputs from canonical host-script runs.

Finding 7.5 — Synthetic fixtures and builders share the same assumptions

Classification: CLEAR WITH LIMITATIONS

scripts/VALIDATOR.md:412–416
The document says committed fixtures and temporary trees use the same builder so they cannot drift from one another.
That prevents fixture-copy drift, but not drift between:
fixture builder;
actual host runtime behavior.
Finding 7.6 — No golden host-generated noncanonical evidence exists

Classification: MISSING
There is no actual host-output fixture proving:

canonical_run;
changed field enumeration;
deviation severity;
verdict ceiling;
manual-form compatibility.
Finding 7.7 — DEVIATIONS generator/template mismatch is not caught by the contract suite

Classification: BLOCKED
ContractTests does not compare the host-generated DEVIATIONS.txt writer with:

the normative template;
validator’s indexed deviation model.
This leaves a canonical host-output incompatibility undetected.
Finding 7.8 — HOST_RUN_METADATA has no schema contract test

Classification: CLEAR WITH LIMITATIONS
Because it is optional auxiliary evidence, this may be intentional. However, it carries load-bearing run metadata such as:

canonical/effective identities;
canonical_run;
verdict_ceiling;
manifest lifecycle.
Its fields are not validator-enforced.
8. Public or normative overstatement of test closure
Finding 8.1 — VALIDATOR.md accurately calls host tests static assertions

Classification: CLEAR

Path: scripts/VALIDATOR.md
Lines: approximately 391–416
It explicitly states that host safety assertions read shell-script text without executing it.
Finding 8.2 — Test-suite header accurately describes contract and fixture scope

Classification: CLEAR

Path: test file
Lines: 1–18
It does not claim behavioral shell execution.
Finding 8.3 — “Cannot drift” wording is too broad

Classification: AMBIGUOUS

Path: scripts/VALIDATOR.md
Lines: 412–416
The statement that on-disk fixtures and tests “cannot drift” is true only relative to their shared builder.
A reader could mistake it for proof that fixtures cannot drift from the host/container scripts. They can.
Finding 8.4 — Current readiness policy still tracks orchestrator alignment as open

Classification: CLEAR

Path: PACKAGE_READINESS_POLICY.md
Lines: 74–78
The package does not claim complete closure of all host classification alignment.
Finding 8.5 — RC4 change-log wording overstates time-stable status closure

Classification: BLOCKED

Path: WITNESS_RUNBOOK.md
Change log: line 418
Path: PACKAGE_READINESS_POLICY.md
Change log: line 110
They claim time-stable annotated-tag wording or removal of pending assertions, while Part 1 found current normative pending-tag language still present.
Finding 8.6 — Host-orchestrator remediation comment overstates closure breadth

Classification: CLEAR WITH LIMITATIONS

Path: host script
Header: lines 5–9
It says the script was rewritten to close a long list of rc3 blockers.
Many host-side controls were improved, but:
early Docker metadata ordering;
raw annotated-tag object type;
DEVIATIONS schema;
evidence-directory collision;
behavioral safety tests
remain unresolved.
9. Original Batch-1 scope items now fully inspected

The following original Batch-1 items are now fully inspected:

transfer/archive identity;
rc1–rc4 immutable-history representation;
rc4 package version and canonical tag;
annotated-tag resolution policy and script implementation;
detached package HEAD and clean-clone enforcement;
absence of self-referential commit placeholders;
time-stable tag wording;
public discoverability;
canonical platform boundaries;
canonical fixed-value enforcement;
noncanonical-deviation behavior;
Witness-ID validation;
WORK_ROOT safety;
managed-child symlink safety;
fresh Weaver Forge clone and rc4 resolution;
fresh Grok Build clone and pinned detached checkout;
direct detached-state probes;
source HEAD, cleanliness, and pre-Docker Cargo.lock enforcement;
isolated host/work/cache/target/evidence paths;
host-side safety and contract-test coverage.
All requested Batch-1 topic areas have now received substantive inspection. Part 4 is reserved for consolidation, any final cross-checks needed to ensure no scope item was omitted, and the complete Batch-1 blocker/limitation/correction lists.
10. Items reserved for Part 4

Part 4 will:

consolidate every Part-1 through Part-3 finding;
confirm all required minimum files were inspected;
produce the complete blocker list;
produce the complete non-fatal limitation list;
provide exact required corrections;
state explicitly whether every requested Batch-1 scope item was inspected;
close Batch 1 without issuing a package-readiness verdict.
It will not begin Batch 2.
11. Complete blockers carried forward
Current normative documents inside the fixed rc4 tag still describe rc4 as under preparation, pending commit/tag, or not yet published.
Change-log/status claims say tag-pending wording was removed, but contradictory current wording remains.
The fixed rc4 snapshot does not represent rc4 itself as an already-published immutable release.
docker version and docker context show execute before package-tag resolution, package/source identity checks, and pre-Docker Cargo.lock verification.
The host does not directly prove that the raw rc4 ref object type is an annotated tag.
The canonical host-generated DEVIATIONS.txt does not follow the normative indexed deviation schema.
Rust and DotSlash accepted-version overrides can materially alter execution but do not receive the host’s FAIL identity ceiling.
A preexisting EVIDENCE_DIR is merged rather than atomically rejected.
Evidence-directory collision can leave mixed prior/current evidence and weaken closed-inventory guarantees.
The host safety suite lacks behavioral coverage for load-bearing authorization, override, identity, collision, and ordering controls.
No behavioral or golden test proves actual host-generated noncanonical fields match templates and validator rules.
Public/change-log statements overstate closure of time-stable wording and some rc4 remediation areas.
12. Complete non-fatal limitations carried forward
Public discoverability is strong, but stale pre-publication wording creates uncertainty about whether rc4 is the intended fixed audit target.
rc4 immutability is defined prospectively rather than reflected as already published.
canonical_run capitalization differs across generated files.
The machine ceiling covers identity overrides only; full classification still depends on the normative policy.
The host’s Rust/DotSlash override handling conflicts with the stricter fixed-version expectations elsewhere.
The evidence run-ID fallback can collide within one second.
Optional HOST_RUN_METADATA.txt has no normative template or validator schema.
Contract tests inspect emitted key names in source text rather than actual runtime output.
Golden fixtures are synthetic and share assumptions with their builder.
Exact WITNESS_ID behavior lacks a valid/invalid matrix.
WORK_ROOT dangerous-path and repository-overlap behavior lacks a matrix.
Nonempty-reset authorization lacks behavioral tests.
Managed-child symlink safety lacks target-survival testing.
The package detached-state probe lacks a dedicated isolated test.
Annotated-tag versus lightweight-tag behavior lacks testing.
Docker command ordering lacks a test.
Closed-inventory validation checks allowed filenames, not current-run provenance.
canonical_run vocabulary should be normalized to one case.
“Fixtures cannot drift” is true only relative to the shared fixture builder, not the actual scripts.
Docker metadata-query failure is deliberately converted to UNKNOWN, which is acceptable only if those fields remain informational.
No final package-readiness verdict is issued in this part.
RC4 BATCH 1 — PART 3 COMPLETE
Do not continue to Part 4 until instructed.