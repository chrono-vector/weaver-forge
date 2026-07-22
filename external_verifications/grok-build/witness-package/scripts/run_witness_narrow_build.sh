#!/usr/bin/env bash
# Independent Witness host orchestrator — Grok Build narrow clean rebuild.
# Author-only helper: do not execute from owner remediation sessions without Witness independence.
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PACKAGE_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
# Weaver Forge repo root when this script lives in the published package path.
WEAVER_FORGE_PACKAGE_REPO_ROOT="$(cd "${SCRIPT_DIR}/../../../.." && pwd)"

CONTAINER_SCRIPT="${SCRIPT_DIR}/container_narrow_build.sh"

WEAVER_FORGE_URL="${WEAVER_FORGE_URL:-https://github.com/chrono-vector/weaver-forge.git}"
WEAVER_FORGE_TAG="${WEAVER_FORGE_TAG:-grok-build-witness-v1.0.0-rc1}"
GROK_BUILD_URL="${GROK_BUILD_URL:-https://github.com/xai-org/grok-build.git}"
GROK_BUILD_COMMIT="${GROK_BUILD_COMMIT:-98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce}"
RUST_IMAGE="${RUST_IMAGE:-docker.io/library/rust@sha256:6ca5ad23231207874325a751b9df584d51cd42c066c74c6963c264e3233c3e8e}"

EXPECTED_CARGO_LOCK_SHA256="1512bb4fef0c1166c6a15a3398da9593903be1759b759ce78d9958913e61b421"
CANONICAL_BUILD_CMD="cargo build -p xai-grok-pager-bin --locked"

ALLOW_NONEMPTY_WORK_ROOT=0

on_err() {
  local ec=$?
  echo "ERROR: host orchestrator failed at line ${BASH_LINENO[0]} (exit ${ec})" >&2
  exit "${ec}"
}
trap on_err ERR

usage() {
  cat <<'EOF'
Usage: run_witness_narrow_build.sh [options] <witness-id>

Required:
  witness-id          GitHub user or witness identifier (e.g. alice)

Options:
  --work-root PATH    Isolated host work root (required via env WORK_ROOT or this flag)
  --allow-nonempty-work-root
                      Permit non-empty WORK_ROOT (Witness must confirm no stale artifacts)

Environment (optional overrides):
  WORK_ROOT           Same as --work-root
  WEAVER_FORGE_URL    Default: https://github.com/chrono-vector/weaver-forge.git
  WEAVER_FORGE_TAG    Default: grok-build-witness-v1.0.0-rc1
  GROK_BUILD_URL      Default: https://github.com/xai-org/grok-build.git
  GROK_BUILD_COMMIT   Default: 98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce
  RUST_IMAGE          Default: digest-pinned official rust image (1.92.0)

Does not execute the product binary. Does not run ldd.
EOF
}

short_run_id() {
  if command -v openssl >/dev/null 2>&1; then
    openssl rand -hex 3
  else
    date -u +%H%M%S
  fi
}

validate_work_root() {
  local wr="$1"
  if [[ -z "${wr}" ]]; then
    echo "WORK_ROOT must not be empty" >&2
    exit 2
  fi
  if [[ "${wr}" == "/" ]]; then
    echo "WORK_ROOT must not be /" >&2
    exit 2
  fi
  local home_real
  home_real="$(realpath "${HOME}" 2>/dev/null || echo "${HOME}")"
  local wr_real
  wr_real="$(realpath "${wr}" 2>/dev/null || echo "${wr}")"
  if [[ "${wr_real}" == "${home_real}" ]]; then
    echo "WORK_ROOT must not equal HOME" >&2
    exit 2
  fi
  if [[ "${wr_real}" == "$(realpath "${WEAVER_FORGE_PACKAGE_REPO_ROOT}" 2>/dev/null || echo "${WEAVER_FORGE_PACKAGE_REPO_ROOT}")" ]]; then
    echo "WORK_ROOT must not be the Weaver Forge repository containing this package" >&2
    exit 2
  fi
  if [[ -e "${wr}" ]] && [[ -n "$(ls -A "${wr}" 2>/dev/null || true)" ]]; then
    if [[ "${ALLOW_NONEMPTY_WORK_ROOT}" -ne 1 ]]; then
      echo "WORK_ROOT is non-empty; pass --allow-nonempty-work-root after confirming safe reset" >&2
      exit 2
    fi
  fi
}

