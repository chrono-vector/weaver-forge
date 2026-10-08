# INR-XR-001 Implementation Matrix (external assurance adapter v0, R3)

Status: IMPLEMENTER RECORD after material remediation R3 (M1 and M3 only; M2 closed
in R2 and unchanged). It has not been independently reviewed. No real external run,
no real provider verification and no real artifact download has been executed.

`structural_bundle: PASS` is not assurance. `external_assurance: PASS` requires
GitHub Actions provider provenance and the bundle-to-run binding, which since R3
binds the submitted bundle CONTENT to the provider-held artifact CONTENT. In this
phase that PASS was reached only in unit tests under clearly labelled trust
substitutes (MOCK_ONLY). Provenance is RUN-LEVEL; job-level provenance is
NOT_CLAIMED. Under the accepted INR supervisor, `all_writer_isolation_established`
cannot be PASS (UNCONFIRMED), so a production `external_assurance` PASS is not
reachable. INR predicates for an external event exist only in the launcher-accepted
report of the XR verifier PROCESS. Nothing here is an INR PASS, IW admission, Human
Final or production permission.

## Status legend

- **PASS:** implemented and tested as specified. A mechanism is tested without
  network access; provider responses come from unit-test trust substitutes.
- **PARTIAL:** implemented and provider-anchored, but the property also rests on
  observations that the runner reports in the bundle. The provider anchors which
  run produced them, not their truth, and no hostile-host claim is made.
- **UNCONFIRMED:** not established by this work. Every requirement whose only
  trusted source is bundle-authored data, and real provider verification, is here.
- **FAIL:** the requirement is not met.

Columns: raw evidence (bundle, untrusted); trusted source; provider verification
step (`provider_github_v0.verify_provider`); local derivation
(`validate_external_run_v0`); integration point (`xr_verifier_v0`); failure
classification. Tests live in `tests/test_validate_external_run_v0.py`. `P:` is
ProviderTests or ProviderTransportTests, `I:` IntegrationTests, `B:`
IsolationBindingTests, `M1-A`..`M1-I` ArtifactContentTests, `M3-01`..`M3-12`
ProtectedExecutionTests, `adv_NN` AdversarialTests, and `F:` FocusedTests or
StaticTests.

## Matrix

