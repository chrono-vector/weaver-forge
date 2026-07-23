16. Product and ldd prohibition — continuation
Finding 16.3 — Prohibition is encoded in generated outcome evidence

Classification: CLEAR

Path: external_verifications/grok-build/witness-package/scripts/container_narrow_build.sh
Functions: write_no_artifact_evidence, successful artifact writer
Lines: 150–196, 969–982
Every ordinary artifact path records:
product_executed=NO
ldd_used=NO
Finding 16.4 — Host Docker evidence independently records both prohibitions

Classification: CLEAR

Path: external_verifications/grok-build/witness-package/scripts/run_witness_narrow_build.sh
Function: write_docker_exit_code_authoritative
Lines: 964–977
Finding 16.5 — Validator requires exact NO

Classification: CLEAR

Path: external_verifications/grok-build/witness-package/scripts/validate_witness_evidence.py
Functions: check_docker_exit_code, check_artifact_identity
Lines: 986–1000, 1019–1025
Finding 16.6 — Static source-text tests do not prove runtime non-execution

Classification: CLEAR WITH LIMITATIONS
The absence of a product invocation and ldd command is statically clear. No behavioral tracing or syscall-level test exists, and none was executed in this audit.

17. Container outcome findings
Finding 17.1 — Container owns the authoritative ordinary outcome

Classification: CLEAR

Path: scripts/container_narrow_build.sh
Function: write_outcome_evidence
Lines: 108–145
The container writes both:
BUILD_EXIT_CODE.txt
BUILD_TIMING.txt

from one function using the same outcome, cargo_started, cargo_exit_code, and failure_stage arguments.

Finding 17.2 — Pre-Cargo failures are classified as BUILD_NOT_STARTED

Classification: CLEAR

Path: same
Function: fail_build_not_started
Lines: 420–438
Result:
outcome=BUILD_NOT_STARTED
cargo_started=NO
build_status=BUILD_NOT_STARTED
cargo_exit_code=NOT_APPLICABLE
Finding 17.3 — Unexpected container failures become INFRASTRUCTURE_FAILURE

Classification: CLEAR

Path: same
Functions: fail_infrastructure, on_err
Lines: 440–482
The ERR trap does not reinterpret an unexpected failure as an ordinary Cargo outcome.
Finding 17.4 — Cargo failure preserves the direct Cargo exit

Classification: CLEAR

Path: same
Cargo result branch
Lines: 828–848
For nonzero Cargo:
outcome=CARGO_FAILED
cargo_started=YES
build_status=FAILED
cargo_exit_code=<direct Cargo exit>
container exit=<same direct Cargo exit>
Finding 17.5 — Cargo zero plus missing artifact is a distinct failure

Classification: CLEAR

Path: same
Lines: 851–861
Result:
outcome=CARGO_SUCCEEDED_ARTIFACT_MISSING
cargo_exit_code=0
container exit=42
Finding 17.6 — Static-inspection failure preserves artifact-present outcome but exits nonzero

Classification: CLEAR

Path: same
Lines: 906–914, 984–1002
Result:
outcome=CARGO_SUCCEEDED_ARTIFACT_PRESENT
cargo_exit_code=0
status=FAILED
container exit=43

This prevents static-inspection failure from being presented as a completed successful run.

Finding 17.7 — Successful artifact-present path exits zero

Classification: CLEAR

Path: same
Lines: 984–1002
Zero occurs only after:
Cargo zero;
artifact present;
every required static command succeeds.
Finding 17.8 — Unexpected infrastructure finalization does not finalize every mandatory file

Classification: BLOCKED

