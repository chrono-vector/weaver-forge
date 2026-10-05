# Dedicated Local Software Ed25519 Custody Helper and Runbook v0 - Human Final

Date:
2026-10-05

Status:
HUMAN_REVIEW_ACCEPTED

Scope:
Dedicated Local Software Ed25519 Custody Helper and Runbook v0

This record saves a Human Final decision explicitly made by the Human authority for this bounded scope only. It does not authorize real key generation, create private or recovery material, perform Admission PREPARE or CONFIRM, authorize signing, or add identity, role, authorization, trust, provenance, truth, evidence, currentness, or revocation semantics.

## Fixed implementation

Implementation commit (accepted as-is):
`d0aedb62904cb39c5cafa55a4b177b3154e420c7`

That commit contains the bounded helper package `ed25519_custody_v0/` and the accompanying runbook. The runbook was introduced at commit `40a00d4e12a6d617a0e897eddc527c0355349fda` as:
`docs/next/DEDICATED_LOCAL_SOFTWARE_ED25519_CUSTODY_HELPER_RUNBOOK_V0_20261005.md`

## Parent Human Design Freeze and frozen D1-R1

Human Design Freeze record:
- commit: `77100848a4485955067b8a8433b987b646f3e140`
- file: `docs/next/DEDICATED_LOCAL_SOFTWARE_ED25519_GENERATION_AND_CUSTODY_PROFILE_V0_HUMAN_DESIGN_FREEZE_20261005.md`
- SHA-256: `E1D3CEFCCDA3D1645F9FF7BA403AF0B7304C84C17DB56A8F62189DFAC97DA1D3`

Frozen D1-R1 design:
- commit: `73942f18b5089c48795039d2fe8f24bf01b0c2f7`
- file: `docs/next/DEDICATED_LOCAL_SOFTWARE_ED25519_GENERATION_AND_CUSTODY_PROFILE_V0_D1_20261005.md`
- SHA-256: `B788A240989F00A01844692C6B714E1106F936D1220C9E79AB67173DDEB01791`

## Independent final review

Independent final review status: `ACCEPT_FOR_HUMAN_FINAL`

- MATERIAL_FINDING_COUNT: 0
- NONMATERIAL_FINDING_COUNT: 3
- Behavioral tests: 120 PASS
- exact_bytes_witness_v0 regression: 38 PASS
- Source mutations observed: 87 actual (86 KILLED / 1 EQUIVALENT / 0 SURVIVED)
- M29d independently judged EQUIVALENT: removing the restore artifact-versus-working volume/file-index identity comparison is defense-in-depth only. Hard-link rejection (link count must be 1), fixed distinct restore-v0 and custody-v0 paths, reparse/junction rejection, and final-path equality already enforce the frozen invariant that restore must never read the working original as restore input; equal identity without a second hard link is not a normal NTFS two-name case.
- PRE_REAL_ENVIRONMENT_ESTABLISHED: NO
- SAFE_FOR_HUMAN_FINAL: YES

### Nonmaterial limitations recorded at final review

1. Runtime pins installed package content via wheel-origin RECORD digests (independently re-derived from lock-matching wheel artifacts). It does not re-hash original wheel bytes at runtime. This is honestly documented. PRE-REAL remains fail-closed because `_INTERPRETER_PROVENANCE` is unset.
2. The implementer claim of broader safe regressions (861 + 186 subtests) was not re-run in the independent final review; only the bounded custody suite and exact_bytes_witness_v0 were executed per review scope.
3. Pre-existing `__pycache__` / `.pytest_cache` directories under unrelated packages were present in the worktree; none were created under `ed25519_custody_v0/` by the independent final review.

## Explicit boundaries

HUMAN FINAL FOR THIS SCOPE ≠ REAL KEY GENERATION AUTHORIZATION
HUMAN FINAL ≠ ADMISSION
HUMAN FINAL ≠ IDENTITY / ROLE / AUTHORIZATION / TRUST
TEST SUCCESS ≠ PRE-REAL ENVIRONMENT ESTABLISHED
VALID CUSTODY HELPER ≠ TRUSTED SIGNER

## Decisions recorded

- HUMAN_FINAL: HUMAN_REVIEW_ACCEPTED
- PRE-REAL environment: NOT established
- Real key generation: NOT authorized; NOT performed
- Real passphrase, seed, or recovery secret: NOT created
- Admission: NOT performed
- Signing API: absent
- Historical Admission semantics: preserved
- CLOSED scopes: unchanged
- Push: NO

## Scope closure and next prerequisite

This Human Final closes the bounded scope Dedicated Local Software Ed25519 Custody Helper and Runbook v0 only.

Next proposed prerequisite scope (not authorized by this record):
PRE-REAL Ed25519 Custody Execution Environment v0

Real key generation remains separately unauthorized until PRE-REAL prerequisites are satisfied and a later Human authorization is recorded.