| # | requirement | raw evidence | trusted source | provider verification step | local derivation | integration point | failure classification | tests | status |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Strict manifest, closed layout | `external_run_manifest.json` | committed profile (closed path set), code-owned schema | - | strict JSON, schema check, closed role/path map | `structural_bundle` must be PASS | violation: FAIL; absent file: UNCONFIRMED | adv_02, F:manifest_classification_field_rejected, F:predicate_and_role_sets_are_closed, F:strict_json | PASS |
| 2 | Hash binding of every raw file; bundle digest | manifest bindings, `raw/sha256sums.txt` | adapter-computed SHA-256 (bundle digest = SHA-256 of manifest bytes) | digest is the artifact-name key | bytes vs manifest; sums = manifest | `bundle_digest` 64-hex required | mismatch: FAIL | adv_13, F:sha256sums_disagreement_rejected, P:provider_tampered_manifest_changes_digest | PASS |
| 3 | Path safety and substitution | manifest paths, bundle tree | closed path map | - | no absolute/traversal/duplicate/symlink/junction/unbound/substituted entries | via `structural_bundle` | FAIL | adv_16-18, F:symlink_escape_rejected, F:junction_escape_rejected, F:substituted_evidence_role_rejected | PASS |
| 4 | M1: structural validity separated from assurance; predicates renamed | whole bundle | - | - | `*_evidence` (10) vs `*_established` (9); `structural_bundle`, `provider_provenance`, `bundle_run_binding`, `external_assurance` | only assurance and gates feed INR | no provider: assurance UNCONFIRMED | adv_20, P:p01, F:predicate_and_role_sets_are_closed, F:combine_precedence | PASS |
| 5 | M1: provider trust anchor (GitHub Actions only) | `runner_identity.json` claims | GitHub REST API at `https://api.github.com`, token from `INR_XR_GITHUB_TOKEN` | fixed 4 JSON endpoints (no redirects) plus the fixed `/actions/artifacts/{id}/zip` endpoint (one redirect to the documented artifact-storage host allowlist, no Authorization on the redirect, 64 MiB cap); no token: BLOCKED before any request | claims compared, never trusted | verifier always uses `GitHubProvider.from_environment()` | no data: BLOCKED; mismatch: FAIL; incomplete: UNCONFIRMED | P:p02, P:transport tests (6, incl. artifact_zip_download_policy), F:cli_uses_real_provider_and_never_passes_offline, I:real_verifier_process_without_token, F:r3_production_constants_and_closed_result_fields | PASS |
| 6 | Mocks unreachable from production | - | - | substitutes (JSON and ZIP) live only in the test module | no argv/env/file mock switch (checked on CLI options and source) | same | - | P:no_mock_switch_in_production_paths | PASS |
| 7 | Real provider verification and real artifact download against GitHub | real run metadata and artifact | GitHub | not executed (no network in this phase); storage-host allowlist not validated live | - | - | stays UNCONFIRMED | - | UNCONFIRMED |
| 8 | M1: submitted bundle CONTENT bound to provider-held artifact CONTENT (one mechanism) | submitted bundle tree | provider artifact listing, artifact metadata and artifact ZIP of the verified run | exactly one artifact `inr-xr-bundle-<digest>`; ID from the listing only; metadata repeats ID/name, names the run and head, unexpired, positive size, created in the claimed job window; ZIP size = `size_in_bytes`, ZIP SHA-256 = metadata `digest` when present; frozen content rule: exactly the manifest plus every bound path, byte-for-byte equal; extra/missing/duplicate/traversal/absolute/symlink/encrypted entries FAIL | digest from submitted manifest; bundle content compared only when bundle integrity holds | `provider_run.artifact_name` is set only when content is bound (verifier unchanged) | content or metadata mismatch, other run/head: FAIL; expired, empty, not unique, no local content: UNCONFIRMED; download unavailable: BLOCKED | M1-A..M1-I, P:p03, P:p07, P:provider_hosted_runner_and_windows, P:provider_tampered_manifest_changes_digest | PASS (mechanism, MOCK_ONLY; live download row 7) |
| 9 | Run, commit and workflow identity (run-level provenance) | claims (run, attempt, head SHA, workflow path, repository) | provider run attempt | all fields compared; head = operator `--expected-head-sha`; workflow = `.github/workflows/inr-xr-external-run.yml` | - | via `provider_provenance`; `run_level_provenance` reported | mismatch: FAIL | P:p04, P:p05, M1-G, M1-H | PASS |
| 9a | Job-level provenance (producing job authenticated) | claimed job ID, runner, times | provider job record (consistency only) | the claimed job must belong to the verified run/attempt/head and its window must contain the artifact and event times, but artifacts are run-scoped: the producing job is not authenticated | - | `job_level_provenance: NOT_CLAIMED`; claimed fields reported as `claimed_job_*` | never PASS | M1-H, P:provider_hosted_runner_and_windows | UNCONFIRMED (NOT_CLAIMED) |
| 10 | Stale or incomplete provider run | - | provider timestamps, status, conclusion; operator `--not-before` | run created < not-before: UNCONFIRMED; not completed/success: UNCONFIRMED; disorder: FAIL; event window outside job window: FAIL | event times from bundle placed in provider window | via `provider_provenance` | as stated | P:p06, adv_19, I:integration_requires_bound_digest_and_run | PASS |
| 11 | Runner identity (`runner_identity_established`) | runner identity | provider job (`runner_name`) of a job of the verified run | step 9a (consistency, not job authentication) | provider known, attempt, times | `non_origin` source | missing: UNCONFIRMED; mismatch: FAIL | adv_04, P:p04 | PARTIAL: run-level only; the job that produced the bundle is not authenticated |
| 12 | Fresh hosted runner (`fresh_hosted_runner_established`) | runner identity, workspace provenance (boot time, listings, caches) | provider `runner_group_name == "GitHub Actions"` for the claimed job | hosted-group check: FAIL otherwise | boot-to-job <= 4h, no prior artifacts/cache restore/inherited state | `non_origin` source | self-hosted/contradiction: FAIL | adv_01, adv_06, F:self_hosted_or_unknown_runner, P:provider_hosted_runner_and_windows | PARTIAL: run-level only; per-job freshness relies on GitHub-hosted runner semantics; boot time and listings are runner-reported |
| 13 | Fresh workspace (`fresh_workspace_established`) | workspace provenance, git identity | provider binding (origin of the observations only) | steps 8-10 | empty listing, timing, `.git` directory, clean tree | `non_origin` source | contradiction: FAIL | adv_05, F:linked_worktree_or_dirty_checkout | PARTIAL: observations runner-reported |
| 14 | Independent acquisition (`independent_acquisition_established`) | acquisition log, git identity, `raw/target/*` | committed pinned digests and TARGET_SHA; authoritative repository | steps 8-10 | adapter hashes acquired PSM bytes; required objects from digest-verified example; no copy/shared store | `non_origin` and `target_identity` source | copy/local: FAIL; target/object/digest: BLOCKED | adv_07-09, F:non_authoritative_or_shared_acquisition, F:target_file_digest_mismatch_blocked | PARTIAL: content identity checked against trusted digests; the acquisition method is runner-reported |
| 15 | Trusted reference binding (target/profile/origin) | manifest and event references | committed INR configuration | - | equality only; never read from bundle | bound target SHA/profile/origin digests must equal the supervisor pins | alternate: UNCONFIRMED; target mismatch: BLOCKED; in INR: FAIL | adv_12, I:i09, I:i10, F:trusted_configuration_unavailable_blocks | PASS |
| 16 | No shared mutable state (`no_shared_mutable_state_established`) | isolation checks, workspace provenance | provider binding (origin only) | steps 8-10 | shared/network mounts, alternates, snapshot, caches | `shared_state_absence` source | detected: FAIL | adv_02, adv_06, F:writable_network_mount_and_shared_object_store | PARTIAL: observable runner-reported state only |
| 17 | M3: actual execution objects bound to the protected inventory (`inventory_binding`) | protected tree; supervisor path; git probe; capture cwd and argv; python identity | trusted tooling and PSM digests; capture records | steps 8-10 | required set derived from runtime data: execution cwd, stage root, staged validator (argv[5]), case JSON (argv[6]), probe (argv[4]), repository (argv[7]), interpreter (argv[0]), Git executable, target tree/files, Git common dir, object store and alternates, supervisor, profile/origin, inputs, command inventory; exact path/kind/digest; extras and substitutions rejected; work dir = actual stage root | `all_writer_isolation` source | substituted/unrelated path, argv outside cwd, cwd outside root, digest mismatch: FAIL; missing entry: UNCONFIRMED | M3-01..M3-06, M3:runtime_executables_and_alternates_bound, B:b12, B:b13, B:b15, B:b16, B:inventory_rules_extra_and_digest | PASS |
| 18 | M3: parent chain and mount identity | protected tree parent chain, devices | - | - | every ancestor (up to the bounded root) of every in-root protected path that is not itself an entry; extra parents FAIL; alias/others-writable FAIL; missing UNCONFIRMED; device boundary UNCONFIRMED | same | as stated | M3-07, B:b14, F:protected_tree_rules | PASS (runtime executables outside the root: no chain required) |
| 19 | M3: frozen protected tree non-writable during execution, output dirs separated (`frozen_tree`) | entries, post_entries, parent chain, output dirs, freeze/post times | - | - | frozen entries and parents neither writable nor owned by the execution principal; post entries equal; freeze/post digests recomputed and equal; freeze/post times enclose the event window; output dirs exactly export/ledger/work_dir, absolute, not overlapping the frozen tree; equal digests alone never suffice | same | writable/owned: UNCONFIRMED; changed/overlap/alias: FAIL | M3-08, M3-09, M3-10, M3-11, M3-12 | PARTIAL: mechanism tested; permissions and ownership are runner-reported |
| 19a | M3: staged execution objects (stage root, cwd, staged validator, case JSON) non-writable during execution (`staged_objects`) | staged entries | accepted supervisor staging model (code constant) | - | accepted supervisor stages them as the execution principal: always UNCONFIRMED; claims of frozen staged objects: FAIL (contradiction) | same | UNCONFIRMED / FAIL | M3-08, M3-09, M3-12, F:r3_production_constants_and_closed_result_fields | UNCONFIRMED |
| 19b | All-writer isolation (`all_writer_isolation_established`) | rows 17-19a | provider binding (origin only) | steps 8-10 | conjunction of rows 17, 18, 19 and 19a | `all_writer_isolation` source | at best UNCONFIRMED in production | M3-12 (PASS only under the hypothetical staging substitute) | UNCONFIRMED |
| 20 | Python 3.11 / Git identity | python identity, git identity, children | provider binding (origin only) | steps 8-10 | CPython 3.11.x; Git ambiguity checks; cross-file consistency | `runtime_identity`, `git_runtime` sources | BLOCKED/FAIL | adv_10, adv_11, F:git_ambiguity_blocked, F:python_implementation_and_inconsistency | PARTIAL: observations runner-reported |
| 21 | Event/supervisor provenance (`current_event_capture_established`) | event start, capture records, streams, post measurement, event complete | operator event ID and not-before; committed pins | event window inside the claimed job window | INR-001 r3 semantics re-derived; supervisor report negative-only | local INR predicates need this AND the report PASS | replay/stale/contradiction: FAIL; absent: UNCONFIRMED | adv_14, adv_15, adv_19, F:child_replay_argv_and_refusal_drift, F:supervisor_report_is_negative_only | PARTIAL: content bound to the verified run's artifact; content runner-reported |
| 22 | Freshness against the runner-side INR ledger | - | none | - | bounded by event ID, not-before, provider run time, job window | - | no PASS without operator parameters | adv_19, P:p06 | UNCONFIRMED |
| 23 | M2: one-way INR integration (XR verifier process) | bundle path only | process boundary: isolated `-I -S -B` verifier process; launcher pid/event/exit binding | performed inside the process | derived inside the same process | `derive_inr_predicates` with `sup.Findings` (16 predicates) | not provider-authenticated: UNCONFIRMED/BLOCKED; event/target/profile/origin mismatch: FAIL; digest missing: FAIL/UNCONFIRMED; stale: UNCONFIRMED | I:i00, I:i08, I:i09, I:i10, I:integration_requires_bound_digest_and_run, I:real_verifier_process_without_token | PASS |
| 24 | Plain JSON or reconstructed results cannot inject INR predicates | forged JSON (argv, bundle, replayed report, env) | process boundary | - | in-process: `IN_PROCESS_NOT_TRUSTED`; bundle-carried result: structural FAIL | launcher rejects pid/kind/event/exit mismatch; supervisor `_assess_external` unchanged | UNCONFIRMED or FAIL, never PASS | I:i11, F:verifier_outside_process_establishes_nothing | PASS |
| 25 | Self-attestation cannot create PASS | `runner_declarations`, unknown fields | - | provider fields are claims | declarations ignored; predicate-named fields rejected (`*_evidence` included) | - | FAIL/UNCONFIRMED/BLOCKED | adv_01-03, F:declarations_are_informational_only_both_ways, F:raw_predicate_field_makes_evidence_inadmissible | PASS |
| 26 | Synthetic bundle gives structural PASS and assurance UNCONFIRMED | synthetic bundle | - | none | all evidence PASS | - | assurance UNCONFIRMED | adv_20, P:p01 | PASS |
| 27 | Accepted INR-001 local tooling unchanged | `docs/inr_001/*` outside `xr/` | - | - | - | none (the integration point is the new XR verifier) | - | existing INR suite (46) | PASS |
| 28 | Real external run | - | - | - | - | - | not executed | - | UNCONFIRMED |

