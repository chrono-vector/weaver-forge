# VECTOR Public Reference v0 — Run #1 evidence record 002 (test pass / CI gate failure)

**Review date:** 2026-11-19 JST
**Status:** **TESTS_PASS_105 / WORKFLOW_FAIL (output-format assertion)**.
Do not label the initial workflow run as all-green or as fully PASS.

## Evidence provenance
- Workflow: `.github/workflows/vector-public-reference.yml` at commit `0b6762cc45bb99bafd356867634c03b479bb97f4`.
- Public source: `chrono-vector/vector-core@d0db1d8bfa38ae4d54f54ae3153f98f87ab2f776`.
- GitHub Actions run: https://github.com/chrono-vector/weaver-forge/actions/runs/44482426799
- Run ID: **44482426799**.
- Test job ID **135417613887** GitHub conclusion: **failure**; test step concluded failure.
- Evidence archive job ID **135417684861** conclusion: success.
- Original evidence artifact ID **14508524010**, byte size **9238**, SHA-256 `63b9b3066ca17ae095fb9c4f2c53246a0b04f28593ac0e8e71d732355f3e08f2`, expires `2027-02-17T07:48:16Z`.
- Independent results artifact ID **14509201179**, byte size **2654**, SHA-256 `53d47f5718195a760738c5bbef36c0156cc31c019c47f91e33f91e7dfb66fda2`, expires `2026-12-19T07:48:24Z`.
- Owner-uploaded `vector-public-reference-run-evidence.zip` inspected. SHA-256 matches original GitHub artifact exactly; ZIP CRC verified.

## Exact original archive entries and SHA-256

| Entry | Size (bytes) | SHA-256 |
| --- | ---: | --- |
| `RUN_METADATA.txt` | 192 | `1e04b46b9c46b27473e2e91ca708186fe25e68e3aa15a308fcfd097d8a12b2c9` |
| `SHA256SUMS.txt` | 262 | `6d1755819c394f51f62626d98ef03a6fad696ae0ebc1d2377d0e84f25b4290b6` |
| `vector-public-job.log` | 22187 | `68aad1997e2c011009520319eae702a7fcff70deae4c6a39afa59ba8680e5b08` |
| `vector-public-output.zip` | 2654 | `53d47f5718195a760738c5bbef36c0156cc31c019c47f91e33f91e7dfb66fda2` |

All three hashes in `SHA256SUMS.txt` match actual entry bytes. Internal result ZIP also passes CRC.

| Inner result | Size (bytes) | SHA-256 |
| --- | ---: | --- |
| `vector-public-pytest.xml` | 14443 | `f3ee85ed7e5ff708e0003f218db9b9d243d532be4b13386612feb00612fba84a` |
| `vector-public-test-output.txt` | 160 | `3d671003f3db5e1802f451e3671e4612726d7b6764553203c7954413f7eb3403` |
| `vector-run-metadata.txt` | 62 | `8e1dc6efdf7f097c36877f7d72e862cecade39bef7acaec28d71aa96792f0aa9` |

The JUnit XML testsuite metadata says `tests="105" errors="0" failures="0" skipped="0"` (105/105 tests successful). The stdout contains the two 72/33 dot progress lines with `[68%]` and `[100%]` but *no* `105 passed` text.

## Root-cause assessment

The workflow ran:

```sh
python -m pytest -q --junitxml="$GITHUB_WORKSPACE/vector-public-pytest.xml" 2>&1 | tee "$GITHUB_WORKSPACE/vector-public-test-output.txt"
test -s vector-public-pytest.xml
grep -Eq '[0-9]+ passed' vector-public-test-output.txt
```

The `pytest` call successfully emitted a JUnit result XML with 105 passed, 0 errors/failures/skips. The final grep criterion erroneously expected a particular stdout summary that was not present; this grep exited with code 1 and the **test step/job concluded failure**. This is a **CI assertion issue**, not a failing public VECTOR test. The original failure remains evidence and **must not be overwritten or relabeled**.

The log confirms Python 3.11.18, pytest 9.2.0 and jsonschema 4.26.0 as installed. Dependencies are not version-locked.

## Corrective gate

Replace the brittle stdout grep with an XML-based check of `tests>0`, `errors=0`, `failures=0`, `skipped=0`. Preserve the original run, and **do not claim the corrected workflow run PASS until fresh actual GitHub job and ZIP evidence are examined**.

This tests only sanitized public VECTOR synthetic reference behavior; it does not exercise real VECTOR authority, private WORLD THIRD Job Agent/Integration Harness, real EIG/Weaver handoff, or independent witness acceptance.

Historical RC8, main and external repositories untouched.
