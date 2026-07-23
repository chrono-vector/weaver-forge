#!/usr/bin/env bash
# In-container narrow build — Grok Build xai-grok-pager-bin only.
#
# C2E-5 / 1.0.0-rc4 schema remediations. Implements an explicit outcome model
# (BUILD_NOT_STARTED / CARGO_FAILED / CARGO_SUCCEEDED_ARTIFACT_MISSING /
# CARGO_SUCCEEDED_ARTIFACT_PRESENT / INFRASTRUCTURE_FAILURE), hard-fails
# required identity/toolchain/version probes (no `|| true` masking), keeps
# the bootstrap-vs-grok Cargo target separation, and guarantees every
# required evidence file exists and is truthful on every exit path.
#
# Static inspection failure contract (artifact present, a required probe fails):
#   - outcome remains CARGO_SUCCEEDED_ARTIFACT_PRESENT
#   - STATIC_ARTIFACT_INSPECTION status=FAILED, inspection_complete=no
#   - container exits with STATIC_INSPECTION_INCOMPLETE_EXIT (dedicated nonzero)
#   - host/validator: verdict ceiling PARTIAL; PASS prohibited
#
# Prohibited unconditionally, in this script and in every code path below:
# executing the built product, and running `ldd` against it.
#
# Do NOT write BOOTSTRAP_PROTOC_VERSION.txt under EVIDENCE_DIR. Protoc version
# output is captured to a shell variable (or /work/bootstrap/) and recorded as
# BOOTSTRAP.txt fields protoc_version_output / protoc_version_exit_code.
set -Eeuo pipefail

# --- Identity expectations (env override; defaults match host canonical) ---
GROK_BUILD_COMMIT="${GROK_BUILD_COMMIT:-98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce}"
EXPECTED_CARGO_LOCK_SHA256="${EXPECTED_CARGO_LOCK_SHA256:-1512bb4fef0c1166c6a15a3398da9593903be1759b759ce78d9958913e61b421}"
CANONICAL_BUILD_CMD="${CANONICAL_BUILD_CMD:-cargo build -p xai-grok-pager-bin --locked}"
EXPECTED_RUSTC_VERSION="${EXPECTED_RUSTC_VERSION:-1.92.0}"
EXPECTED_CARGO_VERSION="${EXPECTED_CARGO_VERSION:-1.92.0}"
EXPECTED_DOTSLASH_VERSION="${EXPECTED_DOTSLASH_VERSION:-0.5.7}"
# Digest-pinned image string (host may pass RUST_IMAGE; default is canonical).
RUST_IMAGE="${RUST_IMAGE:-docker.io/library/rust@sha256:6ca5ad23231207874325a751b9df584d51cd42c066c74c6963c264e3233c3e8e}"

EVIDENCE_SCHEMA_VERSION=1

# --- Dedicated nonzero exit codes (must not collide with cargo's own codes) ---
ARTIFACT_MISSING_EXIT=42
STATIC_INSPECTION_INCOMPLETE_EXIT=43

CARGO_HOME="/work/cargo-home"
CARGO_TARGET_DIR_GROK="/work/cargo-target"
BOOTSTRAP_CARGO_TARGET_DIR="/work/bootstrap-cargo-target"
DOTSLASH_CACHE="/work/dotslash-cache"
HOME="/work/home"
BOOTSTRAP_DIR="/work/bootstrap"
EVIDENCE="/evidence"

ARTIFACT="${CARGO_TARGET_DIR_GROK}/debug/xai-grok-pager"

PROTOC_DESCRIPTOR_SRC="/src/bin/protoc"
PROTOC_DESCRIPTOR_WR="${BOOTSTRAP_DIR}/protoc-descriptor.lf"

# --- Mutable run state used by evidence writers and the ERR trap ---
CURRENT_STAGE="script_init"
CARGO_STARTED="NO"
CARGO_EXIT_CODE=""
EVIDENCE_FINALIZED="NO"
CARGO_START_UTC=""
CARGO_END_UTC=""
CARGO_ELAPSED_SECONDS=""

# CLEAN_TARGET_PROOF schema field state (host may pre-write host_* fields).
CT_STATUS="NOT_REACHED"
CT_OUTCOME="NOT_REACHED"
CT_TARGET_PATH_HOST="NOT_REACHED"
CT_PROOF_UTC_HOST="NOT_REACHED"
CT_OBS_HOST="NOT_REACHED"
CT_TARGET_PREBOOT="NOT_REACHED"
CT_UTC_PREBOOT="NOT_REACHED"
CT_OBS_PREBOOT="NOT_REACHED"
CT_TARGET_PRECARGO="NOT_REACHED"
CT_UTC_PRECARGO="NOT_REACHED"
CT_OBS_CONTAINER="NOT_REACHED"
CT_PROOF_FAILED="no"
CT_FAILURE_STAGE="NOT_REACHED"
CT_LISTINGS=""

ts() { date -u +%Y-%m-%dT%H:%M:%SZ; }

set_stage() { CURRENT_STAGE="$1"; }

# Escape multiline command output to a single key=value line (\n for newlines).
escape_oneline() {
  local s="${1-}"
  s="${s//\\/\\\\}"
  s="${s//$'\r'/}"
  s="${s//$'\n'/\\n}"
  printf '%s' "${s}"
}

# Read first matching key=value from a file (value may be empty).
read_kv() {
  local file="$1" key="$2" default="${3-}"
  local line
  if [[ -f "${file}" ]]; then
    line="$(grep -m1 "^${key}=" "${file}" 2>/dev/null || true)"
    if [[ -n "${line}" ]]; then
      printf '%s' "${line#*=}"
      return 0
    fi
  fi
  printf '%s' "${default}"
}

# --- Evidence writers -------------------------------------------------------

# Writes BUILD_EXIT_CODE.txt and BUILD_TIMING.txt with rc4 schema field names.
# Never leaves NOT_REACHED as final for completed failure paths.
write_outcome_evidence() {
  local outcome="$1" cargo_started="$2" build_status="$3" cargo_exit_code="$4"
  local docker_exit_code="$5" failure_stage="$6" status="$7"
  local cargo_started_utc="$8" cargo_finished_utc="$9" cargo_elapsed_seconds="${10}"

  {
    echo "BEGIN_SCHEMA_BLOCK BUILD_EXIT_CODE"
    echo "evidence_schema_version=${EVIDENCE_SCHEMA_VERSION}"
    echo "status=${status}"
    echo "outcome=${outcome}"
    echo "cargo_started=${cargo_started}"
    echo "build_status=${build_status}"
    echo "cargo_exit_code=${cargo_exit_code}"
    echo "failure_stage=${failure_stage}"
    echo "END_SCHEMA_BLOCK"
  } > "${EVIDENCE}/BUILD_EXIT_CODE.txt"

  {
    echo "BEGIN_SCHEMA_BLOCK BUILD_TIMING"
    echo "evidence_schema_version=${EVIDENCE_SCHEMA_VERSION}"
    echo "status=${status}"
    echo "outcome=${outcome}"
    # Docker wall-clock is host-owned; container records NOT_APPLICABLE.
    echo "docker_started_utc=NOT_APPLICABLE"
    echo "docker_finished_utc=NOT_APPLICABLE"
    echo "docker_elapsed_seconds=NOT_APPLICABLE"
    echo "cargo_started_utc=${cargo_started_utc}"
    echo "cargo_finished_utc=${cargo_finished_utc}"
    echo "cargo_elapsed_seconds=${cargo_elapsed_seconds}"
    echo "cargo_started=${cargo_started}"
    echo "cargo_exit_code=${cargo_exit_code}"
    echo "docker_exit_code=${docker_exit_code}"
    echo "failure_stage=${failure_stage}"
    echo "END_SCHEMA_BLOCK"
  } > "${EVIDENCE}/BUILD_TIMING.txt"
}

