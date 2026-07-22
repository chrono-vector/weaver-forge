#!/usr/bin/env bash
# In-container narrow build — Grok Build xai-grok-pager-bin only.
#
# C2E-4 rewrite. Implements an explicit outcome model (BUILD_NOT_STARTED /
# CARGO_FAILED / CARGO_SUCCEEDED_ARTIFACT_MISSING /
# CARGO_SUCCEEDED_ARTIFACT_PRESENT / INFRASTRUCTURE_FAILURE), hard-fails
# required identity/toolchain/version probes (no `|| true` masking), keeps
# the bootstrap-vs-grok Cargo target separation, and guarantees every
# required evidence file exists and is truthful on every exit path.
#
# Prohibited unconditionally, in this script and in every code path below:
# executing the built product, and running `ldd` against it.
set -Eeuo pipefail

# --- Identity expectations (env override; defaults match host canonical) ---
GROK_BUILD_COMMIT="${GROK_BUILD_COMMIT:-98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce}"
EXPECTED_CARGO_LOCK_SHA256="${EXPECTED_CARGO_LOCK_SHA256:-1512bb4fef0c1166c6a15a3398da9593903be1759b759ce78d9958913e61b421}"
CANONICAL_BUILD_CMD="${CANONICAL_BUILD_CMD:-cargo build -p xai-grok-pager-bin --locked}"
EXPECTED_RUSTC_VERSION="${EXPECTED_RUSTC_VERSION:-1.92.0}"
EXPECTED_CARGO_VERSION="${EXPECTED_CARGO_VERSION:-1.92.0}"
EXPECTED_DOTSLASH_VERSION="${EXPECTED_DOTSLASH_VERSION:-0.5.7}"

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
BUILD_START_UTC=""
BUILD_END_UTC=""

ts() { date -u +%Y-%m-%dT%H:%M:%SZ; }

set_stage() { CURRENT_STAGE="$1"; }

# --- Evidence writers -------------------------------------------------------

# Writes BUILD_EXIT_CODE.txt and BUILD_TIMING.txt as labelled fields (never
# bare numbers). This is the single place both files are produced, so every
# terminal path (success or failure) stays consistent.
write_outcome_evidence() {
  local outcome="$1" cargo_started="$2" build_status="$3" cargo_exit_code="$4"
  local docker_propagated_exit="$5" failure_stage="$6" verdict_ceiling="$7"
  local utc_start="$8" utc_end="$9" elapsed_seconds="${10}"

  {
    echo "evidence_schema_version=${EVIDENCE_SCHEMA_VERSION}"
    echo "outcome=${outcome}"
    echo "cargo_started=${cargo_started}"
    echo "build_status=${build_status}"
    echo "cargo_exit_code=${cargo_exit_code}"
    echo "docker_propagated_exit=${docker_propagated_exit}"
    echo "failure_stage=${failure_stage}"
    echo "verdict_ceiling=${verdict_ceiling}"
    echo "canonical_build_command=${CANONICAL_BUILD_CMD}"
    echo "record_utc=$(ts)"
  } > "${EVIDENCE}/BUILD_EXIT_CODE.txt"

  {
    echo "evidence_schema_version=${EVIDENCE_SCHEMA_VERSION}"
    echo "utc_start=${utc_start}"
    echo "utc_end=${utc_end}"
    echo "elapsed_seconds=${elapsed_seconds}"
    echo "exact_build_command=${CANONICAL_BUILD_CMD}"
    echo "cargo_exit_code=${cargo_exit_code}"
    echo "outcome=${outcome}"
    echo "docker_propagated_exit=${docker_propagated_exit}"
  } > "${EVIDENCE}/BUILD_TIMING.txt"
}

