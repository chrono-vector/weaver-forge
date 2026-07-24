#!/usr/bin/env bash
# Independent Witness host orchestrator — Grok Build narrow clean rebuild.
# Author-only helper: do not execute from owner remediation sessions without Witness independence.
#
# Package version 1.0.0-rc4 (C2E-5 host-orchestrator remediation). Rewritten to align with the
# rc4 container_narrow_build.sh evidence schema (BEGIN_SCHEMA_BLOCK / END_SCHEMA_BLOCK, explicit
# outcome model) and to close the host-side blockers recorded in
# evidence/rc3-static-blind-audit/BATCH_2_FINDINGS.md and BATCH_3_FINDINGS.md (RC3B-003, -005,
# -006, -007, -008, -010, -012, -013, -019, -020, -021, -024).
#
# Canonical identity constants are immutable and separate from the "effective" values actually
# used for a run. Any effective value that differs from its canonical counterpart requires the
# explicit --noncanonical-deviation flag; without it the script refuses to run rather than
# silently accepting an environment-variable override.
#
# Pipeline stages are numbered STEP 1..STEP 22 in comments and in mark_stage() labels below, for
# unambiguous cross-reference between this file, evidence, and remediation records. STEP 10 is
# the host-side ENVIRONMENT.txt generator (dual-owned; the container appends toolchain facts).
#
# Outcome authority (RC3B-008 / Phase 3D): once the container has run, the single source of truth
# for `outcome` is the container-written BUILD_EXIT_CODE.txt. The host NEVER reconstructs an
# ordinary outcome from cargo_started/artifact-presence/raw Docker exit code alone, and NEVER
# overwrites a valid container-owned BUILD_EXIT_CODE.txt after Docker. Missing/invalid container
# results are recorded in host-owned HOST_OUTCOME_INGESTION.txt (see parse_container_result_tuple
# and finalize_post_docker_host_failure). preliminary_success_eligible remains NO until Phase 3F.
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
readonly PACKAGE_VERSION="1.0.0-rc4"
readonly CANONICAL_WEAVER_FORGE_URL="https://github.com/chrono-vector/weaver-forge.git"
readonly CANONICAL_WEAVER_FORGE_TAG="grok-build-witness-v1.0.0-rc4"
# Package commit identity is derived at runtime from the annotated tag
# (refs/tags/${CANONICAL_WEAVER_FORGE_TAG}^{commit}). The tagged package MUST
# NOT embed its own future commit hash — that creates a self-referential
# commit problem. Do not reintroduce CANONICAL_WEAVER_FORGE_EXPECTED_COMMIT.
readonly CANONICAL_GROK_BUILD_URL="https://github.com/xai-org/grok-build.git"
readonly CANONICAL_GROK_BUILD_COMMIT="98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce"
readonly CANONICAL_RUST_IMAGE="docker.io/library/rust@sha256:6ca5ad23231207874325a751b9df584d51cd42c066c74c6963c264e3233c3e8e"
readonly CANONICAL_IMAGE_DIGEST="sha256:6ca5ad23231207874325a751b9df584d51cd42c066c74c6963c264e3233c3e8e"
readonly CANONICAL_CARGO_LOCK_SHA256="1512bb4fef0c1166c6a15a3398da9593903be1759b759ce78d9958913e61b421"
readonly CANONICAL_BUILD_CMD="cargo build -p xai-grok-pager-bin --locked"
readonly CANONICAL_EXPECTED_RUSTC_VERSION="1.92.0"
readonly CANONICAL_EXPECTED_DOTSLASH_VERSION="0.5.7"

# Defensive self-check: CANONICAL_IMAGE_DIGEST must be embedded verbatim in CANONICAL_RUST_IMAGE.
# A drift here would silently desynchronize two constants that must always agree.
if [[ "${CANONICAL_RUST_IMAGE}" != *"@${CANONICAL_IMAGE_DIGEST}" ]]; then
  echo "FATAL[self-check]: CANONICAL_IMAGE_DIGEST is not embedded in CANONICAL_RUST_IMAGE; refusing to run with inconsistent constants" >&2
  exit 2
fi

# ---------------------------------------------------------------------------
# Effective values (default = canonical; overridable via environment, but
# any actual deviation is refused unless --noncanonical-deviation is given).
# ---------------------------------------------------------------------------
EFFECTIVE_WEAVER_FORGE_URL="${WEAVER_FORGE_URL:-${CANONICAL_WEAVER_FORGE_URL}}"
EFFECTIVE_WEAVER_FORGE_TAG="${WEAVER_FORGE_TAG:-${CANONICAL_WEAVER_FORGE_TAG}}"
EFFECTIVE_GROK_BUILD_URL="${GROK_BUILD_URL:-${CANONICAL_GROK_BUILD_URL}}"
EFFECTIVE_GROK_BUILD_COMMIT="${GROK_BUILD_COMMIT:-${CANONICAL_GROK_BUILD_COMMIT}}"
EFFECTIVE_RUST_IMAGE="${RUST_IMAGE:-${CANONICAL_RUST_IMAGE}}"
EFFECTIVE_EXPECTED_CARGO_LOCK_SHA256="${EXPECTED_CARGO_LOCK_SHA256:-${CANONICAL_CARGO_LOCK_SHA256}}"
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

# Closed auxiliary-file allow-list (RC3B-021): the ONLY host-written files under
# EVIDENCE_DIR that are not in MANDATORY_EVIDENCE_FILES and not a manual Witness
# file (WITNESS_STATEMENT.md / WITNESS_VERDICT.md / DEVIATIONS.txt / REDACTIONS.md /
# EVIDENCE_MANIFEST.sha256, none of which this script writes to completion). Any
# other regular file found under EVIDENCE_DIR at the end of the automated run is a
# structural violation (see enforce_closed_aux_inventory()).
readonly ALLOWED_AUX_EVIDENCE_FILES=(
  HOST_RUN_METADATA.txt
  IMAGE_PULL_STDOUT.txt
  IMAGE_PULL_STDERR.txt
  CARGO_LOCK_INTEGRITY.txt
  HOST_OUTCOME_INGESTION.txt
)

# Required (not "aux") file this script also writes directly, outside the
# NOT_REACHED-initialized MANDATORY_EVIDENCE_FILES loop.
readonly DEVIATIONS_FILE_NAME="DEVIATIONS.txt"

# Fixed outcome vocabulary (must match container_narrow_build.sh and
# templates/validate_witness_evidence.py exactly).
readonly OUTCOME_ALLOWED_VALUES=(
  BUILD_NOT_STARTED
  CARGO_FAILED
  CARGO_SUCCEEDED_ARTIFACT_MISSING
  CARGO_SUCCEEDED_ARTIFACT_PRESENT
  INFRASTRUCTURE_FAILURE
)

# Nonterminal sentinels — never accepted as terminal container outcomes (Phase 3B contract).
readonly OUTCOME_NONTERMINAL_SENTINELS=(
  NOT_REACHED
  NOT_STARTED
  NOT_APPLICABLE
  RECORDED
  CHECKED
  pending
  pending_container_toolchain_capture
  bootstrap_complete
)

readonly HOST_OUTCOME_INGESTION_SCHEMA_VERSION="1"
readonly HOST_OUTCOME_INGESTION_FILE_NAME="HOST_OUTCOME_INGESTION.txt"

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
DOCKER_STARTED_EPOCH=""
DOCKER_FINISHED_EPOCH=""
DOCKER_EXIT=""
OUTCOME="BUILD_NOT_STARTED"
FAILURE_STAGE="none"

WF_TAG_RAW_OBJECT_TYPE=""
EVIDENCE_DIR=""
# Pre-Docker source integrity snapshot (Phase 2B); filled before docker run.
PRE_DOCKER_SRC_HEAD=""
PRE_DOCKER_SRC_CLEAN=""
# Load-bearing gate: every Docker CLI invocation (including docker version /
# docker context show metadata) is refused until identity closure sets this to
# exactly "yes" (RC4B-004 / Phase 2A).
IDENTITY_GATE_CLOSED="no"

# Phase 3D host outcome-ingestion state (reset by main; safe defaults for sourced tests).
HOST_FINALIZING_IN_PROGRESS="NO"
HOST_OUTCOME_INGESTION_WRITTEN="NO"
HOST_OUTCOME_INGESTION_FINGERPRINT=""
CONTAINER_RESULT_PRESENCE="MISSING"
CONTAINER_RESULT_VALID="NO"
CONTAINER_RESULT_ERROR="none"
PARSED_CONTAINER_OUTCOME=""
PARSED_CARGO_STARTED=""
PARSED_CARGO_EXIT_CODE=""
PARSED_ARTIFACT_PRESENT=""
PARSED_ARTIFACT_IDENTITY_COMPLETE=""
PARSED_STATIC_INSPECTION_COMPLETE=""
PARSED_SCHEMA_VERSION=""
PARSED_FAILURE_STAGE=""
PARSED_RUN_ID=""
HOST_INFRASTRUCTURE_STATUS="OK"
HOST_SOURCE_INTEGRITY_STATUS="OK"
HOST_POST_BUILD_INTEGRITY_STATUS="OK"
HOST_EVIDENCE_COMPLETENESS_STATUS="INCOMPLETE"
PRELIMINARY_SUCCESS_ELIGIBLE="NO"

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

# Read the first "key=value" line from a file, tolerant of no match (never
# trips `set -e`). Returns `default` when the key is absent or the file is
# missing.
read_first_kv() {
  local file="$1" key="$2" default="${3:-NOT_RECORDED}"
  local line=""
  if [[ -f "${file}" ]]; then
    line="$(grep -m1 "^${key}=" "${file}" 2>/dev/null)" || true
  fi
  if [[ -n "${line}" ]]; then
    printf '%s' "${line#*=}"
  else
    printf '%s' "${default}"
  fi
}

# Symlink-safe reset of a single managed scratch/child path (RC3B-010): a
# symlink is unlinked directly and NEVER followed into `rm -rf`. This is
# independent of, and in addition to, the WORK_ROOT-level guard below.
safe_reset_managed_path() {
  local p="$1"
  if [[ -L "${p}" ]]; then
    rm -f -- "${p}"
    return 0
  fi
  if [[ -e "${p}" ]]; then
    rm -rf -- "${p}"
  fi
}

is_allowed_outcome() {
  local v="$1" o
  for o in "${OUTCOME_ALLOWED_VALUES[@]}"; do
    [[ "${v}" == "${o}" ]] && return 0
  done
  return 1
}

is_nonterminal_outcome_sentinel() {
  local v="$1" s
  for s in "${OUTCOME_NONTERMINAL_SENTINELS[@]}"; do
    [[ "${v}" == "${s}" ]] && return 0
  done
  return 1
}

reject_field_newlines() {
  local label="$1"
  local value="$2"
  if [[ "${value}" == *$'\n'* || "${value}" == *$'\r'* ]]; then
    echo "FATAL: field ${label} contains CR/LF; refusing to write" >&2
    return 1
  fi
  return 0
}

# Atomic same-directory write + rename for host-owned evidence. No eval.
write_evidence_file_atomic() {
  local dest="$1"
  local dir base tmp
  if [[ -z "${dest}" ]]; then
    echo "write_evidence_file_atomic: empty destination" >&2
    return 1
  fi
  dir="$(dirname -- "${dest}")"
  base="$(basename -- "${dest}")"
  if [[ ! -d "${dir}" ]]; then
    echo "write_evidence_file_atomic: evidence directory missing: ${dir}" >&2
    return 1
  fi
  tmp="${dir}/.tmp.${base}.$$.${RANDOM}"
  if ! cat > "${tmp}"; then
    rm -f -- "${tmp}" 2>/dev/null || true
    echo "write_evidence_file_atomic: write failed for ${dest}" >&2
    return 1
  fi
  if ! mv -f -- "${tmp}" "${dest}"; then
    rm -f -- "${tmp}" 2>/dev/null || true
    echo "write_evidence_file_atomic: rename failed for ${dest}" >&2
    return 1
  fi
  return 0
}

# Count exact key= occurrences in a file (literal key prefix).
count_kv_key() {
  local file="$1" key="$2"
  local count=0
  local line
  if [[ ! -f "${file}" ]]; then
    printf '0'
    return 0
  fi
  while IFS= read -r line || [[ -n "${line}" ]]; do
    if [[ "${line}" == "${key}="* ]]; then
      count=$((count + 1))
    fi
  done < "${file}"
  printf '%s' "${count}"
}

# Read first key= value; empty string if absent (no default substitution).
read_kv_strict() {
  local file="$1" key="$2"
  local line val
  if [[ -f "${file}" ]]; then
    while IFS= read -r line || [[ -n "${line}" ]]; do
      # Strip trailing CR from CRLF files before key match.
      line="${line%$'\r'}"
      if [[ "${line}" == "${key}="* ]]; then
        val="${line#*=}"
        printf '%s' "${val}"
        return 0
      fi
    done < "${file}"
  fi
  printf ''
  return 0
}

# Validate a single evidence file for malformed lines / duplicate keys among
# the supplied key list. Sets CONTAINER_RESULT_ERROR on failure.
_validate_kv_file_keys() {
  local file="$1"
  shift
  local -a keys=("$@")
  local line key val k count
  local seen_keys=""

  while IFS= read -r line || [[ -n "${line}" ]]; do
    line="${line%$'\r'}"
    # Skip blanks and comments / schema markers.
    [[ -z "${line}" ]] && continue
    [[ "${line}" == \#* ]] && continue
    [[ "${line}" == BEGIN_SCHEMA_BLOCK* ]] && continue
    [[ "${line}" == END_SCHEMA_BLOCK ]] && continue
    if [[ "${line}" != *=* ]]; then
      CONTAINER_RESULT_ERROR="malformed_key_line"
      return 1
    fi
    key="${line%%=*}"
    val="${line#*=}"
    if [[ -z "${key}" ]]; then
      CONTAINER_RESULT_ERROR="malformed_key_line"
      return 1
    fi
    if [[ "${key}" == *$'\n'* || "${key}" == *$'\r'* || "${val}" == *$'\n'* || "${val}" == *$'\r'* ]]; then
      CONTAINER_RESULT_ERROR="crlf_injection"
      return 1
    fi
    # Track duplicate keys for any key= line in the file.
    case " ${seen_keys} " in
      *" ${key} "*)
        CONTAINER_RESULT_ERROR="duplicate_tuple_key_${key}"
        return 1
        ;;
    esac
    seen_keys="${seen_keys} ${key}"
  done < "${file}"

  for k in "${keys[@]}"; do
    count="$(count_kv_key "${file}" "${k}")"
    if [[ "${count}" -gt 1 ]]; then
      CONTAINER_RESULT_ERROR="duplicate_tuple_key_${k}"
      return 1
    fi
  done
  return 0
}

_reset_parsed_container_result() {
  CONTAINER_RESULT_PRESENCE="MISSING"
  CONTAINER_RESULT_VALID="NO"
  CONTAINER_RESULT_ERROR="none"
  PARSED_CONTAINER_OUTCOME=""
  PARSED_CARGO_STARTED=""
  PARSED_CARGO_EXIT_CODE=""
  PARSED_ARTIFACT_PRESENT=""
  PARSED_ARTIFACT_IDENTITY_COMPLETE=""
  PARSED_STATIC_INSPECTION_COMPLETE=""
  PARSED_SCHEMA_VERSION=""
  PARSED_FAILURE_STAGE=""
  PARSED_RUN_ID=""
}

# Apply Phase 3B tuple consistency rules. Reject contradictions; never normalize.
_validate_container_result_tuple_consistency() {
  local outcome="${PARSED_CONTAINER_OUTCOME}"
  local cargo_started="${PARSED_CARGO_STARTED}"
  local cargo_exit="${PARSED_CARGO_EXIT_CODE}"
  local artifact_present="${PARSED_ARTIFACT_PRESENT}"
  local identity_complete="${PARSED_ARTIFACT_IDENTITY_COMPLETE}"
  local static_complete="${PARSED_STATIC_INSPECTION_COMPLETE}"

  case "${outcome}" in
    BUILD_NOT_STARTED)
      if [[ "${cargo_started}" != "NO" ]]; then
        CONTAINER_RESULT_ERROR="contradiction_BUILD_NOT_STARTED_cargo_started"
        return 1
      fi
      if [[ "${artifact_present}" != "NO" ]]; then
        CONTAINER_RESULT_ERROR="contradiction_BUILD_NOT_STARTED_artifact_present"
        return 1
      fi
      ;;
    CARGO_FAILED)
      if [[ "${cargo_started}" != "YES" ]]; then
        CONTAINER_RESULT_ERROR="contradiction_CARGO_FAILED_cargo_started"
        return 1
      fi
      if [[ "${cargo_exit}" == "0" || "${cargo_exit}" == "NOT_APPLICABLE" ]]; then
        CONTAINER_RESULT_ERROR="contradiction_CARGO_FAILED_cargo_exit_code"
        return 1
      fi
      if ! [[ "${cargo_exit}" =~ ^[0-9]+$ ]]; then
        CONTAINER_RESULT_ERROR="contradiction_CARGO_FAILED_cargo_exit_code"
        return 1
      fi
      if [[ "${cargo_exit}" -eq 0 ]]; then
        CONTAINER_RESULT_ERROR="contradiction_CARGO_FAILED_cargo_exit_code"
        return 1
      fi
      ;;
    CARGO_SUCCEEDED_ARTIFACT_MISSING)
      if [[ "${cargo_started}" != "YES" ]]; then
        CONTAINER_RESULT_ERROR="contradiction_ARTIFACT_MISSING_cargo_started"
        return 1
      fi
      if [[ "${cargo_exit}" != "0" ]]; then
        CONTAINER_RESULT_ERROR="contradiction_ARTIFACT_MISSING_cargo_exit_code"
        return 1
      fi
      if [[ "${artifact_present}" != "NO" ]]; then
        CONTAINER_RESULT_ERROR="contradiction_ARTIFACT_MISSING_artifact_present"
        return 1
      fi
      ;;
    CARGO_SUCCEEDED_ARTIFACT_PRESENT)
      if [[ "${cargo_started}" != "YES" ]]; then
        CONTAINER_RESULT_ERROR="contradiction_ARTIFACT_PRESENT_cargo_started"
        return 1
      fi
      if [[ "${cargo_exit}" != "0" ]]; then
        CONTAINER_RESULT_ERROR="contradiction_ARTIFACT_PRESENT_cargo_exit_code"
        return 1
      fi
      if [[ "${artifact_present}" != "YES" ]]; then
        CONTAINER_RESULT_ERROR="contradiction_ARTIFACT_PRESENT_artifact_present"
        return 1
      fi
      if [[ -z "${identity_complete}" ]]; then
        CONTAINER_RESULT_ERROR="missing_artifact_identity_complete"
        return 1
      fi
      if [[ -z "${static_complete}" ]]; then
        CONTAINER_RESULT_ERROR="missing_static_inspection_complete"
        return 1
      fi
      ;;
    INFRASTRUCTURE_FAILURE)
      if [[ "${cargo_started}" != "YES" && "${cargo_started}" != "NO" ]]; then
        CONTAINER_RESULT_ERROR="contradiction_INFRASTRUCTURE_FAILURE_cargo_started"
        return 1
      fi
      if [[ -z "${PARSED_FAILURE_STAGE}" || "${PARSED_FAILURE_STAGE}" == "NOT_REACHED" || "${PARSED_FAILURE_STAGE}" == "NOT_STARTED" ]]; then
        CONTAINER_RESULT_ERROR="missing_infrastructure_failure_stage"
        return 1
      fi
      ;;
    *)
      CONTAINER_RESULT_ERROR="unsupported_outcome"
      return 1
      ;;
  esac

  # Cross-outcome rejections independent of case branch.
  if [[ "${artifact_present}" == "YES" && "${outcome}" == "CARGO_SUCCEEDED_ARTIFACT_MISSING" ]]; then
    CONTAINER_RESULT_ERROR="contradiction_ARTIFACT_MISSING_artifact_present"
    return 1
  fi
  if [[ "${cargo_exit}" == "0" && "${outcome}" == "CARGO_FAILED" ]]; then
    CONTAINER_RESULT_ERROR="contradiction_CARGO_FAILED_cargo_exit_code"
    return 1
  fi
  if [[ "${cargo_started}" == "NO" && "${outcome}" == "CARGO_FAILED" ]]; then
    CONTAINER_RESULT_ERROR="contradiction_CARGO_FAILED_cargo_started"
    return 1
  fi
  if [[ "${cargo_started}" == "NO" && ( "${outcome}" == "CARGO_SUCCEEDED_ARTIFACT_MISSING" || "${outcome}" == "CARGO_SUCCEEDED_ARTIFACT_PRESENT" ) ]]; then
    CONTAINER_RESULT_ERROR="contradiction_success_outcome_cargo_started"
    return 1
  fi
  return 0
}

