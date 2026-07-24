"""Shared builder for golden Witness-evidence fixtures (1.0.0-rc4).

Each scenario is a full, internally consistent evidence directory that the
structural validator (validate_witness_evidence.py) must accept with zero
errors. The same builders are used both to materialize the on-disk golden
fixtures (see _generate_fixtures.py) and to construct throw-away trees inside
the unit tests, so the two can never drift apart.

Nothing here executes Docker/Cargo/Witness scripts; these are static
key=value artifacts hand-derived from the host/container schema blocks.
"""

from __future__ import annotations

import hashlib
from collections import OrderedDict
from pathlib import Path

# Pinned canonical identities (mirror validate_witness_evidence.py constants).
GROK = "98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce"
IMG = "6ca5ad23231207874325a751b9df584d51cd42c066c74c6963c264e3233c3e8e"
LOCK = "1512bb4fef0c1166c6a15a3398da9593903be1759b759ce78d9958913e61b421"
WEAVER = "89127c78c3a11492892de7e3b5f0dee18d71775a"
BUILD_CMD = "cargo build -p xai-grok-pager-bin --locked"
TAG = "grok-build-witness-v1.0.0-rc4"
RUST_IMAGE = f"docker.io/library/rust@sha256:{IMG}"
ARTIFACT_SHA = "a" * 64
DESC_A = "b" * 64
DESC_B = "c" * 64
IMAGE_ID = "sha256:" + "d" * 64
ARTIFACT_PATH = "/work/cargo-target/debug/xai-grok-pager"

ALL_SCENARIOS = (
    "success-artifact-present",
    "build-not-started",
    "cargo-failed",
    "artifact-missing",
    "infrastructure-failure",
    "static-inspection-incomplete",
    "image-pull-failure",
    "image-inspect-failure",
    "digest-mismatch",
    "platform-mismatch",
)

# Scenarios where the container never launched (pre-docker infrastructure
# failure): container-owned files are truthful NOT_REACHED placeholders.
_PRE_DOCKER = frozenset(
    {"image-pull-failure", "image-inspect-failure", "digest-mismatch", "platform-mismatch"}
)


def _render(od: "OrderedDict[str, str]") -> str:
    return "".join(f"{k}={v}\n" for k, v in od.items())


# ---------------------------------------------------------------------------
# Per-file builders
# ---------------------------------------------------------------------------


def _weaver_forge_package_identity() -> str:
    return _render(
        OrderedDict(
            [
                ("evidence_schema_version", "1"),
                ("witness_id", "witness01"),
                ("run_id", "run-2026-07-22-001"),
                ("package_version", "1.0.0-rc4"),
                ("weaver_forge_url", "https://github.com/chrono-vector/weaver-forge.git"),
                ("weaver_forge_tag_requested", TAG),
                ("weaver_forge_commit_resolved", WEAVER),
                ("package_clone_head", WEAVER),
                ("package_clone_detached", "yes"),
                ("package_clone_clean_status", "yes"),
                ("tag_head_match", "yes"),
                ("package_commit_authority", "annotated_tag_resolution"),
                ("grok_build_source_commit_expected", GROK),
                ("canonical_run", "yes"),
            ]
        )
    )


def _source_acquisition() -> str:
    return _render(
        OrderedDict(
            [
                ("evidence_schema_version", "1"),
                ("weaver_forge_url", "https://github.com/chrono-vector/weaver-forge.git"),
                ("weaver_forge_tag_requested", TAG),
                ("weaver_forge_commit_resolved", WEAVER),
                ("package_clone_head", WEAVER),
                ("package_clone_clean_status", "yes"),
                ("tag_head_match", "yes"),
                ("package_commit_authority", "annotated_tag_resolution"),
                ("grok_build_url", "https://github.com/xai-org/grok-build.git"),
                ("grok_build_commit_requested", GROK),
                ("grok_build_commit_observed", GROK),
                ("grok_build_clean_tree", "yes"),
                ("fresh_clones", "yes"),
            ]
        )
    )


def _source_identity() -> str:
    return _render(
        OrderedDict(
            [
                ("evidence_schema_version", "1"),
                ("status", "OK"),
                ("grok_build_commit_expected", GROK),
                ("grok_build_commit_observed", GROK),
                ("grok_build_detached_head", "yes"),
                ("cargo_lock_sha256_expected", LOCK),
                ("cargo_lock_sha256_before", LOCK),
            ]
        )
    )