# Truthful "no artifact" ARTIFACT_IDENTITY.txt / STATIC_ARTIFACT_INSPECTION.txt.
# applicable=yes only when the outcome expects an artifact check
# (CARGO_SUCCEEDED_ARTIFACT_MISSING); otherwise applicable=no.
write_no_artifact_evidence() {
  local reason="$1"
  local applicable="${2:-no}"
  local outcome="${3:-BUILD_NOT_STARTED}"
  {
    echo "evidence_schema_version=${EVIDENCE_SCHEMA_VERSION}"
    echo "outcome=${outcome}"
    echo "applicable=${applicable}"
    echo "artifact_present=no"
    echo "reason=${reason}"
    echo "product_executed=NO"
    echo "ldd_used=NO"
  } > "${EVIDENCE}/ARTIFACT_IDENTITY.txt"
  {
    echo "BEGIN_SCHEMA_BLOCK STATIC_ARTIFACT_INSPECTION"
    echo "evidence_schema_version=${EVIDENCE_SCHEMA_VERSION}"
    echo "status=NOT_APPLICABLE"
    echo "outcome=${outcome}"
    echo "applicable=no"
    echo "artifact_present=no"
    echo "artifact_path=NOT_APPLICABLE"
    echo "sha256sum_command=NOT_APPLICABLE"
    echo "sha256sum_output=NOT_APPLICABLE"
    echo "sha256sum_exit_code=NOT_APPLICABLE"
    echo "stat_command=NOT_APPLICABLE"
    echo "stat_output=NOT_APPLICABLE"
    echo "stat_exit_code=NOT_APPLICABLE"
    echo "file_command=NOT_APPLICABLE"
    echo "file_output=NOT_APPLICABLE"
    echo "file_exit_code=NOT_APPLICABLE"
    echo "readelf_h_command=NOT_APPLICABLE"
    echo "readelf_h_output=NOT_APPLICABLE"
    echo "readelf_h_exit_code=NOT_APPLICABLE"
    echo "readelf_n_command=NOT_APPLICABLE"
    echo "readelf_n_output=NOT_APPLICABLE"
    echo "readelf_n_exit_code=NOT_APPLICABLE"
    echo "readelf_d_command=NOT_APPLICABLE"
    echo "readelf_d_output=NOT_APPLICABLE"
    echo "readelf_d_exit_code=NOT_APPLICABLE"
    echo "objdump_f_command=NOT_APPLICABLE"
    echo "objdump_f_output=NOT_APPLICABLE"
    echo "objdump_f_exit_code=NOT_APPLICABLE"
    echo "inspection_complete=no"
    echo "failure_stage=NONE"
    echo "reason=${reason}"
    echo "END_SCHEMA_BLOCK"
  } > "${EVIDENCE}/STATIC_ARTIFACT_INSPECTION.txt"
}

# Best-effort (non-fallible) artifact record used only from the generic ERR
# trap, when the normal artifact-evidence path never ran to completion.
write_artifact_evidence_best_effort() {
  local stage="$1"
  if [[ -f "${ARTIFACT}" ]]; then
    {
      echo "evidence_schema_version=${EVIDENCE_SCHEMA_VERSION}"
      echo "applicable=yes"
      echo "artifact_present=yes"
      echo "artifact_path=${ARTIFACT}"
      echo "note=unexpected script failure at stage=${stage}; full identity capture not completed"
      echo "product_executed=NO"
      echo "ldd_used=NO"
    } > "${EVIDENCE}/ARTIFACT_IDENTITY.txt"
    {
      echo "BEGIN_SCHEMA_BLOCK STATIC_ARTIFACT_INSPECTION"
      echo "evidence_schema_version=${EVIDENCE_SCHEMA_VERSION}"
      echo "status=FAILED"
      echo "outcome=NOT_APPLICABLE"
      echo "applicable=yes"
      echo "artifact_present=yes"
      echo "artifact_path=${ARTIFACT}"
      echo "sha256sum_command="
      echo "sha256sum_output="
      echo "sha256sum_exit_code="
      echo "stat_command="
      echo "stat_output="
      echo "stat_exit_code="
      echo "file_command="
      echo "file_output="
      echo "file_exit_code="
      echo "readelf_h_command="
      echo "readelf_h_output="
      echo "readelf_h_exit_code="
      echo "readelf_n_command="
      echo "readelf_n_output="
      echo "readelf_n_exit_code="
      echo "readelf_d_command="
      echo "readelf_d_output="
      echo "readelf_d_exit_code="
      echo "objdump_f_command="
      echo "objdump_f_output="
      echo "objdump_f_exit_code="
      echo "inspection_complete=no"
      echo "failure_stage=${stage}"
      echo "reason=unexpected script failure at stage=${stage} before static inspection completed"
      echo "END_SCHEMA_BLOCK"
    } > "${EVIDENCE}/STATIC_ARTIFACT_INSPECTION.txt"
  else
    write_no_artifact_evidence "unexpected script failure at stage=${stage}; artifact not present at check time" "no" "INFRASTRUCTURE_FAILURE"
  fi
}

# Rewrite CLEAN_TARGET_PROOF schema block; listings are labelled human-review
# sections (not duplicate structured keys).
flush_clean_target_proof() {
  {
    echo "BEGIN_SCHEMA_BLOCK CLEAN_TARGET"
    echo "evidence_schema_version=${EVIDENCE_SCHEMA_VERSION}"
    echo "status=${CT_STATUS}"
    echo "outcome=${CT_OUTCOME}"
    echo "target_path_host=${CT_TARGET_PATH_HOST}"
    echo "proof_utc_host=${CT_PROOF_UTC_HOST}"
    echo "observed_entry_count_host=${CT_OBS_HOST}"
    echo "target_path_container_prebootstrap=${CT_TARGET_PREBOOT}"
    echo "proof_utc_container_prebootstrap=${CT_UTC_PREBOOT}"
    echo "observed_entry_count_container_prebootstrap=${CT_OBS_PREBOOT}"
    echo "target_path_container_precargo=${CT_TARGET_PRECARGO}"
    echo "proof_utc_container_precargo=${CT_UTC_PRECARGO}"
    echo "observed_entry_count_container=${CT_OBS_CONTAINER}"
    echo "proof_failed=${CT_PROOF_FAILED}"
    echo "failure_stage=${CT_FAILURE_STAGE}"
    echo "END_SCHEMA_BLOCK"
    if [[ -n "${CT_LISTINGS}" ]]; then
      echo "# --- listings ---"
      printf '%s' "${CT_LISTINGS}"
    fi
  } > "${EVIDENCE}/CLEAN_TARGET_PROOF.txt"
}

