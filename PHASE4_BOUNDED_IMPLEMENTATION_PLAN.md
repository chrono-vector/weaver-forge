# Phase 4 — Bounded Implementation Plan

Derived only from `WEAVER_FORGE_COMPLETION_MATRIX.md` MISSING items.

## Deliverable package
`weaver-forge/audit_lifecycle/` — productized audit lifecycle for Weaver Forge.

## Components (proven gaps only)

| Module | Stages covered |
|--------|----------------|
| `request.py` / CLI intake | 1–2 |
| `claim_scope.py` | 3–4 |
| `boundary.py` | 5–6, 25 |
| `baseline.py` | 7–8 |
| `pin.py` | 9 |
| `evidence.py` | 11–12, 20 |
| `adapters/base.py` + `adapters/hash_claim.py` | 10, 13–15 |
| `decision.py` | 17 |
| `review_gate.py` | 18 |
| `freeze.py` | 19, 21–23 |
| `orchestrator.py` | wires all; 24 failure preservation |
| `cli.py` | third-party entry: target + claim + policy |

## Non-goals
- Do not rewrite CAW-001..004
- Do not promote CAW crypto to FULL
- Do not claim Independent Witness acceptance
- Do not create unused named components beyond the table

## Test plan
Unit + integration tests under `audit_lifecycle/tests/`:
- happy path → FROZEN package
- failing audit → FAIL preserved, no false PASS
- evidence tamper → verification FAIL
- protected-boundary write → fail-closed
- incomplete evidence → no PASS
- human review required → freeze blocked until gate file present