# Truthful "no artifact" ARTIFACT_IDENTITY.txt / STATIC_ARTIFACT_INSPECTION.txt.
write_no_artifact_evidence() {
  local reason="$1"
  {
    echo "evidence_schema_version=${EVIDENCE_SCHEMA_VERSION}"
    echo "applicable=no"
    echo "artifact_present=no"
    echo "reason=${reason}"
    echo "product_executed=NO"
    echo "ldd_used=NO"
  } > "${EVIDENCE}/ARTIFACT_IDENTITY.txt"
  {
    echo "evidence_schema_version=${EVIDENCE_SCHEMA_VERSION}"
    echo "inspection_applicable=no"
    echo "artifact_present=no"
    echo "reason=${reason}"
    echo "static_inspection_complete=no"
    echo "product_executed=NO"
    echo "ldd_used=NO"
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
      echo "evidence_schema_version=${EVIDENCE_SCHEMA_VERSION}"
      echo "inspection_applicable=yes"
      echo "artifact_present=yes"
      echo "static_inspection_complete=no"
      echo "reason=unexpected script failure at stage=${stage} before static inspection completed"
      echo "product_executed=NO"
      echo "ldd_used=NO"
    } > "${EVIDENCE}/STATIC_ARTIFACT_INSPECTION.txt"
  else
    write_no_artifact_evidence "unexpected script failure at stage=${stage}; artifact not present at check time"
  fi
}

# Empty-target proof, appended to CLEAN_TARGET_PROOF.txt. Returns observed
# entry count on stdout.
append_clean_target_proof() {
  local label="$1"
  local target_dir="$2"
  local count listing find_out
  count="$(find "${target_dir}" -mindepth 1 2>/dev/null | wc -l | tr -d ' ')"
  listing="$(ls -la "${target_dir}" 2>&1 || true)"
  find_out="$(find "${target_dir}" -mindepth 1 -print 2>/dev/null || true)"
  {
    echo "--- ${label} ---"
    echo "cargo_target_dir_absolute=${target_dir}"
    echo "check_utc=$(ts)"
    echo "required_entry_count=0"
    echo "observed_entry_count=${count}"
    echo "--- ls -la ---"
    echo "${listing}"
    echo "--- find ---"
    echo "${find_out}"
  } >> "${EVIDENCE}/CLEAN_TARGET_PROOF.txt"
  echo "${count}"
}

# Pre-populates every container-owned evidence file with truthful, non-empty
# "run in progress" content before any fallible operation executes, so a
# required file is never missing even if the very first real step fails.
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
    echo "evidence_schema_version=${EVIDENCE_SCHEMA_VERSION}"
    echo "status=pending"
    echo "note=container run started at $(ts); overwritten on completion or failure"
  } > "${EVIDENCE}/BUILD_EXIT_CODE.txt"

  {
    echo "evidence_schema_version=${EVIDENCE_SCHEMA_VERSION}"
    echo "status=pending"
    echo "utc_start=$(ts)"
  } > "${EVIDENCE}/BUILD_TIMING.txt"

  {
    echo "evidence_schema_version=${EVIDENCE_SCHEMA_VERSION}"
    echo "status=pending"
  } > "${EVIDENCE}/BOOTSTRAP.txt"

  {
    echo "evidence_schema_version=${EVIDENCE_SCHEMA_VERSION}"
    echo "cargo_target_dir_absolute=${CARGO_TARGET_DIR_GROK}"
    echo "status=pending"
  } > "${EVIDENCE}/CLEAN_TARGET_PROOF.txt"

  {
    echo "evidence_schema_version=${EVIDENCE_SCHEMA_VERSION}"
    echo "status=pending"
  } > "${EVIDENCE}/BUILD_COMMAND.txt"

  {
    echo "evidence_schema_version=${EVIDENCE_SCHEMA_VERSION}"
    echo "status=pending"
  } > "${EVIDENCE}/BUILD_ENVIRONMENT.txt"

  write_no_artifact_evidence "container run in progress; artifact not yet built"
}

# --- Failure handlers --------------------------------------------------------

# BUILD_NOT_STARTED: any failure strictly before `cargo build` is invoked
# (bootstrap, toolchain identity, or pre-cargo checks). Cannot be reached
# after CARGO_STARTED=YES.
fail_build_not_started() {
  local stage="$1"
  local exit_code="${2:-1}"
  EVIDENCE_FINALIZED="YES"
  write_outcome_evidence \
    "BUILD_NOT_STARTED" "NO" "BUILD_NOT_STARTED" "NOT_APPLICABLE" \
    "${exit_code}" "${stage}" "FAIL" \
    "NOT_STARTED" "NOT_STARTED" "NOT_APPLICABLE"
  write_no_artifact_evidence "cargo never started (failing_stage=${stage})"
  echo "BUILD_NOT_STARTED: failing_stage=${stage} exit_code=${exit_code}" >&2
  exit "${exit_code}"
}

