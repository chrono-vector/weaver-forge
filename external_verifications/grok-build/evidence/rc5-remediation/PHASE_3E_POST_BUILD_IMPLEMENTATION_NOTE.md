# Phase 3E — Host POST_BUILD Integrity Implementation Note

## Base

| Item | Value |
|------|-------|
| Branch | `main` |
| Base commit | `7c89619217122c55ad21064f1cb3ccad1b07942a` |
| Owner decision | **Option A** — do not modify `CLAIM_REGISTER.md` or broader public-status/public-claim documents; defer stale public-status wording to a separate documentation/status pass |
| Selected options | **O12** (Phase 3E prerequisites only; validator-gated final success remains Phase 3F) + **O2** (truthful POST_BUILD status + `HOST_POST_BUILD_INTEGRITY_STATUS` / `HOST_OUTCOME_INGESTION` sync) + **O3** (exact POST_BUILD field-set alignment) + **O14** (complete truthful host-owned POST_BUILD on pre-/post-Docker host failure paths) with **O11** atomic commit boundary |
| Cursor options analysis | Implemented exactly the Pi-adjudicated Option A staged set; no redesign; no Phase 3F/3G |
| Pi independent adjudication | Followed; Option A approved by owner |
| RC4 disposition | **NOT READY** (unchanged) |
| RC5 tag | **absent** |
| Independent Witness reproduction | **NOT PERFORMED** |
| Independent Witness PASS | **not claimed** |
| C-014 | **NOT_STARTED** |

## Exact authorized files changed

1. `external_verifications/grok-build/witness-package/scripts/run_witness_narrow_build.sh`
2. `external_verifications/grok-build/witness-package/templates/POST_BUILD_INTEGRITY.txt`
3. `external_verifications/grok-build/witness-package/scripts/validate_witness_evidence.py` (schema-only)
4. `external_verifications/grok-build/witness-package/scripts/tests/test_validate_witness_evidence.py`
5. `external_verifications/grok-build/witness-package/scripts/tests/fixtures_lib.py`
6. `external_verifications/grok-build/witness-package/scripts/tests/fixtures/**/POST_BUILD_INTEGRITY.txt` (and dependent manifests)
7. `external_verifications/grok-build/witness-package/scripts/tests/test_phase3e_post_build_integrity.py` (new)
8. `external_verifications/grok-build/witness-package/scripts/tests/test_phase3d_host_outcome_ingestion.py` (test_35 supersession only)
9. `external_verifications/grok-build/evidence/rc4-static-blind-audit/INTEGRATED_REMEDIATION_LIST.md`
10. `external_verifications/grok-build/witness-package/WITNESS_REQUIREMENTS.md`
11. `external_verifications/grok-build/witness-package/WITNESS_RUNBOOK.md`
12. `external_verifications/grok-build/evidence/rc5-remediation/PHASE_3E_POST_BUILD_IMPLEMENTATION_NOTE.md` (this file)

**Not modified:** `CLAIM_REGISTER.md`, `AUTHORITATIVE_OUTCOME_CONTRACT.json`, Phase 3B/3C/3D historical notes, `container_narrow_build.sh`, container-owned outcome writers, validator `determine_outcome`, host validator invocation, host exit-zero validator gating, rc1–rc4 tags/archives.

## Exact final POST_BUILD field set (ordered)

1. `evidence_schema_version`
2. `status`
3. `outcome`
4. `source_head_before`
5. `source_head_after`
6. `source_head_unchanged`
7. `source_clean_before`
8. `source_clean_after`
9. `cargo_lock_sha256_before`
10. `cargo_lock_sha256_after`
11. `cargo_lock_unchanged`
12. `cargo_lock_post_matches_expected`
13. `source_or_lock_changed`
14. `artifact_path`
15. `artifact_exists`
16. `docker_exit_code`
17. `failure_stage`
18. `evidence_inventory_complete`
19. `full_integrity_gate_all_four_yes`
20. `full_integrity_gate_note`
21. `post_build_integrity_ok`

Identical across: centralized host writer, template, validator `FILE_REQUIRED_FIELDS` / exact-set check, `fixtures_lib.py`, all POST_BUILD fixtures, and Phase 3E test expectations.

## Ownership and lifecycle

- `POST_BUILD_INTEGRITY.txt` is **host-owned**.
- `post_build_integrity_status` / `HOST_POST_BUILD_INTEGRITY_STATUS` are **host-owned**.
- Container remains a **non-writer** of POST_BUILD.
- Validator is a **schema consumer only** during Phase 3E (exact field set, status vocabulary, structural consistency). Does **not** enforce RC4B-017 PASS conditions; does **not** change `determine_outcome`.
- `BUILD_EXIT_CODE.txt` remains container-owned after Docker starts; Phase 3E never creates, replaces, normalizes, infers, or overwrites it.
- Final status vocabulary: `OK` | `FAILED`. Transitional only: `NOT_REACHED`. Prohibited as final: `NOT_APPLICABLE`.
- `status=OK` iff `post_build_integrity_ok=yes`; otherwise `status=FAILED`. Fail-closed.
- `preliminary_success_eligible` remains `NO` throughout Phase 3E.

## Ordinary path behavior

1. Compute existing technical POST_BUILD integrity conditions.
2. Call `write_host_post_build_integrity_record` (centralized).
3. Write `status=OK` only when `post_build_integrity_ok=yes`; otherwise `FAILED`.
4. Set `HOST_POST_BUILD_INTEGRITY_STATUS` from the same policy.
5. Refresh `HOST_OUTCOME_INGESTION.txt` via `sync_host_outcome_ingestion_post_build_status` so `post_build_integrity_status` matches.
6. Do **not** invoke the validator; host exit is **not** validator-gated (Phase 3F).