def _environment(scenario: str) -> str:
    container_ran = scenario not in _PRE_DOCKER
    if container_ran:
        os_release = "Debian GNU/Linux 12 (bookworm)"
        uname = "Linux 6.8.0-40-generic"
        rustc = "1.92.0"
        cargo = "1.92.0"
    else:
        os_release = uname = rustc = cargo = "NOT_REACHED"
    return _render(
        OrderedDict(
            [
                ("evidence_schema_version", "1"),
                ("status", "OK"),
                ("outcome", "BUILD_NOT_STARTED"),
                ("witness_id", "witness01"),
                ("host_os", "Linux"),
                ("host_kernel", "6.8.0-40-generic"),
                ("host_arch", "x86_64"),
                ("host_cpu", "AMD Ryzen 9 7950X 16-Core Processor"),
                ("host_ram_gib", "62"),
                ("host_free_disk_gb", "512"),
                ("docker_client_version", "27.3.1"),
                ("docker_server_version", "27.3.1"),
                ("docker_context", "default"),
                ("canonical_platform", "linux/amd64"),
                ("wsl2_indicator", "no"),
                ("ai_assistance_used", "see_WITNESS_STATEMENT.md"),
                ("ai_assistance_detail", "recorded_in_WITNESS_STATEMENT.md"),
                ("human_review_completed", "pending"),
                ("product_executed", "NO"),
                ("upstream_product_commands_not_run", "yes"),
                ("ldd_used", "NO"),
                ("container_os_release", os_release),
                ("container_uname", uname),
                ("rustc_version", rustc),
                ("cargo_version", cargo),
            ]
        )
    )


def _image_identity(scenario: str) -> str:
    base = OrderedDict(
        [
            ("evidence_schema_version", "1"),
            ("status", "OK"),
            ("failure_stage", "NOT_APPLICABLE"),
            ("requested_image", RUST_IMAGE),
            ("requested_digest", f"sha256:{IMG}"),
            ("pull_command", f"docker pull --platform linux/amd64 {RUST_IMAGE}"),
            ("pull_exit_code", "0"),
            ("inspect_image_id_command", "docker inspect --format {{.Id}} " + RUST_IMAGE),
            ("inspect_image_id_exit_code", "0"),
            ("image_id", IMAGE_ID),
            ("inspect_repo_digests_command", "docker inspect --format {{json .RepoDigests}} " + RUST_IMAGE),
            ("inspect_repo_digests_exit_code", "0"),
            ("repo_digests", f"[docker.io/library/rust@sha256:{IMG}]"),
            ("inspect_os_command", "docker inspect --format {{.Os}} " + RUST_IMAGE),
            ("inspect_os_exit_code", "0"),
            ("observed_os", "linux"),
            ("inspect_architecture_command", "docker inspect --format {{.Architecture}} " + RUST_IMAGE),
            ("inspect_architecture_exit_code", "0"),
            ("observed_architecture", "amd64"),
            ("observed_platform", "linux/amd64"),
            ("image_id_available", "yes"),
            ("digest_match_expected", "yes"),
            ("platform_match_expected", "yes"),
            ("proceeded_to_inspect_or_run", "YES"),
            ("cached_image_fallback_used", "NO"),
        ]
    )
    if scenario == "image-pull-failure":
        base.update(
            status="FAILED",
            failure_stage="image_pull",
            pull_exit_code="1",
            inspect_image_id_command="NOT_REACHED",
            inspect_image_id_exit_code="NOT_REACHED",
            image_id="NOT_REACHED",
            inspect_repo_digests_command="NOT_REACHED",
            inspect_repo_digests_exit_code="NOT_REACHED",
            repo_digests="NOT_REACHED",
            inspect_os_command="NOT_REACHED",
            inspect_os_exit_code="NOT_REACHED",
            observed_os="NOT_REACHED",
            inspect_architecture_command="NOT_REACHED",
            inspect_architecture_exit_code="NOT_REACHED",
            observed_architecture="NOT_REACHED",
            observed_platform="NOT_REACHED",
            image_id_available="no",
            digest_match_expected="no",
            platform_match_expected="no",
            proceeded_to_inspect_or_run="NO",
        )
    elif scenario == "image-inspect-failure":
        base.update(
            status="FAILED",
            failure_stage="image_inspect_id",
            inspect_image_id_exit_code="1",
            image_id="NOT_REACHED",
            inspect_repo_digests_command="NOT_REACHED",
            inspect_repo_digests_exit_code="NOT_REACHED",
            repo_digests="NOT_REACHED",
            inspect_os_command="NOT_REACHED",
            inspect_os_exit_code="NOT_REACHED",
            observed_os="NOT_REACHED",
            inspect_architecture_command="NOT_REACHED",
            inspect_architecture_exit_code="NOT_REACHED",
            observed_architecture="NOT_REACHED",
            observed_platform="NOT_REACHED",
            image_id_available="no",
            digest_match_expected="no",
            platform_match_expected="no",
            proceeded_to_inspect_or_run="NO",
        )
    elif scenario == "digest-mismatch":
        base.update(
            status="FAILED",
            failure_stage="repo_digest_mismatch",
            repo_digests="[docker.io/library/rust@sha256:" + ("e" * 64) + "]",
            digest_match_expected="no",
            platform_match_expected="yes",
            proceeded_to_inspect_or_run="NO",
        )
    elif scenario == "platform-mismatch":
        base.update(
            status="FAILED",
            failure_stage="architecture_mismatch",
            observed_architecture="arm64",
            observed_platform="linux/arm64",
            digest_match_expected="yes",
            platform_match_expected="no",
            proceeded_to_inspect_or_run="NO",
        )
    return _render(base)


