#!/usr/bin/env bash
# Independent Witness host orchestrator — Grok Build narrow clean rebuild.
# Author-only helper: do not execute from owner remediation sessions without Witness independence.
#
# rc3 (C2E-4) rewrite. Canonical identity constants are immutable and separate
# from the "effective" values actually used for a run. Any effective value
# that differs from its canonical counterpart requires the explicit
# --noncanonical-deviation flag; without it the script refuses to run rather
# than silently accepting an environment-variable override.
set -Eeuo pipefail

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PACKAGE_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
# Weaver Forge repo root when this script lives in the published package path.
WEAVER_FORGE_PACKAGE_REPO_ROOT="$(cd "${SCRIPT_DIR}/../../../.." && pwd)"

# ---------------------------------------------------------------------------
# Canonical constants (immutable; never assigned from the environment)
# ---------------------------------------------------------------------------
readonly CANONICAL_WEAVER_FORGE_URL="https://github.com/chrono-vector/weaver-forge.git"
readonly CANONICAL_WEAVER_FORGE_TAG="grok-build-witness-v1.0.0-rc3"
# Package commit identity is derived at runtime from the annotated tag
# (refs/tags/${CANONICAL_WEAVER_FORGE_TAG}^{commit}). The tagged package MUST
# NOT embed its own future commit hash — that creates a self-referential
# commit problem. Do not reintroduce CANONICAL_WEAVER_FORGE_EXPECTED_COMMIT.
readonly CANONICAL_GROK_BUILD_URL="https://github.com/xai-org/grok-build.git"
readonly CANONICAL_GROK_BUILD_COMMIT="98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce"
readonly CANONICAL_RUST_IMAGE="docker.io/library/rust@sha256:6ca5ad23231207874325a751b9df584d51cd42c066c74c6963c264e3233c3e8e"
readonly CANONICAL_EXPECTED_CARGO_LOCK_SHA256="1512bb4fef0c1166c6a15a3398da9593903be1759b759ce78d9958913e61b421"
readonly CANONICAL_BUILD_CMD="cargo build -p xai-grok-pager-bin --locked"
readonly CANONICAL_EXPECTED_RUSTC_VERSION="1.92.0"
readonly CANONICAL_EXPECTED_DOTSLASH_VERSION="0.5.7"

# ---------------------------------------------------------------------------
# Effective values (default = canonical; overridable via environment, but
# any actual deviation is refused unless --noncanonical-deviation is given).
# ---------------------------------------------------------------------------
EFFECTIVE_WEAVER_FORGE_URL="${WEAVER_FORGE_URL:-${CANONICAL_WEAVER_FORGE_URL}}"
EFFECTIVE_WEAVER_FORGE_TAG="${WEAVER_FORGE_TAG:-${CANONICAL_WEAVER_FORGE_TAG}}"
EFFECTIVE_GROK_BUILD_URL="${GROK_BUILD_URL:-${CANONICAL_GROK_BUILD_URL}}"
EFFECTIVE_GROK_BUILD_COMMIT="${GROK_BUILD_COMMIT:-${CANONICAL_GROK_BUILD_COMMIT}}"
EFFECTIVE_RUST_IMAGE="${RUST_IMAGE:-${CANONICAL_RUST_IMAGE}}"
EFFECTIVE_EXPECTED_CARGO_LOCK_SHA256="${EXPECTED_CARGO_LOCK_SHA256:-${CANONICAL_EXPECTED_CARGO_LOCK_SHA256}}"
EFFECTIVE_BUILD_CMD="${BUILD_CMD:-${CANONICAL_BUILD_CMD}}"
EFFECTIVE_EXPECTED_RUSTC_VERSION="${EXPECTED_RUSTC_VERSION:-${CANONICAL_EXPECTED_RUSTC_VERSION}}"
EFFECTIVE_EXPECTED_DOTSLASH_VERSION="${EXPECTED_DOTSLASH_VERSION:-${CANONICAL_EXPECTED_DOTSLASH_VERSION}}"

# Optional ADDITIONAL verification input only. Not a canonical constant.
# When non-empty, the resolved tag commit (and detached HEAD) must equal it.
# Absence does not weaken tag→HEAD consistency checks. Never store a
# placeholder for this value inside the fixed tagged package.
WEAVER_FORGE_EXTERNAL_EXPECTED_COMMIT="${WEAVER_FORGE_EXTERNAL_EXPECTED_COMMIT:-}"

# ---------------------------------------------------------------------------
# Mandatory automated evidence files (initialized to NOT_REACHED before any
# fallible host/container operation; see init_mandatory_evidence()).
# ---------------------------------------------------------------------------
readonly MANDATORY_EVIDENCE_FILES=(
  WEAVER_FORGE_PACKAGE_IDENTITY.txt
  ENVIRONMENT.txt
  SOURCE_ACQUISITION.txt
  SOURCE_IDENTITY.txt
  IMAGE_IDENTITY.txt
  BOOTSTRAP.txt
  CLEAN_TARGET_PROOF.txt
  BUILD_COMMAND.txt
  BUILD_ENVIRONMENT.txt
  CONTAINER_STDOUT.txt
  CONTAINER_STDERR.txt
  DOCKER_EXIT_CODE.txt
  BUILD_STDOUT.txt
  BUILD_STDERR.txt
  BUILD_EXIT_CODE.txt
  BUILD_TIMING.txt
  ARTIFACT_IDENTITY.txt
  STATIC_ARTIFACT_INSPECTION.txt
  POST_BUILD_INTEGRITY.txt
)

readonly SYSTEM_PREFIXES=(
  /bin /boot /dev /etc /lib /lib64 /proc /root /run /sbin /sys
  /usr /usr/bin /usr/sbin /usr/lib /usr/lib64 /usr/local /var
)

# ---------------------------------------------------------------------------
# Mutable run state
# ---------------------------------------------------------------------------
WITNESS_ID=""
WORK_ROOT="${WORK_ROOT:-}"
WORK_ROOT_RESOLVED=""
ALLOW_NONEMPTY_WORK_ROOT=0
FORCE_WORK_ROOT_RESET=0
NONCANONICAL_DEVIATION_ACCEPTED=0
NONCANONICAL_RUN=0
VERDICT_CEILING="PASS"
declare -a CHANGED_IDENTITY_FIELDS=()
declare -a CHANGED_IDENTITY_FIELD_NAMES=()

CURRENT_STAGE="startup"
SPECIFIC_FAILURE_RECORDED=0
CARGO_STARTED="NO"
DOCKER_STARTED_UTC=""
DOCKER_FINISHED_UTC=""
DOCKER_EXIT=""
OUTCOME="BUILD_NOT_STARTED"
FAILURE_STAGE="none"

EVIDENCE_DIR=""

# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------
utc_now() { date -u +%Y-%m-%dT%H:%M:%SZ; }

sha256_of() { sha256sum "$1" | awk '{print $1}'; }

mark_stage() { CURRENT_STAGE="$1"; }

die_arg() {
  echo "FATAL[args]: $*" >&2
  usage >&2
  exit 2
}

# abort(): caller MUST have already written specific evidence describing the
# failure. This marks the failure as "specific" so the ERR trap does not
# clobber it with generic classification output.
abort() {
  local ec="$1"
  shift
  echo "FATAL[stage=${CURRENT_STAGE}]: $*" >&2
  SPECIFIC_FAILURE_RECORDED=1
  exit "${ec}"
}

write_not_reached() {
  local path="$1"
  {
    echo "evidence_schema_version=1"
    echo "status=NOT_REACHED"
    echo "applicable=no"
    echo "reason=stage_not_reached"
    echo "product_executed=NO"
    echo "ldd_used=NO"
  } > "${path}"
}