# Centralized host parser for the explicit container result tuple.
# Performs no filesystem writes, invokes no validator, invokes no external tool.
# Populates PARSED_* / CONTAINER_RESULT_* globals. Returns 0 when valid, 1 otherwise.
parse_container_result_tuple() {
  local build_exit_file="${EVIDENCE_DIR}/BUILD_EXIT_CODE.txt"
  local artifact_file="${EVIDENCE_DIR}/ARTIFACT_IDENTITY.txt"
  local static_file="${EVIDENCE_DIR}/STATIC_ARTIFACT_INSPECTION.txt"
  local outcome_count
  local raw_outcome
  local line key val

  _reset_parsed_container_result

  if [[ ! -e "${build_exit_file}" ]]; then
    CONTAINER_RESULT_PRESENCE="MISSING"
    CONTAINER_RESULT_ERROR="build_exit_code_file_missing"
    CONTAINER_RESULT_VALID="NO"
    return 1
  fi
  if [[ ! -s "${build_exit_file}" ]]; then
    CONTAINER_RESULT_PRESENCE="EMPTY"
    CONTAINER_RESULT_ERROR="build_exit_code_file_empty"
    CONTAINER_RESULT_VALID="NO"
    return 1
  fi
  CONTAINER_RESULT_PRESENCE="PRESENT"

  if ! _validate_kv_file_keys "${build_exit_file}"; then
    CONTAINER_RESULT_VALID="NO"
    return 1
  fi

  outcome_count="$(count_kv_key "${build_exit_file}" "outcome")"
  if [[ "${outcome_count}" -eq 0 ]]; then
    CONTAINER_RESULT_ERROR="outcome_field_missing"
    CONTAINER_RESULT_VALID="NO"
    return 1
  fi
  if [[ "${outcome_count}" -gt 1 ]]; then
    CONTAINER_RESULT_ERROR="outcome_field_duplicated"
    CONTAINER_RESULT_VALID="NO"
    return 1
  fi

  raw_outcome="$(read_kv_strict "${build_exit_file}" "outcome")"
  if is_nonterminal_outcome_sentinel "${raw_outcome}"; then
    CONTAINER_RESULT_ERROR="terminal_sentinel_rejected_${raw_outcome}"
    CONTAINER_RESULT_VALID="NO"
    return 1
  fi
  if ! is_allowed_outcome "${raw_outcome}"; then
    CONTAINER_RESULT_ERROR="unsupported_outcome_${raw_outcome:-EMPTY}"
    CONTAINER_RESULT_VALID="NO"
    return 1
  fi
  PARSED_CONTAINER_OUTCOME="${raw_outcome}"

  # Required keys from BUILD_EXIT_CODE — never default/infer.
  if [[ "$(count_kv_key "${build_exit_file}" "cargo_started")" -eq 0 ]]; then
    CONTAINER_RESULT_ERROR="missing_cargo_started"
    CONTAINER_RESULT_VALID="NO"
    return 1
  fi
  if [[ "$(count_kv_key "${build_exit_file}" "cargo_exit_code")" -eq 0 ]]; then
    CONTAINER_RESULT_ERROR="missing_cargo_exit_code"
    CONTAINER_RESULT_VALID="NO"
    return 1
  fi
  PARSED_CARGO_STARTED="$(read_kv_strict "${build_exit_file}" "cargo_started")"
  PARSED_CARGO_EXIT_CODE="$(read_kv_strict "${build_exit_file}" "cargo_exit_code")"
  PARSED_SCHEMA_VERSION="$(read_kv_strict "${build_exit_file}" "evidence_schema_version")"
  PARSED_FAILURE_STAGE="$(read_kv_strict "${build_exit_file}" "failure_stage")"
  PARSED_RUN_ID="$(read_kv_strict "${build_exit_file}" "run_id")"
  if [[ -z "${PARSED_RUN_ID}" && -n "${RUN_ID:-}" ]]; then
    PARSED_RUN_ID="${RUN_ID}"
  fi

  # artifact_present: explicit only — BUILD_EXIT_CODE or ARTIFACT_IDENTITY.
  if [[ "$(count_kv_key "${build_exit_file}" "artifact_present")" -gt 0 ]]; then
    if [[ "$(count_kv_key "${build_exit_file}" "artifact_present")" -gt 1 ]]; then
      CONTAINER_RESULT_ERROR="duplicate_tuple_key_artifact_present"
      CONTAINER_RESULT_VALID="NO"
      return 1
    fi
    PARSED_ARTIFACT_PRESENT="$(read_kv_strict "${build_exit_file}" "artifact_present")"
  elif [[ -f "${artifact_file}" ]]; then
    if ! _validate_kv_file_keys "${artifact_file}"; then
      CONTAINER_RESULT_VALID="NO"
      return 1
    fi
    if [[ "$(count_kv_key "${artifact_file}" "artifact_present")" -eq 0 ]]; then
      CONTAINER_RESULT_ERROR="missing_artifact_present"
      CONTAINER_RESULT_VALID="NO"
      return 1
    fi
    if [[ "$(count_kv_key "${artifact_file}" "artifact_present")" -gt 1 ]]; then
      CONTAINER_RESULT_ERROR="duplicate_tuple_key_artifact_present"
      CONTAINER_RESULT_VALID="NO"
      return 1
    fi
    PARSED_ARTIFACT_PRESENT="$(read_kv_strict "${artifact_file}" "artifact_present")"
  else
    CONTAINER_RESULT_ERROR="missing_artifact_present"
    CONTAINER_RESULT_VALID="NO"
    return 1
  fi

  # Normalize common lowercase artifact_present from older writers to YES/NO
  # only when already yes/no — do not invent from other fields.
  case "${PARSED_ARTIFACT_PRESENT}" in
    yes) PARSED_ARTIFACT_PRESENT="YES" ;;
    no) PARSED_ARTIFACT_PRESENT="NO" ;;
    YES|NO) ;;
    *)
      CONTAINER_RESULT_ERROR="unsupported_artifact_present_${PARSED_ARTIFACT_PRESENT}"
      CONTAINER_RESULT_VALID="NO"
      return 1
      ;;
  esac

  # Identity / static completion: explicit keys only (no inference from SHA/status).
  if [[ "$(count_kv_key "${build_exit_file}" "artifact_identity_complete")" -gt 0 ]]; then
    PARSED_ARTIFACT_IDENTITY_COMPLETE="$(read_kv_strict "${build_exit_file}" "artifact_identity_complete")"
  elif [[ -f "${artifact_file}" && "$(count_kv_key "${artifact_file}" "artifact_identity_complete")" -gt 0 ]]; then
    PARSED_ARTIFACT_IDENTITY_COMPLETE="$(read_kv_strict "${artifact_file}" "artifact_identity_complete")"
  fi

  if [[ "$(count_kv_key "${build_exit_file}" "static_inspection_complete")" -gt 0 ]]; then
    PARSED_STATIC_INSPECTION_COMPLETE="$(read_kv_strict "${build_exit_file}" "static_inspection_complete")"
  elif [[ -f "${artifact_file}" && "$(count_kv_key "${artifact_file}" "static_inspection_complete")" -gt 0 ]]; then
    PARSED_STATIC_INSPECTION_COMPLETE="$(read_kv_strict "${artifact_file}" "static_inspection_complete")"
  elif [[ -f "${static_file}" && "$(count_kv_key "${static_file}" "static_inspection_complete")" -gt 0 ]]; then
    PARSED_STATIC_INSPECTION_COMPLETE="$(read_kv_strict "${static_file}" "static_inspection_complete")"
  fi

  if ! _validate_container_result_tuple_consistency; then
    CONTAINER_RESULT_VALID="NO"
    return 1
  fi

  CONTAINER_RESULT_VALID="YES"
  CONTAINER_RESULT_ERROR="none"
  return 0
}

# Build HOST_OUTCOME_INGESTION.txt content on stdout (caller pipes to atomic writer).
_host_outcome_ingestion_body() {
  local status="$1"
  local container_outcome_field="${PARSED_CONTAINER_OUTCOME}"
  if [[ "${CONTAINER_RESULT_VALID}" != "YES" ]]; then
    # Preserve missing/invalid visibility — never invent a terminal container outcome.
    if [[ -z "${container_outcome_field}" ]]; then
      container_outcome_field=""
    elif ! is_allowed_outcome "${container_outcome_field}"; then
      container_outcome_field="INVALID"
    fi
  fi
  printf '%s\n' "schema_version=${HOST_OUTCOME_INGESTION_SCHEMA_VERSION}"
  printf '%s\n' "status=${status}"
  printf '%s\n' "container_result_presence=${CONTAINER_RESULT_PRESENCE}"
  printf '%s\n' "container_result_valid=${CONTAINER_RESULT_VALID}"
  printf '%s\n' "container_result_error=${CONTAINER_RESULT_ERROR}"
  printf '%s\n' "container_outcome=${container_outcome_field}"
  printf '%s\n' "container_exit_code=${DOCKER_EXIT:-}"
  printf '%s\n' "cargo_started=${PARSED_CARGO_STARTED}"
  printf '%s\n' "cargo_exit_code=${PARSED_CARGO_EXIT_CODE}"
  printf '%s\n' "artifact_present=${PARSED_ARTIFACT_PRESENT}"
  printf '%s\n' "artifact_identity_complete=${PARSED_ARTIFACT_IDENTITY_COMPLETE}"
  printf '%s\n' "static_inspection_complete=${PARSED_STATIC_INSPECTION_COMPLETE}"
  printf '%s\n' "host_infrastructure_status=${HOST_INFRASTRUCTURE_STATUS}"
  printf '%s\n' "host_source_integrity_status=${HOST_SOURCE_INTEGRITY_STATUS}"
  printf '%s\n' "post_build_integrity_status=${HOST_POST_BUILD_INTEGRITY_STATUS}"
  printf '%s\n' "evidence_completeness_status=${HOST_EVIDENCE_COMPLETENESS_STATUS}"
  printf '%s\n' "preliminary_success_eligible=NO"
  printf '%s\n' "record_owner=HOST"
  printf '%s\n' "run_id=${PARSED_RUN_ID:-${RUN_ID:-}}"
  printf '%s\n' "failure_stage=${FAILURE_STAGE:-none}"
}

_host_outcome_ingestion_fingerprint() {
  local status="$1"
  printf '%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s' \
    "${status}" \
    "${CONTAINER_RESULT_PRESENCE}" \
    "${CONTAINER_RESULT_VALID}" \
    "${CONTAINER_RESULT_ERROR}" \
    "${PARSED_CONTAINER_OUTCOME}" \
    "${HOST_INFRASTRUCTURE_STATUS}" \
    "${HOST_SOURCE_INTEGRITY_STATUS}" \
    "${HOST_POST_BUILD_INTEGRITY_STATUS}" \
    "${HOST_EVIDENCE_COMPLETENESS_STATUS}" \
    "${DOCKER_EXIT:-}" \
    "${FAILURE_STAGE:-none}"
}

# Atomic writer for HOST_OUTCOME_INGESTION.txt. Fail-closed on write errors.
# Same-value repeat is idempotent; conflicting repeat fails closed.
write_host_outcome_ingestion_record() {
  local status="$1"
  local dest fingerprint prior
  dest="${EVIDENCE_DIR}/${HOST_OUTCOME_INGESTION_FILE_NAME}"

  reject_field_newlines "status" "${status}" || return 1
  reject_field_newlines "container_result_error" "${CONTAINER_RESULT_ERROR}" || return 1
  reject_field_newlines "container_outcome" "${PARSED_CONTAINER_OUTCOME}" || return 1
  reject_field_newlines "failure_stage" "${FAILURE_STAGE:-none}" || return 1
  reject_field_newlines "host_infrastructure_status" "${HOST_INFRASTRUCTURE_STATUS}" || return 1
  reject_field_newlines "host_source_integrity_status" "${HOST_SOURCE_INTEGRITY_STATUS}" || return 1

  fingerprint="$(_host_outcome_ingestion_fingerprint "${status}")"
  if [[ "${HOST_OUTCOME_INGESTION_WRITTEN}" == "YES" ]]; then
    if [[ "${HOST_OUTCOME_INGESTION_FINGERPRINT}" == "${fingerprint}" ]]; then
      return 0
    fi
    echo "write_host_outcome_ingestion_record: conflicting host finalization" >&2
    return 1
  fi

  if [[ -z "${EVIDENCE_DIR}" || ! -d "${EVIDENCE_DIR}" ]]; then
    echo "write_host_outcome_ingestion_record: evidence directory unavailable" >&2
    return 1
  fi

  if ! _host_outcome_ingestion_body "${status}" | write_evidence_file_atomic "${dest}"; then
    echo "write_host_outcome_ingestion_record: atomic write failed for ${dest}" >&2
    return 1
  fi
  HOST_OUTCOME_INGESTION_WRITTEN="YES"
  HOST_OUTCOME_INGESTION_FINGERPRINT="${fingerprint}"
  PRELIMINARY_SUCCESS_ELIGIBLE="NO"
  return 0
}

# Host-owned Docker exit evidence writer (safe to call from sourced tests).
write_host_docker_exit_code() {
  local dest="${EVIDENCE_DIR}/DOCKER_EXIT_CODE.txt"
  reject_field_newlines "outcome" "${OUTCOME:-}" || return 1
  reject_field_newlines "failure_stage" "${FAILURE_STAGE:-none}" || return 1
  {
    echo "evidence_schema_version=1"
    echo "docker_started_utc=${DOCKER_STARTED_UTC:-NOT_STARTED}"
    echo "docker_finished_utc=${DOCKER_FINISHED_UTC:-NOT_STARTED}"
    echo "docker_exit_code=${DOCKER_EXIT:-NOT_STARTED}"
    echo "container_platform=linux/amd64"
    echo "network_mode=bridge"
    echo "product_executed=NO"
    echo "ldd_used=NO"
    echo "outcome=${OUTCOME}"
    echo "failure_stage=${FAILURE_STAGE}"
    echo "outcome_source=container_BUILD_EXIT_CODE.txt_authoritative"
  } | write_evidence_file_atomic "${dest}"
}

