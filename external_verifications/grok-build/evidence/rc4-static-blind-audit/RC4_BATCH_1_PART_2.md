RC4 BATCH 1 — PART 2 OF 4
Part-2 scope

This part statically inspected the host orchestrator and directly related policy/test material for:

canonical constants and override handling;
noncanonical-run recording and verdict limits;
WITNESS_ID and WORK_ROOT safety;
managed-child deletion behavior;
fresh Weaver Forge and Grok Build acquisition;
annotated tag resolution;
detached-state, HEAD, cleanliness, and Cargo.lock enforcement;
work/cache/target/evidence isolation;
host-side safety and contract-test coverage.
No script, validator, test, Docker command, build tool, or product was executed.
1. Canonical fixed-value enforcement
Finding 1.1 — Canonical values are immutable shell constants

Classification: CLEAR

Path: external_verifications/grok-build/witness-package/scripts/run_witness_narrow_build.sh
Constants: PACKAGE_VERSION, CANONICAL_*
Lines: 34–51
The orchestrator declares the package and build identities using readonly, including:
PACKAGE_VERSION=1.0.0-rc4
CANONICAL_WEAVER_FORGE_TAG=grok-build-witness-v1.0.0-rc4
CANONICAL_GROK_BUILD_COMMIT=98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce
CANONICAL_RUST_IMAGE=docker.io/library/rust@sha256:6ca5ad23231207874325a751b9df584d51cd42c066c74c6963c264e3233c3e8e
CANONICAL_CARGO_LOCK_SHA256=1512bb4fef0c1166c6a15a3398da9593903be1759b759ce78d9958913e61b421
CANONICAL_BUILD_CMD=cargo build -p xai-grok-pager-bin --locked

Environment variables populate separate EFFECTIVE_* variables and do not mutate the canonical constants.

Finding 1.2 — Rust-image and digest constants have an internal consistency check

Classification: CLEAR

Path: same
Check: canonical image digest self-check
Lines: 53–58
The script exits before argument processing if the pinned digest is not embedded verbatim in the canonical image reference.
Finding 1.3 — All documented overridable fields pass through one identity gate

Classification: CLEAR

Path: same
Functions: check_identity_override, apply_identity_gate
Lines: 567–599
The gate covers:
Weaver Forge URL;
Weaver Forge tag;
Grok Build URL;
Grok Build commit;
Rust image;
expected Cargo.lock SHA-256;
build command;
expected Rust version;
expected DotSlash version.
Finding 1.4 — Identity gate runs before Witness-ID, WORK_ROOT, directory setup, cloning, and Docker stages

Classification: CLEAR

Path: same
Stage call: STEP 1: identity gate
Lines: 822–824
A mismatched environment value cannot silently flow into clone or build stages.
2. Silent override rejection
Finding 2.1 — Differing environment overrides abort without the explicit flag

Classification: CLEAR

Path: scripts/run_witness_narrow_build.sh
Function: check_identity_override
Lines: 567–582
When an effective value differs from its canonical counterpart and:
--noncanonical-deviation

was not supplied, the script exits with code 2.

Finding 2.2 — Merely defining an environment variable to its canonical value does not create a deviation

Classification: CLEAR

Path: same
Lines: 569–570
The gate compares values rather than variable presence. An override equal to the canonical value is accepted as canonical.
Finding 2.3 — The command-line help accurately describes the override rule

Classification: CLEAR

Path: same
Function: usage
Lines: 525–527, 552–558
It explicitly warns that environment overrides alone cannot silently change identity.
3. Explicit noncanonical-deviation mode
Finding 3.1 — Noncanonical mode requires an explicit command-line option

Classification: CLEAR

Path: same
Argument parser
Lines: 786–820
Only:
--noncanonical-deviation

sets:

NONCANONICAL_DEVIATION_ACCEPTED=1
Finding 3.2 — Every accepted mismatch records the changed field and both values

Classification: CLEAR

Path: same
Function: check_identity_override
Lines: 579–581
The script records:
field name;
canonical value;
effective value.
Finding 3.3 — The explicit flag alone does not make a canonical run noncanonical