Path: same
Functions: init_evidence, fail_infrastructure
Lines: 300–416, 440–470
init_evidence creates NOT_REACHED placeholders for multiple files. The generic fail_infrastructure handler rewrites:
outcome files;
clean-target proof;
artifact/static evidence.
It does not systematically replace every remaining mandatory NOT_REACHED file with a final infrastructure-failure record.
Depending on the stage, files such as BUILD_COMMAND.txt, BUILD_ENVIRONMENT.txt, or bootstrap-related evidence can remain in placeholder state.
Therefore the requested confirmation that every container failure path finalizes every mandatory automated file is not established.
18. Host/container outcome consistency
Finding 18.1 — Host accepts only one explicit allowed container outcome

Classification: CLEAR

Path: scripts/run_witness_narrow_build.sh
Function: parse_container_outcome
Lines: 1518–1553
The host requires:
a nonempty BUILD_EXIT_CODE.txt;
exactly one outcome= line;
a value from the allowed outcome list.
Finding 18.2 — Missing, duplicate, or invalid outcome becomes infrastructure failure

Classification: CLEAR

Path: same
Lines: 1522–1547, 1592–1625
Failure conditions include:
docker_run_launch_failure_exit_125
build_exit_code_file_missing_or_empty
outcome_field_missing
outcome_field_duplicated
outcome_field_invalid_value_...

The host rewrites the critical outcome files as:

outcome=INFRASTRUCTURE_FAILURE
failure_stage=invalid_or_missing_container_outcome

and exits through abort 10.

Finding 18.3 — Host does not reconstruct an ordinary outcome

Classification: CLEAR

Path: same
Comments and branch
Lines: 1505–1510, 1595–1629
The script explicitly refuses to derive an ordinary result from:
raw Docker exit;
artifact presence;
cargo_started.
Finding 18.4 — Valid container outcome is preserved in host-owned Docker evidence

Classification: CLEAR

Path: same
Functions: write_docker_exit_code_authoritative, successful parse branch
Lines: 964–977, 1626–1632
Finding 18.5 — Valid container outcome is preserved when host patches timing

Classification: CLEAR

Path: same
Function: patch_build_timing_docker_wallclock
Lines: 1555–1590
The host rewrites the timing file with:
outcome=${OUTCOME}
failure_stage=${FAILURE_STAGE}

while preserving container Cargo timing and Cargo exit fields.

Finding 18.6 — Outcome is identical across the three principal files on recognized paths

Classification: CLEAR
For a valid parsed outcome:

BUILD_EXIT_CODE.txt retains the container outcome;
BUILD_TIMING.txt is rewritten with that outcome;
DOCKER_EXIT_CODE.txt is written with that outcome.
For an invalid or missing outcome, all three are rewritten as INFRASTRUCTURE_FAILURE.
Finding 18.7 — Host validates only the outcome field before accepting authority

Classification: CLEAR WITH LIMITATIONS

Path: host script
Lines: 1531–1552
The host does not validate the complete container-owned tuple before continuing:
cargo_started;
build_status;
cargo_exit_code;
status;
failure_stage;
BUILD_TIMING consistency.
The later validator checks much of this, but the host does not run that validator automatically.
Finding 18.8 — Host can return zero before evidence is validator-confirmed

Classification: BLOCKED

Path: host script
Final exit selection
Lines: 1774–1800
The final host exit is:
DOCKER_EXIT

unless post-build integrity fails.
It is not conditioned on:

schema validation;
complete cross-file outcome validation;
final manifest validation.
Under the intended fixed container writer, ordinary success fields should be consistent. Nevertheless, the host alone does not prove that malformed but outcome-bearing evidence cannot accompany a zero exit.
Finding 18.9 — Invalid-outcome abort does not run the comprehensive post-Docker finalizer

Classification: BLOCKED

Path: same
Lines: 1595–1625
The invalid-outcome branch rewrites three critical files and calls abort directly.
It does not invoke finalize_post_docker_unexpected_failure, does not run the post-build source/lock gate, and does not systematically finalize every remaining mandatory file.
19. Failure-path matrix

The matrix below records statically derived behavior. “Mandatory evidence finalized” means every required automated file is conclusively finalized, not merely present as a placeholder.