# ---------------------------------------------------------------------------
# ERR trap: extends generic failure handling without overwriting more
# specific failure classifications already recorded by abort()-driven paths.
# ---------------------------------------------------------------------------
record_generic_failure() {
  local ec="$1"
  if [[ "${SPECIFIC_FAILURE_RECORDED}" -eq 1 ]]; then
    return 0
  fi
  FAILURE_STAGE="${CURRENT_STAGE}"
  case "${CURRENT_STAGE}" in
    docker_run|cargo_lock_post_docker|post_build_integrity|outcome_determination|manifest_generation)
      OUTCOME="INFRASTRUCTURE_FAILURE"
      ;;
    *)
      OUTCOME="BUILD_NOT_STARTED"
      ;;
  esac
  if [[ -n "${EVIDENCE_DIR}" && -d "${EVIDENCE_DIR}" ]]; then
    {
      echo "evidence_schema_version=1"
      echo "status=UNEXPECTED_FAILURE"
      echo "cargo_started=${CARGO_STARTED}"
      echo "failing_stage=${FAILURE_STAGE}"
      echo "outcome=${OUTCOME}"
      echo "exit_code=${ec}"
    } >> "${EVIDENCE_DIR}/BUILD_EXIT_CODE.txt" 2>/dev/null || true
    {
      echo "evidence_schema_version=1"
      echo "docker_started_utc=${DOCKER_STARTED_UTC:-NOT_STARTED}"
      echo "docker_finished_utc=$(utc_now)"
      echo "docker_exit_code=${ec}"
      echo "container_platform=linux/amd64"
      echo "network_mode=bridge"
      echo "product_executed=NO"
      echo "ldd_used=NO"
      echo "outcome=${OUTCOME}"
      echo "failure_stage=${FAILURE_STAGE}"
    } >> "${EVIDENCE_DIR}/DOCKER_EXIT_CODE.txt" 2>/dev/null || true
    {
      echo "evidence_schema_version=1"
      echo "unexpected_failure_stage=${FAILURE_STAGE}"
      echo "outcome=${OUTCOME}"
    } >> "${EVIDENCE_DIR}/BUILD_TIMING.txt" 2>/dev/null || true
  fi
}

on_err() {
  local ec=$?
  echo "ERROR: host orchestrator failed at stage '${CURRENT_STAGE}' line ${BASH_LINENO[0]} (exit ${ec})" >&2
  record_generic_failure "${ec}"
  exit "${ec}"
}
trap on_err ERR

usage() {
  cat <<EOF
Usage: run_witness_narrow_build.sh [options] <witness-id>

Required:
  witness-id                    ${WITNESS_ID:+(already set) }Identifier matching ^[a-z0-9][a-z0-9._-]{0,63}\$

Options:
  --work-root PATH               Isolated host work root (required via env WORK_ROOT or this flag)
  --allow-nonempty-work-root     Permit a non-empty WORK_ROOT (still requires typed confirmation
                                  or --force-work-root-reset)
  --force-work-root-reset        Non-interactive authorization to reset a non-empty WORK_ROOT
                                  (use instead of the typed confirmation prompt)
  --noncanonical-deviation       Required to accept ANY environment-variable override of a
                                  canonical identity field. Without this flag, an override that
                                  differs from the canonical value is a fatal error.
  -h, --help                     Show this help

Canonical identity (immutable defaults; see script header):
  WEAVER_FORGE_URL             = ${CANONICAL_WEAVER_FORGE_URL}
  WEAVER_FORGE_TAG             = ${CANONICAL_WEAVER_FORGE_TAG}
  GROK_BUILD_URL               = ${CANONICAL_GROK_BUILD_URL}
  GROK_BUILD_COMMIT            = ${CANONICAL_GROK_BUILD_COMMIT}
  RUST_IMAGE                   = ${CANONICAL_RUST_IMAGE}
  EXPECTED_CARGO_LOCK_SHA256   = ${CANONICAL_EXPECTED_CARGO_LOCK_SHA256}
  BUILD_CMD                    = ${CANONICAL_BUILD_CMD}
  EXPECTED_RUSTC_VERSION       = ${CANONICAL_EXPECTED_RUSTC_VERSION}
  EXPECTED_DOTSLASH_VERSION    = ${CANONICAL_EXPECTED_DOTSLASH_VERSION}

Package commit identity is ALWAYS derived from:
  refs/tags/<WEAVER_FORGE_TAG>^{commit}
then checked out detached; HEAD must equal that resolved commit and the
package clone must be clean. The tagged package does not embed its own
future commit hash.

Optional additional verification (not required for canonical execution):
  WEAVER_FORGE_EXTERNAL_EXPECTED_COMMIT
    When set to a full 40-char commit, must equal the resolved tag commit
    and detached HEAD; mismatch is fatal. Absence does not weaken tag→HEAD checks.

Environment variables of the canonical field names may override the values above,
but ONLY take effect when --noncanonical-deviation is also passed. Any accepted
deviation sets canonical_run=NO, is recorded in DEVIATIONS.txt/HOST_RUN_METADATA.txt,
and caps the proposed Witness verdict at PARTIAL (or FAIL for material identity changes).
--noncanonical-deviation does NOT bypass tag→resolved-commit→detached-HEAD integrity
for the effective package tag.

Does not execute the product binary. Does not run ldd.
EOF
}

# ---------------------------------------------------------------------------
# Identity override gate
# ---------------------------------------------------------------------------
check_identity_override() {
  local field_name="$1" canonical_value="$2" effective_value="$3"
  if [[ "${effective_value}" == "${canonical_value}" ]]; then
    return 0
  fi
  if [[ "${NONCANONICAL_DEVIATION_ACCEPTED}" -ne 1 ]]; then
    echo "FATAL: ${field_name} overridden without --noncanonical-deviation" >&2
    echo "  canonical: ${canonical_value}" >&2
    echo "  requested: ${effective_value}" >&2
    echo "Environment overrides alone MUST NOT silently change identity. Pass --noncanonical-deviation to accept this deviation explicitly." >&2
    exit 2
  fi
  NONCANONICAL_RUN=1
  CHANGED_IDENTITY_FIELDS+=("${field_name}: canonical='${canonical_value}' effective='${effective_value}'")
  CHANGED_IDENTITY_FIELD_NAMES+=("${field_name}")
}

apply_identity_gate() {
  check_identity_override "WEAVER_FORGE_URL" "${CANONICAL_WEAVER_FORGE_URL}" "${EFFECTIVE_WEAVER_FORGE_URL}"
  check_identity_override "WEAVER_FORGE_TAG" "${CANONICAL_WEAVER_FORGE_TAG}" "${EFFECTIVE_WEAVER_FORGE_TAG}"
  check_identity_override "GROK_BUILD_URL" "${CANONICAL_GROK_BUILD_URL}" "${EFFECTIVE_GROK_BUILD_URL}"
  check_identity_override "GROK_BUILD_COMMIT" "${CANONICAL_GROK_BUILD_COMMIT}" "${EFFECTIVE_GROK_BUILD_COMMIT}"
  check_identity_override "RUST_IMAGE" "${CANONICAL_RUST_IMAGE}" "${EFFECTIVE_RUST_IMAGE}"
  check_identity_override "EXPECTED_CARGO_LOCK_SHA256" "${CANONICAL_EXPECTED_CARGO_LOCK_SHA256}" "${EFFECTIVE_EXPECTED_CARGO_LOCK_SHA256}"
  check_identity_override "BUILD_CMD" "${CANONICAL_BUILD_CMD}" "${EFFECTIVE_BUILD_CMD}"
  check_identity_override "EXPECTED_RUSTC_VERSION" "${CANONICAL_EXPECTED_RUSTC_VERSION}" "${EFFECTIVE_EXPECTED_RUSTC_VERSION}"
  check_identity_override "EXPECTED_DOTSLASH_VERSION" "${CANONICAL_EXPECTED_DOTSLASH_VERSION}" "${EFFECTIVE_EXPECTED_DOTSLASH_VERSION}"

  VERDICT_CEILING="PASS"
  if [[ "${NONCANONICAL_RUN}" -eq 1 ]]; then
    VERDICT_CEILING="PARTIAL"
    local name
    for name in "${CHANGED_IDENTITY_FIELD_NAMES[@]}"; do
      case "${name}" in
        WEAVER_FORGE_TAG|GROK_BUILD_URL|GROK_BUILD_COMMIT|RUST_IMAGE|EXPECTED_CARGO_LOCK_SHA256|BUILD_CMD)
          VERDICT_CEILING="FAIL"
          ;;
      esac
    done
  fi
}