# Append a labelled human-review listing for one clean-target check.
# Prints observed entry count on stdout.
append_clean_target_listing() {
  local label="$1"
  local target_dir="$2"
  local count listing find_out
  count="$(find "${target_dir}" -mindepth 1 2>/dev/null | wc -l | tr -d ' ')"
  listing="$(ls -la "${target_dir}" 2>&1 || true)"
  find_out="$(find "${target_dir}" -mindepth 1 -print 2>/dev/null || true)"
  CT_LISTINGS+="# --- ${label} ---"$'\n'
  CT_LISTINGS+="# target_dir=${target_dir}"$'\n'
  CT_LISTINGS+="# check_utc=$(ts)"$'\n'
  CT_LISTINGS+="# observed_entry_count_for_review=${count}"$'\n'
  CT_LISTINGS+="# --- ls -la ---"$'\n'
  CT_LISTINGS+="${listing}"$'\n'
  CT_LISTINGS+="# --- find ---"$'\n'
  CT_LISTINGS+="${find_out}"$'\n'
  echo "${count}"
}

# Pre-populates every container-owned evidence file with truthful, non-empty
# "run in progress" / NOT_REACHED placeholders before any fallible operation.
init_evidence() {
  : > "${EVIDENCE}/BUILD_STDOUT.txt"
  : > "${EVIDENCE}/BUILD_STDERR.txt"
  touch "${EVIDENCE}/ENVIRONMENT.txt"
  # ENVIRONMENT.txt is dual-owned (host pre-writes host facts; container
  # appends toolchain facts). Guarantee non-empty even if the host did not
  # pre-init it, without clobbering any host content that is already there.
  if [[ ! -s "${EVIDENCE}/ENVIRONMENT.txt" ]]; then
    {
      echo "evidence_schema_version=${EVIDENCE_SCHEMA_VERSION}"
      echo "status=pending_container_toolchain_capture"
    } > "${EVIDENCE}/ENVIRONMENT.txt"
  fi

  {
    echo "BEGIN_SCHEMA_BLOCK BUILD_EXIT_CODE"
    echo "evidence_schema_version=${EVIDENCE_SCHEMA_VERSION}"
    echo "status=NOT_REACHED"
    echo "outcome=NOT_REACHED"
    echo "cargo_started=NO"
    echo "build_status=NOT_REACHED"
    echo "cargo_exit_code=NOT_REACHED"
    echo "failure_stage=NOT_REACHED"
    echo "END_SCHEMA_BLOCK"
  } > "${EVIDENCE}/BUILD_EXIT_CODE.txt"

  {
    echo "BEGIN_SCHEMA_BLOCK BUILD_TIMING"
    echo "evidence_schema_version=${EVIDENCE_SCHEMA_VERSION}"
    echo "status=NOT_REACHED"
    echo "outcome=NOT_REACHED"
    echo "docker_started_utc=NOT_REACHED"
    echo "docker_finished_utc=NOT_REACHED"
    echo "docker_elapsed_seconds=NOT_REACHED"
    echo "cargo_started_utc=NOT_REACHED"
    echo "cargo_finished_utc=NOT_REACHED"
    echo "cargo_elapsed_seconds=NOT_REACHED"
    echo "cargo_started=NO"
    echo "cargo_exit_code=NOT_REACHED"
    echo "docker_exit_code=NOT_REACHED"
    echo "failure_stage=NOT_REACHED"
    echo "END_SCHEMA_BLOCK"
  } > "${EVIDENCE}/BUILD_TIMING.txt"

  {
    echo "evidence_schema_version=${EVIDENCE_SCHEMA_VERSION}"
    echo "status=NOT_REACHED"
  } > "${EVIDENCE}/BOOTSTRAP.txt"

  # Preserve host-prewritten CLEAN_TARGET host fields when present.
  local existing="${EVIDENCE}/CLEAN_TARGET_PROOF.txt"
  if [[ -f "${existing}" ]]; then
    CT_TARGET_PATH_HOST="$(read_kv "${existing}" "target_path_host" "")"
    if [[ -z "${CT_TARGET_PATH_HOST}" || "${CT_TARGET_PATH_HOST}" == "NOT_REACHED" ]]; then
      CT_TARGET_PATH_HOST="$(read_kv "${existing}" "cargo_target_dir_absolute" "NOT_REACHED")"
    fi
    CT_PROOF_UTC_HOST="$(read_kv "${existing}" "proof_utc_host" "")"
    if [[ -z "${CT_PROOF_UTC_HOST}" || "${CT_PROOF_UTC_HOST}" == "NOT_REACHED" ]]; then
      CT_PROOF_UTC_HOST="$(read_kv "${existing}" "creation_utc" "NOT_REACHED")"
    fi
    CT_OBS_HOST="$(read_kv "${existing}" "observed_entry_count_host" "")"
    if [[ -z "${CT_OBS_HOST}" || "${CT_OBS_HOST}" == "NOT_REACHED" ]]; then
      # Legacy host key (ambiguous); treat as host-scoped when container has not yet written.
      CT_OBS_HOST="$(read_kv "${existing}" "observed_entry_count" "NOT_REACHED")"
    fi
  fi
  CT_STATUS="pending"
  CT_OUTCOME="NOT_REACHED"
  CT_TARGET_PREBOOT="NOT_REACHED"
  CT_UTC_PREBOOT="NOT_REACHED"
  CT_OBS_PREBOOT="NOT_REACHED"
  CT_TARGET_PRECARGO="NOT_REACHED"
  CT_UTC_PRECARGO="NOT_REACHED"
  CT_OBS_CONTAINER="NOT_REACHED"
  CT_PROOF_FAILED="no"
  CT_FAILURE_STAGE="NOT_REACHED"
  CT_LISTINGS=""
  flush_clean_target_proof

  {
    echo "evidence_schema_version=${EVIDENCE_SCHEMA_VERSION}"
    echo "status=NOT_REACHED"
    echo "exact_build_command=${CANONICAL_BUILD_CMD}"
    echo "cargo_incremental=0"
    echo "working_directory=/src"
    echo "product_executed=NO"
  } > "${EVIDENCE}/BUILD_COMMAND.txt"

  {
    echo "BEGIN_SCHEMA_BLOCK BUILD_ENVIRONMENT"
    echo "evidence_schema_version=${EVIDENCE_SCHEMA_VERSION}"
    echo "status=NOT_REACHED"
    echo "outcome=NOT_REACHED"
    echo "docker_platform=linux/amd64"
    echo "network_mode=bridge"
    echo "rust_image=${RUST_IMAGE}"
    echo "workdir=/src"
    echo "home=${HOME}"
    echo "cargo_home=${CARGO_HOME}"
    echo "cargo_target_dir=${CARGO_TARGET_DIR_GROK}"
    echo "bootstrap_cargo_target_dir=${BOOTSTRAP_CARGO_TARGET_DIR}"
    echo "cargo_incremental=0"
    echo "dotslash_cache=${DOTSLASH_CACHE}"
    echo "path=NOT_REACHED"
    echo "grok_build_commit=${GROK_BUILD_COMMIT}"
    echo "expected_cargo_lock_sha256=${EXPECTED_CARGO_LOCK_SHA256}"
    echo "canonical_build_command=${CANONICAL_BUILD_CMD}"
    echo "mount_src=/src:ro"
    echo "mount_work=broad_WORK_ROOT_mount_prohibited"
    echo "mount_evidence=/evidence:rw"
    echo "mount_container_script=/witness/container_narrow_build.sh:ro"
    echo "END_SCHEMA_BLOCK"
  } > "${EVIDENCE}/BUILD_ENVIRONMENT.txt"

  write_no_artifact_evidence "container run in progress; artifact not yet built" "no" "BUILD_NOT_STARTED"
}

