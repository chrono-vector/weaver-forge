# WITNESS_VERDICT.md — required fields (evidence_schema_version=1, RC6-R6 / rc6.5)

Authored by the independent Witness. The `key=value` lines and the single
`Witness proposed verdict:` line below are structurally validated.

- `outcome` must equal the authoritative BUILD_EXIT_CODE.txt outcome.
- `verdict_ceiling` is one of PASS | PARTIAL | FAIL | INDETERMINATE.
- The validator recomputes a machine ceiling and REJECTS any proposed verdict above it (validator-computed outcome ceiling). This template is a proposed-verdict interface only (active package identity Weaver Forge Future Candidate 1 / WF-FC-01 / weaver-forge-fc-01). Independent Witness execution, READY, RC9, and C-014 determination are out of scope for static implementation.
- `maintainer_intake_verdict` must be exactly `pending` at final submission.
  Later maintainer dispositions append outside the hashed package at
  `external_verifications/grok-build/witness-submissions/<run_id>/MAINTAINER_INTAKE_LEDGER.txt`
  and must not mutate this file.
- Equality-bind statement / deviation / redaction / ceiling identities.

```
evidence_schema_version=1
run_id=<run-id-token>
package_identity_ref=WEAVER_FORGE_PACKAGE_IDENTITY.txt
final_binding_ref=WEAVER_FORGE_FINAL_BINDING.txt
package_tag=weaver-forge-fc-01
# package_version mapping (active): WF-FC-01 -> weaver-forge-fc-01 (Repository Owner G-3)
weaver_forge_commit=<40-char lowercase hex commit>
grok_build_commit=98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce
outcome=CARGO_SUCCEEDED_ARTIFACT_PRESENT
verdict_ceiling=PASS
product_executed=NO
ldd_used=NO
maintainer_intake_verdict=pending
witness_statement_sha256=<sha256 of WITNESS_STATEMENT.md>
statement_identity_sha256=<equals WITNESS_STATEMENT.md statement_identity_sha256>
deviations_sha256=<sha256 of DEVIATIONS.txt>
deviation_state=NONE
redactions_index_sha256=<sha256 of REDACTIONS_INDEX.txt>
redaction_state=NONE
final_machine_ceiling=<validator-authoritative ceiling>
```

Witness proposed verdict: PASS

## Justification

Reference WITNESS_CLASSIFICATION.md's precedence table and cite the specific
evidence fields that support the proposed verdict at or below the ceiling.