WITNESS_ID=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --work-root)
      WORK_ROOT="${2:?}"
      shift 2
      ;;
    --allow-nonempty-work-root)
      ALLOW_NONEMPTY_WORK_ROOT=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    -*)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
    *)
      if [[ -z "${WITNESS_ID}" ]]; then
        WITNESS_ID="$1"
      else
        echo "Unexpected argument: $1" >&2
        exit 2
      fi
      shift
      ;;
  esac
done

if [[ -z "${WITNESS_ID}" ]]; then
  usage >&2
  exit 2
fi

WORK_ROOT="${WORK_ROOT:-}"
if [[ -z "${WORK_ROOT}" ]]; then
  echo "Set WORK_ROOT or pass --work-root" >&2
  exit 2
fi

validate_work_root "${WORK_ROOT}"

UTC_DATE="$(date -u +%Y%m%d)"
RUN_ID="${WITNESS_ID}-${UTC_DATE}-$(short_run_id)"

WF_DIR="${WORK_ROOT}/weaver-forge"
SRC_DIR="${WORK_ROOT}/grok-build-src"
CARGO_HOME_DIR="${WORK_ROOT}/cargo-home"
CARGO_TARGET_DIR="${WORK_ROOT}/cargo-target"
DOTSLASH_CACHE_DIR="${WORK_ROOT}/dotslash-cache"
HOME_DIR="${WORK_ROOT}/home"
BOOTSTRAP_DIR="${WORK_ROOT}/bootstrap"
EVIDENCE_DIR="${WORK_ROOT}/evidence/${RUN_ID}"

mkdir -p "${WORK_ROOT}" "${EVIDENCE_DIR}"

{
  echo "run_id=${RUN_ID}"
  echo "witness_id=${WITNESS_ID}"
  echo "utc_start=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "WEAVER_FORGE_URL=${WEAVER_FORGE_URL}"
  echo "WEAVER_FORGE_TAG=${WEAVER_FORGE_TAG}"
  echo "GROK_BUILD_URL=${GROK_BUILD_URL}"
  echo "GROK_BUILD_COMMIT=${GROK_BUILD_COMMIT}"
  echo "RUST_IMAGE=${RUST_IMAGE}"
  echo "WORK_ROOT=${WORK_ROOT}"
  echo "WF_DIR=${WF_DIR}"
  echo "SRC_DIR=${SRC_DIR}"
  echo "EVIDENCE_DIR=${EVIDENCE_DIR}"
} > "${EVIDENCE_DIR}/HOST_RUN_METADATA.txt"

# --- Fresh Weaver Forge clone and tag resolution ---
if [[ -d "${WF_DIR}/.git" ]]; then
  rm -rf "${WF_DIR}"
fi
git clone "${WEAVER_FORGE_URL}" "${WF_DIR}"
git -C "${WF_DIR}" fetch --tags origin
if ! git -C "${WF_DIR}" rev-parse "refs/tags/${WEAVER_FORGE_TAG}^{commit}" >/dev/null 2>&1; then
  echo "FAIL: Weaver Forge tag ${WEAVER_FORGE_TAG} is not present on origin." >&2
  echo "The proposed tag grok-build-witness-v1.0.0-rc1 must be created by maintainers after remediation review." >&2
  git -C "${WF_DIR}" tag -l 'grok-build-witness-*' || true
  exit 3
fi
WEAVER_FORGE_RESOLVED_COMMIT="$(git -C "${WF_DIR}" rev-parse "refs/tags/${WEAVER_FORGE_TAG}^{commit}")"
git -C "${WF_DIR}" checkout --detach "${WEAVER_FORGE_RESOLVED_COMMIT}"

