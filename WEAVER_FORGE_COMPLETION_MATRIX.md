# WEAVER_FORGE_COMPLETION_MATRIX (post Phase 4–6.1 + Pi final-review B1)

**Assessment update (UTC):** 2026-09-15T03:30:00Z  
**Prior Phase 5 assessment:** recorded `WEAVER_FORGE_COMPLETE` pending independent review  
**Codex independent review (Phase 6):** `WEAVER_FORGE_NOT_COMPLETE` (material blockers B1/B2)  
**Pi independent review (Phase 6 re-review):** discovered remaining **FINAL_DECISION semantic verification gap** (material)  
**Pi independent final review (candidate `ad82617817971821c59a2e8ab9895182e8173565`):** `WEAVER_FORGE_NOT_COMPLETE` — **material blocker B1** (freeze one-shot bypass after frozen package directory deletion)  
**Completion verdict status:** **REOPENED** — Pi final-review B1 remediated; do **not** declare `WEAVER_FORGE_COMPLETE`  
**Product package:** `weaver-forge/audit_lifecycle/`  
**Phase 5 clean freeze (historical, unchanged):** `phase5_runs/WFA-20260914T093800Z-1E452FA4`  
**Phase 5 freeze SHA256SUMS digest (unchanged):** `91a36ee4dc74eccac82457637096e65c0fad3a9b90e663b5b3a2fc12169bc877`  
**Phase 6 fresh freeze (unchanged):** `phase6_runs/WFA-20260914T100138Z-4F362FB9`  
**Phase 6 freeze SHA256SUMS digest (unchanged):** `88e46cb8465e47000d3555375de8e609f0efdd8c798ae3c6a9fdf480b115dd75`  
**Phase 6.1 fresh freeze (unchanged):** `phase61_runs/WFA-20260914T101819Z-8C1418EB`  
**Phase 6.1 freeze SHA256SUMS digest (unchanged):** `f7f46fc72cecf5cb824ce8b7003532263d82f787be67582c3427705637b95d04`  
**Pi B1 remediation fresh freeze:** `pi_b1_runs/WFA-20260915T032852Z-C88F783F`  
**Pi B1 remediation freeze SHA256SUMS digest (pre-attack reproduction):** `16b1fe18522b14cccdb75f04b7d8a4219770db2be3a5a01b1a3574fbfc260779`

Status = productized capability after Phase 4–6.1 + **Pi final-review B1 remediation** (FREEZE_STATUS one-shot independent of freeze directory presence).

