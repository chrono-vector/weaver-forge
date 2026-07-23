RC4 STATIC BLIND AUDIT — BATCH 4 OF 4
1. Batch-4 scope and boundaries

This Batch 4 integrates the completed static findings from:

RC4 Batch 1, Parts 1–4;
RC4 Batch 2;
RC4 Batch 3, Parts 1–3.
The review applies the package’s own readiness threshold to:
release identity and public status;
host acquisition and filesystem safety;
container execution design;
evidence generation and schema closure;
manifest completeness;
outcome authority;
manual Witness forms;
deviations, verdict ceilings, and redactions;
correction and maintainer-intake lifecycle;
claim-register semantics;
Independent Witness handoff readiness.
No transfer, archive, extraction, build, Docker, Cargo, Rust, Rustup, DotSlash, protoc, Witness-script, validator, validator-test, ldd, or Grok Build product execution occurred in this Batch.
No file, repository, commit, push, or tag operation occurred.
2. Fixed rc4 identity

The audited fixed identity is:

Package version:
1.0.0-rc4

Canonical annotated tag:
grok-build-witness-v1.0.0-rc4

Tagged Weaver Forge commit:
039b46737c5968a81fb756d7a6d1d0dd57b6ad96

Commit tree:
071c4c1f4ed1b3e3a9164709c79ea9f5235ec2e9

Pinned Grok Build commit:
98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce

Pinned Rust image:
docker.io/library/rust@sha256:6ca5ad23231207874325a751b9df584d51cd42c066c74c6963c264e3233c3e8e

Batch 1 confirmed that the package consistently embeds the rc4 version, canonical tag, pinned Grok Build commit, fixed image digest, fresh-clone model, detached checkout checks, source cleanliness checks, and pre-Docker Cargo.lock verification. It also established that current rc4 documents still describe the release prospectively or as pending, rather than consistently recording the already-fixed immutable tag.

3. Prior audit completion confirmation

All required audit stages are complete:

transfer/archive verification: previously complete;
extraction: previously complete;
Batch 1: complete;
Batch 2: complete;
Batch 3: complete;
Batch 4 integrated static disposition: completed here.
Every required technical and policy area was inspected:
release identity;
host safety;
Docker/image behavior;
mount design;
toolchain and bootstrap;
target cleanliness;
Cargo outcome handling;
artifact/static inspection;
post-build integrity;
evidence inventory;
schemas and templates;
validator behavior;
manifest lifecycle;
manual forms;
deviations;
redactions;
verdict classification;
submission;
correction and intake;
public and claim-register status.
4. Confirmed strengths

The package contains substantial, real controls.

Release and acquisition
Canonical package version and tag are fixed.
Weaver Forge and Grok Build are freshly cloned.
Package and source checkouts are required to be detached.
Package HEAD is compared with the resolved tag commit.
Grok Build HEAD is compared with the pinned commit.
Both trees must be clean.
Cargo.lock is hashed and checked before Docker.
Canonical values cannot be silently changed by environment variables.
Explicit noncanonical mode exists.
Host safety
WITNESS_ID syntax is conservative.
dangerous WORK_ROOT paths are rejected;
repository overlap protections exist;
nonempty reset requires authorization;
managed-child symlinks are unlinked rather than recursively traversed.
Image and container path
The exact digest-pinned Rust image is requested.
Pull stdout/stderr and direct pull exit are captured.
Pull failure stops before inspect or run.
Cached-image fallback is not accepted after pull failure.
Image ID, RepoDigests, OS, and architecture are checked.
Docker run uses the pinned digest and explicit linux/amd64.
Rust and Cargo versions are probed.
DotSlash 0.5.7 is installed with --locked and validated.
Bootstrap and Grok Build Cargo targets are separated.
Pre-bootstrap and immediate pre-Cargo target cleanliness are checked.
Build and artifact handling
Canonical Cargo command is fixed.
Cargo stdout/stderr are separated.
Direct Cargo nonzero exit is preserved.
Cargo zero plus missing artifact produces a distinct nonzero failure.
Artifact-present execution proceeds only to static inspection.
sha256sum, stat, file, readelf, and objdump evidence is captured.
Static-inspection command failure exits nonzero.
The product is never intentionally executed.
ldd is prohibited.
Outcome and integrity
The container writes principal outcome and timing evidence from one outcome path.
The host does not normally reinterpret an ordinary container result from artifact presence or raw Docker exit.
Missing, duplicate, or invalid outcome text is treated as infrastructure failure.
Source HEAD, source cleanliness, Cargo.lock unchanged state, and expected post-lock hash are recomputed after Docker.
Submission and classification
Five build outcomes are named.
Proposed verdict above the selected ceiling is rejected.
Cargo failure and artifact missing cap at FAIL.
build-not-started and infrastructure failure cap at INDETERMINATE.
static-inspection failure caps at PARTIAL.
negative outcomes are intended to remain visible and submit-able.
Witness verdict, maintainer intake, and overall package readiness are conceptually separated.
These strengths are not enough to meet the package’s own readiness threshold because material end-to-end defects remain.
5. Integrated material blockers

