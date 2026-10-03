# Recovery Execution Receipt v0 — Human Final

Date:
2026-10-03

Status:
HUMAN_REVIEW_ACCEPTED

Fixed implementation SHA:
6c02eea615f0eef86d3204d09d49ed3dbf1ae056

Parent:
113fa345663f995b84e7ee302b794b55e484794b

Repository:
C:\dev\Weaver\weaver-forge-r4

Scope:
Recovery Execution Receipt v0

Final technical review:
ACCEPT

Tests:
- Recovery Execution Receipt: 95 passed
- Recovery Preflight v0 regression: 43 passed
- Tested-Envelope v0 regression: 37 passed
- Independent Verification Preflight v0 regression: 49 passed
- Conducting Receipt v0 regression: 72 passed
- pytest review confirmation: 296 passed, 43 subtests passed

Material findings:
NONE

Accepted boundaries:
- R3 unchanged / CLOSED
- R4 unchanged / CLOSED
- WVMA-V1 unchanged / CLOSED
- Tested-Envelope Receipt v0 unchanged / CLOSED
- Recovery Preflight v0 unchanged / CLOSED
- Independent Verification Preflight v0 unchanged / CLOSED
- Conducting Receipt v0 unchanged / CLOSED
- VECTOR unchanged
- EIG unchanged
- accepted baseline unchanged
- no public push
- no private push

## Core semantics

Recovery Execution Receipt v0 preserves:

- authority = false
- recovered = false always in this v0
- RECOVERED_BOUNDED is a local bounded classification only
- Restore != Recovered Until Verified
- No Observability != Verified Success
- Rollback != Recovery
- Exit code / action success != recovered
- Human Review != Human Final
- Independent Verification citation != Independent Evidence admission

Recovery sequence remains separated:

STOP
-> ISOLATE
-> PRE-STATE / SNAPSHOT
-> IMMUTABLE RESTORE TARGET
-> RESTORE / ROLLBACK ACTION
-> POST-RESTORE VERIFY
-> optional HUMAN REVIEW

## R1 remediation semantics

Recovery Execution Receipt v0 preserves:

- CONTENT_DIGEST_MATCH / CONFIG_DIGEST_MATCH / DATA_INTEGRITY expected values are bound to restore-target material
- self-consistent unrelated bytes cannot satisfy target verification
- inherited OPEN risk metadata (statement / severity / introduced order) is immutable until RESOLVED
- custody-gap remains CRITICAL until qualifying evidence resolves it
- any critical OBSERVED_FAIL blocks bounded recovery
- any critical NOT_OBSERVED / disallowed N/A blocks bounded recovery
- required-kind FAIL blocks even if caller sets critical=false
- SIGNATURE_CHECK aggregates all rows; FAIL wins over PASS
- noncritical signature PASS alone cannot close custody gap
- failed attempts/checks remain append-only in history
- Human Review cannot alter technical classification

## Nonmaterial limitations

The following limitations are NONMATERIAL. They do not reopen Recovery Execution Receipt v0. They are reference records, not remediation tasks.

1. Custody approval pin origin:
   `restore_target.approval_ref` is caller-supplied descriptive/pinned input.
   It is not independently rooted by this v0.
   A future hardening scope may require approval_ref to be distinct from target body digest
   and/or bind it to an external trust root.

2. Generic risk resolution_ref:
   Non-custody risks may reference another known in-session digest as resolution_ref.
   This cannot resolve custody-gap, change immutable risk metadata, erase failed checks,
   or bypass required verification.

3. CONFIG_DIGEST_MATCH and CONTENT_DIGEST_MATCH may both bind to the same target body
   for CONFIG scope. v0 does not require separately modeled config/artifact payloads.

4. Free-text check target labels are not independently bound to restore-target identity.
   Digest/body binding controls recovery semantics.

5. Caller-created custom "custody-gap" labels do not gain authority.
   Without qualifying signature/custody evidence the built-in critical custody gap remains blocking.

6. Some guards remain under-tested by direct mutation despite correct live behavior, including:
   - approval pin / expected signature relation
   - qualifying signature critical requirement
   - runtime any-FAIL aggregation
   - critical N/A handling
   - noncritical FAIL limitation surfacing

7. Runtime/health/custody observations are receipt evidence, not proof of production-wide safety.

## Explicit non-claims

Human Final acceptance does NOT mean:

- restore/rollback execution engine exists
- hosts/services are mutated by this package
- production recovery is globally proven
- key custody / ACL / signing is independently certified
- independent evidence admission is configured
- independent_evidence_count > 0
- Human Review equals Human Final
- R4/VECTOR/EIG authority changed
- deployment is safe
- production is safe
- canonical/published/deployed status is established

## Human Final statement

Recovery Execution Receipt v0 は、上記のnonmaterial limitationを含む決められた範囲で完成・確認済みとして正式に受け入れます。

HUMAN_REVIEW_ACCEPTED

This Human Final is authoritative for this scope.

## Record

- This document is a documentation-only record.
- No implementation bytes, tests, or accepted historical artifacts were changed by this record.
- Do not reopen or modify any accepted scope.
