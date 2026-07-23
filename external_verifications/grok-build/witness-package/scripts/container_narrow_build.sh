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
# Phase 3C: every supported terminal container path routes through
# finalize_container_terminal_outcome, which atomically terminalizes
# container-owned evidence exactly once. Host-owned files
# (POST_BUILD_INTEGRITY.txt, DOCKER_EXIT_CODE.txt) are never written here.
# The validator is never invoked from this script.
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
#
# Writer-failure boundary: if the evidence directory is not writable, this
# script cannot produce a complete evidence package. Best-effort stderr is
# emitted; EVIDENCE_FINALIZED is never set to YES; exit is nonzero.
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
FINALIZING_IN_PROGRESS="NO"
CONTAINER_MAIN_ACTIVE="NO"
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

# Phase 3C contract terminal vocabulary (exact five).
TERMINAL_CONTAINER_OUTCOMES=(
  BUILD_NOT_STARTED
  CARGO_FAILED
  CARGO_SUCCEEDED_ARTIFACT_MISSING
  CARGO_SUCCEEDED_ARTIFACT_PRESENT
  INFRASTRUCTURE_FAILURE
)

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

# Reject CR/LF in dynamically generated single-line field values.
reject_field_newlines() {
  local label="$1"
  local value="$2"
  if [[ "${value}" == *$'\n'* || "${value}" == *$'\r'* ]]; then
    echo "FATAL: field ${label} contains CR/LF; refusing to write" >&2
    return 1
  fi
  return 0
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

is_terminal_container_outcome() {
  local candidate="$1"
  local o
  for o in "${TERMINAL_CONTAINER_OUTCOMES[@]}"; do
    if [[ "${candidate}" == "${o}" ]]; then
      return 0
    fi
  done
  return 1
}

# --- Atomic evidence writer -------------------------------------------------
# Writes stdin to a same-directory temporary file, then renames into place.
# On ordinary write failure the final path is not truncated; temp is removed.
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

# Atomically rewrite a file replacing the first key= line (or append if absent).
replace_kv_file_atomic() {
  local file="$1"
  local key="$2"
  local value="$3"
  local tmp line replaced=0
  reject_field_newlines "${key}" "${value}" || return 1
  if [[ ! -f "${file}" ]]; then
    printf '%s=%s\n' "${key}" "${value}" | write_evidence_file_atomic "${file}"
    return $?
  fi
  tmp="${file}.repl.$$.${RANDOM}"
  {
    while IFS= read -r line || [[ -n "${line}" ]]; do
      if [[ "${replaced}" -eq 0 && "${line}" == "${key}="* ]]; then
        printf '%s=%s\n' "${key}" "${value}"
        replaced=1
      else
        printf '%s\n' "${line}"
      fi
    done < "${file}"
    if [[ "${replaced}" -eq 0 ]]; then
      printf '%s=%s\n' "${key}" "${value}"
    fi
  } > "${tmp}" || {
    rm -f -- "${tmp}" 2>/dev/null || true
    return 1
  }
  if ! mv -f -- "${tmp}" "${file}"; then
    rm -f -- "${tmp}" 2>/dev/null || true
    return 1
  fi
  return 0
}

# --- Evidence writers -------------------------------------------------------

# Writes BUILD_EXIT_CODE.txt and BUILD_TIMING.txt with rc4 schema field names.
# Never leaves NOT_REACHED as final for completed failure paths.
write_outcome_evidence() {
  local outcome="$1" cargo_started="$2" build_status="$3" cargo_exit_code="$4"
  local docker_exit_code="$5" failure_stage="$6" status="$7"
  local cargo_started_utc="$8" cargo_finished_utc="$9" cargo_elapsed_seconds="${10}"

  reject_field_newlines "outcome" "${outcome}" || return 1
  reject_field_newlines "failure_stage" "${failure_stage}" || return 1
  reject_field_newlines "cargo_exit_code" "${cargo_exit_code}" || return 1

  write_evidence_file_atomic "${EVIDENCE}/BUILD_EXIT_CODE.txt" <<EOF || return 1
BEGIN_SCHEMA_BLOCK BUILD_EXIT_CODE
evidence_schema_version=${EVIDENCE_SCHEMA_VERSION}
status=${status}
outcome=${outcome}
cargo_started=${cargo_started}
build_status=${build_status}
cargo_exit_code=${cargo_exit_code}
failure_stage=${failure_stage}
END_SCHEMA_BLOCK
EOF

  write_evidence_file_atomic "${EVIDENCE}/BUILD_TIMING.txt" <<EOF || return 1
BEGIN_SCHEMA_BLOCK BUILD_TIMING
evidence_schema_version=${EVIDENCE_SCHEMA_VERSION}
status=${status}
outcome=${outcome}
docker_started_utc=NOT_APPLICABLE
docker_finished_utc=NOT_APPLICABLE
docker_elapsed_seconds=NOT_APPLICABLE
cargo_started_utc=${cargo_started_utc}
cargo_finished_utc=${cargo_finished_utc}
cargo_elapsed_seconds=${cargo_elapsed_seconds}
cargo_started=${cargo_started}
cargo_exit_code=${cargo_exit_code}
docker_exit_code=${docker_exit_code}
failure_stage=${failure_stage}
END_SCHEMA_BLOCK
EOF
  return 0
}

# Truthful "no artifact" ARTIFACT_IDENTITY.txt / STATIC_ARTIFACT_INSPECTION.txt.
# applicable=yes only when the outcome expects an artifact check
# (CARGO_SUCCEEDED_ARTIFACT_MISSING); otherwise applicable=no.
write_no_artifact_evidence() {
  local reason="$1"
  local applicable="${2:-no}"
  local outcome="${3:-BUILD_NOT_STARTED}"
  reject_field_newlines "reason" "$(escape_oneline "${reason}")" || return 1
  local reason_esc
  reason_esc="$(escape_oneline "${reason}")"

  write_evidence_file_atomic "${EVIDENCE}/ARTIFACT_IDENTITY.txt" <<EOF || return 1
evidence_schema_version=${EVIDENCE_SCHEMA_VERSION}
outcome=${outcome}
applicable=${applicable}
artifact_present=no
reason=${reason_esc}
product_executed=NO
ldd_used=NO
EOF

  write_evidence_file_atomic "${EVIDENCE}/STATIC_ARTIFACT_INSPECTION.txt" <<EOF || return 1
BEGIN_SCHEMA_BLOCK STATIC_ARTIFACT_INSPECTION
evidence_schema_version=${EVIDENCE_SCHEMA_VERSION}
status=NOT_APPLICABLE
outcome=${outcome}
applicable=no
artifact_present=no
artifact_path=NOT_APPLICABLE
sha256sum_command=NOT_APPLICABLE
sha256sum_output=NOT_APPLICABLE
sha256sum_exit_code=NOT_APPLICABLE
stat_command=NOT_APPLICABLE
stat_output=NOT_APPLICABLE
stat_exit_code=NOT_APPLICABLE
file_command=NOT_APPLICABLE
file_output=NOT_APPLICABLE
file_exit_code=NOT_APPLICABLE
readelf_h_command=NOT_APPLICABLE
readelf_h_output=NOT_APPLICABLE
readelf_h_exit_code=NOT_APPLICABLE
readelf_n_command=NOT_APPLICABLE
readelf_n_output=NOT_APPLICABLE
readelf_n_exit_code=NOT_APPLICABLE
readelf_d_command=NOT_APPLICABLE
readelf_d_output=NOT_APPLICABLE
readelf_d_exit_code=NOT_APPLICABLE
objdump_f_command=NOT_APPLICABLE
objdump_f_output=NOT_APPLICABLE
objdump_f_exit_code=NOT_APPLICABLE
inspection_complete=no
failure_stage=NONE
reason=${reason_esc}
END_SCHEMA_BLOCK
EOF
  return 0
}

# Best-effort (non-fallible preferred) artifact record used when cargo ran but
# the normal artifact-evidence path never completed.
write_artifact_evidence_best_effort() {
  local stage="$1"
  if [[ -f "${ARTIFACT}" ]]; then
    write_evidence_file_atomic "${EVIDENCE}/ARTIFACT_IDENTITY.txt" <<EOF || return 1
evidence_schema_version=${EVIDENCE_SCHEMA_VERSION}
applicable=yes
artifact_present=yes
artifact_path=${ARTIFACT}
note=unexpected script failure at stage=${stage}; full identity capture not completed
product_executed=NO
ldd_used=NO
EOF
    write_evidence_file_atomic "${EVIDENCE}/STATIC_ARTIFACT_INSPECTION.txt" <<EOF || return 1
BEGIN_SCHEMA_BLOCK STATIC_ARTIFACT_INSPECTION
evidence_schema_version=${EVIDENCE_SCHEMA_VERSION}
status=FAILED
outcome=NOT_APPLICABLE
applicable=yes
artifact_present=yes
artifact_path=${ARTIFACT}
sha256sum_command=
sha256sum_output=
sha256sum_exit_code=
stat_command=
stat_output=
stat_exit_code=
file_command=
file_output=
file_exit_code=
readelf_h_command=
readelf_h_output=
readelf_h_exit_code=
readelf_n_command=
readelf_n_output=
readelf_n_exit_code=
readelf_d_command=
readelf_d_output=
readelf_d_exit_code=
objdump_f_command=
objdump_f_output=
objdump_f_exit_code=
inspection_complete=no
failure_stage=${stage}
reason=unexpected script failure at stage=${stage} before static inspection completed
END_SCHEMA_BLOCK
EOF
  else
    write_no_artifact_evidence "unexpected script failure at stage=${stage}; artifact not present at check time" "no" "INFRASTRUCTURE_FAILURE" || return 1
  fi
  return 0
}

# Rewrite CLEAN_TARGET_PROOF schema block; listings are labelled human-review
# sections (not duplicate structured keys).
flush_clean_target_proof() {
  write_evidence_file_atomic "${EVIDENCE}/CLEAN_TARGET_PROOF.txt" <<EOF || return 1
BEGIN_SCHEMA_BLOCK CLEAN_TARGET
evidence_schema_version=${EVIDENCE_SCHEMA_VERSION}
status=${CT_STATUS}
outcome=${CT_OUTCOME}
target_path_host=${CT_TARGET_PATH_HOST}
proof_utc_host=${CT_PROOF_UTC_HOST}
observed_entry_count_host=${CT_OBS_HOST}
target_path_container_prebootstrap=${CT_TARGET_PREBOOT}
proof_utc_container_prebootstrap=${CT_UTC_PREBOOT}
observed_entry_count_container_prebootstrap=${CT_OBS_PREBOOT}
target_path_container_precargo=${CT_TARGET_PRECARGO}
proof_utc_container_precargo=${CT_UTC_PRECARGO}
observed_entry_count_container=${CT_OBS_CONTAINER}
proof_failed=${CT_PROOF_FAILED}
failure_stage=${CT_FAILURE_STAGE}
END_SCHEMA_BLOCK
$(if [[ -n "${CT_LISTINGS}" ]]; then printf '# --- listings ---\n%s' "${CT_LISTINGS}"; fi)
EOF
  return 0
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
    write_evidence_file_atomic "${EVIDENCE}/ENVIRONMENT.txt" <<EOF || return 1
evidence_schema_version=${EVIDENCE_SCHEMA_VERSION}
status=pending_container_toolchain_capture
EOF
  fi

  write_evidence_file_atomic "${EVIDENCE}/BUILD_EXIT_CODE.txt" <<EOF || return 1
BEGIN_SCHEMA_BLOCK BUILD_EXIT_CODE
evidence_schema_version=${EVIDENCE_SCHEMA_VERSION}
status=NOT_REACHED
outcome=NOT_REACHED
cargo_started=NO
build_status=NOT_REACHED
cargo_exit_code=NOT_REACHED
failure_stage=NOT_REACHED
END_SCHEMA_BLOCK
EOF

  write_evidence_file_atomic "${EVIDENCE}/BUILD_TIMING.txt" <<EOF || return 1
BEGIN_SCHEMA_BLOCK BUILD_TIMING
evidence_schema_version=${EVIDENCE_SCHEMA_VERSION}
status=NOT_REACHED
outcome=NOT_REACHED
docker_started_utc=NOT_REACHED
docker_finished_utc=NOT_REACHED
docker_elapsed_seconds=NOT_REACHED
cargo_started_utc=NOT_REACHED
cargo_finished_utc=NOT_REACHED
cargo_elapsed_seconds=NOT_REACHED
cargo_started=NO
cargo_exit_code=NOT_REACHED
docker_exit_code=NOT_REACHED
failure_stage=NOT_REACHED
END_SCHEMA_BLOCK
EOF

  write_evidence_file_atomic "${EVIDENCE}/BOOTSTRAP.txt" <<EOF || return 1
evidence_schema_version=${EVIDENCE_SCHEMA_VERSION}
status=NOT_REACHED
EOF

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
  flush_clean_target_proof || return 1

  write_evidence_file_atomic "${EVIDENCE}/BUILD_COMMAND.txt" <<EOF || return 1
evidence_schema_version=${EVIDENCE_SCHEMA_VERSION}
status=NOT_REACHED
exact_build_command=${CANONICAL_BUILD_CMD}
cargo_incremental=0
working_directory=/src
product_executed=NO
EOF

  write_evidence_file_atomic "${EVIDENCE}/BUILD_ENVIRONMENT.txt" <<EOF || return 1
BEGIN_SCHEMA_BLOCK BUILD_ENVIRONMENT
evidence_schema_version=${EVIDENCE_SCHEMA_VERSION}
status=NOT_REACHED
outcome=NOT_REACHED
docker_platform=linux/amd64
network_mode=bridge
rust_image=${RUST_IMAGE}
workdir=/src
home=${HOME}
cargo_home=${CARGO_HOME}
cargo_target_dir=${CARGO_TARGET_DIR_GROK}
bootstrap_cargo_target_dir=${BOOTSTRAP_CARGO_TARGET_DIR}
cargo_incremental=0
dotslash_cache=${DOTSLASH_CACHE}
path=NOT_REACHED
grok_build_commit=${GROK_BUILD_COMMIT}
expected_cargo_lock_sha256=${EXPECTED_CARGO_LOCK_SHA256}
canonical_build_command=${CANONICAL_BUILD_CMD}
mount_src=/src:ro
mount_work=broad_WORK_ROOT_mount_prohibited
mount_evidence=/evidence:rw
mount_container_script=/witness/container_narrow_build.sh:ro
END_SCHEMA_BLOCK
EOF

  write_no_artifact_evidence "container run in progress; artifact not yet built" "no" "BUILD_NOT_STARTED" || return 1
}

record_build_environment() {
  write_evidence_file_atomic "${EVIDENCE}/BUILD_ENVIRONMENT.txt" <<EOF || return 1
BEGIN_SCHEMA_BLOCK BUILD_ENVIRONMENT
evidence_schema_version=${EVIDENCE_SCHEMA_VERSION}
status=OK
outcome=RECORDED
docker_platform=linux/amd64
network_mode=bridge
rust_image=${RUST_IMAGE}
workdir=/src
home=${HOME}
cargo_home=${CARGO_HOME}
cargo_target_dir=${CARGO_TARGET_DIR_GROK}
bootstrap_cargo_target_dir=${BOOTSTRAP_CARGO_TARGET_DIR}
cargo_incremental=0
dotslash_cache=${DOTSLASH_CACHE}
path=${PATH}
grok_build_commit=${GROK_BUILD_COMMIT}
expected_cargo_lock_sha256=${EXPECTED_CARGO_LOCK_SHA256}
canonical_build_command=${CANONICAL_BUILD_CMD}
mount_src=/src:ro
mount_work=broad_WORK_ROOT_mount_prohibited
mount_evidence=/evidence:rw
mount_container_script=/witness/container_narrow_build.sh:ro
END_SCHEMA_BLOCK
EOF
}

# --- Phase 3C centralized terminal finalization ----------------------------

_terminalize_bootstrap_file() {
  local outcome="$1"
  local stage="$2"
  local f="${EVIDENCE}/BOOTSTRAP.txt"
  local status body
  [[ -f "${f}" ]] || return 0
  status="$(read_kv "${f}" "status" "")"
  if [[ "${status}" == "bootstrap_complete" ]]; then
    replace_kv_file_atomic "${f}" "status" "OK" || return 1
    return 0
  fi
  if [[ "${status}" == "pending" || "${status}" == "pending_container_toolchain_capture" ]]; then
    replace_kv_file_atomic "${f}" "status" "FAILED" || return 1
    return 0
  fi
  if [[ "${status}" == "NOT_REACHED" ]]; then
    # Early pre-bootstrap failure: NOT_REACHED remains the schema-permitted
    # placeholder terminal for PLACEHOLDER_ELIGIBLE BOOTSTRAP.txt.
    # Partial bootstrap content without completion: mark FAILED.
    if grep -qE '^(apt_packages|dotslash_|protoc_)' "${f}" 2>/dev/null; then
      replace_kv_file_atomic "${f}" "status" "FAILED" || return 1
    fi
    return 0
  fi
  if [[ -z "${status}" ]]; then
    # Bootstrap body written without a status key (mid-bootstrap failure path).
    body="$(cat "${f}")"$'\n'"status=FAILED"$'\n'"failure_stage=${stage}"$'\n'"outcome=${outcome}"
    printf '%s\n' "${body}" | write_evidence_file_atomic "${f}" || return 1
  fi
  return 0
}

_terminalize_build_command_file() {
  local outcome="$1"
  local f="${EVIDENCE}/BUILD_COMMAND.txt"
  local status
  [[ -f "${f}" ]] || return 0
  status="$(read_kv "${f}" "status" "")"
  if [[ "${status}" == "NOT_REACHED" || "${status}" == "pending" ]]; then
    if [[ "${outcome}" == "CARGO_SUCCEEDED_ARTIFACT_PRESENT" || "${outcome}" == "CARGO_SUCCEEDED_ARTIFACT_MISSING" || "${outcome}" == "CARGO_FAILED" ]]; then
      replace_kv_file_atomic "${f}" "status" "RECORDED" || return 1
    else
      # Early failure: FAILED is a truthful terminal alternative to NOT_REACHED
      # when exact_build_command facts are already present from init.
      replace_kv_file_atomic "${f}" "status" "FAILED" || return 1
    fi
  fi
  return 0
}

_terminalize_build_environment_file() {
  local outcome="$1"
  local f="${EVIDENCE}/BUILD_ENVIRONMENT.txt"
  local status
  [[ -f "${f}" ]] || return 0
  status="$(read_kv "${f}" "status" "")"
  # status vocabulary is OK|RECORDED|NOT_REACHED only — no FAILED alternative.
  if [[ "${status}" == "NOT_REACHED" ]]; then
    replace_kv_file_atomic "${f}" "outcome" "${outcome}" || return 1
    local path_val
    path_val="$(read_kv "${f}" "path" "")"
    if [[ "${path_val}" == "NOT_REACHED" ]]; then
      replace_kv_file_atomic "${f}" "path" "NOT_APPLICABLE" || return 1
    fi
  fi
  return 0
}

_terminalize_environment_file() {
  local outcome="$1"
  local f="${EVIDENCE}/ENVIRONMENT.txt"
  [[ -f "${f}" ]] || return 0
  if grep -q '^status=pending_container_toolchain_capture$' "${f}" 2>/dev/null; then
    replace_kv_file_atomic "${f}" "status" "FAILED" || return 1
  fi
  # Do not invent host-owned keys; only clear container provisional status.
  if ! grep -q "^outcome=" "${f}" 2>/dev/null; then
    # Append container-visible outcome note only when absent (host may own outcome).
    :
  fi
  return 0
}

_terminalize_clean_target_state() {
  local outcome="$1"
  local stage="$2"
  if [[ "${CT_STATUS}" == "pending" || "${CT_STATUS}" == "NOT_REACHED" ]]; then
    CT_STATUS="FAILED"
  fi
  if [[ "${CT_OUTCOME}" == "NOT_REACHED" || "${CT_OUTCOME}" == "pending" ]]; then
    CT_OUTCOME="${outcome}"
  fi
  if [[ "${CT_FAILURE_STAGE}" == "NOT_REACHED" && "${CT_STATUS}" == "FAILED" ]]; then
    CT_FAILURE_STAGE="${stage}"
  fi
  flush_clean_target_proof || return 1
  return 0
}

# Ensure raw cargo streams exist (may be empty — truthful when cargo never ran).
_ensure_build_streams() {
  [[ -f "${EVIDENCE}/BUILD_STDOUT.txt" ]] || : > "${EVIDENCE}/BUILD_STDOUT.txt" || return 1
  [[ -f "${EVIDENCE}/BUILD_STDERR.txt" ]] || : > "${EVIDENCE}/BUILD_STDERR.txt" || return 1
  return 0
}

# Centralized, idempotent terminal finalization boundary.
# Args:
#   1: terminal outcome (exact contract vocabulary)
#   2: container/build exit code
#   3: failure_stage
#   4: exit_status for BUILD_EXIT_CODE status field (OK|FAILED); default FAILED
#   5: build_status field; default derived from outcome
#   6: artifact_mode: none | preserve | best_effort | missing_applicable
#
# Never infers a different outcome from secondary facts.
# Never writes POST_BUILD_INTEGRITY.txt or DOCKER_EXIT_CODE.txt.
# Never invokes the validator.
# Sets EVIDENCE_FINALIZED=YES only after required final writes succeed.
finalize_container_terminal_outcome() {
  local outcome="$1"
  local exit_code="$2"
  local failure_stage="$3"
  local exit_status="${4:-FAILED}"
  local build_status="${5:-}"
  local artifact_mode="${6:-}"

  local cargo_started_field cargo_exit_field
  local cargo_started_utc cargo_finished_utc cargo_elapsed
  local existing_outcome
  local write_rc=0
  local artifact_reason=""

  _finalize_end() {
    FINALIZING_IN_PROGRESS="NO"
    if [[ "${CONTAINER_MAIN_ACTIVE}" == "YES" ]]; then
      trap on_err ERR
    else
      trap - ERR
    fi
  }

  if [[ "${FINALIZING_IN_PROGRESS}" == "YES" ]]; then
    echo "finalize_container_terminal_outcome: recursion prevented" >&2
    return 1
  fi
  FINALIZING_IN_PROGRESS="YES"

  # Disable ERR trap recursion for the duration of finalization (no eval).
  trap - ERR
  set +e

  if [[ -z "${EVIDENCE:-}" || ! -d "${EVIDENCE}" ]]; then
    echo "finalize_container_terminal_outcome: evidence directory unavailable; cannot complete evidence package" >&2
    _finalize_end
    return 1
  fi

  if ! is_terminal_container_outcome "${outcome}"; then
    echo "finalize_container_terminal_outcome: unsupported outcome=${outcome}" >&2
    _finalize_end
    return 1
  fi

  reject_field_newlines "failure_stage" "${failure_stage}" || {
    _finalize_end
    return 1
  }

  # Idempotent / fail-closed on conflicting repeat finalization.
  if [[ "${EVIDENCE_FINALIZED}" == "YES" ]]; then
    existing_outcome="$(read_kv "${EVIDENCE}/BUILD_EXIT_CODE.txt" "outcome" "")"
    if [[ "${existing_outcome}" == "${outcome}" ]]; then
      _finalize_end
      return 0
    fi
    echo "finalize_container_terminal_outcome: conflicting repeat finalization existing=${existing_outcome} requested=${outcome}" >&2
    _finalize_end
    return 1
  fi

  # Derive tuple fields from the explicit outcome (never from secondary inference
  # that would replace the caller-supplied outcome).
  case "${outcome}" in
    BUILD_NOT_STARTED)
      cargo_started_field="NO"
      cargo_exit_field="NOT_APPLICABLE"
      cargo_started_utc="NOT_APPLICABLE"
      cargo_finished_utc="NOT_APPLICABLE"
      cargo_elapsed="NOT_APPLICABLE"
      [[ -n "${build_status}" ]] || build_status="BUILD_NOT_STARTED"
      [[ -n "${artifact_mode}" ]] || artifact_mode="none"
      exit_status="FAILED"
      ;;
    CARGO_FAILED)
      cargo_started_field="YES"
      if [[ -n "${CARGO_EXIT_CODE}" ]]; then
        cargo_exit_field="${CARGO_EXIT_CODE}"
      else
        cargo_exit_field="${exit_code}"
      fi
      cargo_started_utc="${CARGO_START_UTC:-NOT_APPLICABLE}"
      cargo_finished_utc="${CARGO_END_UTC:-$(ts)}"
      cargo_elapsed="${CARGO_ELAPSED_SECONDS:-NOT_APPLICABLE}"
      [[ -n "${build_status}" ]] || build_status="FAILED"
      [[ -n "${artifact_mode}" ]] || artifact_mode="none"
      exit_status="FAILED"
      ;;
    CARGO_SUCCEEDED_ARTIFACT_MISSING)
      cargo_started_field="YES"
      cargo_exit_field="0"
      cargo_started_utc="${CARGO_START_UTC:-NOT_APPLICABLE}"
      cargo_finished_utc="${CARGO_END_UTC:-$(ts)}"
      cargo_elapsed="${CARGO_ELAPSED_SECONDS:-NOT_APPLICABLE}"
      [[ -n "${build_status}" ]] || build_status="COMPLETE"
      [[ -n "${artifact_mode}" ]] || artifact_mode="missing_applicable"
      exit_status="FAILED"
      ;;
    CARGO_SUCCEEDED_ARTIFACT_PRESENT)
      cargo_started_field="YES"
      cargo_exit_field="0"
      cargo_started_utc="${CARGO_START_UTC:-NOT_APPLICABLE}"
      cargo_finished_utc="${CARGO_END_UTC:-$(ts)}"
      cargo_elapsed="${CARGO_ELAPSED_SECONDS:-NOT_APPLICABLE}"
      [[ -n "${build_status}" ]] || build_status="COMPLETE"
      [[ -n "${artifact_mode}" ]] || artifact_mode="preserve"
      # exit_status remains caller-supplied (OK on static success, FAILED on static failure)
      ;;
    INFRASTRUCTURE_FAILURE)
      cargo_started_field="${CARGO_STARTED}"
      if [[ -n "${CARGO_EXIT_CODE}" ]]; then
        cargo_exit_field="${CARGO_EXIT_CODE}"
      else
        cargo_exit_field="NOT_APPLICABLE"
      fi
      if [[ "${CARGO_STARTED}" == "YES" ]]; then
        cargo_started_utc="${CARGO_START_UTC:-NOT_APPLICABLE}"
        cargo_finished_utc="${CARGO_END_UTC:-$(ts)}"
        cargo_elapsed="${CARGO_ELAPSED_SECONDS:-NOT_APPLICABLE}"
        [[ -n "${artifact_mode}" ]] || artifact_mode="best_effort"
      else
        cargo_started_utc="NOT_APPLICABLE"
        cargo_finished_utc="NOT_APPLICABLE"
        cargo_elapsed="NOT_APPLICABLE"
        [[ -n "${artifact_mode}" ]] || artifact_mode="none"
      fi
      [[ -n "${build_status}" ]] || build_status="INFRASTRUCTURE_FAILURE"
      exit_status="FAILED"
      ;;
  esac

  _ensure_build_streams || write_rc=1

  case "${artifact_mode}" in
    none)
      case "${outcome}" in
        BUILD_NOT_STARTED)
          artifact_reason="cargo never started (failing_stage=${failure_stage})"
          ;;
        CARGO_FAILED)
          artifact_reason="cargo build exited nonzero (${cargo_exit_field})"
          ;;
        INFRASTRUCTURE_FAILURE)
          artifact_reason="unexpected infrastructure failure at stage=${failure_stage}; cargo never started"
          ;;
        *)
          artifact_reason="artifact not applicable (outcome=${outcome}; stage=${failure_stage})"
          ;;
      esac
      write_no_artifact_evidence "${artifact_reason}" "no" "${outcome}" || write_rc=1
      ;;
    missing_applicable)
      write_no_artifact_evidence \
        "cargo exited 0 but expected artifact ${ARTIFACT} is missing" \
        "yes" "${outcome}" || write_rc=1
      ;;
    preserve)
      # Caller already wrote ARTIFACT_IDENTITY / STATIC_ARTIFACT_INSPECTION.
      if [[ ! -f "${EVIDENCE}/ARTIFACT_IDENTITY.txt" || ! -f "${EVIDENCE}/STATIC_ARTIFACT_INSPECTION.txt" ]]; then
        echo "finalize_container_terminal_outcome: preserve mode missing artifact evidence files" >&2
        write_rc=1
      fi
      ;;
    best_effort)
      write_artifact_evidence_best_effort "${failure_stage}" || write_rc=1
      ;;
    *)
      echo "finalize_container_terminal_outcome: unknown artifact_mode=${artifact_mode}" >&2
      write_rc=1
      ;;
  esac

  _terminalize_clean_target_state "${outcome}" "${failure_stage}" || write_rc=1
  _terminalize_bootstrap_file "${outcome}" "${failure_stage}" || write_rc=1
  _terminalize_build_command_file "${outcome}" || write_rc=1
  _terminalize_build_environment_file "${outcome}" || write_rc=1
  _terminalize_environment_file "${outcome}" || write_rc=1

  write_outcome_evidence \
    "${outcome}" "${cargo_started_field}" "${build_status}" "${cargo_exit_field}" \
    "${exit_code}" "${failure_stage}" "${exit_status}" \
    "${cargo_started_utc}" "${cargo_finished_utc}" "${cargo_elapsed}" || write_rc=1

  # Explicitly do not create or modify host-owned POST_BUILD_INTEGRITY.txt
  # or DOCKER_EXIT_CODE.txt.

  if [[ "${write_rc}" -ne 0 ]]; then
    echo "finalize_container_terminal_outcome: one or more mandatory final writes failed; evidence incomplete; EVIDENCE_FINALIZED remains NO" >&2
    _finalize_end
    return 1
  fi

  EVIDENCE_FINALIZED="YES"
  _finalize_end
  return 0
}