# INFRASTRUCTURE_FAILURE: generic catch-all for unexpected/unclassified
# failures, wired through the ERR trap. Never overwrites a more specific
# classification already finalized by an explicit handler above.
fail_infrastructure() {
  local stage="$1"
  local exit_code="${2:-1}"
  EVIDENCE_FINALIZED="YES"
  local cargo_exit_field="NOT_APPLICABLE"
  if [[ -n "${CARGO_EXIT_CODE}" ]]; then
    cargo_exit_field="${CARGO_EXIT_CODE}"
  fi
  write_outcome_evidence \
    "INFRASTRUCTURE_FAILURE" "${CARGO_STARTED}" "INFRASTRUCTURE_FAILURE" "${cargo_exit_field}" \
    "${exit_code}" "${stage}" "INDETERMINATE" \
    "${BUILD_START_UTC:-NOT_RECORDED}" "$(ts)" "NOT_APPLICABLE"
  if [[ "${CARGO_STARTED}" == "YES" ]]; then
    write_artifact_evidence_best_effort "${stage}"
  else
    write_no_artifact_evidence "unexpected infrastructure failure at stage=${stage}; cargo never started"
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
    echo "evidence_schema_version=${EVIDENCE_SCHEMA_VERSION}"
    echo "platform_expected=linux/amd64"
    echo "HOME=${HOME}"
    echo "CARGO_HOME=${CARGO_HOME}"
    echo "CARGO_TARGET_DIR=${CARGO_TARGET_DIR_GROK}"
    echo "BOOTSTRAP_CARGO_TARGET_DIR=${BOOTSTRAP_CARGO_TARGET_DIR}"
    echo "CARGO_INCREMENTAL=${CARGO_INCREMENTAL:-unset}"
    echo "DOTSLASH_CACHE=${DOTSLASH_CACHE}"
    echo "PROTOC=${PROTOC:-unset}"
    echo "PATH=${PATH}"
    echo "RUSTUP_HOME_effective=${RUSTUP_HOME:-<unset>}"
    echo "network_mode=bridge"
    echo "mounts=/src:ro,/work:rw,/evidence:rw,/witness/container_narrow_build.sh:ro"
    echo "working_directory=/src"
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
TARGET_COUNT="$(append_clean_target_proof "container_pre_bootstrap_grok_target" "${CARGO_TARGET_DIR_GROK}")"
if [[ "${TARGET_COUNT}" != "0" ]]; then
  echo "container Grok Build target not empty before bootstrap" >&2
  fail_build_not_started "pre_bootstrap_empty_target"
fi

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
    echo "evidence_schema_version=${EVIDENCE_SCHEMA_VERSION}"
    echo "--- rustc (version mismatch) ---"
    echo "${RUSTC_RAW}"
    echo "rustc_observed_version=${RUSTC_OBSERVED_VERSION:-UNPARSEABLE}"
    echo "rustc_expected_version=${EXPECTED_RUSTC_VERSION}"
    echo "rustc_version_match=NO"
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
    echo "evidence_schema_version=${EVIDENCE_SCHEMA_VERSION}"
    echo "--- cargo (version mismatch) ---"
    echo "${CARGO_RAW}"
    echo "cargo_observed_version=${CARGO_OBSERVED_VERSION:-UNPARSEABLE}"
    echo "cargo_expected_version=${EXPECTED_CARGO_VERSION}"
    echo "cargo_version_match=NO"
  } >> "${EVIDENCE}/ENVIRONMENT.txt"
  fail_build_not_started "cargo_version_mismatch"
fi