The original blockers are preserved below. Where blockers overlap, the relationship is stated without merging or dropping the original findings.

Blocker 5.1 — Fixed rc4 still describes itself as pending
Classification: BLOCKED
Origin: Batch 1, Blocker 1
Paths:
README.md
external_verifications/grok-build/README.md
external_verifications/grok-build/VERDICT.md
external_verifications/grok-build/witness-package/README.md
external_verifications/grok-build/witness-package/WITNESS_PACKAGE_VERSION.md
external_verifications/grok-build/witness-package/WITNESS_RUNBOOK.md
external_verifications/grok-build/witness-package/PACKAGE_READINESS_POLICY.md
Heading/field: current status banners and release-status sections
Evidence: wording still says rc4 is under preparation, pending commit/tag, or not yet published.
Policy consequence: the fixed package is internally inconsistent and cannot truthfully describe its own release state.
Mandatory correction: replace prospective wording with time-stable text identifying the already-fixed tag and commit while keeping readiness unresolved.
Blocker 5.2 — Closure statements contradict current content
Classification: BLOCKED
Origin: Batch 1, Blockers 2 and 12
Paths:
external_verifications/grok-build/RESULTS.md
external_verifications/grok-build/CLAIM_REGISTER.md
external_verifications/grok-build/witness-package/WITNESS_RUNBOOK.md
external_verifications/grok-build/witness-package/PACKAGE_READINESS_POLICY.md
Heading: rc4 remediation/change-log/status summaries
Evidence: statements say pending wording or related defects were closed while contradictory text and untested paths remain.
Policy consequence: public audit records overstate remediation.
Mandatory correction: change each claim to the exact narrow remediation actually implemented and leave unresolved controls open.
Blocker 5.3 — rc4 is not recorded as the already-published immutable release
Classification: BLOCKED
Origin: Batch 1, Blocker 3
Paths:
external_verifications/grok-build/witness-package/README.md
external_verifications/grok-build/witness-package/WITNESS_PACKAGE_VERSION.md
external_verifications/grok-build/README.md
external_verifications/grok-build/WITNESS_HANDOFF.md
Heading: immutable release history
Evidence: rc1–rc3 history is represented, but rc4 remains prospective.
Policy consequence: release history and current identity disagree.
Mandatory correction: append the rc4 tag, commit, and fixed-under-audit status without claiming readiness.
Blocker 5.4 — Docker metadata is invoked before identity closure
Classification: BLOCKED
Origin: Batch 1, Blocker 4
Path: scripts/run_witness_narrow_build.sh
Function: record_host_environment
Evidence: docker version and docker context show precede package/source/lock identity completion.
Policy consequence: violates the package’s literal no-Docker-before-identity contract.
Mandatory correction: move all Docker CLI calls after package, source, and lock checks, or formally narrow the policy; moving them is preferred.
Blocker 5.5 — Raw annotated-tag type is not enforced
Classification: BLOCKED
Origin: Batch 1, Blocker 5
Path: host tag-resolution block
Evidence: refs/tags/<tag>^{commit} proves commit resolution but accepts a lightweight tag.
Policy consequence: annotated-tag authority is asserted but not enforced.
Mandatory correction: require git cat-file -t refs/tags/<tag> to equal tag, record it, and test lightweight-tag rejection.
Blocker 5.6 — DEVIATIONS.txt generator is incompatible with template and validator
Classification: BLOCKED
Origin: Batch 1, Blocker 6; Batch 3 deviation blockers 38 and 45
Paths:
host deviation writer;
templates/DEVIATIONS.txt;
validator deviation parser;
tests.
Evidence: host emits a summary/changed-field structure; the normative model expects indexed records.
Policy consequence: noncanonical evidence requires manual reconstruction and cannot be relied on for verdict enforcement.
Mandatory correction: make the real generator emit the exact indexed schema directly.
Blocker 5.7 — Rust/DotSlash deviations receive insufficient severity
Classification: BLOCKED
Origin: Batch 1, Blocker 7
Paths: host ceiling logic, requirements, classification policy, validator
Evidence: accepted version deviations require noncanonical mode but are not uniformly FAIL-level.
Policy consequence: materially altered toolchain identity can retain an unsupported ceiling.
Mandatory correction: prohibit those overrides or cap them at FAIL in both host and validator.
Blocker 5.8 — Evidence directory is not atomically fresh
Classification: BLOCKED
Origin: Batch 1, Blockers 8 and 9
Path: host evidence initialization
Evidence: mkdir -p permits reuse and merging.
Policy consequence: prior and current evidence can mix.
Mandatory correction: atomically create an absent directory; reject any collision before writing.
Blocker 5.9 — Behavioral host-safety and actual noncanonical-output tests are absent
Classification: BLOCKED
Origin: Batch 1, Blockers 10 and 11
Paths: host tests and validator tests
Evidence: source-text assertions and synthetic fixtures do not prove destructive-operation safety or actual writer output.
Policy consequence: material host controls are not regression-proven.
Mandatory correction: use temporary repositories and mocked external tools to behaviorally test every host safety and noncanonical branch.
Blocker 5.10 — Source read-only protection is bypassed through /work
Classification: BLOCKED
Origin: Batch 2, Blocker 1
Path: host Docker invocation

