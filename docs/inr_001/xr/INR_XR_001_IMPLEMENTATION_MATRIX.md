# INR-XR-001 Implementation Matrix (external assurance adapter v0, R2)

Status: IMPLEMENTER RECORD after material remediation R2 (M1-M3). It has not been
independently reviewed. No real external run and no real provider verification has
been executed.

`structural_bundle: PASS` is not assurance. `external_assurance: PASS` requires
GitHub Actions provider provenance and the bundle-to-run binding. In this phase that
PASS was reached only in unit tests under clearly labelled trust substitutes. INR
predicates for an external event exist only in the launcher-accepted report of the
XR verifier PROCESS. Nothing here is an INR PASS, IW admission, Human Final or
production permission.

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
IsolationBindingTests, `adv_NN` AdversarialTests, and `F:` FocusedTests or
StaticTests.

## Matrix

| # | requirement | raw evidence | trusted source | provider verification step | local derivation | integration point | failure classification | tests | status |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Strict manifest, closed layout | `external_run_manifest.json` | committed profile (closed path set), code-owned schema | - | strict JSON, schema check, closed role/path map | `structural_bundle` must be PASS | violation: FAIL; absent file: UNCONFIRMED | adv_02, F:manifest_classification_field_rejected, F:predicate_and_role_sets_are_closed, F:strict_json | PASS |
| 2 | Hash binding of every raw file; bundle digest | manifest bindings, `raw/sha256sums.txt` | adapter-computed SHA-256 (bundle digest = SHA-256 of manifest bytes) | digest is the artifact-name key | bytes vs manifest; sums = manifest | `bundle_digest` 64-hex required | mismatch: FAIL | adv_13, F:sha256sums_disagreement_rejected, P:provider_tampered_manifest_changes_digest | PASS |
| 3 | Path safety and substitution | manifest paths, bundle tree | closed path map | - | no absolute/traversal/duplicate/symlink/junction/unbound/substituted entries | via `structural_bundle` | FAIL | adv_16-18, F:symlink_escape_rejected, F:junction_escape_rejected, F:substituted_evidence_role_rejected | PASS |
| 4 | M1: structural validity separated from assurance; predicates renamed | whole bundle | - | - | `*_evidence` (10) vs `*_established` (9); `structural_bundle`, `provider_provenance`, `bundle_run_binding`, `external_assurance` | only assurance and gates feed INR | no provider: assurance UNCONFIRMED | adv_20, P:p01, F:predicate_and_role_sets_are_closed, F:combine_precedence | PASS |
| 5 | M1: provider trust anchor (GitHub Actions only) | `runner_identity.json` claims | GitHub REST API at `https://api.github.com`, token from `INR_XR_GITHUB_TOKEN` | fixed 3 endpoints, GET, no redirects, host/status/size/JSON checks; no token: BLOCKED before any request | claims compared, never trusted | verifier always uses `GitHubProvider.from_environment()` | no data: BLOCKED; mismatch: FAIL; incomplete: UNCONFIRMED | P:p02, P:transport tests (5), F:cli_uses_real_provider_and_never_passes_offline, I:real_verifier_process_without_token | PASS |
| 6 | Mocks unreachable from production | - | - | substitutes live only in the test module | no argv/env/file mock switch (checked on CLI options and source) | same | - | P:no_mock_switch_in_production_paths | PASS |
| 7 | Real provider verification against GitHub | real run metadata | GitHub | not executed (no network in this phase) | - | - | stays UNCONFIRMED | - | UNCONFIRMED |
| 8 | Bundle-to-run binding (one mechanism) | bundle digest | provider artifact list of the verified run | exactly one artifact `inr-xr-bundle-<digest>`, same run and head, not expired/empty, created in the job window | digest from submitted manifest | `provider_run.artifact_name` = prefix + digest required | not bound: UNCONFIRMED; other run or outside window: FAIL | P:p03, P:p07, P:provider_hosted_runner_and_windows, P:provider_tampered_manifest_changes_digest | PASS |
| 9 | Run/job/commit/workflow identity | claims (run, attempt, job, runner, head SHA, workflow path, repository, job start) | provider run attempt and job | all fields compared; head = operator `--expected-head-sha`; workflow = `.github/workflows/inr-xr-external-run.yml` | - | via `provider_provenance` | mismatch: FAIL | P:p04, P:p05, P:provider_hosted_runner_and_windows | PASS |
| 10 | Stale or incomplete provider run | - | provider timestamps, status, conclusion; operator `--not-before` | run created < not-before: UNCONFIRMED; not completed/success: UNCONFIRMED; disorder: FAIL; event window outside job window: FAIL | event times from bundle placed in provider window | via `provider_provenance` | as stated | P:p06, adv_19, I:integration_requires_bound_digest_and_run | PASS |
| 11 | Runner identity (`runner_identity_established`) | runner identity | provider job (`runner_name`, run, job) | step 9 | provider known, attempt, times | `non_origin` source | missing: UNCONFIRMED | adv_04, P:p04 | PASS (mechanism; real verification row 7) |
| 12 | Fresh hosted runner (`fresh_hosted_runner_established`) | runner identity, workspace provenance (boot time, listings, caches) | provider `runner_group_name == "GitHub Actions"` (hosted) | hosted-group check: FAIL otherwise | boot-to-job <= 4h, no prior artifacts/cache restore/inherited state | `non_origin` source | self-hosted/contradiction: FAIL | adv_01, adv_06, F:self_hosted_or_unknown_runner, P:provider_hosted_runner_and_windows | PARTIAL: per-job freshness relies on GitHub-hosted runner semantics; boot time and listings are runner-reported |
| 13 | Fresh workspace (`fresh_workspace_established`) | workspace provenance, git identity | provider binding (origin of the observations only) | steps 8-10 | empty listing, timing, `.git` directory, clean tree | `non_origin` source | contradiction: FAIL | adv_05, F:linked_worktree_or_dirty_checkout | PARTIAL: observations runner-reported |
| 14 | Independent acquisition (`independent_acquisition_established`) | acquisition log, git identity, `raw/target/*` | committed pinned digests and TARGET_SHA; authoritative repository | steps 8-10 | adapter hashes acquired PSM bytes; required objects from digest-verified example; no copy/shared store | `non_origin` and `target_identity` source | copy/local: FAIL; target/object/digest: BLOCKED | adv_07-09, F:non_authoritative_or_shared_acquisition, F:target_file_digest_mismatch_blocked | PARTIAL: content identity checked against trusted digests; the acquisition method is runner-reported |
| 15 | Trusted reference binding (target/profile/origin) | manifest and event references | committed INR configuration | - | equality only; never read from bundle | bound target SHA/profile/origin digests must equal the supervisor pins | alternate: UNCONFIRMED; target mismatch: BLOCKED; in INR: FAIL | adv_12, I:i09, I:i10, F:trusted_configuration_unavailable_blocks | PASS |
| 16 | No shared mutable state (`no_shared_mutable_state_established`) | isolation checks, workspace provenance | provider binding (origin only) | steps 8-10 | shared/network mounts, alternates, snapshot, caches | `shared_state_absence` source | detected: FAIL | adv_02, adv_06, F:writable_network_mount_and_shared_object_store | PARTIAL: observable runner-reported state only |
| 17 | M3: protected inventory bound to actual execution paths | protected tree; supervisor path; git probe; capture cwd/argv | trusted tooling and PSM digests | steps 8-10 | expected set derived from runtime paths (target tree/files, Git dir, objects, profile/origin, inputs, command inventory, capture configuration, stage root); exact path, kind and digest equality; extras rejected; probe/repository argv bound | `all_writer_isolation` source | unrelated path, unused path, capture path outside, unrelated Git dir/object store: FAIL; partial inventory: UNCONFIRMED | B:b12, B:b13, B:b15, B:b16, B:inventory_rules_extra_and_digest | PASS |
| 18 | M3: parent chain and mount identity bound | protected tree parent chain, devices | - | - | every ancestor of every expected path up to the root required; extra parents FAIL; alias/others-writable FAIL; writable or mount boundary UNCONFIRMED | same | as stated | B:b14, F:protected_tree_rules | PASS |
| 19 | All-writer isolation (`all_writer_isolation_established`) | rows 17-18 | provider binding (origin only) | steps 8-10 | rows 17-18 plus freeze/post digest | `all_writer_isolation` source | as rows 17-18 | adv_03, B:* | PARTIAL: permissions runner-reported; privileged/host writers not excluded |
| 20 | Python 3.11 / Git identity | python identity, git identity, children | provider binding (origin only) | steps 8-10 | CPython 3.11.x; Git ambiguity checks; cross-file consistency | `runtime_identity`, `git_runtime` sources | BLOCKED/FAIL | adv_10, adv_11, F:git_ambiguity_blocked, F:python_implementation_and_inconsistency | PARTIAL: observations runner-reported |
| 21 | Event/supervisor provenance (`current_event_capture_established`) | event start, capture records, streams, post measurement, event complete | operator event ID and not-before; committed pins | event window inside the verified job window | INR-001 r3 semantics re-derived; supervisor report negative-only | local INR predicates need this AND the report PASS | replay/stale/contradiction: FAIL; absent: UNCONFIRMED | adv_14, adv_15, adv_19, F:child_replay_argv_and_refusal_drift, F:supervisor_report_is_negative_only | PARTIAL: bound to the verified run by digest; content runner-reported |
| 22 | Freshness against the runner-side INR ledger | - | none | - | bounded by event ID, not-before, provider run time, job window | - | no PASS without operator parameters | adv_19, P:p06 | UNCONFIRMED |
| 23 | M2: one-way INR integration (XR verifier process) | bundle path only | process boundary: isolated `-I -S -B` verifier process; launcher pid/event/exit binding | performed inside the process | derived inside the same process | `derive_inr_predicates` with `sup.Findings` (16 predicates) | not provider-authenticated: UNCONFIRMED/BLOCKED; event/target/profile/origin mismatch: FAIL; digest missing: FAIL/UNCONFIRMED; stale: UNCONFIRMED | I:i00, I:i08, I:i09, I:i10, I:integration_requires_bound_digest_and_run, I:real_verifier_process_without_token | PASS |
| 24 | Plain JSON or reconstructed results cannot inject INR predicates | forged JSON (argv, bundle, replayed report, env) | process boundary | - | in-process: `IN_PROCESS_NOT_TRUSTED`; bundle-carried result: structural FAIL | launcher rejects pid/kind/event/exit mismatch; supervisor `_assess_external` unchanged | UNCONFIRMED or FAIL, never PASS | I:i11, F:verifier_outside_process_establishes_nothing | PASS |
| 25 | Self-attestation cannot create PASS | `runner_declarations`, unknown fields | - | provider fields are claims | declarations ignored; predicate-named fields rejected (`*_evidence` included) | - | FAIL/UNCONFIRMED/BLOCKED | adv_01-03, F:declarations_are_informational_only_both_ways, F:raw_predicate_field_makes_evidence_inadmissible | PASS |
| 26 | Synthetic bundle gives structural PASS and assurance UNCONFIRMED | synthetic bundle | - | none | all evidence PASS | - | assurance UNCONFIRMED | adv_20, P:p01 | PASS |
| 27 | Accepted INR-001 local tooling unchanged | `docs/inr_001/*` outside `xr/` | - | - | - | none (the integration point is the new XR verifier) | - | existing INR suite (46) | PASS |
| 28 | Real external run | - | - | - | - | - | not executed | - | UNCONFIRMED |

## Totals

- PASS: 18 (rows 1-6, 8-11, 15, 17, 18, 23-27)
- PARTIAL: 7 (rows 12-14, 16, 19-21)
- UNCONFIRMED: 3 (rows 7, 22, 28)
- FAIL: 0

Each assurance PASS in the tests depends on unit-test provider substitutes. Real
provider verification (row 7) is UNCONFIRMED, so no real external assurance exists
yet.

## Recorded deviations

- The bundle adds `raw/target/<pinned PSM file>` (unchanged from 304de4d).
- The stage root (`execution_tree`) is the one protected entry that may be
  principal-writable, because the supervisor creates its staging directory there.
- No OIDC/attestation. The one binding mechanism is the provider artifact name.
- No file outside `docs/inr_001/xr/` was added or modified.