Path	Container/host outcome	Cargo started	Build status	Cargo exit	Docker/host exit	Failure stage	Artifact/static applicability	Mandatory evidence finalized	False success
A. Image pull failure	INFRASTRUCTURE_FAILURE	NO	Infrastructure failure	N/A	pull exit	image_pull	not applicable	Yes, through pre-Docker finalizer, subject to generic-schema limitations	No
B. Image inspect command failure	INFRASTRUCTURE_FAILURE	NO	Infrastructure failure	N/A	8	image_identity_enforcement	not applicable	Yes, same limitation	No
C. Missing image ID	INFRASTRUCTURE_FAILURE	NO	Infrastructure failure	N/A	8	image_identity_enforcement	not applicable	Yes, same limitation	No
D. Digest mismatch	INFRASTRUCTURE_FAILURE	NO	Infrastructure failure	N/A	8	image_identity_enforcement	not applicable	Yes, same limitation	No
E. OS mismatch	INFRASTRUCTURE_FAILURE	NO	Infrastructure failure	N/A	8	generic image platform stage	not applicable	Yes, same limitation	No
F. Architecture mismatch	same as E	NO	Infrastructure failure	N/A	8	generic image platform stage	not applicable	Yes, same limitation	No
G. Apt failure	BUILD_NOT_STARTED	NO	BUILD_NOT_STARTED	N/A	normally 1	apt_get_update or apt_get_install	not applicable	Not proven for every mandatory file	No ordinary success
H. Rust version mismatch	BUILD_NOT_STARTED	NO	BUILD_NOT_STARTED	N/A	normally 1	rustc_version_mismatch	not applicable	Not proven for every mandatory file	No
I. Cargo version mismatch	BUILD_NOT_STARTED	NO	BUILD_NOT_STARTED	N/A	normally 1	cargo_version_mismatch	not applicable	Not proven for every mandatory file	No
J. DotSlash install failure	BUILD_NOT_STARTED	NO	BUILD_NOT_STARTED	N/A	normally 1	dotslash_install	not applicable	Not proven for every mandatory file	No
K. DotSlash version mismatch	BUILD_NOT_STARTED	NO	BUILD_NOT_STARTED	N/A	normally 1	dotslash_version_mismatch	not applicable	Not proven for every mandatory file	No
L. protoc failure	BUILD_NOT_STARTED	NO	BUILD_NOT_STARTED	N/A	normally 1	descriptor/probe stage	not applicable	Not proven for every mandatory file	No
M. Pre-bootstrap target nonempty	BUILD_NOT_STARTED	NO	BUILD_NOT_STARTED	N/A	normally 1	pre_bootstrap_empty_target	not applicable	Not proven for every mandatory file	No
N. Immediate pre-Cargo target nonempty	BUILD_NOT_STARTED	NO	BUILD_NOT_STARTED	N/A	normally 1	pre_cargo_empty_target	not applicable	Most files populated, but universal finalization not proven	No
O. Unexpected pre-Cargo infrastructure failure	INFRASTRUCTURE_FAILURE	generally NO	Infrastructure failure	N/A	triggering exit	current stage	not applicable	No	No ordinary success, but evidence may remain incomplete
P. Cargo nonzero	CARGO_FAILED	YES	FAILED	direct nonzero	same direct nonzero	cargo_build	artifact not applicable	Yes for ordinary path	No
Q. Cargo zero, artifact missing	CARGO_SUCCEEDED_ARTIFACT_MISSING	YES	COMPLETE	0	42	artifact_presence	artifact check applicable; static not applicable	Yes for ordinary path	No
R. Static command failure	CARGO_SUCCEEDED_ARTIFACT_PRESENT	YES	COMPLETE	0	43	first failing static command	artifact yes; static applicable but incomplete	Yes for ordinary path	No PASS
S. Artifact-present success	CARGO_SUCCEEDED_ARTIFACT_PRESENT	YES	COMPLETE	0	0, unless host post-build gate sets 9	none	both applicable and complete	Ordinary files finalized	Not fully provable because of writable source alias and no automatic validator gate
Failure-matrix conclusion

