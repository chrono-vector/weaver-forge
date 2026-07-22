# WITNESS_VERDICT.md — required fields (evidence_schema_version=1, 1.0.0-rc4)

Authored by the independent Witness. The `key=value` lines and the single
`Witness proposed verdict:` line below are structurally validated.

- `outcome` must be one of the five build outcomes and must equal the
  authoritative BUILD_EXIT_CODE.txt outcome.
- `verdict_ceiling` is one of PASS | PARTIAL | FAIL | INDETERMINATE and is the
  highest verdict the evidence permits. The validator recomputes a machine
  ceiling and REJECTS any proposed verdict above it.
- `grok_build_commit` must equal the pinned canonical commit.
- `product_executed` and `ldd_used` must be exactly NO.
- `maintainer_intake_verdict` is `pending` at submission time.
- The `Witness proposed verdict:` line must be exact uppercase
  PASS | PARTIAL | FAIL | INDETERMINATE and must not exceed verdict_ceiling.

```
evidence_schema_version=1
run_id=<run-id-token>
package_tag=grok-build-witness-v1.0.0-rc4
weaver_forge_commit=<40-char lowercase hex commit>
grok_build_commit=98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce
outcome=CARGO_SUCCEEDED_ARTIFACT_PRESENT
verdict_ceiling=PASS
product_executed=NO
ldd_used=NO
maintainer_intake_verdict=pending
```

Witness proposed verdict: PASS

## Justification

Reference WITNESS_CLASSIFICATION.md's precedence table and cite the specific
evidence fields (outcome, identity matches, static-inspection completeness)
that support the proposed verdict at or below the ceiling.