## Totals

- PASS: 18 (rows 1-6, 8-10, 15, 17, 18, 23-27)
- PARTIAL: 9 (rows 11-14, 16, 19-21)
- UNCONFIRMED: 6 (rows 7, 9a, 19a, 19b, 22, 28)
- FAIL: 0

Each assurance PASS in the tests depends on unit-test provider substitutes, and the
all-writer PASS additionally on a hypothetical staging substitute. Real provider
verification and real artifact download (row 7) are UNCONFIRMED, job-level
provenance is NOT_CLAIMED (row 9a), and all-writer isolation is UNCONFIRMED under
the accepted supervisor (row 19b), so no real external assurance exists yet.

## Recorded deviations

- The bundle adds `raw/target/<pinned PSM file>` (unchanged from 304de4d).
- R3: the R2 principal-writable stage-root allowance is removed. The accepted INR
  supervisor stages the executed validator and case JSON as the execution principal;
  the accepted tooling is not changed, so `staged_objects` and all-writer isolation
  stay UNCONFIRMED. M3 test 12 reaches bounded-isolation PASS only under a labelled
  hypothetical staging substitute; with the accepted supervisor the same complete
  frozen inventory yields `inventory_binding` PASS, `frozen_tree` PASS,
  `staged_objects` UNCONFIRMED.
- R3: job-level provenance is NOT_CLAIMED (artifacts are run-scoped).
- R3: the storage-redirect allowlist (`productionresultssa<N>.blob.core.windows.net`,
  path `/actions-results/`) follows GitHub's documented behaviour; it is not validated
  live.
- No OIDC/attestation. The one binding mechanism is GitHub artifact content
  verification, keyed by the artifact name.
- No file outside `docs/inr_001/xr/` was added or modified.