# Finalize host timing facts without inventing a container outcome replacement
# into BUILD_EXIT_CODE.txt. Preserves existing container cargo timing when present.
write_host_build_timing_for_failure() {
  local dest="${EVIDENCE_DIR}/BUILD_TIMING.txt"
  local cargo_started_utc cargo_finished_utc cargo_elapsed_seconds cargo_started cargo_exit_code
  local docker_elapsed="NOT_APPLICABLE"
  local timing_outcome="${OUTCOME}"

  if [[ "${CONTAINER_RESULT_VALID}" == "YES" && -n "${PARSED_CONTAINER_OUTCOME}" ]]; then
    timing_outcome="${PARSED_CONTAINER_OUTCOME}"
  elif [[ "${CONTAINER_RESULT_VALID}" != "YES" ]]; then
    # Do not claim a fabricated container terminal outcome in timing when invalid.
    timing_outcome="NOT_APPLICABLE"
  fi

  cargo_started_utc="$(read_first_kv "${dest}" "cargo_started_utc" "NOT_APPLICABLE")"
  cargo_finished_utc="$(read_first_kv "${dest}" "cargo_finished_utc" "NOT_APPLICABLE")"
  cargo_elapsed_seconds="$(read_first_kv "${dest}" "cargo_elapsed_seconds" "NOT_APPLICABLE")"
  if [[ -n "${PARSED_CARGO_STARTED}" ]]; then
    cargo_started="${PARSED_CARGO_STARTED}"
  else
    cargo_started="$(read_first_kv "${dest}" "cargo_started" "${CARGO_STARTED:-NO}")"
  fi
  if [[ -n "${PARSED_CARGO_EXIT_CODE}" ]]; then
    cargo_exit_code="${PARSED_CARGO_EXIT_CODE}"
  else
    cargo_exit_code="$(read_first_kv "${dest}" "cargo_exit_code" "NOT_APPLICABLE")"
  fi
  if [[ -n "${DOCKER_STARTED_EPOCH:-}" && -n "${DOCKER_FINISHED_EPOCH:-}" ]]; then
    docker_elapsed=$(( DOCKER_FINISHED_EPOCH - DOCKER_STARTED_EPOCH ))
  fi

  {
    echo "evidence_schema_version=1"
    echo "status=FAILED"
    echo "outcome=${timing_outcome}"
    echo "docker_started_utc=${DOCKER_STARTED_UTC:-NOT_STARTED}"
    echo "docker_finished_utc=${DOCKER_FINISHED_UTC:-$(utc_now)}"
    echo "docker_elapsed_seconds=${docker_elapsed}"
    echo "cargo_started_utc=${cargo_started_utc}"
    echo "cargo_finished_utc=${cargo_finished_utc}"
    echo "cargo_elapsed_seconds=${cargo_elapsed_seconds}"
    echo "cargo_started=${cargo_started}"
    echo "cargo_exit_code=${cargo_exit_code}"
    echo "docker_exit_code=${DOCKER_EXIT:-NOT_STARTED}"
    echo "failure_stage=${FAILURE_STAGE}"
    echo "container_result_error=${CONTAINER_RESULT_ERROR}"
  } | write_evidence_file_atomic "${dest}"
}

# Centralized post-Docker host-side failure finalizer (Phase 3D).
# Preserves all valid container-owned files. Never rewrites BUILD_EXIT_CODE.txt.
# Always writes HOST_OUTCOME_INGESTION.txt. Returns nonzero. No validator.
# Args:
#   1: failure stage
#   2: exit code
#   3: message
#   4: host_infrastructure_status (OK|FAILED)
#   5: host_source_integrity_status (OK|FAILED)
#   6: post_build_integrity_status (OK|FAILED)
#   7: evidence_completeness_status (COMPLETE|INCOMPLETE|FAILED)
#   8: abort_after (YES|NO) — YES calls abort(); NO returns the exit code
finalize_post_docker_host_failure() {
  local stage="$1"
  local exit_code="$2"
  local message="$3"
  local infra_status="${4:-FAILED}"
  local source_status="${5:-OK}"
  local post_status="${6:-FAILED}"
  local completeness="${7:-FAILED}"
  local abort_after="${8:-YES}"
  local ingestion_status="FAILED"
  local build_exit_before=""
  local build_exit_path=""

  if [[ "${HOST_FINALIZING_IN_PROGRESS}" == "YES" ]]; then
    echo "finalize_post_docker_host_failure: recursion prevented" >&2
    return 1
  fi
  HOST_FINALIZING_IN_PROGRESS="YES"
  trap - ERR

  FAILURE_STAGE="${stage}"
  HOST_INFRASTRUCTURE_STATUS="${infra_status}"
  HOST_SOURCE_INTEGRITY_STATUS="${source_status}"
  HOST_POST_BUILD_INTEGRITY_STATUS="${post_status}"
  HOST_EVIDENCE_COMPLETENESS_STATUS="${completeness}"
  POST_BUILD_INTEGRITY_OK="no"
  PRELIMINARY_SUCCESS_ELIGIBLE="NO"

  build_exit_path="${EVIDENCE_DIR}/BUILD_EXIT_CODE.txt"
  if [[ -f "${build_exit_path}" ]]; then
    build_exit_before="$(cat -- "${build_exit_path}" 2>/dev/null || true)"
  fi

  # Prefer already-parsed state; re-parse only when not yet attempted.
  if [[ "${CONTAINER_RESULT_ERROR}" == "none" && "${CONTAINER_RESULT_VALID}" != "YES" && "${CONTAINER_RESULT_PRESENCE}" == "MISSING" ]]; then
    parse_container_result_tuple || true
  fi

  if [[ "${CONTAINER_RESULT_VALID}" == "YES" ]]; then
    ingestion_status="OK"
    OUTCOME="${PARSED_CONTAINER_OUTCOME}"
    CARGO_STARTED="${PARSED_CARGO_STARTED}"
  else
    ingestion_status="FAILED"
    # Do not invent a container terminal outcome; keep shell OUTCOME only as host note.
    if [[ -n "${PARSED_CONTAINER_OUTCOME}" ]] && is_allowed_outcome "${PARSED_CONTAINER_OUTCOME}"; then
      OUTCOME="${PARSED_CONTAINER_OUTCOME}"
    fi
  fi

  if ! write_host_outcome_ingestion_record "${ingestion_status}"; then
    echo "ERROR: host-owned HOST_OUTCOME_INGESTION.txt could not be written; fail-closed" >&2
    HOST_FINALIZING_IN_PROGRESS="NO"
    if [[ "${abort_after}" == "YES" ]]; then
      abort "${exit_code}" "Host outcome ingestion record write failed during post-Docker finalization (${message})"
    fi
    return "${exit_code}"
  fi

  write_host_docker_exit_code || true
  write_host_build_timing_for_failure || true

  # Never create or rewrite BUILD_EXIT_CODE.txt here.
  if [[ -f "${build_exit_path}" ]]; then
    local build_exit_after
    build_exit_after="$(cat -- "${build_exit_path}" 2>/dev/null || true)"
    if [[ "${build_exit_after}" != "${build_exit_before}" ]]; then
      echo "FATAL: finalize_post_docker_host_failure mutated container-owned BUILD_EXIT_CODE.txt" >&2
      HOST_FINALIZING_IN_PROGRESS="NO"
      if [[ "${abort_after}" == "YES" ]]; then
        abort "${exit_code}" "Host finalizer mutated container BUILD_EXIT_CODE.txt"
      fi
      return "${exit_code}"
    fi
  fi

  if [[ -n "${EVIDENCE_DIR}" && -f "${EVIDENCE_DIR}/HOST_RUN_METADATA.txt" ]]; then
    {
      echo "--- finalize_post_docker_host_failure ---"
      echo "utc_finalized=$(utc_now)"
      echo "finalized_stage=${stage}"
      echo "host_infrastructure_status=${HOST_INFRASTRUCTURE_STATUS}"
      echo "host_source_integrity_status=${HOST_SOURCE_INTEGRITY_STATUS}"
      echo "preliminary_success_eligible=NO"
      echo "container_result_valid=${CONTAINER_RESULT_VALID}"
      echo "container_result_error=${CONTAINER_RESULT_ERROR}"
    } >> "${EVIDENCE_DIR}/HOST_RUN_METADATA.txt" 2>/dev/null || true
  fi

  HOST_FINALIZING_IN_PROGRESS="NO"
  echo "ERROR: post-Docker host failure at stage=${stage}: ${message}" >&2
  if [[ "${abort_after}" == "YES" ]]; then
    abort "${exit_code}" "${message}"
  fi
  return "${exit_code}"
}

# ---------------------------------------------------------------------------
# Phase 2A host preflight helpers (RC4B-004 / RC4B-005 / RC4B-008).
# Defined before main so unit tests may source this file (BASH_SOURCE != $0)
# without executing the pipeline.
# ---------------------------------------------------------------------------

# Strong random suffix for run IDs (not second-resolution timestamps alone).
random_run_suffix() {
  if command -v openssl >/dev/null 2>&1; then
    openssl rand -hex 8
    return 0
  fi
  if [[ -r /dev/urandom ]]; then
    # 16 hex chars from urandom; portable when openssl is absent.
    od -An -N8 -tx1 /dev/urandom | tr -d ' \n'
    return 0
  fi
  # Last-resort unique-ish token; still combined with mkdir atomicity below.
  printf '%s%05d' "$(date -u +%H%M%S)" "${RANDOM:-0}"
}

# Atomically create a fresh EVIDENCE_DIR. Parent may use mkdir -p; the final
# selected run directory MUST be created with plain mkdir (no -p) so a
# preexisting directory is never merged, reused, or overwritten (RC4B-008).
allocate_atomic_evidence_dir() {
  local evidence_parent="${WORK_ROOT}/evidence"
  local max_attempts=32
  local attempt=0
  local suffix=""
  local candidate_id=""
  local candidate_dir=""

  mkdir -p "${evidence_parent}"

  while [[ "${attempt}" -lt "${max_attempts}" ]]; do
    attempt=$((attempt + 1))
    UTC_DATE="$(date -u +%Y%m%d)"
    suffix="$(random_run_suffix)"
    candidate_id="${WITNESS_ID}-${UTC_DATE}-${suffix}"
    candidate_dir="${evidence_parent}/${candidate_id}"
    # Plain mkdir: fails if candidate_dir already exists (including as a file).
    if mkdir "${candidate_dir}" 2>/dev/null; then
      RUN_ID="${candidate_id}"
      EVIDENCE_DIR="${candidate_dir}"
      return 0
    fi
  done

  echo "FATAL[stage=${CURRENT_STAGE}]: could not allocate a fresh atomic EVIDENCE_DIR under ${evidence_parent} after ${max_attempts} attempts; refusing to merge or reuse any preexisting evidence directory" >&2
  exit 2
}

# Require raw annotated-tag object type before checkout acceptance and before
# any Docker CLI invocation (RC4B-005). Accepted value is exactly "tag".
assert_raw_annotated_package_tag_type() {
  local tag_ref="refs/tags/${EFFECTIVE_WEAVER_FORGE_TAG}"
  local observed=""
  observed="$(git -C "${WF_DIR}" cat-file -t "${tag_ref}" 2>/dev/null || true)"
  WF_TAG_RAW_OBJECT_TYPE="${observed}"

  if [[ -n "${EVIDENCE_DIR}" && -f "${EVIDENCE_DIR}/HOST_RUN_METADATA.txt" ]]; then
    {
      echo "weaver_forge_tag_ref=${tag_ref}"
      echo "weaver_forge_tag_raw_object_type=${WF_TAG_RAW_OBJECT_TYPE:-<empty>}"
      echo "weaver_forge_tag_raw_object_type_required=tag"
    } >> "${EVIDENCE_DIR}/HOST_RUN_METADATA.txt"
  fi

  if [[ "${observed}" != "tag" ]]; then
    {
      echo "evidence_schema_version=1"
      echo "status=FAILED"
      echo "reason=package_tag_raw_object_type_not_annotated_tag"
      echo "weaver_forge_url=${EFFECTIVE_WEAVER_FORGE_URL}"
      echo "weaver_forge_tag_requested=${EFFECTIVE_WEAVER_FORGE_TAG}"
      echo "package_version=${PACKAGE_VERSION}"
      echo "weaver_forge_tag_raw_object_type_observed=${observed:-<empty>}"
      echo "weaver_forge_tag_raw_object_type_required=tag"
    } > "${EVIDENCE_DIR}/WEAVER_FORGE_PACKAGE_IDENTITY.txt"
    finalize_pre_docker_infrastructure_failure "weaver_forge_tag_raw_object_type" 3 \
      "Weaver Forge tag ${EFFECTIVE_WEAVER_FORGE_TAG} raw object type must be 'tag' (annotated); observed='${observed:-<empty>}'"
  fi
}

# Close the identity gate only after the required pre-Docker identity checks.
close_identity_gate() {
  IDENTITY_GATE_CLOSED="yes"
  if [[ -n "${EVIDENCE_DIR}" && -f "${EVIDENCE_DIR}/HOST_RUN_METADATA.txt" ]]; then
    {
      echo "identity_gate_closed=yes"
      echo "identity_gate_closed_utc=$(utc_now)"
      echo "identity_gate_requires_before_any_docker_cli=yes"
    } >> "${EVIDENCE_DIR}/HOST_RUN_METADATA.txt"
  fi
}

# ---------------------------------------------------------------------------
# Phase 2B source-mount isolation (RC4B-010 / RC4B-009 mount-plan subset).
# Structured mount plan + fail-closed validation before docker run.
# ---------------------------------------------------------------------------

# Canonicalize an existing path (resolve symlinks/junctions where supported).
# Prints the canonical path on success; returns nonzero on failure.
# Never falls back to an unresolved textual path when resolution fails.
canonicalize_existing_path() {
  local p="$1"
  if [[ -z "${p}" ]]; then
    return 1
  fi
  if [[ ! -e "${p}" && ! -L "${p}" ]]; then
    return 1
  fi
  # Broken symlink: present as a link but not resolvable — fail closed.
  if [[ -L "${p}" && ! -e "${p}" ]]; then
    return 1
  fi
  if command -v realpath >/dev/null 2>&1; then
    realpath -- "${p}" 2>/dev/null && return 0
    # Resolution failed; do not fall back to unresolved text.
    return 1
  fi
  if [[ -d "${p}" ]]; then
    (cd "${p}" && pwd -P) 2>/dev/null && return 0
    return 1
  fi
  if [[ -e "${p}" ]]; then
    local parent base parent_real
    parent="$(dirname -- "${p}")"
    base="$(basename -- "${p}")"
    parent_real="$(cd "${parent}" 2>/dev/null && pwd -P)" || return 1
    printf '%s/%s\n' "${parent_real}" "${base}"
    return 0
  fi
  return 1
}

# Normalize a container absolute path for component-safe comparison.
normalize_container_path() {
  local p="$1"
  # Collapse duplicate slashes; strip trailing slash except for root.
  p="$(printf '%s' "${p}" | sed -e 's://*:/:g')"
  if [[ "${p}" != "/" ]]; then
    p="${p%/}"
  fi
  printf '%s' "${p}"
}