Classification: CLEAR
NONCANONICAL_RUN is set only when a value actually differs. Supplying the flag while retaining every canonical value does not fabricate a deviation.

Finding 3.4 — The flag does not bypass tag-to-HEAD integrity

Classification: CLEAR

Path: same
Help text: lines 557–558
Actual checks: lines 1087–1209
Even in noncanonical mode, the effective package tag must:
resolve;
check out detached;
match HEAD;
produce a clean clone.
4. canonical_run=NO behavior
Finding 4.1 — Noncanonical state is recorded in host metadata

Classification: CLEAR

Path: same
HOST_RUN_METADATA.txt generator
Lines: 883–927
It writes:
canonical_run=NO
verdict_ceiling=<computed ceiling>

for a changed effective identity.

Finding 4.2 — Noncanonical state is recorded in DEVIATIONS.txt

Classification: CLEAR

Path: same
Lines: 929–955
It writes:
deviation_state=PRESENT
canonical_run=NO
noncanonical_deviation_flag_present=yes
changed_identity_field_count=<n>

plus the changed fields.

Finding 4.3 — Package identity evidence records the same state

Classification: CLEAR

Path: same
WEAVER_FORGE_PACKAGE_IDENTITY.txt generator
Lines: 1153–1173
It records:
canonical_run=no
noncanonical_disclosure=<details>
Finding 4.4 — Capitalization differs among evidence files

Classification: CLEAR WITH LIMITATIONS

HOST_RUN_METADATA.txt and DEVIATIONS.txt: YES|NO
WEAVER_FORGE_PACKAGE_IDENTITY.txt: yes|no
The meaning is clear, but the same conceptual field does not use one exact value vocabulary across all generated files.
5. PASS prohibition for noncanonical runs
Finding 5.1 — Every accepted override lowers the machine ceiling below PASS

Classification: CLEAR

Path: same
Function: compute_verdict_ceiling
Lines: 253–278
A noncanonical run begins with:
VERDICT_CEILING=PARTIAL

and selected canonical-identity changes make it:

VERDICT_CEILING=FAIL
Finding 5.2 — Generated deviation evidence explicitly prohibits PASS

Classification: CLEAR

Path: same
Line: 949
The generated text says:
Witness proposed verdict PASS is PREVENTED for this run.
Finding 5.3 — Normative classification independently prohibits noncanonical PASS

Classification: CLEAR

Path: external_verifications/grok-build/witness-package/WITNESS_CLASSIFICATION.md
Severity table and precedence
Lines: 29–33, 60–65, 71–72
A run with any accepted deviation cannot receive PASS.
Finding 5.4 — Machine-ceiling scope is narrower than the complete classification policy

Classification: CLEAR WITH LIMITATIONS

Path: scripts/run_witness_narrow_build.sh
Comments and function: lines 242–251
The script says its ceiling is advisory for identity overrides only and that the Witness must apply stricter classification rules for product execution, outcome, and other conditions.
This is disclosed, but it leaves some final classification responsibility outside the orchestrator.
6. Weaver Forge URL mismatch severity
Finding 6.1 — Weaver Forge URL is included in the material identity list

Classification: CLEAR

Path: same
Function: compute_verdict_ceiling
Lines: 253–277
WEAVER_FORGE_URL is listed among fields that force:
VERDICT_CEILING=FAIL
Finding 6.2 — URL mismatch is checked first and documented as FAIL-level

Classification: CLEAR

Path: same
Function: apply_identity_gate
Lines: 584–588
The implementation comment explicitly identifies the rc3 defect being corrected.
Finding 6.3 — Policy agrees with the implementation

Classification: CLEAR

Path: WITNESS_CLASSIFICATION.md
Clarification row: Weaver Forge URL mismatch
Line: 72
The policy states that even a disclosed mismatch is a material FAIL.
Finding 6.4 — Expected Rust and DotSlash version overrides are not in the FAIL identity list

Classification: CLEAR WITH LIMITATIONS

