# INR-001 Implementation Matrix (r2 candidate)

Status: IMPLEMENTER RECORD — not independently reviewed. Supersedes the C2 matrix
(`INR_001_IMPLEMENTATION_MATRIX.md`, withdrawn `18 / 18 PASS` claim); see
`INR_001_CANDIDATE_SUPERSESSION.md`.

Root invariant: executor-controlled data is not a trusted fact. A PASS-relevant fact
comes only from trusted measurement, trusted capture (a real child launched by
`trusted_capture._launch`), frozen trusted configuration, or verifier-owned
derivation (`validate_inr_v0._verify_live`). JSON exports can only be re-checked
(`recheck_export`) and never yield PASS.

Status vocabulary: PASS = enforced by the r2 local tooling and exercised by a real
regression test; PARTIAL = enforced locally with a stated residual limitation;
UNCONFIRMED = external assurance with no verifier-owned evidence source in v0 (the
verifier always reports it UNCONFIRMED, so the overall INR result cannot be PASS);
FAIL = not enforced.

| finding | invariant | r2 enforcement | regression test(s) | status |
|---|---|---|---|---|
| INR-MF-001 | distribution bytes = executed bytes | Git blob bytes at TARGET_SHA checked against `target_file_digests`; staged source re-measured by the verifier; child hashes and compiles the same bytes | `test_real_child_execution_binds_evidence` | PASS |
| INR-MF-002 | measured source = executed module | child `exec(compile(raw))` of the hashed bytes; executed source path bound to the verifier-derived staging path; not preloaded | `test_real_child_execution_binds_evidence`, `test_argv_mismatch_rejected` | PASS |
| INR-MF-003 | Git runtime bound | pinned absolute Git, `shutil.which` must equal it, no `GIT_*` env, include/extensions/alias/worktree/fsmonitor/alternateRefsCommand config rejected (`-z` parsing), replace refs/alternates/grafts rejected; child cwd = staging dir, child `PATH` = pinned Git dir only, `GIT_NO_REPLACE_OBJECTS=1`; child must resolve the measured Git and no CreateProcess shadowing `git.exe` may exist | `test_real_child_execution_binds_evidence` | PARTIAL (Windows `cmd\git.exe` is a launcher shim; only the shim is hashed) |
| INR-MF-004 | no TOCTOU mutation | staged files read-only, before/after measurement, verifier re-measurement of source/inputs/probe | `test_real_child_execution_binds_evidence` | PARTIAL (same-user writers are not excluded; see MF-012) |
| INR-MF-005 | complete frozen inventory | exactly one minted evidence object per profile case, in order; count/order/case/command checked by the verifier | `test_no_child_process_rejected`, `test_no_child_evidence_is_not_pass` | PASS |
| INR-MF-006 | self-declared non-origin insufficient | `_assess_non_origin()` takes no input; any boolean/string claim is ignored | `test_fake_is_non_origin_is_ignored` | UNCONFIRMED (self-claims ignored; no objective evidence source in v0) |
| INR-MF-007 | evidence not curated after run | streams come from `Popen.communicate` inside the launch path; export digest recorded in the ledger; edited exports FAIL recheck | `test_fake_all_writer_isolation_is_ignored`, `test_valid_new_schema_event_passes_schema` | PASS |
| INR-MF-008 | import hook/preload/pyc blocked | child `-I -S -B`, `PYTHONDONTWRITEBYTECODE=1`, `site`/`sitecustomize`/`usercustomize` must be absent, target compiled from bytes | `test_argv_mismatch_rejected` (dropping `-S` fails) | PARTIAL (stdlib `__pycache__` may still be read) |
| INR-MF-009 | writable parent/symlink/dependency protected | not implemented as objective evidence; folded into all-writer isolation | — | UNCONFIRMED |
| INR-MF-010 | executor cannot weaken profile | profile digest pinned in code; profile schema requires `mandatory_execution: true`, exact refusals | `test_profile_origin_conform_and_digest_is_pinned` | PASS |
| INR-MF-011 | same-host VM/container non-qualifying | no verifier-owned runner evidence | `test_fake_is_non_origin_is_ignored` | UNCONFIRMED |
| INR-MF-012 | all-writer isolation | `_assess_all_writer_isolation()` takes no input | `test_fake_all_writer_isolation_is_ignored` | UNCONFIRMED |
| INR-MF-013 | trusted profile binding | pinned digest + re-freeze record | `test_profile_origin_conform_and_digest_is_pinned` | PASS |
| INR-MF-014 | no shared mutable state | `_assess_shared_state_absence()` takes no input | `test_fake_all_writer_isolation_is_ignored` | UNCONFIRMED |
| INR-MF-015 | origin reference pre-frozen | origin set digest pinned in code before any event; binding checked | `test_profile_origin_conform_and_digest_is_pinned` | PARTIAL (no origin-output comparison is performed by local runs) |
| INR-MF-016 | no cross-event replay | persistent hash-chained ledger rejects repeated event IDs/challenges; per-launch nonce and challenge echoed by the child | `test_challenge_reuse_event_id_rejected`, `test_challenge_reuse_same_challenge_rejected`, `test_historical_output_replay_rejected`, `test_reserve_complete_and_replay` | PASS |
| INR-MF-017 | trusted origin set binding | origin digest pinned in trusted config; no executor input | `test_profile_origin_conform_and_digest_is_pinned` | PASS |
| INR-MF-018 | capture launches target | only `_launch` mints evidence, from a real `subprocess.Popen` it created; fake Popen, forged or replayed records are rejected | `test_no_child_process_rejected`, `test_forged_capture_record_rejected`, `test_evidence_is_single_use_frozen_and_tamper_evident` | PASS |

Totals over INR-MF-001..018: PASS 9, PARTIAL 4, UNCONFIRMED 5, FAIL 0.
No `18 / 18` closure is claimed.

## Review findings on C2 / uncommitted work

| finding | r2 remediation | regression test(s) | status |
|---|---|---|---|
| M1 self-attested verifier (99418b4) | superseded; synthetic-PASS test removed; disk JSON can never PASS | `test_stale_99418b4_event_fails`, `test_synthetic_snapshot_injection_rejected` | PASS |
| M2 mintable `_SESSIONS` snapshot | registry and token API removed; evidence minted only inside `_launch`, frozen, fingerprinted, single use; no module-global writable registry | `test_no_module_global_writable_registry`, `test_evidence_cannot_be_constructed_directly`, `test_synthetic_snapshot_injection_rejected` | PASS |
| M3 wrong-reason negative acceptance | exact `expected_errors` per case; HUMAN_FINAL input keeps the closed key set and hits its dedicated rules | `test_wrong_reason_rejection_is_not_an_expected_refusal`, `test_old_top_level_human_final_input_is_wrong_reason`, `test_human_final_case_hits_intended_refusal`, `test_every_negative_control_hits_its_exact_refusal` | PASS |

## Observed local run (this machine)

`derived_result: BLOCKED` (supervisor/child Python 3.14.3 is outside the frozen 3.11.x
policy; the acquisition repository HEAD is not TARGET_SHA), `local_controls_result:
BLOCKED`. Components `trusted_configuration`, `challenge_ledger`, `git_runtime`,
`child_execution_binding`, `argv_binding`, `module_identity`, `refusal_semantics`: PASS.
`non_origin`, `shared_state_absence`, `all_writer_isolation`: UNCONFIRMED.

INR_PASS_CLAIMED: NO.
