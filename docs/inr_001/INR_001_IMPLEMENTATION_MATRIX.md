> **SUPERSEDED - FAILED / NOT CLOSED.** This matrix belongs to implementation candidate
> `99418b4ff852e9938d785725b49eef124fa841c3`, which failed independent targeted review
> (finding M1: self-attested verifier; a synthetic event reached PASS). Its `18 / 18 PASS`
> claim is withdrawn. It is kept unmodified below as the historical record. Current state:
> `INR_001_CANDIDATE_SUPERSESSION.md` and `INR_001_IMPLEMENTATION_MATRIX_R2.md`.

# INR-001 Implementation Closure Matrix

Failed candidate preserved: `c0747cc2b206ddd84aee2c04265813541cb21c7e`

That candidate passed its own local 20/20 tests, but independent review found 7 material issues. Those tests are therefore recorded as insufficient and this matrix is the remediation reference.

Root invariant: executor-controlled event values are not trusted facts. Security-relevant facts must be measured by trusted code, derived from trusted capture, matched against trusted frozen configuration, or classified non-PASS.

| finding_id | design invariant | implementation function/source | trusted evidence source | verifier check | adversarial test | test result | status |
|---|---|---|---|---|---|---|---|
| INR-MF-001 | distribution/executed bytes bound | `validate_event` byte identity checks | `byte_identity_evidence.measured_by=capture_inr_v0` | missing/fake/changed digest rejects PASS | `test_001_*`, `test_004_toctou_swap` | PASS | PASS |
| INR-MF-002 | measured source equals executed module | `validate_event` module execution checks | capture import probe fields | preloads/loader/path mismatch reject PASS | `test_002_*`, `test_008_*` | PASS | PASS |
| INR-MF-003 | Git runtime bound | `validate_event` Git contract checks | capture/runtime Git evidence | fake git/GIT_DIR/GIT_WORK_TREE/replace/alternates reject PASS | `test_003_*` | PASS | PASS |
| INR-MF-004 | no TOCTOU mutation | byte post-measurement + protected set checks | capture measurements | post digest/protected boundary mismatch rejects PASS | `test_004_toctou_swap` | PASS | PASS |
| INR-MF-005 | complete command/control inventory | case binding/profile checks | trusted profile + capture records | omitted case rejects PASS | `test_005_omitted_control` | PASS | PASS |
| INR-MF-006 | self-declared non-origin insufficient | non-origin evidence checks | runner/workspace/acquisition evidence | `is_non_origin` alone rejects PASS | `test_006_self_claim_non_origin_not_enough` | PASS | PASS |
| INR-MF-007 | evidence not reconstructed after run | capture record/file hash validation | capture-created stdout/stderr files | missing/reconstructed log rejects PASS | `test_007_reconstructed_logs_missing_file` | PASS | PASS |
| INR-MF-008 | import hook/preload/pyc blocked | module execution policy | import probe evidence | sitecustomize/pyc/preload rejects PASS | `test_008_*` | PASS | PASS |
| INR-MF-009 | parent/symlink/dependency protected | protected set isolation checks | isolation evidence | writable parent/symlink rejects PASS | `test_009_*` | PASS | PASS |
| INR-MF-010 | executor cannot weaken profile | profile-owned mandatory cases | trusted profile | optionalized case rejects PASS | `test_010_required_case_optional` | PASS | PASS |
| INR-MF-011 | same-host container/VM non-qualifying | strict runner class check | non-origin evidence | same-host container rejects PASS | `test_011_same_host_container` | PASS | PASS |
| INR-MF-012 | all-writer isolation required | protected set all-writer evidence | isolation evidence | unknown writer isolation rejects PASS | `test_012_other_writer_mutation` | PASS | PASS |
| INR-MF-013 | trusted target/profile binding | trusted constants/profile digest | verifier configuration | wrong profile digest rejects PASS | `test_013_weaker_profile` | PASS | PASS |
| INR-MF-014 | no shared mutable state | non-origin shared-state checks | non-origin evidence | shared cache rejects PASS | `test_014_shared_mutable_state` | PASS | PASS |
| INR-MF-015 | origin reference pre-frozen | origin binding/non-origin checks | trusted origin config | posthoc origin rejects PASS | `test_015_posthoc_origin_choice` | PASS | PASS |
| INR-MF-016 | no cross-event replay | event/challenge binding per result | capture/current event records | old event result rejects PASS | `test_016_cross_event_replay` | PASS | PASS |
| INR-MF-017 | trusted origin set binding | trusted constants/origin digest | verifier configuration | wrong origin set rejects PASS | `test_017_wrong_origin_set` | PASS | PASS |
| INR-MF-018 | capture launches target process | capture record validation | capture process record | wrapper without child rejects PASS | `test_018_wrapper_without_child` | PASS | PASS |

Totals: `18 / 18 PASS`.