Path: scripts/run_witness_narrow_build.sh
Lines: 253–278, 595–596
Overrides to:
EXPECTED_RUSTC_VERSION
EXPECTED_DOTSLASH_VERSION

require the explicit noncanonical flag, but the ceiling function does not include them in its FAIL list. Such changes receive PARTIAL unless another rule is applied.
This is internally consistent with the policy’s narrower enumerated canonical-identity list, but these versions are still presented as canonical fixed values and can materially change the actual toolchain accepted by the run.

7. WITNESS_ID validation
Finding 7.1 — Exact documented regex is implemented

Classification: CLEAR

Path: scripts/run_witness_narrow_build.sh
Function: validate_witness_id
Lines: 604–612
Exact regex:
^[a-z0-9][a-z0-9._-]{0,63}$
Finding 7.2 — Additional defensive checks are present

Classification: CLEAR

Lines: 613–627
The script independently rejects:
/ and \;
..;
whitespace;
control characters;
leading dash.
Some are already impossible under the regex, but the redundancy is conservative.
Finding 7.3 — Validation occurs before path construction

Classification: CLEAR

Validation: lines 826–828
RUN_ID and paths: lines 845–857
Unsafe Witness input cannot reach the evidence path layout.
Finding 7.4 — Static test checks only selected rejection strings, not the exact regex

Classification: CLEAR WITH LIMITATIONS

Path: scripts/tests/test_validate_witness_evidence.py
Test: HostSafetyStaticTests.test_witness_id_validation_present
Lines: 657–662
The test confirms the function and several error messages, but it does not assert the exact regex or test accepted/rejected IDs behaviorally.
8. WORK_ROOT authorization and dangerous-root rejection
Finding 8.1 — WORK_ROOT is mandatory and absolute

Classification: CLEAR

Path: host script
Function: validate_work_root
Lines: 666–673
Empty and relative paths abort.
Finding 8.2 — Existing symlink components are resolved before safety decisions

Classification: CLEAR

Functions: resolve_path_m, validate_work_root
Lines: 648–679
realpath -m is preferred. The fallback resolves the nearest existing ancestor before appending a nonexisting suffix.
Finding 8.3 — Filesystem root is rejected

Classification: CLEAR

Lines: 681–683
Finding 8.4 — Home directories are rejected

Classification: CLEAR

Lines: 685–693
It rejects:
current $HOME;
/home/<user>;
/root.
Finding 8.5 — System prefixes are rejected

Classification: CLEAR

Constants: SYSTEM_PREFIXES
Lines: 133–136
Functions: is_system_prefix, validate_work_root
Lines: 634–642, 700–702
The root itself and descendants of listed system areas are prohibited.
Finding 8.6 — WSL drive roots are rejected

Classification: CLEAR

Function: is_wsl_drive_root
Lines: 644–646
Enforcement: 696–698
Exact form:
/mnt/<single drive letter>

is rejected.

Finding 8.7 — Nonempty WORK_ROOT requires two levels of authorization

Classification: CLEAR

Function: confirm_work_root_reset_if_needed
Lines: 733–781
The caller must first supply:
--allow-nonempty-work-root

and then either:

type the exact resolved root interactively; or
supply --force-work-root-reset.
Finding 8.8 — Noninteractive sessions cannot silently approve reset

Classification: CLEAR

Lines: 767–769
Without the explicit force flag, a noninteractive nonempty-root run aborts.
Finding 8.9 — Reset disclosure lists exact managed deletion targets

Classification: CLEAR

Lines: 741–749
The script displays the root, resolved root, nonempty state, and each managed target before authorization.
9. Repository ancestor/descendant protections
Finding 9.1 — The package repository itself is prohibited

Classification: CLEAR

Path: host script
Lines: 704–708
Finding 9.2 — An ancestor of the package repository is prohibited

Classification: CLEAR

Lines: 709–711
This prevents selecting a broad parent whose managed descendants could overlap the repository.
Finding 9.3 — A path inside the package repository is prohibited

Classification: CLEAR