Classification: BLOCKED
False success is prevented for the explicitly coded ordinary failure branches. A global “false success is impossible” conclusion cannot be confirmed because:

the source clone is writable through /work/grok-build;
not every unexpected failure finalizes every mandatory file;
host success is not conditioned on validator success;
host validates only one authoritative field before accepting the container outcome.
20. Post-build integrity findings
Finding 20.1 — Source HEAD is checked after Docker

Classification: CLEAR

Path: host script
Lines: 1637–1644
Finding 20.2 — Source cleanliness is checked after Docker

Classification: CLEAR

Path: same
Lines: 1639, 1645–1654
Blank porcelain is explicitly normalized to:
source_clean_after=yes
Finding 20.3 — Cargo.lock is rehashed after Docker

Classification: CLEAR

Path: same
Lines: 1640, 1656–1660
Finding 20.4 — Both before/after equality and canonical expected hash are required

Classification: CLEAR
The host computes:

cargo_lock_unchanged=yes
cargo_lock_post_matches_expected=yes

independently.

Finding 20.5 — Technical post-build gate requires all four requested fields

Classification: CLEAR

Path: same
Lines: 1690–1697
The gate fails unless:
source_head_unchanged=yes
source_clean_after=yes
cargo_lock_unchanged=yes
cargo_lock_post_matches_expected=yes
Finding 20.6 — Post-build gate failure changes final host exit to 9

Classification: CLEAR

Path: same
Lines: 1774–1778
Finding 20.7 — POST_BUILD_INTEGRITY status is always written OK

Classification: BLOCKED

Path: same
Writer
Lines: 1703–1725
The file records:
status=OK

even when:

post_build_integrity_ok=no

This is internally contradictory. The final host exit becomes 9, but the evidence file’s top-level status remains OK.

Finding 20.8 — Template omits generated load-bearing fields

Classification: BLOCKED

Generated fields include:
artifact_path
artifact_exists
docker_exit_code
full_integrity_gate_all_four_yes
full_integrity_gate_note
post_build_integrity_ok
Template: templates/POST_BUILD_INTEGRITY.txt
Lines: 13–27
The template does not include those generated fields.
The validator required-field set also omits them.
Finding 20.9 — Validator does not directly require all four technical gate fields to be yes

Classification: BLOCKED

Path: scripts/validate_witness_evidence.py
Functions: check_post_build_integrity, identity mismatch collection
Lines: 864–892, 1168–1179
It checks formatting and derives some mismatch reasons, but it does not directly require:
source_head_unchanged=yes
source_clean_after=yes
cargo_lock_unchanged=yes
cargo_lock_post_matches_expected=yes

as an explicit complete gate.
In particular, cargo_lock_post_matches_expected=no is not directly added to the identity-mismatch reasons in the shown logic.

Finding 20.10 — Writable source alias weakens the post-build guarantee

Classification: BLOCKED
The post-build gate is detective, not preventive. A process can access the source read-write through:

/work/grok-build

despite /src:ro.
A modification restored before the final Git/hash checks would not be detected.

21. Test and generator/schema alignment
Finding 21.1 — Container BUILD_EXIT_CODE keys are contract-tested

Classification: CLEAR

Path: scripts/tests/test_validate_witness_evidence.py
Test: test_container_generated_build_exit_code_keys_match_schema
Lines: 157–161
Finding 21.2 — Container BUILD_TIMING keys are contract-tested

Classification: CLEAR

Path: same
Test around lines 151–155
Finding 21.3 — Static-inspection writer keys are contract-tested

Classification: CLEAR

Path: same
Lines: 163–174
Finding 21.4 — Host POST_BUILD_INTEGRITY test checks missing required keys only

