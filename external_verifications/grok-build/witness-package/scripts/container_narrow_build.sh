#!/usr/bin/env bash
# In-container narrow build — Grok Build xai-grok-pager-bin only.
set -Eeuo pipefail

GROK_BUILD_COMMIT="${GROK_BUILD_COMMIT:-98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce}"
EXPECTED_CARGO_LOCK_SHA256="${EXPECTED_CARGO_LOCK_SHA256:-1512bb4fef0c1166c6a15a3398da9593903be1759b759ce78d9958913e61b421}"
CANONICAL_BUILD_CMD="${CANONICAL_BUILD_CMD:-cargo build -p xai-grok-pager-bin --locked}"

CARGO_HOME="/work/cargo-home"
CARGO_TARGET_DIR="/work/cargo-target"
DOTSLASH_CACHE="/work/dotslash-cache"
HOME="/work/home"
BOOTSTRAP_DIR="/work/bootstrap"
EVIDENCE="/evidence"

PROTOC_DESCRIPTOR_SRC="/src/bin/protoc"
PROTOC_DESCRIPTOR_WR="${BOOTSTRAP_DIR}/protoc-descriptor.lf"

on_err() {
  local ec=$?
  echo "ERROR: container script failed at line ${BASH_LINENO[0]} (exit ${ec})" >&2
  exit "${ec}"
}
trap on_err ERR

