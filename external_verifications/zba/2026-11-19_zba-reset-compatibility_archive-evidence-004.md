# ZBA Reset Compatibility 0.1 — archive evidence record 004

**Review date:** 2026-11-19 JST  
**Verdict:** **PINNED_REFERENCE_REPLAY_PASS / LIMITED_INDEPENDENT_N4_ORACLE_PASS / ARCHIVE_MANIFEST_PASS**. Not a general mathematical proof or formal independent-witness qualification.

## Exact evidence identity

- GitHub Actions run: https://github.com/chrono-vector/weaver-forge/actions/runs/44481500838
- Run ID: `44481500838`; workflow source commit: `3f6e847f616786131c67f507534a81c0ad14db1d`.
- Run branch: `development/independent-verification-v2`.
- External source: `ResearchForumOnline/research@60c343237cbf17ee3ec2969c009ec026840d618e`.
- Replay job ID `135414558650`: completed/success.
- Evidence archive job ID `135414631892`: completed/success.
- Archive artifact `zba-reset-compatibility-run-evidence` ID `14509070711`; GitHub SHA-256 `a7d4522ba6c9839526640f959053661be3858856aa7791fd291c485cbf8fcba6`; size `8137` bytes; expiry shown by API `2027-02-17T07:41:03Z`.
- Source result artifact `zba-reset-compatibility-output` ID `14508148709`; SHA-256 `061eb7d5162c3a5441d53762d7b9adf33c2e73a3c11d576473e17a1bd0a63d70`; size `1304` bytes; expiry `2026-12-19T07:41:09Z`.
- Owner-uploaded `zba-reset-compatibility-run-evidence.zip`: 8137 bytes, SHA-256 `a7d4522ba6c9839526640f959053661be3858856aa7791fd291c485cbf8fcba6`, exact GitHub digest and byte size match.
- ZIP CRC test passed. Inner output ZIP CRC test passed.

## Directly inspected outer ZIP contents

| Filename | Bytes | independently calculated SHA-256 |
| --- | ---: | --- |
| `RUN_METADATA.txt` | 184 | `d03e6b4b98a8940c92974c2f7de9d6bd1f9bce780bee34ddba2f2f0a8b7677e7` |
| `zba-reset-job.log` | 22027 | `77cef684d92a9b210c93d057c0d77346bdbe987abbc95e775c0a23e12aca8095` |
| `zba-reset-output.zip` | 1304 | `061eb7d5162c3a5441d53762d7b9adf33c2e73a3c11d576473e17a1bd0a63d70` |
| `SHA256SUMS.txt` | 254 | `24b4bf857c843e8c6b677259c45f5a26d6bfacf3b7fc37690109549b84f560a1` |

All 3 entries referenced in SHA256SUMS.txt matched independent SHA-256 calculations. The manifest correctly does not list itself.

## Inner ZIP

| Filename | Bytes | SHA-256 |
| --- | ---: | --- |
| `zba-reset-stdout.json` | 170 | `b815962074021852f82e7b7311dfe98dcaf95143c0e57ae14a13d96e15c1abf7` |
| `zba-reset-results.json` | 6299 | `feb2984576f8a30f03bba21f0283378cd02dc6b4f01ebd424ad162fdf0760b9e` |

The result JSON reported `status=passed`, `exhaustive_validator_cases=496`, `synthesis_cases=248`. The five fixed cases `n=4,5,6,7,8` contain respectively 16,32,64,128,256 validators and 8,16,32,64,128 synthesis cases, totals 496 and 248. The 36-state fiber's distribution is **formula-derived**, explicitly **NOT** exhaustive over 2^36 validators.

The **actual logged output lines**, not just echoed commands, included:

```text
ZBA_RESET_REPLAY=PASS finite_cases=496 synthesis_cases=248 fiber=36(formula_only)
ZBA_RESET_INDEPENDENT_ORACLE=PASS n=4 validators=16 histogram_matches; mutated_histogram_rejected
```

The added n=4 finite oracle uses a distinct composition/closure implementation to compare the 16-validator monoid-size histogram, and checks that a corrupted expected histogram differs. This is a narrow independent-computation cross-check, not a standalone full ZBA validator implementation or independent theorem proof.

## Preservation and claim limitations

The original binary archive and full raw job log are **not incorporated into this Markdown or Git history**. They remain temporarily in the GitHub Actions artifact and the user-provided uploaded ZIP. Preserve the original bytes in a controlled store and check SHA-256 before the retention expiry. This report does not make stronger claims about general correctness, all 2^36 validator cases, peer review, cryptographic safety, or production-readiness.

Historical RC8/main/Ryan witness material untouched; previous ZBA and ASIN-HHC receipts not overwritten.