Evidence:

${SRC_DIR}:/src:ro
${WORK_ROOT}:/work:rw

while ${SRC_DIR} is beneath ${WORK_ROOT}.

Policy consequence: /work/grok-build exposes the same source read-write, so source immutability is not preventive.
Mandatory correction: keep source outside all writable mounts or mount only narrow writable subdirectories.
Blocker 5.11 — Unexpected container failures do not finalize all mandatory evidence
Classification: BLOCKED
Origin: Batch 2, Blocker 2
Path: container_narrow_build.sh
Functions: fail_build_not_started, fail_infrastructure
Evidence: mandatory files can remain preliminary or NOT_REACHED.
Policy consequence: some failure submissions require reconstruction and are not complete.
Mandatory correction: one schema-aware finalizer must finish every mandatory automated file on every exit.
Blocker 5.12 — Invalid/missing container outcome finalization is incomplete
Classification: BLOCKED
Origin: Batch 2, Blocker 3
Path: host invalid-outcome branch
Evidence: only principal outcome files are rewritten before abort; full post-Docker integrity and evidence closure are skipped.
Policy consequence: invalid outcome paths produce partial packages.
Mandatory correction: route through a comprehensive post-Docker infrastructure finalizer.
Blocker 5.13 — Host success is not conditioned on validator or full structural validity
Classification: BLOCKED
Origin: Batch 2, Blocker 4
Path: host final exit selection
Evidence: host can return Docker zero after limited checks without full schema/manifest validation.
Policy consequence: malformed but superficially successful evidence can accompany zero host exit.
Mandatory correction: gate zero on a complete structural checker over finalized evidence.
Blocker 5.14 — Host validates only outcome=, not the full tuple
Classification: BLOCKED
Origin: Batch 2, Blocker 5
Path: host outcome parser
Evidence: cargo_started, build status, Cargo exit, failure stage, timing, and status are not fully cross-validated.
Policy consequence: a contradictory outcome package can be accepted by the orchestrator.
Mandatory correction: parse and enforce the complete authoritative tuple.
Blocker 5.15 — POST_BUILD_INTEGRITY.txt can say status=OK when its gate fails
Classification: BLOCKED
Origin: Batch 2, Blocker 6
Path: host post-build writer
Evidence: top-level status=OK is unconditional while post_build_integrity_ok may be no.
Policy consequence: internally contradictory evidence.
Mandatory correction: write status=FAILED whenever the full gate is false.
Blocker 5.16 — Post-build generator, template, and validator are not aligned
Classification: BLOCKED
Origin: Batch 2, Blocker 7; Batch 3 schema blockers
Paths: post-build writer, template, validator, tests
Evidence: load-bearing generated fields are absent from the exact normative schema.
Policy consequence: successful-looking evidence may contain unvalidated integrity assertions.
Mandatory correction: define one exact field set and reject all drift.
Blocker 5.17 — Validator does not explicitly require all four post-build conditions
Classification: BLOCKED
Origin: Batch 2, Blocker 8
Path: check_post_build_integrity
Evidence: all four required yes values are not independently and completely enforced.
Policy consequence: PASS may survive a failed technical gate.
Mandatory correction: require all four yes fields plus post_build_integrity_ok=yes and status=OK.
Blocker 5.18 — Behavioral tests do not prove end-to-end host/container outcome preservation
Classification: BLOCKED
Origin: Batch 2, Blocker 9
Paths: tests and fixture builder
Evidence: tests inspect source text or synthetic evidence instead of actual writers and host rewrites.
Policy consequence: outcome authority and finalization can drift undetected.
Mandatory correction: generator-backed behavioral outcome tests for all paths.
Blocker 5.19 — Global false-success impossibility is unsupported
Classification: BLOCKED
Origin: Batch 2, Blocker 10
Relationship: umbrella consequence of Blockers 5.10–5.18; preserved separately.
Evidence: writable source alias, incomplete finalization, limited tuple validation, no validator-gated zero.
Policy consequence: readiness policy expressly requires NOT READY.
Mandatory correction: resolve all underlying false-success paths and test them behaviorally.
Blocker 5.20 — Auxiliary files may remain outside the manifest
Classification: BLOCKED
Origin: Batch 3 Part 1, Blockers 1 and 2
Path: manifest validator auxiliary exemption
Evidence: allowed auxiliary files can exist without entries.
Policy consequence: submission is not cryptographically closed.
Mandatory correction: require exactly one manifest entry for every regular file except the manifest itself.
Blocker 5.21 — Exact allowed-key schemas are not enforced
Classification: BLOCKED
Origin: Batch 3 Part 1, Blockers 3 and 4
Path: validator FILE_REQUIRED_FIELDS and parse_kv
Evidence: minimum fields are enforced, but unknown and extra keys are accepted.
Policy consequence: unvalidated assertions can coexist with a structural PASS.
Mandatory correction: define exact per-file required/optional/conditional key sets and reject unknown keys.
Blocker 5.22 — Validator outcome inference violates fail-closed authority
Classification: BLOCKED
Origin: Batch 3 Part 1, Blocker 5
Path: determine_outcome
Evidence: missing or invalid outcome can be inferred from secondary fields.
Policy consequence: exactly one explicit authoritative outcome is not fail-closed.
Mandatory correction: remove all inference and require one explicit valid outcome.
Blocker 5.23 — Complete cross-file outcome tuple is absent
Classification: BLOCKED
Origin: Batch 3 Part 1, Blocker 6
Relationship: overlaps Batch 2 host-parser weakness but applies package-wide.
Paths: build exit, timing, Docker exit, verdict, artifact/static, post-build files
Evidence: only selected fields are cross-checked.
Policy consequence: mutually inconsistent evidence may remain structurally accepted.
Mandatory correction: define and enforce one complete outcome tuple across all outcome-bearing files.
Blocker 5.24 — NOT_REACHED placeholders can survive final submission
Classification: BLOCKED
Origin: Batch 3 Part 1, Blockers 7 and 12
Paths: bootstrap, build command, build environment schemas
Evidence: validator skips normal schema for permitted placeholders on negative outcomes.
Policy consequence: a preliminary initializer state can be accepted as final evidence.
Mandatory correction: replace with explicit final NOT_APPLICABLE schemas.
Blocker 5.25 — No machine-wide current-run provenance
Classification: BLOCKED
Origin: Batch 3 Part 1, Blocker 8
Paths: all templates, manual forms, validator
Evidence: one run ID is not required across every file.
Policy consequence: mixed-run packages and copied forms can pass selected checks.
Mandatory correction: require one immutable run ID across all structured and manual evidence, with raw files bound through manifest metadata.
Blocker 5.26 — Host inventory checks only top-level regular files
Classification: BLOCKED
Origin: Batch 3 Part 1, Blocker 9
Path: host inventory function
Evidence: nested objects, directories, symlinks, and special objects are not comprehensively checked by the host.
Policy consequence: host zero can precede discovery of an invalid filesystem inventory.
Mandatory correction: recursively reject all unauthorized object types and paths.
Blocker 5.27 — Validator output can contaminate an allowed auxiliary filename
Classification: BLOCKED
Origin: Batch 3 Part 1, Blocker 10
Evidence: caller-controlled redirection into an exempt allowed filename may remain unhashed.
Policy consequence: final evidence can be contaminated without complete manifest closure.
Mandatory correction: eliminate manifest exemption and exact-schema validate auxiliary files.
Blocker 5.28 — evidence_inventory_complete lifecycle is circular
Classification: BLOCKED
Origin: Batch 3 Part 1, Blocker 11
Paths: manifest policy, runbook, post-build template
Evidence: field is said to become yes only after manifest validation, but changing it after validation invalidates the manifest.
Policy consequence: no coherent canonical finalization sequence exists.
Mandatory correction: set the field before final manifest generation, then validate once, with no post-validation edit.
Blocker 5.29 — Some failure packages require manual reconstruction
Classification: BLOCKED
Origin: Batch 3 Part 1, Blocker 13
Relationship: direct consequence of incomplete finalizers and placeholder schemas; preserved separately.
Evidence: Witness may need to reinterpret or rewrite load-bearing automated files.
Policy consequence: package fails the stated direct-use threshold.
Mandatory correction: all supported outcomes must be generator-complete.
Blocker 5.30 — WITNESS_STATEMENT.md is not bound to the run or outcome
Classification: BLOCKED
Origin: Batch 3 Part 2, Blocker 1
Path: statement template and validator
Evidence: no run ID, package tag, commits, or outcome.
Policy consequence: statement can be copied from another run.
Mandatory correction: add and cross-check all run and outcome identities.
Blocker 5.31 — Manual statement schema is internally incomplete
Classification: BLOCKED
Origin: Batch 3 Part 2, Blocker 2
Fields: ai_assistance_detail, upstream_product_commands_not_run
Evidence: template and semantic checks are not fully reflected in required fields.
Policy consequence: exact manual-form schema closure is absent.
Mandatory correction: include every normative field in exact allowed/required schema rules.
Blocker 5.32 — Verdict run ID, tag, and Weaver Forge commit are not fully cross-checked
Classification: BLOCKED
Origin: Batch 3 Part 2, Blockers 3–5 and 27
Path: verdict template and validator
Evidence: run ID is format-only; tag is grammar-only; commit is hex-only.
Policy consequence: verdict can refer to another run or package.
Mandatory correction: exact equality against package/source identity files.
Blocker 5.33 — New submissions are not forced to start with intake pending
Classification: BLOCKED
Origin: Batch 3 Part 2, Blockers 6 and 26
Path: validator intake values
Evidence: accepted/rejected/superseded values are structurally accepted in an initial submission.
Policy consequence: Witness can predeclare maintainer disposition.
Mandatory correction: separate initial-submission mode from later intake metadata.
Blocker 5.34 — Machine ceiling ignores deviations and canonical state
Classification: BLOCKED
Origin: Batch 3 Part 2, Blockers 7–12
Path: compute_verdict_ceiling
Evidence: deviation state and canonical_run are not complete ceiling inputs.
Policy consequence: unsupported PASS eligibility.
Mandatory correction: machine-recompute the full normative PASS checklist.
Blocker 5.35 — NONMATERIAL_DISCLOSED can retain PASS
Classification: BLOCKED
Origin: Batch 3 Part 2, Blocker 10
Path: deviation severity validation
Evidence: policy says maximum PARTIAL; validator forbids PASS only for stronger categories.
Policy consequence: policy/validator disagreement.
Mandatory correction: enforce PARTIAL maximum.
Blocker 5.36 — Deviation records are not exact, numeric, contiguous, or complete
Classification: BLOCKED
Origin: Batch 3 Part 2, Blockers 13–17
Evidence: nonnumeric and sparse indices are accepted; orphan fields may be ignored; impacts are self-declared; ceilings are not aggregated.
Policy consequence: deviation-bearing evidence can be incomplete or misclassified.
Mandatory correction: require count-backed numeric indices 1..n, full records, no orphans, and automatic strictest-ceiling aggregation.
Blocker 5.37 — Critical redactions are incompletely prohibited or bound
Classification: BLOCKED
Origin: Batch 3 Part 2, Blockers 19–22
Paths: redaction template and validator
Evidence: command, tag, URL, platform, architecture, and broad identity categories are incomplete; declarations are free-text and not bound to exact key/marker.
Policy consequence: structural validity may coexist with concealed critical evidence.
Mandatory correction: bind redactions to exact file/key/original-value hash/replacement marker and prohibit all reproducibility-critical categories.
Blocker 5.38 — Correction ledger is not machine-enforced
Classification: BLOCKED
Origin: Batch 3 Part 2, Blocker 23
Path: CORRECTION_LEDGER.md
Evidence: append-only, original hash, correction hash, and supersession semantics are documentation-only.
Policy consequence: immutable correction history is not structurally guaranteed.
Mandatory correction: define separately validated correction packages or machine-readable ledger records.
Blocker 5.39 — Maintainer intake mutates validated Witness evidence
Classification: BLOCKED
Origin: Batch 3 Part 2, Blockers 24–25
Paths: intake policy, verdict form, correction ledger
Evidence: policy says update maintainer_intake_verdict in the hashed verdict file after validation.
Policy consequence: original evidence and manifest become inconsistent.
Mandatory correction: move maintainer intake to separate append-only metadata outside the immutable Witness package.
Blocker 5.40 — Generator-backed full-submission tests are absent
Classification: BLOCKED
Origin: Batch 3 Part 2, Blocker 28; Batch 3 consolidation test blockers
Paths: fixture builder and validator tests
Evidence: no actual manifest-complete package generated through real writers for all six supported result states.
Policy consequence: central package contract is unproved.
Mandatory correction: generator-backed submission tests for every supported outcome, including mixed-run rejection.
6. Integrated non-fatal limitations