{
  echo "weaver_forge_url=${WEAVER_FORGE_URL}"
  echo "weaver_forge_tag_requested=${WEAVER_FORGE_TAG}"
  echo "weaver_forge_commit_resolved=${WEAVER_FORGE_RESOLVED_COMMIT}"
} > "${EVIDENCE_DIR}/WEAVER_FORGE_PACKAGE_IDENTITY.txt"

HOST_CONTAINER_SCRIPT="${WF_DIR}/external_verifications/grok-build/witness-package/scripts/container_narrow_build.sh"
if [[ ! -f "${HOST_CONTAINER_SCRIPT}" ]]; then
  echo "Resolved Weaver commit missing container script at ${HOST_CONTAINER_SCRIPT}" >&2
  exit 3
fi

# --- Fresh Grok Build clone ---
if [[ -d "${SRC_DIR}/.git" ]]; then
  rm -rf "${SRC_DIR}"
fi
git clone "${GROK_BUILD_URL}" "${SRC_DIR}"
git -C "${SRC_DIR}" checkout --detach "${GROK_BUILD_COMMIT}"

SRC_HEAD="$(git -C "${SRC_DIR}" rev-parse HEAD)"
SRC_STATUS="$(git -C "${SRC_DIR}" status --porcelain)"
CARGO_LOCK_BEFORE="$(sha256sum "${SRC_DIR}/Cargo.lock" | awk '{print $1}')"

{
  echo "grok_build_url=${GROK_BUILD_URL}"
  echo "grok_build_commit_expected=${GROK_BUILD_COMMIT}"
  echo "grok_build_commit_observed=${SRC_HEAD}"
  echo "grok_build_clean_status_porcelain=${SRC_STATUS}"
  echo "cargo_lock_sha256_before=${CARGO_LOCK_BEFORE}"
  echo "cargo_lock_sha256_expected=${EXPECTED_CARGO_LOCK_SHA256}"
} > "${EVIDENCE_DIR}/SOURCE_IDENTITY.txt"

if [[ "${SRC_HEAD}" != "${GROK_BUILD_COMMIT}" ]]; then
  echo "Source commit mismatch" >&2
  exit 4
fi
if [[ -n "${SRC_STATUS}" ]]; then
  echo "Source tree not clean" >&2
  exit 4
fi

# --- Isolated writable directories ---
rm -rf "${CARGO_HOME_DIR}" "${CARGO_TARGET_DIR}" "${DOTSLASH_CACHE_DIR}" "${HOME_DIR}" "${BOOTSTRAP_DIR}"
mkdir -p "${CARGO_HOME_DIR}" "${CARGO_TARGET_DIR}" "${DOTSLASH_CACHE_DIR}" "${HOME_DIR}" "${BOOTSTRAP_DIR}"

TARGET_CREATED_UTC="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
TARGET_LISTING="$(ls -la "${CARGO_TARGET_DIR}" 2>&1 || true)"
TARGET_FIND="$(find "${CARGO_TARGET_DIR}" -mindepth 1 -print 2>/dev/null || true)"
TARGET_COUNT="$(find "${CARGO_TARGET_DIR}" -mindepth 1 | wc -l | tr -d ' ')"

{
  echo "cargo_target_dir_absolute=${CARGO_TARGET_DIR}"
  echo "creation_utc=${TARGET_CREATED_UTC}"
  echo "required_entry_count=0"
  echo "observed_entry_count=${TARGET_COUNT}"
  echo "--- ls -la ---"
  echo "${TARGET_LISTING}"
  echo "--- find ---"
  echo "${TARGET_FIND}"
} > "${EVIDENCE_DIR}/CLEAN_TARGET_PROOF.txt"

if [[ "${TARGET_COUNT}" != "0" ]]; then
  echo "Host pre-build target directory not empty" >&2
  exit 5
fi