Classification: CLEAR WITH LIMITATIONS

Path: same
Lines: 190–194
The test verifies:
required - emitted == empty

It does not require exact equality and therefore does not detect extra generated fields missing from the template/validator contract.

Finding 21.5 — DOCKER_EXIT_CODE generator has an extra unvalidated field

Classification: CLEAR WITH LIMITATIONS

Host writer: outcome_source=container_BUILD_EXIT_CODE.txt_authoritative
Path: host script
Line: 976
Validator required fields: validate_witness_evidence.py:525–536
The extra field is not represented in the template or required schema.
Finding 21.6 — Outcome disagreement tests use synthetic fixtures

Classification: CLEAR WITH LIMITATIONS

Path: test file
Class: OutcomeConsistencyTests
Lines: 265–328
They verify the validator rejects:
Docker outcome disagreement;
timing disagreement;
missing/invalid/duplicate outcome.
They do not invoke the real host parser or real writers.
Finding 21.7 — Host outcome-authority test is source-text only

Classification: CLEAR WITH LIMITATIONS

Path: same
Test: test_host_preserves_container_outcome_authority
Lines: 688–694
It checks strings, not behavior.
Finding 21.8 — Actual generator contracts are only partly covered

Classification: BLOCKED
The tests do not behaviorally prove:

one valid container outcome is preserved;
malformed outcome becomes infrastructure failure;
all three outcome files remain identical after host rewriting;
all mandatory files finalize on every failure;
final host exit follows outcome and post-build policy;
POST_BUILD_INTEGRITY status reflects gate failure;
writable source alias is absent;
exact mount isolation holds.
Finding 21.9 — Validator permits conservative outcome inference

Classification: AMBIGUOUS

Path: validator
Function: determine_outcome
Lines: 928–954
The host requires an explicit valid outcome, but the validator can infer an outcome from cargo_started and build_status when it is missing or invalid.
This weakens alignment with the host’s stricter “exactly one authoritative outcome” rule.
Finding 21.10 — BUILD_EXIT_CODE, BUILD_TIMING, and Docker outcome equality is validator-enforced

Classification: CLEAR

Path: validator
Lines: 986–1009
Finding 21.11 — Complete tuple consistency is incomplete

Classification: CLEAR WITH LIMITATIONS
The validator checks BUILD_EXIT_CODE’s outcome-dependent Cargo fields, but BUILD_TIMING validation mainly checks outcome and timing presence. It does not fully compare:

Cargo started;
Cargo exit;
failure stage
between BUILD_EXIT_CODE and BUILD_TIMING.
22. Batch-2 blockers

The twelve Batch-1 blockers remain carried forward unchanged.
The following Batch-2 blockers were identified:

The same Grok Build source tree is mounted read-only at /src and read-write at /work/grok-build, bypassing preventive source immutability.
Unexpected container infrastructure failures do not systematically finalize every mandatory automated evidence file.
Invalid or missing container-outcome handling rewrites only critical outcome files and aborts without comprehensive mandatory-file finalization or post-build integrity capture.
Host success is not conditioned on validator success or complete cross-file schema validation.
The host accepts an outcome after validating only the single outcome field, not the full authoritative outcome tuple.
POST_BUILD_INTEGRITY.txt always records status=OK, including when its own technical gate is false.
Generated POST_BUILD_INTEGRITY fields, template fields, and validator-required fields are not fully aligned.
Validator logic does not explicitly require all four technical post-build conditions to be yes.
Behavioral tests do not prove real host/container outcome preservation, mandatory evidence finalization, mount isolation, or final exit behavior.
A global claim that false success is impossible cannot be supported while the writable source alias and non-validator-gated host success remain.
23. Batch-2 non-fatal limitations
RepoDigest comparison uses substring matching instead of an exact normalized member comparison.
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
The container and host duplicate expected constants and must remain synchronized.
Network mode is bridge, so dependency/bootstrap acquisition is not network-isolated.
Host outcome parsing defaults missing cargo_started to NO.
BUILD_TIMING tuple consistency is only partly validator-enforced.
Validator outcome inference is more permissive than host outcome authority.
Extra host-generated fields are not rejected merely because they are absent from templates.
Product/ldd prohibition is statically established, not behaviorally traced.
24. Exact corrections required
Correction 24.1 — Eliminate the writable source alias
Classification: Mandatory
Path: external_verifications/grok-build/witness-package/scripts/run_witness_narrow_build.sh
Function/stage: Docker invocation, lines 1477–1498
Precise change: Do not mount the entire ${WORK_ROOT} read-write when ${SRC_DIR} is beneath it.
Preferred design:
place the source clone outside every read-write container mount; or