All prior non-fatal limitations remain unchanged.

Batch-1 limitations
Public discoverability is strong, but stale wording creates uncertainty.
rc4 immutability is represented prospectively.
canonical_run casing differs across files.
Machine ceiling does not encode the entire policy.
Rust/DotSlash override rules conflict with stricter identity wording.
Timestamp fallback run IDs can collide.
HOST_RUN_METADATA.txt has no normative schema.
Host tests inspect source text rather than behavior.
Golden fixtures share assumptions with their builder.
Witness-ID behavior lacks a complete matrix.
WORK_ROOT protections lack a complete behavioral matrix.
Reset authorization lacks behavioral tests.
symlink target survival is not behaviorally tested.
detached package probing lacks a dedicated isolated test.
annotated versus lightweight tags lack testing.
Docker ordering lacks testing.
closed inventory checks names rather than current-run origin.
canonical_run vocabulary is not normalized.
“Cannot drift” applies only within the synthetic fixture system.
Docker metadata failures become UNKNOWN.
tag dereference does not prove raw tag type.
run-ID randomness is not backed by atomic creation.
strong host controls are only textually tested.
optional auxiliary evidence contains load-bearing unschematized data.
Batch-2 limitations
RepoDigest comparison uses substring matching.
Docker inspect stderr is discarded.
OS/architecture failures share one stage.
image-pull logs are not semantically validated.
apt package versions are unpinned.
dpkg-query is best effort.
apt and DotSlash detailed logs remain outside EVIDENCE_DIR.
RUSTUP_HOME is inherited.
broad writable WORK_ROOT weakens path isolation.
evidence has multiple writable aliases.
protoc is not semantically version-pinned.
Cargo executes through bash -c.
Rust/Cargo parsing captures only x.y.z.
pre-Cargo failures generally collapse to exit 1.
static-inspection failure preserves artifact-present outcome and relies on ceiling.
host and container duplicate expected constants.
network mode is bridge.
missing cargo_started defaults to NO in host parsing.
BUILD_TIMING tuple consistency is partial.
validator outcome inference is more permissive than host authority.
extra generated fields are accepted.
product/ldd prohibition is static rather than behaviorally traced.
Batch-3 Part-1 limitations
pull-log presence documentation is inaccurate.
empty directories may remain unhashed.
special nonregular objects are not all explicitly rejected.
manifest generation accepts names broader than validator grammar.
post-validation immutability is procedural.
validator-output location depends on caller discipline.
failure-stage vocabulary is not centralized.
status vocabularies vary.
boolean capitalization varies.
manifest self-integrity depends on an outer immutable object.
synthetic fixtures do not prove actual runtime output.
malformed pseudo-fields may be treated as prose.
Batch-3 Part-2 limitations
independence is self-attested.
a Witness may propose a stricter verdict than the machine ceiling.
“first matching row governs” wording differs from conservative lowering behavior.
AI assistance detail is free text.
Witness identity is not externally verified.
failure-stage free text complicates precedence.
redaction prohibition uses substring matching.
permitted redactions reduce diagnostics.
correction guarantees rely on Git history.
historical intake needs a distinct mode.
human justification is not semantically validated.
manual forms are tested only through synthetic fixtures.
7. Readiness-policy application