# True iff child is strictly inside parent (component-safe; not textual prefix).
path_is_strictly_inside() {
  local child="$1" parent="$2"
  if [[ "${parent}" == "/" ]]; then
    [[ "${child}" != "/" && "${child}" == /* ]]
    return $?
  fi
  [[ "${child}" == "${parent}/"* ]]
}

# True iff ancestor is a strict ancestor of descendant.
path_is_strict_ancestor_of() {
  local ancestor="$1" descendant="$2"
  if [[ "${ancestor}" == "/" ]]; then
    [[ "${descendant}" != "/" ]]
    return $?
  fi
  [[ "${descendant}" == "${ancestor}/"* ]]
}

# MOUNT_PLAN entries: "ro<US>src<US>dst" or "rw<US>src<US>dst" (US = ASCII unit separator).
readonly _MOUNT_US=$'\x1f'
declare -a MOUNT_PLAN=()
declare -a DOCKER_MOUNT_ARGV=()

clear_mount_plan() {
  MOUNT_PLAN=()
  DOCKER_MOUNT_ARGV=()
}

append_mount_plan() {
  local mode="$1" src="$2" dst="$3"
  if [[ "${mode}" != "ro" && "${mode}" != "rw" ]]; then
    echo "FATAL[mount-plan]: mode must be ro or rw (got '${mode}')" >&2
    return 1
  fi
  if [[ -z "${src}" || -z "${dst}" ]]; then
    echo "FATAL[mount-plan]: src and dst must be non-empty" >&2
    return 1
  fi
  if [[ "${dst}" != /* ]]; then
    echo "FATAL[mount-plan]: container dst must be absolute (got '${dst}')" >&2
    return 1
  fi
  MOUNT_PLAN+=("${mode}${_MOUNT_US}${src}${_MOUNT_US}${dst}")
}

# Construct the production bind-mount plan (no broad WORK_ROOT -> /work).
build_canonical_mount_plan() {
  clear_mount_plan
  # Read-only source exactly once.
  append_mount_plan "ro" "${SRC_DIR}" "/src"
  # Smallest necessary package content: the container runner file only.
  append_mount_plan "ro" "${HOST_CONTAINER_SCRIPT}" "/witness/container_narrow_build.sh"
  # Explicit narrow writable children (none contain either checkout).
  append_mount_plan "rw" "${CARGO_TARGET_DIR}" "/work/cargo-target"
  append_mount_plan "rw" "${BOOTSTRAP_CARGO_TARGET_DIR}" "/work/bootstrap-cargo-target"
  append_mount_plan "rw" "${CARGO_HOME_DIR}" "/work/cargo-home"
  append_mount_plan "rw" "${HOME_DIR}" "/work/home"
  append_mount_plan "rw" "${DOTSLASH_CACHE_DIR}" "/work/dotslash-cache"
  append_mount_plan "rw" "${BOOTSTRAP_DIR}" "/work/bootstrap"
  append_mount_plan "rw" "${TMP_DIR}" "/work/tmp"
  append_mount_plan "rw" "${EVIDENCE_DIR}" "/evidence"
}

# Reject comma/CR/LF in a Docker --mount field before argv construction.
# Spaces are allowed (remain one argv element via Bash arrays). No escaping.
validate_docker_mount_field() {
  local field_name="$1"
  local value="$2"
  if [[ "${value}" == *","* ]]; then
    echo "FATAL[mount-plan]: Docker --mount ${field_name} must not contain comma" >&2
    return 1
  fi
  if [[ "${value}" == *$'\n'* || "${value}" == *$'\r'* ]]; then
    echo "FATAL[mount-plan]: Docker --mount ${field_name} must not contain CR or LF" >&2
    return 1
  fi
  return 0
}

_mount_plan_fail() {
  local stage="$1"
  local message="$2"
  if [[ -n "${EVIDENCE_DIR:-}" && -d "${EVIDENCE_DIR:-}" ]]; then
    finalize_pre_docker_infrastructure_failure "${stage}" 7 "${message}"
  fi
  return 1
}

# Convert MOUNT_PLAN into a Bash argv array of --mount entries (one arg each).
# Call only after validate_mount_plan succeeds. Re-checks field syntax fail-closed.
build_docker_mount_argv() {
  DOCKER_MOUNT_ARGV=()
  local entry mode src dst
  local us="${_MOUNT_US}"
  for entry in "${MOUNT_PLAN[@]}"; do
    mode="${entry%%"${us}"*}"
    src="${entry#*"${us}"}"
    dst="${src#*"${us}"}"
    src="${src%%"${us}"*}"
    validate_docker_mount_field "mode" "${mode}" || return 1
    validate_docker_mount_field "src" "${src}" || return 1
    validate_docker_mount_field "dst" "${dst}" || return 1
    if [[ "${mode}" == "ro" ]]; then
      DOCKER_MOUNT_ARGV+=(--mount "type=bind,src=${src},dst=${dst},readonly")
    else
      DOCKER_MOUNT_ARGV+=(--mount "type=bind,src=${src},dst=${dst}")
    fi
  done
}

# Fail-closed mount-plan validator (RC4B-010). Does not invoke Docker.
# Order (explicit, fail-closed):
#   1. mount record structurally present
#   2. source/destination/mode field syntax (comma/CR/LF rejected; spaces allowed)
#   3. required source exists (distinct from canonicalization failure)
#   4. source canonicalization succeeds (no unresolved textual fallback)
#   5. checkout overlap relationships validated
#   6. destination overlap validated
#   7. duplicate destination and ro/rw conflicts validated
# (8–9: structured Docker argv + docker invoke happen only after this returns 0)
# On failure: writes infrastructure-failure evidence via finalize_pre_docker_infrastructure_failure
# when EVIDENCE_DIR is available; otherwise returns nonzero for harnesses.
# Does not create missing mount source directories.
validate_mount_plan() {
  local gb_canon="" wf_canon="" wr_canon=""
  local entry mode src dst src_canon dst_norm
  local us="${_MOUNT_US}"
  local -A seen_dst=()
  local -A src_modes=()
  local prior_mode=""

  # 1. mount record structurally present
  if [[ "${#MOUNT_PLAN[@]}" -eq 0 ]]; then
    echo "FATAL[mount-plan]: mount plan is empty" >&2
    _mount_plan_fail "mount_plan_empty" "Mount-plan validation failed: empty plan"
    return 1
  fi

  # Reference paths for overlap checks (must canonicalize; no textual fallback).
  if ! gb_canon="$(canonicalize_existing_path "${SRC_DIR}")"; then
    echo "FATAL[mount-plan]: cannot canonicalize GROK_BUILD_DIR/SRC_DIR='${SRC_DIR}'" >&2
    _mount_plan_fail "mount_plan_canonicalize_src" \
      "Mount-plan validation failed: cannot canonicalize SRC_DIR=${SRC_DIR}"
    return 1
  fi
  if ! wf_canon="$(canonicalize_existing_path "${WF_DIR}")"; then
    echo "FATAL[mount-plan]: cannot canonicalize WF_DIR='${WF_DIR}'" >&2
    _mount_plan_fail "mount_plan_canonicalize_wf" \
      "Mount-plan validation failed: cannot canonicalize WF_DIR=${WF_DIR}"
    return 1
  fi
  if ! wr_canon="$(canonicalize_existing_path "${WORK_ROOT}")"; then
    echo "FATAL[mount-plan]: cannot canonicalize WORK_ROOT='${WORK_ROOT}'" >&2
    _mount_plan_fail "mount_plan_canonicalize_work_root" \
      "Mount-plan validation failed: cannot canonicalize WORK_ROOT=${WORK_ROOT}"
    return 1
  fi

  for entry in "${MOUNT_PLAN[@]}"; do
    mode="${entry%%"${us}"*}"
    src="${entry#*"${us}"}"
    dst="${src#*"${us}"}"
    src="${src%%"${us}"*}"

    # 2. field syntax valid (comma / CR / LF rejected; ordinary spaces allowed)
    if ! validate_docker_mount_field "mode" "${mode}"; then
      _mount_plan_fail "mount_plan_field_syntax_mode" \
        "Mount-plan validation failed: invalid mode field syntax"
      return 1
    fi
    if ! validate_docker_mount_field "src" "${src}"; then
      _mount_plan_fail "mount_plan_field_syntax_src" \
        "Mount-plan validation failed: invalid src field syntax"
      return 1
    fi
    if ! validate_docker_mount_field "dst" "${dst}"; then
      _mount_plan_fail "mount_plan_field_syntax_dst" \
        "Mount-plan validation failed: invalid dst field syntax"
      return 1
    fi
    if [[ "${mode}" != "ro" && "${mode}" != "rw" ]]; then
      echo "FATAL[mount-plan]: mode must be ro or rw (got '${mode}')" >&2
      _mount_plan_fail "mount_plan_invalid_mode" \
        "Mount-plan validation failed: mode must be ro or rw"
      return 1
    fi
    if [[ -z "${src}" || -z "${dst}" ]]; then
      echo "FATAL[mount-plan]: src and dst must be non-empty" >&2
      _mount_plan_fail "mount_plan_empty_field" \
        "Mount-plan validation failed: empty src or dst"
      return 1
    fi
    if [[ "${dst}" != /* ]]; then
      echo "FATAL[mount-plan]: container dst must be absolute (got '${dst}')" >&2
      _mount_plan_fail "mount_plan_dst_not_absolute" \
        "Mount-plan validation failed: dst not absolute"
      return 1
    fi
    dst_norm="$(normalize_container_path "${dst}")"

    # 3. required source exists (distinct from later canonicalization failure)
    if [[ ! -e "${src}" && ! -L "${src}" ]]; then
      echo "FATAL[mount-plan]: required mount source does not exist: ${src}" >&2
      _mount_plan_fail "mount_plan_source_missing" \
        "Mount-plan validation failed: source missing ${src}"
      return 1
    fi

    # 4. source canonicalization succeeds (never fall back to unresolved text)
    if ! src_canon="$(canonicalize_existing_path "${src}")"; then
      echo "FATAL[mount-plan]: cannot canonicalize mount source '${src}'" >&2
      _mount_plan_fail "mount_plan_canonicalize_mount_source" \
        "Mount-plan validation failed: cannot canonicalize mount source ${src}"
      return 1
    fi

    # 5–6. checkout overlap + destination overlap (writable sources/targets)
    # Prefer alias/overlap diagnostics over generic duplicate/mode-conflict.
    if [[ "${mode}" == "rw" ]]; then
      if [[ "${src_canon}" == "${wr_canon}" ]]; then
        echo "FATAL[mount-plan]: WORK_ROOT itself must not be mounted writable" >&2
        _mount_plan_fail "mount_plan_work_root_writable" \
          "Mount-plan validation failed: WORK_ROOT mounted writable"
        return 1
      fi
      if [[ "${src_canon}" == "${gb_canon}" ]] \
        || path_is_strictly_inside "${src_canon}" "${gb_canon}" \
        || path_is_strict_ancestor_of "${src_canon}" "${gb_canon}"; then
        echo "FATAL[mount-plan]: writable host source aliases GROK_BUILD_DIR ('${src_canon}' vs '${gb_canon}')" >&2
        _mount_plan_fail "mount_plan_writable_aliases_grok_build" \
          "Mount-plan validation failed: writable source aliases GROK_BUILD_DIR"
        return 1
      fi
      if [[ "${src_canon}" == "${wf_canon}" ]] \
        || path_is_strictly_inside "${src_canon}" "${wf_canon}" \
        || path_is_strict_ancestor_of "${src_canon}" "${wf_canon}"; then
        echo "FATAL[mount-plan]: writable host source aliases WF_DIR ('${src_canon}' vs '${wf_canon}')" >&2
        _mount_plan_fail "mount_plan_writable_aliases_wf" \
          "Mount-plan validation failed: writable source aliases WF_DIR"
        return 1
      fi
      if [[ "${dst_norm}" == "/src" ]] \
        || path_is_strictly_inside "${dst_norm}" "/src" \
        || path_is_strict_ancestor_of "${dst_norm}" "/src"; then
        echo "FATAL[mount-plan]: writable container target overlaps /src ('${dst_norm}')" >&2
        _mount_plan_fail "mount_plan_writable_target_overlaps_src" \
          "Mount-plan validation failed: writable target overlaps /src (${dst_norm})"
        return 1
      fi
    fi

    # 7. duplicate destination and ro/rw conflicts
    if [[ -n "${seen_dst[${dst_norm}]+x}" ]]; then
      echo "FATAL[mount-plan]: duplicate container target '${dst_norm}'" >&2
      _mount_plan_fail "mount_plan_duplicate_target" \
        "Mount-plan validation failed: duplicate container target ${dst_norm}"
      return 1
    fi
    seen_dst["${dst_norm}"]=1

    prior_mode="${src_modes[${src_canon}]:-}"
    if [[ -n "${prior_mode}" && "${prior_mode}" != "${mode}" ]]; then
      echo "FATAL[mount-plan]: host source '${src_canon}' mounted both '${prior_mode}' and '${mode}'" >&2
      _mount_plan_fail "mount_plan_source_mode_conflict" \
        "Mount-plan validation failed: source ${src_canon} mounted both ${prior_mode} and ${mode}"
      return 1
    fi
    src_modes["${src_canon}"]="${mode}"
  done

  if [[ -n "${EVIDENCE_DIR:-}" && -f "${EVIDENCE_DIR}/HOST_RUN_METADATA.txt" ]]; then
    {
      echo "mount_plan_validated=yes"
      echo "mount_plan_validated_utc=$(utc_now)"
      echo "mount_plan_broad_work_root_mount=prohibited"
      echo "mount_plan_entry_count=${#MOUNT_PLAN[@]}"
    } >> "${EVIDENCE_DIR}/HOST_RUN_METADATA.txt"
  fi
  return 0
}

# Record pre-Docker source identity snapshot used for post-container integrity.
record_pre_docker_source_integrity_snapshot() {
  PRE_DOCKER_SRC_HEAD="${SRC_HEAD}"
  PRE_DOCKER_SRC_CLEAN="yes"
  if [[ -n "${SRC_STATUS:-}" ]]; then
    PRE_DOCKER_SRC_CLEAN="no"
  fi
  if [[ -n "${EVIDENCE_DIR:-}" && -f "${EVIDENCE_DIR}/HOST_RUN_METADATA.txt" ]]; then
    {
      echo "pre_docker_source_head=${PRE_DOCKER_SRC_HEAD}"
      echo "pre_docker_source_clean=${PRE_DOCKER_SRC_CLEAN}"
    } >> "${EVIDENCE_DIR}/HOST_RUN_METADATA.txt"
  fi
}

# After docker returns: HEAD/clean mismatch is an integrity failure (not PASS-capable).
# Phase 3D: never create or replace container-owned BUILD_EXIT_CODE.txt.
# Missing, empty, malformed, and valid container results are handled only by the
# centralized finalize_post_docker_host_failure (no host-fabricated container outcome).
enforce_post_docker_source_integrity_boundary() {
  local head_ok="$1" clean_ok="$2"
  if [[ "${head_ok}" == "yes" && "${clean_ok}" == "yes" ]]; then
    return 0
  fi
  FAILURE_STAGE="post_docker_source_integrity"
  POST_BUILD_INTEGRITY_OK="no"
  HOST_SOURCE_INTEGRITY_STATUS="FAILED"
  HOST_POST_BUILD_INTEGRITY_STATUS="FAILED"
  HOST_EVIDENCE_COMPLETENESS_STATUS="FAILED"
  PRELIMINARY_SUCCESS_ELIGIBLE="NO"

  if [[ -f "${EVIDENCE_DIR}/HOST_RUN_METADATA.txt" ]]; then
    {
      echo "post_docker_source_integrity_failed=yes"
      echo "post_docker_source_head_unchanged=${head_ok}"
      echo "post_docker_source_clean_after=${clean_ok}"
      echo "host_source_integrity_status=FAILED"
      echo "preliminary_success_eligible=NO"
    } >> "${EVIDENCE_DIR}/HOST_RUN_METADATA.txt"
  fi

  # Delegate missing/empty/malformed/valid result handling to the centralized
  # post-Docker host finalizer. Do not write BUILD_EXIT_CODE.txt here.
  HOST_OUTCOME_INGESTION_WRITTEN="NO"
  HOST_OUTCOME_INGESTION_FINGERPRINT=""
  # Force finalizer re-parse of current container evidence (if any).
  CONTAINER_RESULT_ERROR="none"
  CONTAINER_RESULT_VALID="NO"
  CONTAINER_RESULT_PRESENCE="MISSING"
  finalize_post_docker_host_failure \
    "post_docker_source_integrity" 9 \
    "Post-Docker source HEAD or clean-tree integrity failure" \
    "${HOST_INFRASTRUCTURE_STATUS:-OK}" "FAILED" "FAILED" "FAILED" "NO" || true
  return 0
}

# ---------------------------------------------------------------------------
# Single deterministic verdict-ceiling function (RC3B-024). This is the ONLY
# place VERDICT_CEILING is computed; nothing else in this script independently
# derives it. The canonical-identity field list below MUST equal the
# "canonical identity fields" enumerated in WITNESS_CLASSIFICATION.md's
# NONMATERIAL_DISCLOSED severity row (WEAVER_FORGE_URL included — RC3B-003:
# a Weaver Forge URL mismatch is a material FAIL, never merely PARTIAL).
# This is an advisory host-side ceiling for identity-override deviations
# only; WITNESS_CLASSIFICATION.md remains authoritative for the full
# precedence table (product execution, outcome, etc.) and the Witness must
# apply its stricter ceiling when the two disagree.
# ---------------------------------------------------------------------------
compute_verdict_ceiling() {
  local -a canonical_identity_fields=(
    WEAVER_FORGE_URL
    WEAVER_FORGE_TAG
    GROK_BUILD_URL
    GROK_BUILD_COMMIT
    RUST_IMAGE
    EXPECTED_CARGO_LOCK_SHA256
    BUILD_CMD
  )

  if [[ "${NONCANONICAL_RUN}" -ne 1 ]]; then
    VERDICT_CEILING="PASS"
    return 0
  fi

  VERDICT_CEILING="PARTIAL"
  local name field
  for name in "${CHANGED_IDENTITY_FIELD_NAMES[@]}"; do
    for field in "${canonical_identity_fields[@]}"; do
      if [[ "${name}" == "${field}" ]]; then
        VERDICT_CEILING="FAIL"
      fi
    done
  done
}

# ---------------------------------------------------------------------------
# Evidence finalizers — guarantee no mandatory file is ever left recording
# NOT_REACHED as its FINAL value (RC3B-007), and guarantee the container's
# authoritative outcome (once Docker has run) is never independently
# re-derived (RC3B-008). Both finalizers write evidence and then terminate
# the run via abort(); neither one returns to its caller.
# ---------------------------------------------------------------------------

# Pre-Docker infrastructure failure (RC3B-007): used for every abort path that
# occurs strictly before `docker run` — Weaver Forge / Grok Build identity
# failures, Cargo.lock mismatch, non-empty host target, image pull failure,
# and image identity/digest/platform mismatch. Also reused by the ERR trap
# for any unexpected failure that happens before Docker has started.
finalize_pre_docker_infrastructure_failure() {
  local stage="$1"
  local exit_code="$2"
  local message="$3"

  CARGO_STARTED="NO"
  OUTCOME="INFRASTRUCTURE_FAILURE"
  FAILURE_STAGE="${stage}"

  # Pre-gate-sensitive mandatory files: ALWAYS rewrite on pre-Docker failure,
  # even when an earlier writer published status=OK (Phase 2A truthfulness).
  # Uses only schema-permitted failure/not-reached style fields.
  local pre_gate_sensitive=(
    ENVIRONMENT.txt
    WEAVER_FORGE_PACKAGE_IDENTITY.txt
    SOURCE_IDENTITY.txt
    SOURCE_ACQUISITION.txt
  )
  local f path is_pre_gate
  for f in "${pre_gate_sensitive[@]}"; do
    path="${EVIDENCE_DIR}/${f}"
    {
      echo "evidence_schema_version=1"
      echo "status=FAILED"
      echo "outcome=INFRASTRUCTURE_FAILURE"
      echo "applicable=no"
      echo "inspection_applicable=no"
      echo "artifact_present=no"
      echo "reason=pre_docker_infrastructure_failure_at_stage_${stage}"
      echo "failure_stage=${stage}"
      echo "cargo_started=NO"
      echo "product_executed=NO"
      echo "ldd_used=NO"
    } > "${path}"
  done

  # Remaining mandatory files: rewrite empty/NOT_REACHED, and also any
  # provisional status=OK that appeared before identity-gate closure.
  for f in "${MANDATORY_EVIDENCE_FILES[@]}"; do
    is_pre_gate=0
    for path in "${pre_gate_sensitive[@]}"; do
      [[ "${f}" == "${path}" ]] && is_pre_gate=1 && break
    done
    [[ "${is_pre_gate}" -eq 1 ]] && continue
    path="${EVIDENCE_DIR}/${f}"
    if [[ ! -s "${path}" ]] \
      || grep -q '^status=NOT_REACHED$' "${path}" 2>/dev/null \
      || { [[ "${IDENTITY_GATE_CLOSED}" != "yes" ]] && grep -q '^status=OK$' "${path}" 2>/dev/null; }; then
      {
        echo "evidence_schema_version=1"
        echo "status=FAILED"
        echo "outcome=INFRASTRUCTURE_FAILURE"
        echo "applicable=no"
        echo "inspection_applicable=no"
        echo "artifact_present=no"
        echo "reason=pre_docker_infrastructure_failure_at_stage_${stage}"
        echo "failure_stage=${stage}"
        echo "cargo_started=NO"
        echo "product_executed=NO"
        echo "ldd_used=NO"
      } > "${path}"
    fi
  done

  # Outcome-critical files: always rewritten authoritatively with the exact
  # required fields, regardless of any prior placeholder state.
  {
    echo "evidence_schema_version=1"
    echo "status=FAILED"
    echo "outcome=INFRASTRUCTURE_FAILURE"
    echo "cargo_started=NO"
    echo "build_status=INFRASTRUCTURE_FAILURE"
    echo "cargo_exit_code=NOT_APPLICABLE"
    echo "failure_stage=${stage}"
  } > "${EVIDENCE_DIR}/BUILD_EXIT_CODE.txt"

  {
    echo "evidence_schema_version=1"
    echo "status=FAILED"
    echo "outcome=INFRASTRUCTURE_FAILURE"
    echo "docker_started_utc=NOT_STARTED"
    echo "docker_finished_utc=NOT_STARTED"
    echo "docker_exit_code=NOT_STARTED"
    echo "container_platform=linux/amd64"
    echo "network_mode=bridge"
    echo "product_executed=NO"
    echo "ldd_used=NO"
    echo "failure_stage=${stage}"
  } > "${EVIDENCE_DIR}/DOCKER_EXIT_CODE.txt"

  {
    echo "evidence_schema_version=1"
    echo "status=FAILED"
    echo "outcome=INFRASTRUCTURE_FAILURE"
    echo "docker_started_utc=NOT_STARTED"
    echo "docker_finished_utc=NOT_STARTED"
    echo "docker_elapsed_seconds=NOT_APPLICABLE"
    echo "cargo_started_utc=NOT_APPLICABLE"
    echo "cargo_finished_utc=NOT_APPLICABLE"
    echo "cargo_started=NO"
    echo "cargo_exit_code=NOT_APPLICABLE"
    echo "docker_exit_code=NOT_STARTED"
    echo "failure_stage=${stage}"
  } > "${EVIDENCE_DIR}/BUILD_TIMING.txt"

  {
    echo "evidence_schema_version=1"
    echo "applicable=no"
    echo "artifact_present=no"
    echo "reason=pre_docker_infrastructure_failure_at_stage_${stage}"
    echo "product_executed=NO"
    echo "ldd_used=NO"
  } > "${EVIDENCE_DIR}/ARTIFACT_IDENTITY.txt"

  {
    echo "evidence_schema_version=1"
    echo "status=NOT_APPLICABLE"
    echo "outcome=INFRASTRUCTURE_FAILURE"
    echo "inspection_applicable=no"
    echo "artifact_present=no"
    echo "reason=pre_docker_infrastructure_failure_at_stage_${stage}"
  } > "${EVIDENCE_DIR}/STATIC_ARTIFACT_INSPECTION.txt"

  {
    echo "evidence_schema_version=1"
    echo "status=NOT_APPLICABLE"
    echo "outcome=INFRASTRUCTURE_FAILURE"
    echo "source_head_before=NOT_APPLICABLE"
    echo "source_head_after=NOT_APPLICABLE"
    echo "source_head_unchanged=no"
    echo "source_clean_before=no"
    echo "source_clean_after=no"
    echo "cargo_lock_sha256_before=NOT_APPLICABLE"
    echo "cargo_lock_sha256_after=NOT_APPLICABLE"
    echo "cargo_lock_unchanged=no"
    echo "cargo_lock_post_matches_expected=no"
    echo "source_or_lock_changed=no"
    echo "artifact_exists=no"
    echo "evidence_inventory_complete=no"
    echo "full_integrity_gate_all_four_yes=no"
    echo "post_build_integrity_ok=no"
    echo "failure_stage=${stage}"
  } > "${EVIDENCE_DIR}/POST_BUILD_INTEGRITY.txt"

  if [[ -n "${EVIDENCE_DIR}" && -f "${EVIDENCE_DIR}/HOST_RUN_METADATA.txt" ]]; then
    {
      echo "--- finalize_pre_docker_infrastructure_failure ---"
      echo "utc_finalized=$(utc_now)"
      echo "finalized_stage=${stage}"
      echo "finalized_outcome=INFRASTRUCTURE_FAILURE"
      echo "finalized_exit_code=${exit_code}"
    } >> "${EVIDENCE_DIR}/HOST_RUN_METADATA.txt" 2>/dev/null || true
  fi

  abort "${exit_code}" "${message}"
}

# Post-Docker unexpected failure: used only by the ERR trap when an
# uncaught error occurs after `docker run` has started (i.e. Docker's own
# wall-clock has begun). Ordinary post-Docker outcomes are handled by
# parse_container_result_tuple() / finalize_post_docker_host_failure().
# Phase 3D: never overwrites container-owned BUILD_EXIT_CODE.txt.
finalize_post_docker_unexpected_failure() {
  local stage="$1"
  local exit_code="$2"
  local message="$3"

  CARGO_STARTED="${CARGO_STARTED:-NO}"
  parse_container_result_tuple || true
  if [[ "${CONTAINER_RESULT_VALID}" == "YES" ]]; then
    OUTCOME="${PARSED_CONTAINER_OUTCOME}"
    CARGO_STARTED="${PARSED_CARGO_STARTED}"
  fi

  # Fill incomplete host-owned artifact placeholders only when still NOT_REACHED;
  # never rewrite BUILD_EXIT_CODE.txt.
  local f path
  for f in ARTIFACT_IDENTITY.txt STATIC_ARTIFACT_INSPECTION.txt POST_BUILD_INTEGRITY.txt; do
    path="${EVIDENCE_DIR}/${f}"
    if [[ ! -s "${path}" ]] || grep -q '^status=NOT_REACHED$' "${path}" 2>/dev/null; then
      {
        echo "evidence_schema_version=1"
        echo "status=FAILED"
        echo "applicable=no"
        echo "inspection_applicable=no"
        echo "artifact_present=no"
        echo "reason=unexpected_post_docker_failure_at_stage_${stage}"
        echo "evidence_inventory_complete=no"
        echo "product_executed=NO"
        echo "ldd_used=NO"
      } > "${path}"
    fi
  done

  finalize_post_docker_host_failure \
    "${stage}" "${exit_code}" "${message}" \
    "FAILED" "${HOST_SOURCE_INTEGRITY_STATUS:-OK}" "FAILED" "FAILED" "YES"
}

# ---------------------------------------------------------------------------
# ERR trap: extends generic failure handling without overwriting more
# specific failure classifications already recorded by abort()-driven paths.
# ---------------------------------------------------------------------------
on_err() {
  local ec=$?
  if [[ "${SPECIFIC_FAILURE_RECORDED}" -eq 1 ]]; then
    exit "${ec}"
  fi
  local failing_stage="${CURRENT_STAGE}"
  echo "ERROR: host orchestrator failed unexpectedly at stage '${failing_stage}' line ${BASH_LINENO[0]} (exit ${ec})" >&2

  if [[ -z "${EVIDENCE_DIR}" || ! -d "${EVIDENCE_DIR}" ]]; then
    # Failure occurred before an evidence directory even exists.
    exit "${ec}"
  fi

  if [[ -z "${DOCKER_STARTED_UTC}" ]]; then
    finalize_pre_docker_infrastructure_failure \
      "unexpected_${failing_stage}" "${ec}" \
      "Unexpected failure before Docker started, at stage=${failing_stage}"
  else
    finalize_post_docker_unexpected_failure \
      "unexpected_${failing_stage}" "${ec}" \
      "Unexpected failure after Docker started, at stage=${failing_stage}"
  fi
}

usage() {
  cat <<EOF
Usage: run_witness_narrow_build.sh [options] <witness-id>

Package version: ${PACKAGE_VERSION}

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
  EXPECTED_CARGO_LOCK_SHA256   = ${CANONICAL_CARGO_LOCK_SHA256}
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
and caps the proposed Witness verdict at PARTIAL (or FAIL for material identity
changes, including WEAVER_FORGE_URL — see WITNESS_CLASSIFICATION.md).
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
  # WEAVER_FORGE_URL checked first and explicitly (RC3B-003): any mismatch is a
  # canonical-identity deviation with FAIL consequences, never merely PARTIAL —
  # see compute_verdict_ceiling().
  check_identity_override "WEAVER_FORGE_URL" "${CANONICAL_WEAVER_FORGE_URL}" "${EFFECTIVE_WEAVER_FORGE_URL}"
  check_identity_override "WEAVER_FORGE_TAG" "${CANONICAL_WEAVER_FORGE_TAG}" "${EFFECTIVE_WEAVER_FORGE_TAG}"
  check_identity_override "GROK_BUILD_URL" "${CANONICAL_GROK_BUILD_URL}" "${EFFECTIVE_GROK_BUILD_URL}"
  check_identity_override "GROK_BUILD_COMMIT" "${CANONICAL_GROK_BUILD_COMMIT}" "${EFFECTIVE_GROK_BUILD_COMMIT}"
  check_identity_override "RUST_IMAGE" "${CANONICAL_RUST_IMAGE}" "${EFFECTIVE_RUST_IMAGE}"
  check_identity_override "EXPECTED_CARGO_LOCK_SHA256" "${CANONICAL_CARGO_LOCK_SHA256}" "${EFFECTIVE_EXPECTED_CARGO_LOCK_SHA256}"
  check_identity_override "BUILD_CMD" "${CANONICAL_BUILD_CMD}" "${EFFECTIVE_BUILD_CMD}"
  check_identity_override "EXPECTED_RUSTC_VERSION" "${CANONICAL_EXPECTED_RUSTC_VERSION}" "${EFFECTIVE_EXPECTED_RUSTC_VERSION}"
  check_identity_override "EXPECTED_DOTSLASH_VERSION" "${CANONICAL_EXPECTED_DOTSLASH_VERSION}" "${EFFECTIVE_EXPECTED_DOTSLASH_VERSION}"

  compute_verdict_ceiling
}

# ---------------------------------------------------------------------------
# WITNESS_ID safety (unchanged from rc3 — retained verbatim per rc4 scope)
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
# WORK_ROOT safety (unchanged from rc3 — retained verbatim per rc4 scope;
# evaluated in full before any deletion occurs)
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
  echo "${TMP_DIR}"
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
# Host ENVIRONMENT writers (Phase 2A / RC4B-004): non-Docker host facts may be
# collected early into diagnostics only; ENVIRONMENT.txt status=OK is published
# only after IDENTITY_GATE_CLOSED=yes and Docker metadata collection.
# ---------------------------------------------------------------------------
collect_host_environment_facts() {
  HOST_ENV_UTC="$(utc_now)"
  HOST_ENV_OS="$(uname -s 2>/dev/null || echo UNKNOWN)"
  HOST_ENV_KERNEL="$(uname -r 2>/dev/null || echo UNKNOWN)"
  HOST_ENV_ARCH="$(uname -m 2>/dev/null || echo UNKNOWN)"
  if command -v lscpu >/dev/null 2>&1; then
    HOST_ENV_CPU_SUMMARY="$(lscpu 2>/dev/null | head -n 20 || echo UNKNOWN)"
    HOST_ENV_CPU_MODEL="$(lscpu 2>/dev/null | sed -n 's/^Model name:[[:space:]]*//p' | head -n1)"
  else
    HOST_ENV_CPU_SUMMARY="UNKNOWN"
    HOST_ENV_CPU_MODEL=""
  fi
  [[ -z "${HOST_ENV_CPU_MODEL}" ]] && HOST_ENV_CPU_MODEL="UNKNOWN"
  if command -v free >/dev/null 2>&1; then
    HOST_ENV_RAM="$(free -h 2>/dev/null | head -n 5 || echo UNKNOWN)"
    HOST_ENV_RAM_GIB="$(free -g 2>/dev/null | awk '/^Mem:/{print $2; exit}')"
  else
    HOST_ENV_RAM="UNKNOWN"
    HOST_ENV_RAM_GIB=""
  fi
  [[ -z "${HOST_ENV_RAM_GIB}" ]] && HOST_ENV_RAM_GIB="UNKNOWN"
  if command -v df >/dev/null 2>&1; then
    HOST_ENV_DISK="$(df -h "${WORK_ROOT}" 2>/dev/null || echo UNKNOWN)"
    HOST_ENV_DISK_FREE_GB="$(df -BG "${WORK_ROOT}" 2>/dev/null | awk 'NR==2{gsub(/G/,"",$4); print $4; exit}')"
  else
    HOST_ENV_DISK="UNKNOWN"
    HOST_ENV_DISK_FREE_GB=""
  fi
  [[ -z "${HOST_ENV_DISK_FREE_GB}" ]] && HOST_ENV_DISK_FREE_GB="UNKNOWN"
  HOST_ENV_PLATFORM="linux/amd64"
  if grep -qi microsoft /proc/version 2>/dev/null; then
    HOST_ENV_WSL="likely_WSL2"
  else
    HOST_ENV_WSL="UNKNOWN"
  fi
  # Leave ENVIRONMENT.txt as NOT_REACHED until post-gate publication.
  # Record non-schema diagnostics only.
  if [[ -f "${EVIDENCE_DIR}/HOST_RUN_METADATA.txt" ]]; then
    {
      echo "host_env_facts_collected_utc=${HOST_ENV_UTC}"
      echo "host_env_facts_collected_pre_identity_gate=yes"
      echo "host_os_observed=${HOST_ENV_OS}"
      echo "host_arch_observed=${HOST_ENV_ARCH}"
      echo "environment_schema_status_pending_identity_gate=yes"
    } >> "${EVIDENCE_DIR}/HOST_RUN_METADATA.txt"
  fi
}

# Docker CLI metadata + ENVIRONMENT publication. Refuses unless gate is yes.
# Failures remain informational UNKNOWN after identity closure (not a hard abort).
record_docker_environment_metadata() {
  if [[ "${IDENTITY_GATE_CLOSED}" != "yes" ]]; then
    echo "FATAL[stage=${CURRENT_STAGE}]: record_docker_environment_metadata refused because IDENTITY_GATE_CLOSED='${IDENTITY_GATE_CLOSED}' (required: yes); no Docker CLI may run before identity closure" >&2
    exit 2
  fi

  local docker_client="UNKNOWN" docker_server="UNKNOWN" docker_ctx="UNKNOWN"
  if command -v docker >/dev/null 2>&1; then
    docker_client="$(docker version --format '{{.Client.Version}}' 2>/dev/null || echo UNKNOWN)"
    docker_server="$(docker version --format '{{.Server.Version}}' 2>/dev/null || echo UNKNOWN)"
    docker_ctx="$(docker context show 2>/dev/null || echo UNKNOWN)"
  fi
  [[ -z "${docker_client}" ]] && docker_client="UNKNOWN"
  [[ -z "${docker_server}" ]] && docker_server="UNKNOWN"
  [[ -z "${docker_ctx}" ]] && docker_ctx="UNKNOWN"

  {
    echo "# record_utc=${HOST_ENV_UTC:-$(utc_now)}"
    echo "BEGIN_SCHEMA_BLOCK ENVIRONMENT"
    echo "evidence_schema_version=1"
    echo "status=OK"
    echo "outcome=BUILD_NOT_STARTED"
    echo "witness_id=${WITNESS_ID}"
    echo "host_os=${HOST_ENV_OS:-UNKNOWN}"
    echo "host_kernel=${HOST_ENV_KERNEL:-UNKNOWN}"
    echo "host_arch=${HOST_ENV_ARCH:-UNKNOWN}"
    echo "host_cpu=${HOST_ENV_CPU_MODEL:-UNKNOWN}"
    echo "host_ram_gib=${HOST_ENV_RAM_GIB:-UNKNOWN}"
    echo "host_free_disk_gb=${HOST_ENV_DISK_FREE_GB:-UNKNOWN}"
    echo "docker_client_version=${docker_client}"
    echo "docker_server_version=${docker_server}"
    echo "docker_context=${docker_ctx}"
    echo "canonical_platform=${HOST_ENV_PLATFORM:-linux/amd64}"
    echo "wsl2_indicator=${HOST_ENV_WSL:-UNKNOWN}"
    echo "ai_assistance_used=see_WITNESS_STATEMENT.md"
    echo "ai_assistance_detail=recorded_in_WITNESS_STATEMENT.md"
    echo "human_review_completed=pending"
    echo "product_executed=NO"
    echo "upstream_product_commands_not_run=yes"
    echo "ldd_used=NO"
    echo "END_SCHEMA_BLOCK"
    echo "# --- non-validated context fields (human review only) ---"
    echo "# host_cpu_summary<<EOF"
    echo "# ${HOST_ENV_CPU_SUMMARY:-UNKNOWN}"
    echo "# EOF"
    echo "# host_ram<<EOF"
    echo "# ${HOST_ENV_RAM:-UNKNOWN}"
    echo "# EOF"
    echo "# host_available_disk<<EOF"
    echo "# ${HOST_ENV_DISK:-UNKNOWN}"
    echo "# EOF"
    echo "# docker_metadata_status=recorded_after_identity_closure"
    echo "# --- container-appended toolchain facts follow below this line ---"
  } > "${EVIDENCE_DIR}/ENVIRONMENT.txt"

  if [[ -f "${EVIDENCE_DIR}/HOST_RUN_METADATA.txt" ]]; then
    {
      echo "docker_metadata_recorded_after_identity_gate=yes"
      echo "docker_client_version=${docker_client}"
      echo "docker_server_version=${docker_server}"
      echo "docker_context=${docker_ctx}"
    } >> "${EVIDENCE_DIR}/HOST_RUN_METADATA.txt"
  fi
}

# ---------------------------------------------------------------------------
# Main pipeline (executed only when this file is run as a script)
# ---------------------------------------------------------------------------
run_witness_narrow_build_main() {
# Production initialization: reset load-bearing gate (ignore any inherited env).
IDENTITY_GATE_CLOSED="no"
SPECIFIC_FAILURE_RECORDED=0
CURRENT_STAGE="startup"
OUTCOME="BUILD_NOT_STARTED"
FAILURE_STAGE="none"
CARGO_STARTED="NO"
DOCKER_STARTED_UTC=""
DOCKER_FINISHED_UTC=""
DOCKER_STARTED_EPOCH=""
DOCKER_FINISHED_EPOCH=""
DOCKER_EXIT=""
EVIDENCE_DIR=""
RUN_ID=""
WF_TAG_RAW_OBJECT_TYPE=""
HOST_FINALIZING_IN_PROGRESS="NO"
HOST_OUTCOME_INGESTION_WRITTEN="NO"
HOST_OUTCOME_INGESTION_FINGERPRINT=""
CONTAINER_RESULT_PRESENCE="MISSING"
CONTAINER_RESULT_VALID="NO"
CONTAINER_RESULT_ERROR="none"
PARSED_CONTAINER_OUTCOME=""
PARSED_CARGO_STARTED=""
PARSED_CARGO_EXIT_CODE=""
PARSED_ARTIFACT_PRESENT=""
PARSED_ARTIFACT_IDENTITY_COMPLETE=""
PARSED_STATIC_INSPECTION_COMPLETE=""
PARSED_SCHEMA_VERSION=""
PARSED_FAILURE_STAGE=""
PARSED_RUN_ID=""
HOST_INFRASTRUCTURE_STATUS="OK"
HOST_SOURCE_INTEGRITY_STATUS="OK"
HOST_POST_BUILD_INTEGRITY_STATUS="OK"
HOST_EVIDENCE_COMPLETENESS_STATUS="INCOMPLETE"
PRELIMINARY_SUCCESS_ELIGIBLE="NO"
trap on_err ERR

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

# STEP 1: identity gate (WEAVER_FORGE_URL mismatch handling + machine VERDICT_CEILING)
mark_stage "step1_identity_gate"
apply_identity_gate

# STEP 2: WITNESS_ID validation
mark_stage "step2_witness_id_validation"
validate_witness_id "${WITNESS_ID}"

# STEP 3: WORK_ROOT validation
mark_stage "step3_work_root_validation"
validate_work_root "${WORK_ROOT}"

# ---------------------------------------------------------------------------
# STEP 4: Run identity / directory layout
# ---------------------------------------------------------------------------
mark_stage "step4_run_identity_and_layout"
UTC_DATE="$(date -u +%Y%m%d)"
# RUN_ID / EVIDENCE_DIR are assigned atomically in allocate_atomic_evidence_dir
# (STEP 6). Placeholders until then.
RUN_ID=""
WF_DIR="${WORK_ROOT}/weaver-forge"
SRC_DIR="${WORK_ROOT}/grok-build-src"
CARGO_HOME_DIR="${WORK_ROOT}/cargo-home"
CARGO_TARGET_DIR="${WORK_ROOT}/cargo-target"
BOOTSTRAP_CARGO_TARGET_DIR="${WORK_ROOT}/bootstrap-cargo-target"
DOTSLASH_CACHE_DIR="${WORK_ROOT}/dotslash-cache"
HOME_DIR="${WORK_ROOT}/home"
BOOTSTRAP_DIR="${WORK_ROOT}/bootstrap"
TMP_DIR="${WORK_ROOT}/tmp"
EVIDENCE_DIR=""

# STEP 5: WORK_ROOT reset confirmation
mark_stage "step5_work_root_reset_confirmation"
confirm_work_root_reset_if_needed

# STEP 6: Directory setup — WORK_ROOT may mkdir -p; EVIDENCE_DIR is atomic.
mark_stage "step6_directory_setup"
mkdir -p "${WORK_ROOT}"
allocate_atomic_evidence_dir

# ---------------------------------------------------------------------------
# STEP 7: Evidence initialization — BEFORE any fallible host/container operation.
# ---------------------------------------------------------------------------
mark_stage "step7_evidence_initialization"
init_mandatory_evidence() {
  local f
  for f in "${MANDATORY_EVIDENCE_FILES[@]}"; do
    write_not_reached "${EVIDENCE_DIR}/${f}"
  done
}
init_mandatory_evidence

# ---------------------------------------------------------------------------
# STEP 8: HOST_RUN_METADATA.txt (allowed aux) + DEVIATIONS.txt (required)
# ---------------------------------------------------------------------------
mark_stage "step8_host_run_metadata_and_deviations"
{
  echo "evidence_schema_version=1"
  echo "run_id=${RUN_ID}"
  echo "witness_id=${WITNESS_ID}"
  echo "package_version=${PACKAGE_VERSION}"
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
  echo "CANONICAL_IMAGE_DIGEST=${CANONICAL_IMAGE_DIGEST}"
  echo "CANONICAL_CARGO_LOCK_SHA256=${CANONICAL_CARGO_LOCK_SHA256}"
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
  echo "evidence_dir_allocation=atomic_mkdir"
  echo "evidence_dir_atomic=yes"
  echo "--- closed auxiliary-file allow-list (RC3B-021) ---"
  echo "allowed_aux_evidence_files=${ALLOWED_AUX_EVIDENCE_FILES[*]}"
  echo "--- validator output policy ---"
  echo "validator_output_policy=Validator (validate_witness_evidence.py) stdout/stderr MUST be captured OUTSIDE EVIDENCE_DIR. Do not redirect validator output into EVIDENCE_DIR at any time, and never write validator output into the evidence tree after the final manifest has been generated."
  echo "--- manifest lifecycle ---"
  echo "manifest_lifecycle=This run writes a PRELIMINARY EVIDENCE_MANIFEST.sha256 covering automated evidence only. Finalization is REQUIRED after WITNESS_STATEMENT.md, WITNESS_VERDICT.md, DEVIATIONS.txt, and REDACTIONS.md are completed; regenerate the manifest from within EVIDENCE_DIR using ./relative paths before submission."
} > "${EVIDENCE_DIR}/HOST_RUN_METADATA.txt"

NONCANONICAL_DISCLOSURE_TEXT="none"
if [[ "${NONCANONICAL_RUN}" -eq 1 ]]; then
  NONCANONICAL_DISCLOSURE_TEXT="$(printf '%s; ' "${CHANGED_IDENTITY_FIELDS[@]}")"
fi

{
  echo "evidence_schema_version=1"
  echo "deviation_state=$([[ "${NONCANONICAL_RUN}" -eq 1 ]] && echo PRESENT || echo NONE)"
  echo "status=RECORDED"
  echo "canonical_run=$([[ "${NONCANONICAL_RUN}" -eq 1 ]] && echo NO || echo YES)"
  echo "verdict_ceiling=${VERDICT_CEILING}"
  echo "noncanonical_disclosure=${NONCANONICAL_DISCLOSURE_TEXT}"
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
} > "${EVIDENCE_DIR}/${DEVIATIONS_FILE_NAME}"

echo "--- WORK_ROOT deletion targets recorded to HOST_RUN_METADATA.txt ---" >> "${EVIDENCE_DIR}/HOST_RUN_METADATA.txt"
work_root_managed_targets >> "${EVIDENCE_DIR}/HOST_RUN_METADATA.txt"

# ---------------------------------------------------------------------------
# STEP 9: DOCKER_EXIT_CODE.txt authoritative writer (declared here; used both
# pre- and post-Docker so a single implementation is shared everywhere).
# ---------------------------------------------------------------------------
write_docker_exit_code_authoritative() {
  {
    echo "evidence_schema_version=1"
    echo "docker_started_utc=${DOCKER_STARTED_UTC:-NOT_STARTED}"
    echo "docker_finished_utc=${DOCKER_FINISHED_UTC:-NOT_STARTED}"
    echo "docker_exit_code=${DOCKER_EXIT:-NOT_STARTED}"
    echo "container_platform=linux/amd64"
    echo "network_mode=bridge"
    echo "product_executed=NO"
    echo "ldd_used=NO"
    echo "outcome=${OUTCOME}"
    echo "failure_stage=${FAILURE_STAGE}"
    echo "outcome_source=container_BUILD_EXIT_CODE.txt_authoritative"
  } > "${EVIDENCE_DIR}/DOCKER_EXIT_CODE.txt"
}

# ---------------------------------------------------------------------------
# STEP 10: Host-side ENVIRONMENT fact collection (RC3B-012, RC3B-013, RC4B-004).
# Non-Docker host facts are collected here without publishing status=OK.
# ENVIRONMENT.txt remains NOT_REACHED until close_identity_gate +
# record_docker_environment_metadata (after STEP 13).
# ---------------------------------------------------------------------------
mark_stage "step10_host_environment_recording"
collect_host_environment_facts

# ---------------------------------------------------------------------------
# STEP 11: Weaver Forge package clone + tag resolution + clean/commit enforcement
# ---------------------------------------------------------------------------
mark_stage "step11_weaver_forge_package_clone"
WF_CLONE_START="$(utc_now)"
if [[ -e "${WF_DIR}" || -L "${WF_DIR}" ]]; then
  safe_reset_managed_path "${WF_DIR}"
fi
git clone "${EFFECTIVE_WEAVER_FORGE_URL}" "${WF_DIR}"
git -C "${WF_DIR}" fetch --tags origin
WF_CLONE_END="$(utc_now)"

if ! git -C "${WF_DIR}" rev-parse "refs/tags/${EFFECTIVE_WEAVER_FORGE_TAG}" >/dev/null 2>&1; then
  {
    echo "evidence_schema_version=1"
    echo "status=FAILED"
    echo "reason=requested_tag_not_present_on_origin"
    echo "weaver_forge_url=${EFFECTIVE_WEAVER_FORGE_URL}"
    echo "weaver_forge_tag_requested=${EFFECTIVE_WEAVER_FORGE_TAG}"
    echo "package_version=${PACKAGE_VERSION}"
    echo "available_witness_tags<<EOF"
    git -C "${WF_DIR}" tag -l 'grok-build-witness-*' 2>/dev/null || true
    echo "EOF"
  } > "${EVIDENCE_DIR}/WEAVER_FORGE_PACKAGE_IDENTITY.txt"
  finalize_pre_docker_infrastructure_failure "weaver_forge_tag_resolution" 3 \
    "Weaver Forge tag ${EFFECTIVE_WEAVER_FORGE_TAG} is not present on origin; canonical execution requires successful annotated-tag resolution and stops here"
fi

# RC4B-005: enforce raw annotated-tag object type BEFORE commit peel / checkout
# and BEFORE any Docker CLI invocation.
assert_raw_annotated_package_tag_type

WEAVER_FORGE_RESOLVED_COMMIT="$(git -C "${WF_DIR}" rev-parse "refs/tags/${EFFECTIVE_WEAVER_FORGE_TAG}^{commit}")"
if [[ ! "${WEAVER_FORGE_RESOLVED_COMMIT}" =~ ^[0-9a-f]{40}$ ]]; then
  {
    echo "evidence_schema_version=1"
    echo "status=FAILED"
    echo "reason=tag_did_not_resolve_to_full_40_char_commit"
    echo "weaver_forge_tag_requested=${EFFECTIVE_WEAVER_FORGE_TAG}"
    echo "weaver_forge_commit_resolved=${WEAVER_FORGE_RESOLVED_COMMIT}"
  } > "${EVIDENCE_DIR}/WEAVER_FORGE_PACKAGE_IDENTITY.txt"
  finalize_pre_docker_infrastructure_failure "weaver_forge_tag_resolution_format" 3 \
    "Weaver Forge tag ${EFFECTIVE_WEAVER_FORGE_TAG} did not resolve to a full 40-char lowercase commit (got: ${WEAVER_FORGE_RESOLVED_COMMIT})"
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

# Detached-state proof (RC3B-005 methodology, applied here too): `git
# symbolic-ref -q HEAD` must FAIL (nonzero exit == genuinely detached).
WF_DETACHED="yes"
if git -C "${WF_DIR}" symbolic-ref -q HEAD >/dev/null 2>&1; then
  WF_DETACHED="no"
fi

EXTERNAL_EXPECTED_SUPPLIED="no"
EXTERNAL_EXPECTED_MATCH="not_supplied"
if [[ -n "${WEAVER_FORGE_EXTERNAL_EXPECTED_COMMIT}" ]]; then
  EXTERNAL_EXPECTED_SUPPLIED="yes"
  if [[ ! "${WEAVER_FORGE_EXTERNAL_EXPECTED_COMMIT}" =~ ^[0-9a-f]{40}$ ]]; then
    {
      echo "evidence_schema_version=1"
      echo "status=FAILED"
      echo "reason=external_expected_commit_not_40_char_hex"
    } > "${EVIDENCE_DIR}/WEAVER_FORGE_PACKAGE_IDENTITY.txt"
    finalize_pre_docker_infrastructure_failure "weaver_forge_external_expected_commit_format" 3 \
      "WEAVER_FORGE_EXTERNAL_EXPECTED_COMMIT must be a full 40-char lowercase hex commit when supplied"
  fi
  if [[ "${WEAVER_FORGE_RESOLVED_COMMIT}" == "${WEAVER_FORGE_EXTERNAL_EXPECTED_COMMIT}" && "${WF_HEAD}" == "${WEAVER_FORGE_EXTERNAL_EXPECTED_COMMIT}" ]]; then
    EXTERNAL_EXPECTED_MATCH="yes"
  else
    EXTERNAL_EXPECTED_MATCH="no"
  fi
fi

# Enforce package identity BEFORE publishing status=OK.
if [[ "${WF_DETACHED}" != "yes" ]]; then
  {
    echo "evidence_schema_version=1"
    echo "status=FAILED"
    echo "reason=weaver_forge_not_detached"
    echo "package_clone_detached=${WF_DETACHED}"
    echo "package_clone_head=${WF_HEAD}"
    echo "weaver_forge_commit_resolved=${WEAVER_FORGE_RESOLVED_COMMIT}"
  } > "${EVIDENCE_DIR}/WEAVER_FORGE_PACKAGE_IDENTITY.txt"
  finalize_pre_docker_infrastructure_failure "weaver_forge_detached_head_check" 3 \
    "Weaver Forge package clone is not in detached HEAD state after tag checkout (git symbolic-ref -q HEAD unexpectedly succeeded)"
fi
if [[ "${TAG_HEAD_MATCH}" != "yes" ]]; then
  {
    echo "evidence_schema_version=1"
    echo "status=FAILED"
    echo "reason=weaver_forge_tag_head_mismatch"
    echo "package_clone_head=${WF_HEAD}"
    echo "weaver_forge_commit_resolved=${WEAVER_FORGE_RESOLVED_COMMIT}"
    echo "tag_head_match=${TAG_HEAD_MATCH}"
  } > "${EVIDENCE_DIR}/WEAVER_FORGE_PACKAGE_IDENTITY.txt"
  finalize_pre_docker_infrastructure_failure "weaver_forge_tag_head_mismatch" 3 \
    "Detached HEAD (${WF_HEAD}) does not equal resolved tag commit (${WEAVER_FORGE_RESOLVED_COMMIT})"
fi
if [[ "${WF_CLEAN}" != "yes" ]]; then
  {
    echo "evidence_schema_version=1"
    echo "status=FAILED"
    echo "reason=weaver_forge_dirty_clone"
    echo "package_clone_clean_status=${WF_CLEAN}"
  } > "${EVIDENCE_DIR}/WEAVER_FORGE_PACKAGE_IDENTITY.txt"
  finalize_pre_docker_infrastructure_failure "weaver_forge_dirty_clone" 3 \
    "Weaver Forge package clone tree is not clean after detached checkout"
fi
if [[ "${EXTERNAL_EXPECTED_SUPPLIED}" == "yes" && "${EXTERNAL_EXPECTED_MATCH}" != "yes" ]]; then
  {
    echo "evidence_schema_version=1"
    echo "status=FAILED"
    echo "reason=weaver_forge_external_expected_commit_mismatch"
    echo "external_expected_commit_match=${EXTERNAL_EXPECTED_MATCH}"
  } > "${EVIDENCE_DIR}/WEAVER_FORGE_PACKAGE_IDENTITY.txt"
  finalize_pre_docker_infrastructure_failure "weaver_forge_external_expected_commit_mismatch" 3 \
    "WEAVER_FORGE_EXTERNAL_EXPECTED_COMMIT mismatch: external=${WEAVER_FORGE_EXTERNAL_EXPECTED_COMMIT} resolved_tag=${WEAVER_FORGE_RESOLVED_COMMIT} head=${WF_HEAD}"
fi

{
  echo "evidence_schema_version=1"
  echo "status=OK"
  echo "witness_id=${WITNESS_ID}"
  echo "run_id=${RUN_ID}"
  echo "package_version=${PACKAGE_VERSION}"
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
  echo "noncanonical_disclosure=${NONCANONICAL_DISCLOSURE_TEXT}"
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

HOST_CONTAINER_SCRIPT="${WF_DIR}/external_verifications/grok-build/witness-package/scripts/container_narrow_build.sh"
if [[ ! -f "${HOST_CONTAINER_SCRIPT}" ]]; then
  finalize_pre_docker_infrastructure_failure "container_script_missing" 3 \
    "Resolved Weaver commit missing container script at ${HOST_CONTAINER_SCRIPT}"
fi

# ---------------------------------------------------------------------------
# STEP 12: Grok Build source clone + detached-HEAD/HEAD/clean enforcement
# ---------------------------------------------------------------------------
mark_stage "step12_grok_build_source_clone"
GB_CLONE_START="$(utc_now)"
if [[ -e "${SRC_DIR}" || -L "${SRC_DIR}" ]]; then
  safe_reset_managed_path "${SRC_DIR}"
fi
git clone "${EFFECTIVE_GROK_BUILD_URL}" "${SRC_DIR}"
git -C "${SRC_DIR}" checkout --detach "${EFFECTIVE_GROK_BUILD_COMMIT}"
GB_CLONE_END="$(utc_now)"

SRC_HEAD="$(git -C "${SRC_DIR}" rev-parse HEAD)"
SRC_STATUS="$(git -C "${SRC_DIR}" status --porcelain)"
CARGO_LOCK_BEFORE="$(sha256_of "${SRC_DIR}/Cargo.lock")"

# grok_build_detached_head is DERIVED, never hardcoded (RC3B-005): `git
# symbolic-ref -q HEAD` must FAIL for a genuinely detached checkout.
GB_DETACHED="yes"
if git -C "${SRC_DIR}" symbolic-ref -q HEAD >/dev/null 2>&1; then
  GB_DETACHED="no"
fi

# Enforce source identity + Cargo.lock BEFORE publishing status=OK.
if [[ "${GB_DETACHED}" != "yes" ]]; then
  {
    echo "evidence_schema_version=1"
    echo "status=FAILED"
    echo "reason=grok_build_not_detached"
    echo "grok_build_detached_head=${GB_DETACHED}"
  } > "${EVIDENCE_DIR}/SOURCE_IDENTITY.txt"
  finalize_pre_docker_infrastructure_failure "grok_build_detached_head_check" 4 \
    "Grok Build source clone is not in detached HEAD state after checkout (git symbolic-ref -q HEAD unexpectedly succeeded)"
fi
if [[ "${SRC_HEAD}" != "${EFFECTIVE_GROK_BUILD_COMMIT}" ]]; then
  {
    echo "evidence_schema_version=1"
    echo "status=FAILED"
    echo "reason=grok_build_commit_mismatch"
    echo "grok_build_commit_expected=${EFFECTIVE_GROK_BUILD_COMMIT}"
    echo "grok_build_commit_observed=${SRC_HEAD}"
  } > "${EVIDENCE_DIR}/SOURCE_IDENTITY.txt"
  finalize_pre_docker_infrastructure_failure "grok_build_commit_mismatch" 4 \
    "Grok Build source commit mismatch: observed=${SRC_HEAD} expected=${EFFECTIVE_GROK_BUILD_COMMIT}"
fi
if [[ -n "${SRC_STATUS}" ]]; then
  {
    echo "evidence_schema_version=1"
    echo "status=FAILED"
    echo "reason=grok_build_dirty_clone"
  } > "${EVIDENCE_DIR}/SOURCE_IDENTITY.txt"
  finalize_pre_docker_infrastructure_failure "grok_build_dirty_clone" 4 \
    "Grok Build source tree not clean after detached checkout"
fi

# ---------------------------------------------------------------------------
# STEP 13: Cargo.lock direct enforcement — BEFORE Docker
# ---------------------------------------------------------------------------
mark_stage "step13_cargo_lock_pre_docker"
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
  {
    echo "evidence_schema_version=1"
    echo "status=FAILED"
    echo "reason=cargo_lock_pre_docker_mismatch"
    echo "grok_build_commit_expected=${EFFECTIVE_GROK_BUILD_COMMIT}"
    echo "grok_build_commit_observed=${SRC_HEAD}"
    echo "cargo_lock_sha256_observed=${CARGO_LOCK_BEFORE}"
    echo "cargo_lock_sha256_expected=${EFFECTIVE_EXPECTED_CARGO_LOCK_SHA256}"
  } > "${EVIDENCE_DIR}/SOURCE_IDENTITY.txt"
  finalize_pre_docker_infrastructure_failure "cargo_lock_pre_docker_mismatch" 4 \
    "Cargo.lock SHA-256 mismatch BEFORE Docker (expected ${EFFECTIVE_EXPECTED_CARGO_LOCK_SHA256}, observed ${CARGO_LOCK_BEFORE})"
fi

{
  echo "evidence_schema_version=1"
  echo "status=OK"
  echo "grok_build_url=${EFFECTIVE_GROK_BUILD_URL}"
  echo "grok_build_commit_expected=${EFFECTIVE_GROK_BUILD_COMMIT}"
  echo "grok_build_commit_observed=${SRC_HEAD}"
  echo "grok_build_detached_head=${GB_DETACHED}"
  echo "grok_build_clean_status_porcelain=${SRC_STATUS}"
  echo "cargo_lock_sha256_observed=${CARGO_LOCK_BEFORE}"
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
  echo "grok_build_detached_head=${GB_DETACHED}"
  echo "grok_build_clean_tree=$([[ -z "${SRC_STATUS}" ]] && echo yes || echo no)"
  echo "fresh_clones=yes"
  echo "owner_caches_used=no"
  echo "status=OK"
} >> "${EVIDENCE_DIR}/SOURCE_ACQUISITION.txt"

# Identity closure complete (RC4B-004): package tag exists + raw type=tag +
# resolves to one commit + package detached/HEAD/clean + Grok Build
# detached/HEAD/clean + pre-Docker Cargo.lock match. Only now may Docker CLI
# run (metadata first; pull/run follow later steps).
mark_stage "step13b_identity_gate_close_and_docker_metadata"
close_identity_gate
record_docker_environment_metadata

# ---------------------------------------------------------------------------
# STEP 14: Isolated writable directories + host/container clean target proof
# ---------------------------------------------------------------------------
mark_stage "step14_isolated_directory_setup"
for _managed_dir in "${CARGO_HOME_DIR}" "${CARGO_TARGET_DIR}" "${BOOTSTRAP_CARGO_TARGET_DIR}" "${DOTSLASH_CACHE_DIR}" "${HOME_DIR}" "${BOOTSTRAP_DIR}" "${TMP_DIR}"; do
  safe_reset_managed_path "${_managed_dir}"
done
mkdir -p "${CARGO_HOME_DIR}" "${CARGO_TARGET_DIR}" "${BOOTSTRAP_CARGO_TARGET_DIR}" "${DOTSLASH_CACHE_DIR}" "${HOME_DIR}" "${BOOTSTRAP_DIR}" "${TMP_DIR}"

mark_stage "step14_clean_target_proof"
TARGET_CREATED_UTC="$(utc_now)"
TARGET_LISTING="$(ls -la "${CARGO_TARGET_DIR}" 2>&1 || true)"
TARGET_FIND="$(find "${CARGO_TARGET_DIR}" -mindepth 1 -print 2>/dev/null || true)"
TARGET_COUNT="$(find "${CARGO_TARGET_DIR}" -mindepth 1 | wc -l | tr -d ' ')"

{
  echo "evidence_schema_version=1"
  echo "status=CHECKED"
  # Host/container-scoped fields (RC3B-014): the container preserves these
  # exact key names via its own read_kv() fallback and appends its own
  # container_prebootstrap / container_precargo sections below.
  echo "target_path_host=${CARGO_TARGET_DIR}"
  echo "proof_utc_host=${TARGET_CREATED_UTC}"
  echo "observed_entry_count_host=${TARGET_COUNT}"
  echo "required_entry_count=0"
  echo "--- ls -la (host) ---"
  echo "${TARGET_LISTING}"
  echo "--- find (host) ---"
  echo "${TARGET_FIND}"
} > "${EVIDENCE_DIR}/CLEAN_TARGET_PROOF.txt"

if [[ "${TARGET_COUNT}" != "0" ]]; then
  finalize_pre_docker_infrastructure_failure "host_pre_build_target_not_empty" 5 \
    "Host pre-build target directory not empty (observed_entry_count_host=${TARGET_COUNT})"
fi

# ---------------------------------------------------------------------------
# STEP 15: Docker image pull — FATAL on nonzero exit; never fall back to a
# cached image. Writes IMAGE_IDENTITY.txt (BEGIN/END_SCHEMA_BLOCK, RC3B-006).
# ---------------------------------------------------------------------------
write_image_identity_block() {
  {
    echo "BEGIN_SCHEMA_BLOCK IMAGE_IDENTITY"
    echo "evidence_schema_version=1"
    echo "status=${II_STATUS}"
    echo "failure_stage=${II_FAILURE_STAGE:-NOT_APPLICABLE}"
    echo "requested_image=${EFFECTIVE_RUST_IMAGE}"
    echo "requested_digest=${REQUESTED_DIGEST:-NONE_PARSED}"
    echo "pull_command=${DOCKER_PULL_CMD}"
    echo "pull_exit_code=${IMAGE_PULL_EXIT}"
    echo "inspect_image_id_command=${II_INSPECT_ID_CMD:-NOT_APPLICABLE}"
    echo "inspect_image_id_exit_code=${II_INSPECT_ID_EC:-NOT_APPLICABLE}"
    echo "image_id=${II_IMAGE_ID:-NOT_APPLICABLE}"
    echo "inspect_repo_digests_command=${II_INSPECT_REPODIGESTS_CMD:-NOT_APPLICABLE}"
    echo "inspect_repo_digests_exit_code=${II_INSPECT_REPODIGESTS_EC:-NOT_APPLICABLE}"
    echo "repo_digests=${II_REPO_DIGESTS:-NOT_APPLICABLE}"
    echo "inspect_os_command=${II_INSPECT_OS_CMD:-NOT_APPLICABLE}"
    echo "inspect_os_exit_code=${II_INSPECT_OS_EC:-NOT_APPLICABLE}"
    echo "observed_os=${II_IMAGE_OS:-NOT_APPLICABLE}"
    echo "inspect_architecture_command=${II_INSPECT_ARCH_CMD:-NOT_APPLICABLE}"
    echo "inspect_architecture_exit_code=${II_INSPECT_ARCH_EC:-NOT_APPLICABLE}"
    echo "observed_architecture=${II_IMAGE_ARCH:-NOT_APPLICABLE}"
    echo "observed_platform=${II_IMAGE_PLATFORM:-NOT_APPLICABLE}"
    echo "image_id_available=${II_IMAGE_ID_AVAILABLE:-no}"
    echo "digest_match_expected=${II_DIGEST_MATCH:-no}"
    echo "platform_match_expected=${II_PLATFORM_MATCH:-no}"
    echo "proceeded_to_inspect_or_run=${II_PROCEEDED:-NO}"
    echo "cached_image_fallback_used=NO"
    echo "END_SCHEMA_BLOCK"
    echo "# --- non-schema auxiliary IMAGE_IDENTITY context (human review only) ---"
    echo "# pull_utc_start=${IMAGE_PULL_UTC_START:-NOT_APPLICABLE}"
    echo "# pull_utc_end=${IMAGE_PULL_UTC_END:-NOT_APPLICABLE}"
    echo "# pull_stdout_file=IMAGE_PULL_STDOUT.txt"
    echo "# pull_stderr_file=IMAGE_PULL_STDERR.txt"
    echo "product_executed=NO"
    echo "ldd_used=NO"
  } > "${EVIDENCE_DIR}/IMAGE_IDENTITY.txt"
}

mark_stage "step15_image_pull"
IMAGE_PULL_UTC_START="$(utc_now)"
DOCKER_PULL_CMD="docker pull --platform linux/amd64 ${EFFECTIVE_RUST_IMAGE}"
REQUESTED_DIGEST=""
if [[ "${EFFECTIVE_RUST_IMAGE}" == *"@sha256:"* ]]; then
  REQUESTED_DIGEST="sha256:${EFFECTIVE_RUST_IMAGE##*@sha256:}"
fi

set +e
docker pull --platform linux/amd64 "${EFFECTIVE_RUST_IMAGE}" > "${EVIDENCE_DIR}/IMAGE_PULL_STDOUT.txt" 2> "${EVIDENCE_DIR}/IMAGE_PULL_STDERR.txt"
IMAGE_PULL_EXIT=$?
set -e
IMAGE_PULL_UTC_END="$(utc_now)"

if [[ "${IMAGE_PULL_EXIT}" -ne 0 ]]; then
  II_STATUS="FAILED"
  II_FAILURE_STAGE="image_pull"
  II_PROCEEDED="NO"
  write_image_identity_block
  finalize_pre_docker_infrastructure_failure "image_pull" "${IMAGE_PULL_EXIT}" \
    "docker pull failed (image pull is FATAL); refusing to proceed with a cached/local image"
fi

# ---------------------------------------------------------------------------
# STEP 16: Image identity enforcement — must pass BEFORE docker run
# ---------------------------------------------------------------------------
mark_stage "step16_image_identity_enforcement"
II_PROCEEDED="YES"
II_INSPECT_ID_CMD="docker inspect --format {{.Id}} ${EFFECTIVE_RUST_IMAGE}"
II_INSPECT_REPODIGESTS_CMD="docker inspect --format {{json .RepoDigests}} ${EFFECTIVE_RUST_IMAGE}"
II_INSPECT_OS_CMD="docker inspect --format {{.Os}} ${EFFECTIVE_RUST_IMAGE}"
II_INSPECT_ARCH_CMD="docker inspect --format {{.Architecture}} ${EFFECTIVE_RUST_IMAGE}"

set +e
II_IMAGE_ID="$(docker inspect --format '{{.Id}}' "${EFFECTIVE_RUST_IMAGE}" 2>/dev/null)"
II_INSPECT_ID_EC=$?
II_REPO_DIGESTS="$(docker inspect --format '{{json .RepoDigests}}' "${EFFECTIVE_RUST_IMAGE}" 2>/dev/null)"
II_INSPECT_REPODIGESTS_EC=$?
II_IMAGE_OS="$(docker inspect --format '{{.Os}}' "${EFFECTIVE_RUST_IMAGE}" 2>/dev/null)"
II_INSPECT_OS_EC=$?
II_IMAGE_ARCH="$(docker inspect --format '{{.Architecture}}' "${EFFECTIVE_RUST_IMAGE}" 2>/dev/null)"
II_INSPECT_ARCH_EC=$?
set -e

[[ -z "${II_IMAGE_ID}" ]] && II_IMAGE_ID="UNKNOWN"
[[ -z "${II_REPO_DIGESTS}" ]] && II_REPO_DIGESTS="UNKNOWN"
[[ -z "${II_IMAGE_OS}" ]] && II_IMAGE_OS="UNKNOWN"
[[ -z "${II_IMAGE_ARCH}" ]] && II_IMAGE_ARCH="UNKNOWN"
II_IMAGE_PLATFORM="${II_IMAGE_OS}/${II_IMAGE_ARCH}"

II_IMAGE_ID_AVAILABLE="no"
[[ "${II_INSPECT_ID_EC}" -eq 0 && "${II_IMAGE_ID}" != "UNKNOWN" && -n "${II_IMAGE_ID}" ]] && II_IMAGE_ID_AVAILABLE="yes"

II_DIGEST_MATCH="no"
if [[ -n "${REQUESTED_DIGEST}" && "${II_INSPECT_REPODIGESTS_EC}" -eq 0 && "${II_REPO_DIGESTS}" == *"${REQUESTED_DIGEST}"* ]]; then
  II_DIGEST_MATCH="yes"
fi

II_PLATFORM_MATCH="no"
if [[ "${II_INSPECT_OS_EC}" -eq 0 && "${II_INSPECT_ARCH_EC}" -eq 0 && "${II_IMAGE_OS}" == "linux" && "${II_IMAGE_ARCH}" == "amd64" ]]; then
  II_PLATFORM_MATCH="yes"
fi

# status=OK is gated on EVERY identity sub-check passing (RC3B-006): a
# partial pass (e.g. platform ok, digest mismatched) must never read OK.
if [[ "${II_IMAGE_ID_AVAILABLE}" == "yes" && "${II_DIGEST_MATCH}" == "yes" && "${II_PLATFORM_MATCH}" == "yes" ]]; then
  II_STATUS="OK"
  II_FAILURE_STAGE="NOT_APPLICABLE"
else
  II_STATUS="FAILED"
  if [[ "${II_IMAGE_ID_AVAILABLE}" != "yes" ]]; then
    II_FAILURE_STAGE="image_inspect_id"
  elif [[ "${II_DIGEST_MATCH}" != "yes" ]]; then
    II_FAILURE_STAGE="image_inspect_digest"
  else
    II_FAILURE_STAGE="image_inspect_platform"
  fi
fi
write_image_identity_block

if [[ "${II_STATUS}" != "OK" ]]; then
  finalize_pre_docker_infrastructure_failure "image_identity_enforcement" 8 \
    "Image identity enforcement failed (image_id_available=${II_IMAGE_ID_AVAILABLE} digest_match_expected=${II_DIGEST_MATCH} platform_match_expected=${II_PLATFORM_MATCH}); refusing to run the container"
fi

# ---------------------------------------------------------------------------
# STEP 17: Docker invocation — structured mount plan (RC4B-010 Phase 2B).
# No broad WORK_ROOT -> /work writable mount. Validate before docker run.
# ---------------------------------------------------------------------------
mark_stage "step17_docker_run"
DOCKER_STDOUT="${EVIDENCE_DIR}/CONTAINER_STDOUT.txt"
DOCKER_STDERR="${EVIDENCE_DIR}/CONTAINER_STDERR.txt"

record_pre_docker_source_integrity_snapshot
build_canonical_mount_plan
validate_mount_plan
build_docker_mount_argv

declare -a DOCKER_RUN_ARGV=(
  run --rm
  --platform linux/amd64
  --network bridge
)
DOCKER_RUN_ARGV+=("${DOCKER_MOUNT_ARGV[@]}")
DOCKER_RUN_ARGV+=(
  -e HOME=/work/home
  -e CARGO_HOME=/work/cargo-home
  -e CARGO_TARGET_DIR=/work/cargo-target
  -e CARGO_INCREMENTAL=0
  -e DOTSLASH_CACHE=/work/dotslash-cache
  -e TMPDIR=/work/tmp
  -e PATH=/work/cargo-home/bin:/usr/local/cargo/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
  -e GROK_BUILD_COMMIT="${EFFECTIVE_GROK_BUILD_COMMIT}"
  -e EXPECTED_CARGO_LOCK_SHA256="${EFFECTIVE_EXPECTED_CARGO_LOCK_SHA256}"
  -e CANONICAL_BUILD_CMD="${EFFECTIVE_BUILD_CMD}"
  -e EXPECTED_RUSTC_VERSION="${EFFECTIVE_EXPECTED_RUSTC_VERSION}"
  -e EXPECTED_DOTSLASH_VERSION="${EFFECTIVE_EXPECTED_DOTSLASH_VERSION}"
  -e RUST_IMAGE="${EFFECTIVE_RUST_IMAGE}"
  -w /src
  "${EFFECTIVE_RUST_IMAGE}"
  bash /witness/container_narrow_build.sh
)

DOCKER_STARTED_UTC="$(utc_now)"
DOCKER_STARTED_EPOCH="$(date +%s)"
set +e
docker "${DOCKER_RUN_ARGV[@]}" \
  >"${DOCKER_STDOUT}" 2>"${DOCKER_STDERR}"
DOCKER_EXIT=$?
set -e
DOCKER_FINISHED_UTC="$(utc_now)"
DOCKER_FINISHED_EPOCH="$(date +%s)"

# ---------------------------------------------------------------------------
# STEP 18: Container outcome parsing — Phase 3D complete tuple ingestion.
# Exactly one terminal `outcome=` must be present with a consistent tuple.
# Missing/invalid results fail closed via finalize_post_docker_host_failure
# without fabricating or overwriting BUILD_EXIT_CODE.txt.
# ---------------------------------------------------------------------------
# Rewrites BUILD_TIMING.txt, preserving the container's authoritative
# outcome/failure_stage/cargo_* fields and patching in the host-known Docker
# wall-clock (the container itself cannot know Docker's own start/finish
# time, and records NOT_APPLICABLE placeholders for those specific fields).
# Full rewrite (not append) avoids ever producing a duplicate key.
patch_build_timing_docker_wallclock() {
  local build_timing_file="${EVIDENCE_DIR}/BUILD_TIMING.txt"
  local cargo_started_utc cargo_finished_utc cargo_elapsed_seconds cargo_started cargo_exit_code
  local docker_elapsed="NOT_APPLICABLE"

  cargo_started_utc="$(read_first_kv "${build_timing_file}" "cargo_started_utc" "NOT_APPLICABLE")"
  cargo_finished_utc="$(read_first_kv "${build_timing_file}" "cargo_finished_utc" "NOT_APPLICABLE")"
  cargo_elapsed_seconds="$(read_first_kv "${build_timing_file}" "cargo_elapsed_seconds" "NOT_APPLICABLE")"
  cargo_started="$(read_first_kv "${build_timing_file}" "cargo_started" "${CARGO_STARTED}")"
  cargo_exit_code="$(read_first_kv "${build_timing_file}" "cargo_exit_code" "NOT_APPLICABLE")"

  if [[ -n "${DOCKER_STARTED_EPOCH}" && -n "${DOCKER_FINISHED_EPOCH}" ]]; then
    docker_elapsed=$(( DOCKER_FINISHED_EPOCH - DOCKER_STARTED_EPOCH ))
  fi

  {
    echo "evidence_schema_version=1"
    echo "status=RECORDED"
    echo "outcome=${OUTCOME}"
    echo "docker_started_utc=${DOCKER_STARTED_UTC}"
    echo "docker_finished_utc=${DOCKER_FINISHED_UTC}"
    echo "docker_elapsed_seconds=${docker_elapsed}"
    echo "cargo_started_utc=${cargo_started_utc}"
    echo "cargo_finished_utc=${cargo_finished_utc}"
    echo "cargo_elapsed_seconds=${cargo_elapsed_seconds}"
    echo "cargo_started=${cargo_started}"
    echo "cargo_exit_code=${cargo_exit_code}"
    echo "docker_exit_code=${DOCKER_EXIT}"
    echo "failure_stage=${FAILURE_STAGE}"
  } > "${build_timing_file}"
}

mark_stage "step18_container_outcome_parsing"

# Docker launch failure (exit 125): no trustworthy container result.
if [[ "${DOCKER_EXIT}" -eq 125 ]]; then
  CONTAINER_RESULT_PRESENCE="MISSING"
  CONTAINER_RESULT_VALID="NO"
  CONTAINER_RESULT_ERROR="docker_run_launch_failure_exit_125"
  HOST_INFRASTRUCTURE_STATUS="FAILED"
  finalize_post_docker_host_failure \
    "docker_run_launch_failure" 10 \
    "Docker run launch failure (exit 125); no authoritative container outcome" \
    "FAILED" "OK" "FAILED" "FAILED" "YES"
fi

parse_container_result_tuple || true

if [[ "${CONTAINER_RESULT_VALID}" != "YES" ]]; then
  HOST_INFRASTRUCTURE_STATUS="FAILED"
  # Do not invent OUTCOME=INFRASTRUCTURE_FAILURE into BUILD_EXIT_CODE.txt.
  finalize_post_docker_host_failure \
    "invalid_or_missing_container_outcome" 10 \
    "Container result tuple could not be authoritatively ingested (reason=${CONTAINER_RESULT_ERROR}); refusing to reconstruct or overwrite container outcome" \
    "FAILED" "OK" "FAILED" "FAILED" "YES"
else
  OUTCOME="${PARSED_CONTAINER_OUTCOME}"
  FAILURE_STAGE="${PARSED_FAILURE_STAGE:-NOT_RECORDED}"
  CARGO_STARTED="${PARSED_CARGO_STARTED}"
  write_docker_exit_code_authoritative
  patch_build_timing_docker_wallclock
  # Host ingestion record for valid tuples; always preliminary_success_eligible=NO.
  HOST_INFRASTRUCTURE_STATUS="OK"
  HOST_SOURCE_INTEGRITY_STATUS="OK"
  HOST_POST_BUILD_INTEGRITY_STATUS="OK"
  HOST_EVIDENCE_COMPLETENESS_STATUS="INCOMPLETE"
  write_host_outcome_ingestion_record "OK" || \
    finalize_post_docker_host_failure \
      "host_outcome_ingestion_write_failed" 10 \
      "Valid container tuple parsed but HOST_OUTCOME_INGESTION.txt could not be written" \
      "FAILED" "OK" "FAILED" "FAILED" "YES"
fi

# ---------------------------------------------------------------------------
# STEP 19: Cargo.lock direct enforcement AFTER Docker + POST_BUILD_INTEGRITY
# ---------------------------------------------------------------------------
mark_stage "step19_post_build_integrity"
SRC_HEAD_AFTER="$(git -C "${SRC_DIR}" rev-parse HEAD)"
SRC_STATUS_AFTER="$(git -C "${SRC_DIR}" status --porcelain)"
CARGO_LOCK_AFTER="$(sha256_of "${SRC_DIR}/Cargo.lock")"

SOURCE_HEAD_UNCHANGED="no"
[[ "${SRC_HEAD_AFTER}" == "${SRC_HEAD}" ]] && SOURCE_HEAD_UNCHANGED="yes"

# Blank porcelain output is explicitly normalized before yes/no classification
# (RC3B-019): an empty string means clean (`yes`), never left ambiguous.
SOURCE_CLEAN_AFTER="yes"
if [[ -n "${SRC_STATUS_AFTER}" ]]; then
  SOURCE_CLEAN_AFTER="no"
fi
SOURCE_CLEAN_BEFORE="yes"
if [[ -n "${SRC_STATUS}" ]]; then
  SOURCE_CLEAN_BEFORE="no"
fi

CARGO_LOCK_UNCHANGED="no"
[[ "${CARGO_LOCK_AFTER}" == "${CARGO_LOCK_BEFORE}" ]] && CARGO_LOCK_UNCHANGED="yes"

CARGO_LOCK_POST_MATCHES_EXPECTED="no"
[[ "${CARGO_LOCK_AFTER}" == "${EFFECTIVE_EXPECTED_CARGO_LOCK_SHA256}" ]] && CARGO_LOCK_POST_MATCHES_EXPECTED="yes"

{
  echo "evidence_schema_version=1"
  echo "status=CHECKED"
  echo "stage=post_docker"
  echo "cargo_lock_sha256_expected=${EFFECTIVE_EXPECTED_CARGO_LOCK_SHA256}"
  echo "cargo_lock_sha256_before=${CARGO_LOCK_BEFORE}"
  echo "cargo_lock_sha256_after=${CARGO_LOCK_AFTER}"
  echo "cargo_lock_unchanged=${CARGO_LOCK_UNCHANGED}"
  echo "cargo_lock_post_matches_expected=${CARGO_LOCK_POST_MATCHES_EXPECTED}"
  echo "source_head_before=${SRC_HEAD}"
  echo "source_head_after=${SRC_HEAD_AFTER}"
  echo "source_head_unchanged=${SOURCE_HEAD_UNCHANGED}"
  echo "source_clean_after=${SOURCE_CLEAN_AFTER}"
} >> "${EVIDENCE_DIR}/CARGO_LOCK_INTEGRITY.txt"

# evidence_inventory_complete is ALWAYS "no" from this automated host run: it
# can only become "yes" after the Witness completes WITNESS_STATEMENT.md,
# WITNESS_VERDICT.md, DEVIATIONS.txt, and REDACTIONS.md, and the FINAL
# manifest passes the structural validator (RC3B-020). The four-field gate
# below is computed and disclosed, but will always read "no" at this stage —
# that is expected and is not itself a build defect.
EVIDENCE_INVENTORY_COMPLETE="no"

FULL_INTEGRITY_GATE_ALL_FOUR_YES="no"
if [[ "${SOURCE_HEAD_UNCHANGED}" == "yes" && "${CARGO_LOCK_UNCHANGED}" == "yes" && "${CARGO_LOCK_POST_MATCHES_EXPECTED}" == "yes" && "${EVIDENCE_INVENTORY_COMPLETE}" == "yes" ]]; then
  FULL_INTEGRITY_GATE_ALL_FOUR_YES="yes"
fi

# Technical post-build integrity (three automatable fields only) — this is
# what gates the HOST script's own FINAL_EXIT_CODE below. The full four-field
# gate (including evidence_inventory_complete) is a separate, later Witness
# responsibility per WITNESS_CLASSIFICATION.md's PASS checklist.
POST_BUILD_INTEGRITY_OK="yes"
if [[ "${SOURCE_HEAD_UNCHANGED}" != "yes" || "${CARGO_LOCK_UNCHANGED}" != "yes" || "${CARGO_LOCK_POST_MATCHES_EXPECTED}" != "yes" || "${SOURCE_CLEAN_AFTER}" != "yes" ]]; then
  POST_BUILD_INTEGRITY_OK="no"
fi

# Phase 2B: HEAD or clean-tree drift after Docker is an integrity failure and
# must not leave a PASS-capable / successful package outcome accepted.
# Phase 3D: preserve valid container BUILD_EXIT_CODE.txt; record host source
# integrity separately; route through centralized host finalizer.
enforce_post_docker_source_integrity_boundary "${SOURCE_HEAD_UNCHANGED}" "${SOURCE_CLEAN_AFTER}"
if [[ "${SOURCE_HEAD_UNCHANGED}" != "yes" || "${SOURCE_CLEAN_AFTER}" != "yes" ]]; then
  HOST_SOURCE_INTEGRITY_STATUS="FAILED"
  HOST_POST_BUILD_INTEGRITY_STATUS="FAILED"
  HOST_EVIDENCE_COMPLETENESS_STATUS="FAILED"
  # Allow host-owned ingestion update after any earlier OK write.
  HOST_OUTCOME_INGESTION_WRITTEN="NO"
  HOST_OUTCOME_INGESTION_FINGERPRINT=""
  finalize_post_docker_host_failure \
    "post_docker_source_integrity" 9 \
    "Post-Docker source HEAD or clean-tree integrity failure" \
    "${HOST_INFRASTRUCTURE_STATUS:-OK}" "FAILED" "FAILED" "FAILED" "YES"
fi

ARTIFACT_PATH="${CARGO_TARGET_DIR}/debug/xai-grok-pager"
ARTIFACT_EXISTS="no"
[[ -f "${ARTIFACT_PATH}" ]] && ARTIFACT_EXISTS="yes"

{
  echo "evidence_schema_version=1"
  echo "status=OK"
  echo "outcome=${OUTCOME}"
  echo "source_head_before=${SRC_HEAD}"
  echo "source_head_after=${SRC_HEAD_AFTER}"
  echo "source_head_unchanged=${SOURCE_HEAD_UNCHANGED}"
  echo "source_clean_before=${SOURCE_CLEAN_BEFORE}"
  echo "source_clean_after=${SOURCE_CLEAN_AFTER}"
  echo "cargo_lock_sha256_before=${CARGO_LOCK_BEFORE}"
  echo "cargo_lock_sha256_after=${CARGO_LOCK_AFTER}"
  echo "cargo_lock_unchanged=${CARGO_LOCK_UNCHANGED}"
  echo "cargo_lock_post_matches_expected=${CARGO_LOCK_POST_MATCHES_EXPECTED}"
  echo "source_or_lock_changed=$([[ "${CARGO_LOCK_UNCHANGED}" == "yes" && "${SOURCE_HEAD_UNCHANGED}" == "yes" ]] && echo no || echo yes)"
  echo "artifact_path=${ARTIFACT_PATH}"
  echo "artifact_exists=${ARTIFACT_EXISTS}"
  echo "docker_exit_code=${DOCKER_EXIT}"
  echo "failure_stage=${FAILURE_STAGE}"
  echo "evidence_inventory_complete=${EVIDENCE_INVENTORY_COMPLETE}"
  echo "full_integrity_gate_all_four_yes=${FULL_INTEGRITY_GATE_ALL_FOUR_YES}"
  echo "full_integrity_gate_note=evidence_inventory_complete can only become yes after the Witness completes WITNESS_STATEMENT.md, WITNESS_VERDICT.md, DEVIATIONS.txt, REDACTIONS.md, and the FINAL manifest validates; the automated host run always records evidence_inventory_complete=no"
  echo "post_build_integrity_ok=${POST_BUILD_INTEGRITY_OK}"
} > "${EVIDENCE_DIR}/POST_BUILD_INTEGRITY.txt"

# ---------------------------------------------------------------------------
# STEP 20: Closed auxiliary-file inventory check (RC3B-021)
# ---------------------------------------------------------------------------
enforce_closed_aux_inventory() {
  mark_stage "step20_closed_aux_inventory_check"
  local -a allowed=("${MANDATORY_EVIDENCE_FILES[@]}" "${ALLOWED_AUX_EVIDENCE_FILES[@]}" "${DEVIATIONS_FILE_NAME}")
  local f base is_allowed a
  while IFS= read -r f; do
    base="$(basename "${f}")"
    is_allowed=0
    for a in "${allowed[@]}"; do
      if [[ "${base}" == "${a}" ]]; then
        is_allowed=1
        break
      fi
    done
    if [[ "${is_allowed}" -ne 1 ]]; then
      abort 11 "Unlisted evidence file violates the closed aux-file allow-list: ${base} (allowed aux files are: ${ALLOWED_AUX_EVIDENCE_FILES[*]})"
    fi
  done < <(find "${EVIDENCE_DIR}" -maxdepth 1 -type f -print)
}
enforce_closed_aux_inventory

# ---------------------------------------------------------------------------
# STEP 21: Manifest lifecycle — preliminary manifest, finalization required later.
# ---------------------------------------------------------------------------
mark_stage "step21_manifest_generation"
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
  echo "final_post_build_integrity_ok=${POST_BUILD_INTEGRITY_OK}"
  echo "final_full_integrity_gate_all_four_yes=${FULL_INTEGRITY_GATE_ALL_FOUR_YES}"
} >> "${EVIDENCE_DIR}/HOST_RUN_METADATA.txt"

# ---------------------------------------------------------------------------
# STEP 22: Summary + exit code
# ---------------------------------------------------------------------------
mark_stage "step22_summary_and_exit"
FINAL_EXIT_CODE="${DOCKER_EXIT}"
if [[ "${POST_BUILD_INTEGRITY_OK}" != "yes" ]]; then
  FINAL_EXIT_CODE=9
fi

echo "--- Witness host summary (conservative) ---"
echo "package_version=${PACKAGE_VERSION}"
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
echo "full_integrity_gate_all_four_yes=${FULL_INTEGRITY_GATE_ALL_FOUR_YES} (evidence_inventory_complete is always 'no' from an automated host run; re-evaluate after manual Witness files + final manifest validation)"
echo "evidence_dir=${EVIDENCE_DIR}"
echo "product_executed=NO (orchestrator)"
echo "ldd_used=NO (orchestrator)"
echo "Validator stdout/stderr must be captured OUTSIDE the evidence directory."
echo "Submit evidence per WITNESS_SUBMISSION.md after redaction review and manifest finalization."

exit "${FINAL_EXIT_CODE}"
}

# Standard Bash sourced-file detection: sourcing defines helpers only.
if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  run_witness_narrow_build_main "$@"
fi
