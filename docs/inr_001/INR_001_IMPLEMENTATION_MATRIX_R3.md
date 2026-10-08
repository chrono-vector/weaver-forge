# INR-001 Implementation Matrix (r3 candidate)

Status: IMPLEMENTER RECORD — not independently reviewed. Supersedes
`INR_001_IMPLEMENTATION_MATRIX_R2.md` (r2 / commit 1ce1651, kept with a superseded
banner); see `INR_001_CANDIDATE_SUPERSESSION.md`.

Key requirement: NO LOCAL FALSE PASS PATH. External assurance stays UNCONFIRMED, so
the overall INR result cannot be PASS in v0. No `18 / 18` closure is claimed.

## r3 trust boundary: the supervisor process

```
untrusted caller ── capture_inr_v0 (launcher, computes nothing)
      │  python -I -S -B <worktree>/docs/inr_001/supervisor_inr_v0.py
      │     --event-id --repository --out [--ledger] [--work-dir]   (non-trust parameters only)
      ▼  stdin = DEVNULL
trusted supervisor process  (supervisor_inr_v0.supervise, one execution path)
   loads + pins frozen profile/origin → generates challenge → reserves ledger entry
   → measures pinned Git → stages pinned blobs read-only → launches every target
   child itself → reads stdout/stderr/returncode from the Popen it created → derives
   every predicate and the classification → writes the export, prints the report
      │
      ▼  report on stdout (supervisor_pid, event_id)
launcher accepts the report only if supervisor_pid == pid of the child it launched,
event_id == requested and the exit status agrees with pass_allowed
```

- The supervisor accepts NO evidence, snapshot, capture record, provenance, report or
  classification from argv (argparse with `allow_abbrev=False` rejects any other
  option), stdin (never read; the launcher closes it), environment (INR_* claims are
  ignored and stripped from children) or files (it reads only its own pinned
  configuration, the pinned Git objects and the staged files it wrote).
- No evidence object, registry, token, `_take_evidence`, `register_snapshot`,
  `validate_trusted_evidence` or `_verify_live` exists any more. Per-case derivation
  runs on the values of the child that was just launched, inside the same function.
- Not used as the trust boundary: Python underscore privacy, closure or module
  secrecy, unexported constructors, capability tokens in mutable objects. The
  module holds no mutable registry in globals or closures (test A checks this).
- Result semantics (`Findings`): every required predicate starts `NOT_ESTABLISHED`.
  PASS is the conjunction of all 16 required predicates explicitly established, with
  no FAIL/BLOCKED/UNCONFIRMED, no contradiction (establishing a predicate that has
  an issue counts as FAIL) and nothing missing. An empty `Findings()` or zero checks
  gives UNCONFIRMED.
  Required predicates: `supervisor_process`, `profile_pinned`, `event_challenge`,
  `git_runtime`, `target_identity`, `runtime_identity`, `child_launched`,
  `child_provenance`, `argv_exact`, `capture_complete`, `mandatory_cases_executed`,
  `module_identity`, `refusal_semantics`, `non_origin`, `shared_state_absence`,
  `all_writer_isolation`.
- `supervisor_process` is established only when the code runs as `__main__` of an
  isolated `-I -S -B` interpreter started on the supervisor file. This check is
  defence in depth, not the boundary. Code imported into another process
  (`supervise()`, `main()`, `runpy`) gets `result_kind: IN_PROCESS_NOT_TRUSTED` and
  is never PASS-capable. Its report carries the caller's own pid, so the launcher
  cannot relay it.
- Disk or caller-supplied records (exports, reports, ledger entries) are only
  INFORMATIONAL_RECHECK (`validate_inr_v0.recheck_export`: `pass_allowed: false`,
  `fresh_pass_capable: false`). A recorded PASS stays history.

Status vocabulary: PASS = enforced by the r3 local tooling and exercised by a real
regression test; PARTIAL = enforced locally with a stated residual limitation;
UNCONFIRMED = external assurance with no supervisor-owned evidence source in v0;
FAIL = not enforced.