The package’s own policy requires NOT READY when a material defect:

permits unsafe or false success;
prevents truthful complete submission of an allowed outcome;
leaves execution or evidence logic materially incomplete;
permits structurally inadequate evidence to validate;
requires manual reconstruction;
makes normative and generated schemas incompatible.
All six conditions are present.
Policy threshold analysis

Unsafe or false-success risk: present.

source is writable through a second mount;
host zero is not structurally validator-gated;
full outcome tuple is not enforced.
Incomplete negative-outcome submission: present.
unexpected infrastructure and invalid-outcome paths do not finalize all evidence;
NOT_REACHED can survive;
manual reconstruction may be required.
Incomplete successful-outcome submission: present.
manifest may omit auxiliary files;
run binding is incomplete;
post-build integrity and PASS checklist enforcement are incomplete.
Structurally inadequate evidence can survive selected checks: present.
unknown keys accepted;
auxiliary files may be unhashed;
outcome inference exists;
manual forms are incompletely bound.
Manual reconstruction required: present.
deviations;
some failure finalization;
lifecycle repair.
Material schema incompatibility: present.
deviation generator;
post-build integrity;
exact generator/template/validator equality.
The threshold for READY WITH LIMITATIONS is not met because the remaining defects are not merely disclosed constraints; they affect safety, truthfulness, closure, provenance, and verdict eligibility.
8. Public-status and release-history consistency
Current status