Lines: 712–714
Finding 9.4 — Tests check only textual presence of the guards

Classification: CLEAR WITH LIMITATIONS

Path: scripts/tests/test_validate_witness_evidence.py
Test: test_work_root_guards_present
Lines: 644–655
No behavioral test feeds:
root;
home;
WSL root;
repository ancestor;
repository descendant;
symlink-resolved bypass attempts
into the actual shell function.
10. Managed-child reset and symlink policy
Finding 10.1 — Only deterministic managed children are reset

Classification: CLEAR

Path: host script
Function: work_root_managed_targets
Lines: 719–731
The script does not recursively erase the entire WORK_ROOT. It targets:
Weaver Forge clone;
Grok Build clone;
Cargo homes/targets;
DotSlash cache;
isolated home;
bootstrap directory.
Finding 10.2 — A symlinked managed child is unlinked rather than followed

Classification: CLEAR

Function: safe_reset_managed_path
Lines: 219–231
Logic:
if symlink → rm -f symlink
else if existing → rm -rf path
Finding 10.3 — Both repository clone destinations use the symlink-safe helper

Classification: CLEAR

Weaver Forge: lines 1080–1082
Grok Build: lines 1222–1224
Finding 10.4 — Cache, target, home, and bootstrap destinations use the same helper

Classification: CLEAR

Lines: 1306–1310
Finding 10.5 — Static test confirms implementation strings only

Classification: CLEAR WITH LIMITATIONS

Path: test file
Test: test_managed_child_symlink_policy_present
Lines: 663–667
The test does not construct an actual symlink to an external directory and prove that the target remains untouched.
11. Fresh Weaver Forge clone
Finding 11.1 — The managed package clone path is reset before acquisition

Classification: CLEAR

Path: host script
Lines: 1078–1083
Finding 11.2 — A fresh clone and tag fetch are performed

Classification: CLEAR

Lines: 1083–1085
Commands:
git clone <effective Weaver Forge URL> <WORK_ROOT>/weaver-forge
git -C <clone> fetch --tags origin
Finding 11.3 — The package used for execution comes from the new clone

Classification: CLEAR

Container script path: lines 1211–1215
The later container helper is loaded from the resolved fresh clone, not from the initially attached audit archive.
12. Annotated rc4 tag resolution in the script
Finding 12.1 — Exact tag commit dereference is used

Classification: CLEAR

Path: host script
Lines: 1087, 1102
Exact expression:
refs/tags/${EFFECTIVE_WEAVER_FORGE_TAG}^{commit}

For a canonical run, the effective tag is exactly:

grok-build-witness-v1.0.0-rc4
Finding 12.2 — Missing tag resolution is fatal before Docker

Classification: CLEAR

Lines: 1087–1101
The failure is finalized as a pre-Docker infrastructure failure.
Finding 12.3 — Resolved identity must be full lowercase 40-hex

Classification: CLEAR

Lines: 1102–1113
Finding 12.4 — “Annotated” is an authority description rather than a direct object-type assertion

Classification: CLEAR WITH LIMITATIONS
The script dereferences:

refs/tags/<tag>^{commit}

which works for both annotated and lightweight tags.
It does not separately run:

git cat-file -t refs/tags/<tag>

and require the raw ref object type to be tag.
Therefore it proves tag-to-commit resolution, but does not directly prove that the tag object itself is annotated.
The verified transfer manifest records tag_type=annotated, but the host orchestrator does not independently enforce that property.

13. Detached package checkout and direct probe
Finding 13.1 — Checkout explicitly uses detached mode

Classification: CLEAR

Path: host script
Line: 1114
Finding 13.2 — Detached state is directly probed

Classification: CLEAR

Lines: 1126–1131
The script requires:
git symbolic-ref -q HEAD

to fail.

Finding 13.3 — A non-detached package clone aborts before Docker

Classification: CLEAR

Lines: 1194–1197
Finding 13.4 — Host-side tests do not explicitly assert the package detached probe

Classification: MISSING

