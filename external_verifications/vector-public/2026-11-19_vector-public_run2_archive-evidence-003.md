# VECTOR Public Reference v0 — corrected Run #2 archive evidence record 003

**Review date:** 2026-11-19 JST  
**Verdict:** **PUBLIC_SYNTHETIC_TESTS_PASS_105 / ACTIONS_JOBS_SUCCESS / ARCHIVE_MANIFEST_PASS**. **Not** VECTOR operational authority, private WORLD THIRD integration, Owner Acceptance, or Independent Witness qualification.

## Verifiable exact run identity

- Workflow: `.github/workflows/vector-public-reference.yml`.
- Weaver Forge code commit: `5c3202a6bd4f72c362fc7de50a08e2f42219db13` (corrected JUnit XML gate).
- Public source: `chrono-vector/vector-core@d0db1d8bfa38ae4d54f54ae3153f98f87ab2f776`.
- Run URL: https://github.com/chrono-vector/weaver-forge/actions/runs/44482863686
- Run ID `44482863686`.
- Test job `135419066362`: GitHub `completed/success`.
- Archive job `135419147517`: GitHub `completed/success`.
- Evidence artifact ID `14508749077`, `vector-public-reference-run-evidence`, **9476 bytes**, GitHub SHA-256 `2d01a9470af5a8d218ee665366744a7522fad9f984424b955bd5b97b8af22c5a`, expiry `2027-02-17T07:51:40Z`.
- Inner output artifact ID `14509595412`, `vector-public-reference-output`, **2625 bytes**, SHA-256 `3013819e612b5f313d3270716b1e451c41dcba5c05eaf244d4eb15e95a827f52`, expiry `2026-12-19T07:51:48Z`.
- User-provided original archive filename `vector-public-reference-run-evidence (1).zip`, SHA-256 **2d01a9470af5a8d218ee665366744a7522fad9f984424b955bd5b97b8af22c5a**, size **9476**; exact match to GitHub artifact digest and size. ZIP CRC test succeeded.

## Archive checksums (calculated directly from uploaded bytes)

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| `RUN_METADATA.txt` | 192 | `bb506fa7778d10e6f5e4def5d919647f438773ee9267caf6c46b1ca16c3b02c1` |
| `vector-public-job.log` | 23148 | `8bfbb52cfcc06580e263f23395161811def0128802c5da893c7f028c29d1bbda` |
| `vector-public-output.zip` | 2625 | `3013819e612b5f313d3270716b1e451c41dcba5c05eaf244d4eb15e95a827f52` |
| `SHA256SUMS.txt` | 262 | `fbfe8eb0d6fe16256d954e575f165661dd8540d03febe8156e8b774e2287abb6` |

All three files listed in `SHA256SUMS.txt` independently matched. Manifest does not list itself. Inner artifact ZIP CRC also passed.

| Inner file | Bytes | SHA-256 |
| --- | ---: | --- |
| `vector-public-pytest.xml` | 14443 | `f96873f67e3f4407c8bfee0d68ff1d5013f48eac0b0f3cdd28f0022065bde833` |
| `vector-public-test-output.txt` | 160 | `3d671003f3db5e1802f451e3671e4612726d7b6764553203c7954413f7eb3403` |
| `vector-run-metadata.txt` | 62 | `8e1dc6efdf7f097c36877f7d72e862cecade39bef7acaec28d71aa96792f0aa9` |

## Actual observed test result

- Original JUnit XML contains a single `testsuite`: `tests="105", failures="0", errors="0", skipped="0"`.
- Actual archived run log states: `VECTOR_PUBLIC_SYNTHETIC_TESTS=PASS tests=105 failures=0 errors=0 skipped=0 (public reference only; no execution authority)`.
- Test job and archive job both have GitHub `success` conclusions.
- This is **a new run with the corrected JUnit gate**, not a relabeling of the previous failed run.
- Earlier Run #1, ID `44482426799`, must remain **WORKFLOW_FAIL** despite its 105/105 underlying passing tests; preserve record `2026-11-19_vector-public_run1_evidence-and-ci-failure-002.md`.

## Claim and preservation limits

This independently checked archive demonstrates that the pinned **public sanitized VECTOR synthetic reference tests** executed successfully. The workflow does **not** execute private Job Agent, EIG, VECTOR authority, private Integration Harness, real handoff, operational evidence validation, or Independent Witness qualification.

This receipt preserves hashes and run identity, **not the original archive bytes or full raw log in repository Git history**. Keep an original externally in access-controlled storage and verify SHA-256 before expiry. No modifications to RC8, main, other repos, historic receipts or previous Run #1.
