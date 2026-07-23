RC4 STATIC BLIND AUDIT — BATCH 2 OF 4
1. Batch-2 scope

This batch statically inspected the pinned-image acquisition, Docker invocation, in-container bootstrap/build flow, artifact inspection, outcome authority, post-build integrity, templates, validator rules, and related tests.
No Docker command, Witness script, validator, validator test, compiler, bootstrap tool, product, or artifact-analysis command was executed.
The twelve Batch-1 blockers remain carried forward unchanged and were not re-audited in detail.

2. Files inspected

At minimum, the following archive-relative files were inspected:

external_verifications/grok-build/witness-package/scripts/run_witness_narrow_build.sh
external_verifications/grok-build/witness-package/scripts/container_narrow_build.sh
external_verifications/grok-build/witness-package/scripts/validate_witness_evidence.py
external_verifications/grok-build/witness-package/scripts/tests/test_validate_witness_evidence.py
external_verifications/grok-build/witness-package/WITNESS_REQUIREMENTS.md
external_verifications/grok-build/witness-package/WITNESS_RUNBOOK.md
external_verifications/grok-build/witness-package/WITNESS_CLASSIFICATION.md
external_verifications/grok-build/witness-package/WITNESS_PACKAGE_MANIFEST.md
external_verifications/grok-build/witness-package/PACKAGE_READINESS_POLICY.md
external_verifications/grok-build/witness-package/templates/IMAGE_IDENTITY.txt
templates/BOOTSTRAP.txt
templates/CLEAN_TARGET_PROOF.txt
templates/BUILD_COMMAND.txt
templates/BUILD_ENVIRONMENT.txt
templates/BUILD_EXIT_CODE.txt
templates/DOCKER_EXIT_CODE.txt
templates/BUILD_TIMING.txt
templates/ARTIFACT_IDENTITY.txt
templates/STATIC_ARTIFACT_INSPECTION.txt
templates/POST_BUILD_INTEGRITY.txt
relevant fixture builders and committed golden fixtures.
3. Image acquisition findings
Finding 3.1 — Exact digest-pinned image pull is used

Classification: CLEAR

Path: scripts/run_witness_narrow_build.sh
Constant/command: CANONICAL_RUST_IMAGE, DOCKER_PULL_CMD
Lines: 46, 1382–1392
The host runs:
docker pull --platform linux/amd64 docker.io/library/rust@sha256:6ca5ad23231207874325a751b9df584d51cd42c066c74c6963c264e3233c3e8e

in canonical mode.

Finding 3.2 — Pull stdout and stderr are separately captured

Classification: CLEAR

Path: same
Lines: 1390–1394
Files:
IMAGE_PULL_STDOUT.txt
IMAGE_PULL_STDERR.txt
Finding 3.3 — Direct pull exit code is preserved

Classification: CLEAR

Path: same
Variable: IMAGE_PULL_EXIT
Lines: 1390–1397
The script temporarily disables set -e, captures $? immediately, and restores strict mode.
Finding 3.4 — Pull failure is fatal and stops before inspect/run

Classification: CLEAR

Path: same
Lines: 1396–1403
A failed pull writes failed image identity evidence and calls the pre-Docker infrastructure finalizer.
No image-inspection or docker run path follows.
Finding 3.5 — Cached-image fallback is explicitly prohibited

Classification: CLEAR

Path: same
Fields/message: cached_image_fallback_used=NO
Lines: 1370, 1400–1402
A locally cached image cannot substitute after a failed pull.
Finding 3.6 — Pull-log files are auxiliary, not mandatory schema files

Classification: CLEAR WITH LIMITATIONS

Path: host script
Auxiliary allow-list: approximately 106–118
Writer: 1391
They are captured and allow-listed, but validator semantics concentrate on IMAGE_IDENTITY.txt; the pull-log contents themselves are not deeply validated.
4. Image identity findings
Finding 4.1 — Image ID is directly inspected

Classification: CLEAR

Path: host script
Command: docker inspect --format '{{.Id}}'
Lines: 1410, 1415–1417
Finding 4.2 — RepoDigests are directly inspected

Classification: CLEAR

Path: same
Lines: 1411, 1418–1419
Finding 4.3 — Requested digest is compared against RepoDigests

Classification: CLEAR WITH LIMITATIONS

Path: same
Lines: 1385–1388, 1435–1438
The requested sha256:… is required to occur in the RepoDigests JSON.
This verifies digest presence but uses substring matching and does not require an exact normalized <repository>@<digest> array member.
Finding 4.4 — OS and architecture are directly enforced