# --- Failure handlers --------------------------------------------------------

# BUILD_NOT_STARTED: any failure strictly before `cargo build` is invoked.
fail_build_not_started() {
  local stage="$1"
  local exit_code="${2:-1}"
  if ! finalize_container_terminal_outcome "BUILD_NOT_STARTED" "${exit_code}" "${stage}"; then
    echo "BUILD_NOT_STARTED: finalizer failed at stage=${stage}; evidence not claimed complete" >&2
  fi
  echo "BUILD_NOT_STARTED: failing_stage=${stage} exit_code=${exit_code}" >&2
  exit "${exit_code}"
}

# INFRASTRUCTURE_FAILURE: generic catch-all via ERR trap / explicit infra faults.
fail_infrastructure() {
  local stage="$1"
  local exit_code="${2:-1}"
  if ! finalize_container_terminal_outcome "INFRASTRUCTURE_FAILURE" "${exit_code}" "${stage}"; then
    echo "INFRASTRUCTURE_FAILURE: finalizer failed at stage=${stage}; evidence not claimed complete" >&2
  fi
  echo "INFRASTRUCTURE_FAILURE: stage=${stage} exit_code=${exit_code}" >&2
  exit "${exit_code}"
}

on_err() {
  local ec=$?
  if [[ "${EVIDENCE_FINALIZED}" == "YES" || "${FINALIZING_IN_PROGRESS}" == "YES" ]]; then
    exit "${ec}"
  fi
  echo "ERROR: container script failed unexpectedly at line ${BASH_LINENO[0]} (exit ${ec}) during stage=${CURRENT_STAGE}" >&2
  fail_infrastructure "${CURRENT_STAGE}" "${ec}"
}