def _bootstrap(scenario: str) -> str:
    if scenario in _PRE_DOCKER:
        return _render(
            OrderedDict(
                [
                    ("evidence_schema_version", "1"),
                    ("status", "NOT_REACHED"),
                    ("applicable", "no"),
                    ("reason", "stage_not_reached"),
                    ("product_executed", "NO"),
                    ("ldd_used", "NO"),
                ]
            )
        )
    return _render(
        OrderedDict(
            [
                ("evidence_schema_version", "1"),
                ("status", "bootstrap_complete"),
                ("apt_packages", "ca-certificates git build-essential pkg-config cmake curl perl file binutils"),
                ("dotslash_version", "0.5.7"),
                ("dotslash_binary_path", "/work/cargo-home/bin/dotslash"),
                ("protoc_descriptor_src", "/src/bin/protoc"),
                ("protoc_descriptor_writable", "yes"),
                ("protoc_descriptor_src_sha256", DESC_A),
                ("protoc_descriptor_lf_sha256", DESC_B),
                ("PROTOC", "/work/bootstrap/protoc-descriptor.lf"),
                ("protoc_version_output", "libprotoc 29.3"),
                ("protoc_version_exit_code", "0"),
                ("product_executed", "NO"),
            ]
        )
    )


def _build_command(scenario: str) -> str:
    if scenario in _PRE_DOCKER:
        return _render(
            OrderedDict(
                [
                    ("evidence_schema_version", "1"),
                    ("status", "NOT_REACHED"),
                    ("applicable", "no"),
                    ("reason", "stage_not_reached"),
                    ("product_executed", "NO"),
                    ("ldd_used", "NO"),
                ]
            )
        )
    return _render(
        OrderedDict(
            [
                ("evidence_schema_version", "1"),
                ("exact_build_command", BUILD_CMD),
                ("cargo_incremental", "0"),
                ("working_directory", "/src"),
                ("product_executed", "NO"),
            ]
        )
    )


def _build_environment(scenario: str) -> str:
    if scenario in _PRE_DOCKER:
        return _render(
            OrderedDict(
                [
                    ("evidence_schema_version", "1"),
                    ("status", "NOT_REACHED"),
                    ("applicable", "no"),
                    ("reason", "stage_not_reached"),
                    ("product_executed", "NO"),
                    ("ldd_used", "NO"),
                ]
            )
        )
    return _render(
        OrderedDict(
            [
                ("evidence_schema_version", "1"),
                ("status", "OK"),
                ("outcome", "RECORDED"),
                ("docker_platform", "linux/amd64"),
                ("network_mode", "bridge"),
                ("rust_image", RUST_IMAGE),
                ("workdir", "/src"),
                ("home", "/work/home"),
                ("cargo_home", "/work/cargo-home"),
                ("cargo_target_dir", "/work/cargo-target"),
                ("bootstrap_cargo_target_dir", "/work/bootstrap-cargo-target"),
                ("cargo_incremental", "0"),
                ("dotslash_cache", "/work/dotslash-cache"),
                ("path", "/work/cargo-home/bin:/usr/local/cargo/bin:/usr/bin:/bin"),
                ("grok_build_commit", GROK),
                ("expected_cargo_lock_sha256", LOCK),
                ("canonical_build_command", BUILD_CMD),
                ("mount_src", "/src:ro"),
                ("mount_work", "/work:rw"),
                ("mount_evidence", "/evidence:rw"),
                ("mount_container_script", "/witness/container_narrow_build.sh:ro"),
            ]
        )
    )


def _clean_target_proof(scenario: str) -> str:
    if scenario in _PRE_DOCKER:
        return _render(
            OrderedDict(
                [
                    ("evidence_schema_version", "1"),
                    ("status", "CHECKED"),
                    ("outcome", "BUILD_NOT_STARTED"),
                    ("target_path_host", "/work/cargo-target"),
                    ("proof_utc_host", "2026-07-22T00:00:00Z"),
                    ("observed_entry_count_host", "0"),
                    ("target_path_container_prebootstrap", "NOT_REACHED"),
                    ("proof_utc_container_prebootstrap", "NOT_REACHED"),
                    ("observed_entry_count_container_prebootstrap", "NOT_REACHED"),
                    ("target_path_container_precargo", "NOT_REACHED"),
                    ("proof_utc_container_precargo", "NOT_REACHED"),
                    ("observed_entry_count_container", "NOT_REACHED"),
                    ("proof_failed", "no"),
                    ("failure_stage", "NONE"),
                ]
            )
        )
    if scenario == "build-not-started":
        # pre_cargo_empty_target: container target directory was not empty.
        return _render(
            OrderedDict(
                [
                    ("evidence_schema_version", "1"),
                    ("status", "FAILED"),
                    ("outcome", "BUILD_NOT_STARTED"),
                    ("target_path_host", "/work/cargo-target"),
                    ("proof_utc_host", "2026-07-22T00:00:00Z"),
                    ("observed_entry_count_host", "0"),
                    ("target_path_container_prebootstrap", "/work/cargo-target"),
                    ("proof_utc_container_prebootstrap", "2026-07-22T00:01:00Z"),
                    ("observed_entry_count_container_prebootstrap", "0"),
                    ("target_path_container_precargo", "/work/cargo-target"),
                    ("proof_utc_container_precargo", "2026-07-22T00:05:00Z"),
                    ("observed_entry_count_container", "3"),
                    ("proof_failed", "yes"),
                    ("failure_stage", "pre_cargo_empty_target"),
                ]
            )
        )
    status = "OK"
    outcome = "CLEAN_TARGET_VERIFIED"
    fstage = "NOT_APPLICABLE"
    if scenario == "infrastructure-failure":
        status = "FAILED"
        outcome = "INFRASTRUCTURE_FAILURE"
        fstage = "container_runtime"
    return _render(
        OrderedDict(
            [
                ("evidence_schema_version", "1"),
                ("status", status),
                ("outcome", outcome),
                ("target_path_host", "/work/cargo-target"),
                ("proof_utc_host", "2026-07-22T00:00:00Z"),
                ("observed_entry_count_host", "0"),
                ("target_path_container_prebootstrap", "/work/cargo-target"),
                ("proof_utc_container_prebootstrap", "2026-07-22T00:01:00Z"),
                ("observed_entry_count_container_prebootstrap", "0"),
                ("target_path_container_precargo", "/work/cargo-target"),
                ("proof_utc_container_precargo", "2026-07-22T00:05:00Z"),
                ("observed_entry_count_container", "0"),
                ("proof_failed", "no"),
                ("failure_stage", fstage),
            ]
        )
    )