Path: test file
HostSafetyStaticTests
Lines: 669–686
There is a dedicated test for the Grok Build detached probe, but no corresponding isolated assertion for:
git -C "${WF_DIR}" symbolic-ref -q HEAD

The package tag/head mismatch finalizer is tested textually, but direct package detached-state probe coverage is not.

14. Package HEAD equality and clean-state enforcement
Finding 14.1 — Detached HEAD is compared directly to the resolved tag commit

Classification: CLEAR

Path: host script
Lines: 1116, 1121–1124, 1198–1201
Finding 14.2 — Package clone cleanliness is derived from git status --porcelain

Classification: CLEAR

Lines: 1117–1119
Finding 14.3 — Dirty package clone aborts before Docker

Classification: CLEAR

Lines: 1202–1205
Finding 14.4 — Evidence records resolved commit, HEAD, detached state, cleanliness, and authority

Classification: CLEAR

Lines: 1153–1173
15. Optional external expected-commit behavior
Finding 15.1 — It is optional and not a canonical constant

Classification: CLEAR

Path: host script
Lines: 74–78
Finding 15.2 — Supplied value must be full lowercase 40-hex

Classification: CLEAR

Lines: 1133–1145
Finding 15.3 — Supplied value must match both resolved tag commit and detached HEAD

Classification: CLEAR

Lines: 1146–1150, 1206–1209
Finding 15.4 — Absence does not weaken tag/HEAD enforcement

Classification: CLEAR
The ordinary tag resolution, detached probe, HEAD equality, and clean checks run independently of this optional value.

16. Fresh Grok Build clone
Finding 16.1 — Existing managed source destination is safely reset

Classification: CLEAR

Path: host script
Lines: 1220–1224
Finding 16.2 — Fresh clone uses the effective URL

Classification: CLEAR

Line: 1225
In canonical mode, this is the pinned canonical repository URL.
Finding 16.3 — No owner cache or source checkout is reused

Classification: CLEAR

Evidence generator: lines 1252–1268
It records:
fresh_clones=yes
owner_caches_used=no

The source path is newly reset and cloned.

17. Pinned Grok Build detached checkout
Finding 17.1 — Checkout explicitly targets the pinned full commit

Classification: CLEAR

Path: host script
Line: 1226
Canonical value:
98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce
Finding 17.2 — Checkout explicitly uses --detach

Classification: CLEAR

Line: 1226
18. Direct Grok Build detached-state probe
Finding 18.1 — Detached state is directly probed

Classification: CLEAR

Path: host script
Lines: 1233–1238
Finding 18.2 — Non-detached state aborts before Docker

Classification: CLEAR

Lines: 1270–1273
Finding 18.3 — A dedicated static test covers the probe

Classification: CLEAR WITH LIMITATIONS

Path: test file
Test: test_grok_detached_probe_present
Lines: 683–686
It checks for:
symbolic-ref;
evidence key;
failure finalizer.
It remains a source-text contract test rather than behavioral shell execution.
19. Grok Build HEAD and clean-state enforcement
Finding 19.1 — Observed HEAD is directly compared with the pinned commit

Classification: CLEAR

Path: host script
Lines: 1229, 1274–1277
Finding 19.2 — Cleanliness uses git status --porcelain

Classification: CLEAR

Line: 1230
Finding 19.3 — Dirty source aborts before Docker

Classification: CLEAR

Lines: 1278–1281
Finding 19.4 — Source identity evidence records all three controls

Classification: CLEAR

Lines: 1240–1250
It records:
expected commit;
observed commit;
detached state;
porcelain output;
observed and expected Cargo.lock hashes.
20. Direct Cargo.lock SHA-256 enforcement before Docker
Finding 20.1 — Hash is computed directly from the cloned source

Classification: CLEAR

Path: host script
Line: 1231
Finding 20.2 — Direct equality is evaluated before image pull or Docker run

Classification: CLEAR

Lines: 1283–1301
Finding 20.3 — Mismatch is fatal before Docker

Classification: CLEAR

Lines: 1298–1301
Finding 20.4 — The expected hash itself is overrideable in explicit noncanonical mode