# ---------------------------------------------------------------------------
# Main pipeline (executed only when this file is run as a script)
# ---------------------------------------------------------------------------
container_narrow_build_main() {
CURRENT_STAGE="script_init"
CARGO_STARTED="NO"
CARGO_EXIT_CODE=""
EVIDENCE_FINALIZED="NO"
FINALIZING_IN_PROGRESS="NO"
CONTAINER_MAIN_ACTIVE="YES"
CARGO_START_UTC=""
CARGO_END_UTC=""
CARGO_ELAPSED_SECONDS=""
trap on_err ERR

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
  finalize_container_terminal_outcome "CARGO_FAILED" "${CARGO_EXIT_CODE}" "cargo_build" \
    "FAILED" "FAILED" "none" || true
  exit "${CARGO_EXIT_CODE}"
fi

set_stage "artifact_presence_check"
if [[ ! -f "${ARTIFACT}" ]]; then
  finalize_container_terminal_outcome "CARGO_SUCCEEDED_ARTIFACT_MISSING" "${ARTIFACT_MISSING_EXIT}" \
    "artifact_presence_check" "FAILED" "COMPLETE" "missing_applicable" || true
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

write_evidence_file_atomic "${EVIDENCE}/STATIC_ARTIFACT_INSPECTION.txt" <<EOF
BEGIN_SCHEMA_BLOCK STATIC_ARTIFACT_INSPECTION
evidence_schema_version=${EVIDENCE_SCHEMA_VERSION}
status=${STATIC_STATUS}
outcome=CARGO_SUCCEEDED_ARTIFACT_PRESENT
applicable=yes
artifact_present=yes
artifact_path=${ARTIFACT}
sha256sum_command=${SHA256_CMD}
sha256sum_output=$(escape_oneline "${SHA256_OUT}")
sha256sum_exit_code=${SHA256_EC}
stat_command=${STAT_CMD}
stat_output=$(escape_oneline "${STAT_OUT}")
stat_exit_code=${STAT_EC}
file_command=${FILE_CMD}
file_output=$(escape_oneline "${FILE_OUT}")
file_exit_code=${FILE_EC}
readelf_h_command=${READELF_H_CMD}
readelf_h_output=$(escape_oneline "${READELF_H_OUT}")
readelf_h_exit_code=${READELF_H_EC}
readelf_n_command=${READELF_N_CMD}
readelf_n_output=$(escape_oneline "${READELF_N_OUT}")
readelf_n_exit_code=${READELF_N_EC}
readelf_d_command=${READELF_D_CMD}
readelf_d_output=$(escape_oneline "${READELF_D_OUT}")
readelf_d_exit_code=${READELF_D_EC}
objdump_f_command=${OBJDUMP_F_CMD}
objdump_f_output=$(escape_oneline "${OBJDUMP_F_OUT}")
objdump_f_exit_code=${OBJDUMP_F_EC}
inspection_complete=${INSPECTION_COMPLETE}
failure_stage=${INSPECTION_FAILURE_STAGE}
reason=${INSPECTION_REASON}
END_SCHEMA_BLOCK
EOF

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

write_evidence_file_atomic "${EVIDENCE}/ARTIFACT_IDENTITY.txt" <<EOF
evidence_schema_version=${EVIDENCE_SCHEMA_VERSION}
outcome=CARGO_SUCCEEDED_ARTIFACT_PRESENT
applicable=yes
artifact_present=yes
artifact_path=${ARTIFACT}
artifact_filename=xai-grok-pager
artifact_size_bytes=${ART_SIZE}
artifact_sha256=${ART_SHA}
gnu_build_id=${GNU_BUILD_ID}
static_inspection_complete=${INSPECTION_COMPLETE}
product_executed=NO
ldd_used=NO
EOF

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

finalize_container_terminal_outcome "CARGO_SUCCEEDED_ARTIFACT_PRESENT" "${FINAL_EXIT}" \
  "${EXIT_FAILURE_STAGE}" "${EXIT_STATUS}" "COMPLETE" "preserve" || true

# Container exits with the classified status (Docker preserves it on host).
exit "${FINAL_EXIT}"
} # end container_narrow_build_main

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  container_narrow_build_main "$@"
fi
