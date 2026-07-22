# WITNESS_VERDICT.md — required fields (evidence_schema_version=1)

Fields below are parsed as `key=value` lines by the validator regardless of
surrounding markdown headings. Keep the exact field names.

evidence_schema_version=1
run_id=
package_tag=grok-build-witness-v1.0.0-rc3
weaver_forge_commit=
grok_build_commit=98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce
product_executed=NO
ldd_used=NO
maintainer_intake_verdict=pending

Exactly one of the following four lines must appear verbatim, uppercase,
with no other text on the line. The validator performs an exact,
case-sensitive match; `pass`, `Pass`, and any other case variant are
rejected. Delete the three lines you are not selecting.

Witness proposed verdict: PASS
Witness proposed verdict: PARTIAL
Witness proposed verdict: FAIL
Witness proposed verdict: INDETERMINATE

## Justification

(Reference classification precedence in WITNESS_CLASSIFICATION.md. Explanatory
prose may use the words "pass", "fail", etc. freely — only the exact selection
line above is parsed as the verdict.)

## Deviations

(Summary or pointer to DEVIATIONS.txt.)