{
  echo "evidence_schema_version=${EVIDENCE_SCHEMA_VERSION}"
  echo "--- rustc (validated) ---"
  echo "${RUSTC_RAW}"
  echo "rustc_observed_version=${RUSTC_OBSERVED_VERSION}"
  echo "rustc_expected_version=${EXPECTED_RUSTC_VERSION}"
  echo "rustc_version_match=YES"
  echo "--- cargo (validated) ---"
  echo "${CARGO_RAW}"
  echo "cargo_observed_version=${CARGO_OBSERVED_VERSION}"
  echo "cargo_expected_version=${EXPECTED_CARGO_VERSION}"
  echo "cargo_version_match=YES"
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

set_stage "protoc_version_probe"
set +e
"${PROTOC}" --version > "${EVIDENCE}/BOOTSTRAP_PROTOC_VERSION.txt" 2>&1
PROTOC_VER_EXIT=$?
set -e
echo "protoc_version_exit_code=${PROTOC_VER_EXIT}" >> "${EVIDENCE}/BOOTSTRAP.txt"
cat "${EVIDENCE}/BOOTSTRAP_PROTOC_VERSION.txt" >> "${EVIDENCE}/BOOTSTRAP.txt" 2>/dev/null || true

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
} > "${EVIDENCE}/BUILD_COMMAND.txt"

# Immediate pre-build empty Grok Build target recheck (required before cargo build).
set_stage "pre_cargo_empty_target"
TARGET_COUNT="$(append_clean_target_proof "container_immediate_pre_cargo_grok_target" "${CARGO_TARGET_DIR_GROK}")"
if [[ "${TARGET_COUNT}" != "0" ]]; then
  echo "container Grok Build target not empty immediately before cargo build" >&2
  fail_build_not_started "pre_cargo_empty_target"
fi

# --- Cargo build (the only fallible step permitted to proceed past this) ---

set_stage "cargo_build"
CARGO_STARTED="YES"
BUILD_START_UTC="$(ts)"
BUILD_START_SEC="$(date +%s)"

set +e
( cd /src && bash -c "${CANONICAL_BUILD_CMD}" ) > "${EVIDENCE}/BUILD_STDOUT.txt" 2> "${EVIDENCE}/BUILD_STDERR.txt"
CARGO_EXIT_CODE=$?
set -e

BUILD_END_UTC="$(ts)"
BUILD_END_SEC="$(date +%s)"
ELAPSED=$((BUILD_END_SEC - BUILD_START_SEC))

# --- Outcome classification --------------------------------------------------

set_stage "post_cargo_classification"

if [[ "${CARGO_EXIT_CODE}" -ne 0 ]]; then
  EVIDENCE_FINALIZED="YES"
  write_outcome_evidence \
    "CARGO_FAILED" "YES" "FAILED" "${CARGO_EXIT_CODE}" \
    "${CARGO_EXIT_CODE}" "cargo_build" "FAIL" \
    "${BUILD_START_UTC}" "${BUILD_END_UTC}" "${ELAPSED}"
  write_no_artifact_evidence "cargo build exited nonzero (${CARGO_EXIT_CODE})"
  exit "${CARGO_EXIT_CODE}"
fi

set_stage "artifact_presence_check"
if [[ ! -f "${ARTIFACT}" ]]; then
  EVIDENCE_FINALIZED="YES"
  write_outcome_evidence \
    "CARGO_SUCCEEDED_ARTIFACT_MISSING" "YES" "COMPLETE" "0" \
    "${ARTIFACT_MISSING_EXIT}" "artifact_presence_check" "FAIL" \
    "${BUILD_START_UTC}" "${BUILD_END_UTC}" "${ELAPSED}"
  write_no_artifact_evidence "cargo exited 0 but expected artifact ${ARTIFACT} is missing"
  echo "CARGO_SUCCEEDED_ARTIFACT_MISSING: cargo exit 0 but artifact absent at ${ARTIFACT}" >&2
  exit "${ARTIFACT_MISSING_EXIT}"
fi

# --- Required static inspection (artifact present only; no || true) --------
# Product execution and ldd remain PROHIBITED below and everywhere else.

set_stage "static_artifact_inspection"

if SHA256_OUT="$(sha256sum "${ARTIFACT}" 2>&1)"; then SHA256_EC=0; else SHA256_EC=$?; fi
if STAT_OUT="$(stat "${ARTIFACT}" 2>&1)"; then STAT_EC=0; else STAT_EC=$?; fi
if FILE_OUT="$(file "${ARTIFACT}" 2>&1)"; then FILE_EC=0; else FILE_EC=$?; fi
if READELF_H_OUT="$(readelf -h "${ARTIFACT}" 2>&1)"; then READELF_H_EC=0; else READELF_H_EC=$?; fi
if READELF_N_OUT="$(readelf -n "${ARTIFACT}" 2>&1)"; then READELF_N_EC=0; else READELF_N_EC=$?; fi
if READELF_D_OUT="$(readelf -d "${ARTIFACT}" 2>&1)"; then READELF_D_EC=0; else READELF_D_EC=$?; fi
if OBJDUMP_F_OUT="$(objdump -f "${ARTIFACT}" 2>&1)"; then OBJDUMP_F_EC=0; else OBJDUMP_F_EC=$?; fi

