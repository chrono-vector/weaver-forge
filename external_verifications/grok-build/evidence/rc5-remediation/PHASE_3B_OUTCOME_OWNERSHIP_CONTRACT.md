# Phase 3B — Authoritative Outcome Ownership Contract

## Base

| Item | Value |
|------|-------|
| Branch | `main` |
| Base commit | `24a329c5fca4f9ee2ec974509ea589ecb402f876` |
| RC4 fixed tag | `grok-build-witness-v1.0.0-rc4` → `039b46737c5968a81fb756d7a6d1d0dd57b6ad96` |
| RC4 disposition | **NOT READY** (unchanged) |
| RC5 tag | **absent** |
| Independent Witness reproduction | **NOT PERFORMED** |
| Independent Witness PASS | **not claimed** |
| C-014 | **NOT_STARTED** |

## Phase 3A findings (inputs to this contract)

Relevant blockers for outcome ownership / result-tuple work include RC4B-011 through RC4B-019, RC4B-022 through RC4B-024, RC4B-029, RC4B-034, and RC4B-040. Intentional deferrals remain RC4B-005=OPEN and RC4B-009=OPEN.

Critical current findings this contract addresses as **normative rules only** (no runtime fix in Phase 3B):

- Host exit 0 is currently based on Docker exit plus partial post-build checks.
- Host does not invoke the validator.
- Host reads only `outcome=` rather than a complete authoritative tuple.
- Host may overwrite container `BUILD_EXIT_CODE.txt`.
- Validator may infer a missing outcome.
- `POST_BUILD` may say `status=OK` while one or more gates are false.
- Negative outcomes can leave final `NOT_REACHED` evidence.

## Normative machine contract

**Path:** [`AUTHORITATIVE_OUTCOME_CONTRACT.json`](../../witness-package/AUTHORITATIVE_OUTCOME_CONTRACT.json)

| Field | Value |
|-------|-------|
| `contract_version` | `1.0.0-phase3b` |
| `contract_status` | `CONTRACT_DEFINED_ON_MAIN_IMPLEMENTATION_PENDING` |
| Scope | Vocabulary, producer ownership, result tuple, no-inference, no-overwrite, success eligibility |
| Runtime claim | **None.** Current scripts/validator remain noncompliant in identified areas. |

## Terminal outcome vocabulary (exactly five)

| Value | success_capable | cargo_started | Notes |
|-------|-----------------|---------------|-------|
| `BUILD_NOT_STARTED` | false | NO | Cargo never invoked |
| `CARGO_FAILED` | false | YES | Nonzero cargo exit |
| `CARGO_SUCCEEDED_ARTIFACT_MISSING` | false | YES | Cargo exit 0, artifact absent |
| `CARGO_SUCCEEDED_ARTIFACT_PRESENT` | true | YES | Cargo exit 0, artifact present; **not alone sufficient for PASS / host exit 0** |
| `INFRASTRUCTURE_FAILURE` | false | YES or NO | Must identify failure owner/stage; must **not** impose universal `cargo_started=NO` |

## Nonterminal sentinel vocabulary (not terminal outcomes)

`NOT_REACHED`, `NOT_STARTED`, `NOT_APPLICABLE`, `RECORDED`, `CHECKED`, `pending`, `pending_container_toolchain_capture`, `bootstrap_complete`

Sentinels must not be silently converted into terminal authoritative outcomes.

## Producer ownership

1. Container owns the build execution outcome after container execution begins.
2. Host owns only host infrastructure and orchestration facts.
3. Host must not overwrite a valid container authoritative outcome merely because a later host integrity gate fails.
4. A later host integrity failure must be represented in a separate host-owned result field.
5. Missing, empty, duplicate, malformed, or unsupported authoritative outcome must fail closed.
6. Validator must not infer the authoritative outcome from `cargo_started`, `build_status`, artifact fields, or exit codes.
7. Terminal outcome must be explicitly present exactly once.
8. Nonterminal sentinels must not be accepted as terminal outcomes.
9. `CARGO_SUCCEEDED_ARTIFACT_PRESENT` is only success-capable; it is not itself sufficient for PASS or host exit 0.
10. Every failure-only outcome is permanently ineligible for PASS.

### Ownership map

| Owner | Fields |
|-------|--------|
| Container | `container_outcome`, `cargo_started`, `cargo_exit_code`, `artifact_present`, `artifact_identity_complete`, `static_inspection_complete` |
| Host | `container_exit_code` (Docker process exit), `host_infrastructure_status`, `host_source_integrity_status`, `post_build_integrity_status`, `evidence_completeness_status` |
| Validator | `validator_status`, `machine_verdict_ceiling` |
| Shared identity | `schema_version`, `run_id` |