# --- Failure handlers --------------------------------------------------------

# BUILD_NOT_STARTED: any failure strictly before `cargo build` is invoked.
fail_build_not_started() {
  local stage="$1"
  local exit_code="${2:-1}"
  EVIDENCE_FINALIZED="YES"
  CT_STATUS="FAILED"
  CT_OUTCOME="BUILD_NOT_STARTED"
  if [[ "${CT_PROOF_FAILED}" != "yes" ]]; then
    CT_FAILURE_STAGE="${stage}"
  fi
  flush_clean_target_proof
  write_outcome_evidence \
    "BUILD_NOT_STARTED" "NO" "BUILD_NOT_STARTED" "NOT_APPLICABLE" \
    "${exit_code}" "${stage}" "FAILED" \
    "NOT_APPLICABLE" "NOT_APPLICABLE" "NOT_APPLICABLE"
  write_no_artifact_evidence "cargo never started (failing_stage=${stage})" "no" "BUILD_NOT_STARTED"
  echo "BUILD_NOT_STARTED: failing_stage=${stage} exit_code=${exit_code}" >&2
  exit "${exit_code}"
}

# INFRASTRUCTURE_FAILURE: generic catch-all via ERR trap.
fail_infrastructure() {
  local stage="$1"
  local exit_code="${2:-1}"
  EVIDENCE_FINALIZED="YES"
  local cargo_exit_field="NOT_APPLICABLE"
  local cargo_started_utc="NOT_APPLICABLE"
  local cargo_finished_utc="NOT_APPLICABLE"
  local cargo_elapsed="NOT_APPLICABLE"
  if [[ -n "${CARGO_EXIT_CODE}" ]]; then
    cargo_exit_field="${CARGO_EXIT_CODE}"
  fi
  if [[ "${CARGO_STARTED}" == "YES" ]]; then
    cargo_started_utc="${CARGO_START_UTC:-NOT_APPLICABLE}"
    cargo_finished_utc="$(ts)"
    cargo_elapsed="${CARGO_ELAPSED_SECONDS:-NOT_APPLICABLE}"
  fi
  CT_STATUS="FAILED"
  CT_OUTCOME="INFRASTRUCTURE_FAILURE"
  CT_FAILURE_STAGE="${stage}"
  flush_clean_target_proof
  write_outcome_evidence \
    "INFRASTRUCTURE_FAILURE" "${CARGO_STARTED}" "INFRASTRUCTURE_FAILURE" "${cargo_exit_field}" \
    "${exit_code}" "${stage}" "FAILED" \
    "${cargo_started_utc}" "${cargo_finished_utc}" "${cargo_elapsed}"
  if [[ "${CARGO_STARTED}" == "YES" ]]; then
    write_artifact_evidence_best_effort "${stage}"
  else
    write_no_artifact_evidence "unexpected infrastructure failure at stage=${stage}; cargo never started" "no" "INFRASTRUCTURE_FAILURE"
  fi
  echo "INFRASTRUCTURE_FAILURE: stage=${stage} exit_code=${exit_code}" >&2
  exit "${exit_code}"
}

on_err() {
  local ec=$?
  if [[ "${EVIDENCE_FINALIZED}" == "YES" ]]; then
    exit "${ec}"
  fi
  echo "ERROR: container script failed unexpectedly at line ${BASH_LINENO[0]} (exit ${ec}) during stage=${CURRENT_STAGE}" >&2
  fail_infrastructure "${CURRENT_STAGE}" "${ec}"
}
trap on_err ERR

record_build_environment() {
  {
    echo "BEGIN_SCHEMA_BLOCK BUILD_ENVIRONMENT"
    echo "evidence_schema_version=${EVIDENCE_SCHEMA_VERSION}"
    echo "status=OK"
    echo "outcome=RECORDED"
    echo "docker_platform=linux/amd64"
    echo "network_mode=bridge"
    echo "rust_image=${RUST_IMAGE}"
    echo "workdir=/src"
    echo "home=${HOME}"
    echo "cargo_home=${CARGO_HOME}"
    echo "cargo_target_dir=${CARGO_TARGET_DIR_GROK}"
    echo "bootstrap_cargo_target_dir=${BOOTSTRAP_CARGO_TARGET_DIR}"
    echo "cargo_incremental=0"
    echo "dotslash_cache=${DOTSLASH_CACHE}"
    echo "path=${PATH}"
    echo "grok_build_commit=${GROK_BUILD_COMMIT}"
    echo "expected_cargo_lock_sha256=${EXPECTED_CARGO_LOCK_SHA256}"
    echo "canonical_build_command=${CANONICAL_BUILD_CMD}"
    echo "mount_src=/src:ro"
    echo "mount_work=broad_WORK_ROOT_mount_prohibited"
    echo "mount_evidence=/evidence:rw"
    echo "mount_container_script=/witness/container_narrow_build.sh:ro"
    echo "END_SCHEMA_BLOCK"
  } > "${EVIDENCE}/BUILD_ENVIRONMENT.txt"
}

# --- Begin execution ---------------------------------------------------------

set_stage "directory_setup"
mkdir -p "${BOOTSTRAP_DIR}" "${CARGO_HOME}" "${CARGO_TARGET_DIR_GROK}" "${BOOTSTRAP_CARGO_TARGET_DIR}" "${DOTSLASH_CACHE}" "${HOME}"

set_stage "evidence_init"
init_evidence

if [[ -n "${RUSTUP_HOME:-}" ]]; then
  echo "RUSTUP_HOME is set in container env: ${RUSTUP_HOME} (not overridden by Witness script)" >> "${EVIDENCE}/ENVIRONMENT.txt"
fi

