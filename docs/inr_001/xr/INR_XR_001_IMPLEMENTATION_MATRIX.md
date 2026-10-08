# INR-XR-001 Implementation Matrix (external assurance adapter v0)

Status: IMPLEMENTER RECORD. It has not been independently reviewed, and no real
external run has been executed.

An adapter PASS is an ADAPTER/BUNDLE PASS only. It is NOT an INR external
reconstruction PASS, NOT a fresh local INR PASS, not IW admission, not Human Final
and not production permission. A disk bundle is checked only for internal
consistency and hash binding.

## Status legend

- **PASS:** the requirement is implemented and tested as specified.
- **PARTIAL:** the requirement is implemented, but the evidence cannot fully prove
  the property.
- **UNCONFIRMED:** the requirement is not established by this work.
- **FAIL:** the requirement is not met.

## Matrix

Tests live in `tests/test_validate_external_run_v0.py`. `adv_NN` is
`AdversarialTests.test_adv_NN_*` and `F:` is a `FocusedTests` or `StaticTests` method.

| # | requirement | evidence source | adapter derivation | fail-closed classification | tests | status |
|---|---|---|---|---|---|---|
| 1 | Bundle layout and strict manifest (s4, s17) | `external_run_manifest.json`, schema top level | strict JSON (no duplicate keys/BOM/NaN), code-owned schema check, closed role/path set from the trusted profile | schema violation: FAIL; required file absent: UNCONFIRMED | adv_02, F:manifest_classification_field_rejected, F:predicate_and_role_sets_are_closed, F:strict_json | PASS |
| 2 | Hash binding of every raw file (s4) | manifest `evidence_files`, `raw/sha256sums.txt` | sha256 of the bytes vs the manifest; sha256sums must equal the manifest bindings | mismatch: FAIL (tamper), no derivation | adv_13, F:sha256sums_disagreement_rejected, F:bound_file_missing_on_disk | PASS |
| 3 | Path safety: absolute, traversal, duplicate, symlink escape (s4) | manifest paths, bundle tree | relative POSIX only; no `.`/`..`/empty/colon/backslash; case-folded duplicates; symlink/junction per component and in the walk; resolved path inside the bundle | FAIL | adv_16, adv_17, adv_18, F:symlink_escape_rejected, F:path_rules | PASS |
| 4 | Unknown required-evidence substitution (s4) | manifest roles, bundle tree | role must equal the closed path map; unbound files rejected; unknown case IDs rejected | FAIL | F:substituted_evidence_role_rejected, F:unbound_extra_file_rejected, F:unknown_case_record_rejected | PASS |
| 5 | Runner identity derivation (s5) | `raw/runner_identity.json` | provider (known hosted), run/job ID, runner name, OS/arch/image, boot and job times | missing: UNCONFIRMED | adv_04, F:self_hosted_or_unknown_runner | PASS (runner-reported fields; no provider API check) |
| 6 | Fresh hosted runner (s6) | runner identity + workspace provenance | github-hosted, boot-to-job window <= 4h, no prior-job artifacts, no cache restore, no inherited writable state | self-hosted/contradiction: FAIL; unknown: UNCONFIRMED | adv_01, adv_06, F:self_hosted_or_unknown_runner | PARTIAL: candidate only; freshness rests on runner-reported times and listings, with no provider attestation |
| 7 | Origin comparison (s7) | committed origin set and profile (trusted); manifest references | equality with the trusted id/digest only; the origin is never read from the bundle | alternate/stale/executor-selected: UNCONFIRMED; target mismatch: BLOCKED | adv_12, F:trusted_configuration_comes_from_committed_config, F:trusted_configuration_unavailable_blocks | PASS |
| 8 | Fresh workspace (s8) | workspace provenance, runner identity, git identity | empty initial listing, created after job start, ordered acquisition timing, `.git` directory, clean tree, repository inside the workspace; never the path name alone | contradiction: FAIL; missing: UNCONFIRMED | adv_05, F:linked_worktree_or_dirty_checkout | PASS |
| 9 | Independent acquisition (s9) | `acquisition.log`, git identity, `raw/target/*`, post measurement | authoritative https source, git clone/fetch, no copy/link/shared-store; ref = HEAD = TARGET_SHA; remote = source; adapter-hashed PSM bytes = pinned digests; required commits from the digest-verified example present | copy/local source: FAIL; target/object/digest: BLOCKED; non-authoritative: UNCONFIRMED | adv_07, adv_08, adv_09, F:non_authoritative_or_shared_acquisition, F:target_file_digest_mismatch_blocked | PASS |
| 10 | No shared mutable state (s10) | `isolation_checks.json`, workspace provenance, git identity | writable shared/network mounts (adapter-known network fs types), shared object store/alternates, snapshot restore, restored/shared caches | detected: FAIL; missing: UNCONFIRMED | adv_02, adv_06, F:writable_network_mount_and_shared_object_store | PARTIAL: only observable, runner-reported state; claims nothing about unobserved storage |
| 11 | Protected-tree / all-writer isolation (s11) | `isolation_checks.protected_tree` | 7 categories, named entries = trusted digests, no alias/hard link, not writable (principal/others/parents), mount/cache overlap, adapter-recomputed freeze digest = post digest | alias/others-writable/digest change: FAIL; incomplete/principal-writable/admin: UNCONFIRMED | adv_03, F:protected_tree_rules | PARTIAL: permission observations are runner-reported; privileged/host writers not excluded; INR `all_writer_isolation` stays UNCONFIRMED |
| 12 | Python 3.11 policy (s12) | python identity, supervisor, children, measured digest | CPython 3.11.x, exact version/implementation/executable, cross-file consistency | not 3.11/unknown/non-CPython: BLOCKED; inconsistent: FAIL | adv_10, F:python_implementation_and_inconsistency | PASS |
| 13 | Git identity (s13) | git identity, event Git probe, child reports | executable/path/version/env, replace/alternates/grafts, shallow, rejected config, HEAD, required objects, consistency | unavailable/ambiguous: BLOCKED; inconsistent: FAIL | adv_11, adv_08, F:git_ambiguity_blocked | PASS |
| 14 | Event/supervisor provenance binding (s14) | event start, command results, streams, post measurement, event complete | INR-001 r3 semantics re-derived: event ID/challenge/nonce, isolated accepted supervisor, lifecycle order, child window, argv template, refusal semantics, child identity; supervisor report negative-only | replay/stale/contradiction: FAIL; absent: UNCONFIRMED | adv_14, adv_15, adv_19, F:child_replay_argv_and_refusal_drift, F:supervisor_report_is_negative_only, F:lifecycle_order_and_event_complete_order, F:event_profile_binding_mismatch_unconfirmed, F:operator_parameters_required | PASS (binding and consistency) |
| 15 | Freshness of a disk bundle against the runner-side INR ledger (s14) | none available to the adapter | bounded only by the operator event ID, not-before time and job window | no PASS without operator parameters | adv_19 | UNCONFIRMED: cannot be established from a disk bundle |
| 16 | Bounded predicate list and classification (s15, s16) | adapter | the fixed 10 predicates plus 2 adapter gates; `Findings` semantics reused (default NOT_ESTABLISHED, conjunctive, BLOCKED > FAIL > UNCONFIRMED) | any predicate not PASS: no PASS | adv_01 to adv_20, F:predicate_and_role_sets_are_closed | PASS |
| 17 | Self-attestation cannot create PASS (s3, s17) | `runner_declarations`, unknown fields | declarations ignored (echoed); predicate/classification fields rejected; supervisor report negative-only | rejected manifest: FAIL; inadmissible raw file: UNCONFIRMED/BLOCKED | adv_01, adv_02, adv_03, F:declarations_are_informational_only_both_ways, F:raw_predicate_field_makes_evidence_inadmissible | PASS |
| 18 | Valid synthetic fixture gives an adapter PASS only (s18.20) | synthetic bundle | all gates and predicates PASS; `inr_external_reconstruction_pass` and `fresh_local_inr_pass` false constants | - | adv_20 | PASS |
| 19 | Provider-attested provenance (real external assurance) | none in v0 | not implemented | adapter PASS is not assurance | adv_20 (shows a synthetic bundle passes) | UNCONFIRMED |
| 20 | Integration into the INR-001 classification | - | not implemented; INR tooling unchanged | INR external predicates stay UNCONFIRMED | existing INR suite | UNCONFIRMED |
| 21 | Accepted INR-001 local tooling unchanged | `docs/inr_001/*` outside `xr/` | none | - | existing INR suite (46 tests) unchanged | PASS |

## Totals

- PASS: 15 (rows 1-5, 7-9, 12-14, 16-18, 21)
- PARTIAL: 3 (rows 6, 10, 11)
- UNCONFIRMED: 3 (rows 15, 19, 20)
- FAIL: 0

## Recorded deviation

The bundle adds `raw/target/<pinned PSM file>` to the request's raw list, so the
adapter can hash the acquired PSM bytes itself and derive the required-object set
from the digest-verified pinned example. No file outside `docs/inr_001/xr/` was
added or modified.