Classification: CLEAR WITH LIMITATIONS
A different expected lock hash:

is rejected silently unless the flag is present;
with the flag, sets a FAIL ceiling because EXPECTED_CARGO_LOCK_SHA256 is a canonical identity field.
This prevents PASS but still permits the noncanonical procedure to continue far enough to generate a disclosed negative run.
21. Host/work/cache/target/evidence isolation
Finding 21.1 — Dedicated paths are defined under WORK_ROOT

Classification: CLEAR

Path: host script
Lines: 845–857
Distinct paths exist for:
Weaver Forge clone;
Grok Build clone;
Cargo home;
product target;
bootstrap Cargo target;
DotSlash cache;
isolated HOME;
bootstrap data;
per-run evidence.
Finding 21.2 — Product and bootstrap targets are distinct

Classification: CLEAR

Lines: 852–853
Finding 21.3 — Evidence is namespaced by validated Witness ID, UTC date, and short run ID

Classification: CLEAR

Lines: 845–857
Finding 21.4 — Existing evidence directory collision is not explicitly rejected

Classification: CLEAR WITH LIMITATIONS
RUN_ID uses a random six-hex suffix when OpenSSL is available, otherwise current HHMMSS.
The script uses:

mkdir -p "${WORK_ROOT}" "${EVIDENCE_DIR}"

rather than requiring the selected evidence directory not to exist.
A rare collision, or a precreated matching directory, could cause placeholder initialization to overwrite files in that run directory.

Finding 21.5 — WORK_ROOT itself is not recursively deleted

Classification: CLEAR
Only listed managed children are reset.
Unrelated top-level files remain untouched after authorization.

22. Docker-before-identity-check boundary
Finding 22.1 — docker pull and docker run occur after package, source, clean-state, and lock checks

Classification: CLEAR

Pre-Docker identity stages: lines 1075–1301
Image pull begins: around lines 1384–1402
docker run begins: around lines 1477–1481
The build container is not pulled or started until the required source identities and pre-Docker lock check pass.
Finding 22.2 — Docker CLI/daemon inspection occurs before those identity checks

Classification: BLOCKED

Path: host script
Function: record_host_environment
Lines: 1019–1027
Invocation: lines 1072–1073
Before the Weaver Forge clone, tag resolution, Grok Build checkout, source cleanliness, and Cargo.lock enforcement, the script executes:
docker version --format ...
docker context show

Therefore the requested condition:

no Docker execution occurs before all required identity checks pass

is not literally satisfied.
These commands do not run a container or pull an image, but they are Docker executions and may contact the daemon.

Finding 22.3 — The policy distinguishes build execution from environment discovery only implicitly

Classification: AMBIGUOUS
The runbook’s failure-ordering emphasis concerns image pull and docker run, while the host records Docker environment information earlier.
The package should state explicitly whether pre-identity Docker metadata queries are allowed, or move them after identity enforcement.

23. Host-side contract and safety test coverage
Finding 23.1 — RC4 adds a dedicated host static-contract test class

Classification: CLEAR

Path: scripts/tests/test_validate_witness_evidence.py
Class: HostSafetyStaticTests
Lines: 615–708
It checks textual presence of:
strict shell mode;
canonical constants;
image/digest self-check;
noncanonical override gate;
PASS prohibition;
Weaver URL FAIL handling;
WORK_ROOT guards;
Witness-ID checks;
symlink-safe reset;
tag/HEAD and clean failure finalizers;
Grok commit and lock finalizers;
Grok detached probe;
outcome authority;
no cached-image fallback;
image failure finalizers;
no embedded future rc4 commit.
Finding 23.2 — Tests are static source-string assertions, not orchestrator behavior tests

Classification: CLEAR WITH LIMITATIONS
The test class reads the shell script text:

cls.host = HOST_SCRIPT.read_text(...)

and checks assertIn/assertNotIn.
It does not invoke isolated shell functions or simulate command results.

Finding 23.3 — No behavioral test covers canonical override rejection