# Empty Grok Build target proof inside container (immediate pre-bootstrap).
set_stage "pre_bootstrap_empty_target"
CT_TARGET_PREBOOT="${CARGO_TARGET_DIR_GROK}"
CT_UTC_PREBOOT="$(ts)"
TARGET_COUNT="$(append_clean_target_listing "container_pre_bootstrap_grok_target" "${CARGO_TARGET_DIR_GROK}")"
CT_OBS_PREBOOT="${TARGET_COUNT}"
if [[ "${TARGET_COUNT}" != "0" ]]; then
  CT_PROOF_FAILED="yes"
  CT_FAILURE_STAGE="pre_bootstrap_empty_target"
  CT_STATUS="FAILED"
  CT_OUTCOME="BUILD_NOT_STARTED"
  flush_clean_target_proof
  echo "container Grok Build target not empty before bootstrap" >&2
  fail_build_not_started "pre_bootstrap_empty_target"
fi
flush_clean_target_proof

export DEBIAN_FRONTEND=noninteractive
export CARGO_HOME DOTSLASH_CACHE HOME
export CARGO_INCREMENTAL=0

# --- Rustc / Cargo toolchain identity validation (required; no || true) ----

set_stage "rustc_version_probe"
if RUSTC_RAW="$(rustc --version 2>&1)"; then
  RUSTC_PROBE_EC=0
else
  RUSTC_PROBE_EC=$?
fi
if [[ "${RUSTC_PROBE_EC}" -ne 0 ]]; then
  echo "rustc --version probe failed (exit ${RUSTC_PROBE_EC})" >&2
  fail_build_not_started "rustc_version_probe"
fi
RUSTC_OBSERVED_VERSION="$(printf '%s\n' "${RUSTC_RAW}" | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -n1)"

set_stage "rustc_version_validation"
if [[ "${RUSTC_OBSERVED_VERSION}" != "${EXPECTED_RUSTC_VERSION}" ]]; then
  echo "rustc version mismatch: observed=${RUSTC_OBSERVED_VERSION:-UNPARSEABLE} expected=${EXPECTED_RUSTC_VERSION}" >&2
  {
    echo "# --- rustc (version mismatch) ---"
    echo "# rustc_raw=${RUSTC_RAW}"
    echo "# rustc_observed_version=${RUSTC_OBSERVED_VERSION:-UNPARSEABLE}"
    echo "# rustc_expected_version=${EXPECTED_RUSTC_VERSION}"
    echo "# rustc_version_match=NO"
  } >> "${EVIDENCE}/ENVIRONMENT.txt"
  fail_build_not_started "rustc_version_mismatch"
fi

set_stage "cargo_version_probe"
if CARGO_RAW="$(cargo --version 2>&1)"; then
  CARGO_PROBE_EC=0
else
  CARGO_PROBE_EC=$?
fi
if [[ "${CARGO_PROBE_EC}" -ne 0 ]]; then
  echo "cargo --version probe failed (exit ${CARGO_PROBE_EC})" >&2
  fail_build_not_started "cargo_version_probe"
fi
CARGO_OBSERVED_VERSION="$(printf '%s\n' "${CARGO_RAW}" | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -n1)"

set_stage "cargo_version_validation"
if [[ "${CARGO_OBSERVED_VERSION}" != "${EXPECTED_CARGO_VERSION}" ]]; then
  echo "cargo version mismatch: observed=${CARGO_OBSERVED_VERSION:-UNPARSEABLE} expected=${EXPECTED_CARGO_VERSION}" >&2
  {
    echo "# --- cargo (version mismatch) ---"
    echo "# cargo_raw=${CARGO_RAW}"
    echo "# cargo_observed_version=${CARGO_OBSERVED_VERSION:-UNPARSEABLE}"
    echo "# cargo_expected_version=${EXPECTED_CARGO_VERSION}"
    echo "# cargo_version_match=NO"
  } >> "${EVIDENCE}/ENVIRONMENT.txt"
  fail_build_not_started "cargo_version_mismatch"
fi

CONTAINER_OS_RELEASE="$( ( . /etc/os-release 2>/dev/null && printf '%s' "${PRETTY_NAME:-UNKNOWN}" ) || echo UNKNOWN )"
CONTAINER_UNAME="$(uname -sr 2>/dev/null || echo UNKNOWN)"
{
  echo "# --- container-appended toolchain facts (validated) ---"
  echo "# rustc_raw=${RUSTC_RAW}"
  echo "# cargo_raw=${CARGO_RAW}"
  echo "BEGIN_SCHEMA_BLOCK ENVIRONMENT"
  echo "container_os_release=${CONTAINER_OS_RELEASE}"
  echo "container_uname=${CONTAINER_UNAME}"
  echo "rustc_version=${RUSTC_OBSERVED_VERSION}"
  echo "cargo_version=${CARGO_OBSERVED_VERSION}"
  echo "END_SCHEMA_BLOCK"
  echo "# rustc_expected_version=${EXPECTED_RUSTC_VERSION}"
  echo "# rustc_version_match=YES"
  echo "# cargo_expected_version=${EXPECTED_CARGO_VERSION}"
  echo "# cargo_version_match=YES"
} >> "${EVIDENCE}/ENVIRONMENT.txt"

# --- Bootstrap: apt packages (versions unpinned; record as limitation) ------

APT_PACKAGES=(
  ca-certificates
  git
  build-essential
  pkg-config
  cmake
  curl
  perl
  file
  binutils
)

set_stage "apt_get_update"
if ! apt-get update > "${BOOTSTRAP_DIR}/apt-get-update.log" 2>&1; then
  echo "apt-get update failed; see ${BOOTSTRAP_DIR}/apt-get-update.log" >&2
  fail_build_not_started "apt_get_update"
fi

set_stage "apt_get_install"
if ! apt-get install -y --no-install-recommends "${APT_PACKAGES[@]}" > "${BOOTSTRAP_DIR}/apt-get-install.log" 2>&1; then
  echo "apt-get install failed; see ${BOOTSTRAP_DIR}/apt-get-install.log" >&2
  fail_build_not_started "apt_get_install"
fi

{
  echo "evidence_schema_version=${EVIDENCE_SCHEMA_VERSION}"
  echo "bootstrap_cargo_target_dir=${BOOTSTRAP_CARGO_TARGET_DIR}"
  echo "grok_build_cargo_target_dir=${CARGO_TARGET_DIR_GROK}"
  echo "apt_packages=${APT_PACKAGES[*]}"
  echo "apt_versions_unpinned_limitation=yes"
  echo "apt_update_command=apt-get update"
  echo "apt_install_command=apt-get install -y --no-install-recommends ${APT_PACKAGES[*]}"
  echo "--- apt policy (unpinned; dpkg-query, best-effort) ---"
  dpkg-query -W -f='${Package} ${Version}\n' "${APT_PACKAGES[@]}" 2>/dev/null || true
} > "${EVIDENCE}/BOOTSTRAP.txt"

# --- DotSlash: exact pinned install command, isolated bootstrap target only -