mount only narrowly required writable directories:

${CARGO_HOME}:/work/cargo-home:rw
${CARGO_TARGET_DIR}:/work/cargo-target:rw
${BOOTSTRAP_CARGO_TARGET_DIR}:/work/bootstrap-cargo-target:rw
${DOTSLASH_CACHE}:/work/dotslash-cache:rw
${ISOLATED_HOME}:/work/home:rw
${BOOTSTRAP_DIR}:/work/bootstrap:rw
${EVIDENCE_DIR}:/evidence:rw
${SRC_DIR}:/src:ro
do not expose ${SRC_DIR} through any second mount.
Related paths: container_narrow_build.sh, BUILD_ENVIRONMENT.txt template, validator mount checks, contract tests.
Why it matters: /src:ro must be preventive, not merely descriptive.
Correction 24.2 — Finalize every mandatory file on every container failure
Classification: Mandatory
Path: scripts/container_narrow_build.sh
Functions: fail_build_not_started, fail_infrastructure
Precise change: Add one common finalizer that iterates all mandatory automated files and replaces any empty or NOT_REACHED file with a schema-valid outcome-specific record before exiting.
Why it matters: A failure package must be complete and truthful, not a mixture of final records and placeholders.
Correction 24.3 — Use comprehensive post-Docker invalid-outcome finalization
Classification: Mandatory
Path: scripts/run_witness_narrow_build.sh
Function: invalid branch after parse_container_outcome
Lines: 1595–1625
Precise change: Replace direct three-file rewrite plus abort with a dedicated finalizer that:
records INFRASTRUCTURE_FAILURE;
captures post-Docker HEAD, clean state, and lock hash when possible;
finalizes all mandatory files;
preserves parse-error details;
exits nonzero.
Why it matters: Missing outcome authority must not leave partially finalized evidence.
Correction 24.4 — Validate the full authoritative outcome tuple on the host
Classification: Mandatory
Path: host script
Function: parse_container_outcome
Precise change: Require exactly one valid value for:
status;
outcome;
cargo_started;
build_status;
cargo_exit_code;
failure_stage.
Cross-check them against an outcome rule table before accepting the container result.
Also validate BUILD_TIMING’s outcome, Cargo-started value, Cargo exit, and failure stage before patching it.
Why it matters: A single valid outcome= line is not sufficient proof of a coherent authoritative result.
Correction 24.5 — Gate zero host exit on structural validation
Classification: Mandatory
Path: host script, final exit section
Function: final host exit selection
Lines: 1774–1800
Precise change: Before a zero exit, run an internal structural validation step or an equivalent embedded contract checker over automated evidence. Capture validator output outside the evidence directory if the full validator is used.
A zero host exit must require:
valid authoritative tuple;
cross-file outcome consistency;
mandatory files finalized;
post-build technical gate true.
Why it matters: Docker zero plus source integrity alone does not prove evidence consistency.
Correction 24.6 — Make POST_BUILD_INTEGRITY status truthful
Classification: Mandatory
Path: host script
Writer: POST_BUILD_INTEGRITY.txt
Lines: 1703–1725