# --- Docker invocation (exact contract) ---
DOCKER_STDOUT="${EVIDENCE_DIR}/CONTAINER_STDOUT.txt"
DOCKER_STDERR="${EVIDENCE_DIR}/CONTAINER_STDERR.txt"
DOCKER_EXIT_FILE="${EVIDENCE_DIR}/DOCKER_EXIT_CODE.txt"

set +e
docker run --rm \
  --platform linux/amd64 \
  --network bridge \
  -v "${SRC_DIR}:/src:ro" \
  -v "${WORK_ROOT}:/work" \
  -v "${EVIDENCE_DIR}:/evidence" \
  -v "${HOST_CONTAINER_SCRIPT}:/witness/container_narrow_build.sh:ro" \
  -e HOME=/work/home \
  -e CARGO_HOME=/work/cargo-home \
  -e CARGO_TARGET_DIR=/work/cargo-target \
  -e CARGO_INCREMENTAL=0 \
  -e DOTSLASH_CACHE=/work/dotslash-cache \
  -e PATH=/work/cargo-home/bin:/usr/local/cargo/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
  -e GROK_BUILD_COMMIT="${GROK_BUILD_COMMIT}" \
  -e EXPECTED_CARGO_LOCK_SHA256="${EXPECTED_CARGO_LOCK_SHA256}" \
  -e CANONICAL_BUILD_CMD="${CANONICAL_BUILD_CMD}" \
  -w /src \
  "${RUST_IMAGE}" \
  bash /witness/container_narrow_build.sh \
  >"${DOCKER_STDOUT}" 2>"${DOCKER_STDERR}"
DOCKER_EXIT=$?
set -e

echo "${DOCKER_EXIT}" > "${DOCKER_EXIT_FILE}"

SRC_HEAD_AFTER="$(git -C "${SRC_DIR}" rev-parse HEAD)"
SRC_STATUS_AFTER="$(git -C "${SRC_DIR}" status --porcelain)"
CARGO_LOCK_AFTER="$(sha256sum "${SRC_DIR}/Cargo.lock" | awk '{print $1}')"
ARTIFACT_PATH="${CARGO_TARGET_DIR}/debug/xai-grok-pager"
ARTIFACT_EXISTS=no
if [[ -f "${ARTIFACT_PATH}" ]]; then
  ARTIFACT_EXISTS=yes
fi

{
  echo "source_head_before=${SRC_HEAD}"
  echo "source_head_after=${SRC_HEAD_AFTER}"
  echo "source_clean_before=${SRC_STATUS}"
  echo "source_clean_after=${SRC_STATUS_AFTER}"
  echo "cargo_lock_sha256_before=${CARGO_LOCK_BEFORE}"
  echo "cargo_lock_sha256_after=${CARGO_LOCK_AFTER}"
  echo "artifact_path=${ARTIFACT_PATH}"
  echo "artifact_exists=${ARTIFACT_EXISTS}"
  echo "docker_exit_code=${DOCKER_EXIT}"
} > "${EVIDENCE_DIR}/POST_BUILD_INTEGRITY.txt"

(
  cd "${EVIDENCE_DIR}"
  find . -type f ! -name 'EVIDENCE_MANIFEST.sha256' -print0 | sort -z | xargs -0 sha256sum
) > "${EVIDENCE_DIR}/EVIDENCE_MANIFEST.sha256"

echo "--- Witness host summary (conservative) ---"
echo "run_id=${RUN_ID}"
echo "weaver_forge_tag=${WEAVER_FORGE_TAG}"
echo "weaver_forge_commit=${WEAVER_FORGE_RESOLVED_COMMIT}"
echo "grok_build_commit=${GROK_BUILD_COMMIT}"
echo "docker_exit_code=${DOCKER_EXIT}"
echo "artifact_exists=${ARTIFACT_EXISTS}"
echo "evidence_dir=${EVIDENCE_DIR}"
echo "product_executed=NO (orchestrator)"
echo "ldd_used=NO (orchestrator)"
echo "Submit evidence per WITNESS_SUBMISSION.md after redaction review."

exit "${DOCKER_EXIT}"