| finding | invariant | r3 enforcement | regression test(s) | status |
|---|---|---|---|---|
| INR-MF-001 | distribution bytes = executed bytes | supervisor checks Git blob bytes at TARGET_SHA against `target_file_digests`; staged source measured before/after; child hashes and compiles the same bytes (`module_identity`) | `test_real_children_are_launched_and_bound` | PASS |
| INR-MF-002 | measured source = executed module | child `exec(compile(raw))` of the hashed bytes; executed source path bound to the supervisor-derived staging path; not preloaded | `test_real_children_are_launched_and_bound`, `test_argv_mismatch_rejected` | PASS |
| INR-MF-003 | Git runtime bound | pinned absolute Git, `shutil.which` must equal it, no `GIT_*` env, risky config/replace refs/alternates/grafts rejected; child PATH = pinned Git dir only, `GIT_NO_REPLACE_OBJECTS=1`; every child must resolve the measured Git with no shadowing; Git re-hashed after the event | `test_real_children_are_launched_and_bound` | PARTIAL (Windows `cmd\git.exe` is a launcher shim; only the shim is hashed) |
| INR-MF-004 | no TOCTOU mutation | staged files read-only, before/after measurement, input/probe re-measurement | `test_real_children_are_launched_and_bound` | PARTIAL (same-user writers are not excluded; see MF-012) |
| INR-MF-005 | complete frozen inventory | `mandatory_cases_executed`: executed case list must equal the frozen mandatory list in order; counts per predicate must equal the case count | `test_D_no_child_path_is_never_pass`, `test_real_children_are_launched_and_bound` | PASS |
| INR-MF-006 | self-declared non-origin insufficient | `_assess_external` takes no input; env/JSON claims ignored | `test_overall_never_pass_and_external_unconfirmed`, `test_forged_export_pass_claims_rejected_by_recheck` | UNCONFIRMED |
| INR-MF-007 | evidence not curated after run | streams read by the supervisor from its own Popen; export digest recorded in the ledger; edited exports FAIL recheck; disk records are informational only | `test_forged_export_pass_claims_rejected_by_recheck`, `test_F_historical_or_disk_evidence_never_becomes_fresh_pass` | PASS |
| INR-MF-008 | import hook/preload/pyc blocked | supervisor and children run `-I -S -B`; the supervisor sets `sys.pycache_prefix = os.devnull` before its own imports (no `__pycache__` reads); `site`/`sitecustomize`/`usercustomize` must be absent in children; target compiled from bytes | `test_argv_mismatch_rejected`, `test_supervisor_process_boundary_established` | PARTIAL (child stdlib `__pycache__` may still be read) |
| INR-MF-009 | writable parent/symlink/dependency protected | no objective evidence; folded into all-writer isolation | — | UNCONFIRMED |
| INR-MF-010 | executor cannot weaken profile | profile digest pinned in the supervisor; the supervisor takes no profile input; schema requires `mandatory_execution: true` and exact refusals | `test_profile_origin_conform_and_digest_is_pinned`, `test_D_no_child_path_is_never_pass` (unpinned profile → BLOCKED) | PASS |
| INR-MF-011 | same-host VM/container non-qualifying | no supervisor-owned runner evidence | `test_overall_never_pass_and_external_unconfirmed` | UNCONFIRMED |
| INR-MF-012 | all-writer isolation | no input; always UNCONFIRMED | `test_overall_never_pass_and_external_unconfirmed` | UNCONFIRMED |
| INR-MF-013 | trusted profile binding | pinned digest + r3 re-freeze record | `test_profile_origin_conform_and_digest_is_pinned` | PASS |
| INR-MF-014 | no shared mutable state | no input; always UNCONFIRMED | `test_overall_never_pass_and_external_unconfirmed` | UNCONFIRMED |
| INR-MF-015 | origin reference pre-frozen | origin set digest pinned before any event | `test_profile_origin_conform_and_digest_is_pinned` | PARTIAL (local runs perform no origin-output comparison) |
| INR-MF-016 | no cross-event replay | fresh supervisor-generated challenge + per-launch nonce echoed by the child (output replay → `child_provenance` FAIL); ledger rejects repeated event IDs/challenges; r3 head record detects truncation/deletion of the ledger alone | `test_F_historical_or_disk_evidence_never_becomes_fresh_pass`, `test_event_id_replay_rejected_by_supervisor_process`, `test_challenge_reuse_rejected`, `test_truncated_ledger_fails_closed_via_head_record` | PARTIAL (event-ID single use relies on protected ledger history; deleting ledger and head together is indistinguishable from a fresh ledger) |
| INR-MF-017 | trusted origin set binding | origin digest pinned in trusted config; no executor input | `test_profile_origin_conform_and_digest_is_pinned` | PASS |
| INR-MF-018 | capture launches target | only the supervisor process launches children and reads their streams; fake Popen, duck-typed child, failed launch, synthetic evidence, in-process runs and forged relays are all non-PASS | `test_A_*` .. `test_G_*` in `test_synthetic_mint_r3.py` | PASS |

Totals over INR-MF-001..018: PASS 8, PARTIAL 5, UNCONFIRMED 5, FAIL 0.
(Change from r2: MF-016 PASS → PARTIAL, recording the ledger limitation honestly.)