| # | Stage | Status | Citation |
|---|-------|--------|----------|
| 1 | Audit request intake | IMPLEMENTED+TESTED+E2E_VERIFIED+THIRD_PARTY_REPRODUCIBLE | `audit_lifecycle/request.py`, `cli.py run --request`, Phase 5/6/6.1/Pi-B1 operator requests |
| 2 | Audit ID/run creation | IMPLEMENTED+TESTED+E2E_VERIFIED+THIRD_PARTY_REPRODUCIBLE | `orchestrator.create_run`, runs under `phase5_runs/` / `phase6_runs/` / `phase61_runs/` / `pi_b1_runs/` |
| 3 | Claim definition | IMPLEMENTED+TESTED+E2E_VERIFIED+THIRD_PARTY_REPRODUCIBLE | `claim_scope.compile_claim_and_scope` → `CLAIM.json` |
| 4 | Scope definition | IMPLEMENTED+TESTED+E2E_VERIFIED+THIRD_PARTY_REPRODUCIBLE | `SCOPE.json` auto-compiled |
| 5 | Allowed write boundary | IMPLEMENTED+TESTED+E2E_VERIFIED+THIRD_PARTY_REPRODUCIBLE | `boundary.BoundaryManager` |
| 6 | Protected boundary | IMPLEMENTED+TESTED+E2E_VERIFIED+THIRD_PARTY_REPRODUCIBLE | protected_paths enforced; CAW-003/004 freezes unmutated |
| 7 | Baseline snapshot | IMPLEMENTED+TESTED+E2E_VERIFIED+THIRD_PARTY_REPRODUCIBLE | `BASELINE.json` |
| 8 | Prior frozen evidence integrity | IMPLEMENTED+TESTED+E2E_VERIFIED+THIRD_PARTY_REPRODUCIBLE | `prior_freeze_sums` in baseline; Phase 5/6/6.1/Pi-B1 checked CAW-004 |
| 9 | Source/input pinning | IMPLEMENTED+TESTED+E2E_VERIFIED+THIRD_PARTY_REPRODUCIBLE | `pin.pin_target` → `pinned_target/` + `PROVENANCE.json` |
| 10 | Execution | IMPLEMENTED+TESTED+E2E_VERIFIED+THIRD_PARTY_REPRODUCIBLE | `adapters/hash_claim.py` via orchestrator |
| 11 | Evidence collection | IMPLEMENTED+TESTED+E2E_VERIFIED+THIRD_PARTY_REPRODUCIBLE | `evidence/raw`, `evidence/logs` |
| 12 | Provenance capture | IMPLEMENTED+TESTED+E2E_VERIFIED+THIRD_PARTY_REPRODUCIBLE | `PROVENANCE.json` |
| 13 | Negative controls | IMPLEMENTED+TESTED+E2E_VERIFIED+THIRD_PARTY_REPRODUCIBLE | NC1 in hash_claim + tests |
| 14 | Tamper controls | IMPLEMENTED+TESTED+E2E_VERIFIED+THIRD_PARTY_REPRODUCIBLE | T1 in adapter; evidence-tamper verify FAIL |
| 15 | Reproduction | IMPLEMENTED+TESTED+E2E_VERIFIED+THIRD_PARTY_REPRODUCIBLE | R1 rehash; freeze `REPRODUCTION_INSTRUCTIONS.md` |
| 16 | Independent verification | IMPLEMENTED+TESTED+E2E_VERIFIED | `independent_verification.py` lifecycle hook; default `NOT_CLAIMED` / never IW acceptance |
| 17 | Conservative decision | IMPLEMENTED+TESTED+E2E_VERIFIED+THIRD_PARTY_REPRODUCIBLE | `decision.py`; refuses FULL promotion |
| 18 | Human review gate | IMPLEMENTED+TESTED+E2E_VERIFIED+THIRD_PARTY_REPRODUCIBLE | `review_gate.py`; freeze blocked without `HUMAN_REVIEW.json` when required |
| 19 | Manifest creation | IMPLEMENTED+TESTED+E2E_VERIFIED+THIRD_PARTY_REPRODUCIBLE | `EXECUTION_MANIFEST.json`, freeze `MANIFEST.json` |
| 20 | SHA-256 evidence binding | IMPLEMENTED+TESTED+E2E_VERIFIED+THIRD_PARTY_REPRODUCIBLE | `SHA256SUMS.txt` + verify |
| 21 | Freeze (one-shot) | IMPLEMENTED+TESTED+E2E_VERIFIED+THIRD_PARTY_REPRODUCIBLE | `assert_one_shot_freeze_allowed` — completed `FREEZE_STATUS.json` blocks re-freeze even if `*_FROZEN/` deleted (Pi final B1) |
| 22 | Final evidence index | IMPLEMENTED+TESTED+E2E_VERIFIED+THIRD_PARTY_REPRODUCIBLE | `FINAL_EVIDENCE_INDEX.json` |
| 23 | Re-run/reproduction instructions | IMPLEMENTED+TESTED+E2E_VERIFIED+THIRD_PARTY_REPRODUCIBLE | freeze `REPRODUCTION_INSTRUCTIONS.md` |
| 24 | Failure-path preservation | IMPLEMENTED+TESTED+E2E_VERIFIED+THIRD_PARTY_REPRODUCIBLE | FAIL/INCONCLUSIVE runs retained; `FAILURE.json` on exceptions / freeze integrity |
| 25 | Boundary-violation fail-closed | IMPLEMENTED+TESTED+E2E_VERIFIED+THIRD_PARTY_REPRODUCIBLE | BV1 + `BoundaryViolation`; no probe files in protected freezes |
| 26 | Semantic verify (hash_claim) | IMPLEMENTED+TESTED+E2E_VERIFIED+THIRD_PARTY_REPRODUCIBLE | `semantic_verification.py`; stored DECISION **and** frozen FINAL_DECISION vs recomputed (Phase 6 B2 + Phase 6.1) |

**Unresolved material MISSING after Pi B1 remediation:** none identified for freeze-directory-deletion one-shot bypass; awaiting **independent Pi re-review** and **Codex final review**. Do **not** mark `WEAVER_FORGE_COMPLETE`.

**Scoped non-claims (not gaps against the fixed completion definition):**
- CAW dual-endpoint crypto is prior practice evidence (`CAW-003`/`CAW-004`), not required as the Phase 5/6/6.1/Pi-B1 fresh target.
- New claim families need a registered adapter + semantic verifier; unsupported adapters fail semantic verify conservatively.
- Independent Witness acceptance is never implied by lifecycle PASS.

## Phase 5 results (historical summary — unchanged evidence)