# Outcome parameters per scenario for the container/host outcome-bearing files.
def _outcome(scenario: str) -> str:
    return {
        "success-artifact-present": "CARGO_SUCCEEDED_ARTIFACT_PRESENT",
        "build-not-started": "BUILD_NOT_STARTED",
        "cargo-failed": "CARGO_FAILED",
        "artifact-missing": "CARGO_SUCCEEDED_ARTIFACT_MISSING",
        "infrastructure-failure": "INFRASTRUCTURE_FAILURE",
        "static-inspection-incomplete": "CARGO_SUCCEEDED_ARTIFACT_PRESENT",
        "image-pull-failure": "INFRASTRUCTURE_FAILURE",
        "image-inspect-failure": "INFRASTRUCTURE_FAILURE",
        "digest-mismatch": "INFRASTRUCTURE_FAILURE",
        "platform-mismatch": "INFRASTRUCTURE_FAILURE",
    }[scenario]


def _build_exit_code(scenario: str) -> str:
    outcome = _outcome(scenario)
    if outcome == "CARGO_SUCCEEDED_ARTIFACT_PRESENT":
        incomplete = scenario == "static-inspection-incomplete"
        return _render(
            OrderedDict(
                [
                    ("evidence_schema_version", "1"),
                    ("status", "FAILED" if incomplete else "OK"),
                    ("outcome", outcome),
                    ("cargo_started", "YES"),
                    ("build_status", "COMPLETE"),
                    ("cargo_exit_code", "0"),
                    ("failure_stage", "static_readelf_d" if incomplete else "NOT_APPLICABLE"),
                ]
            )
        )
    if outcome == "CARGO_FAILED":
        return _render(
            OrderedDict(
                [
                    ("evidence_schema_version", "1"),
                    ("status", "FAILED"),
                    ("outcome", outcome),
                    ("cargo_started", "YES"),
                    ("build_status", "FAILED"),
                    ("cargo_exit_code", "101"),
                    ("failure_stage", "cargo_build"),
                ]
            )
        )
    if outcome == "CARGO_SUCCEEDED_ARTIFACT_MISSING":
        return _render(
            OrderedDict(
                [
                    ("evidence_schema_version", "1"),
                    ("status", "FAILED"),
                    ("outcome", outcome),
                    ("cargo_started", "YES"),
                    ("build_status", "COMPLETE"),
                    ("cargo_exit_code", "0"),
                    ("failure_stage", "artifact_presence_check"),
                ]
            )
        )
    if outcome == "BUILD_NOT_STARTED":
        return _render(
            OrderedDict(
                [
                    ("evidence_schema_version", "1"),
                    ("status", "FAILED"),
                    ("outcome", outcome),
                    ("cargo_started", "NO"),
                    ("build_status", "BUILD_NOT_STARTED"),
                    ("cargo_exit_code", "NOT_APPLICABLE"),
                    ("failure_stage", "pre_cargo_empty_target"),
                ]
            )
        )
    # INFRASTRUCTURE_FAILURE
    return _render(
        OrderedDict(
            [
                ("evidence_schema_version", "1"),
                ("status", "FAILED"),
                ("outcome", outcome),
                ("cargo_started", "NO"),
                ("build_status", "INFRASTRUCTURE_FAILURE"),
                ("cargo_exit_code", "NOT_APPLICABLE"),
                ("failure_stage", _infra_stage(scenario)),
            ]
        )
    )