Classification: CLEAR

Path: same
Lines: 1412–1423, 1440–1443
Required values:
linux
amd64
Finding 4.5 — status=OK requires every image sub-check

Classification: CLEAR

Path: same
Lines: 1445–1459
All must be true:
image ID available;
expected digest present;
platform linux/amd64.
Finding 4.6 — IMAGE_IDENTITY is failed on every enforced identity failure

Classification: CLEAR

Path: same
Function: write_image_identity_block
Lines: 1343–1379, 1396–1402, 1447–1464
Pull, missing-ID, digest, and platform failures produce:
status=FAILED
Finding 4.7 — Inspect stderr is discarded

Classification: CLEAR WITH LIMITATIONS

Path: same
Lines: 1416–1423
Every inspect command uses:
2>/dev/null

Exit codes and failed fields remain available, but diagnostic stderr is lost.

Finding 4.8 — Individual OS versus architecture failure is not distinguished

Classification: CLEAR WITH LIMITATIONS

Path: same
Lines: 1452–1458
Both are reported under:
failure_stage=image_inspect_platform

The observed fields reveal which value failed, but the failure stage is not precise.

Finding 4.9 — Image failure finalizes mandatory automated evidence

Classification: CLEAR WITH LIMITATIONS

Path: host script
Function: finalize_pre_docker_infrastructure_failure
Lines: 288–416
Every mandatory file still holding status=NOT_REACHED is replaced with failure evidence, and critical outcome files are rewritten.
However, generic fallback records do not always match each file’s normal full success schema. Validator acceptance depends on its infrastructure-failure placeholder exceptions.
5. Docker invocation and mounts
Finding 5.1 — Exact pinned image is used for docker run

Classification: CLEAR

Path: host script
Lines: 1477–1498
The effective digest-pinned image appears as the image argument after all flags.
Finding 5.2 — Platform and network are explicit

Classification: CLEAR

Path: same
Lines: 1477–1480
--platform linux/amd64
--network bridge
Finding 5.3 — Source is mounted read-only at /src

Classification: CLEAR WITH LIMITATIONS

Path: same
Line: 1480
-v "${SRC_DIR}:/src:ro"
Finding 5.4 — WORK_ROOT is mounted read-write and contains the source clone

Classification: BLOCKED

Path: host script
Paths: SRC_DIR="${WORK_ROOT}/grok-build"
Mounts: lines 1480–1482
The script simultaneously mounts:
${SRC_DIR}:/src:ro
${WORK_ROOT}:/work

Because ${SRC_DIR} is a descendant of ${WORK_ROOT}, the same source tree is available inside the container as:

/src                 read-only
/work/grok-build     read-write

The /src:ro protection is therefore bypassable through the /work mount alias.
Post-build Git checks may detect changes afterward, but they do not provide preventive source immutability.

Finding 5.5 — Evidence directory also has two writable aliases

Classification: CLEAR WITH LIMITATIONS

Path: host script
Lines: 1481–1482
The evidence directory is beneath WORK_ROOT and is mounted both through /work/... and directly as /evidence.
The container script uses /evidence, but dual writable aliases complicate isolation and provenance.
Finding 5.6 — Container helper script is read-only

Classification: CLEAR

Path: same
Line: 1483
Finding 5.7 — Container working directory is /src

Classification: CLEAR

Path: same
Line: 1496
Finding 5.8 — Network isolation is not used

Classification: CLEAR WITH LIMITATIONS

Path: same
Line: 1479
bridge networking is deliberate because apt and Cargo dependency acquisition may require network access.
This means the build is isolated by fresh directories and pins, not by network denial.
6. Container environment
Finding 6.1 — Core paths are explicitly supplied

Classification: CLEAR

Path: host script
Lines: 1484–1495
Environment includes:
isolated HOME;
isolated CARGO_HOME;
Grok target;
bootstrap target indirectly known by script;
DOTSLASH_CACHE;
explicit PATH;
expected commit, lock hash, build command, versions, and image.
Finding 6.2 — Cargo incremental compilation is disabled

Classification: CLEAR

Path: host and container scripts
Host line: 1487
Container lines: 543, 793–798
Finding 6.3 — Container script defaults duplicate host expectations

Classification: CLEAR WITH LIMITATIONS

Path: scripts/container_narrow_build.sh
Lines: 25–33
Defaults provide resilience, but correctness relies on host and container constants remaining synchronized.
Finding 6.4 — RUSTUP_HOME inherited from the image is not overridden

Classification: CLEAR WITH LIMITATIONS