Classification: BLOCKED
The fixed rc4 package does not consistently describe itself as:

already fixed at grok-build-witness-v1.0.0-rc4

Instead, current-facing text still includes pending or under-preparation language.

Historical identities

Classification: CLEAR WITH LIMITATIONS
rc1–rc3 history is substantially preserved, but rc4 itself is not cleanly added as the current immutable release.

Change-log closure

Classification: BLOCKED
Closure claims exceed the inspected implementation in:

tag wording;
host safety coverage;
generator/fixture alignment;
remediation completeness.
Exact required public correction

Every current-facing status document must distinguish:

release identity:
fixed and immutable at rc4

static readiness:
NOT READY

Independent Witness reproduction:
not performed

C-014:
NOT_STARTED
9. Claim-register and claim-rollup assessment
C-014

Must remain:

NOT_STARTED

No audited evidence establishes a qualified Independent Witness reproduction.

C-026

An audit-recording claim may truthfully record that:

an owner-side/static blind audit was completed;
its report was recorded;
the static disposition was NOT READY.
It must not be described as:
package-readiness PASS;
Independent Witness execution;
Independent Witness reproduction;
C-014 completion.
Audit-recording PASS versus package readiness

Classification: BLOCKED where wording is ambiguous or overbroad
A claim may use PASS only for the narrow proposition:

the requested audit was completed and recorded

It must not roll up into package readiness without an explicit separate field.

Claim rollups

The rollup model must separately count:

audit-task completion;
remediation-task completion;
package-readiness status;
Independent Witness status.
A single aggregate PASS count is unsafe if it can make C-026 or earlier audit-recording claims appear to prove readiness.
Required correction

For C-014, C-026, and all related rollups, add explicit fields such as:

claim_scope=audit_recording
package_readiness_effect=none
independent_witness_effect=none
c014_effect=none

No claim should imply a reproduction occurred.

10. C-014 assessment

Status: NOT_STARTED
C-014 cannot advance because:

no qualified Independent Witness execution is present;
no Witness-generated finalized evidence package is present;
no independent host execution occurred;
no independent validator run occurred;
static owner-side inspection is not reproduction;
rc4 is statically NOT READY and should not be recommended for execution in its current form.
The correct transition remains:
C-014=NOT_STARTED

until a later corrected candidate is:

statically re-audited;
found ready for handoff;
executed by a qualified independent Witness;
submitted with complete evidence;
independently validated and classified.
11. Independent Witness handoff assessment
Can rc4 truthfully be handed off as execution-ready?

No.
A technically competent external Witness would still face:

contradictory release wording;
a writable source alias;
incomplete failure finalization;
schema mismatch;
placeholder final evidence;
incomplete run provenance;
incomplete manifest closure;
manual deviation reconstruction;
unsupported PASS paths;
incoherent maintainer-intake mutation.
Is owner contact or undocumented interpretation avoidable?

No.
For some failures and finalization states, the Witness would need to decide how to:

rewrite placeholders;
convert deviations;
resolve evidence_inventory_complete;
handle intake metadata;
reconcile schema mismatches.
Is execution recommended against rc4?

No.
The package should not be recommended for Independent Witness execution until the material static blockers are remediated in a new candidate.

12. Outcome-by-outcome final submission assessment
Outcome	Complete truthful automatic package	Manual reconstruction	Complete manifest	One-run binding	Correct ceiling	Final assessment
BUILD_NOT_STARTED	No	Possible/likely	No	No	Core INDETERMINATE yes	Not submission-clean
INFRASTRUCTURE_FAILURE	No	Yes on unexpected/invalid paths	No	No	Core INDETERMINATE yes	Not submission-clean
CARGO_FAILED	Ordinary path mostly complete	Usually no	No	No	Core FAIL yes	Structurally incomplete package
CARGO_SUCCEEDED_ARTIFACT_MISSING	Ordinary path mostly complete	Usually no	No	No	Core FAIL yes	Structurally incomplete package
Artifact present/static inspection failed	Mostly generated	Usually no	No	No	PARTIAL for detected failure	Structurally incomplete package
Successful artifact-present	Ordinary outputs produced	Manual forms/finalization still needed	No	No	Incomplete normative recomputation	Unsupported PASS possible
Outcome conclusion

One complete, truthful, cryptographically closed, current-run-bound evidence package cannot currently be produced for every supported outcome.
Negative outcomes are normatively preserved, but some actual failure paths are not generator-complete.

13. False-success and unsupported-PASS assessment
False success

Not structurally impossible.
Reasons:

source has a writable alias;
host zero is not conditioned on full structural validation;
host accepts only a partially validated outcome tuple;
post-build status can contradict its technical gate;
actual writer behavior is not fully behaviorally tested.
Unsupported PASS

Not structurally impossible.
PASS prevention is incomplete for:

canonical_run=no;
deviation_state=PRESENT;
NONMATERIAL_DISCLOSED;
unaggregated deviation ceilings;
selected post-build failures;
unknown extra keys;
unhashed auxiliary evidence;
mixed-run evidence;
copied manual forms;
incompletely prohibited redactions.
Negative outcomes

Negative outcomes can be represented conceptually and are not supposed to be upgraded.
However, complete submission is not assured on every path because finalization and schema gaps can require manual reconstruction.

14. Minimal mandatory remediation sequence

No new candidate tag should be created before the following sequence is complete.