record_env() {
  {
    echo "platform_expected=linux/amd64"
    echo "HOME=${HOME}"
    echo "CARGO_HOME=${CARGO_HOME}"
    echo "CARGO_TARGET_DIR=${CARGO_TARGET_DIR}"
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

fail_bootstrap() {
  local stage="$1"
  {
    echo "cargo_started=NO"
    echo "build_status=BUILD_NOT_STARTED"
    echo "failing_bootstrap_stage=${stage}"
  } > "${EVIDENCE}/BUILD_EXIT_CODE.txt"
  echo "BUILD_NOT_STARTED" > "${EVIDENCE}/BUILD_TIMING.txt"
  : > "${EVIDENCE}/BUILD_STDOUT.txt"
  : > "${EVIDENCE}/BUILD_STDERR.txt"
  exit 1
}

mkdir -p "${BOOTSTRAP_DIR}" "${CARGO_HOME}" "${CARGO_TARGET_DIR}" "${DOTSLASH_CACHE}" "${HOME}"

# Record RUSTUP_HOME without overriding image toolchain.
if [[ -n "${RUSTUP_HOME:-}" ]]; then
  echo "RUSTUP_HOME is set in container env: ${RUSTUP_HOME} (not overridden by Witness script)" >> "${EVIDENCE}/BUILD_ENVIRONMENT.txt" || true
fi

# Empty target proof inside container (immediate pre-bootstrap).
TARGET_COUNT="$(find "${CARGO_TARGET_DIR}" -mindepth 1 | wc -l | tr -d ' ')"
{
  echo "cargo_target_dir_absolute=${CARGO_TARGET_DIR}"
  echo "check_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "required_entry_count=0"
  echo "observed_entry_count=${TARGET_COUNT}"
  echo "--- find ---"
  find "${CARGO_TARGET_DIR}" -mindepth 1 -print 2>/dev/null || true
} >> "${EVIDENCE}/CLEAN_TARGET_PROOF.txt"

if [[ "${TARGET_COUNT}" != "0" ]]; then
  echo "container target not empty" >&2
  fail_bootstrap "empty_target_precheck"
fi

export DEBIAN_FRONTEND=noninteractive
export CARGO_HOME CARGO_TARGET_DIR DOTSLASH_CACHE HOME
export CARGO_INCREMENTAL=0

# --- Bootstrap: apt packages (versions unpinned; record as limitation) ---
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

if ! apt-get update; then
  fail_bootstrap "apt-get_update"
fi
if ! apt-get install -y --no-install-recommends "${APT_PACKAGES[@]}"; then
  fail_bootstrap "apt-get_install"
fi

{
  echo "--- apt policy (unpinned) ---"
  dpkg-query -W -f='${Package} ${Version}\n' "${APT_PACKAGES[@]}" 2>/dev/null || true
} > "${EVIDENCE}/BOOTSTRAP.txt"

# --- DotSlash 0.5.7 into isolated CARGO_HOME ---
if ! cargo install dotslash --version 0.5.7 --locked --root "${CARGO_HOME}"; then
  fail_bootstrap "dotslash_install"
fi
DOTSLASH_BIN="${CARGO_HOME}/bin/dotslash"
{
  echo "dotslash_binary_path=${DOTSLASH_BIN}"
  echo "--- dotslash --version ---"
  "${DOTSLASH_BIN}" --version 2>&1 || true
} >> "${EVIDENCE}/BOOTSTRAP.txt"

export PATH="${CARGO_HOME}/bin:${PATH}"

# --- Protoc: LF-normalized writable copy of read-only descriptor (do not modify /src) ---
if [[ ! -f "${PROTOC_DESCRIPTOR_SRC}" ]]; then
  fail_bootstrap "protoc_descriptor_missing"
fi
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
  echo "--- protoc --version via writable descriptor (non-product) ---"
} >> "${EVIDENCE}/BOOTSTRAP.txt"

set +e
"${PROTOC}" --version > "${EVIDENCE}/BOOTSTRAP_PROTOC_VERSION.txt" 2>&1
PROTOC_VER_EXIT=$?
set -e
echo "protoc_version_exit=${PROTOC_VER_EXIT}" >> "${EVIDENCE}/BOOTSTRAP.txt"
cat "${EVIDENCE}/BOOTSTRAP_PROTOC_VERSION.txt" >> "${EVIDENCE}/BOOTSTRAP.txt" 2>/dev/null || true

if [[ "${PROTOC_VER_EXIT}" -ne 0 ]]; then
  fail_bootstrap "protoc_version_probe"
fi

record_env

# Record toolchain / OS (author commands executed during Witness run only).
{
  echo "--- rustc ---"
  rustc --version
  echo "--- cargo ---"
  cargo --version
  echo "--- uname ---"
  uname -a
  echo "--- os-release ---"
  cat /etc/os-release 2>/dev/null || true
} >> "${EVIDENCE}/ENVIRONMENT.txt" 2>&1 || true

# Source identity inside container
SRC_HEAD="$(git -C /src rev-parse HEAD)"
LOCK_SHA="$(sha256sum /src/Cargo.lock | awk '{print $1}')"
{
  echo "grok_build_commit_observed=${SRC_HEAD}"
  echo "grok_build_commit_expected=${GROK_BUILD_COMMIT}"
  echo "cargo_lock_sha256_observed=${LOCK_SHA}"
  echo "cargo_lock_sha256_expected=${EXPECTED_CARGO_LOCK_SHA256}"
} > "${EVIDENCE}/SOURCE_IDENTITY.txt"

if [[ "${SRC_HEAD}" != "${GROK_BUILD_COMMIT}" ]]; then
  fail_bootstrap "source_commit_mismatch"
fi

{
  echo "exact_build_command=${CANONICAL_BUILD_CMD}"
  echo "cargo_incremental=0"
  echo "cargo_fetch_separate_step=OMITTED (deps acquired during locked build; fresh CARGO_HOME)"
} > "${EVIDENCE}/BUILD_COMMAND.txt"

BUILD_START_UTC="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
BUILD_START_SEC="$(date +%s)"

set +e
(
  cd /src
  cargo build -p xai-grok-pager-bin --locked
) > "${EVIDENCE}/BUILD_STDOUT.txt" 2> "${EVIDENCE}/BUILD_STDERR.txt"
CARGO_EXIT=$?
set -e

BUILD_END_UTC="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
BUILD_END_SEC="$(date +%s)"
ELAPSED=$((BUILD_END_SEC - BUILD_START_SEC))

echo "${CARGO_EXIT}" > "${EVIDENCE}/BUILD_EXIT_CODE.txt"
{
  echo "cargo_started=YES"
  echo "build_status=$([[ ${CARGO_EXIT} -eq 0 ]] && echo COMPLETE || echo FAILED)"
  echo "cargo_exit_code=${CARGO_EXIT}"
  echo "docker_exit_code_propagates=cargo_exit_on_success_path"
} >> "${EVIDENCE}/BUILD_EXIT_CODE.txt"

{
  echo "utc_start=${BUILD_START_UTC}"
  echo "utc_end=${BUILD_END_UTC}"
  echo "elapsed_seconds=${ELAPSED}"
  echo "exact_build_command=${CANONICAL_BUILD_CMD}"
  echo "cargo_exit_code=${CARGO_EXIT}"
} > "${EVIDENCE}/BUILD_TIMING.txt"

ARTIFACT="${CARGO_TARGET_DIR}/debug/xai-grok-pager"
if [[ "${CARGO_EXIT}" -eq 0 && -f "${ARTIFACT}" ]]; then
  ART_SHA="$(sha256sum "${ARTIFACT}" | awk '{print $1}')"
  ART_SIZE="$(stat -c '%s' "${ARTIFACT}" 2>/dev/null || wc -c < "${ARTIFACT}")"
  {
    echo "artifact_path=${ARTIFACT}"
    echo "artifact_filename=xai-grok-pager"
    echo "artifact_size_bytes=${ART_SIZE}"
    echo "artifact_sha256=${ART_SHA}"
    echo "product_executed=NO"
    echo "ldd_used=NO"
  } > "${EVIDENCE}/ARTIFACT_IDENTITY.txt"

  {
    echo "artifact_path=${ARTIFACT}"
    echo "--- file ---"
    file "${ARTIFACT}" || true
    echo "--- readelf -h ---"
    readelf -h "${ARTIFACT}" || true
    echo "--- readelf -n ---"
    readelf -n "${ARTIFACT}" || true
    echo "--- readelf -d ---"
    readelf -d "${ARTIFACT}" || true
    echo "--- objdump -f ---"
    objdump -f "${ARTIFACT}" || true
    echo "product_executed=NO"
    echo "ldd_used=NO"
  } > "${EVIDENCE}/STATIC_ARTIFACT_INSPECTION.txt"
else
  echo "artifact_missing_or_build_failed=YES" > "${EVIDENCE}/ARTIFACT_IDENTITY.txt"
fi

# Container exits with Cargo status (Docker preserves it on host).
exit "${CARGO_EXIT}"