STATIC_INSPECTION_OK="YES"
for ec in "${SHA256_EC}" "${STAT_EC}" "${FILE_EC}" "${READELF_H_EC}" "${READELF_N_EC}" "${READELF_D_EC}" "${OBJDUMP_F_EC}"; do
  if [[ "${ec}" -ne 0 ]]; then
    STATIC_INSPECTION_OK="NO"
  fi
done

{
  echo "evidence_schema_version=${EVIDENCE_SCHEMA_VERSION}"
  echo "inspection_applicable=yes"
  echo "artifact_present=yes"
  echo "artifact_path=${ARTIFACT}"
  echo "--- sha256sum ---"
  echo "command=sha256sum ${ARTIFACT}"
  echo "exit_code=${SHA256_EC}"
  echo "${SHA256_OUT}"
  echo "--- stat ---"
  echo "command=stat ${ARTIFACT}"
  echo "exit_code=${STAT_EC}"
  echo "${STAT_OUT}"
  echo "--- file ---"
  echo "command=file ${ARTIFACT}"
  echo "exit_code=${FILE_EC}"
  echo "${FILE_OUT}"
  echo "--- readelf -h ---"
  echo "command=readelf -h ${ARTIFACT}"
  echo "exit_code=${READELF_H_EC}"
  echo "${READELF_H_OUT}"
  echo "--- readelf -n ---"
  echo "command=readelf -n ${ARTIFACT}"
  echo "exit_code=${READELF_N_EC}"
  echo "${READELF_N_OUT}"
  echo "--- readelf -d ---"
  echo "command=readelf -d ${ARTIFACT}"
  echo "exit_code=${READELF_D_EC}"
  echo "${READELF_D_OUT}"
  echo "--- objdump -f ---"
  echo "command=objdump -f ${ARTIFACT}"
  echo "exit_code=${OBJDUMP_F_EC}"
  echo "${OBJDUMP_F_OUT}"
  echo "static_commands_run=sha256sum stat file \"readelf -h\" \"readelf -n\" \"readelf -d\" \"objdump -f\""
  echo "static_inspection_complete=$([[ "${STATIC_INSPECTION_OK}" == "YES" ]] && echo yes || echo no)"
  echo "product_executed=NO"
  echo "ldd_used=NO"
  echo "ldd_prohibited=YES"
  echo "product_execution_prohibited=YES"
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
  echo "applicable=yes"
  echo "artifact_present=yes"
  echo "artifact_path=${ARTIFACT}"
  echo "artifact_filename=xai-grok-pager"
  echo "artifact_size_bytes=${ART_SIZE}"
  echo "artifact_sha256=${ART_SHA}"
  echo "gnu_build_id=${GNU_BUILD_ID}"
  echo "static_inspection_complete=$([[ "${STATIC_INSPECTION_OK}" == "YES" ]] && echo yes || echo no)"
  echo "product_executed=NO"
  echo "ldd_used=NO"
} > "${EVIDENCE}/ARTIFACT_IDENTITY.txt"

EVIDENCE_FINALIZED="YES"
if [[ "${STATIC_INSPECTION_OK}" == "YES" ]]; then
  FINAL_EXIT=0
  VERDICT_CEILING="PASS"
else
  FINAL_EXIT="${STATIC_INSPECTION_INCOMPLETE_EXIT}"
  VERDICT_CEILING="PARTIAL"
  echo "One or more required static inspection commands failed; evidence marked incomplete; verdict capped below PASS." >&2
fi

write_outcome_evidence \
  "CARGO_SUCCEEDED_ARTIFACT_PRESENT" "YES" "COMPLETE" "0" \
  "${FINAL_EXIT}" "NONE" "${VERDICT_CEILING}" \
  "${BUILD_START_UTC}" "${BUILD_END_UTC}" "${ELAPSED}"

# Container exits with the classified status (Docker preserves it on host).
exit "${FINAL_EXIT}"