## Review findings

| finding | remediation | regression test(s) | status |
|---|---|---|---|
| M1 self-attested verifier (99418b4) | superseded; disk JSON is informational only | `test_stale_99418b4_event_fails`, `test_synthetic_export_is_schema_valid_but_not_recorded` | PASS |
| M2 mintable `_SESSIONS` snapshot (C2-uncommitted) | registry removed in r2; r3 removes the in-process evidence path altogether | `test_A_closure_introspection_and_state_mutation_cannot_mint_pass` | PASS |
| M3 wrong-reason negative acceptance | exact `expected_errors` per case | `test_wrong_reason_rejection_is_not_an_expected_refusal`, `test_old_top_level_human_final_input_is_wrong_reason`, `test_every_negative_control_hits_its_exact_refusal` | PASS |
| Codex A: synthetic trust mint (1ce1651 closure registry; empty `_Findings().result()` == PASS) | process boundary (supervisor), no evidence API, conjunctive default-UNCONFIRMED result, launcher pid binding | `test_synthetic_mint_r3.py` A–G | PASS (SYNTHETIC_TRUST_MINT: CLOSED for the local tooling) |
| Codex B: `PSM_NEG_HUMAN_FINAL_PRODUCTION_INFERENCE` overclaim | split into `PSM_NEG_HUMAN_FINAL_INFERENCE` + `PSM_REQUIRED_PRODUCTION_NONCLAIM`; R3 re-freeze | `test_property_boundary_r3.py` | PASS |
| Codex ledger prefix truncation/reuse (nonmaterial) | head record (cheap fail-closed); limitation documented below | `LedgerTests` | NONMATERIAL LIMITATION (documented) |

POSITIVE_PRODUCTION_PERMISSION_GRANT_REFUSAL: NOT_CLAIMED. The pinned PSM validator
has no rule that rejects a positive production-permission assertion, so INR does not
claim that property was reconstructed (see `INR_001_PROFILE_REFREEZE_R3.md`).

## Ledger limitation (nonmaterial while full PASS is otherwise blocked)

- Ledger integrity assumes protected, persistent history.
- r3 adds a cheap fail-closed check: `<ledger>.head` records the newest entry. It
  fails closed when the ledger is truncated below the head, deleted while the head
  remains, or non-empty without a head (r2 ledgers without a head are refused; use a
  new ledger path).
- Deleting or rewriting BOTH the ledger and its head, or the whole ledger directory,
  cannot be detected locally. Truncation or deletion is therefore outside the local
  freshness guarantee unless the ledger location is independently protected.
- The ledger is a local replay guard. It is NOT strong append-only tamper evidence
  (no external anchoring, no signatures). The ledger path is a non-trust parameter.
  Evidence freshness does not depend on the ledger: every run generates a new
  challenge and nonces inside the supervisor.

## Nonmaterial limitations (declared)

- In-process self-attestation: a caller that imports the supervisor code into its
  own interpreter and also forges `sys.flags`/`sys.argv`/`sys.modules["__main__"]`
  can make its own in-process dict claim `supervisor_process`. That dict is the
  caller's own output. The launcher does not relay it (pid binding), recheck does not
  accept it, and it is equivalent to printing "PASS". Python introspection is not a
  trust boundary; the supervisor process is.
- The launcher is untrusted by design: whoever consumes the result must run the
  launcher (or the supervisor directly) in an untampered interpreter, as in
  `INR_001_EXTERNAL_RUN_PROCEDURE.md`. The supervisor code, stdlib, OS and local Git
  are the declared trust base (no hostile-host resistance in v0).

## Observed local run (this machine)

Supervisor process launched by the launcher (Python 3.14.3, worktree HEAD is not
TARGET_SHA): `result_kind: FRESH_SUPERVISOR_RUN`, `derived_result: BLOCKED`,
`local_controls_result: BLOCKED`. PASS predicates: `supervisor_process`,
`profile_pinned`, `event_challenge`, `git_runtime`, `child_launched`,
`child_provenance`, `argv_exact`, `capture_complete`, `mandatory_cases_executed`,
`module_identity`, `refusal_semantics` (11 cases, exact refusals). BLOCKED:
`runtime_identity` (Python 3.14.3 is outside the frozen 3.11.x),
`target_identity` (acquisition repository HEAD is not TARGET_SHA). UNCONFIRMED:
`non_origin`, `shared_state_absence`, `all_writer_isolation`.

INR_PASS_CLAIMED: NO. NON_ORIGIN_RUN_EXECUTED: NO. HUMAN_FINAL_CREATED: NO.