def _infra_stage(scenario: str) -> str:
    return {
        "infrastructure-failure": "container_runtime",
        "image-pull-failure": "image_pull",
        "image-inspect-failure": "image_inspect_id",
        "digest-mismatch": "repo_digest_mismatch",
        "platform-mismatch": "architecture_mismatch",
    }.get(scenario, "container_runtime")


def _docker_exit_code(scenario: str) -> str:
    outcome = _outcome(scenario)
    if scenario in _PRE_DOCKER:
        return _render(
            OrderedDict(
                [
                    ("evidence_schema_version", "1"),
                    ("status", "FAILED"),
                    ("docker_started_utc", "NOT_STARTED"),
                    ("docker_finished_utc", "NOT_STARTED"),
                    ("docker_exit_code", "NOT_STARTED"),
                    ("container_platform", "linux/amd64"),
                    ("network_mode", "bridge"),
                    ("product_executed", "NO"),
                    ("ldd_used", "NO"),
                    ("outcome", outcome),
                    ("failure_stage", _infra_stage(scenario)),
                ]
            )
        )
    dexit = {
        "success-artifact-present": "0",
        "static-inspection-incomplete": "43",
        "cargo-failed": "101",
        "artifact-missing": "42",
        "build-not-started": "1",
        "infrastructure-failure": "1",
    }[scenario]
    fstage = "NONE" if outcome == "CARGO_SUCCEEDED_ARTIFACT_PRESENT" and scenario != "static-inspection-incomplete" else _fail_stage(scenario)
    return _render(
        OrderedDict(
            [
                ("evidence_schema_version", "1"),
                ("status", "RECORDED"),
                ("docker_started_utc", "2026-07-22T00:00:00Z"),
                ("docker_finished_utc", "2026-07-22T01:00:00Z"),
                ("docker_exit_code", dexit),
                ("container_platform", "linux/amd64"),
                ("network_mode", "bridge"),
                ("product_executed", "NO"),
                ("ldd_used", "NO"),
                ("outcome", outcome),
                ("failure_stage", fstage),
            ]
        )
    )


def _fail_stage(scenario: str) -> str:
    return {
        "success-artifact-present": "NONE",
        "static-inspection-incomplete": "static_readelf_d",
        "cargo-failed": "cargo_build",
        "artifact-missing": "artifact_presence_check",
        "build-not-started": "pre_cargo_empty_target",
        "infrastructure-failure": "container_runtime",
    }.get(scenario, "NONE")


def _build_timing(scenario: str) -> str:
    outcome = _outcome(scenario)
    cargo_started = "YES" if outcome in (
        "CARGO_FAILED",
        "CARGO_SUCCEEDED_ARTIFACT_MISSING",
        "CARGO_SUCCEEDED_ARTIFACT_PRESENT",
    ) else "NO"
    incomplete = scenario == "static-inspection-incomplete"
    status = "OK" if outcome == "CARGO_SUCCEEDED_ARTIFACT_PRESENT" and not incomplete else "FAILED"
    if scenario in _PRE_DOCKER:
        return _render(
            OrderedDict(
                [
                    ("evidence_schema_version", "1"),
                    ("status", "FAILED"),
                    ("outcome", outcome),
                    ("docker_started_utc", "NOT_STARTED"),
                    ("docker_finished_utc", "NOT_STARTED"),
                    ("docker_elapsed_seconds", "NOT_APPLICABLE"),
                    ("cargo_started_utc", "NOT_APPLICABLE"),
                    ("cargo_finished_utc", "NOT_APPLICABLE"),
                    ("cargo_elapsed_seconds", "NOT_APPLICABLE"),
                    ("cargo_started", "NO"),
                    ("cargo_exit_code", "NOT_APPLICABLE"),
                    ("docker_exit_code", "NOT_STARTED"),
                    ("failure_stage", _infra_stage(scenario)),
                ]
            )
        )
    if cargo_started == "YES":
        cargo_started_utc = "2026-07-22T00:05:00Z"
        cargo_finished_utc = "2026-07-22T00:55:00Z"
        cargo_elapsed = "3000"
        cargo_exit = "0" if outcome != "CARGO_FAILED" else "101"
    else:
        cargo_started_utc = "NOT_APPLICABLE"
        cargo_finished_utc = "NOT_APPLICABLE"
        cargo_elapsed = "NOT_APPLICABLE"
        cargo_exit = "NOT_APPLICABLE"
    dexit = {
        "success-artifact-present": "0",
        "static-inspection-incomplete": "43",
        "cargo-failed": "101",
        "artifact-missing": "42",
        "build-not-started": "1",
        "infrastructure-failure": "1",
    }[scenario]
    return _render(
        OrderedDict(
            [
                ("evidence_schema_version", "1"),
                ("status", status),
                ("outcome", outcome),
                ("docker_started_utc", "2026-07-22T00:00:00Z"),
                ("docker_finished_utc", "2026-07-22T01:00:00Z"),
                ("docker_elapsed_seconds", "3600"),
                ("cargo_started_utc", cargo_started_utc),
                ("cargo_finished_utc", cargo_finished_utc),
                ("cargo_elapsed_seconds", cargo_elapsed),
                ("cargo_started", cargo_started),
                ("cargo_exit_code", cargo_exit),
                ("docker_exit_code", dexit),
                ("failure_stage", _fail_stage(scenario)),
            ]
        )
    )