# ---------------------------------------------------------------------------
# WITNESS_ID safety
# ---------------------------------------------------------------------------
validate_witness_id() {
  local id="$1"
  local re='^[a-z0-9][a-z0-9._-]{0,63}$'
  if [[ -z "${id}" ]]; then
    die_arg "witness-id must not be empty"
  fi
  if [[ ! "${id}" =~ ${re} ]]; then
    die_arg "witness-id '${id}' does not match required pattern ${re}"
  fi
  if [[ "${id}" == *"/"* || "${id}" == *'\'* ]]; then
    die_arg "witness-id must not contain path separators"
  fi
  if [[ "${id}" == *".."* ]]; then
    die_arg "witness-id must not contain '..'"
  fi
  if [[ "${id}" =~ [[:space:]] ]]; then
    die_arg "witness-id must not contain whitespace"
  fi
  if [[ "${id}" == *[[:cntrl:]]* ]]; then
    die_arg "witness-id must not contain control characters"
  fi
  if [[ "${id}" == -* ]]; then
    die_arg "witness-id must not start with a dash"
  fi
}

# ---------------------------------------------------------------------------
# WORK_ROOT safety (evaluated in full before any deletion occurs)
# ---------------------------------------------------------------------------
is_system_prefix() {
  local p="$1" prefix
  for prefix in "${SYSTEM_PREFIXES[@]}"; do
    if [[ "${p}" == "${prefix}" || "${p}" == "${prefix}/"* ]]; then
      return 0
    fi
  done
  return 1
}

is_wsl_drive_root() {
  [[ "$1" =~ ^/mnt/[A-Za-z]$ ]]
}

resolve_path_m() {
  local p="$1"
  if command -v realpath >/dev/null 2>&1; then
    realpath -m -- "${p}" 2>/dev/null && return 0
  fi
  # Portable fallback: resolve nearest existing ancestor, then append the
  # remaining (non-existent) suffix literally.
  local existing="${p}"
  local suffix=""
  while [[ ! -e "${existing}" && "${existing}" != "/" && -n "${existing}" ]]; do
    suffix="/$(basename -- "${existing}")${suffix}"
    existing="$(dirname -- "${existing}")"
  done
  local existing_real
  existing_real="$(cd "${existing}" 2>/dev/null && pwd || echo "${existing}")"
  echo "${existing_real}${suffix}"
}

validate_work_root() {
  local wr="$1"
  if [[ -z "${wr}" ]]; then
    die_arg "WORK_ROOT must not be empty (set WORK_ROOT or pass --work-root)"
  fi
  if [[ "${wr}" != /* ]]; then
    die_arg "WORK_ROOT must be an absolute path: ${wr}"
  fi

  # Resolve canonical existing parent + final path in one step: this
  # resolves symlinks in every existing path component (defeating dangerous
  # symlinked reset targets) and appends any not-yet-existing suffix as-is.
  local resolved
  resolved="$(resolve_path_m "${wr}")"

  if [[ "${resolved}" == "/" ]]; then
    die_arg "WORK_ROOT must not resolve to / (resolved: ${resolved})"
  fi

  local home_resolved=""
  if [[ -n "${HOME:-}" ]]; then
    home_resolved="$(resolve_path_m "${HOME}")"
  fi
  if [[ -n "${home_resolved}" && "${resolved}" == "${home_resolved}" ]]; then
    die_arg "WORK_ROOT must not resolve to the home directory (resolved: ${resolved})"
  fi
  if [[ "${resolved}" =~ ^/home/[^/]+$ ]] || [[ "${resolved}" == "/root" ]]; then
    die_arg "WORK_ROOT must not resolve to a home directory (resolved: ${resolved})"
  fi

  if is_wsl_drive_root "${resolved}"; then
    die_arg "WORK_ROOT must not resolve to a WSL drive-root mount (resolved: ${resolved})"
  fi

  if is_system_prefix "${resolved}"; then
    die_arg "WORK_ROOT must not resolve within a system prefix (resolved: ${resolved})"
  fi

  local repo_resolved
  repo_resolved="$(resolve_path_m "${WEAVER_FORGE_PACKAGE_REPO_ROOT}")"
  if [[ "${resolved}" == "${repo_resolved}" ]]; then
    die_arg "WORK_ROOT must not be the package repository (resolved: ${resolved})"
  fi
  if [[ "${repo_resolved}" == "${resolved}/"* ]]; then
    die_arg "WORK_ROOT must not be an ancestor of the package repository (resolved: ${resolved})"
  fi
  if [[ "${resolved}" == "${repo_resolved}/"* ]]; then
    die_arg "WORK_ROOT must not be located inside the package repository (resolved: ${resolved})"
  fi

  WORK_ROOT_RESOLVED="${resolved}"
}

# Deterministic Witness-managed subdirectories under WORK_ROOT. These are the
# exact deletion targets reset on every run once WORK_ROOT itself has passed
# validate_work_root().
work_root_managed_targets() {
  echo "${WF_DIR}"
  echo "${SRC_DIR}"
  echo "${CARGO_HOME_DIR}"
  echo "${CARGO_TARGET_DIR}"
  echo "${BOOTSTRAP_CARGO_TARGET_DIR}"
  echo "${DOTSLASH_CACHE_DIR}"
  echo "${HOME_DIR}"
  echo "${BOOTSTRAP_DIR}"
}

# Requires explicit typed confirmation OR --force-work-root-reset for a
# non-empty WORK_ROOT. The default remains: an empty WORK_ROOT only.
confirm_work_root_reset_if_needed() {
  local top_level_nonempty="no"
  if [[ -e "${WORK_ROOT}" ]] && [[ -n "$(ls -A "${WORK_ROOT}" 2>/dev/null || true)" ]]; then
    top_level_nonempty="yes"
  fi

  echo "--- WORK_ROOT deletion-target disclosure ---"
  echo "work_root=${WORK_ROOT}"
  echo "work_root_resolved=${WORK_ROOT_RESOLVED}"
  echo "work_root_top_level_nonempty=${top_level_nonempty}"
  echo "exact_managed_deletion_targets:"
  local t
  while IFS= read -r t; do
    echo "  ${t}"
  done < <(work_root_managed_targets)

  if [[ "${top_level_nonempty}" != "yes" ]]; then
    return 0
  fi

  if [[ "${ALLOW_NONEMPTY_WORK_ROOT}" -ne 1 ]]; then
    die_arg "WORK_ROOT is non-empty; pass --allow-nonempty-work-root after reviewing the deletion targets above (default remains empty-WORK_ROOT-only)"
  fi

  echo "--- current WORK_ROOT top-level contents ---"
  ls -A "${WORK_ROOT}" 2>&1 || true

  if [[ "${FORCE_WORK_ROOT_RESET}" -eq 1 ]]; then
    echo "work_root_reset_authorization=--force-work-root-reset"
    return 0
  fi

  if [[ ! -t 0 ]]; then
    die_arg "WORK_ROOT is non-empty and this session is non-interactive; use --force-work-root-reset to authorize the reset listed above"
  fi

  echo ""
  echo "Non-empty WORK_ROOT reset requires typed confirmation."
  echo "Type the exact resolved WORK_ROOT path to confirm you have reviewed the deletion targets above:"
  echo "  ${WORK_ROOT_RESOLVED}"
  local typed=""
  read -r -p "> " typed || true
  if [[ "${typed}" != "${WORK_ROOT_RESOLVED}" ]]; then
    die_arg "Typed confirmation did not match the resolved WORK_ROOT path; refusing to reset a non-empty WORK_ROOT"
  fi
  echo "work_root_reset_authorization=typed_confirmation"
}

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------
while [[ $# -gt 0 ]]; do
  case "$1" in
    --work-root)
      WORK_ROOT="${2:?--work-root requires a value}"
      shift 2
      ;;
    --allow-nonempty-work-root)
      ALLOW_NONEMPTY_WORK_ROOT=1
      shift
      ;;
    --force-work-root-reset)
      FORCE_WORK_ROOT_RESET=1
      shift
      ;;
    --noncanonical-deviation)
      NONCANONICAL_DEVIATION_ACCEPTED=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    -*)
      die_arg "Unknown option: $1"
      ;;
    *)
      if [[ -z "${WITNESS_ID}" ]]; then
        WITNESS_ID="$1"
      else
        die_arg "Unexpected argument: $1"
      fi
      shift
      ;;
  esac
done

mark_stage "identity_gate"
apply_identity_gate

mark_stage "witness_id_validation"
validate_witness_id "${WITNESS_ID}"

mark_stage "work_root_validation"
validate_work_root "${WORK_ROOT}"

# ---------------------------------------------------------------------------
# Run identity / directory layout
# ---------------------------------------------------------------------------
short_run_id() {
  if command -v openssl >/dev/null 2>&1; then
    openssl rand -hex 3
  else
    date -u +%H%M%S
  fi
}

UTC_DATE="$(date -u +%Y%m%d)"
RUN_ID="${WITNESS_ID}-${UTC_DATE}-$(short_run_id)"

WF_DIR="${WORK_ROOT}/weaver-forge"
SRC_DIR="${WORK_ROOT}/grok-build-src"
CARGO_HOME_DIR="${WORK_ROOT}/cargo-home"
CARGO_TARGET_DIR="${WORK_ROOT}/cargo-target"
BOOTSTRAP_CARGO_TARGET_DIR="${WORK_ROOT}/bootstrap-cargo-target"
DOTSLASH_CACHE_DIR="${WORK_ROOT}/dotslash-cache"
HOME_DIR="${WORK_ROOT}/home"
BOOTSTRAP_DIR="${WORK_ROOT}/bootstrap"
EVIDENCE_DIR="${WORK_ROOT}/evidence/${RUN_ID}"

mark_stage "work_root_reset_confirmation"
confirm_work_root_reset_if_needed

mark_stage "directory_setup"
mkdir -p "${WORK_ROOT}" "${EVIDENCE_DIR}"

# ---------------------------------------------------------------------------
# Evidence initialization — BEFORE any fallible host/container operation.
# ---------------------------------------------------------------------------
mark_stage "evidence_initialization"
init_mandatory_evidence() {
  local f
  for f in "${MANDATORY_EVIDENCE_FILES[@]}"; do
    write_not_reached "${EVIDENCE_DIR}/${f}"
  done
}
init_mandatory_evidence

{
  echo "evidence_schema_version=1"
  echo "run_id=${RUN_ID}"
  echo "witness_id=${WITNESS_ID}"
  echo "utc_start=$(utc_now)"
  echo "canonical_run=$([[ "${NONCANONICAL_RUN}" -eq 1 ]] && echo NO || echo YES)"
  echo "verdict_ceiling=${VERDICT_CEILING}"
  echo "--- canonical identity ---"
  echo "CANONICAL_WEAVER_FORGE_URL=${CANONICAL_WEAVER_FORGE_URL}"
  echo "CANONICAL_WEAVER_FORGE_TAG=${CANONICAL_WEAVER_FORGE_TAG}"
  echo "package_commit_authority=annotated_tag_resolution"
  echo "CANONICAL_GROK_BUILD_URL=${CANONICAL_GROK_BUILD_URL}"
  echo "CANONICAL_GROK_BUILD_COMMIT=${CANONICAL_GROK_BUILD_COMMIT}"
  echo "CANONICAL_RUST_IMAGE=${CANONICAL_RUST_IMAGE}"
  echo "CANONICAL_EXPECTED_CARGO_LOCK_SHA256=${CANONICAL_EXPECTED_CARGO_LOCK_SHA256}"
  echo "CANONICAL_BUILD_CMD=${CANONICAL_BUILD_CMD}"
  echo "CANONICAL_EXPECTED_RUSTC_VERSION=${CANONICAL_EXPECTED_RUSTC_VERSION}"
  echo "CANONICAL_EXPECTED_DOTSLASH_VERSION=${CANONICAL_EXPECTED_DOTSLASH_VERSION}"
  echo "--- effective identity (used for this run) ---"
  echo "EFFECTIVE_WEAVER_FORGE_URL=${EFFECTIVE_WEAVER_FORGE_URL}"
  echo "EFFECTIVE_WEAVER_FORGE_TAG=${EFFECTIVE_WEAVER_FORGE_TAG}"
  echo "EFFECTIVE_GROK_BUILD_URL=${EFFECTIVE_GROK_BUILD_URL}"
  echo "EFFECTIVE_GROK_BUILD_COMMIT=${EFFECTIVE_GROK_BUILD_COMMIT}"
  echo "EFFECTIVE_RUST_IMAGE=${EFFECTIVE_RUST_IMAGE}"
  echo "EFFECTIVE_EXPECTED_CARGO_LOCK_SHA256=${EFFECTIVE_EXPECTED_CARGO_LOCK_SHA256}"
  echo "EFFECTIVE_BUILD_CMD=${EFFECTIVE_BUILD_CMD}"
  echo "EFFECTIVE_EXPECTED_RUSTC_VERSION=${EFFECTIVE_EXPECTED_RUSTC_VERSION}"
  echo "EFFECTIVE_EXPECTED_DOTSLASH_VERSION=${EFFECTIVE_EXPECTED_DOTSLASH_VERSION}"
  echo "WEAVER_FORGE_EXTERNAL_EXPECTED_COMMIT=${WEAVER_FORGE_EXTERNAL_EXPECTED_COMMIT:-<not_supplied>}"
  echo "WORK_ROOT=${WORK_ROOT}"
  echo "WORK_ROOT_RESOLVED=${WORK_ROOT_RESOLVED}"
  echo "WF_DIR=${WF_DIR}"
  echo "SRC_DIR=${SRC_DIR}"
  echo "CARGO_TARGET_DIR=${CARGO_TARGET_DIR}"
  echo "BOOTSTRAP_CARGO_TARGET_DIR=${BOOTSTRAP_CARGO_TARGET_DIR}"
  echo "EVIDENCE_DIR=${EVIDENCE_DIR}"
  echo "--- validator output policy ---"
  echo "validator_output_policy=Validator (validate_witness_evidence.py) stdout/stderr MUST be captured OUTSIDE EVIDENCE_DIR. Do not redirect validator output into EVIDENCE_DIR at any time, and never write validator output into the evidence tree after the final manifest has been generated."
  echo "--- manifest lifecycle ---"
  echo "manifest_lifecycle=This run writes a PRELIMINARY EVIDENCE_MANIFEST.sha256 covering automated evidence only. Finalization is REQUIRED after WITNESS_STATEMENT.md, WITNESS_VERDICT.md, DEVIATIONS.txt, and REDACTIONS.md are completed; regenerate the manifest from within EVIDENCE_DIR using ./relative paths before submission."
} > "${EVIDENCE_DIR}/HOST_RUN_METADATA.txt"

{
  echo "evidence_schema_version=1"
  echo "status=RECORDED"
  echo "canonical_run=$([[ "${NONCANONICAL_RUN}" -eq 1 ]] && echo NO || echo YES)"
  echo "verdict_ceiling=${VERDICT_CEILING}"
  if [[ "${NONCANONICAL_RUN}" -eq 1 ]]; then
    echo "noncanonical_deviation_flag_present=yes"
    echo "changed_identity_field_count=${#CHANGED_IDENTITY_FIELDS[@]}"
    echo "--- changed identity fields ---"
    local_field=""
    for local_field in "${CHANGED_IDENTITY_FIELDS[@]}"; do
      echo "  ${local_field}"
    done
    echo "verdict_impact=Witness proposed verdict PASS is PREVENTED for this run. Proposed verdict is capped at ${VERDICT_CEILING}."
  else
    echo "noncanonical_deviation_flag_present=no"
    echo "changed_identity_field_count=0"
    echo "verdict_impact=No automated identity deviations recorded; this section does not by itself establish PASS eligibility for the other classification rules in WITNESS_CLASSIFICATION.md."
  fi
} > "${EVIDENCE_DIR}/DEVIATIONS.txt"

echo "--- WORK_ROOT deletion targets recorded to HOST_RUN_METADATA.txt ---" >> "${EVIDENCE_DIR}/HOST_RUN_METADATA.txt"
work_root_managed_targets >> "${EVIDENCE_DIR}/HOST_RUN_METADATA.txt"

# ---------------------------------------------------------------------------
# Host environment recording
# ---------------------------------------------------------------------------
record_host_environment() {
  local utc now_os now_kernel now_arch cpu ram disk docker_client docker_server docker_ctx platform wsl
  utc="$(utc_now)"
  now_os="$(uname -s 2>/dev/null || echo UNKNOWN)"
  now_kernel="$(uname -r 2>/dev/null || echo UNKNOWN)"
  now_arch="$(uname -m 2>/dev/null || echo UNKNOWN)"
  if command -v lscpu >/dev/null 2>&1; then
    cpu="$(lscpu 2>/dev/null | head -n 20 || echo UNKNOWN)"
  else
    cpu="UNKNOWN"
  fi
  if command -v free >/dev/null 2>&1; then
    ram="$(free -h 2>/dev/null | head -n 5 || echo UNKNOWN)"
  else
    ram="UNKNOWN"
  fi
  if command -v df >/dev/null 2>&1; then
    disk="$(df -h "${WORK_ROOT}" 2>/dev/null || echo UNKNOWN)"
  else
    disk="UNKNOWN"
  fi
  if command -v docker >/dev/null 2>&1; then
    docker_client="$(docker version --format '{{.Client.Version}}' 2>/dev/null || echo UNKNOWN)"
    docker_server="$(docker version --format '{{.Server.Version}}' 2>/dev/null || echo UNKNOWN)"
    docker_ctx="$(docker context show 2>/dev/null || echo UNKNOWN)"
  else
    docker_client="UNKNOWN"
    docker_server="UNKNOWN"
    docker_ctx="UNKNOWN"
  fi
  platform="linux/amd64"
  if grep -qi microsoft /proc/version 2>/dev/null; then
    wsl="likely_WSL2"
  else
    wsl="UNKNOWN"
  fi
  {
    echo "evidence_schema_version=1"
    echo "status=OK"
    echo "record_utc=${utc}"
    echo "host_os=${now_os}"
    echo "host_kernel=${now_kernel}"
    echo "host_architecture=${now_arch}"
    echo "cpu_information<<EOF"
    echo "${cpu}"
    echo "EOF"
    echo "ram<<EOF"
    echo "${ram}"
    echo "EOF"
    echo "available_disk<<EOF"
    echo "${disk}"
    echo "EOF"
    echo "docker_client_version=${docker_client}"
    echo "docker_server_version=${docker_server}"
    echo "docker_context=${docker_ctx}"
    echo "canonical_platform=${platform}"
    echo "wsl2_indicator=${wsl}"
  } > "${EVIDENCE_DIR}/ENVIRONMENT.txt"
}
mark_stage "host_environment_recording"
record_host_environment

# ---------------------------------------------------------------------------
# Weaver Forge package clone + tag resolution + clean/commit enforcement
# ---------------------------------------------------------------------------
mark_stage "weaver_forge_package_clone"
WF_CLONE_START="$(utc_now)"
if [[ -d "${WF_DIR}/.git" ]]; then
  rm -rf "${WF_DIR}"
fi
git clone "${EFFECTIVE_WEAVER_FORGE_URL}" "${WF_DIR}"
git -C "${WF_DIR}" fetch --tags origin
WF_CLONE_END="$(utc_now)"

if ! git -C "${WF_DIR}" rev-parse "refs/tags/${EFFECTIVE_WEAVER_FORGE_TAG}^{commit}" >/dev/null 2>&1; then
  {
    echo "evidence_schema_version=1"
    echo "status=FAILED"
    echo "reason=requested_tag_not_present_on_origin"
    echo "weaver_forge_url=${EFFECTIVE_WEAVER_FORGE_URL}"
    echo "weaver_forge_tag_requested=${EFFECTIVE_WEAVER_FORGE_TAG}"
    echo "available_witness_tags<<EOF"
    git -C "${WF_DIR}" tag -l 'grok-build-witness-*' 2>/dev/null || true
    echo "EOF"
  } > "${EVIDENCE_DIR}/WEAVER_FORGE_PACKAGE_IDENTITY.txt"
  abort 3 "Weaver Forge tag ${EFFECTIVE_WEAVER_FORGE_TAG} is not present on origin"
fi
WEAVER_FORGE_RESOLVED_COMMIT="$(git -C "${WF_DIR}" rev-parse "refs/tags/${EFFECTIVE_WEAVER_FORGE_TAG}^{commit}")"
if [[ ! "${WEAVER_FORGE_RESOLVED_COMMIT}" =~ ^[0-9a-f]{40}$ ]]; then
  abort 3 "Weaver Forge tag ${EFFECTIVE_WEAVER_FORGE_TAG} did not resolve to a full 40-char lowercase commit (got: ${WEAVER_FORGE_RESOLVED_COMMIT})"
fi
git -C "${WF_DIR}" checkout --detach "${WEAVER_FORGE_RESOLVED_COMMIT}"

WF_HEAD="$(git -C "${WF_DIR}" rev-parse HEAD)"
WF_STATUS="$(git -C "${WF_DIR}" status --porcelain)"
WF_CLEAN="yes"
[[ -n "${WF_STATUS}" ]] && WF_CLEAN="no"

TAG_HEAD_MATCH="yes"
if [[ "${WF_HEAD}" != "${WEAVER_FORGE_RESOLVED_COMMIT}" ]]; then
  TAG_HEAD_MATCH="no"
fi

# Detached-state probe (informational + enforcement: we required --detach above).
WF_DETACHED="yes"
if git -C "${WF_DIR}" symbolic-ref -q HEAD >/dev/null 2>&1; then
  WF_DETACHED="no"
fi

EXTERNAL_EXPECTED_SUPPLIED="no"
EXTERNAL_EXPECTED_MATCH="not_supplied"
if [[ -n "${WEAVER_FORGE_EXTERNAL_EXPECTED_COMMIT}" ]]; then
  EXTERNAL_EXPECTED_SUPPLIED="yes"
  if [[ ! "${WEAVER_FORGE_EXTERNAL_EXPECTED_COMMIT}" =~ ^[0-9a-f]{40}$ ]]; then
    abort 3 "WEAVER_FORGE_EXTERNAL_EXPECTED_COMMIT must be a full 40-char lowercase hex commit when supplied"
  fi
  if [[ "${WEAVER_FORGE_RESOLVED_COMMIT}" == "${WEAVER_FORGE_EXTERNAL_EXPECTED_COMMIT}" && "${WF_HEAD}" == "${WEAVER_FORGE_EXTERNAL_EXPECTED_COMMIT}" ]]; then
    EXTERNAL_EXPECTED_MATCH="yes"
  else
    EXTERNAL_EXPECTED_MATCH="no"
  fi
fi

{
  echo "evidence_schema_version=1"
  echo "status=OK"
  echo "witness_id=${WITNESS_ID}"
  echo "run_id=${RUN_ID}"
  echo "package_version=1.0.0-rc3"
  echo "weaver_forge_url=${EFFECTIVE_WEAVER_FORGE_URL}"
  echo "weaver_forge_tag_requested=${EFFECTIVE_WEAVER_FORGE_TAG}"
  echo "weaver_forge_commit_resolved=${WEAVER_FORGE_RESOLVED_COMMIT}"
  echo "package_clone_head=${WF_HEAD}"
  echo "package_clone_detached=${WF_DETACHED}"
  echo "package_clone_clean_status=${WF_CLEAN}"
  echo "tag_head_match=${TAG_HEAD_MATCH}"
  echo "package_commit_authority=annotated_tag_resolution"
  echo "external_expected_commit_supplied=${EXTERNAL_EXPECTED_SUPPLIED}"
  echo "external_expected_commit=${WEAVER_FORGE_EXTERNAL_EXPECTED_COMMIT:-<not_supplied>}"
  echo "external_expected_commit_match=${EXTERNAL_EXPECTED_MATCH}"
  echo "grok_build_source_commit_expected=${EFFECTIVE_GROK_BUILD_COMMIT}"
  echo "canonical_run=$([[ "${NONCANONICAL_RUN}" -eq 1 ]] && echo no || echo yes)"
} > "${EVIDENCE_DIR}/WEAVER_FORGE_PACKAGE_IDENTITY.txt"

{
  echo "evidence_schema_version=1"
  echo "=== weaver_forge_package_acquisition ==="
  echo "utc_weaver_forge_start=${WF_CLONE_START}"
  echo "utc_weaver_forge_end=${WF_CLONE_END}"
  echo "weaver_forge_url=${EFFECTIVE_WEAVER_FORGE_URL}"
  echo "weaver_forge_tag_requested=${EFFECTIVE_WEAVER_FORGE_TAG}"
  echo "weaver_forge_commit_resolved=${WEAVER_FORGE_RESOLVED_COMMIT}"
  echo "package_clone_head=${WF_HEAD}"
  echo "package_clone_clean_status=${WF_CLEAN}"
  echo "weaver_forge_clone_command=git clone ${EFFECTIVE_WEAVER_FORGE_URL} <work-root>/weaver-forge"
  echo "weaver_forge_fetch_command=git -C <work-root>/weaver-forge fetch --tags origin"
  echo "weaver_forge_checkout_command=git -C <work-root>/weaver-forge checkout --detach ${WEAVER_FORGE_RESOLVED_COMMIT}"
  echo "weaver_forge_detached_head=${WF_DETACHED}"
  echo "weaver_forge_clean_tree=${WF_CLEAN}"
  echo "tag_head_match=${TAG_HEAD_MATCH}"
  echo "package_commit_authority=annotated_tag_resolution"
} > "${EVIDENCE_DIR}/SOURCE_ACQUISITION.txt"

if [[ "${TAG_HEAD_MATCH}" != "yes" ]]; then
  abort 3 "Detached HEAD (${WF_HEAD}) does not equal resolved tag commit (${WEAVER_FORGE_RESOLVED_COMMIT})"
fi
if [[ "${WF_DETACHED}" != "yes" ]]; then
  abort 3 "Weaver Forge package clone is not in detached HEAD state after tag checkout"
fi
if [[ "${WF_CLEAN}" != "yes" ]]; then
  abort 3 "Weaver Forge package clone tree is not clean after detached checkout"
fi
if [[ "${EXTERNAL_EXPECTED_SUPPLIED}" == "yes" && "${EXTERNAL_EXPECTED_MATCH}" != "yes" ]]; then
  abort 3 "WEAVER_FORGE_EXTERNAL_EXPECTED_COMMIT mismatch: external=${WEAVER_FORGE_EXTERNAL_EXPECTED_COMMIT} resolved_tag=${WEAVER_FORGE_RESOLVED_COMMIT} head=${WF_HEAD}"
fi

HOST_CONTAINER_SCRIPT="${WF_DIR}/external_verifications/grok-build/witness-package/scripts/container_narrow_build.sh"
if [[ ! -f "${HOST_CONTAINER_SCRIPT}" ]]; then
  abort 3 "Resolved Weaver commit missing container script at ${HOST_CONTAINER_SCRIPT}"
fi

# ---------------------------------------------------------------------------
# Grok Build source clone + HEAD/clean enforcement
# ---------------------------------------------------------------------------
mark_stage "grok_build_source_clone"
GB_CLONE_START="$(utc_now)"
if [[ -d "${SRC_DIR}/.git" ]]; then
  rm -rf "${SRC_DIR}"
fi
git clone "${EFFECTIVE_GROK_BUILD_URL}" "${SRC_DIR}"
git -C "${SRC_DIR}" checkout --detach "${EFFECTIVE_GROK_BUILD_COMMIT}"
GB_CLONE_END="$(utc_now)"

SRC_HEAD="$(git -C "${SRC_DIR}" rev-parse HEAD)"
SRC_STATUS="$(git -C "${SRC_DIR}" status --porcelain)"
CARGO_LOCK_BEFORE="$(sha256_of "${SRC_DIR}/Cargo.lock")"

{
  echo "evidence_schema_version=1"
  echo "status=OK"
  echo "grok_build_url=${EFFECTIVE_GROK_BUILD_URL}"
  echo "grok_build_commit_expected=${EFFECTIVE_GROK_BUILD_COMMIT}"
  echo "grok_build_commit_observed=${SRC_HEAD}"
  echo "grok_build_clean_status_porcelain=${SRC_STATUS}"
  echo "cargo_lock_sha256_before=${CARGO_LOCK_BEFORE}"
  echo "cargo_lock_sha256_expected=${EFFECTIVE_EXPECTED_CARGO_LOCK_SHA256}"
} > "${EVIDENCE_DIR}/SOURCE_IDENTITY.txt"

{
  echo "evidence_schema_version=1"
  echo "status=OK"
  echo "=== grok_build_source_acquisition ==="
  echo "utc_grok_build_start=${GB_CLONE_START}"
  echo "utc_grok_build_end=${GB_CLONE_END}"
  echo "grok_build_url=${EFFECTIVE_GROK_BUILD_URL}"
  echo "grok_build_commit_requested=${EFFECTIVE_GROK_BUILD_COMMIT}"
  echo "grok_build_commit_observed=${SRC_HEAD}"
  echo "grok_build_clone_command=git clone ${EFFECTIVE_GROK_BUILD_URL} <work-root>/grok-build-src"
  echo "grok_build_checkout_command=git -C <work-root>/grok-build-src checkout --detach ${EFFECTIVE_GROK_BUILD_COMMIT}"
  echo "grok_build_detached_head=yes"
  echo "grok_build_clean_tree=$([[ -z "${SRC_STATUS}" ]] && echo yes || echo no)"
  echo "fresh_clones=yes"
  echo "owner_caches_used=no"
  echo "status=OK"
} >> "${EVIDENCE_DIR}/SOURCE_ACQUISITION.txt"

if [[ "${SRC_HEAD}" != "${EFFECTIVE_GROK_BUILD_COMMIT}" ]]; then
  abort 4 "Grok Build source commit mismatch"
fi
if [[ -n "${SRC_STATUS}" ]]; then
  abort 4 "Grok Build source tree not clean after detached checkout"
fi

# ---------------------------------------------------------------------------
# Cargo.lock direct enforcement — BEFORE Docker
# ---------------------------------------------------------------------------
mark_stage "cargo_lock_pre_docker"
CARGO_LOCK_PRE_MATCH="no"
[[ "${CARGO_LOCK_BEFORE}" == "${EFFECTIVE_EXPECTED_CARGO_LOCK_SHA256}" ]] && CARGO_LOCK_PRE_MATCH="yes"
{
  echo "evidence_schema_version=1"
  echo "status=CHECKED"
  echo "stage=pre_docker"
  echo "cargo_lock_sha256_expected=${EFFECTIVE_EXPECTED_CARGO_LOCK_SHA256}"
  echo "cargo_lock_sha256_observed=${CARGO_LOCK_BEFORE}"
  echo "match=${CARGO_LOCK_PRE_MATCH}"
} > "${EVIDENCE_DIR}/CARGO_LOCK_INTEGRITY.txt"

if [[ "${CARGO_LOCK_PRE_MATCH}" != "yes" ]]; then
  abort 4 "Cargo.lock SHA-256 mismatch BEFORE Docker (expected ${EFFECTIVE_EXPECTED_CARGO_LOCK_SHA256}, observed ${CARGO_LOCK_BEFORE})"
fi

# ---------------------------------------------------------------------------
# Isolated writable directories + clean target proof
# ---------------------------------------------------------------------------
mark_stage "isolated_directory_setup"
rm -rf "${CARGO_HOME_DIR}" "${CARGO_TARGET_DIR}" "${BOOTSTRAP_CARGO_TARGET_DIR}" "${DOTSLASH_CACHE_DIR}" "${HOME_DIR}" "${BOOTSTRAP_DIR}"
mkdir -p "${CARGO_HOME_DIR}" "${CARGO_TARGET_DIR}" "${BOOTSTRAP_CARGO_TARGET_DIR}" "${DOTSLASH_CACHE_DIR}" "${HOME_DIR}" "${BOOTSTRAP_DIR}"

mark_stage "clean_target_proof"
TARGET_CREATED_UTC="$(utc_now)"
TARGET_LISTING="$(ls -la "${CARGO_TARGET_DIR}" 2>&1 || true)"
TARGET_FIND="$(find "${CARGO_TARGET_DIR}" -mindepth 1 -print 2>/dev/null || true)"
TARGET_COUNT="$(find "${CARGO_TARGET_DIR}" -mindepth 1 | wc -l | tr -d ' ')"

{
  echo "evidence_schema_version=1"
  echo "status=CHECKED"
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
  abort 5 "Host pre-build target directory not empty"
fi

# ---------------------------------------------------------------------------
# Docker image pull — FATAL on nonzero exit; never fall back to a cached image
# ---------------------------------------------------------------------------
mark_stage "image_pull"
IMAGE_PULL_UTC="$(utc_now)"
DOCKER_PULL_CMD="docker pull --platform linux/amd64 ${EFFECTIVE_RUST_IMAGE}"
set +e
docker pull --platform linux/amd64 "${EFFECTIVE_RUST_IMAGE}" > "${EVIDENCE_DIR}/IMAGE_PULL_STDOUT.txt" 2> "${EVIDENCE_DIR}/IMAGE_PULL_STDERR.txt"
IMAGE_PULL_EXIT=$?
set -e

if [[ "${IMAGE_PULL_EXIT}" -ne 0 ]]; then
  {
    echo "evidence_schema_version=1"
    echo "status=FAILED"
    echo "reason=docker_pull_nonzero_exit"
    echo "requested_image_string=${EFFECTIVE_RUST_IMAGE}"
    echo "docker_pull_command=${DOCKER_PULL_CMD}"
    echo "docker_pull_exit_code=${IMAGE_PULL_EXIT}"
    echo "docker_pull_stdout_file=IMAGE_PULL_STDOUT.txt"
    echo "docker_pull_stderr_file=IMAGE_PULL_STDERR.txt"
    echo "proceeded_to_inspect_or_run=NO"
    echo "cached_image_fallback_used=NO"
    echo "product_executed=NO"
    echo "ldd_used=NO"
  } > "${EVIDENCE_DIR}/IMAGE_IDENTITY.txt"
  OUTCOME="INFRASTRUCTURE_FAILURE"
  FAILURE_STAGE="image_pull"
  {
    echo "evidence_schema_version=1"
    echo "docker_started_utc=NOT_STARTED"
    echo "docker_finished_utc=NOT_STARTED"
    echo "docker_exit_code=NOT_STARTED"
    echo "container_platform=linux/amd64"
    echo "network_mode=bridge"
    echo "product_executed=NO"
    echo "ldd_used=NO"
    echo "outcome=${OUTCOME}"
    echo "failure_stage=${FAILURE_STAGE}"
    echo "image_pull_exit_code=${IMAGE_PULL_EXIT}"
  } > "${EVIDENCE_DIR}/DOCKER_EXIT_CODE.txt"
  {
    echo "evidence_schema_version=1"
    echo "outcome=${OUTCOME}"
    echo "image_pull_exit_code=${IMAGE_PULL_EXIT}"
  } > "${EVIDENCE_DIR}/BUILD_TIMING.txt"
  abort "${IMAGE_PULL_EXIT}" "docker pull failed (image pull is FATAL); refusing to proceed with a cached/local image"
fi

# ---------------------------------------------------------------------------
# Image identity enforcement — must pass BEFORE docker run
# ---------------------------------------------------------------------------
mark_stage "image_identity_enforcement"
REQUESTED_DIGEST=""
if [[ "${EFFECTIVE_RUST_IMAGE}" == *"@sha256:"* ]]; then
  REQUESTED_DIGEST="sha256:${EFFECTIVE_RUST_IMAGE##*@sha256:}"
fi

DOCKER_INSPECT_ID_CMD="docker inspect --format {{.Id}} ${EFFECTIVE_RUST_IMAGE}"
DOCKER_INSPECT_REPODIGESTS_CMD="docker inspect --format {{json .RepoDigests}} ${EFFECTIVE_RUST_IMAGE}"
DOCKER_INSPECT_OS_CMD="docker inspect --format {{.Os}} ${EFFECTIVE_RUST_IMAGE}"
DOCKER_INSPECT_ARCH_CMD="docker inspect --format {{.Architecture}} ${EFFECTIVE_RUST_IMAGE}"

DOCKER_CLIENT_VER="$(docker version --format '{{.Client.Version}}' 2>/dev/null || echo UNKNOWN)"
DOCKER_SERVER_VER="$(docker version --format '{{.Server.Version}}' 2>/dev/null || echo UNKNOWN)"

set +e
IMAGE_ID="$(docker inspect --format '{{.Id}}' "${EFFECTIVE_RUST_IMAGE}" 2>/dev/null)"
IMAGE_ID_EXIT=$?
REPO_DIGESTS="$(docker inspect --format '{{json .RepoDigests}}' "${EFFECTIVE_RUST_IMAGE}" 2>/dev/null)"
REPO_DIGESTS_EXIT=$?
IMAGE_OS="$(docker inspect --format '{{.Os}}' "${EFFECTIVE_RUST_IMAGE}" 2>/dev/null)"
IMAGE_OS_EXIT=$?
IMAGE_ARCH="$(docker inspect --format '{{.Architecture}}' "${EFFECTIVE_RUST_IMAGE}" 2>/dev/null)"
IMAGE_ARCH_EXIT=$?
set -e

[[ -z "${IMAGE_ID}" ]] && IMAGE_ID="UNKNOWN"
[[ -z "${REPO_DIGESTS}" ]] && REPO_DIGESTS="UNKNOWN"
[[ -z "${IMAGE_OS}" ]] && IMAGE_OS="UNKNOWN"
[[ -z "${IMAGE_ARCH}" ]] && IMAGE_ARCH="UNKNOWN"
IMAGE_PLATFORM="${IMAGE_OS}/${IMAGE_ARCH}"

IMAGE_ID_AVAILABLE="no"
[[ "${IMAGE_ID_EXIT}" -eq 0 && "${IMAGE_ID}" != "UNKNOWN" && -n "${IMAGE_ID}" ]] && IMAGE_ID_AVAILABLE="yes"

DIGEST_MATCH_EXPECTED="no"
if [[ -n "${REQUESTED_DIGEST}" && "${REPO_DIGESTS_EXIT}" -eq 0 && "${REPO_DIGESTS}" == *"${REQUESTED_DIGEST}"* ]]; then
  DIGEST_MATCH_EXPECTED="yes"
fi

PLATFORM_MATCH_EXPECTED="no"
if [[ "${IMAGE_OS_EXIT}" -eq 0 && "${IMAGE_ARCH_EXIT}" -eq 0 && "${IMAGE_OS}" == "linux" && "${IMAGE_ARCH}" == "amd64" ]]; then
  PLATFORM_MATCH_EXPECTED="yes"
fi

{
  echo "evidence_schema_version=1"
  echo "status=OK"
  echo "utc_acquisition=${IMAGE_PULL_UTC}"
  echo "requested_image_string=${EFFECTIVE_RUST_IMAGE}"
  echo "requested_digest=${REQUESTED_DIGEST:-NONE_PARSED}"
  echo "docker_pull_command=${DOCKER_PULL_CMD}"
  echo "docker_pull_exit_code=${IMAGE_PULL_EXIT}"
  echo "docker_client_version=${DOCKER_CLIENT_VER}"
  echo "docker_server_version=${DOCKER_SERVER_VER}"
  echo "docker_inspect_image_id_command=${DOCKER_INSPECT_ID_CMD}"
  echo "docker_inspect_image_id_exit_code=${IMAGE_ID_EXIT}"
  echo "image_id=${IMAGE_ID}"
  echo "docker_inspect_repodigests_command=${DOCKER_INSPECT_REPODIGESTS_CMD}"
  echo "docker_inspect_repodigests_exit_code=${REPO_DIGESTS_EXIT}"
  echo "repo_digests=${REPO_DIGESTS}"
  echo "docker_inspect_os_command=${DOCKER_INSPECT_OS_CMD}"
  echo "docker_inspect_os_exit_code=${IMAGE_OS_EXIT}"
  echo "os=${IMAGE_OS}"
  echo "docker_inspect_architecture_command=${DOCKER_INSPECT_ARCH_CMD}"
  echo "docker_inspect_architecture_exit_code=${IMAGE_ARCH_EXIT}"
  echo "architecture=${IMAGE_ARCH}"
  echo "platform=${IMAGE_PLATFORM}"
  echo "image_id_available=${IMAGE_ID_AVAILABLE}"
  echo "digest_match_expected=${DIGEST_MATCH_EXPECTED}"
  echo "platform_match_expected=${PLATFORM_MATCH_EXPECTED}"
} > "${EVIDENCE_DIR}/IMAGE_IDENTITY.txt"

if [[ "${IMAGE_ID_AVAILABLE}" != "yes" || "${DIGEST_MATCH_EXPECTED}" != "yes" || "${PLATFORM_MATCH_EXPECTED}" != "yes" ]]; then
  abort 8 "Image identity enforcement failed (image_id_available=${IMAGE_ID_AVAILABLE} digest_match_expected=${DIGEST_MATCH_EXPECTED} platform_match_expected=${PLATFORM_MATCH_EXPECTED}); refusing to run the container"
fi

# ---------------------------------------------------------------------------
# Docker invocation (exact contract)
# ---------------------------------------------------------------------------
mark_stage "docker_run"
DOCKER_STDOUT="${EVIDENCE_DIR}/CONTAINER_STDOUT.txt"
DOCKER_STDERR="${EVIDENCE_DIR}/CONTAINER_STDERR.txt"

DOCKER_STARTED_UTC="$(utc_now)"
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
  -e GROK_BUILD_COMMIT="${EFFECTIVE_GROK_BUILD_COMMIT}" \
  -e EXPECTED_CARGO_LOCK_SHA256="${EFFECTIVE_EXPECTED_CARGO_LOCK_SHA256}" \
  -e CANONICAL_BUILD_CMD="${EFFECTIVE_BUILD_CMD}" \
  -e EXPECTED_RUSTC_VERSION="${EFFECTIVE_EXPECTED_RUSTC_VERSION}" \
  -e EXPECTED_DOTSLASH_VERSION="${EFFECTIVE_EXPECTED_DOTSLASH_VERSION}" \
  -w /src \
  "${EFFECTIVE_RUST_IMAGE}" \
  bash /witness/container_narrow_build.sh \
  >"${DOCKER_STDOUT}" 2>"${DOCKER_STDERR}"
DOCKER_EXIT=$?
set -e
DOCKER_FINISHED_UTC="$(utc_now)"

# ---------------------------------------------------------------------------
# Outcome model + Docker exit schema
# ---------------------------------------------------------------------------
mark_stage "outcome_determination"
determine_outcome_after_docker() {
  local build_exit_file="${EVIDENCE_DIR}/BUILD_EXIT_CODE.txt"
  local cargo_started="NO"
  local cargo_exit=""

  if [[ -s "${build_exit_file}" ]] && grep -q '^cargo_started=YES' "${build_exit_file}" 2>/dev/null; then
    cargo_started="YES"
    cargo_exit="$(grep -m1 '^cargo_exit_code=' "${build_exit_file}" 2>/dev/null | cut -d= -f2)"
  fi
  CARGO_STARTED="${cargo_started}"

  if [[ "${DOCKER_EXIT}" -eq 125 ]]; then
    OUTCOME="INFRASTRUCTURE_FAILURE"
    FAILURE_STAGE="docker_run_launch"
  elif [[ "${cargo_started}" != "YES" ]]; then
    OUTCOME="BUILD_NOT_STARTED"
    FAILURE_STAGE="container_bootstrap_or_pre_cargo"
  elif [[ "${cargo_exit}" != "0" ]]; then
    OUTCOME="CARGO_FAILED"
    FAILURE_STAGE="cargo_build"
  else
    local artifact="${CARGO_TARGET_DIR}/debug/xai-grok-pager"
    if [[ -f "${artifact}" ]]; then
      OUTCOME="CARGO_SUCCEEDED_ARTIFACT_PRESENT"
    else
      OUTCOME="CARGO_SUCCEEDED_ARTIFACT_MISSING"
    fi
    FAILURE_STAGE="none"
  fi
}
determine_outcome_after_docker

{
  echo "evidence_schema_version=1"
  echo "docker_started_utc=${DOCKER_STARTED_UTC}"
  echo "docker_finished_utc=${DOCKER_FINISHED_UTC}"
  echo "docker_exit_code=${DOCKER_EXIT}"
  echo "container_platform=linux/amd64"
  echo "network_mode=bridge"
  echo "product_executed=NO"
  echo "ldd_used=NO"
  echo "outcome=${OUTCOME}"
  echo "failure_stage=${FAILURE_STAGE}"
} > "${EVIDENCE_DIR}/DOCKER_EXIT_CODE.txt"

{
  echo "---"
  echo "evidence_schema_version=1"
  echo "docker_started_utc=${DOCKER_STARTED_UTC}"
  echo "docker_finished_utc=${DOCKER_FINISHED_UTC}"
  echo "docker_exit_code=${DOCKER_EXIT}"
  echo "outcome=${OUTCOME}"
} >> "${EVIDENCE_DIR}/BUILD_TIMING.txt"

# ---------------------------------------------------------------------------
# Cargo.lock direct enforcement — AFTER Docker (must remain unchanged)
# ---------------------------------------------------------------------------
mark_stage "cargo_lock_post_docker"
SRC_HEAD_AFTER="$(git -C "${SRC_DIR}" rev-parse HEAD)"
SRC_STATUS_AFTER="$(git -C "${SRC_DIR}" status --porcelain)"
CARGO_LOCK_AFTER="$(sha256_of "${SRC_DIR}/Cargo.lock")"

CARGO_LOCK_UNCHANGED="no"
[[ "${CARGO_LOCK_AFTER}" == "${CARGO_LOCK_BEFORE}" ]] && CARGO_LOCK_UNCHANGED="yes"
CARGO_LOCK_POST_MATCH="no"
[[ "${CARGO_LOCK_AFTER}" == "${EFFECTIVE_EXPECTED_CARGO_LOCK_SHA256}" ]] && CARGO_LOCK_POST_MATCH="yes"
SOURCE_HEAD_UNCHANGED="no"
[[ "${SRC_HEAD_AFTER}" == "${SRC_HEAD}" ]] && SOURCE_HEAD_UNCHANGED="yes"
SOURCE_CLEAN_AFTER="yes"
[[ -n "${SRC_STATUS_AFTER}" ]] && SOURCE_CLEAN_AFTER="no"

{
  echo "evidence_schema_version=1"
  echo "status=CHECKED"
  echo "stage=post_docker"
  echo "cargo_lock_sha256_expected=${EFFECTIVE_EXPECTED_CARGO_LOCK_SHA256}"
  echo "cargo_lock_sha256_before=${CARGO_LOCK_BEFORE}"
  echo "cargo_lock_sha256_after=${CARGO_LOCK_AFTER}"
  echo "cargo_lock_unchanged=${CARGO_LOCK_UNCHANGED}"
  echo "cargo_lock_matches_expected=${CARGO_LOCK_POST_MATCH}"
  echo "source_head_before=${SRC_HEAD}"
  echo "source_head_after=${SRC_HEAD_AFTER}"
  echo "source_head_unchanged=${SOURCE_HEAD_UNCHANGED}"
  echo "source_clean_after=${SOURCE_CLEAN_AFTER}"
} >> "${EVIDENCE_DIR}/CARGO_LOCK_INTEGRITY.txt"

POST_BUILD_INTEGRITY_OK="yes"
if [[ "${CARGO_LOCK_UNCHANGED}" != "yes" || "${SOURCE_HEAD_UNCHANGED}" != "yes" || "${SOURCE_CLEAN_AFTER}" != "yes" ]]; then
  POST_BUILD_INTEGRITY_OK="no"
fi

# ---------------------------------------------------------------------------
# Post-build integrity evidence
# ---------------------------------------------------------------------------
mark_stage "post_build_integrity"
ARTIFACT_PATH="${CARGO_TARGET_DIR}/debug/xai-grok-pager"
ARTIFACT_EXISTS="no"
[[ -f "${ARTIFACT_PATH}" ]] && ARTIFACT_EXISTS="yes"

{
  echo "evidence_schema_version=1"
  echo "status=OK"
  echo "source_head_before=${SRC_HEAD}"
  echo "source_head_after=${SRC_HEAD_AFTER}"
  echo "source_head_unchanged=${SOURCE_HEAD_UNCHANGED}"
  echo "source_clean_before=${SRC_STATUS}"
  echo "source_clean_after=${SRC_STATUS_AFTER}"
  echo "cargo_lock_sha256_before=${CARGO_LOCK_BEFORE}"
  echo "cargo_lock_sha256_after=${CARGO_LOCK_AFTER}"
  echo "cargo_lock_unchanged=${CARGO_LOCK_UNCHANGED}"
  echo "artifact_path=${ARTIFACT_PATH}"
  echo "artifact_exists=${ARTIFACT_EXISTS}"
  echo "docker_exit_code=${DOCKER_EXIT}"
  echo "outcome=${OUTCOME}"
  echo "post_build_integrity_ok=${POST_BUILD_INTEGRITY_OK}"
} > "${EVIDENCE_DIR}/POST_BUILD_INTEGRITY.txt"

# ---------------------------------------------------------------------------
# Manifest lifecycle — preliminary manifest, finalization required later.
# ---------------------------------------------------------------------------
mark_stage "manifest_generation"
(
  cd "${EVIDENCE_DIR}"
  find . -type f ! -name 'EVIDENCE_MANIFEST.sha256' -print0 | sort -z | xargs -0 sha256sum
) > "${EVIDENCE_DIR}/EVIDENCE_MANIFEST.sha256"
{
  echo "manifest_generation=preliminary"
  echo "manifest_finalization_required=yes (regenerate after WITNESS_STATEMENT.md, WITNESS_VERDICT.md, DEVIATIONS.txt, REDACTIONS.md)"
  echo "manifest_generation_command=cd \"\${EVIDENCE_DIR}\" && find . -type f ! -name 'EVIDENCE_MANIFEST.sha256' -print0 | sort -z | xargs -0 sha256sum > EVIDENCE_MANIFEST.sha256"
  echo "utc_end=$(utc_now)"
  echo "final_outcome=${OUTCOME}"
  echo "final_failure_stage=${FAILURE_STAGE}"
  echo "final_verdict_ceiling=${VERDICT_CEILING}"
  echo "final_canonical_run=$([[ "${NONCANONICAL_RUN}" -eq 1 ]] && echo NO || echo YES)"
} >> "${EVIDENCE_DIR}/HOST_RUN_METADATA.txt"

# ---------------------------------------------------------------------------
# Summary + exit code
# ---------------------------------------------------------------------------
FINAL_EXIT_CODE="${DOCKER_EXIT}"
if [[ "${POST_BUILD_INTEGRITY_OK}" != "yes" ]]; then
  FINAL_EXIT_CODE=9
fi

echo "--- Witness host summary (conservative) ---"
echo "run_id=${RUN_ID}"
echo "canonical_run=$([[ "${NONCANONICAL_RUN}" -eq 1 ]] && echo NO || echo YES)"
echo "verdict_ceiling=${VERDICT_CEILING}"
echo "weaver_forge_tag=${EFFECTIVE_WEAVER_FORGE_TAG}"
echo "weaver_forge_commit=${WF_HEAD}"
echo "grok_build_commit=${EFFECTIVE_GROK_BUILD_COMMIT}"
echo "docker_exit_code=${DOCKER_EXIT}"
echo "outcome=${OUTCOME}"
echo "failure_stage=${FAILURE_STAGE}"
echo "artifact_exists=${ARTIFACT_EXISTS}"
echo "post_build_integrity_ok=${POST_BUILD_INTEGRITY_OK}"
echo "evidence_dir=${EVIDENCE_DIR}"
echo "product_executed=NO (orchestrator)"
echo "ldd_used=NO (orchestrator)"
echo "Validator stdout/stderr must be captured OUTSIDE the evidence directory."
echo "Submit evidence per WITNESS_SUBMISSION.md after redaction review and manifest finalization."

exit "${FINAL_EXIT_CODE}"