Classification: MISSING
The test confirms the fatal message exists but does not prove:

a mismatched override aborts without the flag;
the same mismatch proceeds only with the flag;
canonical_run=NO is actually written;
the correct ceiling is produced.
Finding 23.4 — No behavioral Witness-ID matrix exists

Classification: MISSING
There are no direct tests for:

shortest valid ID;
64-character valid ID;
65-character rejection;
uppercase rejection;
leading punctuation rejection;
traversal-like strings;
whitespace/control characters.
Finding 23.5 — No behavioral WORK_ROOT safety matrix exists

Classification: MISSING
No test executes the guard against:

/;
$HOME;
/home/user;
/root;
/mnt/c;
system-prefix descendants;
package repository;
repository ancestor;
repository descendant;
symlink-resolved aliases.
Finding 23.6 — No behavioral managed-child symlink test exists

Classification: MISSING
The code appears conservative, but the test does not prove an external symlink target survives reset.

Finding 23.7 — Package detached-state probe lacks a dedicated contract assertion

Classification: MISSING
The Grok Build probe is tested. The analogous Weaver Forge symbolic-ref probe is not isolated in the test suite.

Finding 23.8 — No explicit ordering test proves Docker commands remain after all identity gates

Classification: MISSING
The suite does not parse command order or ensure that:

package identity;
source identity;
lock validation
precede every Docker invocation.
This omission allowed the early docker version/docker context show calls to remain.
24. Consolidated Part-2 assessment
Confirmed controls
Canonical constants are immutable.
Silent value changes abort.
Explicit noncanonical mode is required for deviations.
Accepted deviations write canonical_run=NO.
Noncanonical PASS is prohibited.
Weaver Forge URL mismatch receives FAIL severity.
Exact safe Witness-ID regex is implemented.
Dangerous WORK_ROOT values are rejected.
Repository overlap and WSL drive-root protections exist.
Nonempty reset requires explicit authorization.
Managed-child symlinks are unlinked, not recursively followed.
Weaver Forge and Grok Build are freshly cloned.
Package tag-to-commit resolution is exact.
Both package and Grok Build checkouts are detached and directly probed.
Both HEAD identities and clean states are enforced.
Cargo.lock is directly hashed and compared before image pull/build container execution.
Work, cache, target, bootstrap, home, and evidence paths are separated.
Part-2 blockers carried forward
Current normative documents inside the fixed rc4 tag still describe rc4 as under preparation, pending commit/tag, or not yet published.
Change-log/status claims say tag-pending wording was removed, but contradictory current wording remains.
The fixed rc4 snapshot does not represent rc4 itself as an already-published immutable release.
Docker CLI/daemon commands (docker version and docker context show) execute before package-tag resolution, package/source identity enforcement, and pre-Docker Cargo.lock verification; therefore the strict “no Docker execution before all required identity checks pass” condition is not met.
Part-2 non-fatal limitations carried forward
Public discoverability is strong, but stale pre-publication wording creates uncertainty about whether rc4 is the intended fixed audit target.
rc4 immutability is defined prospectively rather than reflected as an already-published state.
The host proves tag-to-commit resolution but does not independently assert that the raw rc4 ref object type is an annotated tag rather than a lightweight tag.
canonical_run value capitalization differs across generated evidence.
Expected Rust and DotSlash version overrides require disclosure but do not receive the script’s identity-mismatch FAIL ceiling.
Final machine ceiling covers identity overrides only; complete classification still relies on the stricter normative policy.
Evidence run-directory collisions are not explicitly rejected.
Host safety tests are mainly static source-text assertions.
Exact Witness-ID behavior lacks a test matrix.
WORK_ROOT rejection and authorization behavior lacks a test matrix.
Managed-child symlink safety lacks a behavioral test.
Weaver Forge package detached-state probing lacks a dedicated test.
No test enforces ordering before every Docker CLI invocation.
No final package-readiness verdict is issued in this part.
RC4 BATCH 1 — PART 2 COMPLETE
Do not continue to Part 3 until instructed.