def _artifact_identity(scenario: str) -> str:
    outcome = _outcome(scenario)
    if outcome == "CARGO_SUCCEEDED_ARTIFACT_PRESENT":
        incomplete = scenario == "static-inspection-incomplete"
        return _render(
            OrderedDict(
                [
                    ("evidence_schema_version", "1"),
                    ("outcome", outcome),
                    ("applicable", "yes"),
                    ("artifact_present", "yes"),
                    ("artifact_path", ARTIFACT_PATH),
                    ("artifact_filename", "xai-grok-pager"),
                    ("artifact_size_bytes", "600647920"),
                    ("artifact_sha256", ARTIFACT_SHA),
                    ("gnu_build_id", "abcdef0123456789"),
                    ("static_inspection_complete", "no" if incomplete else "yes"),
                    ("product_executed", "NO"),
                    ("ldd_used", "NO"),
                ]
            )
        )
    applicable = "yes" if outcome == "CARGO_SUCCEEDED_ARTIFACT_MISSING" else "no"
    reason = {
        "cargo-failed": "cargo build exited nonzero (101)",
        "artifact-missing": "cargo exited 0 but expected artifact is missing",
        "build-not-started": "cargo never started (pre_cargo_empty_target)",
        "infrastructure-failure": "infrastructure failure before artifact build",
        "image-pull-failure": "container never launched (image pull failed)",
        "image-inspect-failure": "container never launched (image inspect failed)",
        "digest-mismatch": "container never launched (repo digest mismatch)",
        "platform-mismatch": "container never launched (platform mismatch)",
    }[scenario]
    return _render(
        OrderedDict(
            [
                ("evidence_schema_version", "1"),
                ("outcome", outcome),
                ("applicable", applicable),
                ("artifact_present", "no"),
                ("reason", reason),
                ("product_executed", "NO"),
                ("ldd_used", "NO"),
            ]
        )
    )


def _static_inspection(scenario: str) -> str:
    outcome = _outcome(scenario)
    if outcome == "CARGO_SUCCEEDED_ARTIFACT_PRESENT":
        incomplete = scenario == "static-inspection-incomplete"
        readelf_d_ec = "1" if incomplete else "0"
        status = "FAILED" if incomplete else "OK"
        inspection_complete = "no" if incomplete else "yes"
        reason = (
            "one or more required static inspection commands failed; outcome remains "
            "CARGO_SUCCEEDED_ARTIFACT_PRESENT; verdict ceiling PARTIAL"
            if incomplete
            else "all required static inspection commands succeeded"
        )
        fstage = "static_readelf_d" if incomplete else "NOT_APPLICABLE"
        return _render(
            OrderedDict(
                [
                    ("evidence_schema_version", "1"),
                    ("status", status),
                    ("outcome", "CARGO_SUCCEEDED_ARTIFACT_PRESENT"),
                    ("applicable", "yes"),
                    ("artifact_present", "yes"),
                    ("artifact_path", ARTIFACT_PATH),
                    ("sha256sum_command", f"sha256sum {ARTIFACT_PATH}"),
                    ("sha256sum_output", f"{ARTIFACT_SHA}  {ARTIFACT_PATH}"),
                    ("sha256sum_exit_code", "0"),
                    ("stat_command", f"stat {ARTIFACT_PATH}"),
                    ("stat_output", "Size: 600647920 Blocks: 1173920 IO Block: 4096 regular file"),
                    ("stat_exit_code", "0"),
                    ("file_command", f"file {ARTIFACT_PATH}"),
                    ("file_output", "ELF 64-bit LSB executable, x86-64, dynamically linked"),
                    ("file_exit_code", "0"),
                    ("readelf_h_command", f"readelf -h {ARTIFACT_PATH}"),
                    ("readelf_h_output", "ELF Header: Class ELF64 Machine Advanced Micro Devices X86-64"),
                    ("readelf_h_exit_code", "0"),
                    ("readelf_n_command", f"readelf -n {ARTIFACT_PATH}"),
                    ("readelf_n_output", "Displaying notes Build ID: abcdef0123456789"),
                    ("readelf_n_exit_code", "0"),
                    ("readelf_d_command", f"readelf -d {ARTIFACT_PATH}"),
                    (
                        "readelf_d_output",
                        "readelf: Error: Not a dynamic object" if incomplete else "Dynamic section at offset",
                    ),
                    ("readelf_d_exit_code", readelf_d_ec),
                    ("objdump_f_command", f"objdump -f {ARTIFACT_PATH}"),
                    ("objdump_f_output", "file format elf64-x86-64 architecture i386:x86-64"),
                    ("objdump_f_exit_code", "0"),
                    ("inspection_complete", inspection_complete),
                    ("failure_stage", fstage),
                    ("reason", reason),
                ]
            )
        )
    # applicable=no shape (all per-tool fields present-but-empty or NOT_APPLICABLE)
    empty = OrderedDict(
        [
            ("evidence_schema_version", "1"),
            ("status", "NOT_APPLICABLE"),
            ("outcome", "NOT_APPLICABLE"),
            ("applicable", "no"),
            ("artifact_present", "no"),
            ("artifact_path", ""),
            ("sha256sum_command", ""),
            ("sha256sum_output", ""),
            ("sha256sum_exit_code", ""),
            ("stat_command", ""),
            ("stat_output", ""),
            ("stat_exit_code", ""),
            ("file_command", ""),
            ("file_output", ""),
            ("file_exit_code", ""),
            ("readelf_h_command", ""),
            ("readelf_h_output", ""),
            ("readelf_h_exit_code", ""),
            ("readelf_n_command", ""),
            ("readelf_n_output", ""),
            ("readelf_n_exit_code", ""),
            ("readelf_d_command", ""),
            ("readelf_d_output", ""),
            ("readelf_d_exit_code", ""),
            ("objdump_f_command", ""),
            ("objdump_f_output", ""),
            ("objdump_f_exit_code", ""),
            ("inspection_complete", "no"),
            ("failure_stage", "NOT_APPLICABLE"),
            ("reason", "no artifact to inspect for outcome " + outcome),
        ]
    )
    return _render(empty)