set_stage "dotslash_install"
if CARGO_TARGET_DIR="${BOOTSTRAP_CARGO_TARGET_DIR}" cargo install dotslash --version "${EXPECTED_DOTSLASH_VERSION}" --locked > "${BOOTSTRAP_DIR}/dotslash-install.log" 2>&1; then
  DOTSLASH_INSTALL_EC=0
else
  DOTSLASH_INSTALL_EC=$?
fi
{
  echo "dotslash_install_command=cargo install dotslash --version ${EXPECTED_DOTSLASH_VERSION} --locked"
  echo "dotslash_install_cargo_target_dir=${BOOTSTRAP_CARGO_TARGET_DIR}"
  echo "dotslash_install_exit_code=${DOTSLASH_INSTALL_EC}"
} >> "${EVIDENCE}/BOOTSTRAP.txt"
if [[ "${DOTSLASH_INSTALL_EC}" -ne 0 ]]; then
  echo "DotSlash install failed; see ${BOOTSTRAP_DIR}/dotslash-install.log" >&2
  fail_build_not_started "dotslash_install"
fi

DOTSLASH_BIN="${CARGO_HOME}/bin/dotslash"

set_stage "dotslash_version_probe"
if DOTSLASH_VERSION_RAW="$("${DOTSLASH_BIN}" --version 2>&1)"; then
  DOTSLASH_PROBE_EC=0
else
  DOTSLASH_PROBE_EC=$?
fi
if [[ "${DOTSLASH_PROBE_EC}" -ne 0 ]]; then
  {
    echo "dotslash_binary_path=${DOTSLASH_BIN}"
    echo "--- dotslash --version (required probe FAILED) ---"
    echo "${DOTSLASH_VERSION_RAW:-<no output>}"
    echo "dotslash_version_probe_exit_code=${DOTSLASH_PROBE_EC}"
  } >> "${EVIDENCE}/BOOTSTRAP.txt"
  echo "DotSlash version probe failed (exit ${DOTSLASH_PROBE_EC})" >&2
  fail_build_not_started "dotslash_version_probe"
fi
DOTSLASH_OBSERVED_VERSION="$(printf '%s\n' "${DOTSLASH_VERSION_RAW}" | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -n1)"

set_stage "dotslash_version_validation"
{
  echo "dotslash_binary_path=${DOTSLASH_BIN}"
  echo "--- dotslash --version (required probe) ---"
  echo "${DOTSLASH_VERSION_RAW}"
  echo "dotslash_expected_version=${EXPECTED_DOTSLASH_VERSION}"
  echo "dotslash_observed_version=${DOTSLASH_OBSERVED_VERSION:-UNPARSEABLE}"
  echo "dotslash_version_match=$([[ "${DOTSLASH_OBSERVED_VERSION}" == "${EXPECTED_DOTSLASH_VERSION}" ]] && echo YES || echo NO)"
} >> "${EVIDENCE}/BOOTSTRAP.txt"
if [[ "${DOTSLASH_OBSERVED_VERSION}" != "${EXPECTED_DOTSLASH_VERSION}" ]]; then
  echo "DotSlash version mismatch: observed=${DOTSLASH_OBSERVED_VERSION:-UNPARSEABLE} expected=${EXPECTED_DOTSLASH_VERSION}" >&2
  fail_build_not_started "dotslash_version_mismatch"
fi

export PATH="${CARGO_HOME}/bin:${PATH}"

# --- Protoc: LF-normalized writable copy of read-only descriptor -----------

set_stage "protoc_descriptor_missing"
if [[ ! -f "${PROTOC_DESCRIPTOR_SRC}" ]]; then
  echo "Protoc descriptor missing at ${PROTOC_DESCRIPTOR_SRC}" >&2
  fail_build_not_started "protoc_descriptor_missing"
fi

set_stage "protoc_normalize"
sed 's/\r$//' "${PROTOC_DESCRIPTOR_SRC}" > "${PROTOC_DESCRIPTOR_WR}"
chmod +x "${PROTOC_DESCRIPTOR_WR}"
ORIG_SHA="$(sha256sum "${PROTOC_DESCRIPTOR_SRC}" | awk '{print $1}')"
NORM_SHA="$(sha256sum "${PROTOC_DESCRIPTOR_WR}" | awk '{print $1}')"
export PROTOC="${PROTOC_DESCRIPTOR_WR}"

{
  echo "protoc_descriptor_src=${PROTOC_DESCRIPTOR_SRC}"
  echo "protoc_descriptor_writable=${PROTOC_DESCRIPTOR_WR}"
  echo "protoc_descriptor_src_sha256=${ORIG_SHA}"
  echo "protoc_descriptor_lf_sha256=${NORM_SHA}"
  echo "PROTOC=${PROTOC}"
  echo "--- protoc --version via writable descriptor (non-product; required probe) ---"
} >> "${EVIDENCE}/BOOTSTRAP.txt"

# Capture protoc version to bootstrap dir / shell var — NEVER under EVIDENCE_DIR.
set_stage "protoc_version_probe"
PROTOC_VERSION_RAW=""
PROTOC_VER_EXIT=0
set +e
PROTOC_VERSION_RAW="$("${PROTOC}" --version 2>&1)"
PROTOC_VER_EXIT=$?
set -e
# Optional auxiliary under /work/bootstrap/ only (not EVIDENCE_DIR).
printf '%s\n' "${PROTOC_VERSION_RAW}" > "${BOOTSTRAP_DIR}/protoc-version.raw"
{
  echo "protoc_version_output=$(escape_oneline "${PROTOC_VERSION_RAW}")"
  echo "protoc_version_exit_code=${PROTOC_VER_EXIT}"
} >> "${EVIDENCE}/BOOTSTRAP.txt"

if [[ "${PROTOC_VER_EXIT}" -ne 0 ]]; then
  echo "protoc version probe failed (exit ${PROTOC_VER_EXIT})" >&2
  fail_build_not_started "protoc_version_probe"
fi

echo "status=bootstrap_complete" >> "${EVIDENCE}/BOOTSTRAP.txt"

# Grok Build operations use /work/cargo-target only (never bootstrap target).
export CARGO_TARGET_DIR="${CARGO_TARGET_DIR_GROK}"

set_stage "record_build_environment"
record_build_environment

set_stage "record_os_identity"
{
  echo "--- uname ---"
  uname -a
  echo "--- os-release ---"
  cat /etc/os-release 2>/dev/null || true
} >> "${EVIDENCE}/ENVIRONMENT.txt" 2>&1 || true

# --- Source identity: commit pin and Cargo.lock hash (hard-fail closed) ----