Path: container script
Lines: 520–522
It is only recorded when present.
The script uses the image’s built-in Rust/Cargo installation rather than installing a fresh Rust toolchain.
7. Rust/Cargo toolchain findings
Finding 7.1 — Built-in image rustc is probed directly

Classification: CLEAR

Path: container script
Lines: 545–570
Probe failure or version mismatch results in BUILD_NOT_STARTED.
Finding 7.2 — Built-in image cargo is probed directly

Classification: CLEAR

Path: same
Lines: 572–595
Finding 7.3 — Exact versions are required

Classification: CLEAR

Expected values:
Rust: 1.92.0
Cargo: 1.92.0
Path: container script
Lines: 29–31, 557–595
Finding 7.4 — Version parsing uses the first semantic-version-looking token

Classification: CLEAR WITH LIMITATIONS

Path: same
Lines: 557, 582
The regex is straightforward but accepts only numeric x.y.z and discards full provenance such as commit hash/date.
Finding 7.5 — Probe failures are finalized as BUILD_NOT_STARTED

Classification: CLEAR

Function: fail_build_not_started
Lines: 420–438
Result:
cargo_started=NO
build_status=BUILD_NOT_STARTED
cargo_exit_code=NOT_APPLICABLE
8. Apt bootstrap findings
Finding 8.1 — Exact package set is documented

Classification: CLEAR

Path: container script
Lines: 615–627
Packages include build tools, file, and binutils.
Finding 8.2 — apt-get update and install failures are fatal

Classification: CLEAR

Path: same
Lines: 629–639
Both failures become BUILD_NOT_STARTED.
Finding 8.3 — Apt logs are captured outside evidence

Classification: CLEAR WITH LIMITATIONS

Path: same
Lines: 630, 636
Logs are placed under:
/work/bootstrap/

They are not part of the submitted evidence inventory unless manually copied or disclosed elsewhere.

Finding 8.4 — Apt package versions are unpinned

Classification: CLEAR WITH LIMITATIONS

Path: same
Lines: 641–651
The script explicitly records:
apt_versions_unpinned_limitation=yes

This permits temporal variation in native tools such as file, readelf, and objdump.

Finding 8.5 — dpkg-query is best-effort

Classification: CLEAR WITH LIMITATIONS

Path: same
Line: 650
Failure is masked with || true, so installed package-version inventory can be incomplete without aborting.
9. DotSlash findings
Finding 9.1 — DotSlash is installed at exact version 0.5.7 with --locked

Classification: CLEAR

Path: container script
Lines: 653–668
Finding 9.2 — DotSlash installation uses bootstrap target only

Classification: CLEAR

Path: same
Lines: 655–665
Finding 9.3 — Install failure is fatal

Classification: CLEAR

Lines: 666–668
Finding 9.4 — Version probe and validation are mandatory

Classification: CLEAR

Lines: 671–703
Probe failure and mismatch both produce BUILD_NOT_STARTED.
Finding 9.5 — DotSlash installation log remains outside submitted evidence

Classification: CLEAR WITH LIMITATIONS

Path: same
Line: 656
The full Cargo-install log is under /work/bootstrap, while BOOTSTRAP.txt records command and exit status.
10. Bootstrap/Grok target separation
Finding 10.1 — Dedicated targets exist

Classification: CLEAR

Path: container script
Lines: 41–44
/work/bootstrap-cargo-target
/work/cargo-target
Finding 10.2 — DotSlash uses only the bootstrap target

Classification: CLEAR

Lines: 655–665
Finding 10.3 — Grok Build target is restored before source/build operations

Classification: CLEAR

Lines: 753–754
Finding 10.4 — Whole WORK_ROOT mount weakens conceptual isolation

Classification: CLEAR WITH LIMITATIONS
Both targets and source are under one writable /work tree.
The scripts use distinct variables correctly, but container filesystem permissions do not prevent accidental cross-path writes.

11. protoc findings
Finding 11.1 — Descriptor presence is mandatory

Classification: CLEAR

Path: container script
Lines: 707–713
Finding 11.2 — CRLF is normalized to LF in a writable copy

Classification: CLEAR

Path: same
Lines: 715–720
The original source-mounted descriptor remains untouched.
Finding 11.3 — Original and normalized SHA-256 values are recorded

Classification: CLEAR

Lines: 718–729
Finding 11.4 — Protoc version probe is mandatory

Classification: CLEAR

Lines: 731–749
Nonzero exit causes BUILD_NOT_STARTED.
Finding 11.5 — An auxiliary protoc-version.raw file is created outside evidence