## Pre-Docker failure behavior

`finalize_pre_docker_infrastructure_failure` produces one complete FAILED POST_BUILD through the centralized writer (never `NOT_APPLICABLE` final). Measurements not taken use `NOT_REACHED` / fail-closed yes|no values. Does not imply Docker/Cargo/validator/product execution.

## Post-Docker failure behavior

`finalize_post_docker_host_failure` (and unexpected-failure routing into it) replaces host-owned POST_BUILD with one complete truthful FAILED record, synchronizes `HOST_POST_BUILD_INTEGRITY_STATUS` and `HOST_OUTCOME_INGESTION`, and preserves `BUILD_EXIT_CODE.txt` byte-for-byte (missing stays missing; empty/malformed/valid unchanged). Phase 3D no-fabrication / no-overwrite guarantees for container results remain intact.

## Phase 3D test_35 supersession

- Pre-3E rule against changing POST_BUILD during host finalization was valid for Phase 3D.
- Phase 3E permits truthful rewriting of host-owned POST_BUILD during host finalization.
- `test_35_no_post_build_semantic_rewrite` superseded by
  `test_35_phase3e_allows_truthful_post_build_rewrite_preserves_build_exit`.
- Unrelated Phase 3D protections (BUILD_EXIT_CODE preservation, no fabrication, ingestion ownership, fail-closed) remain.

## Validator schema-only boundary

Permitted and done:

- Exact required POST_BUILD field set
- Legal status vocabulary (`OK|FAILED|NOT_REACHED`; reject final `NOT_APPLICABLE`)
- Exact field-set equality (reject missing/unknown/extra)
- `status` / `post_build_integrity_ok` consistency
- `NOT_REACHED` cannot qualify as finalized success

Prohibited and **not** done: RC4B-017 PASS enforcement, `determine_outcome` changes, host validator invocation, validator-gated exit 0, claiming validator-gated success.

## Phase 3F exclusions

Validator-gated host success, submission lifecycle closure, and overall validation-outcome ownership changes remain Phase 3F. Not begun.

## Exact new Phase 3E test count

**22 discovered / 22 run / 22 passed / 0 failed / 0 errors / 0 skipped**

Command:

```text
cd external_verifications/grok-build/witness-package/scripts/tests
python -m unittest test_phase3e_post_build_integrity -v
```

## Regression results (recorded after implementation)

| Suite | Result |
|-------|--------|
| Phase 3E `test_phase3e_post_build_integrity` | **22 discovered / 22 run / 22 passed / 0 failed / 0 errors / 0 skipped** |
| Phase 3D `test_phase3d_host_outcome_ingestion` | **50 discovered / 50 run / 50 passed / 0 failed / 0 errors / 0 skipped** (test_35 superseded in place; count unchanged) |
| Phase 3B `test_phase3b_outcome_contract` | **25/25 PASS** |
| Phase 2B `test_phase2b_mount_isolation` | **22/22 PASS** |
| Phase 2A `test_phase2a_host_preflight` | **18/18 PASS** |
| Validator `test_validate_witness_evidence` | **65 discovered / 65 run / 65 passed / 0 failed / 0 errors / 0 skipped** |
| Phase 3C | **Not run** — container script unmodified; Pi test_35 supersession verified via Phase 3D suite |

## Correction history

1. Initial Phase 3E `test_21` used `assertNotRegex(..., flags=)` which raised `TypeError` on this Python; corrected to `re.search` + `assertIsNone`.
2. Validator ContractTests previously failed to extract container heredoc schema keys (`echo "`-only regex) and still expected pre-Phase-3D `parse_container_outcome`; fixed in authorized `test_validate_witness_evidence.py` (heredoc bare-key extraction + Phase 3D symbol alignment). These were latent on `main` before Phase 3E.
3. Fixture regenerate on Windows required pure-LF byte rewrite so `EVIDENCE_MANIFEST.sha256` matches working-tree POST_BUILD content under `core.autocrlf`.

## Blocker-status treatment

| Blocker | Treatment |
|---------|-----------|
| RC4B-015 | **IMPLEMENTED_ON_MAIN_PENDING_INTEGRATION_AND_REAUDIT** |
| RC4B-016 | POST_BUILD field-set **subset** implemented on main pending integration/reaudit; **not** fully remediated; **not CLOSED** |
| RC4B-012, RC4B-029, RC4B-019 | remain **OPEN** with Phase 3E progress recorded |
| RC4B-013, RC4B-017 | remain **OPEN** |
| RC4B-022 | remains **CONTRACT_DEFINED_ON_MAIN_IMPLEMENTATION_PENDING** |
| Any blocker CLOSED | **none** |

## Remaining gaps

- Validator-gated host success (Phase 3F)
- Broader exact field-set equality across all non-POST_BUILD writers (remainder of RC4B-016)
- Outcome-inference removal / full cross-file tuple enforcement (RC4B-013/017/022)
- Fixed candidate + repeat static audit
- Independent Witness reproduction / C-014

## Non-claims

- RC4 is **not** READY
- No rc5 tag
- No Independent Witness reproduction or PASS
- C-014 remains NOT_STARTED
- No validator-gated host success
- No real Docker, Cargo, compiler, bootstrap, ldd, network, validator workflow, or product execution in this phase’s tests
- Broad public-status documents deferred (Owner Option A)