set_stage "source_identity_check"
SRC_HEAD="$(git -C /src rev-parse HEAD)"
LOCK_SHA="$(sha256sum /src/Cargo.lock | awk '{print $1}')"
{
  echo "evidence_schema_version=${EVIDENCE_SCHEMA_VERSION}"
  echo "grok_build_commit_observed=${SRC_HEAD}"
  echo "grok_build_commit_expected=${GROK_BUILD_COMMIT}"
  echo "cargo_lock_sha256_observed=${LOCK_SHA}"
  echo "cargo_lock_sha256_expected=${EXPECTED_CARGO_LOCK_SHA256}"
  echo "commit_match=$([[ "${SRC_HEAD}" == "${GROK_BUILD_COMMIT}" ]] && echo YES || echo NO)"
  echo "cargo_lock_sha256_match=$([[ "${LOCK_SHA}" == "${EXPECTED_CARGO_LOCK_SHA256}" ]] && echo YES || echo NO)"
} > "${EVIDENCE}/SOURCE_IDENTITY.txt"

if [[ "${SRC_HEAD}" != "${GROK_BUILD_COMMIT}" ]]; then
  echo "Source commit mismatch: observed=${SRC_HEAD} expected=${GROK_BUILD_COMMIT}" >&2
  fail_build_not_started "source_commit_mismatch"
fi
if [[ "${LOCK_SHA}" != "${EXPECTED_CARGO_LOCK_SHA256}" ]]; then
  echo "Cargo.lock SHA-256 mismatch: observed=${LOCK_SHA} expected=${EXPECTED_CARGO_LOCK_SHA256}" >&2
  fail_build_not_started "cargo_lock_sha256_mismatch"
fi

{
  echo "evidence_schema_version=${EVIDENCE_SCHEMA_VERSION}"
  echo "exact_build_command=${CANONICAL_BUILD_CMD}"
  echo "cargo_incremental=0"
  echo "cargo_fetch_separate_step=OMITTED (deps acquired during locked build; fresh CARGO_HOME)"
  echo "working_directory=/src"
  echo "product_executed=NO"
  echo "status=RECORDED"
} > "${EVIDENCE}/BUILD_COMMAND.txt"

# Immediate pre-build empty Grok Build target recheck (required before cargo build).
set_stage "pre_cargo_empty_target"
CT_TARGET_PRECARGO="${CARGO_TARGET_DIR_GROK}"
CT_UTC_PRECARGO="$(ts)"
TARGET_COUNT="$(append_clean_target_listing "container_immediate_pre_cargo_grok_target" "${CARGO_TARGET_DIR_GROK}")"
CT_OBS_CONTAINER="${TARGET_COUNT}"
if [[ "${TARGET_COUNT}" != "0" ]]; then
  CT_PROOF_FAILED="yes"
  CT_FAILURE_STAGE="pre_cargo_empty_target"
  CT_STATUS="FAILED"
  CT_OUTCOME="BUILD_NOT_STARTED"
  flush_clean_target_proof
  echo "container Grok Build target not empty immediately before cargo build" >&2
  fail_build_not_started "pre_cargo_empty_target"
fi
CT_STATUS="OK"
CT_OUTCOME="CLEAN_TARGET_VERIFIED"
CT_FAILURE_STAGE="NOT_APPLICABLE"
flush_clean_target_proof

# --- Cargo build (the only fallible step permitted to proceed past this) ---

set_stage "cargo_build"
CARGO_STARTED="YES"
CARGO_START_UTC="$(ts)"
CARGO_START_SEC="$(date +%s)"

set +e
( cd /src && bash -c "${CANONICAL_BUILD_CMD}" ) > "${EVIDENCE}/BUILD_STDOUT.txt" 2> "${EVIDENCE}/BUILD_STDERR.txt"
CARGO_EXIT_CODE=$?
set -e

CARGO_END_UTC="$(ts)"
CARGO_END_SEC="$(date +%s)"
CARGO_ELAPSED_SECONDS=$((CARGO_END_SEC - CARGO_START_SEC))

# --- Outcome classification --------------------------------------------------

set_stage "post_cargo_classification"

if [[ "${CARGO_EXIT_CODE}" -ne 0 ]]; then
  EVIDENCE_FINALIZED="YES"
  write_outcome_evidence \
    "CARGO_FAILED" "YES" "FAILED" "${CARGO_EXIT_CODE}" \
    "${CARGO_EXIT_CODE}" "cargo_build" "FAILED" \
    "${CARGO_START_UTC}" "${CARGO_END_UTC}" "${CARGO_ELAPSED_SECONDS}"
  write_no_artifact_evidence "cargo build exited nonzero (${CARGO_EXIT_CODE})" "no" "CARGO_FAILED"
  exit "${CARGO_EXIT_CODE}"
fi

set_stage "artifact_presence_check"
if [[ ! -f "${ARTIFACT}" ]]; then
  EVIDENCE_FINALIZED="YES"
  write_outcome_evidence \
    "CARGO_SUCCEEDED_ARTIFACT_MISSING" "YES" "COMPLETE" "0" \
    "${ARTIFACT_MISSING_EXIT}" "artifact_presence_check" "FAILED" \
    "${CARGO_START_UTC}" "${CARGO_END_UTC}" "${CARGO_ELAPSED_SECONDS}"
  write_no_artifact_evidence "cargo exited 0 but expected artifact ${ARTIFACT} is missing" "yes" "CARGO_SUCCEEDED_ARTIFACT_MISSING"
  echo "CARGO_SUCCEEDED_ARTIFACT_MISSING: cargo exit 0 but artifact absent at ${ARTIFACT}" >&2
  exit "${ARTIFACT_MISSING_EXIT}"
fi

# --- Required static inspection (artifact present only; no || true) --------
# Product execution and ldd remain PROHIBITED below and everywhere else.
# Multiline outputs are escaped to single-line values (\n). Per-tool keys only
# (no repeated generic command=/exit_code=).

set_stage "static_artifact_inspection"

SHA256_CMD="sha256sum ${ARTIFACT}"
STAT_CMD="stat ${ARTIFACT}"
FILE_CMD="file ${ARTIFACT}"
READELF_H_CMD="readelf -h ${ARTIFACT}"
READELF_N_CMD="readelf -n ${ARTIFACT}"
READELF_D_CMD="readelf -d ${ARTIFACT}"
OBJDUMP_F_CMD="objdump -f ${ARTIFACT}"

if SHA256_OUT="$(sha256sum "${ARTIFACT}" 2>&1)"; then SHA256_EC=0; else SHA256_EC=$?; fi
if STAT_OUT="$(stat "${ARTIFACT}" 2>&1)"; then STAT_EC=0; else STAT_EC=$?; fi
if FILE_OUT="$(file "${ARTIFACT}" 2>&1)"; then FILE_EC=0; else FILE_EC=$?; fi
if READELF_H_OUT="$(readelf -h "${ARTIFACT}" 2>&1)"; then READELF_H_EC=0; else READELF_H_EC=$?; fi
if READELF_N_OUT="$(readelf -n "${ARTIFACT}" 2>&1)"; then READELF_N_EC=0; else READELF_N_EC=$?; fi
if READELF_D_OUT="$(readelf -d "${ARTIFACT}" 2>&1)"; then READELF_D_EC=0; else READELF_D_EC=$?; fi
if OBJDUMP_F_OUT="$(objdump -f "${ARTIFACT}" 2>&1)"; then OBJDUMP_F_EC=0; else OBJDUMP_F_EC=$?; fi