Precise change:

status=OK

only when POST_BUILD_INTEGRITY_OK=yes; otherwise:

status=FAILED
Why it matters: Top-level status currently contradicts the recorded gate.
Correction 24.7 — Align POST_BUILD_INTEGRITY generator, template, and validator
Classification: Mandatory
Paths:
host script;
templates/POST_BUILD_INTEGRITY.txt;
scripts/validate_witness_evidence.py;
contract tests.

Precise change: Define one exact field set. Either add generated fields to the normative schema or remove nonnormative fields.
At minimum validate:

source_head_unchanged
source_clean_after
cargo_lock_unchanged
cargo_lock_post_matches_expected
post_build_integrity_ok
failure_stage
Why it matters: Current tests prove only that required keys are not missing, not that the contracts are identical.
Correction 24.8 — Require the four-field technical post-build gate
Classification: Mandatory
Path: validator
Function: check_post_build_integrity

Precise change: For every post-Docker ordinary outcome, reject unless:

source_head_unchanged=yes
source_clean_after=yes
cargo_lock_unchanged=yes
cargo_lock_post_matches_expected=yes

Require:

post_build_integrity_ok=yes

for any PASS-eligible evidence.

Why it matters: Formatting checks alone do not enforce the stated integrity contract.
Correction 24.9 — Remove conservative validator outcome inference
Classification: Mandatory
Path: validator
Function: determine_outcome
Lines: 928–954
Precise change: Require exactly one explicit valid outcome in BUILD_EXIT_CODE.txt. Do not infer it from secondary fields.
Why it matters: The validator should match the host’s authority rule.
Correction 24.10 — Add behavioral generator and failure-matrix tests
Classification: Mandatory
Path: scripts/tests/
Tests required:
A–S failure paths;
actual container writer output;
actual host outcome parsing and timing patching;
missing/duplicate/invalid outcome;
tuple mismatch;
mandatory-file finalization;
post-build gate failure;
Docker zero with malformed evidence;
writable source alias absence;
exact mount list;
product and ldd prohibition checks.
Why it matters: Current contract tests mostly parse source text or synthetic fixtures.
Correction 24.11 — Make RepoDigest matching exact
Classification: Hardening
Path: host image-identity block
Precise change: Parse RepoDigests and require an exact array member matching the expected repository and digest.
Why it matters: Avoids false substring matches.
Correction 24.12 — Preserve image-inspect diagnostics
Classification: Hardening
Path: host image-inspect stage
Precise change: Capture stdout, stderr, and exit code for each inspect operation in auxiliary evidence.
Why it matters: Improves independent diagnosis.
Correction 24.13 — Capture bootstrap logs in evidence or hash them
Classification: Hardening
Paths: container script, package manifest, closed inventory.
Precise change: Either submit apt/DotSlash logs as named auxiliary evidence or record their hashes and exact storage paths.
Why it matters: Current summary fields do not preserve all bootstrap diagnostics.
Correction 24.14 — Strengthen tool provenance
Classification: Hardening
Paths: container script and templates.
Precise change: Record full rustc -Vv, full cargo -Vv where available, and an explicitly accepted protoc identity/version policy.
Why it matters: x.y.z alone is weaker provenance.
Correction 24.15 — Avoid bash -c for the canonical Cargo command
Classification: Hardening
Path: container script

Precise change: Execute the fixed argument vector directly:

cargo build -p xai-grok-pager-bin --locked

while separately recording the canonical display string.

Why it matters: Removes unnecessary shell interpretation.
No final package-readiness verdict is issued. All twelve Batch-1 blockers remain carried forward in addition to the Batch-2 blockers above.
RC4 BATCH 2 COMPLETE — NO FINAL READINESS VERDICT YET
No Independent Witness reproduction occurred.
No Independent Witness PASS is claimed.
C-014 remains NOT_STARTED.
Do not continue to Batch 3 until instructed.