| Path | Result |
|------|--------|
| Normal successful audit → FINAL DECISION + FROZEN package | PASS (`WFA-20260914T093800Z-1E452FA4`) |
| Failing audit | FAIL preserved, no false PASS |
| Evidence tamper | `verify` → sha256sums_ok=false |
| Protected-boundary write | fail-closed PASS |
| Incomplete evidence | INCONCLUSIVE, no false PASS |
| Unit/integration suite (then) | 8 OK |

## Phase 6 remediation (Codex B1/B2)

| Finding | Remediation | Status |
|---------|-------------|--------|
| B1 Freeze overwrite / regeneration | One-shot freeze; `FREEZE_ALREADY_EXISTS` before any mutation | PARTIAL — dir-existence only; Pi final review proved bypass |
| B2 verify trusts stored decision | Independent hash_claim semantic recompute; MATCH/MISMATCH vs DECISION.json | PARTIAL — DECISION covered; FINAL_DECISION gap remained |

| Path | Result |
|------|--------|
| Fresh successful audit + freeze | PASS (`WFA-20260914T100138Z-4F362FB9`) — **unchanged** |
| Second freeze attempt | REJECTED `FREEZE_ALREADY_EXISTS`; freeze byte-identical |
| Semantic verify clean PASS | stored PASS == recomputed PASS (DECISION only at Phase 6) |
| False PASS edit + rebound hashes | hash OK possible; semantic FAIL |
| Incomplete evidence | INCONCLUSIVE |
| Boundary / tamper / prior freezes | fail-closed / detected / CAW-003+004+Phase5 unchanged |
| Unit/integration suite (then) | **12 OK** |

## Phase 6.1 targeted remediation (Pi FINAL_DECISION gap)

| Finding | Remediation | Status |
|---------|-------------|--------|
| FINAL_DECISION.json not compared to independently recomputed decision | Material semantic fields of `FINAL_DECISION["decision"]` vs recomputed; mismatch → `semantic_ok=false` / `verify_ok=false` | ENFORCED + tested (T13) + E2E |

**Discovery note:** Pi reproduced false `CRYPTO_SUPPORTED_E2E_FULL` / `promoted_to_full=true` on a disposable copy with rebound SHA manifests and still observed `verify_ok=true`. Codex Phase 6 review did not detect this case.

| Path | Result |
|------|--------|
| Fresh successful audit + freeze | PASS (`WFA-20260914T101819Z-8C1418EB`) |
| Legitimate frozen FINAL_DECISION | still verifies (`final_decision_match=true`) |
| FINAL_DECISION false promotion + rebound hashes | hash OK possible; **semantic FAIL** (T13) |
| DECISION false PASS + rebound | still semantic FAIL |
| Second freeze / tamper / incomplete / boundary | unchanged fail-closed behavior |
| Prior freezes | CAW-003, CAW-004, Phase 5, Phase 6 **unchanged** |
| Unit/integration suite (then) | `python -m unittest audit_lifecycle.tests.test_lifecycle -v` → **13 OK** |

## Pi final-review B1 remediation (freeze one-shot vs directory deletion)

| Finding | Remediation | Status |
|---------|-------------|--------|
| Freeze one-shot bypassed after `freeze/<id>_FROZEN/` deleted while `FREEZE_STATUS.json` remains | `assert_one_shot_freeze_allowed`: completed `FREEZE_STATUS` rejects re-freeze **before** SHA rebind; missing package → `FREEZE_INTEGRITY_FAILURE` / `FAILURE.json` | ENFORCED + tested (Pi B1 regression) + E2E |

**Root cause:** `freeze_run` / `create_freeze_package` gated only on freeze directory existence, not on prior completed `FREEZE_STATUS.json`.

| Path | Result |
|------|--------|
| Fresh successful audit + freeze | PASS (`WFA-20260915T032852Z-C88F783F`); verify_ok=true |
| Delete only frozen package dir; leave FREEZE_STATUS; re-freeze | **REJECTED** `FREEZE_INTEGRITY_FAILURE` / `FREEZE_PACKAGE_MISSING`; no replacement package; FREEZE_STATUS unchanged |
| Existing completed freeze (dir present) | still `FREEZE_ALREADY_EXISTS` |
| Legitimate first freeze | still succeeds |
| Unit/integration suite | `python -m unittest audit_lifecycle.tests.test_lifecycle -v` → **16 OK** |

**Pending:** independent Pi re-review of this remediation, then Codex final review. **Do not declare `WEAVER_FORGE_COMPLETE`.**

See also: `phase61_runs/PHASE61_COMPLETION_RETEST.json`, `phase6_runs/PHASE6_COMPLETION_RETEST.json`, `phase5_runs/PHASE5_COMPLETION_REPORT.json`.