def _post_build_integrity(scenario: str) -> str:
    outcome = _outcome(scenario)
    gate_note = (
        "evidence_inventory_complete can only become yes after the Witness completes "
        "WITNESS_STATEMENT.md, WITNESS_VERDICT.md, DEVIATIONS.txt, REDACTIONS.md, and the "
        "FINAL manifest validates; the automated host run always records "
        "evidence_inventory_complete=no"
    )
    if scenario in _PRE_DOCKER:
        return _render(
            OrderedDict(
                [
                    ("evidence_schema_version", "1"),
                    ("status", "FAILED"),
                    ("outcome", outcome),
                    ("source_head_before", "NOT_REACHED"),
                    ("source_head_after", "NOT_REACHED"),
                    ("source_head_unchanged", "no"),
                    ("source_clean_before", "no"),
                    ("source_clean_after", "no"),
                    ("cargo_lock_sha256_before", "NOT_REACHED"),
                    ("cargo_lock_sha256_after", "NOT_REACHED"),
                    ("cargo_lock_unchanged", "no"),
                    ("cargo_lock_post_matches_expected", "no"),
                    ("source_or_lock_changed", "yes"),
                    ("artifact_path", "NOT_REACHED"),
                    ("artifact_exists", "no"),
                    ("docker_exit_code", "NOT_STARTED"),
                    ("failure_stage", _infra_stage(scenario)),
                    ("evidence_inventory_complete", "no"),
                    ("full_integrity_gate_all_four_yes", "no"),
                    ("full_integrity_gate_note", gate_note),
                    ("post_build_integrity_ok", "no"),
                ]
            )
        )
    # Post-Docker fixtures: technical POST_BUILD gate passed (source/lock intact).
    # Cargo/outcome failure is recorded elsewhere; POST_BUILD status tracks the
    # integrity gate only (status=OK iff post_build_integrity_ok=yes).
    artifact_exists = "yes" if scenario == "success-artifact-present" else "no"
    docker_exit = "0"
    if scenario == "cargo-failed":
        docker_exit = "1"
    elif scenario in ("infrastructure-failure", "build-not-started"):
        docker_exit = "0"
    return _render(
        OrderedDict(
            [
                ("evidence_schema_version", "1"),
                ("status", "OK"),
                ("outcome", outcome),
                ("source_head_before", GROK),
                ("source_head_after", GROK),
                ("source_head_unchanged", "yes"),
                ("source_clean_before", "yes"),
                ("source_clean_after", "yes"),
                ("cargo_lock_sha256_before", LOCK),
                ("cargo_lock_sha256_after", LOCK),
                ("cargo_lock_unchanged", "yes"),
                ("cargo_lock_post_matches_expected", "yes"),
                ("source_or_lock_changed", "no"),
                ("artifact_path", ARTIFACT_PATH),
                ("artifact_exists", artifact_exists),
                ("docker_exit_code", docker_exit),
                ("failure_stage", "NONE"),
                ("evidence_inventory_complete", "no"),
                ("full_integrity_gate_all_four_yes", "no"),
                ("full_integrity_gate_note", gate_note),
                ("post_build_integrity_ok", "yes"),
            ]
        )
    )


def _witness_statement() -> str:
    return _render(
        OrderedDict(
            [
                ("evidence_schema_version", "1"),
                ("witness_identity_or_handle", "Jane Doe (@janedoe)"),
                ("not_package_owner", "yes"),
                ("not_owner_side_reproducer", "yes"),
                ("witness_controlled_host", "yes"),
                ("ai_assistance_used", "no"),
                ("human_review_completed", "yes"),
                ("product_executed", "NO"),
                ("ldd_used", "NO"),
                ("upstream_product_commands_not_run", "yes"),
            ]
        )
    )