## Authoritative result tuple (minimum)

`schema_version`, `run_id`, `container_outcome`, `container_exit_code`, `cargo_started`, `cargo_exit_code`, `artifact_present`, `artifact_identity_complete`, `static_inspection_complete`, `host_infrastructure_status`, `host_source_integrity_status`, `post_build_integrity_status`, `evidence_completeness_status`, `validator_status`, `machine_verdict_ceiling`

Rules:

- No component may silently overwrite a field owned by another component.
- Contradictory tuple values must be rejected, not normalized.
- Missing required tuple members must be rejected.
- Success acceptance requires every declared success requirement.

## No-inference rule

Prohibited: deriving `container_outcome` from `cargo_started`, `build_status`, `artifact_present`, `cargo_exit_code`, or Docker exit code; replacing a missing outcome with `INFRASTRUCTURE_FAILURE` merely to make a package structurally valid.

Allowed: record a separate host infrastructure failure; retain the original missing/invalid container outcome as missing/invalid; success must be impossible.

## No-overwrite rule

Host must not replace a valid container outcome after source HEAD mismatch, dirty-tree detection, post-build integrity failure, evidence completeness failure, or validator failure.

Required future representation: `container_outcome` unchanged; host-owned fields record `FAILED` / incompleteness as applicable; success becomes impossible without altering the container outcome.

## Success eligibility

Preliminary success is possible only when **all** declared gates are true (explicit terminal outcome `CARGO_SUCCEEDED_ARTIFACT_PRESENT`, Docker exit 0, cargo started/exit 0, artifact present, artifact identity complete, static inspection complete and successful, host infrastructure OK, source integrity OK, post-build integrity OK, evidence completeness COMPLETE, validator PASS, machine verdict ceiling permits PASS).

A single false, missing, duplicate, malformed, `NOT_REACHED`, `NOT_STARTED`, or `NOT_APPLICABLE` value in a required success field prevents success.

Host gating is **not** implemented in Phase 3B.

## Known implementation violations (UNRESOLVED)

These are **not** acceptable. They remain visible until later phases remove them.

| ID | Status | Component | Remediation |
|----|--------|-----------|-------------|
| `VALIDATOR_DETERMINE_OUTCOME_INFERENCE` | **UNRESOLVED_IMPLEMENTATION_VIOLATION** | `validate_witness_evidence.py` → `determine_outcome` infers from `cargo_started`/`build_status` | Later validator slice (not Phase 3B) |
| `HOST_OVERWRITES_CONTAINER_BUILD_EXIT_CODE` | **UNRESOLVED_IMPLEMENTATION_VIOLATION** | `run_witness_narrow_build.sh` → `enforce_post_docker_source_integrity_boundary` (and related host rewrites of `BUILD_EXIT_CODE.txt`) | Phase 3D |

Phase 3B does **not** change host, container, or validator semantic code.

## Later remediation slices

| Slice | Scope |
|-------|-------|
| Phase 3C | Container finalizers |
| Phase 3D | Host ingestion (no-overwrite; host-owned failure fields) |
| Phase 3E | POST_BUILD generation |
| Phase 3F | Validator-gated exit |
| Phase 3G | Generator-backed tests |

## Blocker tracking (Phase 3B)

| ID | Status after Phase 3B |
|----|------------------------|
| RC4B-014 | `CONTRACT_DEFINED_ON_MAIN_IMPLEMENTATION_PENDING` |
| RC4B-022 | `CONTRACT_DEFINED_ON_MAIN_IMPLEMENTATION_PENDING` |
| RC4B-023 | `CONTRACT_DEFINED_ON_MAIN_IMPLEMENTATION_PENDING` |
| RC4B-019 | **OPEN** (unchanged) |
| RC4B-005 | **OPEN** (unchanged) |
| RC4B-009 | **OPEN** (unchanged) |

**Contract definition alone does not remediate runtime behavior.** Closure requires implementation plus a future fixed candidate and repeat static audit. **No blocker is CLOSED.** Do not use `REMEDIATED_ON_MAIN_PENDING_REAUDIT` for these contract-only advances.

## Explicit non-claims

- No scripts or validator semantics changed in Phase 3B.
- No blocker CLOSED.
- RC4 remains **NOT READY**.
- RC5 tag absent.
- No Independent Witness reproduction / PASS.
- C-014 remains **NOT_STARTED**.
- Remote tag state was not rechecked (no network used in this phase).