STATIC_INSPECTION_OK="YES"
INSPECTION_FAILURE_STAGE="NOT_APPLICABLE"
for pair in \
  "sha256sum:${SHA256_EC}" \
  "stat:${STAT_EC}" \
  "file:${FILE_EC}" \
  "readelf_h:${READELF_H_EC}" \
  "readelf_n:${READELF_N_EC}" \
  "readelf_d:${READELF_D_EC}" \
  "objdump_f:${OBJDUMP_F_EC}"; do
  name="${pair%%:*}"
  ec="${pair##*:}"
  if [[ "${ec}" -ne 0 ]]; then
    STATIC_INSPECTION_OK="NO"
    if [[ "${INSPECTION_FAILURE_STAGE}" == "NOT_APPLICABLE" ]]; then
      INSPECTION_FAILURE_STAGE="static_${name}"
    fi
  fi
done

if [[ "${STATIC_INSPECTION_OK}" == "YES" ]]; then
  STATIC_STATUS="OK"
  INSPECTION_COMPLETE="yes"
  INSPECTION_REASON="all required static inspection commands succeeded"
else
  STATIC_STATUS="FAILED"
  INSPECTION_COMPLETE="no"
  INSPECTION_REASON="one or more required static inspection commands failed; outcome remains CARGO_SUCCEEDED_ARTIFACT_PRESENT; verdict ceiling PARTIAL (PASS prohibited — host/validator)"
fi

{
  echo "BEGIN_SCHEMA_BLOCK STATIC_ARTIFACT_INSPECTION"
  echo "evidence_schema_version=${EVIDENCE_SCHEMA_VERSION}"
  echo "status=${STATIC_STATUS}"
  echo "outcome=CARGO_SUCCEEDED_ARTIFACT_PRESENT"
  echo "applicable=yes"
  echo "artifact_present=yes"
  echo "artifact_path=${ARTIFACT}"
  echo "sha256sum_command=${SHA256_CMD}"
  echo "sha256sum_output=$(escape_oneline "${SHA256_OUT}")"
  echo "sha256sum_exit_code=${SHA256_EC}"
  echo "stat_command=${STAT_CMD}"
  echo "stat_output=$(escape_oneline "${STAT_OUT}")"
  echo "stat_exit_code=${STAT_EC}"
  echo "file_command=${FILE_CMD}"
  echo "file_output=$(escape_oneline "${FILE_OUT}")"
  echo "file_exit_code=${FILE_EC}"
  echo "readelf_h_command=${READELF_H_CMD}"
  echo "readelf_h_output=$(escape_oneline "${READELF_H_OUT}")"
  echo "readelf_h_exit_code=${READELF_H_EC}"
  echo "readelf_n_command=${READELF_N_CMD}"
  echo "readelf_n_output=$(escape_oneline "${READELF_N_OUT}")"
  echo "readelf_n_exit_code=${READELF_N_EC}"
  echo "readelf_d_command=${READELF_D_CMD}"
  echo "readelf_d_output=$(escape_oneline "${READELF_D_OUT}")"
  echo "readelf_d_exit_code=${READELF_D_EC}"
  echo "objdump_f_command=${OBJDUMP_F_CMD}"
  echo "objdump_f_output=$(escape_oneline "${OBJDUMP_F_OUT}")"
  echo "objdump_f_exit_code=${OBJDUMP_F_EC}"
  echo "inspection_complete=${INSPECTION_COMPLETE}"
  echo "failure_stage=${INSPECTION_FAILURE_STAGE}"
  echo "reason=${INSPECTION_REASON}"
  echo "END_SCHEMA_BLOCK"
} > "${EVIDENCE}/STATIC_ARTIFACT_INSPECTION.txt"

if [[ "${SHA256_EC}" -eq 0 ]]; then
  ART_SHA="$(printf '%s\n' "${SHA256_OUT}" | awk '{print $1}')"
else
  ART_SHA="UNAVAILABLE_COMMAND_FAILED"
fi
if [[ "${STAT_EC}" -eq 0 ]]; then
  ART_SIZE="$(printf '%s\n' "${STAT_OUT}" | grep -oE 'Size: [0-9]+' | head -n1 | awk '{print $2}')"
  [[ -z "${ART_SIZE}" ]] && ART_SIZE="UNPARSEABLE"
else
  ART_SIZE="UNAVAILABLE_COMMAND_FAILED"
fi
if [[ "${READELF_N_EC}" -eq 0 ]]; then
  GNU_BUILD_ID="$(printf '%s\n' "${READELF_N_OUT}" | grep -oE 'Build ID: [0-9a-f]+' | head -n1 | awk '{print $3}')"
  [[ -z "${GNU_BUILD_ID}" ]] && GNU_BUILD_ID="UNPARSEABLE"
else
  GNU_BUILD_ID="UNAVAILABLE_COMMAND_FAILED"
fi

{
  echo "evidence_schema_version=${EVIDENCE_SCHEMA_VERSION}"
  echo "outcome=CARGO_SUCCEEDED_ARTIFACT_PRESENT"
  echo "applicable=yes"
  echo "artifact_present=yes"
  echo "artifact_path=${ARTIFACT}"
  echo "artifact_filename=xai-grok-pager"
  echo "artifact_size_bytes=${ART_SIZE}"
  echo "artifact_sha256=${ART_SHA}"
  echo "gnu_build_id=${GNU_BUILD_ID}"
  echo "static_inspection_complete=${INSPECTION_COMPLETE}"
  echo "product_executed=NO"
  echo "ldd_used=NO"
} > "${EVIDENCE}/ARTIFACT_IDENTITY.txt"

EVIDENCE_FINALIZED="YES"
if [[ "${STATIC_INSPECTION_OK}" == "YES" ]]; then
  FINAL_EXIT=0
  EXIT_STATUS="OK"
  EXIT_FAILURE_STAGE="NOT_APPLICABLE"
else
  FINAL_EXIT="${STATIC_INSPECTION_INCOMPLETE_EXIT}"
  EXIT_STATUS="FAILED"
  EXIT_FAILURE_STAGE="${INSPECTION_FAILURE_STAGE}"
  echo "One or more required static inspection commands failed; inspection_complete=no; outcome=CARGO_SUCCEEDED_ARTIFACT_PRESENT; exit=${FINAL_EXIT}; verdict ceiling PARTIAL (PASS prohibited)." >&2
fi

write_outcome_evidence \
  "CARGO_SUCCEEDED_ARTIFACT_PRESENT" "YES" "COMPLETE" "0" \
  "${FINAL_EXIT}" "${EXIT_FAILURE_STAGE}" "${EXIT_STATUS}" \
  "${CARGO_START_UTC}" "${CARGO_END_UTC}" "${CARGO_ELAPSED_SECONDS}"

# Container exits with the classified status (Docker preserves it on host).
exit "${FINAL_EXIT}"