def _verdict_params(scenario: str) -> tuple[str, str]:
    """Return (verdict_ceiling, proposed_verdict) for the scenario."""
    return {
        "success-artifact-present": ("PASS", "PASS"),
        "build-not-started": ("INDETERMINATE", "INDETERMINATE"),
        "cargo-failed": ("FAIL", "FAIL"),
        "artifact-missing": ("FAIL", "FAIL"),
        "infrastructure-failure": ("INDETERMINATE", "INDETERMINATE"),
        "static-inspection-incomplete": ("PARTIAL", "PARTIAL"),
        # pre-docker image failures trip identity-mismatch -> machine ceiling FAIL
        "image-pull-failure": ("FAIL", "FAIL"),
        "image-inspect-failure": ("FAIL", "FAIL"),
        "digest-mismatch": ("FAIL", "FAIL"),
        "platform-mismatch": ("FAIL", "FAIL"),
    }[scenario]


def _witness_verdict(scenario: str) -> str:
    ceiling, proposed = _verdict_params(scenario)
    kv = _render(
        OrderedDict(
            [
                ("evidence_schema_version", "1"),
                ("run_id", "run-2026-07-22-001"),
                ("package_tag", TAG),
                ("weaver_forge_commit", WEAVER),
                ("grok_build_commit", GROK),
                ("outcome", _outcome(scenario)),
                ("verdict_ceiling", ceiling),
                ("product_executed", "NO"),
                ("ldd_used", "NO"),
                ("maintainer_intake_verdict", "pending"),
            ]
        )
    )
    return (
        kv
        + "\n"
        + f"Witness proposed verdict: {proposed}\n\n"
        + "## Justification\n\n"
        + "See WITNESS_CLASSIFICATION.md precedence table; proposed verdict is at "
        + "or below the machine-computed ceiling for this run.\n"
    )


def _deviations() -> str:
    return "evidence_schema_version=1\ndeviation_state=NONE\n"


def _redactions() -> str:
    return (
        "evidence_schema_version=1\nredaction_state=NONE\n"
        "semantic_integrity_declaration=yes\n"
    )


def _raw(label: str, scenario: str) -> str:
    if scenario in _PRE_DOCKER:
        return f"# {label}: container never launched ({_infra_stage(scenario)})\n"
    return f"# {label} capture for scenario {scenario}\n(captured output elided in fixture)\n"


def build_scenario(scenario: str) -> "dict[str, str]":
    """Return {relative_filename: file_text} for every required content file
    (the manifest is computed separately by write_tree)."""
    if scenario not in ALL_SCENARIOS:
        raise ValueError(f"unknown scenario: {scenario}")
    return {
        "WEAVER_FORGE_PACKAGE_IDENTITY.txt": _weaver_forge_package_identity(),
        "ENVIRONMENT.txt": _environment(scenario),
        "SOURCE_ACQUISITION.txt": _source_acquisition(),
        "SOURCE_IDENTITY.txt": _source_identity(),
        "IMAGE_IDENTITY.txt": _image_identity(scenario),
        "BOOTSTRAP.txt": _bootstrap(scenario),
        "CLEAN_TARGET_PROOF.txt": _clean_target_proof(scenario),
        "BUILD_COMMAND.txt": _build_command(scenario),
        "BUILD_ENVIRONMENT.txt": _build_environment(scenario),
        "BUILD_STDOUT.txt": _raw("BUILD_STDOUT", scenario),
        "BUILD_STDERR.txt": _raw("BUILD_STDERR", scenario),
        "DOCKER_EXIT_CODE.txt": _docker_exit_code(scenario),
        "BUILD_EXIT_CODE.txt": _build_exit_code(scenario),
        "BUILD_TIMING.txt": _build_timing(scenario),
        "CONTAINER_STDOUT.txt": _raw("CONTAINER_STDOUT", scenario),
        "CONTAINER_STDERR.txt": _raw("CONTAINER_STDERR", scenario),
        "ARTIFACT_IDENTITY.txt": _artifact_identity(scenario),
        "STATIC_ARTIFACT_INSPECTION.txt": _static_inspection(scenario),
        "POST_BUILD_INTEGRITY.txt": _post_build_integrity(scenario),
        "WITNESS_STATEMENT.md": _witness_statement(),
        "WITNESS_VERDICT.md": _witness_verdict(scenario),
        "DEVIATIONS.txt": _deviations(),
        "REDACTIONS.md": _redactions(),
    }


def write_tree(base: Path, files: "dict[str, str]", manifest_name: str = "EVIDENCE_MANIFEST.sha256") -> Path:
    """Materialize a fixture tree and its SHA-256 manifest at ``base``."""
    base.mkdir(parents=True, exist_ok=True)
    for name, text in files.items():
        (base / name).write_text(text, encoding="utf-8", newline="\n")
    lines = []
    for name in sorted(files):
        digest = hashlib.sha256((base / name).read_bytes()).hexdigest()
        lines.append(f"{digest}  ./{name}")
    (base / manifest_name).write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return base


def build_and_write(base: Path, scenario: str) -> Path:
    return write_tree(base, build_scenario(scenario))