1. Correct release and status truthfulness
update all current banners;
record rc4 as fixed immutable history;
narrow closure claims;
correct claim-register and rollup semantics.
2. Correct host filesystem and source-mount safety
remove the /work/grok-build writable source alias;
mount only narrow writable directories;
move every Docker call after identity closure;
enforce raw annotated-tag type.
3. Correct evidence-directory atomicity and run provenance
atomically create an absent EVIDENCE_DIR;
reject collisions;
introduce one immutable run ID across all evidence;
reject mixed-run content.
4. Make every failure path generator-complete
one common host finalizer;
one common container finalizer;
all mandatory files receive exact final schemas;
no final NOT_REACHED.
5. Establish exact generator/template/validator equality
exact allowed keys;
conditional schemas;
no unknown keys;
align post-build, deviation, host metadata, Docker exit, timing, and every other writer.
6. Make outcome authority and post-build integrity fail-closed
remove outcome inference;
enforce one full cross-file tuple;
require all post-build integrity fields;
write truthful status;
gate host zero on complete structural validity.
7. Cryptographically close the full object inventory
manifest every regular file;
reject nested files, directories, symlinks, FIFOs, sockets, devices, and unknown objects;
eliminate auxiliary exemptions.
8. Bind manual forms, deviations, verdict, and redaction
add run/tag/commit/outcome identity to statement and verdict;
enforce pending initial intake;
align deviations;
require numeric contiguous indices;
aggregate ceilings;
categorically bar noncanonical/deviation-present PASS;
bind redactions to exact keys and markers.
9. Make correction and intake immutable
never mutate original Witness evidence;
move maintainer intake to a separate append-only record;
create complete superseding packages;
preserve original and corrected manifests.
10. Add behavioral generator-backed tests

Test:

every supported outcome;
all failure finalizers;
exact schema output;
mount isolation;
run provenance;
mixed-run rejection;
full manifest closure;
PASS prevention;
correction/intake lifecycle.
11. Correct all public claims and rollups
distinguish audit completion from readiness;
distinguish readiness from Independent Witness reproduction;
keep C-014 unchanged;
record this rc4 static disposition as NOT READY.
12. Create and re-audit a new fixed candidate

Only after all above:

commit remediation;
create a new annotated candidate tag;
archive it;
repeat static blind audit from the fixed snapshot;
consider Independent Witness handoff only after a READY or qualifying READY WITH LIMITATIONS static result.
15. Recommended hardening after mandatory remediation
Publish machine-readable schemas for every evidence file.
Normalize boolean and status vocabularies.
use cryptographically random run IDs or mktemp -d.
separate automated staging from immutable final submission directories.
record full Rust/Cargo version provenance.
define exact protoc identity policy.
capture or hash apt and DotSlash logs.
use exact normalized RepoDigest matching.
capture Docker inspect stderr and direct exits.
execute Cargo through a direct argument vector rather than bash -c.
add detached signed final-submission metadata.
add distinct validator modes for:
initial Witness submission;
maintainer intake;
corrected/superseding package.
add explicit conflict-of-interest and public identity metadata for Witnesses.
add filesystem-level read-only sealing after final manifest creation.
16. Matters requiring actual Independent Witness execution

Static inspection cannot establish:

that the pinned image can actually be pulled;
that the image resolves to the expected ID and platform at execution time;
that apt/bootstrap succeeds;
that Rust/Cargo/DotSlash/protoc probes return the expected values;
that the pinned Grok Build commit compiles;
the actual Cargo exit;
whether the expected artifact is created;
the artifact SHA-256, size, ELF metadata, or Build ID;
actual post-build source and Cargo.lock states;
actual Witness independence;
actual human review;
actual evidence submission;
actual proposed Witness verdict;
actual maintainer intake.
Those matters belong only to a later qualified Independent Witness run against a corrected, statically ready fixed candidate.
17. Final static-audit disposition
NOT READY

This disposition follows the package’s own stated threshold.
The fixed rc4 snapshot contains material blockers that:

weaken preventive source immutability;
permit incomplete or mixed-run evidence;
allow submitted files to remain unhashed;
require manual reconstruction for some outcomes;
leave generator/template/validator contracts inconsistent;
fail to bind all evidence and manual forms to one run;
leave outcome authority incompletely fail-closed;
do not independently enforce every normative PASS-preventing condition;
create an incoherent correction and maintainer-intake lifecycle;
overstate selected public remediation and release-status claims.
Therefore:
rc4 does not satisfy its stated package-readiness policy;
rc4 is not suitable for Independent Witness handoff;
one complete truthful package cannot be guaranteed for every outcome;
false success is not structurally impossible;
unsupported PASS is not structurally impossible;
the fixed snapshot is not internally clean;
C-026 or similar audit-recording completion cannot imply readiness;
C-014 cannot advance.
RC4 STATIC BLIND AUDIT COMPLETE
No Independent Witness reproduction occurred.
No Independent Witness PASS is claimed.
C-014 remains NOT_STARTED.
Do not begin remediation until instructed.