Classification: CLEAR

Path: same
Lines: 739–740
The script explicitly avoids generating the previously problematic:
BOOTSTRAP_PROTOC_VERSION.txt

under the evidence directory.

Finding 11.6 — Protoc output content is not semantically version-pinned

Classification: CLEAR WITH LIMITATIONS
The probe must execute successfully, but no exact protoc version is required.
The descriptor hash provides stronger identity than the displayed version string.

12. Clean-target proof findings
Finding 12.1 — Host pre-container target emptiness is checked

Classification: CLEAR

Path: host script
Lines: 1304–1336
A nonempty target prevents image pull and Docker run.
Finding 12.2 — Container pre-bootstrap target emptiness is checked

Classification: CLEAR

Path: container script
Lines: 524–539
Finding 12.3 — Immediate pre-Cargo target emptiness is rechecked

Classification: CLEAR

Path: same
Lines: 801–819
Finding 12.4 — Pre-bootstrap and pre-Cargo failures produce BUILD_NOT_STARTED

Classification: CLEAR
Both set:

cargo_started=NO
outcome=BUILD_NOT_STARTED
Finding 12.5 — The writable /work/grok-build source alias is outside clean-target counting

Classification: CLEAR WITH LIMITATIONS
Target emptiness is well checked, but it does not address writable source aliasing.

13. Cargo command/log/exit findings
Finding 13.1 — Exact canonical Cargo command is recorded and executed

Classification: CLEAR

Path: container script
Lines: 791–799, 821–830
cargo build -p xai-grok-pager-bin --locked
Finding 13.2 — Cargo stdout and stderr are separated

Classification: CLEAR

Path: same
Line: 829
Finding 13.3 — Direct Cargo exit is preserved

Classification: CLEAR

Path: same
Lines: 828–835
Finding 13.4 — Cargo nonzero exits with the same direct code

Classification: CLEAR

Lines: 841–848
The container does not replace the direct Cargo failure code.
Finding 13.5 — Cargo is executed through bash -c

Classification: CLEAR WITH LIMITATIONS

Line: 829
The command was host-gated as an exact canonical string, but bash -c remains a shell interpretation layer.
14. Artifact-presence findings
Finding 14.1 — Cargo zero does not alone imply build success

Classification: CLEAR

Path: container script
Lines: 851–861
Expected artifact:
/work/cargo-target/debug/xai-grok-pager
Finding 14.2 — Missing artifact after Cargo zero exits nonzero

Classification: CLEAR
Dedicated exit:

42

Outcome:

CARGO_SUCCEEDED_ARTIFACT_MISSING
Finding 14.3 — Artifact presence leads to static inspection

Classification: CLEAR

Lines: 863–884
Finding 14.4 — Artifact filename/path are fixed

Classification: CLEAR

Path: same
Lines: 49, 974–982
15. Static-inspection findings
Finding 15.1 — Required commands are directly captured

Classification: CLEAR

Path: container script
Lines: 868–884
Commands:
sha256sum
stat
file
readelf -h
readelf -n
readelf -d
objdump -f
Finding 15.2 — Each command has separate command/output/exit fields

Classification: CLEAR

Lines: 916–949
Finding 15.3 — Required inspection failure exits nonzero

Classification: CLEAR

Lines: 984–1002
Dedicated exit:
43
Finding 15.4 — Static-inspection failure preserves the build outcome

Classification: CLEAR
The outcome remains:

CARGO_SUCCEEDED_ARTIFACT_PRESENT

while:

status=FAILED
inspection_complete=no
Finding 15.5 — PASS is prohibited, but outcome remains artifact-present

Classification: CLEAR WITH LIMITATIONS

Container comments/logic: 11–15, 906–914, 985–999
Validator ceiling logic: approximately 1183–1208
This is a deliberate distinction between build outcome and evidence completeness.
Finding 15.6 — Artifact identity can contain unavailable values

Classification: CLEAR WITH LIMITATIONS
If sha256sum, stat, or readelf -n fails, ARTIFACT_IDENTITY.txt records:

UNAVAILABLE_COMMAND_FAILED

and the run exits 43.
This is truthful, but the artifact identity is incomplete.

16. Product and ldd prohibition
Finding 16.1 — No product execution command was found

Classification: CLEAR

Path: both Witness scripts
Fields/comments throughout
The artifact is inspected only with static tools.
Finding 16.2 — No ldd invocation was found

Classification: CLEAR
Both scripts record:

ldd_used=NO
Finding 16.